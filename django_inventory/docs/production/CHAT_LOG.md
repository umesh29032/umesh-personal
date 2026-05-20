# Chat Log — Production Tracking Session(s)

Chronological summary of decisions made during the build-out chats. Load this in a fresh session to skip re-deriving context.

## Session 1 — Brainstorm + Implementation (2026-05-19)

### Phase 0 — `/brainstorming` skill
12 decisions locked + 3 open questions resolved. Output:
- 8 design docs persisted under `docs/production/` (OVERVIEW, RAW_MATERIALS, PRODUCTION_APP, TRACKING, RBAC, MIGRATIONS, TESTS_AND_RISKS, DECISION_LOG).
- Memory `project_production_design.md` written; `project_batch_architecture.md` marked DEPRECATED.

### Phases 0-9 — Implementation
- Phase 0: scaffold 3 apps + `ROLE_ACCOUNTANT` + qrcode dep
- Phase 1: raw_materials master data CRUD + seed
- Phase 2: ClothRoll + bulk intake + Postgres `cloth_roll_seq`
- Phase 3: Product + WorkflowStage + Adda + per-product counter seed
- Phase 4: AddaStageRecord + LayeringRecord + roll assignment
- Phase 5: CuttingRecord + BatchBarcode QR (ECC Q, density modes)
- Phase 6: history tables + `history_service` single-writer
- Phase 7: dashboards (cloth + Adda + barcode + raw-material index)
- Phase 8: 19 tests written + passing
- Phase 9: doc sync (ARCHITECTURE.md deprecation banner)

End-to-end golden path verified:
bulk create rolls → Adda → assign rolls → complete layering → complete cutting → barcodes generated → history rows logged.

## Session 1 follow-ups (same chat)

### Q1 — Bulk add UX bugs
- State loss after validation error → repopulate breakup rows from POST
- Row clone preserved `<option selected>` carry-over → switched to inert `<template>` element
- Last-row removal → "clear instead of remove" (always one row visible)
- Submit-empty block: client + server side
- Added Color filter dropdown to roll list filters

### Q2 — Sidebar active tab bug
Bug: `{% if m in request.path %}` substring match made multiple items light up.
Fix: `build_menu_for(user, current_path)` picks single longest-match item, sets `entry.is_active=True`. Template renders `{% if item.is_active %}active{% endif %}`.

### Q3 — Cloth dashboard rework
- Split `/raw-materials/` → overall Raw Material index (Cloth live + 6 placeholder tiles: Elastic, Rib, Sui, Dhaga, Button, Tag)
- `/raw-materials/cloth/` → Cloth dashboard with Type × Color pivot + color filter

### Q4 — Timestamps + date filter + time logs
- All models have `created_at` + `updated_at` (added `updated_at` to `tracking.TimeStampedModel` via migration 0003)
- Date-range filter (`?from=&to=`) on all 4 dashboards (cloth + adda + barcode + roll-list)
- Roll list now shows time-log panel at bottom (top 50 movements)

### Q5 — Cloth add button gating
- `RollBulkCreateView` restricted to `ROLE_SUPER_ADMIN` (single-role rule)
- "+ Bulk Add Rolls" button shown only when `can_add_rolls=True` in context

### Q6 — Adda barcode dashboard
- New `/tracking/` route + `BarcodeDashboardView`
- Per-Adda row with status breakdown (pending/packed/dispatched/missing)
- 3 actions per Adda: View / Print QR / Export CSV
- CSV export endpoint `/tracking/barcodes/<code>/export/`

### Q7 — Workers on stage
- `AddaStageRecord.workers` M2M lifted to parent (uniform across stage types)
- `_WorkerCheckboxes` widget (chip-style) replacing default `SelectMultiple`
- Adda detail page now shows stage records with worker chips per stage
- "My Active Stages" panel on user dashboard

### Q8 — QR print sheet (industrial standard)
- ECC level Q (25% damage tolerance) for shop-floor scanning
- 4-module quiet zone (ISO 18004)
- 3 density modes: small (54/page) / medium (35) / large (24)
- Status filter for reprints
- Sticky toolbar on screen, hidden in `@media print`

### Q9 — Bulk add re-check (2nd row select bug)
Root cause: `cloneNode(true)` from live `<select>` carried over `<option selected>` attribute.
Fix: inert `<template id="breakup-row-template">` element; `tpl.content.firstElementChild.cloneNode(true)` gives fresh untouched node every time.

### Q10 — Time logs section on roll list
Added bottom-of-page time log timeline showing latest 50 `ClothRollHistory` events with select_related on roll + cloth_type + cloth_color + actor.

