---
id: l2-data-flows-payment-flow
type: data-flow
status: active
owner: handwritten
scope: payment_flow (data-flow)
anchors: —
verified: 2026-07-13
---

# Data flow: Payment (cash)

## TL;DR
Cash out against payable. One PayrollSettlement + one ledger debit. Recovery REFUSED here.

```
INPUT (amount_paid, method) → management gate → settlement_service.create_settlement [@atomic]
(POST /workers/<pk>/settle/) recover_* present? REFUSE PayrollSettlement INSERT
 amount ≤ pending payable ledger_service.log_debit(settlement_payment) INSERT
```
**Reads:** ledger (pending payable), outstanding_advances (display only).
**Writes:** expense_payrollsettlement + expense_workerledgerentry (debit).
**Tx:** atomic. **Constraints:** amount>0, ≤ payable.

### Debug entry points
`settlement_service.create_settlement` + `SettlementCreateView`,
recover_* refusal; query settlement_payment debits; log `ledger.entry.write`.
Failure: recovery rejected (correct — use Adda settlement); overpay blocked.
Recovery: reverse the debit + new payment.

### Confidence
**Verified from code (verified against commit f067daf0, 2026-06-12; re-verify the cited file if it changed)** (create_settlement, view. ADR-0005.
Chain: [../REQUEST_JOURNEYS/payment.md](../REQUEST_JOURNEYS/payment.md).
