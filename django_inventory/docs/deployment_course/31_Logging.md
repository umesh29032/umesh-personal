# 31 — Logging

> Part of [Deployment Course](00_COURSE_OVERVIEW.md). Prev: [30 — Monitoring & Health Checks](30_Monitoring.md). Next: [32 — Error Tracking with Sentry](32_Sentry.md).

# Purpose
To understand how a production app tells you **what it's doing and what went wrong** — logs. Where they go in a containerized stack (stdout, not files), how to read them, why my logs carry a **request-id + actor**, and the difference between logging (the ongoing story) and error tracking (the alarm, [Ch 32](32_Sentry.md)).

# The Problem
In dev you read the `runserver` console. In production there's no console you're watching — the app runs detached in a container ([Ch 09](09_Processes_and_Services.md)). When a worker reports "the settlement page 500'd at 3pm," you need to find *that* request among thousands, see the traceback, and know *who* did *what*. Unstructured `print()` scattered around won't cut it. You need deliberate, structured, findable logs.

# Theory (from zero)

### Logs vs metrics vs traces (the three telemetry pillars)
- **Logs** — discrete timestamped events ("user X started layering on Adda Y", "DB error"). The narrative.
- **Metrics** — aggregate numbers over time (5xx rate, latency) — monitoring ([Ch 30](30_Monitoring.md)).
- **Traces** — one request's path across components.
This chapter is logs; they're where you go to answer "what exactly happened in *this* case?"

