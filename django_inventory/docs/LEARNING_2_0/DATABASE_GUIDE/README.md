# DATABASE GUIDE — models for someone weak in SQL

> START with the complete data-model + persistence doc:
> [../../LEARNING/02_DATABASE_RELATIONSHIPS.md](../../LEARNING/02_DATABASE_RELATIONSHIPS.md)
> (how a row is born, every model + example row, FK rules, write-flow) and the
> SQL course on real tables: [../../LEARNING/09_SQL_BEGINNER_TO_ADVANCED.md](../../LEARNING/09_SQL_BEGINNER_TO_ADVANCED.md).
> This folder adds ONE deep page per important model (Phase 5, pending).

**Per-model page template v2 (owner 2026-06-12)** — EVERY field explained in
simple language + why it exists; example row; FKs + relationships; what breaks
if removed; WHICH SERVICES write it; WHICH SCREENS read it; SQL examples; real
factory example. Older short template below is superseded by this:
Business meaning · Database meaning (table + columns) · Lifecycle · Relationships
· Example row · Factory example · Indexes · Constraints · FKs + why
PROTECT/CASCADE/SET_NULL chosen · What breaks if changed · ASCII relationship diagram.

| Model | Page | Field source (read, don't trust memory) |
|---|---|---|
| WorkerLedgerEntry | [worker_ledger_entry.md](worker_ledger_entry.md) ✅ | config/expense/models.py |
| AddaSettlement(+Item) | [adda_settlement.md](adda_settlement.md) ✅ | config/expense/models.py |
| StageWorkAssignment | [stage_work_assignment.md](stage_work_assignment.md) ✅ | config/expense/models.py |
| WorkerStageTask | [worker_stage_task.md](worker_stage_task.md) ✅ | config/production/models/worker_task.py |
| WorkerStageContribution | [worker_stage_contribution.md](worker_stage_contribution.md) ✅ | config/production/models/worker_task.py |
| Adda / AddaStageRecord | [adda.md](adda.md) ✅ | config/production/models/adda.py |
| WorkflowStage(+RoleRate) | [workflow_stage.md](workflow_stage.md) ✅ | config/production/models/core.py |
| ClothRoll / leftovers | [cloth_roll.md](cloth_roll.md) ✅ | config/raw_materials/models.py + production/models/layering.py |
| WorkerAdvance / Profile | [advance_profile.md](advance_profile.md) ✅ | config/expense/models.py |
| BarcodeBatch | [barcode_batch.md](barcode_batch.md) ✅ | config/tracking/models.py |

(Each model also has an architecture docstring IN its models.py — read that too.)
