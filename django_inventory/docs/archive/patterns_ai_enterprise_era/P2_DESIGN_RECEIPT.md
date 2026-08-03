# P2 DESIGN RECEIPT — Geometry/CV era build map (2026-07-07)

**One coherent phase (owner order). Governed by: Blueprint V3 · ADR A–H ·
ADR-D2 · ADR-D3 · Master Plan §P2 · Manufacturing V1 Freeze · P1 Freeze.
Contradiction ⇒ STOP.**

## 1. Runtime architecture (ADR-F, binding)

- **Django venv gains ZERO new packages in P2.** All CV/geometry/DXF
  compute runs in `compute/patterns_ai/` — its own pinned venv
  (numpy · opencv-contrib-python-headless · shapely · ezdxf, versions
  locked in `requirements.lock.txt`, POC-proven pins), invoked via
  subprocess with JSON-file I/O (`files/argv`, no sockets). A no-network
  wall test asserts compute scripts never open sockets.
- Compute scripts (each: `--in job.json --out result.json`):
  `synth.py` (deterministic synthetic golden captures — test fixtures +
  commissioning drills) · `calibrate.py` (board detect → homography →
  residuals → mat self-check) · `extract.py` (rectify → segment →
  contours → simplify → canonical µm JSON + confidence + gate) ·
  `dxf_io.py` (DXF-AAMA import → canonical; canonical → DXF export).
- **Segmentation backend ladder (F4/F7):** `classical` (OpenCV threshold/
  morphology/contours — default, always available) + `sam` adapter slot
  (activates only when vendored ONNX weights exist at
  `compute/patterns_ai/artifacts/`; reports itself unavailable honestly
  otherwise). Engine swap = artifact drop-in, zero Django change.
- ADR-B worker stays NOT built (P3); P2 compute is synchronous
  (< 5 s budget/master plan) behind the service.

## 2. Schema (all additive; models 9 → 13, conscious pin move)

- `PieceSizeGeometry` — (version, ProductSize) canonical ADR-C payload;
  chord_tolerance_um; trust_grade (measured / photo_calibrated /
  uncalibrated); source_extraction FK; copied_from FK (ADR-D2
  copy-forward); tape_acceptance JSON; UNIQUE(version, size).
- `GeometryExtraction` — append-only compute+review record: capture FK,
  piece FK, size FK, backend, params, pipeline_version, result JSON,
  gate JSON, confidence, status proposed→accepted|rejected(reason) +
  reviewer audit; guarded save/delete.
- `CalibrationMatCheck` — append-only commissioning/recheck evidence
  (reserved since 2A docstring).
- `PatternSetLabel` — product-homed graded-set label (master plan);
  `PatternPieceVersion.set_label` nullable FK (additive).
- `CalibrationMat.board_spec` JSON (ChArUco squares/marker/dict spec) —
  additive column.

## 3. Single writers (I-1 guard extended)

- `calibration_service` — CalibrationMat + CalibrationMatCheck: register /
  commission (control distances + board spec) / record_check / retire.
- `pattern_geometry_service` (the placeholder becomes real) —
  PatternPiece / PatternPieceVersion / PieceSizeGeometry /
  GeometryExtraction / PatternSetLabel: create_piece · run_extraction
  (per-photo HARD gate per ADR-E §3 — refusal is a recorded fact) ·
  accept_extraction → draft version + geometry row · reject_extraction
  (reason) · edit_draft_geometry (drafts only; confirmed immutable) ·
  confirm_version (**grain vector mandatory** per ADR-C; tape acceptance
  recorded; trust grade stamped; auto-supersede prior) · reject_version ·
  copy-forward on new version · import_dxf → draft · exports.
- `units.py` extends (I-4): mm↔µm, centi-degrees, polyline
  quantize/validate (closure, winding, vertex bounds).
- SVG generation = pure-python string building in Django (no lib);
  DXF via compute runtime.

## 4. UI (mobile-first, canon, management-gated, sidebar-seeded)

Mats registry (list/register/commission/recheck/retire) · phone capture
wizard (product → piece → size → mat → camera; batch = "capture next") ·
extraction annotator (original vs overlay SVG, per-gate metrics,
confidence components, accept/reject-with-reason) · piece library
(per-product; version timelines; per-size grid with trust grades) ·
version detail (SVG render + features, confirm w/ grain + tape numbers,
exports, Gate-1 true-scale print view) · draft geometry editor (vanilla-JS
vertex drag on inline SVG; server validates) · DXF import form.

## 5. Testing

Deterministic synthetic goldens (synth.py, checked-in PNGs): known-mm
squares/L-shapes on rendered board → extract → assert dimensions within
algo tier; gate rejections (blur/missing board/tilt); round-trips
JSON↔SVG and DXF import→canonical→export fidelity; service rules
(immutability, copy-forward, grain-mandatory confirm, one-shot review);
walls (I-1 extension, exactly-13 pin, SELECT-only reads, no-cv2-in-Django
import wall, no-network compute); view permissions; full serial
manufacturing suite.

## 6. P1 debt riding this block (sanctioned by owner-approved register)

3× non-int-id 500 one-liners + dead `big = None` removal. Nothing else.

## 7. Explicitly NOT in P2

Nesting/marker generation (P3) · ADR-B worker (P3) · SuggestionEvent UI
(Era-2 assistant surfaces) · grading engine (reserved payload only) ·
device-profile registry (ADR-D3) · MinIO (ADR-G stays filesystem).
