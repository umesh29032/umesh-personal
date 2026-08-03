---
id: deploy-course-23-environment-variables
type: lesson
status: active
owner: handwritten
scope: deployment, operations — this ERP shipped to a VPS
anchors: docker-compose.yml, deploy/entrypoint.sh, deploy/Caddyfile, deploy/backup.sh
verified: 2026-08-01
---

# 23 — Environment Variables & Secrets

> Part of [Deployment Course](00_COURSE_OVERVIEW.md). Prev: [22 — Redis](22_Redis.md). Next: [24 — Django Settings](24_Django_Settings.md).

# Learning Objectives
By the end of this chapter you can:
- explain why config lives outside code
- list this project's must-set variables
- recover safely from a leaked secret
- decide what belongs in `.env` versus settings

# Purpose
To understand how config + **secrets** (SECRET_KEY, DB password) reach my app **without living in the code or the image** — via **environment variables** and the `.env` file. This is the difference between a leak-proof deploy and one where your DB password is in git forever.

# The Problem
The same code runs on my laptop and the VPS, but with *different* config (DEBUG, DB host, domain, secret key). And some of that config is **secret** — if it leaks (committed to git, baked into an image, printed in a log), an attacker owns the DB. I need config to be **external** to the code, **environment-specific**, and **secrets never committed**.

# Theory (from zero)

