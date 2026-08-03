---
id: deploy-course-architecture
type: lesson
status: active
owner: handwritten
scope: deployment, operations — this ERP shipped to a VPS
anchors: docker-compose.yml, deploy/entrypoint.sh, deploy/Caddyfile, deploy/backup.sh
verified: 2026-08-01
---

# Deployment Architecture — Kapil Enterprises ERP (the complete picture)

> Part of [Deployment Course](00_COURSE_OVERVIEW.md). This is the **capstone reference**: the whole deployment on one page, grounded in the real `docker-compose.yml`, `Dockerfile`, `deploy/Caddyfile`, `deploy/entrypoint.sh`, `deploy/backup.sh`. Read it after the chapters, or use it as the map while reading them. Every box links to the chapter that teaches it.

---

#> 💡 **Samjho aise:** Yeh poore ghar ka **naksha** hai — ek page pe har dabba aur unke beech ke teer.
> Kaunsa chapter kis dabbe ko padhata hai, wo yahin se dikhta hai. Jab kuch samajh
> na aaye, is naksha pe ungli rakho aur poochho: *"main is waqt kaunse dabbe ki baat
> kar raha hoon?"* — aadha confusion wahin khatam ho jaata hai.

# 1. One-paragraph summary
The ERP runs as **five Docker containers on one Ubuntu VPS**, orchestrated by `docker-compose.yml`. The internet reaches only **Caddy** (TLS + reverse proxy), which forwards to **Gunicorn** (3 workers running the Django app), which reads/writes **PostgreSQL** (data of record) and **Redis** (cache + login rate-limiter). A **backup** container dumps Postgres + media nightly to off-site storage via **restic**. Secrets come from a `.env` file; the app never boots half-configured (it waits for healthy DB+Redis, then migrates, collects static, and starts). It is deliberately a *single-box* architecture — cheapest, simplest, and matched to a factory's steady, modest load.

## 2. The full stack diagram
```
                            THE INTERNET  (untrusted)
    worker phones · manager laptops · owner · finance          erp.<domain>
                               │  HTTPS 443 / HTTP 80→redirect
                               ▼
 ┌───────────────────────── ONE UBUNTU VPS ─────────────────────────────────┐
 │  firewall (ufw + cloud SG): ALLOW 22, 80, 443 · deny rest   [Ch05][Ch07]  │
 │                                                                           │
 │   ┌──────────── Docker (systemd-enabled, restart: unless-stopped) ────┐  │
 │   │                                                                    │  │
 │   │   ┌─────────┐  published 80,443   (ONLY public container)          │  │
 │   │   │  caddy  │  caddy:2.9.1                              [Ch11][Ch12]│  │
 │   │   │         │  TLS(Let's Encrypt, auto) · gzip · X-Forwarded-Proto  │  │
 │   │   └────┬────┘  vol: caddy_data(=certs), Caddyfile(:ro)             │  │
 │   │        │ reverse_proxy app:8000   (private docker DNS)  [Ch19]      │  │
 │   │        ▼                                                            │  │
 │   │   ┌─────────┐  build: .  (Dockerfile)               [Ch14][Ch17]   │  │
 │   │   │  app    │  gunicorn config.wsgi:application, 3 workers, :8000   │  │
 │   │   │         │  non-root uid 1000 · DJANGO_SETTINGS=…production      │  │
 │   │   │         │  env_file: .env · vol: media          [Ch23][Ch24]   │  │
 │   │   └──┬───┬──┘  entrypoint: wait-healthy→migrate→collectstatic→gunicorn│
 │   │      │   │                                        [Ch26][Ch27]      │  │
 │   │  5432│   │6379                                                      │  │
 │   │      ▼   ▼                                                          │  │
 │   │ ┌────────┐  ┌────────┐                                             │  │
 │   │ │  db    │  │ redis  │   postgres:16.6-alpine · redis:7.4.2-alpine  │  │
 │   │ │ 5432   │  │ 6379   │   healthchecks (pg_isready / redis-cli ping) │  │
 │   │ │[Ch21]  │  │[Ch22]  │   vol: pgdata(=DATA)                         │  │
 │   │ └───┬────┘  └────────┘                                             │  │
 │   │     │ pg_dump -Fc                                                   │  │
 │   │     ▼                                                               │  │
 │   │ ┌─────────┐  loop: sleep→02:00 IST→ dump + media → restic          │  │
 │   │ │ backup  │  ───────────────────────────────────────►  OFF-SITE    │  │
 │   │ └─────────┘  vols: backups, media(:ro)          [Ch28][Ch29][Ch40] │  │(B2/R2)
 │   └────────────────────────────────────────────────────────────────────┘ │
 │   config: .env (0600, gitignored) ─► compose ─► every container [Ch23]    │
 └───────────────────────────────────────────────────────────────────────────┘
       named volumes (survive container rebuild [Ch20]):
         pgdata ★  media ★  caddy_data  caddy_config  backups
         ★ = "the business" — what the nightly off-site backup protects
```

