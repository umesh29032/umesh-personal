---
id: sql-course-14-indexes
type: lesson
status: active
owner: handwritten
scope: sql, postgresql — database fundamentals taught from this ERP
anchors: config/expense/services/settlement_service.py, config/production/services/pool_service.py
verified: 2026-08-01
---

# 14 — Indexes

> Part of [SQL From Zero](00_COURSE_OVERVIEW.md). Prev: [13](13_Constraints.md) · Next: [15 — EXPLAIN & the Query Planner](15_EXPLAIN_And_The_Planner.md).

# Learning Objectives
By the end of this chapter you can:
- explain what an index is, and name its three costs
- predict when Postgres will *ignore* an index — and prove it with costs
- say why a composite index on (a,b) cannot serve a query on b alone
- find unused indexes in a live database

# Purpose
To understand the single biggest lever on database speed — and to watch Postgres
*refuse* to use one of my indexes, for an excellent reason, with the numbers on
screen to prove it was right.

# The Problem
`WHERE code = '3-PATTI-018'` on 28 rows: instant, who cares. The same query on
5,000,000 rows without help means reading **all five million** to find one. Every
"the page got slow as we grew" story is this. But indexes are not free magic —
they cost write speed and disk, and an index nobody uses is pure waste.

# Theory (from zero)

**Without an index — a sequential scan:** read every row, test each one, discard
the misses.

```
   SEQ SCAN: WHERE code = '3-PATTI-018'
   ┌───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┐
   │ ✗ │ ✗ │ ✗ │ ✗ │ ✗ │ ✗ │ ✓ │ ✗ │ ✗ │ ✗ │ ✗ │ ✗ │   read ALL, keep 1
   └───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┘
   my real EXPLAIN said it out loud:  "Rows Removed by Filter: 27"
```

**With an index — a sorted signpost beside the table:**

```
   INDEX on code (a B-tree, kept SORTED)
                    ┌──────────┐
                    │  M ─ P   │            ← start in the middle
                    └────┬─────┘
              ┌──────────┴──────────┐
        ┌─────▼─────┐         ┌─────▼─────┐
        │ 3-PATTI-… │         │ T-SHIRT-… │  ← halve the search each hop
        └─────┬─────┘         └───────────┘
              ▼
        row pointer ──▶ jump straight to the row in the table
   3 hops instead of 5,000,000 reads. That is what an index buys.
```

A **B-tree** (Postgres's default — and **every application index in my database is
a B-tree**; run the query in Practical #2 for today's count, which grows with every
migration) stays sorted, so lookups, ranges (`>`, `<`, `BETWEEN`) and `ORDER BY` can
all use it. Other types exist for other jobs: **GIN** for JSONB and full-text,
**GiST** for geometry/ranges, **BRIN** for huge naturally-ordered data.

**What you get for free** (Django is generous here):
- every `PRIMARY KEY` → an index automatically
- every `UNIQUE` constraint → an index automatically
- every **ForeignKey** → Django adds an index (so JOINs are fast)

**The costs — this is the part beginners skip:**

```
   ┌─────────────┬──────────────────────────────────────────────┐
   │ READS       │ ↑↑ much faster on selective lookups          │
   │ WRITES      │ ↓  slower — EVERY insert/update/delete must  │
   │             │    also update EVERY index on that table     │
   │ DISK        │ ↓  each index is a real structure on disk    │
   │ maintenance │ ↓  more things to keep statistics for         │
   └─────────────┴──────────────────────────────────────────────┘
   So: index what you actually search on. Not "everything, just in case".
```

> 💡 **Samjho aise:** Index kitab ke **peeche ka index** hai. 2 page ki kitab mein
> index kaun dekhta hai — seedha padh lo (**wahi Postgres ne mere 28-row table pe
> kiya**). 2,000 page ki kitab mein index ke bina zindagi nahi. Par yaad rakho:
> index **muft nahi** — kitab mein naya page joda, to index bhi update karna
> padega. Isi liye index un cheezon pe lagao **jo aap dhoondhte ho**, sab pe nahi.

# Real World Example (My ERP)
The five indexes on my Adda table (real):
```
 production_adda_pkey                     ← from PRIMARY KEY (id)
 production_adda_code_key                 ← from UNIQUE (code)
 production_adda_code_3633e88d_like       ← Django's extra, for LIKE 'prefix%'
 production_adda_created_by_id_9b185f35   ← FK, indexed by Django
 production_adda_product_id_1dc61736      ← FK, indexed by Django
```
Database-wide: **570-plus indexes, all B-tree** — the exact number climbs with
every migration, which is itself the point: *I never typed one.* Migrations built
them from my model definitions (ch 19).

