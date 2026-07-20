# 21 — PostgreSQL

> Part of [Deployment Course](00_COURSE_OVERVIEW.md). Prev: [20 — Docker Volumes](20_Docker_Volumes.md). Next: [22 — Redis](22_Redis.md). *(Term 5 — Data.)*

# Purpose
To understand the **database of record** — PostgreSQL — in production: how it persists ([Ch 20](20_Docker_Volumes.md)), how Django connects to it (`DATABASE_URL`), how connections + health work, and why it's the piece I protect most (it holds every allocation, contribution, and settlement — the factory's money and truth).

# The Problem
All the ERP's durable truth lives in Postgres. In production it must: survive restarts + rebuilds, accept concurrent connections from 3 Gunicorn workers, enforce integrity (no negative earnings, no orphan records), be reachable by name over the private network, and be backed up. If Postgres is misconfigured, I get connection storms, data corruption, or — worst — data loss.

# Theory (from zero)

### What PostgreSQL is
A **relational database (RDBMS)**: data in tables with columns/types, related by keys, queried with SQL, with **ACID** guarantees — **A**tomicity (all-or-nothing transactions), **C**onsistency (constraints always hold), **I**solation (concurrent transactions don't corrupt each other), **D**urability (committed data survives crashes). This is why money code uses a real RDBMS, not a flat file or SQLite: **concurrency + integrity + transactions**.

### Why Postgres (not SQLite) in production
SQLite is a single-file DB, great for dev, but it locks the whole file on writes → terrible under concurrent writers (your 3 workers + settlement). Postgres handles many concurrent connections, real transactions, and rich constraints. Your app relies on Postgres features: `CheckConstraint`, partial unique indexes, advisory locks (settlement 5374 / pool 5375). SQLite couldn't back this ERP safely.

### Persistence — the volume
The Postgres container stores its data at `/var/lib/postgresql/data`, mounted from the **`pgdata` named volume** ([Ch 20](20_Docker_Volumes.md)). That's why the DB survives `docker compose up --build`. Losing this volume = losing the DB → back it up ([Ch 28](28_Backups.md)).

### How Django connects — `DATABASE_URL`
Rather than scattered settings, one env var: `DATABASE_URL=postgres://<user>:<pass>@db:5432/<dbname>`, parsed by **`dj-database-url`** into Django's `DATABASES` config ([Ch 19](19_Docker_Networking.md) for why the host is `db`). In production my `base.py` parses it with `conn_max_age=600` (reuse a DB connection for up to 600s instead of opening one per request — **persistent connections**, less overhead) and `ssl_require=True` (encrypt the DB link). In dev, `conn_max_age=0` (the H-3 fix — don't leak connections with the autoreloader).

### Connections + workers
Each Gunicorn worker opens its own DB connection(s). 3 workers × persistent connections is well within Postgres's default `max_connections` (100). At bigger scale you'd add a pooler (PgBouncer) — not needed here ([Ch 41](41_Scaling.md)).

### Health — `pg_isready`
The compose `db` healthcheck runs `pg_isready -U <user> -d <db>` every 5s; `app` waits for it (`service_healthy`) before migrating ([Ch 18](18_Docker_Compose.md)). So the app never hits a not-yet-ready DB.

### Integrity lives in the DB, not just the app
Your models enforce truth at the **database** level: 30+ `CheckConstraint`s (non-negative money/quantities, `good+alter+missing+damaged` sums), unique constraints (adda code, settlement refs), and **`PROTECT` foreign keys** so a parent delete can't silently orphan/wipe financial rows (RC1 DB audit). This means even a buggy query or a rogue script can't violate the invariants — the DB refuses. That's a deployment-relevant safety net: your data can't go inconsistent behind your back.

### Migrations = schema changes ([Ch 27](27_Migrations.md))
The schema evolves via Django migrations, applied by `manage.py migrate` in the entrypoint before Gunicorn starts. Production has 52 production-app migrations; a fresh deploy runs them against an empty DB fast.

