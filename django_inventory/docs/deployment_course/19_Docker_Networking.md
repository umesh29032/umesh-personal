---
id: deploy-course-19-docker-networking
type: lesson
status: active
owner: handwritten
scope: deployment, operations — this ERP shipped to a VPS
anchors: docker-compose.yml, deploy/entrypoint.sh, deploy/Caddyfile, deploy/backup.sh
verified: 2026-08-01
---

# 19 — Docker Networking

> Part of [Deployment Course](00_COURSE_OVERVIEW.md). Prev: [18 — Docker Compose](18_Docker_Compose.md). Next: [20 — Docker Volumes](20_Docker_Volumes.md).

# Learning Objectives
By the end of this chapter you can:
- explain why containers talk by service name
- say which of this project's ports are reachable from outside
- test connectivity from inside a container
- decide when publishing a port is justified

# Purpose
To understand how my containers **find and talk to each other** — why `reverse_proxy app:8000` and `DATABASE_URL=…@db:5432/…` work using *names*, not IPs — and how the same mechanism keeps Postgres/Redis unreachable from the internet. This is the "wiring" behind [Ch 18](18_Docker_Compose.md)'s topology.

# The Problem
Caddy must reach Gunicorn; Gunicorn must reach Postgres and Redis. But containers get **random private IPs** that change on every restart — hardcoding IPs would break constantly. And I must ensure that while containers can reach each other, the *internet* cannot reach the DB. Docker networking solves both: stable **name-based** addressing on a **private** network.

# Theory (from zero)

### Compose creates a private network
When `docker compose up` runs, Compose creates a **user-defined bridge network** for the project and attaches every service to it. On this network, containers get private IPs (e.g. `172.x.x.x`) — a LAN that exists only among these containers on this host ([Ch 05](05_IP_Address_and_Ports.md)).

### Service name = DNS name (the key idea)
Docker runs an **embedded DNS server** on that network. Each service is reachable by its **service name**. So from the `app` container, `db` resolves to the db container's current IP, `redis` to Redis's, and from `caddy`, `app` resolves to the app container. **Names are stable even though IPs change** — Docker updates DNS automatically. That's why my configs use names:
- Caddy: `reverse_proxy app:8000`
- Django: `DATABASE_URL=postgres://…@db:5432/…`, `REDIS_URL=redis://redis:6379/0`
- backup: `pg_dump -h db …`

### `ports` vs `expose` vs internal-only (the isolation)
- **Internal traffic** (container→container) uses the private network + service names — **no `ports` needed**. `app` talks to `db:5432` purely internally.
- **`expose: 8000`** (app) = advertise to *other containers* only; still no host/internet access.
- **`ports: "443:443"`** (caddy) = **publish** to the host → internet-reachable. Only Caddy does this.
So Postgres (5432) and Redis (6379) are reachable **only** by other containers on the private net, never from outside — isolation by construction, not just firewall rules ([Ch 05](05_IP_Address_and_Ports.md)/[Ch 11](11_Reverse_Proxy.md)).

### One network vs several
By default all services share one project network (fine for a single small app). For stronger isolation you *could* put, say, `db`+`app`+`backup` on an "internal" network and `caddy`+`app` on a "web" network, so the DB isn't even on the same network as the proxy. My stack uses the single default network — adequate because nothing but Caddy is published anyway.

### Localhost inside a container ≠ the host
A common trap: inside the `app` container, `localhost` means *that container*, not the host or the db container. To reach Postgres you use `db` (the service name), never `localhost`. (This is why a Django `DATABASE_HOST=localhost` from laptop dev must become `db` in the container.)

> 💡 **Samjho aise:** Compose ke andar tiffin ek **private gali** mein rehte hain aur ek doosre ko **naam se** bulate hain (`db`, `redis`) — IP yaad rakhne ki zaroorat nahi. Bahar ki duniya us gali mein nahi ghus sakti, jab tak aap khud ek darwaza (`ports:`) na khol do. Isi liye Postgres ka port **bahar kholna hi nahi chahiye**.

