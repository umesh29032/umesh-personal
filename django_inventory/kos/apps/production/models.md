---
id: app-production-models
type: app
verified: 2026-07-19
knowledge_confidence: verified_against_code
answers: "35 production models in 7 modules — which holds what, who writes it, what protects it?"
related: [app-production, feature-stage-tracking, feature-cutting]
---

# production — model knowledge (`config/production/models/`, 7 modules · 35 classes)

> 📂 [production app](README.md) · [Apps](../README.md) · [LOS home](../../README.md)

## `core.py` — flow configuration + rates + pool (12 classes)

| Model | Why · writers |
|---|---|
| `Product` | manufacturing master (NOT catalog) · SA-only CRUD via `product_service` |
| `Stage` | reusable library step: access rules (skills/roles), work type (Manual\|Machine⇒`MachineType` mandatory, DB CHECK), default rate · SA CRUD |
| `StageCategory` / `MachineType` | R10-C data-driven masters (rows, not code) · display grouping NEVER gates money/access |
| `WorkflowStage` | Stage attached to ONE product: order, rate, `cost_method` (incl. FIXED), billed-at grouping, pay-eligibility, `allocation_dimensions` grain · writer `flow_service` (grain monotonicity enforced) |
| `WorkflowStageRoleRate` → `AddaStageRoleRate` | per-role rates on the flow → **frozen per-Adda at stage-record creation** (S1/S2: later edits never re-price) · writer `stage_rate_service` |
| `RateCorrectionAudit` | S1.1 rerate audit (old→new, actor, reason) · sole writer `stage_rate_service.rerate_stage_role` |
| `AllocationDimensions` / `CostMethod` | TextChoices enums — the grain + costing vocabularies |
| `StagePoolSnapshot` (SPS) | frozen good a stage OFFERS downstream (write-once at complete; cutting excluded — reads APSCPB) · sole writer `pool_service` |
| `WorkerStageAllocation` (WSA) | a worker's allocated slice; append-only, void-not-delete; **NO money, owner-locked ⊥** · sole writer `pool_service` |

## `adda.py` — the batch (3)

| Model | Why · writers |
|---|---|
| `Adda` | THE central noun: one batch of one product; auto code · `adda_service` |
| `CuttingStream` | one lay→pattern→cut lane: identity (adda, fabric_group, seq); seq>1 = declared act + mandatory reason; JOIN gates downstream |
| `AddaStageRecord` (ASR) | execution row per Adda×WorkflowStage: status, timestamps (duration AUTO — owner rule), **frozen `processing_cost`** (ADR-0009 cost-truth) |

## `worker_task.py` — production truth (2) 🔒

| Model | Why · writers |
|---|---|
| `WorkerStageTask` (WST) | assignment FSM: assigned→in_progress→completed→[verified]/cancelled; ≤1 active per (ASR, worker); cancel≠delete · **sole writer `worker_task_service` (C-TM, CI gate 4/4)** |
| `WorkerStageContribution` (WSC) | the dimensional line: (color,size) × good/alter/missing (`wsc_gam_nonneg_sum_positive`); `reported` immutable, `verified_quantity` = red pen; `settlement_line` FK = era-B provenance stamp · same sole writer |

Deep page: [stage-tracking](../../features/stage-tracking.md).

## `cutting.py` — the mint (12)

Chain, in birth order ([cutting](../../features/cutting.md)):
`ProductPattern` (Production Component; historical name kept) +
`ProductPatternAssignment` (pieces per garment) → `CuttingPatternRecord` +
`Photo` + `Verification` + `SizeAllocation` + `ProductSize` (the Pattern-
Design evidence set) → `CuttingRecord` → `CuttingPieceBreakup`
(size×color×pattern counts) → `CuttingBundle`/`CuttingBundleItem` (physical
grouping) → **`AddaProductSizeColorPieceBreakdown` (APSCPB)** — the single
verified count everything downstream consumes (barcodes, cutting's pool,
reconciliations). Writers: `stages/cutting/service.py` +
`stages/cutting_pattern/service.py`.

## `layering.py` (3)

`LayeringRecord` + `LayeringRollEntry` (rolls attached, weights) +
`RemainingClothOfClothRoll` (**leftovers = tracked wealth, mandatory at
complete**). Writer: `stages/layering/service.py`.

## `barcode.py` (2)

`BarcodeGenerationRecord` (the stage's run) + `LabelPrintQueue`. Ranges
themselves = `tracking.BarcodeBatch` (other app — piece identity (adda,
seq), printed payloads PERMANENT, ADR-0010).

## Cross-model laws

- **Frozen snapshots everywhere money-adjacent:** `processing_cost`,
  `AddaStageRoleRate`, `expected_*` — config edits never rewrite history.
- Append-only citizenship: WST cancel, WSA void, streams append post-join.
- Grain monotonicity down the flow; pool starts at cutting (pre-piece
  stages = NONE).
- Model docstrings are teaching-grade — read them before asking.

## Required Knowledge (this page)

- [ ] FSMs + append-only citizenship → [stage-tracking §DSA](../../features/stage-tracking.md) · [append-only-tables](../../concepts/database-design/append-only-tables.md)
- [ ] Frozen-snapshot thinking → [two-truths](../../concepts/architecture/two-truths.md)
- [ ] Constraint armor (wsc_gam…) → [constraints](../../concepts/postgresql/constraints.md)

## Learning Graph

**Before:** [cloth-to-garment](../../flows/cloth-to-garment.md) (the story these tables record).
**After:** [services.md](services.md) (the pens) → the model docstrings (teaching-grade).
