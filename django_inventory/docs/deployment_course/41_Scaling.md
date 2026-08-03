---
id: deploy-course-41-scaling
type: lesson
status: active
owner: handwritten
scope: deployment, operations — this ERP shipped to a VPS
anchors: docker-compose.yml, deploy/entrypoint.sh, deploy/Caddyfile, deploy/backup.sh
verified: 2026-08-01
---

# 41 — Scaling

> Part of [Deployment Course](00_COURSE_OVERVIEW.md). Prev: [40 — Disaster Recovery](40_Disaster_Recovery.md). Next: [42 — Final Deployment Playbook](42_Final_Playbook.md).

# Learning Objectives
By the end of this chapter you can:
- resist scaling before you need it
- identify the real bottleneck with measurements
- name the ordered steps this project would take
- explain why one VPS is the right answer today

# Purpose
To know **when** and **how** to make the stack handle more load — and, just as important, when *not* to. Scaling is a path you walk only when the numbers demand it. This chapter maps the path from my single-VPS stack to a larger one, in the order the bottlenecks actually appear.

# The Problem
Two opposite mistakes: scaling **too early** (paying for complexity — Kubernetes, replicas, sharding — before you have the load, which slows you down and adds failure modes), and scaling **too late** (users hitting timeouts because you didn't see the ceiling coming). The cure is to *measure*, know the bottleneck order, and take the smallest next step when a real signal says so.

# Theory (from zero)

### Vertical vs horizontal
- **Vertical (scale up)** — a bigger box (more RAM/CPU). Simplest: no architecture change, just resize the VPS. First resort. Ceiling: one machine's max + a single point of failure.
- **Horizontal (scale out)** — more boxes/containers behind a load balancer. Higher ceiling + redundancy, but needs statelessness, a shared DB/cache/session store, and shared media. Second resort.

### The rule: measure before you scale
Scale in response to the **golden signals** trending badly ([Ch 30](30_Monitoring.md)) — rising latency, CPU/RAM saturation, DB connections near the limit — not to a hunch. "It feels slow" → find *which* resource is the bottleneck first.

### The bottleneck order (where it actually breaks, in sequence)
1. **App CPU/RAM (Gunicorn workers)** — the usual first ceiling. Tune workers, then add RAM (vertical), then add app instances (horizontal).
2. **Database** — usually the real long-term bottleneck (one writer). Add indexes, connection pooling (**PgBouncer**), read replicas, caching — before sharding.
3. **Connections** — many workers × persistent connections exhaust Postgres `max_connections` → pool with PgBouncer ([Ch 21](21_PostgreSQL.md)).
4. **Static/media** — offload static + media to a **CDN / object storage** (removes load from the app) ([Ch 25](25_Static_vs_Media.md)/[Ch 26](26_collectstatic.md)).
5. **Cache** — use Redis more (cache expensive queries/pages) to take pressure off the DB ([Ch 22](22_Redis.md)).

### Statelessness is the prerequisite for horizontal
You can only run *N* app instances if a request can hit *any* of them. That needs: sessions in a shared store (DB/Redis, not local memory), media in shared storage (object store, not a local volume), no in-process state. My app is close to this (Redis cache, stateless workers) — the main change for scale-out is media → object storage.

### Tuning knobs before new machines (cheap wins first)
- **Gunicorn workers**: rule of thumb `2×CPU + 1` (sync); tune to RAM. `--max-requests` recycles workers to bound memory leaks ([Ch 14](14_Gunicorn.md)).
- **DB**: indexes on hot queries, `select_related`/`prefetch_related`, pooling.
- **Caching**: cache heavy reads in Redis with TTLs.
- **Async/queues**: move slow work (emails, reports, exports) off the request into a task queue (Celery/RQ + Redis) so web workers stay free.

### Match the tool to the scale (don't cargo-cult)
One factory on one VPS does **not** need Kubernetes, microservices, or multi-region. The single-VPS Compose stack is the *correct* architecture for the current load; scaling is a known path, not a current task. Add complexity only when a measured ceiling forces it.

> 💡 **Samjho aise:** Scaling ki seedhi: pehle **kaam kam karo** (N+1 hatao, index lagao) → phir **badi machine** → phir connection pooling → phir padhne ke liye copy (replica) → phir table baanto. 90% log pehli seedhi pe hi ruk jaate hain, kyunki asli dikkat wahin thi. Sidha "sharding chahiye" bolna jaldi-baazi hai.

# Real World Example (My ERP)
- **Current = single VPS, and that's right:** one factory, users in one region, one Compose stack (Caddy + 3 Gunicorn sync workers + Postgres + Redis + backup) on 2–4 GB. Load is modest; the architecture fits. No premature scaling.
- **The next steps, in order, when signals demand:**
  1. **Vertical first** — resize the VPS (4→8 GB) and bump Gunicorn workers; zero architecture change. Buys a lot of headroom cheaply.
  2. **DB hygiene** — indexes on hot queries, `select_related`/`prefetch_related`, then **PgBouncer** when workers×`conn_max_age` pressure `max_connections` ([Ch 21](21_PostgreSQL.md)). Managed Postgres (DO/RDS) with a read replica if reads dominate.
  3. **Media → object storage** — move the `media` volume to S3/Spaces via `django-storages` + CDN; static (already hashed/immutable) to the same CDN ([Ch 25](25_Static_vs_Media.md)). This is the key change that unlocks horizontal.
  4. **Horizontal app** — run multiple `app` containers (or hosts) behind Caddy (it load-balances `reverse_proxy` to multiple upstreams); sessions already shareable via Redis. Caddy stays the single TLS terminator.
  5. **Queue** — Celery/RQ on Redis for reports/exports/emails so web workers aren't blocked (Redis already in the stack, [Ch 22](22_Redis.md)).
- **Statelessness status:** app workers are stateless, cache/rate-limiter already in Redis; the one thing blocking scale-out today is media-on-a-local-volume — hence step 3 precedes step 4.
- **Honest scope:** none of this is built or needed now; it's the documented growth path (aligned with ADR-0010 growth/identity). Premature build = wasted effort + new failure modes.

# Visual Diagram
```
  NOW (correct for the load):  Caddy → app(gunicorn ×3) → Postgres + Redis   [1 VPS, 2-4GB]
        │  measure golden signals (latency · CPU/RAM · DB conns) — scale ONLY on real signal
        ▼  bottleneck order:
  ① APP CPU/RAM → tune workers → bigger VPS (VERTICAL, first) ─────────── cheapest
  ② DB          → indexes · select_related · PgBouncer · read replica ── usual long-term ceiling
  ③ CONNECTIONS → PgBouncer pools workers×conns under max_connections
  ④ STATIC/MEDIA→ CDN + object storage (media off local volume) ──────── UNLOCKS horizontal
  ⑤ HORIZONTAL  → Caddy load-balances → app ×N (stateless; sessions/cache in Redis)
  ⑥ QUEUE       → Celery/RQ on Redis for slow work (reports/emails) off the request
  ⚠ don't scale early: 1 factory ≠ Kubernetes. Add complexity only when a ceiling is MEASURED.
```

# Practical — measure, then tune
```bash
# Where's the ceiling? (measure before scaling)
docker stats --no-stream                         # per-container CPU/RAM — is app or db saturated?
docker compose exec db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c \
  "SELECT count(*), (SELECT setting::int FROM pg_settings WHERE name='max_connections') FROM pg_stat_activity;"  # conn headroom
```
```bash
# Find slow queries to index (the cheapest DB win)
docker compose exec db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c \
  "SELECT query, mean_exec_time, calls FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;"  # needs pg_stat_statements
```
```bash
# Cheap vertical wins first: resize VPS, then bump workers (Ch14)
# gunicorn ... --workers $((2*$(nproc)+1)) --max-requests 1000 --max-requests-jitter 100
```

# Production Walkthrough
- Today: **one VPS, five containers, 3 Gunicorn workers.** For one factory with tens of concurrent users that is not a compromise; it is correct (ch 36).
- The ordered path if load ever arrives: **measure** → fix queries and add indexes → cache the expensive aggregates (ch 22) → increase workers within CPU limits (ch 14) → bigger VPS (vertical) → separate the database → only then multiple app servers.
- Almost every real slowness in a Django ERP is a missing index or an N+1 query, not a shortage of servers.
- Note this project's own constraint: money paths use advisory locks, so more workers do not multiply throughput on settlement — that path is intentionally serialised.

# Debugging Guide
1. **Slow requests** — count queries first. N+1 is the default answer (sql_course ch 12).
2. **CPU pinned** — Python work; profile the view before adding workers.
3. **"Too many connections"** — workers × threads exceeded `max_connections` (ch 21). Scaling workers has a database cost.
4. **Slow only under concurrency** — a lock, not capacity.
5. **Memory climbing** — a leak; more RAM postpones it, it does not fix it.

# Performance Notes
- Indexes: milliseconds of work for orders-of-magnitude gains.
- Caching an aggregate beats caching a row you already had.
- Vertical scaling is boring, cheap and immediate — prefer it far longer than instinct suggests.
- Horizontal scaling introduces shared-session, shared-media and shared-lock problems; each is real work.

# Security Considerations
- Every added component is new attack surface (load balancer, replica, object store).
- Shared sessions across app servers need a shared store — usually Redis, which then holds security-relevant state (ch 22).
- More servers mean more places for secrets to live; distribution is a leak risk.
- Complexity is itself a security cost for a solo maintainer.

# Architecture Decisions
- **Scale up before out**, because one machine is dramatically simpler to secure and reason about.
- **Fix the query before buying the server** — the cheapest scaling is deleting work.
- **Serialised money paths accepted**, because correctness outranks throughput on settlement.
- **No premature distribution**: the current design is deliberately sized to one factory.

# Best Practices
- Never scale without a measurement that names the bottleneck.
- Add an index and re-measure before touching infrastructure.
- Know your worker-to-connection arithmetic before raising worker counts.
- Write down what "too slow" means in numbers, before you start.

# Beginner Mistakes
- **Scaling on a hunch** → wasted money/complexity. Measure the golden signals first.
- **Reaching for Kubernetes/microservices at one-factory scale** → huge complexity, new failure modes, slower iteration. Vertical + Compose is correct here.
- **Adding app instances while media is on a local volume** → instances can't share uploads. Object storage first (step 3 before 4).
- **Ignoring the DB** → it's usually the real ceiling. Indexes + pooling beat more app boxes.
- **Too many Gunicorn workers for the RAM** → OOM, not more throughput ([Ch 14](14_Gunicorn.md)). Tune to memory.
- **Not pooling connections** → workers×conns exhaust Postgres. PgBouncer ([Ch 21](21_PostgreSQL.md)).
- **Doing slow work in the request** → blocks web workers. Move to a queue.

# Interview Questions
- **Junior:** "Vertical vs horizontal scaling?" — Vertical = a bigger machine (simplest, no architecture change). Horizontal = more machines/instances behind a load balancer (higher ceiling + redundancy, but needs statelessness + shared DB/cache/media).

- **Mid:** "What do you scale first and how do you decide?" — Measure the golden signals to find the bottleneck. Usually app CPU/RAM first — tune Gunicorn workers, then go vertical (bigger VPS). Don't scale on a hunch; scale on a measured ceiling.

- **Senior:** "What's the prerequisite for running multiple app instances here, and what's the bottleneck order?" — Statelessness: shared sessions/cache (already Redis) and shared media — so today the blocker is media on a local volume, which must move to object storage before scale-out. Bottleneck order: app CPU/RAM → database (indexes, pooling, replicas) → connections (PgBouncer) → static/media (CDN) → then horizontal app instances behind Caddy, plus a queue for slow work.

- **Staff:** "Lay out the scaling roadmap for this ERP and defend not doing it now." — Now, a single-VPS Compose stack is correct: one factory, one region, modest load — added distributed-systems complexity would only add failure modes and slow iteration. The roadmap, driven strictly by measured signals: (1) vertical resize + worker tuning (cheap, no arch change); (2) DB — indexes, query tuning, PgBouncer, then managed Postgres + read replica; (3) media/static → object storage + CDN (also improves DR and latency); (4) horizontal app instances behind Caddy's load-balancing (statelessness already mostly satisfied via Redis); (5) a task queue on the existing Redis for reports/exports. Each step is taken only when a golden signal crosses a threshold, keeping cost and complexity proportional to real load. The invariant: scale in response to measurement, take the smallest next step, and never adopt an architecture the load doesn't justify.

### Why interviewers ask these — and the answer that separates levels

| Testing for | Weak answer | What lands |
|---|---|---|
| Do you scale on measurement or on instinct? | "Traffic is growing, so we need more servers." | **Measure the bottleneck first.** Order: fix queries/indexes → cache aggregates → tune workers within RAM → **bigger VPS** → split the DB → multiple app servers. Almost every "we need to scale" in a Django ERP is **one missing index or an N+1**. |
| Do you know the prerequisite for multiple app instances? | "Add a load balancer and run two containers." | **Statelessness.** Sessions/cache are already shared via Redis, so **the blocker today is media on a local volume** — it must move to object storage first. Adding instances before that gives you users whose uploads exist on only one of two servers. |
| Do you know worker scaling has a database cost? | "More workers means more throughput." | **Workers × threads must respect `max_connections`** (ch 21), and each worker holds a full copy of the app in RAM — so the ceiling is memory and connections, not ambition. Scaling workers is how people take the database down while trying to serve more traffic. |
| Can you defend NOT scaling? | "We should build for scale early." | One factory, one region, modest load: **a single-VPS Compose stack is correct**, and distributed complexity would only add failure modes for a solo maintainer. The mature answer is **a documented scale path that is deliberately not built yet**. |

**The killer follow-up:** *"Money paths use advisory locks. What does that mean for scaling?"* — settlement is **serialised on purpose**, so more workers will not make it faster. **Correctness outranks throughput there** — and knowing which parts of your system refuse to parallelise, and why, is the difference between scaling and hoping.

# Revision Notes
- Today: **1 VPS, 5 containers, 3 workers** — correct for one factory, not a compromise.
- Order: **measure → indexes/N+1 → cache aggregates → more workers (within CPU) → bigger VPS → split DB → multiple app servers.**
- Most Django slowness = missing index or N+1, not servers.
- Workers × threads must respect `max_connections` — scaling workers costs DB connections.
- Money paths use advisory locks: **serialised on purpose**, so more workers will not speed settlement.

# Cheat Sheet
- **Measure first** (golden signals: latency, CPU/RAM, DB conns). Scale on signal, not hunch.
- **Vertical before horizontal** (bigger box + worker tuning = cheapest, no arch change).
- **Bottleneck order:** app CPU/RAM → **DB** (indexes/pooling/replica) → connections (**PgBouncer**) → static/media (**CDN/object store**) → horizontal app → queue.
- **Statelessness unlocks horizontal**: sessions/cache in Redis (have) + media in object storage (the blocker to fix).
- **Caddy load-balances** to multiple app upstreams; it stays the single TLS terminator.
- **Don't over-engineer:** 1 factory ≠ Kubernetes. Single-VPS Compose is correct until a measured ceiling says otherwise.

# My ERP Section
| Step | In my ERP (growth path, not built) |
|---|---|
| Now | 1 VPS: Caddy + gunicorn×3 + Postgres + Redis + backup (correct for load) |
| ① Vertical | resize VPS + bump workers |
| ② DB | indexes, `select_related`, PgBouncer, read replica |
| ③ Media | `media` → S3/Spaces (`django-storages`) + CDN |
| ④ Horizontal | app ×N behind Caddy; Redis-shared sessions/cache |
| ⑤ Queue | Celery/RQ on existing Redis (reports/exports/email) |
| Blocker to scale-out | media on local volume → object storage first |
| Policy | scale on measured signal; ADR-0010 growth path |

# Practice Tasks
1. **Read the code:** find the worker count and thread setting, and compute the connection demand.
2. **Debug:** find one N+1 query in this project and fix it with `select_related`/`prefetch_related`. Measure both times.
3. **Design:** define "too slow" for a worker reporting production, in milliseconds.
4. **Architecture:** argue why serialised settlement is acceptable, and what would have to change to parallelise it safely.

# Homework
1. `docker stats` + the connection-count query — is your current ceiling app or DB? What's the headroom?
2. What single change must happen before you can run two `app` containers, and why? (Hint: where do uploads live?)
3. Compute a Gunicorn worker count for a 2-CPU box. What symptom tells you it's too many?
4. Explain the bottleneck order. Why is the database usually the real long-term ceiling, not the app?
5. Argue *against* adopting Kubernetes for this ERP today. When would that argument flip?

---

# Further Reading & Live Resources
- Gunicorn — *How many workers? / worker tuning*: https://docs.gunicorn.org/en/stable/design.html#how-many-workers
- PgBouncer (connection pooling): https://www.pgbouncer.org/ · Django + PgBouncer notes: https://docs.djangoproject.com/en/5.0/ref/databases/#transaction-pooling-server-side-cursors
- Django docs — *Database optimization* (`select_related`/`prefetch_related`, indexes): https://docs.djangoproject.com/en/5.0/topics/db/optimization/
- Caddy — *reverse_proxy load balancing* (multiple upstreams): https://caddyserver.com/docs/caddyfile/directives/reverse_proxy#load-balancing
- Celery (task queue on Redis): https://docs.celeryq.dev/en/stable/ · django-storages (media → S3): https://django-storages.readthedocs.io/
- Google SRE Workbook — *Managing load*: https://sre.google/workbook/managing-load/
