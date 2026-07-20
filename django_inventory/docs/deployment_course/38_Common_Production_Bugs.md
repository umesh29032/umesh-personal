# 38 — Common Production Bugs (that never appear in dev)

> Part of [Deployment Course](00_COURSE_OVERVIEW.md). Prev: [37 — Post-Deployment Operations](37_Post_Deployment.md). Next: [39 — Debugging Production](39_Debugging_Production.md).

# Purpose
A field guide to the bugs that **only show up in production** — the ones "works on my machine" can't catch — with each one's **signature**, **cause**, and **fix**. Recognizing the signature turns a 30-minute panic into a 30-second diagnosis.

# The Problem
Dev runs `DEBUG=True`, `runserver`, SQLite-or-loose-Postgres, no proxy, no HTTPS, one user, `ALLOWED_HOSTS=['*']`. Production is the opposite on every axis. So a class of bugs is **invisible until deploy**: config mismatches, proxy/TLS interactions, concurrency, and resource limits. Knowing them in advance means you deploy expecting them, not blindsided.

# Theory (from zero): the usual suspects (signature → cause → fix)

### 1. No CSS/JS — the "naked HTML" site
- **Signature:** site loads but unstyled; `/static/...` → 404.
- **Cause:** `collectstatic` didn't run, or `DEBUG=False` (so `runserver`-style auto-serving is off) with no WhiteNoise/`STATIC_ROOT`.
- **Fix:** ensure the entrypoint runs `collectstatic --noinput` + WhiteNoise is configured ([Ch 26](26_collectstatic.md)). Use `{% static %}`, never hardcoded paths.

### 2. `400 Bad Request` on every page
- **Signature:** blank 400 for all requests right after deploy.
- **Cause:** the Host header isn't in `ALLOWED_HOSTS` (empty/wrong domain) with `DEBUG=False`.
- **Fix:** set `ALLOWED_HOSTS` to your real domain via env ([Ch 24](24_Django_Settings.md)).

### 3. `403 CSRF verification failed` on POST/login
- **Signature:** GET works, any form POST → 403 "Referer/Origin" or CSRF error.
- **Cause:** `CSRF_TRUSTED_ORIGINS` missing your `https://domain`, or Django thinks the request is HTTP because it can't see it's behind TLS.
- **Fix:** set `CSRF_TRUSTED_ORIGINS=https://erp.example.com` + `SECURE_PROXY_SSL_HEADER` so Django trusts Caddy's `X-Forwarded-Proto` ([Ch 11](11_Reverse_Proxy.md)/[Ch 24](24_Django_Settings.md)).

### 4. Infinite redirect loop (`ERR_TOO_MANY_REDIRECTS`)
- **Signature:** browser gives up after many 301s.
- **Cause:** `SECURE_SSL_REDIRECT=True` but Django can't tell the request is already HTTPS (Caddy terminated TLS), so it redirects to HTTPS forever.
- **Fix:** set `SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO','https')` ([Ch 11](11_Reverse_Proxy.md)). The single most common proxy bug.

### 5. `502 Bad Gateway`
- **Signature:** Caddy returns 502.
- **Cause:** the app (Gunicorn) isn't up / crashed / still booting / worker timed out on a slow request.
- **Fix:** check `docker compose logs app`; ensure entrypoint finished (DB healthy, migrated); raise `--timeout` or move slow work off the request ([Ch 14](14_Gunicorn.md)).

### 6. DB connection exhaustion / leaks
- **Signature:** intermittent `too many connections` / `FATAL: sorry, too many clients`; slowdowns under load.
- **Cause:** each worker holds persistent connections (`conn_max_age`) × workers > Postgres `max_connections`; or a connection leak (e.g. the dev autoreloader — my real **H-3** fix set `conn_max_age=0` in `local.py`).
- **Fix:** size `conn_max_age` × workers under `max_connections`; add PgBouncer at scale ([Ch 21](21_PostgreSQL.md)/[Ch 41](41_Scaling.md)).

