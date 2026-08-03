---
id: sql-course-17-transactions-and-acid
type: lesson
status: active
owner: handwritten
scope: sql, postgresql — database fundamentals taught from this ERP
anchors: config/expense/services/settlement_service.py, config/production/services/pool_service.py
verified: 2026-08-01
---

# 17 — Transactions & ACID

> Part of [SQL From Zero](00_COURSE_OVERVIEW.md). Prev: [16](16_ORM_To_SQL_And_N_Plus_1.md) · Next: [18 — Locks, Concurrency, MVCC](18_Locks_Concurrency_MVCC.md).

# Learning Objectives
By the end of this chapter you can:
- explain ACID with a money example, not a definition
- describe how the WAL makes "committed" survive a power cut
- name Postgres's default isolation level and what it permits
- spot a missing transaction boundary in real code

# Purpose
To learn the promise that makes a database trustworthy with money: a group of
writes either **all** happen or **none** do. This is the chapter that explains why
my settlement can never half-pay a worker, even if the power dies mid-write.

# The Problem
Finalizing one settlement in my ERP writes several things: the settlement status
flips to FINALIZED, earning lines are created, ledger entries are inserted. Now
kill the power **between** two of those writes.

```
   WITHOUT transactions — the nightmare
   ┌──────────────────────────────────────────────────────────┐
   │ ✓ settlement marked FINALIZED                            │
   │ ✓ 3 of 8 earning lines written                           │
   │ ⚡ POWER CUT                                              │
   │ ✗ ledger entries never inserted                          │
   └──────────────────────────────────────────────────────────┘
   Result: the system says "paid", the ledger says otherwise, and NOBODY
   can tell which is true. The books are corrupt, silently, forever.
```

# Theory (from zero)

A **transaction** is a group of statements treated as **one indivisible unit**:

```sql
BEGIN;              -- open the unit
  UPDATE …;         -- any number of writes
  INSERT …;
  INSERT …;
COMMIT;             -- ALL of it becomes real, in one instant
-- or, any time before COMMIT:
ROLLBACK;           -- NONE of it ever happened
```

There is **no in-between visible to anyone else.** Crash before `COMMIT`? Postgres
recovers to "none of it happened". This is the **A** of **ACID**:

```
   ╔═══╦══════════════╦════════════════════════════════════════════════╗
   ║ A ║ Atomicity    ║ all or nothing — no half-finished settlement    ║
   ║ C ║ Consistency  ║ constraints hold before AND after (ch 13)       ║
   ║ I ║ Isolation    ║ concurrent users don't see each other's drafts  ║
   ║ D ║ Durability   ║ COMMIT survives power loss (the WAL, below)     ║
   ╚═══╩══════════════╩════════════════════════════════════════════════╝
```

**How Durability actually works — the WAL.** Before changing data pages, Postgres
writes the intended change to a **Write-Ahead Log** and flushes *that* to disk.
`COMMIT` returns only once the WAL record is safely down. On restart after a crash,
Postgres replays the WAL: committed work is redone, uncommitted work is discarded.

```
   WRITE-AHEAD LOG — why "committed" means committed
   ────────────────────────────────────────────────────────────
   1. "I intend to change X and Y"   ──▶ WAL   ──▶ flushed to disk ✔
   2. COMMIT returns to the client                    (now it is safe)
   3. data pages updated later, lazily, in the background
   ⚡ crash after step 2? → restart replays the WAL → your data is there.
   ⚡ crash before step 2? → nothing was promised → clean rollback.
```

**Isolation levels** — how much other transactions can affect what you see:

| Level | Prevents | Postgres |
|---|---|---|
| Read Committed | dirty reads | **the default** (verified on my server) |
| Repeatable Read | + non-repeatable reads | available |
| Serializable | + phantoms / write skew | available, strictest |

Under Read Committed, each *statement* sees the latest committed data — so two
statements in one transaction can see different snapshots. That is usually fine,
and occasionally the source of subtle bugs (which is why money paths add locks — ch 18).

> 💡 **Samjho aise:** Transaction ek **pencil se likha draft** hai. `COMMIT` = uspe
> pen phir gaya, ab pakka. `ROLLBACK` = poora page phaad diya, jaise likha hi nahi
> tha. Beech ki aadhi haalat duniya ko **kabhi dikhti nahi** — bijli chali jaaye
> tab bhi: ya poora pen, ya poora phata. Aur WAL wo **rough copy** hai jo pehle
> likhi jaati hai — isi liye bijli jaane ke baad bhi Postgres jaanta hai kya
> pakka tha aur kya nahi.

