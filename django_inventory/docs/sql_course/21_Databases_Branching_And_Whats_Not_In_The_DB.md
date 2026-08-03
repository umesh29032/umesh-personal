---
id: sql-course-21-databases-branching-and-whats-not-in-the-db
type: lesson
status: active
owner: handwritten
scope: sql, postgresql — database fundamentals taught from this ERP
anchors: config/expense/services/settlement_service.py, config/production/services/pool_service.py
verified: 2026-08-01
---

# 21 — Many Databases, Branching & What's NOT in the DB

> Part of [SQL From Zero](00_COURSE_OVERVIEW.md). Prev: [20](20_Backups_And_Restore.md) · Next: [22 — Security & SQL Injection](22_Security_And_SQL_Injection.md).

# Learning Objectives
By the end of this chapter you can:
- create, switch, branch and delete local databases without fear
- name the four things that are NOT in the database
- explain why every local database shares one media folder — and what breaks
- design a "restore the whole system" checklist that is actually complete

# Purpose
To become the confident operator of my own databases — create, switch, fork,
delete without fear — and to learn the four things that live **outside** the
database and therefore break in ways SQL knowledge alone cannot explain.

# The Problem
Two problems, both mine, both real.

**(1) My working database became unusable for judgement.** 28 Addas, 19 products,
106 users of accumulated test data. Opening any list is noise. An honest hand-audit
is impossible — not because the software is wrong, but because **I cannot see the
signal**. The instinct is to wipe it. That instinct destroys the only record of
journeys I have already proved.

**(2) Some of my data is not in the database at all** — and a "complete" database
backup silently omits it.

# Theory (from zero)

**One server, many databases.** PostgreSQL holds many completely separate
databases side by side (ch 01). Which one the app opens is decided by **one line**
in `.env`:

```
   .env:  DB_NAME=inventory_db
                  ▲
                  └── change this word ⇒ the app opens a different database
                      change it back   ⇒ your old data returns, untouched
   Nothing is copied. Nothing is moved. Nothing is deleted. It is a POINTER.
```

**Branching = fork the data at a point in time**, like `git branch` for rows:

```
   THE PROBLEM IT SOLVES
   Setting up product + sizes + flow + rates + cloth + workers = 30 slow minutes.
   Now you want to test something destructive. Do you redo the 30 minutes after?

        test_production ──────●──────────────────────▶  (setup preserved)
                              │  branch
                              └──▶ before_settlement ──▶ break things freely
   Branches NEST: branch off a branch off a branch. Each one is a full,
   independent database, so there is no chain to break and nothing to merge.
```

Mechanically, `db.sh branch` is `pg_dump` → `createdb` → `psql restore` (ch 20).
It is **not** `CREATE DATABASE … TEMPLATE`, because a template copy requires *no
active connections* to the source — impossible while the app is running.

### The four things that are NOT in the database

```
   ┌───────────────────────────────────────────────────────────────────┐
   │ ① UPLOADED FILES → config/media/                                  │
   │    the DB stores only the PATH ("cutting_pattern/3-PATTI-001/x.jpg")│
   │    13 upload columns across 5 apps · ALL databases share ONE tree  │
   ├───────────────────────────────────────────────────────────────────┤
   │ ② LOGIN SESSIONS → inside EACH database (django_session, 370 rows) │
   │    ⇒ every db.sh use LOGS YOU OUT. Normal, not a bug.              │
   ├───────────────────────────────────────────────────────────────────┤
   │ ③ LOGIN LOCKOUT COUNTERS → the process cache (LocMemCache locally) │
   │    ⇒ survives a database switch; cleared by restarting runserver   │
   ├───────────────────────────────────────────────────────────────────┤
   │ ④ SECRETS → .env (+ .env.bak)                                     │
   │    never in git, never in a dump. Lose these and a restore is dead │
   └───────────────────────────────────────────────────────────────────┘
```

