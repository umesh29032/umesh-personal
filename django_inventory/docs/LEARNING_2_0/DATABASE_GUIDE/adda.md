---
id: l2-database-guide-adda
type: database-guide
status: active
owner: handwritten
scope: adda (model)
anchors: —
verified: 2026-07-13
---

# DB: Adda (+ AddaStageRecord) — the production batch

## TL;DR
What: one product's production batch + its per-stage records. Why: the unit all
work/cost/settlement hangs on. Writes: adda_service (create/advance), stage
services (records). Reads: everywhere. Breaks if removed: no production unit.
ADRs: 0010 (code). File: `config/production/models/adda.py`.

## Adda fields
code (max40, unique, editable=False, auto, global), product FK, current_stage FK(null),
status (in_progress/completed/…), started_at(auto), completed_at(null).

## AddaStageRecord fields
adda FK, workflow_stage FK, started_at/completed_at(null), frozen processing_cost
(honest-NULL), cost_*_snapshot, cost_frozen_at. unique_together(adda, workflow_stage).

## Example
`Adda(3-PATTI-001, product=3 Patti, status=in_progress, current_stage=Cutting)`;
`AddaStageRecord(3-PATTI-001, Cutting, processing_cost=NULL until priced)`.

## FK chain
`Adda → Product`; `AddaStageRecord → Adda` + `→ WorkflowStage`; WST/SWA/settlement/
barcode/roll all reference Adda or its SR.

## How data reaches / leaves
IN: create_adda (Adda + one SR per WorkflowStage). advance funnel updates
current_stage/status + freezes SR cost. OUT: never deleted (PROTECT anchors).

## SQL
```sql
SELECT code,status,current_stage_id FROM production_adda WHERE status='in_progress';
```

## Debug in production
No stage records = product had no flow. Code collision = counter lock bypassed
(shouldn't — select_for_update). Query by code.

### Verification Sources
production/models/adda.py + adda_service. **Verified from code (verified against commit f067daf0, 2026-06-12; re-verify the cited file if it changed)** (fields.
