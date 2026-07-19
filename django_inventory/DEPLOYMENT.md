# DEPLOYMENT.md — Production Deployment Kit (ERP v1.0)

> **Status: PREPARATION ONLY.** No VPS exists yet; nothing here has been run against
> production. Every credential in this kit is an obvious placeholder
> (`replace_with_*`, `erp.example.com`, `203.0.113.10`). When the owner purchases the
> infrastructure (the P19.5 provisioning list), deployment = replace placeholders +
> follow §10's checklist. The release being deployed is the frozen, certified tag
> **`erp-v1.0.0`** (commit `90c1f2f3`, battery 1878/1878).

**How this document relates to the other two deployment docs (read this once):**

| Document | Role | When to open |
|---|---|---|
| [`deploy/README.md`](deploy/README.md) | The terse expert **runbook** — *what to type*. Canonical for execution. | On deployment day, in the terminal |
| [`docs/release/DEPLOYMENT_GUIDE.md`](docs/release/DEPLOYMENT_GUIDE.md) | The **architecture** teaching doc — *why the stack looks like this* | To understand the design |
| **This file** | The complete **deployment kit** — every step, file, command, and failure mode taught from zero, for an operator with no DevOps background | To prepare, learn, and verify |

The certified stack files (`docker-compose.yml`, `Dockerfile`, `deploy/Caddyfile`,
`deploy/entrypoint.sh`, `deploy/deploy.sh`, `deploy/backup.sh`, `.env.example`) are
**frozen release assets** — this kit reproduces and teaches them; it never modifies them.

**Contents**

