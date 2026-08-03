---
id: deploy-course-06-linux-basics
type: lesson
status: active
owner: handwritten
scope: deployment, operations — this ERP shipped to a VPS
anchors: docker-compose.yml, deploy/entrypoint.sh, deploy/Caddyfile, deploy/backup.sh
verified: 2026-08-01
---

# 06 — Linux Basics

> Part of [Deployment From Zero](00_COURSE_OVERVIEW.md). Prev: [05 — IP Addresses & Ports](05_IP_Address_and_Ports.md). Next: [07 — SSH](07_SSH.md). *(Term 2 — The machine.)*

# Learning Objectives
By the end of this chapter you can:
- move around a server with ten commands and no mouse
- read a log without opening an editor
- check disk, memory and processes when something is wrong
- use `sudo` deliberately rather than reflexively

# Purpose
My VPS runs **Ubuntu Linux**, with no graphical desktop — just a text **shell**. Every deployment action (installing Docker, editing configs, reading logs, running backups) happens by typing commands. This chapter makes the shell un-scary: what Linux is, how to move around, how to install software, and the handful of commands I'll use daily. It's the ground [Ch 07–10](07_SSH.md) stand on.

# The Problem
On my laptop I click icons. On a server there are no icons — a server is a computer optimized to run programs unattended, reached over the network, controlled by typing. If the shell is a mystery, the whole VPS is a mystery. I need enough Linux fluency to operate my server confidently without copy-pasting commands I don't understand (copy-pasting a wrong `rm -rf` is how people delete production).

# Theory (from zero)

### What Linux is, and why servers use it
**Linux** is a free, open-source operating system kernel; **Ubuntu** is a popular Linux *distribution* (kernel + tools + package manager). Servers overwhelmingly run Linux because it's free, stable, scriptable, lightweight (no GUI wasting RAM), and it's what Docker + almost all server software target. **Ubuntu Server LTS** (Long-Term Support, e.g. 22.04/24.04) is the common VPS choice — 5 years of security updates.

### The shell (bash)
When you log in ([Ch 07](07_SSH.md)) you get a **shell** — a program that reads commands and runs them. The default is **bash**. The prompt looks like:
```
umesh@erp-vps:~$
  │      │      │ │
  user   host   cwd  $ = normal user  (# = root)
```
A command is `program arguments`. Example: `ls -l /var/log` = run `ls` with flag `-l` on path `/var/log`.

### The filesystem is one big tree (details in [Ch 08](08_File_System.md))
Everything hangs off `/` (root). Key spots: `/home/umesh` (your files, shorthand `~`), `/etc` (config), `/var/log` (logs), `/var/lib` (app data, incl. Docker), `/usr/bin` (programs), `/tmp` (scratch). There are no drive letters; storage devices are *mounted* into the tree.

### Users, root, and `sudo`
Linux is multi-user. **root** (uid 0) is the all-powerful admin. You normally log in as a *regular* user and run admin commands with **`sudo`** ("do this as root, just this once"), which asks for your password and logs the action. **Why not just be root?** One typo as root can wipe the system; `sudo` makes destructive power deliberate and auditable. (Permissions in depth: [Ch 08](08_File_System.md).)

