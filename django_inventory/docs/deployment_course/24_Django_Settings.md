---
id: deploy-course-24-django-settings
type: lesson
status: active
owner: handwritten
scope: deployment, operations — this ERP shipped to a VPS
anchors: docker-compose.yml, deploy/entrypoint.sh, deploy/Caddyfile, deploy/backup.sh
verified: 2026-08-01
---

# 24 — Django Settings (base / local / production)

> Part of [Deployment Course](00_COURSE_OVERVIEW.md). Prev: [23 — Environment Variables](23_Environment_Variables.md). Next: [25 — Static vs Media](25_Static_vs_Media.md).

# Learning Objectives
By the end of this chapter you can:
- explain this project's split settings layout
- name the settings that decide whether a deploy is safe
- diagnose the classic settings-related 500s
- decide where a new setting belongs

# Purpose
To understand my **settings split** — `base.py`, `local.py`, `production.py` — what changes between dev and prod and *why*, and how `DJANGO_SETTINGS_MODULE` selects the right one. This file decides whether your production site is secure or leaking.

# The Problem
Dev wants `DEBUG=True`, `ALLOWED_HOSTS=['*']`, a console email backend, and easy reloading. Prod wants `DEBUG=False`, strict hosts, HTTPS enforcement, secure cookies, real email, Redis cache. Same code, opposite settings. Mixing them = either a broken dev experience or (far worse) a production site shipping with `DEBUG=True` leaking secrets. A clean split solves it.

# Theory (from zero)

### The split pattern
Instead of one `settings.py`, a package `config/settings/`:
- **`base.py`** — everything common to all environments (installed apps, middleware, templates, auth backends, `DATABASES` from `DATABASE_URL`, static/whitenoise, password hashers, base logging). Reads config from env ([Ch 23](23_Environment_Variables.md)).
- **`local.py`** — `from .base import *` + dev overrides (`DEBUG=True`, `ALLOWED_HOSTS=['*']`, console email, maybe debug toolbar).
- **`production.py`** — `from .base import *` + prod hardening (`DEBUG=False`, SSL redirect, HSTS, secure cookies, RedisCache, SMTP email, stdout logging).

### Selecting one — `DJANGO_SETTINGS_MODULE`
Django loads the module named by the `DJANGO_SETTINGS_MODULE` env var. My **Dockerfile bakes `DJANGO_SETTINGS_MODULE=config.settings.production`** ([Ch 17](17_Dockerfile.md)), so the container always runs prod settings. Locally you use `config.settings.local`. (RC1 `DEP-F1`: `wsgi.py` defaults to `local` if unset — mitigated because the image pins production.)

