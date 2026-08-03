---
id: sql-course-19-migrations
type: lesson
status: active
owner: handwritten
scope: sql, postgresql — database fundamentals taught from this ERP
anchors: config/expense/services/settlement_service.py, config/production/services/pool_service.py
verified: 2026-08-01
---

# 19 — Migrations: How My Tables Came to Exist

> Part of [SQL From Zero](00_COURSE_OVERVIEW.md). Prev: [18](18_Locks_Concurrency_MVCC.md) · Next: [20 — Backups & Restore](20_Backups_And_Restore.md).

# Learning Objectives
By the end of this chapter you can:
- explain how 115 tables exist without you writing CREATE TABLE
- read `django_migrations` and say what has been applied
- add a NOT NULL column to a large table without downtime
- say what migrations bring — and what they never will

# Purpose
To understand where my 115 tables actually came from — I never typed a single
`CREATE TABLE` — and how the same history can rebuild an empty database into my
exact schema in about a minute.

# The Problem
The schema must change: a new column for `good/alter/missing` quantities, a new
table for allocations. Now multiply that by: my laptop, a teammate's laptop, a
test database created fresh for every test run, and the production server holding
real wages. **The same change must reach all of them, in the same order, with
nobody typing SQL by hand and nobody forgetting a step.**

# Theory (from zero)

A **migration** is a recorded, ordered, replayable schema change.

```
   MODEL (Python)                MIGRATION (recorded step)         TABLE (SQL)
   ─────────────                 ─────────────────────────         ───────────
   class Adda(models.Model):     0001_initial.py                   CREATE TABLE
       code = CharField(…)   ──▶   CreateModel('Adda', …)     ──▶   production_adda
                                                                    ( code varchar…)
   makemigrations  ─────────────▶ writes the step file
   migrate         ─────────────────────────────────────────────▶  runs the SQL
```

**Two commands, two very different jobs:**

| Command | Does | Touches the DB? |
|---|---|---|
| `makemigrations` | compares models to existing migrations, **writes a new step file** | no |
| `migrate` | runs the pending step files **in order** | yes |
| `sqlmigrate app 0001` | prints the SQL a step *would* run | no |
| `showmigrations` | lists steps and which are applied | reads only |

**The ledger of what has run lives in the database itself** — a plain table called
`django_migrations`. That is how `migrate` knows what is left to do:

```
   django_migrations  (188 rows in my database)
   ┌────────────────┬──────────────────────────────────────────────┐
   │ app            │ name                                          │
   ├────────────────┼──────────────────────────────────────────────┤
   │ accounts       │ 0019_seed_my_assigned_work_sidebar            │
   │ production     │ 0052_workerstageallocation_allocation_mode    │
   │ expense        │ 0015_monthly_expense_engine                  │
   │ raw_materials  │ 0012_alter_clothroll_status                   │
   └────────────────┴──────────────────────────────────────────────┘
   Empty table ⇒ every step is "pending" ⇒ a fresh DB builds itself.
```

**Two kinds of step:**
- **Schema migrations** — structure: create table, add column, add constraint/index.
- **Data migrations** — rows: seeding reference data or backfilling a new column.
  (`0019_seed_my_assigned_work_sidebar` in my project is literally a data
  migration that seeded a sidebar rule.)

**Migrations are append-only history.** You do not edit an applied migration —
you add a new one. Same philosophy as the money ledger (ch 12): the record of what
happened stays honest, and corrections are additive.

> 💡 **Samjho aise:** Migration factory ke **naqshe ki diary** hai — *"din 1: Adda
> register banaya · din 40: usme lane ka khaana joda · din 52: allocation-mode ka
> khaana joda"*. Nayi khaali building (fresh DB) khadi karni ho? Diary **shuru se
> chala do** — wahi factory ban jaati hai. Isi liye purani entry kabhi nahi badalte:
> diary jhooth bolegi to nayi building alag banegi, aur kisi ko pata bhi nahi chalega.

