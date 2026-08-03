"""Canonical geometry payload builders/validators (ADR-C).

Integer micrometers, piece-local origin at bbox min, x-right/y-up, outer
CCW, holes CW, polyline-at-tolerance. schema_version mandatory.
"""
GEOMETRY_SCHEMA_VERSION = 1
MAX_VERTICES = 4000
MIN_VERTICES = 3


def signed_area(pts):
    s = 0
    for i in range(len(pts)):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % len(pts)]
        s += x1 * y2 - x2 * y1
    return s / 2.0


def ensure_winding(pts, ccw=True):
    if (signed_area(pts) > 0) != ccw:
        return list(reversed(pts))
    return list(pts)


def mm_polygon_to_canonical(outer_mm, holes_mm=None, chord_tolerance_um=500,
                            features=None):
    """mm float polygon (y-up already) -> canonical payload. Origin shifts
    to bbox min; everything quantized to integer um."""
    holes_mm = holes_mm or []
    all_pts = list(outer_mm) + [p for h in holes_mm for p in h]
    minx = min(p[0] for p in all_pts)
    miny = min(p[1] for p in all_pts)

    def to_um(poly):
        return [[int(round((x - minx) * 1000)), int(round((y - miny) * 1000))]
                for x, y in poly]

    outer = ensure_winding(to_um(outer_mm), ccw=True)
    holes = [ensure_winding(to_um(h), ccw=False) for h in holes_mm]
    return {
        'schema_version': GEOMETRY_SCHEMA_VERSION,
        'units': 'um',
        'origin': 'bbox_min',
        'axes': 'x_right_y_up',
        'chord_tolerance_um': int(chord_tolerance_um),
        'outer': outer,
        'holes': holes,
        'features': features or {
            'grain': None, 'notches': [], 'drills': [],
            'internal_lines': [], 'fold_edge': None,
            'seam_allowance': 'as_cut',
        },
        'grade_rule': None,
    }


def validate_canonical(payload):
    """Return list of problems (empty = valid). Shared contract with the
    Django-side validator (units.py) — keep the rules in lockstep."""
    problems = []
    if payload.get('schema_version') != GEOMETRY_SCHEMA_VERSION:
        problems.append('schema_version missing or unsupported')
        return problems
    outer = payload.get('outer') or []
    if not (MIN_VERTICES <= len(outer) <= MAX_VERTICES):
        problems.append(f'outer vertex count {len(outer)} outside '
                        f'{MIN_VERTICES}..{MAX_VERTICES}')
        return problems
    for ring, name, ccw in ([(outer, 'outer', True)]
                            + [(h, f'hole{i}', False)
                               for i, h in enumerate(payload.get('holes') or [])]):
        for pt in ring:
            if (not isinstance(pt, (list, tuple)) or len(pt) != 2
                    or not all(isinstance(v, int) for v in pt)):
                problems.append(f'{name}: non-integer vertex {pt!r}')
                return problems
        if len(ring) >= MIN_VERTICES and (signed_area(ring) > 0) != ccw:
            problems.append(f'{name}: wrong winding')
        if ring and ring[0] == ring[-1]:
            problems.append(f'{name}: stored closed (first==last); store open')
    xs = [p[0] for p in outer]
    ys = [p[1] for p in outer]
    if min(xs) != 0 or min(ys) != 0:
        problems.append('origin not at bbox min')
    # adr-c.3 (M4.5): optional features.fold_edge — typed when present.
    # Kept in LOCKSTEP with the Django-side twin (units.py).
    fe = (payload.get('features') or {}).get('fold_edge')
    if fe not in (None, {}):
        ok = (isinstance(fe, dict)
              and isinstance(fe.get('p1_um'), (list, tuple))
              and isinstance(fe.get('p2_um'), (list, tuple))
              and len(fe['p1_um']) == 2 and len(fe['p2_um']) == 2
              and all(isinstance(v, int) and not isinstance(v, bool)
                      for v in list(fe['p1_um']) + list(fe['p2_um'])))
        if not ok:
            problems.append('fold_edge needs integer p1_um/p2_um pairs')
        elif fe['p1_um'][0] != fe['p2_um'][0]:
            problems.append('fold_edge must be vertical')
    # adr-c.2 (M2): optional features.notches — typed when present, absent
    # = valid. Kept in LOCKSTEP with the Django-side twin (units.py).
    notches = (payload.get('features') or {}).get('notches')
    if notches not in (None, []):
        if not isinstance(notches, list):
            problems.append('features.notches must be a list')
        else:
            for i, n in enumerate(notches):
                if (not isinstance(n, dict)
                        or not isinstance(n.get('x_um'), int)
                        or isinstance(n.get('x_um'), bool)
                        or not isinstance(n.get('y_um'), int)
                        or isinstance(n.get('y_um'), bool)):
                    problems.append(f'notch {i}: needs integer x_um/y_um')
                    break
    return problems


def bbox_um(payload):
    xs = [p[0] for p in payload['outer']]
    ys = [p[1] for p in payload['outer']]
    return max(xs), max(ys)
