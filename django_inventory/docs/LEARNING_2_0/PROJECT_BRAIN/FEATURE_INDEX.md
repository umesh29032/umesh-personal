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
| Cutting-pattern | production:pattern-* | Pattern*View | pattern stage service | CuttingPatternRecord | APPS/production |
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

Future features (not built): MissingPiece, Alter/Rework, G1-G7 → see PENDING_BACKLOG + ROADMAP.
