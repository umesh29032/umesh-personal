# CLAUDE.md — Kapil Enterprises Inventory

Django 5.0 + PostgreSQL. Personal project. Owner: Umesh (junior dev).

**7 domain apps:** accounts, inventory, raw_materials, production, tracking, **expense** (worker payroll/settlement), storefront. Plus **`core`** — infra app holding shared abstract base models (`TimeStampedModel`, `ActiveManager`); no tables.

**Deep context lives in lazy-load docs — read them only when needed:**
- [docs/ARCHITECTURE_V2.md](docs/ARCHITECTURE_V2.md) — **🔒 LOCKED REDESIGN (worker-tracking + settlement).** Read FIRST before touching worker assignment, contributions, earnings, or settlement. Option B (no ledger until settlement; `expected_*` frozen = visibility), Adda-centric `AddaSettlement` (settlement ≠ payment), `WorkerStageTask`/`WorkerStageContribution` = the SOLE production truth (**V2-1d DONE 2026-06-11**: legacy M2M dropped, migration 0035, data-aware reverse), `StageWorkAssignment` transitional-RETAINED (→ settlement earning line, §11.4). **V2-1a→1d + V2-2 (PR-A→D incl. mgmt UI + `LEDGER_CREDIT_AT_ALLOCATION` lever) COMPLETE 2026-06-11; **V2-3 COMPLETE 2026-06-11** ([docs/V2_3_EXECUTION_REVIEW.md](docs/V2_3_EXECUTION_REVIEW.md)): settlement-first DEFAULT (`LEDGER_CREDIT_AT_ALLOCATION=False`; env True = rollback lever, deletion soak-gated), settlement-money armor (reopen/void guards, gate 4c), worker visibility Expected→Earned→Paid. Next: deploy+soak gate.** Ledger cutover: [docs/adr/0007](docs/adr/0007-allocation-era-ledger-cutover.md) (Option A).
- [docs/REQUIREMENT_REVIEW_STAGE_TRACKING.md](docs/REQUIREMENT_REVIEW_STAGE_TRACKING.md) — **🔒 LOCKED requirement (2026-06-11): per-WorkflowStage Tracking Mode (Manual/Barcode/Both/None on the flow editor)** + C-TM convergence constraint (every capture path → `WorkerStageContribution` via the single-writer chokepoint). Delivery: TM-1 Manual/None (small, post-V2-3) · TM-2 Barcode/Both (only via future Barcode/Traceability review). Read before touching worker reporting or the flow editor.
- [docs/V2_1_REVIEW.md](docs/V2_1_REVIEW.md) — V2-1 pre-implementation review: M2M→`WorkerStageTask` migration, §3.1 full dependency audit, §10 V2-1a deep dive (migration/dual-write/rollback/concurrency/tests).
- [SYSTEM_DESIGN.md](SYSTEM_DESIGN.md) — full system design of the **currently-built** state (pre-V2; V2 wins where they conflict)
- [GLOSSARY.md](GLOSSARY.md) — domain-term glossary (Adda, layering, bundle, settlement…) + core-model ER diagram. **Read first if new to the codebase.**
- [ARCHITECTURE.md](ARCHITECTURE.md) — models, services, ER, security, perf
- [ABOUT_THIS_PROJECT.md](ABOUT_THIS_PROJECT.md) — why + how + learning map
- [UI_COMPONENTS.md](UI_COMPONENTS.md) — component vocabulary, design tokens, DataTables/fancy-select usage
- [docs/production/OVERVIEW.md](docs/production/OVERVIEW.md) — production subsystem (raw_materials + production + tracking); load when touching cloth rolls, Adda batches, workflows, stage records, barcodes, **or stage costing**
- [docs/production/PAYROLL_ARCHITECTURE.md](docs/production/PAYROLL_ARCHITECTURE.md) + [SETTLEMENT_ARCHITECTURE.md](docs/production/SETTLEMENT_ARCHITECTURE.md) + [STAGE_COSTING_PLAN.md](docs/production/STAGE_COSTING_PLAN.md) — load when touching the `expense` app (earnings ledger, advances, settlement) or stage costing
- [docs/production/RBAC.md](docs/production/RBAC.md) — roles/skills, Access Control hub, sidebar + URL enforcement
- [docs/PAGES/](docs/PAGES/) · [docs/FLOWS/](docs/FLOWS/) — per-page contracts, flows
- [docs/adr/](docs/adr/) — locked architecture decisions (ADRs) · [docs/archive/](docs/archive/) — superseded/dated docs (audits, build logs, shipped plans)

## Rules
1. Terse. No greetings, no summaries unless asked.
2. Junior-Django mode: 1-line "why" comments naming Django/PG primitive on first touch.
3. Plan before ≥3-file edits. Use Edit not Write for existing files.
4. **Service layer owns all multi-row writes** (`config/<app>/services/`). Views call services. No signals.
5. **Single-writer discipline:** each ledger/audit table has exactly ONE writer service — `ledger_service` for `WorkerLedgerEntry`, `history_service` for the `*History` tables. (Legacy `StockService`/`StockLedger` were removed 2026-05-19.)
6. Permissions via `permission_service` (`user_has_perm` / `user_has_role`). No raw `is_superuser` checks in views. **RBAC roles: super_admin, manager, worker** (renamed from `karigar` 2026-06-02), listing_team, accountant. Production-STAGE access is **skill**-gated (`access_service.user_can_access_stage`), not role. Menu items + their URLs are gated together by `SidebarItemRule` via `inventory.middleware.SidebarAccessMiddleware` — hiding a menu item also blocks its URL.
7. Shadow `.py` files (inventory views/services/forms + `config/settings.py`) were deleted 2026-05-16. Only package forms exist. If you ever see a duplicate `.py` next to a same-named package dir, flag it.
8. gstack installed — route ship/review/qa/etc. to matching gstack skill. Don't auto-trigger.
9. **Before writing CSS on a template**, check [UI_COMPONENTS.md](UI_COMPONENTS.md). If class exists → use it. If 80% match → extend with modifier. Only add new CSS to `base.html` when same pattern appears in 3+ templates.
10. **Page-specific CSS** goes in page's `{% block extra_head %}`, scoped under a page class (`.user-create`, `.product-list`) so it can't leak to other pages.
11. **Mobile-first is a FUNCTIONAL requirement (owner standing rule 2026-06-11), not polish.** Every new UI (worker, management, settlement, reporting, MissingPiece, Alter, Adda-360, inventory, commerce): worker flows optimized for phones FIRST; management flows must work desktop+tablet+mobile; no UI is "complete" unless usable on common Android sizes; every table needs an explicit responsive strategy (stack/cards/data-label/scroll/summary); touch targets + readability + low-friction entry are first-class. Every future UI execution review MUST include a responsive/mobile section.

## Run
Venv at `env/`. `env/bin/python config/manage.py <cmd>`. Settings: `config.settings.local`.

## Shortcuts
`?` → ≤2 sentences. `explain` → 5-line lesson. `fix` → patch + 1-line reason. `review` → bullets, severity-tagged.
