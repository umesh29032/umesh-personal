---
id: sql-course-01-what-is-a-database
type: lesson
status: active
owner: handwritten
scope: sql, postgresql — database fundamentals taught from this ERP
anchors: config/expense/services/settlement_service.py, config/production/services/pool_service.py
verified: 2026-08-01
---

# 01 — What Is a Database (and SQL, and PostgreSQL)

> Part of [SQL From Zero](00_COURSE_OVERVIEW.md). Next: [02 — Tables, Rows, Columns, Keys](02_Tables_Rows_Columns_Keys.md).

# Learning Objectives
By the end of this chapter you can:
- say the difference between **database**, **SQL** and **PostgreSQL** without hedging
- explain client–server: why Django and `dbshell` see the same data
- open a SQL prompt on your own factory and list its 115 tables
- say where the bytes live — and why you must never touch them by hand

# Purpose
To un-confuse three words that get used interchangeably — **database**, **SQL**,
**PostgreSQL** — and to see that my ERP's data does not live in my project folder
at all, but inside a separate always-running program that Django merely *talks to*.

# The Problem
My factory's truth (28 Addas, 106 users, a ₹18,254.25 ledger) must survive
restarts, survive crashes mid-write, let several people write at the same time
without corrupting each other, and refuse impossible facts (a negative wage, two
Addas with one code). Plain files and Excel can do none of that reliably. A
database program's entire job is to keep those promises.

# Theory (from zero)

| Word | What it actually is |
|---|---|
| **Database** | An organised, durable store of data that keeps correctness promises |
| **SQL** | The *language* for asking a database questions ("Structured Query Language") |
| **PostgreSQL** | One specific database *program* that speaks SQL (MySQL, SQLite, Oracle are others) |

The confusion, cured by one picture:

```
   ┌──────────────────────────────────────────────────────────────────┐
   │  PostgreSQL  ── the PROGRAM  (like "Microsoft Excel")            │
   │  ┌────────────────────────────────────────────────────────────┐  │
   │  │  inventory_db  ── a DATABASE  (like "one .xlsx workbook")  │  │
   │  │  ┌──────────────────────────────────────────────────────┐  │  │
   │  │  │ production_adda ── a TABLE  (like "one sheet")        │  │  │
   │  │  │  id │ code        │ status                            │  │  │
   │  │  │  51 │ 3-PATTI-018 │ completed   ← a ROW               │  │  │
   │  │  └──────────────────────────────────────────────────────┘  │  │
   │  │  …114 more tables                                          │  │
   │  └────────────────────────────────────────────────────────────┘  │
   │  …and other databases beside it (test_production, sql_practice)  │
   └──────────────────────────────────────────────────────────────────┘
              ▲
              │  SQL  ── the LANGUAGE you talk to it with
              │         (not a thing that stores anything)
```

**Say it once out loud:** *"PostgreSQL is the program, my database is inside it,
SQL is how I ask it questions."* Getting these three words right in an interview is
free marks; getting them wrong is a visible tell.

**The client–server idea.** PostgreSQL is a **server**: a program that is always
running, owning data files, waiting for questions on port 5432. Django is a
**client**: it connects, sends SQL text, receives rows. `psql` (what `manage.py
dbshell` opens) is *another* client — me, typing SQL by hand, to the same server.
Anything Django can see, I can see from dbshell. Same drawer, different hands.

**Declarative, not procedural.** In Python I write *how* (loop, compare, append).
In SQL I state *what*: "all completed Addas." The database chooses the how — and
chapter 15 shows it re-chooses as data grows. That's why SQL from 1974 still runs
every bank on earth.

