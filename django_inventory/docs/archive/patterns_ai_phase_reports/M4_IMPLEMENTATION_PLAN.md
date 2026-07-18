> **ARCHIVED 2026-07-13** — shipped-phase report/review (patterns_ai). Live truth: [PLATFORM_STATUS](../../AI_PATTERN_INTELLIGENCE/PLATFORM_STATUS.md) + [PRODUCT_VISION_V2](../../AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md) + the app [GUIDE](../../apps/patterns_ai/GUIDE.md). Kept for history (Phase-7 DOCCLEAN-D, D-OR-1). Outbound links reflect its era.

# M4 IMPLEMENTATION PLAN — the Manufacturing Planner
(2026-07-10 · PLAN ONLY, no code until owner review · constitution:
PRODUCT_DESIGN_FREEZE + UI_WORKFLOW_FREEZE + MGE_MASTER_DESIGN +
M4_GENERIC_PLANNER_REVIEW + the owner's M4 directive of 2026-07-10 —
platform identity: **Manufacturing Knowledge Platform**; the DCT is
one tool inside it; the planner never knows the word "Nickkar".)

## 1 · COMPLETE BUSINESS WORKFLOW (factory first)

The real cutting-master workflow, digitized:
```
Order arrives → master picks FABRIC (roll: width, single/double/
tubular lay, nap) → decides WHICH PIECES this marker covers (Panel =
other fabric ⇒ its own marker; Body+Pocket may share) → decides the
SIZE MIX (e.g. 2×S 2×M 1×L per lay) → chalks the marker → layers →
cuts → bundles.
```
Digitized (M4):
```
Open DCT → MARKER PLAN dialog (the session opener):
  Manufacturing Strategy (optional preset — load or start blank)
  · fabric group (LAW 12) · roll → usable width (human-confirmed)
  · layering type single/double/tubular · sizes × garments-per-size
  · pieces included (mandatory of the group preselected; optional +
    exclusions = the strategy)
→ IMPORT QUEUE (auto-built from Blueprint × plan)
→ ARRANGE (physics, rules-gated) → AI OPTIMIZE (proposal)
→ SAVE DRAFT (plan recorded on the layout) → APPROVE
→ the Adda chooses it → layering suggestion (M6) → cutting advisory.
```
The knowledge the master carried in his head — which combinations,
which widths, which mixes — becomes REUSABLE STRATEGY ROWS + APPROVED
LAYOUTS. The company owns it (owner §6).

## 2 · UI WIREFRAMES

**Marker Plan dialog (opens every DCT session):**
```
┌─ MARKER PLAN · <product name> ──────────────────────────────┐
│ Strategy   [— blank session — ▾]  (e.g. "Panel marker · 42″")│
│ Fabric grp [body ▾]   Roll [R-0231 · 42″ ▾]                  │
│ Usable width [ 1040 ] mm  ← from roll, human-confirmable     │
│ Lay type   (•) Single  ( ) Double  ( ) Tubular               │
│   double/tubular ⇒ "each placement cuts 2 — pairs place once"│
│ Nap: one-way fabric ⇒ 180° rotation disabled (from roll)     │
│ Sizes      ☑ S [2]  ☑ M [2]  ☑ L [1]   (garments per lay)    │
│ Pieces     ☑ Body ×2  ☑ Pocket ×2  ☐ Label (optional)        │
│            [Start composing]        [Save as strategy…]      │
└──────────────────────────────────────────────────────────────┘
```
**Import Queue (left panel, replaces the palette name):**
```
IMPORT QUEUE                     S ●  M ●  L ●   (index colors)
S · 2 garments        4/6 imported
  Body     req 4 · imported 4 · remaining 0   [—]
  Pocket   req 4 · imported 0 · remaining 4   [Import]
  [Import all remaining · S]
M · 2 garments        0/6 imported …
OPTIONAL (opt-in)
  Label    [+ add to plan]
```
**Canvas:** pieces tinted by size-index color, labels `S · Body`;
legend chips in workspace meta; everything else = the frozen DCT.
**Mobile:** DCT stays desktop (frozen carve-out); choose/approve/
library rows stay the built mobile style.

## 3 · MARKER PLAN (component spec)
Session opener, required before composing (existing sessions w/o plan:
legacy open = blank plan prefilled from profile). Inputs above; LAW 12
group lock unchanged; width source order roll→profile→manual; ratio
recorded at save into run params (fills the registered `ratio: {}`
gap); plan is SESSION state (js) until save — zero writes before Save
Draft.

