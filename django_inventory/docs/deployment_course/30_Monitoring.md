# 30 — Monitoring & Health Checks

> Part of [Deployment Course](00_COURSE_OVERVIEW.md). Prev: [29 — Restore & Recovery Drills](29_Restore.md). Next: [31 — Logging](31_Logging.md).

# Purpose
To know your site is **up and healthy** — and to be told *before* your users notice it isn't. This chapter covers health checks (the container-level ones already in my stack), the read-only **`verify_production`** invariant gate, uptime monitoring, and what to actually watch. Monitoring is how "it works on my machine" becomes "it works, and I'll know within a minute if it stops."

# The Problem
A deployed app can fail in ways a green `docker ps` won't show: the DB connection pool exhausts, Redis is down (rate-limiter off), a disk fills, a settlement total drifts, TLS expires, or the container is "running" but returning 500s. Without monitoring you find out from an angry factory owner. You need **automated, layered checks** + **alerts** so problems surface early.

# Theory (from zero)

### Liveness vs readiness (two different questions)
- **Liveness** — "is the process alive?" If not, restart it.
- **Readiness** — "can it serve real traffic *right now*?" (DB reachable, migrations applied, Redis up). A container can be live but not ready.
Docker/compose healthchecks + `depends_on: service_healthy` encode this: don't send traffic to a dependency until it reports healthy.

