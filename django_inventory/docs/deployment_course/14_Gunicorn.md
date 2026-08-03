---
id: deploy-course-14-gunicorn
type: lesson
status: active
owner: handwritten
scope: deployment, operations — this ERP shipped to a VPS
anchors: docker-compose.yml, deploy/entrypoint.sh, deploy/Caddyfile, deploy/backup.sh
verified: 2026-08-01
---

# 14 — Gunicorn (my app server, real config)

> Part of [Deployment Course](00_COURSE_OVERVIEW.md). Prev: [13 — Nginx Comparison](13_Nginx_Comparison.md). Next: [15 — WSGI & ASGI](15_WSGI_ASGI.md).

# Learning Objectives
By the end of this chapter you can:
- explain what an application server does that a framework does not
- choose a worker count from first principles
- tell a worker crash from a container restart
- shut down without dropping in-flight requests

# Purpose
To fully understand the program that actually **runs my Django app in production** — Gunicorn — from my real `Dockerfile` `CMD`: what a worker is, how many I run and why, how requests are handled concurrently, timeouts, graceful reloads, and where its logs go. This is the engine; [Ch 11–13](11_Reverse_Proxy.md) were the front door.

# The Problem
`runserver` can't serve a factory of concurrent users ([Ch 01](01_What_Is_Deployment.md)). Gunicorn can — but only if I understand workers (too few = slow, too many = OOM), timeouts (too short = killed long requests, too long = stuck workers), and graceful reloads (so deploys don't drop requests). Mis-tuning Gunicorn is a top cause of "the site is slow/frozen even though CPU is idle."

# Theory (from zero)

### What Gunicorn is
**Gunicorn** ("Green Unicorn") is a production **WSGI server** (WSGI = the standard way a Python web app and a web server talk to each other; full story in [Ch 15](15_WSGI_ASGI.md)): it loads my Django app and serves it to many clients, robustly. It runs a **master** process that supervises **N worker** processes; each worker is a full, independent copy of Django in RAM handling requests.

### My real command (from the Dockerfile)
```
gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --access-logfile - \
    --error-logfile -
```
- **`config.wsgi:application`** — load the WSGI callable named `application` from `config/wsgi.py` (the "front door" — [Ch 15](15_WSGI_ASGI.md)).
- **`--bind 0.0.0.0:8000`** — listen on port 8000 on all interfaces *inside the container* (safe: the container publishes nothing; only Caddy reaches it — [Ch 05](05_IP_Address_and_Ports.md)).
- **`--workers 3`** — run 3 worker processes.
- **`--access-logfile -` / `--error-logfile -`** — `-` means **stdout/stderr**, so Docker/journald capture logs (12-factor; [Ch 31](31_Logging.md)).

### Workers — the concurrency knob
Each worker handles **one request at a time** (default **sync** worker). 3 workers = 3 requests truly concurrent. Because web work is mostly *waiting* on the DB (not CPU), a worker is often idle-waiting — which is why a slow client or slow query ties up a whole worker ([Ch 01](01_What_Is_Deployment.md)/[Ch 11](11_Reverse_Proxy.md), and why the proxy buffers slow clients).

**How many?** Rule of thumb: **`(2 × CPU cores) + 1`**. On a 1-core box → 3; 2-core → 5. But **workers cost RAM** (each ~loads all of Django). My comment says *"3 sync workers fits a 2–4 GB box."* So the count balances CPU parallelism vs RAM. Measure with `docker stats` and tune ([Ch 09](09_Processes_and_Services.md)/[Ch 41](41_Scaling.md)).

