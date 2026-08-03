---
id: deploy-course-39-debugging-production
type: lesson
status: active
owner: handwritten
scope: deployment, operations — this ERP shipped to a VPS
anchors: docker-compose.yml, deploy/entrypoint.sh, deploy/Caddyfile, deploy/backup.sh
verified: 2026-08-01
---

# 39 — Debugging Production

> Part of [Deployment Course](00_COURSE_OVERVIEW.md). Prev: [38 — Common Production Bugs](38_Common_Production_Bugs.md). Next: [40 — Disaster Recovery](40_Disaster_Recovery.md).

# Learning Objectives
By the end of this chapter you can:
- debug a live system in a disciplined order
- gather evidence without making things worse
- decide between fixing forward and rolling back
- keep users informed while you work

# Purpose
A **method** for finding and fixing bugs on a live system where you *can't* just add `print()` and hit refresh — and where `DEBUG=True` is forbidden. This is the calm, evidence-first procedure that replaces panic-poking a production box.

# The Problem
In dev you reproduce instantly, read tracebacks on the page, and edit-refresh. In production: you can't turn on `DEBUG` (it leaks secrets), the bug may be intermittent or user-specific, real data is at stake, and every "let me just try..." risks making it worse. You need a disciplined approach: gather evidence, form a hypothesis, test it safely, fix at the root, verify.

# Theory (from zero)

### The prime directive: DEBUG stays FALSE
Never flip `DEBUG=True` in production to "see the error." It exposes tracebacks with settings + secrets to anyone who triggers an error ([Ch 24](24_Django_Settings.md)). The information you want is in the **logs** + **error tracker**, obtained safely.

### The scientific method under fire
1. **Observe** — what exactly is wrong? (URL, user, time, error code, frequency.) Get the *specific* report, not "it's broken."
2. **Gather evidence** — logs, the traceback, the request-id, recent deploys, monitoring graphs.
3. **Hypothesize** — one testable cause ("500s started after the release at 14:00" → "the migration/that change").
4. **Test safely** — reproduce in staging / a shell / read-only queries; don't experiment on live writes.
5. **Fix at the root** — patch the cause, add a test that reproduces it, deploy via the normal gated path.
6. **Verify** — confirm the fix in prod (logs clean, `verify_production`, the reported flow works).

### Narrow it down (bisect the problem space)
- **When did it start?** Tie to a deploy → suspect that release (git bisect between tags). "Worked yesterday" is gold.
- **Who/what triggers it?** All users or one? One URL or all? A specific data shape? Narrow the input.
- **Which layer?** Caddy (502/TLS) vs app (500/traceback) vs DB (timeout/lock) vs config (400/403). The error code + which log has it localizes the layer ([Ch 38](38_Common_Production_Bugs.md)).

### Read-only first, on real data
Investigate with **read-only** tools (logs, `SELECT`, `manage.py shell` reads, `verify_production`) before any write. On a money system, a careless "fix" can corrupt data worse than the bug. Take a backup before any corrective write ([Ch 28](28_Backups.md)).

### The request-id is your thread
Every log line of one request shares a request-id ([Ch 31](31_Logging.md)). Get it from the error/user report, then `grep` the whole story of that one request out of the noise — the fastest way to a specific failure.

### Reproduce before you fix
A bug you can't reproduce isn't understood. Reproduce in staging (same images/config) or via a shell with the triggering input. A fix for an unreproduced bug is a guess.

> 💡 **Samjho aise:** Production debugging ki pehli shart: **guess karna band karo**. Kramm yeh hai — kya toota (symptom) → kab se (logs) → kis hop pe (guard/reception/clerk/tijori) → naapo → phir haath lagao. Aur live server pe seedha "thoda change karke dekhte hain" sabse mehnga raasta hai.

