# compute/patterns_ai — isolated geometry/CV runtime (ADR-F, PRODUCTION)

The Django app NEVER imports cv2/numpy/ezdxf (test-walled). Every geometry
computation is a subprocess call into THIS runtime's own pinned venv with
JSON-file I/O — files/argv, no sockets (test-walled), no Django.

## Rebuild (offline-capable once wheels are in the artifact store)
```bash
cd compute/patterns_ai
python3 -m venv venv
./venv/bin/pip install -r requirements.lock.txt
```

## Tools (all: `tool.py --in job.json --out result.json`)
| Tool | Does |
|---|---|
| `synth.py` | deterministic synthetic golden captures (tests + drills) |
| `calibrate.py` | ChArUco detect → hold-out residuals → mat self-check → gate |
| `extract.py` | detect → gate → rectify → segment → contour → simplify → canonical µm geometry + component confidence |
| `dxf_io.py` | DXF-AAMA import → canonical; canonical → DXF export (layers 1/7/8/11) |
| `nest.py` | marker generation/verify/optimize (SVGnest + grid-BLF, one shapely verifier, internal timeboxes) |
| `pdf_io.py` | M8 pure-python production PDF — page 1 = Production Layout Summary, then numbered TRUE-SCALE A4 tiles (10 mm overlap match lines, 100 mm scale bar per tile); zero dependencies |
| `extract_plain.py` | M8 (capture) NO-MAT extraction — Otsu dark-object-on-light-table segmentation (OPEN 21 breaks tape/shadow bridges) → stability = threshold-perturbed IoU → contour → simplify → per-axis scale ANCHORED to human tape width/height (stated numbers land on the bbox exactly); gates: area 2–90% · frame-edge touch = retake · stability ≥ 0.60; trust stays uncalibrated (Django side) |

## Gates (ADR-E §3 — hard, recorded, never silent)
≥50% board corners visible · hold-out residual p95 ≤ 1.0 mm · tilt metric
≤ 0.35 · mat self-check ≤ 2.0 mm on every commissioned control distance ·
piece inside 20 mm border keep-out · plausible piece area ≥ 25 cm².

## Segmentation ladder (`runtime/segment.py`)
`classical` (default, always available): piece = mid-tone region occluding
the black/white board; morphology OPEN→CLOSE (open first — blur bands at
square borders must die before closing can weld them to the piece).
`sam` (adapter slot): activates ONLY when vendored ONNX artifacts exist —
see `artifacts/MANIFEST.md`. Honest unavailability, no silent fallback.

## Invariants
- Pipeline stamped `PIPELINE_VERSION` (runtime/__init__.py) into every result.
- Canonical payloads: integer µm, y-up, outer CCW, origin bbox-min,
  `schema_version` mandatory (`runtime/canonical.py`, kept in LOCKSTEP with
  Django's `patterns_ai/services/units.py` validator).
- Confidence = weakest-component score, display only; acceptance is human.
- `requirements.lock.txt` = the truth; changing any pin re-freezes it.