**Worker types:**
- **sync** (default, mine) — simplest, one request per worker; great for typical DB-bound Django.
- **gthread** (`--worker-class gthread --threads N`) — threads per worker, better for I/O-bound waits without more processes (less RAM than more sync workers).
- **gevent/eventlet** (async) — many concurrent connections per worker; for high-concurrency I/O. Overkill here.
- (For true async Django/websockets you'd use **Uvicorn/ASGI**, not Gunicorn sync — [Ch 15](15_WSGI_ASGI.md).)

### Timeouts
`--timeout 30` (default) — if a worker takes >30s on one request, the master **kills + respawns** it (assumes it's stuck). Too low → legit slow requests (a big report/export) get killed; too high → a genuinely hung worker stays dead-weight. Long jobs belong in a background task, not a web request ([Ch 41](41_Scaling.md)). `--graceful-timeout` governs how long a worker gets to finish on reload.

### Graceful reload (zero-drop deploys)
Sending the master **SIGHUP** reloads workers **gracefully**: it starts new workers, lets old ones finish in-flight requests, then retires them — no dropped requests. On SIGTERM (Docker stop) workers drain then exit ([Ch 09](09_Processes_and_Services.md)). Because my entrypoint `exec`s gunicorn, it's PID 1 and receives these signals directly.

### Self-healing
If a worker crashes (unhandled exception at the worker level, OOM), the **master respawns it**; other workers keep serving. Combined with Docker's `restart: unless-stopped` on the whole container, this is the resilience `runserver` lacks.

> 💡 **Samjho aise:** Gunicorn **chulhe pe kaam karne wale bawarchi** hain — ek nahi, kai (workers). Ek order (request) ek bawarchi leta hai. Bawarchi kam honge to line lagegi; bahut honge to rasoi mein jagah (RAM) khatam. Aur agar ek bawarchi gir gaya, manager turant naya khada kar deta hai — customer ko pata bhi nahi chalta.

# Real World Example (My ERP)
- Gunicorn is launched by the Dockerfile `CMD` (above), *after* `entrypoint.sh` waits for healthy DB+Redis and runs migrate + collectstatic ([Ch 27](27_Migrations.md)/[Ch 26](26_collectstatic.md)), via `exec` → gunicorn is **PID 1** ([Ch 09](09_Processes_and_Services.md)).
- **3 sync workers** = 3 concurrent requests — plenty for a factory's staff (a manager allocating + a few workers reporting + owner viewing). If the owner reports slowness under load with idle CPU, the fix is usually more workers/threads (if RAM allows) or fixing a slow query — not a bigger CPU.
- **Logs to stdout** → `docker compose logs -f app` shows gunicorn access lines (method, path, status, time) alongside my app's request-id logs ([Ch 31](31_Logging.md)).
- **Behind Caddy:** gunicorn never faces the internet; Caddy buffers slow clients so a worker is never held hostage ([Ch 11](11_Reverse_Proxy.md)).
- **Deploys:** rebuild the image + `docker compose up -d` starts a fresh `app` container; for in-place worker reloads you can SIGHUP the master.

# Visual Diagram
```
 entrypoint.sh: wait-healthy → migrate → collectstatic → exec gunicorn (becomes PID 1)

        ┌──────────── gunicorn master (config.wsgi:application, :8000) ───────────┐
        │  supervises + respawns workers · handles SIGTERM(drain) / SIGHUP(reload)│
        │   ┌─────────┐   ┌─────────┐   ┌─────────┐                               │
        │   │ worker1 │   │ worker2 │   │ worker3 │   each = full Django in RAM   │
        │   └─────────┘   └─────────┘   └─────────┘   1 request at a time (sync)  │
        └────────────────────────────────────────────────────────────────────────┘
   count ≈ (2×cores)+1, capped by RAM  |  3 fits a 2–4GB box  |  logs → stdout
   slow client? Caddy buffers it (worker stays free)  |  timeout kills stuck workers
```

# Practical — how to inspect it
```bash
docker compose exec app ps -ef | grep gunicorn    # 1 master + 3 workers (PIDs)
docker compose logs -f app                         # access + error logs (stdout)
docker stats --no-stream app                       # is app RAM near the box limit? (worker sizing)
```
```bash
# Tune (edit Dockerfile CMD or override), then rebuild:
#   --workers N            (parallel requests; RAM-bound)
#   --worker-class gthread --threads 4   (I/O concurrency, less RAM than more procs)
#   --timeout 60           (allow longer requests, e.g. big exports)
docker compose up -d --build app
```
```bash
# Graceful worker reload without a full restart (PID 1 = master):
docker compose exec app sh -c 'kill -HUP 1'        # master reloads workers, drains old ones
```
```bash
# Local smoke test (see it without Docker):
cd config && gunicorn config.wsgi:application --workers 3 --bind 127.0.0.1:8000
```

# Production Walkthrough
- `deploy/entrypoint.sh` ends with `gunicorn config.wsgi --workers 3`: a **master** process plus **3 workers**, each a full Python process with its own memory.
- A worker that crashes is replaced by the master; the request fails, the site does not.
- **3 is a considered number**, not a default: this is a small VPS, workers cost RAM, and the load is a factory's steady trickle, not a spike-driven consumer site.
- Behind Caddy, workers never talk to the internet and never serve static files — they only run Django (ch 11).

# Debugging Guide
1. **`docker compose top web`** — is the master plus 3 workers present?
2. **"WORKER TIMEOUT" in the logs** = a request exceeded the limit; find the slow view (usually N+1 or a slow query — sql_course ch 15/16), do not just raise the timeout.
3. **Workers restarting repeatedly** = memory. Check `free -h` and per-worker memory; a leak shows as steady growth.
4. **502 from Caddy** = no worker answered at all.
5. **Requests dropped on deploy** = shutdown was not graceful.

# Performance Notes
- **Worker count ≠ core count.** Web work is I/O-bound waiting; the useful range for a small box is a handful, tuned by memory and observed latency.
- Each worker holds its own DB connections; workers × pool size must stay under `max_connections` (sql_course ch 24).
- A worker recycled after N requests (`--max-requests`) papers over small leaks — useful, but find the leak.
- Threads or async help I/O-bound waits; they do not help CPU-bound work.

# Security Considerations
- Gunicorn should **not** be exposed directly; it is not hardened for the public internet (that is Caddy's job).
- Run as a non-root user inside the container.
- Timeouts are a denial-of-service control: an unbounded request can hold a worker indefinitely.
- Tracebacks must never reach the browser in production (`DEBUG=False`, ch 24).

# Architecture Decisions
- **Gunicorn + WSGI**, not ASGI, because this ERP has no websockets or long-polling; the simpler runtime is the right default (ch 15).
- **Fixed small worker count** matched to the box, revisited only with evidence.
- **Two supervision layers accepted** (Docker restarts containers, Gunicorn restarts workers) because they recover different failures at different speeds.

# Best Practices
- Tune workers from measurements, not folklore.
- Set a request timeout and treat every timeout as a bug to investigate.
- Ensure graceful shutdown so deploys are invisible to users.
- Keep worker count × DB connections comfortably under the database limit.

# Beginner Mistakes
- **Too many workers → OOM.** Each worker holds all of Django; `50 workers` on a 2 GB box gets OOM-killed ([Ch 09](09_Processes_and_Services.md)). Size by RAM, verify with `docker stats`.
- **Too few workers under load → slow.** One long/slow request blocks its worker; if all are busy, everyone waits. Add workers/threads or fix the slow path.
- **Long jobs in a web request** (giant report/export) → timeout kills the worker mid-work. Raise `--timeout` for that path or move it to a background job.
- **`--bind 127.0.0.1` inside the container** → Caddy (a different container) can't reach it. Must be `0.0.0.0:8000` so the proxy can connect over the docker net.
- **Logging to a file instead of stdout** → logs trapped in the container, lost on rebuild. Use `-` (stdout).
- **Expecting a bigger CPU to fix "slow with idle CPU"** — it's usually worker/wait-bound or a slow query, not CPU.

# Interview Questions
- **Junior:** "What is a Gunicorn worker?" — A separate process running a full copy of the Django app; N workers let the server handle N requests concurrently, and the master respawns any that crash.

- **Mid:** "How many workers, and what's the trade-off?" — Start at ~`(2×cores)+1`, but it's capped by RAM since each worker loads the whole app. More workers = more concurrency but more memory; too many → OOM. Measure real RAM and tune.

- **Senior:** "Requests hang under moderate load though CPU is ~10%. Diagnose." — Workers are blocked waiting (slow DB queries, slow external calls, or slow clients holding sync workers). Options: put a buffering proxy in front (done — Caddy), add workers/threads for I/O concurrency, and profile+fix the slow queries; a bigger CPU won't help a wait-bound bottleneck.

- **Staff:** "Design Gunicorn config + deploy for zero-downtime and safe long operations on this ERP." — Sync (or gthread for I/O) workers sized to RAM (`docker stats`-verified), sensible `--timeout` with genuinely long jobs pushed to a background worker (not the request path); logs to stdout; graceful handling via `exec` (PID 1) so SIGTERM drains and SIGHUP reloads; for deploys, build the new image and start a new container while Caddy keeps serving, or SIGHUP for in-place worker refresh — no dropped requests. Alert on worker restarts + p95 latency ([Ch 30](30_Monitoring.md)).

### Why interviewers ask these — and the answer that separates levels

| Testing for | Weak answer | What lands |
|---|---|---|
| Worker count — do you know the real cap? | "Use (2 × cores) + 1." | That is the **starting point**; the real cap is **RAM**, because each worker loads a full copy of the app. Too many → **OOM kills**. And each worker holds DB connections, so the ceiling is also `max_connections` (ch 21). **Measure with `docker stats`**, do not compute and walk away. |
| Hangs at 10% CPU — can you interpret that? | "The server needs more workers." | Idle CPU with hanging requests means workers are **blocked waiting** — slow DB queries, slow external calls, or slow clients holding sync workers. Web concurrency is mostly about **waiting**, not computing, which is why **worker count ≠ core count**. |
| Do you know what the master process is for? | "Gunicorn runs the app." | The **master supervises and respawns dead workers** while the rest keep serving — so one crashed request does not take the site down. Docker's restart policy is the *outer* layer, for when the master itself dies (ch 09). |
| Where do long jobs belong? | "Raise the timeout." | **Out of the request path entirely.** Raising `--timeout` keeps a worker hostage and pushes the failure to the proxy as a 504. A genuinely long job belongs in a background worker; the timeout should stay tight enough to expose bugs. |

**The killer follow-up:** *"You have 3 workers and 3 threads each. How many database connections can you demand, and does Postgres allow it?"* — do the multiplication out loud and check it against `max_connections` (ch 21). Scaling workers has a **database cost**, and the people who forget that take the database down while trying to serve more traffic.

# Revision Notes
- Gunicorn = the WSGI **application server**: master + N worker processes.
- A worker crash is recovered; the site stays up.
- **Worker count ≠ cores** — web work is waiting; RAM is the real limit.
- "WORKER TIMEOUT" = a slow view; fix the view, not the timeout.
- Never expose Gunicorn to the internet; Caddy fronts it.

# Cheat Sheet
- **Gunicorn = production WSGI server:** master + N workers, self-healing, behind Caddy.
- **My CMD:** `gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3 --access-logfile - --error-logfile -`.
- **Workers:** ~`(2×cores)+1`, **capped by RAM** (each = full Django). Mine = 3 for a 2–4 GB box. sync default; gthread for I/O.
- **Timeout** kills stuck workers; long jobs → background, not the request.
- **Signals:** SIGTERM drain, SIGHUP graceful reload (master = PID 1 via `exec`).
- **Logs → stdout (`-`).** Bind `0.0.0.0:8000` (proxy reaches it). Slow clients handled by Caddy.
- Inspect: `ps -ef|grep gunicorn`, `docker compose logs app`, `docker stats`.

# My ERP Section
| Concept | In my ERP |
|---|---|
| Launch | Dockerfile `CMD` (after entrypoint migrate/collectstatic) |
| App callable | `config.wsgi:application` ([Ch 15](15_WSGI_ASGI.md)) |
| Workers | 3 sync (fits 2–4 GB box) |
| Bind | `0.0.0.0:8000`, private (Caddy → `app:8000`) |
| Logs | access+error → stdout → `docker compose logs app` |
| PID 1 / signals | `exec gunicorn` → graceful SIGTERM/SIGHUP |
| Restart | gunicorn respawns workers · Docker respawns container |

# Practice Tasks
1. **Read the code:** find the gunicorn line in `deploy/entrypoint.sh`. Explain every flag.
2. **Debug:** run gunicorn locally with 1 worker and load two slow pages at once. Observe queuing; then try 3 workers.
3. **Design:** the box has 2 GB RAM and each worker uses ~180 MB. Choose a worker count and justify it, including DB connections.
4. **Architecture:** argue whether to add `--max-requests`. What does it hide, and when is hiding acceptable?

# Homework
1. `docker compose exec app ps -ef | grep gunicorn` — identify the master + 3 workers.
2. `docker stats --no-stream app` — note RAM. Estimate how many workers your box could hold before OOM.
3. Explain why `--bind 0.0.0.0:8000` (not `127.0.0.1`) is required *inside the container* but still not internet-exposed.
4. Which flag would you change to let a 45-second export finish, and what's the *better* long-term fix?
5. Explain what SIGHUP to the gunicorn master does and why `exec` in the entrypoint makes it work.

---

# Further Reading & Live Resources
- Gunicorn — *official docs* (settings, worker types, signals): https://docs.gunicorn.org/en/stable/
- Gunicorn — *Design* (workers, how it works): https://docs.gunicorn.org/en/stable/design.html
- Gunicorn — *How many workers?* (the `(2×cores)+1` guidance): https://docs.gunicorn.org/en/stable/design.html#how-many-workers
- Django docs — *Gunicorn deployment*: https://docs.djangoproject.com/en/5.0/howto/deployment/wsgi/gunicorn/
- DigitalOcean — *Gunicorn + Django* tuning notes: https://www.digitalocean.com/community/tutorials/how-to-set-up-django-with-postgres-nginx-and-gunicorn-on-ubuntu-22-04
