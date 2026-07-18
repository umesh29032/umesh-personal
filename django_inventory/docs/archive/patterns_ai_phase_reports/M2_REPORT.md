> **ARCHIVED 2026-07-13** — shipped-phase report/review (patterns_ai). Live truth: [PLATFORM_STATUS](../../AI_PATTERN_INTELLIGENCE/PLATFORM_STATUS.md) + [PRODUCT_VISION_V2](../../AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md) + the app [GUIDE](../../apps/patterns_ai/GUIDE.md). Kept for history (Phase-7 DOCCLEAN-D, D-OR-1). Outbound links reflect its era.

# M2 — PATTERN INTELLIGENCE STUDIO · implementation report
(2026-07-10 · executes UI_WORKFLOW_FREEZE §1/§2.1/§2.3/§2.4/§2.5/§3/§4
+ PRODUCT_DESIGN_FREEZE §7/§8/§18-g · plan: M2_IMPLEMENTATION_PLAN.md)

## Verdict
M2 delivered and verified. The Studio exists: one room, two modes, the
Acquisition Layer runs as ONE contract for every input, the dashboard
is the 5-station rail, adr-c.2 landed consciously. Spine untouched;
**zero production-app files changed** (no ADR-H exposure this
milestone); all writes still enter the single writers.

## What was built

**The rail (§2.1).** `dashboard.html` reworked: 5 stations with live
verdicts (pieces · designs/sizes-ready · DCT gate · active layouts ·
active layout contracts). "Pattern Manager" is no longer a station;
its URLs stay live.

**Browse mode = the shelf (§2.3).** `studio/?product=N[&size=]` —
size tabs (hierarchy law), CREATION CHECKLIST chips (the same
readiness truth that gates the DCT: ✓/✖ mandatory, ○ optional),
READY-FOR-CUTTING banner, todo-first shelf rows (preview · metadata ·
version+trust · [Open in Studio][History][DXF][SVG]), conveyor button
("Digitize next missing piece"). Mobile: browse/view-only — [Open in
Studio] hidden (owner carve-out honored in CSS).

**Work mode = the room (§2.4).** `studio/work/<piece>/<size>/` —
three panes: EVIDENCE STACK (add DXF · SVG · manual dims inline;
photo via phone hand-off; PDF/PNG/AI = honest-unavailable slots that
say why, no fake rows) · PROPOSAL CANVAS + COMPARE (2+ overlays
color-coded + delta table w/h/area/vertices/confidence; "comparison
informs, never auto-selects") · INSPECTOR (metadata chips incl.
notches-expected-vs-actual · confidence panel DISPLAY-ONLY · draft/
published state · Refine-outline link · Reopen-in-Studio copy-forward
· Verify & Publish tape dialog honestly listing EVERY size on the
draft · reference image). Publish success ADVANCES THE CONVEYOR to
the next missing mandatory design; when none remain → shelf with the
complete banner.

**The acquisition contract (§7) — machinery, not UI.**
- NEW `EvidenceItem` (migration 0012): the piece×size stack row —
  kind · kept original file (evidence is a fact; delete raises;
  updates single-writer-flagged) · status received/proposed/refused
  with recorded reasons. Writer: NEW `acquisition_service`
  (+ `next_missing_design` conveyor + `stack_for`).
- `GeometryExtraction` GENERALIZED additively: `capture` now nullable
  + nullable `evidence` FK — it is the ONE proposal store for every
  adapter (append-only + one-shot review machinery reused verbatim).
- Adapters (in `pattern_geometry_service`, the proposal writer):
  DXF → compute runtime import → proposal · SVG → NEW pure-python
  `svg_import.py` (polygon/polyline/M-L-H-V-Z paths, mm units,
  y-flip, CCW, µm ints; curves refuse with "export as DXF"; >1 shape
  refuses) · manual-dims → rectangle construct. Failures = RECORDED
  refusals (gate.passed=false + reasons), exactly like the photo gate.
- Photo capture now also joins the stack (same transaction) and the
  capture page accepts `?size=` preselect (QR target).
- `accept_extraction` stamps trust BY ADAPTER: photo→photo_calibrated,
  everything else→uncalibrated; tape-accepted confirm stays the ONLY
  path to measured.
- Confidence (§4): display-only dict — manual 100 · DXF 99 · SVG 95 ·
  photo per-run (existing computed metrics). Never a gate.

