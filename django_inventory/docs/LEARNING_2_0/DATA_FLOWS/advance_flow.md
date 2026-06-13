# Data flow: Advance (loan)

## TL;DR
Record a loan. INSERT-only. Does NOT touch the payable ledger — recovery is later, at settlement.

```
INPUT (worker, amount, date) → management gate → advance_service.record_advance [@atomic]
 WorkerAdvance.objects.create INSERT
```
**Reads:** worker. **Writes:** expense_workeradvance only. **Tx:** atomic.
**Events:** none. **Constraints:** amount ≥ 0. **Outstanding** = amount − Σ
non-reversed recovery PSIs (computed live by payroll_service, never stored).

### Debug entry points
`advance_service.py:record_advance`; query `expense_workeradvance WHERE
worker_id=`; outstanding via payroll_service. Failure: "payable changed?" — it
shouldn't (advance ≠ payable debit). Recovery: append-only; correct via settlement adjustment.

### Confidence
**Verified from code (verified against commit f067daf0, 2026-06-12; re-verify the cited file if it changed)** (advance_service. ADR-0005 (advance = separate pool).