### Layers of monitoring (defense in depth)
1. **Container health** — Docker healthchecks per service; unhealthy → restart / block dependents.
2. **App health endpoint** — an HTTP route that checks DB + cache and returns 200/503 (see the honest gap below).
3. **Invariant / data checks** — beyond "up": is the *data* self-consistent? (`verify_production`).
4. **External uptime monitor** — a third party hitting your URL from outside (catches DNS/TLS/network/whole-box failures the box can't self-report).
5. **Resource + cert monitoring** — disk, RAM, CPU, TLS expiry, backup freshness.
6. **Error tracking** — exceptions with context ([Ch 32](32_Sentry.md)).

### The golden signals (what to watch)
Latency, traffic, **errors**, and **saturation** (Google SRE's four). For this ERP the highest-value few: HTTP 5xx rate, request latency, DB connections/CPU, disk free, Redis up, TLS days-to-expiry, and **"a successful backup in the last 26h"** ([Ch 28](28_Backups.md)).

### Alert on symptoms, not noise
Alert on user-visible symptoms (site down, 5xx spike, backup failed, cert expiring in 7 days), not on every transient blip. A pager that cries wolf gets ignored.

# Real World Example (My ERP)
- **Container healthchecks (real, in `docker-compose.yml`):** `db` → `pg_isready -U $POSTGRES_USER -d $POSTGRES_DB` (every 5s); `redis` → `redis-cli ping`. **`app` waits `depends_on: {db: service_healthy, redis: service_healthy}`** so Gunicorn only starts once its dependencies are ready ([Ch 18](18_Docker_Compose.md)). Caddy front-ends the app.
- **`verify_production` (real management command):** the **read-only, production-safe** invariant gate (VER-D3 — "SELECT/aggregate + settings/migration introspection; no request cycle, no writes; runs everywhere"). Its checks: **dev-contamination**, **flags-vs-declaration** (enforcement flags match what's declared), **migrations-consistency** (no drift), **settings-sanity** (DEBUG off etc.), **settlement-items-sum**, **ledger-reversals-net**, ledger/`WorkerStageContribution` **CheckConstraint** verification, and **supersession-chain** integrity. Red check → non-zero exit → deploy gate fails ("the engine never fixes"). This is *data*-level health, run pre/post deploy.
- **Entrypoint readiness:** the boot script waits for db + redis to answer before migrating/serving ([Ch 09](09_Processes_and_Services.md)) — app-level readiness on top of the compose healthchecks.
- **Fail-fast as monitoring:** the app refuses to boot without `REDIS_URL`/`SECRET_KEY` ([Ch 22](22_Redis.md)/[Ch 23](23_Environment_Variables.md)) — a misconfig is a loud crash, not a silent degrade.
- **Backup failure signal:** `deploy/backup.sh` logs `FAILED — investigate` on a bad run ([Ch 28](28_Backups.md)) — the hook an uptime/log alert should watch.
- **Honest gaps (registered, not hidden):** (1) **no dedicated HTTP health endpoint** yet (`/healthz`) and (2) **no external uptime monitor / metrics stack** wired. For a single-VPS v1 these are acceptable-but-tracked; the recommended first adds are below. (Reporting gaps honestly is the project rule — never mark clean on no-findings.)

### Recommended additions (cheap, high value — mostly free, [00B](00B_Deployment_Costs_And_Free_Alternatives.md))
- **`/healthz` endpoint**: a tiny view that does `SELECT 1` + `cache.set/get` and returns 200/503; add an `app` compose healthcheck (`wget -qO- localhost:8000/healthz`) so "running but broken" is caught.
- **External uptime monitor**: UptimeRobot / BetterStack free tier hitting `https://<domain>/healthz` every 1–5 min → email/Telegram on down.
- **Backup-freshness alert**: alert if no `[backup] done` / no new restic snapshot in 26h.
- **Resource + cert**: node exporter / a simple cron mailing `df -h` + `restic snapshots`; Caddy auto-renews TLS but monitor days-to-expiry anyway.

# Visual Diagram
```
  EXTERNAL monitor (UptimeRobot/BetterStack) ──GET /healthz every 1-5m──► catches DNS/TLS/box-down
        │ alert on DOWN
  ┌─────▼──────────────────────────────────────────────────────────┐
  │ Caddy ─► app (gunicorn)   [RECOMMEND: /healthz → SELECT 1 + cache]│
  │ compose healthchecks: db(pg_isready 5s) · redis(redis-cli ping)  │  ← liveness/readiness
  │ app depends_on service_healthy(db,redis)  → won't start early     │
  └───────────────────────────────────────────────────────────────┘
  DATA health:  verify_production (read-only) → dev-contam · flags · migrations ·
                settings-sanity · settlement-sum · ledger-net · constraints · supersession
  OPS signals:  backup "done" < 26h · disk free · TLS days-left · fail-fast boot crash
  Golden signals: latency · traffic · ERRORS(5xx) · SATURATION(db conns/CPU/disk)
  [GAPS tracked: no /healthz yet · no external monitor yet]
```

# Practical — how to inspect it
```bash
docker compose ps                                   # State + Health per service (healthy/unhealthy)
docker inspect --format '{{.State.Health.Status}}' $(docker compose ps -q db)   # db health
docker compose exec app python manage.py verify_production   # read-only invariant gate (0 = pass)
```
```bash
# Resource + cert + backup freshness (the ops signals)
df -h /                                              # disk free (a full disk breaks Postgres + backups)
docker stats --no-stream                             # per-container CPU/RAM
docker compose exec backup restic snapshots | tail   # last off-site snapshot age (< 26h?)
echo | openssl s_client -connect <domain>:443 2>/dev/null | openssl x509 -noout -enddate   # TLS expiry
```
```bash
# (After adding it) prove the health endpoint
curl -sf https://<domain>/healthz && echo OK        # 200 = DB+cache reachable; 503 = degraded
```

# Beginner Mistakes
- **`docker ps` = "it's fine"** → a container can be "running" while returning 500s. Check *health*, not just *up*.
- **No external monitor** → the box can't tell you it's unreachable (DNS/TLS/network/dead box). Monitor from outside.
- **Only liveness, no readiness** → traffic hits an app whose DB isn't ready → errors. Use `service_healthy` + a readiness endpoint.
- **Monitoring "up" but not the data** → the site's up but a settlement total is wrong. `verify_production` catches invariant breaks.
- **Alert fatigue** → paging on every blip trains you to ignore alerts. Alert on symptoms.
- **Forgetting backup-freshness + disk + TLS** → silent backup stop, full disk, expired cert = outages you could've predicted.
- **No health endpoint at all** (my current gap) → add `/healthz`; don't leave "running but broken" invisible.

# Interview Questions
**Junior — "Liveness vs readiness?"** Liveness = is the process alive (else restart); readiness = can it serve traffic now (DB/cache reachable). A container can be live but not ready.

**Mid — "What health checks does this stack have and what's missing?"** Compose healthchecks on `db` (`pg_isready`) and `redis` (`redis-cli ping`), with `app` gated on `service_healthy`; a read-only `verify_production` invariant gate for data health. Missing (tracked): an HTTP `/healthz` endpoint and an external uptime monitor — the recommended first adds.

**Senior — "Beyond 'is it up', how do you know the ERP is *healthy*?"** `verify_production` asserts data-level invariants (no dev contamination, migrations consistent, settlement sums, ledger nets to zero, DB CheckConstraints hold, supersession chains intact) read-only — so a settlement/ledger drift is caught even when the site responds 200. Combined with golden-signal metrics (5xx rate, latency, DB saturation) and backup-freshness, "healthy" means both serving *and* internally consistent.

**Staff — "Design monitoring for this single-VPS ERP: what, how, and what would you add first?"** Layer it: container healthchecks (have) → `/healthz` readiness (add) → external uptime monitor from outside the box (add) → golden signals (5xx/latency/saturation) via a lightweight exporter → data invariants via `verify_production` on a schedule → ops signals (disk, TLS expiry, backup < 26h). Alert on symptoms (down, 5xx spike, backup failed, cert < 7d), route to one channel, keep it low-noise. First adds (cheap, high ROI): `/healthz` + a free external monitor + a backup-freshness alert — because they catch the failures most likely to hurt (whole-box down, running-but-broken, silent backup stop). Scale later to Prometheus/Grafana + alertmanager if the estate grows.

# Cheat Sheet
- **Liveness** (alive?) vs **readiness** (can serve?). Compose: `db`=`pg_isready`, `redis`=`redis-cli ping`, `app` waits `service_healthy`.
- **`verify_production`** = read-only *data* invariant gate (dev-contam, migrations, settlement sum, ledger net, constraints, supersession). 0 = pass.
- **Watch:** 5xx rate, latency, DB conns/CPU, **disk free**, Redis up, **TLS expiry**, **backup < 26h**.
- **Add first (cheap/free):** `/healthz` (SELECT 1 + cache) + `app` healthcheck; external uptime monitor; backup-freshness alert.
- **Alert on symptoms**, from **outside** the box. `docker ps` ≠ healthy.
- **Gaps tracked honestly:** no `/healthz`, no external monitor yet.

# My ERP Section
| Layer | In my ERP |
|---|---|
| Container health | `db` `pg_isready` (5s), `redis` `redis-cli ping` |
| Readiness gating | `app` `depends_on: service_healthy` + entrypoint wait-loop |
| Data invariants | `verify_production` (read-only, 8+ checks, deploy gate) |
| Fail-fast | boot crash on missing `SECRET_KEY`/`REDIS_URL` |
| Backup signal | `backup.sh` logs `FAILED` / `done` |
| HTTP health endpoint | **gap — add `/healthz`** |
| External uptime monitor | **gap — add free monitor** |

# Homework
1. `docker compose ps` — which services report a Health status, and which only "running"? Why do `db`/`redis` have healthchecks but `app` relies on `depends_on`?
2. Run `verify_production` — list the invariants it checks. Which are *data* health vs *config* health?
3. `df -h /` and `restic snapshots | tail` — is disk healthy and is there a snapshot < 26h old? Why do both matter?
4. Sketch a `/healthz` view: what two dependencies should it check, and what status codes should it return?
5. Pick a free external uptime monitor; what URL would it hit and how often? What failure classes does it catch that the box can't self-report?

---

## Further Reading & Live Resources
- Google SRE Book — *Monitoring Distributed Systems* (the four golden signals): https://sre.google/sre-book/monitoring-distributed-systems/
- Docker docs — *HEALTHCHECK / compose healthcheck*: https://docs.docker.com/reference/dockerfile/#healthcheck · https://docs.docker.com/compose/compose-file/05-services/#healthcheck
- Django — *health-check patterns* (`django-health-check`): https://github.com/revsys/django-health-check
- UptimeRobot (free external monitor): https://uptimerobot.com/ · BetterStack: https://betterstack.com/uptime
- Prometheus (metrics, when you outgrow the basics): https://prometheus.io/docs/introduction/overview/
