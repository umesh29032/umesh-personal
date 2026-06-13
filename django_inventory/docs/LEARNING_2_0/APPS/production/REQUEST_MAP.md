# production — URL → View → Service → Model (REQUEST_MAP)

## TL;DR (1 min)
REQUEST_MAP: this app URL-to-View-to-Service-to-Model table.

> Full route list: [../../URL_ATLAS.md](../../URL_ATLAS.md). Deep call chains:
> [../../REQUEST_JOURNEYS/](../../REQUEST_JOURNEYS/README.md).

| URL name | View | Service called | Models written |
|---|---|---|---|
| adda-create | AddaCreateView | adda_service.create_adda | Adda + AddaStageRecord(s) |
| worker-report | WorkerReportView | worker_task_service.report/complete | WorkerStageContribution, WST |
| adda-report-review | AddaReportReviewView | worker_task_service.set_verified_quantity | WSC.verified_quantity |
| layering-* (12) | Layering*View | layering stage service (via facade) + _shared.reopen | LayeringRecord/RollEntry, RemainingCloth, AddaStageRecord |
| pattern-* (10) | Pattern*View | pattern stage service | CuttingPatternRecord, verifications, photos |
| cutting-* (16) | Cutting*View | cutting stage service + allocation_service (allocate/void) | CuttingRecord, breakup, bundles, items, SWA(era-A) |
| barcode-gen-* (5) | BarcodeGen*View | barcode flow + barcode_service | BarcodeGenerationRecord, BarcodeBatch |
| product-flow | ProductFlowEditView | flow_service | WorkflowStage(+RoleRate) |
| costing | ProductionCostingView | cost_service (reads) | none (read-only) |
| stage-* (4) | Stage*View | access_service | Stage |

RBAC: production role + per-stage SKILL gate + assignment gate (worker reports
only on own assigned task — `StageViewAccessMixin`, V2-1c-iv isolation).

---
*Canonical depth (don't duplicate — read these):* business view →
[config/production/README.md](../../../../config/production/README.md) · file-by-file dev
view → [docs/apps/production/GUIDE.md](../../../apps/production/GUIDE.md) · this folder =
the NAVIGATION + FLOW layer only.*
