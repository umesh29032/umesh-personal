---
id: deploy-course-20-docker-volumes
type: lesson
status: active
owner: handwritten
scope: deployment, operations — this ERP shipped to a VPS
anchors: docker-compose.yml, deploy/entrypoint.sh, deploy/Caddyfile, deploy/backup.sh
verified: 2026-08-01
---

# 20 — Docker Volumes

> Part of [Deployment Course](00_COURSE_OVERVIEW.md). Prev: [19 — Docker Networking](19_Docker_Networking.md). Next: [21 — PostgreSQL](21_PostgreSQL.md). *(Completes Term 4.)*

# Learning Objectives
By the end of this chapter you can:
- explain why a container losing data is normal and expected
- name every volume this project depends on
- say exactly which command would destroy the database
- reason about backups versus volumes

# Purpose
To understand **where my data actually lives** so it survives container rebuilds — the difference between the disposable container filesystem and a persistent **volume**. This is the single most important concept for not losing the factory's database. `pgdata` is the business; a volume is why it's safe.

# The Problem
Containers are disposable ([Ch 16](16_Docker.md)) — I rebuild/replace them on every deploy. But the database, user uploads, and TLS certs must **persist** across those rebuilds. If Postgres wrote to the container's own filesystem, every `docker compose up --build` would wipe the factory's data. Volumes are the mechanism that keeps state alive while containers come and go.

# Theory (from zero)

### Three places a container can write
1. **Container writable layer** — the thin RW layer on top of the image. **Ephemeral**: destroyed when the container is removed/replaced. Fine for scratch, fatal for data.
2. **Named volume** — Docker-managed persistent storage (on the host under `/var/lib/docker/volumes/…`), mounted into the container at a path. **Survives** `docker compose down` + rebuilds. This is where stateful data goes.
3. **Bind mount** — a specific host file/dir mounted into the container (`./deploy/Caddyfile:/etc/caddy/Caddyfile:ro`). Great for config you edit on the host; the host owns the file.

### Named volume vs bind mount
- **Named volume** (`pgdata:/var/lib/postgresql/data`) — Docker manages the storage; portable, backed up as data. Use for **application state** (DB, uploads, certs).
- **Bind mount** (`./deploy/backup.sh:/srv/backup.sh:ro`) — a known host path; you see/edit it directly. Use for **config/scripts** injected into the container.

### The lifecycle rule (memorize)
- `docker compose down` → removes **containers**, **keeps named volumes**. Data safe.
- `docker compose down -v` → **also removes named volumes** → **deletes your database**. Data gone.
- Rebuilding the image / recreating a container → keeps volumes (a new container re-mounts the same volume).
So: containers are cattle, **volumes are the herd's DNA** — guard them.

### Why this makes containers "stateless-ish"
Because all durable state is in volumes, the containers themselves hold nothing precious. You can destroy and recreate `app`/`db` freely; the data persists in `pgdata`/`media`. That's what makes deploys safe and rollbacks clean.

### Backups still matter (volumes ≠ backups)
A volume protects against *container* deletion, not against *disk failure, corruption, or `down -v` fat-finger, or the VPS dying*. That's why the `backup` service copies volume data **off-site** nightly ([Ch 28](28_Backups.md)/[Ch 40](40_Disaster_Recovery.md)). A volume is durability *within the box*; backups are durability *beyond the box*.

> 💡 **Samjho aise:** Tiffin dhulne pe sab kuch mit jaata hai — container delete hua, andar ka data gaya. Volume ek **alag almirah** hai jo tiffin ke bahar rehti hai. Isi liye database ka data volume mein rakhte hain: container naya banao, purana data waise ka waisa. **Volume bhoole = data gaya**, aur yeh galti ek hi baar mein sabak de deti hai.

