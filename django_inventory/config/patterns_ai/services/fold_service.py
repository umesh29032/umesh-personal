"""fold_service — M4.5 fold geometry helpers (READ-ONLY + validation;
writes stay in pattern_geometry_service).

Manufacturing model (plan §0): the stored geometry is the physical
HALF-PATTERN; `features.fold_edge` marks the straight VERTICAL outline
segment that sits on the fabric's folded edge. The OPENED piece is
DERIVED here — never stored (standing law).

v1 convention (validated, documented): the fold edge is an
AXIS-ALIGNED VERTICAL segment (x1 == x2) — the marker-table reality:
the fabric crease runs lengthwise, so the pattern's fold line is
digitized vertical. Deterministic only (rule ⑩): no ML anywhere.
"""

FOLD_EDGE_TOL_UM = 500          # symmetry match tolerance (= chord tol)


def validate_fold_edge(payload, fold_edge):
    """Return list of problems (empty = valid) for a fold_edge dict
    against a canonical payload. Rules: typed ints · both points are
    outline VERTICES · adjacent (one outline segment) · vertical."""
    problems = []
    if not isinstance(fold_edge, dict):
        return ['fold_edge must be an object']
    try:
        p1 = [int(fold_edge['p1_um'][0]), int(fold_edge['p1_um'][1])]
        p2 = [int(fold_edge['p2_um'][0]), int(fold_edge['p2_um'][1])]
    except (KeyError, TypeError, ValueError, IndexError):
        return ['fold_edge needs integer p1_um/p2_um pairs']
    outer = payload.get('outer') or []
    if p1 not in outer or p2 not in outer:
        problems.append('fold_edge points must be outline vertices')
        return problems
    i1, i2 = outer.index(p1), outer.index(p2)
    n = len(outer)
    if (i1 + 1) % n != i2 and (i2 + 1) % n != i1:
        problems.append('fold_edge must be ONE outline segment '
                        '(adjacent vertices)')
    if p1[0] != p2[0]:
        problems.append('fold_edge must be vertical (the fabric crease '
                        'runs lengthwise) — rotate the pattern in the '
                        'editor first')
    if p1[1] == p2[1]:
        problems.append('fold_edge has zero length')
    return problems


def get_fold_edge(payload):
    """The typed fold edge or None (payload may predate adr-c.3)."""
    fe = (payload.get('features') or {}).get('fold_edge')
    return fe if isinstance(fe, dict) and fe else None


def unfold_outline(payload):
    """DERIVED opened outline (µm, canonical winding, origin bbox-min):
    the half + its mirror about the vertical fold line, fold-line
    vertices not duplicated. None when no fold edge is marked."""
    fe = get_fold_edge(payload)
    if fe is None:
        return None
    x_fold = int(fe['p1_um'][0])
    outer = payload['outer']
    mirrored = [[2 * x_fold - x, y] for x, y in outer]
    # walk the original, then the mirror reversed, skipping the two
    # fold-line vertices in the mirrored pass (they coincide)
    fold_pts = {tuple(fe['p1_um']), tuple(fe['p2_um'])}
    opened = list(outer)
    for pt, src in zip(reversed(mirrored), reversed(outer)):
        if tuple(src) in fold_pts:
            continue
        opened.append(pt)
    # re-anchor at bbox-min + fix winding (mirror flips orientation of
    # the appended half but the union stays a simple polygon CCW-able)
    minx = min(p[0] for p in opened)
    miny = min(p[1] for p in opened)
    opened = [[x - minx, y - miny] for x, y in opened]
    s = 0
    for i in range(len(opened)):
        x1, y1 = opened[i]
        x2, y2 = opened[(i + 1) % len(opened)]
        s += x1 * y2 - x2 * y1
    if s < 0:
        opened = list(reversed(opened))
    return opened


def detect_fold_edge(payload):
    """DETERMINISTIC proposal (R2-C): find the vertical straight outline
    segment about which the outline is most nearly symmetric. Returns
    {'p1_um', 'p2_um', 'match_pct'} or None. Proposes only — the expert
    owns the answer."""
    outer = payload.get('outer') or []
    n = len(outer)
    if n < 3:
        return None
    best = None
    for i in range(n):
        p1, p2 = outer[i], outer[(i + 1) % n]
        if p1[0] != p2[0] or p1[1] == p2[1]:
            continue                      # vertical candidates only
        x_fold = p1[0]
        # the outline must lie entirely on ONE side of the candidate
        xs = [p[0] for p in outer]
        if not (all(x >= x_fold for x in xs) or
                all(x <= x_fold for x in xs)):
            continue
        # symmetry score: every vertex's mirror must be near the outline
        mirrored = [[2 * x_fold - x, y] for x, y in outer]
        hits = sum(1 for m in mirrored
                   if _near_outline(m, outer, FOLD_EDGE_TOL_UM))
        pct = 100.0 * hits / n
        # tie-breaks: better match → LEFTMOST edge (the marker-table
        # convention: fold lines are digitized on the left) → longest
        if (best is None or pct > best['match_pct']
                or (pct == best['match_pct']
                    and x_fold < int(best['p1_um'][0]))
                or (pct == best['match_pct']
                    and x_fold == int(best['p1_um'][0])
                    and abs(p2[1] - p1[1]) > abs(int(best['p2_um'][1])
                                                 - int(best['p1_um'][1])))):
            best = {'p1_um': list(p1), 'p2_um': list(p2),
                    'match_pct': round(pct, 1)}
    return best


def is_fold_capable_shape(payload, min_match_pct=90.0):
    """Advisory (R2-C second proposal): does the outline look like a
    half-pattern (strong symmetry about a straight vertical edge)?"""
    best = detect_fold_edge(payload)
    return best if best and best['match_pct'] >= min_match_pct else None


def _near_outline(pt, outer, tol_um):
    """Point within tol of any outline vertex or segment (cheap check —
    vertex distance first, then segment projection)."""
    tol2 = tol_um * tol_um
    n = len(outer)
    for i in range(n):
        a, b = outer[i], outer[(i + 1) % n]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L2 = dx * dx + dy * dy
        t = 0.0 if not L2 else max(0.0, min(1.0, (
            (pt[0] - a[0]) * dx + (pt[1] - a[1]) * dy) / L2))
        X = a[0] + t * dx - pt[0]
        Y = a[1] + t * dy - pt[1]
        if X * X + Y * Y <= tol2:
            return True
    return False