1. [The Deployment, Step by Step](#1-the-deployment-step-by-step)
2. [Environment Reference (.env)](#2-environment-reference-env)
3. [docker-compose.yml — the five services, explained](#3-docker-composeyml--the-five-services-explained)
4. [Dockerfile — every instruction](#4-dockerfile--every-instruction)
5. [Caddyfile — HTTPS in four lines](#5-caddyfile--https-in-four-lines)
6. [Systemd — why this stack does not need a unit file](#6-systemd--why-this-stack-does-not-need-a-unit-file)
7. [Backups — pg_dump + restic, nightly](#7-backups--pg_dump--restic-nightly)
8. [Verifying the Deployment](#8-verifying-the-deployment)
9. [Rollback & Recovery](#9-rollback--recovery)
10. [Deployment-Day Checklist](#10-deployment-day-checklist)

---

## 1. The Deployment, Step by Step

> **What this section is:** the complete first-deploy walkthrough, in teaching mode.
> The expert checklist lives in [`deploy/README.md`](deploy/README.md) (steps 1–11) — that file stays canonical.
> This section is the same journey, but every step explains **what / why / success / failure**, because you are doing this for the first time and there is no DevOps person standing behind you.
>
> **The stack you are about to run** (all of it already exists in the repo, certified and frozen at tag `erp-v1.0.0`):
>
> ```
> Internet ──HTTPS──▶ caddy (auto-TLS) ──▶ app (gunicorn + Django) ──▶ db (Postgres 16.6)
>                                                    │                └▶ redis 7.4
>                                                    └── media volume
>                     backup (nightly pg_dump + media → restic → B2/R2)
> ```
>
> One VPS, one `docker compose up`, five containers. Nothing to install by hand except Docker itself.

> 💡 **Samjho aise:** Poora production ek hi machine par hai — jaise ek chhoti factory jisme paanch machinein (caddy, app, db, redis, backup) ek hi shed ke andar lagi hain. `docker-compose.yml` us shed ka layout-map hai: kaunsi machine kahan lagegi, kaunsi pehle chalu hogi, kaunsi bahar ke gate (ports 80/443) se judegi. Aapka kaam sirf shed (VPS) kiraye par lena, bijli-paani (Docker) lagwana, aur map ke hisaab se switch on karna hai.

---

### Step 1 — Buy the VPS

**What:** rent a small Linux server ("VPS" = Virtual Private Server) from a cloud provider.

**The owner-approved spec (P19.5 provisioning list):**

| Item | Value | Why |
|---|---|---|
| RAM | **2–4 GB** | gunicorn runs 3 sync workers + Postgres + Redis + Caddy — 2 GB is the floor, 4 GB is comfortable |
| Region | **India** — DigitalOcean **Bangalore** or Vultr **Mumbai** | the factory and every user is in India; nearest region = lowest latency |
| OS | Ubuntu LTS (22.04 or 24.04) | the commands in this guide assume Ubuntu/`apt` |
| Login | **SSH-key-only** (set up in Step 2) | passwords get brute-forced; keys don't |

**Why this step exists:** everything else in this guide runs *on* this machine. Its public IP address (we'll call it `203.0.113.10` everywhere in this guide — replace with your real one) is what your domain will point at.

**Common mistakes:**
- Picking a US/EU region because it's the default → every page load carries 200+ ms of ocean round-trip. Pick India.
- Picking 1 GB RAM to save money → Postgres + 3 gunicorn workers will OOM under load. 2 GB minimum.
- Skipping the SSH-key option at creation time "to do it later" → your brand-new server gets password-scanned by bots within minutes of boot. Add the key **at creation** (Step 2 shows how to make one).

**Verification:**
```bash
ssh root@203.0.113.10 "uname -a && free -h"
```
Success looks like: a `Linux ... Ubuntu` line, and `free -h` showing `Mem: 2.0Gi` (or more). If `ssh` hangs → wrong IP or the provider's own firewall panel is blocking port 22.

---

### Step 2 — SSH key + disable password login

**What:** create a cryptographic key pair on **your laptop**, put the public half on the server, then turn password login off entirely.

> 💡 **Samjho aise:** Password ek taala hai jise koi bhi hazaar chaabiyan try kar ke tod sakta hai (bots literally yahi karte hain, din-raat). SSH key ek aisi chaabi hai jiska duplicate banana practically impossible hai — private half aapke laptop par rehta hai, public half server par. Server sirf usi laptop ko andar aane deta hai jiske paas private half hai.

**2a. Make the key (on your laptop, not the server):**
```bash
ssh-keygen -t ed25519 -C "kapil-erp-vps"
```
- *What it does:* creates `~/.ssh/id_ed25519` (private — never leaves your laptop, never gets emailed/pasted anywhere) and `~/.ssh/id_ed25519.pub` (public — safe to share).
- *Why `ed25519`:* modern, short, fast; the current default recommendation.
- Press Enter to accept the default path. Setting a passphrase is optional but recommended (a password *on the key file itself*).

**2b. Put the public key on the server.** Best option: paste the contents of `~/.ssh/id_ed25519.pub` into the provider's "SSH keys" box **when creating the VPS** (both DO and Vultr have this). If the server already exists:
```bash
ssh-copy-id root@203.0.113.10
```

**2c. Verify key login works BEFORE going further:**
```bash
ssh root@203.0.113.10
```
Success looks like: you land in a shell **without being asked for the account password** (a key-passphrase prompt is fine — that's your local key, not the server).

**2d. Disable password login.**

> **SECURITY WARNING (pure English, read fully):** Do NOT close your current SSH session until you have confirmed a *second, new* session can log in with the key. If you disable passwords while key login is broken, you are locked out of your own server and will need the provider's rescue console.

On the server, edit `/etc/ssh/sshd_config` and set these two lines (uncomment them if needed):
```
PasswordAuthentication no
PermitRootLogin prohibit-password
```
Then restart the SSH daemon:
```bash
systemctl restart ssh
```
- *What it does:* SSH will now refuse any password attempt; root can only log in with the key.
- *Why:* this single change removes the #1 attack vector against a fresh VPS.

**Verification:** open a **new terminal** and:
```bash
ssh -o PubkeyAuthentication=no root@203.0.113.10
```
Success looks like: `Permission denied (publickey).` — that error is the *goal*: passwords are dead. A normal `ssh root@203.0.113.10` in another terminal must still work.

**Common mistake:** editing `sshd_config`, forgetting `systemctl restart ssh`, and believing you're protected. The config is only read at daemon (re)start.

---

### Step 3 — Firewall (ufw)

**What:** close every network port except the three this stack needs: **22** (SSH), **80** (HTTP — Caddy needs it for the Let's Encrypt challenge and for redirecting to HTTPS), **443** (HTTPS).

This is `deploy/README.md` step 1's second half: `ufw allow 22,80,443; ufw enable`.

> 💡 **Samjho aise:** Server by default ek aisi building hai jisme har taraf darwaze khule hain. Firewall watchman hai jo sab darwaze band kar deta hai aur sirf teen gate khole rakhta hai — ek aapke liye (22), do customers ke liye (80/443). Postgres ka gate (5432), Redis ka gate (6379) — sab bahar se band. (Compose file me waise bhi sirf `caddy` publish karta hai ports — db/redis kabhi internet par exposed nahi hote — lekin firewall doosri, independent deewar hai.)

**Commands (on the server, in this exact order):**
```bash
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

> **SECURITY WARNING:** Run `ufw allow 22/tcp` **BEFORE** `ufw enable`. Enabling the firewall with port 22 still closed cuts off your own SSH session and locks you out. `ufw enable` will ask "Command may disrupt existing ssh connections. Proceed?" — answer `y` only after 22 is allowed.

- *What each does:* the three `allow` lines whitelist the ports; `ufw enable` flips the default to "deny everything else" and makes it persistent across reboots.
- *Why 80 as well as 443:* Let's Encrypt's issuance challenge and Caddy's HTTP→HTTPS redirect both arrive on port 80. Blocking 80 breaks certificate issuance.

**Verification:**
```bash
ufw status
```
Success looks like:
```
Status: active
To                         Action      From
--                         ------      ----
22/tcp                     ALLOW       Anywhere
80/tcp                     ALLOW       Anywhere
443/tcp                    ALLOW       Anywhere
```
**Troubleshooting:** `Status: inactive` → you skipped `ufw enable`. Locked out anyway? Use the provider's web console ("Recovery"/"Console" button in the panel) — it bypasses SSH — then run `ufw allow 22/tcp`.

---

### Step 4 — Install Docker + the compose plugin

**What:** install the container runtime. This is `deploy/README.md` step 2, one command:
```bash
curl -fsSL https://get.docker.com | sh
```
- *What it does:* Docker's official convenience script detects Ubuntu, adds Docker's apt repository, and installs the engine **and** the `docker compose` plugin together.
- *Why Docker at all:* the whole production stack is defined as containers in `docker-compose.yml`. Nothing else — no system Python, no system Postgres, no nginx — ever gets installed on the host. The host stays boring; everything interesting lives in pinned images.

> 💡 **Samjho aise:** Docker image ek sealed dabba hai jisme software apni poori duniya (Python 3.10.16, saari libraries, settings) ke saath packed aata hai. "Mere laptop par to chal raha tha" waali problem isliye khatam ho jaati hai kyunki dabba har jagah bilkul same hota hai. `docker-compose.yml` batata hai kaunse paanch dabbe kholne hain aur unhe aapas me kaise jodna hai.

**Verification:**
```bash
docker --version
docker compose version
systemctl is-enabled docker
```
Success looks like:
```
Docker version 27.x.x, build ...
Docker Compose version v2.x.x
enabled
```
That last `enabled` matters — it means Docker starts automatically on boot (this is why we do NOT need a systemd unit file for the app; §6 explains it fully). If it prints `disabled`, run `systemctl enable docker`.

**Common mistakes:**
- Installing the ancient Ubuntu-repo `docker.io` + standalone `docker-compose` (with a hyphen) instead. This guide and every script in `deploy/` use the **plugin** syntax `docker compose` (with a space). The get.docker.com script gives you the right one.
- Testing with `docker run hello-world` and then leaving that dead container around. Harmless, but `docker image prune` later cleans it.

---

### Step 5 — DNS A record (BEFORE the first `up`)

**What:** in your domain registrar's DNS panel, create an **A record** pointing your ERP hostname at the VPS IP:

```
Type: A    Name: erp    Value: 203.0.113.10    TTL: 300 (or default)
```
(so that `erp.example.com` → `203.0.113.10` — replace both placeholders with your real domain and IP).

**Why this must happen BEFORE the first `docker compose up`:** the certified `deploy/Caddyfile` is three lines:

```caddyfile
# The ONE TLS-terminating proxy (PD's SECURE_PROXY_SSL_HEADER assumption).
# Caddy auto-provisions Let's Encrypt for {$DOMAIN} and sets X-Forwarded-Proto.
{$DOMAIN} {
	encode gzip
	reverse_proxy app:8000
}
```

On first start, Caddy contacts **Let's Encrypt** and asks for a free HTTPS certificate for `$DOMAIN`. Let's Encrypt then *calls back* — it connects to `erp.example.com` from the internet to prove you control that name. If the DNS record doesn't resolve to your server yet, the challenge fails, no certificate is issued, HTTPS doesn't work, and repeated failed attempts get **rate-limited** by Let's Encrypt — meaning you can end up waiting hours even after fixing DNS. Order matters: DNS first, `up` second.

> 💡 **Samjho aise:** DNS internet ki phone-book hai — naam se number nikalti hai. Let's Encrypt certificate dene se pehle phone-book me aapka naam dekh kar usi number par call karta hai: "kya sach me yahi server is naam ka maalik hai?" Agar phone-book me entry hi nahi hai, call fail — certificate nahi milega. Isliye pehle entry, phir dukan kholna.

**Verification (repeat until it passes — DNS can take minutes to propagate):**
```bash
dig +short erp.example.com
```
Success looks like exactly your server IP:
```
203.0.113.10
```
**Troubleshooting:** empty output → record not created / not propagated yet; wait 5–10 minutes. A *different* IP → you edited the wrong record, or a proxy (e.g., Cloudflare orange-cloud) sits in front — for this stack the record should be **DNS-only** so Let's Encrypt reaches Caddy directly.

---

### Step 6 — Clone the repo, checkout the certified release

**What:** get the code onto the server, pinned to the certified release tag. (`deploy/README.md` step 4.)

```bash
git clone <repo-url> kapil-erp
cd kapil-erp
git checkout erp-v1.0.0
```
- *Why the tag:* `erp-v1.0.0` (commit `90c1f2f3`) is the frozen, fully-certified release — 1878/1878 tests, release certificate signed. Deploying "whatever the branch has today" is how untested code reaches the factory. Tags don't move; branches do.
- Git will print `You are in 'detached HEAD' state...` — for a first deploy pinned to a tag this is **normal and expected**, not an error.
- *One honest footnote:* a tiny deploy-asset patch (`3593e567`, which marks `deploy/deploy.sh` executable in git) landed just **after** the tag. The first deploy never runs `deploy.sh`, so this doesn't affect today. When you later use it for updates, `sh ./deploy/deploy.sh` works regardless of the executable bit.

**Verification:**
```bash
git describe --tags
ls deploy/
```
Success looks like: `erp-v1.0.0` on the first line, and `Caddyfile  README.md  backup.sh  deploy.sh  entrypoint.sh` from the second.

**Common mistake:** cloning into some deep temp path you'll forget. Pick a permanent home (e.g. `/opt/kapil-erp` or `/root/kapil-erp`) — the backup service, deploy script, and the systemd notes in §6 all assume "the repo root on the VPS" is a stable, known path.

---

### Step 7 — Create `.env` from `.env.example`

**What:** the single file holding every secret and setting. (`deploy/README.md` step 5.)

```bash
cp .env.example .env
```
Then open `.env` and fill **EVERY** value. The template itself is the reference: every variable in [`.env.example`](.env.example) carries its own purpose + security comment, and §2 of this guide has the full variable-by-variable table. Do not skip any line.

**How to fill the tricky ones (placeholders only — never reuse these literal values):**

| Variable | How / rule |
|---|---|
| `SECRET_KEY` | Generate 50+ random chars: `python3 -c "import secrets; print(secrets.token_urlsafe(64))"` — run it once, paste, never change casually (changing it invalidates sessions). Production **crashes on purpose** if this is missing (`config/config/settings/production.py` has NO default — fail-fast by design). |
| `ALLOWED_HOSTS` / `CSRF_TRUSTED_ORIGINS` / `DOMAIN` | All three carry your real domain, e.g. `erp.example.com` (CSRF one with the `https://` prefix). All three must agree. |
| `DATABASE_URL` & `POSTGRES_PASSWORD` | Pick ONE strong password (e.g. `replace_with_postgres_password`) and put it in **both** places — the password inside `DATABASE_URL` and the `POSTGRES_PASSWORD` line. Mismatch here is first-boot failure #1: Postgres initializes with one password, Django tries the other, the entrypoint wait-loop times out after 120 s. |
| `REDIS_URL` | Keep `redis://redis:6379/0` exactly — `redis` is the compose service name, resolved on Docker's internal network. Also fail-fast: production refuses to boot without it (the login rate-limiter's counters live in Redis; a silent fallback to per-process memory would weaken it ~3× under 3 gunicorn workers). |
| `LEDGER_CREDIT_AT_ALLOCATION` | Leave `False`. This is the settlement-cutover **rollback lever** (ADR-0007), not a tuning knob. |
| `EMAIL_*`, `GOOGLE_CLIENT_*` | Your SMTP provider's host/user/password (port 587) and Google OAuth credentials. |
| `RESTIC_REPOSITORY` / `RESTIC_PASSWORD` / `B2_ACCOUNT_ID` / `B2_ACCOUNT_KEY` | The offsite backup target (Backblaze B2 bucket, or Cloudflare R2 via an `s3:` URI) and its credentials. |

> **SECURITY WARNING:**
> 1. **Store the filled `.env` in the password manager, tonight.** It is one half of the disaster-recovery pair — the other half is the restic repository. With those two things you can rebuild the entire system from a smoking crater (§restore drill). Without them, you cannot.
> 2. **`RESTIC_PASSWORD` encrypts the backups. Losing it = losing every backup.** It is not resettable. Password manager, now.
> 3. **NEVER commit `.env` to git.** The repo's `.gitignore` protects you, but the rule is absolute.
> 4. Optional hardening: `chmod 600 .env` so only root can read it on the host.

> 💡 **Samjho aise:** `.env` factory ki master-chaabi ka guchha hai — database ki chaabi, email ki chaabi, backup-tijori ki chaabi, sab ek ring par. Isi liye do rules: guchhe ki ek copy locker (password manager) me, aur guchha kabhi photo khinch ke (git commit kar ke) public album me nahi.

**Verification:**
```bash
grep -c 'replace_with' .env
```
Success looks like: `0` — every placeholder replaced with a real value. (The command counts leftover `replace_with_*` placeholders; any number above 0 means unfilled secrets remain.)

---

### Step 8 — First start: `docker compose up -d --build`

The big one. (`deploy/README.md` step 6.)

```bash
docker compose up -d --build
docker compose logs -f app caddy
```
- *What it does:* builds the app image from the `Dockerfile` (base `python:3.10.16-slim`, installs `requirements.txt` — all pre-built wheels, so no compiler needed — copies `config/`, runs as non-root user `app`), pulls the exact-pinned images (`caddy:2.9.1`, `postgres:16.6-alpine`, `redis:7.4.2-alpine`), creates the named volumes (`pgdata`, `media`, `caddy_data`, `caddy_config`, `backups`), and starts all five services in dependency order. `-d` = detached (runs in background); `--build` = build the app image first. The second command tails the two logs that matter.

**What happens inside the `app` container — the entrypoint.** This is the most important 47 lines in the deploy. Certified `deploy/entrypoint.sh`, reproduced verbatim:

```sh
#!/bin/sh
# App-container entrypoint (deploy direction C).
# Owner rule #2: do NOT trust depends_on ordering alone — actively wait for a
# HEALTHY database and Redis before migrate/collectstatic/gunicorn.
set -e

echo "[entrypoint] waiting for database + redis…"
python - <<'PY'
import os, sys, time

import django
django.setup()
from django.db import connections

import redis as redis_lib

deadline = time.monotonic() + 120   # 2 min then fail loudly — never boot half-up
db_ok = cache_ok = False
while time.monotonic() < deadline:
    if not db_ok:
        try:
            connections['default'].ensure_connection()
            db_ok = True
            print("[entrypoint] database: ready")
        except Exception:
            pass
    if not cache_ok:
        try:
            redis_lib.from_url(os.environ['REDIS_URL']).ping()
            cache_ok = True
            print("[entrypoint] redis: ready")
        except Exception:
            pass
    if db_ok and cache_ok:
        sys.exit(0)
    time.sleep(2)
sys.exit("[entrypoint] FATAL: db_ok=%s cache_ok=%s after 120s" % (db_ok, cache_ok))
PY

echo "[entrypoint] applying migrations…"
python manage.py migrate --noinput

echo "[entrypoint] collecting static files…"
python manage.py collectstatic --noinput

echo "[entrypoint] starting: $*"
exec "$@"
```

Read it as four acts:

1. **Wait-loop (up to 120 s):** actively pings the real database connection and the real Redis until both answer. Compose's `depends_on: condition: service_healthy` already orders startup, but the entrypoint *double-checks with its own eyes* (owner rule #2). If either dependency never comes up, it **fails loudly** — the container exits with a FATAL line instead of serving a half-working app.
2. **`migrate --noinput`:** applies every pending database migration. This is why deploys later are just "build + up" — schema updates ride the boot.
3. **`collectstatic --noinput`:** gathers all CSS/JS/images into `staticfiles/` for serving.
4. **`exec gunicorn ...`:** hands the process over to gunicorn — 3 sync workers on `0.0.0.0:8000` (fits the 2–4 GB box), logs to stdout so `docker compose logs` sees everything.

> 💡 **Samjho aise:** Entrypoint woh senior operator hai jo line chalu karne se pehle khud check karta hai — bijli aayi? (database ready?) paani aaya? (redis ready?) Nahi aaya to 2 minute wait, phir bhi nahi to **machine chalu hi nahi karta, alarm bajata hai** — aadhi-chalti line se products kharab hote hain. Sab theek to pehle jig set karta hai (migrate), phir tools sajata hai (collectstatic), phir hi production start (gunicorn).

Meanwhile **Caddy** is fetching the Let's Encrypt certificate for your `$DOMAIN` (this is why Step 5 had to come first) and starts reverse-proxying `https://erp.example.com` → `app:8000`, setting `X-Forwarded-Proto` — which pairs with `SECURE_PROXY_SSL_HEADER` in production settings. That pairing is exactly why **gunicorn must never be exposed to the internet directly**; only Caddy publishes ports.

**Success looks like** (in the logs you're tailing):
```
app    | [entrypoint] waiting for database + redis…
app    | [entrypoint] database: ready
app    | [entrypoint] redis: ready
app    | [entrypoint] applying migrations…
app    | Operations to perform: ... Applying ... OK
app    | [entrypoint] collecting static files…
app    | ... static files copied ...
app    | [entrypoint] starting: gunicorn ...
app    | [INFO] Booting worker with pid: ...   (×3)
caddy  | ... certificate obtained successfully ... erp.example.com
```
Then confirm from outside:
```bash
docker compose ps
curl -I https://erp.example.com/
```
`ps` should show all five services `Up` (db and redis `healthy`); `curl` should return `HTTP/2 200` with a valid certificate (no `-k` needed).

**Troubleshooting first-boot failures:**

| Symptom in logs | Cause | Fix |
|---|---|---|
| `[entrypoint] FATAL: db_ok=False ...` after 120 s | `DATABASE_URL` password ≠ `POSTGRES_PASSWORD`, or db container crashed | fix `.env`; if Postgres already initialized with the wrong password on first boot, `docker compose down`, correct `.env`, and (ONLY if the DB is still empty/brand-new) `docker volume rm <project>_pgdata`, then `up -d` again |
| `[entrypoint] FATAL: ... cache_ok=False` | `REDIS_URL` edited/typoed | restore `redis://redis:6379/0` |
| app crashes instantly with a `SECRET_KEY` error | key left empty | intentional fail-fast — fill it (Step 7) |
| Caddy loops on certificate errors | DNS not resolving to this server, or port 80 blocked | re-check Step 5 (`dig +short`) and Step 3 (`ufw status`); then `docker compose restart caddy` |
| Browser shows Django "Bad Request (400)" | `ALLOWED_HOSTS` doesn't contain your domain | fix `.env`, `docker compose up -d` to recreate app |

---

### Step 9 — Create the superuser

(`deploy/README.md` step 7.)
```bash
docker compose exec app python manage.py createsuperuser
```
- *What it does:* interactively creates the first admin account **inside** the running app container, straight into the production database.
- *Why:* a fresh database has zero users; without this nobody can log in to create everything else (roles, workers, products, flows).

> **SECURITY WARNING:** Choose a strong, unique password and store it in the password manager. This account bypasses everything. And the dev seed credentials (`dev.*` / `Dev@12345`) are **DEV ONLY — they must never exist in production.**

**Verification:** open `https://erp.example.com/accounts/login/`, log in with the account you just made, and confirm the dashboard loads.
**Troubleshooting:** `service "app" is not running` → Step 8 didn't finish healthy; fix that first (`docker compose logs app`).

---

### Step 10 — The owner data decision: clean start vs dev dump

(`deploy/README.md` step 8 — this is an **owner decision**, recorded in P19.5.)

Two legitimate options:

**Option A — start CLEAN (recommended):** re-enter master data (Addas, products, workflows, workers, machines) through the admin UIs, by hand.
- *Why recommended:* the dev database contains **validation test rows** — DEV-marked Addas, test workers, seeded scratch data. Production ledgers and settlements must start from a provably-empty truth. Half a day of data entry buys years of "every row in prod is real."

**Option B — import the dev dump:** restore a dump of the dev database using the restore procedure (`deploy/README.md` §Restore drill mechanics — restore section of this kit covers it in teaching mode).
- *Only if* the owner explicitly accepts that test rows come along and must be cleaned up in place.

**Common mistake:** doing Option B "to save time" and then spending weeks unsure whether a settlement row is real or a leftover test. Money tables + test residue = permanent doubt. Clean start is cheaper than it looks.

**Verification (Option A):** after entering master data, spot-check counts in the admin against the owner's paper lists.

---

### Step 11 — Smoke test + the verification gate

(`deploy/README.md` step 9, plus the P13 mandate.)

**11a. The smoke walk — do these in a browser, in order:**

1. `https://erp.example.com/` — the **public homepage (storefront)** renders.
2. `/accounts/login/` — login page renders, login works.
3. Dashboard loads after login.
4. Start an Adda; upload a pattern photo (exercises the media write path).
5. Copy that photo's `/media/...` URL, open it in a **private/incognito window** (not logged in) — it must be **refused/gated**, not served. Media is access-controlled; anonymous access working would be a security bug.

**11b. The formal gate — `verify_production`:**
```bash
docker compose exec app python manage.py verify_production
```
- *What it does:* runs the production verification suite (a management command under `config/verification/`, part of the 78-test verification battery) against the live stack.
- *Why:* the P13 mandate makes this **THE post-deploy gate** — a deploy is not "done" because pages render; it is done when `verify_production` passes. Note there is deliberately **no public HTTP `/health` endpoint** in this system — health is checked from the inside (this command) and by the smoke walk, never by an unauthenticated URL.

Success looks like: the command completes with all checks passing and exit code 0 (`echo $?` → `0`).
**Troubleshooting:** any failure names the failing check — fix the named cause (usually an `.env` value or a skipped step above) and re-run. Do not hand out credentials with this gate red.

---

### Step 12 — Confirm the first backup landed

(`deploy/README.md` step 10.)

The `backup` service is already running — it sleeps until **~02:00 IST** (20:30 UTC — the container clock is UTC) every night, then: `pg_dump -Fc` of the database into `/backups/db-<stamp>.dump`, keeps the 3 newest dumps locally, pushes `/backups` + `/media` to the offsite **restic** repository (B2/R2), applies retention (7 daily / 4 weekly / 6 monthly), and runs a full `restic check` every Sunday. It also runs `restic init` automatically on first boot. RPO = 24 hours.

**The morning after your first night, verify:**
```bash
docker compose exec backup restic snapshots
```
Success looks like: a table with at least one snapshot — ID, last night's timestamp, tag `nightly`, paths `/backups` and `/media`.

**Troubleshooting:**
- Empty list before the first 02:00 IST has passed → normal; check the loop is alive: `docker compose logs backup` should show `[backup] sleeping <N>s until next run`.
- `Fatal: unable to open repository` / auth errors → `RESTIC_REPOSITORY`, `RESTIC_PASSWORD`, or the `B2_*` keys in `.env` are wrong.
- A `[backup] FAILED — investigate (offsite copy missing for today)` line in the logs means exactly what it says: that night has **no offsite copy** — investigate the same day, not "someday".

> 💡 **Samjho aise:** Backup ka pehla snapshot dekhna waisa hi hai jaise nayi insurance policy ka pehla premium receipt haath me lena. Policy "le li" kaafi nahi hai — receipt aayi ya nahi, yeh khud confirm karna padta hai. Aur `RESTIC_PASSWORD` us policy ke locker ki chaabi hai — chaabi gayi to poori policy bekaar.

---

### Step 13 — The restore drill mandate

(`deploy/README.md` step 11 — deliberately the last line of the checklist.)

> **"Run the restore drill once before handing out worker credentials."**

A backup you have never restored is a **hope**, not a backup. The drill (full teaching version in this kit's Backups & Restore section; canonical mechanics in `deploy/README.md` §Restore drill) proves you can rebuild everything from **nothing but**: the repo + the password-manager `.env` + the restic credentials — fresh VPS → `up db redis` → `restic restore` → `pg_restore --clean --if-exists` → copy media back → `up -d` → smoke. The drill **passes only when all six steps complete unaided**, and the standing rule is to **re-run it monthly**.

Why before worker credentials specifically: the moment real workers report real pieces, the database becomes irreplaceable money-truth. You want the proof that you can resurrect it *dated before* the first irreplaceable row exists.

**First deploy is complete when:** all five containers `Up`, `verify_production` green, smoke walk passed, first restic snapshot confirmed, restore drill done once, filled `.env` in the password manager. That is the P19.5 finish line.

---

---

## 2. Environment Reference (.env)

Yeh section poore deployment ka "control panel" samjhaata hai: ek single `.env` file jo server pe rehti hai aur jisme saare secrets + settings hote hain. Code kabhi change nahi karna padta environment badalne ke liye — sirf yeh file.

### 2.1 The 12-factor idea — config code se bahar

The app follows the classic **12-factor** rule: *configuration lives in the environment, never in the code*. Matlab: `SECRET_KEY`, database password, domain name — yeh sab **code ke andar hard-code nahi** hote. Code ek hi hai (git mein, tag `erp-v1.0.0`), lekin har environment (dev laptop, production VPS) apni alag `.env` file deta hai.

> 💡 **Samjho aise:** Code ek **taala** (lock) hai jo sab jagah same hai — factory mein, dukaan mein, ghar mein. `.env` file uski **chaabi** (key) hai, aur har jagah ki chaabi alag hai. Chaabi ko taale ke saath weld nahi karte — warna taala bech diya toh chaabi bhi chali gayi. Isi liye code (taala) git mein jaata hai, `.env` (chaabi) kabhi nahi.

Concretely in this repo:

- The repo ships **`.env.example`** (a template with placeholders — safe to commit).
- On the VPS you copy it to **`.env`** and fill real values (never committed).
- `docker-compose.yml` hands `.env` to the containers: the `app` and `backup` services load it via `env_file: .env`; the `caddy` service reads `DOMAIN`; the `db` service reads `POSTGRES_DB`/`POSTGRES_USER`/`POSTGRES_PASSWORD`.

### 2.2 Why `.env` never enters git

**Security rule — read carefully (pure English on purpose):**

- `.env` contains the master secrets of the whole system: the Django `SECRET_KEY` (signs every session cookie and password-reset token), the database password, SMTP credentials, OAuth secrets, and the backup encryption password.
- Git history is **forever**. One accidental commit means the secret is in every clone, every fork, every backup of the repo — even if you delete it in the next commit. Anyone who ever gets read access to the repo gets the keys to production.
- If a secret ever lands in git: treat it as **compromised**. Rotate it (generate a new one), update `.env` on the server, restart — do not just delete the commit.
- The repo's `.gitignore` already excludes `.env`. Never "temporarily" force-add it.

> 💡 **Samjho aise:** Git history ek **CCTV recording** hai jo kabhi delete nahi hoti. Agar tumne ek second ke liye bhi apna ATM PIN camera ke saamne dikha diya, toh recording mein hamesha rahega. Isliye PIN (secret) ko camera (git) ke saamne laate hi nahi.

### 2.3 The password-manager rule — disaster-recovery pair

The filled `.env` is stored in **two places only**:

1. On the VPS at the repo root (next to `docker-compose.yml`).
2. As a secure note in your **password manager**.

Kyu? Kyunki `.env` + restic backup credentials milke **disaster-recovery pair** banate hain. Restore drill (deploy/README.md) ka starting assumption hi yehi hai: *"from NOTHING but the repo + the password-manager `.env` + restic creds"*. Agar VPS pura jal jaaye (disk gone, provider gone), tum sirf teen cheezon se poora system wapas khada kar sakte ho:

- the git repo (code),
- the `.env` copy from the password manager (secrets),
- the restic repository (encrypted DB dumps + media).

**If the password-manager copy is missing, a dead VPS = lost secrets = you cannot decrypt or reconnect anything.** Update the password-manager copy every time you change `.env` on the server — the two must never drift.

> 💡 **Samjho aise:** Ghar ki ek chaabi jeb mein, ek duplicate bank locker mein. Jeb wali kho gayi (VPS crash) toh locker wali se ghar khulta hai. Duplicate banwana bhool gaye? Toh ghar ke bahar khade raho.

### 2.4 How `.env` flows into Django settings

The chain, step by step:

```
.env  ──(docker compose env_file)──►  container environment variables
      ──(python-decouple: config('NAME'))──►  config/config/settings/base.py + production.py
      ──(dj_database_url.parse)──►  DATABASES (from the single DATABASE_URL string)
```

1. **Compose injects** every line of `.env` as an environment variable into the `app` and `backup` containers.
2. **`DJANGO_SETTINGS_MODULE=config.settings.production`** tells Django *which* settings file to load. (The Dockerfile also sets this as a container ENV, so inside Docker it is always production — this is what overrides the `wsgi.py` local default, the known DEP-F1 register.)
3. Inside the settings files, **python-decouple**'s `config()` reads each variable: `SECRET_KEY = config('SECRET_KEY')`, `ALLOWED_HOSTS = config('ALLOWED_HOSTS', ..., cast=Csv())`, and so on. Where a `default=` is given, the variable is optional; where there is **no default, the variable is mandatory** (see 2.5).
4. **`dj_database_url`** parses the single `DATABASE_URL` string (`postgres://user:password@host:5432/dbname`) into Django's `DATABASES` dict — one line instead of five separate `DB_*` values.

> 💡 **Samjho aise:** `.env` ek **order slip** hai jo waiter (compose) kitchen (container) tak le jaata hai. `decouple.config()` woh cook hai jo slip padh ke exact dish banata hai. Slip pe item missing hai aur dish "compulsory" hai? Cook kaam rok deta hai — galat khana bhejne se accha hai order hi refuse karna. (Woh next section hai.)

### 2.5 Fail-fast variables — crashing on purpose is a feature

Two variables in `config/config/settings/production.py` are read **without a default**:

- `SECRET_KEY = config('SECRET_KEY')` — no fallback, no insecure default.
- `CACHES → LOCATION: config('REDIS_URL')` — no fallback.

If either is missing from `.env`, the app **crashes at boot** with a loud `UndefinedValueError`. That is intentional, and it is a *feature*, not a bug:

- **SECRET_KEY:** a silent fallback (e.g. an insecure dev key) would mean every session cookie and password-reset token in production is signed with a publicly known key — an attacker could forge logins. Crashing at startup is infinitely better than running insecure for weeks without anyone noticing.
- **REDIS_URL:** the **auth rate limiter stores its counters in the default cache**. If Django silently fell back to per-process LocMem cache, each of the 3 gunicorn workers would keep its *own* counter — the brute-force limit would silently become ~3× weaker. Fail-fast guarantees the shared Redis cache is really there.

The rest of the stack follows the same philosophy: `deploy/entrypoint.sh` waits up to 120 seconds for a **healthy** DB and Redis and *fails loudly* rather than booting half-up.

> 💡 **Samjho aise:** Gas cylinder ka regulator dhang se fit nahi hua? Accha chulha **jalta hi nahi** — halka-halka leak karke chalte rehne se better hai bilkul start na hona. Crash-at-boot = regulator check. Tumhe problem *turant* dikh jaati hai, mahine baad accident nahi hota.

### 2.6 Variable-by-variable reference

Every variable in `.env.example`, what it does, and how to treat it. **Placeholders only — replace all `replace_with_*` values.**

| Variable | Purpose | Placeholder example | Security note |
|---|---|---|---|
| `DJANGO_SETTINGS_MODULE` | Tells Django to load the production settings file (`config/config/settings/production.py`) — DEBUG off, HTTPS hardening on. | `config.settings.production` | Not secret, but wrong value = dev settings in production (DEBUG pages leak internals). Never change it on the server. |
| `SECRET_KEY` | Django's master signing key — sessions, CSRF, password-reset tokens all depend on it. **Fail-fast: app refuses to boot if missing.** | `replace_with_50_plus_char_secret_key` | TOP secret. 50+ random chars. Leak = attackers can forge logins. Rotate if ever exposed (all users get logged out — acceptable). |
| `ALLOWED_HOSTS` | Hostnames Django will answer for; anything else gets HTTP 400. Blocks Host-header attacks. | `erp.example.com` | Must exactly match your real domain. Comma-separated if multiple. Never use `*` in production. |
| `CSRF_TRUSTED_ORIGINS` | Origins Django trusts for HTTPS form posts behind the TLS proxy (Caddy). Comma-separated, **scheme included**. | `https://erp.example.com` | Must be `https://` + the same domain. Missing/wrong = every form submit fails with CSRF 403. |
| `DATABASE_URL` | Single connection string for PostgreSQL, parsed by `dj_database_url`. Host is `db` — the compose service name, not an IP. | `postgres://kapil:replace_with_postgres_password@db:5432/kapil` | Contains the DB password — **must match `POSTGRES_PASSWORD` below** or the app can never connect. |
| `REDIS_URL` | Shared cache + auth rate-limiter counter store. **Fail-fast: app refuses to boot if missing.** | `redis://redis:6379/0` | Host is `redis` (compose service name). Redis is never published to the internet — internal network only. |
| `LEDGER_CREDIT_AT_ALLOCATION` | Feature-flag **rollback lever** (ADR-0007). `False` = certified default: worker earnings book ONLY at Adda settlement. `True` = restores legacy allocation-time crediting. | `False` | Not a secret, but a money-behavior switch. Flip only per deploy/README.md rollback procedure — never casually. |
| `EMAIL_HOST` | SMTP server that sends the app's emails (password resets, verification). | `smtp.gmail.com` | Not secret by itself; pairs with the credentials below. |
| `EMAIL_PORT` | SMTP port. 587 = STARTTLS (encrypted connection). | `587` | Keep 587 unless your provider says otherwise. |
| `EMAIL_HOST_USER` | The sending mailbox / SMTP username. | `replace_with_smtp_user@example.com` | Semi-secret (it's an identity). |
| `EMAIL_HOST_PASSWORD` | SMTP password — for Gmail this is an **app password**, never your real account password. | `replace_with_smtp_app_password` | Secret. Leak = someone can send mail as you. Rotate at the provider if exposed. |
| `GOOGLE_CLIENT_ID` | Google OAuth app ID for "Login with Google". | `replace_with_google_oauth_client_id` | Public-ish identifier, but keep it in `.env` with its pair. |
| `GOOGLE_CLIENT_SECRET` | Google OAuth app secret — proves to Google that login requests come from *your* app. | `replace_with_google_oauth_client_secret` | Secret. Leak = someone can impersonate your OAuth app. Rotate in Google Cloud Console if exposed. |
| `DOMAIN` | Read by the **Caddy** container — the hostname it serves and automatically gets a Let's Encrypt certificate for. | `erp.example.com` | Must match `ALLOWED_HOSTS`/`CSRF_TRUSTED_ORIGINS`, and the DNS A record must already point at the server **before** first start, or certificate issuance fails. |
| `POSTGRES_DB` | Database name the `db` container creates on first boot. | `kapil` | Must match the db name inside `DATABASE_URL`. |
| `POSTGRES_USER` | Database superuser the `db` container creates. | `kapil` | Must match the user inside `DATABASE_URL`. |
| `POSTGRES_PASSWORD` | Password for that DB user — set on the very first boot of the `db` container. | `replace_with_postgres_password` | Secret. **Must be byte-identical to the password inside `DATABASE_URL`.** Changing it later requires changing it inside PostgreSQL too, not just here. |
| `RESTIC_REPOSITORY` | Where restic stores encrypted off-site backups — Backblaze B2 bucket by default; use an `s3:` URI (e.g. `s3:https://example-backup`) for Cloudflare R2. | `b2:kapil-erp-backups:/` | Not secret, but pair it with the two keys below. The backup container runs `restic init` here on first run. |
| `RESTIC_PASSWORD` | Encrypts every backup. Restic backups are useless without it — **losing this password = losing ALL backups permanently.** | `replace_with_restic_encryption_password` | The single most unforgiving secret in this file. MUST live in the password manager. There is no reset, no recovery, no support ticket. |
| `B2_ACCOUNT_ID` | Backblaze B2 application key ID — lets restic talk to the bucket. | `replace_with_b2_key_id` | Semi-secret; pairs with the key below. |
| `B2_ACCOUNT_KEY` | Backblaze B2 application key (the actual credential). | `replace_with_b2_application_key` | Secret. Leak = someone can read/delete your backup bucket. Rotate in the B2 console if exposed. |

**Three values that must always agree** (most common first-deploy mistake): the domain in `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` (with `https://`), and `DOMAIN` must all be the same hostname. And the password inside `DATABASE_URL` must equal `POSTGRES_PASSWORD`.

### 2.7 Feature-flag levers — what they mean, and why most stay OFF

The system has behavior switches read from the environment (all defined in `config/config/settings/base.py` with safe defaults):

| Flag | Default | Meaning |
|---|---|---|
| `LEDGER_CREDIT_AT_ALLOCATION` | `False` | **The ADR-0007 rollback lever.** `False` (certified) = worker earnings enter the ledger only at Adda settlement. Setting `True` in `.env` + restart rolls back to legacy allocation-time crediting — **no deploy, no schema change**, and a cross-era double-credit guard protects both directions. This is the only flag present in `.env.example`, because it is the designated emergency lever. |
| `ENFORCE_ALLOCATION_BOUND` | `False` | When ON, refuses work completion that exceeds the allocated pool. **Stays OFF until the post-deploy soak period**, per the enforcement rollout runbook. |
| `ENFORCE_SETTLEMENT_RECONCILIATION` | `False` | When ON, blocks settlement finalize on over-allocation beyond tolerance (super-admin audited override exists). **Stays OFF until soak.** |
| `SETTLEMENT_RECONCILIATION_TOLERANCE` | `0` | Tolerance for the reconciliation block above. |
| `REQUIRE_APPROVED_LAYOUT` | `False` | Layout-approval gate. OFF. |
| `ENFORCE_LAYOUT_RECONCILIATION` | `False` | Layout reconciliation gate. OFF. |
| `LAYOUT_RECONCILIATION_TOLERANCE` | `0` | Tolerance for the layout gate. |

The `ENFORCE_*` flags are deliberately **not** in `.env.example`: their built-in default is the correct production value (`False`) for the first deploy. Deploy OFF → soak → resolve findings → enable. Do not add them to `.env` until the runbook stage that says so.

> 💡 **Samjho aise:** Naye flat mein shift hote hi saare strict house-rules pehle din se enforce nahi karte — pehle 2 hafte dekhte ho ki daily routine kaisa hai, phir rules on karte ho. `ENFORCE_*` flags wahi 2-hafte-wala patience hain. Aur `LEDGER_CREDIT_AT_ALLOCATION` woh ek emergency switch hai jo main-board pe isliye laga hai taaki bijli ka masla ho toh bina wiring khole purane mode pe aa sako.

### 2.8 Generating a strong SECRET_KEY

```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

- **What it does:** asks Django's own utility to print one cryptographically random 50-character key — the exact generator Django uses for new projects.
- **Why it exists:** humans are terrible at inventing randomness; a guessable SECRET_KEY breaks all of Django's signing. This gives you a key with real entropy in one line.
- **What success looks like:** one line of ~50 random characters printed to the terminal, e.g. `django-insecure`-free gibberish like `k3(x!...` (yours will differ every run). Copy it into `.env` as `SECRET_KEY=<that value>` — no quotes needed.
- **Troubleshooting:** `ModuleNotFoundError: No module named 'django'` means Django isn't installed in that Python (normal on a fresh VPS). Use the pure-standard-library alternative instead — no installs required:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
```

Same idea (`secrets` = Python's cryptographic randomness module), produces an 86-character URL-safe key — longer is fine, the requirement is 50+ chars. Generate it **once**, store it in `.env` and the password manager, and never regenerate casually: changing SECRET_KEY invalidates every active session (all users logged out) and every outstanding password-reset link.

### 2.9 The template file itself

The enriched template lives at [`.env.example`](.env.example) in the repo root — same 21
variables as the certified original, same names, same order, with a purpose + security
comment above every variable and obvious `replace_with_*` placeholders. It is the single
canonical template: on the VPS, `cp .env.example .env`, replace every placeholder, and
verify with `grep -c 'replace_with' .env` → `0` (§1 Step 7).

---

> ⚠️ **These three files are certified frozen release bytes (`erp-v1.0.0`).** They are reproduced below exactly as they exist in the repo so you can learn them. **Do NOT edit them** — if something needs changing, that is a new release decision, not a deploy step. The terse expert runbook lives at [`deploy/README.md`](deploy/README.md); this document is the teaching layer on top of it.

---

## 3. docker-compose.yml — the five services, explained

File: **`docker-compose.yml`** (repo root). Yeh file hi production hai — dev mein Docker kabhi use nahi hota. Ek single VPS pe poora stack yahi file define karti hai.

> 💡 **Samjho aise:** docker-compose.yml ek *building ka naksha* hai. Har `service` = ek flat in the building (Caddy, Django app, Postgres, Redis, backup robot). Compose us naksha ko padh ke poori building ek command mein khadi kar deta hai — `docker compose up -d` — aur har flat ko pata hota hai baaki flats kahan hain.

### The file, verbatim

```yaml
# Kapil Enterprises ERP — single-VPS production stack (direction C, 2026-06-11).
# Exact-pinned images (owner rule #1). Only caddy publishes ports. App waits for
# HEALTHY db+redis via depends_on condition AND its own entrypoint wait-loop
# (owner rule #2). Volumes: pgdata + media are the business — backed up nightly.

services:
  caddy:
    image: caddy:2.9.1
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    environment:
      DOMAIN: ${DOMAIN}
    volumes:
      - ./deploy/Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy_data:/data
      - caddy_config:/config
    depends_on:
      - app

  app:
    build: .
    restart: unless-stopped
    env_file: .env
    volumes:
      - media:/srv/app/config/media
    expose:
      - "8000"
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy

  db:
    image: postgres:16.6-alpine
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $${POSTGRES_USER} -d $${POSTGRES_DB}"]
      interval: 5s
      timeout: 3s
      retries: 12

  redis:
    image: redis:7.4.2-alpine
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 12

  backup:
    # postgres-alpine base gives us the matching pg_dump; restic added at boot
    # (one apk install — accepted tradeoff, noted in deploy/README).
    image: postgres:16.6-alpine
    restart: unless-stopped
    entrypoint: ["/bin/sh", "/srv/backup.sh"]
    env_file: .env
    volumes:
      - ./deploy/backup.sh:/srv/backup.sh:ro
      - backups:/backups
      - media:/media:ro
    depends_on:
      db:
        condition: service_healthy

volumes:
  pgdata:
  media:
  caddy_data:
  caddy_config:
  backups:
```

### 3.1 The five services, one by one

#### `caddy` — the front door (TLS terminator)

| Line | Meaning |
|---|---|
| `image: caddy:2.9.1` | Exact-pinned version (owner rule #1 — no floating `latest` tags). Same bytes on every machine, forever reproducible. |
| `ports: "80:80", "443:443"` | **The ONLY service that publishes ports to the internet.** Port 80 = plain HTTP (needed for the Let's Encrypt challenge + redirect), 443 = HTTPS. |
| `environment: DOMAIN: ${DOMAIN}` | Compose reads `DOMAIN` from your root `.env` file and hands it to the Caddy container. The Caddyfile then substitutes it (see §5). |
| `./deploy/Caddyfile:/etc/caddy/Caddyfile:ro` | A **bind mount**: the repo's Caddyfile appears inside the container. `:ro` = read-only — container can never modify your repo file. |
| `caddy_data:/data` | Named volume where Caddy stores **Let's Encrypt certificates**. Delete this and Caddy must re-request certs (rate limits apply!) — leave it alone. |
| `caddy_config:/config` | Caddy's own runtime config state. Small, boring, but keep it. |
| `depends_on: - app` | Plain form (no `condition:`) = **start-order only**. Caddy starts after the app *container is started* — it does not wait for the app to be healthy. That's fine: if the app is still booting, Caddy returns a temporary 502 and recovers on its own. |

- **Why it exists:** HTTPS. Browsers ↔ Caddy speak encrypted TLS; Caddy ↔ app speak plain HTTP privately inside Docker's network. Gunicorn kabhi bhi seedha internet pe nahi aata.

#### `app` — the Django ERP itself

| Line | Meaning |
|---|---|
| `build: .` | No pre-made image — Compose builds it from the repo-root `Dockerfile` (§4). `docker compose build app` rebuilds after a `git pull`. |
| `env_file: .env` | Injects **every** variable from your root `.env` into the container: `SECRET_KEY`, `DATABASE_URL`, `REDIS_URL`, email creds, feature flags — everything. This is how secrets reach Django without ever being baked into the image. |
| `volumes: media:/srv/app/config/media` | Named volume for **user-uploaded files** (product photos etc.). Container is disposable; uploads are not — so uploads live in the volume, not the container. |
| `expose: "8000"` | Announces port 8000 to *other containers only*. **NOT** reachable from the internet (see §3.3). |
| `depends_on: db/redis: condition: service_healthy` | The app container will not even start until Postgres AND Redis have **passed their healthchecks** (see §3.2). |

- **Why it exists:** it is the product. Everything else in this file exists to serve, feed, protect, or back up this one service.

#### `db` — PostgreSQL 16.6 (the memory of the business)

| Line | Meaning |
|---|---|
| `image: postgres:16.6-alpine` | Exact-pinned. `alpine` = small variant. Version matters: `pg_dump`/`pg_restore` should match major version (that's why `backup` uses the *same* image). |
| `environment: POSTGRES_DB/USER/PASSWORD` | On **first boot with an empty `pgdata` volume**, the official Postgres image creates this database + user with this password. These come from `.env` and MUST match the credentials inside `DATABASE_URL`. |
| `volumes: pgdata:/var/lib/postgresql/data` | THE database files. This volume **is** the business (settlements, ledgers, inventory — everything). |
| `healthcheck: pg_isready ...` | Explained in §3.2. Note `$${POSTGRES_USER}` — the double `$$` tells *Compose* "don't substitute this yourself; pass a literal `$` so the shell **inside the container** expands it at check time." |

- **Why it exists:** Django is stateless by design here; every fact lives in Postgres. Lose the container → nothing lost. Lose `pgdata` → restore from backup (Part on backups covers this).

#### `redis` — the shared short-term memory

| Line | Meaning |
|---|---|
| `image: redis:7.4.2-alpine` | Exact-pinned, tiny. |
| `healthcheck: redis-cli ping` | Redis answers `PONG` when alive. Same 5s/3s/12 timing as db. |

- **Why it exists (not optional!):** production settings put Django's cache in Redis, and the **auth rate limiter stores its brute-force counters in that cache**. With 3 gunicorn workers, a per-process local cache would silently weaken the rate limiter 3× (each worker counting separately). Redis = one shared counter for all workers. `production.py` fail-fasts if `REDIS_URL` is missing — deliberately.
- No published ports, no password needed: it is reachable **only** from inside the compose network.

#### `backup` — the nightly robot

| Line | Meaning |
|---|---|
| `image: postgres:16.6-alpine` | Same image as `db` on purpose → its `pg_dump` exactly matches the server version. Restic is installed at container boot via `apk add` (one accepted-unpinned tradeoff, on record in `deploy/README.md`). |
| `entrypoint: ["/bin/sh", "/srv/backup.sh"]` | The container does not run Postgres at all — it runs the backup loop script forever (nightly ~02:00 IST dump + restic offsite push). |
| `env_file: .env` | Needs `POSTGRES_*` (to dump) and `RESTIC_*`/`B2_*` (to push offsite). |
| `./deploy/backup.sh:/srv/backup.sh:ro` | Bind-mounts the script read-only from the repo. |
| `backups:/backups` | Local dump storage (3 newest kept). |
| `media:/media:ro` | Reads the app's media volume **read-only** so restic can back up uploads too. `:ro` guarantees the backup job can never corrupt live uploads. |
| `depends_on: db: condition: service_healthy` | No point starting the dumper before the database is answering. |

- **Why it exists:** RPO 24h — worst case, you lose at most one day of data. The full mechanics live in the backups section of this kit and in `deploy/backup.sh`.

### 3.2 `restart`, `healthcheck`, and `depends_on` — the self-healing trio

**`restart: unless-stopped`** (on every service):
- **What:** if a container crashes, Docker restarts it automatically. If the whole VPS reboots, Docker brings the stack back up when the Docker daemon starts.
- **Why `unless-stopped` and not `always`:** if YOU deliberately ran `docker compose stop`, it stays stopped — even across a reboot. Docker respects your explicit decision.
- **Consequence:** no systemd unit files are required for the app. One-time `systemctl enable docker` on the VPS is enough — then `restart: unless-stopped` handles the rest (covered in the VPS-prep part of this kit).

> 💡 **Samjho aise:** `unless-stopped` matlab ek diligent chowkidar — light chali jaye (crash/reboot) toh sab kuch wapas chalu kar dega, lekin agar maalik ne khud bola "band karo" (`docker compose stop`), toh bina order ke wapas start nahi karega.

**`healthcheck` semantics** (db and redis both use `interval: 5s / timeout: 3s / retries: 12`):
- **`test`** — the command Docker runs *inside* the container. `pg_isready` asks Postgres "accepting connections?"; `redis-cli ping` expects `PONG`. Exit code 0 = pass.
- **`interval: 5s`** — run the test every 5 seconds.
- **`timeout: 3s`** — if a single test hangs longer than 3s, count it as a failure.
- **`retries: 12`** — 12 *consecutive* failures flip the container's status to `unhealthy`. So the stack tolerates roughly `12 × 5s = 60 seconds` of startup grace before declaring a problem.
- **See it live:** `docker compose ps` shows `(healthy)` / `(health: starting)` / `(unhealthy)` next to each service.

**How `depends_on` + `condition: service_healthy` uses it:**
- Plain `depends_on: - app` (caddy) = "start after that container starts" — nothing more.
- `depends_on: db: condition: service_healthy` (app, backup) = "do not even start me until that service's **healthcheck has passed**." So Django never boots against a Postgres that is still initializing.
- **Belt AND braces (owner rule #2):** the app additionally runs its own wait-loop in `deploy/entrypoint.sh` (up to 120s for db + redis) before migrating. Compose gates the *start*; the entrypoint verifies *real connections* from inside the app itself. Either alone could miss an edge case; together they guarantee the app never boots half-up.

### 3.3 `expose` vs `ports` — the security boundary

```yaml
# caddy — PUBLISHED to the internet:
ports:
  - "80:80"
  - "443:443"

# app — visible ONLY to other containers:
expose:
  - "8000"
```

- **`ports: "443:443"`** = "bind VPS port 443 → container port 443." Anyone on the internet can reach it. This is a *publish*.
- **`expose: "8000"`** = documentation + inter-container visibility only. Port 8000 is reachable **only** by other containers on the same compose network (Caddy). It is **not** bound on the VPS at all — `curl http://SERVER_IP:8000` from outside simply fails.
- **Why this is the security boundary:** Django trusts the `X-Forwarded-Proto` header (see §5.2) *precisely because* only Caddy can talk to gunicorn. If gunicorn were published directly, an attacker could send that header themselves and spoof "this request was HTTPS." Postgres and Redis publish nothing either — no internet-facing database, no internet-facing cache, ever.

> 💡 **Samjho aise:** `ports` = building ka main gate jo road pe khulta hai. `expose` = flats ke beech ka internal corridor door — building ke andar wale use kar sakte hain, road se koi nahi. Sirf Caddy ke paas main gate hai; baaki sab corridor se hi baat karte hain.

### 3.4 `env_file` vs `environment`

- **`env_file: .env`** (app, backup) — bulk-load *every* variable from the `.env` file into the container. Used where the process needs many secrets (Django needs ~15 vars; backup needs Postgres + restic creds). The file itself never enters the image — it is injected at container start.
- **`environment:`** (caddy, db) — hand-pick specific variables. `${DOMAIN}` / `${POSTGRES_DB}` etc. are substituted **by Compose** from the same root `.env` at `up` time. Used where a container should see *only* what it needs — Caddy has no business knowing your `SECRET_KEY`.
- **Principle:** least exposure. Har container ko sirf utna hi environment do jitna usko kaam ke liye chahiye.

### 3.5 The five named volumes — what actually lives where

```yaml
volumes:
  pgdata:        # PostgreSQL data files — THE BUSINESS
  media:         # user uploads (product photos, files) — THE BUSINESS
  caddy_data:    # Let's Encrypt certificates + ACME account
  caddy_config:  # Caddy runtime config state
  backups:       # local pg_dump archives (3 newest), staging area before restic offsite
```

- **`pgdata` + `media` ARE the business** — the compose header comment says it in plain words. Every container, image, and even the VPS itself is replaceable from the git repo + `.env`; these two volumes are the only state you cannot regenerate. Both are what `backup.sh` protects nightly (dump of pgdata's contents + restic copy of `/backups` and `/media`).
- `caddy_data` is *convenience* state — losing it forces certificate re-issuance (annoying, rate-limited, but recoverable).
- `backups` is your local safety net — the newest `predeploy-*.dump` there is the **rollback anchor** for every deploy (`deploy/deploy.sh` creates it before pulling code).
- Named volumes live under Docker's control (`docker volume ls` to see them). They survive `docker compose down`, image rebuilds, and container recreation. Only `docker compose down -v` deletes them — **never run `down -v` in production.**

> 💡 **Samjho aise:** containers = staff, volumes = godown. Staff ko kabhi bhi replace kar sakte ho (naya container), lekin godown mein rakha maal (pgdata ka data, media ki photos) hi asli business hai. Isliye backup robot roz raat ko godown ka hi backup leta hai, staff ka nahi.

### 3.6 The invisible network — how `app:8000` and `db` work

Notice the file defines **no `networks:` section** — and yet Caddy finds the app at `app:8000`, and Django's `DATABASE_URL` says `@db:5432`. How?

- Compose automatically creates **one default network** for the project and attaches all five services to it.
- On that network, Docker runs a built-in DNS server: **each service name is a hostname**. `db` resolves to the Postgres container's internal IP, `redis` to Redis, `app` to the Django container.
- That is why the certified `.env.example` uses `DATABASE_URL=postgres://kapil:replace_with_postgres_password@db:5432/kapil` and `REDIS_URL=redis://redis:6379/0` — `db` and `redis` are not magic keywords, they are simply the service names from this file.
- And the Caddyfile's `reverse_proxy app:8000` = "forward to the container named `app`, on its exposed port 8000."
- These names work **only inside** the compose network — from the VPS shell, `curl http://app:8000` fails (use `docker compose exec` to get inside).

> 💡 **Samjho aise:** compose network ek office ka internal phone directory hai. "db" bolo toh line seedha Postgres ke desk pe lagti hai — extension number (IP) yaad rakhne ki zarurat nahi, aur bahar ke log (internet) is directory ko use hi nahi kar sakte.

---

## 4. Dockerfile — every instruction

File: **`Dockerfile`** (repo root). This is the recipe Compose follows when you run `docker compose build app`. It turns the repo into a runnable image.

> 💡 **Samjho aise:** Dockerfile ek recipe card hai, image ek ready tiffin. Recipe ek baar likh do, tiffin har server pe bilkul same banta hai — "mere laptop pe toh chal raha tha" problem hamesha ke liye khatam.

### The file, verbatim

```dockerfile
# Kapil Enterprises ERP — production app image (deploy direction C, 2026-06-11).
# Exact-pinned base (owner rule: no floating tags). All Python deps ship wheels
# (psycopg2-binary, Pillow, argon2-cffi, reportlab) → no compiler, single stage.
FROM python:3.10.16-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DJANGO_SETTINGS_MODULE=config.settings.production

# Layer-cache deps separately from app code.
COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

# Non-root runtime user. Apps are importable top-level from config/ (the repo's
# documented working dir — see .importlinter header), so that's the WORKDIR.
RUN useradd --create-home --uid 1000 app
COPY --chown=app:app config /srv/app/config
WORKDIR /srv/app/config

# Writable dirs the app touches at import/runtime: logs/ (base.py mkdir),
# staticfiles/ (collectstatic at entrypoint), media/ (named volume mounts here).
RUN mkdir -p logs staticfiles media && chown -R app:app logs staticfiles media

COPY --chown=app:app deploy/entrypoint.sh /srv/app/entrypoint.sh
RUN chmod +x /srv/app/entrypoint.sh

USER app
EXPOSE 8000
ENTRYPOINT ["/srv/app/entrypoint.sh"]
# 3 sync workers fits a 2-4GB box; access/error logs → stdout (PD logging rule).
CMD ["gunicorn", "config.wsgi:application", \
     "--bind", "0.0.0.0:8000", "--workers", "3", \
     "--access-logfile", "-", "--error-logfile", "-"]
```

### 4.1 Line by line

**`FROM python:3.10.16-slim` — the base image, exact-pinned**
- **What:** start from the official Python image, `slim` variant (smaller — no compilers, no docs).
- **Why the full `3.10.16` pin (owner rule #1):** a floating tag like `python:3.10` silently changes underneath you on rebuild — today's working image and next month's broken image would both be "the same tag." Exact pin = today's build and next year's rebuild produce the same base. Upgrades happen only as a deliberate, reviewed edit.
- **Why `slim` works here (header comment):** every Python dependency ships pre-built *wheels* (`psycopg2-binary`, `Pillow`, `argon2-cffi`, `reportlab`), so nothing needs compiling → no gcc, no multi-stage build, one simple stage.

**`ENV ...` — the four environment variables**
| Var | What it does | Why |
|---|---|---|
| `PYTHONDONTWRITEBYTECODE=1` | Python skips writing `.pyc` cache files | Useless clutter inside an immutable container |
| `PYTHONUNBUFFERED=1` | print/log output flushes immediately, no buffering | Crash hone pe last log line bhi dikhni chahiye — buffered output crash ke saath kho jaata hai. `docker compose logs` real-time rehta hai |
| `PIP_NO_CACHE_DIR=1` | pip keeps no download cache | Smaller image — you never pip-install again inside a running container anyway |
| `DJANGO_SETTINGS_MODULE=config.settings.production` | Forces **production settings** for every process in this image | Container mein galti se bhi `local.py` (DEBUG=True) load nahi ho sakta. Honest footnote (DEP-F1, open register): `config/config/wsgi.py` defaults to `config.settings.local` — this ENV **overrides** that default inside the container, which is exactly why the wsgi file is safe to leave untouched. |

**`COPY requirements.txt /tmp/requirements.txt` + `RUN pip install ...` — the layer-cache trick**
- **What:** copy *only* the requirements file first, install dependencies, and only *afterwards* copy the application code.
- **Why the order matters:** Docker builds in **layers** and reuses a cached layer when its inputs are unchanged. Dependencies change rarely; app code changes every deploy. By splitting them, a normal deploy rebuild (`docker compose build app` in `deploy.sh`) skips the slow `pip install` entirely and rebuilds in seconds. If deps and code were copied together, every one-line code change would re-download every package.

> 💡 **Samjho aise:** yeh waise hi hai jaise tiffin banate waqt masala ka dabba pehle se taiyar rakhna. Roz sabzi (code) badalti hai, masala (dependencies) nahi — toh masala roz peesne ki zarurat nahi, dabba wahi ka wahi use karo. Kaam 10x fast.

**`RUN useradd --create-home --uid 1000 app` — the non-root user**
- **What:** creates a normal Linux user called `app` with uid 1000.
- **Why non-root (security):** if an attacker ever exploits the Django process, they land as an unprivileged user — they cannot install packages, rewrite the image, or touch root-owned files. Running app processes as root inside containers is a classic, avoidable mistake.
- **Why uid 1000 specifically:** it's the first regular-user uid on most Linux systems (your VPS user is typically 1000 too), which keeps file ownership sane across the volume boundary — files written into mounted volumes carry a predictable, non-root uid.

**`COPY --chown=app:app config /srv/app/config` + `WORKDIR /srv/app/config`**
- **What:** copies the repo's `config/` directory (the whole Django project — all 8 domain apps + core + settings) into the image, owned by `app`, then makes it the working directory.
- **Why this exact WORKDIR:** the repo's documented convention (see the `.importlinter` header) is that Django apps are importable top-level *from inside `config/`* — `manage.py` lives there, imports resolve there. Running from anywhere else would break imports. Every runtime command (`gunicorn config.wsgi:application`, `manage.py migrate` in the entrypoint) assumes this directory.
- `--chown=app:app` sets ownership at copy time — cheaper than a separate `chown -R` layer.

**`RUN mkdir -p logs staticfiles media && chown -R app:app ...` — the three writable dirs**
The image is otherwise effectively read-only for the `app` user; these are the only places it writes:
- `logs/` — `base.py` creates/uses a logs dir at import time; it must exist and be writable (production actually streams logs to stdout, but the import-time expectation stands).
- `staticfiles/` — target of `collectstatic --noinput`, which the entrypoint runs on every boot.
- `media/` — **mount point** for the `media` named volume from docker-compose.yml. The directory in the image is just an empty placeholder; at runtime the volume overlays it, so uploads persist outside the container.

**`COPY ... entrypoint.sh` + `RUN chmod +x` — the boot script**
- Copies `deploy/entrypoint.sh` into the image and makes it executable. Its job (taught in its own section of this kit): wait up to 120s for genuinely-connectable db + redis → `migrate --noinput` → `collectstatic --noinput` → hand over to gunicorn. Fails loudly rather than booting half-up.

**`USER app`**
- Every instruction *after* this line — and, crucially, the **running container process** — executes as `app`, not root. Root was only used for setup (installing packages, creating dirs).

**`EXPOSE 8000` — documentation, not publishing**
- **What it does NOT do:** it opens no port anywhere. It is metadata — a note to humans and tooling that "this image listens on 8000."
- The actual reachability decisions live in docker-compose.yml: `expose: "8000"` (container-to-container) vs `ports:` (internet). See §3.3. Common beginner trap: thinking `EXPOSE` publishes a port. It never does.

**`ENTRYPOINT` + `CMD` — how they combine**
```
ENTRYPOINT ["/srv/app/entrypoint.sh"]     ← always runs
CMD ["gunicorn", "config.wsgi:application", ...]  ← passed to it as arguments
```
- Docker concatenates them: the container actually runs `entrypoint.sh gunicorn config.wsgi:application --bind ... `. The entrypoint script does its checks + migrations, then ends with an *exec* of "whatever arguments it received" — i.e., gunicorn.
- **Why split them:** ENTRYPOINT = the mandatory ritual (wait for deps, migrate, collectstatic — must happen every boot, no exceptions). CMD = the default main process, overridable when needed — e.g. `docker compose run --rm app python manage.py shell` replaces just the CMD while the ENTRYPOINT ritual still runs first.

> 💡 **Samjho aise:** ENTRYPOINT = ghar ka darwaza — andar aana hai toh isi se aana padega (checks + migrations mandatory). CMD = andar aake by-default kya karoge (gunicorn chalana) — chahein toh aaj kuch aur kaam bol do (`manage.py shell`), lekin darwaza wahi rahega.

**The gunicorn command — flag by flag**
| Flag | Meaning |
|---|---|
| `config.wsgi:application` | The WSGI entry object — module `config.wsgi`, variable `application`. This is the handle Django gives web servers. |
| `--bind 0.0.0.0:8000` | Listen on all interfaces *of the container*, port 8000. `0.0.0.0` is safe **only because** compose never publishes 8000 to the internet — Caddy is the sole client (§3.3). |
| `--workers 3` | **3 synchronous worker processes** = 3 requests served truly in parallel. Sizing follows the classic rule of thumb (≈ 2×CPU+1) and the in-file comment: it fits the certified 2–4 GB VPS — each worker holds a full Django process in RAM, so more workers on a small box would swap and get *slower*, not faster. Do not tune this casually; it is part of the certified release. |
| `--access-logfile - --error-logfile -` | `-` means **stdout/stderr** instead of files (the "PD logging rule"). In Docker, stdout is the log system: `docker compose logs -f app` shows everything, nothing hides in files inside a disposable container, and no log file ever fills the container's disk. |

---

## 5. Caddyfile — HTTPS in four lines

File: **`deploy/Caddyfile`**. The entire TLS story of this deployment fits in one screen — that brevity is Caddy's whole selling point.

### The file, verbatim

```caddyfile
# The ONE TLS-terminating proxy (PD's SECURE_PROXY_SSL_HEADER assumption).
# Caddy auto-provisions Let's Encrypt for {$DOMAIN} and sets X-Forwarded-Proto.
{$DOMAIN} {
	encode gzip
	reverse_proxy app:8000
}
```

Four working lines. Compare: the equivalent nginx + certbot setup is ~50 lines plus a cron job plus a renewal script. Caddy does certificates, renewal, HTTP→HTTPS redirect, and proxy headers **by default**.

### 5.1 Automatic HTTPS — how the certificate appears out of thin air

When Caddy starts and sees a real domain name as the site address, it automatically:
1. Generates a key pair and asks **Let's Encrypt** (a free, automated certificate authority) for a certificate for that domain.
2. Let's Encrypt answers with a challenge — the standard one is **ACME HTTP-01**: *"prove you control this domain: serve this exact token at `http://your-domain/.well-known/acme-challenge/...` and I'll check."*
3. Let's Encrypt's servers **resolve your domain via public DNS and connect to it on port 80**. Caddy (already listening on 80 — that's one reason compose publishes it) serves the token.
4. Proof accepted → certificate issued → Caddy starts serving HTTPS on 443 and auto-redirects HTTP→HTTPS. It also **renews automatically** before expiry, forever. No cron, no certbot, no reminder needed.

**Why DNS must resolve BEFORE first start (owner P19.5 item 3):** step 3 is Let's Encrypt *dialing your domain from the outside*. If the DNS A record does not yet point at your VPS, the challenge connects to nothing (or to the wrong machine), issuance fails, and Caddy retries in a loop — and repeated failures burn against Let's Encrypt **rate limits**. Correct order: create the A record → wait for it to resolve (`dig +short erp.example.com` should print your SERVER_IP, e.g. `203.0.113.10`) → only then `docker compose up -d`.

**Where the certificates live:** in the **`caddy_data` named volume** (mounted at `/data`, §3.5) — along with the ACME account key. Because it is a persistent volume, restarts and rebuilds re-use the existing certificate instead of re-asking Let's Encrypt. Deleting that volume forces reissuance and eats into the rate limits — don't.

> 💡 **Samjho aise:** Let's Encrypt ek notary hai jo free mein stamp deta hai, lekin pehle proof maangta hai: "yeh address (domain) sach mein tumhara hai?" Woh proof lene khud tumhare address pe aata hai (DNS → port 80). Address pe naam ki plate hi nahi lagi (DNS record missing) toh notary wapas chala jaata hai. Isliye pehle plate lagao, phir dukan kholo.

**Troubleshooting first-start TLS:** `docker compose logs caddy` — look for `obtaining certificate` / ACME errors. Almost always the cause is: DNS not resolving yet, port 80/443 blocked by the firewall (ufw must allow 22, 80, 443), or `DOMAIN` misspelled in `.env`.

### 5.2 `{$DOMAIN}` — one placeholder, zero hardcoding

`{$DOMAIN}` is Caddy's environment-variable substitution syntax. The chain:

```
.env (root):            DOMAIN=erp.example.com
docker-compose.yml:     environment: DOMAIN: ${DOMAIN}    ← compose injects it into the caddy container
Caddyfile:              {$DOMAIN} { ... }                 ← caddy substitutes it at startup
```

Result: the site address becomes `erp.example.com` without the domain ever being written into a tracked file. Change domains? Edit one line of `.env`, `docker compose up -d` — the certified Caddyfile never changes.

### 5.3 `reverse_proxy app:8000` — and the header handshake with Django

- **What it does:** every request Caddy receives (after TLS decryption) is forwarded over plain HTTP to `app:8000` — the Django container's gunicorn, addressed by compose-network DNS (§3.6). Responses flow back through Caddy, which re-encrypts them to the browser.
- **What it adds silently:** Caddy's `reverse_proxy` sets standard proxy headers on every forwarded request, including **`X-Forwarded-Proto: https`** — "dear backend, the *original* browser connection was HTTPS (I terminated it)."

**Why Django needs that header — the redirect-loop failure mode.** From the certified `config/config/settings/production.py`:

```python
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
```

- `SECURE_SSL_REDIRECT = True` tells Django: any request that is *not* HTTPS → answer with a redirect to the HTTPS URL.
- But from gunicorn's chair, **every** request looks like plain HTTP — because the Caddy→app hop *is* plain HTTP; TLS ended at Caddy.
- Without `SECURE_PROXY_SSL_HEADER`, Django would judge every request "not secure" and redirect it to `https://...`. The browser, already on HTTPS, re-sends the request; Caddy forwards it as plain HTTP again; Django redirects again... **an infinite redirect loop.** The browser eventually gives up with `ERR_TOO_MANY_REDIRECTS`, and the site is completely unusable while every individual component looks "fine."
- `SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')` is the fix: "trust the `X-Forwarded-Proto` header from my proxy — if it says `https`, treat the request as secure." Caddy sets exactly that header. Handshake complete: Caddy states the truth, Django believes it, no loop.

**SECURITY WARNING — pure English, read twice:** `SECURE_PROXY_SSL_HEADER` means Django blindly trusts whoever can send it the `X-Forwarded-Proto` header. That trust is safe **only** while Caddy is the single possible client of gunicorn — which is guaranteed by the compose design: `app` uses `expose`, never `ports` (§3.3). **NEVER expose gunicorn directly to the internet** (never add `ports: - "8000:8000"` to the app service, never bypass Caddy). If you do, any attacker can send `X-Forwarded-Proto: https` themselves, and Django will treat a plain-HTTP, potentially man-in-the-middled request as fully secure — silently defeating `SECURE_SSL_REDIRECT`, secure-cookie protections, and the entire TLS boundary. The Caddyfile's first comment line ("The ONE TLS-terminating proxy") is that contract in writing: exactly one proxy, exactly one door.

### 5.4 `encode gzip` — free bandwidth

Compresses responses (HTML/CSS/JS/JSON) before sending them to browsers that accept gzip — typically 5–10× smaller for text. On factory-floor Android phones over mobile data (this ERP's primary worker device — mobile-first is a functional requirement here), that is directly faster page loads. One word in the Caddyfile, zero code changes.

### 5.5 What success looks like

After first start with DNS in place:

```bash
docker compose logs caddy        # expect: "certificate obtained successfully" for your domain
curl -I http://erp.example.com   # expect: 308 redirect to https://
curl -I https://erp.example.com  # expect: a real response over valid TLS (no cert warning)
```

- Browser shows the padlock on `https://erp.example.com`, no warnings.
- `curl -I https://...` returns headers including `strict-transport-security` (that's Django's HSTS from `production.py`, riding through Caddy).
- If instead you see `ERR_TOO_MANY_REDIRECTS`: something between Caddy and Django dropped the `X-Forwarded-Proto` handshake (§5.3) — verify you are running the certified files unmodified.
- If TLS fails: §5.1 troubleshooting (DNS, firewall 80/443, `DOMAIN` value).

---

*`deploy/entrypoint.sh` (the boot ritual) is taught in §1 Step 8; `deploy/deploy.sh` (deploys + the rollback anchor) in §9; `deploy/backup.sh` (nightly backups + restic) in §7. Expert quick-reference for all of it: [`deploy/README.md`](deploy/README.md).*

---

## 6. Systemd — why this stack does not need a unit file

If you have read other Django deployment tutorials, you have seen the ritual: write a `gunicorn.service` file, `systemctl daemon-reload`, `enable`, `start`, debug unit syntax at midnight. **This stack skips all of that, on purpose.** Here is exactly why — because "we don't need it" is only trustworthy when you understand *what* is doing that job instead.

### The two-layer answer

For the app to survive a reboot, two things must happen, and both are already handled:

1. **Docker itself must start at boot.** That *is* a systemd job — but Docker ships its own unit file (`docker.service`). You never write it; you only make sure it's enabled:

   ```bash
   systemctl enable docker
   systemctl is-enabled docker
   ```
   Success looks like: `enabled`. (The get.docker.com install from Step 4 normally enables it by default — verify anyway; this one word is the entire "boot configuration" of the system.)

2. **The containers must come back once Docker is up.** That is Docker's own job, driven by one line that appears on **every** service in the certified `docker-compose.yml`:

   ```yaml
   restart: unless-stopped
   ```

So: systemd starts Docker, Docker restarts the containers. There is no third thing for a hand-written unit file to do.

> 💡 **Samjho aise:** Building ka head watchman (systemd) subah sirf generator-room (Docker) ka switch on karta hai. Generator-room ke andar likhi hui list (`restart: unless-stopped`) khud decide karti hai kaunsi machinein wapas chalu hongi — woh saari, jo kal raat maalik ne khud band nahi ki thi. Watchman ko har machine ka alag register dena (per-app systemd units) yahan double bookkeeping hoti — same kaam, do jagah, out-of-sync hone ka risk.

### `restart:` policies — what each actually means

| Policy | Container crashes | You ran `docker compose stop` / `docker stop`, then Docker/host restarts | Boot behavior |
|---|---|---|---|
| `no` (default) | stays dead | stays dead | stays dead |
| `on-failure[:N]` | restarts (up to N tries) — **only on non-zero exit** | stays dead | **does NOT come back after daemon restart/reboot** |
| `always` | restarts | **comes back anyway** — Docker resurrects it even though you deliberately stopped it | comes back |
| `unless-stopped` | restarts | **stays stopped** — your manual stop is remembered | comes back (if it wasn't manually stopped) |

Why the certified files chose `unless-stopped` over the other two contenders:

- vs **`always`:** during maintenance ("stop the app while I fix the disk") `always` fights you — reboot the box mid-maintenance and the container you stopped comes back on its own. `unless-stopped` respects a human's deliberate `stop` as a decision, not an accident.
- vs **`on-failure`:** it looks tempting ("restart only on crashes") but it has a fatal gap for a production box: **it does not restart containers after a reboot**. A power cut at 2 AM would leave the ERP down until a human SSHes in. `on-failure` is a batch-job policy, not a service policy.

### What actually happens when the VPS reboots

Trace it once so a power failure never scares you:

1. Power returns / provider migrates the VM → the kernel boots → **systemd** starts.
2. systemd starts `docker.service` (because `is-enabled` said `enabled`).
3. The Docker engine reads its saved container state and applies restart policies: every container with `unless-stopped` that was running before the reboot is started again.
4. `db` and `redis` come up first in practice; their **healthchecks** (`pg_isready`, `redis-cli ping`) begin passing.
5. The `app` container starts and its **entrypoint wait-loop** (§1 Step 8) independently confirms db + redis are truly answering before migrate/collectstatic/gunicorn — so even if Docker's restart ordering were unlucky, the app never serves half-up.
6. `caddy` comes back and reloads its existing Let's Encrypt certificate from the `caddy_data` **volume** — no new certificate issuance, no Let's Encrypt round-trip, HTTPS is instant.
7. `backup` restarts its sleep-until-02:00 loop.

Total human actions required: **zero**.

**Verify it once, deliberately (a mini-drill, do it before real workers depend on the system):**
```bash
sudo reboot
# wait ~60–90 seconds, then from your laptop:
ssh root@203.0.113.10 "cd /opt/kapil-erp && docker compose ps"
curl -I https://erp.example.com/
```
Success looks like: all five services `Up` (db/redis `healthy`) and `HTTP/2 200` — without you having started anything.

**Troubleshooting a reboot that didn't self-heal:**
- Nothing running at all → `systemctl is-enabled docker` probably says `disabled`; run `systemctl enable docker` and note that as the root cause.
- Everything up except `app`, logs show the FATAL wait-loop line → db or redis failed to become healthy; `docker compose logs db redis`.
- One container `Exited` → `docker compose logs <service>` for the crash reason; `restart: unless-stopped` retries crashes, so a persistently-Exited container means it is crashing *every* time — fix the cause, don't just restart harder.

### The optional systemd unit — reference only

There are legitimate reasons some teams *do* wrap a compose stack in a systemd unit: company policy says "every service must show up in `systemctl status`"; they want the stack's start ordered after another unit (say, a network mount that holds data); they want start/stop history in `journald`; or they run many stacks per host and want one uniform control surface. **None of these apply to this single-stack VPS** — but so you recognize the pattern when you meet it elsewhere, here is what such a unit looks like. It is **commented out on purpose: reference only — do NOT install it for this stack.**

```ini
# /etc/systemd/system/kapil-erp.service
# ── REFERENCE ONLY. This stack intentionally relies on
# ── `restart: unless-stopped` + an enabled docker.service instead.
#
# [Unit]
# Description=Kapil Enterprises ERP (docker compose stack)
# Requires=docker.service
# After=docker.service network-online.target
# Wants=network-online.target
#
# [Service]
# Type=oneshot
# RemainAfterExit=yes
# WorkingDirectory=/opt/kapil-erp
# ExecStart=/usr/bin/docker compose up -d
# ExecStop=/usr/bin/docker compose down
#
# [Install]
# WantedBy=multi-user.target
```

Reading notes, line by line: `Type=oneshot` + `RemainAfterExit=yes` = "run `up -d` once, then consider the service 'active' even though the command exited" (compose returns immediately; the containers are the real long-running things). `Requires=/After=docker.service` = never try before Docker exists. `WorkingDirectory` = the repo root, so compose finds `docker-compose.yml` and `.env`.

Two cautions if you ever do adopt this pattern on some other project: `ExecStop=... down` **removes** the containers on stop (named volumes survive, but be aware stop ≠ pause), and running *both* this unit *and* restart policies is fine but means two systems now have opinions about container lifecycle — keep the mental model of who restarts what, or debugging gets confusing.

**Bottom line:** for this stack the entire boot story is one enabled service (`systemctl enable docker`) plus five `restart: unless-stopped` lines that already exist in the certified compose file. Nothing to write, nothing to maintain, nothing to drift.

---

## 7. Backups — pg_dump + restic, nightly

Yeh section poore deployment ka **sabse important** hissa hai. Server dobara ban sakta hai, Docker images dobara build ho sakti hain, code GitHub pe hai — lekin **database aur media files sirf ek jagah hain: aapke VPS pe**. Backup hi woh cheez hai jo factory ka saara settlement, ledger aur production history bachati hai agar VPS mar jaaye.

> 💡 **Samjho aise:** Factory ki khaata-bahi (ledger register) ki photocopy roz raat ko bank ke locker mein rakhna. Factory mein aag lag jaaye toh bhi hisaab safe. `backup` container = woh clerk jo roz raat 2 baje photocopy karke locker (cloud) mein daal deta hai — bina bhoole, bina chhutti.

### 7.1 What runs the backups

Compose stack mein ek dedicated service hai — `backup` (defined in `docker-compose.yml`). Yeh `postgres:16.6-alpine` image use karta hai (taaki `pg_dump` ka version database ke version se **exactly match** kare), aur boot hote hi `deploy/backup.sh` script chalata hai, jo hamesha ke liye loop mein chalti rehti hai.

The certified script, byte-for-byte (`deploy/backup.sh` — **do not edit this file**):

```sh
#!/bin/sh
# Nightly backup loop (backup service): pg_dump + media → restic → B2/R2.
# Runs at ~02:00 IST daily; retention 7d/4w/6m; weekly integrity check.
# RPO 24h. The offsite restic repo + the .env copy in the password manager are
# the disaster-recovery pair (see deploy/README.md restore drill).
set -e

apk add --no-cache restic >/dev/null 2>&1 || true   # accepted boot-time install (README note)

export PGPASSWORD="$POSTGRES_PASSWORD"

run_backup() {
    stamp=$(date +%Y%m%d-%H%M%S)
    echo "[backup] $stamp starting"
    pg_dump -h db -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc \
        -f "/backups/db-$stamp.dump"
    # keep only the 3 newest local dumps — offsite is the real archive
    ls -1t /backups/db-*.dump 2>/dev/null | tail -n +4 | xargs -r rm -f
    restic backup /backups /media --tag nightly
    restic forget --tag nightly --keep-daily 7 --keep-weekly 4 --keep-monthly 6 --prune
    if [ "$(date +%u)" = "7" ]; then
        echo "[backup] weekly restic check"
        restic check
    fi
    echo "[backup] done"
}

# Initialize the restic repo on first run (no-op if it exists).
restic snapshots >/dev/null 2>&1 || restic init

while true; do
    # Sleep until the next 02:00 (container TZ defaults UTC; 02:00 IST = 20:30 UTC).
    target="20:30"
    now=$(date +%s)
    next=$(date -d "today $target" +%s 2>/dev/null || date -D "%H:%M" -d "$target" +%s)
    [ "$next" -le "$now" ] && next=$((next + 86400))
    echo "[backup] sleeping $((next - now))s until next run"
    sleep $((next - now))
    run_backup || echo "[backup] FAILED — investigate (offsite copy missing for today)"
done
```

Line-by-line, kya ho raha hai:

| Script ka hissa | Kya karta hai | Kyun |
|---|---|---|
| `apk add --no-cache restic` | Container boot pe restic install karta hai | **Accepted tradeoff, on record** — see §7.5 |
| `pg_dump -h db ... -Fc -f /backups/db-<stamp>.dump` | Poore database ka snapshot ek file mein | Database = the business. §7.2 explains `-Fc` |
| `ls -1t ... tail -n +4 ... rm -f` | Sirf 3 newest local dumps rakhta hai | Disk bharne se bachata hai — **offsite is the real archive** |
| `restic backup /backups /media --tag nightly` | Dump files **aur** media (uploaded photos) cloud pe bhejta hai | Media volume database mein nahi hota — dono chahiye |
| `restic forget --keep-daily 7 --keep-weekly 4 --keep-monthly 6 --prune` | Purane cloud snapshots ki safai | §7.4 — retention policy |
| Sunday: `restic check` | Weekly integrity check | Backup jo verify nahi hua, backup nahi hai |
| `while true` + sleep until `20:30` UTC | Roz raat chalti hai | §7.3 — timing |
| `restic init` on first run | Cloud repository pehli baar banata hai | One-time; baad mein no-op |

### 7.2 What `pg_dump -Fc` is (and why not plain SQL)

`pg_dump` PostgreSQL ka official backup tool hai — poora database (tables, data, indexes, constraints) ek file mein likh deta hai. Flag `-Fc` matlab **"Format: custom"**.

- **Plain SQL dump** (`pg_dump` without `-Fc`): ek giant `.sql` text file — hazaaron `INSERT` statements. Restore = poori file ko `psql` se dobara run karna. Big, slow, all-or-nothing.
- **Custom format** (`-Fc`): compressed, binary, **table-of-contents wala** archive. Restore hota hai `pg_restore` tool se, jo selective restore, parallel restore, aur — sabse important hamare liye — `--clean --if-exists` support karta hai (pehle purani tables drop karo, phir fresh restore karo, bina errors ke).

> 💡 **Samjho aise:** Plain SQL dump = poori kitaab haath se dobara likhna. Custom format (`-Fc`) = kitaab ki compressed PDF **with index** — chhoti bhi hai, aur restore karte waqt `pg_restore` ko exactly pata hota hai kya kahan rakhna hai.

This is why every dump in this system — nightly (`db-<stamp>.dump`) and pre-deploy (`predeploy-<stamp>.dump` from `deploy/deploy.sh`) — is `-Fc` format, and every restore uses `pg_restore`, never `psql`.

### 7.3 Timing: 02:00 IST = 20:30 UTC

Script sleep karti hai agli **20:30 UTC** tak. Containers ka default timezone UTC hota hai, aur India Standard Time = UTC + 5:30. Isliye:

```
20:30 UTC  =  02:00 IST (next day)
```

Raat 2 baje isliye: factory band, koi settlement chal nahi raha, database shaant — clean, consistent snapshot. **RPO 24h** ka matlab: worst case, aap maximum **ek din ka data** kho sakte ho (aaj raat ke backup se pehle crash ho jaaye toh kal raat tak ka data hai). Owner ne yeh risk accept kiya hai — single-VPS setup ke liye reasonable hai.

Log line dekhoge to: `[backup] sleeping 43200s until next run` type output — yeh normal hai, container so raha hai agle 20:30 UTC tak.

### 7.4 restic — beginner concepts

restic ek open-source backup tool hai jo files ko **encrypted** form mein ek **repository** mein store karta hai. Chaar concepts samajhne hain:

1. **Repository** — cloud pe ek storage location jahan saare backups rehte hain. `.env` mein `RESTIC_REPOSITORY` se set hota hai. Placeholder examples:
   - Backblaze B2: `RESTIC_REPOSITORY=b2:example-backups:/`
   - Cloudflare R2 (S3-compatible): `RESTIC_REPOSITORY=s3:https://example-backup`
2. **Snapshots** — har `restic backup` run ek snapshot banata hai (point-in-time copy of `/backups` + `/media`). restic **deduplicates**: agar kal se sirf 2 MB badla hai, toh sirf 2 MB upload hota hai. Isliye roz full-looking backup hone ke bawajood cloud bill chhota rehta hai.
3. **Encryption** — everything in the repository is encrypted with `RESTIC_PASSWORD` before it leaves your server. The cloud provider cannot read your data.

   **SECURITY — READ CAREFULLY:** `RESTIC_PASSWORD` is NOT recoverable. There is no "forgot password" flow. If you lose it, every backup in the repository is permanently unreadable — equivalent to having no backups at all. It lives in `.env`, and the filled `.env` lives in your password manager. Verify this today, not on disaster day.
4. **forget + prune (retention)** — bina safai ke snapshots infinitely badhte jaayenge. Policy: `--keep-daily 7 --keep-weekly 4 --keep-monthly 6` = pichhle **7 din** roz ka, pichhle **4 hafte** har hafte ka, pichhle **6 mahine** har mahine ka ek snapshot. `--prune` un snapshots ka actual data delete karta hai jo ab kisi policy mein nahi aate. Plus, har **Sunday** `restic check` chalti hai — repository ki internal consistency verify karti hai.

> 💡 **Samjho aise:** restic repository = bank locker. `RESTIC_PASSWORD` = locker ki **ek-lauti chaabi** — duplicate banti hi nahi. Snapshots = locker mein rakhi dated photocopies. `forget --prune` = purani photocopies shred karna ek samajhdaar rule se: is hafte ki saari, is mahine ki weekly, is saal ki monthly.

### 7.5 The apk-add-at-boot tradeoff (on record)

Script ki pehli kaam-ki line hai `apk add --no-cache restic` — matlab restic har container-boot pe internet se install hota hai, **unpinned version**. Baaki poora stack exact-pinned hai (owner rule #1), toh yeh ek jaan-boojh ke liya gaya exception hai, `deploy/README.md` mein recorded:

> "Accepted tradeoff (noted): restic is `apk add`-ed at backup-container boot — one unpinned package; revisit if it ever bites."

Kyun accept kiya: postgres-alpine base image hi chahiye thi (matching `pg_dump` ke liye), aur uske upar ek custom image maintain karna ek aur moving part hota. Risk chhota hai (restic ka CLI stable hai), aur documented hai. **Agar kabhi backup logs mein restic-install failure dikhe, this is the first suspect** — and the recorded fix path is to revisit this decision (pin it), not to patch around it silently.

### 7.6 Manual backup — any time

Runbook (`deploy/README.md`) ka command:

```bash
docker compose exec backup sh -c '. /srv/backup.sh'
```

- **What it does:** running `backup` container ke andar script dobara source karta hai — fresh dump + restic upload abhi, raat ka wait kiye bina. (Runbook alternative: "or run the pg_dump line by hand" — i.e. run just the `pg_dump -h db ... -Fc` line from §7.1 inside the container.)
- **Why it exists:** deploy se pehle, ya kisi risky manual data-work se pehle, ek extra safety copy.
- **Success looks like:** `[backup] <stamp> starting` ... `[backup] done`, and a new snapshot in `restic snapshots`.
- **If it fails:** `docker compose logs backup` padho. Common causes: `RESTIC_REPOSITORY`/`RESTIC_PASSWORD`/`B2_ACCOUNT_ID`/`B2_ACCOUNT_KEY` galat ya missing in `.env`; internet issue; ya restic install failure (§7.5).

Snapshots list karne ke liye (yeh bhi verification hai — Deployment-Day Checklist item):

```bash
docker compose exec backup restic snapshots
```

**Success looks like:** ek table jisme har row = snapshot (ID, time, host, tags `nightly`, paths `/backups /media`). **Empty ya error** = backups configured nahi hain — treat as production emergency, fix before doing anything else.

### 7.7 The disaster-recovery PAIR

Poora disaster recovery **do cheezon** pe khada hai. Runbook ke words: restore is possible *"from NOTHING but: repo + password-manager .env + restic credentials."*

1. **The filled `.env` in your password manager** — contains `RESTIC_REPOSITORY`, `RESTIC_PASSWORD`, B2/R2 keys, `SECRET_KEY`, DB password. Without it, you cannot open the locker.
2. **The restic repository in the cloud** — contains the actual data. Without it, there is nothing in the locker.

**SECURITY:** One without the other is worthless. Losing the password-manager copy of `.env` = losing `RESTIC_PASSWORD` = losing all backups. Never store `.env` only on the VPS — the VPS dying is exactly the scenario backups exist for. Never commit `.env` to git.

### 7.8 Full restore procedure — the 6-step drill

Yeh **exact** drill hai `deploy/README.md` se ("Restore drill / disaster recovery"). Scenario: VPS poori tarah gone. Aapke paas sirf: GitHub repo + password manager wala `.env` + restic credentials. Runbook rule: **"Drill passes when 1-6 complete unaided. Re-run monthly."** — aur first-deploy checklist step 11: run this once **before handing out worker credentials**.

**Step 1 — Fresh VPS → first-deploy steps 1-4 → write `.env`.**
Naya server lo, firewall + Docker install karo, DNS point karo, repo clone karo (§10 checklist ke pehle steps / §1 Steps 1–6), phir password manager se `.env` file bana ke repo root mein rakho.
*Success:* `cat .env` shows every value filled (placeholders like `replace_with_*` gone).
*If stuck:* yeh step §1 Steps 1–7 (server prep + configuration) ka repeat hai — wahi troubleshooting apply hoti hai.

**Step 2 — Start only the database and redis:**
```bash
docker compose up -d db redis
```
*What/why:* sirf `db` + `redis` uthao — **app abhi nahi**, kyunki app boot hote hi empty database pe migrate kar dega, aur hum uski jagah backup restore karna chahte hain.
*Success:* `docker compose ps` shows `db` and `redis` as `Up (healthy)`.
*If it fails:* `docker compose logs db` — usually `POSTGRES_*` values missing in `.env`.

**Step 3 — Pull everything down from the cloud:**
```bash
docker compose run --rm backup sh -c 'apk add restic && restic restore latest --target /restore'
```
*What:* ek temporary backup-container chalata hai (`run --rm` = kaam khatam, container delete), usme restic install karta hai, aur **latest snapshot** ko container ke `/restore` folder mein utaar deta hai — database dumps + media, dono.
*Success:* restic prints the snapshot being restored and file counts; exit without error.
*If it fails:* wrong `RESTIC_REPOSITORY` / `RESTIC_PASSWORD` / B2 keys in `.env` (error message will say "wrong password" or "repository not found") — go back to the password manager, do not guess.

**Step 4 — Load the newest dump into Postgres:**
```bash
docker compose exec -T db pg_restore -U $POSTGRES_USER -d $POSTGRES_DB --clean --if-exists < <newest db-*.dump from /restore>
```
*What:* `pg_restore` custom-format dump ko database mein wapas likhta hai. `--clean --if-exists` = pehle existing objects drop karo (agar hain toh), phir recreate — repeat-safe.
*Note:* `<newest db-*.dump from /restore>` ko actual file path se replace karna hai — step 3 wale `/restore/backups/` mein sabse naya `db-<stamp>.dump` (filename ke timestamp se hi newest dikh jaata hai).
*Success:* command completes; the odd "does not exist, skipping" notice on a fresh DB is harmless (that is `--if-exists` doing its job).
*If it fails:* role/database name mismatch → confirm `POSTGRES_USER`/`POSTGRES_DB` in `.env` match the values the dump was taken with.

**Step 5 — Copy restored media into the media volume:**
```bash
docker compose run --rm -v media:/m backup sh -c 'cp -r /restore/media/* /m/'
```
*What/why:* uploaded files (pattern photos etc.) database mein nahi, `media` **volume** mein rehte hain — unhe alag se wapas rakhna padta hai.
*Success:* command exits silently (Unix mein no news = good news).
*If it fails:* "No such file or directory" = step 3 ka `/restore` is temporary container mein available nahi — steps 3 and 5 must run against the same restored data (re-run 3 then 5 in one session if needed).

**Step 6 — Bring the full stack up and smoke-test:**
```bash
docker compose up -d
```
Then smoke: **login → dashboard → one media file** (runbook's exact list). App ka entrypoint migrate chalayega — restored DB pe yeh no-op ya chhota top-up hota hai.
*Success:* login works with your **old** production credentials (proof the restored DB is real), dashboard data dikhta hai, ek media file browser mein khulti hai.
*If it fails:* Section 8 verification steps se diagnose karo — the same checks apply.

> 💡 **Samjho aise:** Restore drill = fire drill. Aag lagne ke din seekhna nahi chahoge ki emergency exit kahan hai. Mahine mein ek baar drill karo — 30 minute ka kharcha, poori factory ka records ka beema.

---

## 8. Verifying the Deployment

Deploy "chal gaya" aur deploy "sahi chal raha hai" — do alag cheezein hain. Yeh section layer-by-layer verify karta hai: Docker → containers → logs → database → redis → static → media → HTTPS → application health → admin. Har check ke saath: command, expected output, aur fail hone pe kahan dekhna hai.

> 💡 **Samjho aise:** Nayi machine factory mein lagi hai. Sirf switch on karke chale mat jao — pehle bijli check, phir motor ki awaaz, phir ek test piece chala ke dekho. Har layer alag se check hoti hai, taaki problem ho toh pata ho **kaunsi layer** mein hai.

### 8.1 Docker itself

```bash
docker --version
systemctl status docker
```

- **What:** confirms Docker installed hai aur uska daemon (background service) chal raha hai.
- **Expected:** version string (e.g. `Docker version 27.x`); status output mein `Active: active (running)`, aur `enabled` (so it starts on boot — remember `systemctl enable docker` from server prep).
- **If it fails:** `docker: command not found` → install step reh gaya (`curl -fsSL https://get.docker.com | sh`). `Cannot connect to the Docker daemon` → `sudo systemctl start docker`, phir `sudo systemctl enable docker`.

### 8.2 Containers — `docker compose ps`

```bash
cd /path/to/repo && docker compose ps
```

- **What:** stack ke paanch services ka status: `caddy`, `app`, `db`, `redis`, `backup`.
- **Expected:**
  - `db` and `redis` → `Up ... (healthy)` — these two have healthchecks in `docker-compose.yml` (`pg_isready` and `redis-cli ping`), so Docker itself keeps probing them.
  - `app`, `caddy`, `backup` → `Up` (no `(healthy)` suffix — they have no compose healthcheck; that is normal, not a problem).
- **`Up` vs `healthy` samjho:** `Up` = process chal raha hai. `(healthy)` = Docker ne andar jaake test kiya aur service ne sahi jawab diya. `app` service `depends_on: condition: service_healthy` ki wajah se **tab tak start hi nahi hoti** jab tak db+redis healthy na ho — plus entrypoint apna khud ka 120s wait bhi karta hai (double protection, owner rule #2).
- **If it fails:** `Restarting` loop ya `Exited` → us service ke logs: `docker compose logs <service>`. `db` unhealthy → `POSTGRES_*` values in `.env`. `app` exited → §8.3.

### 8.3 Logs — what a good boot looks like

```bash
docker compose logs -f app caddy
```

(`-f` = follow, live stream; `Ctrl+C` se bahar.)

**A healthy `app` boot prints, in order** (these lines come from `deploy/entrypoint.sh` — read it to see why):

```
[entrypoint] waiting for database + redis…
[entrypoint] database: ready
[entrypoint] redis: ready
[entrypoint] applying migrations…
  Applying ... OK        (many lines on first boot; few or none afterwards)
[entrypoint] collecting static files…
  <N> static files copied to '/srv/app/config/staticfiles'.
[entrypoint] starting: gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3 ...
[INFO] Starting gunicorn ...
[INFO] Booting worker with pid: ...   (three of these — 3 workers)
```

**A healthy `caddy` boot:** lines about obtaining/managing a certificate for your `DOMAIN`, ending in success (message like `certificate obtained successfully`), then quiet serving.

- **If `app` is stuck on the wait line:** entrypoint waits max 120s, then dies loudly with `[entrypoint] FATAL: db_ok=... cache_ok=... after 120s`. `db_ok=False` → check `DATABASE_URL` and `POSTGRES_*` in `.env` (password must match!). `cache_ok=False` → check `REDIS_URL` (should be `redis://redis:6379/0`).
- **If migrations fail:** the app refuses to boot — by design (never boot half-up). Read the traceback; if a deploy caused this, go to Section 9 (broken migration rollback).
- **If caddy loops with TLS errors:** DNS A record is not resolving to this server yet — Caddy cannot pass the Let's Encrypt challenge. Fix DNS first; Caddy retries on its own.

### 8.4 Database

```bash
docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "select 1"'
```

- **What:** database container ke andar ghusa ke ek trivial query — proof ki Postgres queries le raha hai.
- **Expected:**
  ```
   ?column?
  ----------
          1
  (1 row)
  ```
- **Bonus check — migrations actually applied:**
  ```bash
  docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "select count(*) from django_migrations"'
  ```
  **Expected:** a positive count (Django apni har applied migration ki entry is table mein rakhta hai). The number should only ever grow across deploys — never shrink.
- **If it fails:** `psql: FATAL: password authentication failed` → `.env` mismatch between `POSTGRES_PASSWORD` and the password embedded in `DATABASE_URL` (they must match — the `.env.example` comment says exactly this). `relation "django_migrations" does not exist` → migrate never ran → app boot failed, see §8.3.

### 8.5 Redis

```bash
docker compose exec redis redis-cli ping
```

- **What:** Redis se "zinda ho?" poochna.
- **Expected:** `PONG` — bas itna hi.
- **Why it matters here:** production mein Redis sirf cache nahi hai — **auth rate-limiter ke counters** yahin rehte hain (production settings intentionally have NO fallback: `REDIS_URL` missing = crash, because a local-memory fallback would silently weaken login rate limiting across the 3 gunicorn workers).
- **If it fails:** container not running → `docker compose ps`, `docker compose logs redis`.

### 8.6 Static files (CSS/JS)

Do proofs chahiye — collect hua, aur serve ho raha hai:

1. **Collected?** Boot logs mein (§8.3) line dhundo: `<N> static files copied to '/srv/app/config/staticfiles'.` — N should be in the hundreds+ range, not 0.
2. **Served?** Open `https://erp.example.com/accounts/login/` in a browser, view page source, copy any `/static/...` URL from it, then:
   ```bash
   curl -I https://erp.example.com/static/<path-you-copied>
   ```
   **Expected:** `HTTP/2 200`.
- **If it fails (404 on static):** collectstatic didn't run or errored — check the boot log. Note: agar page browser mein "naked" dikh raha hai (no styling), yehi problem hai.

### 8.7 Media files (uploads) — including the anonymous gate

Media = users ke uploaded files (e.g. pattern photos). Do-tarfa check:

1. **Upload + fetch (logged in):** app mein login karke ek file upload karo (e.g. a pattern photo, per the runbook smoke), phir usko page pe dekho / uska `/media/...` URL kholo. **Expected:** file renders, `200`.
2. **Anonymous gate:** open the same `/media/...` URL in a private/incognito browser window (not logged in). **Expected:** you do NOT get the file — access is gated for anonymous users (this is the runbook's own smoke item: "`/media/...` gated for anon").
- **If anon gets the file:** treat as a security finding — stop and investigate before going live. **If logged-in fetch fails:** check the `media` volume is mounted (`docker-compose.yml` mounts `media:/srv/app/config/media`) and app logs.

### 8.8 HTTPS / TLS

```bash
curl -I https://erp.example.com
```
- **Expected:** `HTTP/2 200` (or a `302` redirect to login — both fine), **plus** a `strict-transport-security` header containing `max-age=31536000; includeSubDomains; preload` (that is HSTS, set by Django production settings — browser ko bolta hai "is site pe ab kabhi http mat try karna").

```bash
curl -I http://erp.example.com
```
- **Expected:** a permanent redirect (`308` or `301`) with `location: https://erp.example.com/...` — Caddy plain HTTP ko HTTPS pe bhej deta hai.

Certificate khud check karna ho:
```bash
openssl s_client -connect erp.example.com:443 -servername erp.example.com </dev/null 2>/dev/null | openssl x509 -noout -issuer -dates
```
- **Expected:** issuer = Let's Encrypt, and `notAfter` a date ~90 days out (Caddy auto-renews — you never touch it). Ya seedha browser mein padlock icon → certificate details.
- **If TLS fails:** almost always DNS — the A record must resolve to the VPS **before** Caddy's first start (P19.5 provisioning item 3). Check `dig erp.example.com`, fix DNS, then watch `docker compose logs -f caddy` retry.

### 8.9 Application health — the honest truth

**There is no `/health` HTTP endpoint in this system. Do not look for one, do not add one.** The certified health gate is a management command plus a smoke list:

```bash
docker compose exec app python manage.py verify_production
```

- **What:** the `verify_production` management command (`config/verification/`, part of the 78-test verification suite) — the **P13-mandated post-deploy gate**. It checks the running production configuration/system from the inside.
- **Expected:** the command completes cleanly, reporting its checks as passing. **Any failure = the deploy is NOT verified** — read the failure message; do not proceed to handing the system to users.
- **Plus the smoke URLs** (all in a browser):
  1. Public homepage (storefront) renders
  2. `/accounts/login/` renders
  3. Admin login works
  4. Dashboard loads after login
  5. One `/media/` file: 200 logged-in, gated for anon (§8.7)

> 💡 **Samjho aise:** `verify_production` = doctor ka internal check-up (blood test); smoke URLs = "chal ke dikhao" walk test. Dono pass = discharge. Sirf "server chalu hai" bolna health check nahi hai.

### 8.10 Admin login

§1 Step 9 mein banaya hua superuser (`docker compose exec app python manage.py createsuperuser`) se login karo.

- **Expected:** login succeeds, dashboard/admin khulta hai.
- **SECURITY:** The dev seed credentials (`dev.*` / `Dev@12345`) are DEV ONLY. They must never exist in production. If the data decision was "import dev dump", verify those accounts are removed/disabled before real users touch the system.
- **If login fails:** wrong credentials → re-run `createsuperuser`. Redirect loop / CSRF error → `CSRF_TRUSTED_ORIGINS` in `.env` must be `https://erp.example.com` (with the scheme).

---

## 9. Rollback & Recovery

Cheezein bigadti hain — plan yeh nahi ki kabhi na bigde, plan yeh hai ki bigadne pe **rasta pehle se pata ho**. Is system mein chaar failure classes hain, har ek ka apna, rehearsed rasta.

> 💡 **Samjho aise:** Gaadi mein stepney isliye hoti hai ki puncture kahin bhi ho sakta hai. Lekin stepney tabhi kaam aati hai jab (a) usme hawa ho, aur (b) aapko pata ho jack kahan hai. Rollback bhi wahi hai — pre-deploy dump = stepney, restore drill = jack chalana seekhna. **Rehearse before you need it.**

### 9.0 The rollback anchor — pre-deploy dump

`deploy/deploy.sh` ki **pehli** action (sab kuch se pehle, `git pull` se bhi pehle):

```sh
docker compose exec -T db sh -c \
    'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' \
    > "predeploy-$(date +%Y%m%d-%H%M%S).dump"
```

Har deploy se theek pehle database ka full `-Fc` snapshot repo root mein `predeploy-<stamp>.dump` naam se ban jaata hai. Script comments ise khud "the rollback anchor" bolti hai — **deploy ke theek pehle ki duniya ki exact photo**. Kuch bhi bigde, is anchor pe wapas aa sakte ho. Isi liye script ka order sacred hai: dump FIRST, then build, then switch.

### 9.1 Failure class 1 — failed deployment (bad code)

**Symptom:** deploy ke baad app crash ho raha hai, ya feature toota hua hai — lekin database theek hai (koi migration problem nahi).

**The runbook fix (`deploy/README.md` §Rollback):**

```bash
git checkout <previous-tag>     # e.g. git checkout erp-v1.0.0
./deploy/deploy.sh              # (skip pull)
```

- **What happens:** git working tree purane, known-good release pe chala jaata hai; deploy script phir wahi safe order chalati hai — fresh pre-deploy dump, image rebuild, `up -d`.
- **"(skip pull)" ka matlab:** deploy.sh normally `git pull --ff-only` karta hai — lekin rollback mein aap deliberately purane tag pe ho, pull yahan apply nahi hota (tag checkout = detached state; the pull step is not part of a rollback). Practical form: script chalao aur pull step ko na-lagoo samjho — ya script ki bachi hui lines (dump → `docker compose build app` → `docker compose up -d` → `docker image prune -f`) haath se, isi order mein chala do. **Never edit deploy.sh itself** — it is a certified file.
- **Why images are effectively versioned too:** is stack mein Docker image kahin registry se nahi aati — `docker compose build app` **checked-out code + checked-out Dockerfile** se banti hai, aur Dockerfile khud git mein pinned hai (exact base image `python:3.10.16-slim`, pinned requirements). Matlab: `git checkout <tag>` = us tag ki **exact image** dobara reproducible. Code version = image version. Isi tarah infra files (compose/Caddyfile/Dockerfile) bhi git-versioned hain — "revert like code" (runbook line).
- **Success looks like:** Section 8 verification passes on the old version.

### 9.2 Failure class 2 — broken migration

**Symptom:** deploy ke baad migrations fail hui, ya migration chal toh gayi lekin data/schema galat ho gaya. Ab sirf code rollback kaafi nahi — **database bhi deploy-se-pehle wali state pe wapas chahiye**.

**The runbook fix:** restore the `predeploy-*.dump` taken by deploy.sh, **then** roll code back.

```bash
# 1. Stop the app so nothing writes to the DB mid-restore:
docker compose stop app

# 2. Restore the anchor (use the newest predeploy-*.dump in the repo root):
docker compose exec -T db sh -c \
    'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists' \
    < predeploy-<stamp>.dump

# 3. Roll the code back (this also restarts the stack):
git checkout <previous-tag>
./deploy/deploy.sh              # (skip pull)
```

- **`--clean --if-exists` recap:** drop-then-recreate every object from the dump; `--if-exists` makes the drops error-free even where objects are missing. Result: database = exactly the pre-deploy photo.
- **Why NOT reverse migrations first?** Django migrations technically "reverse" ho sakti hain (`migrate <app> <previous>`), lekin production incident mein woh **first choice nahi** hai:
  1. Har migration reversible nahi hoti (data migrations, column drops — reverse code hota hi nahi ya lossy hota hai).
  2. Broken migration aadhi chal ke fail ho sakti hai — reverse ab undefined state pe chalega.
  3. Reverse path shaayad kabhi test nahi hua; dump-restore **deterministic** hai — photo wapas laga do, done.
  4. Incident ke waqt aapko surgery nahi, restore chahiye. Fast, boring, correct.
- **Order matters:** DB restore pehle, code rollback baad — kyunki naya (broken) code purane DB schema pe phir migrate karne ki koshish karega. Restore + old code = matched pair.
- **Success looks like:** app boots on old code, `django_migrations` count matches pre-deploy, Section 8 passes.

### 9.3 Failure class 3 — full database loss

**Symptom:** VPS gone / disk corrupt / `pgdata` volume destroyed. Local `predeploy-*.dump` bhi gaya.

**The fix:** the restic path — Section 7.8 ka poora 6-step restore drill, from nothing but repo + password-manager `.env` + restic credentials. Worst case aap pichhli raat 02:00 IST ke snapshot pe wapas aate ho (**RPO 24h** — yeh accepted hai).

Yehi woh moment hai jiske liye monthly drill practice hoti hai. Agar aapne drill kabhi nahi ki, aaj mat seekho — isliye checklist (Section 10) mein drill **go-live se pehle** hai.

### 9.4 Failure class 4 — the settlement lever (config rollback)

Yeh ek **business-logic** rollback hai, infrastructure nahi — aur poore system ka sabse elegant safety valve.

**Background (1 line):** V2-3 / ADR-0007 cutover ke baad, worker earnings **sirf Adda settlement pe** book hoti hain (`LEDGER_CREDIT_AT_ALLOCATION=False`, the default); legacy allocation-time crediting path refuse karta hai aur uska UI hidden hai — lekin woh path **deleted nahi hai**, fully tested in CI, soak-gated deletion.

**If the settlement-first flow misbehaves in production:**

```bash
# In .env on the VPS, change:
LEDGER_CREDIT_AT_ALLOCATION=True

# Then restart the app to pick up the new env:
docker compose up -d
```

- **What happens:** system legacy allocation-time crediting pe wapas chala jaata hai. **No deploy, no code change, no schema change** — sirf ek env flag + restart.
- **Safety:** a cross-era guard prevents double credit in both directions (an earning credited in one era cannot be credited again in the other), and the lever path stays fully tested in CI (runbook, verbatim).
- **When it goes away:** the legacy path's physical deletion is soak-gated — the lever stays until the real-worker soak passes. Until then, it is a legitimate, documented rollback.

> 💡 **Samjho aise:** Factory mein nayi automatic machine lagayi, lekin purani manual machine ko abhi bech nahi diya — corner mein covered khadi hai, serviced. Nayi machine din bhar ke liye bigdi? Cover hatao, purani chalu karo, production nahi rukta. `LEDGER_CREDIT_AT_ALLOCATION=True` = woh cover hatana.

### 9.5 The philosophy: rehearse before you need it

Chaar raste, ek rule: **incident ke din invent mat karo.**
- Pre-deploy dump automatic hai (deploy.sh line 1) — aapko yaad rakhna bhi nahi padta. Free stepney on every deploy.
- Restore drill monthly — runbook mandate, and once **before** worker credentials go out.
- Rollback commands runbook mein likhe hain (`deploy/README.md` §Rollback) — is teaching doc se seekhna, us runbook se execute karna. When in doubt, the terse runbook is canonical.

---

## 10. Deployment-Day Checklist

Print this. Zero se verified production tak, **exact execution order**. Har box = ek action. Sab boxes tick = you are live. (Details: sections 3–9; canonical terse runbook: `deploy/README.md`.)

**SECURITY (before you start):** placeholders below (`erp.example.com`, `203.0.113.10`) must be replaced with YOUR values; every secret goes only in `.env` + the password manager, never in git, never in chat logs.

- ☐ **Buy the VPS** — 2–4 GB RAM, India region (DO Bangalore / Vultr Mumbai). Note its IP (e.g. `203.0.113.10`).
- ☐ **SSH-key-only login** — add your public key at provisioning; disable password auth. Verify: `ssh root@203.0.113.10` works without a password prompt.
- ☐ **Firewall** — `ufw allow 22 && ufw allow 80 && ufw allow 443 && ufw enable` → `ufw status` shows exactly 22, 80, 443.
- ☐ **Install Docker + compose plugin** — `curl -fsSL https://get.docker.com | sh` → then `systemctl enable docker` (boot-start; with `restart: unless-stopped` in compose, this is why no systemd units are needed). Verify: `docker --version`.
- ☐ **DNS A record** — `erp.example.com → 203.0.113.10`. MUST resolve **before** first `compose up` (Caddy TLS needs it). Verify: `dig erp.example.com` returns the VPS IP.
- ☐ **Clone the repo** — `git clone <repo-url> && cd <repo-dir>`.
- ☐ **Check out the release** — `git checkout erp-v1.0.0` (the frozen, certified release tag).
- ☐ **Fill `.env`** — `cp .env.example .env`, fill EVERY value (SECRET_KEY 50+ chars; `POSTGRES_PASSWORD` must match the one inside `DATABASE_URL`; restic repo + `RESTIC_PASSWORD`).
- ☐ **Store the filled `.env` in the password manager** — it is half of the disaster-recovery pair (Section 7.7). Do this NOW, not later.
- ☐ **First start** — `docker compose up -d --build`.
- ☐ **Watch the boot** — `docker compose logs -f app caddy` until you see: db ready → redis ready → migrations applied → static collected → 3 gunicorn workers booted → caddy certificate obtained (§8.3).
- ☐ **Create the superuser** — `docker compose exec app python manage.py createsuperuser`.
- ☐ **Data decision (owner)** — start CLEAN (recommended — re-enter master data via admin UIs; the dev DB contains validation test rows) OR import the dev dump via the restore procedure (§7.8 steps 3–5 pattern with the dev dump).
- ☐ **Run the post-deploy gate** — `docker compose exec app python manage.py verify_production` → must pass clean (§8.9). No `/health` URL exists; this command IS the gate.
- ☐ **Smoke list (browser)** — public homepage renders → `/accounts/login/` renders → admin login works → dashboard loads → upload a pattern photo → its `/media/...` URL is 200 logged-in and gated for anon.
- ☐ **HTTPS checks** — `curl -I https://erp.example.com` → 200/302 + `strict-transport-security` header; `curl -I http://erp.example.com` → 301/308 redirect to https (§8.8).
- ☐ **First backup confirmed** — `docker compose exec backup restic snapshots` shows a snapshot (nightly runs at 02:00 IST; to not wait, trigger one manually: `docker compose exec backup sh -c '. /srv/backup.sh'` — §7.6).
- ☐ **Restore drill, once, now** — full §7.8 drill (ideally on a scratch VPS) BEFORE handing out worker credentials. Runbook step 11 — not optional.
- ☐ **Record the deployed version** — write the tag (`erp-v1.0.0`), commit (`90c1f2f3`), date, and verify_production result into the RELEASE FREEZE RECORD (`docs/RELEASE_CERTIFICATION_LOG.md`).

**All boxes ticked = Kapil Enterprises ERP is live, verified, backed up, and rollback-rehearsed.** 🏁
