---
id: sql-course-24-scaling-and-limitations
type: lesson
status: active
owner: handwritten
scope: sql, postgresql — database fundamentals taught from this ERP
anchors: config/expense/services/settlement_service.py, config/production/services/pool_service.py
verified: 2026-08-01
---

# 24 — Scaling & Limitations: What Postgres Is NOT Good At

> Part of [SQL From Zero](00_COURSE_OVERVIEW.md). Prev: [23](23_JSONB.md) · Next: [25 — Interview Master Sheet](25_Interview_Master_Sheet.md).

# Learning Objectives
By the end of this chapter you can:
- recite the scaling ladder in order, and say which rung you are on
- name six things Postgres is genuinely not good at
- explain why two databases cannot share a transaction
- answer "SQL vs NoSQL" naming the trade rather than picking a side

# Purpose
To learn my tool's **edges**. Everything so far taught what Postgres does superbly.
Nothing marks an engineer as senior faster than knowing, precisely and without
defensiveness, where their favourite tool stops being the right answer.

# The Problem
My factory database is 26 MB with 28 Addas. Postgres finds this comical — it is
built for terabytes. So the honest risk is not "will Postgres cope?" (it will, for
years). The risk is **reaching for the wrong tool later**, or believing marketing
about systems that traded away the exact guarantees my payroll depends on.

# Theory (from zero)

### The scaling ladder — in the order you should climb it

```
   ①  DO LESS WORK          fix N+1 (ch 16), add the right index (ch 14)
       │                    ← 90% of "we need to scale" is actually this
       ▼
   ②  SCALE UP              more RAM/CPU/faster disk on ONE machine
       │                    ← Postgres does this superbly; boring and effective
       ▼
   ③  CONNECTION POOLING    PgBouncer — thousands of clients, few DB connections
       │                    (each Postgres connection is a real OS process)
       ▼
   ④  READ REPLICAS         copy the WAL to followers; send reports there
       │                    ⚠️ replication lag: a replica can be seconds behind
       ▼
   ⑤  PARTITIONING          one huge table split by range/list (e.g. by month)
       │                    still one database, still transactional
       ▼
   ⑥  SHARDING              split WRITES across machines — genuinely hard,
                            loses cross-shard transactions. Last resort.
   ═══════════════════════════════════════════════════════════════════════
   My factory sits comfortably at ① for the foreseeable future.
   Knowing the ladder exists is the point; climbing it prematurely is the mistake.
```

### The six honest limitations

**1. Files.** Photos, videos, PDFs belong on disk or object storage; the DB keeps
paths (ch 21). My project already does this — and pays the honest price: a DB dump
is not a full backup.

**2. One machine for writes.** Postgres scales *up* magnificently and *reads* out
via replicas, but multi-machine **write** scaling means sharding, which is external
and hard. NoSQL systems (Cassandra, DynamoDB) chose the opposite trade: easy
horizontal writes, weaker guarantees. **For money, choose the guarantees.**

**3. Fixed schema.** Every column declared up front (ch 03). JSONB is the pressure
valve, and chapter 23 catalogued exactly what it costs.

**4. Search.** `LIKE '%term%'` cannot use a B-tree (ch 06/14). Postgres has decent
built-in full-text search and trigram indexes — enough for most apps. Google-grade
relevance ranking wants a dedicated engine (Elasticsearch, Meilisearch, Typesense).

**5. Transactions stop at the database boundary.**

```
   ONE database                     TWO databases
   ┌──────────────────────┐         ┌──────────┐   ┌──────────┐
   │ BEGIN                │         │ BEGIN    │   │ BEGIN    │
   │  write A             │         │  write A │   │  write B │
   │  write B             │         │ COMMIT ✔ │   │ ✗ FAILS  │
   │ COMMIT — atomic ✅   │         └──────────┘   └──────────┘
   └──────────────────────┘         → A committed, B did not.
                                      NO shared atomicity. Ever.
   ⇒ This is the deep technical reason behind my ADR-0010:
     "multi-factory = ONE database + a site dimension, NEVER a fork."
     Two deployments = two ledgers that can never be reconciled.
```

**6. Analytics at extreme scale.** Aggregating billions of rows across all history
is columnar-warehouse territory (ClickHouse, BigQuery, DuckDB). Row-store Postgres
is fine for operational reporting; know where the line is.

**Bonus limitation worth knowing:** `count(*)` on a huge table is **slow** in
Postgres — MVCC (ch 18) means visibility is per-transaction, so there is no cheap
global counter. Use `pg_class.reltuples` for an estimate, or maintain a counter.

