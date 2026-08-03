> **ARCHIVED 2026-07-13** — shipped-phase report/review (patterns_ai). Live truth: [PLATFORM_STATUS](../../AI_PATTERN_INTELLIGENCE/PLATFORM_STATUS.md) + [PRODUCT_VISION_V2](../../AI_PATTERN_INTELLIGENCE/PRODUCT_VISION_V2.md) + the app [GUIDE](../../apps/patterns_ai/GUIDE.md). Kept for history (Phase-7 DOCCLEAN-D, D-OR-1). Outbound links reflect its era.

# PLATFORM · PHASE 1 REPORT — Pattern Dashboard entry + truth stamp
(2026-07-09)

**Status: ✅ PHASE 1 COMPLETE — STOPPED. Phase 2 (Blueprint) will not
start without approval.**

Implemented the approved Phase-1 plan + the owner's final corrections
(workflow-step dashboard, Blueprint vocabulary from birth).

## What shipped

**1 · The Pattern Dashboard** (`patterns_ai:dashboard?product=N`) — the
permanent home of all pattern work, rendered as the owner's numbered
workflow, not three flat cards:
`STEP 1 Pattern Blueprint → ▼ → STEP 2 Pattern Manager → ▼ → STEP 3
Digital Cutting Table`. Each step: title · one-line responsibility ·
action button · honest meta line (pieces defined / designs confirmed /
sizes Ready). Readiness line on top (`4/4 sizes Ready for Cutting`).
DCT step obeys the owner-locked gate (≥1 Ready size, same facade field
as the Manager) — disabled state shows the honest reason. Product
chooser without `?product`; worker 403; unknown product 404; GET writes
nothing. Mobile-first (stacked steps, full-width buttons).

**2 · Patterns action → Dashboard.** `production:product-patterns` is
now `ProductPatternsEntryView` — a login-only redirect to the dashboard
(URL-name reverse, no patterns_ai import — ADR-H intact). Every
existing link (product list, sizes page) lands on the dashboard
unchanged. The assignment editor is re-homed and RENAMED (owner
correction #2 — never "legacy"): **Pattern Blueprint** at
`products/<pk>/patterns/blueprint/` (`product-pattern-blueprint`),
strict `change_productpattern` gate unchanged, hero reads "STEP 1 —
define the garment structure… (piece rules arrive in Phase 2)", footer
buttons: ← Pattern Dashboard · STEP 2 Pattern Manager → · Sizes →.

**3 · The truth stamp** (the 500-factory insurance).
`PieceSizeGeometry.geometry_contract_version` (migration **patterns_ai
0008**, additive, default `'adr-c.1'` backfills all legacy rows) +
`GEOMETRY_CONTRACT_VERSION = 'adr-c.1'` constant in
`pattern_geometry_service` — stamped explicitly at **all six** write
paths: extraction-accept (create + row-reuse branches), manual edit,
confirm-normalize, DXF import, and copy-forward (which CARRIES the
original stamp — payload unchanged). Future contract bump = one
constant, single-writer-controlled.

**4 · DCT rename** — gate button reads "🪡 Open Digital Cutting Table"
(enabled + disabled) on the Manager; the dashboard uses the full name
from birth. Manager gained "← Dashboard".

## Deviations from plan (all small, all named)
- Blueprint URL slug `blueprint/` not `set/` — follows owner correction
  #2 (vocabulary from birth).
- `production/views/__init__.py` export list — one missed file in the
  plan's touch list (caught immediately by Django at first run).
- One new-test fixture fix: login redirect asserts `?next=` (project
  LOGIN_URL is `/app/`, not `…/login/`).

## Tests
NEW `test_phase1_dashboard.py` (9): workflow steps · gate
disabled→enabled transition on data change · chooser/worker-403/404 ·
zero-GET-writes · entry redirect + login required · Manager
back-link + rename · contract stamp across paths (default → edit →
confirm → copy-forward-carries) · constant=field-default pin.
Conscious updates (each commented "Phase 1"): `test_pattern_pieces_count`
(Blueprint URL) · `test_phase6_m4` entry tests (302 → dashboard;
worker checks split entry/Blueprint/dashboard) · `test_pdm_w2`
VocabularyTests (redirect + Blueprint page).

## Battery (counts read from output, serial, fresh)
- patterns_ai: **354/354 OK** (345 + 9 new — exact).
- Full manufacturing suite incl. storefront: **1239/1239 OK**
  (1230 + 9 — exact; first run of 1228 explained: storefront's 11
  weren't in that app list, 1219+9=1228 ✓).
- `makemigrations --check`: **No changes detected** (after 0008).
- Import contracts: **1 kept, 1 broken — identical pre-existing
  baseline** (tracking→inventory target); ADR-H wall untouched.

## Browser (live, real data, server restarted)
- Note: sign-in is now OTP-email — browser validation used a
  shell-minted session cookie (dev-only, nothing persisted).
- **Entry redirect live**: `/production/products/2/patterns/` →
  `/patterns/dashboard/?product=2` (`p1_dashboard_desktop.png`) —
  T-SHIRT dashboard = the owner's sketch: numbered steps, ▼ arrows,
  `4/4 sizes Ready`, `8 pieces defined`, `30/32 designs confirmed`,
  DCT step ENABLED with full name.
- **Gated state** (DEV-HUB, real gaps): `0/2 sizes Ready … finish at
  least one size`, DCT `aria-disabled` (`p1_dashboard_gated.png`).
- **Blueprint page**: STEP-1 hero + assignments table + Dashboard/
  Manager hand-offs (`p1_blueprint.png`).
- **Mobile 390×844**: stacked steps, full-width buttons, no horizontal
  scroll (`p1_dashboard_mobile.png`).

## Docs-sync (rule 12)
patterns_ai GUIDE (+3 rows: dashboard · truth stamp · tests) ·
production GUIDE (pattern_views Phase-1 note) · this report ·
PHASE1_PATTERN_DASHBOARD_PLAN.md = the approved plan ·
MA1_IMPLEMENTATION_PLAN.md already marked superseded.

**STOPPED — Phase 1 complete and verified. Awaiting owner review +
Phase 2 (Pattern Blueprint: grain_rule field, unified piece-rules
editing, atomic Add-Pattern-Definition) approval.**
