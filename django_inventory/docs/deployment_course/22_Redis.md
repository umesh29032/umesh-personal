# 22 — Redis

> Part of [Deployment Course](00_COURSE_OVERVIEW.md). Prev: [21 — PostgreSQL](21_PostgreSQL.md). Next: [23 — Environment Variables](23_Environment_Variables.md).

# Purpose
To understand the **in-memory data store** in my stack — Redis — what it does for the ERP (cache + the login **rate-limiter**), why the app **refuses to boot without it**, and why it (unlike Postgres) has **no volume**. Redis is small in my stack but load-bearing for security.

# The Problem
Some data must be **fast** and **shared across all workers**: a cache to avoid recomputing, and — critically — the **login rate-limiter counters** (how many failed attempts from this IP/email). Postgres could store these but it's slower and it's wasteful to hammer the money DB with ephemeral counters. Redis is the purpose-built fast, shared, atomic store for exactly this.

# Theory (from zero)

### What Redis is
**Redis** = an **in-memory** key-value store: data lives in RAM → microsecond reads/writes. It supports strings, counters, hashes, lists, sets, TTLs (auto-expiry), and **atomic operations** (e.g. `INCR` a counter with no race) — perfect for caches, sessions, rate-limit counters, and queues. Because it's in RAM, it's fast but **volatile** (data can be lost on restart unless persistence is configured).

### Redis's jobs in a Django deploy
1. **Cache backend** — Django's cache framework stores computed values with TTLs (`cache.get/set`), shared by all workers.
2. **Session store** (optional) — sessions in Redis instead of the DB (fast, shared).
3. **Rate limiting** — atomic counters (`INCR` + TTL) to throttle abusive clients; your login throttle uses the cache (Redis) to count failed attempts per IP/email and lock out brute-force ([accounts throttle], RC1 security).
4. **Task queue broker** — Celery/RQ use Redis (not used here today).

### Why my app FAIL-FASTS without Redis (a deliberate choice)
My `production.py` sets the cache to `RedisCache` with `LOCATION = config('REDIS_URL')` — **no default**. If `REDIS_URL` is unset (or Redis is down at boot), the app **refuses to start**. Why on purpose? Because the **login rate-limiter lives in the cache**. If Redis silently vanished and the app fell back to a dummy/local cache, the rate-limiter would be **silently bypassed** → brute-force protection gone with no alarm. Better to **fail loudly** than to run insecure. The entrypoint wait-loop also pings Redis before starting ([Ch 09](09_Processes_and_Services.md)).

