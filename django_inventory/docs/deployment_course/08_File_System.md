---
id: deploy-course-08-file-system
type: lesson
status: active
owner: handwritten
scope: deployment, operations — this ERP shipped to a VPS
anchors: docker-compose.yml, deploy/entrypoint.sh, deploy/Caddyfile, deploy/backup.sh
verified: 2026-08-01
---

# 08 — The File System

> Part of [Deployment From Zero](00_COURSE_OVERVIEW.md). Prev: [07 — SSH](07_SSH.md). Next: [09 — Processes & Services](09_Processes_and_Services.md).

# Learning Objectives
By the end of this chapter you can:
- navigate the Linux tree and say what each top-level directory is for
- find configs, logs and data without searching blindly
- explain where this project's data and uploads actually live
- reason about what survives a container rebuild

# Purpose
To know *where things live* on a Linux server and *who is allowed to touch them* — so I can find my app, my configs, my logs, and (critically) my database files, and so I understand the permission errors that block deploys ("permission denied", "read-only file system", a container that can't write logs).

# The Problem
A deploy fails with "permission denied" writing a log; the DB won't start because its data dir has the wrong owner; a config edit "doesn't take" because I edited the wrong path. All three are **file system + permissions** issues. On a server there's no Finder — I must reason about the tree and its ownership directly.

# Theory (from zero)

### One tree, rooted at `/`
No drive letters. Everything hangs off `/`. The spots that matter for deployment:
- `/home/<user>` (`~`) — your files; the project checkout when not containerized.
- `/etc` — system + service config (e.g. `/etc/ssh/sshd_config`, `/etc/caddy/…`).
- `/var/log` — logs. `/var/lib` — variable app data, including **`/var/lib/docker`** (images, containers, and **volumes** = your Postgres data — [Ch 20](20_Docker_Volumes.md)).
- `/usr/bin`, `/usr/local/bin` — installed programs.
- `/tmp` — scratch, wiped on reboot.
- `/srv` — served app data. **In my ERP the container's app lives at `/srv/app/config`** (Dockerfile `WORKDIR`).

### Absolute vs relative paths
`/srv/app/config/manage.py` = absolute (from root). `manage.py` / `./deploy/backup.sh` = relative (from where you are, `pwd`). Scripts should prefer absolute paths so they work regardless of the caller's directory.

### Permissions: user / group / other × read / write / execute
Every file has an **owner (user)**, a **group**, and a mode for **user / group / other**, each with **r (read) / w (write) / x (execute)**. `ls -l` shows it:
```
-rwxr-x---  1 app  app   1234  entrypoint.sh
│└┬┘└┬┘└┬┘    │    │
│ u  g  o     owner group
type: - file, d dir, l link
```
`rwxr-x---` = owner rwx, group r-x, other nothing. **Directories need `x`** to be entered. `x` on a file = executable.

Numeric (octal): r=4, w=2, x=1. So `chmod 600 file` = owner rw, nobody else (secrets like `.env`). `chmod 700 dir` = owner-only dir. `chmod +x script` = make runnable.

### Ownership + `chown`
`chown app:app file` sets owner:group. This matters constantly with containers: a process running as a specific UID must **own** the dirs it writes. My Dockerfile runs as a non-root user (`uid 1000`, `app`) and explicitly `chown`s the writable dirs (`logs`, `staticfiles`, `media`) to `app` — otherwise the container couldn't write logs or collectstatic output.

### Mounts + volumes (preview)
Storage devices and Docker **volumes** are *mounted* into the tree at a path. My Postgres data lives in a named volume mounted at `/var/lib/postgresql/data` *inside the db container*; on the host it sits under `/var/lib/docker/volumes/…`. Deleting the container does **not** delete the volume — that's why the DB survives rebuilds ([Ch 20](20_Docker_Volumes.md)).

> 💡 **Samjho aise:** Linux ka file system ek **ulta ped** hai: jad `/` upar, shaakhein neeche. `/etc` = settings ka daftar, `/var/log` = diary, `/home` = aapka kamra, `/tmp` = raddi ki tokri (reboot pe khaali). Server pe kuch dhoondhna ho to yeh naksha yaad rakho — Google se pehle.

# Real World Example (My ERP)
From the real `Dockerfile` + `docker-compose.yml`:
- App code is copied to **`/srv/app/config`** (the WORKDIR); `manage.py`, `config/`, etc. live there *inside the container*.
- The image creates + `chown`s three writable dirs to the non-root `app` user: **`logs/`** (base.py makes it; log files), **`staticfiles/`** (collectstatic writes here — [Ch 26](26_collectstatic.md)), **`media/`** (a named volume mounts here — user uploads like pattern photos).
- **`.env`** sits on the host (project dir), mounted into the app via `env_file: .env`; it must be `chmod 600` + gitignored ([Ch 23](23_Environment_Variables.md)) — it holds `POSTGRES_PASSWORD`, `SECRET_KEY`.
- **Postgres data** = the `pgdata` named volume → `/var/lib/postgresql/data` in the db container → host `/var/lib/docker/volumes/…_pgdata`. **This is "the business" — backed up nightly** ([Ch 28](28_Backups.md)).
- The Caddyfile is mounted **read-only** (`:ro`) into Caddy at `/etc/caddy/Caddyfile` — the container can read config but not alter it.

# Visual Diagram
```
/                                             (host root)
├── home/umesh/django_inventory/   ← project checkout (.env, deploy/, git)
├── etc/                           ← system config (ssh, ...)
├── var/
│   ├── log/                       ← host logs
│   └── lib/docker/volumes/        ← DOCKER VOLUMES (survive container delete)
│         ├── ..._pgdata/          ←★ Postgres data = THE BUSINESS (backup!)
│         ├── ..._media/           ← user uploads (backup!)
│         └── ..._caddy_data/      ← TLS certs Caddy obtained
└── srv/app/config/   (INSIDE the app container)  ← WORKDIR: manage.py, config/
      ├── logs/  staticfiles/  media/   ← chown app:app (writable by uid 1000)

 perms:  -rwxr-x---   owner=app group=app   |  chmod 600 .env  |  chmod +x *.sh
 dirs need x to enter; .env must be 600; container writes need chown to its UID
```

# Practical — how to inspect it
```bash
ls -l /srv/app/config         # owner/group/mode of app files
ls -ld logs media staticfiles # -d = the dir itself (not contents); check they're app:app
stat .env                     # exact perms + owner (want 600, your user)
namei -l /srv/app/config/logs # every component's perms along a path (why "can't enter dir")
```
```bash
chmod 600 .env                # lock secrets to owner-only
chmod +x deploy/*.sh          # make scripts runnable
sudo chown -R app:app logs    # fix "permission denied" when a UID can't write
```
```bash
du -sh /var/lib/docker/volumes/*   # size of each volume (which is your DB? how big?)
df -h                              # disk space per mount (full disk → writes fail)
find / -name "Caddyfile" 2>/dev/null   # locate a file (2>/dev/null hides permission noise)
```
```bash
# Inside a container, check what IT sees (paths differ from host!)
docker compose exec app ls -l /srv/app/config
docker compose exec db  ls -ld /var/lib/postgresql/data
```

# Production Walkthrough
Where this project's things actually sit:
- **App code** — inside the container image, replaced on every deploy. Never edit it live.
- **Postgres data** — a Docker **volume**, deliberately outside the container so a rebuild does not erase the database (ch 20).
- **Uploaded media** — a volume too, and included in the nightly backup alongside the dump (ch 28). The database stores only paths (sql_course ch 21).
- **`.env`** — on the host, next to `docker-compose.yml`, readable by its owner only, never in git.
- **Logs** — stdout, collected by Docker; no log files to hunt for (ch 31).

# Debugging Guide
1. **"Where is the config?"** — `/etc` on a normal host; for this project, `.env` plus `deploy/`.
2. **"Where are the logs?"** — `docker compose logs`, not a file path.
3. **Disk full?** `du -sh /var/lib/docker/*` and check backups and images before deleting anything.
4. **"My change disappeared after deploy"** — you edited inside a container. Containers are disposable by design.
5. **"Data disappeared"** — a volume was not mounted, or was recreated. That is the incident to fear, and why ch 20 exists.

# Performance Notes
- Volume I/O is essentially native disk speed; there is no meaningful container penalty for Postgres.
- Many small files (uploads) are slower to back up than one large file of the same size.
- Disk latency matters more than capacity for a database; a slow disk shows up as slow COMMITs (WAL fsync).

# Security Considerations
- **`.env` permissions**: owner-read-only. A world-readable secrets file on a shared host is a breach.
- Uploaded media is user-supplied content; never serve it from a path that could execute (Caddy serves it as static files, not scripts).
- Backups on the same disk as the data are not backups (ch 28).

# Architecture Decisions
- **Persistent state in named volumes, everything else disposable.** That line is the whole mental model of container deployment.
- **Media on the filesystem, paths in the database** — standard, with the honest cost that backups must cover both.
- **Config in `.env` on the host**, so the same image runs in any environment.

# Best Practices
- Never edit files inside a running container.
- Know, without looking, which paths are volumes.
- Check `df -h` weekly; disk-full failures are avoidable.
- Keep `.env` out of git and in a password manager as well.

# Beginner Mistakes
- **Editing the host path when the container uses a copy.** App code is baked into the image at build; editing the host `config/` won't change a running container until you rebuild ([Ch 17](17_Dockerfile.md)). (Configs mounted as volumes, like the Caddyfile, DO update on restart.)
- **`chmod 777` to "fix" permission denied.** World-writable = security hole. The right fix is correct **ownership** (`chown` to the process's UID) + minimal mode.
- **`.env` world-readable or in git.** Every secret exposed. `600` + gitignore.
- **Deleting a volume thinking it's a container.** `docker volume rm ..._pgdata` deletes your **database**. Know the difference ([Ch 20](20_Docker_Volumes.md)).
- **Full disk mystery.** Writes silently fail (DB, logs). `df -h` + `du -sh` to find the hog (often Docker images/logs).

# Interview Questions
- **Junior:** "What does `chmod 600 .env` do and why?" — Sets read+write for the owner only, no access for group/others — so secrets in `.env` can't be read by other users on the box.

- **Junior:** "What's the difference between an absolute and relative path?" — Absolute starts from `/` and is unambiguous anywhere; relative is resolved from the current directory.

- **Mid:** "A container can't write to its log directory. Diagnose." — The process runs as a specific UID (here `app`/1000) but the directory is owned by root or has no write bit for that UID. Fix: `chown` the dir to the container's user (my Dockerfile does this for `logs/staticfiles/media`), or mount a volume owned correctly — never `chmod 777`.

- **Senior:** "Explain how my Postgres data survives `docker compose down` and a rebuild, in file-system terms." — The data lives in the **`pgdata` named volume**, stored on the host under `/var/lib/docker/volumes/…`, mounted into the container at `/var/lib/postgresql/data`. `down` removes containers, not named volumes; a rebuild makes a new container that re-mounts the same volume — so the files persist. Only `docker volume rm` (or `down -v`) destroys them.

- **Staff:** "Design the writable-path + permission model for a hardened Django container." — Run as a non-root fixed UID; bake code read-only into the image; create + `chown` to that UID only the few dirs the app must write (logs, collected static, media); mount media (and any user-writable data) as a volume owned by that UID; keep secrets in an env file mounted read-only with `600` perms; everything else read-only. Least privilege: the process can write exactly what it needs and nothing else, so a compromise can't rewrite the app or read other users' files.

### Why interviewers ask these — and the answer that separates levels

| Testing for | Weak answer | What lands |
|---|---|---|
| Do you know what `chmod 600` actually asserts? | "It makes the file private." | **Owner read+write, nothing for group or others.** For `.env` that matters because **anyone who can read that file owns the system** — DB password, `SECRET_KEY`, backup credentials. |
| Container cannot write its log directory — can you diagnose? | "Permissions issue, I will chmod 777." | The process runs as a **specific UID** (here `app`/1000) and the directory is owned by root. Fix by **`chown` to that UID** (this Dockerfile does it for `logs`, `staticfiles`, `media`) or mount a volume owned by it. `777` makes the symptom vanish and the box less safe. |
| Can you explain data survival in file-system terms? | "Docker keeps the data somewhere." | The **`pgdata` named volume** lives on the host under `/var/lib/docker/volumes/…` and is mounted at `/var/lib/postgresql/data`. **`down` removes containers, not named volumes** — which is exactly why `down -v` is the dangerous one. |
| Can you design writable paths for a hardened container? | "Run the container and let it write where it needs." | **Non-root fixed UID** · code baked **read-only** into the image · `chown` **only** the few dirs that must be writable (logs, static, media) · user data on a **volume** owned by that UID. Writable-by-default is how a compromised process persists itself. |

**The killer follow-up:** *"Your container writes uploads and they vanish after a deploy. What happened?"* — the write went to the **container filesystem instead of a volume**, so it died with the container. That is not a bug to debug, it is **data already lost** — and the reason to verify one upload after every deploy that touches storage.

# Revision Notes
- `/` root · `/etc` config · `/var/log` logs · `/home` users · `/tmp` scratch.
- Containers are **disposable**; only **volumes** persist.
- This project: Postgres data + media = volumes · `.env` = host file · logs = stdout.
- Editing inside a container is always wrong — it vanishes on deploy.
- Backups on the same disk are not backups.

# Cheat Sheet
- **One tree from `/`.** Key: `/etc` config, `/var/log` logs, `/var/lib/docker/volumes` (**your DB!**), `/srv/app/config` (app in container).
- **Perms = owner/group/other × rwx.** `600` secrets, `700` private dir, `+x` scripts. Dirs need `x` to enter.
- **`chown` to the process UID** fixes "permission denied" — not `chmod 777`.
- **Volumes ≠ containers:** deleting a container keeps the volume; `volume rm` deletes data.
- **Inspect:** `ls -l`, `stat`, `namei -l`, `du -sh`, `df -h`, `docker compose exec <svc> ls`.
- Editing baked-in code needs a rebuild; mounted configs (Caddyfile) update on restart.

# My ERP Section
| Concept | In my ERP |
|---|---|
| App path (in container) | `/srv/app/config` (Dockerfile WORKDIR) |
| Runtime user | non-root `app` (uid 1000) |
| Writable dirs (chowned) | `logs/`, `staticfiles/`, `media/` |
| DB data | `pgdata` volume → `/var/lib/postgresql/data` (★ backup) |
| Media uploads | `media` volume (★ backup) |
| Secrets | `.env` on host, `env_file`, must be `600` + gitignored |
| Read-only mount | `deploy/Caddyfile` → `/etc/caddy/Caddyfile:ro` |

# Practice Tasks
1. **Read the code:** list the `volumes:` in `docker-compose.yml`. For each, say what is lost if it were missing.
2. **Debug:** create a file inside a running container, redeploy, and confirm it is gone. Feel it once.
3. **Design:** where would you put a new export feature's generated files, and what does that decision imply for backups?
4. **Architecture:** argue for moving uploads to object storage. What gets simpler, what gets harder?

# Homework
1. `ls -l` this project's `deploy/` dir — which files have `+x`? Should `backup.sh`/`entrypoint.sh`?
2. `stat` your `.env` (if present). Is it `600`? If not, why is that dangerous, and fix it.
3. Explain, in file-system terms, exactly why deleting the `app` container does NOT lose your Postgres data.
4. `du -sh /var/lib/docker/volumes/*` (on the VPS later) — which volume is the DB, and how big? (This feeds the backup-size estimate in [00B](00B_Deployment_Costs_And_Free_Alternatives.md).)
5. Predict what happens to a running container if you edit the host `config/views.py` — does the change appear? Why or why not?

---

# Further Reading & Live Resources
- Linux Foundation — *Filesystem Hierarchy Standard* (what each top dir is for): https://refspecs.linuxfoundation.org/FHS_3.0/fhs/index.html
- DigitalOcean — *Introduction to Linux Permissions*: https://www.digitalocean.com/community/tutorials/an-introduction-to-linux-permissions
- DigitalOcean — *chmod/chown permissions basics*: https://www.digitalocean.com/community/tutorials/linux-permissions-basics-and-how-to-use-umask-on-a-vps
- `chmod` calculator (visualize octal modes): https://chmod-calculator.com/
- Docker docs — *Volumes* (where container data really lives): https://docs.docker.com/storage/volumes/
- explainshell (paste `ls -l` / `chmod 600` to decode): https://explainshell.com/