### 7. Media 404 / uploads vanish on deploy
- **Signature:** newly uploaded files 404; old uploads disappear after a rebuild.
- **Cause:** media not on a persistent volume, or `MEDIA_ROOT` nested in `STATIC_ROOT` (wiped by `collectstatic`).
- **Fix:** persistent `media` volume, separate roots ([Ch 20](20_Docker_Volumes.md)/[Ch 25](25_Static_vs_Media.md)).

### 8. Concurrency bugs — races, double-submit, deadlocks
- **Signature:** wrong totals under load, duplicate rows, occasional 500s that never reproduce in dev.
- **Cause:** dev has one user; prod has many concurrent requests hitting the same rows. Missing locks / non-atomic multi-row writes.
- **Fix:** `transaction.atomic` + `select_for_update` / advisory locks in the service layer (my stack uses advisory locks 5374 settlement / 5375 pool). This is exactly the class of my real **C-1** (layering-start atomic-hijack 500) and **C-2** (multi-lane worker-report 500) regressions found in the P19A audit — concurrency/edge paths that dev's single-user flow never exercised.

### 9. Timezone / datetime bugs
- **Signature:** times off by hours; "today" rolls over at the wrong moment; backup runs at the wrong time.
- **Cause:** container defaults to UTC; naive datetimes; assuming server local time.
- **Fix:** `USE_TZ=True`, store UTC, convert on display; be explicit about schedules (my `backup.sh` computes 02:00 IST as 20:30 UTC, [Ch 28](28_Backups.md)).

### 10. Out-of-memory (OOM) / worker killed
- **Signature:** workers restart, 502s under load, `dmesg` shows OOM-killer.
- **Cause:** too many workers × memory each on a small VPS, or a memory-heavy request.
- **Fix:** size workers to RAM (my stack: 3 sync workers on 2–4 GB), `--max-requests` to recycle workers, bump RAM ([Ch 14](14_Gunicorn.md)/[Ch 41](41_Scaling.md)).

### 11. `DEBUG=True` accidentally shipped
- **Signature:** a real traceback page shown to users on error.
- **Cause:** wrong settings module / env.
- **Fix:** `DEBUG=False` in `production.py`, pinned `DJANGO_SETTINGS_MODULE`, `check --deploy`, `verify_production` gate ([Ch 24](24_Django_Settings.md)/[Ch 30](30_Monitoring.md)).

### 12. Secret/config missing → boot crash (this one's *good*)
- **Signature:** app refuses to boot; log names the missing var.
- **Cause:** fail-fast var (`SECRET_KEY`/`REDIS_URL`/`CSRF_TRUSTED_ORIGINS`) unset.
- **Fix:** set it in `.env`. This is a *feature* — a loud crash beats a silent insecure boot ([Ch 23](23_Environment_Variables.md)).