### Why Redis has NO volume in my stack (and that's correct)
In `docker-compose.yml`, `redis` has **no volume** — its data is **ephemeral**. That's intentional:
- The **cache** is rebuildable (a cold cache just recomputes; no data lost).
- The **rate-limit counters** resetting on a Redis restart means, at worst, an attacker gets a fresh attempt window right after a restart — a brief, acceptable weakening, not a data-loss event.
- None of Redis's contents are *the business* (that's Postgres). So persisting Redis buys little and adds complexity. Contrast: `pgdata` MUST persist ([Ch 20](20_Docker_Volumes.md)); Redis need not.
(If Redis later held Celery task state you cared about, you'd enable persistence + a volume.)

### Health
The compose `redis` healthcheck runs `redis-cli ping` (expects `PONG`) every 5s; `app` waits `service_healthy` before starting ([Ch 18](18_Docker_Compose.md)).

# Real World Example (My ERP)
- **Service:** `redis` = `redis:7.4.2-alpine` (pinned), `restart: unless-stopped`, **no volume**, healthcheck `redis-cli ping` ([Ch 18](18_Docker_Compose.md)).
- **Connect:** `.env` `REDIS_URL=redis://redis:6379/0` (host `redis` = service name, [Ch 19](19_Docker_Networking.md), db index 0). `production.py` uses it for `CACHES` (RedisCache), **no default → boot fails if missing** (RC1 verified — fail-fast).
- **Security role:** the accounts login throttle stores per-IP/per-email failed-attempt counters in this cache; that's the brute-force lockout ([Ch 07](07_SSH.md) is server SSH; this is *app* login). Losing Redis would disable that silently — hence fail-fast.
- **Not public:** no `ports:` → private ([Ch 05](05_IP_Address_and_Ports.md)); admin via `docker compose exec` or SSH tunnel.
- **Ephemeral by design:** a `docker compose restart redis` clears the cache (recomputed on demand) and resets throttle counters (brief, acceptable) — no business data lost.

# Visual Diagram
```
  3 Gunicorn workers ── REDIS_URL=redis://redis:6379/0 ──► redis (7.4.2, in-memory)
        (Django CACHES = RedisCache)                          │ NO volume (ephemeral)
   uses:  cache (TTL values)  ·  login rate-limiter counters (INCR + expiry) ★security
   health: redis-cli ping → PONG → app waits service_healthy
   FAIL-FAST: REDIS_URL has NO default → app refuses to boot without Redis
              (so the rate-limiter is NEVER silently bypassed)
   private (no ports)  |  restart clears cache + counters (acceptable; not "the business")
```

# Practical — how to inspect it
```bash
docker compose exec redis redis-cli ping            # PONG = healthy
docker compose exec app python -c "import os;print(os.environ['REDIS_URL'])"  # redis://redis:6379/0
```
```bash
# Prove Django uses it as the cache
docker compose exec app python -c "from django.core.cache import cache; cache.set('k','v',30); print(cache.get('k'))"   # -> v
docker compose exec redis redis-cli KEYS '*'        # see cache/throttle keys
docker compose exec redis redis-cli INFO memory | grep used_memory_human   # RAM used
```
```bash
# Prove fail-fast (on a TEST stack): stop redis, restart app → app should refuse/err at boot
docker compose stop redis
docker compose restart app
docker compose logs app | tail            # boot fails / wait-loop times out (by design)
docker compose start redis                # bring it back
```

# Beginner Mistakes
- **Adding a default for `REDIS_URL`** ("so it doesn't crash") → defeats the fail-fast; the app could run with the rate-limiter silently off. Keep it no-default in prod.
- **Persisting Redis + treating it like a database** → it's a cache/counter store here; the business is Postgres. Don't put durable truth in Redis without deliberate persistence.
- **Publishing 6379** → an open Redis is a classic breach (attackers scan for it). Keep it private ([Ch 05](05_IP_Address_and_Ports.md)).
- **Storing huge/unbounded data without TTLs** → Redis is RAM; no expiry → memory fills → eviction/OOM. Use TTLs.
- **Assuming cache = source of truth** → cache can be cold/cleared anytime; always be able to recompute from Postgres.
- **Wrong host** (`localhost` vs `redis`) inside the container → connection refused ([Ch 19](19_Docker_Networking.md)).

# Interview Questions
**Junior — "What is Redis and what's it used for here?"** An in-memory key-value store used as the Django cache and, importantly, to hold the login rate-limiter's per-IP/email counters — fast, shared across workers.

**Mid — "Why does the app refuse to boot without Redis?"** Because the login rate-limiter's counters live in the Redis-backed cache; if Redis were missing and the app silently fell back to a local/dummy cache, brute-force protection would be off with no warning. Failing fast forces the operator to fix it rather than run insecure.

**Senior — "Why does Redis have no volume while Postgres does?"** Redis holds rebuildable cache values and ephemeral rate-limit counters — not the business data. A restart cold-caches (recomputed on demand) and resets counters (a brief, acceptable window), so persistence buys little. Postgres holds the money/truth and MUST persist via `pgdata`. Match durability to data value.

**Staff — "What are the security + availability implications of Redis in this stack, and how would you harden/scale it?"** Security: Redis is the enforcement point for brute-force protection, so its availability is a security control (hence fail-fast + healthcheck); keep it private (no published port), and if ever exposed, require auth + TLS. Availability: a single ephemeral instance is fine at this scale; the risk is a restart briefly resetting counters. To scale/harden: enable AUTH, bind to the private net only, add `maxmemory` + an eviction policy to bound RAM, and (if it later brokers Celery or holds sessions you value) enable persistence (AOF) + a volume, or managed Redis with HA. Monitor `used_memory` and evictions.

# Cheat Sheet
- **Redis = in-memory key-value store:** cache + **login rate-limiter counters** (atomic INCR + TTL). Fast, shared across workers, volatile.
- **`REDIS_URL=redis://redis:6379/0`**, no default → **app fail-fasts without it** (so the rate-limiter can't be silently bypassed).
- **No volume = intentional:** cache/counters are not "the business" (Postgres is); restart clears them (acceptable).
- **Private** (no `ports:`); health `redis-cli ping`→PONG; app waits `service_healthy`.
- Use **TTLs**; never treat cache as source of truth; recompute from Postgres.
- Inspect: `redis-cli ping/KEYS/INFO memory`.

# My ERP Section
| Concept | In my ERP |
|---|---|
| Image | `redis:7.4.2-alpine` (pinned), no volume |
| Connect | `.env` `REDIS_URL=redis://redis:6379/0` |
| Role | Django `CACHES` (RedisCache) + login rate-limiter |
| Fail-fast | `config('REDIS_URL')` no default → boot fails if missing |
| Health | `redis-cli ping` (compose) + entrypoint ping |
| Persistence | none (ephemeral by design) |
| Public? | No `ports:` → private |

# Homework
1. `docker compose exec redis redis-cli ping` → PONG. What compose directive makes `app` wait for this?
2. Set + get a cache key via the app (command above). Then `redis-cli KEYS '*'` — see it. What happens to it after `docker compose restart redis`, and why is that OK?
3. In `production.py`, find the `CACHES`/`REDIS_URL` config. Why is there no default, and what security control depends on Redis being present?
4. Explain why Redis has no volume but Postgres must — in terms of "is this the business?"
5. Why is publishing port 6379 dangerous, and how would you inspect prod Redis safely instead?

---

## Further Reading & Live Resources
- Redis — *official docs* (data types, TTL, INCR): https://redis.io/docs/latest/
- Django docs — *Caching / Redis cache backend*: https://docs.djangoproject.com/en/5.0/topics/cache/#redis
- Redis official Docker image: https://hub.docker.com/_/redis
- Redis — *Try Redis* (free interactive tutorial): https://try.redis.io/
- OWASP — *Blocking brute-force attacks* (why rate-limiting matters): https://owasp.org/www-community/controls/Blocking_Brute_Force_Attacks
- Redis — *security* (never expose it open): https://redis.io/docs/latest/operate/oss_and_stack/management/security/
