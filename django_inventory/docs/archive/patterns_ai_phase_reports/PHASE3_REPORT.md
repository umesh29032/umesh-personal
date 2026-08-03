> **ARCHIVED 2026-07-13** — shipped-phase report/review (patterns_ai). Live truth: [PLATFORM_STATUS](../../AI_PATTERN_INTELLIGENCE/PLATFORM_STATUS.md) + [PRODUCT_VISION_V2](../../AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md) + the app [GUIDE](../../apps/patterns_ai/GUIDE.md). Kept for history (Phase-7 DOCCLEAN-D, D-OR-1). Outbound links reflect its era.

# PLATFORM · PHASE 3 REPORT — Universal Size + archive guard
(2026-07-09)

**Status: ✅ PHASE 3 COMPLETE — STOPPED. Phase 4 (Digital Cutting Table
Shell) will not start without approval.**

Implemented exactly as approved (D-1/D-2/D-3 + both owner notes).

## What shipped

**1 · `ensure_universal_size(product)`** — in production's existing
`product_size_service` (D-2: sizes stay production-owned). Idempotent:
creates the REAL `ProductSize(code='universal', label='Universal',
order 0)`, adopts/reactivates an existing row, never duplicates. No
user gate (convention write; callers role-gated).

**2 · The two D-1 write moments — GET stays pure:**
- **Auto**: `register_pattern_definition` on a product with zero active
  sizes ensures Universal in the SAME transaction.
- **Explicit**: `[Start with Universal]` on the Manager's no-sizes card
  + the Dashboard's no-sizes line (both POST to the Manager endpoint's
  new `start_universal` action; worker 403).

**3 · Archive guard via validator registry (D-3).**
`ARCHIVE_VALIDATORS = []` + run-loop in `archive_product_size`
(production, ~6 lines, imports nothing); `patterns_ai/apps.ready()`
registers `size_guards.refuse_archiving_sole_design_size`: refuses
archiving a size holding confirmed designs while NO other active size
has any — honest block-with-reason. **Owner note #2 honored**: the TODO
comment sits at the exact refusal block — *"Copy Universal Designs into
newly created sizes"* — future roadmap, NOT implemented.

**4 · Owner note #1 honored — Universal is a NORMAL size everywhere.**
Same size-card component on the Manager (verified visually), plain row
on the production Sizes page, no special casing anywhere in UI. The
only "special" knowledge = the convention constant inside the service.

## Zero migrations. Nothing renamed. No new abstractions beyond the
approved ~10-line registry.

## Tests
NEW `test_phase3_universal.py` (10): auto-materialize on first
definition + idempotent · no auto when real sizes exist · reactivate-
not-duplicate · button POST creates / GET never writes · dashboard
button + worker 403 · Universal renders as a normal card · guard:
sole-confirmed-size REFUSED (message + state unchanged) · allowed when
another active size holds confirmed designs (copy-forward fixture) ·
design-less size archives freely · guard registered exactly once.
No conscious updates needed — existing no-sizes asserts still hold
(text retained).

## Battery (counts from output, serial, fresh)
- patterns_ai: **376/376 OK** (366 + 10 — exact).
- Full suite incl. storefront: **1261/1261 OK** (1251 + 10 — exact).
- `makemigrations --check`: **No changes detected** (zero-migration
  phase, as planned).
- Import contracts: **1 kept, 1 broken — pre-existing baseline**;
  production still imports patterns_ai nowhere (sweep green — the
  registry inversion worked as designed).

## Browser (live, DEV products 20/21 — sanctioned test data)
- **Button flow (DEV-P3A)**: Dashboard no-sizes line → [Start with
  Universal] → Manager shows the Universal card — SAME component as any
  size (🔴 Missing Designs 0/0 · Manage Pattern Designs · gate honestly
  disabled) + success message (`p3_manager_universal.png`,
  `p3_dash_nosizes.png`).
- **Auto flow (DEV-P3B)**: Blueprint `+ Add Pattern Definition` on a
  sizeless product → DB shows `('universal', 'Universal', True)` — same
  transaction.
- Production Sizes page renders Universal like any size (js-verified).
- Mobile 390×844 (`p3_mobile_universal.png`).
- Guard refusal exercised at service level by the suite (4 tests);
  golden T-SHIRT untouched.

## Docs-sync (rule 12)
patterns_ai GUIDE + production GUIDE rows added · this report.

**STOPPED — Phase 3 complete and verified. Awaiting owner review +
Phase 4 approval (Digital Cutting Table SHELL — the owner-flagged next
design-review checkpoint).**
