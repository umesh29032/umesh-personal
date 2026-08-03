"""extract_plain — M8 no-mat capture (the Evidence-Set adapter's CV leg).

The owner's REAL workflow: cardboard flat on a plain light table, no
calibration mat; scale comes from HUMAN-STATED tape measurements
(width/height mm), so the result is honest-UNCALIBRATED until the tape
gate at publish upgrades it. Deterministic only: the existing classical
segmentation ladder + contours; per-axis scale = stated / measured-px
(tape truth wins per axis).

Protocol (ADR-F files/argv): extract_plain.py --in job.json --out result.json
job: {image_path, width_mm, height_mm, params:{backend, chord_tolerance_um}}
"""
import argparse
import json
import sys

import cv2
import numpy as np

from runtime import PIPELINE_VERSION
from runtime.canonical import mm_polygon_to_canonical, validate_canonical
from runtime.segment import available_backends

MIN_AREA_FRAC = 0.02       # piece must fill ≥2% of the frame (junk guard)
MAX_AREA_FRAC = 0.90       # and not BE the frame (segmentation blowout)
MIN_STABILITY = 0.60       # threshold-insensitivity gate (honest refusal)
EDGE_MARGIN_PX = 3         # piece touching the frame = retake


def _plain_mask(gray, t_shift=0):
    """Dark-object-on-light-table (the REAL factory photo: brown
    cardboard on a grey-white surface — proven on the owner's real
    20-photo set). Otsu split + a strong OPEN that breaks thin bridges
    (tape-measure print, shadows) before CLOSE heals the piece."""
    blur = cv2.GaussianBlur(gray, (7, 7), 0)
    t, _ = cv2.threshold(blur, 0, 255,
                         cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    mask = (blur < max(1, min(254, t + t_shift))).astype(np.uint8) * 255
    mask = cv2.morphologyEx(
        mask, cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (21, 21)))
    mask = cv2.morphologyEx(
        mask, cv2.MORPH_CLOSE,
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))
    return mask


def _segment_plain(gray):
    """(mask, stability): stability = IoU of the base mask against a
    threshold-perturbed one — the same honesty metric as the mat path."""
    base = _plain_mask(gray)
    alt = _plain_mask(gray, t_shift=-12)
    inter = np.logical_and(base > 0, alt > 0).sum()
    union = np.logical_or(base > 0, alt > 0).sum()
    return base, (float(inter / union) if union else 0.0)


