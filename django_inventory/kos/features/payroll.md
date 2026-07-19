---
id: feature-payroll
type: feature
verified: 2026-07-19
knowledge_confidence: verified_against_code
answers: "How does cash actually leave the factory, and how does anyone know what is still owed?"
related: [feature-settlement, feature-ledger, feature-advances]
---

# Payroll — the cash event and the money board

> 📂 [Features](README.md) · [KOS home](../README.md) — *pehle yeh page, phir code.*

## Business Purpose

Settlement decides what is OWED; payroll is where cash actually MOVES and
where management sees the whole money picture: every worker's payable, every
outstanding advance, every payment ever made. The worker's own window
(`/expense/my/`) shows the same truth from their side — **Expected → Earned
→ Paid**, three numbers that never overlap.

## Mental Model

> Cash is just another ledger event. A payment doesn't "close" anything —
> it appends a DEBIT that makes the derived payable smaller. There is no
> "mark as paid" state anywhere; there are only entries and sums.

## 💡 Samjho Aise

Hisaab pehle, cash baad mein. Adda settle hua = udhaar-kitab mein "dena
banta hai" likha gaya. Cash dena = usi kitaab mein "diya" ki entry. Screen
par jo "payable" dikhta hai wo kitaab ka LIVE jod hai — koi checkbox nahi
jo "paid ho gaya" bolta ho. Checkbox jhooth bol sakta hai; jod nahi.

## Technical Deep Dive

**The cash event** — `settlement_service.create_settlement` (SOLE writer of
`PayrollSettlement` + its items, ADR-0002), at `/expense/workers/<pk>/settle/`:

- **PAYMENT-ONLY since V2-2** — pass `recoveries` and it refuses with
  *"Advance recovery now happens at Adda settlement (finalize)"*. One event,
  one meaning.
- Invariant: `amount_paid ≤ current payable` — can't pay more than owed;
  equality = full settlement (payable → 0).
- Writes: 1 `PayrollSettlement` (reference `SETL-xxxx`) + ledger DEBIT
  (`settlement_payment`) via `ledger_service`.
- **F&F write-offs** (super-admin + mandatory reason): forgive an advance's
  remaining as an audited PSI row with **NO ledger debit** — a forgiven loan
  is not a payment; payable untouched, outstanding derives to 0.

**Two real race stories baked into this function** (read them in code —
they teach more than any textbook):

1. *The reference race:* two clerks pay two DIFFERENT workers at once; both
   read max reference `SETL-0001`, both compute `SETL-0002` → the second
   INSERT dies on the unique constraint → 500. Per-worker locks can't help
   (different workers!). Fix: a **global advisory lock** around reference
   allocation.
2. *The over-pay race:* two cash payments for the SAME worker both read the
   same payable and each pay it in full. Fix: lock a **stable per-worker
   row** (`WorkerProfile`, `select_for_update`) so the second waits and
   re-reads the reduced payable. Note the subtlety: a lock on the worker's
   *advances* wouldn't protect a cash-only payment (no advance rows to lock)
   — you must lock something that ALWAYS exists.

**The read surfaces** (`payroll_service` — pure derivations, nothing stored):

| Surface | Function | Shows |
|---|---|---|
| `/expense/payroll/` overview | `payroll_totals`, `outstanding_advances_bulk` | every worker: payable, outstanding advance (grouped aggregates — one query, not N) |
| `/expense/workers/<pk>/` detail | `worker_summary`, `worker_balance_breakdown` | itemized derivation: gross earnings − reversals − debits-by-category = payable — **the dispute-resolution tool** |
| `/expense/my/` (worker) | `unsettled_expected` + ledger sums | Expected (unsettled work) → Earned (credits) → Paid (debits) |

`worker_balance_breakdown` deserves special respect: when anyone asks *"why
is my balance ₹X?"*, this one call answers with components instead of you
re-doing reversal-netting math over raw rows.

