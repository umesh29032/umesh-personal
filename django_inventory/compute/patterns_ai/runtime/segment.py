"""Segmentation backend ladder (ADR-F / F4 engine independence).

`classical` — default, always available: the piece is found as the
mid-tone region occluding the known black/white board pattern on the
rectified image. Deterministic, no ML.

`sam` — adapter slot: activates ONLY when vendored ONNX artifacts exist
under compute/patterns_ai/artifacts/ (see MANIFEST.md). Reports itself
unavailable honestly otherwise — no silent fallback.
"""
import os

import cv2
import numpy as np

ARTIFACT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                            'artifacts')
SAM_ENCODER = os.path.join(ARTIFACT_DIR, 'mobile_sam.encoder.onnx')
SAM_DECODER = os.path.join(ARTIFACT_DIR, 'mobile_sam.decoder.onnx')

# mid-tone band: board is near-black/near-white after rectification;
# cardboard/chalk pieces sit between. Margins are the stability knob.
DARK_MARGIN = 60
LIGHT_MARGIN = 60


def available_backends():
    out = ['classical']
    if os.path.exists(SAM_ENCODER) and os.path.exists(SAM_DECODER):
        try:
            import onnxruntime  # noqa: F401  (lives in THIS venv if vendored)
            out.append('sam')
        except ImportError:
            pass
    return out


def segment(rect_gray, backend='classical'):
    """Return (mask uint8 0/255, stability 0..1). Raises ValueError for an
    unavailable backend — the caller records the refusal, never guesses."""
    if backend == 'classical':
        return _classical(rect_gray)
    if backend == 'sam':
        if 'sam' not in available_backends():
            raise ValueError(
                'sam backend unavailable: vendored ONNX artifacts missing '
                f'under {ARTIFACT_DIR} (see MANIFEST.md)')
        return _sam(rect_gray)
    raise ValueError(f'unknown backend {backend!r}')


def _midtone_mask(gray, dark, light):
    mask = ((gray > dark) & (gray < 255 - light)).astype(np.uint8) * 255
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
    # OPEN first: blur creates thin mid-tone bands along every black/white
    # square border — opening erases them BEFORE closing can weld them onto
    # the piece (weld = systematic bbox inflation, caught by golden tests).
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, k)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k)
    return mask


def _classical(rect_gray):
    base = _midtone_mask(rect_gray, DARK_MARGIN, LIGHT_MARGIN)
    # stability: same segmentation at perturbed margins; IoU of the masks
    # is an honest self-consistency score (1.0 = threshold-insensitive).
    alt = _midtone_mask(rect_gray, DARK_MARGIN + 15, LIGHT_MARGIN + 15)
    inter = np.logical_and(base > 0, alt > 0).sum()
    union = np.logical_or(base > 0, alt > 0).sum()
    stability = float(inter / union) if union else 0.0
    return base, stability


def _sam(rect_gray):  # pragma: no cover - exercised only with vendored weights
    import onnxruntime  # noqa: F401
    raise NotImplementedError(
        'sam adapter: wire encoder/decoder sessions per MANIFEST.md when '
        'the vendored artifacts land (ADR-F artifact drop-in).')
