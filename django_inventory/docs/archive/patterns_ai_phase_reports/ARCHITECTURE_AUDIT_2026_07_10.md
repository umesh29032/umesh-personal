> **ARCHIVED 2026-07-13** — shipped-phase report/review (patterns_ai). Live truth: [PLATFORM_STATUS](../../AI_PATTERN_INTELLIGENCE/PLATFORM_STATUS.md) + [PRODUCT_VISION_V2](../../AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md) + the app [GUIDE](../../apps/patterns_ai/GUIDE.md). Kept for history (Phase-7 DOCCLEAN-D, D-OR-1). Outbound links reflect its era.

# ARCHITECTURE AUDIT — what ACTUALLY exists (2026-07-10)
(Owner-ordered STOP audit. Code-level truth only — every claim
re-verified in the repository this session. No plans, no futures,
no "could/should". Implementation halted pending this audit.)

==================================================
## PART 1 — PATTERN GEOMETRY
==================================================

**1. Where geometry actually comes from — exactly THREE birth paths:**
- **Photo extraction** (`run_extraction` → compute `extract.py`): a
  phone photo of a piece lying ON a commissioned ChArUco calibration
  mat → accepted into a draft row.
- **DXF-AAMA import** (`import_dxf` → compute `dxf_io.py`): one closed
  boundary polyline on AAMA layer 1 (+ optional grainline layer 7).
- **Copy-forward**: a new version inherits the prior confirmed rows.
There is **NO draw-from-scratch path**: `edit_draft_geometry` REFUSES
when no row exists ("no geometry recorded for that size yet") — the
editor is a REFINEMENT tool (drag vertices, set grain angle) on rows
born by the two paths above. (Test fixtures create rows directly; that
is not an operator path.)

**2/3. What is stored — `PieceSizeGeometry.geometry` JSONField, the
ADR-C canonical payload:**
```
{schema_version: 1,
 outer:  [[x_um, y_um], ...]   ← INTEGER MICROMETRES, open ring, CCW,
                                  origin at bbox-min (validator-enforced)
 holes:  [[...]] (CW),
 chord_tolerance_um: int,
 features: {grain: {angle_cdeg}}   ← optional per-geometry grain ANGLE}
```
**POLYGON POINTS. Not SVG, not bezier, not raster, not an image.**
Plus columns: `trust_grade` (measured / photo_calibrated /
uncalibrated), `tape_acceptance` (numeric tape verdict frozen at
confirm), `source_extraction` (custody chain; NULL for DXF/manual),
`copied_from`, `geometry_contract_version` ('adr-c.1', stamped by the
single writer at all six write paths).

**4. Real geometry or images?** REAL geometry. Images are inputs and
documentation only: `CaptureAsset` stores originals (immutable,
hash-named); the reference image is display-only and structurally
banned from extraction. Every downstream consumer (facade, DCT,
verifier, exports, marker content) reads the polygon payload — never
pixels.

**5. Automatic generation?** Semi-automatic: the extraction PIPELINE is
automatic (photo → polygon proposal), but a HUMAN must accept the
proposal and a HUMAN must confirm the version (tape ±2 mm gate →
`measured`). Nothing confirms itself.

**6. Manually drawn?** Refined manually (vertex drag + grain angle in
the annotator/editor). Created manually from nothing: **NOT
IMPLEMENTED.**

**7. Imported?** YES — DXF-AAMA, one piece per file, validated through
the same canonical validator, `trust_grade=uncalibrated` until
tape-confirmed. (The flagship T-SHIRT's 30 designs entered THIS way,
not by photo.)

**8. Versioned?** YES — append-only `PatternPieceVersion` chain per
PIECE (draft → confirmed → superseded; confirmed rows immutable at
model level; copy-forward provenance; forward `superseded_by` lineage).

**9. Validated?** YES, twice: `validate_canonical_geometry` lives in
BOTH runtimes (Django twin + compute) — schema, vertex counts, integer
µm, winding, open-ring, origin-at-bbox-min. Plus the extraction hard
gate (mat active/commissioned, board detected, piece off mat edge,
minimum area) with recorded refusal reasons; plus the tape gate at
confirm.

**10. Reusable?** YES — one confirmed geometry row feeds: the facade →
Manager/Library/DCT, marker generation, the layout verifier, SVG/DXF/
PDF exports, marker content counting. Single source, many readers.

**11–13. Owners/writers:** models `patterns_ai/models/geometry.py`
(GeometryExtraction append-only; PieceSizeGeometry draft-mutable →
frozen-with-version). ONE writer: `pattern_geometry_service`
(extraction run/accept/reject · edit · confirm · copy-forward · DXF
import · piece/rule setters · `register_pattern_definition`).
Adversarially re-verified this week: zero writes elsewhere.

