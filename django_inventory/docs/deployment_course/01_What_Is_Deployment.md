---
id: deploy-course-01-what-is-deployment
type: lesson
status: active
owner: handwritten
scope: deployment, operations — this ERP shipped to a VPS
anchors: docker-compose.yml, deploy/entrypoint.sh, deploy/Caddyfile, deploy/backup.sh
verified: 2026-08-01
---

# 01 — What Is Deployment

> Part of [Deployment From Zero](00_COURSE_OVERVIEW.md). Next: [02 — How The Internet Works](02_How_The_Internet_Works.md).

# Learning Objectives
By the end of this chapter you can:
- say why `runserver` is unfit for production, naming four specific properties
- draw this project's five containers and what each one does
- name each component's failure mode without looking it up
- explain why web concurrency is mostly about *waiting*, not CPU

# Purpose
To understand what "deploying" actually means, and *why* a production setup looks so different from `python manage.py runserver`. Every later chapter (Caddy, Gunicorn, Docker, Postgres…) is a piece of the answer to this chapter's question. If this chapter clicks, the rest of the course is "filling in the boxes."

# The Problem
On my laptop, one command runs the ERP for exactly one person: me. Production is a different problem entirely — *strangers* (workers, managers, owner, finance) hitting it **at the same time**, over the **public internet**, expecting it to be **safe**, **fast**, and **up at 3am when I'm asleep**. Development optimizes for *my* speed of change. Production optimizes for *their* safety, uptime, and concurrency. Almost every confusing thing about deployment comes from that shift. Deployment is the work of crossing that gap.

# Theory (from zero)

> **New to all this?** Don't worry if the names below (Gunicorn, Caddy, Docker, Postgres…) mean nothing yet — **this chapter is the map, not the details.** Each later chapter teaches one box; here, just get the *shape*.

### What `runserver` actually is
When I run `python manage.py runserver`, Django starts a **tiny web server written in Python**, built into Django itself. Four properties define it:
1. **It's a teaching server** — correct, not fast (`wsgiref`).
2. **It binds to `127.0.0.1:8000`** — that address means "this machine only, nobody else." (Chapter 05 makes IPs rigorous.)
3. **It handles ~one request at a time** — single process, lightly threaded.
4. **It auto-reloads** on file save — lovely in dev, dangerous in prod.

Perfect for a developer. But look again: *every one of those four is wrong for production.*

### Why `runserver` cannot be production
- **Slow / not concurrent** — a manager allocating, three workers reporting, and an owner viewing a snapshot at once will queue behind each other; users see spinners.
- **Not hardened** — never security-reviewed for hostile internet traffic (slow clients, malformed requests).
- **localhost only** — nobody outside the machine can reach it.
- **`DEBUG=True` danger** — dev runs with `DEBUG=True`, which shows a full stack trace (your code, settings, data) to *anyone* who triggers an error → information leak. (My `production.py` sets `DEBUG=False`.)
- **No recovery** — nothing restarts it if it dies overnight.

### The three roles production needs (that `runserver` mashes into one)
1. **An application server** to run Django efficiently for many users, and restart itself → **Gunicorn**.
2. **A reverse proxy** to face the internet: encryption (HTTPS), static files, protection from slow/malicious clients → **Caddy**.
3. **Long-lived data services** the app talks to → **PostgreSQL** (data) + **Redis** (cache/sessions/rate-limit).

**Gunicorn** runs multiple copies of my app called **workers** (mine: 3). Three clerks at three windows — three requests truly in flight at once; if one is rendering a heavy page, the other two still serve worker phones. If a worker dies, Gunicorn restarts it (self-healing).

**Why not point the internet straight at Gunicorn?** Because Gunicorn is great at *running Python* and deliberately bad at the *public-facing* jobs: terminating HTTPS, serving static files without waking a Python worker, and surviving slow/malicious clients. A handful of clients each sending 1 byte/second (a "slowloris") would tie up all 3 workers and freeze the whole ERP — no skill required. So we put a specialist in front.

**A reverse proxy** sits between the internet and the app server. "Reverse" because it fronts *your server* (a normal/forward proxy fronts outgoing clients). It takes every public request, does TLS + static files + buffering + limits, and forwards the real app request to Gunicorn over a **private** connection. Gunicorn never talks to strangers.