### The surprise: Postgres ignoring my index — with receipts

```sql
EXPLAIN SELECT * FROM production_adda WHERE code = '3-PATTI-018';
--  Seq Scan on production_adda  (cost=0.00..1.31 rows=1 width=86)
--    Filter: ((code)::text = '3-PATTI-018'::text)
```
Sequential scan?! There *is* an index on `code`. So I forced the other path to see
its price:
```sql
SET enable_seqscan = off;    -- "pretend scanning isn't allowed"
EXPLAIN SELECT * FROM production_adda WHERE code = '3-PATTI-018';
--  Index Scan using production_adda_code_3633e88d_like  (cost=0.14..8.15 rows=1)
SET enable_seqscan = on;
```

```
     scanning the whole tiny table   cost  1.31   ← planner chose THIS
     going through the index         cost  8.15   ← 6× more expensive!
```

**The planner was right.** 28 rows live in one 8 KB page; reading that page once
beats opening an index *and then* reading the page. On a big table the same SQL
flips automatically — proof, from my 611-row history table:

```sql
EXPLAIN SELECT * FROM tracking_addahistory WHERE adda_id = 51;
--  Index Scan using tracking_addahistory_adda_id_28cb4f59  (cost=0.15..8.19 rows=1)
```
Same shape of query, bigger table, **index used**. I changed nothing but the data.
This is chapter 1's "declarative" promise being kept: I say *what*, Postgres
re-decides *how* as the factory grows.

# Visual Diagram
```
   HOW THE CHOICE FLIPS AS DATA GROWS
   cost
    ▲
    │            seq scan ────────────────────────────▶ (grows with row count)
    │           ╱
    │          ╱
    │─────────╳──────────── index scan ─────────────── (nearly flat: log n)
    │        ╱ │
    │       ╱  └── the crossover: below it scanning wins,
    │      ╱       above it the index wins
    └──────┴──────────────────────────────────────────▶ rows
        28 rows          611 rows            5,000,000 rows
      (my addas:       (my history:          (the future)
       seq scan)        index scan)
   The planner finds this crossover for you, on every query, every time.
```

# Practical — try it yourself
```sql
-- 1. what indexes exist on a table?
SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'production_adda';

-- 2. how many indexes on MY tables, and of what type? (all btree; count grows
--    with every migration — that is expected, not drift)
SELECT count(*) FROM pg_indexes WHERE schemaname = 'public';
--    ^ 'public' = my tables. Counting pg_class instead gives a bigger number
--      because it includes Postgres's own system + TOAST indexes.
SELECT am.amname AS type, count(*) FROM pg_class i
JOIN pg_am am ON am.oid = i.relam WHERE i.relkind = 'i' GROUP BY am.amname;

-- 3. the "ignored index" demo — run all three and compare the cost numbers
EXPLAIN SELECT * FROM production_adda WHERE code = '3-PATTI-018';   -- Seq Scan, 1.31
SET enable_seqscan = off;
EXPLAIN SELECT * FROM production_adda WHERE code = '3-PATTI-018';   -- Index Scan, 8.15
SET enable_seqscan = on;        -- ALWAYS turn it back on (session-only, but still)

-- 4. a table big enough to want its index (REAL: Index Scan)
EXPLAIN SELECT * FROM tracking_addahistory WHERE adda_id = 51;

-- 5. which of my indexes are never used? (the waste-finder — needs real traffic)
SELECT relname, indexrelname, idx_scan
FROM pg_stat_user_indexes ORDER BY idx_scan ASC LIMIT 10;
--    ^ idx_scan = 0 means "nobody has ever used this index": write cost, no read benefit
```

# Production Walkthrough
- **570-plus indexes, every one a B-tree**, and I typed none of them — migrations built them from model definitions (ch 19). PKs, UNIQUEs and every ForeignKey get one automatically.
- That automation is why the ch 07 JOINs are fast without tuning, and why the A360 page can join several tables per request.
- On the live server the same query may choose a *different* plan than on my laptop, because the row counts differ. That is correct behaviour, and the reason performance work must be measured where the data lives.
- `CREATE INDEX CONCURRENTLY` is the only safe form on a busy table — it does not block writes (and cannot run inside a transaction).