**Where the bytes live.** On my laptop: `/var/lib/postgresql/14/main` — owned by
the postgres program, never edited by hand (a half-copied file = corrupt drawer;
that's why `db.sh` exists instead of `cp`).

> 💡 **Samjho aise:** Postgres ek **bank** hai jo hamesha khula rehta hai. Uski
> tijori (data files) ko koi seedha haath nahi lagata — sab kaam **counter** se
> hota hai. Django us bank ka ek customer hai; `dbshell` se main khud bhi customer
> ban jaata hoon — **dono ek hi counter** pe jaate hain, isi liye jo Django dekhta
> hai wahi main dekh sakta hoon. Aur SQL wo **form** hai jo counter pe bharte ho:
> fixed format, jisme sirf yeh likhna hota hai *kya chahiye*, na ki *kaise laao*.

# Real World Example (My ERP)
- Server: PostgreSQL **14** on localhost:5432 (production will run **16** in Docker — ch 20 explains why that ordering matters).
- My databases inside that one server: `inventory_db` (real work), `test_production` (rehearsal), plus any branches.
- `inventory_db` holds **115 tables**. Every `class Adda(models.Model)` in the code *is* one of them.
- Clients: Django via `config/settings` DB block (`.env` → `DB_NAME`), and me via `dbshell`.

# Visual Diagram
```
   my code (Django)          me (dbshell/psql)
        │ SQL                     │ SQL
        ▼                         ▼
   ┌──────────────────────────────────────┐
   │ PostgreSQL server  (always running)  │
   │   inventory_db   test_production  …  │
   │   data files: /var/lib/postgresql/…  │
   └──────────────────────────────────────┘
        ▲ rows                    ▲ rows
```

# Practical — try it yourself
```bash
# Which database program and version is running?
psql --version                        # client version (14.x)
# Open the SQL prompt, already connected to whatever .env points at:
env/bin/python config/manage.py dbshell --settings=config.settings.local
```
Inside psql:
```
\conninfo        -- who am I, which database, which port?
\l               -- list ALL databases in this server (my drawers)
\dt              -- list tables in THIS database (expect ~115 rows)
SELECT version();     -- ask the SERVER its version (statement → ends with ;)
SELECT current_database();
\q               -- quit
```
Every psql `\` command is a client-side shortcut; everything ending in `;` is
real SQL sent to the server.

# Production Walkthrough
Same three words, on the live server:
- **The program** is `postgres:16.6-alpine` in a Docker container (`docker-compose.yml`), not a service you installed by hand. It restarts with the machine because Docker restarts it.
- **The database** is created once by the container on first boot, then filled by `migrate` from `deploy/entrypoint.sh` (ch 19).
- **The client** is Gunicorn's Django processes — several of them, sharing a connection pool (`CONN_MAX_AGE = 600`, so each request does not pay a fresh handshake).
- **Nobody outside the app can reach it.** The Postgres port is never published to the internet; only the app's private Docker network can see it (ch 22).

# Debugging Guide
"The app can't reach the database" — check in this order, cheapest first:
1. **Am I even pointed at the right one?** `./scripts/db.sh current`. Half of local confusion ends here.
2. **Is the server running?** `psql --version` proves the *client* exists, nothing more. Try to connect: `manage.py dbshell`.
3. **Right credentials?** They come from `.env`. A typo there fails at connect time with `fe_sendauth` / `password authentication failed`.
4. **Right host?** `localhost` on your laptop, the service name `db` inside Docker. This is the single most common "works locally, breaks in the container" cause.
5. **`DATABASE_URL` set?** If it is, Django ignores every `DB_*` var — `db.sh` refuses to run at all for this reason (ch 21).

# Performance Notes
- Each Postgres connection is a real **OS process**, not a thread. That is why connections are expensive and why `CONN_MAX_AGE` (reuse for 10 minutes) matters more than it looks.
- At this factory's scale the database is never the bottleneck; the app's *number of queries* is (ch 16).
- The server keeps its own page cache (`shared_buffers`) — a "slow first query, fast second" pattern is the cache warming, not magic.

# Security Considerations
- The database must not be reachable from the internet. Ever. Port 5432 stays inside the private network.
- Credentials live in `.env`, gitignored. A leaked `.env` is a leaked database.
- On this laptop there is exactly **one role: `postgres`, a superuser** — fine for local, wrong for production, where the app should own its tables and nothing more (ch 22 records this as owed work).

# Architecture Decisions
- **PostgreSQL, not SQLite or MySQL** — because this system holds money: exact `numeric` arithmetic, real constraints, advisory locks, mature backup tooling (ch 03, 13, 18, 20).
- **One database, not one per factory** — locked by ADR-0010: two databases cannot share a transaction, so a forked ledger can never be reconciled (ch 17, 24).
- **The app talks SQL through the ORM, not raw strings** — safety by default (ch 22), with raw SQL reserved for things the ORM cannot express.

# Best Practices
- Learn `dbshell` early: anything the app can see, you can see.
- Never edit `/var/lib/postgresql` by hand; use `pg_dump`/`psql` (ch 20).
- Keep the connection string in one place (`.env`) and never in code.
- When something is confusing, first ask *"which database am I actually on?"*

# Beginner Mistakes
- Thinking data lives in the project folder. It does not; `git clone` on a new
  machine brings **zero data** — that's what backups are for (ch 20).
- Editing `/var/lib/postgresql` files by hand. Corruption, guaranteed.
- Saying "a SQL database" when you mean Postgres, and "Postgres" when you mean
  the SQL language. Interviewers notice.
- Forgetting the `;` — psql silently waits for it; it is not frozen.

# Interview Questions
- **Junior:** *Difference between SQL and PostgreSQL?* — SQL is the language;
  PostgreSQL is one program that implements it.
- **Junior:** *Why a database over files/Excel?* — concurrency, integrity rules,
  crash-safe atomic writes, query power.
- **Mid:** *What does "declarative" mean for SQL?* — you specify the result, the
  planner picks the algorithm; plans change as data grows without code changes.
- **Senior:** *What actually happens between client and server on one query?* —
  connection (auth) → SQL text → parse → plan → execute → rows stream back; the
  client never touches data files.
- **Staff:** *When is a relational database the wrong choice?* — When your access
  pattern genuinely fights the model, not when the data "feels unstructured". Real
  cases: append-only event streams at volumes where you never query a single row
  (a log store), full-text search at scale (a dedicated index), caches and
  ephemeral counters (Redis — this project uses it exactly there, and deliberately
  does **not** back it up because nothing durable lives in it), and blobs, which
  belong in object storage with only the *path* in the database. The failure mode I
  would push back on is the opposite one: reaching for a document store to avoid
  designing a schema, then re-implementing joins, constraints and transactions in
  application code — badly. This project keeps money in Postgres precisely because
  it needs `numeric`, constraints and transactions; but it keeps uploaded photos on
  disk and the session cache in Redis. Choose per access pattern, not per fashion,
  and be able to name what you would lose.

### Why interviewers ask these — and the answer that separates levels

| Testing for | Weak answer | What lands |
|---|---|---|
| Do you separate the **language** from the **engine**? | "SQL and PostgreSQL are basically the same thing." | SQL is the **language/standard**; Postgres is one **implementation** of it. That is why `LIMIT` here is `TOP` in SQL Server — portable SQL is a myth you should name. |
| Do you know what a database gives you that a file cannot? | "It stores data in a structured way." | Four things a file cannot: **concurrency** (many writers, no corruption), **integrity** (constraints refuse bad rows), **atomic crash-safe writes**, and a **query planner**. Say "my books cannot be half-written". |
| Do you understand *declarative*? | "You write SQL and it runs it." | You state the **result**, not the algorithm. The **planner** picks the strategy and re-picks it as the data grows — so the same query changes plan without a code change (ch 15). |
| Can you narrate one query end to end? | "It sends the query and gets rows back." | connection+auth → **parse** → **plan** → **execute** → rows stream back. The client **never touches the data files** — that indirection is what makes concurrency and permissions possible at all. |

**The killer follow-up:** *"So why not just use MongoDB / Excel / a JSON file for this?"* — the answer must name a real invariant you would lose. For a factory ledger: no atomic multi-row write means a settlement can land half-written, and money that is half-written is money lost.

# Revision Notes
- **database** = the store · **SQL** = the language · **PostgreSQL** = the program.
- Client–server: Django and `dbshell` are both clients of the same server.
- SQL is **declarative** — you say *what*, the planner picks *how* (ch 15).
- Data lives in Postgres's own files, not your project folder.
- One server holds many databases; `.env DB_NAME` picks one.

# Cheat Sheet
- database = organised durable store · SQL = the language · Postgres = the program
- Postgres is a server on :5432; Django and psql are both clients
- one server, many databases; mine: `inventory_db` + rehearsal branches
- data files live under `/var/lib/postgresql/14/main` — never hand-edit
- `\l` databases · `\dt` tables · `\conninfo` where am I · `;` ends SQL

# My ERP Section
| Thing | Where |
|---|---|
| Which DB the app opens | `.env` → `DB_NAME` (read by `config/settings/base.py`) |
| SQL prompt | `manage.py dbshell` |
| The 115 tables | created by migrations (ch 19) |
| Drawer management | `scripts/db.sh` (list/new/use/branch…) |

# Practice Tasks
1. **Read the code:** open `config/config/settings/base.py` and find the `DATABASES` block. Which env var chooses the database, and what happens if `DATABASE_URL` is set instead?
2. **Debug:** set `DB_NAME` to a name that does not exist and run `manage.py dbshell`. Read the exact error, then fix it. You have now seen the failure you will meet on a real server.
3. **Design:** the factory wants a second site next year. Argue, in five sentences, why a second *database* is the wrong answer (use ch 17's atomicity point).

# Homework
1. Open dbshell, run `\conninfo`, `\l`, `\dt`. Count: does `\dt` show ~115 tables?
2. Run `SELECT current_database();` — confirm it matches `./scripts/db.sh current`.
3. Say out loud, without notes, the difference between SQL and PostgreSQL. (Kos law: out loud or it doesn't count.)

# Further Reading & Live Resources
- [SQLBolt — interactive lessons](https://sqlbolt.com/) — do lessons 1–2 today
- [Postgres official tutorial, ch 1](https://www.postgresql.org/docs/current/tutorial-start.html)
- [psql cheat sheet](https://www.postgresqltutorial.com/postgresql-administration/psql-commands/)
- [Postgres docs — Architectural Fundamentals](https://www.postgresql.org/docs/current/tutorial-arch.html) — the client/server split this chapter describes, from the source
- [Use The Index, Luke — anatomy of an SQL query](https://use-the-index-luke.com/sql/anatomy) — what the server does between receiving text and returning rows
- [Designing Data-Intensive Applications, ch 1–2](https://dataintensive.net/) — the standard reference on when a relational model fits and when it does not (book; ch 1–2 are the relevant part)
- Sibling course: [Deployment ch 21 — PostgreSQL](../deployment_course/21_PostgreSQL.md) — the same database, seen as a thing you have to run and back up
