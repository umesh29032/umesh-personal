> **ARCHIVED 2026-07-13** — shipped-phase report/review (patterns_ai). Live truth: [PLATFORM_STATUS](../../AI_PATTERN_INTELLIGENCE/PLATFORM_STATUS.md) + [PRODUCT_VISION_V2](../../AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md) + the app [GUIDE](../../apps/patterns_ai/GUIDE.md). Kept for history (Phase-7 DOCCLEAN-D, D-OR-1). Outbound links reflect its era.

# M4 — THE MANUFACTURING PLANNER · implementation report
(2026-07-10 · executes M4_IMPLEMENTATION_PLAN.md + owner refinements
R1–R10 · one milestone, one report, one stop)

## Verdict
M4 delivered and verified end-to-end on the owner's REAL example
(DEV-NICKAR: Body ×2 pair + Pocket ×2 on body fabric, Panel ×2 pair on
OTHER fabric). The DCT is now a Manufacturing Planner: every session
opens with a MARKER PLAN, the queue does the placement math the
cutting master does in his head, and the plan persists into the saved
asset. The engine still doesn't know what a Nickar is — and now a
TEST guarantees it never will.

## What was built (per plan section)
- **Marker Plan dialog (§2/§3)** — session opener: Marker Recipe (R1
  wording) · fabric group (LAW 12) · roll picker → usable width
  human-confirmed ("never trusted from nominal inches") · lay type
  single/double/tubular with the honest note ("each placement cuts 2 —
  pairs come mirrored by the lay") · sizes × garments-per-lay · piece
  selection (mandatory preselected, optional opt-in) · layout notes
  (R3). Session state only — zero writes before Save Draft.
- **Marker Recipe (§4)** — `ManufacturingStrategy` (migration 0014) +
  `strategy_service` single writer (save = update-by-name; never
  deleted, deactivate only) + `table/<pk>/recipe/` endpoint. Load
  prefills the dialog; the saved layout stamps which recipe produced
  it (provenance = owned knowledge). The engine never sees the name.
- **Import Queue (§5/§8)** — required placements =
  ceil(Blueprint count × garments ÷ multiplier); rule chips (R4):
  req · in · mirror ✓ · rot 0/180° · fold · "cuts 2/placement";
  over-import refused with the count; optional pieces refuse until
  added to the plan; [Import all remaining] + `I` key; `G` = grid.
- **G3 double-lay math** — `layer_multiplier` (single 1 ·
  double/tubular 2) recorded in save params; `marker_content` =
  placements × multiplier PER LAID LAYER; provider applies per-usage;
  production's expected math unchanged (content × lay_count). Legacy
  layouts (no key) → multiplier 1, byte-identical (tested).
- **G4 roll metadata** — ClothRoll + usable_width_mm · stretch_class ·
  is_one_way_nap · selvedge_note (raw_materials 0011, additive;
  import-linter verified: patterns_ai = top layer, read-down legal).
- **G5 nap** — one-way roll ⇒ rotation sets narrowed (TWO_WAY→[0],
  FREE→[0,90]) in selbar/R-key/engine (`allow_180=false`); honest
  hints name the fabric as the reason.
- **Size colors (§10)** — palette cycles by SIZE-CHART ORDER INDEX
  (F4: proven in tests on a numeric 28/30 chart); canvas tint yields
  to the semantic physics paint (red/amber/violet/grey keep
  authority); labels size-first `S · Nickar Body`; queue headers
  carry the dots.
- **Live estimates (R2)** — Expected Pieces (placements × multiplier,
  "/ layer") · Waste % · Ratio · width — all live before save; the
  Layout Information Cut Plan/Ratio slots finally light up.
- **"Suggest Better Layout" (R5/R6)** — button reworded; the engine
  result is now a PENDING PROPOSAL with an explained verdict:
  "Current: 54.2% · 880 mm → Suggested: +25.4% utilization, −278.8 mm
  (waste saved 25.4%). 6 piece(s) would move; locked stay." +
  [Accept suggestion]/[Keep current]. Nothing auto-applies. Engine
  contract untouched (presentation change only).
- **§18-f** — the ~740-line inline DCT engine moved VERBATIM to
  `static/patterns_ai/dct.js` (+M4 features); template hands over
  DATA only (ws-config/ws-payload); collectstatic manifest updated.
- **§18-d retirements (owner-confirmed)** — Generate link off the DCT
  toolbar; home page → Dashboard-only nav (manual-marker/generate/
  library links out); `ToolRedirectView` new priority: ready →
  Cutting Table · pieces → Studio · else → Blueprint (★ designation +
  generator workspace no longer steer). All legacy pages stay LIVE at
  their URLs; data untouched.
- **Genericity guard (§23)** — a PERMANENT test: garment-name regex
  over all non-test patterns_ai + compute code (venv/migrations
  excluded; 1-entry allowlist for the known cosmetic help-text).
  The wall is now automated, not a one-time audit.
- **R10 reproducibility** — recorded as the library-boundary law in
  the plan; engines were already deterministic + seeded (rule ⑩).

## Proof
- **Tests: patterns_ai 463/463** (448 + 15 M4). **Full serial battery
  1348/1348** (1333 + 15 — counts from output). makemigrations clean;
  import contracts baseline ("1 kept, 1 broken", pre-existing).
- **Conscious test updates (all documented in-code):** phase-4/5/6
  template-string tests now read the static dct.js (behavior
  unchanged, home moved) · palette test → queue + payload-data
  assertions · AI wording · Generate-link assertions inverted ·
  phase-6-M4 smart-redirect table REWRITTEN to the §18-d priority ·
  model pin +ManufacturingStrategy.
- **Browser (DEV-NICKAR, port 8003, dev.mgr):** plan dialog (recipe/
  roll/width/lay/sizes/pieces/notes — wireframe-exact) → roll pick
  prefilled 1040 mm → double lay S×2 M×1 → queue math EXACT (Body·S
  req 2 = 4 pieces ÷ 2; chips mirror ✓ · rot 0/180° · cuts
  2/placement) → import all (6 placed · 0 remaining · Expected 12/layer
  · waste live · ratio S×2 M×1 · 6 size-tinted pieces · `S · Nickar
  Body` labels) → `I` key honest refusal ("queue complete") →
  Suggest Better Layout → explained verdict + Accept → 79.6%
  utilization → recipe saved ("Body+Pocket · double · 42″") → Save
  Draft → **DB-verified params: lay double · mult 2 · ratio {S:2,M:1}
  · roll CR-DEV-M4A · notes** → approved **LAY-DEV-NICKAR-000001**
  (ACTIVE) with content/layer {S:8, M:4} = the G3 math on a real
  asset → recipe reload prefills a fresh session → one-way roll
  (CR-DEV-M4B): chip "one-way nap — flips disabled", rotate disabled
  with the fabric named → **Panel marker: group OTHER → queue = Panel
  only** — the real factory's separate-panel marker falls out of
  LAW 12, zero new code. Screenshots: m4_plan_dialog ·
  m4_queue_imported · m4_suggest_verdict · m4_recipe_loaded ·
  m4_nap_oneway · m4_panel_marker · m4_dct_clean.

## Honest notes
- **Caught + fixed during browser verify:** multi-line `{# #}`
  comments leaked as page text (the KNOWN regression, my own standing
  rule) — all 5 converted, battery re-run green, clean screenshot
  taken. Also: the first approve attempt hit the sidebar Sign-Out
  form via a lazy selector (my browser-driving bug, not app code) —
  re-done against the real approve form.
- Engine optimize requires spacing 0.5–50 mm (pre-existing contract):
  products without a fabric-profile spacing get an honest refusal from
  the suggestion — DEV-NICKAR got a profile (3.0 mm) as data, no code
  bend.
- Approve review page name field: layout named at approval as before;
  recipe/notes live in params (library-row display of notes = M5
  polish item).
- DEV artifacts: DEV-NICKAR (product 23, 3 pieces × S/M confirmed,
  profile 3.0 mm), rolls CR-DEV-M4A/M4B, recipe "Body+Pocket · double
  · 42″", LAY-DEV-NICKAR-000001 ACTIVE + one un-approved draft. Golden
  T-SHIRT untouched.

## Migrations
patterns_ai 0014 (ManufacturingStrategy) · raw_materials 0011 (roll
planning fields). Additive; applied locally.

**STOPPED — M4 complete. Next per frozen order: M4.5 (fold placement
— its own plan first) on your go.**
