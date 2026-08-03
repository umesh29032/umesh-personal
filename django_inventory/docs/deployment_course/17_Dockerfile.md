---
id: deploy-course-17-dockerfile
type: lesson
status: active
owner: handwritten
scope: deployment, operations — this ERP shipped to a VPS
anchors: docker-compose.yml, deploy/entrypoint.sh, deploy/Caddyfile, deploy/backup.sh
verified: 2026-08-01
---

# 17 — Dockerfile (my app image, line by line)

> Part of [Deployment Course](00_COURSE_OVERVIEW.md). Prev: [16 — Docker](16_Docker.md). Next: [18 — Docker Compose](18_Docker_Compose.md).

# Learning Objectives
By the end of this chapter you can:
- read this project's Dockerfile line by line
- order instructions so builds stay fast
- explain why layer caching rewards putting code last
- avoid baking secrets into an image

# Purpose
To read **my actual `Dockerfile`** line by line — the recipe that builds the `app` image (Django + Gunicorn + the exact Python + deps). When a build fails, the image is huge, or the container can't write a file, the cause is one of these lines. This is the most-edited deployment file, so I must own it.

# The Problem
The `app` container must contain *exactly* the right Python, my pinned dependencies, my code, a non-root user, writable dirs, and the startup command — assembled reproducibly. The Dockerfile is that assembly. Get the order wrong → slow rebuilds; get ownership wrong → "permission denied"; miss a pin → "worked last month, broken today."

