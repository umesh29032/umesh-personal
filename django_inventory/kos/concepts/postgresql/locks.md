---
id: concept-pg-locks
type: concept
verified: 2026-07-19
knowledge_confidence: verified_against_code
answers: "When does this project lock rows vs take advisory locks, and why is lock ORDER the whole game?"
related: [concept-django-transactions, feature-settlement, feature-payroll]
---

# PostgreSQL Locks — freeze exactly what you bill

> 📂 [PostgreSQL concepts](README.md) · [All concepts](../README.md) · [KOS home](../../README.md)

## 1. The project hook

Manager A clicks *Finalize* on settlement ADST-0007. At the same second,
manager B corrects Meena's verified quantity from 38 to 35. Without locks,
finalize bills 38 while the row already says 35 — a **lost update on money**.
This exact scenario is why `finalize_adda_settlement` locks
`WorkerStageContribution` rows — a real fix in this repo (PA-11-3).

## 2. 💡 Samjho Aise

Do taale hain factory mein. **Kamre ka taala** (row lock) — "yeh almari
abhi meri hai, main gin raha hoon." **Gate ka taala** (advisory lock) —
"settlement ka kaam chal raha hai, doosra settlement rukega." Kamra to
almari ke saath aata hai; gate ka taala tumhe khud banana padta hai —
PostgreSQL sirf number maangta hai (5374), matlab tum do.

## 3. Mental Model

> Ask two questions, always in this order: **"What must not CHANGE while I
> read-and-bill it?"** → row locks (`select_for_update`) on exactly those
> rows. **"What operation must not RUN TWICE concurrently?"** → an advisory
> lock naming that operation. Then the senior question: **"in what ORDER?"**
> — because two correct locks in two different orders are a deadlock.

## 4. Technical Deep Dive

**Row locks** — `select_for_update()` → SQL `FOR UPDATE`: the selected rows
are yours until commit; others' `FOR UPDATE` reads WAIT, plain reads don't
(PostgreSQL readers never block on writers — MVCC).

- `of=('self',)` — the repo's hard-won variant: locking a queryset that
  `select_related`s a **nullable** FK makes PG refuse (`FOR UPDATE cannot be
  applied to the nullable side of an outer join`). `of` names which table
  actually gets locked. Real bug, real fix, remembered in the chokepoint doc.

**Advisory locks** — `SELECT pg_advisory_xact_lock(key)`: PostgreSQL
maintains the lock, YOU define the meaning of the key. Transaction-scoped
(`_xact_`) = auto-release on commit/rollback — no leak possible.

**This repo's advisory namespace** (disjoint by design):

