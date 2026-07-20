# 11 — Reverse Proxy

> Part of [Deployment From Zero](00_COURSE_OVERVIEW.md). Prev: [10 — systemd](10_Systemd.md). Next: [12 — Caddy](12_Caddy.md). *(Term 3 — The web front.)*

# Purpose
[Ch 01](01_What_Is_Deployment.md) introduced the idea; this chapter makes the **reverse proxy** concept rigorous, because it's the single most important box in the production diagram — the only thing the internet touches, and the specialist that does every public-facing job so Gunicorn doesn't have to.

# The Problem
Gunicorn runs Django well but is a bad *front door*: it can't cheaply serve static files, terminate TLS, buffer slow clients, compress responses, or route by path — and if exposed, a few slow clients freeze all its workers ([Ch 01](01_What_Is_Deployment.md)/[Ch 09](09_Processes_and_Services.md)). I need a hardened, purpose-built program in front to absorb the hostile internet and hand clean requests to the app.

# Theory (from zero)

### Forward vs reverse proxy
- A **forward proxy** sits in front of *clients* going out (e.g. a corporate proxy filtering employees' web traffic). It represents the client.
- A **reverse proxy** sits in front of *your servers* taking requests in. It represents the server. Clients think they're talking to your app; really they're talking to the proxy, which forwards to the app privately.

### The jobs a reverse proxy does (why it exists)
1. **TLS termination** — handles HTTPS/certs so the app speaks plain HTTP internally ([Ch 03](03_HTTP_HTTPS.md)).
2. **Static file serving** — serves CSS/JS/images directly, fast, without waking a Python worker.
3. **Slow-client buffering** — reads the full slow request, then hands it to the app in one shot; a client sending 1 byte/sec ties up the proxy (built for it), not a precious Gunicorn worker.
4. **Compression** — gzip/brotli responses to save bandwidth.
5. **Routing** — send `/static/*` one place, `/api/*` another, everything else to the app.
6. **Load balancing** — spread requests across multiple app instances ([Ch 41](41_Scaling.md)).
7. **Limits & security** — max request size, timeouts, rate limits, security headers; a single choke point to defend.
8. **Header injection** — tells the app the real client IP + original scheme (`X-Forwarded-For`, `X-Forwarded-Proto`).

### The trust boundary
Public (untrusted) traffic terminates at the proxy. Between proxy and app is a **private** network ([Ch 19](19_Docker_Networking.md)) — plaintext HTTP is fine there because the internet can't reach it. This is why only the proxy publishes ports ([Ch 05](05_IP_Address_and_Ports.md)).

### The `X-Forwarded-Proto` gotcha
When the proxy terminates TLS, the app *receives* plain HTTP and would think "this isn't secure" — breaking HTTPS redirects (infinite loop) and secure-cookie logic. The proxy sets **`X-Forwarded-Proto: https`**; the app is told to trust it (`SECURE_PROXY_SSL_HEADER` — [Ch 03](03_HTTP_HTTPS.md)). Get this wrong and you get redirect loops.

### Popular reverse proxies
**Caddy** (auto-HTTPS, tiny config — your choice, [Ch 12](12_Caddy.md)), **Nginx** (ubiquitous, powerful, more config — [Ch 13](13_Nginx_Comparison.md)), Traefik, HAProxy, Apache.

# Real World Example (My ERP)
- **Caddy is the only public-facing box.** `docker-compose.yml` publishes only Caddy's `80:80` + `443:443`; `app`/`db`/`redis` publish nothing.
- Caddy **terminates TLS** (auto Let's Encrypt), **compresses** (`encode gzip`), and **reverse-proxies** the request to the app service at `app:8000` over the private Docker network.
- It sets **`X-Forwarded-Proto`**, which pairs with Django's `SECURE_PROXY_SSL_HEADER=('HTTP_X_FORWARDED_PROTO','https')` (`production.py`) — the Caddyfile comment literally notes it's "the ONE TLS-terminating proxy (PD's SECURE_PROXY_SSL_HEADER assumption)."
- Static files: at this scale my Django serves compressed static via **WhiteNoise** ([Ch 25](25_Static_vs_Media.md)), so Caddy just proxies; a larger deploy could route `/static/*` to Caddy directly. Either way the *principle* holds — the proxy is the edge.
- Result: the hostile internet only ever reaches Caddy; Gunicorn's 3 workers only see clean, buffered, internal requests.

# Visual Diagram
```
        forward proxy:  client → [proxy] → many sites     (fronts the CLIENT)
        reverse proxy:  many clients → [proxy] → your app (fronts the SERVER)  ← us

  INTERNET (untrusted)                    │  PRIVATE docker net (trusted)
     phones/laptops ──HTTPS 443──►  CADDY  ── HTTP app:8000 ──►  GUNICORN → Django
                                    (only public box)             (never sees internet)
     jobs Caddy does:  TLS · gzip · buffer slow clients · limits · X-Forwarded-Proto
     Gunicorn is freed to do ONE thing: run Django for clean internal requests
```

# Practical — how to inspect it
```bash
# Confirm only the proxy is public
docker compose ps          # only caddy shows 0.0.0.0:80/443; app/db/redis = no host ports
```
```bash
# See the proxy add forwarded headers (from a shell that can reach the app)
docker compose exec app python -c "print('app only speaks plain HTTP internally')"
curl -sI https://erp.<domain>/ | grep -i -E 'server|strict-transport'   # served via Caddy, HSTS present
```
```bash
# Watch the two hops: browser→Caddy (TLS) and Caddy→app (plain)
docker compose logs -f caddy   # access lines: method, path, status, upstream
docker compose logs -f app     # gunicorn access lines for the SAME request (internal)
```
```bash
# Prove the slow-client protection matters conceptually: (don't DoS yourself)
#  a proxy buffers a slow request fully before touching the app; Gunicorn workers stay free.
```

# Beginner Mistakes
- **Exposing the app directly "to skip the proxy."** Loses TLS/static/buffering/limits; slow clients freeze workers.
- **Forgetting `X-Forwarded-Proto` trust** → redirect loop or "insecure" cookies ([Ch 03](03_HTTP_HTTPS.md)).
- **Serving big static/media through Django** at scale — wakes a worker per asset. Let the proxy (or WhiteNoise/CDN) do it.
- **Trusting forwarded headers blindly on a multi-hop path** — only trust `X-Forwarded-*` from *your* proxy, or clients can spoof their IP/scheme. (Single Caddy in front = safe.)
- **No request-size/timeout limits at the edge** — lets a huge upload or slow client hurt the app.

# Interview Questions
**Junior — "What is a reverse proxy?"** A server in front of your application that receives all client requests, handles public-facing concerns (TLS, static, limits), and forwards requests to the app on a private connection.

**Mid — "Name four jobs a reverse proxy does that the app server shouldn't."** TLS termination, static-file serving, slow-client buffering, and compression (also routing, load balancing, rate limiting, security headers). Keeping these off the app server frees its workers for app logic and shields them from hostile clients.

**Senior — "Why does terminating TLS at the proxy cause redirect loops, and how do you fix it?"** The app receives plain HTTP from the proxy, sees "not secure", and (with `SECURE_SSL_REDIRECT`) 301s to HTTPS — which the proxy again forwards as HTTP → loop. Fix: the proxy sets `X-Forwarded-Proto: https` and the app trusts it via `SECURE_PROXY_SSL_HEADER`, so it knows the original request was secure.

**Staff — "Design the edge for this ERP: what terminates where, and what's the trust model?"** One reverse proxy (Caddy) is the sole internet-facing component: it terminates TLS, enforces size/timeout limits + security headers, compresses, and forwards to Gunicorn over a private Docker network that publishes no ports. The app trusts `X-Forwarded-*` only because there's exactly one proxy in front (no spoofable multi-hop). Data stores are unreachable from outside by construction. Scale later by putting N app instances behind the same proxy as a load-balancer upstream ([Ch 41](41_Scaling.md)) — the edge contract doesn't change.

# Cheat Sheet
- **Reverse proxy fronts the SERVER** (forward proxy fronts the client). Only the proxy is public.
- **Jobs:** TLS termination · static serving · slow-client buffering · compression · routing · load balancing · limits/security · forwarded headers.
- **Trust boundary:** internet→proxy (TLS), proxy→app (plain, private).
- **`X-Forwarded-Proto` + `SECURE_PROXY_SSL_HEADER`** or you get redirect loops.
- My ERP: **Caddy** = the one public box → `app:8000` private.
- Inspect: `docker compose ps` (only caddy public), `docker compose logs caddy`/`app`.

# My ERP Section
| Concept | In my ERP |
|---|---|
| The proxy | Caddy (only public container) |
| Publishes | 80 + 443 (compose); app/db/redis private |
| Forwards to | `app:8000` (Docker DNS name) |
| TLS | terminated at Caddy (Let's Encrypt) |
| Compression | `encode gzip` (Caddyfile) |
| Forwarded scheme | `X-Forwarded-Proto` ↔ `SECURE_PROXY_SSL_HEADER` |
| Static at scale | WhiteNoise now; proxy/CDN option later |

# Homework
1. `docker compose ps` — list which container publishes host ports. Explain why that's the only one the internet reaches.
2. In `production.py`, find `SECURE_PROXY_SSL_HEADER`. Explain what breaks if you delete it, given Caddy terminates TLS.
3. Watch the same request in `docker compose logs caddy` and `docker compose logs app` — note Caddy sees HTTPS:443, app sees HTTP:8000. Why is the plaintext hop safe?
4. List, from memory, five jobs Caddy does so Gunicorn doesn't have to.
5. Read the header comment in `deploy/Caddyfile` — how does it describe Caddy's role? (Then [Ch 12](12_Caddy.md) walks the file.)

---

## Further Reading & Live Resources
- Cloudflare Learning — *What is a reverse proxy?*: https://www.cloudflare.com/learning/cdn/glossary/reverse-proxy/
- NGINX — *What is a reverse proxy server?*: https://www.nginx.com/resources/glossary/reverse-proxy-server/
- Django docs — *SECURE_PROXY_SSL_HEADER* (the forwarded-proto setting): https://docs.djangoproject.com/en/5.0/ref/settings/#secure-proxy-ssl-header
- Caddy docs — *reverse_proxy* directive: https://caddyserver.com/docs/caddyfile/directives/reverse_proxy
- OWASP — *Slowloris / slow HTTP attacks* (why buffering matters): https://owasp.org/www-community/attacks/Slowloris_DoS_Attack
