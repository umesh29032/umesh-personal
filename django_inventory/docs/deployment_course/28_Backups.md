---
id: deploy-course-28-backups
type: lesson
status: active
owner: handwritten
scope: deployment, operations — this ERP shipped to a VPS
anchors: docker-compose.yml, deploy/entrypoint.sh, deploy/Caddyfile, deploy/backup.sh
verified: 2026-08-01
---

# 28 — Backups (pg_dump + restic, off-site)

> Part of [Deployment Course](00_COURSE_OVERVIEW.md). Prev: [27 — Migrations](27_Migrations.md). Next: [29 — Restore & Recovery Drills](29_Restore.md).

# Learning Objectives
By the end of this chapter you can:
- state what this project backs up and what it deliberately does not
- explain why off-site matters more than frequency
- verify a backup actually contains data
- design a retention policy you can defend

# Purpose
To understand how the factory's data survives *disasters* — not just container rebuilds, but disk failure, corruption, a fat-fingered `down -v`, or the whole VPS dying. This chapter walks my **real `deploy/backup.sh`** line by line: nightly `pg_dump` + media, encrypted off-site with **restic**, with retention and integrity checks.

# The Problem
A Docker volume ([Ch 20](20_Docker_Volumes.md)) protects `pgdata` against *container* deletion — but not against the disk dying, silent corruption, ransomware, an accidental `docker compose down -v`, or the VPS being terminated. Any of those loses the business. I need copies of the data **off the box**, **encrypted**, **automatic**, **retained over time**, and **proven restorable**. That's what the `backup` service does.

# Theory (from zero)

### What must be backed up (and what needn't)
- **Postgres** = the business truth (Addas, workers, settlements, money) → **YES**.
- **Media** = user uploads, irreplaceable, not in git → **YES** ([Ch 25](25_Static_vs_Media.md)).
- **Static / code** = in git, reproducible → **NO**.
- **Redis** = ephemeral cache/counters → **NO** ([Ch 22](22_Redis.md)).

### What a "dump" actually IS — open one and look
Before the tool, the artefact. A **database dump** is an ordinary **text file full of SQL
statements** that, when replayed, rebuilds the database from nothing. Not a photo of the
data — the **instructions to recreate it**. Two halves, always in this order:

**1. The shape** — `CREATE TABLE` statements, so the empty structure exists first:
```sql
CREATE TABLE public.accounts_user (
    id bigint NOT NULL,
    password character varying(128) NOT NULL,   -- the stored hash
    email character varying(254) NOT NULL,
    salary numeric(10,2)
);
```

**2. The contents** — a `COPY … FROM stdin` block, then one row per line, tab-separated:
```sql
COPY public.accounts_user (id, password, email, salary) FROM stdin;
1	pbkdf2_sha256$1000000$3ukT81…$etmD3r…=	umesh@example.com	1000.00
\.
```

Open any dump in a text editor and you can **read every row of your database**. That is the
whole point — and the whole danger (see *Security Considerations*).

The top of the file names the tool and version that made it, which is how you identify a
stray dump you find lying around:
```
-- PostgreSQL database dump
-- Dumped from database version 14.18 (Ubuntu 14.18-0ubuntu0.22.04.1)
-- Dumped by pg_dump version 14.18
```

**Reading a filename.** `mydb_backup_20250620.sql` decodes as `mydb` (which database) +
`backup` + `20250620` (**2025-06-20**, the date it was taken) + `.sql` (plain SQL text).
Dated filenames are convention, not magic: `pg_dump` writes whatever name you pass it, so
the date is only as honest as the person who typed it. Prefer letting a script stamp it
(`$(date +%F)`) over typing it by hand.

> 💡 **Samjho aise:** Dump = **ghar banane ki poori likhi hui vidhi** — pehle deewaar
> (`CREATE TABLE`), phir andar ka saaman (`COPY`). Photo nahi hai, **nuskha** hai. Isliye
> notepad mein khol ke saara data padha ja sakta hai — apna bhi, aur chori karne wale ka bhi.

