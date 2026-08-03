---
id: sql-course-15-explain-and-the-planner
type: lesson
status: active
owner: handwritten
scope: sql, postgresql — database fundamentals taught from this ERP
anchors: config/expense/services/settlement_service.py, config/production/services/pool_service.py
verified: 2026-08-01
---

# 15 — EXPLAIN & the Query Planner

> Part of [SQL From Zero](00_COURSE_OVERVIEW.md). Prev: [14](14_Indexes.md) · Next: [16 — From ORM to SQL, and N+1](16_ORM_To_SQL_And_N_Plus_1.md).

# Learning Objectives
By the end of this chapter you can:
- read a plan tree innermost-first and name each node
- tell `Index Cond` from `Filter` and say why it matters
- use estimated-vs-actual rows to diagnose bad statistics
- EXPLAIN a write safely, without changing anything

# Purpose
To stop guessing why a query is slow. `EXPLAIN` is the x-ray: it shows the exact
plan Postgres chose, what it estimated, and — with `ANALYZE` — what actually
happened. This chapter turns performance work from folklore into measurement.

# The Problem
A page is slow. The temptations are all bad: add indexes at random, rewrite the
query by vibe, blame "the server". None of these tell me *what Postgres is
actually doing*. Optimising without measuring is superstition with a keyboard.

# Theory (from zero)

Between my `;` and the rows coming back, four stages:

```
   my SQL text
       │
   ①  PARSER      "is this valid SQL?"           → a parse tree
       │
   ②  PLANNER     "what are ALL the ways to      → THE interesting part
       │           get this answer, and which
       │           costs least?"                    uses table STATISTICS
       │
   ③  EXECUTOR    runs the winning plan          → streams rows
       │
   ④  rows to me
```

**The planner is an accountant, not a magician.** It knows roughly how many rows
each table has and how values are distributed (statistics, refreshed by
`ANALYZE`/autovacuum). For each candidate plan it estimates a **cost** in
arbitrary units and picks the cheapest. Chapter 14 showed it choosing cost 1.31
over 8.15 — that arithmetic *is* the planner.

**Reading a plan — the two rules:**
1. **Read innermost/most-indented first.** Plans are trees; children feed parents.
2. **Cost is `startup..total`** — `cost=0.00..1.31` means "first row at 0.00,
   all rows by 1.31".

**The node types you will actually meet:**

| Node | Meaning |
|---|---|
| `Seq Scan` | read the whole table |
| `Index Scan` | walk the index, then fetch each row |
| `Index Only Scan` | answer entirely from the index (table never touched) |
| `Bitmap Heap Scan` | many index matches → collect, then read pages in order |
| `Nested Loop` | for each row of A, look up B — great when A is tiny |
| `Hash Join` | build a hash of one side, stream the other — great for big joins |
| `Merge Join` | both sides sorted, zip them together |
| `Aggregate` / `HashAggregate` | your `count`/`sum`/`GROUP BY` (ch 08) |
| `Sort` | your `ORDER BY` (watch for `external merge Disk`) |

**`EXPLAIN` vs `EXPLAIN ANALYZE`:**

```
   EXPLAIN          → the PLAN only. Nothing runs. Always safe.
   EXPLAIN ANALYZE  → actually RUNS the query, then shows plan + real timings.
                      ⚠️ on an UPDATE/DELETE this really writes! Wrap in
                      BEGIN; … ROLLBACK; if the statement is not a SELECT.
```

The gold is in comparing **estimated vs actual**:
`rows=1` (estimate) next to `rows=1` (actual) = the planner understands your data.
`rows=1` next to `rows=50000` = it is flying blind, and the plan is probably wrong.

> 💡 **Samjho aise:** Planner ek **tez munshi** hai jo kaam shuru karne se pehle
> hisaab lagata hai: *"is register ko poora padhna sasta padega, ya index se
> dhoondhna?"* Aur register mota hone ke saath **apna faisla khud badal leta hai**
> — mujhe query nahi badalni padti. `EXPLAIN` uska **kaagaz pe likha plan** hai;
> `EXPLAIN ANALYZE` plan ke saath **stopwatch** bhi. Andaaza lagane ki jagah
> **naap lo** — dheeme page ka ilaaj wahin se shuru hota hai.

# Real World Example (My ERP)
Real `EXPLAIN ANALYZE` on my Adda lookup — annotated:

