---
id: deploy-course-26-collectstatic
type: lesson
status: active
owner: handwritten
scope: deployment, operations — this ERP shipped to a VPS
anchors: docker-compose.yml, deploy/entrypoint.sh, deploy/Caddyfile, deploy/backup.sh
verified: 2026-08-01
---

# 26 — collectstatic & WhiteNoise

> Part of [Deployment Course](00_COURSE_OVERVIEW.md). Prev: [25 — Static vs Media](25_Static_vs_Media.md). Next: [27 — Migrations](27_Migrations.md).

# Learning Objectives
By the end of this chapter you can:
- explain what collectstatic actually does
- say why it runs inside the deploy, not on your laptop
- fix an unstyled production site
- reason about cache-busting filenames

# Purpose
To understand the command that makes your CSS/JS actually appear in production — `collectstatic` — and the library that serves it — **WhiteNoise** — plus why static files get **hashed names** and **far-future caching**. This is why a fresh deploy shows styled pages, not a naked HTML skeleton.

# The Problem
In dev, Django finds static files scattered across every app's `static/` dir and each installed package's static dir, and `runserver` serves them on the fly. In production there's no `runserver`, and files in dozens of directories can't be served efficiently. You need to (1) **gather** every static file into one directory, and (2) **serve** that directory fast, cached, and cache-busted. `collectstatic` does the gathering; WhiteNoise does the serving.

# Theory (from zero)

### `collectstatic`
`python manage.py collectstatic` walks every `STATICFILES_DIRS` + every app's `static/` + every installed app's static assets, and **copies them all into `STATIC_ROOT`** (one flat, deployable tree). Run at deploy time. `--noinput` skips the "are you sure?" prompt (needed in automation). It's **idempotent** — safe to run every boot; it only copies what changed.

### WhiteNoise
Normally you'd need a separate web server (Nginx) to serve static files. **WhiteNoise** lets your **Django/Gunicorn process serve them directly** — added as middleware high in the stack. It serves from `STATIC_ROOT` with proper `Content-Type`, gzip/brotli compression, and caching headers. Result: no separate static server, simpler stack, one less moving part — ideal for a single-VPS deploy. (Caddy still sits in front for TLS; WhiteNoise handles the static bytes inside the app.)

