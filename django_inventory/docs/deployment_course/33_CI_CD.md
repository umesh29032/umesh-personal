---
id: deploy-course-33-ci-cd
type: lesson
status: active
owner: handwritten
scope: deployment, operations — this ERP shipped to a VPS
anchors: docker-compose.yml, deploy/entrypoint.sh, deploy/Caddyfile, deploy/backup.sh
verified: 2026-08-01
---

# 33 — CI/CD (Continuous Integration / Delivery)

> Part of [Deployment Course](00_COURSE_OVERVIEW.md). Prev: [32 — Error Tracking with Sentry](32_Sentry.md). Next: [34 — Production Security](34_Production_Security.md).

# Learning Objectives
By the end of this chapter you can:
- explain what CI would catch that a human will not
- describe the pipeline this project deserves
- explain why the test battery must run sequentially on a fresh database
- decide how far to automate deployment

# Purpose
To automate the path from "I committed code" to "it's safely running in production" — running the checks and the deploy the same way every time, so a human never forgets a step. This chapter maps my **real** automation today (pre-commit hooks + `deploy.sh`) and the CI/CD pipeline I'd add next.

# The Problem
Manual deploys are where mistakes live: you forget to run the tests, skip `collectstatic`, deploy an un-migrated branch, or push code that a linter would have rejected. Each is a 2am incident waiting to happen. **CI/CD** makes the checks and the deploy **scripted, automatic, and identical every time** — so quality gates can't be skipped and a deploy is one boring command, not a nervous ritual.

# Theory (from zero)

### CI vs CD
- **Continuous Integration (CI)** — every push automatically runs the quality gates: lint, type-check, **tests**, migration-drift check, build. Catches breakage *before* it merges.
- **Continuous Delivery (CD)** — every green build is automatically made *deployable* (image built + pushed), and deploying is one click/command.
- **Continuous Deployment** — goes further: green build → auto-deployed to prod with no human. (Most small teams stop at Delivery — a human presses the button.)

### The pipeline (stages, fail-fast)
```
commit → lint → test → build image → [gate] → deploy → verify
```
Each stage must pass before the next. A red stage stops the pipeline — you never ship code that failed a gate.

### Two places gates run
1. **Locally, pre-commit** — fast checks on *changed* files at commit time (lint, format). Instant feedback, but only as reliable as each dev's setup.
2. **Server-side CI** — the *authoritative* gate on a shared runner (GitHub Actions, GitLab CI): runs the full test suite on a clean machine on every push/PR. Can't be skipped or misconfigured per-laptop.
You want both: pre-commit for speed, CI for authority.

### Idempotent, scripted deploys
A deploy should be a **script** (not remembered steps), **safe to re-run**, and **ordered for safety**: back up first, then build, then switch, then verify — with a defined **rollback**.

> 💡 **Samjho aise:** CI wo **darwaze pe khada checker** hai jo har code change pe saare test khud chala deta hai — thaka hua insaan bhool sakta hai, checker nahi. CD uske baad **khud deploy** kar deta hai. Is project ka sach: abhi CI **nahi** hai, aur isi wajah se ek purani galti 7 din tak chhupi rahi thi.

# Real World Example (My ERP)
**What's automated today:**
- **Pre-commit gate (`.pre-commit-config.yaml`, real):** two local hooks on changed files —
  - **`ruff`** (autofix, lenient F-set) on changed `*.py` (excludes migrations/env/staticfiles) — catches unused imports (F401), unused vars (F841), etc.
  - **`ds-lint`** (`scripts/ds_lint.sh --changed`) — a **ratchet** that blocks *new* inline raw design values (`#hex`, `font-size:Npx`, `border-radius:Npx`) in changed templates, enforcing the frozen design system without touching old code.
  These are the gates that (correctly) blocked a commit until I moved inline styles to scoped classes — the design system, enforced by machine.
