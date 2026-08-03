---
id: deploy-course-36-my-erp-deployment
type: lesson
status: active
owner: handwritten
scope: deployment, operations — this ERP shipped to a VPS
anchors: docker-compose.yml, deploy/entrypoint.sh, deploy/Caddyfile, deploy/backup.sh
verified: 2026-08-01
---

# 36 — Deploying My ERP (step by step)

> Part of [Deployment Course](00_COURSE_OVERVIEW.md). Prev: [35 — The Deployment Checklist](35_Deployment_Checklist.md). Next: [37 — Post-Deployment Operations](37_Post_Deployment.md).

# Learning Objectives
By the end of this chapter you can:
- describe this exact deployment end to end, from your laptop to a worker's phone
- name every moving part and why it exists
- explain what is deliberately missing
- deploy it yourself following the written path

# Purpose
The capstone. Every concept in this course, applied end to end: from a bare VPS to my ERP live on HTTPS with backups running. This chapter mirrors the **real, certified runbook** (`DEPLOYMENT.md` + `deploy/README.md`, frozen at tag `erp-v1.0.0` = commit `90c1f2f3`) in teaching mode — what / why / success / failure at each step.

# The Problem
Every previous chapter taught one piece — DNS, TLS, Docker, Gunicorn, volumes, backups. A real deploy is those pieces **in the right order**, where one wrong sequence (firewall before allowing SSH, `up` before DNS) locks you out or breaks TLS. This is the single ordered path, done once, correctly.

# Theory (from zero): the shape of the deploy
Five containers on one VPS — `caddy → app → db + redis`, plus `backup` — started by one `docker compose up`. The order of the *setup* around it is what matters:
```
buy VPS → SSH keys → firewall → Docker → DNS → clone → .env → up → superuser → data → verify → backup → restore-drill
   host security first ─┘         │        └─ DNS BEFORE up (TLS needs it)     └─ prove it's live + recoverable
```
Two rules govern the whole thing (owner rules): **exact-pinned images** (`caddy:2.9.1`, `postgres:16.6-alpine`, `redis:7.4.2-alpine`, `python:3.10.16-slim`) and **never trust `depends_on` alone** — the entrypoint actively waits for healthy DB+Redis.

> 💡 **Samjho aise:** Yahan tak sab **auzaar** seekhe; yeh chapter **asli kaam** hai — hamari factory ka apna deploy, apni file ke saath. Baaki chapters theory the; yeh wo page hai jo aap us raat khologe jab sach mein server pe jaana hoga. Isi liye ismein andaaza nahi, **hamare repo ki asli command** likhi hain.

# Real World Example (My ERP) — the 13 steps
> Placeholders used throughout: server IP `203.0.113.10`, hostname `erp.example.com`. Replace with yours.

### Step 1 — Buy the VPS
Rent a small Ubuntu LTS server. **Spec:** 2–4 GB RAM (2 GB floor: 3 Gunicorn workers + Postgres + Redis + Caddy; 4 GB comfortable), **India region** (DO Bangalore / Vultr Mumbai — users are in India, lowest latency), SSH-key login chosen **at creation**.
```bash
ssh root@203.0.113.10 "uname -a && free -h"   # ✓ Ubuntu line + Mem: 2.0Gi+
```
*Fail:* 1 GB RAM → OOM under load; US/EU region → +200 ms per request.

### Step 2 — SSH key + disable password login ([Ch 07](07_SSH.md))
```bash
ssh-keygen -t ed25519 -C "kapil-erp-vps"      # on your LAPTOP; private half never leaves it
ssh-copy-id root@203.0.113.10                 # or paste .pub at VPS creation
```
Then on the server set in `/etc/ssh/sshd_config`: `PasswordAuthentication no` + `PermitRootLogin prohibit-password`, and `systemctl restart ssh`.
> ⚠️ Keep your current session open. Confirm a **new** session logs in with the key **before** disabling passwords — else you're locked out (use the provider's rescue console to recover).
```bash
ssh -o PubkeyAuthentication=no root@203.0.113.10   # ✓ "Permission denied (publickey)" = passwords dead
```

