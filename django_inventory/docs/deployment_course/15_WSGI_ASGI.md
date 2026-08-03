---
id: deploy-course-15-wsgi-asgi
type: lesson
status: active
owner: handwritten
scope: deployment, operations — this ERP shipped to a VPS
anchors: docker-compose.yml, deploy/entrypoint.sh, deploy/Caddyfile, deploy/backup.sh
verified: 2026-08-01
---

# 15 — WSGI & ASGI

> Part of [Deployment Course](00_COURSE_OVERVIEW.md). Prev: [14 — Gunicorn](14_Gunicorn.md). Next: [16 — Docker](16_Docker.md). *(Completes Term 3 — The web front.)*

# Learning Objectives
By the end of this chapter you can:
- explain WSGI as a contract between server and framework
- say what ASGI adds and when you actually need it
- decide which this ERP should use, with a reason
- name what changes in your code if you switch

# Purpose
To understand the **contract** that lets Gunicorn ([Ch 14](14_Gunicorn.md)) talk to Django at all — **WSGI** — and its async cousin **ASGI**. This demystifies `config.wsgi:application` (the exact thing Gunicorn loads), and tells me *when* my ERP would need ASGI (spoiler: not yet, and knowing why is the point).

# The Problem
Gunicorn is a generic server; Django is a specific framework. They're built by different people. Something must define *how a web server hands a request to a Python app and gets a response back* — a standard interface, so any WSGI server can run any WSGI app. That standard is WSGI. Without knowing it, `config.wsgi:application` and "sync vs async" are magic.

# Theory (from zero)

### WSGI — the sync contract
**WSGI (Web Server Gateway Interface)** is a Python standard (PEP 3333): the app exposes a single **callable** named `application(environ, start_response)`:
- `environ` = a dict of the request (method, path, headers, body).
- `start_response` = a function the app calls with the status + headers.
- the app returns the response body.

Gunicorn speaks WSGI; Django provides a WSGI `application`. So Gunicorn imports it and, per request, calls it with the request dict and sends back what Django returns. **One request in → one response out, synchronously.** That's the whole model — and it's exactly right for typical DB-backed CRUD like this ERP.

### `config/wsgi.py` — the front door
Django's `startproject` generates `wsgi.py` containing:
```python
import os
from django.core.wsgi import get_wsgi_application
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
application = get_wsgi_application()
```
`get_wsgi_application()` builds the WSGI callable (loads settings, sets up middleware). The module path + callable name = **`config.wsgi:application`** — precisely what my Gunicorn `CMD` loads ([Ch 14](14_Gunicorn.md)). `runserver` uses this same callable in dev.

### ASGI — the async contract
**ASGI (Asynchronous Server Gateway Interface)** is the newer standard for **async** Python web + **long-lived connections**: WebSockets, Server-Sent Events, long-polling, and `async def` views. WSGI is strictly request/response and **can't** hold a WebSocket open; ASGI can. An ASGI app exposes `async def application(scope, receive, send)`. Django also generates `config/asgi.py` (`get_asgi_application()`), served by an **ASGI server** like **Uvicorn** or **Daphne** (Gunicorn can supervise Uvicorn workers).

### WSGI vs ASGI — when each
- **WSGI (sync):** standard request/response apps (forms, pages, JSON APIs). Simpler, mature, less to go wrong. **My ERP.**
- **ASGI (async):** you need **WebSockets** (live dashboards pushing updates), lots of concurrent long-lived connections, or heavy `async def` I/O. Requires an ASGI server + often Django Channels + a channel layer (Redis).
- **Myth:** "async = faster." For DB-bound CRUD, async adds complexity without speed — the bottleneck is the DB, not the request loop. Reach for ASGI when you need its *capabilities* (real-time), not for imagined speed.

### How this sits under Gunicorn
Gunicorn's default **sync workers** run the **WSGI** app directly ([Ch 14](14_Gunicorn.md)). To run **ASGI**, you'd run Uvicorn (`uvicorn config.asgi:application`) or Gunicorn with a Uvicorn worker class. My stack uses plain WSGI — the simplest correct choice.

