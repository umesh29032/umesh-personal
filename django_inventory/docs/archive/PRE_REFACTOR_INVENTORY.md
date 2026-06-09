# Pre-Refactor Inventory — Baseline Snapshot

> **Purpose:** the "nothing vanished" oracle. Captured immediately before the M0–M7
> architecture remediation begins. When halfway through M2 (stage-engine refactor),
> diff against this to confirm no model / service / view / stage silently disappeared.
>
> - Date: 2026-06-09
> - Branch: `new_flask_app`
> - Parent commit (pre-baseline): `96a7d6c3`
> - Baseline tag: `pre-refactor-baseline`
> - Tests: **305 methods, all green** (~103s, `--settings=config.settings.local`)
> - Coverage: NOT measured (coverage tool not installed → install + record in P0.2 CI gate)

## Apps (8)
`accounts` · `core` · `raw_materials` · `production` · `tracking` · `expense` · `storefront` · `inventory`
(`core` = abstract bases, no tables. `inventory` = RBAC infra/hub/dashboards, 0 models, 21 legacy migrations.)

## Models — 56 classes total
| App | Classes | Notes |
|---|---|---|
| accounts | 5 | User, UserType, Skill, Role, SidebarItemRule |
| core | 4 | abstract bases (TimeStampedModel, ActiveManager, AbstractHistoryEntry, FieldChangeMixin) |
| raw_materials | 4 | ClothRoll, ClothType, ClothColor, StorageLocation |
| production | 24 | package: core.py(5) adda.py(2) layering.py(3) cutting.py(12) barcode.py(2) |
| tracking | 4 | AddaHistory, ClothRollHistory, ProductHistory, BatchBarcode |
| expense | 6 | StageWorkAssignment, WorkerLedgerEntry, WorkerAdvance, PayrollSettlement, PayrollSettlementItem, WorkerProfile |
| storefront | 7 | homepage/category/featured/hero/whyus/footer/nav |
| inventory | 0 | models relocated to accounts |

### production/models/ package (engine — stays central in M2)
```
core.py    5 classes  224 lines   (CostMethod, Product, Stage, WorkflowStage, WorkflowStageRoleRate)
adda.py    2 classes  176 lines   (Adda, AddaStageRecord ← polymorphic parent)
layering.py 3 classes 176 lines   (LayeringRecord, LayeringRollEntry, RemainingClothOfClothRoll) → moves to stages/layering/
cutting.py 12 classes 571 lines   (CuttingRecord + pattern/size/breakup/bundle/breakdown) → moves to stages/cutting/
barcode.py  2 classes  88 lines   (BarcodeGenerationRecord, LabelPrintQueue) → moves to stages/barcode_generation/
```

## Services — 27 files
- **accounts:** auth_service(41), permission_service(654), user_service(105)
- **production:** access_service(94), activity_service(180), adda_service(203), barcode_generation_service(402), cost_service(192), cutting_pattern_service(583), cutting_service(1189), flow_service(246), layering_service(800), product_service(111), product_size_service(112), _shared(153)
- **expense:** advance_service(37), allocation_service(155), ledger_service(123), payroll_service(293), settlement_service(174), _shared(10)
- **raw_materials:** master_service(66), roll_service(303)
- **tracking:** barcode_export_service(371), barcode_service(370), history_service(48)
- **storefront:** image_service(36)

## Views — 29 files
(thin per CLAUDE rule #4). God-file: `production/views/stage_views.py` = **1460 lines** (dissolves in M2.8).

## Stage surface (M2 target — verify each still works post-refactor)
| Stage | service LOC | dispatch sites today |
|---|---|---|
| layering | 800 | stage_views, adda_service (first-stage special-case), cost_service._quantity_for |
| cutting_pattern | 583 | stage_views |
| cutting | 1189 (→ split bundle/breakup/completion) | stage_views, cost_service, adda_views snapshot, complete_cutting sentinel |
| barcode_generation | 402 | stage_views |
| **stage_views.py** | **1460** | the central `if/elif stage_type==` dispatcher |

## RBAC files (M3 target)
- `accounts/services/permission_service.py` — **654 lines** (→ split into package M3.2)
- `accounts/models.py` — 293 (User/UserType/Skill/Role/SidebarItemRule)
- `inventory/middleware.py` — 86 (SidebarAccessMiddleware)
- `production/services/access_service.py` — 94 (skill-gated stage access)

## Expense files (payroll — M1/M4 target)
models.py(367) · admin(88) · forms(49) · views(265) · urls(15) ·
services: allocation(155) ledger(123) payroll(293) settlement(174) advance(37) _shared(10) ·
tests: test_expense(174) test_views(149) test_allocation_ui(166)

## Tracking files (M4 cycle-break target)
models.py(379) · admin(49) · views: barcode(193) dashboard(139) export(122) history(52) ·
services: barcode_service(370) barcode_export_service(371) history_service(48) ·
tests: test_barcode_export(311) test_barcode_service(250) test_scan_view(183)
> ⚠️ `tracking.services` reads `production` models for barcode gen/export — the `tracking→production`
> half of the cycle (M4.2 relocates barcode-assembly into production).

## Known cross-app edges at baseline (to be broken — see REMEDIATION_PLAN M4)
- `production ↔ expense` (stage_views.py:59-61 imports expense; allocation_service imports production) → M2/R1
- `production ↔ tracking` (mutual) → M4.2
- `accounts → production` (user_service → sync_layering_workers_for_skill) → M4.1
