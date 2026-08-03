---
id: deploy-course-09-processes-and-services
type: lesson
status: active
owner: handwritten
scope: deployment, operations — this ERP shipped to a VPS
anchors: docker-compose.yml, deploy/entrypoint.sh, deploy/Caddyfile, deploy/backup.sh
verified: 2026-08-01
---

# 09 — Processes & Services

> Part of [Deployment From Zero](00_COURSE_OVERVIEW.md). Prev: [08 — The File System](08_File_System.md). Next: [10 — systemd](10_Systemd.md).

# Learning Objectives
By the end of this chapter you can:
- tell a process from a service, and say why production needs the second
- list what is running and kill the right thing
- explain what happens to your app when you close the terminal
- name who restarts this project's containers, and when

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

> 💡 **Samjho aise:** Process ek **chalta hua kaam** hai (aapka app), service wo kaam jo **apne aap shuru hota hai** aur girne pe khud khada ho jaata hai. Terminal se chalaya app aapke logout pe mar jaata hai; service reboot ke baad bhi zinda milti hai. Production ko doosri cheez chahiye.

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

# Production Walkthrough
- Nothing here is started by hand. **Docker is the supervisor**: `restart: unless-stopped` means a crashed container comes back, and everything starts again after a reboot.
- Inside the web container, **Gunicorn is itself a supervisor**: a master process plus 3 workers. A worker that dies is replaced without dropping the site.
- So there are two layers of "keep it running", and knowing which one acted explains most restart mysteries: a *worker* restart is invisible; a *container* restart shows in `docker compose ps` as a recent start time.

# Debugging Guide
1. **`docker compose ps`** — look at STATUS and uptime. A container that restarted 30 seconds ago is your lead.
2. **Restart loop?** `logs --tail=100` shows the same fatal error repeating — usually config (`.env`) or a failed migration.
3. **`docker compose top web`** — is Gunicorn's master plus 3 workers actually there?
4. **Killed with no error?** Suspect the OOM killer: `free -h`, then `dmesg | tail`.
5. **Ran fine manually but dies as a service?** Different environment — services do not inherit your shell's variables.

# Performance Notes
- Each Gunicorn worker is a separate process with its own memory; worker count is bounded by RAM, not ambition.
- Restarts are not free: in-flight requests are lost unless the shutdown is graceful (Gunicorn drains on `SIGTERM`).
- A restart loop burns CPU and fills logs — fix the cause rather than raising the retry limit.

# Security Considerations
- Processes should run as a **non-root user inside the container**; a container escape is far less useful without root.
- A service that restarts forever on a config error can leak the same secret into logs repeatedly — check what your fatal errors print.
- Only Docker should manage lifecycle; ad-hoc `nohup` processes are invisible to monitoring and survive nothing.

# Architecture Decisions
- **Docker restart policies instead of hand-written systemd units per service** — one supervision mechanism for all five containers (ch 10 covers the case where systemd is the right answer).
- **Gunicorn's own worker supervision** kept, because it recovers from application-level crashes faster than a container restart.
- **Fail fast on missing dependencies** (Redis/DB) rather than starting degraded — the entrypoint waits for health first.

# Best Practices
- Never run production processes from an interactive shell.
- Read STATUS and uptime before reading logs; it tells you *what* happened.
- Make shutdown graceful so deploys do not drop requests.
- Keep the restart policy explicit in compose, not implied.

# Beginner Mistakes
- **`kill -9` as the default.** SIGKILL skips cleanup — half-finished writes, no graceful drain. Try SIGTERM first; reserve `-9` for truly stuck processes.
- **Running the server in the foreground over SSH** (`gunicorn …` in your terminal) — it dies when you log out. Services must run detached (Docker/systemd do this).
- **Ignoring `restart:` policy.** Without `unless-stopped`, a crash stays down. (But beware a **crash-loop**: a mis-set restart on a program that instantly fails just spins — read the logs.)
- **Forgetting `exec` in an entrypoint.** Signals hit the shell, not the app → containers take the full 10s SIGKILL timeout to stop, dropping in-flight requests.
- **Under-provisioned RAM → OOM kills.** Silent, brutal. Right-size ([Ch 14](14_Gunicorn.md)/[00B](00B_Deployment_Costs_And_Free_Alternatives.md)) and watch `docker stats`.

# Interview Questions
- **Junior:** "What's a process? What's a PID?" — A running instance of a program with its own memory; the PID is its unique id the OS uses to reference/signal it.

- **Junior:** "Difference between SIGTERM and SIGKILL?" — SIGTERM asks the process to shut down cleanly (it can finish work + release resources); SIGKILL forcibly terminates it immediately with no cleanup.

- **Mid:** "How does the site stay up if a Gunicorn worker crashes?" — The Gunicorn master process supervises workers and respawns any that die; the other workers keep serving meanwhile. If the whole container dies, Docker's restart policy brings it back.

