---
id: deploy-course-34-production-security
type: lesson
status: active
owner: handwritten
scope: deployment, operations — this ERP shipped to a VPS
anchors: docker-compose.yml, deploy/entrypoint.sh, deploy/Caddyfile, deploy/backup.sh
verified: 2026-08-01
---

# 34 — Production Security

> Part of [Deployment Course](00_COURSE_OVERVIEW.md). Prev: [33 — CI/CD](33_CI_CD.md). Next: [35 — Deployment Checklist](35_Deployment_Checklist.md).

# Learning Objectives
By the end of this chapter you can:
- run and interpret Django's deployment audit
- name this project's layered defences
- respond to a suspected compromise in the right order
- judge which hardening steps are worth their cost

# Purpose
To pull every security thread in this course into **one layered defense** — from the firewall down to the Django cookie flags — so you can see the whole picture and verify it. Security isn't one setting; it's **defense in depth**: many independent layers, so one failure isn't a breach.

# The Problem
A public server is attacked continuously — automated scanners hit your IP within minutes of it going live, probing for open ports, default passwords, exposed databases, `DEBUG=True` pages, and known CVEs. There is no "too small to target." You need every layer hardened, because attackers only need **one** weak one. This chapter is the consolidated checklist of the layers built across the course.

# Theory (from zero): the layers (outside → in)

### 1. Network perimeter — firewall + minimal exposure
Only expose what must be public. A **firewall (ufw)** allows **only 22 (SSH), 80, 443**; everything else is denied. In the app stack, **only Caddy publishes ports** (80/443) — `app`/`db`/`redis`/`backup` have **no `ports:`**, so they're unreachable from the internet ([Ch 05](05_IP_Address_and_Ports.md)/[Ch 19](19_Docker_Networking.md)). An open Postgres/Redis port is a classic instant breach; here there are none.

### 2. Host access — SSH keys, no passwords, no root
SSH with **key auth only**, **password login disabled**, **root login disabled** ([Ch 07](07_SSH.md)). Keys can't be brute-forced like passwords. Optionally move SSH off 22 / add fail2ban to cut scanner noise.

### 3. Transport — HTTPS everywhere
**Caddy** auto-provisions Let's Encrypt TLS and redirects HTTP→HTTPS ([Ch 12](12_Caddy.md)); Django adds **HSTS** (tell browsers "HTTPS only" for a year, + preload/subdomains) so even the first request can't be downgraded ([Ch 03](03_HTTP_HTTPS.md)). `SECURE_PROXY_SSL_HEADER` lets Django trust Caddy's `X-Forwarded-Proto` ([Ch 11](11_Reverse_Proxy.md)).

