---
id: sql-course-pointer
type: topic-canonical
status: superseded
owner: handwritten
scope: sql, postgresql — pointer to the chapter course
anchors: docs/sql_course/00_COURSE_OVERVIEW.md
verified: 2026-08-01
title: SQL & PostgreSQL course — MOVED
supersedes: this single file was the first draft
canonical: docs/sql_course/00_COURSE_OVERVIEW.md
---

# ➡️ This course now lives in `docs/sql_course/`

> **⚠️ SUPERSEDED (2026-07-31)** — this single-file draft is *superseded by*
> [docs/sql_course/00_COURSE_OVERVIEW.md](sql_course/00_COURSE_OVERVIEW.md), the 26-file
> chapter course. Nothing was deleted: every topic here was expanded there.

The single-file draft has been replaced by a **26-file chapter course** in the same
format as the [Deployment course](deployment_course/00_COURSE_OVERVIEW.md) — basic
→ advanced, one topic per file, 12 fixed sections per chapter (Purpose · Problem ·
Theory · Real World Example (My ERP) · Visual Diagram · Practical · Beginner
Mistakes · Interview Questions · Cheat Sheet · My ERP Section · Homework ·
Further Reading).

## 👉 Start here: [docs/sql_course/00_COURSE_OVERVIEW.md](sql_course/00_COURSE_OVERVIEW.md)

```
   Part A — Foundations        01 What is a database · 02 Tables/rows/keys
                              03 Data types & money  · 04 NULL
   Part B — Reading data      05 SELECT · 06 Filtering · 07 JOINs
                              08 GROUP BY · 09 Subqueries & CTEs · 10 Window fns
   Part C — Writing data      11 INSERT/UPDATE/DELETE · 12 Append-only money
                              13 Constraints
   Part D — The engine        14 Indexes · 15 EXPLAIN & planner
                              16 ORM → SQL & N+1 · 17 Transactions & ACID
                              18 Locks, concurrency, MVCC
   Part E — Operations        19 Migrations · 20 Backups & restore
                              21 Databases, branching & what's NOT in the DB
                              22 Security & SQL injection
   Part F — The edges         23 JSONB · 24 Scaling & limitations
                              25 Interview master sheet
```

Every example is a **real query against my own factory database with its real
output** (28 Addas · ledger 201 rows / ₹18,254.25 · 115 tables · 188 migrations).
Each chapter carries a 💡 Samjho-aise box, ASCII diagrams, an explicit limitation,
Junior→Staff interview questions with answers, and free online resources.

**Practise safely:** `./scripts/db.sh branch sql_practice --use`
(then `./scripts/db.sh use inventory_db` to come home).

Human-facing companion: [kos local-testing-environment](../kos/concepts/testing/local-testing-environment.md).
