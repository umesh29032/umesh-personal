# 37 — Post-Deployment Operations (Day 2)

> Part of [Deployment Course](00_COURSE_OVERVIEW.md). Prev: [36 — Deploying My ERP](36_My_ERP_Deployment.md). Next: [38 — Common Production Bugs](38_Common_Production_Bugs.md).

# Purpose
Deploying is Day 1. **Keeping it running** is every day after — "Day 2 operations." This chapter is the routine of a live system: what to watch, how to ship updates safely, how to keep TLS/deps/backups fresh, and how to not let a healthy launch rot into an outage three weeks later.

# The Problem
A site that launched fine still fails later: the disk fills with logs, TLS silently expires, dependencies grow CVEs, backups quietly stop, an update deploy breaks something, or load creeps past capacity. None of these announce themselves. Day 2 ops is the discipline that catches slow decay before it becomes downtime.

# Theory (from zero)

### Day 1 vs Day 2
- **Day 1** — provisioning + first deploy ([Ch 36](36_My_ERP_Deployment.md)). One-time.
- **Day 2** — everything after: monitoring, updates, patching, backups, incidents, capacity. Forever. Most of a system's life is Day 2.

### The routine cadences
- **Continuous (automated):** monitoring + alerts ([Ch 30](30_Monitoring.md)), nightly backups ([Ch 28](28_Backups.md)), Caddy TLS auto-renewal, container `restart: unless-stopped`.
- **Per-release:** the `deploy.sh` update loop (dump → pull → build → up → verify).
- **Weekly:** glance at logs/errors, disk, backup freshness, restic weekly check.
- **Monthly:** dependency/CVE update + image rebuild, restore drill ([Ch 29](29_Restore.md)), review access/permissions.

### The update-deploy loop (the thing you'll do most)
Shipping a change to a *running* system is the common Day-2 action. It must be: backup-first, from a tag, scripted, verifiable, reversible — exactly `deploy/deploy.sh` ([Ch 33](33_CI_CD.md)). Never hand-edit files on the server; always go through git + the script so prod matches a known commit.

### Keeping the edges fresh (they decay silently)
- **TLS** — Caddy auto-renews (~30 days before expiry) as long as ports 80/443 are open and DNS still points at you; monitor days-to-expiry anyway ([Ch 12](12_Caddy.md)).
- **Dependencies** — pinned images/requirements don't self-update; you must rebuild to pick up CVE patches (`pip-audit`, base-image bumps) ([Ch 34](34_Production_Security.md)).
- **Backups** — verify they're *still running and restorable*, not just configured ([Ch 28](28_Backups.md)/[Ch 29](29_Restore.md)).
- **Disk** — logs, images, dumps accumulate; `docker image prune` (in `deploy.sh`) + bounded log driver + local-dump cap keep it bounded ([Ch 31](31_Logging.md)).

### Capacity watch
Track the golden signals over time ([Ch 30](30_Monitoring.md)); rising latency / DB connections / RAM is the early signal to tune or scale ([Ch 41](41_Scaling.md)) *before* users feel it.

# Real World Example (My ERP)
- **Update loop = `deploy/deploy.sh`:** on the VPS, `git`-tag the new certified release, then `sh deploy/deploy.sh` → pre-deploy `pg_dump` (rollback anchor) → `git pull --ff-only` → `docker compose build app` → `up -d` (entrypoint migrates + collects static) → `docker image prune -f` → smoke-check login/dashboard/media. **Rollback:** `git checkout <previous tag>` + rerun; bad migration → restore the predeploy dump ([Ch 29](29_Restore.md)).
- **Self-healing (already on):** `restart: unless-stopped` on every service + Docker enabled at boot → a crash or VPS reboot brings the stack back with no human ([Ch 10](10_Systemd.md)). The entrypoint re-waits for healthy DB+Redis each time.
- **TLS:** Caddy renews automatically; `caddy_data` volume persists the certs/account so renewals and restarts don't re-issue (avoids rate limits, [Ch 20](20_Docker_Volumes.md)).
- **Backups:** nightly at ~02:00 IST, weekly `restic check` (Sundays), local dumps capped at 3; watch for `[backup] done` vs `FAILED` ([Ch 28](28_Backups.md)).
- **Enforcement soak:** post-deploy is when the `ENFORCE_ALLOCATION_BOUND` / `ENFORCE_SETTLEMENT_RECONCILIATION` flags are observed OFF, then flipped after the soak window ([Ch 27](27_Migrations.md)) — a deliberate Day-2 milestone, not a Day-1 toggle.
- **Known Day-2 backlog (tracked honestly):** wire `/healthz` + external uptime monitor + Sentry ([Ch 30](30_Monitoring.md)/[Ch 32](32_Sentry.md)); add `pip-audit`/Dependabot; the S6 `reported_quantity` retirement is post-deploy soak-gated. These are recorded, not forgotten.

