---
id: l2-request-journeys-settlement-reverse
type: request-journey
status: active
owner: handwritten
scope: settlement_reverse (request-journey)
anchors: —
verified: 2026-07-13
---

# Journey: Settlement Reverse / Supersede (fix a finalized settlement)

## TL;DR (1 min)
Finalized settlement wrong? Reverse it (compensating ledger rows + SWA void) —
optionally Supersede (opens a successor draft; chain kept). History never edited.

**URL** `expense:adda-settlement-detail` POST `action=reverse|supersede`. **View**
`AddaSettlementDetailView.post`. **Service** `adda_settlement_service.reverse_adda_settlement(supersede=bool)`.
**Models read** the settlement's earning_lines (SWAs), their ledger credits,
recovery PSIs. **Models written** WorkerLedgerEntry (compensating debit/credit via
reverse_entry) · StageWorkAssignment (voided_at) · PayrollSettlementItem (reversed_at
stamp) · AddaSettlement (status=reversed|superseded) · successor AddaSettlement
(draft, if supersede) · AddaHistory (SETTLEMENT_REVERSED/SUPERSEDED). **Tx** atomic
+ advisory lock + select_for_update on earning_lines. **RBAC** management.
**ADRs** 0007 (correction model), 0002. **Tables** as finalize + the successor.

### How would I debug this in production?
- **First file:** `adda_settlement_service.py:reverse_adda_settlement` (~.
- **First breakpoint:** the earning_lines select_for_update + reverse_entry loop.
- **First query:** `SELECT id,voided_at,adda_settlement_id FROM expense_stageworkassignment WHERE adda_settlement_id=<ADST id>;` + ledger rows for the workers.
- **First log:** settlement reverse + `ledger.reverse`.
- **Failure modes:** can't reverse a draft (only finalized); re-settle after reverse = the era guard re-arms (lines settleable again).
- **Expected DB state:** original credits each have a reversal row; SWAs voided; frozen items UNCHANGED (audit record); status reversed/superseded.
- **Recovery path:** this IS the recovery path. Then settle the successor draft correctly.

### Confidence
**Verified from code (verified against commit f067daf0, 2026-06-12; re-verify the cited file if it changed)** (reverse_adda_settlement+). Tests: test_adda_settlement_service.py (ReversalLifecycleTests), test_v2_3_guards.py.