> 💡 **Samjho aise:** Postgres ek **bahut mazboot bada almirah** hai — usme tumhari
> poori factory rakh lo, hil bhi nahi jayega. Par almirah **ek jagah khada** hai:
> zyada jagah chahiye to bada almirah lo (scale up), padhne wale zyada hain to
> uski **copy** rakh do (replica). Par do alag almirah rakh ke ek hi taala dono pe
> lagana **naamumkin** hai — isi liye paise ka register kabhi do almirah mein nahi
> baantte. Aur photo? Wo almirah mein nahi, alag godown mein — almirah sirf pata
> rakhta hai.

# Real World Example (My ERP)
```
   MY REAL NUMBERS vs WHERE THE LIMITS ACTUALLY ARE
   ═══════════════════════════════════════════════════════════════════
   inventory_db size      26 MB          Postgres routine: terabytes
   biggest table          611 rows       routine: 100,000,000+ rows
   ledger entries         201            banks run billions here
   indexes                772 (B-tree)   fine; GIN available if JSONB needs it
   live connections       1              PgBouncer matters around hundreds
   ═══════════════════════════════════════════════════════════════════
   Verdict: I am ~6 orders of magnitude from any Postgres limit.
   My real constraints are all in ① — query counts and correct indexes.
```

Where the limits *do* already touch my project, concretely:
- **Files:** `config/media/` holds every photo; the DB stores paths only (ch 21).
  Consequence already documented as finding **F-4**.
- **Cross-database atomicity:** `ADR-0010 Decision 2` forbids forking the ledger
  into a second deployment for exactly the reason in limitation 5. It is *accepted
  policy*, not a preference — and note nothing is built yet: a second factory would
  be a `site` dimension **inside** one database.
- **Search:** my Adda lookups are prefix searches (`code LIKE '3-PATTI-%'`) which
  are index-friendly; I have deliberately not needed full-text search.
- **JSONB:** confined to `patterns_ai` (ch 23) — schema flexibility bought only
  where shape really varies.

# Visual Diagram
```
   CHOOSING THE RIGHT STORE  (the decision I should be able to defend)
   ═══════════════════════════════════════════════════════════════════════
   Does it need transactions, constraints, exact money?
        │
        ├── YES ─────────▶  PostgreSQL   ← my ERP. Not negotiable.
        │
        └── NO ──┬── is it a FILE (photo/video/pdf)?
                 │        └──▶ disk / S3-style object storage + a path in the DB
                 │
                 ├── is it a CACHE / counter / rate-limit?
                 │        └──▶ Redis  (my login lockouts live here — ch 21)
                 │
                 ├── is it FULL-TEXT relevance search at scale?
                 │        └──▶ Postgres FTS first; Elasticsearch if truly needed
                 │
                 └── is it BILLIONS of rows of analytics?
                          └──▶ columnar warehouse (ClickHouse / BigQuery)
   ═══════════════════════════════════════════════════════════════════════
   "Use Postgres until it hurts, and know exactly where it will hurt."
```

# Practical — try it yourself
```sql
-- 1. how big is my database really, and its biggest tables?
SELECT pg_size_pretty(pg_database_size(current_database())) AS total;
SELECT relname, n_live_tup, pg_size_pretty(pg_total_relation_size(relid)) AS size
FROM pg_stat_user_tables ORDER BY n_live_tup DESC LIMIT 5;

-- 2. connection reality check (each connection is an OS process)
SELECT count(*) AS live FROM pg_stat_activity WHERE datname = current_database();
SHOW max_connections;
--    ^ when app instances × pool size approaches this, you need PgBouncer

-- 3. the count(*) limitation — exact vs estimated
SELECT count(*) FROM tracking_addahistory;              -- exact: scans
SELECT reltuples::bigint AS estimate FROM pg_class
WHERE relname = 'tracking_addahistory';                 -- instant estimate

-- 4. memory knobs the planner and sorts depend on
SHOW work_mem;          -- per-sort/hash memory (spills to disk beyond this)
SHOW shared_buffers;    -- Postgres's own page cache

-- 5. is anything actually straining? (cache hit ratio; >99% is healthy)
SELECT sum(heap_blks_hit) * 100.0 / nullif(sum(heap_blks_hit + heap_blks_read),0)
       AS cache_hit_pct FROM pg_statio_user_tables;

-- 6. MVCC's cost from ch 18, made visible (dead rows awaiting vacuum)
SELECT relname, n_dead_tup FROM pg_stat_user_tables
ORDER BY n_dead_tup DESC LIMIT 5;
```