# Visual Diagram
```
  DAY 1 (once): Ch36 deploy ───────────────► DAY 2 (forever):
  ┌────────────────────────────────────────────────────────────────────┐
  │ CONTINUOUS: monitoring+alerts · nightly backup · Caddy TLS renew ·   │
  │             restart:unless-stopped (self-heal on crash/reboot)       │
  │ PER-RELEASE: deploy.sh  dump→pull(tag)→build→up(migrate+static)→smoke│
  │              rollback = prev tag + deploy.sh / restore predeploy dump│
  │ WEEKLY: logs+errors · disk (df -h) · backup freshness · restic check │
  │ MONTHLY: dep/CVE update + image rebuild · RESTORE DRILL · access rvw │
  └────────────────────────────────────────────────────────────────────┘
  edges decay silently: TLS · deps(CVEs) · backups(still restorable?) · disk(prune)
  capacity: watch latency/DB-conns/RAM trend → tune/scale BEFORE users feel it (Ch41)
```

# Practical — the Day-2 commands
```bash
# Ship an update (on the VPS)
git fetch --tags && git checkout <new-tag> && sh deploy/deploy.sh
docker compose exec app python manage.py verify_production      # post-deploy gate
```
```bash
# Weekly health glance
df -h /                                        # disk (logs/images/dumps creep)
docker compose ps                              # all healthy / serving
docker compose logs --since 168h app | grep -i error | tail
docker compose exec backup restic snapshots | tail            # backup < 26h? retention working?
echo | openssl s_client -connect erp.example.com:443 2>/dev/null | openssl x509 -noout -enddate  # TLS days left
```
```bash
# Monthly maintenance
pip-audit -r requirements.txt                  # CVEs in deps → bump + rebuild
docker compose build --pull app && docker compose up -d        # pick up base-image patches
# + run a restore drill into a scratch DB (Ch29) and assert goldens
```

# Beginner Mistakes
- **"It launched, I'm done."** → Day 2 is 99% of the lifetime. Set the cadences up front.
- **Hand-editing files on the server** → prod drifts from git; the next `deploy.sh` `git pull` conflicts or reverts it. Change via git + deploy.
- **Never updating dependencies** → CVEs accumulate on a "working" site. Monthly `pip-audit` + rebuild.
- **Assuming backups still run** → they silently stopped weeks ago. Check freshness + do restore drills.
- **Ignoring disk** → full disk breaks Postgres *and* backups. `df -h`, prune, bounded logs.
- **No rollback rehearsed** → first real rollback is during an incident. Know the two rollback paths cold.
- **Updating without a pre-deploy backup** → `deploy.sh` does it; don't bypass the script.
- **Flipping enforcement flags without the soak** → post-deploy is for *observing* first.

# Interview Questions
**Junior — "What's 'Day 2 operations'?"** Everything after the first deploy: monitoring, shipping updates, patching dependencies, verifying backups, handling incidents, watching capacity — the ongoing running of the system.