### Log to stdout/stderr in containers (12-factor)
The [12-factor](https://12factor.net/logs) rule: an app **doesn't manage log files** — it writes to **stdout/stderr** as an event stream, and the platform captures/routes it. In Docker, whatever the process prints to stdout is captured by the Docker log driver and read with `docker compose logs`. **Don't write app logs to files inside the container** — they vanish with the container and fill the writable layer. My Gunicorn is configured `--access-logfile - --error-logfile -` (the `-` = stdout) exactly for this ([Ch 14](14_Gunicorn.md)).

### Log levels
`DEBUG < INFO < WARNING < ERROR < CRITICAL`. Prod typically logs INFO+ (DEBUG is too noisy and can leak data). Set the threshold so normal operation is a readable story and problems stand out.

### Structure + correlation (the part beginners miss)
A raw traceback tells you *what* broke but not *which request* or *who*. Two multipliers:
- **Request-id**: a unique id attached to every log line of a single request, so you can `grep` one request's whole story out of interleaved concurrent logs.
- **Actor**: which user/role did it — turns "a 500 happened" into "manager `dev.mgr` hit a 500 finalizing settlement #123".
Structured (key=value / JSON) logs make these machine-filterable.

### Rotation & retention
File logs must be rotated (`logrotate`) or they fill the disk — a classic outage ([Ch 30](30_Monitoring.md) watches disk). With stdout + Docker's `json-file` driver, set `max-size`/`max-file` so container logs don't grow unbounded; or ship them to a log service with retention.

### Never log secrets / PII
No passwords, tokens, session keys, full card/financial numbers, `os.environ` ([Ch 23](23_Environment_Variables.md)). Logs are read by many and often shipped off-box.

# Real World Example (My ERP)
- **stdout everywhere:** Gunicorn access + error logs go to stdout (`--access-logfile - --error-logfile -`); Django's `LOGGING` in `base.py` uses console handlers → all captured by `docker compose logs`.
- **Request-id + actor filter:** the base `LOGGING` config includes a **request-id filter** (and actor context) so each request's log lines are correlatable and attributable — you can trace one worker's one action end to end. (Referenced across [Ch 24](24_Django_Settings.md); it's why prod logging is "stdout with request-id + actor".)
- **Prod vs dev:** `production.py` logs to **stdout** (container-captured); `local.py` is free to use file/console for dev convenience ([Ch 24](24_Django_Settings.md)).
- **Security log:** the accounts app keeps a security/audit trail (failed logins, lockouts) feeding the brute-force protection ([Ch 22](22_Redis.md)) — security events are first-class logs, not afterthoughts.
- **Backup log line:** `deploy/backup.sh` prints `[backup] done` / `FAILED — investigate` to stdout — a log line monitoring watches ([Ch 28](28_Backups.md)).
- **Retention:** Docker's default `json-file` driver holds logs on the host; set `max-size`/`max-file` (or ship to a log service) so they don't fill the disk. Off-box shipping (Loki/BetterStack/Papertrail) is the growth step.

# Visual Diagram
```
  Django (LOGGING: console + request-id + actor)  ┐
  Gunicorn --access-logfile - --error-logfile -   ├─► STDOUT/STDERR (12-factor: app doesn't manage files)
  backup.sh echo "[backup] done/FAILED"           ┘         │
                                              Docker log driver (json-file, set max-size/max-file)
                                                            │
                                        docker compose logs -f app   ◄── you read here
                                                            │  (growth) ship off-box → Loki/BetterStack (retention+search)
  correlate:  request-id  → grep ONE request's whole story   |   actor → WHO did it
  levels: DEBUG<INFO<WARNING<ERROR<CRITICAL (prod = INFO+)   |   NEVER log secrets/PII
```

# Practical — how to inspect it
```bash
docker compose logs -f app                     # live tail of the app (Gunicorn access + Django logs)
docker compose logs --since 15m app            # last 15 min
docker compose logs --tail 200 app | grep -i error   # recent errors
docker compose logs backup | grep -iE 'done|FAILED'  # backup outcome (Ch28)
```
```bash
# Correlate one request by its request-id (once you have one from an error)
docker compose logs app | grep '<request-id>'  # the full story of that single request
```
```bash
# Bound host log growth (add to each service in compose)
#   logging: { driver: json-file, options: { max-size: "10m", max-file: "5" } }
docker inspect --format '{{.HostConfig.LogConfig}}' $(docker compose ps -q app)   # current log driver/limits
```

# Beginner Mistakes
- **`print()` for logging** → no levels, no timestamps, no filtering. Use Python's `logging` (already configured).
- **Writing logs to files in the container** → gone on rebuild, fills the writable layer. Log to **stdout** (12-factor).
- **`DEBUG` level in prod** → noise + potential data leakage. INFO+ in prod.
- **No request-id/actor** → can't isolate one request or know who did it. Keep the request-id + actor filter.
- **Logging secrets/PII** (passwords, tokens, `os.environ`, financial numbers) → a breach in your logs. Never.
- **Unbounded logs** → disk fills → outage. Set `max-size`/`max-file` or ship off-box.
- **Only logging errors** → no context for *why*. Log key business events at INFO too (started layering, finalized settlement).

# Interview Questions
**Junior — "Where do logs go in a Dockerized Django app?"** To stdout/stderr — the app doesn't manage log files (12-factor). Docker captures them; you read with `docker compose logs`.

**Mid — "Why a request-id and actor in your logs?"** To correlate all log lines of a single request out of interleaved concurrent traffic, and to know *who* (user/role) triggered it — turning "a 500 happened" into "this user, this action, this request, this traceback."

**Senior — "Logs vs error tracking — why both?"** Logs are the continuous event stream you search after the fact (INFO business events + tracebacks, correlated by request-id). Error tracking ([Ch 32](32_Sentry.md)) actively *alerts* on exceptions, deduplicates them, and attaches request/user context — you don't grep logs hoping to notice a new error; Sentry pages you. Logs = the record; Sentry = the alarm. You want the alarm *and* the searchable record.

**Staff — "Design logging/observability for this ERP as it grows."** Standardize structured (JSON) logs to stdout with a request-id + actor on every line and consistent levels; never log secrets/PII. Bound container logs (`max-size`/`max-file`) now; as volume grows, ship to a centralized store (Loki/ELK/BetterStack) with retention + full-text search + dashboards, and correlate logs↔metrics↔traces by request-id. Treat security/audit events (logins, settlement finalizations, overrides) as durable, tamper-evident logs separate from app chatter. Pair with error tracking (Sentry) for alerting and with the golden-signal metrics for trends. The invariant: every production event is attributable (who/what/when/which-request), searchable, retained appropriately, and free of secrets.

# Cheat Sheet
- **Log to stdout/stderr** (12-factor); don't manage files in the container. Gunicorn `--*-logfile -`.
- **Levels:** DEBUG<INFO<WARNING<ERROR<CRITICAL; prod = **INFO+**.
- **Request-id + actor** on every line → correlate one request + know *who*.
- **Never log** secrets/PII/`os.environ`/financial numbers.
- **Bound growth:** Docker `json-file` `max-size`/`max-file`, or ship off-box (Loki/BetterStack).
- Read: `docker compose logs -f app`, `--since`, `--tail`, `grep <request-id>`.
- **Logs = the record; Sentry = the alarm** ([Ch 32](32_Sentry.md)).

# My ERP Section
| Concept | In my ERP |
|---|---|
| Destination | stdout (Gunicorn `--access/-error-logfile -`, Django console handlers) |
| Correlation | request-id filter + actor in base `LOGGING` |
| Prod vs dev | `production.py` → stdout; `local.py` → file/console |
| Security log | accounts failed-login/lockout audit trail |
| Ops log | `backup.sh` `[backup] done/FAILED` |
| Read with | `docker compose logs -f app` |
| Growth step | `max-size`/`max-file` → ship to a log service |

# Homework
1. `docker compose logs --tail 50 app` — identify a Gunicorn access line vs a Django app line. What fields do you see?
2. Find (or trigger on a TEST stack) an error, grab its request-id, and `grep` the full request story. Why is that easier than reading raw logs?
3. Why must app logs go to stdout instead of a file inside the container? What breaks if you use a file?
4. Add a `logging:` block with `max-size`/`max-file` to a service — why is this an availability concern ([Ch 30](30_Monitoring.md))?
5. List three things you must never put in a log line, and say why for each.

---

## Further Reading & Live Resources
- The Twelve-Factor App — *XI. Logs*: https://12factor.net/logs
- Python docs — *Logging HOWTO*: https://docs.python.org/3/howto/logging.html
- Django docs — *Logging*: https://docs.djangoproject.com/en/5.0/topics/logging/
- Docker docs — *Configure logging drivers* (`json-file`, max-size/max-file): https://docs.docker.com/config/containers/logging/configure/
- Gunicorn docs — *logging* (`--access-logfile`, `--error-logfile`): https://docs.gunicorn.org/en/stable/settings.html#logging
- Grafana Loki (log aggregation, when you outgrow `docker logs`): https://grafana.com/oss/loki/
