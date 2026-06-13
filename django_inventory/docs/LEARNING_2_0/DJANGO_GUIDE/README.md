# DJANGO GUIDE — Django as THIS project uses it

## TL;DR (2 min)
Generic Django basics are taught in [../../LEARNING/01_DJANGO_CONCEPTS.md](../../LEARNING/01_DJANGO_CONCEPTS.md)
(models/FK/constraints/managers/migrations), [03_TRANSACTIONS_AND_LOCKS.md](../../LEARNING/03_TRANSACTIONS_AND_LOCKS.md)
(atomic/select_for_update/locks), [04_SERVICE_LAYER.md](../../LEARNING/04_SERVICE_LAYER.md)
(service pattern). Official links mapped to usage: [../../LEARNING/10_ONLINE_RESOURCES.md](../../LEARNING/10_ONLINE_RESOURCES.md).
**This page = the project-SPECIFIC conventions, real examples, common mistakes,
and debugging that you won't find in a Django tutorial.** (Scope-narrowed by
owner: no generic re-teaching — only how THIS codebase bends Django.)

## The non-negotiable conventions (how this project differs from a tutorial)
| Convention | Generic Django | THIS project | Why |
|---|---|---|---|
| Where writes live | views/forms freely write models | **services ONLY** write multi-row/truth tables; views parse+gate+delegate | ADR-0001; auditable, atomic, guarded |
| Signals | common for side-effects | **BANNED** (inventory/signals.py is a tombstone) | order-undefined, fire outside txn → orphaned rows |
| Balances/totals | often stored + updated | **never stored** — live `SUM` | append-only ledger, no drift |
| Corrections | edit/delete the row | **reverse/void/stamp** (append-only) | financial trust, immutable history |
| Single writer | any code writes any model | one service per truth table, **CI-gated** (4/4b/4c) | corruption impossible by construction |
| New stage type | if/else in views | **new StageHandler package** (open-closed) | zero core churn |
| Quantities | one mutable field | reported (immutable) + verified (correction) + expected (frozen visibility) | dispute-proof; ADR-0005 |

## Real project examples (open these files)
- **Models + constraints:** `config/expense/models.py` — see `CheckConstraint`
 (amount>0, finalized⇒settled_at, recovered≤outstanding), partial-unique on
 `production/models/worker_task.py` (active task). DB page: [../DATABASE_GUIDE/](../DATABASE_GUIDE/README.md).
- **Service + atomic + lock order:** `expense/services/adda_settlement_service.py:finalize_adda_settlement`
 — `@transaction.atomic`, `pg_advisory_xact_lock(5374)`, ordered `select_for_update`.
 Trace: [../CHOKEPOINTS/adda_settlement_service.md](../CHOKEPOINTS/adda_settlement_service.md).
- **select_for_update gotcha:** `worker_task_service.set_verified_quantity` uses
 `select_for_update(of=('self',))` — Postgres refuses FOR UPDATE on a nullable
 FK's LEFT JOIN. (Project-specific bug, fixed.)
- **CBV pattern:** `expense/views.py:AddaSettlementDetailView` — parse POST →
 `_ManagementOnly` gate → ONE service → redirect+message. No business logic.
- **Forms:** `production/forms/_shared.py` (worker checkbox→chip widget);
 `raw_materials/forms/roll_forms.py` (role-gated field `pop`).
- **Middleware:** `inventory/middleware.py` — sidebar rule = menu+URL gate together.
- **Migrations (data-aware):** `expense/migrations/0009` — RunPython backfill;
 note RunPython goes in `operations`, never `dependencies` (a real crash this session).
- **Managers:** `core/models.py` `.active` opt-in (soft-delete), default `.objects` untouched.
- **Constraints as architecture:** `core/tests.py` foundation-purity + doc-accuracy = tests, not convention.

## Common mistakes seen / prevented IN THIS PROJECT
1. Writing a truth table from a view → gate 4/4b/4c fails the build.
2. `reported_quantity` edit → use `verified_quantity` (reported is immutable).
3. Reading `expected_*` as money → it's visibility only (ADR-0005).
4. Summing `processing_cost` + settled labor → same labor twice (ADR-0009).
5. `select_for_update` on a nullable-FK `select_related` → add `of=('self',)`.
6. RunPython in migration `dependencies` → "not subscriptable"; put in `operations`.
7. New menu item without a `SidebarItemRule` → URL left unprotected (whitelist bug).
8. New stage via if/else → use a StageHandler package (open-closed).
9. Resurrecting signals → banned (ADR-0001); use explicit service calls.
10. UI without 360/768/1280 verification → rule 11 violation.

## Debugging techniques specific to this project
- `print(qs.query)` to see the real SQL of any queryset (perf-baseline tests pin counts).
- `bash scripts/check.sh` — the 6 gates; a broken invariant fails here, not in prod.
- Money looks wrong → it's a live SUM; list ledger rows, find missing/extra (never a stored value).
- Per-symptom map: [../PROJECT_BRAIN/DEBUGGING_INDEX.md](../PROJECT_BRAIN/DEBUGGING_INDEX.md).
- Per-flow debug playbooks: each [REQUEST_JOURNEY](../REQUEST_JOURNEYS/README.md) + [CHOKEPOINT](../CHOKEPOINTS/README.md) has a "debug in production" section.

### Verification Sources
Conventions cross-checked against CLAUDE.md rules + scripts/check.sh + the
chokepoint services + models read this session. **Verified from code (verified against commit f067daf0, 2026-06-12; re-verify the cited file if it changed)** for the
file references; mistakes list is **observed** during this session's work.
