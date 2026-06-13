# CLAUDE.md — Kapil Enterprises Inventory

Django 5.0 + PostgreSQL. Personal project. Owner: Umesh (junior dev).

**7 domain apps:** accounts, inventory, raw_materials, production, tracking, **expense** (worker payroll/settlement), storefront. Plus **`core`** — infra app holding shared abstract base models (`TimeStampedModel`, `ActiveManager`); no tables.

**Deep context lives in lazy-load docs — read them only when needed:**
- [docs/ARCHITECTURE_V2.md](docs/ARCHITECTURE_V2.md) — **🔒 LOCKED REDESIGN (worker-tracking + settlement).** Read FIRST before touching worker assignment, contributions, earnings, or settlement. Option B (no ledger until settlement; `expected_*` frozen = visibility), Adda-centric `AddaSettlement` (settlement ≠ payment), `WorkerStageTask`/`WorkerStageContribution` = the SOLE production truth (**V2-1d DONE 2026-06-11**: legacy M2M dropped, migration 0035, data-aware reverse), `StageWorkAssignment` transitional-RETAINED (→ settlement earning line, §11.4). **V2-1a→1d + V2-2 (PR-A→D incl. mgmt UI + `LEDGER_CREDIT_AT_ALLOCATION` lever) COMPLETE 2026-06-11; **V2-3 COMPLETE 2026-06-11** (review archived: docs/archive/reviews/): settlement-first DEFAULT (`LEDGER_CREDIT_AT_ALLOCATION=False`; env True = rollback lever, deletion soak-gated), settlement-money armor (reopen/void guards, gate 4c), worker visibility Expected→Earned→Paid. Next: deploy+soak gate — all open items: [docs/PENDING_BACKLOG.md](docs/PENDING_BACKLOG.md).** Ledger cutover: [docs/adr/0007](docs/adr/0007-allocation-era-ledger-cutover.md) (Option A).
- [docs/REQUIREMENT_REVIEW_STAGE_TRACKING.md](docs/REQUIREMENT_REVIEW_STAGE_TRACKING.md) — **🔒 LOCKED requirement (2026-06-11): per-WorkflowStage Tracking Mode (Manual/Barcode/Both/None on the flow editor)** + C-TM convergence constraint (every capture path → `WorkerStageContribution` via the single-writer chokepoint). Delivery: TM-1 Manual/None (small, post-V2-3) · TM-2 Barcode/Both (only via future Barcode/Traceability review). Read before touching worker reporting or the flow editor.
- [docs/PROJECT_KNOWLEDGE_MAP.md](docs/PROJECT_KNOWLEDGE_MAP.md) — **FIRST-READ for any new developer/owner**: business flow → architecture → database → code; truth flows, settlement lifecycle, chokepoint services, phase history, ADR + G1-G7 summaries. Companion: [docs/LEARNING_PATH.md](docs/LEARNING_PATH.md) · index of every active doc: [docs/DOCUMENTATION_INDEX.md](docs/DOCUMENTATION_INDEX.md).
- [SYSTEM_DESIGN.md](SYSTEM_DESIGN.md) — full system design of the **currently-built** state (pre-V2; V2 wins where they conflict)
- [GLOSSARY.md](GLOSSARY.md) — domain-term glossary (Adda, layering, bundle, settlement…) + core-model ER diagram. **Read first if new to the codebase.**
- [ABOUT_THIS_PROJECT.md](ABOUT_THIS_PROJECT.md) — why + how + learning map
- [UI_COMPONENTS.md](UI_COMPONENTS.md) — component vocabulary, design tokens, DataTables/fancy-select usage
- [docs/production/OVERVIEW.md](docs/production/OVERVIEW.md) — production subsystem (raw_materials + production + tracking); load when touching cloth rolls, Adda batches, workflows, stage records, barcodes, **or stage costing**
- [config/expense/README.md](config/expense/README.md) — load when touching the `expense` app (settlement, ledger, advances, payment); cost-truth rules live in [ADR-0009](docs/adr/0009-cost-truth.md). (Pre-V2 payroll/settlement docs are archived.)
- [docs/production/RBAC.md](docs/production/RBAC.md) — roles/skills, Access Control hub, sidebar + URL enforcement
- [docs/PAGES/](docs/PAGES/) — per-page contracts. Flows: [docs/LEARNING_2_0/DATA_FLOWS/](docs/LEARNING_2_0/DATA_FLOWS/) (write-path) + [docs/LEARNING_2_0/REQUEST_JOURNEYS/](docs/LEARNING_2_0/REQUEST_JOURNEYS/) (call-chain)
- [docs/adr/](docs/adr/) — locked architecture decisions (ADRs; **0009 cost-truth + 0010 growth/identity = C-1 policy locks, read before any costing/commerce/multi-factory/barcode/rework design**) · [docs/archive/](docs/archive/) — superseded/dated docs (audits, build logs, shipped plans)

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
12. **⚠️ DOCS-SYNC (owner standing rule 2026-06-12, VERY IMPORTANT): code change ⇒ docs change, same session.** Before editing any file, check its md exists in docs/ (IGNORE docs/archive/): lookup `docs/apps/<app>/GUIDE.md` → `config/<app>/README.md` → topic canonical via [docs/DOCUMENTATION_INDEX.md](docs/DOCUMENTATION_INDEX.md). Missing → read the file, CREATE the md. Present → UPDATE it to match the change. New files → add to the app's GUIDE table. PDFs regenerate only on request (md = live truth). **PKALS-LIVE (2026-06-12): documentation drift = an architecture bug.** For any non-trivial change use [docs/LEARNING_2_0/LIVING_DOCUMENTATION_SYSTEM/CHANGE_IMPACT_MATRIX.md](docs/LEARNING_2_0/LIVING_DOCUMENTATION_SYSTEM/CHANGE_IMPACT_MATRIX.md) (changed-file → docs to update) — implementation is incomplete until those docs are updated or each is stated N/A. AI agents: run docs/LEARNING_2_0/AI_AGENT_GUIDE first (read-4-files → canonical lookup → cheap navigation).

## Run
Venv at `env/`. `env/bin/python config/manage.py <cmd>`. Settings: `config.settings.local`.

## Shortcuts
`?` → ≤2 sentences. `explain` → 5-line lesson. `fix` → patch + 1-line reason. `review` → bullets, severity-tagged.