# Real World Example (My ERP)
My `docker-compose.yml` declares five **named volumes**:
| Volume | Mounted in | Holds | Business-critical? |
|---|---|---|---|
| **`pgdata`** | db `/var/lib/postgresql/data` | the entire PostgreSQL database | ★ YES — back up |
| **`media`** | app + backup `/srv/app/config/media` | user uploads (pattern photos, attachments) | ★ YES — back up |
| **`caddy_data`** | caddy `/data` | issued TLS certs + ACME account | important (avoid re-issue/rate-limit — [Ch 12](12_Caddy.md)) |
| **`caddy_config`** | caddy `/config` | Caddy's autosaved config | minor |
| **`backups`** | backup `/backups` | local dump staging before off-site push | transient |

Plus **bind mounts** for config: `./deploy/Caddyfile:ro`, `./deploy/backup.sh:ro`.
- **Rebuild safety:** `docker compose up -d --build` replaces the `app` (and can recreate `db`) container, but `pgdata`/`media` persist → no data loss on deploy.
- **The one deadly command:** `docker compose down -v` would delete `pgdata` = the factory's production database. I never run `-v` on prod.
- **Backup pairing:** the `backup` service mounts `media:ro` + dumps Postgres, then restic pushes both off-site — so even losing the whole VPS (and all volumes) is recoverable ([Ch 28](28_Backups.md)).

# Visual Diagram
```
  IMAGE (read-only) ─run─► CONTAINER
                            ├─ writable layer  ← EPHEMERAL (gone when container removed)
                            ├─ named volume    ← PERSISTENT (host /var/lib/docker/volumes)
                            │     pgdata ★ (DB) · media ★ (uploads) · caddy_data (certs)
                            └─ bind mount      ← host file (Caddyfile:ro, backup.sh:ro)

  docker compose down      → removes containers, KEEPS volumes   (data safe)
  docker compose down -v    → removes containers AND volumes = DELETES DB ⚠
  up --build / recreate     → new container re-mounts SAME volume (data persists)

  volume = durability INSIDE the box  |  off-site backup = durability BEYOND the box (Ch28)
```

# Practical — how to inspect it
```bash
docker volume ls                              # all volumes (see <project>_pgdata etc.)
docker compose ps --format '{{.Name}}'        # containers using them
docker volume inspect <project>_pgdata        # host mountpoint + metadata
du -sh /var/lib/docker/volumes/*_pgdata/_data # size of the DB on disk (backup estimate — 00B)
```
```bash
# See what's inside a volume via a container
docker compose exec db ls -lh /var/lib/postgresql/data      # the live DB files
docker compose exec app ls -lh /srv/app/config/media        # uploaded files
```
```bash
# The lifecycle proof (do on a TEST stack, never prod):
docker compose down          # stop; then:
docker volume ls             # pgdata STILL there
docker compose up -d         # DB data still present
# docker compose down -v     # ⚠ would delete pgdata — DO NOT on prod
```

# Production Walkthrough
Three volumes carry everything that must survive:
- **Postgres data** — the factory's truth. Losing it means restoring from backup (ch 29).
- **Media** — uploaded pattern photos, receipts, profile pictures. The database holds only paths, so this volume is *half* your data (sql_course ch 21).
- **Caddy certificates/state** — losing it re-issues certificates; harmless but rate-limited.

Deploys replace containers and never touch volumes, which is precisely what makes `up -d --build` safe to run casually.

# Debugging Guide
1. **"The database is empty after deploy"** — a volume was not mounted or a different volume name was used. Stop; do not "fix forward".
2. **`docker volume ls`** and **`docker compose config`** — confirm the expected names are attached.
3. **Disk full?** Volumes grow: database, media, and old backup files. `du -sh` before deleting anything (ch 06).
4. **Permission denied writing media** = ownership mismatch between the container user and the volume.
5. **`docker compose down -v`** is the command that deletes volumes. If someone ran it, you are in a restore scenario, not a debugging one.

# Performance Notes
- Named volumes are near-native disk speed; suitable for Postgres without caveats.
- Bind mounts can be slower and add host-path coupling; named volumes are preferred here.
- Many small media files make backups slower than their total size suggests.
- Disk latency shows up as slow COMMITs (WAL fsync), not as slow queries.