def run(job):
    image_path = job['image_path']
    width_mm = float(job['width_mm'])
    height_mm = float(job['height_mm'])
    params = job.get('params') or {}
    backend = params.get('backend', 'classical')
    chord_um = int(params.get('chord_tolerance_um', 500))
    if width_mm <= 0 or height_mm <= 0:
        return {'ok': False, 'error': 'stated width/height must be > 0 mm'}

    img = cv2.imread(image_path)
    if img is None:
        return {'ok': False, 'error': f'unreadable image: {image_path}'}
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    H, W = gray.shape[:2]

    mask, stability = _segment_plain(gray)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL,
                                   cv2.CHAIN_APPROX_SIMPLE)
    reasons = []
    contour = None
    if not contours:
        reasons.append('no piece found against the background')
    else:
        contour = max(contours, key=cv2.contourArea)
        area_frac = cv2.contourArea(contour) / float(H * W)
        bx, by, bw, bh = cv2.boundingRect(contour)
        if area_frac < MIN_AREA_FRAC:
            reasons.append(f'largest shape covers only '
                           f'{area_frac * 100:.1f}% of the frame — move '
                           'closer / plainer background')
        if area_frac > MAX_AREA_FRAC:
            reasons.append('segmentation covered the whole frame — '
                           'background not distinguishable')
        touches = sum([bx <= EDGE_MARGIN_PX, by <= EDGE_MARGIN_PX,
                       bx + bw >= W - EDGE_MARGIN_PX,
                       by + bh >= H - EDGE_MARGIN_PX])
        if touches:
            reasons.append(f'piece touches the photo edge on {touches} '
                           'side(s) — retake with background margin all '
                           'around (keep the tape BESIDE the piece, '
                           'never across it)')
    if stability < MIN_STABILITY:
        reasons.append(f'segmentation unstable ({stability:.2f} < '
                       f'{MIN_STABILITY}) — lighting/shadows; retake')

    gate = {'passed': not reasons, 'reasons': reasons,
            'stability': round(stability, 3)}
    provenance = {'pipeline_version': PIPELINE_VERSION,
                  'tool': 'extract_plain-1',
                  'params': {'backend': backend,
                             'chord_tolerance_um': chord_um,
                             'width_mm': width_mm,
                             'height_mm': height_mm},
                  'backends_available': available_backends()}
    if reasons:
        return {'ok': True, 'gate': gate, 'geometry': None,
                'confidence': {}, 'provenance': provenance,
                'segmentation': {'stability': round(stability, 3)},
                'metrics': {}, 'checks': {}}

    # per-axis scale: the TAPE numbers are the truth for each axis —
    # bbox lands exactly on the stated dims; other stated measurements
    # become cross-checks on the Django side.
    x, y, w_px, h_px = cv2.boundingRect(contour)
    if w_px < 2 or h_px < 2:
        return {'ok': False, 'error': 'degenerate contour'}
    px_per_mm = (w_px / width_mm + h_px / height_mm) / 2.0
    eps_px = max(1.0, (chord_um / 1000.0) * px_per_mm)
    simplified = cv2.approxPolyDP(contour, eps_px, True).reshape(-1, 2)
    if len(simplified) < 3:
        return {'ok': False, 'error': 'outline degenerated below 3 points'}
    # per-axis scale anchored to the SIMPLIFIED outline's span, so the
    # human tape numbers land on the payload bbox EXACTLY (simplify can
    # shave a pixel off the raw-contour bbox)
    sxs = simplified[:, 0]
    sys_ = simplified[:, 1]
    x0, x1 = int(sxs.min()), int(sxs.max())
    y0, y1 = int(sys_.min()), int(sys_.max())
    if x1 - x0 < 2 or y1 - y0 < 2:
        return {'ok': False, 'error': 'degenerate contour'}
    sx = width_mm / float(x1 - x0)
    sy = height_mm / float(y1 - y0)
    # px (y-down) -> mm (y-up): flip about the outline bottom
    poly_mm = [[(px - x0) * sx, (y1 - py) * sy]
               for px, py in simplified.tolist()]
    payload = mm_polygon_to_canonical(poly_mm,
                                      chord_tolerance_um=chord_um)
    problems = validate_canonical(payload)
    if problems:
        return {'ok': False, 'error': f'canonical validation: {problems}'}

    # display-only confidence: stability drives it; the scale is human
    confidence = {'overall': int(round(70 + 20 * stability)),
                  'segmentation_stability': round(stability, 3)}
    return {'ok': True, 'gate': gate, 'geometry': payload,
            'confidence': confidence, 'provenance': provenance,
            'segmentation': {'stability': round(stability, 3),
                             'bbox_px': [int(x), int(y),
                                         int(w_px), int(h_px)],
                             'vertices': len(simplified)},
            'metrics': {'px_per_mm': round(px_per_mm, 2)},
            'checks': {'area_frac': round(
                cv2.contourArea(contour) / float(H * W), 4)}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--in', dest='inp', required=True)
    ap.add_argument('--out', dest='out', required=True)
    args = ap.parse_args()
    with open(args.inp) as fh:
        job = json.load(fh)
    try:
        result = run(job)
    except Exception as exc:                       # honest failure record
        result = {'ok': False, 'error': f'{type(exc).__name__}: {exc}'}
    with open(args.out, 'w') as fh:
        json.dump(result, fh)
    return 0


if __name__ == '__main__':
    sys.exit(main())