# Real World Example (My ERP)
In Django I rarely type `BEGIN`. The decorator does it:

```python
@transaction.atomic          # ← BEGIN … COMMIT around the whole function
def finalize(...):
    ...                      # any exception → automatic ROLLBACK
```

My project's rule *"the service layer owns all multi-row writes"* is really the
rule **"every business event gets exactly one transaction boundary"**. Settlement
finalize is the flagship: status change + earning lines + ledger entries, all
inside one atomic function, so `sum(amount)` can never be half-updated.

**And here is the proof that this matters, from my own history:** the **P19A C-1**
bug. A helper function was inserted *between* `@transaction.atomic` and the `def`
it was meant to decorate, so `start_layering` silently lost its transaction. The
result was `TransactionManagementError` 500s **and partially committed writes** on
every layering roster update. One missing decorator line, real corruption. It is
now pinned by a regression test that uses `TransactionTestCase` — because a normal
`TestCase` wraps each test in a transaction and would **hide** the very bug being
tested. (That subtlety is a genuinely senior-level testing insight.)

# Visual Diagram
```
   ONE BUSINESS EVENT = ONE TRANSACTION
   ══════════════════════════════════════════════════════════════════
     @transaction.atomic  finalize(settlement)
     ┌────────────────────────────────────────────────────────┐
     │ BEGIN                                                  │
     │   ① lock the settlement row      (ch 18)                │
     │   ② re-check state: already FINALIZED? → refuse         │
     │   ③ UPDATE settlement → FINALIZED                       │
     │   ④ INSERT earning lines                                │
     │   ⑤ INSERT ledger entries      ← money becomes real     │
     │ COMMIT  ◀── everything above becomes visible AT ONCE    │
     └────────────────────────────────────────────────────────┘
        ⚡ crash at ③, ④ or ⑤  →  ROLLBACK  →  as if never started
        ✗ exception anywhere    →  ROLLBACK  →  no partial payment

   Outsiders see exactly two states: "not settled" or "fully settled".
   Never "half settled". That is the entire value of this chapter.
```

# Practical — try it yourself
```sql
-- 1. what is my default isolation level? (REAL: read committed)
SHOW transaction_isolation;

-- 2. FEEL atomicity — completely safe, nothing persists:
BEGIN;
  SELECT count(*) FROM raw_materials_clothcolor;   -- e.g. 21
  DELETE FROM raw_materials_clothcolor;            -- "everything is gone"
  SELECT count(*) FROM raw_materials_clothcolor;   -- 0  ← only MY session sees this
ROLLBACK;
  SELECT count(*) FROM raw_materials_clothcolor;   -- 21 — nothing happened

-- 3. a failed statement inside a transaction poisons the rest of it:
BEGIN;
  SELECT 1;
  SELECT 1/0;                       -- ERROR: division by zero
  SELECT 1;                         -- ERROR: current transaction is aborted…
ROLLBACK;                           -- the only way out
--    ^ lesson: in Postgres, one error aborts the WHOLE transaction unless you
--      used a SAVEPOINT. Django's atomic() blocks mirror this exactly.

-- 4. SAVEPOINT — a nested undo point (Django's nested atomic() uses these)
BEGIN;
  SAVEPOINT s1;
    SELECT 1/0;                     -- error
  ROLLBACK TO SAVEPOINT s1;         -- recover just that part
  SELECT 'transaction still alive';
ROLLBACK;
```
```bash
# 5. see the decorator in the real code
grep -rn "@transaction.atomic" config/expense/services/adda_settlement_service.py | head -5
```

# Production Walkthrough
- **Settlement finalize** is the flagship: status change + earning lines + ledger entries, all inside one `@transaction.atomic`. Outsiders only ever see "not settled" or "fully settled".
- **The P19A C-1 bug is the cautionary tale.** A helper function was inserted *between* `@transaction.atomic` and the `def` it was meant to decorate, so `start_layering` silently lost its transaction — producing `TransactionManagementError` 500s **and partially committed writes** on every layering roster update. One line of indentation-level mistake, real corruption.
- The regression test for it uses **`TransactionTestCase`**, because a normal `TestCase` wraps each test in a transaction and would *hide* the very bug being tested. That subtlety is genuinely senior-level.
- On deploy, `migrate` runs before the app starts (ch 19) — a schema change and the code that needs it must not be half-applied either.

