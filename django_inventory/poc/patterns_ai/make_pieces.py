"""P0 harness piece generator — realistic, mm-true garment polygons.

HONESTY NOTE (P0 report §inputs): these are hand-constructed realistic
geometries based on standard M-size knitwear dimensions, NOT captures
(capture = P2). All engines consume the SAME JSON, so relative bake-off
numbers are valid. Units: mm, y-up, CCW outer boundary (ADR-C conventions).
Ratio grading approximated by uniform scale (harness only — real grading is
NOT uniform; ADR-C grade_rule handles that later).
"""
import json
import math
import os


def bezier(p0, p1, p2, n=8):
    """Quadratic bezier sampled to n points (excludes p0, includes p2)."""
    pts = []
    for i in range(1, n + 1):
        t = i / n
        x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t ** 2 * p2[0]
        y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t ** 2 * p2[1]
        pts.append((round(x, 1), round(y, 1)))
    return pts


def tee_front():
    """M tee front: chest 530, length 680, shoulder 460, neck drop 90."""
    w, L, sh, nd, ah = 530, 680, 460, 90, 240   # armhole depth 240
    p = [(0, 0), (w, 0)]                                   # hem
    p += [(w, L - ah)]                                     # side seam up
    p += bezier((w, L - ah), (w - 45, L - 60), ((w + sh) / 2, L - 25))  # armhole
    p += [((w + sh) / 2, L)]                               # shoulder point → up
    p += bezier(((w + sh) / 2, L), (w / 2 + 60, L - 10), (w / 2 + 80, L - 20))
    p += bezier((w / 2 + 80, L - 20), (w / 2, L - nd - 25), (w / 2 - 80, L - 20))  # neck
    p += bezier((w / 2 - 80, L - 20), (w / 2 - 60, L - 10), ((w - sh) / 2, L))
    p += [((w - sh) / 2, L)]
    p += bezier(((w - sh) / 2, L - 25), (45, L - 60), (0, L - ah))      # armhole L
    return p


def tee_back():
    f = tee_front()
    # back = front with shallow neck (raise the neck dip points)
    out = []
    for x, y in f:
        if 600 < y < 680 and 130 < x < 400:   # neck region points
            y = min(680 - 25, y + 55)
        out.append((x, y))
    return out


def sleeve():
    """Short sleeve: bicep 380, cap height 140, underarm length 200."""
    b, cap, ln = 380, 140, 200
    p = [(0, 0), (b, 0), (b - 25, ln)]                     # hem + underseam
    p += bezier((b - 25, ln), (b * 0.75, ln + cap * 1.15), (b / 2, ln + cap))
    p += bezier((b / 2, ln + cap), (b * 0.25, ln + cap * 1.15), (25, ln))
    return p


def patti_front():
    """Brief front panel 280×260 with leg curves."""
    p = [(60, 0), (220, 0)]                                # gusset seam
    p += bezier((220, 0), (275, 90), (280, 175))           # leg curve R
    p += [(280, 260), (0, 260)]                            # waist
    p += bezier((0, 175), (5, 90), (60, 0))
    return [(x, y) for x, y in p]


def patti_back():
    p = [(80, 0), (250, 0)]
    p += bezier((250, 0), (325, 100), (330, 190))
    p += [(330, 280), (0, 280)]
    p += bezier((0, 190), (5, 100), (80, 0))
    return p


def gusset():
    return [(0, 0), (160, 0), (150, 120), (10, 120)]


def lower_leg():
    """Track-pant leg panel >1 m: 1080 long, tapered 320→220."""
    p = [(0, 0), (220, 0), (320, 1080 - 260)]
    p += bezier((320, 820), (300, 1000), (250, 1080))
    p += [(0, 1080)]
    return p


def half_front_onfold():
    """Tee front HALF for cut-on-fold: fold edge = x=0."""
    full = tee_front()
    cx = 265
    # keep right half, project fold edge onto x=0
    right = [(x - cx, y) for x, y in full if x >= cx - 1]
    ys = [y for _, y in right]
    return [(0, min(ys))] + right + [(0, max(ys))]


def scaled(poly, f):
    return [(round(x * f, 1), round(y * f, 1)) for x, y in poly]


def piece(pid, poly, qty, allow_180=True, allow_mirror=False, on_fold=False):
    xs = [p[0] for p in poly]; ys = [p[1] for p in poly]
    poly = [(x - min(xs), y - min(ys)) for x, y in poly]
    return {"id": pid, "qty": qty, "allow_180": allow_180,
            "allow_mirror": allow_mirror, "on_fold": on_fold,
            "polygon": poly}


RATIO = [("S", 0.95, 2), ("M", 1.00, 2), ("L", 1.05, 1)]   # S2:M2:L1 per repeat

sets = {}

tee = []
for sz, f, q in RATIO:
    tee.append(piece(f"front-{sz}", scaled(tee_front(), f), q))
    tee.append(piece(f"back-{sz}", scaled(tee_back(), f), q))
    tee.append(piece(f"sleeve-{sz}", scaled(sleeve(), f), q * 2, allow_mirror=True))
sets["tee"] = {"name": "T-SHIRT body M-ratio S2M2L1", "width_mm": 1100, "pieces": tee}

patti = []
for sz, f, q in RATIO:
    patti.append(piece(f"pfront-{sz}", scaled(patti_front(), f), q))
    patti.append(piece(f"pback-{sz}", scaled(patti_back(), f), q))
    patti.append(piece(f"gusset-{sz}", scaled(gusset(), f), q))
sets["patti"] = {"name": "3-PATTI brief S2M2L1 (tube-flat 940)", "width_mm": 940, "pieces": patti}

sets["stress"] = {"name": "stress: >1m leg + curved sleeve + on-fold half-front",
                  "width_mm": 940, "pieces": [
                      piece("leg-L", lower_leg(), 2, allow_mirror=True),
                      piece("leg-R", lower_leg(), 2, allow_mirror=True),
                      piece("sleeve", sleeve(), 2, allow_mirror=True),
                      piece("halffront-fold", half_front_onfold(), 1, on_fold=True),
                  ]}

os.makedirs("pieces", exist_ok=True)
for k, v in sets.items():
    # polygon areas (shoelace) for utilization math
    for pc in v["pieces"]:
        poly = pc["polygon"]
        a = 0.0
        for i in range(len(poly)):
            x1, y1 = poly[i]; x2, y2 = poly[(i + 1) % len(poly)]
            a += x1 * y2 - x2 * y1
        pc["area_mm2"] = abs(a) / 2
        if pc["on_fold"]:
            pc["area_mm2"] *= 2   # fold doubles the cut area credit
    with open(f"pieces/{k}.json", "w") as fh:
        json.dump(v, fh, indent=1)
    total = sum(p["area_mm2"] * p["qty"] for p in v["pieces"])
    print(f"{k}: {len(v['pieces'])} piece types, total area/repeat = {total/1e6:.3f} m^2")