# Real World Example (My ERP)
- **Caddy → app:** `deploy/Caddyfile` says `reverse_proxy app:8000`. Docker DNS resolves `app` to the Gunicorn container; Caddy connects over the private net ([Ch 12](12_Caddy.md)).
- **Django → Postgres/Redis:** `.env` sets `DATABASE_URL=postgres://<user>:<pass>@db:5432/<dbname>` and `REDIS_URL=redis://redis:6379/0`. The hostnames `db` and `redis` are **service names** resolved by Docker DNS ([Ch 21](21_PostgreSQL.md)/[Ch 22](22_Redis.md)).
- **Backup → Postgres:** `backup.sh` runs `pg_dump -h db …` — again the `db` name ([Ch 28](28_Backups.md)).
- **Isolation:** `db`/`redis` have no `ports:`, so from the internet they don't exist; only reachable via the private net by name. To inspect Postgres from my laptop I SSH-tunnel ([Ch 07](07_SSH.md)), I don't publish 5432.
- **Stability:** if I `docker compose restart db`, its IP may change, but `db` still resolves — the app reconnects without config changes.

# Visual Diagram
```
        INTERNET ── 443 ──►  caddy  (only published service)
                              │  name "app" → DNS → 172.x  (private)
   ┌───────── project bridge network (private, Docker DNS) ─────────┐
   │   caddy ──"app:8000"──► app ──"db:5432"──► db                   │
   │                          └───"redis:6379"──► redis             │
   │   backup ──"db"──► db                                          │
   │   (db, redis, app, backup: NO host ports → invisible to internet)│
   └────────────────────────────────────────────────────────────────┘
   service NAME = stable DNS (IP can change) | localhost-in-container = that container only
```

# Practical — how to inspect it
```bash
docker network ls                          # the project's bridge network exists
docker network inspect <project>_default   # which containers + their private IPs
```
```bash
# Prove name-based reachability from inside the app container
docker compose exec app sh -c 'getent hosts db redis'      # names resolve to private IPs
docker compose exec app sh -c 'nc -vz db 5432 && nc -vz redis 6379'  # reachable internally
docker compose exec app sh -c 'python -c "import os;print(os.environ[\"DATABASE_URL\"])"'  # uses @db:5432
```
```bash
# Prove the DB is NOT internet-reachable
docker compose ps          # db/redis show NO 0.0.0.0 host port (only caddy does)
#   from your laptop: nc -vz <vps-ip> 5432  → refused/timeout (good)
```
```bash
# The localhost trap
docker compose exec app sh -c 'nc -vz localhost 5432'   # FAILS: Postgres isn't in THIS container
docker compose exec app sh -c 'nc -vz db 5432'          # WORKS: db is the service name
```

# Production Walkthrough
- Compose creates a **private network**. `web` reaches the database at host `db`, port 5432 — a name, never an IP, because container IPs change on every recreate.
- `.env` therefore contains `DB_HOST=db` in production and `localhost` on your laptop. **That one difference explains most "works locally, fails in Docker" errors.**
- **Postgres and Redis publish no ports.** From the internet they do not exist. That is the strongest single security property of this deployment (ch 05).
- Only Caddy publishes 80/443.

# Debugging Guide
1. **From inside the app container**: `docker compose exec web python -c "import socket;print(socket.gethostbyname('db'))"` — does the name resolve?
2. **"could not translate host name 'db'"** = you are running outside Compose (or on the laptop with the wrong `DB_HOST`).
3. **"connection refused" to `db`** = the container is up but Postgres is not ready yet — the health gate exists for exactly this (ch 18).
4. **Works from the host but not the container** (or vice versa) = a `localhost` vs service-name mix-up.
5. **`docker network inspect`** lists who is actually attached.

