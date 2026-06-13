# DB: WorkerLedgerEntry — the money kitab

## TL;DR
What: append-only money rows. Why: single financial truth, balance=live SUM.
Writes: ledger_service ONLY. Reads: payroll_service (My Earnings, payroll, worker
detail). Breaks if removed: no financial truth at all. ADRs: 0002/0005. Future:
G1/G3 read it for cost/loss. File: `config/expense/models.py` (class.

## Every field
| Field | Type | Meaning |
|---|---|---|
| worker | FK→User (PROTECT) | whose money |
| entry_type | char(8) | credit (↑payable) / debit (↓payable) |
| category | char(24) | stage_earning / advance_recovery / settlement_payment / reversal / … |
| amount | Decimal(12,2), CHECK>0 | always positive; direction is entry_type |
| entry_date | Date | business date (reversal COPIES original → in-period netting) |
| assignment | FK→SWA (PROTECT, null) | which earning line (provenance) |
| advance | FK→WorkerAdvance (PROTECT, null) | which loan (recovery) |
| settlement | FK→PayrollSettlement (PROTECT, null) | which cash payment |
| reverses | self-FK (null, UNIQUE) | the entry this one reverses |

## Example row
`id=10, worker=utest, credit, stage_earning, 180.00, entry_date=2026-06-11, assignment=SWA#42, reverses=NULL`

## FK chain
`WorkerLedgerEntry.assignment → StageWorkAssignment.adda_settlement → AddaSettlement`.
Reversal: `reverses → another WorkerLedgerEntry`. Worker → User.

## How data reaches / leaves
IN: ledger_service.log_credit/log_debit (at settlement finalize / payment / recovery).
OUT: never deleted/edited; "removed" effect = a reverse_entry row. Balance read =
`SUM(credit)−SUM(debit)` (worker_balance).

## SQL
```sql
SELECT SUM(CASE WHEN entry_type='credit' THEN amount ELSE -amount END)
FROM expense_workerledgerentry WHERE worker_id=7; -- live payable
```

## Factory example
utest earns ₹180 (credit) at ADST-0003; ₹15 advance recovered (debit); later
₹165 paid (debit). Balance walks 180 → 165 → 0.

## Debug in production
Balance wrong → list rows ordered by id, look for missing reversal / extra row
(never a stored value). Log `ledger.entry.write`. Recovery = reverse_entry.

### Verification Sources
Read expense/models.py (WorkerLedgerEntry, ledger_service.py. **Verified from code (verified against commit f067daf0, 2026-06-12; re-verify the cited file if it changed).** Tests: test_expense.py.
