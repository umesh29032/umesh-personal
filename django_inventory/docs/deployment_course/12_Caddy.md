---
id: deploy-course-12-caddy
type: lesson
status: active
owner: handwritten
scope: deployment, operations — this ERP shipped to a VPS
anchors: docker-compose.yml, deploy/entrypoint.sh, deploy/Caddyfile, deploy/backup.sh
verified: 2026-08-01
---

# 12 — Caddy (my reverse proxy, real config)

> Part of [Deployment From Zero](00_COURSE_OVERVIEW.md). Prev: [11 — Reverse Proxy](11_Reverse_Proxy.md). Next: [13 — Nginx Comparison](13_Nginx_Comparison.md).

# Learning Objectives
By the end of this chapter you can:
- read this project's Caddyfile line by line
- explain how automatic HTTPS actually works
- set body limits, headers and a static-file route
- say what Caddy does *not* solve

# Purpose
To read and fully understand **my actual `deploy/Caddyfile`** and Caddy's `docker-compose.yml` service — line by line — so the box that faces the internet is not a mystery. When HTTPS breaks, or the cert won't issue, or "502 Bad Gateway" appears, I know exactly which line is responsible.

# The Problem
Caddy is the only thing between the internet and my ERP ([Ch 11](11_Reverse_Proxy.md)). If I can't read its config, I can't debug TLS, renewals, or proxying. Most proxies (Nginx) need dozens of config lines; mine is **three**. That brevity is a feature — but only if I know *why* three lines are enough.

# Theory (from zero)

### What Caddy is
Caddy is a modern web server + reverse proxy whose headline feature is **automatic HTTPS**: given a domain, it obtains a Let's Encrypt certificate, installs it, redirects HTTP→HTTPS, and **renews forever** — no certbot, no cron ([Ch 03](03_HTTP_HTTPS.md)/[Ch 04](04_DNS_Domains.md)). Config lives in a **Caddyfile**.

### My real Caddyfile — every line
```caddyfile
# The ONE TLS-terminating proxy (PD's SECURE_PROXY_SSL_HEADER assumption).
# Caddy auto-provisions Let's Encrypt for {$DOMAIN} and sets X-Forwarded-Proto.
{$DOMAIN} {
	encode gzip
	reverse_proxy app:8000
}
```
Line by line:
- **`# …`** — comments; they state the contract: this is *the* TLS terminator, and it sets `X-Forwarded-Proto` (which Django trusts via `SECURE_PROXY_SSL_HEADER`, [Ch 11](11_Reverse_Proxy.md)).
- **`{$DOMAIN}`** — the **site address**, read from the `DOMAIN` environment variable (compose passes it from `.env`). This one token is *why HTTPS is automatic*: because it's a real domain (not `localhost`/an IP), Caddy **automatically** provisions + renews a Let's Encrypt cert for it and enables HTTPS on 443 with an HTTP→HTTPS redirect on 80. No `tls` line needed — that's the default behavior.
- **`{ … }`** — the **site block**: config for that domain.
- **`encode gzip`** — compress responses with gzip (smaller/faster; [Ch 11](11_Reverse_Proxy.md)). (Caddy would also do zstd/brotli if listed.)
- **`reverse_proxy app:8000`** — forward every request to **`app:8000`** — the `app` service (Gunicorn) on port 8000, resolved by **Docker's internal DNS** ([Ch 19](19_Docker_Networking.md)). Caddy also **auto-adds** `X-Forwarded-For`, `X-Forwarded-Proto`, `X-Forwarded-Host` on proxied requests — that's how Django learns the real client IP + that the original request was HTTPS.

**That's the whole proxy.** Three functional lines because Caddy's secure defaults do the rest (TLS, redirect, HSTS-capable, sane timeouts).

