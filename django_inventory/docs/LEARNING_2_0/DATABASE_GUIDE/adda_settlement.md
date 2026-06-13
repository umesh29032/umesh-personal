# DB: AddaSettlement (+ AddaSettlementItem) — the money event

## TL;DR
What: the Adda-level earning/recovery event + frozen per-worker snapshots. Why:
explicit, reviewable, reversible point where production→financial truth. Writes:
adda_settlement_service ONLY (gate 4b). Reads: settlement screens, KM. Breaks if
removed: money has no audit/approval record. ADRs: 0005/0007. File: `config/expense/models.py`.

## AddaSettlement fields (key)
reference (ADST-XXXX unique), adda FK, status (draft/finalized/reversed/superseded),
frozen totals, supersedes (self-FK, chain), settled_at/by. **finalized ⇒ settled_at** (CHECK).

## AddaSettlementItem fields (FROZEN, per worker)
adda_settlement FK, worker, expected_earning, advance_outstanding_before,
advance_recovered, final_payable. **recovered ≤ outstanding_before** (CHECK). Never recomputed.

## Example
`ADST-0003 (3-PATTI-001, finalized, expected_total=225)`; Item `(utest, expected=225, recovered=15, final_payable=210)`.

## FK chain
`AddaSettlement → Adda`; `AddaSettlementItem → AddaSettlement`; era-B SWA →
AddaSettlement; supersedes → AddaSettlement (correction chain).

## How data reaches / leaves
IN: create_draft (status=draft, no items) → finalize (items frozen + totals). OUT:
reverse → status reversed/superseded, items UNTOUCHED (audit). Drafts discardable.

## SQL
```sql
SELECT reference,status,settled_at FROM expense_addasettlement WHERE adda_id=<id> ORDER BY id;
```

## Debug in production
"Nothing to settle" = all lines credited. Chain confusion = follow supersedes.
Item ≠ ledger? items are frozen snapshots, ledger is live truth (expected).

### Verification Sources
expense/models.py (AddaSettlement/Item) + adda_settlement_service. **Verified from code (verified against commit f067daf0, 2026-06-12; re-verify the cited file if it changed).** Tests: test_adda_settlement_models.py/_service.py.
