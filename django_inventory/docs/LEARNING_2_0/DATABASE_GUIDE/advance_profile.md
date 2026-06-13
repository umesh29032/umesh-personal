# DB: WorkerAdvance (+ WorkerProfile)

## TL;DR
What: worker loans + payroll metadata. Why: advance = separate loan pool (not a
payable debit). Writes: advance_service (advance), worker profile edit. Reads:
payroll_service (outstanding), settlement (recovery cap). Breaks if removed: no
loan tracking. ADRs: 0005. File: `config/expense/models.py`.

## WorkerAdvance fields
worker FK, amount Decimal, advance_date, entered_by FK, notes. Outstanding =
amount − Σ non-reversed recovery PSIs (computed, never stored).

## WorkerProfile fields
user (1:1), bank/UPI, opening advance/metadata. Mutable (not history).

## Example
`WorkerAdvance(utest, 500.00, 2026-06-01, entered_by=manager1)`.

## FK chain
`WorkerAdvance → User`; `PayrollSettlementItem.advance → WorkerAdvance` (recovery);
ledger advance_recovery debit references it.

## How data reaches / leaves
IN: record_advance (INSERT). Recovery happens at Adda settlement (PSI + ledger
debit). OUT: append-only; outstanding via live computation.

## SQL
```sql
SELECT amount,advance_date FROM expense_workeradvance WHERE worker_id=<id>;
```

## Debug in production
"Advance reduced payable" = misconception (it doesn't). Outstanding wrong =
check reversed recovery PSIs (reversed_at).

### Verification Sources
expense/models.py (WorkerAdvance/Profile) + advance_service + payroll_service. **Verified from code (verified against commit f067daf0, 2026-06-12; re-verify the cited file if it changed).** ADR-0005.
