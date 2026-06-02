# CLAUDE.md — Kapil Enterprises Inventory

Django 5.2 + PostgreSQL. Personal project. Owner: Umesh (junior dev).

**7 apps:** accounts, inventory, raw_materials, production, tracking, **expense** (worker payroll/settlement), storefront.

**Deep context lives in lazy-load docs — read them only when needed:**
- [SYSTEM_DESIGN.md](SYSTEM_DESIGN.md) — **current full system design** (most up-to-date; read first for the big picture)
- [ARCHITECTURE.md](ARCHITECTURE.md) — models, services, ER, security, perf
- [ABOUT_THIS_PROJECT.md](ABOUT_THIS_PROJECT.md) — why + how + learning map
- [UI_COMPONENTS.md](UI_COMPONENTS.md) — component vocabulary, design tokens, DataTables/fancy-select usage
- [docs/production/OVERVIEW.md](docs/production/OVERVIEW.md) — production subsystem (raw_materials + production + tracking); load when touching cloth rolls, Adda batches, workflows, stage records, barcodes, **or stage costing**
- [docs/production/PAYROLL_ARCHITECTURE.md](docs/production/PAYROLL_ARCHITECTURE.md) + [SETTLEMENT_ARCHITECTURE.md](docs/production/SETTLEMENT_ARCHITECTURE.md) + [STAGE_COSTING_PLAN.md](docs/production/STAGE_COSTING_PLAN.md) — load when touching the `expense` app (earnings ledger, advances, settlement) or stage costing
- [docs/production/RBAC.md](docs/production/RBAC.md) — roles/skills, Access Control hub, sidebar + URL enforcement
- [docs/PAGES/](docs/PAGES/) · [docs/FLOWS/](docs/FLOWS/) · [docs/QA/](docs/QA/) — per-page contracts, flows, audit/bug/fix logs

## Rules
1. Terse. No greetings, no summaries unless asked.
2. Junior-Django mode: 1-line "why" comments naming Django/PG primitive on first touch.
3. Plan before ≥3-file edits. Use Edit not Write for existing files.
4. **Service layer owns all multi-row writes** (`config/inventory/services/`). Views call services. No signals.
5. `StockService.log(...)` is the only writer to `StockLedger`.
6. Permissions via `permission_service` (`user_has_perm` / `user_has_role`). No raw `is_superuser` checks in views. **RBAC roles: super_admin, manager, worker** (renamed from `karigar` 2026-06-02), listing_team, accountant. Production-STAGE access is **skill**-gated (`access_service.user_can_access_stage`), not role. Menu items + their URLs are gated together by `SidebarItemRule` via `inventory.middleware.SidebarAccessMiddleware` — hiding a menu item also blocks its URL.
7. Shadow `.py` files (inventory views/services/forms + `config/settings.py`) were deleted 2026-05-16. Only package forms exist. If you ever see a duplicate `.py` next to a same-named package dir, flag it.
8. gstack installed — route ship/review/qa/etc. to matching gstack skill. Don't auto-trigger.
9. **Before writing CSS on a template**, check [UI_COMPONENTS.md](UI_COMPONENTS.md). If class exists → use it. If 80% match → extend with modifier. Only add new CSS to `base.html` when same pattern appears in 3+ templates.
10. **Page-specific CSS** goes in page's `{% block extra_head %}`, scoped under a page class (`.user-create`, `.product-list`) so it can't leak to other pages.

## Run
Venv at `env/`. `env/bin/python config/manage.py <cmd>`. Settings: `config.settings.local`.

## Shortcuts
`?` → ≤2 sentences. `explain` → 5-line lesson. `fix` → patch + 1-line reason. `review` → bullets, severity-tagged.