**Why ① bites hard.** Adda codes repeat across databases (every fresh DB can mint
`3-PATTI-001`), and upload paths are keyed by Adda code. So two databases' files
land in the *same directories*:

```
   config/media/cutting_pattern/3-PATTI-001/photos/x.jpg
                                 ▲
        inventory_db's rows point here ─┬─ test_production's rows point here TOO
                                        │
   Deleting that photo in ONE database deletes the REAL FILE for both.
   The other database keeps a row pointing at nothing (a dead link).
   ⇒ On test databases: don't delete photos.
   ⇒ db.sh delete drops a database but ORPHANS its media forever.
```

> 💡 **Samjho aise:** Database ek **register** hai jisme likha hai *"photo almirah
> #3 mein rakhi hai"*. Photo khud register mein nahi — almirah mein hai. Register
> ka backup lene se photo ka backup **nahi** hota. Aur saari databases **ek hi
> almirah** share karti hain — to ek register se photo phaad di, to doosre register
> ka bhi link toot gaya. Isi liye: test database pe photo delete mat karo.

# Real World Example (My ERP)
```
   MY ACTUAL DATABASES (db.sh list, with contents so I know which is which)
   ─────────────────────────────────────────────────────────────────────
   → inventory_db      26 MB   23 stages · 19 products · 28 addas · 106 users
     test_production   18 MB   21 stages ·  5 products ·  0 addas ·   0 users
     v21d_rehearsal    16 MB    4 stages ·  5 products ·  1 addas ·   5 users
     v22_rehearsal     16 MB    4 stages ·  5 products ·  2 addas ·   5 users
   ─────────────────────────────────────────────────────────────────────
   0 addas + 0 users = an untouched fresh one.  ~18 MB each when empty.
```

`config/media/` on my machine holds: `advances/`, `cutting_pattern/`,
`patterns_ai/`, `profile_pics/`, `storefront/`. Both `media/` and `config/media/`
are gitignored — correctly, since they hold real people's photos.

**A trap now guarded:** if `DATABASE_URL` is set in `.env`, Django **ignores
`DB_NAME` entirely** — so every `db.sh` command would have acted on the wrong
database while printing success. The tool now refuses to run at all in that case.
`DATABASE_URL` belongs on the server, never on my laptop.

# Visual Diagram
```
   THE FULL PICTURE OF "MY DATA"
   ═══════════════════════════════════════════════════════════════════════
                    ┌──────────────── PostgreSQL server ───────────────┐
   .env DB_NAME ───▶│ inventory_db │ test_production │ sql_practice … │
       (a pointer)  └──────────────────────────────────────────────────┘
                              │ rows contain PATHS, not files
                              ▼
                    config/media/  (ONE shared tree, all databases)
                    ├── cutting_pattern/3-PATTI-001/photos/x.jpg
                    ├── profile_pics/ · advances/ · storefront/
                    │
                    .env  ← secrets (not in git, not in any dump)
   ═══════════════════════════════════════════════════════════════════════
   db.sh save        backs up ▓▓▓ the database only
   deploy/backup.sh  backs up ▓▓▓ database ▓▓▓ AND media  ← the real one (ch 20)
```

# Practical — try it yourself
```bash
# 1. the operator's dashboard: what do I have, and what's in each?
./scripts/db.sh list
./scripts/db.sh current                 # which one am I on?
./scripts/db.sh check                   # is THIS one ready to run a batch?

# 2. fork before doing something risky (a save-point for data)
./scripts/db.sh branch before_settlement --use
#    ...experiment, break things, mis-settle on purpose...
./scripts/db.sh use test_production     # your careful setup is untouched

# 3. prove sessions live in the database (fact ②)
./scripts/db.sh use test_production     # → you are logged out of the app. Expected.

# 4. see the files that are NOT in any database (fact ①)
ls config/media/
du -sh config/media/ 2>/dev/null
git check-ignore -v config/media/probe  # proves it's gitignored

# 5. clean up a database you're done with (auto-backup first)
./scripts/db.sh delete before_settlement --yes-delete before_settlement
#    NOTE: its media files stay behind in config/media/ as orphans, forever
```
```sql
-- 6. sessions really are rows, in THIS database (REAL: 370 in inventory_db)
SELECT count(*) FROM django_session;

-- 7. the DB stores paths, not files — look at one
SELECT image FROM production_cuttingpatternphoto LIMIT 3;
--    ^ text like 'cutting_pattern/<ADDA>/photos/<file>.jpg' — a POINTER to disk
```