# Real World Example (My ERP)
- **Service:** `db` = `postgres:16.6-alpine` (pinned), `restart: unless-stopped`, data in `pgdata` volume, `POSTGRES_DB/USER/PASSWORD` from `.env`, healthcheck `pg_isready` ([Ch 18](18_Docker_Compose.md)).
- **Connect:** `.env` `DATABASE_URL=postgres://<user>:<pass>@db:5432/<dbname>` → `dj-database-url` → Django. Host `db` = the service name over the private net ([Ch 19](19_Docker_Networking.md)); `ssl_require` + `conn_max_age=600` in prod.
- **Never public:** `db` has no `ports:` — unreachable from the internet; admin access via SSH tunnel ([Ch 07](07_SSH.md)).
- **Integrity:** the settlement (`AddaSettlement`/items), worker contributions, and ledger are guarded by CheckConstraints + PROTECT FKs (RC1), and money writes are `@transaction.atomic` under advisory locks — so concurrent settlement/allocation can't corrupt or double-count.
- **Backed up:** the `backup` service `pg_dump -Fc -h db …` nightly → restic off-site ([Ch 28](28_Backups.md)).

# Visual Diagram
```
  3 Gunicorn workers ── DATABASE_URL=postgres://…@db:5432/… ──► db (postgres:16.6)
        (dj-database-url; conn_max_age=600, ssl_require in prod)      │
                                                                data: pgdata volume ★
  compose healthcheck: pg_isready every 5s → app waits service_healthy → migrate → gunicorn
  integrity IN the DB: 30+ CheckConstraints · unique(adda code, settl refs) · PROTECT FKs
  money writes: @transaction.atomic + advisory locks (5374 settlement / 5375 pool)
  private (no ports) → admin via SSH tunnel   |   nightly pg_dump → restic off-site (Ch28)
```

# Practical — how to inspect it
```bash
# Health + connection
docker compose exec db pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"   # "accepting connections"
docker compose exec app python -c "import os;print(os.environ['DATABASE_URL'])"  # uses @db:5432
docker compose exec app python manage.py dbshell    # open psql as the app's DB user
```
```bash
# Inside psql (docker compose exec db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB")
\dt                      # list tables
\d+ production_adda      # describe a table (columns, indexes, constraints)
SELECT count(*) FROM production_workerstagecontribution;   # sanity counts
SELECT * FROM pg_stat_activity;   # live connections (how many? from which workers?)
\q
```
```bash
# Size + health from the host
du -sh /var/lib/docker/volumes/*_pgdata/_data     # DB size on disk
docker compose exec db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT pg_size_pretty(pg_database_size('$POSTGRES_DB'));"
```
```bash
# Migrations
docker compose exec app python manage.py showmigrations   # applied vs pending (Ch27)
docker compose exec app python manage.py migrate --plan   # what WOULD run
```

# Beginner Mistakes
- **Publishing 5432 to the internet** → the DB is now attackable. Keep it private; tunnel for admin ([Ch 05](05_IP_Address_and_Ports.md)/[Ch 07](07_SSH.md)).
- **No backups** (relying only on the volume) → disk failure/`down -v` = total loss ([Ch 20](20_Docker_Volumes.md)/[Ch 28](28_Backups.md)).
- **Using SQLite "to keep it simple" in production** → write-locking + no real concurrency/constraints → corruption/timeouts under load.
- **`conn_max_age` too high with many workers** → idle connections pile up toward `max_connections`. 600s with 3 workers is fine; watch `pg_stat_activity` at scale.
- **Wrong DB host** (`localhost` vs `db`) → connection refused inside the container ([Ch 19](19_Docker_Networking.md)).
- **Running heavy/locking data migrations at deploy on a big table** → downtime; plan those separately ([Ch 27](27_Migrations.md)).
- **Not pinning the Postgres version** → a `:latest` bump can change on-disk format and refuse to start on old data. Pin (`16.6-alpine`).

# Interview Questions
**Junior — "Why Postgres instead of SQLite in production?"** Postgres handles many concurrent connections/writers, real transactions, and rich constraints; SQLite locks the whole file on writes and doesn't scale to concurrent users — unsafe for a multi-worker money app.