# Real World Example (My ERP)
- **188 applied migrations** in `inventory_db` today.
- Per app: `production` 52 · `inventory` 21 · `accounts` 19 · `tracking` 18 ·
  `patterns_ai` 17 — the busiest app has the longest diary, exactly as you'd expect.
- This is precisely why `./scripts/db.sh new test_01` works: it creates an empty
  database, runs `migrate` (replaying all 188 steps → 115 tables), then seeds the
  platform master data.
- **The limitation this exposes** — and it is a real finding in my project:
  migrations bring *structure* plus whatever rows a data migration seeds, and
  **nothing else**. Which is why a fresh database has only 4 of 21 stages and
  **zero users**, documented in [FRESH_DB_REQUIREMENTS](../FRESH_DB_REQUIREMENTS.md) §1.
  Migrations are not a substitute for a seed.

# Visual Diagram
```
   ONE HISTORY, MANY DATABASES — the whole point
   ═══════════════════════════════════════════════════════════════════
        migrations/  (188 ordered steps, in git)
                │
      ┌─────────┼─────────────┬─────────────────┬───────────────────┐
      ▼         ▼             ▼                 ▼                   ▼
  my laptop  test DB      test_production   sql_practice        PRODUCTION
  inventory_db (created &  (db.sh new)       (db.sh branch)      (deploy:
   115 tables   destroyed                                        entrypoint
               per test run)                                     runs migrate)
   ═══════════════════════════════════════════════════════════════════
   Same steps, same order ⇒ same schema everywhere. That is reproducibility.

   AND on deploy, my entrypoint does exactly this, in this order:
      migrate  ──▶  seed_master_data  ──▶  collectstatic  ──▶  gunicorn
      (structure)    (platform rows)      (static files)     (serve)
```

# Practical — try it yourself
```bash
# 1. what has been applied? (reads only — safe)
env/bin/python config/manage.py showmigrations production --settings=config.settings.local | tail -8
#   [X] = applied, [ ] = pending

# 2. see the actual SQL a migration runs — the ORM→DDL bridge, revealed
env/bin/python config/manage.py sqlmigrate production 0001 --settings=config.settings.local | head -25
#   CREATE TABLE "production_stage" ("id" bigint NOT NULL PRIMARY KEY …

# 3. are my models and migrations in sync? (CI-grade check, writes nothing)
env/bin/python config/manage.py makemigrations --check --dry-run --settings=config.settings.local
#   exits non-zero if a model change has no migration — a great pre-commit gate
```
```sql
-- 4. the ledger, from SQL (REAL: 188)
SELECT count(*) FROM django_migrations;
SELECT app, count(*) FROM django_migrations GROUP BY app ORDER BY 2 DESC LIMIT 5;
SELECT app, name, applied FROM django_migrations ORDER BY id DESC LIMIT 4;
```
```bash
# 5. see a REAL data migration (rows, not structure)
sed -n '1,25p' config/accounts/migrations/0019_seed_my_assigned_work_sidebar.py
```

# Production Walkthrough
- `deploy/entrypoint.sh` runs, in order: **migrate → seed_master_data → collectstatic → gunicorn**. Schema before data before assets before serving; each step assumes the previous one finished.
- **A schema change and the code that needs it deploy together.** Old code against a new schema (or vice versa) is the classic mid-rollout 500.
- `migrate` is idempotent — running it twice is a no-op, which is why it is safe on every container boot.
- **What migrations do NOT bring:** business data. A fresh production DB gets 4 of 21 stages and zero users, which is why `FRESH_DB_REQUIREMENTS.md` exists.

# Debugging Guide
"The migration failed" / "the schema is wrong":
1. **`showmigrations`** — find the exact step that did not apply.
2. **`sqlmigrate <app> <n>`** — read the SQL *before* blaming it.
3. **Was it a lock timeout?** A big `ALTER` waits behind open transactions (ch 18); look for `idle in transaction`.
4. **Model/migration drift?** `makemigrations --check --dry-run` tells you if a model changed without a migration — put this in CI.
5. **Never edit an applied migration** to "fix" it; add a new one. Editing makes your DB and the file disagree forever.

