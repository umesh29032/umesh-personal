---
id: sql-course-20-backups-and-restore
type: lesson
status: active
owner: handwritten
scope: sql, postgresql — database fundamentals taught from this ERP
anchors: config/expense/services/settlement_service.py, config/production/services/pool_service.py
verified: 2026-08-01
---

# 20 — Backups & Restore

> Part of [SQL From Zero](00_COURSE_OVERVIEW.md). Prev: [19](19_Migrations.md) · Next: [21 — Many Databases, Branching & What's NOT in the DB](21_Databases_Branching_And_Whats_Not_In_The_DB.md).

# Learning Objectives
By the end of this chapter you can:
- state your RPO and RTO in numbers
- choose between plain and custom dump formats, and restore each
- explain why a dump is not a full backup of this system
- run a restore drill and verify it with independent numbers

# Purpose
To be able to say, honestly, *"if the server died right now, here is exactly how I
get my factory back, and here is what I would lose."* Anything less than that
sentence is not a backup strategy.

# The Problem
Every other chapter protects data *while the system works*. This chapter is about
the day it doesn't: disk failure, a `DELETE` without a `WHERE` (ch 11), a bad
migration that dropped a column (ch 19), a stolen laptop, ransomware. Constraints
and transactions cannot help — the data is gone. Only a **copy elsewhere** can.

# Theory (from zero)

**Two families of backup:**

```
   ┌─ LOGICAL  (pg_dump) ──────────────────────────────────────────┐
   │  "the SQL needed to recreate everything"                      │
   │  portable across versions/machines · per-table possible       │
   │  slower to make and restore · what db.sh uses                 │
   └───────────────────────────────────────────────────────────────┘
   ┌─ PHYSICAL (the data files + WAL) ─────────────────────────────┐
   │  a byte-level copy of the cluster                             │
   │  fast · version-locked · whole-cluster only                   │
   │  enables Point-In-Time Recovery (replay WAL to any second)    │
   └───────────────────────────────────────────────────────────────┘
```

**Two dump formats** — and the difference matters operationally:

| Format | Made with | Restored with | Readable? |
|---|---|---|---|
| plain `.sql` | `pg_dump` | **`psql`** | yes — open it in an editor |
| custom `-Fc` | `pg_dump -Fc` | **`pg_restore`** | no (compressed) |

Open a plain dump once and the mystery dies: it is `CREATE TABLE …` followed by
thousands of `COPY … FROM stdin` data lines. **A dump is literally the SQL that
rebuilds everything.**

**The two numbers every professional quotes:**

```
   ┌──────────────────────────────────────────────────────────────┐
   │  RPO — Recovery Point Objective                               │
   │        how much data may I LOSE?  = time since last backup    │
   │        nightly backup ⇒ RPO up to 24 hours                    │
   │                                                               │
   │  RTO — Recovery Time Objective                                │
   │        how LONG may recovery take? = restore + verify time     │
   └──────────────────────────────────────────────────────────────┘
   Saying "my RPO is 24h, RTO about 30 minutes" is the language of someone
   who has actually thought about it. It is also an interview differentiator.
```

**The version rule — one-way traffic:**

```
   pg_dump on 14  ──▶ restore on 16   ✅  old → new is supported
   pg_dump on 16  ──▶ restore on 14   ❌  new → old generally FAILS
   My laptop = PostgreSQL 14 · my production = postgres:16.6-alpine
   ⇒ laptop dumps go up fine; server dumps do NOT come down to my laptop.
   ⇒ Rehearse restores on the machine that will actually do the restoring.
```

> 💡 **Samjho aise:** Backup **photo nahi, recipe hai** — poora khaana dobara
> banane ki likhi hui vidhi. Aur vidhi tab hi bharosemand hai jab ek baar usse
> **sach mein bana ke** dekha ho. Jo backup kabhi restore karke nahi dekha, wo
> backup nahi — **umeed** hai. Shaadi mein bina chakha khaana parosna wahi hai.

# Real World Example (My ERP)
I have **two different backup systems**, on purpose, and confusing them is a real
hazard:

```
   ① LOCAL — for testing convenience         ② PRODUCTION — for survival
   ═══════════════════════════════════        ══════════════════════════════════
   scripts/db.sh save                        deploy/backup.sh (nightly service)
   pg_dump --clean --if-exists  →  .sql      pg_dump -h db -Fc  →  /backups
   restore: psql -v ON_ERROR_STOP=1          + restic backup /backups /media
   lives in  db_backups/  (gitignored)       → offsite (B2/R2), tagged nightly
   DATABASE ONLY                             DATABASE **AND** MEDIA
   my laptop's pg14                          server's pg16
   ─────────────────────────────────────────────────────────────────────────
   restic retention (real): --keep-daily 7 --keep-weekly 4 --keep-monthly 6
   stated RPO in that script: 24h
```

Three consequences I must keep straight:
1. **`db.sh save` is not my go-live backup.** It omits `config/media/` entirely
   (ch 21) and it is a local convenience. `deploy/backup.sh` is the real one, and
   it backs up **both** the dump and the media directory.
2. **The formats are not interchangeable.** A `-Fc` archive from the server cannot
   be replayed with `psql`; it needs `pg_restore`. And my local `pg_restore` is
   version 14, so a v16 archive will refuse.
3. **`ON_ERROR_STOP=1` exists because of a real bug found in this project.**
   Without it, `psql` walks past SQL errors and exits 0 — so a *partially*
   restored database got a green tick. That is the worst possible failure mode:
   a corrupt copy you believe is good, right before you delete the original.
   The tool now stops on the first error and drops the half-restored database.

# Visual Diagram
```
   THE RESTORE DRILL — and where each piece comes from
   ═════════════════════════════════════════════════════════════════════
   DISASTER: production server is gone
        │
        ├─ ① new server + docker-compose (from git)          ← code: git
        ├─ ② .env with secrets                               ← password manager
        │      ⚠️ NOT in git, NOT in the backup. If this is lost,
        │         you have data you cannot decrypt/connect to.
        ├─ ③ restic restore latest                           ← offsite repo
        │      ├── /backups/*.dump   → pg_restore into the new DB
        │      └── /media/*          → the uploaded photos (ch 21)
        ├─ ④ migrate (schema already in the dump; runs clean) ← ch 19
        └─ ⑤ verify: row counts, ledger sum, log in, open one Adda
   ═════════════════════════════════════════════════════════════════════
   Data lost = everything since last night's run  (RPO ≤ 24h)
   THE ONLY WAY TO KNOW THIS WORKS IS TO HAVE DONE IT ONCE.
```

# Practical — try it yourself
```bash
# 1. make a real backup of the current database
./scripts/db.sh save
#    → db_backups/<name>__<timestamp>.sql   (gitignored, contains real data)

# 2. LOOK INSIDE a dump — this demystifies backups permanently
head -40 db_backups/*.sql            # CREATE TABLE / SET statements
grep -c "^COPY " db_backups/*.sql    # how many tables carry data

# 3. list what you have
./scripts/db.sh backups

# 4. THE DRILL THAT MATTERS: restore into a NEW database and verify it
./scripts/db.sh restore <file>.sql --into restore_drill
DB_NAME=restore_drill env/bin/python config/manage.py shell \
  --settings=config.settings.local -c "
from production.models import Adda
from expense.models import WorkerLedgerEntry
from django.db.models import Sum
print('addas:', Adda.objects.count(),
      'ledger:', WorkerLedgerEntry.objects.count(),
      Sum and WorkerLedgerEntry.objects.aggregate(s=Sum('amount'))['s'])"
#    Compare against the original: 28 addas · 201 rows · 18254.25
#    Numbers match ⇒ you now have a TESTED backup, not a hope.

# 5. clean up the drill
./scripts/db.sh delete restore_drill --yes-delete restore_drill --no-backup

# 6. read the production backup script — the one that actually matters
sed -n '1,25p' deploy/backup.sh
```

# Production Walkthrough
- `deploy/backup.sh` runs nightly in its own container: `pg_dump -Fc` **plus** `/media`, pushed off-site via **restic**, retained `--keep-daily 7 --keep-weekly 4 --keep-monthly 6`. Stated RPO: **24 hours**.
- **The local tool is not the production backup.** `db.sh save` writes a plain `.sql` of the database only — convenient for branching, useless for disaster recovery because it omits media and secrets.
- **`.env` is in neither backup, on purpose.** It lives in a password manager. Restore the data without it and you have rows you cannot connect to.
- Version direction matters on this project specifically: laptop **pg14**, server **pg16**. Dumps go up, not down.

# Debugging Guide
"The restore did not work" — or worse, appeared to:
1. **Did it stop on the first error?** Without `-v ON_ERROR_STOP=1`, `psql` walks past failures and exits 0 — a partial restore with a green tick. This project hit exactly that bug and now stops and drops the half-restored target.
2. **Check the file size.** A 0-byte or tiny dump is a failed `pg_dump`, not a backup — `db.sh` now refuses files under 1 KB.
3. **Wrong tool for the format?** Plain `.sql` → `psql`; `-Fc` → `pg_restore`. Using the wrong one fails confusingly.
4. **Version mismatch?** A v16 dump will not load into v14 tooling.
5. **Verify with numbers, not exit codes** — row counts and a known money total.

# Performance Notes
- `pg_dump` is a long read-only transaction: it does not block writers, but it does hold a snapshot that delays vacuum of dead rows (ch 18).
- `-Fc` (custom) is compressed and supports parallel restore (`pg_restore -j`); plain SQL restores single-threaded.
- Restore time, not dump time, is what your RTO depends on — measure the restore.
- Nightly logical dumps cap your RPO at 24h; WAL archiving (PITR) is what buys minutes instead of hours.

# Security Considerations
- **A dump contains everything**, including personal data and password hashes. Treat the file as the crown jewels: encrypted at rest, access-restricted, retention-limited.
- Anonymise before using production data anywhere non-production.
- `db_backups/`, `*.sql` and `.env.bak` are gitignored here precisely because a committed dump is an unrecoverable leak.
- Off-site copies need their own credentials — and those credentials must not live only on the machine being backed up.

# Architecture Decisions
- **Two systems, different jobs** — local convenience (`db.sh`) vs production survival (`backup.sh` + restic). Conflating them is the mistake.
- **DB + media backed up together** in production, because the app is only whole with both (ch 21).
- **Secrets stored separately** so a leaked backup is not also a leaked credential.
- **Restore is stopped-on-error and self-cleaning** — a half-restored database is worse than a failed restore, so the tool removes it.

# Best Practices
- Rehearse a restore on a schedule; an untested backup is a hope.
- Verify with independent assertions (counts, a known total), never just "the command finished".
- Write down RPO/RTO where the next person will find it.
- Never restore over a live database — restore into a new name, verify, then switch.

# Beginner Mistakes
- **Never having restored a backup.** The universal mistake. Untested backups fail
  precisely when tested for the first time, i.e. during the disaster.
- Restoring with `psql` and no `ON_ERROR_STOP=1`, then trusting the green tick.
- Assuming the database dump includes uploaded files. It does not (ch 21).
- Keeping backups only on the same machine/disk as the database.
- Committing a dump to git. It contains real people's data **and password hashes**
  — which is why `db_backups/` and `*.sql` are gitignored here.
- Backing up the data but not the **`.env`** secrets — you restore rows you cannot
  connect to or decrypt.
- Trying to restore a v16 `-Fc` archive with v14 tools.

# Interview Questions
- **Junior:** *What does `pg_dump` produce?* — a logical backup: the SQL/archive needed to recreate the database.
- **Junior:** *How would you restore a plain `.sql` dump?* — `psql -d newdb -f dump.sql`, ideally with `-v ON_ERROR_STOP=1`.
- **Mid:** *Logical vs physical backup?* — dump (portable, per-object, slower) vs file-level copy of the cluster (fast, version-locked, enables PITR).
- **Mid:** *What are RPO and RTO, and what are yours?* — max data loss vs max recovery time; mine: RPO ≤ 24h from a nightly run, RTO the time to provision + restic restore + verify. **Answering with numbers marks experience.**
- **Senior:** *What is Point-In-Time Recovery and when do you need it?* — a base backup plus archived WAL replayed to a chosen instant; needed when a 24-hour RPO is unacceptable or when you must recover to just before a bad statement.
- **Senior:** *A restore "succeeded" but the app is broken. How do you catch that class of failure?* — stop on the first SQL error, then verify with independent assertions (row counts, a known financial total, an actual login), not just an exit code. This project learned that lesson concretely.
- **Staff:** *Design a backup strategy for a payroll system.* — nightly logical dump + WAL archiving for PITR; offsite, encrypted, retention tiers (daily/weekly/monthly); dump **and** media together; secrets stored separately in a password manager; automated periodic **restore rehearsal** with verification assertions; document RPO/RTO. (That is close to `deploy/backup.sh` plus a rehearsal habit.)

### Why interviewers ask these — and the answer that separates levels

| Testing for | Weak answer | What lands |
|---|---|---|
| Do you answer RPO/RTO with **numbers**? | "We back up nightly and could restore if needed." | **RPO** = max data loss you accept · **RTO** = max downtime. Mine: RPO **≤ 24h** from a nightly run; RTO = provision + restic restore + verify, **measured once so it is a fact**. Answering with numbers is the single clearest experience marker here. |
| Logical vs physical — do you know what each unlocks? | "Both are backups, dump is easier." | `pg_dump` = **logical**: portable, per-object, slower. File-level cluster copy = **physical**: fast, **version-locked**, and the only route to **PITR**. If you need to recover to *just before* a bad statement, only the physical path can do it. |
| Do you know a restore can "succeed" and still be broken? | "The restore exited 0, so we are fine." | **Stop on the first SQL error** (`-v ON_ERROR_STOP=1`) — otherwise you get a half-restored database that looks alive. Then verify with **independent assertions**: row counts, a **known financial total**, an actual login. This project learned that concretely. |
| Is your backup complete, or just the database? | "The database is backed up." | A dump has **no media and no secrets**. Full recovery = **dump + uploads + `.env`** from a password manager. Restoring only the database gives you a working app with every image broken. |

**The killer follow-up:** *"When did you last restore from backup?"* — "Never" ends the topic. An untested backup is a rumour, and rehearsing once is the cheapest seniority you can buy. The strong answer names the date, the elapsed time, and what you asserted to prove it worked.

# Revision Notes
- Logical (`pg_dump`) = portable · physical (files+WAL) = fast, enables PITR.
- Plain `.sql` → **psql** · `-Fc` → **pg_restore**.
- Always `psql -v ON_ERROR_STOP=1`.
- **RPO** = data you may lose · **RTO** = time to be back.
- DB dump ≠ full backup: **media + `.env`** are separate.

# Cheat Sheet
- logical = `pg_dump` (portable) · physical = files+WAL (fast, PITR)
- plain `.sql` → restore with **`psql`** · `-Fc` → restore with **`pg_restore`**
- always `psql -v ON_ERROR_STOP=1` — a silent partial restore is the worst outcome
- **RPO** = data you may lose · **RTO** = time to be back
- dumps travel **old → new** only (my pg14 → pg16 fine, reverse fails)
- DB dump ≠ full backup: **media + .env** are separate (ch 21)
- an untested backup is a hope, not a backup

# My ERP Section
| Piece | Where |
|---|---|
| Local convenience backup | `scripts/db.sh save` → `db_backups/*.sql` (plain, gitignored) |
| Local restore | `db.sh restore <file> --into <new>` (`ON_ERROR_STOP=1`, drops target on failure) |
| Production backup | `deploy/backup.sh` — `pg_dump -Fc` + `restic backup /backups /media` |
| Retention (real) | `--keep-daily 7 --keep-weekly 4 --keep-monthly 6`, tag `nightly` |
| Stated RPO | 24h (documented in `deploy/backup.sh`) |
| Secrets | `.env` — password manager, never git, never in the dump |
| Runbook | [deploy/README.md](../../deploy/README.md) |

# Practice Tasks
1. **Read the code:** open `deploy/backup.sh`. Write down what it dumps, what else it includes, where it sends it, and each retention tier.
2. **Debug:** do the full restore drill into a new database and verify 28 addas / 201 ledger rows / ₹18,254.25. You now have a *tested* backup.
3. **Design:** the owner says 24 hours of data loss is unacceptable. Design the change (name the mechanism) and state the new RPO.
4. **Architecture:** write the one-page disaster-recovery runbook for this system, in the order you would actually execute it at 3am.

# Homework
1. Run `./scripts/db.sh save`, then `head -40` the file. Find one `CREATE TABLE` and one `COPY` line. Say out loud what a dump *is*.
2. Do the full restore drill (Practical #4) and confirm 28 addas / 201 ledger rows / ₹18,254.25 in the restored copy. You now have a *tested* backup.
3. Read `deploy/backup.sh`. Write down: what it dumps, what else it includes besides the database, where it sends it, and how long each tier is kept.

# Further Reading & Live Resources
- [Postgres: backup and restore](https://www.postgresql.org/docs/current/backup.html) — read "SQL Dump" and "Continuous Archiving"
- [pg_dump reference](https://www.postgresql.org/docs/current/app-pgdump.html) · [pg_restore](https://www.postgresql.org/docs/current/app-pgrestore.html)
- [restic documentation](https://restic.readthedocs.io/en/stable/) — the offsite tool my production script uses
- [Postgres PITR](https://www.postgresql.org/docs/current/continuous-archiving.html)