## 4 · MANUFACTURING STRATEGY (the new frozen concept)
**Definition: a NAMED, REUSABLE Marker Plan preset = manufacturing
knowledge as data.** Not engine logic; the engine never sees the name.
- Model `ManufacturingStrategy` (patterns_ai, additive): product FK ·
  name · fabric_group · layering_type · piece selection (ids + include
  flags) · size ratio JSON · optimize intent · notes · is_active ·
  created_by. Single writer: `strategy_service` (create/update/
  deactivate; no deletes).
- Owner's examples map: SEPARATE_PANEL/BODY_PLUS_POCKET = piece
  selection + group · SINGLE/DOUBLE/TUBULAR = layering type ·
  HIGH_UTILIZATION = optimize intent · EXPORT_ORDER = name/label.
- v1 scope (no over-engineering): load preset → prefills dialog;
  "Save as strategy" after filling; strategy label stamped into the
  saved layout's params (provenance: which strategy produced this
  asset). Nothing else.
**Genericity gate: strategy = rows; resolver output = pieces/rules/
width/layers/ratio. Engine input unchanged.**

## 5 · IMPORT QUEUE
Derived live from Blueprint × plan: required = pieces_count ×
garments(size) (×1 placement-wise on double lay — see §8); imported =
session count; remaining = max(0, req−imported). Over-import REFUSED
with the honest count. Optional pieces = separate opt-in list (join
the plan explicitly). [Import] = first-fit clear-spot (exists);
[Import all remaining] per size. Group lock unchanged.

