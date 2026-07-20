# Deployment From Zero — my personal DevOps university

> **Who this is for:** me (Umesh), six months from now, having forgotten everything.
> **Promise:** if I read only these notes, I can deploy, run, monitor, back up, restore, upgrade, and debug my ERP **without** watching a single YouTube tutorial or copying a blog.
> **Rule of this course:** never a generic example. Every concept is explained on **my real ERP** — my Docker setup, my Caddy config, my Postgres, my production settings, my deploy scripts.

---

## How to use this folder

1. Read the chapters **in order, 01 → 42** — each builds on the last. (The two ⭐ files **00A/00B are decision references**, not lesson 1: skim them first for the *where-to-host* and *what-it-costs* call, then come back after Ch 16–21, once terms like Docker/Postgres/serverless click.)
2. Each chapter is self-contained and follows the **same 12-part format** (below), so you always know where to look.
3. Do the **Homework** in each chapter on the real VPS/containers — reading is not learning; running commands is.
4. When stuck in production later, jump straight to `39_Debugging_Production.md` and `38_Common_Production_Bugs.md`.

## The standard chapter format (every file has these headings)

1. **# Purpose** — why this topic exists.
2. **# The Problem** — what problem it solves.
3. **# Theory** — from first principles, assume zero prior knowledge.
4. **# Real World Example (My ERP)** — exactly where this appears in *this* project (file / container / env var / setting / script).
5. **# Visual Diagram** — ASCII diagram.
6. **# Practical — how to inspect it** — Linux / Docker / Django / Postgres / networking commands, **every command explained**.
7. **# Beginner Mistakes** — misunderstandings, production-killers, "never do this".
8. **# Interview Questions** — Junior / Mid / Senior / Staff, with answers.
9. **# Cheat Sheet** — quick summary, key commands, key files, key flow, things to remember.
10. **# My ERP Section** — the "where in my project" table (file/container/env/setting/script/service).
11. **# Homework** — small hands-on exercises.
12. **# Further Reading & Live Resources** — curated official docs + quality tutorials + live/interactive tools (real links).

---

## My ERP's production stack — the one picture to remember

Everything in this course is a piece of this diagram. Come back here whenever a term feels abstract.

```
   Worker phone / Owner laptop / Finance PC        (the public internet, HTTPS)
                        │
                        ▼   ports 80 (→redirect) + 443 (HTTPS)
              ┌───────────────────┐
              │       CADDY        │   reverse proxy: TLS certs (auto), static
              │  (deploy/Caddyfile)│   files, HTTP→HTTPS, buffering, limits
              └───────────────────┘
                        │   plain HTTP, PRIVATE docker network only
                        ▼   port 8000 (NOT exposed to internet)
              ┌───────────────────┐
              │      GUNICORN      │   WSGI app server, 3 sync workers
              │  (config.wsgi)     │   each = a full copy of Django
              └───────────────────┘
                    │            │
                    ▼            ▼
          ┌───────────────┐  ┌──────────────┐
          │  POSTGRESQL   │  │    REDIS     │   data of record  +  cache /
          │ (db service)  │  │(redis service)│  sessions / login rate-limiter
          └───────────────┘  └──────────────┘

   All four boxes = Docker containers, wired by docker-compose.yml,
   running on ONE rented Linux server (a VPS), behind its firewall.
   restic backs up Postgres nightly to off-site object storage.
```

**One-line summary:** *the internet talks only to Caddy; Caddy talks to Gunicorn; Gunicorn runs my Django app which talks to Postgres + Redis; all of it is containers on one Linux box; backups go off-site.*

> 📐 **The full picture, in depth:** [ARCHITECTURE.md](ARCHITECTURE.md) — the capstone reference: every container, the request lifecycle, the boot sequence, security boundaries, data/backup flow, failure-modes→recovery, the scaling path, and the "why we chose this" decision log. Read the chapters to learn each box; read ARCHITECTURE to see how they fit.

