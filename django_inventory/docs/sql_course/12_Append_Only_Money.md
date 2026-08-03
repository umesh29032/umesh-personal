---
id: sql-course-12-append-only-money
type: lesson
status: active
owner: handwritten
scope: sql, postgresql — database fundamentals taught from this ERP
anchors: config/expense/services/settlement_service.py, config/production/services/pool_service.py
verified: 2026-08-01
---

# 12 — The Append-Only Money Philosophy

> Part of [SQL From Zero](00_COURSE_OVERVIEW.md). Prev: [11](11_INSERT_UPDATE_DELETE.md) · Next: [13 — Constraints](13_Constraints.md).

# Learning Objectives
By the end of this chapter you can:
- explain why a money row is never edited, to a non-technical person
- design a correction as a reversing entry with an author and a reason
- say what append-only costs you, and why the trade is worth it
- answer "how do you correct a posted transaction?" like a senior

# Purpose
To understand *why my own ledger is built the way it is* — the single most
important design decision in my ERP, and the one that let an audit prove
₹18,254.25 to the paisa. This chapter is architecture, not syntax.

# The Problem
A worker was paid ₹500. It should have been ₹400. The obvious move is
`UPDATE … SET amount = 400`. One statement, done.

But now answer these, six months later, to a worker who is arguing:
*Was it always 400? Who changed it? When? Why? What did I actually get paid?*
The `UPDATE` erased every one of those answers. **Edited history is unprovable
history** — and a payroll system that cannot prove itself is worthless in the one
moment it matters.

# Theory (from zero)

Two ways to hold a fact that changes:

```
   ①  MUTABLE STATE  (the intuitive way)          ②  APPEND-ONLY  (the ledger way)
   ═══════════════════════════════════            ═══════════════════════════════
   one row = the current truth                    many rows = the whole story
                                                   
   row 7 │ amount 500 │  ← UPDATE …               row 7 │ +500 │ earned
   row 7 │ amount 400 │  ← now says 400           row 8 │ -500 │ reversal (why: wrong rate)
                                                  row 9 │ +400 │ corrected
   history: GONE                                  
   "who/when/why?" → cannot answer                balance = 500 − 500 + 400 = 400
   audit: impossible                              history: COMPLETE. audit: trivial.
```

The append-only rule in one line: **never change a money row; add a new row that
corrects it.** The correcting row is called a **reversal** or **compensating
entry** — the same idea double-entry bookkeeping has used since the 1400s.

**Consequences you must accept (the honest trade-offs):**

