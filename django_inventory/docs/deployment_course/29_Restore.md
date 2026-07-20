# 29 — Restore & Recovery Drills

> Part of [Deployment Course](00_COURSE_OVERVIEW.md). Prev: [28 — Backups](28_Backups.md). Next: [30 — Monitoring & Health Checks](30_Monitoring.md).

# Purpose
To learn the half of backups that actually saves you: **getting the data back**. A backup you've never restored is a guess. This chapter is the step-by-step restore of my stack from a restic snapshot, plus the **recovery drill** that turns "I hope it works" into "I've done it."

# The Problem
The backup job runs nightly ([Ch 28](28_Backups.md)) — but on the day the disk dies or a bad migration corrupts data, can you actually rebuild? Restores fail for real reasons: wrong `pg_restore` flags, a missing `RESTIC_PASSWORD`, version mismatch, forgetting media, or a snapshot that was silently corrupt for weeks. The only way to know is to **rehearse** before you need it.

# Theory (from zero)

### Two restore scenarios
1. **Partial / logical** — the app is fine but data is wrong (bad migration, accidental delete). Restore the DB (or specific tables) from the latest good `pg_dump` into the running stack.
2. **Total loss** — the VPS is gone. Rebuild from zero on a new box: install Docker, clone repo, restore `.env` from the password manager, pull the restic repo, restore DB + media, `up`.

### The recovery objectives
- **RPO** (how much data you can lose) = backup interval = **≤ 24h** here ([Ch 28](28_Backups.md)).
- **RTO** (how long recovery takes) = how fast you can execute this runbook = target a few hours for total loss (mostly provisioning + download time).

### `restic restore` + `pg_restore`
- **`restic restore <snapshot> --target /path`** pulls a snapshot's files back (needs `RESTIC_REPOSITORY` + `RESTIC_PASSWORD`). `latest` = newest; or pick a snapshot ID from `restic snapshots`.
- **`pg_restore`** loads a custom-format (`-Fc`) dump into Postgres. `--clean --if-exists` drops existing objects first (for restoring over an existing DB); into a fresh empty DB you omit `--clean`.
- **Media** is just files — copy the restored `/media` tree back into the `media` volume.

### The golden rule: rehearse into scratch, assert, then trust
A drill restores the latest snapshot into a **throwaway** DB/stack and **asserts known truths** (row counts, a known settlement total) — never over production. My project has fixed sentinels for exactly this: the PRIMARY dev-DB sentinel (**170 rows / Σ₹10,880.25**) and golden settlements (**₹344.25 / ₹801 / ₹633**, + the historical ₹225). If a restore reproduces those numbers, it's real.

# Real World Example (My ERP)

### A) Partial restore — roll the DB back to last night (stack still up)
```bash
# 1. Pull the newest dump from off-site into the backup container
docker compose exec backup sh -c 'restic restore latest --target /restore --include /backups'
docker compose exec backup ls -lt /restore/backups            # find db-STAMP.dump
# 2. Restore it over the live DB (⚠ takes the app down briefly — stop app first)
docker compose stop app
docker compose exec backup sh -c 'pg_restore -h db -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists /restore/backups/db-STAMP.dump'
docker compose start app
```

### B) Total loss — rebuild on a new VPS
```bash
# 1. New box: install Docker + compose plugin (Ch16), clone the repo
git clone <repo> && cd django_inventory
# 2. Restore .env from the password manager (the DR pair — Ch23/Ch28); it carries RESTIC_* + DB creds
#    (place the file, chmod 600 .env)
# 3. Bring up ONLY db + backup (backup has restic + the repo creds from .env)
docker compose up -d db backup
# 4. Restore DB + media from off-site
docker compose exec backup sh -c 'restic restore latest --target /restore'      # /restore/backups + /restore/media
docker compose exec backup sh -c 'pg_restore -h db -U "$POSTGRES_USER" -d "$POSTGRES_DB" /restore/backups/db-*.dump'
docker compose exec backup sh -c 'cp -a /restore/media/. /media/'               # media volume mounted here
# 5. Bring up the rest; entrypoint runs migrate (no-op, schema already current) + collectstatic
docker compose up -d
```

### C) The drill (do this on a schedule, never on prod)
```bash
docker compose exec backup sh -c 'restic restore latest --target /drill'
# load into a SCRATCH db, then assert known truth:
#   SELECT count(*), sum(...) FROM ...  →  expect 170 / ₹10,880.25 (PRIMARY sentinel)
#   settlement goldens reproduce ₹344.25 / ₹801 / ₹633
# match ⇒ backup proven restorable; mismatch ⇒ backups are broken, fix NOW
```
- **Verify after any restore:** run `verify_production` + the sentinel/golden checks; confirm login, a worker report, and a settlement page render ([Ch 30](30_Monitoring.md)).
- **DR pair reminder:** without the `.env` (from the password manager) you can't decrypt the restic repo — step B-2 is non-negotiable ([Ch 28](28_Backups.md)).

# Visual Diagram
```
  PARTIAL (data wrong, box alive):
    restic restore latest --include /backups → pg_restore --clean over live DB (stop app first)

  TOTAL LOSS (box gone):
    new VPS → install Docker → clone repo → RESTORE .env (password manager!) →
    up db+backup → restic restore latest → pg_restore + cp media → up -d
                                  │
                                  └── needs BOTH: restic repo (data) + .env (RESTIC_PASSWORD)

  DRILL (scheduled, scratch only):
    restore latest → scratch DB → ASSERT 170/₹10,880.25 + goldens ₹344.25/₹801/₹633
    match ⇒ backups real | mismatch ⇒ FIX NOW
  RPO ≤ 24h (data loss window)   ·   RTO = how fast you run this runbook
```

