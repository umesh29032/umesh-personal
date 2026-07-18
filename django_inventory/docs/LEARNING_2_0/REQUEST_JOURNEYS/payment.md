---
id: l2-request-journeys-payment
type: request-journey
status: active
owner: handwritten
scope: payment (request-journey)
anchors: —
verified: 2026-07-13
---

# Journey: Payment (cash to worker — payment-only)

## TL;DR (1 min)
Pay cash against pending payable. Recovery is REFUSED here (it's the Adda settlement's job).

**URL** `expense:settlement-create` POST `/expense/workers/<pk>/settle/`. **View**
`expense/views.py:SettlementCreateView`; refuses stray `recover_*`.
**Form** SettlementForm (amount/method/date). **Service** `settlement_service.create_settlement`
(recoveries=None; raises if passed). **Models read** ledger (pending payable),
outstanding_advances (display only). **Models written** PayrollSettlement (INSERT)
+ WorkerLedgerEntry (debit settlement_payment, via ledger_service). **Tx** atomic.
**RBAC** management. **ADRs** 0005 (settlement≠payment). **Tables**
expense_payrollsettlement, expense_workerledgerentry. **Payload** `amount_paid=225&method=cash`.
**Before→after** payable 225 → ledger debit 225 → payable 0.

### How would I debug this in production?
- **First file:** `expense/views.py:SettlementCreateView` + `settlement_service.create_settlement`.
- **First breakpoint:** the recover_* refusal / log_debit call.
- **First query:** `SELECT entry_type,category,amount FROM expense_workerledgerentry WHERE worker_id=<id> AND category='settlement_payment';`
- **First log:** payment create + `ledger.entry.write`.
- **Failure modes:** "recovery refused" = correct (use Adda settlement); overpay blocked (amount > payable).
- **Expected DB state:** a PayrollSettlement + one settlement_payment debit; payable = live SUM after.
- **Recovery:** wrong payment → reverse its ledger debit + new correct PayrollSettlement (never edit).

### Confidence
**Verified from code (verified against commit f067daf0, 2026-06-12; re-verify the cited file if it changed)** (SettlementCreateView; create_settlement). Tests: test_views.py, test_expense.py.