- **Deploy script (`deploy/deploy.sh`, real):** the scripted, safety-ordered deploy, run on the VPS:
  ```sh
  pg_dump -Fc > predeploy-STAMP.dump   # ① rollback anchor FIRST
  git pull --ff-only                   # ② fetch the certified code
  docker compose build app             # ③ build new image
  docker compose up -d                 # ④ entrypoint migrates + collectstatic + gunicorn
  docker image prune -f                # ⑤ reclaim space
  # smoke-check: login, dashboard, one media file
  ```
  **Rollback** = `git checkout <previous tag>` + rerun `deploy.sh`; a bad migration = restore the pre-deploy dump ([Ch 29](29_Restore.md)).
- **The test battery:** **1878 tests**, run on a **fresh DB, sequentially** (never parallel/keepdb) — plus goldens (₹344.25/₹801/₹633) and `verify_production` ([Ch 30](30_Monitoring.md)). This is the suite CI *should* run on every push.
- **Release tagging:** releases are git-tagged (e.g. `erp-v1.0.0` = a specific SHA) — the unit CD/rollback operates on.

**Honest gap (tracked):** there is **no server-side CI pipeline yet** (no `.github/workflows`). The full battery is run **manually** before a release. That's fine for a solo dev but is the #1 automation upgrade — it makes the authoritative gate un-skippable.

**Recommended: a GitHub Actions CI workflow** (`.github/workflows/ci.yml`)
```yaml
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    services: { postgres: {...}, redis: {...} }     # CI DB + cache
    steps:
      - uses: actions/checkout@v4
      - run: pip install -r requirements.txt
      - run: ruff check .                            # same lint as pre-commit
      - run: python config/manage.py makemigrations --check --dry-run   # no schema drift (Ch27)
      - run: python config/manage.py test            # the 1878-test battery, fresh DB
      - run: docker build -t erp:${{ github.sha }} . # prove the image builds
```
CD later: on a tag, SSH to the VPS and run `deploy.sh` (or push the image to a registry the VPS pulls).

# Visual Diagram
```
  LOCAL (fast, per-dev)            SERVER-SIDE CI (authoritative)         CD (deploy)
  git commit                       on push/PR (GitHub Actions):           on tag / manual:
   ├─ ruff (autofix) ─┐             ├─ ruff check .                        ssh VPS → deploy.sh:
   └─ ds-lint (ratchet)┘ ✔ before   ├─ makemigrations --check (no drift)    ① pg_dump (rollback anchor)
      the commit lands              ├─ test  ← 1878 fresh-DB, sequential    ② git pull --ff-only
                                    └─ docker build (image compiles)        ③ compose build app
   RED stage ⇒ pipeline STOPS (never ship a failed gate)                   ④ up -d (migrate+collectstatic)
                                                                           ⑤ verify_production + smoke
  rollback: git checkout <prev tag> + deploy.sh ; bad migration → restore predeploy dump (Ch29)
  [GAP tracked: no .github/workflows yet — battery run manually]
```

# Practical — how to run the gates
```bash
# Pre-commit (local gate) — install once, then it runs on every commit
env/bin/pre-commit install --config .pre-commit-config.yaml
env/bin/pre-commit run --all-files            # run all hooks now (ruff + ds-lint)
```
```bash
# The checks CI should run, run them by hand today:
env/bin/ruff check .
env/bin/python config/manage.py makemigrations --check --dry-run   # fails if models drifted (Ch27)
env/bin/python config/manage.py test                               # 1878 tests, fresh DB
env/bin/python config/manage.py verify_production                  # invariant gate (Ch30)
```
```bash
# Deploy (on the VPS)
sh deploy/deploy.sh                            # dump → pull → build → up → prune → smoke
```