**14. Readers:** `pattern_design_facade` (THE read contract),
`marker_generation_service` (resolve + verify + save),
`svg_render`, exports, `layout_usage_service.marker_content`,
`layout_library_service.layout_is_stale`.

**15. Still missing (geometry itself):** draw-from-scratch · lens/
distortion correction (see Part 3) · multi-photo capture for pieces
larger than a mat · grading (each size is digitized independently) ·
seam-allowance modeling (the contract DECLARES cut-ready; nothing
computes offsets).

==================================================
## PART 2 — PATTERN INTELLIGENCE
==================================================

"Pattern Intelligence" today = the patterns_ai app's DERIVED-AT-READ
brains. No ML anywhere in it. Concretely, it calculates:

1. **Readiness** (facade): per-size verdicts (ready/attention/missing
   tiers), per-row checks (geometry/reference/confirmed/dxf), the
   ≥1-Ready gate, `any_size_ready`.
2. **Metrics** (`derive_candidate_metrics`): length, utilization %,
   waste %, per-garment meters — pure polygon math over STORED
   placements, never persisted (F6).
3. **Benchmark/Advisor/Insights/Yield** (P3–P5 era, research-frozen):
   proven-beats-theory marker recommendation, yield m/100 boards,
   executive KPIs — all SELECT-only, all display.
4. **Marker content** (8C): per-(pattern, size) piece counts from
   stored placements.
5. **Staleness** (Law 11): frozen version-ids vs current confirmed.
6. **AI Optimize** (the one searcher): the nest engine —
   deterministic-per-seed BLF raster + vendored SVGnest, obstacles,
   ranking rules — placement search ONLY.

**Inputs:** confirmed geometry payloads + Blueprint rules (grain, pair,
fold, optional, fabric group, counts) + stored placements + recorded
usage/outcome facts. **Outputs:** verdicts, numbers, rankings,
placements. **Geometry-aware:** yes (polygons). **Image-aware:** NO —
zero intelligence reads pixels (segmentation lives in the capture
pipeline, not here). **Knows** grain/pair/mirror/fold/area/fabric
group/ready/relationships: YES, all via Blueprint + facade + payload.
**Image-dependent:** NO — a DXF-born product gets identical
intelligence (the T-SHIRT proves it). **Deliberately does NOT:**
approve anything, write anything, own plies, own money, edit geometry,
touch production models directly.

==================================================
## PART 3 — IMAGE PIPELINE (the honest section)
==================================================

**YES, a real CV pipeline exists** — `compute/patterns_ai/` (isolated
venv, subprocess bridge, ADR-F). Step by step against your list:

| Step | Status | Truth |
|---|---|---|
| Photo upload | ✅ EXISTS | `CaptureAsset` — magic-byte sniff, size caps, sha256, immutable |
| Perspective correction | ✅ EXISTS | ChArUco board detect (`cv2.aruco.CharucoDetector`) → RANSAC homography px→mm with HOLD-OUT residual quality metrics → image rectified onto the mm grid |
| Lens correction | ❌ **NOT IMPLEMENTED** | no distortion coefficients anywhere in `detect.py` — homography only; wide-angle phone distortion is uncorrected |
| Calibration | ✅ EXISTS | commissioned `CalibrationMat` (board_spec + control-distance TAPE truth), recheck-on-capture, retire — a real metrology loop |
| AI segmentation | 🟡 **SLOT ONLY** | backend ladder: `classical` (deterministic mid-tone occlusion of the known board — no ML) ALWAYS; `sam` activates only if MobileSAM ONNX artifacts exist under `artifacts/` — **the directory holds MANIFEST.md ONLY. No model shipped. Honest self-report, not a placeholder lie — but in practice segmentation is classical-only.** |
| Edge detection | ✅ EXISTS | `cv2.findContours` on the rectified mask |
| Contour extraction | ✅ EXISTS | largest contour, min-area gate, mat-edge keep-out |
| Polygon generation | ✅ EXISTS | `approxPolyDP` chord-tolerance simplification → integer-µm canonical ring |
| Geometry validation | ✅ EXISTS | canonical validator in BOTH runtimes + the hard gate with recorded refusals + confidence (display-only, never auto-accepts) |
| → PieceGeometry | ✅ EXISTS | accept (one-shot human review) → draft row → tape-gated confirm |

**The practical constraint nobody should gloss:** capture REQUIRES the
piece to lie fully ON a commissioned mat (border keep-out enforced).
Pieces larger than the physical mat cannot be photo-captured. **The
real T-SHIRT panels entered via DXF import, not the photo path** — the
photo pipeline is real and tested (golden ±2 mm suite) but its
production-scale use for full-size garment panels is UNPROVEN, and
multi-photo stitching is NOT IMPLEMENTED.

==================================================
## PART 4 — DXF / SVG
==================================================

