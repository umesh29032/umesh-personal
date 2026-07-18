#!/usr/bin/env python
"""nest.py — marker generation engines + INDEPENDENT layout verification.

Engines (ADR-A): `svgnest` (primary, node subprocess on the vendored core)
and `blf` (deterministic grid bottom-left-fill floor — always available).
`auto` runs both and returns every complete candidate.

EVERY candidate is verified here with shapely BEFORE it leaves the runtime:
pairwise overlap, width containment, exact length from the real polygons —
the engine's own claims are never trusted (honest-AI).

Protocol: nest.py --in job.json --out result.json
job: {"width_mm", "spacing_mm"?, "margin_mm"?, "timebox_s"?, "seed"?,
      "engine": "auto"|"svgnest"|"blf",
      "pieces": [{"key", "polygon_mm" (y-up, grain along +y),
                  "qty", "allow_180", "allow_mirror"}]}
result: {"ok", "candidates": [{engine, placements:[{key, instance,
         mirrored, rotation_deg, polygon_mm}], length_mm,
         verification:{ok, max_overlap_mm2, within_width, piece_count}}],
         "errors": {engine: reason}}
"""
import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
from shapely import affinity
from shapely.geometry import Point, Polygon
from shapely.prepared import prep

from runtime import PIPELINE_VERSION

GRID = 2.0
OVERLAP_TOL_MM2 = 4.0        # raster/clipper rounding allowance
WIDTH_TOL_MM = 0.5


# ---------- BLF floor (P0-proven, parametrized) ----------------------------

def _blf_variants(poly, allow_180, allow_mirror, spacing):
    variants = [('r0', poly, 0, False)]
    if allow_180:
        variants.append(('r180', affinity.rotate(poly, 180, origin='centroid'),
                         180, False))
    if allow_mirror:
        m = affinity.scale(poly, xfact=-1, origin='centroid')
        variants.append(('m0', m, 0, True))
        if allow_180:
            variants.append(('m180', affinity.rotate(m, 180, origin='centroid'),
                             180, True))
    out = []
    for label, p, rot, mir in variants:
        p = affinity.translate(p, -p.bounds[0], -p.bounds[1])
        # buffered outline provides the spacing; shift so the BUFFER sits at
        # (0,0) and the true poly sits `pad` inside it
        b = p.buffer(spacing / 2, join_style=2)
        p = affinity.translate(p, -b.bounds[0], -b.bounds[1])
        b = affinity.translate(b, -b.bounds[0], -b.bounds[1])
        gw = int(np.ceil(b.bounds[2] / GRID)) + 1
        gh = int(np.ceil(b.bounds[3] / GRID)) + 1
        mask = np.zeros((gh, gw), dtype=bool)
        xs = (np.arange(gw) + 0.5) * GRID
        ys = (np.arange(gh) + 0.5) * GRID
        pb = prep(b)
        for j, y in enumerate(ys):
            mask[j] = [pb.contains(Point(x, y)) for x in xs]
        out.append({'label': label, 'mask': mask, 'poly': p,
                    'rot': rot, 'mirrored': mir,
                    'pad': spacing / 2})
    return out


BLF_TIMEOUT_MSG = ('the Quick method ran out of time on this layout — '
                   'use the Thorough method for large mixes, or reduce '
                   'the piece count.')