# Security Considerations
- **A volume is not a backup.** Same disk, same machine, same fire. Off-site copies are the backup (ch 28).
- Volume contents include personal data (photos, receipts) — protect the host accordingly.
- Anyone with Docker access effectively has full access to every volume; Docker group membership is root-equivalent.

# Architecture Decisions
- **Named volumes for all persistent state**, so nothing important lives inside a container.
- **Media on a volume rather than in the database**, accepting that backups must cover both.
- **Explicit volume names** in compose so an accidental rename cannot silently create an empty one.

# Best Practices
- Know the three volume names by heart.
- Never run `down -v` on a machine with real data.
- Verify the volume is attached after any compose change involving it.
- Test a restore (ch 29) — that is the only way to know the volume strategy holds.

# Beginner Mistakes
- **`docker compose down -v` on production** → instant database loss. The `-v` flag deletes named volumes. Build the habit: plain `down`.
- **Writing data to the container FS** (not a volume) → gone on next rebuild. Mount a volume for anything that must survive.
- **Assuming a volume = a backup** → it doesn't survive disk failure / corruption / VPS death / `-v`. Keep off-site backups ([Ch 28](28_Backups.md)).
- **Bind-mounting the DB dir from a host path with wrong ownership** → Postgres refuses to start. Named volumes avoid this; let Docker manage DB storage.
- **Deleting "unused" volumes with `docker volume prune`** without checking → can nuke a stopped project's data. Inspect first.
- **Not persisting `caddy_data`** → re-request certs each deploy → Let's Encrypt rate-limit ([Ch 12](12_Caddy.md)).

# Interview Questions
- **Junior:** "What's a Docker volume and why use one?" — Docker-managed persistent storage mounted into a container; it survives container removal/rebuilds, so stateful data (like a database) isn't lost when you redeploy.

- **Mid:** "Named volume vs bind mount – when each?" — Named volume for application state Docker should manage (DB, uploads) — portable and lifecycle-safe. Bind mount for host files you edit directly (config, scripts) — the host path is the source of truth. My stack: `pgdata`/`media` = named; `Caddyfile`/`backup.sh` = bind mounts.

- **Senior:** "Exactly how does my Postgres data survive `docker compose up -d --build`?" — The data lives in the `pgdata` named volume on the host, mounted at `/var/lib/postgresql/data`. `up --build` may recreate the `db` container from a (possibly new) image, but the new container re-mounts the same `pgdata` volume, so the files persist. Only `docker volume rm`/`down -v` destroys them.

- **Staff:** "Volumes protect data across rebuilds – why isn't that enough, and what's your full durability design?" — Volumes only protect against container churn, not disk failure, filesystem corruption, accidental `down -v`, or losing the VPS. Full design: named volumes for live state (fast, local) **plus** nightly `pg_dump` + media bundled by restic to encrypted **off-site** object storage with retention (7d/4w/6m) and periodic `restic check`, and a rehearsed restore drill — so RPO ≤ 24h and a total-loss event is recoverable ([Ch 28](28_Backups.md)/[Ch 40](40_Disaster_Recovery.md)). Volumes = in-box durability; off-site backups = beyond-box durability; you need both.

### Why interviewers ask these — and the answer that separates levels

| Testing for | Weak answer | What lands |
|---|---|---|
| Named volume or bind mount — do you have a rule? | "They both persist data." | **Named volume** for state Docker should manage (DB, uploads) — portable, lifecycle-safe. **Bind mount** for host files you edit directly (config, scripts) — the host path is the source of truth. Here: `pgdata`/`media` are named; the Caddyfile is bound. |
| Can you explain survival across `up --build`? | "Volumes are persistent." | Mechanically: `up --build` may **recreate the `db` container from a new image**, and the new container **re-mounts the same `pgdata` volume** at `/var/lib/postgresql/data`. The container is replaced; the data was never inside it. |
| Do you know all three volumes here? | "The database volume." | **Postgres data · media uploads · Caddy certificates/state.** Media is *half your data* (the DB stores only paths) and losing Caddy state means re-issuing certs — harmless but **rate-limited** (ch 12). |
| Do you know a volume is not a backup? | "Volumes keep the data safe." | A volume survives **container churn only** — not disk failure, filesystem corruption, an accidental `down -v`, or losing the VPS. **Same disk, same machine, same fire.** Off-site copies are the backup (ch 28). |

