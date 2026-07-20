# 13 — Nginx (and why we chose Caddy)

> Part of [Deployment Course](00_COURSE_OVERVIEW.md). Prev: [12 — Caddy](12_Caddy.md). Next: [14 — Gunicorn](14_Gunicorn.md).

# Purpose
Nginx is the world's most common reverse proxy — you'll meet it in almost every tutorial, job, and legacy system. This chapter explains what it is, how it compares to my **Caddy** ([Ch 12](12_Caddy.md)), and *when* I'd switch — so I can read any Nginx config and make an informed choice instead of cargo-culting.

# The Problem
Most Django deployment guides say "Nginx + Gunicorn". My ERP uses Caddy. If I only know Caddy, I'll be lost the moment I touch someone else's server, and I won't know whether my choice was right. I need to understand the alternative and the trade-off.

# Theory (from zero)

### What Nginx is
**Nginx** ("engine-x") is a high-performance web server + reverse proxy, ~2004, powering a huge fraction of the internet. It does the same **reverse-proxy jobs** as Caddy ([Ch 11](11_Reverse_Proxy.md)): TLS termination, static serving, buffering, compression, routing, load balancing. Config lives in `nginx.conf` / files under `/etc/nginx/sites-enabled/`.

### The core difference: HTTPS
- **Caddy:** HTTPS is **automatic + auto-renewing** by default (built-in ACME/Let's Encrypt). Zero cert code.
- **Nginx:** you wire up TLS **yourself** — install **certbot**, obtain the cert, point Nginx at the cert files, and rely on a **renewal cron/timer**. More steps, more to forget (the classic "site down because the cert expired and the cron didn't run").

### Config verbosity
My whole Caddy proxy is **3 lines** ([Ch 12](12_Caddy.md)). The equivalent Nginx is ~15–30 lines: `server {}` blocks, `listen 443 ssl`, `ssl_certificate` paths, `location / { proxy_pass … }`, a `proxy_set_header X-Forwarded-Proto $scheme;` you must not forget ([Ch 11](11_Reverse_Proxy.md)), plus a separate `server {}` for the HTTP→HTTPS redirect and gzip settings.

A minimal Nginx equivalent of my Caddyfile:
```nginx
server {                                  # HTTP → HTTPS redirect
    listen 80;
    server_name erp.example.com;
    return 301 https://$host$request_uri;
}
server {
    listen 443 ssl;
    server_name erp.example.com;
    ssl_certificate     /etc/letsencrypt/live/erp.example.com/fullchain.pem;   # from certbot
    ssl_certificate_key /etc/letsencrypt/live/erp.example.com/privkey.pem;
    gzip on;
    location / {
        proxy_pass http://app:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;   # ← forget this = redirect loop
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```
Everything Caddy did by default, spelled out — including the forwarded headers you set by hand.

### Where Nginx wins
- **Ecosystem/ubiquity:** more examples, modules, Stack Overflow answers, ops familiarity.
- **Fine-grained tuning** at very high scale (buffers, worker connections, caching layers).
- **Existing infra:** if the shop already runs Nginx, match it.

### Where Caddy wins (my case)
- **Automatic HTTPS** (no certbot, no renewal cron, no expiry surprise).
- **Tiny, hard-to-misconfigure config** — fewer footguns for a solo/junior operator.
- **Secure defaults** out of the box.

Both are excellent, production-grade, and proxy to Gunicorn identically. The choice is *operational ergonomics*, not capability.

# Real World Example (My ERP)
- I run **Caddy** precisely because I'm a solo operator who values not babysitting certs: `deploy/Caddyfile` is 3 lines and HTTPS renews itself ([Ch 12](12_Caddy.md)).
- If this ERP later joined a company already standardized on **Nginx** (with its own cert automation, CDN, WAF), I'd swap the `caddy` service for an `nginx` service + the config above + a certbot sidecar — **nothing else in the stack changes** (Gunicorn still listens on `app:8000`; Django still trusts `X-Forwarded-Proto`). That swap-ability is the point: the reverse-proxy *contract* ([Ch 11](11_Reverse_Proxy.md)) is the same; only the front box's config differs.
- The one thing I must preserve on any proxy: set **`X-Forwarded-Proto`** (Caddy auto; Nginx by hand) so `SECURE_PROXY_SSL_HEADER` works and I avoid redirect loops.

# Visual Diagram
```
  SAME jobs, SAME upstream — different front box + config effort

  CADDY (mine)                         NGINX (the classic)
  ┌───────────────────┐                ┌───────────────────────────────┐
  │ {$DOMAIN} {        │                │ server{listen 80; return 301…} │
  │   encode gzip      │  ⇄ equivalent  │ server{listen 443 ssl;         │
  │   reverse_proxy    │                │   ssl_certificate …(certbot)   │
  │     app:8000       │                │   location/ { proxy_pass …;    │
  │ }                  │                │     X-Forwarded-Proto $scheme}}│
  └───────────────────┘                └───────────────────────────────┘
  auto-HTTPS, 3 lines                   manual certbot + cron, ~20 lines
                    both ──► app:8000 (Gunicorn) ──► Django
```

# Practical — how to inspect it (read an Nginx box)
```bash
nginx -t                              # test config syntax (do before reload)
sudo systemctl reload nginx           # apply config without dropping connections
cat /etc/nginx/sites-enabled/*        # the active site configs
ls /etc/letsencrypt/live/             # certbot-managed certs (if used)
sudo certbot renew --dry-run          # test the renewal you must maintain
```
```bash
# My Caddy equivalents (for contrast)
docker compose exec caddy caddy validate --config /etc/caddy/Caddyfile   # = nginx -t
docker compose exec caddy caddy reload --config /etc/caddy/Caddyfile     # = reload nginx
# (no certbot/renew step exists — Caddy does it internally)
```

# Beginner Mistakes
- **Forgetting `proxy_set_header X-Forwarded-Proto $scheme;` in Nginx** → Django redirect loop / insecure cookies ([Ch 11](11_Reverse_Proxy.md)). (Caddy sets it for you.)
- **Letting certbot renewal lapse** → cert expires → hard HTTPS errors. Nginx makes renewal *your* job; monitor it.
- **Editing config and not testing** → `nginx -t` first, always; a bad reload can take the site down.
- **Copy-pasting a giant Nginx config you don't understand** — every `proxy_*`/buffer/timeout line has meaning; unknown lines are future outages.
- **Thinking one is "better" absolutely** — they're both great; pick for *your* ops reality.

# Interview Questions
**Junior — "What is Nginx?"** A high-performance web server and reverse proxy used to terminate TLS, serve static files, and forward requests to an app server like Gunicorn.

**Mid — "Caddy vs Nginx — the practical difference?"** Same capabilities; Caddy gives automatic, auto-renewing HTTPS and a tiny config, while Nginx needs manual TLS (certbot + renewal) and more verbose config but has a larger ecosystem and finer tuning. Choose Caddy for low-ops simplicity, Nginx for ubiquity/existing infra.

**Senior — "You're handed an Nginx+Gunicorn box with intermittent redirect loops on login. First check?"** The `location` block's forwarded headers — specifically `proxy_set_header X-Forwarded-Proto $scheme;` (and that Django's `SECURE_PROXY_SSL_HEADER` matches). Missing/incorrect forwarded scheme makes Django think HTTPS requests are HTTP and 301 them in a loop.

