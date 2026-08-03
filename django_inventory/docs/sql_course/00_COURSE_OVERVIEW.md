---
id: sql-course-00-course-overview
type: lesson
status: active
owner: handwritten
scope: sql, postgresql — database fundamentals taught from this ERP
anchors: config/expense/services/settlement_service.py, config/production/services/pool_service.py
verified: 2026-08-01
---

# 00 — SQL & PostgreSQL From Zero: Course Overview

> The database twin of [Deployment From Zero](../deployment_course/00_COURSE_OVERVIEW.md).
> Same rules: taught from MY project, zero prior knowledge assumed, every chapter self-contained.

## How to use this folder

- Read in order — chapters build on each other (basic → advanced).
- Every example is a REAL query against MY factory database, shown with the REAL
  output it produced on 2026-07-31 (28 addas · ledger 201 rows/₹18,254.25 · 115
  tables). Numbers drift as the dev DB grows; concepts don't. Re-run anything.
- **Practice safely:** `./scripts/db.sh branch sql_practice --use` — a full copy
  of my data to experiment on. `./scripts/db.sh use inventory_db` to come home.
- Open the SQL prompt any time:
  `env/bin/python config/manage.py dbshell --settings=config.settings.local`

## The standard chapter format (every file has these headings)

1. **# Purpose** — why this topic exists.
2. **# The Problem** — what problem it solves.
3. **# Theory (from zero)** — first principles, no prior knowledge assumed.
4. **# Real World Example (My ERP)** — the exact table/query/constraint in *this* project.
5. **# Visual Diagram** — ASCII picture.
6. **# Practical — try it yourself** — real commands, every command explained.
7. **# Beginner Mistakes** — misunderstandings and data-killers.
8. **# Interview Questions** — Junior / Mid / Senior / Staff, with answers.
9. **# Cheat Sheet** — the chapter in 10 lines.
10. **# My ERP Section** — where this lives in my project (files/tables/services).
11. **# Homework** — small hands-on exercises on the practice branch.
12. **# Further Reading & Live Resources** — official docs + free interactive sites.

## My database — the one picture to remember

```
 Django app (client)      psql / dbshell (client — YOU)
        │                        │
        └────────┬───────────────┘
                 │  SQL text in → rows out
        ┌────────▼─────────────────────────────┐
        │  PostgreSQL 14 (the server program)  │
        │  ┌────────────────────────────────┐  │
        │  │ inventory_db     (115 tables)  │  │   ← my real factory
        │  │ test_production  (fresh)       │  │   ← rehearsal
        │  │ sql_practice     (branch)      │  │   ← this course's playground
        │  └────────────────────────────────┘  │
        │  files: /var/lib/postgresql/14/main  │   ← never touch by hand
        └──────────────────────────────────────┘
   NOT in any database: uploaded photos/videos → config/media/  (ch 21)
```

| Piece | In my project | Chapter |
|---|---|---|
| The tables | `production_adda`, `expense_workerledgerentry`, … (115) | 02 |
| Money type | `numeric(12,2)` on every ₹ column | 03 |
| Honest NULL | `cost_per_kg` on unpriced rolls | 04 |
| Foreign keys | `adda.product_id → production_product.id` | 07 |
| The proven total | `sum(amount)` = ₹18,254.25 | 08 |
| CHECK constraints | `wsc_gamd_nonneg_sum_positive` (+~26 more) | 13 |
| Indexes | `production_adda_code_key` … | 14 |
| Atomic money event | settlement finalize (`@transaction.atomic`) | 17 |
| Named locks | advisory keys **5374** (settlement) / **5375** (allocation) | 18 |
| Schema history | `django_migrations` table | 19 |
| Backups | `db.sh save` (plain) · `deploy/backup.sh` (restic, `-Fc`) | 20 |
| DB tooling | `scripts/db.sh` — fresh/branch/check/save/restore | 21 |
| Secrets | `.env` (`DB_PASSWORD`), never committed | 22 |
| Schema-less valve | `jsonb` columns in patterns_ai | 23 |
| The never-fork rule | ADR-0010: one ledger, one database | 24 |

## Curriculum (read in order)

**Part A — Foundations**
- [01 — What Is a Database (and SQL, and PostgreSQL)](01_What_Is_A_Database.md)
- [02 — Tables, Rows, Columns, Keys](02_Tables_Rows_Columns_Keys.md)
- [03 — Data Types, and Why Money Is Never a Float](03_Data_Types_And_Money.md)
- [04 — NULL: "Unknown" Is Not "Zero"](04_NULL.md)

**Part B — Reading data**
- [05 — SELECT Basics](05_SELECT_Basics.md)
- [06 — Filtering & Expressions](06_Filtering_And_Expressions.md)
- [07 — JOINs: How Tables Point at Each Other](07_JOINs.md)
- [08 — GROUP BY & Aggregates: My Ledger, Summed](08_GROUP_BY_And_Aggregates.md)
- [09 — Subqueries & CTEs](09_Subqueries_And_CTEs.md)
- [10 — Window Functions](10_Window_Functions.md)

**Part C — Writing data**
- [11 — INSERT, UPDATE, DELETE](11_INSERT_UPDATE_DELETE.md)
- [12 — The Append-Only Money Philosophy](12_Append_Only_Money.md)
- [13 — Constraints: Rules Data Cannot Break](13_Constraints.md)

**Part D — The engine**
- [14 — Indexes](14_Indexes.md)
- [15 — EXPLAIN & the Query Planner](15_EXPLAIN_And_The_Planner.md)
- [16 — From ORM to SQL, and the N+1 Problem](16_ORM_To_SQL_And_N_Plus_1.md)
- [17 — Transactions & ACID](17_Transactions_And_ACID.md)
- [18 — Locks, Concurrency, MVCC](18_Locks_Concurrency_MVCC.md)

**Part E — Operations (being your own DBA)**
- [19 — Migrations: How My Tables Came to Exist](19_Migrations.md)
- [20 — Backups & Restore](20_Backups_And_Restore.md)
- [21 — Many Databases, Branching, and What's NOT in the DB](21_Databases_Branching_And_Whats_Not_In_The_DB.md)
- [22 — Security & SQL Injection](22_Security_And_SQL_Injection.md)

**Part F — The edges**
- [23 — JSONB: Escaping the Fixed Schema (Carefully)](23_JSONB.md)
- [24 — Scaling & Limitations: What Postgres Is NOT Good At](24_Scaling_And_Limitations.md)
- [25 — Interview Master Sheet](25_Interview_Master_Sheet.md)

## Prerequisites

None for SQL — this course starts at "what is a database". Assumed from daily
life with the project: running `manage.py` commands, editing `.env`, and the
`db.sh` tool ([kos guide](../../kos/concepts/testing/local-testing-environment.md)).

## Status of this course

Written 2026-07-31 from the live codebase; every output real. Living document —
when a schema change breaks an example, fix the example and log it in
[FRESH_DB_REQUIREMENTS.md](../FRESH_DB_REQUIREMENTS.md) §6.
