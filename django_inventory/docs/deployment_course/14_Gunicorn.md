# 14 — Gunicorn (my app server, real config)

> Part of [Deployment Course](00_COURSE_OVERVIEW.md). Prev: [13 — Nginx Comparison](13_Nginx_Comparison.md). Next: [15 — WSGI & ASGI](15_WSGI_ASGI.md).

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

# Beginner Mistakes
- **Too many workers → OOM.** Each worker holds all of Django; `50 workers` on a 2 GB box gets OOM-killed ([Ch 09](09_Processes_and_Services.md)). Size by RAM, verify with `docker stats`.
- **Too few workers under load → slow.** One long/slow request blocks its worker; if all are busy, everyone waits. Add workers/threads or fix the slow path.
- **Long jobs in a web request** (giant report/export) → timeout kills the worker mid-work. Raise `--timeout` for that path or move it to a background job.
- **`--bind 127.0.0.1` inside the container** → Caddy (a different container) can't reach it. Must be `0.0.0.0:8000` so the proxy can connect over the docker net.
- **Logging to a file instead of stdout** → logs trapped in the container, lost on rebuild. Use `-` (stdout).
- **Expecting a bigger CPU to fix "slow with idle CPU"** — it's usually worker/wait-bound or a slow query, not CPU.

# Interview Questions
**Junior — "What is a Gunicorn worker?"** A separate process running a full copy of the Django app; N workers let the server handle N requests concurrently, and the master respawns any that crash.

**Mid — "How many workers, and what's the trade-off?"** Start at ~`(2×cores)+1`, but it's capped by RAM since each worker loads the whole app. More workers = more concurrency but more memory; too many → OOM. Measure real RAM and tune.

**Senior — "Requests hang under moderate load though CPU is ~10%. Diagnose."** Workers are blocked waiting (slow DB queries, slow external calls, or slow clients holding sync workers). Options: put a buffering proxy in front (done — Caddy), add workers/threads for I/O concurrency, and profile+fix the slow queries; a bigger CPU won't help a wait-bound bottleneck.

**Staff — "Design Gunicorn config + deploy for zero-downtime and safe long operations on this ERP."** Sync (or gthread for I/O) workers sized to RAM (`docker stats`-verified), sensible `--timeout` with genuinely long jobs pushed to a background worker (not the request path); logs to stdout; graceful handling via `exec` (PID 1) so SIGTERM drains and SIGHUP reloads; for deploys, build the new image and start a new container while Caddy keeps serving, or SIGHUP for in-place worker refresh — no dropped requests. Alert on worker restarts + p95 latency ([Ch 30](30_Monitoring.md)).

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

# Homework
1. `docker compose exec app ps -ef | grep gunicorn` — identify the master + 3 workers.
2. `docker stats --no-stream app` — note RAM. Estimate how many workers your box could hold before OOM.
3. Explain why `--bind 0.0.0.0:8000` (not `127.0.0.1`) is required *inside the container* but still not internet-exposed.
4. Which flag would you change to let a 45-second export finish, and what's the *better* long-term fix?
5. Explain what SIGHUP to the gunicorn master does and why `exec` in the entrypoint makes it work.

---

## Further Reading & Live Resources
- Gunicorn — *official docs* (settings, worker types, signals): https://docs.gunicorn.org/en/stable/
- Gunicorn — *Design* (workers, how it works): https://docs.gunicorn.org/en/stable/design.html
- Gunicorn — *How many workers?* (the `(2×cores)+1` guidance): https://docs.gunicorn.org/en/stable/design.html#how-many-workers
- Django docs — *Gunicorn deployment*: https://docs.djangoproject.com/en/5.0/howto/deployment/wsgi/gunicorn/
- DigitalOcean — *Gunicorn + Django* tuning notes: https://www.digitalocean.com/community/tutorials/how-to-set-up-django-with-postgres-nginx-and-gunicorn-on-ubuntu-22-04
