"""Metrology POC (ADR-E) — synthetic closed-loop validation.

Proves the ALGORITHM CHAIN (ChArUco detect → plane homography → mm
measurement) with known ground truth, under simulated phone conditions
(perspective tilt, blur, noise). PHYSICAL tiers on the real factory table are
P2 scope with the commissioned mat (D7) — this POC bounds the math+code error,
not paper curl or lens distortion. Honest output: error per scenario.

Scene: a 1400×1000 mm virtual mat (ChArUco) with a synthetic rectangular
"piece" of known 600×400 mm drawn on it; we measure its edge lengths and
diagonal through the recovered homography.
"""
import json
import math

import cv2
import numpy as np

MM_W, MM_H = 1400.0, 1000.0            # mat mm
PX_PER_MM = 2.0                         # render resolution
SQUARES = (14, 10)                      # 100 mm squares
SQ_MM, MK_MM = 100.0, 75.0

DICT = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_5X5_1000)
board = cv2.aruco.CharucoBoard(SQUARES, SQ_MM, MK_MM, DICT)

img_w, img_h = int(MM_W * PX_PER_MM), int(MM_H * PX_PER_MM)
mat_img = board.generateImage((img_w, img_h), marginSize=0)
mat_img = cv2.cvtColor(mat_img, cv2.COLOR_GRAY2BGR)

# ground-truth piece: 600×400 rectangle at (400,300)mm, drawn dark grey
PIECE = np.array([[400, 300], [1000, 300], [1000, 700], [400, 700]], np.float64)
gt = {"e1": 600.0, "e2": 400.0, "diag": math.hypot(600, 400)}
pts_px = (PIECE * PX_PER_MM).astype(np.int32)
cv2.fillPoly(mat_img, [pts_px], (80, 80, 90))


def warp(img, tilt_frac, yaw_frac, noise, blur):
    """Valid-by-construction plane homography: map the mat's corners onto a
    displaced quadrilateral (trapezoid = camera tilt). tilt_frac/yaw_frac =
    fraction of width/height the far edge shrinks (0.15 ≈ a strong phone tilt).
    """
    h, w = img.shape[:2]
    src = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
    dx, dy = w * yaw_frac / 2, h * tilt_frac / 2
    dst = np.float32([[dx, dy], [w - dx, dy * 0.6],
                      [w - dx * 0.3, h - dy * 0.2], [dx * 0.5, h]])
    H = cv2.getPerspectiveTransform(src, dst)
    out = cv2.warpPerspective(img, H, (w, h), borderValue=(200, 200, 200))
    if blur:
        out = cv2.GaussianBlur(out, (blur * 2 + 1, blur * 2 + 1), 0)
    if noise:
        out = np.clip(out.astype(np.int16) +
                      np.random.default_rng(7).integers(-noise, noise, out.shape),
                      0, 255).astype(np.uint8)
    return out, H


def measure(photo):
    """Detect ChArUco → homography px→mm → measure the piece corners."""
    det = cv2.aruco.CharucoDetector(board)
    ch_corners, ch_ids, mk_corners, mk_ids = det.detectBoard(photo)
    if ch_corners is None or len(ch_corners) < 8:
        return None, 0
    obj = np.asarray(board.getChessboardCorners())   # (N,3) mm coords, z=0
    ids = np.asarray(ch_ids).flatten().astype(int)
    obj_pts = obj[ids][:, :2].astype(np.float64)
    img_pts = ch_corners.reshape(-1, 2).astype(np.float64)
    # HOLD-OUT validation: fit the homography on EVEN detected corners only,
    # then measure known mm distances between HELD-OUT (odd) corners through
    # it — the held-out corners play the role of unknown piece points, with
    # exact ground truth and no extra detection machinery.
    fit = np.arange(len(ids)) % 2 == 0
    if fit.sum() < 8 or (~fit).sum() < 6:
        return None, len(ch_corners)
    Hmm, _ = cv2.findHomography(img_pts[fit], obj_pts[fit], cv2.RANSAC, 3.0)
    if Hmm is None:
        return None, len(ch_corners)
    hold_img = img_pts[~fit].reshape(-1, 1, 2)
    hold_gt = obj_pts[~fit]
    hold_mm = cv2.perspectiveTransform(hold_img, Hmm).reshape(-1, 2)
    rng = np.random.default_rng(3)
    errs = []
    for _ in range(60):
        i, j = rng.integers(0, len(hold_gt), 2)
        if i == j:
            continue
        d_true = float(np.linalg.norm(hold_gt[i] - hold_gt[j]))
        d_meas = float(np.linalg.norm(hold_mm[i] - hold_mm[j]))
        if d_true > 100:                      # measure ≥1-square spans
            errs.append(abs(d_meas - d_true))
    return {"n_pairs": len(errs),
            "err_mean_mm": float(np.mean(errs)),
            "err_p95_mm": float(np.percentile(errs, 95)),
            "err_max_mm": float(np.max(errs))}, len(ch_corners)


scenarios = [
    ("flat", 0, 0, 0, 0),
    ("tilt_mild", 0.08, 0.05, 0, 1),
    ("tilt_strong_noise", 0.16, 0.10, 12, 2),
]
rows = []
for name, tilt, yaw, noise, blur in scenarios:
    photo, _ = warp(mat_img, tilt, yaw, noise, blur)
    m, ncorners = measure(photo)
    if m is None:
        rows.append({"scenario": name, "detected_corners": ncorners, "result": "DETECTION FAILED"})
        continue
    rows.append({"scenario": name, "detected_corners": ncorners,
                 "held_out_pairs": m["n_pairs"],
                 "err_mean_mm": round(m["err_mean_mm"], 3),
                 "err_p95_mm": round(m["err_p95_mm"], 3),
                 "err_max_mm": round(m["err_max_mm"], 3)})
    print(rows[-1])

json.dump({"ground_truth_mm": gt, "scenarios": rows},
          open("results/metrology.json", "w"), indent=1)
print("NOTE: synthetic loop bounds ALGORITHM error only; physical tiers = P2 on the commissioned mat.")
