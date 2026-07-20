# 09 — Processes & Services

> Part of [Deployment From Zero](00_COURSE_OVERVIEW.md). Prev: [08 — The File System](08_File_System.md). Next: [10 — systemd](10_Systemd.md).

# Purpose
To understand what a "running program" actually is on the server — a **process** — how to see them, how they use CPU/RAM, and how a long-running **service** (like Gunicorn or Postgres) differs from a command you run once. This is the vocabulary for "the app is using 100% CPU", "kill the stuck process", and "the container keeps restarting".

# The Problem
When the ERP is "up", *something* is running and listening. When it's "down", that something died or hung. I can't diagnose either without being able to list processes, see their resource use, and stop/inspect them. And I need to know why a server program must run **forever** (and auto-restart), unlike a script that runs and exits.

# Theory (from zero)

### A process = a running program
Every running program is a **process** with a **PID** (process id), an **owner** (which user), a parent, and its own memory. `python manage.py migrate` is a process that runs and **exits**. `gunicorn …` is a process that **stays running**, listening for requests — a **long-running service (daemon)**.

### Foreground vs background; parent/child
A command in your terminal runs in the **foreground** (you wait for it). A service must run in the **background**, detached from your session, so it survives logout. Gunicorn spawns **child** worker processes (3 of them here) — a parent "master" managing 3 workers; kill a worker and the master respawns it.

### Signals — how you talk to a process
You control processes with **signals**: `SIGTERM` (15) = "please shut down cleanly" (finish current request, then exit — a **graceful** stop); `SIGKILL` (9) = "die now" (forced, no cleanup — last resort); `SIGHUP` (1) = often "reload config". Good software traps SIGTERM to drain in-flight work. Docker sends SIGTERM on `stop`, then SIGKILL after a timeout.

### Exit codes
When a process exits it returns a code: **0 = success**, non-zero = failure. Docker/entrypoints use this: my `entrypoint.sh` does `set -e` (exit on first error) and `sys.exit("FATAL…")` if the DB/Redis never come up — a non-zero exit so the container is marked failed rather than booting half-configured.

### Why services auto-restart
A server program can crash (bug, OOM, transient error). Production must bring it back automatically. Two layers do this: **Docker's `restart: unless-stopped`** (restarts a crashed container) and, inside Gunicorn, the **master respawning dead workers**. Without auto-restart, one crash at 3am = downtime till morning. (On a non-Docker host, **systemd** plays the restart role — [Ch 10](10_Systemd.md).)

### Resource use
Each process consumes **CPU** (compute) and **RAM** (memory). Gunicorn workers each hold a full copy of Django in RAM — that's why worker count is bounded by RAM ([Ch 14](14_Gunicorn.md)). The **OOM killer**: if the box runs out of RAM, Linux kills the biggest process (often your DB or a worker) to survive — a nasty, silent outage cause.

# Real World Example (My ERP)
- **Long-running services** (containers with `restart: unless-stopped`): `caddy`, `app` (gunicorn master + **3 workers**), `db` (postgres), `redis`, `backup` (a sleep-loop that wakes at 02:00). Each is a process (or process tree) inside its container.
- **Run-once processes** (exit when done): `migrate` and `collectstatic` in `entrypoint.sh` — they run, exit 0, then `exec` hands the container over to the long-running gunicorn.
- **`exec "$@"`** in the entrypoint replaces the shell with gunicorn so gunicorn becomes **PID 1** in the container and receives Docker's SIGTERM directly → clean shutdown (drains requests). Without `exec`, signals would hit the shell, not gunicorn.
- **Auto-restart proof:** kill a gunicorn worker → the master respawns it (site unaffected); kill the whole `app` container → Docker restarts it (`unless-stopped`).
- **Health-gated start:** the entrypoint's wait-loop is a process that blocks until `db`+`redis` answer, then exits 0 — so gunicorn never starts against a dead DB.

# Visual Diagram
```
 CONTAINER: app                         signals:  SIGTERM=graceful  SIGKILL=force
   PID 1  gunicorn master  ◄── Docker stop sends SIGTERM here (via exec)
     ├── worker 1  (Django copy in RAM)   crash? → master respawns
     ├── worker 2
     └── worker 3

 lifecycle in entrypoint.sh:
   [wait db+redis healthy]  → exit 0 →  migrate → exit 0 → collectstatic → exit 0
                                                        → exec gunicorn (stays forever)

 restart layers:  Gunicorn respawns dead WORKERS  |  Docker restarts dead CONTAINERS
 danger: RAM exhausted → Linux OOM-killer kills biggest process (DB/worker) → outage
```

# Practical — how to inspect it
```bash
# Host: live process/resource view
top                 # or: htop (nicer) — CPU%/RAM% per process, q to quit
ps aux | grep gunicorn   # find gunicorn master + workers, their PIDs + RAM
```
```bash
# Per-container resource use (the one you'll use most)
docker stats --no-stream    # CPU/RAM per container — is app/db hot? near RAM limit?
```
```bash
# Inside a container: what's running as PID 1?
docker compose exec app ps -ef      # expect gunicorn master + 3 workers
```
```bash
# Signals / stopping
docker compose stop app     # sends SIGTERM (graceful), then SIGKILL after ~10s
kill -TERM <pid>            # graceful stop a host process
kill -9 <pid>              # SIGKILL — last resort, no cleanup
```
```bash
# Did a container die/restart? why?
docker compose ps          # STATE: running / restarting / exited(code)
docker compose logs --tail 50 app   # last output before it died
dmesg | grep -i oom        # was the OOM killer invoked? (RAM exhaustion)
```