### The compose service — where Caddy gets its powers
```yaml
caddy:
  image: caddy:2.9.1          # exact-pinned (owner rule #1) — reproducible
  restart: unless-stopped     # auto-restart on crash/reboot (Ch 09/10)
  ports: ["80:80","443:443"]  # the ONLY container publishing to the internet
  environment: { DOMAIN: ${DOMAIN} }   # fills {$DOMAIN} in the Caddyfile
  volumes:
    - ./deploy/Caddyfile:/etc/caddy/Caddyfile:ro   # config, read-only
    - caddy_data:/data                             # ★ stores the TLS certs + keys
    - caddy_config:/config
  depends_on: [app]           # start after the app exists
```
- **`caddy_data:/data`** is critical: Caddy stores the **issued certificates + private keys + ACME account** here. Because it's a **named volume** ([Ch 20](20_Docker_Volumes.md)), certs **survive container rebuilds** — so you don't re-request a cert (and hit Let's Encrypt rate limits) on every deploy.
- **`ports: 80 + 443`** — 443 serves HTTPS; **80 is required** so Let's Encrypt's HTTP-01 challenge can reach Caddy to issue/renew ([Ch 04](04_DNS_Domains.md)). Don't close 80.
- **Caddyfile mounted `:ro`** — the container reads config but can't alter it ([Ch 08](08_File_System.md)).

### The one prerequisite
Before Caddy can get a cert: the **`DOMAIN`'s DNS A record must point at this VPS** and **ports 80+443 must be open** ([Ch 04](04_DNS_Domains.md)/[Ch 05](05_IP_Address_and_Ports.md)). DNS first → then Caddy succeeds on first boot.

> 💡 **Samjho aise:** Caddy wo guard hai jo **HTTPS ka certificate khud le aata hai** aur khud renew karta hai. Purane zamane mein yeh kaam haath se hota tha (aur log bhool jaate the, site down ho jaati thi). Caddy ki config chhoti hoti hai kyunki usne **sahi default** chun liye hain — yahi uski taakat hai.

# Real World Example (My ERP)
Boot sequence, concretely:
1. `docker compose up` starts `caddy` with `DOMAIN=erp.<mydomain>` from `.env`.
2. Caddy reads the Caddyfile, sees a real domain, and runs the ACME HTTP-01 challenge over port 80; Let's Encrypt verifies + issues a cert; Caddy stores it in `caddy_data`.
3. Caddy now serves HTTPS on 443, redirects HTTP→HTTPS, compresses, and proxies to `app:8000`, adding `X-Forwarded-Proto: https`.
4. Django (`production.py`) trusts that header (`SECURE_PROXY_SSL_HEADER`), so its `SECURE_SSL_REDIRECT`/secure-cookies/HSTS all behave — no redirect loop.
5. ~60 days later Caddy renews the cert automatically; I do nothing.
If I ever see **502 Bad Gateway**, it means Caddy is up but `app:8000` isn't reachable (Gunicorn crashed / not healthy) — a `docker compose logs app` problem, not a Caddy one ([Ch 03](03_HTTP_HTTPS.md)).

# Visual Diagram
```
 .env DOMAIN=erp.example.com ─► compose env ─► {$DOMAIN} in Caddyfile
                                                     │
 Let's Encrypt ◄── ACME HTTP-01 on :80 ──────────── CADDY :443/:80
      │  issues cert ──► stored in caddy_data volume (survives rebuilds)
      ▼
 browser ──HTTPS──► CADDY  { encode gzip ; reverse_proxy app:8000 }
                      │ adds X-Forwarded-Proto: https
                      ▼
                    app:8000 (Gunicorn)  →  Django trusts SECURE_PROXY_SSL_HEADER

 502 = Caddy up but app:8000 down     |     cert fails = DNS/:80 not ready
```

# Practical — how to inspect it
```bash
docker compose logs caddy | grep -iE 'certificate|acme|obtain|renew'  # cert issuance/renewal
docker compose exec caddy caddy validate --config /etc/caddy/Caddyfile # config valid?
```
```bash
# Reload Caddy after editing the Caddyfile (zero-downtime, no full restart)
docker compose exec caddy caddy reload --config /etc/caddy/Caddyfile
#  (or) docker compose restart caddy
```
```bash
# See the live cert Caddy is serving + its expiry (from your laptop)
echo | openssl s_client -connect erp.<domain>:443 -servername erp.<domain> 2>/dev/null \
  | openssl x509 -noout -issuer -dates      # issuer=Let's Encrypt, notAfter=~90d out
```
```bash
# Where are the certs stored?
docker compose exec caddy ls -R /data/caddy/certificates   # the caddy_data volume
```
```bash
curl -sI http://erp.<domain>/    # expect 30x redirect to https (Caddy's default)
curl -sI https://erp.<domain>/   # expect 200 (or your app's redirect), served by Caddy
```

# Production Walkthrough
- `deploy/Caddyfile` is the entire public configuration — a handful of lines because Caddy's defaults are already the right ones.
- **Automatic HTTPS**: on first start Caddy proves domain control (ACME), fetches a certificate, and renews it before expiry. The classic "certificate expired on a Sunday" outage simply cannot happen here.
- It reverse-proxies to the `web` service by name on the private network (ch 19) and serves `/static/` and `/media/` from volumes directly (ch 25).
- Certificates are stored in a volume — losing it means re-issuing, which is harmless but rate-limited, so keep the volume.

# Debugging Guide
1. **`docker compose logs caddy`** — certificate problems are always explained here, in plain English.
2. **Certificate failing?** DNS not pointing at this server yet, or **port 80 blocked** (the challenge needs it). Both are external to Caddy.
3. **`caddy validate --config /etc/caddy/Caddyfile`** before reload — a syntax error should not take the site down.
4. **502** → the upstream name/port is wrong or the app is down.
5. **Hitting ACME rate limits** while experimenting? Use the staging issuer, not repeated production attempts.

# Performance Notes
- Static files served by Caddy never touch Python — the single biggest easy win.
- HTTP/2 and compression are on by default; no tuning needed for this workload.
- Caddy is written in Go and handles far more concurrency than this factory will ever produce; it will not be your bottleneck.

# Security Considerations
- Modern TLS defaults out of the box — you are not choosing cipher suites by hand, which is where people get it wrong.
- Add security headers deliberately (HSTS, `X-Content-Type-Options`, referrer policy) — Caddy makes this a couple of lines.
- **Body-size limits belong here**, at the edge, so oversized uploads never reach a worker.
- Serve `/media/` as static content only; user-uploaded files must never be executable.

# Architecture Decisions
- **Caddy over Nginx** for automatic certificates and a config small enough to review in one screen — for a solo maintainer that is a real reliability gain (ch 13 argues the other side fairly).
- **Config in git** (`deploy/Caddyfile`) so the public surface is reviewable and reproducible.
- **Certificates in a named volume** so restarts do not re-issue.

# Best Practices
- Validate config before reloading.
- Keep the Caddyfile short; every line is public attack surface you must understand.
- Set explicit limits rather than trusting defaults for uploads.
- Read Caddy's logs first for anything TLS-related; they are unusually clear.

# Beginner Mistakes
- **Closing port 80** "because we use HTTPS" → Let's Encrypt HTTP-01 renewal fails → cert eventually expires → hard browser errors. Keep 80 open.
- **Not persisting `caddy_data`** → every rebuild re-requests certs → you hit Let's Encrypt **rate limits** and get temporarily blocked. The named volume prevents this.
- **Requesting TLS before DNS is live** → ACME fails on first boot. DNS A record first ([Ch 04](04_DNS_Domains.md)).
- **Blaming Caddy for 502** → 502 means the **upstream (`app:8000`) is down**, not Caddy. Check `docker compose logs app`.
- **Hardcoding the domain in the Caddyfile** instead of `{$DOMAIN}` → can't reuse config across staging/prod; the env placeholder keeps it portable.
- **Editing the Caddyfile and forgetting to reload** → old config still active. `caddy reload`.

# Interview Questions
- **Junior:** "How does Caddy give you HTTPS?" — You give it a domain; it automatically requests a free Let's Encrypt certificate, installs it, serves HTTPS, redirects HTTP→HTTPS, and auto-renews — no manual cert steps.

- **Mid:** "Walk through my 3-line Caddyfile." — `{$DOMAIN}` = site address from an env var (a real domain → auto-HTTPS); `encode gzip` = compress responses; `reverse_proxy app:8000` = forward to the Gunicorn `app` service via Docker DNS, adding `X-Forwarded-*` headers. Defaults handle TLS + redirect.

- **Senior:** "Certs vanished / rate-limited after a redeploy. Root cause + fix?" — The `caddy_data` volume wasn't persisted (or was wiped), so Caddy re-requested certs each deploy and hit Let's Encrypt's issuance rate limit. Fix: ensure `caddy_data:/data` is a persistent named volume so certs/keys survive; if rate-limited, wait out the window or use the staging ACME endpoint while testing.

- **Staff:** "Why is a 3-line Caddyfile safe for production here, and when would you outgrow it?" — Caddy's secure defaults (auto-TLS, HTTP→HTTPS, modern ciphers, sane timeouts) cover a single-app single-domain edge, and the app enforces its own security headers/HSTS in `production.py`, so minimal config = fewer footguns. You'd add config when you need: path-based routing to multiple upstreams, load-balancing across app replicas, per-route rate limits/auth, request-size caps, or serving static/media directly at the edge — all expressible in Caddy, just not needed yet.

### Why interviewers ask these — and the answer that separates levels

| Testing for | Weak answer | What lands |
|---|---|---|
| Do you know what "automatic HTTPS" actually does? | "Caddy handles the certificate for you." | Given a real domain it **requests a Let's Encrypt cert, installs it, serves HTTPS, redirects HTTP→HTTPS, and auto-renews** — no cert steps in your runbook at all. That is four manual jobs deleted, not one. |
| Can you read the 3-line Caddyfile? | "It proxies to the app." | `{$DOMAIN}` = site address **from an env var** (real domain ⇒ auto-HTTPS) · `encode gzip` · `reverse_proxy app:8000` reaches Gunicorn **by Docker DNS name** and adds the **`X-Forwarded-*`** headers Django depends on (ch 11). |
| Certs vanished after a redeploy — root cause? | "Let's Encrypt rate-limited us, we have to wait." | The rate limit is the **symptom**. The cause is that **`caddy_data` was not a persistent volume**, so Caddy re-requested certs on every deploy until it hit the limit. Fix the volume, not the waiting. |
| Can you defend a 3-line config for production? | "It is minimal, we should add more directives." | Caddy's **secure defaults** (auto-TLS, HTTP→HTTPS, modern ciphers, sane timeouts) cover a single-app single-domain edge, and the app sets its own **HSTS and security headers** in `production.py`. **Minimal config is fewer things to get wrong** — say where you would outgrow it (WAF, multi-site, fine tuning). |

**The killer follow-up:** *"Reload after editing the Caddyfile — full restart or something better?"* — **reload, zero-downtime**, no dropped connections. Anyone whose only tool is `restart` will take a small outage every time they touch a header.

# Revision Notes
- Caddy = reverse proxy with **automatic HTTPS** (issue + renew, no cron).
- Needs **DNS correct and port 80 open** to get a certificate.
- Serves static/media directly; proxies everything else to `web`.
- Set **body limits and security headers** here, at the edge.
- Config lives in `deploy/Caddyfile`, in git.

# Cheat Sheet
- **Caddy = reverse proxy with automatic Let's Encrypt HTTPS** (issue + renew, no cron).
- **My Caddyfile:** `{$DOMAIN} { encode gzip ; reverse_proxy app:8000 }` — domain-from-env, compress, proxy to Gunicorn.
- **Auto-HTTPS trigger:** a real domain as the site address (not localhost/IP).
- **`caddy_data` volume = the certs** — must persist or you re-request + hit rate limits.
- **Keep port 80 open** for ACME renewal. **DNS A record first**, then certs issue.
- **502 = upstream `app` down**, not Caddy. Reload after edits: `caddy reload`.

# My ERP Section
| Concept | In my ERP |
|---|---|
| Config file | `deploy/Caddyfile` (3 functional lines) |
| Image | `caddy:2.9.1` (pinned) |
| Public ports | 80 + 443 (only container that publishes) |
| Domain source | `{$DOMAIN}` ← `DOMAIN` env ← `.env` |
| Upstream | `reverse_proxy app:8000` (Docker DNS) |
| Cert storage | `caddy_data:/data` volume (persists certs) |
| Forwarded scheme | auto `X-Forwarded-Proto` ↔ `SECURE_PROXY_SSL_HEADER` |
| Compression | `encode gzip` |

# Practice Tasks
1. **Read the code:** open `deploy/Caddyfile` and annotate every directive with what it does.
2. **Debug:** break the config deliberately, run `caddy validate`, and read the error. Fix it.
3. **Design:** add HSTS and a 50 MB body limit. Write the exact lines.
4. **Architecture:** argue when you would switch to Nginx for this project. Be specific about the trigger.

# Homework
1. Open `deploy/Caddyfile` and annotate each line in your own words. Which line makes HTTPS automatic, and why?
2. In `docker-compose.yml`, find the `caddy` service. Which volume stores certs? What breaks if it's not persistent?
3. Explain why port 80 must stay open even though users use HTTPS.
4. Predict: DNS not yet pointed at the VPS, you `docker compose up`. What does Caddy log, and what does a browser see? (Then verify on the real VPS.)
5. Explain what a `502 Bad Gateway` from Caddy tells you and which logs you'd read.

---

# Further Reading & Live Resources
- Caddy docs — *Getting Started*: https://caddyserver.com/docs/getting-started
- Caddy docs — *Caddyfile concepts* + *reverse_proxy* + *encode*: https://caddyserver.com/docs/caddyfile/concepts · https://caddyserver.com/docs/caddyfile/directives/reverse_proxy · https://caddyserver.com/docs/caddyfile/directives/encode
- Caddy docs — *Automatic HTTPS* (how/why it just works): https://caddyserver.com/docs/automatic-https
- Caddy + Docker Compose guide: https://caddyserver.com/docs/running#docker-compose
- Let's Encrypt — *Rate limits* (why persisting `caddy_data` matters): https://letsencrypt.org/docs/rate-limits/
- **Live tool** — SSL Labs test your HTTPS grade: https://www.ssllabs.com/ssltest/