| Key | Meaning | Taken by |
|---|---|---|
| **5374** | "a settlement-system money operation is running" | create_draft, finalize, reverse, `set_pay_basis` (joins so a basis flip can't race finalize) |
| **5375** (+objid) | pool draw-down per pool object | `pool_service` allocate/void — production-side, deliberately DISJOINT from 5374 |
| SETL ref lock | serialize `SETL-xxxx` reference allocation | `settlement_service.create_settlement` |

Why advisory for the gates: the thing being protected ("the settlement
operation") spans SIX tables — there is no single row that represents it.
You lock the *concept*, so you invent a key for the concept.

**The order — this repo's money lock sequence** (memorize; canonical in the
chokepoint doc):

```
pg_advisory_xact_lock(5374)          -- the gate, ALWAYS first
→ AddaSettlement row                 -- the event
→ AddaStageRecord rows               -- the stage snapshot
→ WorkerStageContribution of=('self',)  -- the billed quantities (PA-11-3)
→ WorkerProfile rows, sorted by worker_id  -- per-worker serialization
→ WorkerAdvance rows                 -- recovery targets
```

Two rules inside it: **gate first** (every settlement op — so a lighter op
like `set_verified_quantity`, which takes only its WSC row, can never
deadlock against finalize: finalize already holds the gate) and **sorted
worker order** (all transactions walk worker locks small→large — circular
wait impossible).

## 5. Engineering Thinking

*Why not rely on `transaction.atomic`?* Atomicity ≠ isolation-for-your-
read-then-write: READ COMMITTED lets two transactions both read DRAFT and
both proceed ([transactions](../django/transactions.md) Q2). *Why not
SERIALIZABLE?* You'd trade targeted, predictable waits for global retry
storms — and money code with retries must be idempotent EVERYWHERE, a far
bigger tax than six ordered lock lines. *Why not Redis locks?* The truth
lives in PostgreSQL; a lock in a different system can't be released
atomically with the commit it protects — PG advisory `_xact_` locks die
WITH the transaction, no crashed-holder problem, no TTL guessing.
*Assumption:* every writer path goes through the services that know the
order — single-writer discipline is what makes a documented order
enforceable at all.

## 6. How THIS project uses it

Three worked specimens, all in code you can read tonight:
1. **Finalize** — the full sequence above
   (`adda_settlement_service.finalize_adda_settlement`).
2. **The reference race** — two clerks, different workers, same
   `SETL-0002` computed → second INSERT dies on unique → 500. Per-worker
   locks CANNOT fix a cross-worker race; the advisory lock can
   (`settlement_service.create_settlement`, comment tells the whole story).
3. **The stable-row trick** — over-pay race fixed by locking
   `WorkerProfile`: a lock target that ALWAYS exists, unlike the worker's
   advances (empty set for cash-only payments locks nothing)
   ([payroll](../../features/payroll.md)).

## 7. What breaks without it

PA-11-3's lost update (bill 38, truth 35) · double-finalize double-pay ·
`SETL` reference 500s under two clerks · over-payment on concurrent cash
events · and the subtlest: ad-hoc lock ordering that works for months, then
deadlocks on the busiest day of the year — deadlocks are load-triggered,
which is why order is designed, not debugged.

## 8. Common mistakes (humans)

- Locking AFTER reading the value you bill (lock, THEN re-read — the
  pre-lock read is stale by definition).
- `select_for_update` outside `transaction.atomic` — Django refuses; the
  lock has no transaction to live in.
- Locking parent rows and assuming children are frozen (the PA-11-3 lesson:
  lock what you READ-and-bill, not what feels parental).
- Long computation while holding locks — validate and compute first, lock
  late, commit fast.

## 9. AI Implementation Pitfalls

- ❌ Adding any settlement-adjacent operation that takes row locks WITHOUT
  taking 5374 first — instant deadlock lottery.
- ❌ Inventing a new advisory key that overlaps 5374/5375 semantics — the
  namespaces are disjoint BY DESIGN; new key = owner decision.
- ❌ "Optimizing away" the WSC lock because SRs are already locked — that
  reverts PA-11-3.
- ❌ Redis/file locks around DB writes — wrong system owns the truth.
- ✅ Always verify: the documented order in the chokepoint doc still matches
  the code after ANY lock change; concurrency tests + goldens green.

## 10. DSA & Complexity

Deadlock = cycle in the waits-for graph. **Total ordering of lock
acquisition makes cycles impossible** — every edge points "up" the order,
and a DAG has no cycles. That's the whole theorem behind `sorted(by_worker)`
— an O(n log n) sort buys deadlock-freedom, the cheapest correctness
purchase in the repo. (Same idea you know from resource-ordering solutions
to dining philosophers.)

## 11. Interview corner

*Interview Signal: 🟠 Senior — lock ordering/deadlock-freedom is pure senior territory.*

**Q. "Row locks vs advisory locks — when each?"**
- *Short:* Rows exist → `FOR UPDATE`. The thing you're protecting is an *operation or concept* with no single row → advisory.
- *Senior:* Advisory locks are named mutexes the DB referees: transaction-scoped ones release atomically with your commit — no orphaned-holder problem external lock stores have. But they protect nothing by themselves; every participant must agree to take them. That agreement is an architectural property (here: single-writer services).
- *Project example:* 5374 gates the settlement system (6 tables, no single row); WSC rows get `FOR UPDATE of=('self',)` because their quantities are what gets billed.
- *Follow-ups:* "Why `of=('self',)`?" (nullable-FK outer-join refusal) · "How do you prevent deadlocks?" (total order; gate-first) · "What does a plain SELECT see while rows are locked?" (last committed version — MVCC, readers don't block).

## 12. 🧠 Remember This

Do sawal: kya CHANGE nahi hona chahiye (row lock — wahi rows jo bill hongi),
kaun sa kaam DO BAAR nahi chalna chahiye (advisory — concept ka taala).
Phir EK order, hamesha wahi: gate pehle, kamre baad mein, worker sorted.
Deadlock ka ilaaj order hai, luck nahi.

## 13. 30-Second Revision

- `select_for_update` = FOR UPDATE; writers wait, readers don't (MVCC)
- `of=('self',)` — nullable-FK outer join refusal (real repo bug)
- Advisory `pg_advisory_xact_lock(key)` = named mutex, dies with the transaction
- 5374 settlement gate · 5375+objid pool · SETL ref lock — disjoint namespaces
- Money order: 5374 → ADST → SR → WSC → profiles(sorted) → advances
- Lock-then-re-read; lock what you bill; sorted order = no cycles

## 14. What You Should Now Understand

The two lock species and the question each answers, why the gate+order
design makes deadlocks structurally impossible, the three real races this
repo fixed, and why advisory-in-PG beats external lock stores. Shaky?
Re-read §4 + §6.

**Recommended next topic:** [pg/constraints](constraints.md) — the walls
that hold even when every lock is bypassed.

## Implementation References

- Canonical order: [chokepoint doc](../../../docs/LEARNING_2_0/CHOKEPOINTS/adda_settlement_service.md) · lessons [docs/LEARNING/03](../../../docs/LEARNING/03_TRANSACTIONS_AND_LOCKS.md)

## Code References
- `adda_settlement_service.finalize_adda_settlement` · `settlement_service.create_settlement` (both lock stories in comments) · `pool_service` (5375)

## Further Reading

- Official: [PostgreSQL — Explicit locking](https://www.postgresql.org/docs/current/explicit-locking.html) · [Advisory locks](https://www.postgresql.org/docs/current/explicit-locking.html#ADVISORY-LOCKS)

## Related

[transactions](../django/transactions.md) · [settlement](../../features/settlement.md) ·
[payroll](../../features/payroll.md) · [single-writer](../architecture/single-writer.md)