# Beginner Mistakes
- **`kill -9` as the default.** SIGKILL skips cleanup — half-finished writes, no graceful drain. Try SIGTERM first; reserve `-9` for truly stuck processes.
- **Running the server in the foreground over SSH** (`gunicorn …` in your terminal) — it dies when you log out. Services must run detached (Docker/systemd do this).
- **Ignoring `restart:` policy.** Without `unless-stopped`, a crash stays down. (But beware a **crash-loop**: a mis-set restart on a program that instantly fails just spins — read the logs.)
- **Forgetting `exec` in an entrypoint.** Signals hit the shell, not the app → containers take the full 10s SIGKILL timeout to stop, dropping in-flight requests.
- **Under-provisioned RAM → OOM kills.** Silent, brutal. Right-size ([Ch 14](14_Gunicorn.md)/[00B](00B_Deployment_Costs_And_Free_Alternatives.md)) and watch `docker stats`.

# Interview Questions
**Junior — "What's a process? What's a PID?"** A running instance of a program with its own memory; the PID is its unique id the OS uses to reference/signal it.

**Junior — "Difference between SIGTERM and SIGKILL?"** SIGTERM asks the process to shut down cleanly (it can finish work + release resources); SIGKILL forcibly terminates it immediately with no cleanup.

**Mid — "How does the site stay up if a Gunicorn worker crashes?"** The Gunicorn master process supervises workers and respawns any that die; the other workers keep serving meanwhile. If the whole container dies, Docker's restart policy brings it back.

**Senior — "Container shows STATE=restarting in a loop. How do you debug?"** It's crash-looping: the process exits non-zero on start and Docker keeps restarting it. Read `docker compose logs` for the startup error (bad env var, DB unreachable, migration failure, port conflict). Fix the root cause; the restart policy is doing its job — the app is the problem.

**Staff — "Design graceful shutdown for zero dropped requests during a deploy."** App must trap SIGTERM and drain: stop accepting new connections, finish in-flight requests within a grace window, then exit 0. Ensure the app is PID 1 (via `exec`) so it *receives* Docker's SIGTERM; set Docker's stop grace period ≥ the longest reasonable request; put a proxy (Caddy) in front so it can retry/queue during the brief swap; for true zero-downtime, start the new container and shift traffic before stopping the old ([Ch 33](33_CI_CD.md)). Gunicorn's graceful worker handling covers the app side.

# Cheat Sheet
- **Process** = running program (PID, owner, RAM). **Service/daemon** = long-running process (gunicorn, postgres). Run-once (migrate) exits.
- **Signals:** SIGTERM (15, graceful) → SIGKILL (9, force, last resort). Docker: stop = TERM then KILL.
- **Auto-restart layers:** Gunicorn respawns workers · Docker `restart: unless-stopped` respawns containers.
- **`exec "$@"`** → app becomes PID 1 → receives signals → clean shutdown.
- **Inspect:** `docker stats`, `docker compose ps`, `docker compose logs`, `ps aux`, `top/htop`, `dmesg|grep oom`.
- **RAM out → OOM killer** murders the biggest process. Right-size + monitor.

# My ERP Section
| Concept | In my ERP |
|---|---|
| Long-running services | caddy, app(gunicorn+3 workers), db, redis, backup |
| Run-once processes | `migrate`, `collectstatic` (entrypoint), then `exec gunicorn` |
| PID 1 / signals | `exec "$@"` → gunicorn is PID 1 → graceful SIGTERM |
| Container restart | `restart: unless-stopped` on every service |
| Worker respawn | gunicorn master (3 workers) |
| Health gate | entrypoint wait-loop blocks until db+redis ready |
| OOM risk | 3 workers × Django RAM — size the box (2–4 GB) |

# Homework
1. `docker stats --no-stream` (once the stack runs) — note each container's RAM. Which is largest? How close to the box's limit?
2. `docker compose exec app ps -ef` — identify the gunicorn master and its 3 workers by PID.
3. Kill one worker (`docker compose exec app kill <worker-pid>`) and watch (`ps -ef` again) the master respawn it. Site stayed up?
4. `docker compose stop app` then `start` — read the entrypoint logs: wait-loop → migrate → collectstatic → gunicorn. Match each to a process.
5. Explain why `exec gunicorn` (vs just `gunicorn`) matters for clean shutdown during a deploy.

---

## Further Reading & Live Resources
- DigitalOcean — *Process management in Linux* / `ps`, `kill`, signals: https://www.digitalocean.com/community/tutorials/how-to-use-ps-kill-and-nice-to-manage-processes-in-linux
- Julia Evans — *signals* (zine/posts, very clear): https://jvns.ca/blog/2015/04/23/what-happens-when-you-press-ctrl-c/
- Docker docs — *start containers automatically / restart policies*: https://docs.docker.com/config/containers/start-containers-automatically/
- Gunicorn — *signal handling*: https://docs.gunicorn.org/en/stable/signals.html
- `man 7 signal` (the signal list): https://man7.org/linux/man-pages/man7/signal.7.html
- Linux OOM killer explained: https://www.kernel.org/doc/gorman/html/understand/understand016.html