# Production Walkthrough
- **Current reality: 26 MB, biggest table 611 rows, one live connection.** That is roughly six orders of magnitude from any Postgres limit — the honest headline of this chapter.
- The real constraints here are all rung ①: query counts (ch 16) and correct indexes (ch 14).
- **ADR-0010 is the scaling decision already made**: a second factory becomes a `site` dimension inside one database, never a second deployment, because two databases cannot share a transaction.
- Files already live outside the database (`config/media/`), so the "don't put blobs in Postgres" rule is followed — and the honest price is that a DB dump is not a full backup (ch 20, 21).

# Debugging Guide
"We think we need to scale":
1. **Measure first.** `pg_stat_statements` for the worst queries; count queries per request (ch 16).
2. **Check the cache hit ratio** (`pg_statio_user_tables`) — below ~99% suggests memory, not architecture.
3. **Check connections** against `max_connections`; if app instances × pool size is close, you need PgBouncer, not a bigger database.
4. **Check for bloat** (`n_dead_tup`) and long-running transactions blocking autovacuum (ch 18).
5. **Only then** consider replicas, partitioning, sharding — in that order.

# Performance Notes
- Postgres scales **up** superbly; reads scale out via replicas; writes stay on one primary.
- Each connection is an OS process — pooling matters long before sharding does.
- `count(*)` is O(rows) because of MVCC visibility; use `reltuples` for estimates.
- Partitioning helps time-series pruning inside one database and keeps transactions intact; sharding gives that up.

# Security Considerations
- Every scaling step adds surface: a replica is another host with a full copy of your data, and it needs the same firewall, TLS and backup discipline.
- Connection poolers sit between app and database and see every query — they are part of the trust boundary.
- Sharding often leaks data across boundaries through "just this one cross-shard query"; that is a security and correctness risk, not only a performance one.

# Architecture Decisions
- **One machine, one database, until measured otherwise.** Boring, cheap, and correct for a factory's load.
- **Never fork the ledger** (ADR-0010) — the strongest architectural constraint in the whole system, and it comes from ch 17's atomicity boundary.
- **Files to object storage, not the database** — already true, with the backup consequence documented rather than hidden.
- **Cache/rate-limit state deliberately outside the DB** (Redis), accepting that it is lost on restart because it is not truth.

# Best Practices
- Fix the query before buying the server.
- State RPO/RTO before designing for scale — availability targets drive topology (ch 20).
- Keep one source of truth even when adding replicas: route must-be-current reads to the primary.
- Write down the scaling decision *and its reason* (this project has an ADR for exactly that).

# Beginner Mistakes
- Reaching for "we need NoSQL / sharding" when the real problem is N+1 or a missing
  index. **Almost always step ①.**
- Storing files as bytea/blobs in the database.
- Adding a read replica and then reading your own just-written data from it —
  replication lag makes that a real, confusing bug class.
- Assuming a replica helps write throughput. It does not; writes still go to one primary.
- Believing "Postgres doesn't scale" from a benchmark that measured a missing index.
- Splitting a ledger across two databases and expecting to reconcile it later.
- Treating `count(*)` on a large table as free.

# Interview Questions
- **Junior:** *When would you NOT use a relational database?* — very large binary files, pure caching, extreme write-scale key-value workloads, or genuinely schema-less document stores.
- **Junior:** *Vertical vs horizontal scaling?* — a bigger machine vs more machines; Postgres favours vertical plus read replicas.
- **Mid:** *SQL vs NoSQL — how do you decide?* — need transactions, constraints and exact arithmetic → SQL; need extreme horizontal write scale or truly variable documents → NoSQL. Name the **trade** (guarantees vs scale-out) and pick SQL for money without hedging. **The most common system-design opener.**
- **Mid:** *What does a connection pooler solve?* — Postgres connections are heavyweight OS processes; PgBouncer multiplexes many client connections onto a few server ones.
- **Senior:** *Read replicas — what breaks?* — replication lag: read-after-write inconsistency, stale reports, and failover complexity. Route reads that must be current to the primary.
- **Senior:** *Partitioning vs sharding?* — partitioning splits a table within one database (still transactional, planner-aware, great for time-series pruning); sharding splits data across databases/machines and gives up cross-shard transactions and joins.
- **Staff:** *Your company wants a second factory on the same system. Design it.* — a `site` dimension inside **one** database (FK on the batch entity, scoped queues and dashboards), with globally unique references so any future consolidation is a filter rather than a renumbering — explicitly **not** a second deployment, because forking splits the ledger into two unmergeable sets of books with no shared atomicity. *(That is ADR-0010, and it is the mature answer.)*
- **Staff:** *Postgres is "too slow" at 500 GB. Your first three moves?* — measure (`pg_stat_statements`, EXPLAIN the top offenders), fix query counts/indexes, then partition the hot table by time and move reporting to a replica — before anyone says "shard".

