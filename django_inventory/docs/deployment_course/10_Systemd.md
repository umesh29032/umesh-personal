# 10 — systemd

> Part of [Deployment From Zero](00_COURSE_OVERVIEW.md). Prev: [09 — Processes & Services](09_Processes_and_Services.md). Next: [11 — Reverse Proxy](11_Reverse_Proxy.md). *(Completes Term 2.)*

# Purpose
To understand the thing that starts and supervises long-running programs on a Linux server — **systemd** — because *something* must launch Docker (and your whole stack) automatically when the VPS boots or reboots, restart it if it dies, and give you one place to read its logs.

# The Problem
[Ch 09](09_Processes_and_Services.md) said services must run in the background forever and auto-restart. But *who* starts them at boot? If the VPS reboots at 4am (kernel update, power blip), someone must bring everything back with no human. On Linux that "someone" is **systemd** — the init system (PID 1 on the host) that manages services. Even in a Dockerized stack, systemd is what starts **Docker itself**, which then starts your containers.

# Theory (from zero)

### What systemd is
**systemd** is the first process the Linux kernel starts (host **PID 1**), and the manager of all **services**. It starts things in the right order at boot, restarts crashed services, tracks their state, and collects their logs. On Ubuntu it's the default.

### Units
systemd manages **units** — mostly **service units** (`something.service`) describing how to run a program: the command, the user, restart policy, dependencies. Examples on your VPS: `ssh.service`, `docker.service`. You control them with `systemctl`:
- `systemctl status docker` — is it running? recent logs?
- `systemctl start/stop/restart docker`
- `systemctl enable docker` — **start automatically on every boot** (the crucial one).
- `systemctl disable docker` — don't auto-start.

### `enable` vs `start` (the classic confusion)
- **`start`** = run it *now* (this boot).
- **`enable`** = run it *on every future boot*.
You almost always want **both**: `systemctl enable --now docker` = start now + on every boot.

### journald / journalctl — one log for everything
systemd captures each service's stdout/stderr into the **journal**, read with `journalctl`:
- `journalctl -u docker` — logs for the docker service.
- `journalctl -u ssh -f` — follow SSH logs live.
- `journalctl -b` — logs since last boot.
Unified, timestamped, filterable — no hunting through scattered log files.

### systemd vs Docker (who supervises what in MY stack)
Two valid models:
1. **Non-Docker deploy:** you'd write a `gunicorn.service` unit; systemd runs Gunicorn directly, restarts it, logs it. (Common in tutorials that skip Docker.)
2. **My Docker deploy:** **systemd's job shrinks to "start `docker.service` on boot"**; then **Docker** (via `restart: unless-stopped` in `docker-compose.yml`) supervises the individual containers ([Ch 09](09_Processes_and_Services.md)). So I don't hand-write unit files per app service — Docker does per-container supervision, systemd just guarantees Docker is up.
   - *Optional polish:* a tiny `docker-compose@erp.service` unit can run `docker compose up -d` at boot so the stack comes back after a reboot even if you never logged in. Otherwise, `restart: unless-stopped` + `docker.service` being enabled already brings containers back on reboot.

# Real World Example (My ERP)
- On the VPS, **`systemctl enable --now docker`** guarantees the Docker daemon starts on boot. That's the main systemd action I take.
- After a reboot: systemd starts `docker.service` → Docker sees containers with `restart: unless-stopped` and brings **caddy, app, db, redis, backup** back automatically — the site self-heals without me.
- I read daemon-level issues with `journalctl -u docker` (e.g. "why didn't Docker start?"), and **app-level** logs with `docker compose logs` ([Ch 31](31_Logging.md)) — two different log planes: journald for the host/daemon, Docker logs for the containers.
- SSH itself is a systemd service (`ssh.service`); hardening it ([Ch 07](07_SSH.md)) ends with `systemctl restart ssh`.
- I do **not** hand-write a gunicorn unit — the Dockerfile's `CMD` + compose `restart:` policy replace that.

# Visual Diagram
```
 BOOT
  kernel → systemd (host PID 1)
             │ enabled units start in dependency order
             ├── ssh.service            (you can log in)
             └── docker.service ★        (the daemon)
                     │  Docker reads docker-compose (restart: unless-stopped)
                     ├── caddy   ├── app(gunicorn) ├── db ├── redis ├── backup
                     └────────── all containers back up, no human ───────────

 logs:  journalctl -u docker   (host/daemon)      docker compose logs app  (container)
 commands:  systemctl {status|start|stop|restart|enable|disable} <unit>
 enable = on every boot   |   start = now   |   enable --now = both
```

