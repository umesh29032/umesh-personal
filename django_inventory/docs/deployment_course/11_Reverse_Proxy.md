---
id: deploy-course-11-reverse-proxy
type: lesson
status: active
owner: handwritten
scope: deployment, operations — this ERP shipped to a VPS
anchors: docker-compose.yml, deploy/entrypoint.sh, deploy/Caddyfile, deploy/backup.sh
verified: 2026-08-01
---

# 11 — Reverse Proxy

> Part of [Deployment From Zero](00_COURSE_OVERVIEW.md). Prev: [10 — systemd](10_Systemd.md). Next: [12 — Caddy](12_Caddy.md). *(Term 3 — The web front.)*

# Learning Objectives
By the end of this chapter you can:
- explain what a reverse proxy does that an app server should not
- name four jobs it takes off your workers
- say why one slow client can freeze an unproxied app
- read a proxy config and trace where a request goes

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

> 💡 **Samjho aise:** Reverse proxy building ka **guard + reception** hai. Bahar ki duniya usse baat karti hai, aap ke app se seedha koi nahi. Wo TLS ka lifafa kholta hai, static files khud de deta hai, dheeme client ko rok ke rakhta hai — taaki andar baithe workers ek slow aadmi ki wajah se saare kaam na rok den.

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

# Production Walkthrough
- **Caddy is the only process the internet touches.** It terminates TLS, serves static files, enforces limits, and forwards the rest to Gunicorn over the private network.
- **The slow-client problem is the reason it exists.** Without buffering, a client on bad wifi trickling a request occupies a Gunicorn worker for seconds. Three workers, three slow clients, site frozen — with idle CPU. The proxy absorbs that.
- Static files never reach Python: Caddy serves them straight from disk (ch 25/26), so workers only do application work.
- Django is configured to trust the proxy's forwarded headers, so it builds correct `https://` URLs and sees the real client IP.

# Debugging Guide
1. **502** = the proxy is up and the app is not (or is not answering). Check the app container.
2. **504** = the app is too slow; the proxy gave up. Find the slow request (ch 39), do not just raise the timeout.
3. **413** = upload larger than the proxy limit — raise it *there*, and check Django's limit too.
4. **Wrong scheme/host in links** = forwarded headers not trusted or not set.
5. **Real IP shows as the proxy's** = the app is reading the socket address instead of the forwarded header — relevant for rate limiting (ch 34).

# Performance Notes
- Static-file serving by Caddy is dramatically cheaper than by Python, and it frees workers for real work.
- Compression and HTTP/2 at the edge cut bytes and round-trips for phones on factory wifi (ch 02).
- Request buffering converts many slow clients into a queue at the proxy instead of blocked workers.
- The proxy adds a hop of microseconds — irrelevant next to what it saves.

# Security Considerations
- **One public process** means one place to harden: TLS versions, headers, limits, timeouts.
- The app never faces the internet, so app-level bugs are one layer further from an attacker.
- Body-size and rate limits at the edge stop abusive requests before they cost you a worker or a database query.
- Only trust forwarded headers from *your* proxy — trusting them blindly lets a client spoof its IP.

# Architecture Decisions
- **Separate proxy and app server** because the jobs are different: public-facing hardening vs running Python. Merging them means an app server doing security work badly.
- **Caddy over Nginx** here for automatic certificates and a small config (ch 12/13 compare them honestly).
- **Static served by the proxy**, so `collectstatic` output is a first-class deploy artefact (ch 26).

# Best Practices
- Never expose the app server directly, not even briefly.
- Set body-size and timeout limits deliberately rather than relying on defaults.
- Keep the proxy config in version control (`deploy/Caddyfile`) — it is infrastructure code.
- When a 5xx appears, decide first *which* process produced it.

# Beginner Mistakes
- **Exposing the app directly "to skip the proxy."** Loses TLS/static/buffering/limits; slow clients freeze workers.
- **Forgetting `X-Forwarded-Proto` trust** → redirect loop or "insecure" cookies ([Ch 03](03_HTTP_HTTPS.md)).
- **Serving big static/media through Django** at scale — wakes a worker per asset. Let the proxy (or WhiteNoise/CDN) do it.
- **Trusting forwarded headers blindly on a multi-hop path** — only trust `X-Forwarded-*` from *your* proxy, or clients can spoof their IP/scheme. (Single Caddy in front = safe.)
- **No request-size/timeout limits at the edge** — lets a huge upload or slow client hurt the app.

# Interview Questions
- **Junior:** "What is a reverse proxy?" — A server in front of your application that receives all client requests, handles public-facing concerns (TLS, static, limits), and forwards requests to the app on a private connection.

- **Mid:** "Name four jobs a reverse proxy does that the app server shouldn't." — TLS termination, static-file serving, slow-client buffering, and compression (also routing, load balancing, rate limiting, security headers). Keeping these off the app server frees its workers for app logic and shields them from hostile clients.