- Import DXF: **YES** — ezdxf, AAMA layers (1 = boundary, 7 =
  grainline), LWPOLYLINE/POLYLINE, one piece per file, scale-checked,
  canonical-validated.
- Export DXF: **YES** — per confirmed geometry row
  (`export_dxf_bytes` → compute `dxf_io` export op; download button on
  the Library rows).
- Generate DXF: only in the sense of export-from-geometry. No layout-
  level (multi-piece marker) DXF export: **NOT IMPLEMENTED** —
  marker exports are SVG/PDF/print-tiles.
- Store DXF: **NO** — generated on demand, never persisted.
- Generate SVG: **YES** — `svg_render` (READ-ONLY; the ONE y-flip
  home): piece previews, true-scale piece SVG, full marker SVG with
  stamped summary metadata.
- Store SVG: **NO** — rendered on demand.
- Render SVG: **YES** — Library previews, candidate pages, DCT palette
  thumbnails, marker downloads, print tiles.
- Polygons FROM SVG: **NO** — SVG is output-only; polygons come from
  extraction/DXF.
- SVG in the DCT: **YES**, twice — palette previews (`preview_svg`) and
  the workspace pieces themselves are `<polygon>` elements built from
  `outline_mm` (facade-converted µm→mm floats).
- SVG in Manufacturing: **YES** — the pattern-stage Manufacturing
  Layout panel links the approved marker's SVG (`candidate-svg`), and
  the production PDF/print-tiles come from the same stored placements.

==================================================
## PART 5 — DIGITAL CUTTING TABLE
==================================================

**What reaches the DCT: FACADE ROWS.** Not images, not raw models.
Exact object: the Design-Row dict (design_key `piece:size`,
`outline_mm` = the canonical ring converted to mm floats, dims, area,
badges, `grain_rule`, `fabric_group`, checks) — confirmed designs of
READY sizes only, serialized once into `workspace_payload`
(json_script).

**The data structure through the pipeline:**
```
PieceSizeGeometry.geometry (int µm, canonical)
  → facade outline_mm (mm floats)                    [read]
  → runtime piece {instance_id, design_key, x_mm, y_mm, rotation,
     mirror, locked, _outline, _bbox}                [browser session]
  → engine frame swap ([across,down] → [along,across])
  → placements [{key, instance, polygon_mm, rotation_deg, mirrored,
     locked}]                                        [verify/optimize/save]
  → GeneratedMarkerCandidate.placements (verbatim)   [immutable]
```
- **Import**: click → LAW-12 group lock → first-fit clear-spot scan via
  the constraint pipeline.
- **Rotation**: 90° steps filtered by the Blueprint `grain_rule`
  (strict 0° / two_way 0-180 / free 4-way), transform about the piece
  centre; world mm never change (camera separate).
- **Collision**: client pipeline `boundary → polygon intersection
  (segment tests + containment) → spacing margin (min edge distance vs
  the profile's spacing)`; red/amber/violet channels; the SAME
  `placementStatus` drives import, Compact, Auto Place.
- **AI optimization**: stateless POST → `optimize_layout` → nest engine
  (locked = fixed obstacles; grain → `allow_180`) → honest
  better/same/worse verdict; better applies as movable session pieces.
- Save = verify-then-persist verbatim; Approve = human review page →
  `ApprovedLayout` pointer.

==================================================
## PART 6 — MANUFACTURING
==================================================

Manufacturing (the Adda chain) consumes:
- **ApprovedLayout** — via `ApprovedLayoutUsage` (pointer, per fabric
  group), chosen on the choose page, displayed on the pattern-stage
  panel, marker SVG one click away. Stale/inactive refused at record.
