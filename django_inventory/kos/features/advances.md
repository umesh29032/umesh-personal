---
id: feature-advances
type: feature
verified: 2026-07-19
knowledge_confidence: verified_against_code
answers: "How does the factory lend workers money without the loan corrupting the earnings math?"
related: [feature-ledger, feature-payroll, feature-settlement]
---

# Advances — the loan pool that never touches earnings

> 📂 [Features](README.md) · [LOS home](../README.md) — *pehle yeh page, phir code.*

## Business Purpose

Factory reality: a worker needs ₹500 today, mid-month, before any settlement.
The owner lends it. The dangerous design — and what most naive systems do —
is treating that loan as *negative earnings*. This system keeps advances in
a **separate pool**: a loan is recorded when given, and recovered **only**
when the owner explicitly chooses, at settlement time, advance by advance.

## Mental Model

> **Two pockets, one owner.** Earnings pocket fills through work; loan
> pocket fills through trust. Money moves between them only when the owner
> deliberately moves it (recovery at settlement) — never automatically,
> never silently. If the pockets ever blur, both numbers become unprovable.

## 💡 Samjho Aise

Udhaar dena dosti hai, hisaab business hai. Worker ko ₹500 diye — yeh
uski kamai ka hissa NAHI, alag udhaar hai. Kamai apni jagah badhti rahegi.
Jab Adda ka hisaab hoga, tab malik khud tay karega: "is baar ₹200 kaat lo,
baaki agli baar." System kabhi apne aap nahi kaatta — kyunki auto-kataai
par jhagda hota hai, chosen-kataai par nahi.

## Technical Deep Dive

**Recording** — `advance_service.record_advance` (SOLE writer of
`WorkerAdvance`, ADR-0002), at `/expense/advances/add/`:

- Immutable row: worker, amount (>0, DB CHECK `expense_advance_amount_positive`),
  `advance_date`, notes, attachment (proof photo), entered_by.
- **NO ledger entry is written.** The old design posted advances to the
  ledger (legacy `advance` category still visible in old rows); today the
  loan pool and the earnings book are fully separate.
- **Temporary business rule** (owner, hostile-review M-2): monthly-salary
  workers can't take advances — *both* recovery paths are unreachable for
  them (no settlement lines; payable always 0), so the money would sit
  outstanding until F&F write-off. The service refuses with a full
  explanation. A rule that explains itself survives; a bare `raise` gets
  deleted by the next confused developer.

**Derived, never stored:**
- `advance_remaining(advance)` = amount − Σ non-reversed recoveries against it
- `advance_outstanding(worker)` = Σ remaining across their advances
- `outstanding_advances_bulk(workers)` — the overview's grouped aggregate
  (one query for the whole board, not N)

**Recovery** — happens in exactly ONE place: Adda-settlement finalize
([settlement](settlement.md)). Owner picks per-advance amounts; each is
validated `≤ remaining` **under `select_for_update`**; writes a ledger
DEBIT (`advance_recovery`) + a `PayrollSettlementItem` linking advance ↔
debit entry. Cash payment (`create_settlement`) REFUSES recoveries since
V2-2 — one event, one meaning.

**Forgiveness** — F&F write-off (super-admin + mandatory reason): audited
PSI row, **no ledger debit** — a forgiven loan is not a payment.

## Debugging Guide

| Symptom | Start |
|---|---|
| Outstanding looks wrong | `advance_remaining` per advance in shell; check `reversed_at` stamps on PSI rows — reversed recoveries restore remaining |
| "Recovery exceeds remaining" | Correct guard — someone else recovered concurrently; re-read under lock showed the truth |
| Monthly worker needs a loan | By design refused — read the service's own explanation; handle via salary for now |
| Advance "disappeared" after F&F | Look for the write-off PSI row + reason — forgiven, not deleted |

## Change Impact

Recovery path in `adda_settlement_service.finalize` · `payroll_service`
derivations (remaining/outstanding/bulk) · overview + worker-detail +
My Earnings surfaces · F&F write-offs (`fnf_service`) · tests
`test_r7_fnf.py`, `test_adda_settlement_service.py` recovery cases.

## AI Implementation Pitfalls

- ❌ Auto-recovering advances (FIFO or otherwise) — recovery is an OWNER
  decision, per advance, at settlement. Never automate it.
- ❌ Posting a ledger entry when recording an advance — the loan pool is
  ledger-free by design; only RECOVERY touches the ledger.
- ❌ Storing `remaining` on the advance row — derived from recoveries, always.
- ❌ Netting outstanding against payable in a display "for convenience" —
  the two numbers answer different questions; blending them creates disputes.
- ✅ Always verify: `advance_deducted == Σ items.amount_recovered` identity
  and the monthly-worker refusal test stay green.

## Interview Notes

*Interview Signal: 🟡 Mid — domain-modeling judgment.*

**Q. "Model employee loans alongside payroll."**
- *Short:* Separate pool; recovery as explicit, audited events; everything derived.
- *Senior:* The failure mode is coupling — auto-netting makes both loan and
  wage history unauditable. Keep the loan immutable, recoveries as linked
  events with their own reversal semantics, and refuse loans where no
  recovery path exists (a loan you can't recover is a write-off waiting).
- *Project example:* `WorkerAdvance` (no ledger) → recovery only at ADST
  finalize (`≤ remaining` under lock) → F&F write-off as audited non-payment.
  The monthly-worker refusal is exactly the "no recovery path" principle in code.
- *Follow-ups:* "Interest?" (new event type, same pool) · "Partial reversals
  of a recovery?" (reverse the PSI's ledger entry — the `reversed_at` stamp
  restores remaining).

## 🧠 Remember This

Udhaar alag jeb, kamai alag jeb. Jeb-badli sirf malik ke haath se, settlement
ke waqt, hisaab-ke-andar-hisaab ke saath. Remaining kabhi likha nahi jaata —
gina jaata hai. Aur jis udhaar ka wapas aane ka raasta hi nahi, wo udhaar
dena hi mana hai.

## 30-Second Revision

- `record_advance` = immutable row, NO ledger entry, amount>0 CHECK
- Recovery: ONLY at ADST finalize, owner-chosen, ≤ remaining under lock
- Cash event refuses recoveries (V2-2, pinned)
- remaining/outstanding = derived; bulk aggregate for the board
- Monthly workers: refused (no recovery path) — temporary owner rule M-2
- F&F write-off = audited PSI + reason, no debit

## Implementation References

- Design: [docs/ARCHITECTURE_V2.md](../../docs/ARCHITECTURE_V2.md) §11 · ADR [0002](../../docs/adr/0002-single-writer-per-ledger-and-history-table.md)

## Code References
- `config/expense/services/advance_service.py` (whole file — small, read it) · recovery in `adda_settlement_service.py` · derivations in `payroll_service.py`
- Tests: `config/expense/tests/test_r7_fnf.py` · settlement recovery cases

## Related Concepts

[ledger](ledger.md) · [payroll](payroll.md) · [settlement](settlement.md) ·
[single-writer](../concepts/architecture/single-writer.md)