**Caddy** is my reverse proxy. Its killer feature: **automatic HTTPS** — give it a domain, it fetches a free Let's Encrypt certificate, installs it, and **renews it forever**, no cron, no manual step. (Chapter 03 explains TLS; Chapter 12 walks my Caddyfile.)

### From my laptop to the internet — the whole arc (answering "how does my local code go live?")
Right now the ERP is just files on my laptop, reachable by nobody. Going "live on the internet" means making **five things** become true — that's *all* deployment is; the rest of this course is just *how* to do each one:
1. **Rent an always-on computer with a public address** — a **VPS**. *(A VPS is simply another computer: like my laptop but with no screen, always on, sitting in a data center, rented for a few dollars a month and controlled over the network. Renting computers like this is what "**the cloud**" means.)* → [Ch 06](06_Linux_Basics.md) / [00A](00A_Where_To_Deploy_Hosting_Options.md)
2. **Copy my project onto it** — my code doesn't teleport; I send it over the network with **git** (`git clone` / `git pull` *on the VPS*), the same tool I already use to save code. → [Ch 07](07_SSH.md) / [Ch 36](36_My_ERP_Deployment.md)
3. **Build + run it as a server** — package the code + Python + libraries into a **container** and start **Gunicorn** so it sits *listening* for requests (not `runserver`). → [Ch 16](16_Docker.md) / [Ch 14](14_Gunicorn.md)
4. **Point a name at it** — map my domain (`erp.example.com`) to the VPS's address via **DNS**, so people type a name, not a number. → [Ch 04](04_DNS_Domains.md)
5. **Open the door safely** — let the internet reach ports **80/443** (firewall), and Caddy adds HTTPS. → [Ch 05](05_IP_Address_and_Ports.md) / [Ch 12](12_Caddy.md)