### Installing software = a package manager (apt)
You don't download installers. Ubuntu uses **apt**: a curated catalog of software + dependency resolution + security updates.
- `sudo apt update` — refresh the catalog (what's available/what updates exist).
- `sudo apt upgrade` — install available updates.
- `sudo apt install <pkg>` — install a package (+ its dependencies).
This is how Docker, git, curl, etc. get onto the VPS.

### Stdin/stdout/stderr and pipes (the superpower)
Every program has **stdout** (normal output), **stderr** (errors), **stdin** (input). The **pipe** `|` feeds one program's stdout into the next's stdin, so small tools compose:
```
docker compose logs web | grep ERROR | tail -20
#   all web logs  →  keep lines with ERROR  →  show last 20
```
Redirection: `>` writes stdout to a file (overwrite), `>>` appends, `2>` redirects errors.

> 💡 **Samjho aise:** Linux ka terminal **rasoi** hai aur commands aapke **aujaar**. Mouse nahi hai to darne ki baat nahi — 10 command seekh lo (`ls`, `cd`, `cat`, `grep`, `tail`, `ps`, `df`, `top`, `sudo`, `systemctl`) aur 90% kaam nikal jaata hai. Server pe GUI nahi hota, isi liye yeh 10 hi aapke haath hain.

# Real World Example (My ERP)
- The VPS is **Ubuntu Server LTS**. I `ssh` in ([Ch 07](07_SSH.md)) and land in a bash shell as a non-root user (say `umesh`), using `sudo` for admin tasks.
- I install the runtime with apt: `sudo apt update && sudo apt install docker.io docker-compose-plugin git` (then Docker runs everything else — [Ch 16](16_Docker.md)).
- My **deploy scripts are bash**: `deploy/entrypoint.sh`, `deploy/backup.sh`, `deploy/deploy.sh` — literally sequences of the commands in this course. `entrypoint.sh` waits for the DB/Redis to be healthy, then runs `migrate` + `collectstatic` + `gunicorn` ([Ch 14](14_Gunicorn.md)/[Ch 26](26_collectstatic.md)/[Ch 27](27_Migrations.md)).
- I read production behavior by piping logs: `docker compose logs -f web` (follow), or `... | grep <request-id>` to trace one request ([Ch 31](31_Logging.md)).
- App code lives under the project dir; Postgres *data* lives in a Docker **volume** under `/var/lib/docker/volumes/...` ([Ch 20](20_Docker_Volumes.md)) — which is why deleting a container doesn't delete the database.

# Visual Diagram
```
  YOU  ──ssh──►  UBUNTU VPS
                   │
                 bash shell   umesh@erp-vps:~$  <command> <args>
                   │
        ┌──────────┴───────────── filesystem tree ─────────────┐
        /                                                        
        ├── home/umesh   (~  your files, the project checkout)   
        ├── etc          (system + service config)               
        ├── var/log      (system logs)                           
        ├── var/lib/docker (images, containers, VOLUMES=your DB) 
        ├── usr/bin      (installed programs: docker, git, curl) 
        └── tmp          (scratch)                               

  power:  you (normal user)  ──sudo──►  root (admin, careful!)
  install: apt update → apt install <pkg>
  compose tools: cmd1 | cmd2 | cmd3   (stdout → stdin chain)
```

# Practical — how to inspect it (every command explained)
```bash
pwd                 # print working directory — "where am I?"
ls -lah /var/log    # list: -l long form, -a hidden files, -h human sizes
cd ~/project        # change directory (~ = your home)
cat deploy/entrypoint.sh   # dump a whole file to screen
less deploy/entrypoint.sh  # page through a file (q to quit, / to search)
head -20 file / tail -20 file   # first / last 20 lines
tail -f /var/log/syslog        # follow a file live (Ctrl-C to stop)
grep -R "ALLOWED_HOSTS" config/ # recursively search text in files
```
```bash
whoami              # which user am I?
id                  # my uid + groups
sudo <cmd>          # run <cmd> as root (asks password, logs it)
```
```bash
sudo apt update                 # refresh package catalog
apt list --upgradable           # what has updates
sudo apt install -y curl git    # install packages non-interactively
```
```bash
df -h               # disk space per filesystem (watch this — full disk = outage)
free -h             # RAM usage
top   (or) htop     # live CPU/RAM/process view (q to quit)
uname -a            # kernel + arch
cat /etc/os-release # which Ubuntu version
```
```bash
man ls              # the manual for any command (q to quit) — your offline teacher
ls --help           # quick flag summary
```

# Production Walkthrough
- The VPS is Ubuntu with **no desktop**: these ten commands are the entire interface.
- Almost everything you touch is inside Docker, so the pattern is `docker compose <cmd>` for the app and plain Linux for the host (disk, memory, firewall).
- **Disk full is the most common host-level outage** for a small VPS — Docker images, logs and backups accumulate. `df -h` belongs in your weekly habit (ch 37).

# Debugging Guide
1. **`df -h`** — disk full breaks Postgres in confusing ways; check it first, always.
2. **`free -h`** — out of memory triggers the OOM killer, which kills a container silently.
3. **`docker compose ps`** then **`logs --tail=50`** — the app's own account of events.
4. **`journalctl -u docker --since "10 min ago"`** — host-level container failures.
5. **`top`** — one process eating everything.
6. Read errors **literally**; Linux messages are terse but rarely vague.

# Performance Notes
- A small VPS is usually memory-constrained before CPU-constrained.
- Log files grow forever unless rotated; unbounded logs are a disk-full incident waiting.
- `docker system prune` reclaims real space, but read what it will delete first.

# Security Considerations
- **Do not work as root.** A normal user plus `sudo` for specific commands limits accident and attack blast radius.
- Every `sudo` is logged — that is a feature.
- Keep the system patched (`unattended-upgrades`); unpatched kernels and OpenSSH are how boxes get taken.
- File permissions matter for `.env`: it should be readable by its owner only.

# Architecture Decisions
- **Docker as the unit of deployment**, so host-level Linux stays boring: no per-app Python versions, no system-wide packages.
- **One VPS you can fully understand** over managed complexity you cannot debug.
- **Logs to stdout** so Docker collects them and you never hunt for a log file path (ch 31).

# Best Practices
- Learn the ten commands until they are reflex; you will use them under pressure.
- Check `df -h` and `free -h` before theorising about any weird failure.
- Never paste a command you do not understand into a production shell.
- Keep a runbook of the exact commands for this server (ch 42).

# Beginner Mistakes
- **Running as root all the time.** One bad command = dead system. Use a normal user + `sudo`.
- **`rm -rf` without looking.** `rm -rf /path` deletes everything under `/path` with no recycle bin. Double-check the path; never run a pasted `rm -rf` you don't understand. (The `careful` mindset: [Ch 40](40_Disaster_Recovery.md).)
- **Editing files you can't restore.** Before editing a config, copy it: `cp file file.bak`.
- **Ignoring disk space.** A full `/` (from logs or Docker images) silently breaks the app. `df -h` regularly; prune old Docker images ([Ch 16](16_Docker.md)).
- **Assuming apt = latest.** apt gives the *distro's* version; Docker's official install script or repo is sometimes needed for current Docker ([Ch 16](16_Docker.md)).
- **Not reading stderr.** Errors go to stderr; if you only `> file` stdout, you miss them. Use `2>&1` to capture both.

# Interview Questions
- **Junior:** "What does `sudo` do and why not just log in as root?" — It runs a single command with root privileges (prompting + logging), so you keep least-privilege day-to-day and make destructive actions deliberate/auditable instead of one typo away at all times.

- **Junior:** "How do you install software on Ubuntu?" — `sudo apt update` then `sudo apt install <package>` — apt resolves dependencies and pulls from the distro's curated, security-patched repositories.

- **Mid:** "Explain a pipeline like `logs | grep ERROR | wc -l`." — Each program's stdout feeds the next's stdin: get all logs, keep only lines containing ERROR, then count them. Composability of small single-purpose tools is core Unix philosophy.

- **Senior:** "The app is down and `df -h` shows `/` at 100%. What happened and how do you recover safely?" — A full disk stops writes (DB, logs, temp) → cascading failures. Find the hog (`du -sh /var/lib/docker/*`, big logs in `/var/log`), free space safely (prune dangling Docker images/old logs, never delete live DB/volume files), then restart affected services. Prevent with log rotation + image pruning + disk alerts.

- **Staff:** "How do you keep an Ubuntu VPS patched without breaking the app, and what's your rollback if a kernel/security update misbehaves?" — Enable `unattended-upgrades` for security patches only; schedule reboots in a maintenance window; snapshot the VM before major upgrades (provider snapshots) so rollback is restoring the snapshot; keep the app in containers so the host OS and app lifecycle are decoupled — a host reboot just restarts containers (with `restart: unless-stopped`). Test upgrades on a staging box first.

### Why interviewers ask these — and the answer that separates levels

| Testing for | Weak answer | What lands |
|---|---|---|
| Do you know why `sudo` beats logging in as root? | "sudo gives you root when you need it." | Three properties: **least privilege by default**, an **audit trail** of who ran what, and it makes destructive actions **deliberate** rather than one typo away all day. Root shells have no undo and no log. |
| Can you read a pipeline as composition? | "grep filters the log." | **Each program's stdout feeds the next's stdin** — small single-purpose tools composed on demand. That is why you can build a one-off diagnostic in seconds without writing a script, which is the actual Unix skill. |
| Disk at 100% — do you know why *everything* broke? | "The disk is full, so I will delete some files." | A full disk **stops writes** — Postgres refuses, logs stop, temp files fail — so it presents as **random failures everywhere**. Find the hog with `du -sh`, then prune **dangling Docker images and rotated logs**. **Never delete a file a live process still holds open** — space is not reclaimed until it closes. |
| Can you patch a box without breaking the app? | "Run apt upgrade regularly." | **`unattended-upgrades` for security patches only**, reboots in a maintenance window, and a **provider snapshot before major upgrades** so rollback is one restore. Unscoped `apt upgrade` on a Friday is how a kernel change becomes an outage. |

**The killer follow-up:** *"You deleted a big log file and `df` still shows the disk full. Why?"* — the file is **still held open** by a running process, so the inode survives until it closes; you need `truncate` or a restart of that process. Not knowing this turns a 30-second fix into an hour of confusion.

# Revision Notes
- No GUI on a server: ten commands do 90% of the work.
- `ls cd cat grep tail ps df free top sudo systemctl` — learn these cold.
- **Check `df -h` and `free -h` first** when something is inexplicable.
- `docker compose ps` / `logs` for the app; plain Linux for the host.
- Work as a normal user; `sudo` deliberately.

# Cheat Sheet
- **Linux/Ubuntu** = the server OS; you drive it via the **bash shell** (`user@host:cwd$`).
- **Move/read:** `pwd`, `ls -lah`, `cd`, `cat`, `less`, `head/tail`, `tail -f`, `grep -R`.
- **Admin:** `sudo`, `whoami`, `id`. **Install:** `apt update` → `apt install`.
- **Health:** `df -h` (disk!), `free -h` (RAM), `htop` (processes), `cat /etc/os-release`.
- **Compose tools:** `a | b | c`, `>`/`>>`/`2>&1`. **Learn any cmd:** `man <cmd>`.
- **Golden rules:** don't live as root; back up a file before editing; watch disk; never paste a destructive command you don't understand.

# My ERP Section
| Concept | In my ERP |
|---|---|
| Server OS | Ubuntu Server LTS (the VPS) |
| How I control it | `ssh` → bash → `sudo` for admin ([Ch 07](07_SSH.md)) |
| Install runtime | `apt install docker.io docker-compose-plugin git` |
| My scripts are | bash: `deploy/entrypoint.sh`, `backup.sh`, `deploy.sh` |
| Read prod behavior | `docker compose logs -f web` + `grep` |
| App vs data on disk | project dir (code) vs `/var/lib/docker/volumes` (Postgres data) |

# Practice Tasks
1. **Read the code:** open `deploy/README.md` and list every Linux command it asks you to run. Do you know what each does?
2. **Debug:** fill a temp file to shrink free space on your laptop (safely), then run `df -h` and read what it tells you.
3. **Design:** write the five-command "is the server healthy?" check you would run every morning.
4. **Architecture:** argue why Docker makes the host's Linux setup simpler — and what it does *not* protect you from.

# Homework
1. On any Linux box (or a local Ubuntu container: `docker run -it ubuntu bash`): run `pwd`, `ls -lah /`, `cd /var/log`, `ls`. Narrate what each shows.
2. `man ls`, scroll, find what `-t` and `-S` do, quit. You just used the built-in teacher.
3. Build a pipeline: `cat /etc/passwd | grep bash | wc -l` — explain each stage and the final number.
4. `df -h` and `free -h` — write down your disk % and free RAM. Which one, if it hit 100%, takes the site down first, and why?
5. Read `deploy/entrypoint.sh` in this project with `less`. List, in order, the commands it runs at container start. (You'll recognize `migrate`, `collectstatic`, `gunicorn` — future chapters.)

---

# Further Reading & Live Resources
- **Free book** — *The Linux Command Line* by William Shotts (the classic, start-to-finish): https://linuxcommand.org/tlcl.php
- Ubuntu Server documentation (official): https://ubuntu.com/server/docs
- DigitalOcean — *Initial Server Setup with Ubuntu* (users, sudo, firewall — do this on your VPS): https://www.digitalocean.com/community/tutorials/initial-server-setup-with-ubuntu-22-04
- Ryan's Tutorials — *Linux Tutorial* (gentle, interactive): https://ryanstutorials.net/linuxtutorial/
- **Live tool** — explainshell.com (paste any command, see each flag explained): https://explainshell.com/
- MDN — *Command line crash course*: https://developer.mozilla.org/en-US/docs/Learn/Tools_and_testing/Understanding_client-side_tools/Command_line
- Julia Evans — *Bite Size Linux* / zines: https://wizardzines.com/
