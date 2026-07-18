---
id: l2-request-journeys-advance
type: request-journey
status: active
owner: handwritten
scope: advance (request-journey)
anchors: —
verified: 2026-07-13
---

# Journey: Advance (give a worker a loan)

## TL;DR (1 min)
Record an advance (loan pool). Does NOT debit payable. Recovery happens later, only at Adda settlement.

**URL** `expense:advance-add` POST. **View** `expense/views.py:AdvanceCreateView`.
**Form** AdvanceForm (`expense/forms.py`). **Service** `advance_service.record_advance`. **Models read** worker. **Models written** WorkerAdvance (INSERT,.
**Tx** atomic. **RBAC** management. **ADRs** 0005 (advance = separate loan
pool, not a payable debit). **Tables** expense_workeradvance. **Payload**
`worker=7&amount=500&advance_date=…`. **Before→after** none → WorkerAdvance(₹500);
worker's payable UNCHANGED (recovery is at settlement).

### How would I debug this in production?
- **First file:** `advance_service.py:record_advance`.
- **First query:** `SELECT amount,advance_date FROM expense_workeradvance WHERE worker_id=<id>;` + remaining = amount − Σ recoveries (payroll_service).
- **First log:** advance create log.
- **Failure modes:** "advance reduced my payable" = misconception (it doesn't — recovery is at settlement); outstanding wrong = check reversed recovery PSIs.
- **Expected DB state:** advance row exists; outstanding = amount − non-reversed recoveries.
- **Recovery:** wrong advance → it's append-only; correct via a compensating entry/settlement adjustment (not edit).

### Confidence
**Verified from code (verified against commit f067daf0, 2026-06-12; re-verify the cited file if it changed)** (advance_service. Tests: expense tests.