# Practical — how to inspect it
```bash
docker compose exec backup restic snapshots        # pick the snapshot to restore (id + date)
docker compose exec backup restic restore latest --target /restore --dry-run   # preview (no writes)
```
```bash
# Verify a restored DB before trusting it
docker compose exec app python manage.py verify_production        # deploy-gate checks
docker compose exec app python manage.py shell -c "..."           # assert sentinel row-count / totals
```

# Beginner Mistakes
- **Never testing restore** → the #1 real backup failure. A backup is unproven until restored + asserted.
- **No `.env` copy off the box** → can't decrypt restic after total loss. Password manager, always ([Ch 28](28_Backups.md)).
- **`pg_restore` without stopping the app** → the app writes mid-restore → inconsistent state. Stop `app` first for a partial restore.
- **Restoring over prod to "test"** → you can destroy live data. Drills go to a scratch DB/stack.
- **Forgetting media** → DB restored but uploads missing. Restore `/media` too.
- **Version drift** → restoring a dump into a much older/newer Postgres. Keep the `backup`/`db` images version-aligned (both pinned 16.x).
- **No assertions** → "it restored" without checking numbers. Assert sentinels/goldens.

# Interview Questions
**Junior — "How do you restore a backup here?"** Use `restic restore` to pull the latest snapshot, then `pg_restore` the custom-format dump into Postgres and copy the media files back; verify the app comes up.

**Mid — "Partial vs total-loss restore — what differs?"** Partial: stack is alive, stop `app`, `pg_restore --clean` the latest dump over the live DB. Total loss: provision a new box, install Docker, clone repo, **restore `.env` from the password manager**, bring up db+backup, `restic restore`, `pg_restore` + copy media, then `up -d`.

**Senior — "What makes a backup 'proven', and how do you prove it here?"** A scheduled restore drill into a scratch DB that **asserts known truths** — my sentinels (170 rows / ₹10,880.25) and golden settlements (₹344.25/₹801/₹633). Matching numbers prove both data integrity and the whole restore path (repo access, decryption, pg_restore flags, media). Without assertions, "it restored" is meaningless.

**Staff — "Design the recovery program (RPO/RTO, drills, DR) for this ERP."** Define objectives: RPO ≤ 24h (nightly dumps; tighten with PITR if needed), RTO a few hours for total loss. Keep the DR pair (restic repo + `.env` in a password manager, plus a sealed offline copy). Automate a **monthly** restore drill into an isolated scratch stack that asserts sentinels/goldens and alerts on mismatch — so a broken backup is caught in days, not during a fire. Document the total-loss runbook (the B steps) and rehearse it at least once so RTO is measured, not guessed. Replicate the restic repo to a second region to remove the single-repo SPOF. The invariant: recovery is a *practiced procedure with assertions*, not a hope.

# Cheat Sheet
- **Restore = `restic restore latest` → `pg_restore -Fc` → copy `/media`.** Verify with sentinels/goldens.
- **Partial:** stop `app`, `pg_restore --clean --if-exists` over live DB, start `app`.
- **Total loss:** new box → Docker → repo → **`.env` from password manager** → up db+backup → restore → up -d.
- **Drill on a scratch DB**, assert **170 / ₹10,880.25** + **₹344.25/₹801/₹633**; never on prod.
- **RPO ≤ 24h; RTO = runbook speed.** Keep `backup`/`db` versions aligned. Restore media too.
- **A backup is unproven until a restore reproduces known numbers.**

# My ERP Section
| Concept | In my ERP |
|---|---|
| Restore tools | `restic restore` + `pg_restore -Fc` (backup container has both) |
| Partial | stop app → `pg_restore --clean` latest dump |
| Total loss | `.env` from password manager → restore repo → pg_restore + copy media |
| Drill assertions | sentinel 170/₹10,880.25 + goldens ₹344.25/₹801/₹633 |
| Post-restore verify | `verify_production` + login/report/settlement render |
| DR pair | restic repo + `.env` (password manager) |
| RPO / RTO | ≤ 24h / few hours (total loss) |

# Homework
1. `restic snapshots` then `restic restore latest --target /restore --dry-run` — what would come back? (dumps + media)
2. Write the exact `pg_restore` command for a partial restore over the live DB. Why stop `app` first?
3. List the total-loss steps from memory. Which single step fails if `.env` isn't in your password manager?
4. Design a scratch-DB drill: which sentinel numbers would you assert to prove the restore is real?
5. Define RPO and RTO for this stack. What change would cut RPO below 24h, and is it worth it?

---

## Further Reading & Live Resources
- restic — *Restoring from backup*: https://restic.readthedocs.io/en/stable/050_restore.html
- Postgres docs — *`pg_restore`*: https://www.postgresql.org/docs/current/app-pgrestore.html
- Google SRE Book — *Data Integrity: what you back up you must be able to restore*: https://sre.google/sre-book/data-integrity/
- Backblaze — *how to test your backups*: https://www.backblaze.com/blog/how-to-test-your-backups/
- Postgres wiki — *Backup & restore practices*: https://wiki.postgresql.org/wiki/Backup