# Theory (from zero) — every line of my real Dockerfile
```dockerfile
FROM python:3.10.16-slim
```
**Base image**, exact-pinned (owner rule #1). `slim` = Debian minus extras (small). Everything builds on top of this. Pinning `3.10.16` means the Python never drifts.

```dockerfile
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DJANGO_SETTINGS_MODULE=config.settings.production
```
**Environment defaults** baked into the image:
- `PYTHONDONTWRITEBYTECODE=1` — don't write `.pyc` files (pointless in a container).
- `PYTHONUNBUFFERED=1` — **print/log immediately to stdout** (so `docker compose logs` is live, not buffered — [Ch 31](31_Logging.md)).
- `PIP_NO_CACHE_DIR=1` — don't keep pip's cache (smaller image).
- `DJANGO_SETTINGS_MODULE=config.settings.production` — **the app defaults to production settings** (fixes the `wsgi.py`-defaults-to-local risk, [Ch 15](15_WSGI_ASGI.md)/[Ch 24](24_Django_Settings.md)).

```dockerfile
COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt
```
**Deps before code** — the layer-cache trick ([Ch 16](16_Docker.md)). Copying *only* `requirements.txt` first means this expensive `pip install` layer is **cached** and reused on every code-only change; it re-runs only when deps change. The comment notes all deps ship **wheels** (psycopg2-binary, Pillow, argon2-cffi, reportlab) → no C compiler needed → single-stage, small.

```dockerfile
RUN useradd --create-home --uid 1000 app
```
**Create a non-root user** `app` (uid 1000). Running as non-root is a core hardening step ([Ch 34](34_Production_Security.md)) — if the app is compromised, the attacker isn't root inside the container.

```dockerfile
COPY --chown=app:app config /srv/app/config
WORKDIR /srv/app/config
```
**Copy the app code** (the `config/` dir = the project) to `/srv/app/config`, owned by `app`. `WORKDIR` = the default dir for later commands + the running process (so `manage.py`, `config/` are right here — [Ch 08](08_File_System.md)).

```dockerfile
RUN mkdir -p logs staticfiles media && chown -R app:app logs staticfiles media
```
**Create + own the writable dirs** the app touches at runtime: `logs/` (base.py writes logs), `staticfiles/` (collectstatic output — [Ch 26](26_collectstatic.md)), `media/` (uploads; a volume mounts here — [Ch 20](20_Docker_Volumes.md)). Owned by `app` so the non-root process can write — this prevents "permission denied" ([Ch 08](08_File_System.md)).

```dockerfile
COPY --chown=app:app deploy/entrypoint.sh /srv/app/entrypoint.sh
RUN chmod +x /srv/app/entrypoint.sh
```
Copy + make the **entrypoint** executable ([Ch 09](09_Processes_and_Services.md)) — the wait-healthy→migrate→collectstatic→gunicorn script.

```dockerfile
USER app
```
**Switch to the non-root user** for everything after (and for the running container). Least privilege.

```dockerfile
EXPOSE 8000
```
**Documents** that the app listens on 8000. (Documentation only — it does *not* publish the port; only compose `ports:` does, and my `app` has none → private — [Ch 05](05_IP_Address_and_Ports.md).)

```dockerfile
ENTRYPOINT ["/srv/app/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", \
     "--workers", "3", "--access-logfile", "-", "--error-logfile", "-"]
```
**ENTRYPOINT** = the program the container always runs (my entrypoint script). **CMD** = the default arguments passed to it → the script's `exec "$@"` runs this Gunicorn command ([Ch 14](14_Gunicorn.md)). So container start = entrypoint (wait+migrate+collectstatic) → `exec gunicorn …` (PID 1, 3 workers, logs to stdout).

### ENTRYPOINT vs CMD (the classic confusion)
`ENTRYPOINT` is the fixed executable; `CMD` is the default, overridable arguments. Here: entrypoint always prepares the environment, then `exec`s whatever CMD is (gunicorn by default) — you could `docker compose run app python manage.py shell` and the entrypoint still runs the wait-loop first, then execs `python manage.py shell` instead of gunicorn.

> 💡 **Samjho aise:** Dockerfile tiffin banane ki **recipe** hai — line by line: *base lo, packages daalo, code copy karo, yeh command chalao*. Aur Docker har line ka **result cache** karta hai, isi liye badalne wali cheezein (aapka code) **sabse aakhir mein** likhte hain — warna har build poori recipe dobara banata hai.

# Real World Example (My ERP)
- This Dockerfile builds the `app` image used by the `app` (and `backup` shares the postgres image, not this one) service. `docker compose build app` runs these steps; `docker compose up -d` runs a container from the result.
- The **order is deliberate**: deps cached before code (fast rebuilds on code edits), non-root user + chowned writable dirs (no permission errors, hardened), production settings baked in (never boots dev config), stdout logging (observable).
- **Single-stage** (no builder stage) because every dep is a prebuilt wheel — simpler + still small. If a dep needed compiling, you'd add a multi-stage build to keep the compiler out of the final image.

# Visual Diagram
```
 docker compose build app  ──►  reads Dockerfile top→bottom, each step = a LAYER

  FROM python:3.10.16-slim          ← pinned base
  ENV …production, UNBUFFERED…      ← prod settings + live logs baked in
  COPY requirements.txt ; pip install  ← CACHED layer (deps change rarely)  ★fast rebuilds
  useradd app (uid 1000)            ← non-root
  COPY config → /srv/app/config     ← app code (changes often → later = cache-friendly)
  WORKDIR /srv/app/config
  mkdir+chown logs staticfiles media← writable dirs owned by app (no perm errors)
  COPY entrypoint ; chmod +x
  USER app                          ← drop privileges
  EXPOSE 8000                       ← doc only (not published)
  ENTRYPOINT entrypoint.sh          ← always: wait→migrate→collectstatic
  CMD gunicorn config.wsgi:application --workers 3 … -  ← default: run the app
                    │
                    ▼   image ready → container: entrypoint → exec gunicorn (PID 1)
```

# Practical — how to inspect it
```bash
docker compose build app             # build the image (watch which layers are CACHED)
docker images | grep -i app          # the built image + its size
docker history <app-image-id>        # every layer + size — spot bloat
```
```bash
docker compose exec app python --version    # 3.10.16 (pinned) regardless of host
docker compose exec app whoami              # "app" (non-root) — hardening proof
docker compose exec app ls -ld logs staticfiles media   # owned by app (writable)
docker compose exec app env | grep DJANGO_SETTINGS_MODULE  # config.settings.production
```
```bash
# Prove the cache trick: edit a .py, rebuild → pip install layer is "CACHED", build is fast
docker compose build app | grep -iE 'cached|running pip'
```

# Production Walkthrough
- The `Dockerfile` starts from a pinned Python base, installs system packages, installs Python requirements, **then** copies the application code — deliberately in that order.
- **Why the order matters:** Docker caches each layer. Requirements change rarely, code changes every deploy. Copying code last means a normal deploy re-runs only the final cheap layers instead of reinstalling every dependency.
- `deploy/entrypoint.sh` is the container's startup script (wait for health → migrate → seed → collectstatic → gunicorn), kept separate from the build so behaviour is readable without rebuilding.

# Debugging Guide
1. **Build suddenly slow?** A layer's cache was invalidated — usually because a file copied early changed.
2. **"file not found" during build** = it is outside the build context or excluded by `.dockerignore`.
3. **Works locally, fails in image** = a system package or environment variable that exists on your machine and not in the image.
4. **`docker compose build --no-cache`** when you suspect a stale layer — but understand *why* first.
5. **Image huge?** Check for build tools left in the final image and for copied caches.

# Performance Notes
- Layer order is the single biggest build-time lever.
- `.dockerignore` keeps `.git`, media and caches out of the build context — smaller, faster, and avoids accidentally shipping data.
- Multi-stage builds keep compilers out of the runtime image.
- Alpine-based images are small but occasionally awkward with Python wheels; the trade is size vs build friction.

# Security Considerations
- **Never `COPY .env` or bake a secret into a layer.** Layers are permanent and inspectable — a deleted secret in a later layer is still in the image.
- Pin the base image; rebuild to absorb upstream security patches.
- Create and use a **non-root user** for the runtime.
- Do not install a shell full of debugging tools in production images; every binary is attack surface.

# Architecture Decisions
- **Dependencies before code** for cache efficiency — a deliberate ordering decision, not an accident.
- **Entrypoint as a separate script** so start-up logic is version-controlled and reviewable independently of the image.
- **One image for the app**, configured by environment, so the same artefact runs anywhere (ch 23).

# Best Practices
- Copy requirements, install, then copy code. Always in that order.
- Keep a `.dockerignore` and check what is actually in the context.
- Rebuild on a schedule for base-image patches.
- Read the whole Dockerfile before changing one line of it.

# Beginner Mistakes
- **Copying all code before `pip install`** → every code edit busts the deps layer → slow rebuilds. Copy `requirements.txt` first.
- **Running as root** (no `USER app`) → compromised app = root in container. Add a non-root user.
- **Forgetting to `chown` writable dirs** → non-root process can't write logs/static/media → "permission denied" at boot ([Ch 08](08_File_System.md)).
- **Floating base tag (`python:3.10-slim` or `:latest`)** → surprise Python bumps. Pin the patch version.
- **Not setting `PYTHONUNBUFFERED`** → logs buffer and appear late/never in `docker logs`.
- **Baking secrets into the image** (`ENV SECRET_KEY=…`) → anyone with the image has your secret. Secrets come from `.env` at runtime, not the image ([Ch 23](23_Environment_Variables.md)).
- **Confusing ENTRYPOINT and CMD** → overriding the command unexpectedly skips the entrypoint prep, or vice-versa.

# Interview Questions
- **Junior:** "What does a Dockerfile do?" — It's the recipe to build an image: a series of steps (base image, install deps, copy code, set user, define the start command) that produce a reproducible, runnable environment for the app.

- **Mid:** "Why `COPY requirements.txt` + `pip install` before `COPY` the code?" — Layer caching — deps change rarely, so isolating them in an earlier layer lets code-only changes reuse the cached `pip install` layer, making rebuilds fast.

- **Senior:** "Walk the security-relevant lines of this Dockerfile." — Non-root `USER app` (uid 1000) so a compromise isn't root; `chown` limits writable dirs to exactly `logs/staticfiles/media`; `DJANGO_SETTINGS_MODULE=…production` baked so it can't accidentally run dev/`DEBUG=True`; no secrets in the image (they arrive via `.env` at runtime); pinned base for reproducibility. Least privilege + reproducibility.

- **Staff:** "When would you convert this to a multi-stage build, and what would you gain?" — When a dependency requires compilation (no wheel) — you'd build/compile in a `builder` stage with the toolchain, then copy only the built artifacts/wheels into a slim final stage, keeping the compiler and build headers out of the production image (smaller attack surface + size). Here every dep ships wheels, so single-stage is already minimal; multi-stage would add complexity for no gain until a source-only dep appears.

### Why interviewers ask these — and the answer that separates levels

| Testing for | Weak answer | What lands |
|---|---|---|
| Can you read a Dockerfile as a **security** document? | "It installs the app and runs it." | Point at the lines: **`USER app` (uid 1000)** so a compromise is not root · **`chown` limits writable dirs** to exactly `logs`/`staticfiles`/`media` · **`DJANGO_SETTINGS_MODULE=…production` baked in** so it cannot accidentally boot with `DEBUG=True`. |
| Do you know why a pinned base image matters? | "Use the latest base image for security patches." | `latest` means **a rebuild can silently change your runtime**. Pin it, then **move the pin deliberately** — that way an upgrade is a reviewed commit, not a surprise at 2 a.m. Pinning is not the opposite of patching; it is how you control patching. |
| Do you know what layer ordering costs you? | "Order does not really matter." | Every layer after a changed one is **rebuilt**. Copy code before installing dependencies and you rebuild the whole dependency tree on every commit — minutes per deploy, paid forever, for one misplaced line. |
| When would you go multi-stage? | "Multi-stage builds are best practice, always use them." | When a dependency **needs compilation** (no wheel available): build in a `builder` stage with the toolchain, then copy **only the artefacts** into a slim final image — so the compiler never ships to production. Without that need, it is added complexity for no gain. |

**The killer follow-up:** *"Your image is 1.2 GB. Walk me through getting it down."* — slim base · dependencies before code for caching · **`.dockerignore`** so `.git`, tests and local junk never enter the context · multi-stage if a toolchain is present. The tell is whether `.dockerignore` is mentioned at all — most people forget the build context entirely.

# Revision Notes
- Dockerfile = the recipe; each instruction is a **cached layer**.
- Put **rarely-changing** steps first, **code last** — that is the build-speed rule.
- `.dockerignore` shrinks context and prevents shipping junk.
- **Secrets never go in layers** — layers are permanent.
- Pin the base image; run as non-root.

# Cheat Sheet
- **Dockerfile = image recipe**, built top→bottom into cached **layers**.
- **My order:** pinned base → ENV (prod + unbuffered) → **deps (cached)** → non-root user → code → chown writable dirs → entrypoint → `USER app` → EXPOSE → ENTRYPOINT+CMD.
- **ENTRYPOINT** = fixed program (my prep script); **CMD** = default args (gunicorn), overridable.
- **Rules:** deps-before-code, non-root, chown writable dirs, pin the base, `PYTHONUNBUFFERED`, **no secrets in the image**.
- Inspect: `docker history`, `exec … whoami/python --version/env`.

# My ERP Section
| Line/Concept | In my Dockerfile |
|---|---|
| Base | `python:3.10.16-slim` (pinned) |
| Baked settings | `DJANGO_SETTINGS_MODULE=config.settings.production` |
| Live logs | `PYTHONUNBUFFERED=1` |
| Cache trick | `COPY requirements.txt` → `pip install` before code |
| User | non-root `app` (uid 1000), `USER app` |
| Writable dirs | `logs/ staticfiles/ media/` chowned to `app` |
| Prep | `ENTRYPOINT ["/srv/app/entrypoint.sh"]` |
| Run | `CMD gunicorn config.wsgi:application --workers 3 … -` |
| Port | `EXPOSE 8000` (doc only; not published) |

# Practice Tasks
1. **Read the code:** open the `Dockerfile` and mark which layers a normal code-only deploy will rebuild.
2. **Debug:** change one line in `requirements.txt`, rebuild, and observe which layers re-run.
3. **Design:** reorder a deliberately bad Dockerfile (code copied first) and measure the build-time difference.
4. **Architecture:** argue for or against a multi-stage build here. What would it save at this project's size?

# Homework
1. Read the real `Dockerfile`. Annotate each line's purpose in your own words.
2. `docker compose build app`, edit any `config/**.py`, rebuild — confirm the `pip install` layer says **CACHED**. Why?
3. `docker compose exec app whoami` + `ls -ld media` — prove non-root + writable. What line makes each true?
4. Explain ENTRYPOINT vs CMD using this file, and what runs if you do `docker compose run app python manage.py migrate`.
5. Where do secrets like `SECRET_KEY` come from — the Dockerfile or elsewhere — and why must they NOT be baked into the image?

---

# Further Reading & Live Resources
- Docker docs — *Dockerfile reference*: https://docs.docker.com/reference/dockerfile/
- Docker docs — *Building best practices* (layer caching, small images, non-root): https://docs.docker.com/develop/develop-images/dockerfile_best-practices/
- Docker docs — *Multi-stage builds*: https://docs.docker.com/build/building/multi-stage/
- testdriven.io — *Dockerizing Django with Postgres, Gunicorn* (real-world Dockerfile patterns): https://testdriven.io/blog/dockerizing-django-with-postgres-gunicorn-and-nginx/
- *ENTRYPOINT vs CMD* explained: https://docs.docker.com/reference/dockerfile/#understand-how-cmd-and-entrypoint-interact
- **Live tool** — Dive (analyze image layers/bloat): https://github.com/wagoodman/dive
