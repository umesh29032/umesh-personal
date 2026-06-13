## TL;DR (2 min)
Two services. `ledger_service` = the ONLY pen that writes WorkerLedgerEntry
(append-only; log_credit/log_debit/reverse_entry; balance = live SUM).
`settlement_service` = cash PAYMENT only (recovery refused — that's the Adda
settlement's job). Never write the ledger anywhere else.

# Chokepoint: ledger_service + settlement_service (money pen + cash)

Files: `config/expense/services/ledger_service.py` · `settlement_service.py`

## ledger_service — THE pen that writes money
**Owns / writes:** `WorkerLedgerEntry` (append-only). Functions: `log_credit`,
`log_debit`, `reverse_entry`, `worker_balance` (live SUM, never stored). CI
gate rule 5.
**Who calls:** other expense services ONLY (never views).
**Invariants:** append-only — row never UPDATE/DELETE; correction = opposite
REVERSAL row with original `entry_date` copied (so monthly totals net
in-period); `amount > 0` CHECK; balance = SUM(credit) − SUM(debit) always live.
**Breaks if bypassed:** silent, permanent balance corruption — no reference,
no reversal path.

## settlement_service — payment-ONLY (V2-2 narrowed)
**Owns / writes:** `PayrollSettlement` (+ its ledger `settlement_payment`
debit). **Recovery is REFUSED here** — it moved to adda_settlement_service.
**Why:** cash handover (worker-scoped, fungible) is a different event from
earning/recovery approval (Adda-scoped, reviewable, reversible). Mixing them
re-creates the ambiguity V2-2 removed.

Lessons: [../../LEARNING/06_FINANCIAL_TRUTH_AND_SETTLEMENT.md](../../LEARNING/06_FINANCIAL_TRUTH_AND_SETTLEMENT.md).

---
## v2 — VERIFIED traces 

**ledger_service** (`expense/services/ledger_service.py`):
```
_create_entry → WorkerLedgerEntry.objects.create(...) INSERT (amount>0)
log_credit / log_debit → _create_entry thin wrappers
reverse_entry: if entry.reverses_id is not None → (guard: can't reverse a reversal) _create_entry(entry_date=entry.entry_date COPIED, reverses=entry) INSERT opposite
worker_balance → SUM(credit) − SUM(debit) NO row, pure read
```
Key: reversal COPIES the original `entry_date` → the correction nets in
the SAME period. Append-only: no UPDATE/DELETE anywhere in the file.

**settlement_service** (`expense/services/settlement_service.py:create_settlement`:
```
@transaction.atomic if recoveries: raise ValidationError ← payment-only guard (recovery → Adda settlement)
 PayrollSettlement.objects.create(...) INSERT (cash event)
 ledger_service.log_debit(settlement_payment) INSERT ledger debit
```

### How would I debug this in production?
- **First file:** `expense/services/ledger_service.py` (balance) /
 `settlement_service.py` (payment).
- **First breakpoint:** `_create_entry` (every money row passes here) or
 `worker_balance`.
- **First query:**
 `SELECT entry_type,category,amount,entry_date,reverses_id FROM expense_workerledgerentry WHERE worker_id=<id> ORDER BY id;`
- **First log:** grep `ledger.entry.write` / `ledger.reverse` (the service logs every write).
- **Common failure modes:** balance "wrong" = a missing reversal or an extra
 row (it's a SUM, never edit); "recovery rejected" on payment = correct (use
 Adda settlement); reversal-of-reversal blocked by the guard.
- **Expected DB state:** every credit has a matching settlement/SWA reference;
 every reversal has `reverses_id` set + copied entry_date.
- **Recovery path:** wrong entry → `reverse_entry` (never edit/delete); a wrong
 cash payment → reverse its debit + new correct PayrollSettlement.

### Confidence
**Verified from code (verified against commit f067daf0, 2026-06-12; re-verify the cited file if it changed)** (ledger_service, settlement_service, lines
cited). Test coverage: expense/tests/test_expense.py, test_views.py (lever-pinned).