### Q11 — Filter chips on /raw-materials/rolls/
Active-filter strip below filter card. Each chip = one filter dimension with `✕` button that strips just that filter, keeping others intact. Plus filtered count + "Clear all".

### Q12 — Color filter on roll list
Added 4th filter dropdown alongside status/type/location. Same chip-removal pattern applies.

### Q13 — Mobile-friendly templates + form shell rebuild
Sweep of all 28 new templates per `feedback_html_standards` + `feedback_ui_polish` + `project_form_shell` memories:
- `data-label` on every `<td>`
- Form-shell pattern (hero + numbered panels + cream inputs + sticky CTA) on all create/edit pages
- `production/_form_styles.html` shared partial
- Global classes adopted (`.kpis`/`.kpi`, `.tbl`, `.card`, `.btn-primary`/`.btn-ghost`, `.empty-state`)
- Filter cards single-row + horizontal scroll

### Q14 — Hinglish comments
- Updated 16+ Python files (services, models, forms, views, mixins, migrations, templatetag) with Hinglish "YEH FILE KYU HAI" docstrings + 1-line "why" inline comments naming Django/PG primitive
- Same applied to all HTML templates (verbose English comments → terse Hinglish)
- Verified `{# #}` Django comments don't leak to rendered HTML (browser View Source clean)

### Q15 — Collapsible time-log accordion
Native `<details>/<summary>` HTML5 — no JS needed. Shared partials:
- `templates/inventory/_time_log_styles.html` (CSS)
- `templates/inventory/_roll_events_accordion.html` (cloth-roll movements)
- `templates/inventory/_adda_events_accordion.html` (Adda lifecycle)

Applied to 5 dashboards: `/raw-materials/`, `/raw-materials/cloth/`, `/raw-materials/rolls/`, `/production/`, `/tracking/`.

## Current state at session end

```
git status                  → many template/view/service edits uncommitted on branch new_flask_app
manage.py check             → clean
manage.py test ...          → 19/19 OK
HTTP smoke (12 routes)      → all 200
```

## Open follow-ups (not blocking)

1. WorkflowStage CRUD UI — currently hardcoded data migration; OK until 2nd product needs different stages
2. Scan-to-mark-done — `BatchBarcode.status` enum + `mark_status` service exist; scan view just shows detail today. Add status buttons to `scan_detail.html` when needed.
3. `expense` app — placeholder. Worker payment ledger (hours, rates, payouts). M2M seam ready: `AddaStageRecord.workers` → `through='expense.StageWorkAssignment'`.
4. Cost reports / financial dashboards for `ROLE_ACCOUNTANT` — sidebar entry exists but no views.
5. Phase-9 doc sync — `ARCHITECTURE.md` has deprecation banner pointing here; full rewrite deferred.
6. CI must run against PostgreSQL (Roll ID sequence is Postgres-only).

## Key invariants to preserve

1. **Service layer owns multi-row writes** (CLAUDE.md rule #4). Views call services; no direct ORM writes for >1-row ops.
2. **History tables write-only via `history_service.log_*`** — analog of old `StockService.log` (CLAUDE.md rule #5).
3. **`permission_service` for RBAC** — never `is_superuser` direct checks (rule #6).
4. **Cross-app FK direction**: `production → raw_materials` (string FK for cycles), `tracking → both upstream`. Never reverse.
5. **PROTECT on all master FKs** — soft archive via `is_active`, hard delete only when usage_count==0.
6. **Postgres-only** — `cloth_roll_seq` sequence + `SELECT FOR UPDATE` patterns.
7. **Roll ID + Adda code are service-generated** — `editable=False` on models; admin/client never set them.
8. **Hinglish comments** — every new file matches existing "YEH FILE KYU HAI?" style.
9. **Mobile-first** — `data-label` on `<td>`, page-scoped CSS, single-row scrolling filter bars.
10. **Form-shell required** — no plain Django forms ship to user.

## Bootstrap commands for new chat

```
1. Load docs/production/OVERVIEW.md
2. Load this CHAT_LOG.md (current file)
3. Load relevant sub-doc based on task:
   - cloth roll work       → RAW_MATERIALS.md
   - Adda/Product/stages   → PRODUCTION_APP.md
   - barcodes/history      → TRACKING.md
   - UI/templates/mobile   → UI_PATTERNS.md
   - role gating           → RBAC.md
   - tests/risks           → TESTS_AND_RISKS.md
4. Memory MEMORY.md auto-loads — project_production_design points to all of above
5. Verify: env/bin/python config/manage.py test raw_materials production tracking
```
