> **ARCHIVED 2026-07-13** — shipped-phase report/review (patterns_ai). Live truth: [PLATFORM_STATUS](../../AI_PATTERN_INTELLIGENCE/PLATFORM_STATUS.md) + [PRODUCT_VISION_V2](../../AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md) + the app [GUIDE](../../apps/patterns_ai/GUIDE.md). Kept for history (Phase-7 DOCCLEAN-D, D-OR-1). Outbound links reflect its era.

# M2 — PATTERN INTELLIGENCE STUDIO · implementation plan
(2026-07-10 · executes UI_WORKFLOW_FREEZE §1/§2.1/§2.3/§2.4/§2.5/§3/§4 +
PRODUCT_DESIGN_FREEZE §7/§8 · additive-only, spine untouched, production
app untouched — zero ADR-H exposure this milestone)

## The mapping discovery (recon verdict)
The frozen acquisition contract ALREADY exists structurally for photo:
`CaptureAsset (evidence) → run_extraction (adapter) → GeometryExtraction
(proposal: append-only, one-shot review, gate, confidence, provenance) →
accept (human) → draft row → confirm (tape gate) → truth`.
M2 = generalize that machinery to every adapter + build the room around
it. The compute runtime's canonical payload already reserves
`features.notches` — adr-c.2 formalizes it.

## Changes (all patterns_ai; ONE migration 0012)

**Models**
- NEW `EvidenceItem` (models/geometry.py): piece FK · size FK · kind
  (photo/dxf/svg/pdf/png/manual_dims/ai_api) · capture FK nullable
  (photo wraps CaptureAsset) · file nullable (dxf/svg originals kept —
  evidence is a fact) · params JSON (manual dims) · status
  (received/proposed/refused) · refusal_reason · created_by. Delete
  refused; service-flagged transitions only (house pattern).
- `GeometryExtraction.capture` → null=True (non-photo adapters);
  + `evidence` FK nullable. Existing rows untouched.
- `PatternPiece` + `expected_notches` (PositiveSmallIntegerField null)
  + `seam_allowance_mm` (Decimal null) — Blueprint metadata slots
  (UI freeze §3).

**adr-c.2 (conscious contract bump — the stamp was built for this)**
- `GEOMETRY_CONTRACT_VERSION = 'adr-c.2'` (single constant, single writer).
- Validator TWINS (units.py + compute runtime canonical.py, lockstep):
  optional `features.notches` = list of `{x_um:int, y_um:int, label?}`
  — type-checked when present; absent = valid (c.1 payloads remain valid).
- `edit_draft_geometry` gains `notches` param (re-anchored with the
  outline). Notch-count vs Blueprint expectation = DISPLAY-ONLY chip
  (warnings explain, never modify).

**Services**
- NEW `acquisition_service` = single writer for EvidenceItem
  (add_evidence · record_photo_evidence · refuse flows · conveyor
  `next_missing_design(product, after=None)`).
- `pattern_geometry_service` (owner of GeometryExtraction) gains
  `run_evidence_adapter(user, evidence)` dispatching by kind:
  dxf → compute_bridge dxf import → proposal · svg → NEW pure-python
  `svg_import.py` (straight-segment paths/polygons, mm units; curves =
  honest refusal "export as DXF") → proposal · manual_dims → rectangle
  construct → proposal. PDF/PNG/AI = menu slots, honest-unavailable
  (SAM-precedent ladder rule) — no fake rows.
- `accept_extraction`: trust grade BY ADAPTER — photo→photo_calibrated,
  others→uncalibrated (tape confirm still the only path to measured).
- Confidence display dict (freeze §4 table): manual 100 · DXF 99 ·
  SVG 95 · photo per-run (existing metrics) · display-only.
- Legacy `import_dxf` API + page stay (frozen tests) — Studio path is
  the proposal-contract path; navigation points at the Studio.

**Views/URLs**
- `studio/` StudioView — BROWSE mode: size tabs (hierarchy law) ·
  creation-checklist chips (existing readiness truth, new surface) ·
  Ready banner · shelf rows (facade Design Rows + preview + [Open in
  Studio] [History] [DXF] [SVG]) · conveyor button.
- `studio/work/<piece>/<size>/` StudioWorkView — WORK mode 3-pane:
  evidence stack (add DXF/SVG/manual-dims inline; photo → QR hand-off
  panel: qrcode lib SVG + link to existing capture page w/ `?size=`
  preselect + 5s evidence poll) · proposal canvas + COMPARE overlay w/
  delta table · inspector (metadata chips §3 · confidence · provenance ·
  Verify & Publish tape dialog → conveyor "Next: X · S →").
- `studio/work/<piece>/<size>/evidence-count/` tiny JSON poll endpoint.
- Dashboard → 5-STATION RAIL (§2.1): Blueprint · Studio · DCT ·
  Layout Library · Manufacturing; live verdicts (pieces · sizes-ready ·
  gate · active layouts · active usages).
- `PatternCaptureView` also records the EvidenceItem (same transaction)
  + accepts `?size=` preselect + mat-guidance hint text.
- Existing Manager/size-library URLs stay live (no retirement in M2).

**Explicitly NOT M2** (frozen order): Import Queue/Marker Plan/size
colors (M4) · DCT JS extraction (M4) · layering edge + gates (M6) ·
Layout Library station page (M5) · assistant (M7) · §18-d retirements
(owner-confirmed set, lands with M4/M5 nav work).

**Tests**: test_m2_studio.py (~20: rail stations/verdicts · tabs ·
checklist · conveyor · dxf/svg/dims adapters → proposals · refusals
recorded · trust-by-adapter · compare deltas · publish→next · QR panel ·
notches validate/stamp/twin · blueprint fields · evidence immutability ·
capture-creates-evidence) + model-pin +1 (EvidenceItem) + full serial
battery + makemigrations --check + lint-imports baseline.