- **Senior:** "Why does terminating TLS at the proxy cause redirect loops, and how do you fix it?" — The app receives plain HTTP from the proxy, sees "not secure", and (with `SECURE_SSL_REDIRECT`) 301s to HTTPS — which the proxy again forwards as HTTP → loop. Fix: the proxy sets `X-Forwarded-Proto: https` and the app trusts it via `SECURE_PROXY_SSL_HEADER`, so it knows the original request was secure.

- **Staff:** "Design the edge for this ERP: what terminates where, and what's the trust model?" — One reverse proxy (Caddy) is the sole internet-facing component: it terminates TLS, enforces size/timeout limits + security headers, compresses, and forwards to Gunicorn over a private Docker network that publishes no ports. The app trusts `X-Forwarded-*` only because there's exactly one proxy in front (no spoofable multi-hop). Data stores are unreachable from outside by construction. Scale later by putting N app instances behind the same proxy as a load-balancer upstream ([Ch 41](41_Scaling.md)) — the edge contract doesn't change.

### Why interviewers ask these — and the answer that separates levels

| Testing for | Weak answer | What lands |
|---|---|---|
| Can you name jobs the app server should NOT do? | "The proxy forwards requests to the app." | Four, minimum: **TLS termination · static-file serving · slow-client buffering · compression**. Each one removed keeps a Gunicorn worker free for app logic — a worker held open by a slow client is capacity you paid for and lost. |
| Do you know why the redirect loop happens? | "Turn off SECURE_SSL_REDIRECT to fix the loop." | The app sees **plain HTTP** from the proxy, decides "not secure", 301s to HTTPS, and the proxy forwards it as HTTP again → loop. Fix: proxy sets **`X-Forwarded-Proto`** and Django trusts it via **`SECURE_PROXY_SSL_HEADER`**. Turning the redirect off hides the loop and drops your HTTPS enforcement. |
| Do you know why buffering is a *security* feature? | "Buffering makes things faster." | It is the defence against **slowloris-style** slow clients: the proxy absorbs a trickle-fed request and hands the app a complete one, so a handful of malicious connections cannot occupy every worker. |
| Can you state the trust model? | "The proxy is in front, so the app is safe." | **One** internet-facing component (Caddy); the app is reachable **only** on the private Docker network; the app trusts `X-Forwarded-*` **because nothing else can reach it**. If the app were also publicly reachable, trusting that header would let anyone claim HTTPS. |

**The killer follow-up:** *"Why is trusting `X-Forwarded-Proto` safe here but a vulnerability elsewhere?"* — because the app has **no published port**, so only Caddy can set it. Expose the app directly and the same setting lets a client forge "I am secure". The setting is not safe or unsafe by itself — **the network topology is what makes it either**.

# Revision Notes
- Reverse proxy = the public front door; app server runs the code.
- It handles **TLS · static files · buffering · limits**.
- Without it, one slow client can occupy a worker — frozen site, idle CPU.
- **502** app down · **504** app too slow · **413** body too large.
- Trust forwarded headers only from your own proxy.

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

# Practice Tasks
1. **Read the code:** open `deploy/Caddyfile` and trace exactly where a request for `/static/x.css` goes versus `/production/addas/`.
2. **Debug:** stop the app container and observe the status Caddy returns. Then start it and watch the difference.
3. **Design:** pattern videos are 50 MB. List every limit you must change, in both the proxy and Django.
4. **Architecture:** argue whether the proxy should also do caching for this ERP. What is cacheable in a system where almost every page is per-user?

# Homework
1. `docker compose ps` — list which container publishes host ports. Explain why that's the only one the internet reaches.
2. In `production.py`, find `SECURE_PROXY_SSL_HEADER`. Explain what breaks if you delete it, given Caddy terminates TLS.
3. Watch the same request in `docker compose logs caddy` and `docker compose logs app` — note Caddy sees HTTPS:443, app sees HTTP:8000. Why is the plaintext hop safe?
4. List, from memory, five jobs Caddy does so Gunicorn doesn't have to.
5. Read the header comment in `deploy/Caddyfile` — how does it describe Caddy's role? (Then [Ch 12](12_Caddy.md) walks the file.)

---

# Further Reading & Live Resources
- Cloudflare Learning — *What is a reverse proxy?*: https://www.cloudflare.com/learning/cdn/glossary/reverse-proxy/
- NGINX — *What is a reverse proxy server?*: https://www.nginx.com/resources/glossary/reverse-proxy-server/
- Django docs — *SECURE_PROXY_SSL_HEADER* (the forwarded-proto setting): https://docs.djangoproject.com/en/5.0/ref/settings/#secure-proxy-ssl-header
- Caddy docs — *reverse_proxy* directive: https://caddyserver.com/docs/caddyfile/directives/reverse_proxy
- OWASP — *Slowloris / slow HTTP attacks* (why buffering matters): https://owasp.org/www-community/attacks/Slowloris_DoS_Attack
