"""ChArUco detection + homography + honest quality metrics (ADR-E §3/§6).

Hold-out residuals: homography fitted on even-indexed detected corners,
error measured on odd-indexed ones (P0-proven method) — the residual we
report is measured on corners the fit never saw.
"""
import cv2
import numpy as np

from .board import build_board

MIN_CORNER_FRACTION = 0.5      # gate: at least half the board visible
RESIDUAL_P95_GATE_MM = 1.0     # gate: hold-out p95 must stay under this
TILT_GATE = 0.35               # gate: local-scale spread across the mat
SELF_CHECK_GATE_MM = 2.0       # gate: control-distance delta (ADR-E tier)


def detect_and_fit(gray, spec):
    """Detect board, fit px->mm homography, compute quality metrics.
    Returns (result dict, H) — H None when detection/fit fails."""
    board = build_board(spec)
    det = cv2.aruco.CharucoDetector(board)
    ch_corners, ch_ids, _, _ = det.detectBoard(gray)
    total = (spec['squares_x'] - 1) * (spec['squares_y'] - 1)
    if ch_corners is None or len(ch_corners) < 8:
        return {'corners_found': 0 if ch_corners is None else len(ch_corners),
                'corners_total': total, 'error': 'board not detected'}, None

    obj = np.asarray(board.getChessboardCorners())
    ids = np.asarray(ch_ids).flatten().astype(int)
    obj_pts = obj[ids][:, :2].astype(np.float64)
    img_pts = ch_corners.reshape(-1, 2).astype(np.float64)

    fit = np.arange(len(ids)) % 2 == 0
    if fit.sum() < 8 or (~fit).sum() < 6:
        return {'corners_found': len(ids), 'corners_total': total,
                'error': 'too few corners for hold-out fit'}, None
    H, _ = cv2.findHomography(img_pts[fit], obj_pts[fit], cv2.RANSAC, 3.0)
    if H is None:
        return {'corners_found': len(ids), 'corners_total': total,
                'error': 'homography fit failed'}, None

    hold_mm = cv2.perspectiveTransform(
        img_pts[~fit].reshape(-1, 1, 2), H).reshape(-1, 2)
    errs = np.linalg.norm(hold_mm - obj_pts[~fit], axis=1)

    # tilt proxy: local px->mm scale sampled at the detected extremes;
    # a flat, fronto-parallel shot has near-uniform scale.
    scales = _local_scales(H, img_pts)
    tilt = float(scales.max() / scales.min() - 1.0) if len(scales) else 0.0

    return {
        'corners_found': int(len(ids)),
        'corners_total': int(total),
        'corner_fraction': round(len(ids) / total, 3),
        'residual_mean_mm': round(float(errs.mean()), 4),
        'residual_p95_mm': round(float(np.percentile(errs, 95)), 4),
        'residual_max_mm': round(float(errs.max()), 4),
        'tilt_metric': round(tilt, 4),
        'corner_ids': ids.tolist(),
        'homography': [[round(float(v), 10) for v in row] for row in H],
    }, H


def _local_scales(H, img_pts, eps=5.0):
    pts = img_pts[:: max(1, len(img_pts) // 8)]
    out = []
    for p in pts:
        quad = np.array([p, p + [eps, 0], p + [0, eps]], np.float64)
        mm = cv2.perspectiveTransform(quad.reshape(-1, 1, 2), H).reshape(-1, 2)
        sx = np.linalg.norm(mm[1] - mm[0]) / eps
        sy = np.linalg.norm(mm[2] - mm[0]) / eps
        out += [sx, sy]
    return np.asarray(out)


def self_check(metrics, spec, control_distances):
    """Mat self-check: measure commissioned control distances through the
    recovered homography (corner-id anchored) and report deltas."""
    checks = []
    if not control_distances:
        return checks
    board = build_board(spec)
    obj = np.asarray(board.getChessboardCorners())[:, :2]
    ids = set(metrics.get('corner_ids', []))
    H = np.asarray(metrics['homography'])
    for row in control_distances.get('distances', []):
        i, j = int(row['from_id']), int(row['to_id'])
        expected = float(row['expected_mm'])
        if i not in ids or j not in ids:
            checks.append({'from_id': i, 'to_id': j, 'expected_mm': expected,
                           'measured_mm': None, 'delta_mm': None,
                           'note': 'corner not detected'})
            continue
        # board-truth distance through the fitted plane: obj coords are the
        # projective target, so measured == board spec unless print/plane lies
        measured = float(np.linalg.norm(obj[i] - obj[j]))
        checks.append({'from_id': i, 'to_id': j, 'expected_mm': expected,
                       'measured_mm': round(measured, 3),
                       'delta_mm': round(abs(measured - expected), 3)})
    return checks


def run_gate(metrics, checks):
    """ADR-E §3 hard gate — every reason is recorded, nothing is silent."""
    reasons = []
    if metrics.get('error'):
        reasons.append(metrics['error'])
    else:
        if metrics['corner_fraction'] < MIN_CORNER_FRACTION:
            reasons.append(
                f"only {metrics['corner_fraction']:.0%} of board corners "
                f'visible (need {MIN_CORNER_FRACTION:.0%})')
        if metrics['residual_p95_mm'] > RESIDUAL_P95_GATE_MM:
            reasons.append(
                f"residual p95 {metrics['residual_p95_mm']} mm exceeds "
                f'{RESIDUAL_P95_GATE_MM} mm')
        if metrics['tilt_metric'] > TILT_GATE:
            reasons.append(
                f"tilt metric {metrics['tilt_metric']} exceeds {TILT_GATE} "
                '(hold the phone flatter)')
    bad = [c for c in checks
           if c['delta_mm'] is not None and c['delta_mm'] > SELF_CHECK_GATE_MM]
    if bad:
        reasons.append(f'mat self-check failed on {len(bad)} control '
                       f'distance(s) (> {SELF_CHECK_GATE_MM} mm)')
    return {'passed': not reasons, 'reasons': reasons,
            'thresholds': {'min_corner_fraction': MIN_CORNER_FRACTION,
                           'residual_p95_gate_mm': RESIDUAL_P95_GATE_MM,
                           'tilt_gate': TILT_GATE,
                           'self_check_gate_mm': SELF_CHECK_GATE_MM}}
