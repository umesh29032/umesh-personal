> **ARCHIVED 2026-07-13** — shipped-phase report/review (patterns_ai). Live truth: [PLATFORM_STATUS](../../AI_PATTERN_INTELLIGENCE/PLATFORM_STATUS.md) + [PRODUCT_VISION_V2](../../AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md) + the app [GUIDE](../../apps/patterns_ai/GUIDE.md). Kept for history (Phase-7 DOCCLEAN-D, D-OR-1). Outbound links reflect its era.

# Implementation Readiness — M5 · Layout Library polish
(2026-07-10 · the new one-page format · product engineering mode)

**Problem**: The Layout Library is manufacturing truth but reads like a
debug row: no notes, no recipe, no lay type, no preview, no lineage,
no search — the cutting master can't FIND or TRUST the right asset
fast. Recipes can be created but not managed.

**Why now?** M4/M4.5/M6 filled the library with real assets (plans,
recipes, fold markers); the data exists, the surface doesn't show it.
Debt items 7 (notes-on-rows) + recipe management are already logged.

**Real factory workflow**: the master scans the shelf of markers,
recognizes them by name/width/lay ("Body+Pocket double 42″"), checks
the note ("works only on 42″"), picks or prints. Search + chips +
thumbnails = that recognition, digitized.

**Modules touched**: `CuttingTableShellView` (library rows context) ·
`cutting_table.html` (library section + recipe block) ·
`CuttingTableRecipeView` (+deactivate action) · dct.js untouched ·
zero models · zero migrations · zero ERP files.

**Browser journey**: DEV-NICKAR library → 2 rows with thumbnail ·
recipe chip · lay chip · notes line · lineage "supersedes V1" → type
in search → rows filter live → deactivate a recipe → gone from the
plan dialog. T-SHIRT library → legacy rows (no plan params) render
clean with honest defaults.

**Tests**: rows carry notes/recipe/lay/thumb/lineage · legacy rows
default-safe · search box + filter hooks present · recipe deactivate
endpoint (one-shot, refusals) · empty states · full battery.

**Out of scope**: station page (waits for real volume) · new models ·
any architecture · exports/engine/planner changes · ERP surfaces.
