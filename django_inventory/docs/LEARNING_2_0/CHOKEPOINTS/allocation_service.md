## TL;DR (2 min)
The LEGACY earning path (era-A). Default OFF since V2-3 (`LEDGER_CREDIT_AT_
ALLOCATION=False`); env True = tested rollback lever. Writes era-A SWA + its
ledger credit; void reverses era-A only (era-B refuses → reverse the settlement).

# Chokepoint: allocation_service (legacy earning path — rollback lever)

File: `config/expense/services/allocation_service.py`

**Why exists:** purana "allocation par hi credit" rasta (era-A). V2-3 ke baad
DEFAULT band (`LEDGER_CREDIT_AT_ALLOCATION=False`); env `True` = tested
rollback lever. Era-A rows readable + reversible forever (ADR-0007).

**Owns / writes:** era-A `StageWorkAssignment` (creation, lever-ON only) + its
era-A void. Shares CI gate [4c/4] with adda_settlement_service.

**Who can call:** management; but `allocate_stage_work` REFUSES when the lever
is off, and refuses if the worker-stage already has a settlement credit
(symmetric guard). `void_allocation` REFUSES era-B lines ("reverse the
settlement instead").

**Invariants protected:** symmetric double-credit guard (allocation ↔
settlement never both pay the same line) · era-B lines untouchable here.

**What breaks if bypassed:** legacy path racing a settlement = the exact
double-credit V2-3 closed.

ADR [0007](../../adr/0007-allocation-era-ledger-cutover.md). Costing duality:
[../../LEARNING/07_COSTING.md](../../LEARNING/07_COSTING.md).

---
## v2 — VERIFIED trace 

`expense/services/allocation_service.py`:
```
allocate_stage_work: if not LEDGER_CREDIT_AT_ALLOCATION: raise ← lever OFF (default) refuses if SWA(...,adda_settlement__isnull=False).exists: raise ← already settled (symmetric guard) if no cost_rate: raise ; if qty<=0: raise CuttingBundleItem.select_for_update (item allocation — lock) StageWorkAssignment.objects.create(...) INSERT era-A line (adda_settlement NULL) ledger_service.log_credit(...) INSERT credit
void_allocation: SWA.select_for_update ; if voided: raise if adda_settlement_id is not None: raise ← era-B line REFUSES (reverse settlement) ledger_service.reverse_entry(credit) compensating debit assignment.voided_at = now ; save soft void
```

### How would I debug this in production?
- **First file:** `allocation_service.py`. **First breakpoint:** `allocate_stage_work` (lever check) or `void_allocation` (era guard).
- **First query:** `SELECT id,adda_settlement_id,voided_at,earning_amount_snapshot FROM expense_stageworkassignment WHERE stage_record_id=<id>;`
- **First log:** `expense.allocate` / `expense.void_allocation`.
- **Common failure modes:** "allocation disabled" = lever off (expected default);
 "already credited by a settlement" = era-B exists (correct); void refused on a
 settlement line (correct — reverse the ADST).
- **Expected DB state:** era-A rows have `adda_settlement_id IS NULL`; era-B have it set.
- **Recovery path:** wrong era-A allocation → `void_allocation` (reverses credit).
 era-B mistake → reverse the AddaSettlement instead.

### Confidence
**Verified from code (verified against commit f067daf0, 2026-06-12; re-verify the cited file if it changed)** (allocation_service). Tests:
expense/tests/test_v2_3_guards.py (void/era guards), test_adda_settlement_views.py (lever).