```
 Seq Scan on production_adda  (cost=0.00..1.31 rows=1 width=86)
                              (actual time=0.010..0.011 rows=1 loops=1)
   Filter: ((code)::text = '3-PATTI-018'::text)
   Rows Removed by Filter: 27          ← read 28, threw away 27, kept 1
 Planning Time: 0.518 ms               ← deciding took LONGER than doing
 Execution Time: 0.025 ms              ← 25 microseconds
```

Three lessons in five lines:
1. `Rows Removed by Filter: 27` — a sequential scan, admitted in plain text.
2. **estimate `rows=1` vs actual `rows=1`** — the planner's statistics are accurate.
3. Planning 0.518 ms > execution 0.025 ms. On tiny tables **thinking costs more
   than working** — which is exactly why micro-optimising my dev database teaches
   nothing about production.

Contrast, on my 611-row history table — the index gets used:
```
 Index Scan using tracking_addahistory_adda_id_28cb4f59  (cost=0.15..8.19 rows=1)
   Index Cond: (adda_id = 51)
```
Note `Index Cond` (the index did the filtering) versus `Filter` (rows were read
then discarded). **That word tells you whether your index actually worked.**

And an aggregate plan, from `count(*)` on my 370-row session table:
```
 Aggregate  (cost=32.58..32.59 rows=1 width=8)
   ->  Seq Scan on django_session  (cost=0.00..31.66 rows=366 width=0)
```
Read it inside-out: scan the table (child), then aggregate (parent). Also note
`rows=366` estimated vs 370 actual — statistics are *approximate by design*.

# Visual Diagram
```
   READING A PLAN TREE  (innermost first, children feed parents)

   Aggregate                          ③ finally: count them
     └─▶ Hash Join                    ② then: match the two sides
           ├─▶ Seq Scan on adda       ① first: read this
           └─▶ Hash                   ① and build a hash of this
                 └─▶ Seq Scan on product

   ┌────────────────────────────────────────────────────────────┐
   │  WORD TO LOOK FOR          WHAT IT MEANS                    │
   │  Index Cond:               the index did the work  ✅        │
   │  Filter:                   rows read, then thrown away  ⚠️   │
   │  Rows Removed by Filter:   how much work was wasted         │
   │  rows=1 vs actual rows=9k  statistics are WRONG  🔴          │
   │  external merge Disk       sort spilled to disk 🔴 (work_mem)│
   └────────────────────────────────────────────────────────────┘
```

# Practical — try it yourself
```sql
-- 1. plan only, nothing runs
EXPLAIN SELECT * FROM production_adda WHERE code = '3-PATTI-018';

-- 2. plan + real timings (REAL output in the section above)
EXPLAIN ANALYZE SELECT * FROM production_adda WHERE code = '3-PATTI-018';

-- 3. a JOIN plan — see which join algorithm my data earns
EXPLAIN ANALYZE
SELECT a.code, p.name FROM production_adda a
JOIN production_product p ON p.id = a.product_id;

-- 4. an aggregate plan (ch 08's ledger total)
EXPLAIN ANALYZE SELECT sum(amount) FROM expense_workerledgerentry;

-- 5. the full-detail version, when you are serious:
EXPLAIN (ANALYZE, BUFFERS, VERBOSE)
SELECT u.email, sum(l.amount) FROM expense_workerledgerentry l
JOIN accounts_user u ON u.id = l.worker_id GROUP BY u.email;
--    BUFFERS shows pages read from cache vs disk — "shared hit" vs "read"

-- 6. refresh the statistics the planner relies on (safe, read-mostly maintenance)
ANALYZE production_adda;

-- 7. EXPLAIN a write SAFELY — the seatbelt from ch 11:
BEGIN;
  EXPLAIN ANALYZE UPDATE raw_materials_clothcolor SET updated_at = now()
  WHERE name = 'does-not-exist';
ROLLBACK;
```

# Production Walkthrough
- On my 28-row Adda table, **planning took 0.518 ms and execution 0.025 ms** — thinking cost 20× more than working. That is why micro-optimising a dev database teaches nothing about production.
- The same query shape picks `Index Scan` on the 611-row history table. Nothing changed but the data — this is the declarative promise from ch 01 being kept.
- In production the useful tool is `pg_stat_statements` (aggregate slowest queries), not EXPLAIN on a hunch.
- The kos playbook `page-slow-or-erroring` puts **counting queries** before reading plans, because most slow pages are N+1 (ch 16).

