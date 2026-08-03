---
id: docs-ai-pattern-intelligence-p2-geometry-pipeline
type: topic-canonical
status: active
owner: handwritten
scope: patterns_ai
anchors: config/patterns_ai/
verified: 2026-07-18
---

# P2 Geometry Pipeline & Payload Spec (ADR-C/D2/D3 — spec of record)

## 1. Canonical geometry payload (schema_version 1)
Stored on `PieceSizeGeometry.geometry` and proposed on
`GeometryExtraction.geometry`. ANY tool in any language reads it with this
page (ADR-C promise).

```json
{
  "schema_version": 1,
  "units": "um",                    // integer micrometres, ALWAYS
  "origin": "bbox_min",             // piece-local, min corner = (0,0)
  "axes": "x_right_y_up",
  "chord_tolerance_um": 500,        // polyline-at-tolerance record
  "outer": [[0,0], [150000,0], ...],   // CCW, stored OPEN (first != last)
  "holes": [[[...]]],               // CW rings
  "features": {
    "grain": {"angle_cdeg": 9000},  // integer centi-degrees; MANDATORY at confirm
    "notches": [], "drills": [], "internal_lines": [[[x,y],...]],
    "fold_edge": null, "seam_allowance": "as_cut"
  },
  "grade_rule": null                // reserved (ADR-C §5), never repurposed
}
```
Validators (kept in lockstep — a rule change edits BOTH):
`compute/patterns_ai/runtime/canonical.py` ·
`config/patterns_ai/services/units.py::validate_canonical_geometry`.
Bounds: 3..4000 vertices; winding enforced; origin at bbox-min.

## 2. Truth chain (who writes what)
```
photo (CaptureAsset, immutable, mat FK)            capture_service
  └─ extraction (GeometryExtraction, append-only)  pattern_geometry_service.run_extraction
       gate REFUSED -> recorded reasons, no geometry, cannot be accepted
       gate PASSED  -> proposal + component confidence (display only)
  └─ HUMAN accept  -> PieceSizeGeometry on the piece's DRAFT version
  └─ HUMAN confirm -> version CONFIRMED (grain mandatory; optional tape
       acceptance ±2 mm -> trust MEASURED; else PHOTO_CALIBRATED;
       DXF imports start UNCALIBRATED) -> prior version auto-SUPERSEDED
  └─ later sizes   -> start_next_version copy-forward (copied_from provenance)
```
Trust grades (ADR-E §7): measured · photo_calibrated · uncalibrated.
Confirmed geometry is immutable (model save/delete guards + service refusals).

## 3. Provenance payloads (ADR-D3)
- `CaptureAsset.metadata.exif` — camera make/model/software/datetime/
  orientation/pixel_size (PIL metadata read; never used in math).
- `GeometryExtraction.result` — metrics (corners, hold-out residuals,
  tilt, homography), self-check deltas, segmentation stats, provenance
  (pipeline_version, backend, params, available_backends).
- `GeometryExtraction.gate` — passed + recorded reasons + thresholds.
- `CalibrationMatCheck.evidence` — calibrate.py output per
  commissioning/recheck row.
- `PieceSizeGeometry.tape_acceptance` — width/height tape numbers + deltas
  + tolerance at confirm.

## 4. Exports (ADR-C §7 guarantees)
- **SVG** — `svg_render.geometry_svg` (pure Django-side string building):
  y-flip happens THERE only; true-scale mode spans viewBox+pad in mm
  (print-shrink pinned by test); grain arrow; Gate-1 print page adds a
  10 cm scale bar.
- **DXF-AAMA** — via the runtime (`dxf_io.py`): layer 1 boundary ·
  7 grainline · 11 cutouts · 8 internal lines; $INSUNITS=4; round-trip
  byte-exact on µm integers (test-pinned).

## 5. The mat (ADR-E)
`CalibrationMat` lifecycle: register → commission (board_spec + tape
control distances; tape is the print-scale catch) → active → recheck rows
(run on captures stored on that mat) → retire(reason). All evidence =
append-only `CalibrationMatCheck` rows. Every capture's gate re-runs the
self-check — a mat whose tape disagrees with its print refuses every
photo taken on it.