# How Django Finds This Database — the 5-hop chain

**The question this answers:** *"I switched database and now I cannot log in. Is the
admin login part of Django, or part of the database?"*

**One idea first:** **a login is DATA, not CODE.** It is one row in the
`accounts_user` table, inside **one** database. Switch database and you switch which
`accounts_user` table you are reading — so a new database has no login for the same
reason it has no orders.

> 💡 **Samjho aise:** Postgres = **poori building** · ek database = **ek flat** ·
> ek table = **flat ke andar almari** · ek row = **almari mein ek file**.
> Aapka login ek *file* hai. Doosre flat mein wo file nahi rakhi — isliye wahan
> chaabi kaam nahi karegi. Code same hai, **data alag hai**.

## The four layers

```
POSTGRES SERVER (one program, port 5432)
│
├── DATABASE inventory_db ──── TABLE accounts_user ──── 106 rows  ← real logins
├── DATABASE test_from_zero ── TABLE accounts_user ────   0 rows  ← no login yet
└── DATABASE test_production ─ TABLE accounts_user ────   0 rows
```

Same server. Same table *name*. Same columns. **Different rows.** That is the whole
puzzle.

## The chain, hop by hop

Open each file at the line shown — this is the entire mechanism, no magic left:

```
YOU: env/bin/python config/manage.py runserver
        │
  ① config/manage.py:9
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
        │                           ↳ "read settings from config/settings/local.py"
  ② config/config/settings/base.py:16
    from decouple import config      ↳ the tool that READS .env
        │
  ③ config/config/settings/base.py:168
    'NAME': config('DB_NAME', default='inventory_db')
        │                           ↳ "which database? ask .env"
  ④ .env      DB_NAME=test_from_zero
        │                           ↳ ⭐ ONE LINE decides everything
  ⑤ PostgreSQL localhost:5432 → opens database "test_from_zero"
```

| Hop | Where | Decides |
|---|---|---|
| ① | `config/manage.py:9` | which settings file |
| ② | `config/config/settings/base.py:16` | that `.env` is the config source |
| ③ | `config/config/settings/base.py:168` | `DB_NAME` names the database |
| ③b | `config/config/settings/base.py:165-173` | the full `DATABASES` dict (user/password/host/port) |
| ③c | `config/config/settings/base.py:173` | `CONN_MAX_AGE: 600` — reuse a connection for 10 minutes |
| ④ | `.env` (never in git) | **the actual answer** |
| ⑤ | Postgres `:5432` | hands over that database |

**So "switching database" = editing one line of `.env`.** The code never changes.

## ⚠️ Why a restart is compulsory

```
server START ─► reads settings ONCE ─► opens a connection ─┐
                                                           ▼
every later request ──────────────► reuses that open connection
                                    (CONN_MAX_AGE = 600s)
```

Django reads settings **once, at start-up**. A running server still holds the *old*
database. Edit `.env` under a live server and nothing it can see changes — you would
be reading the old data and blaming the tool. **Switch → Ctrl+C → start again.**

## How a login actually succeeds

```
1. createsuperuser        → INSERT one row into accounts_user (CURRENT database only)
2. you submit email + password
3. Django runs:  SELECT * FROM accounts_user WHERE email = <typed>
                 └── in whichever database hop ③ chose
4. no row?  → "invalid login"          ← exactly the 0-users case
   row?     → compare password to the stored HASH
5. hash matches → you are in
```

