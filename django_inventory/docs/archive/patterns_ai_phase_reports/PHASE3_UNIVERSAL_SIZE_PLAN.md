> **ARCHIVED 2026-07-13** — shipped-phase report/review (patterns_ai). Live truth: [PLATFORM_STATUS](../../AI_PATTERN_INTELLIGENCE/PLATFORM_STATUS.md) + [PRODUCT_VISION_V2](../../AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md) + the app [GUIDE](../../apps/patterns_ai/GUIDE.md). Kept for history (Phase-7 DOCCLEAN-D, D-OR-1). Outbound links reflect its era.

# PHASE 3 PLAN — Universal Size workflow + archive guard
(2026-07-09 · PLAN ONLY — no code until owner approval · engineering
mode; everything below solved INSIDE the frozen architecture)

## Goal (frozen spec)
Every product entering pattern preparation always has ≥1 active size:
a product with no sizes automatically gets **Universal** (a REAL
`ProductSize`, `code='universal'`). Real sizes may be added later;
Universal may then be archived — but **never silently destroying the
only design set** (the owner-approved archive guard).

## Ground truth (verified)
- `production/services/product_size_service.py` already exists — sizes
  have a single writer (`add/update/archive/reactivate_product_size`);
  the Sizes page dispatches into it. Guard hooks THERE, not in views.
- `PieceSizeGeometry.size` is PROTECT — hard-delete already impossible;
  the gap is soft-archive (`is_active=False`), exactly as planned.
- Zero-GET-writes is a tested law on every platform page — Universal
  can never materialize on a GET.

## Design decisions (3, each solved inside the frozen walls)

**D-1 · WHEN Universal materializes (two write-moments, GET stays pure):**
1. **Auto** — `register_pattern_definition` (the ONLY definition-create
   API) on a product with zero active sizes creates Universal inside
   the same transaction: the moment structure begins, the preparation
   universe exists. This is the owner's "automatically create".
2. **Explicit** — the Manager/Dashboard "no sizes yet" states gain a
   one-tap **[Start with Universal]** button (POST) for products that
   already have structure but no sizes (legacy/edge). No hidden work
   (Rule I): the button says exactly what it does.

**D-2 · WHO creates Universal — production keeps size ownership.**
New tiny function `ensure_universal_size(product)` in
`production/services/product_size_service.py` (the existing single
writer — sizes stay production-owned, frozen law intact). patterns_ai
CALLS it (patterns_ai→production import = the allowed direction, same
as assignment writes in Phase 2). No new module, no ownership move.

**D-3 · Archive guard without breaking the ADR-H wall.**
Problem: the guard needs patterns_ai knowledge ("does this size hold
the product's only confirmed designs?") but lives in production's
writer, and production can never import patterns_ai.
Solution — **validator registry (dependency inversion, ~10 lines):**
`product_size_service` gains `ARCHIVE_VALIDATORS = []` and
`archive_product_size` runs each validator (raising ValidationError
blocks the archive with its honest message). `patterns_ai/apps.py
ready()` APPENDS its guard — patterns_ai imports production (allowed);
production imports nothing (wall intact; the boundary sweep test stays
green). Guard rule (owner-approved wording): **refuse archiving a size
that holds confirmed designs while NO OTHER active size has confirmed
designs** — error names the honest paths ("confirm designs in another
size first, or add sizes and prepare them"). Applies to every size,
Universal included.

## Scope
1. `ensure_universal_size(product)` — idempotent; creates/reactivates
   `ProductSize(code='universal', label='Universal', display_order=0)`;
   returns existing when present.
2. Auto-materialize inside `register_pattern_definition` (zero active
   sizes → ensure Universal, same transaction).
3. `ARCHIVE_VALIDATORS` registry + guard registered from
   `patterns_ai.apps.ready()` (module-path string import, no cycle).
4. **[Start with Universal]** button on the Manager's no-sizes state +
   the Dashboard's no-sizes line (POST to a small patterns_ai action →
   `ensure_universal_size`; then straight into normal flow).
5. Sizes-page polish (minimal, no over-engineering): archive errors
   from the guard surface as the existing message pattern; Universal
   row renders like any size. NOT DONE deliberately: per-size design
   status on the Sizes page (would need patterns_ai data in a
   production template — wall says no; the Manager already shows it).

## NOT in Phase 3
DCT anything (P4+) · per-size requiredness · "copy Universal designs
into new sizes" migration helper (registered future — the guard's
block-with-reason covers v1; copying = a later convenience) · grading.

## File touch list (~9)
| File | Change |
|---|---|
| `production/services/product_size_service.py` | `ensure_universal_size` + `ARCHIVE_VALIDATORS` + run-loop in `archive_product_size` |
| `patterns_ai/apps.py` | `ready()` registers the confirmed-designs guard |
| `patterns_ai/services/pattern_geometry_service.py` | `register_pattern_definition`: zero-active-sizes → `ensure_universal_size` (same transaction) |
| `patterns_ai/views.py` | small `start_universal` POST action (Manager/Dashboard button target; strict = management role, same as pages) |
| `patterns_ai/templates/patterns_ai/piece_list.html` | no-sizes state + [Start with Universal] |
| `patterns_ai/templates/patterns_ai/dashboard.html` | no-sizes line + same button |
| tests: NEW `patterns_ai/tests/test_phase3_universal.py` | see below |
| conscious updates | `test_pdm_w2` no-sizes state assert (+button) · production size-service tests if any assert archive unconditionally |
| docs | both GUIDEs + report |

Zero migrations (Universal = data convention on the existing model).

## New-test coverage
Auto-materialize on first definition (sizeless product → Universal
exists, one row, idempotent on second add) · explicit button (POST
creates; GET never does; worker 403) · reactivate-not-duplicate (archived
Universal + button → reactivated, no second row) · guard: archiving the
only confirmed-design size REFUSED with honest message (Universal and
non-Universal both) · archiving allowed when another active size has
confirmed designs · archiving a design-less size always allowed ·
guard error surfaces on the Sizes page flow · registry: production
imports clean (boundary sweep already asserts) · zero-GET-writes
retained on both touched pages.

## Risks
- R-1 `ready()` import timing — registry import at app-ready is the
  standard Django hook; validator imports models lazily inside the
  function body (no app-loading cycle).
- R-2 `code='universal'` collision with a user-created size of the same
  code — `ensure_universal_size` adopts it (same code = same meaning;
  idempotent by code).
- R-3 guard false-block (product with confirmed designs ONLY on the
  size being archived but the operator genuinely wants it gone) —
  by design: block-with-reason is the owner-approved honest path;
  copy-forward convenience = registered future.
- R-4 conscious test drift — no-sizes state changes one W2R assert;
  commented.

## Acceptance criteria
1. Sizeless product + first Blueprint definition → Universal exists
   (active, order 0), same transaction; second definition adds nothing.
2. [Start with Universal] on Manager + Dashboard no-sizes states works,
   POST-only, role-gated; reactivates instead of duplicating.
3. Archive guard: sole-confirmed-designs size REFUSED (honest message,
   both surfaces); other cases archive normally; hard-delete still
   impossible (PROTECT untouched).
4. production imports patterns_ai NOWHERE (existing sweep green);
   sizes stay production-owned (only `product_size_service` writes).
5. Battery green (counts from output) · zero migrations · browser
   desktop + 390×844: sizeless DEV product → button → Universal flow →
   Blueprint auto-case → guard refusal message; screenshots.

---
**STOP — Phase-3 plan delivered. No code. Awaiting your approval
(D-1 two write-moments · D-2 production-owned ensure · D-3 validator
registry).**