# Production Walkthrough
- **CI now exists** (2026-08-03): `.github/workflows/ci.yml` at the monorepo root, four jobs on every PR into `main` — `lint` (ruff + design-system ratchet), `migrations` (`makemigrations --check`), `test` (the full battery against a `postgres:16.6-alpine` service), `docs` (`knowledge_sync` must report BLOCKER=0). `test` declares `needs: [lint, migrations]`, so a typo never costs a full battery run. This chapter's earlier "no CI yet" note is superseded — see also [Git Course ch 28](../git_course/28_CI_With_GitHub_Actions.md), which teaches this exact file line by line.
- The asset CI protects: **2,033 tests** across all 14 installed apps, run **sequentially against a fresh database** — never in parallel, never with `--keepdb`, because money tests use advisory locks and shared sequences that parallel runs corrupt into false failures. Measured wall clock: **424 s**.
- **Free-tier arithmetic matters here.** Private-repo Actions is metered at ~2,000 minutes/month (public repos are unlimited). At ~7 minutes a run, that is roughly 280 runs/month — ample for a 1–2 person team. `concurrency: cancel-in-progress` means pushing twice does not pay twice, and a `paths` filter means edits to unrelated monorepo folders start no run at all. If minutes ever get tight, a **self-hosted runner on the deploy VPS** is free and unlimited; upgrading the plan is the last resort, not the first.
- Two real gotchas this file had to solve, both worth knowing: **GitHub Actions rejects YAML anchors** (`&x`/`*x`), so the database env block is repeated by hand; and the DB is configured through `DB_*` variables rather than `DATABASE_URL`, because `base.py` forces `ssl_require=True` on the `DATABASE_URL` branch — which a plain service container cannot satisfy, producing an SSL error that looks like a real failure.
- Deployment stays manual — the two-command deploy (ch 18) is already short, and a human decides *when* the factory goes down. CI gates the *merge*, not the *deploy*.
- Deployment stays manual — the two-command deploy (ch 18) is already short, and a human decides *when* the factory goes down.

# Debugging Guide
1. **Green locally, red in CI** — usually environment: missing `.env` values, different Postgres version, or a timezone assumption.
2. **Flaky failures** — first suspect parallelism or shared state, not the code. This project has already seen a wall-clock timeout produce fake failures under load.
3. **Slow pipeline** — cache dependencies; do not cache the database.
4. **Passing CI, failing production** — CI does not test the server. That is what `verify_production` is for (ch 30).

# Performance Notes
- Fresh-database sequential runs are slower and are the correct trade for trustworthy money tests.
- Dependency caching is the cheapest large win.
- Split fast checks (lint, `check --deploy`) before the slow battery so obvious breakage fails in seconds.

# Security Considerations
- **CI secrets are production secrets.** A pipeline with deploy rights is a path into the server.
- Never echo secrets in build logs; masked variables still leak through `set -x`.
- Pull requests from forks must not receive secrets.
- Restrict who can change the pipeline definition — it runs with the pipeline's privileges.

# Architecture Decisions
- **Tests exist and are trusted; automation of running them is the gap** — capability first, convenience second.
- **Sequential fresh-database battery** as a hard rule, derived from how the money paths lock.
- **Manual deploy** so a factory outage is always a human decision.
- **Recorded as open** rather than partially wired.

# Best Practices
- Run the full battery before every release, with or without CI.
- Put `check --deploy` in the pipeline so nobody has to remember it.
- Never weaken a test to make the pipeline green.
- Keep the pipeline definition in the repository, reviewed like code.

# Beginner Mistakes
- **Deploying by remembered steps** → one gets skipped eventually. Script it (`deploy.sh`) and make it re-runnable.
- **Relying only on pre-commit** → it's per-laptop and skippable (`--no-verify`). Add server-side CI as the authority.
- **No migration-drift check in CI** → a model change without a migration ships and 500s. `makemigrations --check`.
- **Tests with `--keepdb`/parallel in CI** → hides ordering/fresh-DB bugs. My battery is deliberately fresh-DB + sequential.
- **No pre-deploy backup** → a bad deploy is unrecoverable. `deploy.sh` dumps first ([Ch 29](29_Restore.md)).
- **No rollback plan** → a bad release means panic. Tag releases; rollback = checkout previous tag + `deploy.sh`.
- **Auto-deploying to prod with no gate** (full Continuous Deployment) before you have solid tests/monitoring → ship bugs fast. Stop at Delivery (human presses go) until confidence is high.