**The killer follow-up:** **⚠️ *"Which single command would destroy your production database?"*** — **`docker compose down -v`.** If that is not instant knowledge, the `-v` will eventually get typed. Then the real follow-up: *"and could you recover?"* — which is a question about ch 28 and ch 29, not about volumes.

# Revision Notes
- Containers are disposable; **volumes persist**.
- This project: **Postgres data · media · Caddy state**.
- Deploys replace containers, never volumes — that is why deploys are safe.
- ⚠️ `docker compose down -v` **deletes volumes** = deletes the database.
- A volume is **not** a backup: same disk, same fire (ch 28).

# Cheat Sheet
- **Container FS = ephemeral; named volume = persistent; bind mount = host file.**
- **State → named volumes** (`pgdata`★, `media`★, `caddy_data`). **Config → bind mounts** (`Caddyfile`, `backup.sh`).
- **`down` keeps volumes; `down -v` DELETES them (= your DB).** Rebuild keeps volumes.
- **Volume ≠ backup** — add off-site backups for disk/VPS loss ([Ch 28](28_Backups.md)).
- Inspect: `docker volume ls/inspect`, `du -sh …/_pgdata/_data`.
- Persist `caddy_data` (certs) to avoid re-issue rate limits.

# My ERP Section
| Volume | Holds | Rule |
|---|---|---|
| `pgdata` | PostgreSQL DB | ★ back up; never `down -v` |
| `media` | user uploads | ★ back up |
| `caddy_data` | TLS certs | persist (avoid rate-limit) |
| `caddy_config` | Caddy autosave | keep |
| `backups` | local dump staging | transient (off-site is the archive) |
| bind: `Caddyfile`,`backup.sh` | config/scripts (`:ro`) | edit on host |

# Practice Tasks
1. **Read the code:** list the volumes in `docker-compose.yml` and match each to what it stores.
2. **Debug:** on a throwaway project, run `down` and then `down -v`, and observe the difference in what survives.
3. **Design:** write the one-paragraph rule you would give a new developer about volumes, so they never run `-v` by accident.
4. **Architecture:** argue whether media should stay on a volume or move to object storage. What changes in ch 28's backup script?

# Homework
1. `docker volume ls` — find your `pgdata`, `media`, `caddy_data`. `docker volume inspect <pgdata>` — where does it live on the host?
2. `du -sh` the pgdata volume's `_data` — how big is the DB? (Backup-size estimate for [00B](00B_Deployment_Costs_And_Free_Alternatives.md).)
3. On a TEST stack: `down`, confirm `docker volume ls` still shows pgdata, `up -d`, confirm data present. Then explain what `down -v` would have done.
4. List your five named volumes; mark the two that MUST be backed up and say why.
5. Explain in one sentence why a volume is not a substitute for an off-site backup.

---

# Further Reading & Live Resources
- Docker docs — *Volumes*: https://docs.docker.com/storage/volumes/
- Docker docs — *Storage overview* (volumes vs bind mounts vs tmpfs): https://docs.docker.com/storage/
- Docker docs — *Back up, restore, or migrate data volumes*: https://docs.docker.com/storage/volumes/#back-up-restore-or-migrate-data-volumes
- Postgres in Docker — persisting data (official image notes): https://hub.docker.com/_/postgres
- DigitalOcean — *Sharing/persisting data with Docker volumes*: https://www.digitalocean.com/community/tutorials/how-to-share-data-between-docker-containers