### Step 3 — Firewall (ufw) ([Ch 05](05_IP_Address_and_Ports.md))
Open only **22 / 80 / 443**; deny the rest.
```bash
ufw allow 22/tcp && ufw allow 80/tcp && ufw allow 443/tcp   # 22 FIRST
ufw enable                                                  # then enable
ufw status                                                  # ✓ three ALLOW lines, Status: active
```
> ⚠️ Allow 22 **before** `ufw enable` or you cut your own SSH. Port 80 is required (Let's Encrypt challenge + HTTP→HTTPS redirect). This is a second wall on top of "only Caddy publishes ports" ([Ch 19](19_Docker_Networking.md)).

### Step 4 — Install Docker + compose plugin ([Ch 16](16_Docker.md))
```bash
curl -fsSL https://get.docker.com | sh        # engine + `docker compose` plugin together
docker --version && docker compose version && systemctl is-enabled docker   # ✓ versions + "enabled"
```
`enabled` = Docker starts on boot, so `restart: unless-stopped` brings the stack back after a reboot — why no systemd unit is needed ([Ch 10](10_Systemd.md)). *Fail:* installing the old `docker.io` + hyphen `docker-compose` — every script here uses the **space** `docker compose`.

### Step 5 — DNS A record, BEFORE the first `up` ([Ch 04](04_DNS_Domains.md)/[Ch 12](12_Caddy.md))
In your registrar: `A  erp  →  203.0.113.10  TTL 300`.
```bash
dig +short erp.example.com                    # ✓ prints exactly 203.0.113.10 (wait for propagation)
```
> ⚠️ **DNS must resolve before `up`.** On first boot Caddy asks Let's Encrypt for a cert; LE calls back to `erp.example.com` to verify you own it. No DNS → challenge fails → no HTTPS → repeated fails get **rate-limited** (hours of waiting). DNS-only (no Cloudflare proxy) so LE reaches Caddy directly.

### Step 6 — Clone + checkout the certified tag ([Ch 27](27_Migrations.md)/[Ch 33](33_CI_CD.md))
```bash
git clone <repo-url> kapil-erp && cd kapil-erp
git checkout erp-v1.0.0                        # frozen, 1878/1878 tests, signed certificate
git describe --tags && ls deploy/              # ✓ erp-v1.0.0 + Caddyfile/README/backup.sh/deploy.sh/entrypoint.sh
```
"detached HEAD" on a tag is **normal**. Clone to a stable path (e.g. `/opt/kapil-erp`) — backup/deploy scripts assume a known repo root.

### Step 7 — Create `.env` from `.env.example` ([Ch 23](23_Environment_Variables.md))
```bash
cp .env.example .env      # then fill EVERY value (21 vars; each line documents itself)
```
The tricky ones:
- **`SECRET_KEY`** — `python3 -c "import secrets; print(secrets.token_urlsafe(64))"`; prod **crashes if missing** (no default — fail-fast).
- **`ALLOWED_HOSTS` / `CSRF_TRUSTED_ORIGINS` / `DOMAIN`** — all your real domain (CSRF with `https://`); all three must agree.
- **`DATABASE_URL` + `POSTGRES_PASSWORD`** — same strong password in **both** places. Mismatch = first-boot failure #1 (Postgres inits one password, Django tries the other, entrypoint times out at 120s).
- **`REDIS_URL`** = `redis://redis:6379/0` exactly (`redis` = service name); fail-fast ([Ch 22](22_Redis.md)).
- **`LEDGER_CREDIT_AT_ALLOCATION`** = leave `False` (rollback lever, not a knob). **`ENFORCE_*`** flags stay OFF (soak-gated, [Ch 27](27_Migrations.md)).
- **`RESTIC_REPOSITORY` / `RESTIC_PASSWORD` / `B2_*`** — off-site backup target + creds ([Ch 28](28_Backups.md)).
> ⚠️ Tonight: store the filled `.env` in a **password manager** (the DR pair with the restic repo). `RESTIC_PASSWORD` is **not resettable** — lose it, lose every backup. Never commit `.env`. `chmod 600 .env`.
```bash
grep -c 'replace_with' .env                    # ✓ 0 (no placeholder left)
```

### Step 8 — First start ([Ch 18](18_Docker_Compose.md)/[Ch 09](09_Processes_and_Services.md))
```bash
docker compose up -d --build                   # build app image, pull pinned images, create volumes, start 5 services
docker compose logs -f app caddy               # watch the two that matter
```
Inside `app`, the **entrypoint** ([Ch 09](09_Processes_and_Services.md)): waits (≤120s) for **healthy** DB + Redis → `migrate --noinput` ([Ch 27](27_Migrations.md)) → `collectstatic --noinput` ([Ch 26](26_collectstatic.md)) → `exec gunicorn config.wsgi:application --workers 3` ([Ch 14](14_Gunicorn.md)). Caddy fetches the TLS cert.
- ✓ app log: "Booting worker" ×3; caddy log: "certificate obtained".
- *Fail:* entrypoint wait-loop times out → DB password mismatch (Step 7). Caddy cert fails → DNS not resolving (Step 5).

### Step 9 — Create the superuser
```bash
docker compose exec app python manage.py createsuperuser
```
The first admin account (login at `https://erp.example.com`). *Fail:* running before `app` is healthy → connection error; wait for Step 8 green.

### Step 10 — The owner data decision
Clean start (fresh DB, real factory data entered live) **or** load a dev dump. Owner's call ([Test-Data Authorization]). A clean start needs nothing here; a dump is `pg_restore` into `db` ([Ch 29](29_Restore.md)). Do **not** ship dev scratch data to prod.

### Step 11 — Smoke test + verification gate ([Ch 30](30_Monitoring.md))
```bash
curl -sI https://erp.example.com               # ✓ 200 + strict-transport-security header
curl -sI http://erp.example.com | grep -i location   # ✓ 301 → https
docker compose exec app python manage.py verify_production   # ✓ 0 red checks
docker compose exec app python manage.py check --deploy      # ✓ hardening flags satisfied
```
By hand in the browser: login · dashboard · a worker report · a settlement page · one media file. All must work.

### Step 12 — Confirm the first backup landed ([Ch 28](28_Backups.md))
```bash
docker compose logs backup                     # ✓ "[backup] done" (or wait to ~02:00 IST / force a run)
docker compose exec backup restic snapshots    # ✓ a nightly snapshot exists off-site
```

### Step 13 — The restore-drill mandate ([Ch 29](29_Restore.md))
A backup is unproven until restored. Schedule a drill: `restic restore latest` into a **scratch** DB and assert known truth (sentinel 170 / ₹10,880.25, goldens ₹344.25/₹801/₹633). Match ⇒ backups real.

**Updates later** = `sh deploy/deploy.sh` (dump → pull → build → up → prune → smoke); rollback = `git checkout <prev tag>` + rerun, or restore the predeploy dump ([Ch 33](33_CI_CD.md)).

# Practical — dry-run the whole deploy on your laptop first
Every step below is safe: nothing touches a server, and nothing is irreversible.
Do this **before** you buy a VPS, so deploy day has no surprises.

```bash
# 1. Does the compose file resolve with your .env? (catches typos + missing vars)
docker compose config | head -40

# 2. Does the image build? (catches Dockerfile + dependency errors — ch 17)
docker compose build web

# 3. Bring the whole stack up locally, exactly as production would
docker compose up -d --build
docker compose ps                      # every service "healthy", none restarting

# 4. Did the entrypoint do its four jobs?
#    (wait-for-health → migrate → seed_master_data → collectstatic)
docker compose logs web | head -40

# 5. Prove the app answers, and that static files are being served
curl -sI http://localhost:8000/ | head -3

# 6. Prove the private network works the way ch 19 claims
docker compose exec web python -c "import socket; print(socket.gethostbyname('db'))"

# 7. Prove a fresh database can actually run the factory (the known blocker)
docker compose exec web python manage.py seed_master_data --dry-run

# 8. Tear down WITHOUT touching volumes (note: no -v — ch 20)
docker compose down
```

If all eight succeed locally, the only things left that can fail on the server
are **the server itself** (ch 03–07), **DNS** (ch 04) and **your `.env`** (ch 23).
That is a much smaller list to debug at 11 p.m.

# Visual Diagram
```
  ① VPS(2-4GB, India)  ② SSH keys, no-password  ③ ufw 22/80/443  ④ Docker(get.docker.com)
        host secured ─────────────────────────────────────────────┘
  ⑤ DNS A erp→IP  (dig ✓)  ── BEFORE ⑧ (TLS callback needs it) ──┐
  ⑥ git clone + checkout erp-v1.0.0    ⑦ cp .env.example .env, fill 21 vars, chmod 600, → password manager
                                                                   │
  ⑧ docker compose up -d --build  →  entrypoint: wait healthy db+redis → migrate → collectstatic → gunicorn×3
                                     caddy → Let's Encrypt cert
  ⑨ createsuperuser  ⑩ data decision  ⑪ smoke + verify_production + check --deploy  ⑫ backup landed  ⑬ restore drill
  updates: deploy.sh (dump→pull→build→up→prune→smoke) | rollback: prev tag + deploy.sh / restore predeploy dump
```

# Production Walkthrough
The whole system, in the order a request travels:
1. **Worker's phone** hits `https://domain` → DNS (ch 04) → the VPS.
2. **Caddy** terminates TLS with an automatic certificate (ch 12, ch 13), serves static and media directly (ch 25), and proxies everything else.
3. **Gunicorn**, 3 workers, runs `config.wsgi` (ch 14, ch 15).
4. **Django** handles the request: permission service gates access, service layer owns multi-row writes, settlement is the only money boundary.
5. **Postgres** on a private network holds the truth; **Redis** caches (ch 21, ch 22).
6. **Volumes** persist database, media and certificates (ch 20).
7. **`deploy/backup.sh`** copies database + media off-site (ch 28).

Deploy itself is: push code → `docker compose up -d --build` → the entrypoint waits for health, collects static, migrates, then starts Gunicorn (ch 18, ch 26, ch 27).

What is deliberately absent: no error tracker (ch 32), no CI (ch 33), no dashboards (ch 30). (A fresh database also needs its platform master data — migrations give only 4 of 21 stages — but the entrypoint now seeds that automatically on every boot.)

# Debugging Guide
1. **Locate the failure by layer** — Caddy, Gunicorn, Django, Postgres, in that order (ch 31).
2. **502** = the app is not answering. **504** = it is too slow. Different problems, different fixes.
3. **Unstyled** = static. **Broken images** = media. **Wrong numbers** = application, and treat it as serious.
4. **Cannot start an Adda** = master data missing, not a code bug.
5. **Slow everything** = check host disk and memory first (ch 06).

# Performance Notes
- 3 Gunicorn workers is a starting point tied to CPU count, not to traffic (ch 14).
- Caddy serving files keeps workers free for Python.
- `CONN_MAX_AGE` reuses database connections (ch 21).
- The first minute after deploy is cold; expect it and do not panic-tune.

# Security Considerations
- Only 22/80/443 open; key-only SSH (ch 05, ch 07).
- No published database or cache ports (ch 19).
- `DEBUG=False`, HSTS, secure cookies, Argon2, rate limiting (ch 34).
- Settlement-only money writes limit damage even from a valid login.
- Backups hold everything — encrypt them (ch 28).

# Architecture Decisions
- **Docker Compose on one VPS** — a solo maintainer can hold this in their head, and it fits the load of one factory.
- **Caddy over Nginx** for automatic certificates and a short config.
- **Everything in git**: compose, Caddyfile, entrypoint, backup script.
- **Recovery over observation**: health checks and restarts before dashboards.
- **Known gaps recorded**, not hidden — seeding, CI, error tracking.

# Best Practices
- Follow `deploy/README.md`; treat this chapter as the map, that file as the runbook.
- Verify with a real financial total after every deploy (ch 35).
- Keep the deployment simple until real load says otherwise (ch 41).
- Record every deploy's git hash and time.

# Beginner Mistakes
- **`ufw enable` before allowing 22** → locked out. 22 first, always (Step 3).
- **`up` before DNS resolves** → Caddy can't get a cert, then Let's Encrypt rate-limits you (Step 5).
- **`POSTGRES_PASSWORD` ≠ the one in `DATABASE_URL`** → entrypoint times out at 120s (Step 7). #1 first-boot failure.
- **Deploying a branch, not the tag** → untested code in the factory. `git checkout erp-v1.0.0` (Step 6).
- **`.env` not in a password manager** → can't decrypt backups after a total loss (Step 7 / [Ch 28](28_Backups.md)).
- **Declaring "done" at Step 8** → container up ≠ working. Do Steps 11–13 (verify + backup + restore drill).
- **Flipping `ENFORCE_*` / `LEDGER_CREDIT_AT_ALLOCATION` on** → skips the soak. Leave defaults.
- **Old `docker-compose` (hyphen)** → the plugin is `docker compose` (space) everywhere here.

# Interview Questions
- **Junior:** "What's the first thing you do on a fresh VPS, and why not last?" — Lock down host access — SSH keys, disable password login, firewall to 22/80/443 — before anything else, because a fresh public server is scanned by bots within minutes.

- **Mid:** "Why must DNS resolve before the first `docker compose up`?" — Caddy requests a Let's Encrypt cert on first boot, and LE calls back to the domain to verify ownership. If DNS doesn't point at the server, the challenge fails, no cert is issued, and repeated failures get rate-limited — so DNS first, `up` second.

- **Senior:** "Walk the entrypoint sequence and why each step is ordered so." — Wait for *healthy* DB+Redis (don't trust `depends_on` alone) so migrations/queries can't hit a not-ready dependency → `migrate` so the schema matches the code before serving → `collectstatic` so static is present → `exec gunicorn` (PID 1, receives signals) to serve. Ordered so the app never serves a request against an unready DB or missing schema/static.

- **Staff:** "A junior is doing this first deploy alone. What are the three failure points you'd most want guardrails on, and how are they guarded here?" — (1) Lockout — mitigated by "verify new key session before disabling passwords" + provider rescue console + "allow 22 before enable." (2) TLS/DNS ordering — mitigated by an explicit DNS-before-`up` step with a `dig` verification gate and the rate-limit warning. (3) DB password mismatch (silent 120s hang) — mitigated by the "same password in both places" rule + a documented failure signature. Beyond those: the certified tag (no untested code), fail-fast env vars (misconfig crashes loudly not silently), and the verify+backup+restore-drill closeout so "up" is never mistaken for "done, recoverable." The design turns the dangerous steps into gated, self-verifying ones.

### Why interviewers ask these — and the answer that separates levels

| Testing for | Weak answer | What lands |
|---|---|---|
| Do you know what comes first on a fresh VPS, and why? | "Install Docker and deploy the app." | **Lock down host access first** — SSH keys, `PasswordAuthentication no`, firewall to 22/80/443 — because **a fresh public server is scanned by bots within minutes**. Deploying onto an unhardened box means racing them. |
| Do you know why DNS must resolve before the first `up`? | "DNS can be pointed after deployment." | Caddy requests a cert on first boot and **Let's Encrypt calls back to the domain** to verify ownership. No DNS → failed challenge → no cert → and **repeated failures hit the issuance rate limit**, so you are then blocked by the clock. |
| Can you justify the entrypoint order? | "It starts the app." | **Wait for *healthy* DB+Redis** (not just `depends_on`) → **`migrate`** so the schema matches the code before any request → **`collectstatic`** → **`exec` Gunicorn** so it becomes PID 1 and receives SIGTERM (ch 09). Every step is ordered against a specific failure. |
| Can you name the lockout guardrail? | "Be careful with SSH config." | **Verify the new key in a second session BEFORE disabling password login** — and know the provider's rescue console exists. "Be careful" has locked a lot of people out of their own servers; a second open session has not. |

**The killer follow-up:** *"A junior is doing this deploy alone tonight. What are the three things you guard, and how?"* — **(1) lockout** — verify the key in a second session before disabling passwords, rescue console known; **(2) cert rate-limiting** — DNS before first `up`, persistent `caddy_data`; **(3) data loss** — backup before migrate, and never `down -v`. Naming *your own* riskiest steps is the senior signal here.

# Revision Notes
- Path: **phone → DNS → Caddy (TLS, static/media) → Gunicorn ×3 → Django → Postgres/Redis**, volumes underneath, backups off-site.
- Deploy = `docker compose up -d --build`; entrypoint waits-for-health → **migrate → seed_master_data → collectstatic** → serve.
- Absent on purpose: error tracker, CI, dashboards. Fresh DB master data is seeded by the entrypoint.
- 502 = not answering · 504 = too slow · unstyled = static · broken images = media.
- One VPS, one compose file, everything in git — chosen for a solo maintainer.

# Cheat Sheet
- **Order:** VPS → SSH keys → ufw(22 first) → Docker → **DNS(before up)** → clone tag → `.env`(fill+600+pw-manager) → `up -d --build` → superuser → data → **verify+check** → backup landed → restore drill.
- **Pinned images:** caddy 2.9.1 · postgres 16.6 · redis 7.4.2 · python 3.10.16. **Tag:** `erp-v1.0.0`.
- **Entrypoint:** wait healthy db+redis → migrate → collectstatic → gunicorn×3.
- **Top failures:** ufw-before-22 / up-before-DNS / password-mismatch(120s) / branch-not-tag / .env-not-escrowed.
- **Updates:** `deploy.sh` (dump→pull→build→up→prune→smoke). **Rollback:** prev tag + deploy.sh / restore predeploy dump.
- **Not done until:** verify_production ✓ + backup landed ✓ + restore drill scheduled ✓.

# My ERP Section
| Step | Command / value |
|---|---|
| VPS | Ubuntu LTS, 2–4 GB, India |
| SSH | `ssh-keygen -t ed25519`; `PasswordAuthentication no` |
| Firewall | `ufw allow 22,80,443/tcp; ufw enable` |
| Docker | `curl -fsSL https://get.docker.com \| sh` |
| DNS | `A erp → 203.0.113.10`; `dig +short` = IP |
| Code | `git checkout erp-v1.0.0` |
| Config | `cp .env.example .env`; fill 21; `chmod 600`; → password manager |
| Start | `docker compose up -d --build` |
| Verify | `verify_production` + `check --deploy` + browser smoke |
| Backup | `docker compose logs backup` → `[backup] done`; `restic snapshots` |
| Recover | restore drill (sentinel 170/₹10,880.25, goldens ₹344.25/₹801/₹633) |
| Update | `sh deploy/deploy.sh` |

# Practice Tasks
1. **Read the code:** open `docker-compose.yml`, `deploy/Caddyfile`, `deploy/entrypoint.sh` together and trace one request through all three.
2. **Debug:** for each of the five symptoms above, write which log you check first.
3. **Design:** write your own one-page version of this architecture from memory, then diff it against the file.
4. **Architecture:** argue Compose-on-one-VPS versus a managed platform for this business, in cost and risk terms.

# Homework
1. From memory, list the 13 steps in order. Which two, if swapped, lock you out or break TLS?
2. Explain exactly why `POSTGRES_PASSWORD` must equal the password inside `DATABASE_URL`. What's the failure signature?
3. Why `git checkout erp-v1.0.0` instead of `git pull` on `main`? What does the tag guarantee?
4. Trace the entrypoint's four actions and justify the order. Why wait for *healthy*, not just *started*?
5. You've reached Step 8 and the container is up. List the five things (Steps 9–13) still required before you can call the deploy done + recoverable.

---

# Further Reading & Live Resources
- My canonical runbooks: `DEPLOYMENT.md` (teaching kit) + `deploy/README.md` (expert steps 1–11) + `docs/release/` (Operations Handbook).
- DigitalOcean — *Django + Postgres + Gunicorn + Nginx on Ubuntu 22.04* (classic end-to-end, non-Docker comparison): https://www.digitalocean.com/community/tutorials/how-to-set-up-django-with-postgres-nginx-and-gunicorn-on-ubuntu-22-04
- Docker docs — *Get Docker (convenience script)*: https://docs.docker.com/engine/install/ubuntu/
- Caddy docs — *Automatic HTTPS*: https://caddyserver.com/docs/automatic-https
- Let's Encrypt — *How it works / challenges + rate limits*: https://letsencrypt.org/how-it-works/ · https://letsencrypt.org/docs/rate-limits/
- DigitalOcean — *Initial server setup (SSH + ufw)*: https://www.digitalocean.com/community/tutorials/initial-server-setup-with-ubuntu-22-04