**Mid — "How do you ship an update to the running ERP safely?"** `deploy/deploy.sh`: take a pre-deploy DB dump (rollback anchor), `git pull` the new certified tag, rebuild the app image, `up -d` (entrypoint migrates + collects static), prune, then smoke test + `verify_production`. Rollback is the previous tag + rerun, or restore the dump.

**Senior — "What decays silently on a running site and how do you counter each?"** TLS (Caddy auto-renews; still monitor expiry), dependencies (pin + monthly `pip-audit` + rebuild for CVEs), backups (verify freshness + periodic restore drills, not just "configured"), and disk (prune images, bound logs, cap local dumps). Each is invisible until it causes an outage, so each gets a scheduled check.

**Staff — "Design the Day-2 operating rhythm for this single-operator ERP."** Automate the continuous layer (monitoring + alerts on down/5xx/backup-failed/cert<7d, nightly encrypted backups, self-healing restarts). Make releases boring: tag → `deploy.sh` (backup-first, verifiable, one-command rollback), gated by CI. Put the human work on a calendar: weekly (logs/disk/backup-freshness), monthly (dependency+image patching, a restore drill asserting goldens, an access review). Track the golden-signal trend to scale proactively. Close the known gaps (/healthz, external monitor, Sentry, pip-audit) since a solo operator can't eyeball logs 24/7 — automation *is* the second engineer. The invariant: nothing critical depends on someone remembering; it's automated or on a cadence with a verification command.

# Cheat Sheet
- **Day 2 = forever.** Continuous (monitor/backup/TLS-renew/self-heal) · per-release (`deploy.sh`) · weekly (logs/disk/backup) · monthly (deps/rebuild/restore-drill/access).
- **Update = `deploy.sh`** (dump→pull tag→build→up→prune→smoke). Rollback = prev tag / restore dump.
- **Self-heal:** `restart: unless-stopped` + Docker-on-boot. **TLS:** Caddy auto-renews (persist `caddy_data`).
- **Decays silently:** TLS · deps (CVEs) · backups (restorable?) · disk (prune). Check on a cadence.
- **Never hand-edit on the server** — go through git. **Watch capacity trend** → scale before pain ([Ch 41](41_Scaling.md)).
- **Soak** enforcement flags post-deploy before flipping.

# My ERP Section
| Cadence | Action in my ERP |
|---|---|
| Continuous | monitoring, nightly restic backup, Caddy TLS renew, `restart: unless-stopped` |
| Per-release | `deploy/deploy.sh` + `verify_production` |
| Weekly | `df -h`, logs, `restic snapshots`, restic check (auto Sun) |
| Monthly | `pip-audit` + `build --pull`, restore drill (goldens), access review |
| Rollback | prev tag + `deploy.sh` / restore predeploy dump |
| Milestone | soak → flip `ENFORCE_*`; S6 retirement (gated) |
| Tracked backlog | /healthz, external monitor, Sentry, pip-audit |

# Homework
1. Run the "weekly health glance" block. Is disk healthy, backup < 26h, TLS > 30 days out? Which would you alert on?
2. Do a dry update on a TEST stack with `deploy.sh`. Where's the rollback anchor created, and what are the two rollback paths?
3. Why must you change prod via git + `deploy.sh` rather than editing files on the server?
4. `pip-audit` your requirements. Any CVEs? What's the fix workflow (bump → rebuild → verify)?
5. Build a one-page Day-2 calendar (weekly/monthly) for yourself. Which items are automated vs manual, and which gap would you close first?

---

## Further Reading & Live Resources
- Google SRE Book — *Being On-Call* + *Emergency Response* (operating live systems): https://sre.google/sre-book/being-on-call/
- Google SRE Workbook — *Simple, reliable operations*: https://sre.google/workbook/table-of-contents/
- Caddy — *Automatic HTTPS / certificate renewal*: https://caddyserver.com/docs/automatic-https#renewal
- Docker docs — *`docker system prune` / managing disk*: https://docs.docker.com/config/pruning/
- pip-audit + Dependabot (keeping deps patched): https://pypi.org/project/pip-audit/ · https://docs.github.com/en/code-security/dependabot