> 💡 **Samjho aise:** WSGI ek **standard plug** hai — koi bhi server (Gunicorn) kisi bhi Python app (Django) mein lag jaata hai. ASGI wahi plug, par **intezaar wale kaam** ke liye behtar (websocket, live updates): ek bawarchi kai orders ka intezaar ek saath kar sakta hai. Normal ERP ke liye WSGI kaafi hai.

# Real World Example (My ERP)
- My Gunicorn loads **`config.wsgi:application`** — the WSGI callable from `config/wsgi.py`. The Dockerfile sets `DJANGO_SETTINGS_MODULE=config.settings.production`, so the app boots with production settings ([Ch 24](24_Django_Settings.md)).
- Every worker report, allocation, snapshot, and settlement is a normal **request → response** cycle — a perfect fit for **WSGI/sync**. No WebSockets, no async views today.
- **The snapshot is a *live view* but not *real-time push*** — the manager refreshes to see updates (it re-queries on each load). That's WSGI-friendly. **If** the owner later wanted a factory dashboard that *pushes* live updates to screens without refresh, that's the WSGI→ASGI trigger: add Django Channels + Redis channel layer + an ASGI server, swapping `config.wsgi` for `config.asgi`. Until then, adding ASGI would be complexity with no payoff.
- Practical note: `DEP-F1` in RC1 flags that `config/wsgi.py` defaults its settings module to `local` if unset — mitigated because the Dockerfile pins `production` via `ENV` ([Ch 24](24_Django_Settings.md)).

# Visual Diagram
```
  WSGI (my ERP — sync, request/response)
    Caddy → Gunicorn(sync worker) → calls application(environ, start_response)
                                     └─ Django builds ONE response ─┘
    config.wsgi:application = get_wsgi_application()   (config/wsgi.py)

  ASGI (only if real-time needed later)
    Caddy → Uvicorn/Daphne → async application(scope, receive, send)
                              └─ can hold WebSockets open, async views ─┘
    config.asgi:application = get_asgi_application()   (config/asgi.py) + Channels + Redis

  choose by CAPABILITY (need live push? → ASGI), not by "async is faster"
```

# Practical — how to inspect it
```bash
cat config/config/wsgi.py     # see application = get_wsgi_application() + settings default
grep -n "config.wsgi:application" Dockerfile   # confirm what Gunicorn loads
```
```bash
# Prove the callable loads under production settings (inside the app container)
docker compose exec app python -c "import os; print(os.environ['DJANGO_SETTINGS_MODULE'])"
docker compose exec app python -c "from config.wsgi import application; print(type(application))"
```
```bash
# (Contrast only — do NOT switch) an ASGI run would look like:
#   uvicorn config.asgi:application --host 0.0.0.0 --port 8000
```

# Production Walkthrough
- `gunicorn config.wsgi` names the **WSGI entry point** — `config/wsgi.py`. That file is the contract: any WSGI server can run this app.
- **This ERP has no websockets, no server-sent events, no long-polling.** Every request is short: read a form, write rows, render a page. WSGI is exactly right, and choosing ASGI would add a runtime with different failure modes for no benefit.
- If live stage updates on the factory floor ever arrive, that is the day ASGI earns its place — and the migration is the entry point plus the server, not a rewrite.

# Debugging Guide
1. **"Application object must be callable"** = wrong entry point in the command.
2. **Works with `runserver`, fails under Gunicorn** = something relied on the dev server (auto-reload, static serving, or a settings default).
3. **Sync code inside an async view** blocks the event loop — the classic ASGI foot-gun, and the reason mixed codebases get slower rather than faster.
4. **Check `DJANGO_SETTINGS_MODULE`** — the entry point sets it; a wrong value produces baffling config errors.