def run_blf(job):
    """Deterministic grid BLF. Axes: canonical pieces keep grain along +y;
    the lay LENGTH runs along y (grain parallel to selvage), width along x.
    Output rings are converted to the common lay frame (x = length,
    y = width) to match the svgnest engine.

    Phase-6 M1 (finding F1): the pass carries an INTERNAL deadline and
    gives up honestly instead of hanging until the bridge kills it."""
    spacing = float(job.get('spacing_mm', 2.0))
    width = float(job['width_mm'])
    gw = int(width // GRID)
    deadline = time.time() + float(job.get('timebox_s', 20))
    items = []
    for pc in job['pieces']:
        poly = Polygon(pc['polygon_mm'])
        variants = _blf_variants(poly, pc.get('allow_180', True),
                                 pc.get('allow_mirror', False), spacing)
        for q in range(int(pc['qty'])):
            items.append({'key': pc['key'], 'instance': q,
                          'variants': variants, 'area': poly.area})
    items.sort(key=lambda i: (-i['area'], i['key'], i['instance']))

    occ = np.zeros((1, gw), dtype=bool)              # rows = length(y), cols = width(x)

    def grow(rows):
        nonlocal occ
        if rows > occ.shape[0]:
            occ = np.vstack([occ,
                             np.zeros((rows - occ.shape[0], gw), dtype=bool)])

    placements = []
    for it in items:
        best = None
        for v in it['variants']:
            mask = v['mask']
            mh, mw = mask.shape                       # mh along length, mw across width
            if mw > gw:
                continue
            found = None
            y = 0
            while y < occ.shape[0] + mh + 2:
                if (y % 64 == 0) and time.time() > deadline:   # honest give-up
                    return None, BLF_TIMEOUT_MSG
                grow(y + mh)
                sub = occ[y:y + mh]
                for x in range(0, gw - mw + 1):
                    if not (mask & sub[:, x:x + mw]).any():
                        found = (y, x)
                        break
                if found:
                    break
                y += 1
            if found:
                fy, fx = found
                score = (fy + mh, fx)                 # shortest lay, then left
                if best is None or score < best[0]:
                    best = (score, fy, fx, v)
        if best is None:
            return None, 'a piece does not fit the fabric width'
        _, fy, fx, v = best
        grow(fy + v['mask'].shape[0])
        occ[fy:fy + v['mask'].shape[0], fx:fx + v['mask'].shape[1]] |= v['mask']
        px = fx * GRID + v['pad']                     # across width (x)
        py = fy * GRID + v['pad']                     # along length (y)
        placed = affinity.translate(v['poly'], px, py)
        # common lay frame: x = length, y = width  ->  swap axes
        ring = [[round(y_, 3), round(x_, 3)]
                for x_, y_ in placed.exterior.coords[:-1]]
        placements.append({'key': it['key'], 'instance': it['instance'],
                           'mirrored': v['mirrored'],
                           'rotation_deg': v['rot'], 'polygon_mm': ring})
    return placements, None


# ---------- SVGnest (primary) ----------------------------------------------

def run_svgnest(job, base):
    node = shutil.which('node')
    if node is None:
        return None, 'node runtime not available on this machine'
    with tempfile.TemporaryDirectory(prefix='pai_nest_') as td:
        jin = Path(td) / 'job.json'
        jout = Path(td) / 'out.json'
        jin.write_text(json.dumps(job))
        proc = subprocess.run(
            [node, str(base / 'nest_runner.js'), str(jin), str(jout)],
            capture_output=True, text=True,
            timeout=float(job.get('timebox_s', 20)) + 30)
        if proc.returncode != 0:
            return None, f'svgnest runner failed: {proc.stderr.strip()[-300:]}'
        res = json.loads(jout.read_text())
    if not res.get('ok'):
        return None, res.get('error', 'svgnest produced no placement')
    return res['placements'], None


# ---------- Phase-5 M1: optimize op (locks/out-of-scope = obstacles) --------

EFFORT_MAP = {'fast': (8, 3.0), 'balanced': (30, 10.0), 'best': (80, 30.0)}
UTIL_TOL_PCT = 0.01              # utilization tie tolerance (percentage points)


def _swap(ring):
    """lay frame (x=length, y=width) <-> internal BLF frame (x=width,
    y=length) — the exact convention run_blf already uses."""
    return [[y, x] for x, y in ring]


def _raster_fixed(fixed_rings_internal, gw, spacing):
    """Occupancy mask with every fixed piece (buffered by spacing/2) burned
    in as a permanent obstacle."""
    from shapely.prepared import prep as _prep
    max_y = 0.0
    polys = []
    for ring in fixed_rings_internal:
        b = Polygon(ring).buffer(spacing / 2, join_style=2)
        polys.append(_prep(b))
        max_y = max(max_y, b.bounds[3])
    rows = int(np.ceil(max_y / GRID)) + 2 if polys else 1
    occ = np.zeros((rows, gw), dtype=bool)
    if not polys:
        return occ
    xs = (np.arange(gw) + 0.5) * GRID
    for j in range(rows):
        y = (j + 0.5) * GRID
        row = occ[j]
        for pb in polys:
            hits = [pb.contains(Point(x, y)) for x in xs]
            row |= np.asarray(hits, dtype=bool)
    return occ


def _place_free(items, base_occ, gw, deadline=None):
    """One BLF pass of `items` (pre-built variants) over a COPY of the
    obstacle mask. Returns lay-frame placements, None (no fit), or the
    string 'timeout' when the internal deadline expires (Phase-6 M1)."""
    occ = base_occ.copy()

    def grow(rows):
        nonlocal occ
        if rows > occ.shape[0]:
            occ = np.vstack([occ,
                             np.zeros((rows - occ.shape[0], gw), dtype=bool)])

    out = []
    for it in items:
        best = None
        for v in it['variants']:
            mask = v['mask']
            mh, mw = mask.shape
            if mw > gw:
                continue
            found = None
            y = 0
            while y < occ.shape[0] + mh + 2:
                if (deadline is not None and y % 64 == 0
                        and time.time() > deadline):
                    return 'timeout'
                grow(y + mh)
                sub = occ[y:y + mh]
                for x in range(0, gw - mw + 1):
                    if not (mask & sub[:, x:x + mw]).any():
                        found = (y, x)
                        break
                if found:
                    break
                y += 1
            if found:
                fy, fx = found
                score = (fy + mh, fx)
                if best is None or score < best[0]:
                    best = (score, fy, fx, v)
        if best is None:
            return None
        _, fy, fx, v = best
        grow(fy + v['mask'].shape[0])
        occ[fy:fy + v['mask'].shape[0], fx:fx + v['mask'].shape[1]] |= v['mask']
        px = fx * GRID + v['pad']
        py = fy * GRID + v['pad']
        placed = affinity.translate(v['poly'], px, py)
        ring = [[round(y_, 3), round(x_, 3)]              # swap back to lay
                for x_, y_ in placed.exterior.coords[:-1]]
        out.append({'key': it['key'], 'instance': it['instance'],
                    'mirrored': it['mirrored'],
                    'rotation_deg': (it['base_rot'] + v['rot']) % 360,
                    'locked': False,
                    'polygon_mm': ring})
    return out


def _compactness(free_placements):
    """Rule 9.7 tie-break ONLY: spread of free-piece centroids around
    their mean (lower = more compact). Never beats utilization/length."""
    cents = []
    for p in free_placements:
        ring = p['polygon_mm']
        cx = sum(q[0] for q in ring) / len(ring)
        cy = sum(q[1] for q in ring) / len(ring)
        cents.append((cx, cy))
    if len(cents) <= 1:
        return 0.0
    mx = sum(c[0] for c in cents) / len(cents)
    my = sum(c[1] for c in cents) / len(cents)
    return round(sum(((c[0] - mx) ** 2 + (c[1] - my) ** 2) ** 0.5
                     for c in cents), 3)


def run_optimize(job):
    """Rearrange ONLY the free pieces around fixed obstacles.

    Correction-1 ranking: discard invalid (overlap / width / height /
    moved-fixed) FIRST; then utilization desc -> length asc (within
    utilization tolerance) -> compactness LAST tie-break.
    Correction-2: fully deterministic per seed (fixed iteration order,
    seeded shuffles, no wall-clock dependence in results — the timebox
    only caps how many orderings run, and ordering count is itself
    deterministic per effort)."""
    import random

    width = float(job['width_mm'])
    height = float(job['height_mm'])
    spacing = float(job.get('spacing_mm', 2.0))
    seed = int(job.get('seed', 42))
    wanted = max(1, min(8, int(job.get('options_wanted', 3))))
    effort = str(job.get('effort', 'balanced')).lower()
    if effort not in EFFORT_MAP:
        return {'ok': False, 'error': f'unknown effort {effort!r}'}
    orderings, timebox = EFFORT_MAP[effort]

    fixed_in = job.get('fixed') or []
    free_in = job.get('free') or []
    if not free_in:
        return {'ok': False,
                'error': 'nothing to optimize — every piece is locked or '
                         'out of the selection.'}

    gw = int(width // GRID)
    fixed_internal = [_swap(f['polygon_mm']) for f in fixed_in]
    base_occ = _raster_fixed(fixed_internal, gw, spacing)

    # free pieces: local lay-frame rings -> internal frame -> variants
    items = []
    for f in free_in:
        ring = _swap(f['polygon_mm'])
        poly = Polygon(ring)
        variants = _blf_variants(poly, bool(f.get('allow_180', True)),
                                 False, spacing)
        if all(v['mask'].shape[1] > gw for v in variants):
            return {'ok': False,
                    'error': f"piece {f['key']} does not fit the fabric "
                             'width.'}
        items.append({'key': f['key'], 'instance': f['instance'],
                      'mirrored': bool(f.get('mirrored')),
                      'base_rot': int(f.get('rotation_deg', 0)) % 360,
                      'variants': variants,
                      'area': poly.area})

    base_order = sorted(items, key=lambda i: (-i['area'], i['key'],
                                              i['instance']))
    rng = random.Random(seed)
    t0 = time.time()
    deadline = t0 + timebox
    raw = []
    tried = 0
    timeouts = 0
    for k in range(orderings):
        if time.time() > deadline:
            break
        if k == 0:
            order = base_order
        else:
            order = base_order[:]
            rng.shuffle(order)
        tried += 1
        placed = _place_free(order, base_occ, gw, deadline=deadline)
        if placed == 'timeout':               # honest give-up mid-pass (M1)
            timeouts += 1
            break
        if placed is not None:
            raw.append(placed)

    # combine + validate + rank
    fixed_out = [dict(f) for f in fixed_in]        # byte-identical passthrough
    total_area = (sum(Polygon(r).area for r in fixed_internal)
                  + sum(i['area'] for i in items))
    seen = set()
    valid = []
    dropped = {'overlap_or_width': 0, 'height': 0, 'timeout': timeouts}
    for placed in raw:
        placements = fixed_out + placed
        verification, length = verify_layout(width, placements, spacing)
        if not verification['ok']:                 # 9.1 overlap / 9.2 width
            dropped['overlap_or_width'] += 1
            continue
        if length > height + 0.001:                # 9.3 height
            dropped['height'] += 1
            continue
        key = json.dumps([[p['key'], p['instance'], p['rotation_deg'],
                           p['polygon_mm']] for p in placed])
        if key in seen:                            # dedupe
            continue
        seen.add(key)
        util = round(total_area / (width * length) * 100, 4) if length else 0.0
        valid.append({'placements': placements,
                      'length_mm': length,
                      'utilization_pct': util,
                      'compactness': _compactness(placed),
                      'verification': verification})
    if not valid:
        if timeouts and not raw:
            return {'ok': False, 'orderings_tried': tried,
                    'dropped': dropped, 'error': BLF_TIMEOUT_MSG}
        return {'ok': False, 'orderings_tried': tried, 'dropped': dropped,
                'error': "couldn't fit within the fabric height — unlock or "
                         'deselect more pieces, shorten the layout, or '
                         'increase the height.'}

    # utilization desc (tolerance-bucketed) -> length asc -> compactness asc
    valid.sort(key=lambda o: (-round(o['utilization_pct'] / UTIL_TOL_PCT),
                              o['length_mm'], o['compactness']))
    return {'ok': True, 'pipeline_version': PIPELINE_VERSION,
            'seed': seed, 'effort': effort, 'orderings_tried': tried,
            'dropped': dropped, 'options': valid[:wanted]}


# ---------- independent verification ----------------------------------------

def verify_layout(width_mm, placements, spacing_mm):
    polys = [Polygon(p['polygon_mm']) for p in placements]
    max_overlap = 0.0
    for i in range(len(polys)):
        for j in range(i + 1, len(polys)):
            if polys[i].intersects(polys[j]):
                max_overlap = max(max_overlap,
                                  polys[i].intersection(polys[j]).area)
    min_y = min((p.bounds[1] for p in polys), default=0)
    max_y = max((p.bounds[3] for p in polys), default=0)
    within = (min_y >= -WIDTH_TOL_MM
              and max_y <= width_mm + WIDTH_TOL_MM)
    length = max((p.bounds[2] for p in polys), default=0.0)
    return {'ok': bool(max_overlap <= OVERLAP_TOL_MM2 and within),
            'max_overlap_mm2': round(max_overlap, 3),
            'within_width': bool(within),
            'piece_count': len(polys)}, round(length, 2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--in', dest='inp', required=True)
    ap.add_argument('--out', dest='out', required=True)
    args = ap.parse_args()
    job = json.load(open(args.inp))
    base = Path(__file__).resolve().parent

    if job.get('op') == 'optimize':
        json.dump(run_optimize(job), open(args.out, 'w'))
        return 0

    if job.get('op') == 'verify':
        # Phase-4 workspace: verify a HUMAN-adjusted layout with THE SAME
        # verifier generation uses — one verification home, ever.
        verification, length = verify_layout(
            float(job['width_mm']), job['placements'],
            float(job.get('spacing_mm', 2.0)))
        json.dump({'ok': True, 'verification': verification,
                   'length_mm': length}, open(args.out, 'w'))
        return 0

    engine = job.get('engine', 'auto')
    spacing = float(job.get('spacing_mm', 2.0))

    candidates, errors = [], {}

    def add(engine_name, placements):
        verification, length = verify_layout(job['width_mm'], placements,
                                             spacing)
        candidates.append({'engine': engine_name,
                           'pipeline_version': PIPELINE_VERSION,
                           'spacing_mm': spacing,
                           'seed': job.get('seed', 42),
                           'placements': placements,
                           'length_mm': length,
                           'verification': verification})

    if engine in ('auto', 'blf'):
        pl, err = run_blf(job)
        if pl is not None:
            add('blf', pl)
        else:
            errors['blf'] = err
    if engine in ('auto', 'svgnest'):
        pl, err = run_svgnest(job, base)
        if pl is not None:
            add('svgnest', pl)
        else:
            errors['svgnest'] = err

    json.dump({'ok': bool(candidates), 'candidates': candidates,
               'errors': errors}, open(args.out, 'w'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
