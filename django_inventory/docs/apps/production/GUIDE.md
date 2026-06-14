# production app — file-by-file GUIDE

> Business view: [config/production/README.md](../../../config/production/README.md).
> Sabse bada app: Adda lifecycle, stages, worker truth, costing freeze.

## models/ (split by domain — har file = ek concern)
| File | What lives here | Pattern / why |
|---|---|---|
| `core.py` | Product, Stage (library), WorkflowStage (+RoleRate), AddaStageRoleRate, RateCorrectionAudit | WorkflowStage = per-product POLICY row (order, cost_rate dual-duty ADR-0009, credits_workers, cost_billed_at grouping; TM-1 field aayega yahin). AddaStageRoleRate = frozen resolved payable rate (S1/S2). RateCorrectionAudit = append-only re-rate audit (S1.1) |
| `adda.py` | Adda, AddaStageRecord (+ pending_report_workers helper) | SR = stage ka polymorphic parent; processing_cost frozen (honest-NULL) |
| `worker_task.py` | WorkerStageTask, WorkerStageContribution | THE production truth (ADR-0005, C-TM); partial-unique active task; settlement_line provenance string-FK. **S3: good/alter/missing columns (good NOT NULL = payable; alter/missing immutable observations); reported dual-written = good (renamed-not-dropped @S6); constraint wsc_gam_nonneg_sum_positive** |
| `layering.py` | LayeringRecord, LayeringRollEntry, RemainingClothOfClothRoll | per-roll verify + MANDATORY leftovers (G1 ke facts) |
| `cutting.py` | CuttingRecord, ProductSize, PatternVerification, PieceBreakup, Bundle(+items), ProductPattern | cutting = first real quantities; breakup = expected denominators |
| `barcode.py` | BarcodeGenerationRecord | archetype-E stage record |

## services/ (ALL writes — views kabhi nahi)
| File | Role |
|---|---|
| `worker_task_service.py` | ★ chokepoint: WST/WSC sole writer, expected freeze, verified qty (P1), auto-cancel resolve |
| `adda_service.py` | Adda create (race-safe per-product counter) + stage advance |
| `cost_service.py` | processing_cost freeze/clear; `role_rate_for` (grouped-member guard C-1) |
| `flow_service.py` | WorkflowStage CRUD + grouping guards |
| `stage_rate_service.py` | ★ sole writer of AddaStageRoleRate: snapshot/freeze/lock/edit + `rerate_stage_role` (S1.1 super-admin correct-until-settlement + recalc + RateCorrectionAudit) |
| `_shared.py` | auth helpers + ★ reopen_stage_record skeleton (V2-3 settled-block) |
| `access_service.py` | skill-gating reads |
| `activity_service.py` | timeline UNION reads |
| `product_service.py` / `product_size_service.py` | masters |
| `reconciliation_service.py` | counter sanity (read-only) |

## stages/ — the OPEN-CLOSED engine
`base/handler.py` (contract: typed record, complete validations,
cost_quantity, contribution_schema) + `base/registry` + per-stage packages
(layering/cutting/cutting_pattern/barcode_generation each = handler + service).
NAYA STAGE = naya package; worker UI ko haath nahi lagana padta.

## views/ (12 modules — parse→gate→delegate ONLY)
FILE MAPs already in code: `stage_views.py` (1.4k — layering+cutting consoles,
6 sections documented at top), `pattern_stage_views.py`, `barcode_gen_views.py`,
`worker_report_views.py` (★ phone report + AddaReportReviewView P1),
`adda_views.py`, `flow_views.py`, `costing_views.py`, `dashboard.py`,
`product_views.py`, `pattern_views.py`, `access_views.py`, `mixins.py` (RBAC).

## forms/ · urls.py · templates/
forms = plain Django forms per stage (`_shared.py` = worker chips widget).
urls.py header me poora route-group map. Templates: `_stage_panel_*.html`
(operator consoles), `worker_report*.html` (phone), `product_flow.html` (editor).

## Dots kaise connect (ek request)
```
worker report POST → urls → WorkerReportView ( assignment gate )
  → worker_task_service.report_contributions/complete (WSC + freeze)
  → history via stage services · settlement (expense) baad me READS WSC
```

## Topics yahan use hote hain — kahan padhein
Har concept ka official link + "is project me kahan" mapping:
[../../LEARNING/10_ONLINE_RESOURCES.md](../../LEARNING/10_ONLINE_RESOURCES.md).
App ka business-view: README (code ke saath). Deep lessons: [docs/LEARNING/](../../LEARNING/README.md).