# Performance Notes
- Container-to-container traffic stays on the host — effectively local, no physical network involved.
- DNS inside Compose is resolved per connection; connection reuse (`CONN_MAX_AGE`) avoids repeating it.
- Publishing a port adds a small proxying hop, which is another small reason not to publish what you do not need.

# Security Considerations
- **Not publishing a port is a firewall you cannot misconfigure.** It is stronger than a firewall rule because there is nothing listening publicly at all.
- If you must reach Postgres, use an **SSH tunnel** (ch 07) — temporary access, no permanent surface.
- Service names are internal only; do not rely on them being unreachable *within* the host, though — anything on that network can talk to the database.
- Redis has no password here because it is private-network only; the moment it were exposed, that assumption becomes a vulnerability.

# Architecture Decisions
- **Service-name addressing** so containers are replaceable without config changes.
- **Zero published database ports**, with SSH tunnelling as the sanctioned exception.
- **Environment-provided hostnames** so one image runs on laptop and server unchanged.

# Best Practices
- Never publish a database or cache port "temporarily".
- Test connectivity from inside the container that actually needs it.
- Keep `DB_HOST` in `.env`, not in code.
- Remember: anything on the private network can reach the database — container isolation is not user isolation.

# Beginner Mistakes
- **Using `localhost` to reach the DB from the app container** → connection refused; `localhost` is the app container itself. Use the service name `db` ([this is the #1 Docker-networking bug]).
- **Hardcoding container IPs** → they change on restart; use names.
- **Publishing `db`/`redis` ports to "make them reachable"** → exposes them to the internet ([Ch 05](05_IP_Address_and_Ports.md)). They're already reachable *internally* by name; keep them unpublished + tunnel for admin.
- **Expecting containers on different Compose projects to see each other** → they're on separate networks by default. Same project = same network.
- **Forgetting the app→db dependency at boot** → name resolves but the DB isn't *ready*; that's why healthchecks + the wait-loop exist ([Ch 18](18_Docker_Compose.md)).

# Interview Questions
- **Junior:** "How do containers in Compose find each other?" — Compose puts them on a shared private network with an embedded DNS server; each container is reachable by its service name (e.g. `db`, `redis`, `app`), which resolves to its current private IP.

- **Mid:** "Why `@db:5432` and not `@localhost:5432` in the app's DATABASE_URL?" — Inside the app container, `localhost` is that container, where Postgres isn't running. `db` is the service name of the Postgres container, resolved by Docker DNS over the private network.

- **Senior:** "How is Postgres kept off the internet while still reachable by the app?" — The `db` service has no `ports:` mapping, so it's not published to the host/internet; it's only attached to the private Compose network, where the `app` (and `backup`) containers reach it by the name `db`. Isolation is structural (no published port), reinforced by the host firewall.

- **Staff:** "When would you split into multiple Docker networks for this ERP, and how?" — If you wanted defense-in-depth so the proxy can't even route to the database's network: put `db`/`redis`/`backup`/`app` on an `internal` network and `caddy`/`app` on a `web` network, with `app` bridging both. Then a compromised Caddy has no network path to Postgres at all. At current single-tenant scale the single network + unpublished DB is sufficient; I'd add the split if the threat model or a shared host demanded it.

### Why interviewers ask these — and the answer that separates levels

| Testing for | Weak answer | What lands |
|---|---|---|
| Do you know why containers use names, not IPs? | "Docker assigns IPs to containers." | It does — and **they change on every recreate**. Compose runs an **embedded DNS server** so `db`, `redis`, `app` resolve to the current IP. Hardcoding an IP works until the first redeploy. |
| The classic gotcha — do you know why `localhost` fails? | "localhost should reach the database." | Inside the app container **`localhost` IS that container**, where Postgres is not running. You need the **service name `db`**. This is why `.env` has `DB_HOST=db` in Docker and `localhost` on your laptop — and why most "works locally, fails in Docker" reports land here. |
| Can you explain the isolation precisely? | "The database is behind the firewall." | Stronger than that: **`db` has no `ports:` mapping at all**, so it is never published to the host or internet — only attached to the private network where `app` and `backup` reach it by name. **There is nothing listening publicly to attack.** |
| Do you know the limit of that isolation? | "The private network means the database is secure." | **Anything on that network can reach the database.** Container isolation is not user isolation. That is the honest caveat, and it is why Redis having no password is a *conditional* decision, not a safe default. |

**The killer follow-up:** *"When would you split this into multiple Docker networks?"* — for defence in depth, so the internet-facing proxy **cannot even route to the database's network**: `db`/`redis`/`backup` on an `internal` network, `caddy` on a `web` network, and **`app` bridging both**. Anyone who says "one network is fine" without naming that trade has not thought about lateral movement.

# Revision Notes
- Compose gives a **private network**; containers talk by **service name** (`db`, `redis`).
- Container IPs change on recreate — never hardcode them.
- `DB_HOST=db` in Docker, `localhost` on the laptop. This is the classic gotcha.
- **Postgres/Redis publish no ports** — invisible from the internet.
- Need psql access? **SSH tunnel**, not a published port.

# Cheat Sheet
- **Compose = one private bridge network; service name = DNS name** (stable across IP changes).
- **My wiring:** Caddy→`app:8000`, Django→`db:5432`+`redis:6379`, backup→`db` — all by name.
- **Isolation:** internal traffic needs no `ports`; only Caddy publishes → db/redis invisible to internet.
- **`localhost` inside a container = that container** (not the host/db). Use the service name.
- Inspect: `docker network inspect`, `getent hosts db`, `nc -vz db 5432`.
- Names resolve, but readiness is separate → healthchecks + wait-loop.

# My ERP Section
| Concept | In my ERP |
|---|---|
| Network | project default bridge (private) |
| Name→service | `app`(gunicorn), `db`(postgres), `redis`, `caddy`, `backup` |
| Proxy wiring | Caddyfile `reverse_proxy app:8000` |
| DB/cache wiring | `.env` `DATABASE_URL=…@db:5432`, `REDIS_URL=redis://redis:6379/0` |
| Backup wiring | `pg_dump -h db` |
| Published | only `caddy` (80/443); db/redis/app private |
| Admin DB access | SSH tunnel, not a published port ([Ch 07](07_SSH.md)) |

# Practice Tasks
1. **Read the code:** find every hostname in `.env.example`. Which values differ between laptop and server, and why?
2. **Debug:** from inside the `web` container, resolve and connect to `db`. Then try the same from the host and explain the difference.
3. **Design:** you need read-only psql access for an accountant, once. Design it without publishing a port.
4. **Architecture:** argue whether Redis should have a password even on a private network.

# Homework
1. `docker compose exec app sh -c 'getent hosts db redis'` — see the names resolve to private IPs. Restart `db`, resolve again — did the name still work despite a possibly-new IP?
2. From the app container, `nc -vz localhost 5432` vs `nc -vz db 5432` — explain the different results.
3. `docker compose ps` — confirm only `caddy` publishes host ports. Why does that make `db` safe even without a firewall rule?
4. In `.env`, find the host portion of `DATABASE_URL` and `REDIS_URL`. Why are they `db`/`redis` and not IPs or `localhost`?
5. Sketch how you'd split into `web` + `internal` networks and what attack that would prevent.

---

# Further Reading & Live Resources
- Docker docs — *Networking overview*: https://docs.docker.com/network/
- Docker docs — *Networking in Compose* (service-name DNS): https://docs.docker.com/compose/how-tos/networking/
- Docker docs — *Bridge networks*: https://docs.docker.com/network/drivers/bridge/
- DigitalOcean — *Docker networking explained*: https://www.digitalocean.com/community/tutorials/how-to-network-docker-containers
- dj-database-url (how `DATABASE_URL` becomes Django's DB config): https://github.com/jazzband/dj-database-url
