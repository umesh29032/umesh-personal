# 20 — Docker Volumes

> Part of [Deployment Course](00_COURSE_OVERVIEW.md). Prev: [19 — Docker Networking](19_Docker_Networking.md). Next: [21 — PostgreSQL](21_PostgreSQL.md). *(Completes Term 4.)*

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

# Beginner Mistakes
- **`docker compose down -v` on production** → instant database loss. The `-v` flag deletes named volumes. Build the habit: plain `down`.
- **Writing data to the container FS** (not a volume) → gone on next rebuild. Mount a volume for anything that must survive.
- **Assuming a volume = a backup** → it doesn't survive disk failure / corruption / VPS death / `-v`. Keep off-site backups ([Ch 28](28_Backups.md)).
- **Bind-mounting the DB dir from a host path with wrong ownership** → Postgres refuses to start. Named volumes avoid this; let Docker manage DB storage.
- **Deleting "unused" volumes with `docker volume prune`** without checking → can nuke a stopped project's data. Inspect first.
- **Not persisting `caddy_data`** → re-request certs each deploy → Let's Encrypt rate-limit ([Ch 12](12_Caddy.md)).

# Interview Questions
**Junior — "What's a Docker volume and why use one?"** Docker-managed persistent storage mounted into a container; it survives container removal/rebuilds, so stateful data (like a database) isn't lost when you redeploy.

**Mid — "Named volume vs bind mount — when each?"** Named volume for application state Docker should manage (DB, uploads) — portable and lifecycle-safe. Bind mount for host files you edit directly (config, scripts) — the host path is the source of truth. My stack: `pgdata`/`media` = named; `Caddyfile`/`backup.sh` = bind mounts.

**Senior — "Exactly how does my Postgres data survive `docker compose up -d --build`?"** The data lives in the `pgdata` named volume on the host, mounted at `/var/lib/postgresql/data`. `up --build` may recreate the `db` container from a (possibly new) image, but the new container re-mounts the same `pgdata` volume, so the files persist. Only `docker volume rm`/`down -v` destroys them.

**Staff — "Volumes protect data across rebuilds — why isn't that enough, and what's your full durability design?"** Volumes only protect against container churn, not disk failure, filesystem corruption, accidental `down -v`, or losing the VPS. Full design: named volumes for live state (fast, local) **plus** nightly `pg_dump` + media bundled by restic to encrypted **off-site** object storage with retention (7d/4w/6m) and periodic `restic check`, and a rehearsed restore drill — so RPO ≤ 24h and a total-loss event is recoverable ([Ch 28](28_Backups.md)/[Ch 40](40_Disaster_Recovery.md)). Volumes = in-box durability; off-site backups = beyond-box durability; you need both.

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

# Homework
1. `docker volume ls` — find your `pgdata`, `media`, `caddy_data`. `docker volume inspect <pgdata>` — where does it live on the host?
2. `du -sh` the pgdata volume's `_data` — how big is the DB? (Backup-size estimate for [00B](00B_Deployment_Costs_And_Free_Alternatives.md).)
3. On a TEST stack: `down`, confirm `docker volume ls` still shows pgdata, `up -d`, confirm data present. Then explain what `down -v` would have done.
4. List your five named volumes; mark the two that MUST be backed up and say why.
5. Explain in one sentence why a volume is not a substitute for an off-site backup.

---

## Further Reading & Live Resources
- Docker docs — *Volumes*: https://docs.docker.com/storage/volumes/
- Docker docs — *Storage overview* (volumes vs bind mounts vs tmpfs): https://docs.docker.com/storage/
- Docker docs — *Back up, restore, or migrate data volumes*: https://docs.docker.com/storage/volumes/#back-up-restore-or-migrate-data-volumes
- Postgres in Docker — persisting data (official image notes): https://hub.docker.com/_/postgres
- DigitalOcean — *Sharing/persisting data with Docker volumes*: https://www.digitalocean.com/community/tutorials/how-to-share-data-between-docker-containers
