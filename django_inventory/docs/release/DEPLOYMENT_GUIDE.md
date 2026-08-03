---
id: release-deployment-guide
type: topic-canonical
status: active
owner: handwritten
scope: release-handbook
anchors: deploy/
verified: 2026-07-19
---

# Deployment Guide — ERP v1.0

> **Companion to** [deploy/README.md](../../deploy/README.md) (the terse ops
> runbook). That file tells you *what to type*; this one teaches *why each
> step exists and how it fails*. The stack was certified at RCP-8 and the
> restore path was drilled on the real database before v1.0 shipped.
> The complete zero-assumed-knowledge kit (per-step walkthrough, env
> reference, file annotations, verification, rollback, deployment-day
> checklist) = [DEPLOYMENT.md](../../DEPLOYMENT.md) (P19.5).

## The deployment architecture, and why it looks like this

```
 Internet ──443──▶ Caddy (auto-TLS) ──▶ gunicorn (Django app) ──▶ PostgreSQL 16.6
                       │                        │                      ▲
                       │ 80→443 redirect        └──────▶ Redis 7.4     │ nightly
                       ▼                                 (cache +      │ pg_dump
                  Let's Encrypt                          rate-limit)   │
                                                                        │
                                            backup container ── restic ─┴─▶ B2/R2 (offsite)
```

> **💡 Samjho aise:** ek hi VPS par 5 containers chalte hain. Caddy darwaza
> hai (HTTPS khud manage karta hai), gunicorn ke andar Django app hai,
> Postgres mein saara keemti data hai, Redis sirf cache + login-rate-limit ke
> counters rakhta hai, aur backup container roz raat ko dump lekar offsite
> (B2/R2) bhejta hai. **Din ke ant mein sirf 3 cheezein bachani hain: yeh git
> repo + bhara hua `.env` (password manager) + restic repo** — in teeno se
> poora system shoonya se wapas khada hota hai.

**Why a single VPS with Docker Compose?** One factory, one operator, tens of
users. A managed-Kubernetes footprint would add operational surface without
adding value. Compose gives pinned, reproducible containers with one file;
the runbook records config-level "future exits" (managed Postgres, S3 media)
if the business outgrows it.

**Why Caddy?** Automatic TLS. The single most common small-deploy failure is
an expired certificate; Caddy renews itself. The cost: **DNS must resolve
before first start** (see DNS below).

**Why Redis is mandatory, not optional?** The login rate-limiter stores its
counters in the Django cache. With per-process local memory under
multi-worker gunicorn, an attacker gets N× the budget — silently. So
production settings **crash on boot if `REDIS_URL` is unset**. That crash is
a feature.

## Prerequisites (owner-provisioned)

| What | Why | Common failure |
|---|---|---|
| VPS 2–4 GB, India region | users are in India; latency | undersized RAM → OOM during `docker build` |
| SSH-key-only + `ufw allow 22,80,443` | password SSH on a public box gets brute-forced within hours | forgetting to `ufw enable` |
| Docker + compose plugin | the whole stack is containers | old distro docker without the compose plugin — install from get.docker.com |
| DNS A record → VPS IP | Caddy proves domain ownership to Let's Encrypt at first boot | starting compose before DNS propagates → TLS fails; wait, then restart caddy |
| Filled `.env` | every secret lives here, nowhere else | see the next section — most first-deploy failures are .env failures |

## Environment variables and secrets — the fail-fast philosophy

Copy `.env.example` (21 variables) → `.env`, fill **every** value, then
**store the filled file in the password manager**. The `.env` + the restic
repository are the two halves of disaster recovery: with those two things and
this git repo you can rebuild the entire system from nothing.

> **💡 Samjho aise:** production settings ka usool hai — **"secret nahi mila
> to chup-chaap kamzor default mat lo, crash karo."** Isliye SECRET_KEY ya
> REDIS_URL missing ho to app boot hi nahi hota. Yeh irritating lag sakta
> hai, par iska matlab hai ki "galti se insecure production" is system mein
> ho hi nahi sakta. Crash ka message khud batata hai kya missing hai.

Why the settings are shaped this way:

- `DJANGO_SETTINGS_MODULE=config.settings.production` appears **twice** — in
  `.env` *and* baked into the Dockerfile. Belt and braces: a container can
  never accidentally boot with dev settings (`DEBUG=True`,
  `ALLOWED_HOSTS=['*']`). *Known edge:* running the app **outside** Docker on
  bare metal falls back to local settings if the variable is unset
  ([KNOWN_LIMITATIONS](KNOWN_LIMITATIONS.md) DEP-F1) — don't deploy bare-metal.
- `SECRET_KEY`, `REDIS_URL`, `CSRF_TRUSTED_ORIGINS` have **no defaults** in
  production settings. Missing value = boot crash with a clear message. We
  chose loud failure over silently-insecure defaults; proven live during
  release verification (a secretless clone refuses to run).
- `CSRF_TRUSTED_ORIGINS` exists because Django rejects HTTPS POSTs whose
  Origin header isn't trusted when running behind a TLS-terminating proxy.
  Symptom of forgetting it: **every form submit returns 403** while GETs work.
