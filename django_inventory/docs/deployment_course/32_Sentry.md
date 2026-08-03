---
id: deploy-course-32-sentry
type: lesson
status: active
owner: handwritten
scope: deployment, operations — this ERP shipped to a VPS
anchors: docker-compose.yml, deploy/entrypoint.sh, deploy/Caddyfile, deploy/backup.sh
verified: 2026-08-01
---

# 32 — Error Tracking with Sentry

> Part of [Deployment Course](00_COURSE_OVERVIEW.md). Prev: [31 — Logging](31_Logging.md). Next: [33 — CI/CD](33_CI_CD.md). *(Completes Term 6.)*

# Learning Objectives
By the end of this chapter you can:
- explain what error tracking adds over logs
- describe how you would wire it into this project
- avoid the privacy mistakes error trackers invite
- decide whether you need it yet

# Purpose
To stop finding out about production errors from your users. **Error tracking** (Sentry) actively captures every exception with full context — traceback, request, user, release — deduplicates it, and alerts you. This chapter explains why logs alone aren't enough, how Sentry fits a Django + Docker deploy, and how to wire it without leaking data or spending money.

# The Problem
`docker compose logs` ([Ch 31](31_Logging.md)) records errors — but only if you're *looking*. A new 500 at 2am scrolls past unseen; the same bug hits 50 users and you learn about it days later from a complaint. And a raw log traceback lacks the *context* you need: which user, which URL, which POST data, which release, how many times. You need something that **notices** errors for you, **groups** them, and **tells you** — with the context to fix them fast.

# Theory (from zero)

### Error tracking vs logging
- **Logging** = the continuous event stream you *search after the fact*.
- **Error tracking** = a service that *actively intercepts exceptions*, **groups** identical ones into a single issue (so 500 occurrences = 1 issue with a count, not 500 log lines), attaches rich context, and **alerts** you the first time.
Logs are the record; Sentry is the alarm + the magnifying glass.

### What Sentry captures
On an unhandled exception it sends an **event**: the full traceback (with local variables), the request (URL, method, headers, sanitized params), the **user/actor**, the **release** version, the environment (prod/staging), and breadcrumbs (the trail of events leading up to it). It then **fingerprints** the error to group recurrences and tracks first-seen/last-seen/frequency + **regression** (an error you resolved that came back).

### How it integrates with Django
The `sentry-sdk` with the Django integration hooks into Django's error handling + WSGI ([Ch 15](15_WSGI_ASGI.md)) middleware. You call `sentry_sdk.init(dsn=…, environment=…, release=…)` once at startup (in `production.py`). The **DSN** (a URL identifying your project) comes from an env var — it's a write-only ingest key, but still config, so it lives in `.env` ([Ch 23](23_Environment_Variables.md)), not code.

### Privacy: scrub PII/secrets before sending
Sentry sends data *off your box* to a third party, so **scrub sensitive fields**: `send_default_pii=False`, and the SDK's default data scrubbers strip passwords/tokens/auth headers. For a financial app, also scrub financial fields you don't want off-site. Same rule as logging: never ship secrets ([Ch 31](31_Logging.md)).