**Mid — "How does Django connect to Postgres in this deployment, and where does the config come from?"** Via `DATABASE_URL` (`postgres://user:pass@db:5432/name`) in `.env`, parsed by `dj-database-url` into `DATABASES`, with `conn_max_age` for persistent connections and `ssl_require` in prod. Host `db` is the Docker service name resolved on the private network.

**Senior — "How is data integrity guaranteed even if application code has a bug?"** Integrity is enforced at the database level: CheckConstraints (non-negative money/quantities, sum rules), unique constraints, and PROTECT foreign keys, plus money writes wrapped in atomic transactions under advisory locks. A bad query or script can't violate these — Postgres rejects the write — so invariants hold regardless of app-layer bugs.

**Staff — "Design the production Postgres story: durability, concurrency, and safe schema change."** Persist to a named volume for in-box durability; nightly `pg_dump` + off-site restic with retention + `restic check` for beyond-box durability and a rehearsed restore ([Ch 29](29_Restore.md)/[Ch 40](40_Disaster_Recovery.md)); pin the major version; use `conn_max_age` sized to worker count (add PgBouncer only when connections approach `max_connections`); apply migrations in the entrypoint for additive changes, but stage heavy/locking migrations (large backfills, non-concurrent index builds) as separate maintenance steps to avoid deploy-time locks; enforce invariants with DB constraints so correctness doesn't depend on app code. Monitor DB size + slow queries.

# Cheat Sheet
- **Postgres = ACID RDBMS = the data of record.** Chosen over SQLite for concurrency + integrity + transactions.
- **Persists via `pgdata` volume** ([Ch 20](20_Docker_Volumes.md)); **connect via `DATABASE_URL=…@db:5432`** (dj-database-url, `conn_max_age`, `ssl_require`).
- **Health:** `pg_isready`; app waits `service_healthy` then migrates.
- **Integrity in the DB:** CheckConstraints + unique + PROTECT FKs + atomic+advisory-lock money writes.
- **Never public** (tunnel for admin). **Always backed up** off-site ([Ch 28](28_Backups.md)). **Pin the version.**
- Inspect: `pg_isready`, `manage.py dbshell`, `psql \dt/\d+`, `pg_stat_activity`, `pg_database_size`.

# My ERP Section
| Concept | In my ERP |
|---|---|
| Image | `postgres:16.6-alpine` (pinned) |
| Data | `pgdata` volume → `/var/lib/postgresql/data` |
| Connect | `.env` `DATABASE_URL=…@db:5432` (dj-database-url) |
| Prod tuning | `conn_max_age=600`, `ssl_require=True` |
| Health | `pg_isready` (compose) + app wait-loop |
| Integrity | 30+ CheckConstraints, unique, PROTECT FKs, atomic+advisory locks |
| Public? | No `ports:` → private; SSH tunnel for admin |
| Backup | `pg_dump -Fc -h db` nightly → restic ([Ch 28](28_Backups.md)) |

# Homework
1. `docker compose exec db pg_isready …` — confirm "accepting connections". What compose directive gates the app on this?
2. `manage.py dbshell` → `\dt` → pick a table → `\d+ <table>` — find a CheckConstraint or a foreign key `ON DELETE`. Why does DB-level enforcement matter beyond app validation?
3. `SELECT pg_size_pretty(pg_database_size(current_database()));` — how big is the DB? Estimate the backup size.
4. In `.env`, read the `DATABASE_URL` host — why `db` not `localhost`? ([Ch 19](19_Docker_Networking.md))
5. Explain why publishing 5432 would be dangerous, and how you'd instead inspect prod Postgres from your laptop.

---

## Further Reading & Live Resources
- PostgreSQL — *official docs*: https://www.postgresql.org/docs/
- Django docs — *Databases* (PostgreSQL settings, persistent connections): https://docs.djangoproject.com/en/5.0/ref/databases/
- dj-database-url (parse `DATABASE_URL`): https://github.com/jazzband/dj-database-url
- Postgres official Docker image (env vars, data dir): https://hub.docker.com/_/postgres
- *Use the Index, Luke!* (free, how indexes really work — for [Ch 41](41_Scaling.md)): https://use-the-index-luke.com/
- PostgreSQL — *transactions & MVCC / locking*: https://www.postgresql.org/docs/current/mvcc.html