# Debugging Guide
"This query is slow":
1. **`EXPLAIN` it** (ch 15). Look for `Seq Scan` on a large table with a selective filter.
2. **Check the words.** `Index Cond:` = the index worked. `Filter:` + `Rows Removed by Filter:` = rows were read then thrown away.
3. **Is the column wrapped in a function?** `lower(email) = …` cannot use a plain index — needs an expression index.
4. **Leading wildcard?** `LIKE '%x%'` cannot use B-tree; consider `pg_trgm`.
5. **Small table?** A `Seq Scan` is correct — do not "fix" it.
6. **Then, and only then, add an index** — and verify with `pg_stat_user_indexes` that it is actually used.

# Performance Notes
- Reads faster; **writes slower** (every INSERT/UPDATE/DELETE maintains every index — ch 11); more disk.
- An index only helps a **selective** predicate. If a filter matches half the table, scanning wins.
- **Index-only scans** happen when every column needed is in the index — the table is never touched.
- Composite order matters: `(a, b)` serves `a` and `a AND b`, never `b` alone.
- Stale statistics mislead the planner; `ANALYZE` refreshes them (autovacuum usually does it for you).

# Security Considerations
- An index on a sensitive column stores that data a second time — it is inside every backup and every dump (ch 20). Indexing a secret does not make it less secret.
- Unused indexes are pure attack-surface-free waste, but they *do* slow writes; auditing them is hygiene, not paranoia.
- A missing index can be a denial-of-service vector: one expensive endpoint that scans a huge table can exhaust the connection pool.

# Architecture Decisions
- **Rely on Django's automatic indexes first** — PK, UNIQUE, FK — and add bespoke ones only from measured evidence.
- **Prefer a UNIQUE constraint over a bare index** when the rule is a business rule: you get the guarantee *and* the speed (ch 13).
- **Partial indexes for state queries** (`WHERE completed_at IS NULL`) are the right tool for "find the in-progress rows" at scale.
- **No speculative indexing** — an index nobody uses is a write tax with no return.

# Best Practices
- Measure before and after; keep the `EXPLAIN` output in the commit message.
- Index what you filter, join and sort on — not "every column".
- Use `CREATE INDEX CONCURRENTLY` in production, always.
- Review `idx_scan = 0` periodically and drop the dead weight.

# Beginner Mistakes
- "Add an index to every column." Writes slow down, disk fills, and the planner
  ignores most of them anyway.
- Expecting an index to help `LIKE '%text%'` — a leading wildcard has no prefix to
  seek (ch 06). Fix: `pg_trgm` trigram index, or full-text search.
- Expecting an index on `email` to help `WHERE lower(email) = 'x'` — the function
  hides the indexed value. Fix: an **expression index** on `lower(email)`.
- Concluding "my index is broken" from a Seq Scan on a small table. It is correct.
- Assuming a composite index on `(a, b)` helps a query filtering only on `b`.
  It cannot — see the phonebook question in Interview Questions.
- Leaving `enable_seqscan = off` on after experimenting.

# Interview Questions
- **Junior:** *What is an index, and what does it cost?* — a sorted lookup structure that speeds reads; costs write speed and disk.
- **Junior:** *Which indexes do you get automatically?* — PRIMARY KEY and UNIQUE constraints create them; Django additionally indexes ForeignKeys.
- **Mid:** *My column is indexed but the query is slow. Why?* — leading-wildcard LIKE, a function wrapping the column, a tiny table where scanning wins, stale statistics, or low selectivity (the value matches most rows).
- **Mid:** *Composite index on `(a, b)` — does it serve `WHERE b = ?`* — **no.** It is sorted by `a` first, exactly like a phonebook sorted by surname cannot find people by first name. It serves `a` alone, or `a AND b`. **Classic question.**
- **Senior:** *When is a Seq Scan the right plan?* — small tables, or when the predicate matches a large fraction of rows (random index lookups then cost more than one sequential sweep). My 28-row Adda table is the textbook case, with cost 1.31 vs 8.15.
- **Senior:** *What is a covering index / index-only scan?* — when every column the query needs is in the index, Postgres can answer without touching the table at all (`INCLUDE (...)` helps build these).
- **Staff:** *How do you add an index to a busy production table safely?* — `CREATE INDEX CONCURRENTLY` (does not block writes, cannot run inside a transaction, and can leave an INVALID index to clean up if it fails). Then verify with `pg_stat_user_indexes` that it is actually used.

### Why interviewers ask these — and the answer that separates levels