### Sampling & cost control
- **Errors**: capture 100% (they're rare and each matters).
- **Performance traces** (`traces_sample_rate`): sample a fraction (e.g. 0.1) or disable — full tracing on every request is noisy and eats quota.
Sentry's **free tier** (or **self-hosted** Sentry, or the open-source **GlitchTip** which speaks the same protocol) keeps this at **$0** ([00B](00B_Deployment_Costs_And_Free_Alternatives.md)).

### Releases → know which deploy broke it
Tag each event with a **release** (e.g. the git SHA / `erp-v1.0.0`). Then Sentry shows "this error started in release X" — instantly tying a regression to the deploy that caused it, and marking it resolved when a later release stops it.

> 💡 **Samjho aise:** Log diary hai; Sentry **alarm + jaanch report** hai. Error hone pe wo aapko turant batata hai, aur saath mein poora scene deta hai: kaunsi line, kaunsa user, kya data, kitni baar. Diary mein wahi baat dhoondhne mein aadha ghanta lagta — Sentry aadhe minute mein de deta hai.

# Real World Example (My ERP)
- **Status — honest:** Sentry is **not yet wired** in my stack (a tracked gap, like the `/healthz` endpoint in [Ch 30](30_Monitoring.md)). Today production errors surface via `docker compose logs` + the accounts security log. This chapter is the **recommended addition** — one of the highest-value, lowest-cost upgrades for a first real deploy.
- **How it would slot in (minimal, safe):**
  1. `pip install sentry-sdk` → add to `requirements.txt` (rebuild the image, [Ch 17](17_Dockerfile.md)).
  2. In `production.py` only:
     ```python
     import sentry_sdk
     from sentry_sdk.integrations.django import DjangoIntegration
     SENTRY_DSN = config('SENTRY_DSN', default='')      # env, not code (Ch23)
     if SENTRY_DSN:                                      # opt-in; absent in dev/test
         sentry_sdk.init(
             dsn=SENTRY_DSN,
             integrations=[DjangoIntegration()],
             environment='production',
             release=config('RELEASE', default='erp-v1.0.0'),
             send_default_pii=False,                     # scrub PII (financial app)
             traces_sample_rate=0.0,                     # errors only to start (cost/noise)
         )
     ```
  3. Add `SENTRY_DSN=` to `.env.example` (placeholder) + the real DSN to `.env` on the VPS.
  4. Set `release` to the deploy's git SHA/tag so regressions map to deploys (my releases are tagged, e.g. `erp-v1.0.0`).
- **Fits existing rules:** DSN via env (fail-safe: empty = disabled), production-only init (never in dev/test), PII scrubbed (money app), no new money-write path. Pairs with the request-id/actor logging ([Ch 31](31_Logging.md)) so a Sentry issue and the log story share context.
- **Free option:** point the DSN at **GlitchTip** or **self-hosted Sentry** for $0 if you'd rather not use the SaaS free tier ([00B](00B_Deployment_Costs_And_Free_Alternatives.md)).

# Visual Diagram
```
  request → Django → 💥 unhandled exception
                         │  sentry-sdk (DjangoIntegration) intercepts
                         ▼
             EVENT: traceback + request(URL/method) + actor + release(git SHA)
                    + breadcrumbs   ── send_default_pii=False (scrub secrets/PII) ──►
                         │
                    Sentry / GlitchTip (SaaS free tier OR self-hosted = $0)
                    ├─ GROUP identical errors → 1 issue + count (not 500 log lines)
                    ├─ ALERT you (email/Slack) on first occurrence + regressions
                    └─ "started in release X" → which deploy broke it
  DSN from .env (Ch23)  ·  errors 100%, traces_sample_rate small/0  ·  prod-only init
  logs = the record (Ch31)   +   Sentry = the alarm + magnifier   ← use BOTH
```

# Practical — how to wire & verify it
```bash
# 1. add dependency, rebuild
echo 'sentry-sdk' >> requirements.txt
docker compose up -d --build app
# 2. put the DSN in .env (real) and .env.example (placeholder)
```
```bash
# 3. Verify capture from inside the container (sends a test event)
docker compose exec app python -c "import sentry_sdk; sentry_sdk.init(dsn='<DSN>'); sentry_sdk.capture_message('deploy test'); print('sent')"
# → the event appears in your Sentry/GlitchTip project within seconds
```
```bash
# 4. Confirm it's OFF when unset (fail-safe): empty DSN → init skipped, no crash
docker compose exec app python -c "from django.conf import settings; print('DSN set:', bool(getattr(settings,'SENTRY_DSN','')))"
```

# Production Walkthrough
- **Not currently installed.** This chapter is the design, and the honest status is part of the lesson.
- The gap it fills: logs are pull ("I went and looked"), error tracking is push ("it told me"). With one owner and no on-call rota, push matters.
- Wiring would be: a DSN in `.env` (ch 23), initialisation in the production settings module (ch 24), and nothing at all in local settings.
- The value is grouping — one exception seen 400 times becomes one item with a count, not 400 log lines.

# Debugging Guide
1. **Events not arriving** — DSN missing or wrong environment; the SDK stays silent by design when unconfigured.
2. **Everything reported, including handled cases** — noise; filter expected exceptions or you will stop reading it.
3. **Local errors polluting production data** — always tag the environment; never enable it locally.
4. **Traceback without context** — attach the request path, user id and release; a traceback alone rarely reproduces.

# Performance Notes
- Reporting is asynchronous; the request should not wait on it.
- Sampling keeps volume and cost sane on high-traffic paths.
- Never let the reporter's failure fail the request — errors about errors are a bad loop.

# Security Considerations
- **This is the highest-risk integration in the course**: it ships your errors, with context, to a third party.
- Scrub aggressively — `send_default_pii=False`, and filter `SECRET_KEY`, passwords, tokens, and financial identifiers.
- Local variables in frames can contain wage data or receipts; know what your SDK captures by default.
- Treat the DSN as a secret in `.env`; treat access to the dashboard as access to your data.

# Architecture Decisions
- **Deferred, not forgotten** — recorded as an open item rather than half-built. A half-configured reporter that leaks data is worse than none.
- **Production-only initialisation**, so laptop noise never mixes with real signal.
- **Scrubbing before convenience**: default to sending less than the SDK offers.

# Best Practices
- Configure environment and release tags from day one, or the data is unusable.
- Set up scrubbing before you set up alerting.
- Review what one real event contains before trusting the integration.
- Keep logs (ch 31) regardless; error tracking is an addition, not a replacement.

# Beginner Mistakes
- **Relying on `docker logs` to *notice* errors** → you won't, at scale/at night. Sentry alerts you actively.
- **Hardcoding the DSN in code** → it's config; put it in `.env`. Keep init behind `if SENTRY_DSN:` so dev/test stay off.
- **`send_default_pii=True` on a financial app** → ships user data off-box. Scrub PII; review what's sent.
- **`traces_sample_rate=1.0`** → floods quota + noise. Start errors-only (0.0), sample perf later if needed.
- **No `release` tag** → can't tell which deploy introduced a regression. Tag with the git SHA/version.
- **Initializing in `base.py`/dev** → dev noise + test pollution. Production-only init.
- **Treating Sentry as a log store** → it's for *errors/exceptions*, not your INFO event stream ([Ch 31](31_Logging.md)). Use both for their jobs.

# Interview Questions
- **Junior:** "What does Sentry do that logs don't?" — It actively captures every exception, groups duplicates into one issue with a count, attaches context (request, user, release), and alerts you — instead of you having to watch logs to notice an error.

- **Mid:** "How does Sentry integrate with Django and where does the DSN live?" — Via `sentry-sdk` + `DjangoIntegration`, initialized once at startup (in `production.py`); it hooks Django's error handling to capture unhandled exceptions. The DSN is config, read from an env var in `.env`, not hardcoded.

- **Senior:** "What context makes a Sentry issue actionable, and what must you scrub?" — Traceback + local vars, request (URL/method/sanitized params), actor/user, environment, and **release** (so regressions map to a deploy), plus breadcrumbs. You must scrub secrets/PII — `send_default_pii=False` + the default scrubbers strip passwords/tokens/auth headers; for a money app, also strip financial fields you don't want off-site.

- **Staff:** "How would you roll out error tracking on this ERP safely and cheaply?" — Add `sentry-sdk`, init **production-only** behind an env DSN (empty = disabled, so dev/test and a missing var are fail-safe), `send_default_pii=False`, errors at 100% and `traces_sample_rate` low/0 to control cost/noise, and tag events with the release SHA so regressions tie to deploys. Route alerts to one channel, correlate with the request-id/actor logs for the full story, and keep cost at $0 via the free tier or self-hosted GlitchTip. As it grows: raise trace sampling selectively on hot paths, add source maps if a JS frontend appears, and wire deploy hooks so Sentry knows each release. It layers cleanly on the existing logging/monitoring without touching money-write paths.

### Why interviewers ask these — and the answer that separates levels

| Testing for | Weak answer | What lands |
|---|---|---|
| Do you know what error tracking adds over logs? | "Sentry stores your errors in one place." | It **groups duplicates into one issue with a count**, attaches context (request, user, **release**), and **alerts you** — so 400 occurrences become one item instead of 400 log lines you have to go looking for. Push, not pull (ch 31). |
| Do you know what makes an issue *actionable*? | "The traceback tells you what broke." | Traceback **plus** request (URL/method/sanitised params), **actor**, environment, and — the one people forget — **release**, so a regression maps to the deploy that caused it. A traceback with no context rarely reproduces. |
| Do you know the fail-safe wiring? | "Add the DSN and initialise it." | **Production-only init behind an env DSN, empty = disabled** — so dev, tests and a missing variable are all fail-safe. Initialising unconditionally means laptop noise pollutes real signal and a missing var becomes a crash. |
| ⚠️ Do you know what this integration risks? | "It only sends error messages." | It **ships your errors, with context, to a third party** — and local variables in frames can contain **wage data or receipts**. So: **`send_default_pii=False`**, scrub secrets and financial identifiers, and **review one real event before trusting it**. Scrubbing comes before alerting. |

**The killer follow-up:** *"You enable Sentry and the first issue arrives. What do you check before you tell the team it is working?"* — **what the event actually contains.** If a settlement amount or a phone number is in the payload, you have just built an exfiltration path with good intentions. Configure scrubbing first, alerting second.

# Revision Notes
- Error tracking = **push** ("it told me"); logs = **pull** ("I looked"). Both, not either.
- Not installed here — deferred deliberately, recorded as open.
- Wiring: DSN in `.env`, init in **production settings only**, environment + release tags.
- Value = **grouping**: 400 occurrences become one item with a count.
- ⚠️ It sends your errors off-site. Scrub PII, secrets, wage data **before** enabling alerts.

# Cheat Sheet
- **Sentry = active error capture + grouping + alerting + context**; logs = the searchable record. Use both.
- Integrate via `sentry-sdk` + `DjangoIntegration`, **init in `production.py` only**, DSN from `.env` (empty = off).
- **Scrub:** `send_default_pii=False`; never ship secrets/financial PII off-box.
- **Errors 100%, `traces_sample_rate` small/0** (cost/noise). Tag **`release`** = git SHA → regressions map to deploys.
- **$0** via free tier / self-hosted Sentry / **GlitchTip**.
- **Status in my ERP: not yet wired (tracked gap)** — this is a recommended first-deploy add.

# My ERP Section
| Concept | In my ERP |
|---|---|
| Current status | **not wired yet (tracked gap)** — errors via `docker logs` + security log |
| Recommended SDK | `sentry-sdk` + `DjangoIntegration` |
| Init location | `production.py`, behind `if SENTRY_DSN:` |
| DSN | `.env` `SENTRY_DSN` (placeholder in `.env.example`) |
| Privacy | `send_default_pii=False` (financial app) |
| Sampling | errors 100%, `traces_sample_rate=0.0` to start |
| Release tag | git SHA / `erp-v1.0.0` (regressions → deploy) |
| Free option | GlitchTip / self-hosted Sentry ($0) |

# Practice Tasks
1. **Read the code:** confirm no error tracker exists today, and find where you would initialise it.
2. **Debug:** write the exact settings block, including scrubbing, without enabling it.
3. **Design:** list the exception types you would filter as expected noise in this ERP.
4. **Architecture:** argue whether a single-owner factory app needs error tracking before it needs monitoring (ch 30).

# Homework
1. Explain, with the "500 occurrences = 1 issue" example, why grouping matters vs raw logs.
2. Write the `sentry_sdk.init(...)` block for `production.py`. Why guard it behind `if SENTRY_DSN:` and put it in prod settings only?
3. Which fields must you scrub for this financial ERP, and which setting turns off default PII?
4. Why tag events with a `release`? How does that help when a bug reappears after you fixed it?
5. Pick a $0 path (free tier vs GlitchTip vs self-hosted). What's the trade-off of each for a solo dev?

---

# Further Reading & Live Resources
- Sentry — *Django integration* (setup, DSN, options): https://docs.sentry.io/platforms/python/integrations/django/
- Sentry — *Data scrubbing / `send_default_pii`*: https://docs.sentry.io/data-management/sensitive-data/
- Sentry — *Releases* (tie errors to deploys): https://docs.sentry.io/product/releases/
- GlitchTip (open-source, Sentry-compatible, self-hostable, free): https://glitchtip.com/
- Sentry — *self-hosted* (run your own, $0 licence): https://develop.sentry.dev/self-hosted/
- Sentry — *sampling / `traces_sample_rate`*: https://docs.sentry.io/platforms/python/configuration/sampling/