# Debugging Guide
The order that actually works:
1. **Count the queries for the request.** If it is 50, no plan will save you (ch 16).
2. **`EXPLAIN ANALYZE` the worst single query.**
3. **Compare estimated vs actual rows.** A 1-vs-90,000 gap means bad statistics → `ANALYZE`, or correlated columns needing extended statistics.
4. **Look for `Filter` + `Rows Removed by Filter`** — visible wasted work.
5. **Check for `external merge Disk`** in sorts — raise `work_mem` or reduce the sort.
6. **Add `BUFFERS`** to see cache hits vs disk reads before blaming the disk.
7. ⚠️ **Wrap `EXPLAIN ANALYZE` of a write in `BEGIN … ROLLBACK`** — ANALYZE *executes*.

# Performance Notes
- `EXPLAIN` alone is free (no execution). `EXPLAIN ANALYZE` pays the full query cost.
- Planning time is per-execution; thousands of trivial queries each pay it — another reason N+1 hurts twice.
- Cost units are arbitrary and only comparable *within* one plan comparison.
- `ANALYZE` (the maintenance command) is cheap and often the whole fix.

# Security Considerations
- Plans can leak schema detail (table and column names, row counts). Never surface raw EXPLAIN output in a user-facing error page.
- `EXPLAIN ANALYZE` on a write statement in production is a real footgun — it performs the write. Treat it as a production change, not a read.

# Architecture Decisions
- **Measure, then change** — this project treats "add an index" as requiring evidence, which is why the audit reported cost numbers rather than opinions.
- **Keep queries in the ORM** so plans stay consistent and reviewable, dropping to SQL only where needed (ch 16, 22).
- **Trust the planner; feed it facts.** Indexes and statistics, not hints — Postgres has no query hints by design.

# Best Practices
- Read plans innermost-first, every time.
- Always compare estimate to actual before theorising.
- Keep a copy of the plan before and after your change.
- Turn `enable_seqscan` back on after experimenting.

# Beginner Mistakes
- Running `EXPLAIN ANALYZE` on an `UPDATE`/`DELETE` and being surprised it *ran*.
  Plain `EXPLAIN` is safe; `ANALYZE` executes.
- Tuning against my 28-row dev database and expecting production truth. Plan
  choices *change with size* — that is the whole point of chapter 14's crossover.
- Reading a plan top-down and getting the order of operations backwards.
- Seeing `Seq Scan` and immediately adding an index, without checking whether the
  table is small or the predicate unselective.
