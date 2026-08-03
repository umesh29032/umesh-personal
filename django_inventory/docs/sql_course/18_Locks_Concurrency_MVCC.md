---
id: sql-course-18-locks-concurrency-mvcc
type: lesson
status: active
owner: handwritten
scope: sql, postgresql — database fundamentals taught from this ERP
anchors: config/expense/services/settlement_service.py, config/production/services/pool_service.py
verified: 2026-08-01
---

# 18 — Locks, Concurrency, MVCC

> Part of [SQL From Zero](00_COURSE_OVERVIEW.md). Prev: [17](17_Transactions_And_ACID.md) · Next: [19 — Migrations](19_Migrations.md).

# Learning Objectives
By the end of this chapter you can:
- state the MVCC rule about readers and writers, and use the word correctly
- implement lock-then-re-check to make an operation safe to retry
- explain what an advisory lock is and when a row lock is not enough
- prevent deadlocks by lock ordering rather than by hoping

# Purpose
To answer the question that decides whether a payroll system is safe:
**what happens when two managers press "Finalize" on the same settlement at the
same instant?** My ERP answers it with named locks — and this chapter explains the
machinery, including why my *readers* never wait.

# The Problem
Isolation (ch 17) promised that concurrent users don't corrupt each other. But
*how*? Consider the double-pay disaster:

```
   TIME →   Manager A                        Manager B
   ─────────────────────────────────────────────────────────────────
   t1       read settlement: status=DRAFT
   t2                                        read settlement: status=DRAFT
   t3       "not finalized yet, proceed"
   t4                                        "not finalized yet, proceed"
   t5       INSERT ledger entries  ₹7,146
   t6                                        INSERT ledger entries  ₹7,146
   ─────────────────────────────────────────────────────────────────
   RESULT: the worker is paid TWICE. Both managers did nothing wrong.
           Both saw a valid state. The bug is the RACE, not the people.
```

# Theory (from zero)

**MVCC — Multi-Version Concurrency Control.** Postgres does not overwrite a row in
place; it keeps **versions**. Each transaction sees a consistent snapshot. The
consequence is the single most important sentence in this chapter:

```
   ┌──────────────────────────────────────────────────────────────┐
   │  In Postgres:  READERS never block WRITERS                    │
   │                WRITERS never block READERS                    │
   │                WRITERS block WRITERS  (same row only)         │
   └──────────────────────────────────────────────────────────────┘
   So a manager viewing a report never freezes a worker submitting a report.
   Only two people writing THE SAME ROW have to take turns.
```

**Row locks — `SELECT … FOR UPDATE`.** "Fetch this row *and* reserve it; I am about
to change it." Anyone else wanting to write that row waits for my COMMIT.

```
   THE FIX for the race above
   ─────────────────────────────────────────────────────────────────
   Manager A                          Manager B
   BEGIN                              BEGIN
   SELECT … FOR UPDATE  ← holds lock   SELECT … FOR UPDATE
     status=DRAFT                        ⏳ WAITS (blocked, not broken)
   UPDATE → FINALIZED                    ⏳
   INSERT ledger ₹7,146                  ⏳
   COMMIT ───────────────────────────▶  ▶ proceeds now, re-reads the row
                                        status = FINALIZED
                                        → REFUSES. No second payment. ✅
   ─────────────────────────────────────────────────────────────────
   The pattern has TWO halves: lock the row, then RE-CHECK the state.
   Locking alone is not enough — you must look again after you get the lock.
```

