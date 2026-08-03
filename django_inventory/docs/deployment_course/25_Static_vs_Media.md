---
id: deploy-course-25-static-vs-media
type: lesson
status: active
owner: handwritten
scope: deployment, operations — this ERP shipped to a VPS
anchors: docker-compose.yml, deploy/entrypoint.sh, deploy/Caddyfile, deploy/backup.sh
verified: 2026-08-01
---

# 25 — Static vs Media Files

> Part of [Deployment Course](00_COURSE_OVERVIEW.md). Prev: [24 — Django Settings](24_Django_Settings.md). Next: [26 — collectstatic & WhiteNoise](26_collectstatic.md).

# Learning Objectives
By the end of this chapter you can:
- state the difference between static and media in one sentence each
- explain why only one of them needs backing up
- diagnose missing images and missing CSS separately
- reason about who should serve each

# Purpose
To understand the two completely different kinds of files a Django site serves — **static** (your CSS/JS/logos, shipped with the code) and **media** (user uploads, created at runtime) — why they're stored, served, and backed up differently, and why confusing them is a classic deploy bug.

# The Problem
In dev, `runserver` serves both your CSS and any uploaded photo automatically, so beginners think they're the same thing. In production `runserver` is gone ([Ch 14](14_Gunicorn.md)), and the two need opposite handling: static files are **read-only, versioned with the code, rebuilt every deploy**; media files are **written at runtime, must persist across deploys, must be backed up**. Treat them the same and you either lose user uploads on every deploy or fail to serve your CSS at all.

# Theory (from zero)