# Real World Example (My ERP)
- **Tools available, safely:** `docker compose logs` (Gunicorn access + Django tracebacks, correlated by request-id + actor), `manage.py shell` for read-only inspection, `verify_production` (read-only invariant gate — proves whether *data* is consistent), `check --deploy` (config), the accounts security log (auth issues). Sentry would add active capture + grouping ([Ch 32](32_Sentry.md), tracked gap).
- **How the real C-1/C-2 500s were handled:** the P19A audit *observed* the exact failing flows (layering-start; multi-lane worker-report), localized them to app-layer concurrency/edge paths, and **blocked the deploy** rather than hot-patching prod — evidence-first, root-cause, no rushed live edits. That's this method in practice.
- **Measurement honesty (a real trap):** earlier certification runs saw phantom "console errors" that turned out to be **stale-buffer / grep artifacts** (real count 0), and a "settlements render=false" that was a **false positive** matching `₹1500.00`. The lesson baked into my process: **verify the measurement before believing the bug** — reproduce and confirm, don't report an artifact as a defect ([Audit honesty rule]).
- **Backups make debugging safe:** because a pre-deploy dump + nightly restic exist, a corrective write can be attempted knowing there's a rollback ([Ch 28](28_Backups.md)/[Ch 29](29_Restore.md)).

# Visual Diagram
```
  REPORT ("500 on settlement finalize, ~14:05, user dev.mgr")
     │  DEBUG stays FALSE (never leak tracebacks)
     ▼
  ① OBSERVE  → URL? user? code? frequency? started when?
  ② EVIDENCE → docker compose logs (grep request-id/actor) · monitoring · recent deploy?
  ③ HYPOTHESIS → "started after 14:00 release → that change / migration"
  ④ TEST SAFELY → reproduce in staging / read-only shell / SELECT — NO live experiments
  ⑤ FIX ROOT → patch cause + add reproducing test → deploy via gated deploy.sh
  ⑥ VERIFY → logs clean · verify_production ✓ · the reported flow works
  narrow by: WHEN(deploy bisect) · WHO/WHAT(input) · WHICH LAYER(caddy/app/db/config)
  ⚠ verify the MEASUREMENT before believing the bug (phantom console-errors lesson)
  ⚠ backup before any corrective WRITE (money data)
```

# Practical — the debugging toolkit
```bash
# ① observe + ② evidence
docker compose logs --since 30m app | grep -iE '500|error|traceback'   # find it
docker compose logs app | grep '<request-id>'          # the ONE request's full story (Ch31)
docker compose ps                                       # which layer unhealthy?
docker compose logs --since 30m caddy | grep -iE '502|tls'  # proxy/TLS layer
```
```bash
# ④ test safely — read-only inspection, never DEBUG=True
docker compose exec app python manage.py shell          # inspect ORM state (reads)
docker compose exec app python manage.py verify_production   # is the DATA consistent?
docker compose exec app python manage.py check --deploy      # is it a CONFIG bug?
docker compose exec db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c \
  "SELECT pid, state, query, wait_event FROM pg_stat_activity WHERE state <> 'idle';"  # locks/slow queries
```
```bash
# narrow by deploy: which release introduced it?
git log --oneline erp-v1.0.0..HEAD        # changes since the last-good tag → bisect suspects
```

# Production Walkthrough
The method, in order, every time:
1. **Observe** — `docker compose ps`, then the logs of the layer that reported the error (ch 31).
2. **Reproduce** — exactly which user, page, and action? "It's broken" is not a bug report.
3. **Isolate the layer** — Caddy, Gunicorn, Django, Postgres.
4. **Form one hypothesis**, test it, write down the result.
5. **Decide**: fix forward if the cause is understood and the change is small; **roll back** if it is not (ch 35).

Safe evidence-gathering on this stack: `docker compose logs`, `exec … python manage.py shell` for read-only queries, `pg_stat_activity` for what the database is doing right now.

# Debugging Guide
1. **Never debug with `DEBUG=True` in production.** It exposes settings and source to whoever is watching (ch 34).
2. **A hang is a lock, not slowness** — look for a long transaction holding `FOR UPDATE` (ch 21).
3. **Intermittent** = load, cache, or a scheduled job. Correlate with time.
4. **Only some users affected** = permissions, roles, or per-user cached content (ch 22).
5. **Nothing in the logs** = wrong service, or the process died before logging.
6. **Do not run write queries to "test"** — reads only, until you understand the state.

