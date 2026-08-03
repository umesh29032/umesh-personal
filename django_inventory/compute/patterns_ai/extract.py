#!/usr/bin/env python
"""extract.py — photo + board spec -> canonical piece geometry proposal.

Protocol (ADR-F files/argv): extract.py --in job.json --out result.json
job: {"image_path", "board_spec", "control_distances"?, "params"?:
      {"backend": "classical", "chord_tolerance_um": 500, "px_per_mm": 2.0}}
result: {"ok", "gate", "metrics", "checks", "geometry"?, "confidence"?,
         "provenance"}   — gate failure => ok true, geometry absent,
         gate.passed false with recorded reasons (refusal is a fact).
"""
import argparse
import json
import sys

import cv2
import numpy as np

from runtime import PIPELINE_VERSION
from runtime.board import board_size_mm
from runtime.canonical import mm_polygon_to_canonical, validate_canonical
from runtime.detect import detect_and_fit, run_gate, self_check
from runtime.segment import available_backends, segment

BORDER_KEEPOUT_MM = 20         # contour touching the mat edge = piece exits cage
MIN_PIECE_AREA_MM2 = 2500      # 5x5 cm floor: below this = nothing on the mat


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--in', dest='inp', required=True)
    ap.add_argument('--out', dest='out', required=True)
    args = ap.parse_args()
    job = json.load(open(args.inp))
    result = run(job)
    json.dump(result, open(args.out, 'w'), indent=1)
    return 0


def run(job):
    spec = job['board_spec']
    params = job.get('params') or {}
    backend = params.get('backend', 'classical')
    tol_um = int(params.get('chord_tolerance_um', 500))
    px_per_mm = float(params.get('px_per_mm', 2.0))

    img = cv2.imread(job['image_path'], cv2.IMREAD_GRAYSCALE)
    if img is None:
        return {'ok': False, 'error': f"unreadable image {job['image_path']}"}

    metrics, H = detect_and_fit(img, spec)
    checks = self_check(metrics, spec, job.get('control_distances')) if H is not None else []
    gate = run_gate(metrics, checks)
    prov = {'pipeline_version': PIPELINE_VERSION, 'backend': backend,
            'params': {'chord_tolerance_um': tol_um, 'px_per_mm': px_per_mm},
            'available_backends': available_backends()}
    base = {'ok': True, 'gate': gate, 'metrics': metrics, 'checks': checks,
            'provenance': prov}
    if not gate['passed']:
        return base

    # rectify photo onto the mm grid (mat plane), then segment the piece
    mat_w, mat_h = board_size_mm(spec)
    size = (int(mat_w * px_per_mm), int(mat_h * px_per_mm))
    S = np.diag([px_per_mm, px_per_mm, 1.0])
    rect = cv2.warpPerspective(img, S @ np.asarray(H), size,
                               borderValue=255)
    try:
        mask, stability = segment(rect, backend)
    except (ValueError, NotImplementedError) as exc:
        base['gate'] = {'passed': False, 'reasons': [str(exc)],
                        'thresholds': gate['thresholds']}
        return base

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL,
                                   cv2.CHAIN_APPROX_SIMPLE)
    contours = [c for c in contours
                if cv2.contourArea(c) / px_per_mm ** 2 >= MIN_PIECE_AREA_MM2]
    if not contours:
        base['gate'] = {'passed': False,
                        'reasons': ['no piece found on the mat (segmentation '
                                    'produced no plausible region)'],
                        'thresholds': gate['thresholds']}
        return base
    contour = max(contours, key=cv2.contourArea)

    xs = contour[:, 0, 0] / px_per_mm
    ys = contour[:, 0, 1] / px_per_mm
    keep = BORDER_KEEPOUT_MM
    if (xs.min() < keep or ys.min() < keep
            or xs.max() > mat_w - keep or ys.max() > mat_h - keep):
        base['gate'] = {'passed': False,
                        'reasons': ['piece touches the mat border keep-out '
                                    f'({keep} mm) — recentre and retake'],
                        'thresholds': gate['thresholds']}
        return base

    eps_px = (tol_um / 1000.0) * px_per_mm
    simplified = cv2.approxPolyDP(contour, eps_px, True).reshape(-1, 2)
    # image y grows DOWN; canonical is y-up (ADR-C) — flip about the mat.
    poly_mm = [(float(x) / px_per_mm, mat_h - float(y) / px_per_mm)
               for x, y in simplified]
    geometry = mm_polygon_to_canonical(poly_mm, chord_tolerance_um=tol_um)
    problems = validate_canonical(geometry)
    if problems:
        base['gate'] = {'passed': False,
                        'reasons': [f'canonical validation: {p}' for p in problems],
                        'thresholds': gate['thresholds']}
        return base

    confidence = _confidence(metrics, checks, stability)
    base.update({'geometry': geometry, 'confidence': confidence,
                 'segmentation': {'stability': round(stability, 3),
                                  'mask_area_mm2':
                                      round(float((mask > 0).sum()) / px_per_mm ** 2, 1),
                                  'vertices': len(geometry['outer'])}})
    return base


def _confidence(metrics, checks, stability):
    """Deterministic, component-visible score. NEVER an acceptance
    authority — humans confirm (Era-2 stance)."""
    comp = {
        'board_coverage': round(min(1.0, metrics['corner_fraction'] /
                                    0.9), 3),
        'residual': round(max(0.0, 1.0 - metrics['residual_p95_mm'] / 1.0), 3),
        'self_check': round(1.0 if not checks else max(
            0.0, 1.0 - max((c['delta_mm'] or 0) for c in checks) / 2.0), 3),
        'segmentation_stability': round(stability, 3),
    }
    composite = int(round(100 * min(comp.values())))
    return {'components': comp, 'composite': composite,
            'note': 'weakest-component score; display only, never auto-accept'}


if __name__ == '__main__':
    sys.exit(main())