- Login field is **email**, not username: `config/accounts/models.py:205`
  → `USERNAME_FIELD = "email"`. The model itself: `config/accounts/models.py:116`.
- **The password is never stored** — only an **Argon2 hash**. Nobody can read a
  password out of the database, which is why a stolen dump is survivable (ch 22).
- Step 3 is a plain `SELECT`. You can run it yourself — see below.

## Built-in commands vs the ones this project added

| Command | What it really does | Whose? |
|---|---|---|
| `migrate` | creates/alters **tables** (shapes, never data) | Django built-in |
| `createsuperuser` | one `INSERT` into `accounts_user` | Django built-in |
| `runserver` | the development web server | Django built-in |
| `shell` | Python prompt with your models loaded | Django built-in |
| `dbshell` | drops you into raw `psql` on the current DB | Django built-in |
| `seed_master_data` | inserts the 21 stages, 10 skills, access links | **this project** |
| `verify_production` | asserts the data is sane after a deploy | **this project** |
| `db.sh new/use/save/…` | wraps `createdb`/`dropdb`/`pg_dump` + the `.env` edit | **this project** |

> 💡 **Samjho aise:** Django ke saath kai **ready-made** commands aate hain. Humne
> factory ke liye kuch **apne** banaye. Dono ek hi tarah chalte hain:
> `manage.py <command>`. Naya banana = `management/commands/` mein ek file rakhna.

## Prove the whole chain yourself (read-only, 30 seconds)

```bash
./scripts/db.sh current
#    → test_from_zero          (what .env says)

env/bin/python config/manage.py shell --settings=config.settings.local -c \
  "from django.conf import settings; print(settings.DATABASES['default']['NAME'])"
#    → test_from_zero          (what DJANGO says — same name = chain proved)

env/bin/python config/manage.py dbshell --settings=config.settings.local
```
then, at the `psql` prompt:
```sql
SELECT count(*) FROM accounts_user;   -- 0 on a fresh database
\dt                                   -- every table in THIS database
\q
```

That `SELECT` is literally step 3 of the login. Run it before and after
`createsuperuser` and watch `0` become `1` — that is your login appearing as a row.

**Deeper, with clickable line numbers:**
[kos local-testing-environment](../../kos/concepts/testing/local-testing-environment.md)
§ *Behind the scenes*.

