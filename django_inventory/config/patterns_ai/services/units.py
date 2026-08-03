"""ONE quantization home for patterns_ai (Blueprint I-4).

Why this file exists: manufacturing's paisa rule survived as three identical
copies only by luck (engineering sweep consolidated q_paisa). Geometry and
yield math never take that risk — every rounding/conversion in this app goes
through these functions. Facts at rest are INTEGER mm (geometry later: µm);
display/derived values are Decimal, quantized HERE and nowhere else.
"""
from decimal import Decimal, ROUND_HALF_UP

MM_PER_M = Decimal(1000)


def to_int_mm(value) -> int:
    """Canonical fact representation: whole millimetres (HALF_UP)."""
    return int(Decimal(str(value)).quantize(Decimal('1'), rounding=ROUND_HALF_UP))


def mm_to_m(mm) -> Decimal:
    """Display metres, 2dp (HALF_UP)."""
    return (Decimal(int(mm)) / MM_PER_M).quantize(Decimal('0.01'), ROUND_HALF_UP)


def q2(value) -> Decimal:
    """Generic 2dp quantize (percentages, metres-per-garment displays)."""
    return Decimal(str(value)).quantize(Decimal('0.01'), ROUND_HALF_UP)


def width_band(usable_width_mm: int) -> int:
    """Stored resolution-key bucket (V2 C10): floor(mm/10). Stamped by
    marker_service at creation; recompute anywhere else = a bug."""
    return int(usable_width_mm) // 10


def m_to_mm(value_m) -> int:
    """UI speaks metres; facts are integer mm (HALF_UP). One conversion home."""
    return int((Decimal(str(value_m)) * MM_PER_M)
               .quantize(Decimal('1'), rounding=ROUND_HALF_UP))


# ---- P2 geometry era (ADR-C): integer micrometres at rest ----------------

GEOMETRY_SCHEMA_VERSION = 1     # kept in LOCKSTEP with compute runtime
MAX_VERTICES = 4000
MIN_VERTICES = 3


def mm_to_um(value_mm) -> int:
    """Geometry facts are integer µm (ADR-C §2, HALF_UP)."""
    return int((Decimal(str(value_mm)) * 1000)
               .quantize(Decimal('1'), rounding=ROUND_HALF_UP))


def um_to_mm(um) -> Decimal:
    """Display mm, 1dp — geometry is never shown finer than 0.1 mm."""
    return (Decimal(int(um)) / 1000).quantize(Decimal('0.1'), ROUND_HALF_UP)


def _signed_area(pts):
    s = 0
    for i in range(len(pts)):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % len(pts)]
        s += x1 * y2 - x2 * y1
    return s / 2.0


def validate_canonical_geometry(payload):
    """Django-side twin of the compute runtime's validator (trust but
    verify at the boundary). Returns list of problems; empty = valid."""
    problems = []
    if not isinstance(payload, dict) \
            or payload.get('schema_version') != GEOMETRY_SCHEMA_VERSION:
        return ['schema_version missing or unsupported']
    outer = payload.get('outer') or []
    if not (MIN_VERTICES <= len(outer) <= MAX_VERTICES):
        return [f'outer vertex count {len(outer)} outside '
                f'{MIN_VERTICES}..{MAX_VERTICES}']
    for ring, name, ccw in ([(outer, 'outer', True)]
                            + [(h, f'hole{i}', False)
                               for i, h in enumerate(payload.get('holes') or [])]):
        for pt in ring:
            if (not isinstance(pt, (list, tuple)) or len(pt) != 2
                    or not all(isinstance(v, int) and not isinstance(v, bool)
                               for v in pt)):
                return [f'{name}: non-integer vertex {pt!r}']
        if len(ring) >= MIN_VERTICES and (_signed_area(ring) > 0) != ccw:
            problems.append(f'{name}: wrong winding')
        if ring and ring[0] == ring[-1]:
            problems.append(f'{name}: stored closed (first==last); store open')
    xs = [p[0] for p in outer]
    ys = [p[1] for p in outer]
    if min(xs) != 0 or min(ys) != 0:
        problems.append('origin not at bbox min')
    # adr-c.3 (M4.5): optional features.fold_edge — typed when present
    # (straight VERTICAL outline segment; full rules in fold_service,
    # shape-checked here in LOCKSTEP with the compute twin).
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
    # = valid (every adr-c.1 payload remains a valid adr-c.2 payload).
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
                    problems.append(
                        f'notch {i}: needs integer x_um/y_um')
                    break
    return problems