- Ignoring the estimate-vs-actual gap — the single most diagnostic number on screen.
- Forgetting that `Planning Time` counts too: thousands of trivial queries each pay
  planning cost (which is chapter 16's real subject).

# Interview Questions
- **Junior:** *What does EXPLAIN do?* — shows the execution plan Postgres would use, without running the query.
- **Junior:** *EXPLAIN vs EXPLAIN ANALYZE?* — plan vs plan-plus-real-execution (and ANALYZE actually runs it).
- **Mid:** *How do you read a plan?* — innermost/most-indented first; each node's cost is `startup..total` and includes its children; compare estimated to actual rows.
- **Mid:** *`Index Cond` vs `Filter` — why does the distinction matter?* — Index Cond means the index restricted the rows; Filter means rows were fetched and then discarded (visible waste in `Rows Removed by Filter`).
- **Senior:** *Estimated 1 row, actual 90,000 — what do you do?* — the statistics are stale or the distribution is skewed/correlated: run `ANALYZE`, raise the statistics target, consider extended statistics for correlated columns, and re-check the plan. A wrong estimate usually means a wrong join algorithm downstream.
- **Senior:** *Nested Loop vs Hash Join — when is each right?* — nested loop wins when the outer side is tiny and the inner is indexed; hash join wins for large unsorted sets; merge join when both inputs are already sorted.
- **Staff:** *Your endpoint is slow but every individual query looks fast in EXPLAIN. Next step?* — count the queries. Latency is usually N+1 round-trips, not one bad plan (ch 16). Measure at the request level (query counts, `pg_stat_statements`) before touching plans.

### Why interviewers ask these — and the answer that separates levels

| Testing for | Weak answer | What lands |
|---|---|---|
| Can you actually read a plan, or only run it? | "I run EXPLAIN and look for Seq Scan." | Read **innermost/most-indented first**; each node's cost is `startup..total` and **includes its children**; then compare **estimated vs actual rows**. Seq Scan is not automatically bad — on my 28-row Adda table it wins at cost **1.31** against the index at **8.15**. |
| `Index Cond` vs `Filter` — do you know the difference? | "Both mean the index was used." | **`Index Cond`** = the index restricted the rows. **`Filter`** = rows were fetched **and then thrown away** — the waste is printed as `Rows Removed by Filter`. That line is where your missing index is hiding. |
| Estimated 1 row, actual 90,000 — what now? | "The query is just slow, add an index." | That gap means **stale or skewed statistics**, and a wrong estimate usually picks a **wrong join algorithm downstream**. Run `ANALYZE`, raise the statistics target, consider **extended statistics** for correlated columns, then re-read the plan. |
| Do you know which join belongs where? | "Hash join is the fast one." | **Nested Loop** wins when the outer side is tiny and the inner is indexed · **Hash Join** for large unsorted sets · **Merge Join** when both inputs are already sorted. The planner is choosing, not guessing. |

**The killer follow-up:** *"Every query in this endpoint is fast in EXPLAIN, but the page takes 2 seconds. Next step?"* — **count the queries.** Latency is usually N+1 round-trips, not one bad plan (ch 16). Measure at the request level (`pg_stat_statements`, query counts) before touching a single plan.

# Revision Notes
- `EXPLAIN` = plan (safe) · `EXPLAIN ANALYZE` = plan + timings (**it runs**).
- Read **innermost first**; `cost=startup..total`.
- `Index Cond` ✅ index used · `Filter` ⚠️ read-then-discard.
- Estimate vs actual rows is the most diagnostic number on screen.
- Planning can cost more than execution on small tables.

# Cheat Sheet
- `EXPLAIN` = plan (safe) · `EXPLAIN ANALYZE` = plan + timings (**it runs**)
- read **innermost first**; `cost=startup..total`
- `Index Cond` ✅ index worked · `Filter` ⚠️ read-then-discard
- estimate vs actual rows = the truth-teller; fix with `ANALYZE`
- `BUFFERS` shows cache hits vs disk reads
- planning can cost more than execution on small tables
- one slow query ≠ a slow page — count queries too (ch 16)

# My ERP Section
| Observation | Real value in my DB |
|---|---|
| Adda lookup plan | `Seq Scan`, cost 1.31, `Rows Removed by Filter: 27` |
| Planning vs execution | 0.518 ms vs 0.025 ms — thinking dominates at this size |
| Index actually used | `tracking_addahistory` (611 rows) → `Index Scan`, `Index Cond` |
| Statistics approximate | session table estimated 366, actual 370 |
| Debugging playbook | [kos: page-slow-or-erroring](../../kos/debugging/page-slow-or-erroring.md) · [query-performance](../../kos/concepts/postgresql/query-performance.md) |

# Practice Tasks
1. **Read the code:** pick any list view and get its SQL via `.query` (ch 16), then `EXPLAIN ANALYZE` it. Name every node in the tree.
2. **Debug:** find a query in this database whose estimate differs from actual by more than 2×. Run `ANALYZE` on the table and re-check.
3. **Design:** you must prove a proposed index helps. Write the exact before/after measurement procedure you would put in the pull request.
4. **Architecture:** Postgres deliberately has no query hints. Argue why that is a good design decision for a long-lived system.

# Homework
1. `EXPLAIN ANALYZE` the Adda lookup. Find `Rows Removed by Filter` and say what it proves.
2. `EXPLAIN ANALYZE` the ch 08 per-worker GROUP BY. Name every node in the tree, innermost first, and find where the grouping happens.
3. Compare `EXPLAIN` output for `WHERE code = '3-PATTI-018'` versus `WHERE code LIKE '%PATTI%'`. Which one says `Index Cond` and which says `Filter`? Explain using chapter 6.

# Further Reading & Live Resources
- [Postgres: Using EXPLAIN](https://www.postgresql.org/docs/current/using-explain.html) — the authoritative walkthrough
- [explain.depesz.com](https://explain.depesz.com/) — paste a plan, get it colour-coded and ranked by cost
- [PEV2 — visual plan explorer](https://explain.dalibo.com/) — free, renders the tree graphically
- [Use The Index, Luke — execution plans](https://use-the-index-luke.com/sql/explain-plan)