# Practical — how to inspect it
```bash
systemctl status docker        # running? enabled? recent log lines
systemctl is-enabled docker    # "enabled" = will start on boot (want this)
sudo systemctl enable --now docker   # start now + every boot
```
```bash
systemctl status ssh           # your login service
sudo systemctl restart ssh     # after editing sshd_config (Ch07)
```
```bash
journalctl -u docker --no-pager | tail -50   # docker daemon logs
journalctl -u ssh -f                          # follow auth/ssh logs live
journalctl -b -p err                          # errors since last boot
systemctl list-units --type=service --state=running   # what's running
```
```bash
# Prove reboot-resilience (on a test VPS): reboot, then after it's back:
docker compose ps    # were containers restarted automatically? (should be "Up")
```

# Beginner Mistakes
- **`start` without `enable`.** Works until the first reboot, then the service is dead and "the site randomly went down after a reboot." Use `enable --now`.
- **Hand-writing unit files when using Docker.** Redundant — Docker's restart policy supervises containers. Just enable `docker.service`.
- **Looking in the wrong log plane.** Container app errors are in `docker compose logs`, not `journalctl` (which shows the *daemon*). Know which plane.
- **Editing a unit and forgetting `daemon-reload`.** After changing a `.service` file: `sudo systemctl daemon-reload` then restart, or your edits are ignored.
- **Assuming reboot brings the app back with no config.** It does *only if* `docker.service` is enabled AND containers have a restart policy (yours do). Verify with a test reboot.

# Interview Questions
**Junior — "Difference between `systemctl start` and `systemctl enable`?"** `start` runs the service now; `enable` makes it start automatically on every boot. `enable --now` does both.

**Mid — "In a Dockerized deployment, what does systemd actually manage vs Docker?"** systemd manages the host and the Docker daemon (`docker.service`) — ensuring Docker starts on boot; Docker then manages the individual containers via their restart policies. You typically don't write per-app systemd units.

**Senior — "After a VPS reboot the site is down. Walk your checks."** `systemctl status docker` (did the daemon start? is it enabled?), then `docker compose ps` (are containers up/restarting/exited?), then `journalctl -u docker` for daemon errors and `docker compose logs` for app errors. Common root causes: `docker.service` not enabled, a volume/mount issue, or an env var only present in a shell that didn't run at boot.

**Staff — "Guarantee the full stack returns after any reboot, unattended, and is observable."** Enable `docker.service`; give every container `restart: unless-stopped` (done); optionally add a systemd unit that runs `docker compose up -d` in the project dir at boot (belt-and-suspenders if compose isn't started by the daemon alone); ship container logs to stdout (done) so `docker compose logs`/journald capture them; add an external uptime check ([Ch 30](30_Monitoring.md)) so you *know* within a minute if the reboot didn't fully recover. Test by actually rebooting a staging box.

# Cheat Sheet
- **systemd** = host PID 1 + service manager; starts/supervises/logs services at boot.
- **`systemctl status|start|stop|restart|enable|disable <unit>`.** `enable --now` = now + every boot.
- **`journalctl -u <unit>`** = that service's logs (host/daemon plane).
- **My stack:** enable `docker.service`; Docker's `restart: unless-stopped` supervises containers. Don't hand-write app units.
- After editing a unit: `systemctl daemon-reload`.
- Two log planes: **journald** (daemon/host) vs **docker logs** (containers).

# My ERP Section
| Concept | In my ERP |
|---|---|
| What systemd manages | the host + `docker.service` (enable on boot) |
| What Docker manages | the containers (via `restart: unless-stopped`) |
| Reboot recovery | enabled docker + restart policy → stack self-heals |
| Daemon logs | `journalctl -u docker` |
| App/container logs | `docker compose logs <svc>` ([Ch 31](31_Logging.md)) |
| SSH service | `ssh.service` (`systemctl restart ssh` after Ch07 hardening) |
| Hand-written app units? | No — Dockerfile CMD + compose restart replace them |

# Homework
1. `systemctl is-enabled docker` on any Docker host — is it set to start on boot? Why does that matter for your ERP surviving a reboot?
2. `systemctl status ssh` — find its state, PID, and last few log lines. What unit file backs it?
3. `journalctl -u docker | tail -30` — read the daemon's recent activity.
4. Explain, in your Dockerized stack, exactly what brings `caddy/app/db/redis` back after a 4am reboot — name the two mechanisms.
5. (Test VPS) reboot it, wait, then `docker compose ps` — confirm everything came back "Up" with no manual step.

---

## Further Reading & Live Resources
- DigitalOcean — *Systemd Essentials: services, targets, journalctl*: https://www.digitalocean.com/community/tutorials/systemd-essentials-working-with-services-units-and-the-journal
- DigitalOcean — *Using journalctl to view logs*: https://www.digitalocean.com/community/tutorials/how-to-use-journalctl-to-view-and-manipulate-systemd-logs
- Arch Wiki — *systemd* (dense but authoritative reference): https://wiki.archlinux.org/title/Systemd
- Docker docs — *Start containers automatically (restart policies + systemd)*: https://docs.docker.com/config/containers/start-containers-automatically/
- `man systemctl` / `man journalctl`: https://man7.org/linux/man-pages/man1/systemctl.1.html
