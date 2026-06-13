# SEARCH INDEX — keyword/symbol → file + doc

## TL;DR
Project "ctrl-F". Look up a term → exact code file + the doc that explains it.
Alphabetical-ish by concept.

| Term / symbol | Code file | Doc |
|---|---|---|
| Adda | production/models/adda.py | ARCHITECTURE_EXPLAINED, GLOSSARY |
| AddaSettlement / ADST | expense/models.py · adda_settlement_service.py | CHOKEPOINTS/adda_settlement_service · ADR-0005/0007 |
| AddaStageRecord | production/models/adda.py | APPS/production/FILE_MAP |
| advisory lock 5374 | adda_settlement_service.py (pg_advisory_xact_lock) | LEARNING/03 · CHOKEPOINTS/adda_settlement_service v2 |
| append-only | expense/services/ledger_service.py | ARCHITECTURE_EXPLAINED/07 |
| BarcodeBatch / (adda,seq) | tracking/models.py | APPS/tracking · ADR-0010 §3 |
| C-TM convergence | worker_task_service.py | REQUIREMENT_REVIEW_STAGE_TRACKING |
| cost duality / processing_cost | production/services/cost_service.py | ADR-0009 · CHOKEPOINTS/cost_service |
| cost_billed_at (grouping) | production/models/core.py | ADR-0009 (grouped-member guard) |
| ClothRoll / cost_per_kg | raw_materials/models.py · roll_service.py | APPS/raw_materials · ADR-0009 §5 |
| era-A / era-B / lever | expense/models.py (SWA.adda_settlement) · allocation_service.py | ARCHITECTURE_EXPLAINED/10 · ADR-0007 |
| expected_rate / expected_earning (frozen) | production/models/worker_task.py | ARCHITECTURE_EXPLAINED/02 · ADR-0005 |
| finalize | adda_settlement_service.py:finalize_adda_settlement | REQUEST_JOURNEYS/settlement_finalize |
| honest-NULL | cost_service.py · costing_views.py | ADR-0009 |
| ledger / WorkerLedgerEntry | expense/models.py · ledger_service.py | CHOKEPOINTS/ledger_and_payment · ARCHITECTURE_EXPLAINED/04 |
| lock order §11.5 | adda_settlement_service.py | LEARNING/03 |
| open-closed / StageHandler | production/stages/base/handler.py | ARCHITECTURE_EXPLAINED/11 · R1 |
| reported_quantity (immutable) | production/models/worker_task.py | ARCHITECTURE_EXPLAINED/02,09 |
| reverse / supersede | adda_settlement_service.py:reverse_adda_settlement | ARCHITECTURE_EXPLAINED/08 |
| select_for_update | (many services) | LEARNING/03 · CHOKEPOINTS |
| settlement ≠ payment | settlement_service.py (payment-only) | ARCHITECTURE_EXPLAINED/05 |
| settlement_line (provenance) | production/models/worker_task.py | LEARNING/02 |
| SidebarItemRule / middleware | accounts/models.py · inventory/middleware.py | APPS/inventory |
| single-writer gates 4/4b/4c | scripts/check.sh | CHOKEPOINTS · DRIFT_PREVENTION |
| StageWorkAssignment / SWA | expense/models.py | CHOKEPOINTS/adda_settlement+allocation |
| verified_quantity | production/models/worker_task.py · worker_task_service.set_verified_quantity | ARCHITECTURE_EXPLAINED/09 |
| WorkerStageTask / WST | production/models/worker_task.py | CHOKEPOINTS/worker_task_service · ARCHITECTURE_EXPLAINED/01 |
| WorkerStageContribution / WSC | production/models/worker_task.py | ARCHITECTURE_EXPLAINED/02 |

### Verification Sources
Symbols cross-checked against the files cited (read across installments 1–6). Confidence: High.