### Where each piece lives (master reference)
| Piece | In my project | Chapter |
|---|---|---|
| Reverse proxy | `deploy/Caddyfile` (Caddy container) | 11, 12 |
| App server | `gunicorn config.wsgi --workers 3` in `deploy/entrypoint.sh` | 14, 15 |
| Django app | `config/`, settings `config.settings.production` | 24 |
| Database | `db` container (PostgreSQL), `DATABASE_URL` env | 21 |
| Cache/rate-limit | `redis` container, `REDIS_URL` env | 22 |
| Container orchestration | `docker-compose.yml` | 16–20 |
| Secrets/config | `.env` (never committed) + `.env.example` | 23 |
| Static files | WhiteNoise + `collectstatic` at startup | 25, 26 |
| DB schema changes | `manage.py migrate` at startup | 27 |
| Backups | `deploy/backup.sh` (restic) | 28, 29 |
| Health/pre-deploy check | `manage.py verify_production` | 30, 35 |
| Logs | stdout (request-id + actor-tagged) | 31 |

---

## Curriculum (read in order)

> **This one folder (`docs/deployment_course/`) is the whole course — nothing lives anywhere else.** Every deployment concept for this project is here: the fundamentals, the machine, the web front, containers, data, operations, security, scaling, the *real* step-by-step deploy of THIS ERP, **plus where we can host it and what it costs (and the free/open substitutes).**

### ⭐ Decision references — skim first for the decision, understand fully after Ch 16–21
> These two name tools (Docker, Postgres, serverless, Kubernetes) taught later in the course. Skim now to make the *where/what-cost* decision; the deep understanding comes once you've read the container + data chapters. **The actual from-zero learning starts at [01](01_What_Is_Deployment.md).**
- [00A — Where Can We Deploy This ERP?](00A_Where_To_Deploy_Hosting_Options.md) — VPS vs PaaS vs serverless vs a box at the factory; the right pick + why.
- [00B — Deployment Costs & Free/Open-Source Alternatives](00B_Deployment_Costs_And_Free_Alternatives.md) — every paid piece, **why** you'd pay, real price, and the **free/self-hosted substitute** (deploy this ERP for ~$6/mo, or $0).

### Term 1 — Fundamentals (the ground under your feet)
- [01 — What Is Deployment](01_What_Is_Deployment.md) — runserver vs production, Gunicorn, reverse proxy, Caddy, the request journey.
- [02 — How The Internet Works](02_How_The_Internet_Works.md) — packets, clients/servers, requests, the trip from phone to VPS.
- [03 — HTTP & HTTPS](03_HTTP_HTTPS.md) — what a request/response actually is, headers, status codes, why HTTPS.
- [04 — DNS & Domains](04_DNS_Domains.md) — turning `erp.example.com` into your server's IP.
- [05 — IP Addresses & Ports](05_IP_Address_and_Ports.md) — public vs private IP, localhost, 80/443/8000, sockets.

### Term 2 — The machine
- [06 — Linux Basics](06_Linux_Basics.md) — Ubuntu, the shell, packages, why servers run Linux.
- [07 — SSH](07_SSH.md) — logging into the VPS safely, keys not passwords.
- [08 — The File System](08_File_System.md) — paths, permissions, where your app + data live.
- [09 — Processes & Services](09_Processes_and_Services.md) — what a running program is, ports, killing/monitoring.
- [10 — systemd](10_Systemd.md) — keeping things running + auto-start on boot (and why Docker changes this).

### Term 3 — The web front
- [11 — Reverse Proxy](11_Reverse_Proxy.md) — the concept, in depth.
- [12 — Caddy](12_Caddy.md) — my `deploy/Caddyfile` line by line, automatic HTTPS.
- [13 — Nginx Comparison](13_Nginx_Comparison.md) — the alternative, trade-offs, when you'd switch.
- [14 — Gunicorn](14_Gunicorn.md) — workers, threads, timeouts, how many for my box.
- [15 — WSGI & ASGI](15_WSGI_ASGI.md) — the Python-web contract, sync vs async, `config/wsgi.py`.