### `pg_dump` (logical backup)
`pg_dump` exports the database as a restorable file. The **custom format** (`-Fc`) is compressed and lets `pg_restore` do selective/parallel restores. A logical dump is portable across minor version differences and easy to verify — ideal for a single-VPS deploy. (Contrast: physical/PITR backups via WAL archiving — more powerful, more complex; overkill here.)

### restic (encrypted, deduplicated, off-site)
**restic** is a backup tool that stores **encrypted**, **deduplicated**, **snapshotted** backups in a remote repository (Backblaze B2, Cloudflare R2, S3, …). Key properties:
- **Encrypted client-side** — the remote never sees plaintext; the `RESTIC_PASSWORD` is the only key.
- **Deduplicated** — unchanged data isn't re-uploaded → cheap daily snapshots.
- **Snapshots + retention** — `forget --keep-daily/weekly/monthly` prunes old ones on a schedule (grandfather-father-son).
- **Integrity-checkable** — `restic check` verifies the repo isn't corrupt.

### 3-2-1 & RPO
The classic rule: **3** copies, on **2** media, **1** off-site. My stack: live volume (1) + local dump staging (2) + off-site restic repo (off-site = the 1). **RPO** (Recovery Point Objective) = how much data you can afford to lose = the backup interval. Nightly → **RPO ≤ 24h**.

### The disaster-recovery *pair*
Off-site encrypted backups are useless if you can't decrypt them. The **two things** you need to rebuild from zero: the **restic repo** (the data) **+** the **`.env`** (holds `RESTIC_PASSWORD` + DB creds) kept in a **password manager** ([Ch 23](23_Environment_Variables.md)). Lose the password → backups are permanently unreadable. This is why `.env` lives in a password manager, not just on the (possibly dead) VPS.

> 💡 **Samjho aise:** Backup **recipe** hai, photo nahi — poora khana dobara banane ki likhi hui vidhi. Aur roz raat ko apne aap banti hai, **ghar se bahar** (offsite) rakhi jaati hai. Do cheez yaad rakho: (1) database ke saath **media** bhi, (2) `.env` ki chaabi **alag** jagah — warna data milega par taala nahi khulega.

