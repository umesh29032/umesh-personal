---
id: concept-pg-indexes
type: concept
verified: 2026-07-19
knowledge_confidence: verified_against_code
answers: "Which indexes does this project declare, why each one — and why does PostgreSQL sometimes ignore them?"
related: [concept-from-orm-to-sql, concept-query-performance, feature-ledger]
---

# PostgreSQL Indexes — declared for the future, judged by the planner

> 📂 [PostgreSQL concepts](README.md) · [All concepts](../README.md) · [KOS home](../../README.md)

## 1. The project hook

The ledger declares FIVE indexes. Today's live `EXPLAIN` on the balance
query shows PostgreSQL using **none of them** — a Seq Scan, 168 rows thrown
away, 0.4 ms. Was declaring them a mistake? No — and understanding WHY both
facts are correct at once is the entire skill of indexing.

## 2. 💡 Samjho Aise

Index = kitaab ke peeche ka vishay-soochi (back-of-book index). 4 panne ki
pustika mein index kaun dekhta hai? Poori palat lo, jaldi hai. Par 4,000
panne ki kitaab mein index ke bina dhoondhna saza hai. PostgreSQL har baar
khud hisaab lagata hai: "palatna sasta hai ya soochi dekhna?" — aur 170-row
ki dev-table par palatna hamesha jeet'ta hai. Index bekaar nahi hua;
kitaab abhi patli hai.

## 3. Mental Model

> An index is a **standing offer, not an order.** You declare access paths;
> the cost-based planner accepts the offer only when statistics say it's
> cheaper than scanning. So index design = predicting your REAL query
> shapes (WHERE/ORDER BY/JOIN columns) at production scale — and then
> verifying with EXPLAIN at something like that scale, never at dev size.

## 4. Technical Deep Dive — the full chain, live

**Declared** (`WorkerLedgerEntry.Meta.indexes` — each maps to a query shape):

| Index | The query it serves |
|---|---|
| `(worker, -created_at)` | worker's statement, newest-first (`worker_ledger`) |
| `(worker, entry_type)` | THE balance aggregate (credit/debit split) |
| `(worker, category)` | per-category breakdowns (`debits_by_category`) |
| `(worker, entry_date)` | settlement-window / period statements |
| `(entry_date)` | global period reports |

Plus the ones Django created without being asked: the PK, **an index per
plain FK** (advance, assignment, settlement, reverses, created_by — that's
why FKs are cheap to JOIN), and `uniq_one_reversal_per_entry` (the partial
unique — an index doing constraint duty).

**The live evidence, both directions** (dev DB, today):

Planner's free choice — ignores the index:
```
Seq Scan on expense_workerledgerentry  (cost=0.00..6.12 rows=3)
  Filter: (worker_id = 2)          Rows Removed by Filter: 168
  Buffers: shared hit=4            ← the WHOLE table is 4 pages
```

Same query, `SET enable_seqscan=off` (proving the path exists and works):
```
Bitmap Heap Scan on expense_workerledgerentry  (cost=4.17..8.41 rows=3)
  Recheck Cond: (worker_id = 2)
  -> Bitmap Index Scan on expense_wor_worker__6c8504_idx (cost=0.00..4.17)
```

Read the costs: index path 8.41 vs seq scan 6.12 — **at 170 rows the index
is genuinely more expensive** (index pages + heap pages vs just 4 heap
pages). At 170,000 rows the same arithmetic flips by orders of magnitude.
The planner isn't moody; it's doing cost math on `pg_class`/`pg_statistic`
numbers refreshed by autovacuum's ANALYZE.

**Composite index rules this repo's declarations follow:**
- **Leftmost prefix**: `(worker, entry_type)` serves `worker=?` alone too —
  but NOT `entry_type=?` alone. Order columns equality-first, most-selective
  first.
- **Direction**: `(worker, -created_at)` bakes the newest-first ORDER BY
  into the btree — no sort node needed for the statement view.
- **Partial**: the reversal unique indexes ONLY rows `WHERE reverses_id IS
  NOT NULL` — small, and doubles as a constraint
  ([pg/constraints](constraints.md)).

## 5. Engineering Thinking

*Why declare before the data justifies?* Because indexes on empty tables
are free and indexes on huge tables are a migration event (build time,
locks — `CREATE INDEX CONCURRENTLY` exists for a reason). This repo
declares at design time from QUERY SHAPES, not from observed slowness —
the shapes were known (statement, balance, period). *The cost of the
habit:* every INSERT updates every index — the append-only ledger pays 5+
index writes per money row, forever. That's a conscious trade: this table
is write-few-read-many. On a write-hot table you'd prune. *What a senior
refuses:* indexing every column "to be safe" (write amplification + planner
confusion), and TRUSTING dev-size EXPLAIN as proof for production behavior
— the plan you saw is a function of the row count you had.

## 6. How THIS project uses it

The `worker_balance` docstring says it plainly: *"ONE indexed
conditional-aggregate (index worker,entry_type)"* — the code KNOWS which
index it's built for; the comment binds query to access path. The perf
suite then pins query COUNTS (12 `assertNumQueries`) rather than
milliseconds — counts are stable across machines, plans aren't
([query-performance](query-performance.md) takes it from here). And the
FK-index freebie is why the settlement detail page can `select_related`
across advance/assignment/settlement chains without JOIN pain.