# Performance Notes
- Most `ALTER TABLE` operations are fast metadata changes; the expensive ones **rewrite the table** or take a strong lock. Adding a nullable column with a constant default is instant in modern Postgres.
- Adding an index in a migration blocks writes unless you use `CONCURRENTLY` (which cannot run inside a transaction — use `AddIndexConcurrently` / `atomic = False`).
- Adding a CHECK or NOT NULL validates every existing row; split it with `NOT VALID` + `VALIDATE CONSTRAINT` (ch 13).
- Data migrations that loop over millions of rows should batch and commit, not run as one giant transaction.

# Security Considerations
- Migrations run with **schema-change privileges** — the most powerful thing your deploy does. Anyone who can add a migration can change your data model.
- Review data migrations like code: one can silently rewrite rows.
- Migrations are the wrong place for secrets or environment-specific values; those belong in `.env` (ch 22).
- Always have a fresh backup before a schema change (ch 20) — some migrations are one-way.

# Architecture Decisions
- **Migrations are append-only history**, exactly like the money ledger (ch 12): the record of what happened is never edited.
- **Additive-first as a rule** — new nullable column, backfill, then tighten. This project's U14 gate formalises it (additive new tables get approval quickly; destructive changes do not).
- **Seed platform data in a command, not a migration** — re-runnable, dry-runnable, and inspectable, whereas a migration runs once and hides.
- **Migrations deploy before the app starts**, so the app never sees a schema it was not built for.

# Best Practices
- One migration per logical change, with a name that says what it does.
- Read the generated file before committing it; it is code.
- `makemigrations --check` in CI to catch drift.
- Take a backup before any migration touching money tables.

# Beginner Mistakes
- Editing an **applied** migration. Your database and the file now disagree; the
  next fresh database builds something different. Add a new migration instead.
- Deleting migration files to "clean up". You destroy the ability to rebuild.
- Running `makemigrations` and not reading the generated file. It is code; review it.
- Forgetting that `migrate` on production **changes the live schema** — it belongs
  in a deploy step (mine is in `deploy/entrypoint.sh`), taken with a backup in hand.
- Adding a `NOT NULL` column without a default to a populated table → the migration
  fails or blocks; do it additively (nullable → backfill → tighten).
- Assuming migrations restore *data*. They don't. That's ch 20.

# Interview Questions
- **Junior:** *What is a migration?* — a versioned, ordered schema change that can be replayed on any database.
- **Junior:** *`makemigrations` vs `migrate`?* — write the step file vs apply pending steps.
- **Mid:** *How does the framework know what has already run?* — a table in the database itself (`django_migrations`); it diffs that against the files on disk.
- **Mid:** *Schema vs data migration?* — structure vs rows; data migrations seed or backfill and should be idempotent and reversible where possible.
- **Senior:** *How do you add a NOT NULL column to a large busy table with zero downtime?* — add it nullable (instant in modern Postgres, especially with a constant default), backfill in batches, then add the NOT NULL/CHECK as `NOT VALID` and `VALIDATE` separately to avoid a long exclusive lock (ch 13).
- **Senior:** *How do you roll back a bad migration?* — apply the reverse migration if it is genuinely reversible; if it dropped data, only a restore helps — which is why a backup precedes every deploy.
- **Staff:** *How do you keep migrations safe in CI/CD with multiple developers?* — `makemigrations --check` in CI to catch model/migration drift, one migration per logical change, review the generated SQL (`sqlmigrate`), never edit applied files, and deploy schema-compatible-first so old and new code can both run during a rollout.

### Why interviewers ask these — and the answer that separates levels

