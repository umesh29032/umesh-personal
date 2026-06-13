# DB: WorkflowStage (+ RoleRate) — per-product stage policy

## TL;DR
What: a product's stage at an order, with cost/pay policy. Why: data-driven flow
(no code per product). Writes: flow_service (flow editor). Reads: adda_service
(create), cost_service (rate), worker_task_service (freeze). Breaks if removed:
Addas can't be built. ADRs: 0009 (cost_rate dual-duty). File: `config/production/models/core.py`.

## Fields (key)
product FK, order (int), stage FK→Stage (library), cost_method, **cost_rate**
(Decimal, null — DUAL: standard cost + default pay), credits_workers (bool),
**cost_billed_at** self-FK (grouping → member cost billed at payer). RoleRate:
(workflow_stage, role) → cost_rate override. (Future: scan_policy / TM-1 field.)

## Example
`WorkflowStage(product=3 Patti, order=3, stage=Cutting, cost_rate=3.00, credits_workers=True, cost_billed_at=NULL)`

## FK chain
`WorkflowStage → Product` + `→ Stage`; `AddaStageRecord → WorkflowStage`;
`WorkflowStageRoleRate → WorkflowStage`.

## How data reaches / leaves
IN: flow editor (flow_service, with grouping guards). OUT: protected while Addas
use it. cost_rate read at freeze + role_rate_for (grouped → None).

## SQL
```sql
SELECT order,stage_id,cost_rate,credits_workers,cost_billed_at_id
FROM production_workflowstage WHERE product_id=<id> ORDER BY "order";
```

## Debug in production
Grouped-member double-pay → role rate on a cost_billed_at member (C-1 guard
returns None). Unpriced stage → cost_rate NULL (honest-NULL).

### Verification Sources
production/models/core.py (WorkflowStage+) + cost_service. **Verified from code (verified against commit f067daf0, 2026-06-12; re-verify the cited file if it changed).** ADR-0009.
