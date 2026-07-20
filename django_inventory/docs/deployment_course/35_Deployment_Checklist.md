# 35 — The Deployment Checklist

> Part of [Deployment Course](00_COURSE_OVERVIEW.md). Prev: [34 — Production Security](34_Production_Security.md). Next: [36 — Deploying My ERP (step by step)](36_My_ERP_Deployment.md).

# Purpose
A single, runnable **pre-flight → go-live → post-deploy** checklist that gathers everything from the course into one page you tick through before every release. A pilot doesn't fly from memory; neither should you deploy from memory. This is the list that turns a nervous deploy into a boring one.

# The Problem
Deploys fail on the *forgotten* step, not the hard one: DEBUG left on, `.env` missing a var, no backup taken before a migration, static not collected, TLS not ready, no rollback plan. Under pressure you *will* forget. A checklist externalizes memory so nothing load-bearing is skipped — and gives you a defined stop/go at each phase.

# Theory (from zero)

### Why checklists (not skill) prevent outages
Deploys are high-consequence and repetitive — exactly where a written checklist beats expertise (Gawande's *Checklist Manifesto*: even experts miss steps under load). The value is the **discipline**, not the difficulty.

### Three phases, each with a gate
1. **Pre-flight** (before touching prod) — code green, config ready, backup fresh, rollback known.
2. **Go-live** (the switch) — the ordered deploy: backup → pull → build → up (migrate + collectstatic) → verify.
3. **Post-deploy** (prove it) — smoke test, invariants, backup landed, monitoring green, watch logs.
A **stop** at any failed gate: do not proceed to the next phase.

### First deploy vs update deploy
The **first** deploy also does one-time setup (VPS, firewall, DNS, `.env` creation, superuser, data decision) — that's [Ch 36](36_My_ERP_Deployment.md). **Update** deploys are the repeatable `deploy.sh` path. This checklist covers both; first-time-only items are marked ⭐.

# The Checklist

### A. Pre-flight (local / before prod)
```
[ ] Code is the certified release, git-tagged (e.g. erp-v1.0.0); working tree clean
[ ] ruff clean            → env/bin/ruff check .
[ ] No migration drift    → manage.py makemigrations --check --dry-run
[ ] Full battery GREEN     → manage.py test   (1878, fresh DB, sequential)
[ ] Goldens intact        → ₹344.25 / ₹801 / ₹633 reproduce
[ ] verify_production passes (run in dev = rehearsal)
[ ] pre-commit gates pass  → ruff + ds-lint (no new inline design values)
[ ] .env.example covers every var the code reads (fail-fast vars present)
[ ] Rollback known: previous tag noted; predeploy dump path known
```

### B. Config / infra readiness (⭐ = first deploy only)
```
[ ] ⭐ VPS provisioned; ufw allows ONLY 22/80/443
[ ] ⭐ SSH key-only, password + root login disabled
[ ] ⭐ Docker + compose plugin installed
[ ] ⭐ DNS A record → VPS IP, propagated (dig +short <domain>)  BEFORE first `up` (TLS needs it)
[ ] .env present on VPS, chmod 600, NOT in git (git ls-files | grep -x .env → empty)
[ ]   DEBUG=False · ALLOWED_HOSTS=<domain> · CSRF_TRUSTED_ORIGINS=https://<domain>
[ ]   SECRET_KEY set (strong, unique) · DATABASE_URL · REDIS_URL · POSTGRES_* 
[ ]   RESTIC_REPOSITORY + RESTIC_PASSWORD set; .env copy in password manager (DR pair)
[ ] DJANGO_SETTINGS_MODULE=config.settings.production (Dockerfile pins it)
```

### C. Go-live (the switch — deploy.sh order)
```
[ ] ① Pre-deploy pg_dump taken (rollback anchor)        ← deploy.sh does this FIRST
[ ] ② git pull --ff-only to the certified tag
[ ] ③ docker compose build app
[ ] ④ docker compose up -d   → entrypoint: wait db+redis healthy → migrate → collectstatic → gunicorn
[ ] ⑤ docker image prune -f
[ ] ⭐ createsuperuser (first deploy only)
[ ] ⭐ data decision: clean start vs dev dump (owner call)
```

### D. Post-deploy (prove it live)
```
[ ] TLS valid: https:// loads, http:// 301→https, HSTS header present
[ ] Smoke test: login · dashboard · a worker report · a settlement page · one media file loads
[ ] verify_production (in the container) → 0 red checks
[ ] No 5xx in logs: docker compose logs --since 10m app | grep -i error
[ ] Health: docker compose ps → db/redis healthy; app serving
[ ] check --deploy → Django hardening flags satisfied
[ ] First backup landed: docker compose logs backup → "[backup] done"; restic snapshots shows it
[ ] ⭐ Restore drill scheduled (prove backups restore — Ch29)
[ ] Monitoring/alerts on (or gap noted): uptime, backup-freshness, disk, TLS expiry
```

### E. Rollback (if any gate fails)
```
[ ] Bad release  → git checkout <previous tag> && sh deploy/deploy.sh
[ ] Bad migration → restore predeploy-STAMP.dump (Ch29: stop app → pg_restore --clean → start app)
[ ] Confirm rollback with the same smoke test + verify_production
```

# Real World Example (My ERP)
- **Pre-flight numbers are concrete:** battery **1878** green (fresh-DB, sequential), goldens **₹344.25 / ₹801 / ₹633** (+ historical ₹225 refusal pinned), PRIMARY dev-DB sentinel **170 rows / Σ₹10,880.25** — these are the "known truth" you assert.
- **Config gates map to real vars:** the 21-var `.env.example`; fail-fast on `SECRET_KEY`/`REDIS_URL`/`CSRF_TRUSTED_ORIGINS` means a missing one crashes at boot (a gate that enforces itself, [Ch 23](23_Environment_Variables.md)).
- **Go-live IS `deploy/deploy.sh`** — the order (dump → pull → build → up → prune → smoke) is exactly this checklist's section C ([Ch 33](33_CI_CD.md)).
- **Post-deploy gate = `verify_production`** (read-only invariants) + the smoke set ([Ch 30](30_Monitoring.md)); backup confirmation = `[backup] done` + `restic snapshots` ([Ch 28](28_Backups.md)).
- **Enforcement flags stay OFF:** `ENFORCE_ALLOCATION_BOUND` / `ENFORCE_SETTLEMENT_RECONCILIATION` ship **False**, flipped only after a soak ([Ch 27](27_Migrations.md)) — a deliberate checklist item, not an afterthought.
- **Known gaps to note (not silently skip):** `/healthz` + external monitor + Sentry not yet wired ([Ch 30](30_Monitoring.md)/[Ch 32](32_Sentry.md)) — the honest "monitoring on or gap noted" box.

# Visual Diagram
```
  A PRE-FLIGHT ──gate──► B CONFIG/INFRA ──gate──► C GO-LIVE ──gate──► D POST-DEPLOY
  code green,            .env+DNS+VPS               dump→pull→build→up      smoke+verify_production
  tests 1878,            firewall, TLS-ready        (migrate+collectstatic) backup landed, logs clean
  rollback known         DR pair in pw manager      prune                   monitoring/gaps noted
        │                      │                        │                        │
        └── STOP if red ───────┴──── STOP if red ───────┴──── STOP if red ───────┘
                                  E ROLLBACK (any failure):
                    bad release → checkout prev tag + deploy.sh
                    bad migration → restore predeploy dump (Ch29)
  ⭐ first-deploy-only: VPS/firewall/DNS/.env-create/superuser/data-decision/restore-drill
```

# Practical — run the gates
```bash
# A. Pre-flight (local)
env/bin/ruff check . && \
env/bin/python config/manage.py makemigrations --check --dry-run && \
env/bin/python config/manage.py test && \
env/bin/python config/manage.py verify_production
```
```bash
# C+D. On the VPS: deploy, then prove
sh deploy/deploy.sh
docker compose exec app python manage.py verify_production
docker compose exec app python manage.py check --deploy
curl -sI https://<domain> | grep -i strict-transport-security
docker compose logs backup | grep -i done
```

# Beginner Mistakes
- **Deploying without a fresh backup** → a bad migrate is unrecoverable. Section C-① is first for a reason.
- **Skipping the DNS-before-`up`** step (⭐) → Caddy can't get a cert → no HTTPS. DNS must resolve first ([Ch 12](12_Caddy.md)).
- **Not verifying post-deploy** → "it deployed" ≠ "it works". Run the smoke set + `verify_production`.
- **No rollback noted** → panic on failure. Write the previous tag + dump path *before* you deploy.
- **Forgetting the DR pair** (`.env` in a password manager) → backups you can't decrypt later ([Ch 28](28_Backups.md)).
- **Flipping enforcement flags on day one** → skip the soak. Ship them OFF.
- **Silently skipping a gap** → note it ("monitoring gap: no /healthz yet"), don't pretend it's done.

# Interview Questions
**Junior — "Why use a deployment checklist?"** Deploys fail on forgotten steps, not hard ones; a checklist externalizes memory so nothing critical (backup, DEBUG off, migrate, verify) is skipped under pressure.

**Mid — "Walk me through your go-live order and why that order."** Pre-deploy `pg_dump` first (rollback anchor) → `git pull` the certified tag → build the image → `up` (entrypoint migrates + collects static) → prune → smoke + `verify_production`. Backup-first so any later step is recoverable; verify-last so you don't declare success blind.

**Senior — "What's on your post-deploy gate specifically, and why each?"** TLS/redirect/HSTS (transport works), smoke of login+report+settlement+media (real paths work), `verify_production` (data invariants intact), logs clean of 5xx (no runtime breakage), `check --deploy` (hardening on), and backup-landed (recoverable going forward). Each proves a different failure class; passing all is "actually live," not "container started."

**Staff — "How do you make the checklist self-enforcing rather than trust-based?"** Convert boxes into automated gates: CI runs pre-flight (lint/tests/migration-drift), fail-fast env vars turn config boxes into boot invariants, `deploy.sh` scripts the go-live order so it can't be reordered, and `verify_production` + smoke are a scripted post-deploy gate that fails the deploy on a red check. What can't be automated (DNS, DR-pair, data decision) stays an explicit ⭐ item with a verification command. The goal: the checklist is mostly *executed by machines*, and the human boxes are the few genuinely-judgment ones — with gaps *noted*, never silently skipped.

# Cheat Sheet
- **Three phases, each a gate:** Pre-flight (green + config + backup + rollback) → Go-live (dump→pull→build→up→verify) → Post-deploy (smoke + verify_production + backup landed).
- **Backup FIRST** (rollback anchor); **verify LAST** (don't declare blind).
- ⭐ first-deploy-only: VPS/firewall/DNS/`.env`-create/superuser/data-decision/restore-drill.
- **Assert known truth:** 1878 tests, goldens ₹344.25/₹801/₹633, sentinel 170/₹10,880.25.
- **Rollback:** bad release → prev tag + `deploy.sh`; bad migration → restore predeploy dump.
- **Enforcement flags OFF**; **note gaps** (no /healthz/monitor/Sentry) — never skip silently.

# My ERP Section
| Phase | Concrete gate in my ERP |
|---|---|
| Pre-flight | ruff · `makemigrations --check` · 1878 tests · goldens · verify_production |
| Config | 21-var `.env` (600, gitignored) · fail-fast vars · DNS · DR pair |
| Go-live | `deploy/deploy.sh` (dump→pull→build→up→prune→smoke) |
| Post-deploy | smoke set · verify_production · check --deploy · `[backup] done` |
| Flags | `ENFORCE_*` OFF until soak |
| Rollback | prev tag + `deploy.sh` / restore predeploy dump |
| Noted gaps | /healthz · external monitor · Sentry (not yet wired) |

# Homework
1. Copy sections A–E into a `DEPLOY_CHECKLIST.md` you actually tick. Which boxes are already automated (CI/fail-fast/deploy.sh) vs manual?
2. Run section A locally. Do all four commands pass? Record the test count + golden values as your "known truth."
3. Explain why C-① (pg_dump) is the *first* go-live step and D-last (verify) is the *last*.
4. For your first deploy, list every ⭐ item. Which one, if skipped, breaks TLS?
5. Write your rollback line for (a) a bad release and (b) a bad migration. Where is the predeploy dump?

---

## Further Reading & Live Resources
- Django docs — *Deployment checklist* (authoritative): https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/
- Atul Gawande — *The Checklist Manifesto* (why checklists beat memory): https://atulgawande.com/book/the-checklist-manifesto/
- Google SRE Workbook — *Canarying / safe releases*: https://sre.google/workbook/canarying-releases/
- 12factor — *Build, release, run* (V) + *Dev/prod parity* (X): https://12factor.net/build-release-run · https://12factor.net/dev-prod-parity
- DigitalOcean — *Django production deployment* (end-to-end reference): https://www.digitalocean.com/community/tutorials/how-to-set-up-django-with-postgres-nginx-and-gunicorn-on-ubuntu-22-04
