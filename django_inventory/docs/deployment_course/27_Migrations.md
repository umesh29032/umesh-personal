# 27 — Database Migrations in Production

> Part of [Deployment Course](00_COURSE_OVERVIEW.md). Prev: [26 — collectstatic & WhiteNoise](26_collectstatic.md). Next: [28 — Backups](28_Backups.md). *(Completes Term 5.)*

# Purpose
To understand how database **schema changes** ship safely to a live production database — `makemigrations` vs `migrate`, when they run in a deploy, and the rules that stop a migration from taking your factory offline or corrupting data. This is where "deploy new code" meets "don't lose the money data."

# The Problem
Your models change over time (new field, new table, renamed column). The production database must change to match — but it's **live**, it holds the real factory data, and a careless schema change can **lock a table for minutes** (downtime), **drop a column with data** (loss), or leave code and schema **out of sync** (500s). You need a disciplined, repeatable, reversible way to evolve the schema alongside the code.

# Theory (from zero)

### Migrations = versioned schema changes
A **migration** is a Python file describing a database change (add field, create table, run SQL). Django tracks which have been applied in a `django_migrations` table. Migrations are **ordered** and **dependency-linked**, so any database can be brought from any state to the latest by applying the missing ones in order. They live in each app's `migrations/` dir and are **committed to git** (they're part of the code).

### `makemigrations` vs `migrate`
- **`makemigrations`** (dev only): compares your models to the latest migration and **generates** a new migration file. You run this on your laptop and commit the result. **Never** in production.
- **`migrate`** (every environment): **applies** unapplied migration files to the database. This runs in production — but only files that already exist in git. Prod never *generates* migrations, only *applies* them.

### When migrations run in a deploy
In my stack the **entrypoint** runs `python manage.py migrate --noinput` on container boot, **after** the DB is healthy and **before** `collectstatic` + Gunicorn ([Ch 09](09_Processes_and_Services.md)). So a new image brings the schema current before it serves a single request. `--noinput` = no interactive prompts (required in automation).

### The safety rules (why deploys don't break the DB)
1. **Back up first.** A `pg_dump` before migrating means any bad migration is recoverable ([Ch 28](28_Backups.md)). My deploy runbook takes a fresh dump before `up`.
2. **Additive-first / backward-compatible.** Deploy schema changes that the *old* code still tolerates: add nullable columns/tables first, backfill, *then* (a later deploy) enforce/drop. This is **expand → migrate data → contract**. It lets old and new code overlap safely (and enables zero-downtime).
3. **Never drop columns with data in the same step as the code change.** Rename = add new + copy + switch reads + drop old, across deploys — not a single destructive rename.
4. **Watch table locks.** On big tables, adding an indexed/`NOT NULL`-with-default column or building an index can lock writes. On Postgres, prefer nullable-add + backfill in batches + `CREATE INDEX CONCURRENTLY`. (At my current data size this is small, but the discipline scales.)
5. **Data migrations are reversible where possible.** A `RunPython` should provide a reverse function so a rollback can undo it.

### Migration vs data (schema ≠ money)
`migrate` changes **structure**, not business truth. Destructive data changes (dropping a column that holds real values, retiring a field) are treated with extra care in my project — gated behind soak periods, never bundled casually into a routine deploy.

# Real World Example (My ERP)
- **Applied at boot:** entrypoint runs `migrate --noinput` after `pg_isready`/redis-ping, before collectstatic + gunicorn ([Ch 09](09_Processes_and_Services.md)).
- **Migration count:** the `production` app alone is at **0052** (`0052_workerstageallocation_allocation_mode`), plus `accounts` **0019** (`0019_seed_my_assigned_work_sidebar`), etc. — dozens of ordered files, all in git, all replayable on a fresh DB (the test battery builds a fresh DB from them 1878 times).
- **Money-data caution:** the S6 "retire `reported_quantity`" change is **irreversible + soak-gated** — deliberately *not* shipped in a routine deploy; the enforcement flags (`ENFORCE_ALLOCATION_BOUND`, `ENFORCE_SETTLEMENT_RECONCILIATION`) ship **OFF** and flip only after a soak. That's rule 2/5 in practice.
- **Data migrations:** e.g. `accounts 0019` seeds a sidebar rule; production data migrations carry reverse functions where the data allows (the V2-1d M2M drop had a "data-aware reverse").
- **Deploy gate:** `verify_production` + the fresh-DB battery ensure code and schema agree before a release is cut ([Ch 30](30_Monitoring.md)).
- **Backup pairing:** the deploy runbook takes a `pg_dump` immediately before `docker compose up` so a bad migrate is recoverable ([Ch 28](28_Backups.md)/[Ch 29](29_Restore.md)).

# Visual Diagram
```
  DEV (laptop)                              PROD (VPS, live data)
   edit models.py                            (never makemigrations here)
   makemigrations  → 0052_*.py  ──commit──►  git  ──deploy──► entrypoint:
   (generate)                                                   pg_isready ✓
   git commit migration + code                                  migrate --noinput  ← APPLY only
                                                                 collectstatic
                                                                 exec gunicorn
  SAFE ORDER (expand→contract), never destructive-in-one-step:
    deploy1: ADD nullable col / new table   (old code still works)
    deploy2: backfill data                  (RunPython, reversible)
    deploy3: enforce NOT NULL / drop old    (after soak)     ← S6 lives here, gated
  ALWAYS: pg_dump BEFORE migrate (Ch28) — bad migration ⇒ restore (Ch29)
```

