"""BLF baseline nester — the deterministic always-works floor (ADR-A).

Grid-rasterized bottom-left-fill: pieces rasterized at GRID mm, placed by
scanning candidate rows bottom-up, leftmost x that fits (piece mask vs occupied
mask). Rotations {0,180} when allowed, mirror for pair pieces, on-fold pieces
pinned to y=0 (fold line at lay edge). Deterministic: fixed sort (area desc,
id asc), no randomness. Reports geometric utilization = piece area / (width ×
used length) — end allowances excluded ON PURPOSE (engine-comparable number;
consumption math adds allowances separately, per blueprint honesty rules).
"""
import json
import sys
import time

import numpy as np
from shapely.geometry import Polygon
from shapely import affinity

GRID = 2.0            # mm per cell
SPACING = 2.0         # inter-piece spacing mm (half kerf each side)


def masks_for(poly, allow_180, allow_mirror):
    """Rasterize orientation variants → list of (mask, w_mm, h_mm, label)."""
    variants = [("r0", poly)]
    if allow_180:
        variants.append(("r180", affinity.rotate(poly, 180, origin="centroid")))
    if allow_mirror:
        m = affinity.scale(poly, xfact=-1, origin="centroid")
        variants.append(("m0", m))
        if allow_180:
            variants.append(("m180", affinity.rotate(m, 180, origin="centroid")))
    out = []
    for label, p in variants:
        p = affinity.translate(p, -p.bounds[0], -p.bounds[1])
        b = p.buffer(SPACING / 2, join_style=2)
        w, h = b.bounds[2], b.bounds[3]
        gw, gh = int(np.ceil(w / GRID)) + 1, int(np.ceil(h / GRID)) + 1
        mask = np.zeros((gh, gw), dtype=bool)
        # rasterize: cell center containment (fast enough at POC scale)
        xs = (np.arange(gw) + 0.5) * GRID + b.bounds[0]
        ys = (np.arange(gh) + 0.5) * GRID + b.bounds[1]
        from shapely.prepared import prep
        pb = prep(b)
        from shapely.geometry import Point
        for j, y in enumerate(ys):
            row = [pb.contains(Point(x, y)) for x in xs]
            mask[j] = row
        out.append((mask, w, h, label, p))
    return out


def place(width_mm, items):
    """items: list of dicts w/ masks. Returns placements + used length."""
    gw = int(width_mm // GRID)
    occ = np.zeros((1, gw), dtype=bool)

    def grow(rows):
        nonlocal occ
        if rows > occ.shape[0]:
            occ = np.vstack([occ, np.zeros((rows - occ.shape[0], gw), dtype=bool)])

    placements = []
    for it in items:
        best = None
        for mask, w, h, label, poly in it["variants"]:
            mh, mw = mask.shape
            if mw > gw:
                continue
            if it["on_fold"]:
                y_range = [0]                      # fold edge pinned to lay edge
            else:
                y_range = range(0, max(occ.shape[0] + mh + 2, 4))
            found = None
            for y in y_range:
                grow(y + mh)
                sub = occ[y:y + mh]
                # slide x: first fit
                free = ~sub
                for x in range(0, gw - mw + 1):
                    if not (mask & sub[:, x:x + mw]).any():
                        found = (y, x)
                        break
                if found:
                    break
            if found:
                y, x = found
                score = (y + mh, x)                # lowest top edge, then left
                if best is None or score < best[0]:
                    best = (score, y, x, mask, label)
        if best is None:
            return None, None                      # width too small
        _, y, x, mask, label = best
        grow(y + mask.shape[0])
        occ[y:y + mask.shape[0], x:x + mask.shape[1]] |= mask
        placements.append({"id": it["id"], "x_mm": x * GRID, "y_mm": y * GRID,
                           "variant": label})
    used_rows = np.where(occ.any(axis=1))[0]
    used_len = (used_rows.max() + 1) * GRID if len(used_rows) else 0
    return placements, used_len


def run(path):
    spec = json.load(open(path))
    t0 = time.time()
    items = []
    for pc in spec["pieces"]:
        poly = Polygon(pc["polygon"])
        variants = masks_for(poly, pc["allow_180"], pc["allow_mirror"])
        if pc["on_fold"]:
            # fold: nest the half piece against y=0; area credit already doubled
            pass
        for _ in range(pc["qty"]):
            items.append({"id": pc["id"], "variants": variants,
                          "on_fold": pc["on_fold"], "area": pc["area_mm2"]})
    items.sort(key=lambda i: (-i["area"], i["id"]))
    placements, used_len = place(spec["width_mm"], items)
    dt = time.time() - t0
    if placements is None:
        return {"set": spec["name"], "engine": "BLF-grid", "error": "does not fit width"}
    area = sum(i["area"] for i in items)
    util = area / (spec["width_mm"] * used_len)
    return {"set": spec["name"], "engine": "BLF-grid", "grid_mm": GRID,
            "spacing_mm": SPACING, "pieces_placed": len(placements),
            "marker_length_mm": round(used_len, 1),
            "utilization_pct": round(util * 100, 2),
            "wall_clock_s": round(dt, 2), "placements": placements}


if __name__ == "__main__":
    import os
    os.makedirs("results", exist_ok=True)
    out = []
    for s in sys.argv[1:] or ["pieces/tee.json", "pieces/patti.json", "pieces/stress.json"]:
        r = run(s)
        out.append(r)
        print({k: v for k, v in r.items() if k != "placements"})
    json.dump(out, open("results/blf.json", "w"), indent=1)