# Real World Example (My ERP) — `deploy/backup.sh` walked
The `backup` service (`postgres:16.6-alpine`, so it has a matching `pg_dump`; restic added via one `apk add` at boot) runs `deploy/backup.sh` as a loop:
```sh
export PGPASSWORD="$POSTGRES_PASSWORD"          # auth pg_dump from .env (Ch23)
run_backup() {
  stamp=$(date +%Y%m%d-%H%M%S)
  pg_dump -h db -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc -f "/backups/db-$stamp.dump"   # ① logical dump, custom format
  ls -1t /backups/db-*.dump | tail -n +4 | xargs -r rm -f          # ② keep only 3 newest LOCAL dumps (offsite is the archive)
  restic backup /backups /media --tag nightly                       # ③ push dumps + media volume off-site, encrypted+deduped
  restic forget --tag nightly --keep-daily 7 --keep-weekly 4 --keep-monthly 6 --prune   # ④ retention: 7d/4w/6m
  [ "$(date +%u)" = "7" ] && restic check                           # ⑤ weekly (Sun) integrity verify
}
restic snapshots >/dev/null 2>&1 || restic init                     # ⑥ init repo on first run (no-op after)
while true; do  sleep <until 20:30 UTC = 02:00 IST>;  run_backup || echo "FAILED — investigate";  done   # ⑦ nightly loop
```
- **`db` connection:** over the private Docker network (`-h db`), not a published port ([Ch 19](19_Docker_Networking.md)); `media` mounted **read-only** (backup can't corrupt live uploads).
- **Off-site target:** `.env` `RESTIC_REPOSITORY` = Backblaze **B2** bucket (or Cloudflare **R2** via an `s3:` URI) + `RESTIC_PASSWORD` (⚠ *"NO reset, NO recovery: losing this = backups permanently unreadable"* — must be in the password manager).
- **Retention:** 7 daily + 4 weekly + 6 monthly snapshots, auto-pruned. **RPO ≤ 24h.**
- **Local hygiene:** only 3 newest `.dump` files kept on the box (off-site is the real archive) — bounds local disk.
- **Failure visibility:** a failed run logs `FAILED — investigate` (a hook for monitoring, [Ch 30](30_Monitoring.md)); the weekly `restic check` catches silent repo corruption.
- **Cost:** a few GB in B2/R2 ≈ well under $1/mo ([00B](00B_Deployment_Costs_And_Free_Alternatives.md)).

# Visual Diagram
```
  nightly 02:00 IST (backup service loop)
   ┌─────────────────────────────────────────────────────────────┐
   │ ① pg_dump -Fc  (db over private net) → /backups/db-STAMP.dump │
   │ ② keep 3 newest local dumps (rm older)                        │
   │ ③ restic backup /backups /media  ──encrypt+dedupe──►  OFF-SITE│───► B2 / R2
   │ ④ restic forget --keep 7d/4w/6m --prune                       │      (encrypted repo)
   │ ⑤ Sundays: restic check (integrity)                           │
   └─────────────────────────────────────────────────────────────┘
  media mounted :ro (can't corrupt live)   |   RPO ≤ 24h   |   3-2-1: live vol + local dump + off-site
  DR PAIR to rebuild:  restic repo  +  .env(RESTIC_PASSWORD) in a password manager  (lose pw ⇒ data unreadable)
```

# Practical — how to inspect it
```bash
docker compose logs backup | tail            # "[backup] done" / sleep countdown / FAILED
docker compose exec backup ls -lht /backups  # the (≤3) local dumps
```
```bash
# Query the off-site repo (needs .env creds in the backup container's env)
docker compose exec backup restic snapshots           # list off-site snapshots + dates
docker compose exec backup restic stats               # repo size (cost estimate — 00B)
docker compose exec backup restic check               # integrity (also auto weekly)
```
```bash
# Force an on-demand backup (don't wait for 02:00) — TEST/verify
docker compose exec backup sh -c '. /srv/backup.sh; run_backup'   # runs one cycle now
```

# Production Walkthrough
- `deploy/backup.sh` dumps Postgres and archives media, on a schedule. Both parts, because either alone is an incomplete restore (ch 25).
- Static is **not** backed up — it is regenerated by `collectstatic` (ch 26).
- `.env` is not in git, so it needs its own secure copy or a restore will stall on missing secrets (ch 23).
- Off-site is the point: a backup on the same disk dies with the disk.

# Debugging Guide
1. **Zero-byte or tiny dump file** — the dump failed but the file exists. Size-check every backup; a 0-byte file is the most dangerous kind because it looks like success. (The local `db.sh save` helper refuses these for exactly this reason.)
2. **`pg_dump: server version mismatch`** — client older than server. Dump from a matching version.
3. **Backup ran but nothing appeared** — cron environment differs from your shell; log the script's output to a file.
4. **Disk filling up** — retention is not being applied. Old backups are the usual cause of a full disk (ch 06).
5. **Restore fails on a "good" backup** — you never tested it. That is ch 29's whole argument.

# Performance Notes
- Dumps compete for I/O with live traffic; schedule them off-peak.
- Compression trades CPU for transfer size and is usually worth it.
- Many small media files make the archive step dominate total time.
- `pg_dump` takes a consistent snapshot; it does not block writers.

# Security Considerations
- **A backup is a complete copy of every worker's earnings, every receipt, every login record.** It deserves stronger protection than the server.
- Encrypt at rest and in transit; restrict who can read the backup location.
- Test restores in an isolated environment, never against production.
- A stolen backup is a full data breach even if the server was never touched.
- **Never commit a dump to git.** A dump is plaintext, so `git add` publishes every row —
  emails, password hashes, session keys, and any OAuth client secret sitting in
  `socialaccount_socialapp`. Worse, git history is **append-only**: deleting the file in a
  later commit leaves it fully readable in every earlier commit, so `git rm` alone is not a
  fix. Removing it for real means rewriting history (`git-filter-repo` + a force-push).
  Prevent instead — a `*.sql` / `*.dump` line in `.gitignore` costs nothing and closes the
  hole permanently. *(This repo learned it the hard way: two June-2025 dumps from an old
  practice app sat in public history. Audited — OAuth tables empty, hashes 1,000,000-iteration
  pbkdf2, sessions long expired, so exposure was mild — but the lesson stands.)*

# Architecture Decisions
- **Database and media together**, because the database stores paths and the disk stores bytes.
- **Script in the repository**, so the backup mechanism is reviewable and versioned.
- **Off-site copies**, because local redundancy does not survive the failure modes that actually happen.
- **Retention policy over infinite history** — cost and breach surface both grow with the archive.

# Best Practices
- Size-check and log every run.
- Keep at least one copy on different hardware, ideally a different provider.
- Write down the retention rule and enforce it in the script.
- Schedule a restore drill (ch 29). A backup you have not restored is a hypothesis.

# Beginner Mistakes
- **Treating the volume as a backup** → it dies with the disk/VPS. Off-site is mandatory ([Ch 20](20_Docker_Volumes.md)).
- **Losing `RESTIC_PASSWORD`** → backups are permanently undecryptable. Keep `.env` in a password manager (the DR pair).
- **Never testing restore** → an untested backup is a hope, not a backup. Rehearse it ([Ch 29](29_Restore.md)).
- **Backing up on the same disk/box only** → correlated failure. Off-site to another provider/region.
- **No retention** → either infinite cost or only last night (a corruption you notice late overwrites all good copies). Keep 7d/4w/6m.
- **No integrity check** → silent repo corruption discovered only when you desperately need it. Weekly `restic check`.
- **No failure alerting** → backups silently stop; you find out during a disaster. Watch the `FAILED` log line ([Ch 30](30_Monitoring.md)).
- **Backing up media read-write** → a buggy backup could mangle live uploads; mount `:ro`.
- **Committing the dump to git** → a `.sql` file is plaintext, so the repo now publishes every
  email and password hash, and history keeps it even after you delete the file. `.gitignore`
  `*.sql` from day one; keep dumps in a backup directory that git never sees.

# Interview Questions
- **Junior:** "What do you back up and how often?" — Postgres (the business data) and the media uploads, nightly, encrypted, to off-site storage — RPO ≤ 24h. Static/code aren't backed up (they're in git).