# Interview Questions
- **Junior:** "CI vs CD?" — CI automatically runs quality gates (lint/tests/build) on every push to catch breakage early; CD automatically makes every green build deployable (and optionally deploys it), so releasing is one reliable command.

- **Mid:** "What gates run in your pipeline and where?" — Locally, pre-commit runs `ruff` + a design-system `ds-lint` ratchet on changed files. The authoritative gates (recommended in CI) are `ruff`, `makemigrations --check` (no schema drift), the 1878-test fresh-DB battery, and a `docker build`. Deploy is the scripted `deploy.sh` (dump → pull → build → up → verify).

- **Senior:** "Why fresh-DB + sequential tests, and why a migration-drift check?" — Fresh-DB sequential runs catch bugs that `--keepdb`/parallel hide — order dependence, migration replayability, and state leakage between tests — which matters for a money system where a hidden ordering assumption could corrupt totals. `makemigrations --check` fails the build if models changed without a committed migration, preventing a deploy where code and schema disagree ([Ch 27](27_Migrations.md)).

- **Staff:** "Design the CI/CD for this ERP and its rollback story." — CI on every push/PR: lint → migration-drift check → the full fresh-DB battery + goldens + `verify_production` → build the image; branch protection blocks merge on red. CD on a release tag: build/push the pinned image, then run the safety-ordered `deploy.sh` (pre-deploy `pg_dump` as the rollback anchor → pull → build → `up` which migrates + collects static → post-deploy `verify_production` + smoke). Rollback is deterministic: `git checkout <previous tag>` + rerun `deploy.sh`; a bad migration restores the pre-deploy dump. Keep it Continuous *Delivery* (human presses go) given a solo operator and financial data, and only move toward auto-deploy once monitoring + error tracking ([Ch 30](30_Monitoring.md)/[Ch 32](32_Sentry.md)) make regressions obvious within minutes. The invariant: no code reaches prod without passing the same gates, and every deploy has a one-command rollback.

### Why interviewers ask these — and the answer that separates levels

| Testing for | Weak answer | What lands |
|---|---|---|
| Do you know why fresh-DB **sequential** tests are non-negotiable here? | "Parallel tests are faster and fine." | Because the money paths use **advisory locks and shared sequences** — parallel or `--keepdb` runs turn those into **false failures**, and hide order dependence, migration replayability and state leakage. Slower and trustworthy beats fast and ambiguous on a money system. |
| Do you know what `makemigrations --check` is for? | "It creates any missing migrations." | It **fails the build** if models and migrations have drifted — no file is written. It catches the "someone changed a model and forgot the migration" class **before** production meets "column does not exist" (ch 27). |
| Can you order the gates sensibly? | "Run all the tests in CI." | **Fast checks first**: `ruff` → **migration-drift check** → `check --deploy` → then the full fresh-DB battery + goldens + `verify_production`. Obvious breakage should fail in seconds, not after a ten-minute suite. |
| ⚠️ Do you know what CI secrets really are? | "CI needs the deploy credentials." | **CI secrets are production secrets** — a pipeline with deploy rights is a path into the server. Never echo them (`set -x` leaks masked variables), never expose them to **fork PRs**, and restrict who can edit the pipeline definition, because it runs with the pipeline's privileges. |

**The killer follow-up:** *"Your pipeline is red and the fix is urgent. What do you do?"* — the wrong answer is **weaken or skip the test**. Either fix forward or roll back. A suite that gets relaxed under pressure stops being a gate exactly when you need it most.