# Performance Notes
- Measure before optimising: `EXPLAIN ANALYZE` for queries, timing for views.
- N+1 queries are the most common Django slowness; the query count tells you immediately.
- One missing index outweighs every server tuning knob (sql_course ch 12).
- Load matters: this project once saw fake test failures caused purely by load from another process. Remove load before diagnosing.

# Security Considerations
- Do not paste production logs into third-party tools — they contain personal and financial data (ch 31).
- Read-only access is enough for almost all diagnosis; use it.
- Every emergency shortcut (open port, disabled check) must be written down and reverted the same day.
- Preserve evidence before restarting if a compromise is possible (ch 34).

# Architecture Decisions
- **A written order of operations**, because incident pressure destroys improvisation.
- **Rollback is cheap here** — two commands and a backup — so it is a legitimate first response.
- **Logs per service**, so isolation takes one command.

# Best Practices
- Write a timeline as you go; you will need it afterwards.
- One change at a time, and revert what did not help.
- Tell users what is happening in plain language.
- After the incident: a pin (test or checklist line), then a short write-up.

# Beginner Mistakes
- **Turning on `DEBUG=True` in prod** → leaks secrets to users. Use logs/Sentry ([Ch 24](24_Django_Settings.md)).
- **Poking live data with writes** → a bad "fix" corrupts the money DB. Read-only first; backup before writes.
- **Fixing without reproducing** → you're guessing; the bug returns. Reproduce in staging/shell first.
- **Fixing the symptom** (catch + swallow the 500) → root cause remains. Patch the cause + add a test.
- **Believing the first measurement** → phantom errors/false positives (my stale-buffer lesson). Confirm the signal is real.
- **Not noting "when it started"** → skips the fastest clue. Tie to a deploy.
- **Hot-patching files on the server** → drifts from git; unreproducible. Fix in code → gated deploy.

# Interview Questions
- **Junior:** "A production page 500s. What's your first move – and what do you NOT do?" — First: read `docker compose logs app` for the traceback (and its request-id). Do **not** set `DEBUG=True` in production — it leaks secrets; the logs already have the traceback.

- **Mid:** "How do you narrow down a production bug quickly?" — Three axes: *when* it started (tie to a deploy → suspect that release), *who/what* triggers it (all users or one, which URL, which input), and *which layer* (error code + which log: Caddy 502/TLS, app 500, DB timeout/lock, config 400/403). Each cut shrinks the search space fast.

- **Senior:** "Walk your method for an intermittent 500 under load on a financial endpoint." — Observe the exact flow/frequency; pull logs by request-id + actor to see the failing requests; check `pg_stat_activity` for locks/slow queries and monitoring for a load correlation; hypothesize a concurrency/race (dev-invisible); reproduce in staging by hammering the endpoint concurrently; fix at the root with atomic + row/advisory locks in the service layer + a reproducing test; take a backup, deploy via the gated path, and verify with `verify_production` + the flow. This mirrors the real C-1/C-2 handling.

- **Staff:** "Design your team's production-debugging discipline for a money system." — Codify: DEBUG never on in prod; structured logs with request-id + actor + an error tracker (Sentry) so issues are captured and grouped, not hunted; a staging env mirroring prod to reproduce safely; read-only-first investigation with a backup before any corrective write; root-cause + a reproducing test required before a fix ships (no symptom patches); deploys only via the gated `deploy.sh` (no server hot-edits) so every fix maps to a commit and is reversible; and a "verify the measurement" rule so artifacts aren't chased as bugs. Pair with blameless postmortems that feed tests/monitoring. The invariant: evidence → hypothesis → safe test → root fix → verify, with data safety and reversibility at every step.

### Why interviewers ask these — they are testing method, not trivia

| Testing for | Weak answer | What lands |
|---|---|---|
| Do you have a **method** or do you guess? | "I'd check the logs." | An order: reproduce/scope → **when did it start** → which hop (proxy / app / DB) → measure → only then change. Guessing is the failure mode being probed. |
| Can you resist changing production while blind? | "Try a fix and see." | Read-only investigation first; change one thing, with a way to undo it. Say out loud that a live edit without a rollback path is the actual risk. |
| Do you know slow ≠ one slow query? | "Optimise the query." | **Count the queries first** — most slow pages are N+1, and no query plan will reveal that. Then EXPLAIN the worst one. |