**Staff — "When would you migrate this ERP from Caddy to Nginx, and how, safely?"** When joining infra standardized on Nginx (shared config mgmt, WAF, CDN, cert automation) or needing tuning Caddy can't express easily. Migrate by adding an Nginx service with a config mirroring the Caddyfile's behavior (TLS via existing automation or certbot, gzip, `proxy_pass app:8000`, forwarded headers), test on a staging domain, then cut over DNS/ports; the app/DB/redis are untouched because the proxy contract is identical. Keep Caddy config in git so rollback is a one-service swap.

# Cheat Sheet
- **Nginx = the ubiquitous reverse proxy;** same jobs as Caddy, but **manual TLS (certbot + renewal cron)** and **verbose config**.
- **Caddy = automatic HTTPS + 3-line config;** why I chose it (solo, low-ops).
- **Swappable:** both proxy to `app:8000`; only the front box's config changes. Preserve **`X-Forwarded-Proto`**.
- **Nginx ops:** `nginx -t` → `systemctl reload nginx`; watch `certbot renew`.
- Pick for *your* reality: ubiquity/tuning (Nginx) vs simplicity/auto-certs (Caddy).

# My ERP Section
| Concept | In my ERP |
|---|---|
| Proxy in use | Caddy (auto-HTTPS, 3-line config) |
| Nginx role | the alternative I could swap to; would need certbot + ~20-line config |
| Invariant on any proxy | set `X-Forwarded-Proto` (Caddy auto; Nginx manual) |
| What a swap touches | only the front container/config — app/db/redis unchanged |
| Cert renewal | Caddy: automatic · Nginx: certbot cron (my responsibility) |

# Homework
1. Read the minimal Nginx config above and map each line to a line/behavior in my 3-line Caddyfile.
2. Which single Nginx line, if omitted, reproduces the redirect-loop bug — and what's the Caddy equivalent (auto or manual)?
3. List two reasons you'd pick Nginx and two reasons you'd pick Caddy for a given project.
4. Explain why swapping Caddy→Nginx wouldn't require any change to the `app`, `db`, or `redis` services.

---

## Further Reading & Live Resources
- Nginx docs — *Beginner's Guide*: https://nginx.org/en/docs/beginners_guide.html
- DigitalOcean — *Django with Gunicorn and **Nginx*** (the classic setup to contrast): https://www.digitalocean.com/community/tutorials/how-to-set-up-django-with-postgres-nginx-and-gunicorn-on-ubuntu-22-04
- Certbot (Let's Encrypt for Nginx — the manual renewal Caddy avoids): https://certbot.eff.org/
- Caddy docs — *Caddy vs. Nginx / migration notes*: https://caddyserver.com/docs/
- **Live tool** — Nginx config generator (DigitalOcean): https://www.digitalocean.com/community/tools/nginx
- Mozilla SSL Config Generator (TLS snippets for Nginx): https://ssl-config.mozilla.org/
