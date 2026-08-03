---
id: l2-data-flows-costing-flow
type: data-flow
status: active
owner: handwritten
scope: costing_flow (data-flow)
anchors: —
verified: 2026-07-13
---

# Data flow: Costing (standard-cost freeze)

## TL;DR
At stage advance, freeze the stage's STANDARD manufacturing cost. NOT worker pay.
Honest-NULL if unpriced. Grouped members → cost on payer, member yields nothing.

```
stage advance → adda_service advance funnel → cost_service.freeze_stage_cost [@atomic]
 compute_processing_cost: grouped? rate×qty or NULL
 sr.processing_cost = cost ; save UPDATE
reopen → clear_stage_cost → NULLs the frozen cost (re-freeze on re-complete)
```
**Reads:** WorkflowStage (method/rate/cost_billed_at), typed stage record (quantity).
**Writes:** production_addastagerecord (processing_cost + snapshots). **Tx:** atomic.
**Constraint:** NULL ≠ 0 (unpriced honest-NULL). **NEVER** added to settled labor (ADR-0009).

### Debug entry points
`cost_service.py` (compute / freeze / clear; query
`processing_cost,cost_frozen_at FROM production_addastagerecord`; log `cost.freeze`/`cost.clear`.
Failure: NULL cost (unpriced — expected); report doubled (someone summed standard+actual labor).
Recovery: reopen → clear → re-freeze.

### Confidence
**Verified from code (verified against commit f067daf0, 2026-06-12; re-verify the cited file if it changed)** (cost_service compute/freeze/clear installment 8). ADR-0009.