- `SECURE_PROXY_SSL_HEADER` is set because gunicorn sits behind Caddy;
  without it `SECURE_SSL_REDIRECT` loops forever. The flip side, and this is
  a security rule: **never expose gunicorn's port directly to the internet**
  — a client could then spoof `X-Forwarded-Proto` and fake HTTPS.

## What happens on `docker compose up -d --build`

The app container's entrypoint runs, in order — each step exists for a reason:

1. **Wait-loop for HEALTHY Postgres and Redis.** `depends_on` alone only
   orders *starts*, not *readiness*; without the loop, migrations race the
   database and the first boot flakes.
2. **`migrate --noinput`** — the schema converges from whatever state exists.
   Certified property: the full graph (186 migrations) applies cleanly from
   an empty database. Operational rule learned during certification
   (DAT-R1): if you ever reverse a single app's migration by hand, **finish
   with a plain global `migrate`** — Django cascades reversals across
   dependent apps and an app-scoped forward leaves the estate partial.
3. **`collectstatic --noinput`** — WhiteNoise serves static files from the
   app container itself (no nginx to configure or forget).
4. **gunicorn** starts.

Media files (pattern photos, advance receipts) live in a named Docker volume
and are **access-gated by Django views** — media URLs are not public files.

## First deployment (runbook steps 4–11, annotated)

1. `git clone` the repo, `cd` into it. Deploy from a **tag** (`erp-v1.0.0`),
   not a moving branch — the tag is the certified anchor and your rollback
   vocabulary.
2. Fill `.env` (above). Password manager. Really.
3. `docker compose up -d --build`; watch `docker compose logs -f app caddy`
   until you see gunicorn workers and a successful certificate issuance.
4. `docker compose exec app python manage.py createsuperuser`
5. **Owner data decision (one-time):** start CLEAN (re-enter master data —
   recommended; the dev database carries test rows and a `dev.*` user cast)
   OR import the dev dump via the restore procedure. Recorded as an explicit
   owner call — don't make it implicitly.
6. Smoke: login → dashboard → create a test Adda → upload a pattern photo →
   confirm anonymous access to a `/media/...` URL is refused → public
   homepage renders.
7. **`docker compose exec app python manage.py verify_production`** — the
   read-only correctness gate (engine checks migrations consistency, settings
   sanity, dev-contamination, money-table integrity). **A deploy is not done
   until this passes.** It exists so "it started" can never be confused with
   "it is correct".
8. Confirm the first nightly backup: `docker compose exec backup restic snapshots`.
9. **Run the restore drill once before handing out worker credentials** —
   a backup you have never restored is a hope, not a backup. The drill is in
   the [OPERATIONS_MANUAL](OPERATIONS_MANUAL.md); its core (dump → restore →
   sentinel check) was already proven on the real data at certification.

## Upgrades

```
./deploy/deploy.sh        # from the repo root on the VPS
```

Order and why: **pre-deploy `pg_dump` FIRST** (this dump is the rollback
anchor for the upgrade) → `git pull --ff-only` (ff-only = the server never
invents merge commits; history is decided in development) → build → `up -d`
(entrypoint re-migrates) → image prune. Then smoke + `verify_production`.

## Rollback — three separate levers, pick by failure class

| Failure | Lever | Why it's safe |
|---|---|---|
| Bad code, schema fine | `git checkout <previous tag>` → `./deploy/deploy.sh` (skip pull) | tags exist from v1.0.0 onward; images rebuild deterministically |
| Bad migration / bad data | restore the `predeploy-*.dump` taken automatically by deploy.sh, then roll code back | the exact `pg_restore` path was drilled on the real database at RCP-8 |
| Settlement-era emergency | `LEDGER_CREDIT_AT_ALLOCATION=True` in `.env` + restart | ADR-0007's tested rollback lever; a cross-era guard prevents double-credit in both directions. Don't touch without reading ADR-0007. |

The three enforcement flags (`LEDGER_CREDIT_AT_ALLOCATION`,
`ENFORCE_ALLOCATION_BOUND`, `ENFORCE_SETTLEMENT_RECONCILIATION`) all default
**OFF**. Enabling them post-soak follows
[../ENFORCEMENT_ROLLOUT_RUNBOOK_2026_06_14.md](../ENFORCEMENT_ROLLOUT_RUNBOOK_2026_06_14.md)
— never flip them casually; they change refusal behavior at money boundaries.

## Health checks and monitoring

What exists today: db/redis container healthchecks, structured request-id
logging to stdout (the platform collects it), a separate security log,
persisted audit rows for every money/permission mutation, and the
`verify_production` gate. What does **not** exist yet (accepted, temporary —
C2 record in the release log): error aggregation (Sentry hook is built, set
`SENTRY_DSN` + add `sentry-sdk` to activate), an app `/healthz` endpoint,
uptime probes, alerting. **Install that menu at or immediately after first
deploy** — it is all config-level work.
