> **ARCHIVED 2026-07-13** — shipped-phase report/review (patterns_ai). Live truth: [PLATFORM_STATUS](../../AI_PATTERN_INTELLIGENCE/PLATFORM_STATUS.md) + [PRODUCT_VISION_V2](../../AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md) + the app [GUIDE](../../apps/patterns_ai/GUIDE.md). Kept for history (Phase-7 DOCCLEAN-D, D-OR-1). Outbound links reflect its era.

# PHASE 2 PLAN — the Pattern Blueprint module
(2026-07-09 · PLAN ONLY — no code until owner approval · implements the
responsibility freeze: PLATFORM_RESPONSIBILITY_FREEZE.md)

## Goal

The Blueprint becomes a REAL module: the single surface where the
product's structure lives — every piece + every rule (count · required/
optional · pair/mirror · fold · **grain rule** · fabric group) — and the
two freeze violations (V-1 piece-registration on the Library, V-2
optional-toggle on Library rows) migrate home.

## The one structural decision — D-1 (needs your yes/no)

**The Blueprint module page moves INTO `patterns_ai`**
(`patterns_ai:blueprint?product=N`), replacing the production-side
editor page. Why:
- The atomic "Add Pattern Definition" (one action → library pattern +
  assignment + PatternPiece with rules) must call `create_piece` — a
  patterns_ai single-writer. A production view cannot import it
  (ADR-H). patterns_ai importing production models is the ALLOWED
  direction (its FKs already do).
- The Dashboard is the permanent home; its STEP-1 card should open a
  module INSIDE the platform, like STEP 2 and 3.
- Production keeps `product-pattern-blueprint` as a redirect (same
  pattern as `product-patterns` → dashboard), so no link breaks.
Perm: the module keeps the OLD editor's strict gate
(`production.change_productpattern` via `user_has_perm`, super-admin
bypass) — structure edits stay admin-level; nothing loosens.

## Scope

1. **`grain_rule` on `PatternPiece`** — migration patterns_ai **0009**
   (additive): TextChoices `STRICT` (place on grain, 0° only) ·
   `TWO_WAY` (180° allowed) · `FREE` (any rotation). **Default
   `TWO_WAY`** — matches today's actual behavior (the workspace rotates
   180°-only), so the backfill tells no lies.
2. **Blueprint page** (`patterns_ai/templates/patterns_ai/blueprint.html`):
   one row per piece — name · count (assignment `pieces_count`) ·
   required/optional · pair · fold · grain · fabric group — all
   editable in place; **atomic “+ Add Pattern Definition”** form
   (name + count + rules → ONE transaction: `ProductPattern`
   get-or-create by name → assignment → `create_piece` with rules);
   remove piece = REFUSED with honest reason if any version/design
   exists (append-only history), else removes piece + assignment.
   Header = STEP-1 vocabulary; ← Dashboard; STEP 2 hand-off. Mobile:
   stacked rows, data-labels.
3. **New single-writer functions** (in `pattern_geometry_service`,
   nowhere else): `set_piece_rules(*, user, piece, is_pair=…, on_fold=…,
   grain_rule=…, fabric_group=…)` (validated choices; optional stays in
   the existing `set_piece_optional`) ·
   `register_pattern_definition(*, user, product, name, pieces_count,
   **rules)` (the atomic add, `transaction.atomic`) ·
   `remove_pattern_definition(*, user, piece)` (refuse-if-designs).
   Count edit = assignment update inside the service (crossing to
   production models is the allowed direction).
4. **V-1/V-2 migration**: Library loses “+ Add Pattern Design” and the
   optional-toggle; rows gain a quiet pointer “structure & rules live
   in the Blueprint”. Reference add/replace/remove STAYS (documentation,
   per the freeze census).
5. **Wiring**: Dashboard STEP-1 card + Blueprint-page hand-offs →
   `patterns_ai:blueprint`; production `product-pattern-blueprint`
   becomes a redirect to it; the old production editor template
   retires (its safe-parse behavior moves into the new form/service
   validation).
6. **Facade**: rows already expose `checks`/badges; add `grain_rule` +
   `fabric_group` to the row contract (contract-ADDITIVE — CT will need
   both as placement constraints).

## NOT in Phase 2
Universal size + archive guard (Phase 3, owner's order) · any DCT work ·
per-size requiredness (registered future) · fabric spec master (DCT
phase) · reference-image ownership change (stays with preparation).

## File touch list (~12 + 1 migration)
patterns_ai: `models/pieces.py` (+grain_rule) · migration 0009 ·
`pattern_geometry_service` (+3 functions) · `views.py`
(+BlueprintView) · `urls.py` (+blueprint/) · `templates/blueprint.html`
(NEW) · `dashboard.html` (STEP-1 target) · `size_library.html` +
`_design_row.html` (V-1/V-2 removal + pointer) ·
`pattern_design_facade.py` (row +grain/fabric_group) · tests (NEW
`test_phase2_blueprint.py`; conscious updates: `test_pdm_w2`
manage-in-place tests, `test_pattern_pieces_count` re-targets the new
form, `test_phase1_dashboard` STEP-1 target).
production: `urls.py`/`pattern_views.py` (blueprint route → redirect;
old editor view + template retire) · docs (both GUIDEs + report).

## Risks
- R-1 `create_piece` currently takes rules at create — atomic function
  reuses it verbatim (no signature change; grain passes through a new
  kwarg with the same default).
- R-2 removing the old editor = 3 POST actions (add/remove/
  update_count) must ALL exist on the new page before retirement —
  acceptance covers each.
- R-3 fabric-group/grain edits after designs exist: allowed (constraint
  metadata; geometry untouched) — layout staleness machinery arrives
  with the DCT phases, noted not built.
- R-4 test drift: every changed assertion carries a "Phase 2" comment.

## Acceptance criteria
1. Blueprint page shows every piece with all 6 rules + count; each
   editable in place; strict perm enforced; worker 403.
2. Atomic add: one form → pattern + assignment + piece (with rules) in
   one transaction; duplicate name → honest error; safe-parse on count
   preserved.
3. Remove: refused with reason when designs exist; clean removal when
   none.
4. Library no longer registers pieces or toggles optional; pointer to
   Blueprint present; reference management still works.
5. Dashboard STEP-1 opens the module; production blueprint URL
   redirects; no broken links (redirect chain tested).
6. Facade rows carry `grain_rule` + `fabric_group` (additive; existing
   keys untouched).
7. `makemigrations --check` clean after 0009; battery green (counts
   from output); browser desktop + 390×844 walkthrough with
   screenshots.

---
**STOP — Phase-2 plan delivered. No code. Awaiting your approval
(including D-1: Blueprint module lives in patterns_ai).**