### Why interviewers ask these — and the answer that separates levels

| Testing for | Weak answer | What lands |
|---|---|---|
| SQL vs NoSQL — do you name the **trade**? | "NoSQL scales better, SQL is more structured." | Name the actual trade: **guarantees vs scale-out**. Transactions, constraints and exact arithmetic → SQL. Extreme horizontal *write* scale or genuinely variable documents → NoSQL. **For money, pick SQL without hedging** — the hedge is what loses the point. |
| Do you know why connections are expensive in Postgres? | "Too many connections slow the server down." | Each connection is a **heavyweight OS process**. That is why **PgBouncer** multiplexes many client connections onto a few server ones — and why worker×thread arithmetic matters more than traffic when sizing. |
| Read replicas — what actually breaks? | "Replicas take load off the primary, so it is a win." | **Replication lag**: read-after-write inconsistency (a worker submits, then sees stale data), stale reports, and failover complexity. **Route reads that must be current to the primary** — and know which of your reads those are. |
| Partitioning vs sharding — do you keep them apart? | "Both split the data up." | **Partitioning** splits a table **within one database** — still transactional, planner-aware, excellent for time-series pruning. **Sharding** splits across databases/machines and **gives up cross-shard transactions and joins**. Conflating them is how a team accidentally signs up for the hard one. |

**The killer follow-up:** *"The company wants a second factory on this system. Design it."* — a **`site` dimension inside ONE database** (FK on the batch entity, scoped queues and dashboards) with globally unique references, so a future consolidation is a **filter, not a renumbering**. Explicitly **not** a second deployment: forking splits the ledger into two unmergeable sets of books with **no shared atomicity**. That is ADR-0010, and it is the mature answer.

# Revision Notes
- Ladder: **do less work → scale up → pool → replicas → partition → shard**.
- Weak at: files · multi-machine writes · rigid schema · relevance search · cross-DB transactions · huge analytics.
- **No shared transaction across two databases** ⇒ never fork a ledger.
- Replicas scale reads and introduce **lag**.
- I am ~6 orders of magnitude from any Postgres limit — the bottleneck is my code.

# Cheat Sheet
- ladder: **do less work → scale up → pool → replicas → partition → shard**
- Postgres is weak at: **files · multi-machine writes · rigid schema (JSONB helps) · relevance search · cross-DB transactions · huge analytics**
- files → object storage + path in DB · cache/counters → Redis
- **no shared transaction across two databases** ⇒ never fork a ledger (ADR-0010)
- replicas scale **reads**, and introduce **lag**
- `count(*)` is not free (MVCC); use `reltuples` for estimates
- I am ~6 orders of magnitude from any Postgres limit

# My ERP Section
| Limitation | How my project handles it |
|---|---|
| Files not in the DB | `config/media/` + paths; F-4 in [FRESH_DB_REQUIREMENTS](../FRESH_DB_REQUIREMENTS.md) |
| No cross-DB atomicity | **ADR-0010 Decision 2**: one database + future `site` dimension, never a fork |
| Fixed schema | JSONB confined to `patterns_ai` (ch 23) |
| Search | prefix `LIKE 'CODE-%'` (index-friendly); no FTS needed yet |
| Cache/rate-limit state | outside the DB (login lockouts, ch 21) |
| Current scale | 26 MB · biggest table 611 rows · 1 live connection |

# Practice Tasks
1. **Read the code:** open `docs/adr/0010-growth-and-identity-policy.md`, Decision 2. Restate it in your own words and name the ch 17 property it depends on.
2. **Debug:** run the size, connection and cache-hit queries from Practical. Write down which rung of the ladder you are actually on.
3. **Design:** design the `site` dimension for a second factory — which table gets the FK, and which queries must change?
4. **Architecture:** the owner asks for a live analytics dashboard over all history. At what data volume does Postgres stop being the right tool, and what would you move to?

# Homework
1. Run Practical #1 and #2. Write down your database size, biggest table, and live connection count. Then say which rung of the ladder you are on.
2. Run Practical #3 (exact vs estimated count). Explain why MVCC makes the exact count expensive.
3. Answer the Staff "second factory" question out loud, from memory, in under 60 seconds. Then check it against ADR-0010.

# Further Reading & Live Resources
- [Postgres: high availability & replication](https://www.postgresql.org/docs/current/high-availability.html)
- [Postgres table partitioning](https://www.postgresql.org/docs/current/ddl-partitioning.html)
- [PgBouncer](https://www.pgbouncer.org/) — the standard connection pooler
- [Postgres full-text search](https://www.postgresql.org/docs/current/textsearch.html)
- [Use The Index, Luke](https://use-the-index-luke.com/) — because step ① is usually the answer
