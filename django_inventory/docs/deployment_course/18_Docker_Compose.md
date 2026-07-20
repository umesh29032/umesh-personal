# 18 — Docker Compose (my whole stack, service by service)

> Part of [Deployment Course](00_COURSE_OVERVIEW.md). Prev: [17 — Dockerfile](17_Dockerfile.md). Next: [19 — Docker Networking](19_Docker_Networking.md).

# Purpose
To read **my actual `docker-compose.yml`** — the single file that declares all five services, how they're wired, their volumes, health gates, and restart policies. This file *is* my deployment topology as code. `docker compose up -d` turns it into a running ERP; understanding it means understanding the whole stack ([ARCHITECTURE.md](ARCHITECTURE.md)).

# The Problem
The ERP is not one program — it's Caddy + Gunicorn + Postgres + Redis + a backup loop, that must start in the right order, find each other by name, persist the right data, and restart on failure. Doing that with individual `docker run` commands is error-prone and undocumented. Compose declares it all in one versioned file: reproducible, readable, one-command.

# Theory (from zero)

### What Compose is
`docker-compose.yml` is a YAML file describing **services** (containers), **volumes** (persistent storage), and their relationships. `docker compose up -d` reads it and creates everything; `down` removes it. It's **infrastructure-as-code** for a single host ([Ch 16](16_Docker.md)).

### My real file — service by service
```yaml
services:
  caddy:
    image: caddy:2.9.1               # pinned reverse proxy (Ch12)
    restart: unless-stopped          # auto-restart on crash/reboot (Ch09/10)
    ports: ["80:80","443:443"]       # ★ ONLY service published to the internet (Ch05)
    environment: { DOMAIN: ${DOMAIN} }  # fills {$DOMAIN} in the Caddyfile
    volumes:
      - ./deploy/Caddyfile:/etc/caddy/Caddyfile:ro  # config, read-only
      - caddy_data:/data                            # ★ TLS certs persist here (Ch12)
      - caddy_config:/config
    depends_on: [app]                # start after app exists
```
```yaml
  app:
    build: .                         # build from MY Dockerfile (Ch17)
    restart: unless-stopped
    env_file: .env                   # ★ secrets/config injected here (Ch23)
    volumes: [ media:/srv/app/config/media ]  # uploads persist (Ch20/25)
    expose: ["8000"]                 # visible to other containers, NOT the host (Ch05)
    depends_on:
      db:    { condition: service_healthy }   # wait until DB healthcheck passes
      redis: { condition: service_healthy }   # wait until Redis healthcheck passes
```
```yaml
  db:
    image: postgres:16.6-alpine      # pinned Postgres
    restart: unless-stopped
    environment: { POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD from .env }
    volumes: [ pgdata:/var/lib/postgresql/data ]   # ★ THE DATABASE lives here (Ch20/21)
    healthcheck:                     # "is Postgres actually ready?"
      test: ["CMD-SHELL","pg_isready -U $${POSTGRES_USER} -d $${POSTGRES_DB}"]
      interval: 5s ; timeout: 3s ; retries: 12
```
```yaml
  redis:
    image: redis:7.4.2-alpine        # pinned Redis
    restart: unless-stopped
    healthcheck: { test: ["CMD","redis-cli","ping"], interval: 5s, retries: 12 }
```
```yaml
  backup:
    image: postgres:16.6-alpine      # reuse pg image → matching pg_dump
    restart: unless-stopped
    entrypoint: ["/bin/sh","/srv/backup.sh"]   # the nightly loop (Ch28)
    env_file: .env
    volumes:
      - ./deploy/backup.sh:/srv/backup.sh:ro
      - backups:/backups
      - media:/media:ro              # read media to back it up (can't modify it)
    depends_on: { db: { condition: service_healthy } }

volumes: { pgdata: , media: , caddy_data: , caddy_config: , backups: }   # named volumes (Ch20)
```

