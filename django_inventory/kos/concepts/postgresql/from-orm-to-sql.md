---
id: concept-from-orm-to-sql
type: concept
verified: 2026-07-19
knowledge_confidence: verified_against_code
answers: "When I write a Django queryset, what SQL actually runs, and how do I SEE it instead of guessing?"
related: [concept-pg-indexes, concept-query-performance, concept-django-transactions]
---

# From ORM to SQL — stop guessing, start reading

> 📂 [PostgreSQL concepts](README.md) · [All concepts](../README.md) · [KOS home](../../README.md)

## 1. The project hook

Every money number on every screen of this system is a queryset. When
`worker_balance` looks slow, or a payroll total looks wrong, "the ORM did
something" is not an answer. This page teaches the full chain — **ORM →
generated SQL → what PostgreSQL actually did** — using this repo's real
queries, so you can interrogate any queryset you will ever write.

## 2. 💡 Samjho Aise

ORM ek translator hai — tum Hindi mein bolte ho, wo PostgreSQL ki bhasha
mein anuvad karta hai. Translator par bharosa theek hai, par paisa uske
anuvad par chalta hai — to anuvad PADHNA seekho. Teen kadam: kya bola
(queryset), kya anuvad hua (SQL), aur sunne wale ne kya SAMJHA aur KIYA
(EXPLAIN). Teeno alag cheez hain.

## 3. Mental Model

> A queryset is a **description, not a command** — lazy until iterated.
> `str(qs.query)` shows the *approximate* translation. The database's
> `EXPLAIN` shows the *actual decision*. Three artifacts, three questions:
> what did I ask? what SQL was sent? what plan did PostgreSQL choose?
> Debugging persistence = knowing which of the three to look at.

## 4. Technical Deep Dive — the chain, on a REAL query

**Step 1 — the ORM** (a real aggregation, run today on the dev DB):

```python
(WorkerLedgerEntry.objects
    .filter(worker_id=2, entry_type='credit')
    .values('category')                 # → GROUP BY
    .annotate(total=Sum('amount'))      # → aggregate per group
    .order_by('-total'))
```

**Step 2 — the generated SQL** (`str(qs.query)`, captured live):

```sql
SELECT "expense_workerledgerentry"."category",
       SUM("expense_workerledgerentry"."amount") AS "total"
FROM "expense_workerledgerentry"
WHERE ("expense_workerledgerentry"."entry_type" = credit
       AND "expense_workerledgerentry"."worker_id" = 2)
GROUP BY "expense_workerledgerentry"."category"
ORDER BY 2 DESC
```

Read the translation rules straight off it: `values()` before `annotate()`
became `GROUP BY category`; the `Sum` became an aggregate over each group;
`-total` became `ORDER BY 2 DESC` (position!, because total is an alias).

**⚠ The `str(qs.query)` gotcha you must know:** see `= credit` — unquoted.
`str(qs.query)` interpolates params NAÏVELY for display; it is NOT the wire
SQL and can even be invalid to paste. The REAL statement is parameterized
(`entry_type = %s` + bound params — which is also why SQL injection can't
ride through the ORM). For exact executed SQL use
`django.db.connection.queries` (DEBUG) or `CaptureQueriesContext` (tests) —
that's how this page's captures were made.