# Performance Notes
- WSGI: one request per worker at a time; concurrency comes from *processes*. Simple and predictable.
- ASGI: one process can hold many waiting connections — a large win for websockets/streaming, roughly neutral for ordinary CRUD.
- The ERP's latency is dominated by database round-trips (sql_course ch 16), which ASGI does not fix.
- Threads (`--threads`) can help I/O-bound WSGI workloads without an ASGI migration.

# Security Considerations
- The entry point loads settings, so it decides whether you boot with `DEBUG=True` — a wrong `DJANGO_SETTINGS_MODULE` in production is a real exposure (ch 24).
- Async code paths bypass some assumptions of sync middleware; mixing them carelessly can skip a security check.
- Neither protocol is more or less secure; the risk is in the mismatch.

# Architecture Decisions
- **WSGI, deliberately**, because nothing in the requirements needs long-lived connections. Simplicity is the feature.
- **A documented switch trigger**: real-time updates. Until then, no ASGI.
- **Entry point in version control** (`config/wsgi.py`) rather than assembled at deploy time.

# Best Practices
- Keep the entry point trivial — it should only load settings and hand over.
- Do not adopt async because it sounds modern; adopt it for a workload that waits on connections.
- If you do go async, go async *end to end* for that path, not halfway.

# Beginner Mistakes
- **Confusing the WSGI *module* with the WSGI *server*.** `config/wsgi.py` is the app's callable; Gunicorn is the server that calls it. Both are needed.
- **Switching to ASGI "for performance"** on a DB-bound CRUD app → more moving parts (ASGI server, Channels, Redis layer), no speed gain. Use ASGI for *real-time features*, not speed.
- **`wsgi.py` settings default wrong in prod** → app boots with dev settings. Pin `DJANGO_SETTINGS_MODULE=…production` in the environment (Dockerfile does this).
- **Blocking calls in async views** — if you *do* go ASGI, a sync/blocking DB call inside `async def` stalls the event loop; you must use async-safe paths. (Another reason not to adopt ASGI casually.)
- **Pointing Gunicorn at the wrong callable** (`config.wsgi` vs `config.wsgi:application`) → boot error. It's `module:callable`.

# Interview Questions
- **Junior:** "What is WSGI?" — A Python standard interface between a web server and a Python web app: the app exposes an `application(environ, start_response)` callable the server invokes per request to get a response. It lets any WSGI server run any WSGI app.

- **Mid:** "What does `config.wsgi:application` mean and where is it used?" — It's `module:callable` — load `application` (the WSGI callable from `config/wsgi.py`) — which Gunicorn imports and calls for every request. It's what both Gunicorn (prod) and `runserver` (dev) serve.

- **Senior:** "When would you move this ERP to ASGI, and what does it entail?" — When you need capabilities WSGI can't provide — WebSockets/live push (e.g. a real-time factory dashboard), SSE, or many long-lived connections. It entails an ASGI server (Uvicorn/Daphne, or Gunicorn+Uvicorn workers), `config.asgi:application`, likely Django Channels + a Redis channel layer, and careful async-safe code. Not for speed on DB-bound CRUD.

- **Staff:** "Argue for keeping this ERP on WSGI." — The workload is request/response CRUD bottlenecked by Postgres, not by connection concurrency; sync WSGI + Gunicorn is mature, simple, and easy to reason about, with fewer failure modes (no event-loop blocking, no channel layer to operate). ASGI's benefits (real-time push, massive concurrent long-lived connections) aren't needed; adopting it would add operational surface and subtle async bugs for zero user-visible gain. Introduce ASGI only when a concrete real-time feature requires it, and then only for that surface.

### Why interviewers ask these — and the answer that separates levels