### The key directives
- **`image:` vs `build:`** — pull a pinned image, or build from my Dockerfile (`app`).
- **`restart: unless-stopped`** — bring the container back on crash/reboot, unless I explicitly stopped it ([Ch 09](09_Processes_and_Services.md)/[Ch 10](10_Systemd.md)).
- **`ports:` vs `expose:`** — `ports` publishes to the **host/internet** (only Caddy); `expose` only advertises to **other containers** (app's 8000 stays private — [Ch 05](05_IP_Address_and_Ports.md)).
- **`depends_on` + `condition: service_healthy`** — start ordering *gated on a real healthcheck*, not just "started." So `app` waits until Postgres actually answers `pg_isready` and Redis answers `ping` (owner rule #2 — belt-and-suspenders with the entrypoint wait-loop, [Ch 09](09_Processes_and_Services.md)).
- **`healthcheck:`** — the command Docker runs to decide "healthy"; drives `depends_on` + shows in `docker compose ps`.
- **`env_file: .env`** — inject secrets/config at runtime (never baked into the image — [Ch 23](23_Environment_Variables.md)).
- **`volumes:` (named)** — persistent storage that outlives containers ([Ch 20](20_Docker_Volumes.md)); `./path:/inside:ro` = a **bind mount** of a host file (Caddyfile, backup.sh) read-only.
- **`environment:`** — inline env vars (e.g. `DOMAIN`, the `POSTGRES_*` for db init).

### Why the healthcheck ordering matters
Without it, `app` could start, try to `migrate`, and crash because Postgres wasn't ready yet. With `service_healthy`, Compose holds `app` until the DB passes `pg_isready`. My stack doubles down: the app **also** runs its own wait-loop in `entrypoint.sh` before migrating — so even a flaky healthcheck can't cause a half-up boot.

# Real World Example (My ERP)
- `docker compose up -d` boots the stack in dependency order: `db`+`redis` start and become healthy → `app` starts (waits healthy, migrates, collects static, runs gunicorn) → `caddy` starts (gets cert, proxies to `app:8000`) → `backup` sleeps until 02:00. See [ARCHITECTURE.md §5](ARCHITECTURE.md).
- **Only `caddy` has `ports:`** (80/443) — the internet-facing rule, enforced in this file ([Ch 05](05_IP_Address_and_Ports.md)/[Ch 11](11_Reverse_Proxy.md)).
- **Secrets** (`SECRET_KEY`, `POSTGRES_PASSWORD`, `DATABASE_URL`, `REDIS_URL`, `DOMAIN`) all come from `.env` via `env_file`/`environment` — the file itself contains no secrets, so it's safe to commit (and it is, in the AE commit) while `.env` stays gitignored ([Ch 23](23_Environment_Variables.md)).
- **The business volumes** — `pgdata` (DB) + `media` (uploads) — are declared here and backed up nightly by the `backup` service ([Ch 28](28_Backups.md)). `caddy_data` (certs) also persists.
- **Deploy** = `docker compose up -d --build` (rebuild the app image, recreate changed services); **inspect** = `docker compose ps`; **logs** = `docker compose logs -f <svc>`.

# Visual Diagram
```
 docker-compose.yml (topology as code)  ──docker compose up -d──►  running stack

  caddy ─ports 80/443(host)─┐ depends_on: app
    │ reverse_proxy app:8000 │
  app ─expose 8000(private)──┘ depends_on: db(healthy)+redis(healthy) · env_file .env · vol media
    ├─ db  (healthcheck pg_isready) · vol pgdata ★
    └─ redis (healthcheck ping)
  backup ─ depends_on db(healthy) · vols backups + media:ro ─► restic off-site (Ch28)

  named volumes: pgdata★ media★ caddy_data caddy_config backups   (survive down; NOT down -v)
  ports = public (only caddy) · expose = container-only · service_healthy = ordered start
```

# Practical — how to inspect it
```bash
docker compose config          # validate + show the fully-resolved file (env substituted)
docker compose ps              # services, health, published ports (only caddy public)
docker compose up -d           # start all (detached)
docker compose up -d --build   # rebuild app image + recreate changed services (deploy)
docker compose logs -f app     # follow one service
docker compose restart caddy   # restart one service
docker compose down            # stop+remove containers — KEEPS named volumes
docker compose exec db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"   # into Postgres (Ch21)
```
```bash
# See health + dependency behavior
docker inspect --format '{{.State.Health.Status}}' $(docker compose ps -q db)   # healthy?
docker compose ps            # STATE column: "healthy"/"starting"/"unhealthy"
```

# Beginner Mistakes
- **`docker compose down -v`** → deletes the named volumes = **your database** ([Ch 20](20_Docker_Volumes.md)). Use plain `down`.
- **Adding `ports:` to `db`/`app` "to debug"** → exposes them to the internet ([Ch 05](05_IP_Address_and_Ports.md)). Use `expose` + an SSH tunnel ([Ch 07](07_SSH.md)).
- **Trusting `depends_on` alone** (without `condition: service_healthy`) → "started" ≠ "ready"; app races the DB. Use healthchecks (this file does) + the app-side wait-loop.
- **Putting secrets inline in the committed compose** → leaked. Use `env_file: .env` (gitignored).
- **Floating image tags** → non-reproducible stack. Pin (this file does).
- **Editing the running container instead of the file** → changes vanish on `up`. The file is the source of truth; edit + `up -d`.
- **Forgetting `--build`** → `up -d` after a code change reuses the old image; the change doesn't appear ([Ch 17](17_Dockerfile.md)).

# Interview Questions
**Junior — "What does docker-compose.yml do?"** Declares a multi-container app — its services, images/builds, volumes, networks, and dependencies — so one command (`docker compose up`) starts the whole stack reproducibly.

**Mid — "Difference between `ports` and `expose`?"** `ports` publishes a container port to the host (internet-reachable); `expose` only makes it reachable by other containers on the Docker network. Only Caddy uses `ports` here, keeping app/db/redis private.

**Senior — "How does this file guarantee the app never migrates against a not-ready database?"** `app`'s `depends_on` uses `condition: service_healthy` for `db` and `redis`, so Compose won't start `app` until their healthchecks (`pg_isready`, `redis-cli ping`) pass; and the app's own `entrypoint.sh` runs a second wait-loop before `migrate`. Two independent gates → no half-up boot.

**Staff — "Critique this Compose file for a production single-VPS deploy; what's strong, what would you add?"** Strong: pinned images, only-Caddy-public, health-gated ordering + app wait-loop, named volumes for state, `restart: unless-stopped`, secrets via `.env`, a dedicated off-site backup service. Additions to consider: explicit `logging` limits (log rotation to cap disk), resource limits (`mem_limit`) to prevent one service OOMing the box, a healthcheck on `app` itself (for a `/healthz`), and a `networks:` block if you later want to isolate the backup/db on a separate internal network. None are blockers at current scale.

# Cheat Sheet
- **Compose = stack topology as code**; `up -d` runs it, `down` removes containers (**`down -v` deletes volumes/DB**).
- **My 5 services:** caddy (public 80/443) · app (build, private 8000, env_file) · db (pgdata★) · redis · backup (off-site).
- **`ports` = public, `expose` = container-only.** Only Caddy is public.
- **`depends_on: service_healthy`** + app wait-loop = ordered, never-half-up boot.
- **`env_file: .env`** for secrets (gitignored); **named volumes** for state; **pinned images**.
- Deploy: `up -d --build`. Inspect: `config`, `ps`, `logs`, `exec`.

# My ERP Section
| Directive | In my compose |
|---|---|
| Public service | only `caddy` (`ports: 80,443`) |
| Built service | `app` (`build: .` → Dockerfile) |
| Private ports | `app` `expose: 8000` (no host mapping) |
| Ordering | `app depends_on db+redis: service_healthy` |
| Healthchecks | db `pg_isready`, redis `redis-cli ping` |
| Secrets | `env_file: .env` (caddy DOMAIN via `environment`) |
| State volumes | `pgdata`★, `media`★, `caddy_data`, `caddy_config`, `backups` |
| Backup service | `backup` → `backup.sh` → restic off-site |

# Homework
1. `docker compose config` — read the resolved file. Which service has `ports:`? Why only that one?
2. Trace the boot order from `depends_on` + healthchecks: which two services must be *healthy* before `app` starts, and what commands prove their health?
3. List the five named volumes and mark which two are "the business" (backed up).
4. Explain what `docker compose down` keeps vs `down -v` destroys — and rewrite the safe habit in one sentence.
5. You changed a `.py` file and ran `docker compose up -d` but the change didn't appear. What flag did you forget, and why?

---

## Further Reading & Live Resources
- Docker docs — *Compose file reference* (services/volumes/healthcheck/depends_on): https://docs.docker.com/reference/compose-file/
- Docker docs — *Control startup order / depends_on + healthcheck*: https://docs.docker.com/compose/how-tos/startup-order/
- Docker docs — *Compose in production*: https://docs.docker.com/compose/how-tos/production/
- testdriven.io — *Dockerizing Django with Postgres/Gunicorn/Compose*: https://testdriven.io/blog/dockerizing-django-with-postgres-gunicorn-and-nginx/
- Awesome Compose (real multi-service examples): https://github.com/docker/awesome-compose