# Production Walkthrough
- On the server there is **one** database, not several: branching is a *development* technique. The production equivalent of a branch is a **restore into a new name** (ch 20).
- `MEDIA_ROOT = config/media/` is a real directory on the server, mounted as a Docker volume so it survives container replacement (ch 20's `/media` in the backup path).
- Sessions live in `django_session` in the database, so a production database restore also restores whoever was logged in at the time — harmless (8-hour cookie) but worth knowing.
- Login rate-limit counters live in Redis, deliberately *not* the DB: they are protection state, not truth, and losing them on restart is acceptable.

# Debugging Guide
"It works on my machine" / "the images are broken":
1. **Which database am I on?** `db.sh current`. First question, always.
2. **Did the server restart after `.env` changed?** Settings are read at boot.
3. **Broken images after a restore?** The rows point at files that were never copied — media is separate (ch 20).
4. **Logged out unexpectedly?** You switched databases; sessions live inside each one.
5. **Locked out after wrong passwords?** That counter is in the cache — restart the dev server, not the database.
6. **`DATABASE_URL` set locally?** Django then ignores `DB_NAME` entirely; the tool now refuses to run at all rather than act on the wrong database.

# Performance Notes
- Each empty database costs ~18 MB — branching freely is cheap at this scale.
- `db.sh branch` is dump+restore, so its cost scales with data size; it works while the app runs, which `CREATE DATABASE … TEMPLATE` does not.
- Many idle databases cost almost nothing; many idle *connections* do (ch 24).
- Large media directories slow backups far more than the database does — plan the media strategy before the DB strategy at scale.

# Security Considerations
- **A dump is as sensitive as the database** — `db_backups/` and `*.sql` are gitignored for that reason (ch 20, 22).
- `config/media/` holds people's photos and receipts; it is gitignored and needs the same protection as the database.
- `.env.bak` (created by `db.sh use`) contains secrets — also gitignored.
- Test databases restored from production data carry real personal data. Anonymise, or accept that your laptop is now in scope for a data breach.

# Architecture Decisions
- **Create beside, never wipe.** The tool has no delete path at all for creation flows; the only destructive verb requires the name typed twice plus an automatic backup.
- **Files outside the database** (paths in rows) — the standard choice, with the honest cost that backups must cover both.
- **Cache state outside the database** so it can be lost without consequence.
- **One gate for "which database"** — a single `.env` line, so switching is auditable and reversible.

# Best Practices
- Run `db.sh check` after creating a database; do not guess whether it is usable.
- Branch before anything risky; a branch is cheaper than a re-setup.
- Never delete photos on a test database — the file is shared with every other database.
- Keep `DATABASE_URL` out of local `.env` files entirely.

# Beginner Mistakes
- Wiping the working database to "start clean" — losing the settled journeys that
  are your only regression evidence. **Create beside it instead.**
- Believing a `.sql` dump is a complete backup. It has no media (ch 20).
- Deleting a pattern photo on a test database — the shared real file goes with it,
  breaking other databases and older backups.
- Editing `.env` and not restarting the server, then debugging "stale data".
- Being surprised by the logout after a switch (it is `SESSION_ENGINE = db`).
- Looking for `media/` at the repo root — `MEDIA_ROOT` is **`config/media/`**.
- Leaving `DATABASE_URL` in a local `.env`.

# Interview Questions
- **Junior:** *Where should user-uploaded files live — in the database or on disk?* — on disk/object storage, with only the path in the database; blobs bloat the DB, break dump size, and can't be served efficiently.
- **Junior:** *Where do Django sessions live by default?* — the `django_session` table (so they are per-database).
- **Mid:** *Your DB backup restored fine but all images are broken. Why?* — media is filesystem state, backed up separately; a complete strategy covers DB **and** media (and secrets separately).
- **Mid:** *How would you give every developer a realistic database safely?* — restore a sanitised dump into a per-developer database; switch via config, never share one; **anonymise personal data** for non-production copies.
- **Senior:** *How do you implement "database branching" without downtime on the source?* — dump/restore into a new database (works with live connections), or `CREATE DATABASE … TEMPLATE` **only** when the source has no active sessions; managed platforms use copy-on-write snapshots instead.
- **Senior:** *Files on local disk vs object storage (S3) — trade-offs?* — local disk is simple and fast but ties you to one machine, complicates scaling/containers and must be backed up separately; object storage is durable, shareable across instances and independently versioned, at the cost of latency and a new dependency. A containerised deploy pushes hard toward object storage.
- **Staff:** *What is in scope for "restore the system", beyond the database?* — schema + data (dump), uploaded media, secrets/config, TLS certs, and the runbook itself; plus a rehearsal proving the sequence works and a stated RPO/RTO (ch 20).

### Why interviewers ask these — and the answer that separates levels

| Testing for | Weak answer | What lands |
|---|---|---|
| Where do uploaded files belong? | "In the database, so backups cover everything." | **On disk or object storage, with only the path in the database.** Blobs bloat the DB, wreck dump size and cannot be served efficiently. The cost you accept: media must be backed up **separately** (ch 20). |
| DB restored fine, every image broken — why? | "The restore must have failed." | It did not. **Media is filesystem state**, backed up on a different mechanism — and the database only ever held the **path**. DB and media must be restored from the **same moment** or the paths point at nothing. |
| Can you give every developer a realistic database safely? | "Share a staging database." | Restore a **sanitised** dump into a **per-developer** database, switched by config, never shared — and **anonymise personal data** for any non-production copy. A shared dev database means one person's test deletes another's afternoon. |
| Local disk or object storage? | "Local disk is fine and faster." | Local disk is simple and fast but **ties you to one machine**, complicates containers/scaling, and needs its own backup. Object storage is durable, shareable across instances and independently versioned, at the cost of latency and a dependency. **A containerised deploy pushes hard toward object storage.** |

**The killer follow-up:** *"Define the full scope of 'restore the system'."* — schema+data, uploaded media, secrets/config, TLS certs, **and the runbook itself** — plus a rehearsal proving the sequence and a stated RPO/RTO. Anyone whose answer stops at "the database" has never actually rebuilt one.

# Revision Notes
- One Postgres server holds many databases; `.env DB_NAME` is a **pointer**.
- `db.sh`: `list · current · check · fresh · new · use · branch · save · restore · delete`.
- **Branch** = dump+restore fork; nests freely; the source is untouched.
- NOT in the DB: **media files · cache/lockouts · `.env` secrets** (and sessions are per-DB).
- `MEDIA_ROOT = config/media/` is **shared by every local database**.

# Cheat Sheet
- one Postgres server, many databases; `.env DB_NAME` is just a **pointer**
- `db.sh`: `list · current · check · fresh · new · use · branch · save · restore · delete`
- **branch** = dump+restore fork; nests freely; source stays untouched
- NOT in the DB: **media files · (sessions are per-DB) · cache lockouts · .env secrets**
- `MEDIA_ROOT = config/media/` — **shared by every local database**
- deleting a photo anywhere deletes the shared file; `db.sh delete` orphans media
- switching databases logs you out; restart the server after editing `.env`

# My ERP Section
| Fact | Value |
|---|---|
| Databases today | `inventory_db` (26 MB, real) · `test_production` · two rehearsals |
| Media root | `config/media/` — advances, cutting_pattern, patterns_ai, profile_pics, storefront |
| Upload columns | 13 FileField/ImageField across 5 apps |
| Sessions | `django_session` in each DB (370 rows in `inventory_db`), 8h cookie |
| Lockout counters | process cache — cleared by restarting `runserver` |
| `DATABASE_URL` guard | `db.sh` refuses to run if it is set |
| Human guide | [kos: local-testing-environment](../../kos/concepts/testing/local-testing-environment.md) |
| Registry of findings | [FRESH_DB_REQUIREMENTS](../FRESH_DB_REQUIREMENTS.md) F-4 |

# Practice Tasks
1. **Read the code:** find `MEDIA_ROOT` in `config/config/settings/base.py`. Then list `config/media/` and match one folder to the model that writes there.
2. **Debug:** branch a database, delete something significant on the branch, switch back, and prove the original is intact.
3. **Design:** write the complete "restore the whole system" checklist — every artefact, in execution order. Compare it with `deploy/backup.sh` and note anything missing.
4. **Architecture:** argue whether uploads should move to object storage (S3-style). What does it buy, what does it cost, and what would change in the backup script?

# Homework
1. Run `db.sh list`. For each database, say from the counts alone whether it is real work or a fresh shell.
2. Branch your practice database, delete something big on the branch, then switch back and prove the original is intact.
3. Run Practical #7 and look at a stored `image` value. Then find that exact file under `config/media/`. Explain in one sentence why a `.sql` backup would not contain it.

# Further Reading & Live Resources
- [Postgres: managing databases](https://www.postgresql.org/docs/current/managing-databases.html)
- [Django: file uploads & MEDIA_ROOT](https://docs.djangoproject.com/en/5.0/topics/files/)
- [Django: sessions](https://docs.djangoproject.com/en/5.0/topics/http/sessions/)
- [Postgres CREATE DATABASE (TEMPLATE)](https://www.postgresql.org/docs/current/sql-createdatabase.html)