- **Mid:** "Why restic + off-site instead of just the Docker volume?" — The volume only survives container churn, not disk failure/corruption/VPS loss/`down -v`. restic stores encrypted, deduplicated snapshots off the box with retention and integrity checks, so a total-loss event is recoverable.

- **Senior:** "Walk me through your backup.sh and its safety properties." — Nightly loop: `pg_dump -Fc` over the private net → keep 3 local dumps → `restic backup` dumps+media (encrypted, deduped) off-site → `forget --keep 7d/4w/6m --prune` → weekly `restic check`. Media is mounted read-only so the job can't corrupt live data; failures log a `FAILED` line for alerting; the repo is client-side encrypted so the provider never sees plaintext. RPO ≤ 24h; 3-2-1 satisfied.

- **Staff:** "Assess this backup design's risks and how you'd harden it for a financial system." — Strengths: off-site, encrypted, deduped, retained, integrity-checked, cheap. Gaps/hardening: (1) RPO 24h means up to a day of settlements lost — add WAL archiving/PITR (or more frequent dumps) if that's unacceptable; (2) a single restic repo is a single point of failure — replicate to a second provider/region; (3) untested restores are the top real-world failure — schedule an automated periodic restore-drill into a scratch DB with row-count/settlement-total assertions; (4) the `RESTIC_PASSWORD` is a catastrophic single secret — escrow it in a password manager + a sealed offline copy; (5) alert on backup failure and on "no successful snapshot in 26h," not just log it. The invariant: backups are only real once a restore has been rehearsed and monitored.

### Why interviewers ask these — and the answer that separates levels