- **Marker content** (derived from the approved layout's placements) ×
  **lay_count** (layering's truth) → the ADVISORY suggested breakup +
  the completion WARN. Operator numbers always stand.
- NOT images, NOT DXF, NOT geometry rows directly, NOT intelligence
  dashboards.

**Manufacturing truth today = `AddaProductSizeColorPieceBreakdown`** —
the operator's verified bundle counts, frozen at cutting completion,
feeding barcodes → tracking/inventory. The approved layout is the
manufacturing CONTRACT/reference; the breakdown is the manufacturing
FACT. (Enforcement gates — require-layout, count reconciliation — are
DESIGNED for 8D and **NOT YET IMPLEMENTED**; today the layout link is
optional and advisory end-to-end.)

==================================================
## PART 7 — THE MISSING LAYER
==================================================

Judging ONLY the implementation: **the paper-to-polygon front door is
the bottleneck — full-size pattern digitization.**

Every layer after geometry exists and is wired: Blueprint → Manager →
readiness → DCT → verify → save → approve → choose → advisory numbers.
The chain from "a confirmed polygon" to "an Approved Layout an Adda
consumes" is COMPLETE. But getting a real factory's FULL-SIZE paper
pattern INTO a confirmed polygon currently requires either:
(a) the photo path — real, but mat-bounded (piece must lie fully on a
commissioned ChArUco mat), classical-only segmentation (SAM artifacts
absent), no lens correction, no multi-shot stitching — unproven at
garment-panel scale; or
(b) DXF files — which most small factories don't have (the T-SHIRT
used this path because we made the DXFs).

So the single missing subsystem is **large-piece capture / production-
grade digitization** (mat-scale capture proven; panel-scale capture
not). Everything else on the paper→ApprovedLayout road exists.
Secondary genuine absences, stated not solved: cut-plan/ratio input
(layout `ratio={}` honest), grading, 8D enforcement gates, layout-level
DXF export, ★-vs-library unification.

==================================================
## PART 8 — THE REAL ARCHITECTURE, AS IMPLEMENTED
==================================================

```
PRODUCT (production)
  ↓
PATTERN DASHBOARD (patterns_ai) — STEP 1/2/3 workflow
  ↓
BLUEPRINT — pieces + rules (count·optional·pair·fold·grain·fabric group)
  ↓
GEOMETRY BIRTH:
   photo→mat→homography→classical-segment→contour→polygon  [mat-sized only]
   ******** MISSING: lens correction ********
   ******** MISSING: SAM artifacts (slot empty — classical only) ********
   ******** MISSING: large-piece / multi-shot capture ********
   DXF-AAMA import                                          [works]
   ******** MISSING: draw-from-scratch ********
   ******** MISSING: grading engine (per-size manual entry) ********
  ↓
HUMAN REVIEW → draft → TAPE-GATED CONFIRM → PieceSizeGeometry
  (int-µm polygon · versioned · immutable · contract-stamped)
  ↓
PATTERN MANAGER — per-size readiness (facade = the ONE read contract)
  ↓
DIGITAL CUTTING TABLE — session runtime · physics · Compact/AutoPlace ·
  AI optimize (nest engine) — mm world, engine-frame at the boundary
   ******** MISSING: cut-plan / ratio input (ratio stored {}) ********
  ↓
SAVE (verify-then-persist, verbatim) → immutable run+candidate
  ↓
HUMAN APPROVE → APPROVED LAYOUT LIBRARY (uid · version chain · stale
  derived · exports: SVG/PDF/print — layout-level DXF ******** MISSING ********)
  ↓
ADDA chooses → ApprovedLayoutUsage (per fabric group · history forever)
  ↓
ADVISORY NUMBERS: marker content × lay_count → suggestion + WARN
   ******** MISSING: 8D enforcement flags (designed, not built) ********
   ******** MISSING: ★ designation vs library unification ********
  ↓
CUTTING (operator truth) → Breakdown → BARCODES → TRACKING/INVENTORY
```

==================================================
## FINAL TABLE
==================================================

| Subsystem | Complete % | Status | Missing responsibilities |
|---|---|---|---|
| Blueprint (structure + rules) | 95% | LIVE | per-size requiredness (registered future) |
| Geometry storage/versioning/contract | 95% | LIVE | seam-allowance modeling (declared, not computed) |
| Photo capture pipeline | 70% | LIVE at mat scale | lens correction · SAM artifacts · large-piece/multi-shot capture · panel-scale field proof |
| DXF import/export (piece) | 90% | LIVE | multi-piece files; layout-level marker DXF |
| Manual geometry | 40% | REFINE-ONLY | draw-from-scratch NOT IMPLEMENTED |
| Grading | 0% | NOT IMPLEMENTED | base-size + rules → sizes (each size manual today) |
| Pattern Manager / readiness | 100% | LIVE | — |
| Pattern Intelligence (derive-at-read) | 90% | LIVE (research pieces frozen) | nothing pending by design |
| Digital Cutting Table (session) | 90% | LIVE | cut-plan/ratio input · marquee/multi-select niceties |
| Save / Approve / Library | 95% | LIVE | layout-level DXF export; supersede-from-library shortcut |
| Adda consumption (choose/display) | 90% | LIVE (advisory) | 8D: stage-record stamp wiring |
| Expected/reconciliation | 85% | LIVE (advisory) | 8D: enforcement flags (default-OFF gates) |
| Enforcement (rule 9 as code-law) | 0% | NOT IMPLEMENTED (designed 8D) | REQUIRE_APPROVED_LAYOUT · ENFORCE_LAYOUT_RECONCILIATION |
| Barcodes/inventory hand-off | 100% | LIVE (pre-existing) | consumes Breakdown only (by design) |

**Audit verdict:** the platform's middle and end are real and armored;
the honest weak point is the FRONT DOOR at production scale
(large-piece digitization) plus the deliberately-deferred 8D gates.

**STOPPED — audit delivered. No code written. Awaiting your direction.**