# Debugging Guide
"Data is half-written" or "TransactionManagementError":
1. **Find the boundary.** Is the write inside an `@transaction.atomic` service, or did a view write directly?
2. **Check the decorator is actually attached to the `def`** — the C-1 bug in one sentence.
3. **Look for an error swallowed mid-transaction.** In Postgres one failed statement aborts the whole transaction; subsequent statements fail with "current transaction is aborted" until rollback.
4. **Check for a long-open transaction** holding locks (ch 18) — `pg_stat_activity` shows `idle in transaction`.
5. **Reproduce with `TransactionTestCase`**, not `TestCase`, or autocommit-related bugs stay invisible.

# Performance Notes
- Transactions are cheap; **long** transactions are expensive — they hold locks and block autovacuum from reclaiming dead rows (ch 18, 24).
- `COMMIT` waits for the WAL to reach disk — that fsync is the durability cost, and it is worth paying.
- Batching many inserts into one transaction is far faster than one transaction each.
- Never keep a transaction open across a user interaction or an external API call.

# Security Considerations
- Atomicity is a **security** property for money: a partially applied payment is a financial discrepancy, and discrepancies are where fraud hides.
- Audit rows must be written **inside** the same transaction as the change they describe, or a crash can produce a change with no record of who made it.
- A rollback must not leave side effects outside the database (files written, emails sent) — those belong after commit.

# Architecture Decisions
- **One business event = one transaction**, expressed as "services own all multi-row writes".
- **Read Committed (the default) plus explicit locks** where correctness needs more, rather than globally raising the isolation level and paying for it everywhere (ch 18).
- **Money creation happens at exactly one gate** so there is exactly one transaction boundary to get right (ch 12).

# Best Practices
- Put `@transaction.atomic` on the service function, not sprinkled at call sites.
- Keep transactions short and free of network calls.
- Use `SAVEPOINT` (nested `atomic()`) when part of a unit may legitimately fail.
- Test transactional behaviour with `TransactionTestCase`.

# Beginner Mistakes
- Assuming autocommit means safety. Each *statement* is atomic by default; a
  **group** of statements is not, unless you make it one transaction.
- Doing multi-row money writes in a view instead of an `@transaction.atomic` service.
- Inserting anything between `@transaction.atomic` and its `def` — the P19A C-1 bug,
  which cost real 500s and partial writes.
- Long-running transactions (open while waiting on a user, an API, a file upload).
  They hold locks and block everyone (ch 18).
- Testing transaction behaviour with `TestCase` — it wraps tests in a transaction,
  so autocommit-related bugs are invisible. Use `TransactionTestCase`.
- Expecting a statement error to be survivable without a `SAVEPOINT`.

# Interview Questions
- **Junior:** *Explain ACID.* — Atomicity, Consistency, Isolation, Durability, ideally with a money example. **The single most-asked database interview question.** My answer: settlement finalize.
- **Junior:** *What do COMMIT and ROLLBACK do?* — make all changes permanent / discard them all.
- **Mid:** *What is the default isolation level in Postgres and what does it allow?* — Read Committed; each statement sees the latest committed snapshot, so non-repeatable reads and phantoms are possible within one transaction.
- **Mid:** *How does a database survive a power cut mid-write?* — write-ahead logging: the intent is flushed to the WAL before COMMIT returns; recovery replays committed WAL records and discards the rest.
- **Senior:** *Two transactions update the same row — what happens?* — the second blocks until the first commits or rolls back, then proceeds against the new state (ch 18).
- **Senior:** *When would you choose SERIALIZABLE?* — when correctness depends on invariants across rows that locking can't easily express (write skew, e.g. "at most N of X"); pay with serialization failures the app must retry.
- **Staff:** *Can a transaction span two databases?* — not natively; you'd need two-phase commit (`PREPARE TRANSACTION`) or a saga pattern, both with real operational cost. **This is exactly why ADR-0010 forbids forking my ledger into a second deployment: two databases = no shared atomicity, hence two unmergeable ledgers** (ch 24).

### Why interviewers ask these — and the answer that separates levels