**What they are really buying:** someone who stays calm and ordered while things burn. Describing the *sequence* proves that better than any single fix.

**The killer follow-up:** *"You have been stuck for 30 minutes and users are blocked. Now what?"* — **roll back and think afterwards.** The answer they are listening for is that you know when to stop debugging; someone who keeps investigating while the factory waits has the wrong instinct, however good their method is.
# Revision Notes
- Order: **observe → reproduce → isolate layer → one hypothesis → fix-forward or roll back.**
- Evidence: `compose logs`, read-only `manage.py shell`, `pg_stat_activity`. **Reads only.**
- Hang = lock (long `FOR UPDATE`), not slowness. Intermittent = load/cache/cron.
- Understood + small ⇒ fix forward. Not understood ⇒ **roll back**.
- ⚠️ Never `DEBUG=True` in production; never paste production logs into third-party tools.

# Cheat Sheet
- **DEBUG stays FALSE.** Evidence lives in **logs** (grep the **request-id**) + Sentry, not a leaked traceback.
- **Method:** observe → evidence → hypothesis → test safely → root fix (+ test) → verify.
- **Narrow by:** *when* (deploy bisect), *who/what* (input), *which layer* (code → Caddy/app/db/config).
- **Read-only first**; **backup before any corrective write** (money data).
- **Reproduce before you fix**; patch the **root**, not the symptom; add a reproducing test.
- **Verify the measurement** before believing the bug (phantom-error lesson). **Fix in code → gated deploy**, never hot-edit the server.
- Tools: `docker compose logs`, `manage.py shell`/`verify_production`/`check --deploy`, `pg_stat_activity`.

# My ERP Section
| Step | Tool in my ERP |
|---|---|
| Evidence | `docker compose logs` (request-id + actor), security log |
| Data consistency | `verify_production` (read-only) |
| Config check | `check --deploy` |
| DB locks/slow | `pg_stat_activity` |
| Deploy bisect | git tags (`erp-v1.0.0..HEAD`) |
| Real case | C-1/C-2 500s: observed, root-caused, deploy blocked (no hot-patch) |
| Safety | pre-deploy dump + nightly restic before corrective writes |
| Trap avoided | phantom console-errors / ₹1500 false-positive (verify measurement) |

# Practice Tasks
1. **Read the code:** write the exact commands for steps 1–3 for this project.
2. **Debug:** hold a row lock in one psql session and diagnose the resulting hang from the other side.
3. **Design:** write your incident template — timeline, hypothesis, action, result.
4. **Architecture:** define your own rule for fix-forward versus roll back, and defend it.

# Homework
1. Given "500 on `/settlement/finalize`, started 14:05, one manager," write your first three commands. Why not `DEBUG=True`?
2. Practice the request-id trace: cause an error on a TEST stack, grab its id, `grep` the full request. How much faster is that than scrolling?
3. Use `pg_stat_activity` to spot a long-running/locking query. How would that explain intermittent 500s under load?
4. Explain "verify the measurement" using my phantom-console-error example. How could reporting the artifact have wasted a day?
5. Why must a fix be reproduced + tested + deployed via `deploy.sh` rather than edited live? Tie it to reversibility.

---

# Further Reading & Live Resources
- Django docs — *Logging* (your prod window): https://docs.djangoproject.com/en/5.0/topics/logging/
- Postgres docs — *`pg_stat_activity`* (see live queries/locks): https://www.postgresql.org/docs/current/monitoring-stats.html#MONITORING-PG-STAT-ACTIVITY-VIEW
- Google SRE Book — *Effective Troubleshooting*: https://sre.google/sre-book/effective-troubleshooting/
- Julia Evans — *debugging zines / tools* (practical, beginner-friendly): https://jvns.ca/
- Brendan Gregg — *Linux performance & debugging tools*: https://www.brendangregg.com/linuxperf.html
- Google SRE Book — *Postmortem culture (blameless)*: https://sre.google/sre-book/postmortem-culture/