**Phone hand-off (§2.5).** Work mode → QR (qrcode lib, SVG inline) +
short link to the capture page with the size preselected; a 5 s poll
(`evidence-count` endpoint) reloads the desktop stack when the phone
uploads. Guided-frame TEXT ships (mat + border + flat); live
viewfinder overlay and multi-shot large-piece = future/reserved.

**adr-c.2 (§18-g — the stamp did its job).**
`GEOMETRY_CONTRACT_VERSION = 'adr-c.2'`; model default follows
(migration 0013); the constant=default pin test forced the conscious
edit exactly as designed. Validator TWINS (units.py + compute
runtime canonical.py, lockstep) accept optional typed
`features.notches` [{x_um,y_um,label?}] — absent = valid, so every
c.1 payload remains valid and old rows keep their stamp.
`edit_draft_geometry(notches=)` re-anchors notches with the outline;
the editor gained NOTCH MODE (click-to-place, click-to-remove).
Blueprint gained the two metadata slots `expected_notches` +
`seam_allowance_mm` (`set_piece_rules`, advisory display-only —
warnings explain, never modify).

## Proof
- **Tests: patterns_ai 448/448** (424 + 24 M2 — counts from output).
  **Full serial battery 1333/1333** (was 1309, +24 exact).
  `makemigrations --check` clean. import-linter baseline unchanged
  ("1 kept, 1 broken" — the known pre-existing test import).
- **Conscious test updates (all pre-existing invariants, updated with
  reasons in-code):** phase-1 dashboard steps → 5 stations · contract
  pin adr-c.1 → adr-c.2 (twice) · purity model pin +EvidenceItem ·
  FileField pin +models/geometry.py (kept-evidence philosophy) ·
  M2 conveyor-order expectation fixed in MY test (facade alphabetical
  order — code right, test wrong).
- **Browser (DEV data only, port 8003, minted session, dev.mgr):**
  DEV-P8B rail = 5 stations w/ REAL verdicts (1 layout, 1 contract —
  the 8B/8C artifacts). Full journey on DEV-P3B: shelf ✖ Front Panel →
  conveyor → work room (3 panes, QR rendered, honest-unavailable
  slots) → dims evidence ×2 (confidence 100, stack live) → COMPARE
  overlay + delta table (302×198 vs 300×200) → Use proposal → draft
  v1 → editor notch mode (notch placed, DB-verified re-anchored
  {x_um:150000,y_um:180726}, stamp adr-c.2) → Verify & Publish with
  tape 300/200 → trust MEASURED (delta 0.0), version CONFIRMED →
  conveyor verdict "every mandatory design confirmed" → shelf READY
  banner. Poll endpoint {"count":2}; capture page `?size=31`
  preselects. Mobile 390×844: [Open in Studio] hidden, browse works.
  Screenshots: m2_rail · m2_browse · m2_work_empty · m2_work_stack ·
  m2_work_compare · m2_editor_notch · m2_shelf_ready ·
  m2_mobile_browse (session scratchpad).
- Server log clean (no tracebacks; one expected 404 from a test id).

## Honest limits (in-scope choices, reported not hidden)
- Vertex refinement stays the existing editor SCREEN, linked from the
  room (depth 3 — within §16); full in-canvas re-skin = later polish.
- Reference ghost underlay on the proposal canvas: not yet (reference
  shows in the inspector).
- Phone flow v1 = guided text + QR + poll; live mat-detect viewfinder
  and multi-shot stitching remain future (owner's large-piece decision
  still open — UI slot reserved).
- Legacy DXF-import page + `import_dxf` API stay (frozen tests, direct
  drafts); the Studio path is the contract path. Fold-away rides the
  M4/M5 navigation retirements (§18-d, owner-confirmed set).
- DEV artifacts: DEV-P3B "Front Panel · Universal" now confirmed v1
  (300×200, 1 notch, measured) + 2 evidence rows — DEV-marked per the
  test-data rule. Golden T-SHIRT untouched.

## Migrations
0012 (EvidenceItem + extraction capture-nullable/evidence-FK +
piece expected_notches/seam_allowance_mm) · 0013 (contract default
adr-c.2). Both additive; applied locally.

**STOPPED — M2 complete. Next per frozen order: M4 (Marker Plan ·
Import Queue · size colors · DCT JS extraction · §18-d retirements).**