## 6 · ROLL PLANNING (G4)
`ClothRoll` additive fields (raw_materials migration):
`usable_width_mm` (null) · `stretch_class` (choices none/2-way/4-way,
null) · `is_one_way_nap` (bool default False) · `selvedge_note`
(char, blank). Roll picker in Marker Plan lists ACTIVE rolls (code ·
nominal ″ · usable mm); picking prefills usable width — ALWAYS
human-confirmable (the legacy Marker's own law: "never trusted from
nominal inches"). Cross-app read: patterns_ai already imports
production models; raw_materials read = same direction — verify
import-linter contract in implementation; if the contract forbids,
fall back to a provider registration (production-side pattern,
inverted). Docs-sync: raw_materials GUIDE.

## 7 · LAYERING (input side)
Layering TYPE (single/double/tubular) = a Marker Plan input recorded
on the layout. The layering STAGE integration (suggested length =
marker length × operator's plies) stays M6 — unchanged, not smuggled
in.

## 8 · DOUBLE-LAYER LOGIC (G3)
`layer_multiplier` = 1 (single) / 2 (double/tubular), recorded in run
params at `save_table_layout` + surfaced by the provider. Effects:
- Import Queue required counts show PLACEMENTS: on double lay a pair
  (is_pair) needs HALF the placements (each placement cuts 2 mirrored
  pieces — mirror comes free from the fold of the lay). Non-pair
  pieces on double lay also cut ×2 per placement — required
  placements = ceil(required_pieces / multiplier), with the honest
  math shown in the queue row ("cuts 2 per placement").
- Expected math (8C): expected = content × multiplier × lay_count —
  `expected_pieces` gains the multiplier from layout params (default 1
  = today's behavior, byte-identical for existing layouts).
- Advisory bundle info = same derivation, persisted nowhere.
Genericity: multiplier = arithmetic on rows.

## 9 · NAP CONSTRAINTS (G5)
Roll `is_one_way_nap` ⇒ session flag: rotation sets narrowed
(TWO_WAY→[0], FREE→[0,90? NO — one-way = no 180-family: FREE→[0,90]
…decided: one-way removes 180 and 270, keeps 0/90 for FREE; TWO_WAY→
[0]; STRICT unchanged) + engine `allow_180=false` per piece. Honest
hint on the toolbar ("one-way nap: flips disabled"). Pure data
narrowing of the existing grain machinery.

## 10 · SIZE COLORS
Palette = fixed cycle assigned by SIZE-CHART ORDER INDEX (F4 binding:
never name-keyed): index%6 → blue/green/orange/violet/teal/rose
(tokens, distinct from the frozen semantic law colors in their usage
context: fills at low opacity + label chips). Canvas piece tint +
`S · Body` labels + legend in meta row + queue headers.

## 11 · DCT WORKSPACE LAYOUT
Unchanged frozen geometry (toolbar order · left panel · canvas hero ·
meta bar). Left panel renamed **Import Queue** (freeze §18-c). Plan
summary chip row under the toolbar (group · roll · width · lay type ·
strategy name) — read-only session facts, one line.

## 12 · KEYBOARD SHORTCUTS
Existing frozen set unchanged (R rotate · M mirror · L lock · Del ·
Ctrl+Z · arrows 1mm/Shift 10mm · 0 zoom-reset). M4 adds: `I` = import
next remaining (queue order) · `G` = toggle grid. No conflicts;
documented in a `?` hint popover (static list).

## 13 · DESKTOP INTERACTION MODEL
Canvas hero; no page reloads mid-session (plan dialog + queue + save
= same page; approve stays its own review page per freeze); zoom =
camera only; fabric width visually stable; every refusal names the
fix. Session undo covers imports/moves/rotates/locks (existing stack).

## 14 · MOBILE INTERACTION MODEL
DCT = desktop-first (frozen carve-out). Mobile keeps: view-only layout
rows, choose page, approve review (read + confirm button), library.
No CAD on phones. Marker Plan dialog functional-but-not-optimized on
mobile (standard form controls, 44px targets).

## 15 · DATA FLOW
```
Blueprint(rules,counts) ──┐
ClothRoll(+G4 fields) ────┤→ MARKER PLAN (session, js state)
ManufacturingStrategy ────┘        │ prefill/save preset
                                   ▼
                    IMPORT QUEUE (derived, live)
                                   ▼
                    session placements (runtime objects)
                                   ▼ Save Draft
save_table_layout(params += ratio·layering_type·layer_multiplier·
roll_ref·strategy_label) → candidate → Approve → ApprovedLayout
                                   ▼ provider (content only + multiplier)
production: choose → suggestion = content×multiplier×lay_count (8C′)
```
Zero writes before Save Draft (law). Expected numbers persisted
nowhere (law).

## 16 · SERVICES
- NEW `strategy_service` — single writer for ManufacturingStrategy.
- `marker_generation_service.save_table_layout` — EXTENDED params
  (ratio, layering_type, layer_multiplier, roll reference,
  strategy_label). Same verifier, same pipeline.
- `layout_usage_service.expected_pieces` — × multiplier (default 1).
- `layout_panel_provider` — + multiplier + plan facts (content stays
  plies-free; multiplier is a LAYOUT fact, not a plies fact —
  asserted).
- production `cutting/service.py` suggestion math — × multiplier
  (read from provider dict; fallback unchanged).
- NO new money paths; no ledger/costing contact.

## 17 · MODELS
- `ManufacturingStrategy` (patterns_ai) — §4 fields, active-flag soft
  state, no deletes.
- `ClothRoll` +4 additive fields (raw_materials) — §6.
- NO changes to ApprovedLayout/Usage/geometry models (plan facts live
  in run/candidate params — existing JSON, no migration).

## 18 · MIGRATIONS
patterns_ai 0014 (ManufacturingStrategy) · raw_materials +1 (roll
fields). Both additive, defaults safe, reversible.

## 19 · TESTS (planned ~24)
Strategy: create/update/deactivate · prefill resolve · stamp on save ·
model pin +1 (conscious). Marker Plan: required-before-compose ·
width source order · LAW 12 unchanged. Queue: required math single vs
double (pair + non-pair) · over-import refusal · optional opt-in ·
import-all. Colors: index-cycle on a NON-S/M/L chart (28/30/32) —
genericity proof. G3: multiplier recorded · expected ×2 · legacy
layouts byte-identical (golden ₹225 + existing 8C tests untouched).
G4: roll fields + picker read. G5: nap narrows rotations + engine
allow_180=false. Retirements: generate link gone · redirect priority ·
★ surface gone. JS extraction: page serves static file, behavior tests
re-run. Genericity gate test: grep-style guard (no garment names in
non-test patterns_ai/compute python — automated F5 wall). Full serial
battery + makemigrations --check + lint-imports baseline.

## 20 · BROWSER VERIFICATION (DEV only)
Create **DEV-NICKAR** (owner's real example, as TEST DATA): Blueprint
Body ×2 pair (body group) · Panel ×2 pair (OTHER group — forces the
separate-panel marker via LAW 12, exactly the real factory) · Pocket
×2 (body). Geometry via Studio (dims/SVG adapters). Then: plan a
body-group marker on a double-lay roll (Body+Pocket, S/M mix) →
queue math (pairs place once) → compose → save → approve → strategy
saved ("Body+Pocket · double") → second session loads strategy →
separate Panel marker → choose page on a DEV Adda → suggestion shows
×2×lay math. Screenshots per station + mobile choose page. Golden
T-SHIRT untouched.

## 21 · RISKS
- Double-lay pair math (the subtlest logic): mitigated by explicit
  queue wording ("cuts 2 per placement") + the pair/non-pair test
  matrix + operator numbers remaining authority everywhere.
- Legacy layouts must be unaffected: multiplier defaults 1;
  byte-identical assertions on existing goldens.
- Cross-app raw_materials read: verify import-linter direction before
  wiring; provider fallback ready.
- ★ redirect-priority swap changes ToolRedirectView behavior: covered
  by conscious test update + report.
- Scope size: 6 components — internally staged (plan→queue/colors→
  G3→G4/G5→retirements/JS), ONE report, battery after each stage.

## 22 · ACCEPTANCE CRITERIA
Marker Plan opens every session and records into the saved layout ·
queue counts correct single AND double (pair + non-pair) · over-import
refused · size colors correct on a numeric size chart · expected math
× multiplier, legacy unchanged · roll picker + confirmed width · nap
disables flips · generate/★/research out of navigation · DCT JS in a
static file, all interactions identical · battery green (counts
verified) · DEV-NICKAR browser journey complete with screenshots ·
genericity guard test green.

## 23 · GENERICITY GATE (per component)
| Component | Inputs | Garment knowledge |
|---|---|---|
| Marker Plan | product sizes, group enum, roll row, lay enum | none |
| Strategy | rows (name = label, engine-invisible) | none |
| Import Queue | Blueprint counts × plan | none |
| Size colors | size-chart ORDER INDEX | none |
| G3 multiplier | arithmetic | none |
| G4/G5 | roll fields | none |
| Engine | polygons + allow_180/allow_mirror/spacing | none (unchanged) |
Plus the automated guard test (§19) making this gate permanent.

## 24 · M4.5 SEPARATION (fold stays out)
Fold placement (G1) = its OWN milestone after M4: payload `fold_edge`
(reserved slot; adr-c.3 if payload shape changes) · half-piece-on-fold
DCT physics · engine support · readiness law stops blocking `on_fold`
· its own plan/battery/browser/report. Nothing in M4 pre-builds fold
beyond the layering-type field (which M4.5 will reuse).

---
**STOPPED — plan delivered, no code. On your review + approval, M4
implementation begins: one milestone · one report · one verification ·
one stop. Everything additive, deterministic, generic,
manufacturing-first.**

---
## OWNER APPROVAL + REFINEMENTS (2026-07-10 — binding for M4)
**APPROVED — implementation begins.** Ten refinements accepted:
R1 UI says **"Marker Recipe"** (model stays ManufacturingStrategy) ·
R2 LIVE session estimates before save (width · length · utilization ·
waste · expected pieces = content×multiplier, client-side) ·
R3 **Layout Notes** at save (params.notes → library/approve display) ·
R4 Import Queue rows carry RULE CHIPS (required · mirror · fold ·
rotation · imported — the operator sees WHY) ·
R5 AI button = **"Suggest Better Layout"** (never "Optimize") ·
R6 AI verdict = explained comparison (current vs suggested: length/
util/waste saved · pieces moved · [Accept suggestion]/[Keep current])
— explanations, never magic ·
R7 3-pane direction confirmed (queue · canvas · inspector-lite) ·
R8 **Factory Simulation = FUTURE backlog** (marker × layers × width →
expected pieces/fabric/waste/cost) — recorded, NOT M4 ·
R9 fold stays M4.5 ·
R10 **PERMANENT LAW — REPRODUCIBILITY: everything reaching the Layout
Library is reproducible. Same geometry + recipe + roll + width +
rules ⇒ same result (manual arrangement and explicitly-accepted AI
proposals are the only variation sources). Nothing magical, hidden or
random.** Engines already deterministic + seeded (locked rule ⑩);
this elevates it to a library-boundary law.
Discipline: one internal stage at a time, verification after each,
zero scope beyond this plan.