## 3. Components (what each is, and its chapter)
| Service | Image (pinned) | Role | Public? | Key volumes | Chapter |
|---|---|---|---|---|---|
| `caddy` | caddy:2.9.1 | reverse proxy, auto-HTTPS, gzip | **Yes: 80,443** | caddy_data (certs), Caddyfile:ro | [11](11_Reverse_Proxy.md),[12](12_Caddy.md) |
| `app` | built from `Dockerfile` | Gunicorn (3 workers) + Django | No (`expose 8000`) | media | [14](14_Gunicorn.md),[17](17_Dockerfile.md),[24](24_Django_Settings.md) |
| `db` | postgres:16.6-alpine | PostgreSQL (data of record) | No | **pgdata ★** | [21](21_PostgreSQL.md) |
| `redis` | redis:7.4.2-alpine | cache + login rate-limiter | No | (none; ephemeral OK) | [22](22_Redis.md) |
| `backup` | postgres:16.6-alpine + restic | nightly pg_dump+media → off-site | No | backups, media:ro | [28](28_Backups.md) |

## 4. Request lifecycle (one worker opening `/production/my-work/`)
1. Phone → **DNS** resolves `erp.<domain>` → VPS IP ([Ch04](04_DNS_Domains.md)).
2. **TCP+TLS** to VPS `:443`; Caddy presents the Let's Encrypt cert ([Ch03](03_HTTP_HTTPS.md)).
3. **Caddy** decrypts, gzip-negotiates, adds `X-Forwarded-Proto: https`, `reverse_proxy` → `app:8000` over the private net ([Ch12](12_Caddy.md)).
4. **Gunicorn** hands the request to one of 3 workers → Django (`config.settings.production`) ([Ch14](14_Gunicorn.md)).
5. Django trusts the forwarded scheme (`SECURE_PROXY_SSL_HEADER`), authorizes the worker (RBAC), reads **Postgres** (their allocations) + **Redis** (session), renders.
6. Response → Caddy → re-encrypt → phone. Static assets are served compressed by WhiteNoise in the app ([Ch25](25_Static_vs_Media.md)).

## 5. Boot / startup sequence (deterministic — no half-up state)
```
docker compose up -d
   ├─ db     starts → healthcheck pg_isready loops until READY
   ├─ redis  starts → healthcheck redis-cli ping until READY
   ├─ app    (depends_on db+redis: service_healthy) then entrypoint.sh:
   │           1) wait-loop: ensure DB conn + Redis ping (120s deadline, else FATAL exit)
   │           2) manage.py migrate --noinput        [Ch27]
   │           3) manage.py collectstatic --noinput   [Ch26]
   │           4) exec gunicorn … (becomes PID 1, 3 workers)   [Ch09]
   ├─ caddy  (depends_on app) → obtains/loads cert → serves 443, proxies app:8000
   └─ backup → sleeps until 02:00 IST, then dumps
```
Two independent safeties on ordering: compose `depends_on: service_healthy` **and** the entrypoint's own wait-loop (owner rule: don't trust `depends_on` alone).

## 6. Trust & security boundaries ([Ch34](34_Production_Security.md))
- **Only Caddy is public** (80/443); `app`/`db`/`redis`/`backup` publish nothing → unreachable from the internet by construction, not just by firewall rule ([Ch05](05_IP_Address_and_Ports.md)).
- **TLS terminates at Caddy**; internal hop is plaintext on the private Docker net (single-tenant VPS).
- **App runs non-root** (uid 1000); writable dirs limited to `logs/staticfiles/media` ([Ch08](08_File_System.md)).
- **Secrets** live only in `.env` (0600, gitignored) → injected via `env_file`; production settings are `DEBUG=False`, HSTS, secure cookies, SSL redirect ([Ch23](23_Environment_Variables.md),[Ch24](24_Django_Settings.md)).
- **Redis fail-fast**: the app refuses to boot without Redis (so the login rate-limiter is never silently bypassed) ([Ch22](22_Redis.md)).
- SSH is key-only, root login off ([Ch07](07_SSH.md)).
- *(Open items from RC1: bump Django 5.0.x, scope `/media/` object-auth, sanitize storefront SVG — see `docs/RELEASE_CANDIDATE_CERTIFICATION_RC1.md`.)*