# Practical — how to inspect it
```bash
docker compose exec app python manage.py showmigrations           # [X]=applied, [ ]=pending, per app
docker compose exec app python manage.py showmigrations production | tail   # ...0052 applied?
docker compose exec app python manage.py migrate --plan           # what WOULD run, in order (dry preview)
```
```bash
# In a deploy (already automated by entrypoint) — manual form:
docker compose exec app python manage.py migrate --noinput
```
```bash
# Guardrails
docker compose exec app python manage.py makemigrations --check --dry-run   # CI: fails if models drifted from migrations
docker compose exec app python manage.py sqlmigrate production 0052         # show the exact SQL a migration emits
```

# Beginner Mistakes
- **Running `makemigrations` in production** → generates files on the server that aren't in git → drift + chaos. Generate on dev, commit, only `migrate` in prod.
- **No backup before migrating** → a bad migration is unrecoverable. Always `pg_dump` first ([Ch 28](28_Backups.md)).
- **Destructive change in one step** (drop/rename column with data) → data loss + old-code 500s. Use expand→contract across deploys.
- **Forgetting `--noinput`** in automation → the entrypoint hangs on a prompt.
- **Not committing migration files** → other envs/CI can't reach the schema; fresh-DB build fails.
- **Editing an already-applied migration** → the DB and the file disagree; make a *new* migration instead.
- **Assuming migrations are instant** → large-table locks cause downtime; check with `sqlmigrate`/`--plan` and prefer concurrent/batched ops at scale.

# Interview Questions
**Junior — "`makemigrations` vs `migrate`?"** `makemigrations` generates migration files from model changes (dev only); `migrate` applies existing migration files to the database (runs everywhere, including prod).

**Mid — "How and when do migrations run in your deploy?"** The container entrypoint runs `migrate --noinput` after the DB is healthy and before collectstatic + Gunicorn, so the schema is current before the app serves requests. Migrations are generated on dev, committed to git, and only applied in prod.

**Senior — "How do you change a production schema with zero downtime and no data loss?"** Expand→contract: first deploy an additive, backward-compatible change (nullable column / new table) the old code tolerates; backfill data with a reversible data migration; then, in a later deploy after soak, enforce/drop. Take a `pg_dump` before each migrate, avoid long table locks (nullable-add, batched backfill, `CREATE INDEX CONCURRENTLY`), and keep reverse functions so you can roll back.

**Staff — "Design a migration policy for a live financial system like this ERP."** Migrations are code: generated on dev, reviewed, committed, replayable on a fresh DB (enforced by a full-suite fresh-DB build). Deploys apply them automatically at boot, always preceded by a backup and gated by `makemigrations --check` in CI (no drift) + a `verify_production` gate. Schema evolution follows expand→contract so old/new code overlap safely; **destructive or money-semantic changes** (dropping a field that held real values, flipping enforcement) are decoupled from routine deploys — shipped OFF/behind flags and only enabled after an observation soak, with a rehearsed restore path. Principle: structure changes are reversible and boring; money-data changes are deliberate, isolated, and soak-gated.

# Cheat Sheet
- **`makemigrations`** = generate (DEV only, commit the file). **`migrate --noinput`** = apply (prod, at boot).
- Entrypoint order: DB healthy → **migrate** → collectstatic → gunicorn.
- **Always `pg_dump` before migrate** ([Ch 28](28_Backups.md)); bad migrate ⇒ restore ([Ch 29](29_Restore.md)).
- **Expand → migrate data → contract**; never destructive-in-one-step; watch table locks at scale.
- Migrations are in **git**, ordered, replayable (my fresh-DB battery proves it).
- Money-semantic/irreversible changes (S6, enforcement flags) = **soak-gated, OFF by default**, not in routine deploys.
- Inspect: `showmigrations`, `migrate --plan`, `sqlmigrate`, `makemigrations --check`.

# My ERP Section
| Concept | In my ERP |
|---|---|
| Applied by | entrypoint `migrate --noinput` (after DB healthy) |
| Latest | production `0052`, accounts `0019`, … (all in git) |
| Replayable | fresh-DB battery builds schema 1878× |
| Data migrations | reversible where data allows (e.g. V2-1d) |
| Irreversible/gated | S6 `reported_quantity` retirement (soak-gated) |
| Enforcement flags | ship OFF, flip after soak |
| Backup pairing | `pg_dump` before every deploy migrate |
| CI guard | `makemigrations --check` (no drift) + verify_production |

# Homework
1. `showmigrations production | tail` — is `0052` applied? What table records this?
2. `migrate --plan` on a clean stack — read the order. Why does order/dependency matter?
3. `sqlmigrate production 0052` — read the actual SQL. Would it lock a large table? How would you avoid that at scale?
4. Describe expand→contract for renaming a column that holds real data, across three deploys.
5. Why are the S6 change and the enforcement flags deliberately *not* part of a routine deploy? Which safety rules does that follow?

---

## Further Reading & Live Resources
- Django docs — *Migrations*: https://docs.djangoproject.com/en/5.0/topics/migrations/
- Django docs — *`migrate` / `makemigrations` / `sqlmigrate`*: https://docs.djangoproject.com/en/5.0/ref/django-admin/#migrate
- Django docs — *Writing data migrations (RunPython, reverse)*: https://docs.djangoproject.com/en/5.0/topics/migrations/#data-migrations
- Postgres — *`CREATE INDEX CONCURRENTLY`* (lock-free indexing): https://www.postgresql.org/docs/current/sql-createindex.html
- Braintree — *Safe Operations for High-Volume PostgreSQL* (expand/contract in practice): https://www.braintreepayments.com/blog/safe-operations-for-high-volume-postgresql/
- `django-pg-zero-downtime-migrations` (tooling for lock-safe migrations): https://github.com/tbicr/django-pg-zero-downtime-migrations
