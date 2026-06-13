## TL;DR (2 min)
Freezes a stage's STANDARD manufacturing cost (`processing_cost = ws.cost_rate ×
handler quantity`, role-independent) at stage advance; honest-NULL if unpriced.
This is NOT worker pay (that's settled earnings) — NEVER add the two (ADR-0009).
Also `role_rate_for` = earning rate source, with the grouped-member guard.

# Chokepoint: cost_service (standard-cost freeze + role rates)

File: `config/production/services/cost_service.py`

**Why exists:** stage ka MANUFACTURING (standard) cost freeze karta hai +
worker earning ka rate source deta hai. ADR-0009 ka enforcement point.

**Owns / writes:** `AddaStageRecord.processing_cost` (frozen at stage advance,
honest-NULL = unpriced, never 0) via `freeze`/`clear`. `role_rate_for` =
per-role earning rate (read).

**Who calls:** stage services (freeze on advance/complete); worker_task_service
+ allocation_service read `role_rate_for`.

**Invariants protected:** **THE COST DUALITY** — processing_cost (standard) and
settled worker earnings (actual) are TWO measurements of the SAME labor →
NEVER add them (ADR-0009). Price-at-time-of-order (frozen, later rate edits
don't rewrite history). **Grouped-member guard (C-1):** a stage with
`cost_billed_at` set yields NO role rate → member never double-pays (payer
stage covers the group).

**What breaks if bypassed:** retroactive cost rewrites; grouped-member
double-pay; the "full Adda cost" report adding labor twice.

Lessons: [../../LEARNING/07_COSTING.md](../../LEARNING/07_COSTING.md) ·
ADR [0009](../../adr/0009-cost-truth.md).

---
## v2 — VERIFIED trace 

`production/services/cost_service.py`:
```
compute_processing_cost — pure, no DB write: if ws.cost_billed_at_id is not None: → grouped MEMBER (cost billed at payer)
 method/rate from WorkflowStage; quantity from _quantity_for(sr)
 qty is None → cost None (UNPRICED, honest-NULL, not 0)
freeze_stage_cost: method,rate,qty,cost = compute_processing_cost(sr) sr.processing_cost = cost ; sr.save(_COST_FIELDS) UPDATE (frozen snapshot)
clear_stage_cost — reopen path: nulls the frozen cost (re-freeze on re-complete)
role_rate_for(ws, role) — grouped-member guard (C-1): cost_billed_at set → returns None
```

### How would I debug this in production?
- **First file:** `cost_service.py`. **First breakpoint:** `compute_processing_cost` (grouping) or `freeze_stage_cost`.
- **First query:** `SELECT id,processing_cost,cost_rate_snapshot,cost_quantity_snapshot,cost_frozen_at FROM production_addastagerecord WHERE adda_id=<id>;`
- **First log:** `cost.freeze` / `cost.clear` (service logs rate/qty/processing_cost).
- **Common failure modes:** `processing_cost` NULL = unpriced stage (honest-NULL,
 surfaces on costing dashboard — NOT a bug); cost looks doubled in a report =
 someone summed processing_cost + settled labor (ADR-0009 violation, the doc bug).
- **Expected DB state:** payable stages have settled labor in the ledger; standard
 cost in processing_cost; grouped members → cost on the payer, member rate None.
- **Recovery path:** wrong frozen cost → reopen the stage (`clear_stage_cost`) →
 re-complete re-freezes at the corrected rate/quantity.

### Confidence
**Verified from code (verified against commit f067daf0, 2026-06-12; re-verify the cited file if it changed)** (cost_service compute, freeze, role_rate_for;). Tests: production/tests/test_c1_hardening.py (grouped-member guard).
