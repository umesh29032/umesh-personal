# P2 COMPLETION REPORT — Geometry & Computer Vision era (2026-07-07)

**Status: ✅ PHASE 2 COMPLETE — one coherent unit as ordered. STOPPED.
Phase 3 (Marker Generation & Optimization) will NOT start without explicit
owner approval.**

Companions: [P2_ENGINEERING_REVIEW](P2_ENGINEERING_REVIEW.md) ·
[P2_REGRESSION_REPORT](P2_REGRESSION_REPORT.md) ·
[P2_DESIGN_RECEIPT](P2_DESIGN_RECEIPT.md) ·
[P2_GEOMETRY_PIPELINE](P2_GEOMETRY_PIPELINE.md) (spec of record) ·
[ADR-D2](ADR/ADR-D2-piece-grain.md) · [ADR-D3](ADR/ADR-D3-capture-provenance.md)

## 1. Executive summary

Cardboard patterns can now become **confirmed, trusted, per-size digital
truth** — measured honestly on a commissioned calibration mat, reviewed
and confirmed by a human, immutable forever after, exportable to SVG and
DXF-AAMA, and printable at true scale for physical Gate-1 verification.

Everything the owner's Phase-2 order listed is live:

| Ordered | Delivered |
|---|---|
| D2 + D3 decisions | ADR-D2 (piece-level versions, per-size geometry rows, copy-forward) · ADR-D3 (provenance = versioned JSON payloads, EXIF subset, no profiling tables) |
| Calibration workflow + CalibrationMat | register → tape commission (print-scale catch) → active → recheck-on-capture → retire(reason); append-only `CalibrationMatCheck` evidence |
| Pattern capture workflow + provenance | phone wizard (camera attr) → immutable `CaptureAsset` (kind=pattern_capture, mat FK, EXIF metadata) |
| PatternPiece / PatternPieceVersion | live with the geometry era: draft→confirm/reject/supersede chain, `PatternSetLabel` grouping |
| OpenCV integration | isolated compute runtime (ADR-F): ChArUco detect, hold-out residuals, rectification, contours — cv2 NEVER enters Django (test-walled) |
| SAM integration | backend-ladder adapter slot: activates on vendored ONNX artifacts (MANIFEST.md), reports honest unavailability until then; `classical` = default occlusion-segmentation backend |
| Perspective correction + scale recovery | homography px→mat-mm plane (P0-proven method), local-scale tilt metric, rectified mm grid |
| Pattern extraction + cleanup | mid-tone occlusion segmentation → morphology (OPEN→CLOSE) → largest contour → border keep-out → approxPolyDP at chord tolerance |
| Canonical geometry | integer-µm payload (ADR-C §1-5): y-up, CCW, bbox-min origin, features block, schema_version; twin validators in lockstep |
| SVG generation | pure-Python renderer: library view + true-scale export + Gate-1 print with 10 cm scale bar |
| DXF import/export | DXF-AAMA both directions via runtime (layers 1/7/8/11, INSUNITS); round-trip byte-exact test |
| Human review + confidence | annotator: photo vs proposal overlay, gate verdict with recorded refusal reasons, weakest-component confidence (display-only, never auto-accepts), accept / reject-with-reason, one-shot |
| Geometry editing | draft-only vanilla-JS vertex editor on inline SVG; server re-validates winding/µm/bounds; confirmed geometry immutable |
| Validation | ADR-E hard gates per photo · Django-side canonical validation at every boundary · tape acceptance ±2 mm at confirm |
| Browser UI | 11 new templates, 18 new URLs, mobile-first canon, sidebar-inherited gating |
| Complete testing | +34 tests (128 app total; 1013 full suite) incl. REAL-runtime goldens |
| Documentation | pipeline spec, runtime README, GUIDE, index, this package |

## 2. The three big architecture moves

1. **Two-runtime isolation is now real (ADR-F):** `compute/patterns_ai/`
   owns its pinned venv (numpy · opencv-contrib-headless 5.0 · shapely ·
   ezdxf, `requirements.lock.txt`); Django invokes it via subprocess with
   JSON files. Source-scan walls enforce: no cv-stack import in Django, no
   Django/network import in compute. Engine swap = artifact drop-in.