## 7. What breaks without it

Nothing — today, at 170 rows. That's the trap. The ledger grows forever
(append-only); at year-two scale every payroll screen recomputes balances
over a table that no longer fits in 4 pages. Missing indexes fail SLOWLY —
no error, just a system that ages badly. Declared-from-shapes indexes are
how this repo pre-paid that debt.

## 8. Common mistakes (humans)

- "PG ignored my index → PG is broken / force it" — read the cost math first;
  at your row count it may be right.
- Composite in the wrong order — `(entry_type, worker)` would serve the
  balance query badly (low-selectivity column first).
- Forgetting FK auto-indexes and adding duplicates.
- Testing index effect with dev-sized data — the planner answers a
  different question than production will ask.
- `EXPLAIN` without `ANALYZE`/`BUFFERS` when investigating — estimates
  alone can't reveal stale statistics.

## 9. AI Implementation Pitfalls

- ❌ Adding an index per slow-page report without reading the plan — the
  common real cause is N+1 at the call site, not a missing index.
- ❌ Removing "unused" indexes based on dev-DB EXPLAINs — usage is a
  function of scale; check `pg_stat_user_indexes` in PRODUCTION.
- ❌ Reordering composite columns during a "cleanup" — the leftmost prefix
  contract silently breaks dependent queries.
- ✅ Always verify: new hot query → name the index it should use in a
  comment (the `worker_balance` convention) + capture one EXPLAIN.

## 10. DSA & Complexity

A btree index = sorted structure: point lookup O(log n), range scan
O(log n + k). Seq scan = O(n) but with PERFECT locality (sequential pages).
The planner's whole job is comparing `log n × random-page-cost` against
`n ÷ rows-per-page × seq-page-cost` — the same tradeoff you know as
"binary search a sorted array vs scan a small one; for small n, scanning
wins because of constants." Today's 6.12-vs-8.41 costs are that lecture,
running live in your database.

## 11. Interview corner

*Interview Signal: 🟡 Mid — index reasoning is the classic mid-level probe.*

**Q. "You added an index but the query didn't get faster. Walk me through it."**
- *Short:* EXPLAIN first — is the index even used? Small table (seq scan wins), wrong column order (leftmost prefix), stale stats, or the time was never in the scan (N+1, sort, network).
- *Senior:* Indexes are offers evaluated by a cost model over statistics. Verify at representative scale; compare estimated vs actual rows for stats drift; check the index actually matches the predicate shape (equality columns leading, direction for ORDER BY). And measure where time went before touching the schema — the plan tells you.
- *Project example:* the ledger's 5 declared indexes vs today's honest Seq Scan at 170 rows, WITH the forced-off proof that the path exists; costs 6.12 vs 8.41 read straight from the plans.
- *Follow-ups:* "When would you use a partial index?" (the one-reversal constraint — small + doubles as armor) · "Index-only scans?" (covering indexes; needs visibility map) · "Cost of an index?" (write amplification per INSERT — append-only tables pay forever).

## 12. 🧠 Remember This

Index ek khada hua PRASTAAV hai — hukum nahi. Planner ka hisaab: chhoti
kitaab palto, badi mein soochi kholo. Shape se declare karo (WHERE/ORDER
BY), production-jaisi scale par EXPLAIN se jancho, aur har INSERT ki
index-keemat yaad rakho. Patli kitaab ka Seq Scan galti nahi — samajhdari hai.

## 13. 30-Second Revision

- 5 declared ledger indexes, each ↔ a named query shape; FKs auto-indexed; partial unique = index-as-constraint
- Planner = cost model over stats; small table ⇒ Seq Scan is CORRECT (6.12 < 8.41, live proof)
- Composite: equality/selective columns first; leftmost prefix; direction for ORDER BY
- Every INSERT pays every index — append-only tables pay forever (conscious trade)
- Verify at scale; `pg_stat_user_indexes` for real usage; comment binds query↔index

## 14. What You Should Now Understand

Why declared-but-unused is often correct, how to read the planner's choice
and force-test the alternative, composite ordering rules, and the write
cost you sign up for. Shaky? Re-read §4's two plans side by side.

**Recommended next topic:** [query-performance](query-performance.md) —
where time ACTUALLY goes in this app, and how the repo pins it.

## Implementation References

- Live plans: dev DB 2026-07-19, both directions (free choice + `enable_seqscan=off`)

## Code References
- Declarations: `WorkerLedgerEntry.Meta.indexes` (`config/expense/models.py`) — comment-bound query in `ledger_service.worker_balance`

## Further Reading

- Official: [PostgreSQL — Indexes](https://www.postgresql.org/docs/current/indexes.html) · [Row estimation](https://www.postgresql.org/docs/current/planner-stats.html)
- One resource: *Use The Index, Luke* (Markus Winand) — read the btree +
  composite chapters; skip vendor-specific parts.

## Related

[from-orm-to-sql](from-orm-to-sql.md) · [query-performance](query-performance.md) ·
[constraints](constraints.md) · [ledger](../../features/ledger.md)