| Testing for | Weak answer | What lands |
|---|---|---|
| Do you know what WSGI actually is? | "WSGI is how Python web apps run." | A **standard interface**: the app exposes an `application(environ, start_response)` callable the server invokes per request. Because it is a *standard*, **any WSGI server can run any WSGI app** — which is why swapping Gunicorn for uWSGI needs no app change. |
| Can you decode `config.wsgi:application`? | "It points at the Django app." | It is **`module:callable`** — import `application` from `config/wsgi.py` and call it per request. Same callable used by Gunicorn in production and `runserver` in development, which is why "works in runserver" says little about production. |
| Do you know when ASGI is actually required? | "ASGI is newer and faster, so we should move." | ASGI buys what WSGI **cannot do**: **WebSockets, SSE, many long-lived connections**. It is not a speed upgrade for request/response CRUD. Moving without one of those needs is complexity you pay for and do not use. |
| Can you argue for staying on WSGI? | "WSGI is fine for now." | Make it a real argument: the workload is **request/response CRUD bottlenecked by Postgres, not by connection concurrency**; sync WSGI is mature with **fewer failure modes** — no event-loop blocking, no channel layer to operate. Choosing the boring option deliberately is a senior signal. |

**The killer follow-up:** *"What breaks first if you move this app to ASGI without changing the code?"* — a **single synchronous DB call blocks the event loop** and takes down concurrency for everyone on that worker. ASGI is not a drop-in; the answer must name the blocking-call hazard.

# Revision Notes
- WSGI = the **contract**: any WSGI server can run any WSGI framework.
- ASGI adds long-lived connections (websockets, streaming).
- This ERP: short request/response only ⇒ **WSGI is correct**.
- Concurrency under WSGI comes from **processes** (ch 14).
- Switch trigger = real-time features, not fashion.

# Cheat Sheet
- **WSGI = sync request/response contract** (server ↔ Python app). Django exposes `application` in `config/wsgi.py`.
- **`config.wsgi:application`** = `module:callable` Gunicorn loads (my ERP).
- **ASGI = async contract** for WebSockets / async views (Uvicorn/Daphne + often Channels+Redis).
- **Choose by capability** (need live push? → ASGI), **not** "async = faster" — DB-bound CRUD gains nothing from async.
- Pin `DJANGO_SETTINGS_MODULE=…production` so the callable boots prod settings.
- My ERP = **WSGI/sync**, correctly.

# My ERP Section
| Concept | In my ERP |
|---|---|
| Interface | WSGI (sync) |
| Callable | `config.wsgi:application` (`config/wsgi.py`) |
| Server | Gunicorn sync workers ([Ch 14](14_Gunicorn.md)) |
| Settings pin | `DJANGO_SETTINGS_MODULE=config.settings.production` (Dockerfile) |
| ASGI today? | No — no WebSockets/async needed |
| ASGI trigger | a real-time push dashboard → Channels + Redis + Uvicorn/`config.asgi` |

# Practice Tasks
1. **Read the code:** open `config/wsgi.py`. What are its only two responsibilities?
2. **Debug:** run gunicorn with a deliberately wrong entry point and read the error precisely.
3. **Design:** the owner wants live stage updates on the floor. Sketch what changes (server, entry point, one view) — and what does not.
4. **Architecture:** argue why adding async to only one view could make the app slower.

# Homework
1. `cat config/config/wsgi.py` — find the `application` and the default settings module. Match `config.wsgi:application` to the Gunicorn `CMD`.
2. In one sentence, explain the difference between `config/wsgi.py` (the module) and Gunicorn (the server).
3. Give one concrete feature that would justify ASGI for this ERP, and one reason async would NOT make the current pages faster.
4. Confirm (in the container) that `DJANGO_SETTINGS_MODULE` is `…production` and explain why that matters for the loaded WSGI app.

---

# Further Reading & Live Resources
- Django docs — *How to deploy with WSGI*: https://docs.djangoproject.com/en/5.0/howto/deployment/wsgi/
- Django docs — *How to deploy with ASGI*: https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
- PEP 3333 — *Python WSGI spec* (the actual standard): https://peps.python.org/pep-3333/
- ASGI documentation (the spec + rationale): https://asgi.readthedocs.io/
- Django Channels (WebSockets on Django, if you ever go ASGI): https://channels.readthedocs.io/
- Uvicorn (ASGI server): https://www.uvicorn.org/
