"""svg_import — M2 SVG evidence adapter (UI freeze §7: SVG → convert →
verify → proposal). Pure python, honest scope: straight-segment shapes
only (<polygon>/<polyline>/<path> with M/L/H/V/Z); curve commands refuse
with the fix named ("export as DXF"). SVG user units are read as mm —
the same convention our own true-scale exports write — so a round-trip
through our SVG is exact.

Returns (canonical_payload, None) or (None, refusal_reason). The caller
re-validates against the canonical twins; nothing here writes.
"""
import re
import xml.etree.ElementTree as ET

_CURVE_CMDS = set('CcSsQqTtAa')
_NUM = re.compile(r'[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?')


def _path_points(d):
    """Flatten an M/L/H/V/Z path into absolute [x, y] mm points.
    Returns (points, refusal)."""
    tokens = re.findall(r'[A-Za-z]|' + _NUM.pattern, d or '')
    pts, cur, cmd = [], [0.0, 0.0], None
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if t.isalpha():
            if t in _CURVE_CMDS:
                return None, ('curved path commands are not supported yet '
                              '— export the piece as DXF instead.')
            if t in 'Zz':
                i += 1
                continue
            cmd = t
            i += 1
            continue
        if cmd is None:
            return None, 'path data does not start with a command.'
        try:
            if cmd in 'Hh':
                x = float(t); i += 1
                cur = [x if cmd == 'H' else cur[0] + x, cur[1]]
            elif cmd in 'Vv':
                y = float(t); i += 1
                cur = [cur[0], y if cmd == 'V' else cur[1] + y]
            else:                                  # M/m/L/l pairs
                x, y = float(t), float(tokens[i + 1]); i += 2
                cur = ([x, y] if cmd in 'ML'
                       else [cur[0] + x, cur[1] + y])
                # subsequent implicit pairs after M behave as lineto
                if cmd == 'M':
                    cmd = 'L'
                elif cmd == 'm':
                    cmd = 'l'
        except (ValueError, IndexError):
            return None, 'malformed path numbers.'
        pts.append(list(cur))
    return pts, None


def _points_attr(raw):
    nums = [float(n) for n in _NUM.findall(raw or '')]
    return [[nums[i], nums[i + 1]] for i in range(0, len(nums) - 1, 2)]


def svg_to_canonical(raw_bytes, chord_tolerance_um=500):
    """First (and only) shape in the file becomes the outer ring."""
    try:
        root = ET.fromstring(raw_bytes)
    except ET.ParseError as exc:
        return None, f'not a readable SVG: {exc}'
    shapes = []
    for el in root.iter():
        tag = el.tag.rsplit('}', 1)[-1]
        if tag in ('polygon', 'polyline'):
            shapes.append(('points', el.get('points')))
        elif tag == 'path':
            shapes.append(('d', el.get('d')))
    if not shapes:
        return None, 'no polygon/polyline/path outline found in the SVG.'
    if len(shapes) > 1:
        return None, (f'SVG contains {len(shapes)} shapes — one piece '
                      'per file (split the file).')
    kind, data = shapes[0]
    if kind == 'points':
        pts = _points_attr(data)
    else:
        pts, refusal = _path_points(data)
        if refusal:
            return None, refusal
    if pts and pts[0] == pts[-1]:
        pts = pts[:-1]                       # store open (canonical rule)
    if len(pts) < 3:
        return None, 'outline needs at least 3 vertices.'
    # SVG y grows DOWN; canonical is y-up — flip, then anchor bbox-min at 0
    maxy = max(p[1] for p in pts)
    um = [[int(round(x * 1000)), int(round((maxy - y) * 1000))]
          for x, y in pts]
    minx = min(p[0] for p in um); miny = min(p[1] for p in um)
    outer = [[x - minx, y - miny] for x, y in um]
    s = 0
    for i in range(len(outer)):
        x1, y1 = outer[i]
        x2, y2 = outer[(i + 1) % len(outer)]
        s += x1 * y2 - x2 * y1
    if s < 0:
        outer = list(reversed(outer))
    return {'schema_version': 1, 'units': 'um', 'origin': 'bbox_min',
            'axes': 'x_right_y_up',
            'chord_tolerance_um': int(chord_tolerance_um),
            'outer': outer, 'holes': [],
            'features': {'grain': None, 'notches': []},
            'grade_rule': None}, None
