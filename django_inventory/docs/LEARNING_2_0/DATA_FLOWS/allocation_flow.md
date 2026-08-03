---
id: l2-data-flows-allocation-flow
type: data-flow
status: active
owner: handwritten
scope: allocation_flow (data-flow)
anchors: —
verified: 2026-07-13
---

# Data flow: Allocation (era-A legacy, lever-gated)

## TL;DR
The OLD "credit at allocation" path. Default OFF (lever). When ON: SWA + ledger
credit at allocation time. Void reverses (era-A only).

```
INPUT (worker, qty, [bundle_item]) → LEVER ON? else REFUSE → allocate_stage_work [@atomic]
 already settled? REFUSE bundle_item select_for_update
 cost_rate set? qty>0? SWA INSERT (adda_settlement NULL)
 ledger_service.log_credit
VOID: void_allocation → era-B? REFUSE → reverse_entry (compensating debit) + voided_at
```
**Reads:** WorkflowStage rate, existing SWAs (era guard). **Writes:**
expense_stageworkassignment (era-A) + ledger credit. **Tx:** atomic +
select_for_update. **Events:** none.

### Debug entry points
`allocation_service.py` (allocate / void; query SWA
`WHERE adda_settlement_id IS NULL`; log `expense.allocate`/`expense.void_allocation`.
Failure: "allocation disabled" (lever off = expected default); void refused on era-B.
Recovery: `void_allocation` (era-A) / reverse the settlement (era-B).

### Confidence
**Verified from code (verified against commit f067daf0, 2026-06-12; re-verify the cited file if it changed)** (allocation_service installment 8). ADR-0007.