The arc, in one line: **rent a box → git my code onto it → build → run → point a domain → open 80/443.** [Ch 36](36_My_ERP_Deployment.md) does all five for real, command by command; everything between here and there teaches one piece. (Chapter 02 covers the *other* direction — how a user's request travels *back* to reach a live server.)

> 💡 **Samjho aise:** Laptop pe `runserver` chalana **ghar ki rasoi** hai — ek aadmi ke liye khana banao, kaafi hai. Production ek **dhaba** hai: ek saath 50 log aayenge, khana garam chahiye, hygiene chahiye, aur raat 3 baje bhi shutter khula rehna chahiye. Isi liye dhabe mein alag chulha (Gunicorn), alag counter (Caddy), alag store (Postgres) hota hai — ek hi banda sab nahi kar sakta.

# Real World Example (My ERP)
The exact journey when a worker opens their phone:
1. Request hits **Caddy** on port 443 (HTTPS). Caddy decrypts it.
2. If it's a static file (CSS/JS), Caddy serves it itself, fast. If it's `/production/my-work/`, Caddy forwards it over the private Docker network to **Gunicorn** on port 8000.
3. Gunicorn hands it to one of its **3 workers**, running my Django app with `config.settings.production`.
4. Django reads/writes **PostgreSQL** (the allocation, the contribution, the settlement) and **Redis** (session, login rate-limiter), builds the response.
5. Response returns: Gunicorn → Caddy → re-encrypted → phone.

All four — Caddy, Gunicorn, Postgres, Redis — run as **Docker containers** wired by `docker-compose.yml` on **one rented Linux VPS**. Only Caddy is exposed to the internet; the rest are sealed on a private network. This is the "single-VPS Docker-Compose + Caddy" target named in `docs/RELEASE_CANDIDATE_CERTIFICATION_RC1.md`.

# Visual Diagram
```
Phone/Laptop ──HTTPS(443)──► CADDY ──HTTP(8000, private)──► GUNICORN (3 workers)
                             (TLS,                              │        │
                              static,                           ▼        ▼
                              limits)                       POSTGRES    REDIS

  runserver (dev)   =  one Python toy server, localhost, 1 user, auto-reload
  the above (prod)  =  proxy + app-server(×3 workers) + data services, on a VPS
```

# Practical — how to inspect it
Run these and read the output. (Full Linux/Docker command teaching is Chapters 06/16; here just enough to *see* the concepts.)

```bash
# On your LAPTOP — see the dev server vs a real app server
python config/manage.py runserver          # dev toy: note "development server", auto-reload
# Ctrl-C, then:
cd config && gunicorn config.wsgi --workers 3 --bind 127.0.0.1:8000
#   ^ production engine: no banner, no auto-reload, 3 worker processes
```
- `runserver` → Django's built-in dev server. `gunicorn config.wsgi` → the real WSGI server loading your app via `config/wsgi.py` (the "front door", Chapter 15).
- `--workers 3` → start 3 worker processes. `--bind 127.0.0.1:8000` → listen on localhost port 8000.

```bash
# On the VPS later — see the running production shape
docker compose ps        # lists containers: caddy, web(gunicorn), db, redis — each explained in Ch18
docker compose logs web  # gunicorn's own logs (worker boot, request lines)
```
- `docker compose ps` → shows each service, its state, and which ports are published. You should see **only Caddy** publishing 80/443 to the host; `web`/`db`/`redis` have no host ports (private).

# Production Walkthrough
The whole stack on one VPS, from `docker-compose.yml`:
- **Caddy** faces the internet: TLS (certificates fetched and renewed automatically), static files, request limits. If Caddy dies the site is down but the **data is safe**.
- **Gunicorn**, 3 workers, runs the Django app. A worker crash is auto-recovered; nobody notices.
- **Postgres 16** is the only irreplaceable component — hence backups (ch 28) and `RESTRICT` foreign keys.
- **Redis** for cache + login rate-limiting. The app **fails fast** if it is absent — a deliberate correctness choice so the rate limiter is never silently bypassed.
- **backup** container: nightly `pg_dump -Fc` + media → restic → off-site.
`deploy/entrypoint.sh` waits for healthy DB+Redis, then migrates, seeds, collects static, and only then starts serving — so the app never boots half-configured.

# Debugging Guide
"The site is down" — in the order that finds it fastest:
1. **Is it DNS, TLS, or the app?** `curl -I https://…` tells you which layer answered. No answer at all = network/Caddy; a 502 = Caddy is up but Gunicorn is not.
2. **`docker compose ps`** — which container is unhealthy or restarting?
3. **`docker compose logs --tail=50 web`** — the app's own words.
4. **Did the entrypoint finish?** A failed `migrate` stops the boot; the log says so explicitly.
5. **Data safe?** Postgres up but app down is a *deployment* incident. Postgres down is a *data* incident — different urgency (ch 40).

# Performance Notes
- Worker count ≠ core count. Web work is mostly **waiting** (on the DB, on slow clients), so workers are tuned for I/O, not CPU.
- The reverse proxy buffers slow clients so one bad connection cannot occupy a worker for seconds.
- `CONN_MAX_AGE = 600` avoids a fresh Postgres handshake per request.
- The first bottleneck in practice is almost never the server — it is query count (sql_course ch 16).

# Security Considerations
- **Only Caddy is exposed.** Postgres and Redis are reachable only on the private Docker network — never published to the internet.
- `DEBUG=False` in production is non-negotiable: `DEBUG=True` turns an error page into a schema-and-settings tour for an attacker.
- Secrets come from `.env`, which is never in git.
- TLS everywhere, because a login form over HTTP hands out passwords.

# Architecture Decisions
- **Single box, five containers** — cheapest and simplest that still keeps the internet away from the app and the data. Matched to a factory's steady, modest load.
- **Reverse proxy in front of the app server** — different jobs (public-facing hardening vs running Python), and the proxy shields the workers.
- **Fail fast on missing Redis** rather than degrade silently: a bypassed rate limiter is worse than an error.
- **One VPS, not Kubernetes** — deliberately. Complexity you cannot debug at 3am is not resilience.

# Best Practices
- Never run `runserver` in production, for any "temporary" reason.
- Keep the deploy reproducible: same image, same compose file, same entrypoint.
- Read the entrypoint once so you know the boot order by heart.
- Make every component either stateless-restartable or backed up — and know which each one is.

# Beginner Mistakes
- **Running `runserver` in production** "because it works." It works until strangers or a crawler arrive, then it serializes and falls over.
- **Exposing Gunicorn's port 8000 to the internet.** Skips every protection the proxy gives; slow clients can freeze it.
- **Setting `DEBUG=True` in production** to "see the error." Leaks `SECRET_KEY`, settings, and data; also disables `ALLOWED_HOSTS` protection. **Never.**
- **Thinking the DB/cache are "part of the app."** They're separate, long-lived services with their own lifecycle (Chapters 21–22).
- **One giant worker, or a hundred workers.** Workers cost RAM; the count is a real decision (Chapter 14).

# Interview Questions
- **Junior:** "Why can't you use `runserver` in production?" — 
It's a single-threaded dev server on localhost, not hardened, and runs with dev conveniences (auto-reload, and typically `DEBUG=True`) that are unsafe. Production needs concurrency, security, public reachability, and self-recovery — a real WSGI server (Gunicorn) behind a reverse proxy.

- **Mid:** "What's the difference between a WSGI server and a reverse proxy, and why both?" — 
The WSGI server (Gunicorn) *runs the Python app* and manages worker processes. The reverse proxy (Caddy) *faces the internet*: TLS termination, static-file serving, request buffering, limits, and protection from slow/malicious clients. Different jobs; the proxy shields the app server so one slow client can't starve all workers.

- **Senior:** "The site freezes under load but CPU is near-idle. Why?" — 
Workers are likely all blocked waiting (on the DB, on slow clients), not computing. Web concurrency is mostly about *waiting*, not CPU. Fixes: put a proxy in front to buffer slow clients, raise/adjust worker count or use threads/async for I/O-bound waits, and profile the slow DB queries. (This is why worker count ≠ core count.)

- **Staff:** "Design the smallest production topology for this ERP and justify each component's existence and failure mode." — 
Caddy (public, TLS+static+limits; if it dies, site is down but data safe) → Gunicorn N workers (app; a worker crash is auto-recovered) → Postgres (single source of truth; protect with backups + PROTECT FKs) → Redis (cache/rate-limit; app fail-fasts if absent, a deliberate correctness choice so the rate limiter is never silently bypassed). One VPS, one firewall, off-site backups. Justification: minimizes moving parts while keeping the internet away from the app + data, and every component is either stateless-restartable or backed up.

### Why interviewers ask these — and where candidates lose the point

| The question is really testing | Weak answer | What lands |
|---|---|---|
| *"Why not runserver?"* — do you know the difference between a dev convenience and a production contract? | "It's slow." | Name the **four** properties (single-threaded · localhost-only · dev conveniences like auto-reload/DEBUG · no self-recovery) and say why each is wrong for strangers hitting it at once. |
| *"WSGI server vs reverse proxy"* — can you separate responsibilities instead of listing tools? | "Nginx serves the site, Gunicorn runs Python." | **Different jobs**: Gunicorn runs the app and manages workers; the proxy faces the internet (TLS, static, buffering, limits) and *shields* workers so one slow client cannot starve them. |
| *"Idle CPU but frozen site"* — do you understand that web concurrency is mostly *waiting*? | "Add more CPU / more workers." | Workers are **blocked**, not computing — usually DB waits or slow clients. Buffer at the proxy, tune workers for I/O, profile the slow queries. Explains why worker count ≠ core count. |
| *"Design the smallest topology"* — can you justify each box **and its failure mode**? | Lists components. | For each box: what it does **and what breaks if it dies** (Caddy down = site down, data safe · worker crash = auto-restarted · Postgres = the only irreplaceable one, hence backups). |

**The meta-signal:** juniors name tools, seniors name **responsibilities and failure modes**. Answer in those terms and the level takes care of itself.

**The killer follow-up:** *"So what breaks if the database disappears right now?"* — every other component is replaceable from git in minutes; **Postgres is the only irreplaceable box**, which is why backups (ch 28) and not redundancy are the answer. Candidates who list all five services as equally critical have not thought about what is actually at risk.
# Revision Notes
- `runserver` = dev only: single-threaded, localhost, auto-reload, no recovery.
- Production shape: **Caddy → Gunicorn → Postgres (+ Redis) + nightly backup**.
- Proxy faces the internet; app server runs Python. Different jobs.
- Concurrency is about **waiting**, so worker count ≠ core count.
- Only Postgres is irreplaceable — everything else restarts.

# Cheat Sheet
- **Deployment =** turning "runs for me on localhost" into "runs safely for many, over the internet, unattended."
- **Flow to memorize:** Internet → **Caddy** (TLS/static/limits) → **Gunicorn** (3 workers) → **Django** → **Postgres + Redis**, all containers on one VPS.
- **runserver = dev toy** (localhost, 1-user, auto-reload, often DEBUG). **Never in prod.**
- **Gunicorn** runs + self-heals your app. **Caddy** faces the internet. **Never expose Gunicorn directly.**
- Key files/commands: `config/wsgi.py`, `gunicorn config.wsgi --workers 3`, `docker compose ps`.
- Remember: production's job is to survive *thousands of impatient, occasionally hostile* users at once — not one polite you.

# My ERP Section
| Question | Answer for my ERP |
|---|---|
| Which app server? | Gunicorn, 3 sync workers (`deploy/entrypoint.sh`) |
| Which proxy? | Caddy (`deploy/Caddyfile`) |
| Which settings in prod? | `config.settings.production` (set via Dockerfile `ENV`) |
| Which WSGI entry? | `config/config/wsgi.py` |
| Data services? | `db` (PostgreSQL) + `redis` containers |
| Orchestrated by? | `docker-compose.yml` |
| Exposed to internet? | Only Caddy (80/443); gunicorn/db/redis are private |
| DEBUG in prod? | `False` (`config/config/settings/production.py`) |

# Practice Tasks
1. **Read the code:** open `docker-compose.yml` and list all five services with one sentence each on what breaks if it stops.
2. **Debug:** on your laptop, run `runserver` and then `gunicorn config.wsgi --workers 3`. Note every visible difference (banner, reload, process count).
3. **Design:** the owner asks "can we skip Caddy and expose Gunicorn directly?" Write the three-sentence refusal.
4. **Architecture:** argue for and against adding a second VPS. What does it buy at this factory's scale, and what does it cost in complexity?

# Homework
1. Run `runserver`, then `gunicorn config.wsgi --workers 3 --bind 127.0.0.1:8000`. Write down 3 differences you observe.
2. From a second device on your wifi, try to reach `http://<laptop-ip>:8000/` after `runserver 127.0.0.1:8000` vs after `runserver 0.0.0.0:8000`. Explain why one is reachable and one isn't. (Answer lands in [Ch 05](05_IP_Address_and_Ports.md).)
3. Draw the request-journey diagram from memory. If you can't, re-read *Theory → the three roles*.
4. Open `config/config/settings/production.py`, find `DEBUG`, and explain out loud why a stack-trace page is safe in dev and dangerous in prod.
5. (After the VPS exists) run `docker compose ps` and confirm only Caddy publishes ports to the host.

---

# Further Reading & Live Resources
- Django docs — *Deploying Django* (the official overview): https://docs.djangoproject.com/en/5.0/howto/deployment/
- Django docs — *Deployment checklist* (bookmark this — [Ch 35](35_Deployment_Checklist.md) leans on it): https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/
- Gunicorn — *official docs* (workers, WSGI, settings): https://docs.gunicorn.org/en/stable/
- Django docs — *How to use Django with Gunicorn*: https://docs.djangoproject.com/en/5.0/howto/deployment/wsgi/gunicorn/
- DigitalOcean — *Set up Django with Postgres, Gunicorn, Nginx* (classic end-to-end, concepts map 1:1 to Caddy): https://www.digitalocean.com/community/tutorials/how-to-set-up-django-with-postgres-nginx-and-gunicorn-on-ubuntu-22-04
- *The Twelve-Factor App* (why config/env/processes are split the way they are — read III, X, XI): https://12factor.net/
- MDN — *What is a web server?*: https://developer.mozilla.org/en-US/docs/Learn/Common_questions/Web_mechanics/What_is_a_web_server