# Revision Notes
- **CI exists** since 2026-08-03: `.github/workflows/ci.yml`, four jobs — lint · migrations · test · docs — on every PR into `main`.
- **2,033 tests** in **424 s**, run **sequentially on a fresh DB** — never parallel, never `--keepdb` (advisory locks + sequences ⇒ fake failures).
- Pipeline order: install → `check` → migrations check → battery; `test` `needs:` the cheap jobs so a typo never costs 45 minutes.
- Free tier: ~2,000 private Actions min/month (public unlimited) ⇒ ~280 runs; `concurrency` cancels superseded runs; self-hosted runner on the VPS if it ever gets tight.
- Two traps: **Actions rejects YAML anchors**; use `DB_*` vars not `DATABASE_URL` (the latter forces `ssl_require=True`).
- Deploy stays **manual** — a human decides when the factory pauses.
- ⚠️ CI secrets = production secrets. Never echo them; no secrets to fork PRs.

# Cheat Sheet
- **CI** = auto gates on push (lint/test/build). **CD** = every green build deployable (human presses go).
- Pipeline: **commit → lint → test → build → deploy → verify**; red stage stops it.
- **My local gate:** pre-commit `ruff` + `ds-lint` (design ratchet). **My deploy:** `deploy.sh` (dump→pull→build→up→prune→smoke).
- **CI should run:** `ruff`, `makemigrations --check`, the **1878 fresh-DB** battery, `docker build`, `verify_production`.
- **Rollback:** `git checkout <prev tag>` + `deploy.sh`; bad migration → restore predeploy dump.
- **Gap tracked:** no `.github/workflows` yet — add it as the un-skippable authority.

# My ERP Section
| Concept | In my ERP |
|---|---|
| Local gate | `.pre-commit-config.yaml`: `ruff` + `ds-lint` ratchet (changed files) |
| Deploy script | `deploy/deploy.sh` (dump→pull→build→up→prune→smoke) |
| Test battery | 1878 tests, fresh DB, **sequential** (+ goldens + verify_production) |
| Release unit | git tag (e.g. `erp-v1.0.0` = a SHA) |
| Rollback | checkout previous tag + `deploy.sh`; bad migration → predeploy dump |
| Server-side CI | **gap — add `.github/workflows/ci.yml`** |

# Practice Tasks
1. **Read the code:** find how the battery is invoked today and write it as a pipeline script.
2. **Debug:** run part of the suite in parallel and observe the money-test failures. Explain the cause.
3. **Design:** write the CI file you would add, fast checks first.
4. **Architecture:** argue for manual deployment in a single-factory business.

# Homework
1. `pre-commit run --all-files` — which two hooks run? What does each reject? (Tie back to the commit that got blocked.)
2. Run the four "CI-should-run" commands by hand. Which one catches a model change with no migration?
3. Read `deploy/deploy.sh` — why is the `pg_dump` step *first*? What is the exact rollback for a bad release vs a bad migration?
4. Draft a minimal `.github/workflows/ci.yml` that runs ruff + the battery on push. Why run it on a clean runner, not just pre-commit?
5. Why stop at Continuous *Delivery* (human presses go) rather than full auto-deploy for this financial app right now?

---

# Further Reading & Live Resources
- GitHub Actions — *docs / quickstart*: https://docs.github.com/en/actions
- GitHub Actions — *Django example workflow*: https://docs.github.com/en/actions/automating-builds-and-tests/building-and-testing-python
- pre-commit — *framework docs*: https://pre-commit.com/
- Ruff — *linter docs*: https://docs.astral.sh/ruff/
- Martin Fowler — *Continuous Integration* + *Continuous Delivery*: https://martinfowler.com/articles/continuousIntegration.html · https://martinfowler.com/bliki/ContinuousDelivery.html
- Django docs — *testing / `--parallel` & `--keepdb` tradeoffs*: https://docs.djangoproject.com/en/5.0/topics/testing/overview/
