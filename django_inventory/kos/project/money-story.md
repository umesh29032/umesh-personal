---
id: project-money-story
type: project
verified: 2026-07-19
knowledge_confidence: verified_against_code
answers: "How does money actually work in this system — from 'I stitched 40 pieces' to provable rupees?"
related: [feature-settlement, flow-worker-gets-paid, concept-django-transactions]
---

# The Money Story — two truths and one gate

> 📂 [Project — the WHY layer](README.md) · [KOS home](../README.md)

## Business Purpose

Every payroll dispute in a factory is the same argument: *"I did the work"*
vs *"I never approved that."* This system ends the argument structurally, by
keeping **two separate truths** and connecting them through **one auditable
gate**:

- **Production truth** — what work happened (who, what, how much, verified).
- **Financial truth** — what money exists (earned, recovered, paid).

Work being reported creates NO money. Money is born only when the owner
**settles** — and from that moment it is immutable, traceable, and provable.

## 💡 Samjho Aise

Do alag kitaabein hain. Ek **kaam ki kitaab** (production) — worker likhta
hai "40 piece kiye", manager kaat-peet kar sakta hai "38 sahi nikle". Doosri
**paise ki kitaab** (ledger) — is mein sirf MALIK ke settle karne par entry
hoti hai, aur **pen se likhi entry kabhi mitti nahi** — galti hui to neeche
ulti entry. Kaam ki kitaab pencil hai, paise ki kitaab pen. **Settlement =
pencil se pen mein utaarna.**

## Technical Deep Dive

**The worker's three numbers** (non-overlapping, proven by tests):

```
EXPECTED  ──settle──▶  EARNED  ──cash──▶  PAID
unsettled work         ledger CREDITs      ledger DEBITs
(expected_* frozen     (stage_earning,     (settlement_payment,
 = visibility ONLY,     at AddaSettlement    at PayrollSettlement —
 NO ledger row)         finalize)            a SEPARATE event)
```

**The lifecycle** (canonical: [PKM §4](../../docs/PROJECT_KNOWLEDGE_MAP.md)):

1. Worker reports → `WorkerStageContribution`; rate frozen into
   `expected_rate` — visibility, never money (**Option B**,
   [ADR-0005](../../docs/adr/0005-production-truth-vs-financial-truth-option-b.md)).
2. Manager verifies → `verified_quantity` on the SAME row; production truth
   corrected freely because no money exists yet.
3. Owner settles the Adda → [settlement feature](../features/settlement.md):
   DRAFT (scratchpad) → FINALIZE = the atomic money write — earning lines +
   ledger CREDITs (qty = verified ?? reported × frozen rate) + owner-chosen
   advance-recovery DEBITs + frozen per-worker snapshots.
4. Mistake? → REVERSE or REVERSE+SUPERSEDE — compensating entries, chain
   kept, nothing edited.
5. Cash day → `PayrollSettlement` (payment-ONLY event) → ledger DEBIT.

**The ledger laws** (`WorkerLedgerEntry`, sole writer `ledger_service`):
- Append-only, immutable — corrections are reversal rows (DB-unique: one
  reversal per entry).
- Amounts always positive; direction lives in `entry_type` — so `SUM()`
  aggregates stay clean.
- **Balance is never stored** — always `SUM(credits) − SUM(debits)`, live
  (real SQL: [transactions §6](../concepts/django/transactions.md#6-how-this-project-uses-it)).
- Every credit traces to an earning line; every debit to an advance or a
  payment; every line to an `ADST-xxxx` settlement reference.

**Advances are a separate pool** — a loan, not negative earnings. Recovery
happens ONLY at settlement, per-advance, owner-chosen, guarded ≤ remaining
under lock. No silent netting, ever.

**Cost truth is a third thing** ([ADR-0009](../../docs/adr/0009-cost-truth.md)):
Adda manufacturing cost = frozen `processing_cost` snapshots; **never** add
settled labor on top (double count). Factory running costs (rent, tea,
electricity) = `FactoryExpense` — factory-level, never allocated per-Adda
([ADR-0011](../../docs/adr/0011-monthly-salary-factory-level.md)).

**Why you can trust all of it:** reconciliation identities (ledger ≡
settlement totals ≡ Σ items ≡ Σ snapshots) run in tests and live; golden
journeys replay real business scenarios end-to-end and assert **byte-identical**
money — ₹344.25 · ₹801 · ₹633 (+ historical ₹225); 88 DB constraints stand
behind the services.

## Interview corner

*Interview Signal: 🔴 Staff — business modeling as system design.*

**Q. "Design a payroll system for piece-rate workers."** *(system-design classic — this page IS your answer)*
- *Short answer:* Separate production truth (correctable observations) from financial truth (append-only ledger); convert at one atomic, audited settlement event; derive all balances live.
- *Senior answer:* The design hinges on change-physics: work reports need cheap corrections, money needs immutability — so no ledger writes until an explicit boundary, frozen snapshots at that boundary, corrections after it as compensating events. Advances as a separate loan pool with owner-chosen recovery, never auto-netting.
- *Project example:* Expected→Earned→Paid ladder; ADST references; reverse/supersede chains; goldens ₹344.25/₹801/₹633 byte-identical as the regression armor.
- *Follow-ups:* "What if a report is wrong AFTER payment?" (reverse the settlement — the interlocks force the right order) · "Scale to 10k workers?" (same boundaries; snapshot-table seam is registered) · "Why not credit on approval?" (that WAS the old design — ADR-0007 cutover story).

## 🧠 Remember This

Kaam pencil, paisa pen. Pencil freely sudhaaro; pen sirf settlement ke
darwaze se, aur pen ki galti = ulti entry, kabhi rubber nahi. Balance kabhi
likha nahi jaata — hamesha gina jaata hai. Advance alag jeb hai, cost alag
kitaab. **Do truths, ek gate, zero edit.**

## Implementation References

- The gate itself: [features/settlement.md](../features/settlement.md) · journey: [flows/worker-gets-paid.md](../flows/worker-gets-paid.md)
- Locked design: [docs/ARCHITECTURE_V2.md](../../docs/ARCHITECTURE_V2.md) §11 · ADRs [0002](../../docs/adr/0002-single-writer-per-ledger-and-history-table.md)/[0005](../../docs/adr/0005-production-truth-vs-financial-truth-option-b.md)/[0007](../../docs/adr/0007-allocation-era-ledger-cutover.md)/[0009](../../docs/adr/0009-cost-truth.md)/[0011](../../docs/adr/0011-monthly-salary-factory-level.md)

## Code References
- `config/expense/services/ledger_service.py` · `adda_settlement_service.py` · `payroll_service.py`