**Advisory locks — locking an *idea*, not a row.** Postgres lets an application
lock an arbitrary number: `pg_advisory_xact_lock(5374)`. Nothing in the schema
knows what 5374 means; *my code* decides it means "settlement work". Released
automatically at transaction end (that's the `_xact_` part).

**Deadlock — the mutual wait:**

```
   A holds row1, wants row2  ─┐
                              ├─▶  both wait forever
   B holds row2, wants row1  ─┘
   Postgres DETECTS this, kills one victim with an error, the other proceeds.
   THE CURE IS NOT the detector — it is LOCK ORDER DISCIPLINE:
   always take locks in the same order, in every code path, forever.
```

> 💡 **Samjho aise:** Ek hi khaata, do munshi, ek hi waqt. Pehla munshi register pe
> **haath rakh deta hai** (`FOR UPDATE`) — doosra khada intezaar karta hai. Pehla
> likh ke COMMIT karta hai, phir doosra dekhta hai: *"arre, ye to ho hi chuka"* —
> aur **mana kar deta hai**. Dono ne sahi kaam kiya, paisa ek hi baar gaya.
> Aur padhne wale? Unhe rukna hi nahi padta — Postgres purani copy dikha deta hai
> (MVCC). Deadlock = dono ek-doosre ke register pe haath rakh ke khade hain;
> Postgres ek ko zabardasti ghar bhej deta hai.

# Real World Example (My ERP)
My settlement service uses **all three** mechanisms, deliberately:

```python
# real code, config/expense/services/adda_settlement_service.py
_REF_LOCK = 5374          # SHARED with settlement_service — one serialization domain

with connection.cursor() as cur:
    cur.execute('SELECT pg_advisory_xact_lock(%s)', [_REF_LOCK])
```

- **5374 = the settlement domain.** Reference numbering (`SETL-XXXX`), finalize,
  reopen and void **all** take 5374 *first*, so they form one queue. Its docstring
  states the rule out loud: *"lock-ORDER dono race-safe; order todna = deadlock"* —
  breaking the order **is** the deadlock.
- **5375 = the allocation/pool domain** — a *different* number, so allocation work
  and settlement work never queue behind each other unnecessarily.
- **Row locks** via `select_for_update()` on the settlement row, plus the re-check
  that makes the second manager refuse rather than double-pay.
- Contribution rows are locked with `of=('self',)` so a verify-edit racing a
  finalize blocks and then refuses.

```
   MY TWO LOCK DOMAINS — why two numbers instead of one
   ═══════════════════════════════════════════════════════════════
   5374  settlement │ finalize · reopen · void · SETL numbering
                    │ ── all serialize together (they must)
   5375  allocation │ pool draw-down · allocate · void
                    │ ── independent queue (they need not wait)
   ═══════════════════════════════════════════════════════════════
   Same Adda settling twice → queue.  Two DIFFERENT Addas → parallel.
   One global lock would have made the whole factory single-file.
```

# Visual Diagram
```
   MVCC: WHY YOUR REPORT NEVER FREEZES SOMEONE'S WORK
   ══════════════════════════════════════════════════════════════════
   row 7, version history kept by Postgres:

     v1 (amount 500) ──── committed at t1
     v2 (amount 400) ──── written at t5, NOT yet committed
                          │
   Manager reading at t6  ┘
        sees ────────────▶ v1 (500)      ← the last COMMITTED version
        waits? ──────────▶ NO. Never.

   Writer at t6 wanting row 7 ──▶ ⏳ waits for the t5 writer's COMMIT
   ══════════════════════════════════════════════════════════════════
   Cost of this magic: old versions pile up as "dead tuples" until
   VACUUM cleans them (autovacuum does it for you). That is the trade.
```

# Practical — try it yourself
This is the one chapter that needs **two terminals**. Open dbshell in both.

```sql
-- ── Terminal 1 ──────────────────────────────────────────────
BEGIN;
SELECT id, name FROM raw_materials_clothcolor WHERE id = 1 FOR UPDATE;
--   ^ row 1 is now LOCKED by me. I am holding it. Do not COMMIT yet.

-- ── Terminal 2 ──────────────────────────────────────────────
BEGIN;
SELECT id, name FROM raw_materials_clothcolor WHERE id = 1 FOR UPDATE;
--   ^ this HANGS. It is not broken — it is waiting for Terminal 1.

-- but a plain READ does NOT wait (this is MVCC, live):
SELECT id, name FROM raw_materials_clothcolor WHERE id = 1;   -- instant ✅

-- ── Terminal 1 ──────────────────────────────────────────────
ROLLBACK;          -- release
-- ── Terminal 2 now unblocks. ROLLBACK there too.
```
Inspect the machinery while Terminal 2 is blocked (from a third session, or after):
```sql
-- who is waiting for whom?
SELECT pid, wait_event_type, wait_event, left(query, 60) AS query
FROM pg_stat_activity WHERE datname = current_database();

-- what locks exist right now?
SELECT locktype, relation::regclass, mode, granted FROM pg_locks
WHERE NOT granted OR relation IS NOT NULL LIMIT 10;

-- advisory locks are visible too (run inside a transaction that took one):
BEGIN;
  SELECT pg_advisory_xact_lock(5374);
  SELECT locktype, objid, mode FROM pg_locks WHERE locktype = 'advisory';
COMMIT;         -- released automatically here
```
```bash
# see my real advisory lock in the source
grep -n "advisory_xact_lock\|_REF_LOCK" config/expense/services/adda_settlement_service.py | head -5
```

# Production Walkthrough
Three mechanisms, all live in `adda_settlement_service`:
- **Advisory lock 5374** is the settlement serialization domain: finalize, reopen, void and `SETL-XXXX` numbering all take it **first**, forming one queue. Its own docstring states the rule — *breaking the lock order is the deadlock*.
- **5375** is the allocation/pool domain, deliberately a different number so allocation work and settlement work do not queue behind each other.
- **Row locks** via `select_for_update()` on the settlement row, plus the **re-check** that makes the second manager refuse rather than double-pay.
- Contribution rows lock with `of=('self',)` so a verify-edit racing a finalize blocks and then refuses.
- The audit ran a full journey and found **variance ₹0** — evidence that these guards hold under a real sequence, not just in theory.

# Debugging Guide
"A request hangs" / "deadlock detected":
1. **`pg_stat_activity`** — find sessions with `wait_event_type = 'Lock'` and see what they are waiting on.
2. **`pg_locks`** with `granted = false` — the exact blocked request.
3. **Look for `idle in transaction`** — someone opened a transaction and went away; that is usually the real culprit.
4. **Deadlock in the log?** Read both statements; the fix is a consistent lock order in code, not a retry loop bolted on.
5. **Slow but not blocked?** Readers do not block in Postgres, so look at N+1 (ch 16) or plans (ch 15) instead.

# Performance Notes
- Locks serialize: a single hot row becomes a queue. Design so writers contend on *different* rows — which is exactly what per-Adda advisory keys achieve.
- MVCC's cost is **dead tuples**; autovacuum reclaims them, but a long-running transaction prevents that and causes bloat.
- `SELECT … FOR UPDATE` on many rows can escalate into a lot of waiting; lock the narrowest set (`of=('self',)`).
- This is also why `count(*)` is not cheap in Postgres — visibility is per-transaction (ch 24).

# Security Considerations
- A missing lock is a **financial** vulnerability, not just a race: double-submit is the classic way to get paid twice. The lock-then-re-check pattern is the defence.
- Idempotency matters: an operation that can safely be retried cannot be exploited by resubmitting.
- Advisory lock keys are application constants, not secrets — but colliding numbers across subsystems would serialise unrelated work, so they are documented deliberately.

# Architecture Decisions
- **Two lock domains, not one global lock** — otherwise the whole factory would run single-file.
- **Pessimistic locking for money** (`FOR UPDATE`), optimistic elsewhere: money cannot afford a lost update.
- **Lock order is a documented rule**, because deadlock prevention is a discipline and the detector is only a backstop.
- **Advisory locks for non-row concerns** (numbering, per-entity workflows) — the right tool when there is no single row to lock.

# Best Practices
- Lock, then **re-read and re-check the state**. Half the pattern is not the pattern.
- Take locks in the same order in every code path, forever.
- Never hold a transaction open across a human or a network call.
- Make write operations idempotent so a retry is harmless.

# Beginner Mistakes
- Locking the row but **not re-checking** the state after acquiring it. The lock
  serialises; only the re-check *refuses*. Half the pattern is not the pattern.
- Taking locks in different orders in different functions → deadlocks that only
  appear under load, in production, at month-end.
- Holding a transaction open across a user interaction, HTTP call, or file upload.
- Assuming a slow read means it is "locked" — in Postgres readers don't block.
  Look for N+1 (ch 16) or a bad plan (ch 15) instead.
- Using one global advisory lock for everything, making the whole app single-file.
- Forgetting `select_for_update()` needs an open transaction (`@transaction.atomic`).

# Interview Questions
- **Junior:** *What is a deadlock and how does Postgres respond?* — two transactions waiting on each other's locks; Postgres detects it and aborts one with an error. Prevention = consistent lock ordering.
- **Junior:** *Do readers block writers in Postgres?* — no, thanks to MVCC. **Saying "MVCC" here marks you out.**
- **Mid:** *Optimistic vs pessimistic locking?* — pessimistic locks up front (`FOR UPDATE`, what my money paths use); optimistic detects conflict at write time via a version column and retries. Money → pessimistic.
- **Mid:** *What does `SELECT … FOR UPDATE` do?* — takes a row-level exclusive lock until the transaction ends, so concurrent writers queue.
- **Senior:** *How would you prevent double-processing of a settlement?* — advisory or row lock + **re-read and re-check the state inside the lock**, all in one transaction; make the operation idempotent so a retry is harmless.
- **Senior:** *What is an advisory lock and when would you use one?* — an application-defined lock on an arbitrary key, for serialising work that isn't a single row (a job, a numbering sequence, a per-entity workflow). My 5374/5375 domains are exactly this.
- **Staff:** *What does MVCC cost, and how do you manage it?* — dead tuples and bloat; autovacuum reclaims them, long-running transactions prevent that reclamation, and monitoring `n_dead_tup`/oldest transaction age is the operational duty. Also why `count(*)` can't be a cheap counter in Postgres.

### Why interviewers ask these — and the answer that separates levels

| Testing for | Weak answer | What lands |
|---|---|---|
| Do readers block writers? The one-word tell. | "Reads take a shared lock, so yes, sometimes." | **No — MVCC.** Readers see a snapshot; writers create new row versions. Saying **"MVCC"** marks you out immediately, because it explains *why* rather than just answering. |
| Optimistic or pessimistic — and for money? | "Optimistic locking scales better, so use that." | Pessimistic locks up front (**`SELECT … FOR UPDATE`**); optimistic detects the conflict at write time via a version column and **retries**. **For money: pessimistic** — a retry loop around a payment is a way to pay twice. |
| Can you actually prevent double-processing? | "Take a lock before the update." | The lock is half of it: **re-read and re-check the state INSIDE the lock**, in one transaction, and make the operation **idempotent** so a retry is harmless. A lock without a re-check just serialises two identical mistakes. |
| Do you know what an advisory lock is for? | "It is a lock on a row." | An **application-defined lock on an arbitrary key** — for serialising work that is not a single row: a job, a numbering sequence, a per-entity workflow. This system uses domains **5374 (settlement)** and **5375 (allocation)**, deliberately disjoint. |

**The killer follow-up:** *"What does MVCC cost you operationally?"* — **dead tuples and bloat.** Autovacuum reclaims them, **long-running transactions prevent that reclamation**, and watching `n_dead_tup` plus the oldest transaction age is the real duty. It is also why `count(*)` can never be a cheap counter in Postgres. Anyone who calls MVCC free has not operated a database.

# Revision Notes
- **MVCC**: readers never block writers; writers block writers on the same row.
- `SELECT … FOR UPDATE` reserves a row — **then re-check the state**.
- Advisory lock = lock an *idea* (`pg_advisory_xact_lock(5374)`), freed at COMMIT.
- My domains: **5374 settlement · 5375 allocation** (separate queues, on purpose).
- Deadlock cure = **consistent lock order**, not the detector.

# Cheat Sheet
- **MVCC**: readers ↔ writers never block; writers block writers on the same row
- `SELECT … FOR UPDATE` = reserve the row; **then RE-CHECK the state**
- advisory lock = lock an *idea* (`pg_advisory_xact_lock(5374)`), auto-released at COMMIT
- my domains: **5374 settlement · 5375 allocation** (separate queues on purpose)
- deadlock cure = **same lock order everywhere**, not the detector
- never hold a transaction open across a human or a network call
- inspect with `pg_stat_activity` (waits) and `pg_locks` (locks)

# My ERP Section
| Mechanism | Where in my project |
|---|---|
| Advisory lock 5374 | `adda_settlement_service._REF_LOCK` — finalize/reopen/void/numbering |
| Advisory lock 5375 | allocation / pool draw-down domain |
| Row lock + re-check | settlement row via `select_for_update()`, then state re-verify |
| Narrow row locks | contribution rows locked `of=('self',)` |
| Lock-order rule | stated in the service docstring: breaking order = deadlock |
| Deep dive | [kos: locks](../../kos/concepts/postgresql/locks.md) |

# Practice Tasks
1. **Read the code:** find `_REF_LOCK` in `config/expense/services/adda_settlement_service.py`. List every operation that takes 5374 and say why they must share one queue.
2. **Debug:** do the two-terminal `FOR UPDATE` drill. Confirm the second *write* waits and a plain `SELECT` does not — you have just witnessed MVCC.
3. **Design:** two managers press Finalize simultaneously. Write the pseudo-code that makes the second one refuse, and mark the exact line that prevents double payment.
4. **Architecture:** argue for or against replacing the advisory lock with a row lock on the Adda. What would you gain and lose?

# Homework
1. Do the two-terminal `FOR UPDATE` drill. Confirm two things: the second write **waits**, and a plain `SELECT` **does not**. That second fact is MVCC, witnessed.
2. While blocked, run the `pg_stat_activity` query and find your waiting session's `wait_event`.
3. Read `adda_settlement_service.py` around `_REF_LOCK`. Write down every operation that takes 5374, and explain why they must all share one queue.

# Further Reading & Live Resources
- [Postgres explicit locking](https://www.postgresql.org/docs/current/explicit-locking.html) — lock modes and what conflicts with what
- [Postgres MVCC](https://www.postgresql.org/docs/current/mvcc-intro.html)
- [Postgres advisory lock functions](https://www.postgresql.org/docs/current/functions-admin.html#FUNCTIONS-ADVISORY-LOCKS)
- [Django select_for_update](https://docs.djangoproject.com/en/5.0/ref/models/querysets/#select-for-update)
