---
id: feature-index
type: topic-canonical
status: active
owner: handwritten
scope: all features — the features/-layer seed (Design Record R3)
anchors: config/inventory/urls.py, config/production/urls.py, config/expense/urls.py, config/machines/urls.py, config/patterns_ai/urls.py
verified: 2026-07-13
---

# FEATURE INDEX — feature → where it lives

## TL;DR
Each row: a feature → its URL name · primary View · owning Service · key
Model(s) · canonical doc. Jump straight to the layer you need.

| Feature | URL name | View | Service | Model(s) | Doc |
|---|---|---|---|---|---|
| Login (OTP/password) | accounts:login / login_password | Login/PasswordLogin | auth_service | User | APPS/accounts |
| User/role admin | accounts:user_* / skill_* | User/Skill CRUD | user_service, permission_service | User, Role | APPS/accounts |
| Adda create | production:adda-create | AddaCreateView | adda_service.create_adda | Adda, AddaStageRecord | REQUEST_JOURNEYS/adda_creation |
| Worker assignment | (stage workspaces) | Layering/Cutting/etc | worker_task_service.set_stage_workers | WorkerStageTask | CHOKEPOINTS/worker_task_service |
| Worker reporting | production:worker-report | WorkerReportView | worker_task_service.report/complete | WorkerStageContribution | REQUEST_JOURNEYS/worker_reporting |
| Verify quantity (P1) | production:adda-report-review | AddaReportReviewView | worker_task_service.set_verified_quantity | WSC.verified_quantity | ARCHITECTURE_EXPLAINED/09 |
| Layering | production:layering-* | Layering*View | layering stage service | LayeringRecord, RollEntry, RemainingCloth | APPS/production |
| Cutting | production:cutting-* | Cutting*View | cutting stage service | CuttingRecord, breakup, bundles | APPS/production |
| Cutting-pattern (display: "Pattern Design" — stage-trio spec 2026-07-05) | production:pattern-* | Pattern*View | pattern stage service | CuttingPatternRecord | APPS/production + STAGE_TRIO_SPEC_IMPACT |
| Barcode generation | production:barcode-gen-* | BarcodeGen*View | barcode flow + barcode_service | BarcodeGenerationRecord, BarcodeBatch | APPS/tracking |
| Stage completion / reopen | (per stage)/reopen | *CompleteView/*ReopenView | _shared.reopen_stage_record | AddaStageRecord | ARCHITECTURE_EXPLAINED/08 |
| Costing dashboard | production:costing | ProductionCostingView | cost_service (reads) | AddaStageRecord.processing_cost | CHOKEPOINTS/cost_service |
| Flow editor (rates/grouping) | production:product-flow | ProductFlowEditView | flow_service | WorkflowStage(+RoleRate) | ADR-0009 |
| Settlement queue | expense:adda-settlement-list | AddaSettlementListView | adda_settlement_service.settlement_queue | AddaSettlement | REQUEST_JOURNEYS/settlement_finalize |
| Settlement finalize | expense:adda-settlement-detail | AddaSettlementDetailView | adda_settlement_service.finalize | ADST, Item, SWA, ledger | CHOKEPOINTS/adda_settlement_service |
| Settlement reverse/supersede | (same, action=reverse) | AddaSettlementDetailView | adda_settlement_service.reverse | ADST, ledger reversal | ARCHITECTURE_EXPLAINED/08 |
| Advance | expense:advance-add | AdvanceCreateView | advance_service | WorkerAdvance | APPS/expense |
| Payment (cash) | expense:settlement-create | SettlementCreateView | settlement_service | PayrollSettlement, ledger debit | CHOKEPOINTS/ledger_and_payment |
| My Earnings (worker) | expense:my-earnings | MyEarningsView | payroll_service (reads) | ledger (SUM) | APPS/expense |
| Roll intake | raw_materials:roll-bulk-create | RollBulkCreateView | roll_service.bulk_create_rolls | ClothRoll | APPS/raw_materials |
| Roll→Adda assign | raw_materials:roll-assign | RollAssignView | roll_service.assign_roll_to_adda | ClothRoll | APPS/raw_materials |
| Leftover consume | (no UI yet) | — | roll_service.consume_leftover | RemainingCloth | ADR-0009 §5 |
| Sidebar/access control | inventory access-control/* | access_hub/role/sidebar | permission_service | Role, SidebarItemRule | APPS/inventory |
| Public homepage | / | public_views | master_service | storefront config models | APPS/storefront |
| Machines: assets + operator possession (R10-A, 2026-07-05) | machines:* | machine list/create/assign views | machines app services (possession windows) | Machine, machine-assignment/possession models (see GUIDE) | apps/machines/GUIDE + config/machines/README |
| Pattern layout tool (blueprint → usage → outcome/void; READY gate; exports) | patterns_ai:* | pattern dashboard/workspace views | patterns_ai services (blueprint gate, usage lifecycle) | blueprint/usage/outcome models (see GUIDE) | apps/patterns_ai/GUIDE + AI_PATTERN_INTELLIGENCE/PLATFORM_STATUS |
| Multi-worker pool split + blind reporting (OP-1, 2026-07-05) | production: stage workspaces + worker-report | pool split UI + manager board | pool_service.allocate + worker_task_service | WorkerStageAllocation, StagePoolSnapshot, WSC | CHOKEPOINTS/pool_service + OP1_EXECUTION_PLAN |
| Adda 360 hub (A360) | production: adda-360 pages | A360 management views (read aggregates) | reads across settlement/task/pool services | Adda + per-stage aggregates (no new writes) | A360_EXECUTION_PLAN |

Future features (not built): MissingPiece, Alter/Rework, G1-G7 → see PENDING_BACKLOG + ROADMAP.

_Row-set refreshed 2026-07-13 (Phase-7 Q-A1, doc-sourced from MANUFACTURING_V1_FREEZE + app
GUIDEs + execution-plan receipts; pre-refresh vintage was 2026-06-13 — machines/patterns_ai/
OP-1/A360 rows were absent, F-D-08)._
