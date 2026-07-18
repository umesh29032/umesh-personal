#!/usr/bin/env python
"""dxf_io.py — DXF-AAMA import/export <-> canonical geometry (ADR-C §7).

AAMA layer convention honored: 1 = cut boundary, 7 = grainline,
8 = internal lines, 11 = internal cutouts (holes).

Protocol:
  import: {"op":"import", "dxf_path"} -> {"ok", "pieces":[canonical,...],
           "units", "notes":[...]}
  export: {"op":"export", "geometry": canonical, "out_path"} -> {"ok",
           "dxf_path"}
"""
import argparse
import json
import math
import sys

import ezdxf

from runtime.canonical import mm_polygon_to_canonical, validate_canonical

INSUNITS_TO_MM = {0: 1.0, 1: 25.4, 4: 1.0, 5: 10.0, 6: 1000.0}


def do_import(job):
    doc = ezdxf.readfile(job['dxf_path'])
    unit = doc.header.get('$INSUNITS', 4)
    scale = INSUNITS_TO_MM.get(unit)
    notes = []
    if scale is None:
        return {'ok': False, 'error': f'unsupported $INSUNITS {unit}'}
    if unit == 0:
        notes.append('$INSUNITS=0 (unitless) — assuming millimetres')

    boundaries, holes, internals, grain = [], [], [], None
    for e in doc.modelspace():
        layer = str(e.dxf.layer)
        pts = _points(e, scale)
        if pts is None:
            continue
        if layer == '1' and len(pts) >= 3:
            boundaries.append(pts)
        elif layer == '11' and len(pts) >= 3:
            holes.append(pts)
        elif layer == '8' and len(pts) >= 2:
            internals.append(pts)
        elif layer == '7' and len(pts) >= 2 and grain is None:
            dx = pts[-1][0] - pts[0][0]
            dy = pts[-1][1] - pts[0][1]
            grain = {'angle_cdeg': int(round(math.degrees(
                math.atan2(dy, dx)) * 100)) % 36000}
    if not boundaries:
        return {'ok': False,
                'error': 'no closed boundary polyline on AAMA layer 1'}

    pieces = []
    for b in boundaries:
        # holes/internals are assigned to the boundary containing their
        # first vertex (single-piece files — the overwhelming AAMA case)
        mine_h = [h for h in holes if _inside(h[0], b)]
        mine_i = [i for i in internals if _inside(i[0], b)]
        minx = min(p[0] for p in b); miny = min(p[1] for p in b)
        feats = {
            'grain': grain, 'notches': [], 'drills': [],
            'internal_lines': [
                [[int(round((x - minx) * 1000)), int(round((y - miny) * 1000))]
                 for x, y in line] for line in mine_i],
            'fold_edge': None, 'seam_allowance': 'as_cut',
        }
        geo = mm_polygon_to_canonical(b, holes_mm=mine_h, features=feats)
        problems = validate_canonical(geo)
        if problems:
            return {'ok': False,
                    'error': f'imported geometry invalid: {problems}'}
        pieces.append(geo)
    return {'ok': True, 'pieces': pieces,
            'units': f'INSUNITS={unit}', 'notes': notes}


def _points(entity, scale):
    t = entity.dxftype()
    if t == 'LWPOLYLINE':
        pts = [(p[0] * scale, p[1] * scale) for p in entity.get_points()]
    elif t == 'POLYLINE':
        pts = [(v.dxf.location.x * scale, v.dxf.location.y * scale)
               for v in entity.vertices]
    elif t == 'LINE':
        pts = [(entity.dxf.start.x * scale, entity.dxf.start.y * scale),
               (entity.dxf.end.x * scale, entity.dxf.end.y * scale)]
    else:
        return None
    if len(pts) > 1 and pts[0] == pts[-1]:
        pts = pts[:-1]                        # canonical stores rings open
    return pts


def _inside(pt, poly):
    x, y = pt
    n = len(poly); inside = False
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]; xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def do_export(job):
    geo = job['geometry']
    problems = validate_canonical(geo)
    if problems:
        return {'ok': False, 'error': f'geometry invalid: {problems}'}
    doc = ezdxf.new('R2010')
    doc.header['$INSUNITS'] = 4               # millimetres
    msp = doc.modelspace()

    def mm(ring):
        return [(x / 1000.0, y / 1000.0) for x, y in ring]

    msp.add_lwpolyline(mm(geo['outer']), close=True,
                       dxfattribs={'layer': '1'})
    for h in geo.get('holes') or []:
        msp.add_lwpolyline(mm(h), close=True, dxfattribs={'layer': '11'})
    feats = geo.get('features') or {}
    for line in feats.get('internal_lines') or []:
        msp.add_lwpolyline(mm(line), close=False, dxfattribs={'layer': '8'})
    grain = feats.get('grain')
    if grain and grain.get('angle_cdeg') is not None:
        # draw the grainline through the bbox centre, half-bbox long
        xs = [p[0] for p in geo['outer']]; ys = [p[1] for p in geo['outer']]
        cx, cy = max(xs) / 2000.0, max(ys) / 2000.0
        L = max(max(xs), max(ys)) / 4000.0
        a = math.radians(grain['angle_cdeg'] / 100.0)
        msp.add_line((cx - L * math.cos(a), cy - L * math.sin(a)),
                     (cx + L * math.cos(a), cy + L * math.sin(a)),
                     dxfattribs={'layer': '7'})
    doc.saveas(job['out_path'])
    return {'ok': True, 'dxf_path': job['out_path']}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--in', dest='inp', required=True)
    ap.add_argument('--out', dest='out', required=True)
    args = ap.parse_args()
    job = json.load(open(args.inp))
    result = do_import(job) if job.get('op') == 'import' else do_export(job)
    json.dump(result, open(args.out, 'w'), indent=1)
    return 0


if __name__ == '__main__':
    sys.exit(main())