## 7. Data & durability ([Ch20](20_Docker_Volumes.md),[Ch28](28_Backups.md),[Ch40](40_Disaster_Recovery.md))
- **pgdata** (Postgres) + **media** (uploads) = the irreplaceable state; both are **named volumes** that survive `docker compose down`/rebuild.
- **caddy_data** holds issued certs (persist to avoid Let's Encrypt rate limits).
- **Nightly (02:00 IST):** `backup.sh` runs `pg_dump -Fc` + bundles media → **restic** → off-site (B2/R2), retention **7 daily / 4 weekly / 6 monthly**, weekly `restic check`. **RPO ≈ 24h.**
- **DR pair:** the off-site restic repo **+** the `.env` copy in a password manager = everything needed to rebuild on a fresh VPS ([Ch40](40_Disaster_Recovery.md)).

## 8. Config flow (where a value travels)
```
.env (host, 0600)  ──env_file──►  app container env  ──►  config.settings.production
     │                                                     (DATABASE_URL, SECRET_KEY,
     │                                                      ALLOWED_HOSTS, REDIS_URL…)
     └──environment: DOMAIN──►  caddy  ──►  {$DOMAIN} in Caddyfile
     └──POSTGRES_*──►  db container init
```

## 9. Failure modes → what recovers each
| Failure | Effect | Recovery |
|---|---|---|
| A gunicorn worker crashes | one request fails | master respawns worker ([Ch09](09_Processes_and_Services.md)) |
| `app` container crashes | brief 502s | `restart: unless-stopped` |
| VPS reboots | all down briefly | systemd starts docker → restart policy brings all back ([Ch10](10_Systemd.md)) |
| Postgres down | app 500/health-wait | restart policy; data safe in pgdata |
| Cert renewal fails | HTTPS errors near expiry | keep :80 open; Caddy retries; monitor expiry ([Ch12](12_Caddy.md),[Ch30](30_Monitoring.md)) |
| Disk full | writes fail (DB/logs) | prune images/logs; alert on disk ([Ch06](06_Linux_Basics.md)) |
| VPS/disk destroyed | total loss | rebuild VPS + `restic restore` + `.env` ([Ch40](40_Disaster_Recovery.md)) |
| Bad deploy | app broken | `deploy.sh` pre-dump + rollback to prior image/commit ([Ch33](33_CI_CD.md)) |

## 10. Scaling path (don't pre-scale — trigger on measured pain) ([Ch41](41_Scaling.md))
```
NOW: 1 VPS, all-in-one (fits a factory's load)
 └► bump VPS RAM/CPU + more gunicorn workers        (RAM/CPU pressure)
   └► split managed Postgres off the box            (DB is the bottleneck / want HA backups)
     └► N app replicas behind Caddy load-balancer    (app CPU-bound / need zero-downtime)
       └► add Redis for shared cache/sessions, CDN   (global users / cache pressure)
         └► (only at real scale) Kubernetes           (many services, big team)
```

## 11. Why this architecture (decision log)
- **Single VPS + Docker Compose + Caddy**, not PaaS/serverless/K8s: cheapest (~$6/mo or $0 free-tier), full control, maximal learning, and it matches the app's steady modest load. Serverless (Cloud Run) would need stateless rework (`$PORT`, S3 media); K8s is overkill. See [00A](00A_Where_To_Deploy_Hosting_Options.md)/[00B](00B_Deployment_Costs_And_Free_Alternatives.md).
- **Caddy over Nginx**: automatic, auto-renewing HTTPS + a 3-line config = fewer footguns ([Ch13](13_Nginx_Comparison.md)).
- **Self-hosted Postgres/Redis in containers**, not managed: $0 at this scale; managed earns its cost only at HA/scale.
- **restic off-site backups**: the one non-negotiable spend (pennies) — a single-box architecture MUST have off-site copies.
- **Exact-pinned images + non-root + fail-fast config**: reproducible, least-privilege, never-half-up (owner rules).

## 12. The 10-second recall
*Internet → Caddy(TLS) → Gunicorn(3) → Django → Postgres + Redis; five containers, one VPS, `.env` secrets, nightly off-site backups, everything auto-restarts.*

---

## Where to go next
- Learn each box: follow the chapter links above, in order from [00](00_COURSE_OVERVIEW.md).
- Do the real thing: [36 — My ERP Deployment](36_My_ERP_Deployment.md) (full command-by-command deploy).
- Keep it alive: [30 Monitoring](30_Monitoring.md) · [28 Backups](28_Backups.md) · [40 Disaster Recovery](40_Disaster_Recovery.md) · [42 Final Playbook](42_Final_Playbook.md).