### What actually differs (dev → prod)
| Setting | local | production | why |
|---|---|---|---|
| `DEBUG` | True | **False** | True leaks stack traces/secrets ([Ch 03](03_HTTP_HTTPS.md)) |
| `ALLOWED_HOSTS` | `['*']` | env (`erp.<domain>`) | reject spoofed Host headers ([Ch 04](04_DNS_Domains.md)) |
| `SECRET_KEY` | dev fallback | `config('SECRET_KEY')` no default | real secret, fail-fast ([Ch 23](23_Environment_Variables.md)) |
| SSL/HSTS/secure cookies | off | on (SSL redirect, HSTS 1yr, secure cookies) | HTTPS enforcement ([Ch 03](03_HTTP_HTTPS.md)) |
| `SECURE_PROXY_SSL_HEADER` | — | set (trust Caddy's X-Forwarded-Proto) | avoid redirect loop ([Ch 11](11_Reverse_Proxy.md)) |
| CACHES | locmem/simple | RedisCache (`REDIS_URL`, no default) | shared cache + rate-limiter ([Ch 22](22_Redis.md)) |
| EMAIL | console | SMTP (env creds) | real password resets |
| LOGGING | file/console | stdout (request-id + actor) | container log capture ([Ch 31](31_Logging.md)) |
| `conn_max_age` | 0 | 600 | persistent DB conns in prod ([Ch 21](21_PostgreSQL.md)) |

### Why DEBUG=False is non-negotiable
With `DEBUG=True`, any error shows a full traceback page including settings + local variables (which can contain data/secrets), and `ALLOWED_HOSTS` isn't enforced. In production that's an information-disclosure vulnerability. `production.py` sets `DEBUG=False` — verified in RC1.

> 💡 **Samjho aise:** Ek hi app, do mizaaj: ghar pe (`local`) — galti dikhao, detail do, aaram se. Bahar (`production`) — galti chhupao, tez chalo, sakhti se. Isi liye settings **do file** mein baanti hai. Aur `DEBUG=True` production mein rehna sabse mehnga bhool hai: wo galti ke saath aapka poora ghar dikha deta hai.

# Real World Example (My ERP)
- **`config/config/settings/`** = `base.py` + `local.py` + `production.py`.
- **`base.py`**: `SECRET_KEY = config('SECRET_KEY', default='')` with a dev-only insecure fallback *only* when running `test`/`makemigrations`/`migrate` (which don't need real crypto); `ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=Csv())`; `DATABASES` from `DATABASE_URL` (dj-database-url, `conn_max_age=600`, `ssl_require` in prod); Argon2 password hashers; WhiteNoise static storage; base LOGGING with the request-id filter ([Ch 31](31_Logging.md)).
- **`local.py`**: `DEBUG=True`, `ALLOWED_HOSTS=['*']`, `conn_max_age=0` (the H-3 connection-leak fix with the autoreloader).
- **`production.py`**: `DEBUG=False`, `SECRET_KEY=config('SECRET_KEY')` (no default → fail-fast), `SECURE_SSL_REDIRECT`, HSTS (1yr+preload+subdomains), secure cookies, `SECURE_PROXY_SSL_HEADER`, `RedisCache` (no default), `CSRF_TRUSTED_ORIGINS` (no default), SMTP email, stdout logging.
- **Selection:** the Dockerfile's `ENV DJANGO_SETTINGS_MODULE=config.settings.production` → the container always runs prod. `verify_production` re-checks DEBUG-off + SECRET_KEY-present as a deploy gate ([Ch 30](30_Monitoring.md)).

# Visual Diagram
```
        config/settings/
          base.py  ── common: apps, middleware, DB(from DATABASE_URL), whitenoise,
          │            Argon2, logging(request-id), ALLOWED_HOSTS(env)
          ├── local.py       from .base import *  + DEBUG=True, ALLOWED_HOSTS=['*'], conn_max_age=0
          └── production.py  from .base import *  + DEBUG=False, SSL redirect, HSTS,
                                secure cookies, SECURE_PROXY_SSL_HEADER, RedisCache,
                                SECRET_KEY(no default), SMTP, stdout logging

  which one?  DJANGO_SETTINGS_MODULE   →  Dockerfile pins config.settings.production
  dev: config.settings.local           →  runserver / local manage.py
```

# Practical — how to inspect it
```bash
docker compose exec app printenv DJANGO_SETTINGS_MODULE     # config.settings.production
docker compose exec app python -c "from django.conf import settings; print('DEBUG=',settings.DEBUG, 'HOSTS=',settings.ALLOWED_HOSTS)"
docker compose exec app python manage.py diffsettings | grep -Ei 'DEBUG|SECURE_|ALLOWED|CACHES'  # prod overrides
```
```bash
# Django's own production audit
docker compose exec app python manage.py check --deploy    # flags DEBUG/SSL/cookie/HSTS issues
```
```bash
# Local dev uses local settings
DJANGO_SETTINGS_MODULE=config.settings.local python config/manage.py runserver
```

# Production Walkthrough
- Settings are a **package**, not a file: a shared base plus `local` and `production` modules. Production imports the base and then overrides only what differs.
- `DJANGO_SETTINGS_MODULE` chooses which one runs. On the server that is the production module; on your laptop, `config.settings.local`.
- Production sets `DEBUG=False`, a real `ALLOWED_HOSTS`, secure cookies, HSTS, and the database/cache from `.env` (ch 23).
- `manage.py check --deploy` is the audit that reads these settings and tells you what is still unsafe (ch 34).

# Debugging Guide
1. **DisallowedHost** — the domain is missing from `ALLOWED_HOSTS`. The error names the host you need to add.
2. **CSRF verification failed** on HTTPS — `CSRF_TRUSTED_ORIGINS` needs the scheme+domain.
3. **Infinite redirect loop** — `SECURE_SSL_REDIRECT` on while the proxy header is not trusted; Caddy terminates TLS, so Django must be told the request was secure.
4. **Static files 404 in production** — `STATIC_ROOT` / `collectstatic` mismatch (ch 26).
5. **Wrong settings module loaded** — everything looks "local" on the server. Print the module name at start-up when in doubt.

# Performance Notes
- Settings are imported once; no runtime cost.
- `CONN_MAX_AGE` here decides connection reuse (ch 21) — one line, large effect.
- Template caching is on in production and off locally, which is why the local server needs a restart after template edits.
- Middleware order is a performance and correctness decision, not decoration.

# Security Considerations
- **`DEBUG=False` is non-negotiable.** With `DEBUG=True`, an error page shows source, settings and environment to the internet.
- `ALLOWED_HOSTS` blocks Host-header abuse; wildcards defeat it.
- `SECURE_HSTS_SECONDS`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE` — all three matter once HTTPS exists (ch 12).
- Never import the production module on your laptop; it expects real secrets.
- `check --deploy` before every release; treat its warnings as a to-do list.

# Architecture Decisions
- **Split settings** so environment differences are explicit and reviewable, instead of buried in `if DEBUG:`.
- **Base + overrides** so a shared change cannot be forgotten in one environment.
- **Everything environment-specific from `.env`**, so the modules themselves are safe to commit.
- **One production module** rather than per-server files — servers differ by `.env`, not by code.

# Best Practices
- Add new environment-specific settings to `.env.example` and the base, not to a single environment.
- Run `check --deploy` in CI (ch 33) so nobody has to remember it.
- Keep local and production as close as possible; every difference is a class of bug that only appears in one place.
- Never commit a real secret into a settings module.

# Beginner Mistakes
- **Shipping `DEBUG=True`** → full tracebacks + secrets to anyone who triggers an error. The cardinal prod sin ([Ch 03](03_HTTP_HTTPS.md)).
- **`ALLOWED_HOSTS=['*']` in prod** → accepts spoofed Host headers (cache poisoning, etc.). Set the real domain.
- **One settings.py with `if DEBUG:` everywhere** → brittle; the split is cleaner and prevents accidental leaks.
- **Forgetting `DJANGO_SETTINGS_MODULE`** → app loads dev settings in prod (RC1 `DEP-F1`, mitigated by the Dockerfile ENV — keep it).
- **Duplicating (drift) between local/prod** → put shared things in `base.py`; only override differences.
- **Not running `check --deploy`** → miss easy hardening flags Django detects for you.

# Interview Questions
- **Junior:** "Why is `DEBUG=False` important in production?" — With DEBUG on, errors expose a full traceback with settings and local variables (potentially secrets/data) and `ALLOWED_HOSTS` isn't enforced — an information-disclosure risk. Off, users get a generic error page.

- **Mid:** "How does the settings split work and how is the right one chosen?" — A `base.py` holds common config; `local.py`/`production.py` import it and override per-environment. `DJANGO_SETTINGS_MODULE` picks which; the Docker image pins `config.settings.production` so containers always run prod settings.

- **Senior:** "Which production settings enforce HTTPS correctly behind Caddy, and what breaks if one is missing?" — `SECURE_SSL_REDIRECT` (HTTP→HTTPS), `SECURE_HSTS_SECONDS` (+ subdomains/preload), `SESSION/CSRF_COOKIE_SECURE`, and crucially `SECURE_PROXY_SSL_HEADER` so Django trusts Caddy's `X-Forwarded-Proto`. Without the proxy header, `SECURE_SSL_REDIRECT` sees "HTTP" (Caddy terminated TLS) and loops forever ([Ch 11](11_Reverse_Proxy.md)).

- **Staff:** "How do you guarantee prod never boots with dev settings, and audit hardening continuously?" — Pin `DJANGO_SETTINGS_MODULE=…production` in the image ENV (not relying on `wsgi.py`'s default); run `manage.py check --deploy` in CI and a `verify_production` gate post-deploy asserting `DEBUG=False` + `SECRET_KEY` present + enforcement flags; keep secrets fail-fast (no defaults) so a missing prod var crashes rather than silently degrades; and keep the base/prod split so dev conveniences can't leak in. Defense: pin + verify + fail-fast.

### Why interviewers ask these — and the answer that separates levels

| Testing for | Weak answer | What lands |
|---|---|---|
| `DEBUG=False` — do you know exactly what leaks? | "Debug mode shows errors to users." | It exposes a **full traceback with settings and local variables** — potentially secrets and customer data — **and `ALLOWED_HOSTS` is not enforced**. It is an information-disclosure vulnerability, not an untidy error page. |
| Can you name the four HTTPS settings behind a proxy? | "Turn on the secure settings." | **`SECURE_SSL_REDIRECT`** · **`SECURE_HSTS_SECONDS`** · **`SESSION_COOKIE_SECURE`/`CSRF_COOKIE_SECURE`** · and crucially **`SECURE_PROXY_SSL_HEADER`** so Django trusts Caddy's `X-Forwarded-Proto`. Omit the last one and you get an **infinite redirect loop** (ch 11). |
| Do you know how the right settings module is chosen? | "It defaults to the production settings." | **`DJANGO_SETTINGS_MODULE`** — and the image **pins `config.settings.production` in ENV** rather than relying on `wsgi.py`'s default. Relying on a default is how a container boots with dev settings and nobody notices. |
| Do you audit hardening, or assume it? | "We set the secure settings once." | **`manage.py check --deploy`** in CI plus a **`verify_production`** gate after deploy. Settings drift; a checklist that runs itself is the only kind that keeps working. |

**The killer follow-up:** *"Prove production cannot boot with dev settings."* — the answer is a **mechanism, not a promise**: `DJANGO_SETTINGS_MODULE` pinned in the image ENV, `check --deploy` in CI, and a post-deploy verification gate. "We are careful" is not proof, and this is a question about proof.

# Revision Notes
- Settings = **package**: base + `local` + `production`; `DJANGO_SETTINGS_MODULE` picks one.
- Production must have `DEBUG=False`, real `ALLOWED_HOSTS`, secure cookies, HSTS.
- DisallowedHost → add the domain. CSRF fail on HTTPS → `CSRF_TRUSTED_ORIGINS`.
- Redirect loop → SSL redirect on but proxy header not trusted.
- `manage.py check --deploy` = the pre-release audit (ch 34).

# Cheat Sheet
- **Split:** `base.py` (common) + `local.py` (DEBUG on) + `production.py` (hardened). Import base, override differences.
- **Selection:** `DJANGO_SETTINGS_MODULE`; Docker pins `config.settings.production`.
- **Prod flips:** DEBUG **off**, ALLOWED_HOSTS real, SECRET_KEY fail-fast, SSL redirect + HSTS + secure cookies + `SECURE_PROXY_SSL_HEADER`, RedisCache, SMTP, stdout logs, `conn_max_age=600`.
- **`DEBUG=True` in prod = leak.** **Missing `SECURE_PROXY_SSL_HEADER` = redirect loop.**
- Audit: `manage.py check --deploy`, `diffsettings`, `verify_production`.

# My ERP Section
| Concept | In my ERP |
|---|---|
| Files | `config/config/settings/{base,local,production}.py` |
| Selection | `DJANGO_SETTINGS_MODULE=config.settings.production` (Dockerfile ENV) |
| Prod hardening | DEBUG off, SSL redirect, HSTS 1yr, secure cookies, proxy header, RedisCache, SMTP, stdout logs |
| Fail-fast | SECRET_KEY / REDIS_URL / CSRF_TRUSTED_ORIGINS (no default) |
| DB | `DATABASE_URL` (dj-database-url, conn_max_age 600, ssl_require) |
| Deploy gate | `verify_production` (DEBUG off + SECRET_KEY present) |

# Practice Tasks
1. **Read the code:** diff the production module against base. Every difference — why does it exist?
2. **Debug:** run `check --deploy` locally with the production module and read every warning.
3. **Design:** you add a feature flag. Where does it live: base, production, or `.env`? Justify it.
4. **Architecture:** argue split settings versus one file with `if DEBUG:` branches.

# Homework
1. `docker compose exec app python -c "from django.conf import settings;print(settings.DEBUG, settings.ALLOWED_HOSTS)"` — confirm prod values.
2. `manage.py check --deploy` (in the container) — read every warning; which are already satisfied by `production.py`?
3. Open `production.py`; list the 5 security settings that enforce HTTPS. Which one prevents a redirect loop and why?
4. Explain how `DJANGO_SETTINGS_MODULE` + the Dockerfile guarantee the container never runs `local`.
5. Why does `SECRET_KEY` have a dev fallback in `base.py` but no default in `production.py`?

---

# Further Reading & Live Resources
- Django docs — *Settings* + *Deployment checklist*: https://docs.djangoproject.com/en/5.0/ref/settings/ · https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/
- Django docs — *`manage.py check --deploy`*: https://docs.djangoproject.com/en/5.0/ref/django-admin/#check
- cookiecutter-django settings split (the canonical pattern): https://cookiecutter-django.readthedocs.io/en/latest/settings.html
- Django docs — *Security / SSL/HTTPS settings*: https://docs.djangoproject.com/en/5.0/topics/security/
- Adam Johnson — *Django settings best practices*: https://adamj.eu/tech/2020/07/13/how-to-split-django-settings/
