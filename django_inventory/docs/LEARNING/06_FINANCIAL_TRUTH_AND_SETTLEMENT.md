---
id: learning-06-financial-truth-and-settlement
type: lesson
status: active
owner: handwritten
scope: learning — generic concept
anchors: —
verified: 2026-07-13
---

# Financial truth & settlement — the heart

## The ledger (WorkerLedgerEntry)
Append-only. Credit = paisa bana; debit = paisa gaya/recover hua.
Galti = OPPOSITE-direction REVERSAL row (entry_date copied — month ka total
sahi netting karta hai). UPDATE/DELETE kabhi nahi. Balance = SUM, hamesha live.

## Settlement = approval event, NOT payment (Model A)
AddaSettlement finalize: "is Adda ka kaam check ho gaya — earnings book karo,
advances me se YEH wale recover karo." Cash baad mein, alag event
(PayrollSettlement, payment-only).

## The lifecycle (and the correction story)
draft (scratchpad) → FINALIZE (money writes, frozen per-worker items) →
galti? REVERSE (compensating rows; SWA void; PSI stamped) ya
REVERSE & SUPERSEDE (successor draft, chain visible: ADST-0001→0002→0003).
History kabhi edit nahi hoti — kal ki galti aaj ke naye events se theek hoti
hai. Live-proven on dev with real chains.

## The guards you will meet in code
- settled line dobara settle nahi hoti (era-A + era-B skip classes, labeled
  in the draft UI);
- reopen of a settled stage REFUSES, ADST naam le ke;
- void on a settlement line REFUSES → "reverse the settlement";
- recovery ≤ remaining, under lock;
- finalize lock order (see [03](03_TRANSACTIONS_AND_LOCKS.md)).

## Eras (ADR-0007 — executed)
Era-A = purana allocation-time crediting (SWA.adda_settlement NULL) —
readable + reversible forever, population frozen since V2-3.
Era-B = settlement lines. Lever: `LEDGER_CREDIT_AT_ALLOCATION` (default
False; env True = tested rollback). Deletion PR soak-gated.

## Worker's three numbers
Expected (unsettled, frozen WSC) → Earned (ledger) → Paid (cash).
Non-overlapping by construction — tests prove the rupee never shows twice.