| Testing for | Weak answer | What lands |
|---|---|---|
| Do you know a backup is a *process*, not a file? | "We run pg_dump nightly." | Name **RPO/RTO** in numbers, say where it goes (off-site), how long it is kept, **and that you have restored it**. |
| Do you know what a DB dump leaves out? | "The database is backed up, so we're covered." | A dump has **no media files and no secrets**. Full recovery = dump **+** uploads **+** `.env` from a password manager. |
| Have you actually *done* a restore? | "It should work." | Describe the drill: restore into a **new** database, then verify with independent numbers (row counts, a known money total) — not just an exit code. |

**The killer follow-up:** *"When did you last restore from backup?"* — "Never" ends the topic. Rehearsing once is the cheapest seniority you can buy.
# Revision Notes
- Back up **database + media**. Static is regenerated (ch 26), so it is excluded.
- `.env` needs its own secure copy — it is not in git (ch 23).
- ⚠️ **Size-check every dump.** A 0-byte file looks like success and is the worst failure.
- Off-site beats frequent: local copies die with the disk.
- A backup is a full data breach if stolen — **encrypt it**.

# Cheat Sheet
- **Back up:** Postgres + media. **Skip:** static/code (git), Redis (ephemeral).
- **`pg_dump -Fc`** (compressed, restorable) → **restic** (encrypted + deduped + off-site) to **B2/R2**.
- **Retention:** `--keep-daily 7 --keep-weekly 4 --keep-monthly 6 --prune`. **RPO ≤ 24h.**
- **Weekly `restic check`**; media mounted **`:ro`**; only 3 local dumps kept.
- **DR pair = restic repo + `.env`(RESTIC_PASSWORD) in a password manager.** Lose password ⇒ data unreadable.
- **A backup isn't real until restore is tested** ([Ch 29](29_Restore.md)) + failures are alerted ([Ch 30](30_Monitoring.md)).

# My ERP Section
| Concept | In my ERP |
|---|---|
| Service | `backup` (`postgres:16.6-alpine` + restic), `deploy/backup.sh` |
| DB backup | `pg_dump -Fc` over private net (`-h db`) |
| Media | `restic backup /media` (mounted `:ro`) |
| Off-site | `RESTIC_REPOSITORY` = B2 (or R2 via `s3:`), encrypted |
| Schedule | nightly ~02:00 IST (20:30 UTC), RPO ≤ 24h |
| Retention | 7 daily / 4 weekly / 6 monthly, `--prune` |
| Integrity | weekly `restic check` (Sundays) |
| DR pair | restic repo + `.env` (RESTIC_PASSWORD) in password manager |

# Practice Tasks
1. **Read the code:** read `deploy/backup.sh` line by line. What exactly is included, and where does it go?
2. **Debug:** deliberately break the dump (wrong password), and check whether the script would have noticed.
3. **Design:** write a retention policy — daily/weekly/monthly counts — and justify each number.
4. **Architecture:** argue whether backups belong on the same provider as the server.

# Homework
1. `docker compose logs backup | tail` — is it sleeping until the next run or reporting `done`/`FAILED`?
2. `docker compose exec backup restic snapshots` — how many snapshots, and what's the oldest (retention working)?
3. Read `deploy/backup.sh` — why is `/media` mounted read-only, and why keep only 3 local dumps?
4. What are the *two* things you need to rebuild the ERP after the VPS is destroyed? Where does each live?
5. `restic stats` — estimate monthly storage cost from the repo size ([00B](00B_Deployment_Costs_And_Free_Alternatives.md)). What happens if you lose `RESTIC_PASSWORD`?

---

# Further Reading & Live Resources
- restic — *official docs* (backup, forget/prune, check): https://restic.readthedocs.io/en/stable/
- restic — *removing snapshots / retention policy*: https://restic.readthedocs.io/en/stable/060_forget.html
- Postgres docs — *`pg_dump`*: https://www.postgresql.org/docs/current/app-pgdump.html
- Backblaze B2 (cheap off-site target): https://www.backblaze.com/cloud-storage · Cloudflare R2: https://developers.cloudflare.com/r2/
- *3-2-1 backup rule* explained: https://www.backblaze.com/blog/the-3-2-1-backup-strategy/