### Config is environment, not code (12-factor)
The [Twelve-Factor App](https://12factor.net/config) rule III: **store config in the environment.** Code is identical everywhere; the *environment* provides the values. Django reads them at startup. This is why the same image runs in dev and prod — only the env differs.

### Environment variables
Key=value pairs the OS/container hands to a process. Django reads them (via `os.environ` or a helper like `python-decouple`/`config()`). In Docker, they come from the container's environment, set by Compose's `env_file:` / `environment:` ([Ch 18](18_Docker_Compose.md)).

### The `.env` file
A plain file of `KEY=value` lines, **loaded into the environment** at boot. It holds the real values for one environment (the VPS). **It is NOT committed** — it's gitignored. A committed **`.env.example`** documents *which* vars exist (with placeholders), so anyone can reproduce the config without seeing secrets.

### Secrets vs non-secrets
- **Secrets** (must never leak): `SECRET_KEY`, `POSTGRES_PASSWORD`, `DATABASE_URL` (contains the password), email/API creds, restic repo password.
- **Non-secret config**: `DEBUG`, `ALLOWED_HOSTS`, `DOMAIN`, `CSRF_TRUSTED_ORIGINS`.
All go in `.env`; the secret ones are why the file is `0600` + gitignored.

### Fail-fast config (no dangerous defaults)
In production, critical vars have **no default** — if unset, the app **crashes at boot** rather than running mis-configured. My `production.py`: `SECRET_KEY = config('SECRET_KEY')` (no default), `REDIS_URL` (no default → [Ch 22](22_Redis.md)), `CSRF_TRUSTED_ORIGINS` (no default), and `DATABASE_URL` for prod. Better a loud crash than a silent insecure boot.

### Where secrets must NOT be
- **Not in code** (`SECRET_KEY = 'abc'` in settings) — it's in git history forever.
- **Not in the Docker image** (`ENV SECRET_KEY=…`) — anyone with the image reads it ([Ch 17](17_Dockerfile.md)).
- **Not in logs** — don't `print(os.environ)`.
- **Not in the committed compose** — use `env_file: .env`, not inline secrets ([Ch 18](18_Docker_Compose.md)).
Secrets live only in `.env` on the VPS (0600) + a copy in a password manager (for disaster recovery — [Ch 40](40_Disaster_Recovery.md)).

> 💡 **Samjho aise:** `.env` ghar ki **chaabiyon ka guchcha** hai — password, secret key, database ka pata. Guchcha **kabhi git mein nahi jaata** (poori duniya ko chaabi baant dena hoga). Code mein likha hota hai *"chaabi guchche se le lo"*, aur guchcha server pe alag rehta hai. Guchcha kho gaya = restore karke bhi taala nahi khulega.

# Real World Example (My ERP)
- **`.env` on the VPS** holds the real values; **`.env.example`** (committed) documents 21 vars: `SECRET_KEY`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `DATABASE_URL`, `REDIS_URL`, `POSTGRES_DB/USER/PASSWORD`, `DOMAIN`, email, OAuth, restic creds.
- **Compose injects them:** `app` + `backup` use `env_file: .env`; `caddy` gets `environment: { DOMAIN }`; `db` gets `POSTGRES_*` ([Ch 18](18_Docker_Compose.md)).
- **`.gitignore`** excludes `.env` — verified not tracked (RC1 security). `.env.example` = placeholders only, safe to commit.
- **Fail-fast:** unset `SECRET_KEY`/`REDIS_URL`/`CSRF_TRUSTED_ORIGINS` → the app won't boot (deliberate). The base `SECRET_KEY` dev fallback only applies to `test`/`migrate` commands that don't need real crypto ([Ch 24](24_Django_Settings.md)).
- **Disaster-recovery pair:** the off-site restic repo **+** the `.env` copy in a password manager = everything needed to rebuild ([Ch 40](40_Disaster_Recovery.md)). Losing `.env` with no copy = you can't decrypt backups / can't reboot the stack.
- **Permissions:** `.env` is `chmod 600` on the VPS ([Ch 08](08_File_System.md)) — only the owner reads it.

# Visual Diagram
```
  CODE (in git, identical everywhere)          CONFIG (per environment, NOT in code)
  settings read config('X') ◄──────────────── .env  (VPS, 0600, GITIGNORED)
                                                 SECRET_KEY=…  ← secret
                                                 DATABASE_URL=…@db:5432 ← secret
                                                 DEBUG/ALLOWED_HOSTS/DOMAIN ← non-secret
        docker compose: env_file: .env / environment:  ──► container env ──► os.environ

  committed:  .env.example (placeholders only)   |   NEVER committed: .env
  fail-fast:  config('SECRET_KEY')  (no default) → unset ⇒ boot CRASH (loud > insecure)
  DR pair:   off-site backups  +  .env in a password manager
```

# Practical — how to inspect it
```bash
cat .env.example              # which vars exist (placeholders) — the documentation
git check-ignore .env         # prints ".env" if correctly gitignored (safe)
git ls-files | grep -x .env   # MUST be empty — .env must NOT be tracked
stat -c '%a' .env             # 600 (owner-only) — Ch08
```
```bash
# What env does the running app actually see?
docker compose exec app printenv | grep -E 'DEBUG|ALLOWED_HOSTS|DOMAIN'   # non-secrets, safe to view
# (avoid dumping SECRET_KEY/passwords to your terminal/logs)
```
```bash
# Prove fail-fast (TEST stack): blank SECRET_KEY → app refuses to boot
#   temporarily unset it in a test .env → docker compose up → boot error (by design)
```

# Production Walkthrough
- One `.env` on the server holds every environment-specific value: `SECRET_KEY`, `DB_PASSWORD`, `ALLOWED_HOSTS`, `DEBUG`, `DB_HOST`, `REDIS_URL`, backup and email settings — 21 documented variables in `.env.example`.
- **`.env` is gitignored; `.env.example` is committed.** The example documents names and shapes with placeholders and never real values.
- Compose injects them, so the same image runs on laptop and server with different behaviour (ch 18).
- This is what makes `DEBUG=False` in production a configuration fact rather than a code edit (ch 34).

# Debugging Guide
1. **`docker compose config`** — see the resolved values. A blank means "not set", and that explains most odd behaviour.
2. **"Improperly configured / SECRET_KEY missing"** — the variable never reached the container; check the file name, location and quoting.
3. **DisallowedHost** — `ALLOWED_HOSTS` missing your domain (ch 24).
4. **Works locally, fails in Docker** — usually `DB_HOST` (ch 19).
5. **Changed `.env`, nothing happened** — variables are read at start-up; recreate the containers.

# Performance Notes
- Read once at start-up; zero runtime cost.
- Restart is required for changes, which is a small price for not having secrets in code.
- Keep the file small; long files invite copy-paste mistakes between environments.

# Security Considerations
- **A leaked `SECRET_KEY` means forged sessions and tampered signed values.** Rotating it logs everyone out — do it anyway.
- Treat a leaked `DB_PASSWORD` as a database compromise: rotate, then check access logs.
- **Never commit `.env`.** If it happens, rotate every value in it — deleting the commit is not enough, git history and any clone still hold it.
- `chmod 600 .env`, owned by the deploy user. Anyone who can read it owns the system.
- Do not print environment variables in logs or error pages.

# Architecture Decisions
- **Twelve-factor config**: one image, many environments.
- **`.env.example` as living documentation**, so a new deploy has a checklist instead of guesswork.
- **Secrets in a file rather than in compose**, because compose is in git.
- Placeholders only in committed files — the repository must never contain a real secret.

# Best Practices
- After editing `.env`, run `docker compose config`, then recreate.
- Add a variable to `.env.example` in the same commit that starts using it.
- Back up `.env` separately and securely; it is not in git, so nothing else protects it.
- Rotate on any suspicion. Rotation is cheap; investigation is not.

# Beginner Mistakes
- **Committing `.env`** → secrets in git history forever (rotate everything if this happens). Gitignore it; commit only `.env.example`.
- **Baking secrets into the image** (`ENV SECRET_KEY=`) → in every copy of the image ([Ch 17](17_Dockerfile.md)).
- **Hardcoding secrets in `settings.py`** → in git. Use `config('SECRET_KEY')`.
- **Giving prod secrets a default** → app silently runs insecure if the env is missing. No defaults for critical prod vars.
- **`.env` world-readable** → other users on the box read your DB password. `chmod 600`.
- **Losing `.env` with no backup copy** → can't reboot the stack / can't decrypt restic backups. Keep a copy in a password manager.
- **Printing `os.environ`** in a debug view/log → leaks secrets.

# Interview Questions
- **Junior:** "Why put config in environment variables instead of settings.py?" — So the same code runs everywhere with different, environment-specific values, and secrets stay out of the codebase/git. It's the 12-factor "config in the environment" principle.

- **Mid:** "What's the role of `.env` vs `.env.example`?" — `.env` holds the real (secret) values for an environment and is gitignored; `.env.example` is committed with placeholder values to document which vars are required, so the config is reproducible without exposing secrets.

- **Senior:** "Why do critical prod settings have no default, and what's the trade-off?" — No default means the app crashes at boot if a required secret/config is missing — you can't accidentally run with a weak fallback (e.g. an insecure SECRET_KEY or a bypassed rate-limiter). Trade-off: a misconfigured deploy fails loudly instead of limping insecurely — which is exactly what you want for security-critical values.

- **Staff:** "Design secret management for this ERP now and as it grows." — Now: `.env` on the VPS (0600, gitignored) + `.env.example` in git + a copy of `.env` in a team password manager for DR; fail-fast on critical vars; never in image/logs/git. As it grows: move to a secrets manager (Vault/Doppler/cloud Secrets Manager) injected at deploy, enable rotation + audit, and per-environment scoping (dev/staging/prod). Keep the fail-fast contract regardless. The invariant: secrets are injected at runtime, never at build, never committed, and always recoverable for DR.

### Why interviewers ask these — and the answer that separates levels

| Testing for | Weak answer | What lands |
|---|---|---|
| `.env` vs `.env.example` — do you know why both exist? | "One is real, one is a template." | `.env` holds real values and is **gitignored**; `.env.example` is **committed with placeholders** so the required config is **documented and reproducible without exposing a secret**. Here that is 21 documented variables. |
| Do you know why critical settings have **no default**? | "Defaults make it easier to run." | A default means you can **accidentally run with a weak fallback** — an insecure `SECRET_KEY`, a bypassed rate-limiter. No default = **crash at boot**, loudly, before serving anyone. Fail-fast beats fail-quietly on anything security-relevant. |
| Do you know when variables are read? | "Change the .env and it picks it up." | **At start-up only** — you must recreate the containers. And **`docker compose config`** shows the resolved values, which answers most "why is it connecting to nothing" questions in one command. |
| Committed a secret — do you know the real remedy? | "Delete the commit and force-push." | **Rotate every value in the file.** Git history and every existing clone still hold it, so removing the commit is not containment. Rotation is cheap; assuming the leak was harmless is not. |

**The killer follow-up:** *"How does secret management evolve as this grows?"* — **now**: `.env` at `0600`, gitignored, `.env.example` in git, and **a copy of `.env` in a password manager for disaster recovery** (it is not in git, so nothing else protects it). **Later**: a secret manager with rotation and audit. The DR copy is the part people forget until a restore stalls on a missing secret.

# Revision Notes
- Config outside code: one `.env` per environment, one image everywhere.
- **`.env` gitignored · `.env.example` committed with placeholders** (21 vars).
- Must-set: `SECRET_KEY`, `DB_PASSWORD`, `ALLOWED_HOSTS`, `DEBUG=False`, `DB_HOST`, `REDIS_URL`.
- Variables read at **start-up** — edit then recreate containers.
- ⚠️ Committed a secret? **Rotate it.** Deleting the commit does not help.

# Cheat Sheet
- **Config in the environment** (12-factor), not code/image. Django reads `config('X')`.
- **`.env`** = real values, **gitignored + 0600**; **`.env.example`** = committed placeholders (docs).
- **Secrets** (SECRET_KEY, DB pass, DATABASE_URL, restic pass) NEVER in git/image/logs.
- **Fail-fast:** critical prod vars have **no default** → unset = boot crash (loud > insecure).
- **DR pair:** off-site backups + `.env` in a password manager.
- Check: `git check-ignore .env`, `git ls-files|grep .env` (empty), `stat -c%a .env` (600).

# My ERP Section
| Concept | In my ERP |
|---|---|
| Real values | `.env` on VPS (0600, gitignored) |
| Documentation | `.env.example` (21 vars, placeholders, committed) |
| Injected via | compose `env_file: .env` (app/backup) + `environment` (caddy/db) |
| Fail-fast vars | `SECRET_KEY`, `REDIS_URL`, `CSRF_TRUSTED_ORIGINS`, prod `DATABASE_URL` |
| Secrets held | SECRET_KEY, POSTGRES_PASSWORD, DATABASE_URL, email/OAuth, restic |
| DR requirement | `.env` copy in password manager + off-site backups |

# Practice Tasks
1. **Read the code:** open `.env.example` and mark each variable as secret / environment / feature-flag.
2. **Debug:** blank out `ALLOWED_HOSTS`, restart, and read the exact error. Then fix it.
3. **Design:** write the rotation runbook for `SECRET_KEY` — steps, expected impact on users, verification.
4. **Architecture:** argue why `DEBUG` is configuration rather than a code branch.

# Homework
1. `cat .env.example` — list which vars are secret vs non-secret. Which have no default in prod?
2. `git check-ignore .env` and `git ls-files | grep -x .env` — prove `.env` is not tracked. What would you do if it *were* committed?
3. `stat -c '%a' .env` — is it 600? Why does that matter on a multi-user box?
4. In `production.py`, find one `config('X')` with no default. Explain what happens at boot if it's unset, and why that's safer than a default.
5. Name the two things (a file + a repo) that together let you rebuild the whole ERP after losing the VPS.

---

# Further Reading & Live Resources
- The Twelve-Factor App — *III. Config*: https://12factor.net/config
- python-decouple (the `config()` helper): https://pypi.org/project/python-decouple/
- Django docs — *SECRET_KEY* + settings: https://docs.djangoproject.com/en/5.0/ref/settings/#secret-key
- DigitalOcean — *Django env vars / settings for prod*: https://www.digitalocean.com/community/tutorials/how-to-set-up-django-with-postgres-nginx-and-gunicorn-on-ubuntu-22-04
- GitGuardian — *why secrets in git are dangerous + remediation*: https://blog.gitguardian.com/how-to-handle-secrets-in-git/
- Docker docs — *environment variables in Compose*: https://docs.docker.com/compose/how-tos/environment-variables/
