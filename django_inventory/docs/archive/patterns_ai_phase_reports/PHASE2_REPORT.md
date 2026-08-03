> **ARCHIVED 2026-07-13** — shipped-phase report/review (patterns_ai). Live truth: [PLATFORM_STATUS](../../AI_PATTERN_INTELLIGENCE/PLATFORM_STATUS.md) + [PRODUCT_VISION_V2](../../AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md) + the app [GUIDE](../../apps/patterns_ai/GUIDE.md). Kept for history (Phase-7 DOCCLEAN-D, D-OR-1). Outbound links reflect its era.

# PLATFORM · PHASE 2 REPORT — the Pattern Blueprint module
(2026-07-09)

**Status: ✅ PHASE 2 COMPLETE — STOPPED. Phase 3 (Universal Size) will
not start without approval.**

Implemented the approved Phase-2 plan exactly (all owner approvals:
D-1 · grain_rule TWO_WAY · atomic API as the ONLY definition-create
path · V-1/V-2 cleanup · facade additions).

## What shipped

**1 · The Blueprint module** (`patterns_ai:blueprint?product=N` — D-1,
lives in the platform; production launches it). One row per piece:
name + REQUIRED/OPTIONAL + fabric-group chips · in-place editors for
**all 6 rules** (fabric group · grain rule · pair · fold · count/garment
· optional) · Remove. "Not registered" continuity rows for old-editor
assignments with one-click register. STEP-1 vocabulary, ← Dashboard,
STEP-2 hand-off. Strict gate = the old editor's
`change_productpattern` (super-admin bypass) — nothing loosened.
Mobile: stacked, full-width controls.

**2 · `grain_rule`** — migration patterns_ai **0009** (additive):
STRICT (on grain, 0°) · TWO_WAY (180°, DEFAULT — matches the
workspace's actual 180°-only behavior, backfill tells no lies) · FREE.

**3 · The atomic API** — `register_pattern_definition` in
`pattern_geometry_service` = **the ONLY public write API for creating
Pattern Definitions**: ONE transaction → ProductPattern (get-or-create
by name) → assignment (pieces_count) → PatternPiece (rules). Blank/
duplicate names refused honestly, no partial rows (tested). Plus
single-writer setters: `set_piece_rules` (validated choices),
`set_piece_count` (count lives on the assignment — one truth),
`remove_pattern_definition` (REFUSED with reason if any design history
exists — append-only law; clean removal also removes the assignment).

**4 · V-1/V-2 migrated (freeze census closed).** The Library lost
“+ Add Pattern Design” (piece-new URL + `PieceCreateView` +
`PieceCreateForm` + template RETIRED) and the optional-toggle (the
Manager's `set_optional` POST action removed — posting it now writes
NOTHING, tested). Library rows keep reference management
(documentation) + gained a pointer to the Blueprint. The smart
redirect's "register" branch → Blueprint.

**5 · Facade additive**: rows now carry `grain_rule` + `fabric_group`
(future DCT placement constraints); `design_key` and all prior keys
untouched.

**6 · Production side**: `product-pattern-blueprint` → redirect to the
module; `ProductPatternsEditView` + its template retired (all 3 POST
actions live on the Blueprint); ADR-H boundary test upgraded to sweep
EVERY production view file for patterns_ai imports.

## Tests
NEW `test_phase2_blueprint.py` (12): atomic add w/ rules · duplicate/
blank refused w/ no partial rows · register-unregistered continuity ·
rules/count/optional round-trips · bad grain refused (default intact) ·
remove refused-with-history · clean remove drops assignment · worker
403 + zero-GET-writes · production redirect · facade additive keys ·
Library lost V-1/V-2, kept reference.
Conscious updates (each commented "Phase 2"): `test_phase6_m4` (register
redirect → blueprint; blueprint URL followed; boundary test → all-view
sweep), `test_phase6_m6` (toggle + tamper wall + register → `_bp_post`;
Manager refuses retired action), `test_pdm_w2` (labels; set_optional
now writes nothing; vocabulary follows redirect),
`test_phase1_dashboard` (STEP-1 target), `test_pattern_pieces_count`
(safe-parse guarantee re-homed to the Blueprint add).
One fix during the run: my new blank-name test logged in AFTER posting
(test bug, not app bug).

## Battery (counts from output, serial, fresh)
- patterns_ai: **366/366 OK** (354 + 12 new — exact).
- Full suite incl. storefront: **1251/1251 OK** (1239 + 12 — exact).
- `makemigrations --check`: **No changes detected** (after 0009).
- Import contracts: **1 kept, 1 broken — pre-existing baseline**.

## Browser (live, T-SHIRT, server restarted, minted session)
- Blueprint module: 8 real pieces w/ chips (Back Panel REQUIRED·BODY,
  Brand/Care Label OPTIONAL·TRIM…), rules editors live, FancySelect
  auto-upgrade ✓ (`p2_blueprint_desktop.png`).
- Dashboard STEP-1 → the module (`step1-target: OPEN BLUEPRINT`).
- Library L: add-button GONE · make-optional GONE · reference actions
  PRESENT · Blueprint pointer PRESENT (js-verified booleans).
- Mobile 390×844: stacked rows, full-width 44px controls
  (`p2_blueprint_mobile.png`).
- No live writes against T-SHIRT (golden data untouched; write paths
  proven by the suite).

## Docs-sync (rule 12)
patterns_ai GUIDE (+3 rows) · production GUIDE (Phase-1+2 note,
retirement recorded) · this report · PLATFORM_RESPONSIBILITY_FREEZE.md
census now CLOSED (V-1/V-2 migrated).

**STOPPED — Phase 2 complete and verified. Awaiting owner review +
Phase 3 approval (Universal Size workflow: lazy materialization +
archive guard + Product Size polish).**