| Testing for | Weak answer | What lands |
|---|---|---|
| Can you explain ACID with a **money** example, not a definition? | Reciting "Atomicity, Consistency, Isolation, Durability". | Walk one real write: settlement finalize either creates **every** ledger entry or **none** (A), respects every CHECK (C), is invisible to a concurrent reader until commit (I), and survives a power cut because the WAL was flushed before COMMIT returned (D). |
| Do you know what "committed" physically means? | "It saved to the database." | COMMIT returns only after the **write-ahead log** is on disk. Recovery replays committed WAL and discards the rest. That is why commit rate is bounded by disk fsync, not CPU. |
| Do you know your default isolation level? | "Transactions are isolated." | Postgres defaults to **Read Committed** — so **non-repeatable reads and phantoms are still possible inside one transaction**. Knowing the default is the whole question. |
| Do you know when SERIALIZABLE earns its cost? | "Use SERIALIZABLE to be safe." | Only when correctness depends on an invariant across rows that locking cannot express (write skew, "at most N of X") — and you must then **retry serialization failures** in the app. |

**The killer follow-up:** *"How would you make one transaction span two databases?"* — the honest answer is **you don't**: two-phase commit or a saga, both expensive. This is exactly why ADR-0010 refuses to fork the ledger into a second deployment — two databases means no shared atomicity, hence two unmergeable ledgers.

# Revision Notes
- `BEGIN … COMMIT` = one indivisible unit; `ROLLBACK` = never happened.
- **ACID**: Atomic · Consistent · Isolated · Durable.
- Durability = **WAL flushed before COMMIT returns**.
- Postgres default isolation = **Read Committed**.
- Django: `@transaction.atomic` — and make sure it decorates the `def`.

# Cheat Sheet
- `BEGIN … COMMIT` = one indivisible unit; `ROLLBACK` = never happened
- **ACID**: Atomic · Consistent · Isolated · Durable
- Durability = **WAL flushed before COMMIT returns**
- Postgres default isolation = **Read Committed**
- Django: `@transaction.atomic` (watch the decorator actually touches the `def`!)
- one business event ⇒ one transaction · never keep one open waiting on a human
- an error aborts the whole transaction unless you used a `SAVEPOINT`

# My ERP Section
| Concept | Where |
|---|---|
| Atomic money event | `@transaction.atomic` on settlement finalize (`adda_settlement_service`) |
| Rule that encodes it | "service layer owns all multi-row writes" (CLAUDE.md) |
| Real failure it prevents | P19A **C-1**: lost decorator → `TransactionManagementError` + partial commits |
| Test that pins it | a `TransactionTestCase` (a plain `TestCase` would hide the bug) |
| Deep dive | [kos: transactions](../../kos/concepts/django/transactions.md) · [transaction-boundary](../../kos/concepts/patterns/transaction-boundary.md) |

# Practice Tasks
1. **Read the code:** open `config/expense/services/adda_settlement_service.py`, find an `@transaction.atomic`, and list every write inside that boundary.
2. **Debug:** reproduce the aborted-transaction state (`SELECT 1/0` inside BEGIN), then recover the same scenario with a `SAVEPOINT`.
3. **Design:** you must send an email when a settlement finalizes. Where exactly does that go, and why not inside the transaction?
4. **Architecture:** explain why a `TestCase` would hide the P19A C-1 bug, and what that tells you about trusting a green test suite.

# Homework
1. Run the `BEGIN; DELETE …; ROLLBACK;` drill. Then run it again replacing ROLLBACK with COMMIT — **on a practice branch only** — and describe what you just learned about the word "commit".
2. Reproduce the aborted-transaction error (`SELECT 1/0` inside BEGIN), then recover the same scenario using a `SAVEPOINT`.
3. Open `config/expense/services/adda_settlement_service.py`, find an `@transaction.atomic`, and list every write that happens inside that one boundary.

# Further Reading & Live Resources
- [Postgres transactions tutorial](https://www.postgresql.org/docs/current/tutorial-transactions.html) — short and excellent
- [Postgres transaction isolation](https://www.postgresql.org/docs/current/transaction-iso.html)
- [Postgres WAL / reliability](https://www.postgresql.org/docs/current/wal-intro.html)
- [Django database transactions](https://docs.djangoproject.com/en/5.0/topics/db/transactions/)