# Real World Example (My ERP)
- **The concurrency class is real here:** the P19A Business Acceptance Audit found **C-1** (layering-start atomic-hijack → 500) and **C-2** (multi-lane worker-report → 500) — both **production-path/edge/concurrency** bugs that the single-user dev flow and even the test battery's happy paths didn't surface, which is exactly why they blocked the deploy until fixed. Classic "only in prod-like conditions."
- **The DB-leak class is real here:** **H-3** — the dev autoreloader leaked connections; the fix was `conn_max_age=0` in `local.py` (prod keeps 600). A textbook connection-lifecycle bug.
- **My stack pre-empts most config bugs:** `SECURE_PROXY_SSL_HEADER` set (no #3/#4), `ALLOWED_HOSTS`/`CSRF_TRUSTED_ORIGINS` from env (no #2/#3), WhiteNoise + entrypoint `collectstatic` (no #1), persistent `media` volume + separate roots (no #7), fail-fast vars (#12 by design), UTC-aware backup scheduling (#9). The certification suite + `verify_production` exist to catch the rest before users do.

# Visual Diagram
```
  DEV (DEBUG=True, runserver, 1 user, HOSTS=['*'], no proxy/TLS)
        │  deploy flips every axis ▼
  PROD (DEBUG=False, gunicorn, many users, real domain, Caddy TLS proxy)
  ─────────────────────────────────────────────────────────────────────
  CONFIG bugs:  no-CSS(collectstatic) · 400(ALLOWED_HOSTS) · 403(CSRF_TRUSTED) ·
                redirect-loop(SECURE_PROXY_SSL_HEADER) · DEBUG-shipped
  PROXY/TLS:    #3/#4 ← Django must trust X-Forwarded-Proto (Ch11)
  CONCURRENCY:  races/500s under load ← locks+atomic (my C-1/C-2) ← dev never sees
  RESOURCE:     DB conn exhaustion(H-3) · OOM · worker timeout(502)
  DATA/TIME:    media vanish(volume/roots) · timezone(UTC vs IST)
  FAIL-FAST:    missing secret → boot crash (GOOD — loud > silent-insecure)
```

# Practical — reproduce/diagnose the signatures
```bash
docker compose logs --since 30m app | grep -iE '400|403|500|csrf|allowed_host|redirect|timeout|too many'
docker compose exec app python manage.py check --deploy      # catches DEBUG/hosts/cookie/HSTS misconfig
curl -sI http://erp.example.com | grep -i location            # redirect loop? (should be one 301→https)
```
```bash
# Concurrency: hammer an endpoint to surface races (TEST stack)
seq 20 | xargs -P10 -I{} curl -s -o /dev/null -w "%{http_code}\n" https://<domain>/<hot-endpoint>
# DB connections in use vs limit
docker compose exec db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c \
  "SELECT count(*), (SELECT setting FROM pg_settings WHERE name='max_connections') FROM pg_stat_activity;"
```

# Beginner Mistakes
- **Testing only the happy path in dev** → misses concurrency + edge bugs (C-1/C-2). Test prod-like: many users, real proxy, `DEBUG=False`.
- **Turning `DEBUG=True` in prod to "see the error"** → leaks secrets to users. Read logs instead ([Ch 39](39_Debugging_Production.md)).
- **Blaming the app for a proxy bug** → #3/#4 are *config* (missing `SECURE_PROXY_SSL_HEADER`), not code.
- **Ignoring the fail-fast crash** → it's telling you exactly which var is missing. Set it.
- **Not load-testing before launch** → resource/concurrency bugs appear on day one with real users.
- **Assuming dev DB behavior = prod** → `conn_max_age`, isolation, connection limits differ (H-3).

# Interview Questions
**Junior — "Name two bugs that appear only in production."** No CSS (collectstatic/WhiteNoise not set up) and `400 Bad Request` (empty/wrong `ALLOWED_HOSTS` with `DEBUG=False`) — both invisible in dev where DEBUG is on and runserver auto-serves.

**Mid — "A site behind a proxy shows an infinite redirect loop. Diagnose it."** `SECURE_SSL_REDIRECT` is on but Django sees the (proxied) request as HTTP because TLS was terminated at Caddy, so it redirects to HTTPS endlessly. Fix: set `SECURE_PROXY_SSL_HEADER` so Django trusts `X-Forwarded-Proto` ([Ch 11](11_Reverse_Proxy.md)).

**Senior — "Why do concurrency bugs escape dev and the test suite, and how do you defend?"** Dev is single-user and tests often exercise happy paths, so races on shared rows (double-submit, interleaved multi-row writes) don't trigger. Defense: atomic transactions + row/advisory locks in the service layer, plus load/concurrency tests. My real C-1/C-2 500s were exactly this class — prod/edge concurrency paths — caught by an adversarial acceptance audit, not by normal dev use.

**Staff — "How do you systematically shrink the dev↔prod bug gap for this ERP?"** Minimize the axes that differ: run `DEBUG=False` + real settings in a staging env that mirrors prod (same images, proxy, Postgres, TLS), so config/proxy bugs surface pre-launch; enforce fail-fast config so misconfig crashes loudly; keep a full fresh-DB test battery + adversarial acceptance audits to hit concurrency/edge paths (the C-1/C-2 class); load-test hot endpoints; and gate deploys on `verify_production` + `check --deploy`. Track resource trends to pre-empt OOM/connection exhaustion. The strategy: make prod's conditions appear *before* users do, and make the remaining unknowns fail loudly and observably.

# Cheat Sheet
- **No CSS** → collectstatic/WhiteNoise ([Ch 26](26_collectstatic.md)). **400** → `ALLOWED_HOSTS`. **403 CSRF** → `CSRF_TRUSTED_ORIGINS` + proxy header.
- **Redirect loop** → `SECURE_PROXY_SSL_HEADER` ([Ch 11](11_Reverse_Proxy.md)). **502** → app down / worker timeout ([Ch 14](14_Gunicorn.md)).
- **`too many clients`** → `conn_max_age`×workers > `max_connections` / leak (H-3). **OOM** → workers×RAM.
- **Media vanish** → volume + separate roots ([Ch 25](25_Static_vs_Media.md)). **Timezone** → `USE_TZ`, store UTC.
- **Concurrency 500s** (my C-1/C-2) → atomic + locks; dev's 1 user never sees them.
- **Missing secret → boot crash = GOOD** (fail-fast). **Never** flip `DEBUG=True` in prod.

# My ERP Section
| Bug class | In my ERP |
|---|---|
| Concurrency 500s | **C-1** layering-start, **C-2** multi-lane report (P19A audit) |
| DB conn leak | **H-3** → `conn_max_age=0` in `local.py` |
| Proxy/TLS | pre-empted: `SECURE_PROXY_SSL_HEADER` set |
| 400/403 | pre-empted: `ALLOWED_HOSTS`/`CSRF_TRUSTED_ORIGINS` from env |
| No-CSS | pre-empted: WhiteNoise + entrypoint collectstatic |
| Media | pre-empted: persistent `media` volume, separate roots |
| Timezone | backup 02:00 IST = 20:30 UTC (explicit) |
| Guard | `verify_production` + `check --deploy` + fresh-DB battery |

# Homework
1. For each of the 12 signatures, write the one-line fix from memory. Which three are proxy/TLS-related?
2. Which bugs does `manage.py check --deploy` catch? Run it — are they all already fixed in `production.py`?
3. Explain why C-1/C-2 (concurrency 500s) escaped dev + the happy-path tests. How would you write a test that catches them?
4. Simulate the redirect loop: what setting removes it and why does Caddy make it necessary?
5. Compute a safe `conn_max_age` × workers for your Postgres `max_connections`. What happens if the product exceeds it?

---

## Further Reading & Live Resources
- Django docs — *Deployment checklist* (the config bugs, pre-empted): https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/
- Django docs — *`SECURE_PROXY_SSL_HEADER`* (redirect-loop fix): https://docs.djangoproject.com/en/5.0/ref/settings/#secure-proxy-ssl-header
- Django docs — *`ALLOWED_HOSTS`* + *CSRF `CSRF_TRUSTED_ORIGINS`*: https://docs.djangoproject.com/en/5.0/ref/settings/#allowed-hosts · https://docs.djangoproject.com/en/5.0/ref/settings/#csrf-trusted-origins
- Django docs — *Database connections / `CONN_MAX_AGE`*: https://docs.djangoproject.com/en/5.0/ref/databases/#persistent-connections
- Gunicorn — *worker timeouts / `--max-requests`*: https://docs.gunicorn.org/en/stable/settings.html
- Django docs — *`select_for_update` / transactions* (concurrency): https://docs.djangoproject.com/en/5.0/ref/models/querysets/#select-for-update