**Pay basis (R4):** `set_pay_basis` — the SOLE writer of `WorkerPayBasisAudit`;
super-admin only; joins advisory lock 5374 so a basis flip can't race a
finalize. Monthly workers' lines are structurally excluded from settlement.

## Debugging Guide

| Symptom | Start |
|---|---|
| "Payable doesn't match what I expect" | `worker_balance_breakdown(worker)` — read the components, not the screens |
| Payment refused "exceeds payable" | Correct behavior — settle the Adda first (Expected isn't payable yet) |
| Recovery attempted at payment | Refused by design since V2-2 — recovery lives at Adda-settlement finalize |
| Two payments, one 500 | Check the advisory-lock path — the reference race above |

## Change Impact

Models `PayrollSettlement`/`Item` · ledger categories `settlement_payment` ·
My Earnings + overview + worker-detail templates · F&F flow (`fnf_service`) ·
tests `test_views.py`, `test_r7_fnf.py`, `test_perf_settlement.py` · goldens.

## AI Implementation Pitfalls

- ❌ Re-adding recovery to the cash event — V2-2 moved it to Adda settlement; the refusal is pinned by tests.
- ❌ "Mark as paid" flags/status columns — payable is derived, always.
- ❌ Paying without the WorkerProfile lock — the over-pay race returns.
- ❌ Write-off as a ledger debit — forgiveness ≠ payment; it's a PSI row with reason.
- ✅ Always verify: `amount_paid + advance_deducted == payable_settled` identity and Expected/Earned/Paid non-overlap tests stay green.

## Interview Notes

*Interview Signal: 🟠 Senior — double-spend races under concurrency.*

**Q. "Two concurrent requests both pass your balance check — how do you stop double-spend?"**
- *Short:* Serialize on a stable row lock; re-read inside the lock.
- *Senior:* The check-then-act gap is the bug; locks make the second actor re-read post-commit state. Pick a lock target that exists for EVERY request path — locking "related rows" fails when the set is empty.
- *Project example:* `WorkerProfile` lock (always exists via get_or_create) vs the tempting-but-wrong advances lock (empty for cash-only payments). Plus the global advisory lock for reference allocation across workers.
- *Follow-ups:* "Why not unique-constraint-retry instead?" (works for the reference, ugly for money math) · "Isolation levels instead?" (SERIALIZABLE retries cost more than a targeted lock here).

## 🧠 Remember This

Cash bhi sirf ek entry hai. Payable = jod, status nahi. Recovery settlement
par, cash payment par, maafi (write-off) sirf super-admin + reason —
teeno alag events, ek hi kitaab. Aur race ka ilaaj: aisa taala jo HAR
raste par mile (WorkerProfile), na ki jo kabhi-kabhi ho (advances).

## 30-Second Revision

- `create_settlement` = PAYMENT-ONLY (recovery → Adda finalize; refusal pinned)
- Guard: amount_paid ≤ live payable; lock WorkerProfile → re-read
- Reference race → global advisory lock; over-pay race → per-worker row lock
- Write-off (F&F) = audited PSI, NO ledger debit, super-admin + reason
- Breakdown call = dispute tool: gross − reversed − debits-by-cat = payable
- Worker view: Expected → Earned → Paid, non-overlapping, all derived

## Implementation References

- Design: [docs/ARCHITECTURE_V2.md](../../docs/ARCHITECTURE_V2.md) §11.2 (Model A) · ADR [0002](../../docs/adr/0002-single-writer-per-ledger-and-history-table.md)

## Code References
- `config/expense/services/settlement_service.py` (`create_settlement`) · `payroll_service.py` (`worker_balance_breakdown`, `set_pay_basis`) · `config/expense/urls.py`
- Tests: `config/expense/tests/test_views.py` · `test_r7_fnf.py`

## Related Concepts

[ledger](ledger.md) · [advances](advances.md) · [settlement](settlement.md) ·
[pg/locks](../concepts/postgresql/locks.md) · [single-writer](../concepts/architecture/single-writer.md)