| Testing for | Weak answer | What lands |
|---|---|---|
| Do you know where "already applied" is recorded? | "The framework tracks it in a file." | In **the database itself** — the `django_migrations` table — diffed against the files on disk. That is why a restored database knows exactly where it is, and why editing an applied migration is a lie. |
| Can you add NOT NULL to a big busy table safely? | "Add the column with a default." | Add it **nullable** (instant in modern Postgres) → **backfill in batches** → add the constraint **`NOT VALID`** → **`VALIDATE`** separately (ch 13). One statement that rewrites the table is an outage. |
| Can a bad migration be rolled back? | "Yes, just migrate backwards." | Only if it is **genuinely reversible**. **If it dropped data, only a restore helps** — which is exactly why a backup precedes every deploy. Say that limit out loud; it is the difference between a plan and a hope. |
| Do you know schema from data migrations? | "They are both just migrations." | Structure vs **rows**. Data migrations seed or backfill and must be **idempotent** and reversible where possible — and one touching earnings deserves the same hostile review as money code. |

**The killer follow-up:** *"Two developers, one CI pipeline — how do migrations stay safe?"* — `makemigrations --check` in CI to catch model/migration drift · one migration per logical change · **review the generated SQL with `sqlmigrate`** · never edit an applied file · and **deploy schema-compatible-first** so old and new code both run during the rollout. That last one is the answer most candidates miss.

# Revision Notes
- Migration = recorded, ordered, replayable schema change.
- `makemigrations` writes · `migrate` applies · `sqlmigrate` shows the SQL.
- Applied history lives in the **`django_migrations`** table.
- **Never edit an applied migration** — add a new one.
- Migrations bring structure, **never your business data**.

# Cheat Sheet
- migration = recorded, ordered, replayable schema change
- `makemigrations` writes · `migrate` applies · `sqlmigrate` shows the SQL · `showmigrations` lists
- applied history lives in the **`django_migrations`** table (188 rows here)
- **never edit an applied migration** — add a new one
- migrations bring structure (+seeded rows), **never your business data**
- deploy order: `migrate → seed_master_data → collectstatic → gunicorn`
- CI gate: `makemigrations --check --dry-run`

# My ERP Section
| Fact | Value / location |
|---|---|
| Applied migrations | 188 (`django_migrations`) |
| Busiest app | `production` — 52 steps |
| A real data migration | `accounts/0019_seed_my_assigned_work_sidebar.py` |
| Fresh-DB rebuild path | `./scripts/db.sh new <name>` → migrate → seed |
| Deploy application | `deploy/entrypoint.sh` (migrate before collectstatic) |
| What migrations DON'T give | [FRESH_DB_REQUIREMENTS](../FRESH_DB_REQUIREMENTS.md) §1 — 4/21 stages, 0 users |
| Deep dive | [kos: migrations](../../kos/concepts/django/migrations.md) |

# Practice Tasks
1. **Read the code:** open `config/accounts/migrations/0019_seed_my_assigned_work_sidebar.py`. Is it a schema or a data migration? What makes it safe to re-run — or is it not?
2. **Debug:** run `makemigrations --check --dry-run`. If it reports changes, explain what drifted; if not, explain what that check protects you from.
3. **Design:** write the migration plan (as steps, not code) for adding a NOT NULL `site_id` to `production_adda` on a live system with 5 million rows.
4. **Architecture:** argue why platform seed data belongs in a management command rather than a data migration — then name one case where a data migration *is* correct.

# Homework
1. Run `showmigrations production | tail -8`. Which was the most recent step, and what does its name tell you about what changed?
2. Run `sqlmigrate production 0001 | head -25`. Find one `CREATE TABLE` and match a column to the model field that produced it.
3. Run `makemigrations --check --dry-run`. Does my repo currently have model changes without migrations? Explain why that check belongs in CI.

# Further Reading & Live Resources
- [Django migrations](https://docs.djangoproject.com/en/5.0/topics/migrations/) — official, thorough
- [Django: migration operations](https://docs.djangoproject.com/en/5.0/ref/migration-operations/)
- [Postgres ALTER TABLE](https://www.postgresql.org/docs/current/sql-altertable.html) — what your migrations really run
- [Strong Migrations (patterns for zero-downtime changes)](https://github.com/ankane/strong_migrations#checks) — Rails-flavoured but the rules are universal