### Term 4 — Containers
- [16 — Docker](16_Docker.md) — containers vs VMs, images, the "works on my machine" cure.
- [17 — Dockerfile](17_Dockerfile.md) — my `Dockerfile` line by line.
- [18 — Docker Compose](18_Docker_Compose.md) — my `docker-compose.yml` service by service.
- [19 — Docker Networking](19_Docker_Networking.md) — how Caddy reaches Gunicorn reaches Postgres by name.
- [20 — Docker Volumes](20_Docker_Volumes.md) — why my Postgres data survives a container rebuild.

### Term 5 — Data
- [21 — PostgreSQL](21_PostgreSQL.md) — persistence, connections, `DATABASE_URL`, indexes, transactions.
- [22 — Redis](22_Redis.md) — cache, sessions, my login rate-limiter, why the app refuses to boot without it.
- [23 — Environment Variables](23_Environment_Variables.md) — `.env`, secrets, fail-fast config.
- [24 — Django Settings](24_Django_Settings.md) — base/local/production split, what changes and why.
- [25 — Static vs Media](25_Static_vs_Media.md) — CSS/JS vs user uploads, why they're different.
- [26 — collectstatic](26_collectstatic.md) — what it generates, WhiteNoise, the manifest.
- [27 — Migrations](27_Migrations.md) — schema changes safely, my 52 production migrations, zero-downtime rules.

### Term 6 — Keeping it alive
- [28 — Backups](28_Backups.md) — my `deploy/backup.sh`, restic, the 3-2-1 rule.
- [29 — Restore](29_Restore.md) — the drill you must rehearse before you need it.
- [30 — Monitoring](30_Monitoring.md) — is it up? is it healthy? `verify_production`.
- [31 — Logging](31_Logging.md) — my request-id + actor-tagged logs, reading them.
- [32 — Sentry](32_Sentry.md) — knowing about errors before the owner calls.

### Term 7 — Change & scale
- [33 — CI/CD](33_CI_CD.md) — deploy pipelines, rollback, blue-green, zero-downtime.
- [34 — Production Security](34_Production_Security.md) — HTTPS/CSRF/XSS/secrets/uploads/RBAC, the RC1 findings.
- [35 — Deployment Checklist](35_Deployment_Checklist.md) — the pre-flight list.
- [36 — My ERP Deployment](36_My_ERP_Deployment.md) — the real thing, every command, start to finish.
- [37 — Post Deployment](37_Post_Deployment.md) — the first hour, first day, first week.
- [38 — Common Production Bugs](38_Common_Production_Bugs.md) — the ones that will actually happen.
- [39 — Debugging Production](39_Debugging_Production.md) — a calm method when it's on fire.
- [40 — Disaster Recovery](40_Disaster_Recovery.md) — server gone, DB corrupt, what now.
- [41 — Scaling](41_Scaling.md) — when one box isn't enough, DB bottlenecks, caching.
- [42 — Final Deployment Playbook](42_Final_Playbook.md) — the one-page runbook that ties it all together.

---

## Prerequisites (what I already know, so we skip it)
Django development: models, services, views, transactions, RBAC, business logic. **Everything else — the OS, the network, containers, the proxy, TLS — this course teaches from zero.**

## Status of this course
✅ **COMPLETE — all 42 chapters + 00A/00B + [ARCHITECTURE.md](ARCHITECTURE.md) written** (46 files), each in the full 12-part format with ASCII diagrams, real ERP files, and live resource links. This overview is the map; each chapter is a full lesson; [42 — Final Deployment Playbook](42_Final_Playbook.md) is the one-page runbook that condenses everything.

*Next: start with [01 — What Is Deployment](01_What_Is_Deployment.md), or jump to [42 — Final Deployment Playbook](42_Final_Playbook.md) for the condensed runbook.*