### Static files
Files that ship **with the application** and never change at runtime: CSS, JavaScript, fonts, icons, logos. They live in the repo (each app's `static/` dir), are collected into one folder at deploy time (`collectstatic` → `STATIC_ROOT`, [Ch 26](26_collectstatic.md)), and served under `STATIC_URL` (e.g. `/static/`). Because they're part of the code, a new deploy = new static files; nothing is lost by rebuilding.

### Media files
Files **created by users at runtime**: uploaded pattern photos, attachments, profile images. They live under `MEDIA_ROOT`, served under `MEDIA_URL` (e.g. `/media/`). They are **not** in the repo and **not** in the image — they appear after deploy as users upload. Therefore they must live on a **persistent volume** ([Ch 20](20_Docker_Volumes.md)) and be **backed up** ([Ch 28](28_Backups.md)); a rebuild must never wipe them.

### The core contrast (memorize)
| | Static | Media |
|---|---|---|
| Created by | developers (in the repo) | users (at runtime) |
| Changes at runtime? | no | yes (new uploads) |
| In git / the image? | yes | no |
| Setting | `STATIC_URL` / `STATIC_ROOT` | `MEDIA_URL` / `MEDIA_ROOT` |
| Storage | rebuilt each deploy (`collectstatic`) | persistent volume (`media`) |
| Backup? | no (it's in git) | **YES** (irreplaceable) |
| Served by | WhiteNoise (in-process) | app/volume (here) |

### How each is served in production
- **Static** → **WhiteNoise** ([Ch 26](26_collectstatic.md)): a middleware that lets Gunicorn serve the collected static files directly (hashed, compressed, far-future cached) with no separate web server. Simpler than the classic "Nginx serves /static" split.
- **Media** → served by the app from the persistent `media` volume (small-scale). At larger scale you'd move media to object storage (S3/Spaces) via `django-storages` and serve via CDN — but the volume approach is correct for one VPS.

### Why never mix them
- Putting media in `STATIC_ROOT` → wiped on `collectstatic`/rebuild → **user uploads lost**.
- Putting static in the media volume → not versioned, stale CSS after deploys, cache confusion.
Keep the two roots and two URLs strictly separate.

> 💡 **Samjho aise:** Do tarah ki file hoti hai: **static** = jo aapne likhi (CSS, JS, logo) — code ke saath aati hai, sabke liye ek jaisi. **Media** = jo user ne upload ki (pattern photo, receipt) — har din nayi banti hai aur **backup mein alag se** jaani chahiye. Dono ko ek samajh lena = ya CSS gayab, ya photo gayab.

# Real World Example (My ERP)
- **Static:** each app's `static/` (e.g. `storefront/static/storefront/js/home-motion.js`, the design-system CSS in `base.html`); `collectstatic` gathers them into `staticfiles/` (`STATIC_ROOT`), served by **WhiteNoise** under `/static/`. The Dockerfile pre-creates + chowns `staticfiles/` to the `app` user, and the entrypoint runs `collectstatic --noinput` on boot ([Ch 17](17_Dockerfile.md)).
- **Media:** user uploads (pattern photos, attachments) under `MEDIA_ROOT = /srv/app/config/media`, mounted as the **`media` named volume** (also mounted read-only into the `backup` service). Served under `/media/`.
- **Backup asymmetry:** the `backup` service bundles the `media` volume (+ the Postgres dump) off-site nightly ([Ch 28](28_Backups.md)); static is **not** backed up because it's reproducible from git + `collectstatic`.
- **Deploy safety:** `docker compose up -d --build` rebuilds the image (fresh static) but re-mounts the same `media` volume → uploads survive ([Ch 20](20_Docker_Volumes.md)).

# Visual Diagram
```
  STATIC (devs make it, in git)                 MEDIA (users make it, runtime)
   app/static/*  ──collectstatic──► staticfiles/   uploads ──► MEDIA_ROOT=/srv/app/config/media
        │                     (STATIC_ROOT)              │        (media named VOLUME)
        └─ served by WhiteNoise  /static/                └─ served by app  /media/
   rebuilt every deploy (safe to wipe)             MUST persist + be BACKED UP
   NOT backed up (it's in git)                     backup service bundles it off-site (Ch28)

   ⚠ never point MEDIA_ROOT inside STATIC_ROOT → collectstatic/rebuild wipes uploads
```

# Practical — how to inspect it
```bash
docker compose exec app python -c "from django.conf import settings; print('STATIC_ROOT',settings.STATIC_ROOT,'\nMEDIA_ROOT',settings.MEDIA_ROOT,'\nSTATIC_URL',settings.STATIC_URL,'MEDIA_URL',settings.MEDIA_URL)"
docker compose exec app ls -lh /srv/app/config/staticfiles | head   # collected static (rebuilt each deploy)
docker compose exec app ls -lh /srv/app/config/media | head         # user uploads (persistent volume)
```
```bash
# Prove each is served
curl -I https://<domain>/static/<some-css>     # 200, long Cache-Control (WhiteNoise)
curl -I https://<domain>/media/<an-upload>      # 200 from the media volume
```
```bash
# Prove media persists across a rebuild (TEST): note a file, rebuild, confirm still there
docker compose exec app ls /srv/app/config/media
docker compose up -d --build app
docker compose exec app ls /srv/app/config/media   # same files
```

# Production Walkthrough
- **Static = files you wrote** (CSS, JS, icons). They ship with the code, are collected at deploy (ch 26), and can always be regenerated from the repository.
- **Media = files users uploaded** (pattern photos, receipts, profile pictures). They exist nowhere else. The database stores only the *path*.
- Media lives on a volume (ch 20) and **must be in the backup** (ch 28). Static must not be — it is derivable.
- Caddy serves both as plain files, so Django is never woken up for an image (ch 13).

# Debugging Guide
1. **Site loads but unstyled** — static problem: `collectstatic` not run, or Caddy's static path wrong (ch 26).
2. **Broken image thumbnails** — media problem: volume not mounted, or `MEDIA_ROOT` mismatch.
3. **Upload succeeds, file missing after deploy** — you were writing inside the container instead of the volume. This is data loss; check before repeating it.
4. **403/404 on media** — permissions on the volume, or Caddy not configured for that prefix.
5. **Confirm which layer answered**: response headers tell you whether Caddy or Django served it.

# Performance Notes
- Static served by Caddy with long cache headers is essentially free; hashed filenames make long caching safe.
- Media files can be large; serving them through Django would occupy a worker for the whole transfer (ch 14).
- Many small media files make backups slow relative to their size (ch 28).
- Never serve either through Django in production.

# Security Considerations
- **Uploads are untrusted input.** Validate type and size; never trust the client-provided filename.
- Media here includes personal data — worker photos, expense receipts. Restrict access accordingly; "hard to guess URL" is not access control.
- Never make the media directory browsable.
- Executable content in a media directory is a serious risk; keep uploads non-executable.

# Architecture Decisions
- **Media on a volume, in backups; static regenerated at deploy** — the split follows directly from "can I rebuild this?".
- **Paths in the database, bytes on disk**, which is why a restore needs both parts to match (sql_course ch 21).
- **Caddy serves files**, Django serves logic.

# Best Practices
- Ask of every file: can I regenerate it? Yes → static. No → media, and back it up.
- Test one upload after every deploy that touches storage.
- Verify a restore brings back both database and media together (ch 29).
- Validate every upload path; treat filenames as hostile.

# Beginner Mistakes
- **Expecting `runserver`-style auto-serving in prod** → in prod nothing serves files unless configured (WhiteNoise for static, volume for media). Missing config = 404s / no CSS.
- **Pointing `MEDIA_ROOT` inside `STATIC_ROOT`** → uploads deleted on the next `collectstatic`/rebuild. Keep them separate dirs.
- **Not backing up media** → user uploads are irreplaceable (not in git). Back up the media volume ([Ch 28](28_Backups.md)).
- **Backing up static** → wasted space; it's reproducible from git + `collectstatic`.
- **Forgetting `collectstatic`** → no CSS/JS in prod (blank-looking site). The entrypoint runs it ([Ch 26](26_collectstatic.md)).
- **Storing media in the container FS (no volume)** → gone on next rebuild ([Ch 20](20_Docker_Volumes.md)).

# Interview Questions
- **Junior:** "Static vs media files?" — Static = developer assets shipped with the code (CSS/JS/logos), read-only, versioned in git. Media = user uploads created at runtime (photos, attachments), not in git, must persist.

- **Mid:** "Why back up media but not static?" — Media is user-generated and irreplaceable — it exists only on the server. Static is reproducible any time from git + `collectstatic`, so backing it up adds nothing.

- **Senior:** "How are static and media served in this stack, and why differently?" — Static via WhiteNoise (in-process, hashed + compressed + far-future cached) since it's immutable and versioned; media from a persistent Docker volume by the app, since it's mutable and must survive rebuilds. Different lifecycles → different serving/storage.

- **Staff:** "This ERP grows to many large uploads and multiple app servers – how does media handling evolve, and what stays the same?" — A single local volume no longer works across multiple app hosts and doesn't scale for large blobs, so move media to object storage (S3/Spaces) via `django-storages`, serve through a CDN, and keep signed URLs for access control; static can go to the same CDN. What stays the same: the strict static/media separation, media being backed up (now via the object store's versioning/replication), and static remaining reproducible from the build. The principle is invariant; only the backing store changes.

### Why interviewers ask these — and the answer that separates levels

| Testing for | Weak answer | What lands |
|---|---|---|
| Can you define the split by one test? | "Static is CSS, media is uploads." | The test is **"can I regenerate it?"** Yes → static (rebuild from git + `collectstatic`). No → media, **and it must be backed up**. That one question settles every new file type you meet. |
| Do you know why static is excluded from backups? | "Everything important should be backed up." | Static is **reproducible any time from git**, so backing it up adds bytes and no safety. Media is **irreplaceable** — it exists only on the server. Backing up derivable data is a habit that hides what actually matters. |
| Do you know why they are served differently? | "The proxy serves both." | **Static via WhiteNoise** — immutable, hashed, compressed, far-future cached. **Media from a persistent volume** — mutable and must survive deploys. Different lifecycles demand different mechanisms; the same treatment for both is the bug. |
| Do you know how the two halves of media relate? | "Media files are in the media folder." | The **database stores only the path**; the **disk stores the bytes**. So a restore needs both **from the same moment**, or every stored path points at nothing (ch 29). |

**The killer follow-up:** *"Uploads work, then vanish after a deploy. What happened?"* — the write went to the **container filesystem instead of the volume**. That is not a bug to investigate — it is **data already lost**, and the reason to test one upload after every deploy that touches storage.

# Revision Notes
- **Static = you wrote it** (CSS/JS) → regenerate at deploy, do **not** back up.
- **Media = users uploaded it** (photos/receipts) → exists nowhere else, **must** back up.
- DB stores paths; disk stores bytes. A restore needs both to match.
- Unstyled site = static bug. Broken image = media bug. Different problems.
- Caddy serves both; Django never should.

# Cheat Sheet
- **Static** = dev assets, in git, `STATIC_ROOT`/`STATIC_URL`, rebuilt each deploy via `collectstatic`, served by **WhiteNoise**, **not** backed up.
- **Media** = user uploads, not in git, `MEDIA_ROOT`/`MEDIA_URL`, on a **persistent volume**, served by the app, **backed up** off-site.
- **Never** nest `MEDIA_ROOT` inside `STATIC_ROOT`.
- My roots: `staticfiles/` (static) · `/srv/app/config/media` (media volume).
- Scale path: media → object storage + CDN; static → CDN.

# My ERP Section
| Concept | In my ERP |
|---|---|
| Static source | each app's `static/` + base.html design system |
| STATIC_ROOT | `staticfiles/` (collected on boot) |
| Static served by | WhiteNoise (`/static/`) |
| Media root | `/srv/app/config/media` (`media` named volume) |
| Media served by | app (`/media/`) |
| Backed up | media **yes**, static **no** |
| Deploy safety | rebuild = fresh static, same media volume |

# Practice Tasks
1. **Read the code:** find `STATIC_ROOT`, `MEDIA_ROOT` and the Caddy rules for each.
2. **Debug:** upload a file, find it on the volume, then confirm the database stores only its path.
3. **Design:** list every media directory this project writes to and confirm ch 28's backup covers each.
4. **Architecture:** argue whether media should move to object storage, and what ch 28 and ch 29 would then change.

# Homework
1. Print `STATIC_ROOT`, `MEDIA_ROOT`, `STATIC_URL`, `MEDIA_URL` (command above). Which two dirs are they, and are they separate?
2. `curl -I` a `/static/` asset — what `Cache-Control` does WhiteNoise set, and why so long? ([Ch 26](26_collectstatic.md))
3. On a TEST stack, upload a file, then `docker compose up -d --build` — is it still there? Why (which volume)?
4. Explain why static is not in the backup set but media is.
5. What single misconfiguration would cause `collectstatic` to delete user uploads?

---

# Further Reading & Live Resources
- Django docs — *Managing static files*: https://docs.djangoproject.com/en/5.0/howto/static-files/
- Django docs — *Deploying static files* (STATIC_ROOT/collectstatic): https://docs.djangoproject.com/en/5.0/howto/static-files/deployment/
- Django docs — *Managing user-uploaded (media) files*: https://docs.djangoproject.com/en/5.0/topics/files/
- WhiteNoise docs (serving static from Django): https://whitenoise.readthedocs.io/en/stable/
- django-storages (S3/Spaces for media at scale): https://django-storages.readthedocs.io/en/latest/
