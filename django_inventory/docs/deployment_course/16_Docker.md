# 16 — Docker

> Part of [Deployment Course](00_COURSE_OVERVIEW.md). Prev: [15 — WSGI & ASGI](15_WSGI_ASGI.md). Next: [17 — Dockerfile](17_Dockerfile.md). *(Term 4 — Containers.)*

# Purpose
To understand **Docker** — the technology that packages my whole ERP (app + its exact Python, system libs, and config) into portable **containers**, so "works on my machine" becomes "works identically on the VPS." Docker is the backbone of my deployment; every service (Caddy, app, Postgres, Redis, backup) is a container.

# The Problem
Without Docker, deploying means: install the exact Python on the VPS, install every system lib Pillow/psycopg need, install Postgres + Redis + Caddy, get versions matching my laptop, wire them together, and hope nothing drifted. One mismatched library = a bug that only happens in production. Docker eliminates this by shipping the *entire environment* as an image, byte-identical everywhere.

# Theory (from zero)

### Container vs Virtual Machine
- A **VM** virtualizes a whole computer (its own OS kernel) — heavy (GBs, slow boot).
- A **container** shares the host's Linux kernel but isolates everything above it (filesystem, processes, network) — light (MBs, boots in ms). A container is basically "a process (or few) running in an isolated box with its own filesystem."
Docker runs containers. On a small VPS you can run 5 containers where you couldn't run 5 VMs.

### Image vs Container
- An **image** = a frozen, read-only template: a filesystem snapshot + metadata (what to run). Built from a **Dockerfile** ([Ch 17](17_Dockerfile.md)). Immutable + versioned (tags like `postgres:16.6-alpine`).
- A **container** = a running (or stopped) *instance* of an image, with a thin writable layer on top. `image : container :: class : object`. You can start many containers from one image.

### Registry
Images are shared via a **registry** (Docker Hub by default). `postgres:16.6-alpine`, `caddy:2.9.1`, `redis:7.4.2-alpine` are pulled from there. My `app` image is **built locally** from my Dockerfile (not pulled).

### Layers + caching
An image is built in **layers** (one per Dockerfile step). Layers are cached: if a step's inputs didn't change, Docker reuses the cached layer. This is why my Dockerfile copies `requirements.txt` and `pip install`s **before** copying the app code — deps rarely change, so that expensive layer is cached across code edits ([Ch 17](17_Dockerfile.md)).