- **Senior:** "Container shows STATE=restarting in a loop. How do you debug?" — It's crash-looping: the process exits non-zero on start and Docker keeps restarting it. Read `docker compose logs` for the startup error (bad env var, DB unreachable, migration failure, port conflict). Fix the root cause; the restart policy is doing its job — the app is the problem.

- **Staff:** "Design graceful shutdown for zero dropped requests during a deploy." — App must trap SIGTERM and drain: stop accepting new connections, finish in-flight requests within a grace window, then exit 0. Ensure the app is PID 1 (via `exec`) so it *receives* Docker's SIGTERM; set Docker's stop grace period ≥ the longest reasonable request; put a proxy (Caddy) in front so it can retry/queue during the brief swap; for true zero-downtime, start the new container and shift traffic before stopping the old ([Ch 33](33_CI_CD.md)). Gunicorn's graceful worker handling covers the app side.

### Why interviewers ask these — and the answer that separates levels

| Testing for | Weak answer | What lands |
|---|---|---|
| SIGTERM vs SIGKILL — do you know which one you should ever send? | "Both stop the process, KILL is stronger." | **SIGTERM asks** — the process can finish in-flight work and release resources. **SIGKILL cannot be caught** and skips all cleanup. Reaching for `-9` first is how you truncate a request mid-write. |
| Do you know what actually keeps the site up? | "Docker restarts it if it crashes." | **Two layers**: the **Gunicorn master respawns dead workers** while the others keep serving, and Docker's **restart policy** covers the whole container dying. Naming both shows you know where a single worker crash stops. |
| Crash-looping container — can you resist restarting it again? | "I will restart it and see." | A restart loop means the process **exits non-zero at startup** and the policy keeps retrying — so restarting changes nothing. **Read `docker compose logs`** for the startup error: bad env var, DB unreachable, migration failure, port conflict. |
| Do you know why PID 1 matters? | "The app just needs to run." | Your app must **be PID 1** (start it with `exec`) or it **never receives Docker's SIGTERM** — the shell swallows it, nothing drains, and every deploy kills in-flight requests after the grace period. A one-word `exec` is the whole fix. |

**The killer follow-up:** *"Design graceful shutdown with zero dropped requests during a deploy."* — trap **SIGTERM** → stop accepting new connections → **finish in-flight requests within a grace window** → exit 0; be **PID 1** so the signal arrives; set Docker's stop grace period **longer than your slowest request**. Candidates who skip the PID-1 half have never actually watched a deploy drop traffic.

# Revision Notes
- Process = a running program. Service = a process that **starts itself and recovers**.
- Terminal-started apps die at logout; production needs supervision.
- Here: **Docker supervises containers**; **Gunicorn supervises workers**.
- `docker compose ps` → STATUS + uptime tells you what restarted.
- Restart loop = the same fatal error repeating; read the logs, do not raise retries.

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

# Practice Tasks
1. **Read the code:** find the `restart:` policy in `docker-compose.yml`. What exactly does its value promise?
2. **Debug:** run `docker compose top web` (or locally, `ps aux | grep gunicorn`). Identify master vs workers.
3. **Design:** describe what should happen, step by step, if the app crashes at 3am — and who is notified (ch 30).
4. **Architecture:** argue when a systemd unit would be better than a Docker restart policy.

# Homework
1. `docker stats --no-stream` (once the stack runs) — note each container's RAM. Which is largest? How close to the box's limit?
2. `docker compose exec app ps -ef` — identify the gunicorn master and its 3 workers by PID.
3. Kill one worker (`docker compose exec app kill <worker-pid>`) and watch (`ps -ef` again) the master respawn it. Site stayed up?
4. `docker compose stop app` then `start` — read the entrypoint logs: wait-loop → migrate → collectstatic → gunicorn. Match each to a process.
5. Explain why `exec gunicorn` (vs just `gunicorn`) matters for clean shutdown during a deploy.

---

# Further Reading & Live Resources
- DigitalOcean — *Process management in Linux* / `ps`, `kill`, signals: https://www.digitalocean.com/community/tutorials/how-to-use-ps-kill-and-nice-to-manage-processes-in-linux
- Julia Evans — *signals* (zine/posts, very clear): https://jvns.ca/blog/2015/04/23/what-happens-when-you-press-ctrl-c/
- Docker docs — *start containers automatically / restart policies*: https://docs.docker.com/config/containers/start-containers-automatically/
- Gunicorn — *signal handling*: https://docs.gunicorn.org/en/stable/signals.html
- `man 7 signal` (the signal list): https://man7.org/linux/man-pages/man7/signal.7.html
- Linux OOM killer explained: https://www.kernel.org/doc/gorman/html/understand/understand016.html