2. **Metrology chain of custody (ADR-E):** tape-commissioned mats; every
   photo re-runs the self-check; hold-out residuals (fit on even corners,
   error measured on odd) make the reported accuracy honest; every refusal
   is a recorded fact on an append-only row.
3. **Geometry = knowledge under the same constitution as P1:** single
   writers, append-only evidence, human confirmation as the only truth
   boundary, derived things (SVG, DXF, prints) regenerable from canonical
   payloads.

## 3. Live browser proof (12 screenshots, real UI end-to-end)

`MAT-DEV-01` registered + tape-commissioned via forms (check #1 PASS) →
`Lower Back Panel` piece registered → synthetic golden capture (truth
150×100 mm) UPLOADED through the phone wizard → **gate PASSED (19/35
corners visible with the piece occluding the board · residual p95
0.0452 mm · tilt 0.0287 · confidence 60/100 weakest-component)** →
human Accept → draft v1 → **Confirm with grain 90° + tape 150.0×100.0 →
trust MEASURED, "geometry is now permanent knowledge"** → SVG export
(200, `image/svg+xml`, attachment) · DXF export (15,675 bytes,
`application/dxf`) · Gate-1 print page with scale bar → copy-forward v2
(1 size carried) → vertex editor (8 draggable handles) → v2 rejected with
reason (one-draft discipline restored). Screenshots:
`p2_capture_desktop` · `p2_annotator_{390,desktop}` ·
`p2_version_draft_390` · `p2_version_confirmed_{390,desktop}` ·
`p2_print_desktop` · `p2_library_{390,desktop}` · `p2_mat_390` ·
`p2_editor_desktop` · `p2_home_390`.

## 4. Golden accuracy (synthetic closed loop, real runtime, test-pinned)

150×100 mm ground-truth piece under tilt+blur → extracted
**within ±2 mm** (ADR-E in-cage tier); detection residual p95 0.045 mm
(matches P0's published algo-chain numbers). The physical tier on the
real printed mat remains **to be validated at rollout (D7 purchase)** —
exactly as ADR-E requires; nothing is claimed beforehand.

## 5. Schema (migration patterns_ai 0005 — all additive)

+`GeometryExtraction` (append-only, one-shot review) ·
+`PieceSizeGeometry` (unique per version×size, draft-mutable then frozen) ·
+`CalibrationMatCheck` (append-only) · +`PatternSetLabel` ·
`CalibrationMat.board_spec` · `PatternPieceVersion.set_label`.
Model pin consciously moved 9 → **13**. I-1 single-writer guard extended
to all four. Zero manufacturing schema involvement.

## 6. P1 debt cleared (rode this block, as the register sanctioned)

3× tampered-id 500s → `_int_or_404` (404s test-pinned) · dead `big = None`
removed. Plus 2 NEW bugs found by this phase's own hostile pass and fixed
+ pinned: true-scale SVG print shrink (viewBox/width mismatch) and grain
prefill units (centi-degrees into a degrees field).

## 7. Honest limitations (documented, not hidden)

- Physical error tier unvalidated until the real mat exists (D7) — the
  runbook step is the ADR-E addendum ritual on the factory table.
- `classical` segmentation assumes mid-tone pieces on the b/w board;
  very dark/light materials need the SAM backend (vendor weights) or a
  backend extension — the refusal path already reports "no piece found".
- Multi-piece DXF files refuse honestly (one piece per file, v1).
- Notches/drills/internal lines: schema + renderer + DXF layers support
  them; no capture UI creates them yet (annotation era work).
- Compute is synchronous behind the request (<5 s budget upheld on
  goldens); ADR-B worker remains P3 scope by master plan.

## 8. What Phase 3 gets to stand on

Confirmed per-size canonical geometry with trust grades + custody chains,
DXF/SVG round-trips, an isolated engine runtime with a proven bridge
protocol, and P0's nesting engine decision (SVGnest-core headless + BLF
floor) already vendored in poc/. **None of it started — awaiting your go.**