| Testing for | Weak answer | What lands |
|---|---|---|
| Do you know an index is a **trade**, not a free win? | "Indexes make queries fast." | Faster reads, **slower writes, more disk** — and every write must update every index on that table. Name the cost before the benefit. |
| Do you understand *leftmost prefix*? | "It is indexed, so it is covered." | A composite `(a, b)` cannot serve `WHERE b = ?` — it is sorted by `a` first, like a phonebook by surname. Say **leftmost prefix** and give the phonebook. |
| Do you trust measurement over instinct? | "Add an index and it will be fast." | `EXPLAIN ANALYZE` first. Sometimes Seq Scan **is** the right plan — on my 28-row Adda table the planner picks cost **1.31** over the index at **8.15**, and it is right. |
| Can you ship an index without an outage? | "CREATE INDEX." | `CREATE INDEX CONCURRENTLY` — no write lock, **cannot run inside a transaction**, and can leave an INVALID index to clean up. Then confirm use via `pg_stat_user_indexes`. |

**The killer follow-up:** *"You added the index. Did the query actually get faster — show me the two plans."* Anyone can add an index. Only someone who has read a plan can prove it helped.

# Revision Notes
- Index = sorted signpost. Faster reads, **slower writes**, more disk.
- Free with PK/UNIQUE; Django adds them on FKs (570+ here, all B-tree).
- Cannot help `'%mid%'`, `func(col)`, or a tiny table.
- Composite `(a,b)`: serves `a`, `a+b`, **never `b` alone**.
- Postgres chose Seq Scan (1.31) over Index (8.15) on 28 rows — and was right.

# Cheat Sheet
- index = sorted signpost; B-tree is the default (all of mine are)
- free with PK / UNIQUE; Django adds them on FKs
- helps: `=`, ranges, `ORDER BY`, prefix `LIKE 'x%'`
- cannot help: `'%x%'`, `func(col) = …` (needs an expression index), tiny tables
- composite `(a,b)`: serves `a` and `a+b`, never `b` alone
- costs: slower writes + disk · find dead ones via `idx_scan = 0`
- `CREATE INDEX CONCURRENTLY` in production

# My ERP Section
| Index | Why it exists |
|---|---|
| `production_adda_pkey` | PRIMARY KEY (id) |
| `production_adda_code_key` | UNIQUE(code) — one code per Adda (ch 13) |
| `production_adda_code_…_like` | Django's helper for `code LIKE '3-PATTI-%'` (ch 06) |
| `…_product_id_…`, `…_created_by_id_…` | FKs — makes the ch 07 JOINs fast |
| `tracking_addahistory_adda_id_…` | 611 rows → real Index Scan |
| Deep dive | [kos: indexes](../../kos/concepts/postgresql/indexes.md) · [query-performance](../../kos/concepts/postgresql/query-performance.md) |

# Practice Tasks
1. **Read the code:** list the indexes on `expense_workerledgerentry`. For each, say which model declaration created it.
2. **Debug:** run the `enable_seqscan = off` demo. Write both cost numbers down and explain in one sentence why the planner preferred the scan.
3. **Design:** the dashboard needs "all in-progress Addas" on a table with 5 million rows. Design the index. Why is a *partial* index the right answer?
4. **Architecture:** argue whether to add an index for a report that runs once a month. What is the write cost you are accepting every day for it?

# Homework
1. Run the three-step "ignored index" demo. Write down both cost numbers and explain, in one sentence, why 1.31 beat 8.15.
2. List the indexes on `expense_workerledgerentry`. Which ones did Django create for you, and from what?
3. Run the `idx_scan = 0` query. Are there indexes in my database nobody has used? (Careful: my dev traffic is tiny, so this is indicative, not proof.)

# Further Reading & Live Resources
- [Use The Index, Luke](https://use-the-index-luke.com/) — the free book; read the first three chapters slowly
- [Postgres index types](https://www.postgresql.org/docs/current/indexes-types.html)
- [Postgres CREATE INDEX (incl. CONCURRENTLY)](https://www.postgresql.org/docs/current/sql-createindex.html)
- [Use The Index, Luke](https://use-the-index-luke.com/) — the best free book on indexing, full stop
- [Postgres docs — Index types](https://www.postgresql.org/docs/current/indexes-types.html) — B-tree, hash, GiST, GIN, BRIN, and when each earns its keep
- [Postgres docs — Indexes and ORDER BY / multicolumn](https://www.postgresql.org/docs/current/indexes-ordering.html) — why column order in a composite index decides whether it is used
- [Postgres docs — `CREATE INDEX CONCURRENTLY`](https://www.postgresql.org/docs/current/sql-createindex.html#SQL-CREATEINDEX-CONCURRENTLY) — adding an index without locking writes in production
- Sibling chapter: [15 — EXPLAIN & the Planner](15_EXPLAIN_And_The_Planner.md) — proving an index is actually used, instead of hoping