**Step 3 — what PostgreSQL actually DID** (`EXPLAIN (ANALYZE, BUFFERS)`,
live, on the balance query from [transactions §6](../django/transactions.md#6-how-this-project-uses-it)):

```
Aggregate  (cost=6.16..6.17 rows=1 width=64) (actual time=0.353..0.353 rows=1)
  Buffers: shared hit=4
  ->  Seq Scan on expense_workerledgerentry  (cost=0.00..6.12 rows=3 width=11)
        Filter: (worker_id = 2)
        Rows Removed by Filter: 168
Execution Time: 0.397 ms
```

Read it bottom-up (inner node feeds outer): PG **seq-scanned all 170 rows**
(4 buffer pages), threw away 168, aggregated 2 — and this was the RIGHT
choice: the whole table is 4 pages; an index round-trip costs more.
[indexes](indexes.md) continues this exact story.

**How to read any EXPLAIN, the 5-line version:**
1. Bottom-up: leaves are scans (Seq/Index/Bitmap), parents consume them.
2. `cost=a..b` = planner's estimate (startup..total, arbitrary units);
   `actual time` (with ANALYZE) = reality in ms. Estimates wrong by 10×+ =
   stale statistics → `ANALYZE tablename`.
3. `rows=` estimate vs `rows=` actual — the most important comparison on
   the page: bad row estimates cause bad plans.
4. `Buffers: shared hit` = pages from cache; `read` = from disk.
5. `Rows Removed by Filter` = work wasted — the number indexes exist to shrink.

## 5. Engineering Thinking

*Why not just trust the ORM?* Trust, but be ABLE to verify — the ORM
optimizes for correctness and composability, not for your specific query's
plan. The senior discipline: any query on a hot path or money surface gets
its SQL read once and its plan read once — then you KNOW, and query-count
pins ([query-performance](query-performance.md)) keep it known. *Why
parameterized SQL matters twice:* injection safety AND plan reuse — PG can
cache plans for repeated shapes. *When to drop to raw SQL:* this repo
almost never does — the FILTER-aggregates, Coalesce resolvers, and grouped
sums are all expressible in ORM (`Sum(filter=Q(...))`, `Coalesce`) — and
staying in ORM keeps queries composable with `.filter()` at call sites.
Raw SQL is the escape hatch AFTER `EXPLAIN` proves the ORM can't express
the efficient shape, not before.

## 6. How THIS project uses it

The repo's signature ORM patterns, each a translation worth knowing:
- **Conditional aggregation** — `Sum('amount', filter=Q(entry_type=CREDIT))`
  → SQL `SUM(amount) FILTER (WHERE entry_type='credit')` — one pass, two
  sums (`worker_balance`, `worker_balance_breakdown`, `payroll_totals`).
- **SQL-side resolver** — `Coalesce('verified_quantity', 'good_quantity')`
  in `pool_service` — the verified-else-good rule computed IN the query,
  not in Python loops.
- **Grouped board aggregate** — `outstanding_advances_bulk`: one
  `values('worker').annotate(...)` for the whole payroll overview instead
  of N per-worker queries.
- **Capture tooling** — `CaptureQueriesContext(connection)` in perf tests:
  the same tool this page used, pinned into the battery (12
  `assertNumQueries` pins).

## 7. What breaks without it

You ship a page that "works" — then someone `.filter()`s inside a template
loop and the ORM's laziness politely runs 300 queries. Or a report sums in
Python what SQL would aggregate in one pass. Nobody notices in dev (170
rows!); production notices. The chain-reading habit is the vaccine.

## 8. Common mistakes (humans)

- Pasting `str(qs.query)` into psql and trusting it (unquoted params — it lies politely).
- Reading `cost=` as milliseconds — it's unitless planner arithmetic.
- Running `EXPLAIN ANALYZE` on WRITES casually — ANALYZE **executes** the
  statement; wrap in `BEGIN; ... ROLLBACK;` or you just ran the write.
- Forgetting querysets are lazy — the query runs at iteration, so the slow
  line in the profiler is the `for`, not the `.filter()`.

## 9. AI Implementation Pitfalls

- ❌ Rewriting an ORM query to raw SQL "for performance" without an EXPLAIN
  showing the ORM shape is the problem — composability lost for nothing.
- ❌ Moving aggregation into Python loops (the ORM expresses FILTER/Coalesce/
  GROUP BY — this repo proves it).
- ❌ Adding `.distinct()` or `.select_related()` speculatively "to be safe" —
  each changes the SQL; read what you generated.
- ✅ Always verify: after touching any hot queryset, capture its SQL + plan
  once; keep the query-count pin green.

## 10. DSA & Complexity

`GROUP BY` = hash-aggregate (build a hash map keyed by group) or
sort-aggregate — check which your EXPLAIN chose (`HashAggregate` vs
`GroupAggregate`); hash is O(n) with memory, sort is O(n log n) streaming.
The FILTER-aggregate trick = one O(n) pass computing k sums instead of k
passes — loop fusion, in SQL clothing.

## 11. Interview corner

*Interview Signal: 🟡 Mid — reading generated SQL separates mid from junior.*

**Q. "How do you debug a slow Django query?"**
- *Short:* Get the real SQL (connection.queries / CaptureQueriesContext), run `EXPLAIN (ANALYZE, BUFFERS)`, compare estimated vs actual rows, fix the biggest waste (scan shape, missing index, N+1 at the call site).
- *Senior:* Distinguish the three artifacts — description (queryset), translation (SQL), decision (plan). Most "ORM is slow" cases are call-site problems (laziness in loops) or plan problems (stale stats, wrong index), not translation problems. And measure on production-shaped data — planners change their minds with row counts.
- *Project example:* the balance query's honest Seq Scan at 170 rows (right choice, proven with BUFFERS=4); FILTER-aggregates replacing double scans; 12 pinned query counts keeping regressions loud.
- *Follow-ups:* "What does ANALYZE do vs plain EXPLAIN?" (executes; needs rollback care) · "Why is str(qs.query) unsafe to trust?" (naïve interpolation) · "HashAggregate vs GroupAggregate?" (memory vs ordering).

## 12. 🧠 Remember This

Queryset = farmaish, SQL = anuvad, EXPLAIN = asliyat. Teeno padhna aata ho
to ORM jaadu nahi, kaanch ka gilaas hai — aar-paar dikhta hai.
`str(qs.query)` jhooth-sa sach hai (params naqli); asli SQL
CaptureQueriesContext se; asli faisla EXPLAIN se.

## 13. 30-Second Revision

- Lazy: query runs at iteration, not definition
- values()+annotate() = GROUP BY; Sum(filter=Q()) = FILTER aggregate; Coalesce = SQL-side resolver
- str(qs.query) = display-only (unquoted params); real SQL = connection.queries/CaptureQueriesContext
- EXPLAIN: read bottom-up · cost=estimate (unitless) · ANALYZE=reality (and EXECUTES!) · est-vs-actual rows = the tell · Rows Removed = waste
- Raw SQL only AFTER EXPLAIN proves ORM can't express the shape

## 14. What You Should Now Understand

The three-artifact chain and which to inspect for which symptom; how this
repo's signature patterns translate; how to read a plan in five lines.
Shaky? Re-run §4's capture yourself in shell — 3 minutes.

**Recommended next topic:** [indexes](indexes.md) — continues the SAME
captured query into the "why did PG ignore my index?" story.

## Implementation References

- Live captures: dev DB 2026-07-19 (`CaptureQueriesContext` + `EXPLAIN (ANALYZE, BUFFERS)`)

## Code References
- `ledger_service.worker_balance` · `payroll_service.worker_balance_breakdown` / `outstanding_advances_bulk` · `pool_service` Coalesce
- Pins: 12 `assertNumQueries` across `test_perf_settlement.py`, `test_perf_baseline.py`, `test_queue_batching.py`, `test_a360_overview.py`, `accounts/tests.py`

## Further Reading

- Official: [Django — QuerySet API](https://docs.djangoproject.com/en/5.0/ref/models/querysets/) · [PostgreSQL — Using EXPLAIN](https://www.postgresql.org/docs/current/using-explain.html)

## Related

[indexes](indexes.md) · [query-performance](query-performance.md) ·
[transactions](../django/transactions.md) · [ledger](../../features/ledger.md)