### Why Docker for my ERP (the payoff)
- **Reproducible:** the same image runs identically on laptop, staging, VPS. No "worked on my machine."
- **Isolated:** app, DB, Redis each in their own box; versions can't collide.
- **One-command stack:** `docker compose up -d` starts all 5 services wired together ([Ch 18](18_Docker_Compose.md)).
- **Disposable + self-healing:** a broken container is replaced from the image; state lives in **volumes** ([Ch 20](20_Docker_Volumes.md)), so containers stay stateless-ish.
- **Pinned versions** (owner rule #1): exact tags = reproducible builds.

### When NOT to use Docker
- A pure static site or a tiny script — overkill.
- Environments that forbid it, or when a managed PaaS already abstracts it.
- **GUI/desktop apps.** For a multi-service web app like this ERP, Docker is the right tool.

### Docker vs Docker Compose
- **`docker`** = manage single images/containers.
- **`docker compose`** = manage a **multi-container app** declared in `docker-compose.yml` (start/stop/build all services together). My whole stack is Compose ([Ch 18](18_Docker_Compose.md)).

# Real World Example (My ERP)
- **5 services, 5 containers**, from `docker-compose.yml`: `caddy` (image `caddy:2.9.1`), `app` (built from my `Dockerfile`), `db` (`postgres:16.6-alpine`), `redis` (`redis:7.4.2-alpine`), `backup` (postgres image + restic).
- The `app` **image** bakes: `python:3.10.16-slim` + my pinned `requirements.txt` + my `config/` code + entrypoint. Build once → the *same* image runs on my laptop and the VPS ([Ch 17](17_Dockerfile.md)).
- **All images exact-pinned** (`:16.6-alpine`, `:2.9.1`, `:3.10.16-slim`) — owner rule #1 — so a rebuild months later produces the identical stack, not "whatever's latest."
- **State is in volumes**, not containers: `pgdata` (DB), `media` (uploads) — so I can rebuild/replace the `db`/`app` containers without losing data ([Ch 20](20_Docker_Volumes.md)).
- **Deploy = build + up:** `docker compose up -d --build` builds the app image and (re)starts changed services. Rollback = redeploy the previous image/commit.

# Visual Diagram
```
  Dockerfile ──build──► IMAGE (frozen template, tagged)  ──run──► CONTAINER (instance)
     (recipe)            e.g. my app image / postgres:16.6-alpine    (a running box)

  VM: full OS per app (heavy)     vs     Container: shares host kernel, isolates above (light)

  MY STACK (docker compose up -d):     one host kernel
   ┌ caddy(caddy:2.9.1) ┐ ┌ app(built) ┐ ┌ db(postgres:16.6) ┐ ┌ redis(7.4.2) ┐ ┌ backup ┐
   └────────────────────┘ └────────────┘ └───────────────────┘ └──────────────┘ └────────┘
   images: pulled (caddy/postgres/redis) + built (app)   |   state: VOLUMES (Ch20)
   layers cached: requirements.txt installed BEFORE code copy → fast rebuilds
```

# Practical — how to inspect it
```bash
docker --version && docker compose version   # runtime present?
docker compose ps            # my running services + state + published ports
docker images               # local images + sizes + tags
docker ps -a                # all containers (running + stopped) + exit codes
```
```bash
docker compose logs -f app   # follow a service's logs (Ch31)
docker compose exec app sh   # shell INSIDE the app container (debug)
docker stats --no-stream     # per-container CPU/RAM (Ch09)
```
```bash
docker compose build app     # build the app image from the Dockerfile
docker compose up -d          # start the whole stack detached
docker compose up -d --build  # rebuild changed images + restart
docker compose down           # stop + remove containers (KEEPS named volumes)
docker compose down -v        # ⚠ ALSO deletes volumes = deletes your DB (Ch20)
```
```bash
docker system df             # disk used by images/containers/volumes
docker image prune -f        # reclaim space from dangling images (watch disk — Ch06)
```

# Beginner Mistakes
- **`docker compose down -v` on production** → deletes the `pgdata` volume = your database. `-v` is a data-destroying flag ([Ch 20](20_Docker_Volumes.md)).
- **Floating tags (`postgres:latest`)** → a rebuild silently pulls a new major version and breaks. **Pin exact tags** (owner rule).
- **Editing code inside a running container** → lost on the next rebuild; the image is built from the repo. Edit the source, rebuild.
- **Storing data inside the container filesystem** → gone when the container is replaced. Persist to volumes.
- **Not pruning** → old images fill the disk → app breaks ([Ch 06](06_Linux_Basics.md)). `docker image prune` periodically.
- **Confusing image and container** → "restarting the container" ≠ "rebuilding the image"; a code change needs a rebuild.

# Interview Questions
**Junior — "What's the difference between a Docker image and a container?"** An image is a read-only template (filesystem + run config) built from a Dockerfile; a container is a running instance of that image with a writable layer. One image → many containers.

**Junior — "Container vs VM?"** A VM virtualizes a whole OS (heavy); a container shares the host kernel and isolates only the app's filesystem/processes/network (light, fast). More containers fit on the same box.

**Mid — "Why does my Dockerfile copy requirements.txt before the app code?"** Layer caching: dependencies change rarely, so installing them in an earlier layer means code edits don't invalidate the expensive `pip install` layer — much faster rebuilds.

**Senior — "How do containers stay disposable while my database survives?"** State is externalized into **named volumes** mounted into the containers; the container filesystem is ephemeral. Deleting/replacing a container keeps the volume, so Postgres data (`pgdata`) persists across rebuilds; only `docker volume rm`/`down -v` destroys it.

**Staff — "Argue Docker Compose (not bare Docker or Kubernetes) for this ERP."** Compose declaratively wires 5 interdependent services (proxy, app, DB, cache, backup) with health-gated ordering, named volumes, and one-command lifecycle — reproducible and readable, matching a single-VPS deployment. Bare `docker run` commands would be error-prone and undocumented; Kubernetes adds a control plane, networking, and operational overhead unjustified for one box and one team. Compose is the sweet spot: infrastructure-as-code without a cluster.

# Cheat Sheet
- **Image** = frozen template (from Dockerfile); **container** = running instance. `class:object`.
- **Containers share the host kernel** (light) vs VMs (heavy). Pull from a registry; **pin exact tags**.
- **Layer cache:** deps before code = fast rebuilds. **State in volumes**, not containers.
- **My stack = 5 containers via `docker compose`.** `up -d --build` deploys; **`down -v` deletes data**.
- Inspect: `docker compose ps/logs/exec`, `docker images`, `docker stats`, `docker system df`; prune to save disk.

# My ERP Section
| Concept | In my ERP |
|---|---|
| Services/containers | caddy, app, db, redis, backup (5) |
| Built vs pulled | `app` built (Dockerfile) · caddy/postgres/redis pulled |
| Image pins | caddy:2.9.1, postgres:16.6-alpine, redis:7.4.2-alpine, python:3.10.16-slim |
| State | volumes `pgdata`,`media` (not container FS) |
| Orchestration | `docker-compose.yml` ([Ch 18](18_Docker_Compose.md)) |
| Deploy | `docker compose up -d --build` |
| Danger flag | `down -v` (deletes volumes = DB) |

# Homework
1. `docker compose ps` + `docker images` — match each running container to its image + tag. Which image is *built* vs *pulled*?
2. `docker compose exec app sh`, then `python --version` inside — is it the pinned `3.10.16`? Exit. Why is that guaranteed regardless of the VPS's own Python?
3. Explain, in one sentence each, image vs container, and why editing code inside a container is pointless.
4. `docker system df` — how much disk do images/volumes use? Which command reclaims dangling images?
5. State exactly what `docker compose down` keeps vs what `docker compose down -v` destroys, and why that distinction is life-or-death for the DB.

---

## Further Reading & Live Resources
- Docker docs — *Get started / What is a container?*: https://docs.docker.com/get-started/
- Docker docs — *Overview of Docker Compose*: https://docs.docker.com/compose/
- DigitalOcean — *How To Install and Use Docker on Ubuntu*: https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-on-ubuntu-22-04
- Julia Evans — *Docker* zine/posts (beginner-friendly mental models): https://wizardzines.com/
- **Play with Docker** (free in-browser Docker playground): https://labs.play-with-docker.com/
- Docker docs — *Best practices for building images*: https://docs.docker.com/develop/develop-images/dockerfile_best-practices/