### 4. Application — Django hardening
- **`DEBUG=False`** (no traceback/secret leak) + **`ALLOWED_HOSTS`** (reject spoofed Host) ([Ch 24](24_Django_Settings.md)).
- **Secure cookies** (`SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, HttpOnly) → cookies only over HTTPS, not readable by JS.
- **CSRF** protection on + **`CSRF_TRUSTED_ORIGINS`** set (no default → fail-fast).
- **Password hashing = Argon2** (memory-hard, slow to crack) ([project baseline]).
- **Rate limiting / brute-force lockout** on login, counters in Redis; the app **fail-fasts** without Redis so the limiter can't be silently off ([Ch 22](22_Redis.md)).
- **Authorization**: permissions via a single `permission_service` (no raw `is_superuser` in views), skill-gated stage access, menu+URL gated together — least privilege in the app layer.

### 5. Container — least privilege
The image runs as a **non-root user** (`app`, uid 1000), not root ([Ch 17](17_Dockerfile.md)) — a container escape starts unprivileged. **Pinned base images** (exact versions) → reproducible + patchable. Only the needed packages installed (slim image = smaller attack surface).

### 6. Secrets — never in code/image/logs/git
Secrets live in **`.env`** (0600, gitignored) + a password manager; **fail-fast** critical vars (no defaults) so a misconfig crashes loudly instead of running insecure ([Ch 23](23_Environment_Variables.md)). Never logged ([Ch 31](31_Logging.md)) or shipped to Sentry ([Ch 32](32_Sentry.md)).

### 7. Data — encrypted backups, private DB
Backups are **client-side encrypted** (restic) and off-site ([Ch 28](28_Backups.md)); the DB is private (no published port) and password-protected; media served with access control.

### 8. Supply chain + maintenance
Pin dependencies; update them for CVEs (`pip-audit`/Dependabot); rebuild images to pick up base-image patches. Security is ongoing, not one-time.

### The principle: defense in depth + least privilege
No single layer is trusted alone. Firewall *and* private services *and* HTTPS *and* app hardening *and* non-root *and* secret hygiene. Each assumes the others might fail.

> 💡 **Samjho aise:** Security **taalon ki parat** hai, ek taala nahi: firewall (sirf 80/443 khule), SSH key-only, `DEBUG=False`, secret `.env` mein, database ka port bahar band, password Argon2 se hashed, backup encrypted. Ek parat tootne pe doosri bachati hai — isi liye "ek cheez kar li, ho gaya" sabse khatarnaak soch hai.

# Real World Example (My ERP)
| Layer | Control | Where |
|---|---|---|
| Firewall | ufw allows only 22/80/443 | VPS setup ([Ch 07](07_SSH.md)) |
| Exposure | only `caddy` publishes ports; db/redis/app/backup private | `docker-compose.yml` ([Ch 19](19_Docker_Networking.md)) |
| SSH | key-only, password + root login disabled | VPS setup |
| TLS | Caddy auto Let's Encrypt + HTTP→HTTPS | `deploy/Caddyfile` ([Ch 12](12_Caddy.md)) |
| HSTS | 1yr + preload + subdomains | `production.py` |
| DEBUG/hosts | `DEBUG=False`, `ALLOWED_HOSTS` from env | `production.py` |
| Cookies | secure + HttpOnly session/CSRF cookies | `production.py` |
| CSRF | on + `CSRF_TRUSTED_ORIGINS` (no default) | `production.py` |
| Passwords | Argon2 hasher | `base.py` |
| Brute-force | login rate-limiter in Redis; app fail-fasts without Redis | accounts + `production.py` ([Ch 22](22_Redis.md)) |
| AuthZ | `permission_service`, skill-gated stages, menu+URL gated | inventory/accounts |
| Container | non-root `app` uid 1000, pinned slim images | `Dockerfile` ([Ch 17](17_Dockerfile.md)) |
| Secrets | `.env` 0600 gitignored + password manager, fail-fast vars | `.env` ([Ch 23](23_Environment_Variables.md)) |
| Backups | restic client-side encrypted, off-site | `backup.sh` ([Ch 28](28_Backups.md)) |

- **Audited:** `manage.py check --deploy` validates the Django-layer flags; the project's security baseline (Argon2, per-IP+email rate limit, self-lockout protection, security log) is an established, tested part of the accounts app.
- **Honest note:** hardening beyond v1 (WAF, fail2ban, automated dependency scanning, off-24 SSH port) is optional/tracked, not yet wired — reasonable for a single-VPS v1 but worth adding as you grow.

# Visual Diagram
```
  Internet (hostile: scanners hit within minutes)
     │  ufw: ONLY 22/80/443 open  ───────────────────────── layer 1 perimeter
     ▼
  :443 Caddy (TLS/Let's Encrypt, HTTP→HTTPS) ────────────── layer 3 transport
     │  X-Forwarded-Proto → Django trusts (SECURE_PROXY_SSL_HEADER)
     ▼  (private Docker net — db/redis/app have NO published port · layer 1)
  app (gunicorn, NON-ROOT uid 1000) ─────────────────────── layer 5 container
     │  Django: DEBUG=off · ALLOWED_HOSTS · HSTS · secure cookies · CSRF ── layer 4 app
     │  Argon2 · login rate-limit(Redis, fail-fast) · permission_service
     ▼
  db / redis (private, password) · backups restic-ENCRYPTED off-site ────── layer 7 data
  secrets: .env 0600 + password manager, fail-fast (never code/image/log/git) layer 6
  SSH: key-only, no password, no root ──────────────────────────────────── layer 2 host
  DEFENSE IN DEPTH: attacker must beat EVERY layer; one weak layer ≠ breach
```

# Practical — how to verify it
```bash
sudo ufw status                                   # only 22/80/443 ALLOW
docker compose ps --format '{{.Name}} {{.Ports}}' # only caddy shows 0.0.0.0:80/443; others blank
docker compose exec app whoami                    # app (NOT root) — Ch17
docker compose exec app python manage.py check --deploy   # Django hardening audit (Ch24)
```
```bash
# TLS + HSTS + secure headers
curl -sI https://<domain> | grep -iE 'strict-transport-security|x-frame|content-type-options'
curl -sI http://<domain>  | grep -i location    # 301 → https (redirect works)
git ls-files | grep -x .env                       # MUST be empty (.env not tracked — Ch23)
stat -c '%a' .env                                 # 600
```
```bash
# Dependency CVE scan (recommended add)
pip install pip-audit && pip-audit -r requirements.txt
```

# Production Walkthrough
The defences here stack, deliberately:
- **`DEBUG=False`** — the single most important line (ch 24).
- **`ALLOWED_HOSTS`** set to real domains only.
- **HTTPS everywhere** via Caddy, with HSTS (ch 12).
- **Secure, HttpOnly cookies**; CSRF protection on every form.
- **Argon2 password hashing**, plus per-IP and per-email login rate limiting.
- **No published database or cache ports** (ch 19) — nothing to attack that is not the app.
- **Firewall to 22/80/443**, key-only SSH (ch 05, ch 07).
- **Role-based access enforced through a permission service**, with menu and URL gated together so hiding a link also blocks the route.
- **Settlement as the only money-write boundary** — an application-level control that limits blast radius even for an authenticated attacker.

`manage.py check --deploy` audits the settings part of that list. Run it before every release.

# Debugging Guide
1. **`check --deploy` warnings** — treat each as a task, not noise.
2. **CSRF failures after enabling HTTPS** — `CSRF_TRUSTED_ORIGINS` (ch 24).
3. **Locked out by rate limiting** — expected behaviour; know how to clear a counter before you need to.
4. **Suspected compromise, correct order**: preserve evidence → rotate every secret (ch 23) → patch the entry point → then restore service. Restoring first destroys the evidence.
5. **Unexpected admin access** — check the security log and the role assignments, not just the users table.

# Performance Notes
- TLS and Argon2 cost CPU on purpose; Argon2's cost *is* the protection.
- Rate limiting protects the database more than the login page.
- HSTS removes a redirect round-trip after the first visit.
- Security controls here cost milliseconds; a breach costs the business.

# Security Considerations
- Patch the OS and rebuild images regularly; pinned versions must still be *moved forward* deliberately (ch 16).
- Backups are a breach surface (ch 28) — encrypt them.
- Least privilege everywhere: database user, deploy user, Docker group membership is root-equivalent.
- Personal and financial data raises the stakes: worker wages, photos, receipts.
- **Never build a new money-write path outside the approved single-writer services** — stop and report instead.

# Architecture Decisions
- **Layers, not a wall** — every control assumes the one in front of it may fail.
- **Application-level money boundary** in addition to infrastructure controls.
- **Menu and URL gated together**, because hidden-but-reachable is a real vulnerability class.
- **Audit tooling in the release process**, so security is a checklist item and not a mood.

# Best Practices
- `check --deploy` in CI (ch 33).
- Rotate on suspicion, not on proof.
- Review `ports:` on every compose change.
- Keep the incident order memorised: evidence, rotate, patch, restore.

# Beginner Mistakes
- **Publishing the DB/Redis port** ("easier to connect") → instant internet-facing DB = breach. Keep them private; tunnel via SSH.
- **`DEBUG=True` in prod** → leaks tracebacks + secrets ([Ch 24](24_Django_Settings.md)). The cardinal sin.
- **Password SSH / root login** → brute-forced. Keys only, no root.
- **Running the container as root** → a bug/escape is now root on the host. Non-root user ([Ch 17](17_Dockerfile.md)).
- **Secrets in git/image/logs** → permanent leak. `.env` + fail-fast + never log ([Ch 23](23_Environment_Variables.md)).
- **Giving the rate-limiter a fallback** → silently disabled brute-force protection. Fail-fast on Redis ([Ch 22](22_Redis.md)).
- **Never updating dependencies** → known CVEs stay exploitable. Scan + patch.
- **Trusting one layer** → assume each can fail; that's why there are many.

# Interview Questions
- **Junior:** "Name three production security basics for a Django deploy." — HTTPS everywhere (+ HSTS), `DEBUG=False` with proper `ALLOWED_HOSTS`, and not exposing the database to the internet (firewall + private services).

- **Mid:** "What is defense in depth here?" — Multiple independent layers — firewall, private services, key-only SSH, TLS/HSTS, Django hardening (DEBUG off, secure cookies, CSRF), Argon2 + rate-limiting, non-root container, secret hygiene, encrypted backups — so a single failure isn't a breach.

- **Senior:** "Why does the app fail-fast without Redis, and how is that a *security* control?" — The login brute-force limiter's counters live in the Redis-backed cache. If Redis vanished and the app fell back to a dummy cache, the limiter would be silently off. Refusing to boot without Redis makes availability of the security control a boot invariant — you can't accidentally run with brute-force protection disabled ([Ch 22](22_Redis.md)).

- **Staff:** "Audit this stack's security posture and prioritize hardening." — Strong baseline: minimal perimeter (ufw + only-Caddy-published), key-only/no-root SSH, auto-TLS + HSTS, DEBUG-off + secure cookies + CSRF + Argon2 + Redis-backed rate-limit (fail-fast), non-root pinned containers, `.env`/fail-fast secret hygiene, encrypted off-site backups, and `check --deploy` in the loop. Prioritized adds: (1) automated dependency/CVE scanning (pip-audit/Dependabot) + scheduled base-image rebuilds — supply chain is the most likely real hole; (2) fail2ban + SSH off-22 to cut scanner noise; (3) a WAF / rate-limit at Caddy for app-layer abuse; (4) 2FA for admin; (5) periodic access-control review (least privilege drift). Each is an independent layer; none is load-bearing alone. Verify continuously (`check --deploy`, header scans, `.env` not-tracked) rather than trusting it stays configured.

### Why interviewers ask these — and the answer that separates levels

| Testing for | Weak answer | What lands |
|---|---|---|
| Can you describe defence in depth concretely? | "We have several security measures." | Name the **independent layers**: firewall → private services → key-only SSH → TLS/HSTS → `DEBUG=False` + secure cookies + CSRF → Argon2 + rate limiting → non-root container → secret hygiene → encrypted backups. **Every layer assumes the one in front may fail.** |
| Do you know an *availability* control can be a *security* control? | "Redis being down is just a performance problem." | The **brute-force limiter's counters live in Redis**. If the app fell back to a dummy cache the limiter would be **silently off**, so refusing to boot is a **security** decision. Silent degradation of a security control is worse than an outage. |
| Do you know the incident order? | "Restore service as fast as possible." | **Preserve evidence → rotate every secret → patch the entry point → then restore service.** Restoring first destroys the evidence you need to know what was taken. Getting this order wrong is the most expensive mistake on the list. |
| Do you know the application-level money boundary? | "Access control protects the money." | **Settlement is the only money-write path**, so even a valid stolen manager login has a narrow blast radius. And the standing rule: **a new money-write path outside the approved services means stop and report, never silently fix.** |

**The killer follow-up:** *"An attacker has a valid manager password. What can they actually do?"* — this is the question infrastructure security cannot answer, and it is why **application-level boundaries exist**. If your answer is "anything a manager can do", you have no blast-radius design — only a perimeter.

# Revision Notes
- Layers: `DEBUG=False` · `ALLOWED_HOSTS` · HTTPS+HSTS · secure cookies+CSRF · Argon2+rate limit · **no DB/Redis ports** · firewall 22/80/443 · key-only SSH · permission service (menu+URL together) · **settlement-only money writes**.
- `manage.py check --deploy` = the settings audit. Every warning is a task.
- Compromise order: **preserve evidence → rotate secrets → patch → restore.** Not restore-first.
- Docker group = root. Backups are a breach surface — encrypt.
- ⚠️ New money-write path outside approved services ⇒ **stop and report**.

# Cheat Sheet
- **Defense in depth + least privilege.** Attacker must beat every layer.
- **Perimeter:** ufw 22/80/443 only; **only Caddy publishes ports** (db/redis/app private).
- **Host:** SSH key-only, no password, no root. **Transport:** Caddy TLS + HSTS + proxy header.
- **App:** DEBUG off · ALLOWED_HOSTS · secure+HttpOnly cookies · CSRF (+trusted origins) · Argon2 · Redis rate-limit (fail-fast) · permission_service.
- **Container:** non-root uid 1000, pinned slim images. **Secrets:** `.env` 0600 + password manager, fail-fast, never logged.
- **Data:** private DB, restic-encrypted off-site backups. **Maintain:** pin + scan + patch deps.
- **Verify:** `check --deploy`, `ufw status`, `compose ps` ports, header/`.env` checks.

# My ERP Section
| Layer | Control (see table above) |
|---|---|
| Perimeter | ufw 22/80/443; only `caddy` publishes ports |
| Host | key-only SSH, no password/root |
| Transport | Caddy Let's Encrypt + HSTS 1yr + proxy header |
| App | DEBUG off, ALLOWED_HOSTS, secure cookies, CSRF, Argon2, Redis rate-limit (fail-fast), permission_service |
| Container | non-root `app` uid 1000, pinned images |
| Secrets | `.env` 0600 + password manager, fail-fast vars |
| Data | private DB, restic-encrypted off-site backups |
| Tracked adds | pip-audit/Dependabot, fail2ban, WAF, admin 2FA |

# Practice Tasks
1. **Read the code:** run `check --deploy` and map each warning to the setting that fixes it.
2. **Debug:** trigger the login rate limit deliberately, then clear it. Document both.
3. **Design:** write the one-page incident runbook in the correct order.
4. **Architecture:** explain how the settlement money boundary limits damage from a stolen manager password.

# Homework
1. `docker compose ps --format '{{.Name}} {{.Ports}}'` — confirm only `caddy` is published. Why is a published `db` port dangerous?
2. `docker compose exec app whoami` — is it root? Why does running non-root matter after a container escape?
3. `manage.py check --deploy` — which warnings are already satisfied by `production.py`? Which (if any) remain?
4. `curl -sI https://<domain>` — find the HSTS header. What does it tell the browser, and why does that protect the *first* visit next time?
5. Explain defense in depth using three layers from this stack: how does each still protect you if one adjacent layer failed?

---

# Further Reading & Live Resources
- Django docs — *Security in Django* + *Deployment checklist*: https://docs.djangoproject.com/en/5.0/topics/security/ · https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/
- OWASP — *Top Ten* (the canonical web risk list): https://owasp.org/www-project-top-ten/
- Mozilla — *Web Security Guidelines / Observatory* (scan your site): https://observatory.mozilla.org/
- DigitalOcean — *Initial server setup + ufw + SSH hardening (Ubuntu 22.04)*: https://www.digitalocean.com/community/tutorials/initial-server-setup-with-ubuntu-22-04
- Docker docs — *Security best practices* (non-root, least privilege): https://docs.docker.com/develop/security-best-practices/
- pip-audit (dependency CVE scanning): https://pypi.org/project/pip-audit/