| You gain | You pay |
|---|---|
| complete, provable history | tables grow forever (disk is cheap) |
| every correction has an author + reason | "current balance" becomes a *computation*, not a stored number |
| no lost-update races | reads do more work (`sum()` — but see ch 10's running balance) |
| audits become arithmetic | you must resist the urge to "just fix it" |

**Soft-state, the same idea for non-money rows.** Instead of `DELETE`, mark:
`is_active = false`, `cancelled_at = now()`, `voided_by = <user>`. The row stays
as evidence that it existed and was withdrawn.

**Single-writer discipline** — the rule that makes it enforceable:

```
      many callers                    ONE door                the table
   ┌──────────────┐              ┌──────────────┐        ┌──────────────────┐
   │ settlement   │─────┐        │              │        │                  │
   │ views        │     ├───────▶│ ledger_      │───────▶│ WorkerLedgerEntry│
   │ payroll      │─────┤        │ service      │        │  (append-only)   │
   │ advances     │─────┘        │              │        │                  │
   └──────────────┘              └──────────────┘        └──────────────────┘
                                  ▲ all rules live here:
                                    atomicity · audit rows · refusals
   If every caller could INSERT directly, "the rules" would live in N places
   and the newest code path would forget one. One door = one place to be right.
```

> 💡 **Samjho aise:** Paise ka register **rubber se mitaya nahi jaata.** Galti
> hui? Purani entry waise hi rehne do, aur **ulti entry** daal do — "500 kaat
> diye, 400 sahi hain". Do saal baad koi poochhe "mera hisaab kaise bana?", to
> poori kahani register mein likhi milegi: kya hua, kisne badla, kyun badla.
> Jo register mein rubber chalta hai, us register pe koi bharosa nahi karta.
> Aur likhne ka **ek hi darwaza** rakho (`ledger_service`) — das darwaze honge
> to koi ek darwaza niyam bhool jaayega.

# Real World Example (My ERP)
```
        MY ACTUAL MONEY ARCHITECTURE
  ────────────────────────────────────────────────────────────────
   work happens        →  Expected   (a calculation, no money yet)
        │                     │            edit freely, nothing is real
        │                     ▼
   settlement gate      →  Earned    ← the ONE place money is created
        │                     │            (atomic, locked, audited — ch 17/18)
        ▼                     ▼
   payment              →  Paid
  ────────────────────────────────────────────────────────────────
   after the gate: NEVER edit. Reversal only.
   proof it works: 201 ledger rows · sum = ₹18,254.25 · audit variance ₹0
```

- `WorkerLedgerEntry` — the money table. **INSERT only.** 201 rows today,
  `credit` 170 / `debit` 31, summing to exactly ₹18,254.25.
- `ledger_service` — the **sole writer**. Nothing else may INSERT there.
- Settlement is the single gate where "expected" becomes "earned"; before it,
  quantities are freely correctable, after it a mistake is a *reversal*, never an
  edit. (That asymmetry — cheap zone permissive, expensive gate armoured — is the
  design's core.)
- Corrections carry a **mandatory reason** and an author, because a reversal
  without a why is just a mystery with better paperwork.

# Visual Diagram
```
   THE PENCIL / PEN LINE
   ═════════════════════════════════════════════════════════════════
        DRAFT ZONE                    │        COMMITTED ZONE
        (pencil ✏️)                    │        (pen 🖊️)
                                      │
   quantities, reports, expected ₹    │   ledger entries, paid money
   ──────────────────────────────     │   ─────────────────────────────
   edit as often as you like          │   append-only, forever
   nothing is real yet                │   every row is a fact that happened
   mistakes cost nothing              │   mistakes cost a REVERSAL row
                                      │
                   ┌──────────────────┴──────────────────┐
                   │      THE SETTLEMENT GATE            │
                   │  atomic · locked · audited · once   │
                   └─────────────────────────────────────┘
   Cross it in one direction only. That is the whole philosophy.
```

# Practical — try it yourself
```sql
-- 1. the ledger's shape: credits and debits, never edits (REAL)
SELECT entry_type, count(*), sum(amount)
FROM expense_workerledgerentry GROUP BY entry_type;
--  credit | 170 | 15629.25
--  debit  |  31 |  2625.00

-- 2. balance as a COMPUTATION, not a stored column (REAL: 18254.25)
SELECT sum(amount) AS balance FROM expense_workerledgerentry;

-- 3. is there an "amount was changed" column? No — because amounts are never
--    changed. Look at what the table DOES record instead:
\d expense_workerledgerentry
--    ^ note created_at (when the fact was recorded) and the FK to its source.
--      Immutability is visible in the schema's silence about edits.

-- 4. reconstruct one worker's story in order — the audit trail, readable:
SELECT l.id, l.entry_type, l.amount,
       sum(l.amount) OVER (ORDER BY l.id) AS running
FROM expense_workerledgerentry l JOIN accounts_user u ON u.id=l.worker_id
WHERE u.email='a2.cm1@audit.local' ORDER BY l.id;
--  264 credit  500.00 |  500.00
--  265 credit 2000.00 | 2500.00
--  266 credit 2000.00 | 4500.00
--  267 credit 2000.00 | 6500.00
--    ^ THIS is what append-only buys: the number AND its derivation.
```

# Production Walkthrough
- The **settlement gate** is the only place money is created. Before it, quantities are freely correctable; after it, a mistake is a reversal. That asymmetry — permissive in the cheap zone, armoured at the expensive one — is the design.
- The audit ran a full 12-stage journey, settled ₹7,146.50, and proved **cost == earnings on every payable stage** with **variance ₹0**. That proof is only possible because the inputs are immutable.
- `ledger_service` is the sole writer. A second writer would mean two places where the append-only rule could be forgotten.
- Corrections carry a **mandatory reason** — a reversal nobody can explain is a mystery with better paperwork.

# Debugging Guide
"A worker says their payment is wrong":
1. **Which state are they looking at?** Expected / Earned / Paid are three different numbers and all three can be correct at once (ch 08, and the kos `money-looks-wrong` playbook).
2. **Read the entries in order** with a running balance (ch 10). The story is in the sequence, not the total.
3. **Look for the reversal.** If a correction happened, there are *three* rows, not one changed row. Missing reversal + changed total = someone edited by hand.
4. **Reconcile.** Settlement total vs ledger delta must match; a gap points at the exact stage.
5. **Never "fix" it with an UPDATE.** That destroys the evidence you are currently using to debug.

# Performance Notes
- Append-only tables grow forever. At this factory's volume (201 rows) that is irrelevant; at millions, partition by period and keep the current window hot.
- "Current balance" is a `sum()` — cheap now, and if it ever isn't, the answer is a **materialised** snapshot *derived* from the entries, never a hand-maintained counter.
- Immutability is a performance *gift* for reads: rows never change, so caches and reports cannot go stale mid-flight.

# Security Considerations
- Immutable rows are the audit trail. Anyone with UPDATE rights on the ledger can rewrite history — which is why the app connects as a limited role in production and why hand-edits are forbidden by convention *and* by having a single writer.
- Every reversal records **who** and **why**; without an author, an audit cannot distinguish a correction from tampering.
- Backups of a money table are as sensitive as the table (ch 20, 22).

# Architecture Decisions
- **Append-only, not mutable state** — chosen because provable history beats convenient editing when the subject is wages.
- **Balance computed, never stored** — one source of truth (the entries).
- **One writer service per money table** — invariants live in exactly one place.
- **Settlement as a single gate** — one atomic, locked, audited crossing rather than money created in many places (ch 17, 18).
- **Soft-state elsewhere** — non-money records are withdrawn (`cancelled_at`), not deleted, for the same evidentiary reason.

# Best Practices
- Correct with a reversal; never edit, never delete.
- Require a reason on every correction, and store the author.
- Keep the "expected" zone editable and cheap — that is where honest mistakes belong.
- Prove every important total by a second, independent path.

# Beginner Mistakes
- "I'll just `UPDATE` the amount, it's faster." It is faster, and it destroys the
  only evidence of what happened.
- `DELETE`ing a wrong entry instead of reversing it. Now the total is right and the
  history lies — the worst of both.
- Storing a `balance` column *and* the entries, with no single writer. Two sources
  of truth drift, and nobody can say which is correct.
- Reversing without a reason field. A correction nobody can explain is a future argument.
- Editing money rows by hand in dbshell — bypasses `ledger_service`, its
  transaction boundary, and its audit rows.

# Interview Questions
- **Junior:** *Why would a system never delete financial records?* — auditability and legal traceability; corrections are additive.
- **Mid:** *How do you correct a posted transaction?* — post a reversing entry (and, if needed, a fresh correct entry); never mutate the original. **A genuine differentiator — most candidates say "update it".**
- **Mid:** *Where does the current balance live in an append-only design?* — nowhere; it is `sum()` of the entries, optionally cached but never authoritative.
- **Senior:** *Trade-offs of append-only vs mutable state?* — unbounded growth and heavier reads, in exchange for provable history, natural concurrency safety, and reproducible totals. Mitigations: partitioning, periodic snapshots/materialised balances *derived* from entries.
- **Senior:** *Why one writer per table?* — invariants, audit rows and transaction boundaries are enforced in exactly one place; new code paths cannot forget them, and "who can change this?" has a one-word answer.
- **Staff:** *Design a payroll ledger from scratch.* — immutable entries with `numeric` amounts; a single settlement gate that creates money atomically under a lock; reversals for corrections with mandatory reason + author; totals proven by independent reconciliation; one writer service. (That is a description of this project — you own the worked example.)

### Why interviewers ask these — and the answer that separates levels

| Testing for | Weak answer | What lands |
|---|---|---|
| Do you know *why* money is never deleted? | "For record-keeping." | **Auditability and legal traceability** — you must be able to prove what was true at a past moment, including the mistakes. Corrections are **additive**, so the wrong entry and its reversal are both visible forever. |
| The differentiator question: correcting a posted transaction. | "Update the amount to the correct value." | **Post a reversing entry**, then a fresh correct one if needed — original untouched, with a mandatory **reason and author**. Most candidates say "update it". This single answer separates people who have run books from people who have only written CRUD. |
| Where does the balance live? | "In a balance column on the worker." | **Nowhere.** It is `sum()` of the entries — optionally cached, **never authoritative**. A stored balance is a second source of truth, and the moment it disagrees with the entries you cannot tell which is right. |
| Can you argue the trade-off honestly? | "Append-only is just better." | You pay **unbounded growth and heavier reads**; you buy **provable history, natural concurrency safety, reproducible totals**. Mitigations are partitioning and periodic snapshots that are **derived from** entries, never a replacement for them. |

**The killer follow-up:** *"Design a payroll ledger from scratch."* — immutable entries with exact numeric amounts · one settlement gate creating money atomically **under a lock** · reversals with mandatory reason+author · totals proven by **independent reconciliation** · exactly one writer service. That is a description of this project, so you own the worked example — including the advisory locks 5374/5375 and why they exist.

# Revision Notes
- Money rows: **INSERT only**. Correction = **reversing entry** + reason + author.
- History stays complete, so any total is reproducible and provable.
- Balance is a **computation** (`sum`), not a stored fact.
- Cost: tables grow, reads do more work. Benefit: the books can face an audit.
- Non-money records use **soft-state**, not DELETE.

# Cheat Sheet
- money rows: **INSERT only** — never UPDATE, never DELETE
- correction = **reversal row** (+ reason + author), history stays whole
- non-money rows: **soft-state** (`is_active=false`, `cancelled_at`) over DELETE
- balance = computed `sum()`, not a stored fact
- **one writer per table** (`ledger_service`, `history_service`)
- pencil before the settlement gate, pen after it

# My ERP Section
| Principle | Where |
|---|---|
| Append-only ledger | `expense_workerledgerentry` (201 rows, ₹18,254.25) |
| Sole writer | `config/expense/services/ledger_service.py` |
| History append-only | `*History` tables via `history_service` |
| The single money gate | `adda_settlement_service` (ch 17, 18) |
| Independent proof | `reconciliation_service`, audit variance ₹0 |
| Human pages | [kos: append-only-ledger](../../kos/concepts/patterns/append-only-ledger.md) · [money-looks-wrong](../../kos/debugging/money-looks-wrong.md) |

# Practice Tasks
1. **Read the code:** open `config/expense/services/ledger_service.py` and write down, in your own words, the one thing it refuses to do.
2. **Debug:** reconstruct one worker's full story with a running balance (ch 10). Can you explain every line to that worker?
3. **Design:** a manager settled the wrong Adda. Write the exact sequence of rows you would create to fix it, including what goes in the reason field.
4. **Architecture:** append-only means unbounded growth. Propose a strategy for year five that does **not** break the "single source of truth" rule.

# Homework
1. Compute the ledger balance from `credit − debit` and check it equals `sum(amount)`. You just performed a reconciliation.
2. Read the docstring at the top of `config/expense/services/ledger_service.py` and write down, in your own words, what it refuses to do.
3. Explain to the wall why `UPDATE ledger SET amount=400` would have been cheaper today and much more expensive next year.

# Further Reading & Live Resources
- [Martin Fowler: Event Sourcing](https://martinfowler.com/eaaDev/EventSourcing.html) — the general form of this idea
- [Martin Fowler: Accounting patterns (Ledger)](https://martinfowler.com/eaaDev/AccountingNarrative.html)
- [Postgres: transactions](https://www.postgresql.org/docs/current/tutorial-transactions.html) — the mechanism the gate relies on (ch 17)