### Hashed filenames + the manifest (cache-busting)
With `ManifestStaticFilesStorage` (WhiteNoise's compressed-manifest variant), each file is renamed with a hash of its contents: `home-motion.js` → `home-motion.4f9a1c.js`. A generated `staticfiles.json` **manifest** maps original → hashed names, and `{% static %}` in templates emits the hashed URL. Why:
- **Cache-busting:** change the file → new hash → new URL → browsers fetch the new one. Same content → same hash → browser reuses cache.
- **Far-future caching:** because the URL changes when content changes, WhiteNoise can send `Cache-Control: max-age=31536000, immutable` (1 year) safely — huge performance win, zero stale-asset risk.

### Where it runs in my stack
The **entrypoint** runs `collectstatic --noinput` on every container boot ([Ch 09](09_Processes_and_Services.md)), *before* Gunicorn starts serving. So a fresh image always has current, hashed static ready. The Dockerfile pre-creates + `chown`s `staticfiles/` to the `app` user so the non-root process can write it ([Ch 17](17_Dockerfile.md)).

> 💡 **Samjho aise:** Aapki CSS/JS kai app ke folder mein bikhri hai. `collectstatic` un sabko **ek almirah** mein sameta deta hai, taaki server ko dhoondhna na pade — sidha uthake de de. Isi liye yeh command **har deploy pe** chalti hai; bhool gaye to site khulegi par **bina kapdon ke** (styling gayab).

# Real World Example (My ERP)
- **Storage backend:** WhiteNoise compressed-manifest static storage → hashed names + `.gz`/`.br` variants + `staticfiles.json` manifest.
- **Middleware:** WhiteNoise is placed right after `SecurityMiddleware` in `base.py` (order matters — high in the stack).
- **STATIC_ROOT:** `staticfiles/` (Dockerfile creates + chowns it to uid-1000 `app`; entrypoint fills it).
- **Boot sequence:** entrypoint waits db+redis healthy → **`migrate --noinput`** ([Ch 27](27_Migrations.md)) → **`collectstatic --noinput`** → `exec gunicorn` ([Ch 14](14_Gunicorn.md)). So every deploy re-collects fresh static automatically.
- **Served under `/static/`** by WhiteNoise with 1-year immutable caching on hashed assets; Caddy in front only terminates TLS + proxies ([Ch 11](11_Reverse_Proxy.md)).
- **Not backed up:** reproducible from git + `collectstatic` ([Ch 25](25_Static_vs_Media.md)).

# Visual Diagram
```
  many source dirs                       collectstatic --noinput      WhiteNoise serves /static/
  app1/static/*  ┐                        (entrypoint, every boot)      (inside Gunicorn)
  app2/static/*  ├──── gather ──────────► STATIC_ROOT = staticfiles/ ──► GET /static/home.4f9a1c.js
  pkg/static/*   ┘                          home-motion.js → .4f9a1c.js     Cache-Control: max-age=1yr,
                                            + staticfiles.json (manifest)                    immutable
  {% static 'x.js' %} ── reads manifest ──► emits hashed URL  →  content changes ⇒ hash changes ⇒ cache-bust

  boot order:  wait db+redis → migrate → COLLECTSTATIC → exec gunicorn
```

# Practical — how to inspect it
```bash
docker compose exec app python manage.py collectstatic --noinput   # gather (idempotent; safe anytime)
docker compose exec app ls -lh /srv/app/config/staticfiles | head  # hashed files + staticfiles.json
docker compose exec app cat /srv/app/config/staticfiles/staticfiles.json | head   # original→hashed map
```
```bash
# Prove WhiteNoise serves it cached + compressed
curl -I https://<domain>/static/<hashed-file>        # Cache-Control: max-age=31536000, immutable
curl -I -H 'Accept-Encoding: br,gzip' https://<domain>/static/<hashed-css>  # Content-Encoding: br/gzip
```
```bash
# See it happen at boot
docker compose logs app | grep -i "static files copied"   # collectstatic ran during entrypoint
```

# Production Walkthrough
- `collectstatic` copies static files from every app and every configured directory into one folder (`STATIC_ROOT`) that a web server can serve.
- It runs in `deploy/entrypoint.sh` on every start, **before** the app serves traffic — so a deploy can never serve a half-collected mixture.
- Caddy then serves that folder directly (ch 13); Django is not involved.
- `--noinput` is used because a deploy has nobody to answer prompts.

# Debugging Guide
1. **Unstyled site** — the classic symptom. Check that collectstatic ran (entrypoint logs) and that Caddy points at the same folder.
2. **Old CSS still served** — browser or proxy cache. Hard-reload first; if hashed names are in use, a stale name means collectstatic did not re-run.
3. **"file not found" from ManifestStaticFilesStorage** — a template references a file that was never collected; the manifest is strict, on purpose.
4. **Permission denied** — the container user cannot write `STATIC_ROOT`.
5. **Works locally, breaks in production** — locally Django serves static itself in DEBUG; production does not. Never conclude from local behaviour.

# Performance Notes
- Collection takes seconds and happens once per deploy — irrelevant at runtime.
- Hashed filenames allow a one-year cache header safely; that is the biggest front-end win available.
- Compression, if enabled, is also a deploy-time cost paid once.
- Serving from disk via Caddy means zero Python involvement per asset.

# Security Considerations
- Do not collect anything secret into `STATIC_ROOT` — everything in it is public by definition.
- Source maps and development artefacts leak implementation detail; exclude them deliberately.
- A browsable static directory reveals the file inventory; keep directory listing off.

# Architecture Decisions
- **Run in the entrypoint** so it is impossible to forget, and so it happens on the machine that will serve the files.
- **Static as a build artefact, not source** — hence excluded from backups (ch 25).
- **Server-served static**, so a slow asset never consumes a Gunicorn worker (ch 14).

# Best Practices
- Never commit `STATIC_ROOT` to git.
- After a deploy, hard-reload once and confirm styling before declaring success.
- If you add a static file, reference it through `{% static %}` so the manifest can find it.
- Keep the entrypoint's ordering: **migrate → seed master data → collect → serve.** Collecting before migrating would serve assets for a schema that does not exist yet.

# Beginner Mistakes
- **Forgetting to run `collectstatic`** → prod serves no CSS/JS (site looks broken/naked). The entrypoint runs it — don't remove that.
- **`STATIC_ROOT` not writable by the app user** → `collectstatic` fails at boot. Dockerfile chowns it to `app` (uid 1000).
- **Hardcoding static URLs** (`/static/x.js`) instead of `{% static 'x.js' %}` → you get the un-hashed name → 404 under manifest storage (the real file is `x.4f9a1c.js`). Always use `{% static %}`.
- **Editing files directly in `staticfiles/`** → overwritten on next `collectstatic`. Edit the source in the app's `static/`.
- **Expecting media to be collected** → `collectstatic` is static-only; media is a separate volume ([Ch 25](25_Static_vs_Media.md)).
- **Missing/stale manifest** → `{% static %}` raises for a file not in `staticfiles.json`. Re-run `collectstatic` after adding assets.

# Interview Questions
- **Junior:** "What does `collectstatic` do?" — Copies all static files from every app/package into one directory (`STATIC_ROOT`) so they can be served in production; run at deploy time with `--noinput`.

- **Mid:** "What is WhiteNoise and why use it here?" — A library that lets the Django/Gunicorn process serve static files directly (compressed, cached) without a separate web server — simplifying a single-VPS stack while Caddy handles only TLS + proxying.

- **Senior:** "Explain hashed filenames + the manifest, and why they enable 1-year caching." — Manifest storage renames each file with a content hash and records the mapping in `staticfiles.json`; `{% static %}` emits the hashed URL. Because the URL changes whenever content changes, WhiteNoise can safely send `immutable`, `max-age=1yr` — browsers cache aggressively yet never serve a stale asset, since a change produces a new URL.

- **Staff:** "Where does static serving live in this stack and when would you change it?" — Today WhiteNoise serves static in-process behind Caddy — correct for one VPS: no extra component, hashed + compressed + far-future cached. I'd change it when traffic/geography justify a CDN: push `staticfiles/` (already hashed/immutable) to a CDN/object store and serve `/static/` from the edge, offloading the app and cutting latency. The manifest + hashing already make assets CDN-ready; only the origin changes. Until then, added complexity isn't worth it.

### Why interviewers ask these — and the answer that separates levels

| Testing for | Weak answer | What lands |
|---|---|---|
| Do you know what `collectstatic` gathers, and from where? | "It copies the static folder." | From **every app and every configured directory** — including third-party packages and the admin — into one `STATIC_ROOT`. Run with **`--noinput`** in the entrypoint, because a deploy has nobody to answer prompts. |
| Can you explain hashed filenames properly? | "Hashing busts the cache." | Manifest storage renames each file by **content hash** and records the mapping in **`staticfiles.json`**; `{% static %}` emits the hashed URL. Because **the URL changes whenever the content changes**, you can safely cache for **a year** — the biggest free front-end win available. |
| Do you know why the manifest is strict? | "A missing file just 404s." | With manifest storage a `{% static %}` reference to an uncollected file **raises at render time**, on purpose — it fails at deploy rather than shipping a silently broken page. Strictness is the feature. |
| Do you know why local behaviour proves nothing? | "It works locally, so static is fine." | In DEBUG **Django serves static itself**; production **never** does. So local success tests a completely different code path — which is exactly why "unstyled site" is the classic first-deploy symptom. |

**The killer follow-up:** *"The site deployed successfully but has no styling. Where do you look, in order?"* — did `collectstatic` actually run (entrypoint logs) → does the serving layer point at the **same** `STATIC_ROOT` → hard-reload once for cache. Guessing "clear the cache" first wastes the only minute when the deploy is still fresh in mind.

# Revision Notes
- `collectstatic` = gather app static files into one folder Caddy can serve.
- Runs in `deploy/entrypoint.sh` with `--noinput`, **before** traffic.
- Unstyled site = collectstatic missing or Caddy path mismatch.
- Hashed names make long cache headers safe.
- Local DEBUG serves static automatically — production never does, so never test this locally only.

# Cheat Sheet
- **`collectstatic --noinput`** = gather all static into `STATIC_ROOT`; idempotent; runs every boot via the entrypoint.
- **WhiteNoise** = serve static from inside Gunicorn (compressed + cached); no separate static server.
- **Manifest storage** = content-hashed names + `staticfiles.json` → cache-busting + `immutable` 1-year caching.
- Always `{% static 'x' %}` (never hardcode), edit **source** `static/` not `STATIC_ROOT`.
- Boot order: migrate → **collectstatic** → gunicorn. STATIC_ROOT must be app-writable.
- Static reproducible → not backed up ([Ch 25](25_Static_vs_Media.md)).

# My ERP Section
| Concept | In my ERP |
|---|---|
| Command | `collectstatic --noinput` (entrypoint, every boot) |
| STATIC_ROOT | `staticfiles/` (chowned to app uid 1000) |
| Storage | WhiteNoise compressed-manifest (hashed + gz/br) |
| Middleware | WhiteNoise after SecurityMiddleware (base.py) |
| Served | `/static/`, `Cache-Control: immutable` 1yr |
| Front | Caddy TLS/proxy only; WhiteNoise serves bytes |

# Practice Tasks
1. **Read the code:** find the collectstatic line in the entrypoint and the matching Caddy directive.
2. **Debug:** reference a non-existent file with `{% static %}` and observe the manifest error.
3. **Design:** write the two checks you will run after every deploy to prove static is healthy.
4. **Architecture:** argue why static is excluded from backups while media is not (ch 25).

# Homework
1. Run `collectstatic --noinput` in the container — how many files copied? Run again — why far fewer (idempotent)?
2. `cat staticfiles.json | head` — find one original→hashed mapping. Why does the hash matter for caching?
3. `curl -I` a hashed asset — record `Cache-Control`. Why is 1 year safe here but dangerous without hashing?
4. Change a source CSS file, re-run `collectstatic`, and observe the new hash. What happens to browsers' cached copy?
5. Trace the entrypoint: why must `collectstatic` run before Gunicorn starts, and why must `STATIC_ROOT` be app-writable?

---

# Further Reading & Live Resources
- Django docs — *`collectstatic`*: https://docs.djangoproject.com/en/5.0/ref/contrib/staticfiles/#collectstatic
- Django docs — *`ManifestStaticFilesStorage`* (hashing): https://docs.djangoproject.com/en/5.0/ref/contrib/staticfiles/#manifeststaticfilesstorage
- WhiteNoise — *Using WhiteNoise with Django*: https://whitenoise.readthedocs.io/en/stable/django.html
- WhiteNoise — *compression & caching*: https://whitenoise.readthedocs.io/en/stable/base.html#compression-support
- MDN — *HTTP caching (`Cache-Control`, `immutable`)*: https://developer.mozilla.org/en-US/docs/Web/HTTP/Caching
