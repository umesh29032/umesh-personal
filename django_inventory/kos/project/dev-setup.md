---
id: project-dev-setup
type: project
verified: 2026-07-19
knowledge_confidence: verified_against_code
answers: "Fresh machine → working dev environment → first safe commit. The canonical onboarding runbook (certification task 18's fix)."
related: [kos-start-here, project-tech-stack]
---

# Dev Setup — fresh machine to first safe commit

> 📂 [Project — the WHY layer](README.md) · [LOS home](../README.md)
> Production setup is DIFFERENT — that's [deploy/README.md](../../deploy/README.md)
> (VPS runbook). This page = your laptop. *(Yeh tumhari machine ke liye hai,
> server ke liye nahi.)*

## 0. What you're installing (2 minutes of orientation)

Django 5.0.1 + PostgreSQL app, venv-based, `.env`-configured, seeded by its
own `devseed` engine. Redis is production-only for dev purposes — local
settings use in-memory cache, so you can skip Redis today
([tech-stack](tech-stack.md)).

## 1. Clone + Python

```bash
git clone <your-remote> umesh-personal && cd umesh-personal/django_inventory
python3 --version        # 3.12-class expected; match what runs in the repo's env/
python3 -m venv env
source env/bin/activate  # you'll see (env) in the prompt
pip install -r requirements.txt -r requirements-dev.txt
```

House convention (memorize): every manage.py call is
**`env/bin/python config/manage.py <cmd>`** — works without activating too.

## 2. PostgreSQL

Install PostgreSQL (16.x — production pins 16.6-alpine; match major
version). Create your dev database + user, e.g.:

```bash
sudo -u postgres psql -c "CREATE USER dev WITH PASSWORD 'dev' CREATEDB;"
sudo -u postgres psql -c "CREATE DATABASE inventory_dev OWNER dev;"
```

**The scratch law (before you seed ANYTHING):** long-lived team dev DBs are
protected (sentinel rows prove restores; seeding them is forbidden — only
designated `inventory_seed_scratch_*` DBs). On YOUR fresh machine, your own
new `inventory_dev` is yours to seed freely. The law bites when you later
touch a shared/primary dev DB — ask before seeding anything you didn't create.

## 3. Environment

```bash
cp .env.example .env     # then fill EVERY value — the file shows what's needed
```

Missing required values = loud boot crash BY DESIGN
([settings](../concepts/django/settings.md) — fail-fast, don't add defaults).
DB values point at your `inventory_dev`; secret can be any long random for dev.

## 4. Migrate + verify the skeleton

```bash
env/bin/python config/manage.py migrate      # full chain from zero — every run of
                                             # CI does exactly this (fresh-DB law)
env/bin/python config/manage.py runserver    # settings: config.settings.local
```

Open `http://127.0.0.1:8000/` → you should meet the login page. Ctrl-C.

## 5. Seed a real world

```bash
# the demo world: minimal + one settled money journey
env/bin/python config/manage.py seed_demo
# or the full factory: T-SHIRT + LOWER + 3-PATTI golden worlds + machines
env/bin/python config/manage.py seed_factory
# every seeder supports a dry-run flag that prints the plan and writes nothing
```

devseed seeds THROUGH the real services (single-writer law holds even for
test data) and leaves a manifest — scenarios live in
`config/devseed/scenarios/`. *(Seeder bhi asli raste se hi chalta hai.)*

## 6. Dev login

The seeded dev cast uses `dev.*` emails with the shared dev password
(`Dev@12345` — dev machines only, obviously). Log in as the dev super-admin
first; the worker/manager cast exists for role-testing. OTP flows in dev:
codes are printed to the runserver console (no real email needed).

## 7. Verification checklist — your environment is REAL when

- [ ] `runserver` boots with zero warnings about missing env
- [ ] Login works; `/inventory/my-dashboard/` renders role-aware
- [ ] `/inventory/styleguide/` renders (the design canon, live)
- [ ] One app's tests pass: `env/bin/python config/manage.py test accounts`
- [ ] A seeded Adda opens: `/production/addas/` → any detail page
- [ ] `/expense/payroll/` shows the seeded money board
- [ ] Money check: shell → `ledger_service.worker_balance(worker)` returns
      a Decimal ([your first ledger read](../features/ledger.md))

**Full battery** (before any real PR): sequential, fresh-DB, NEVER
`--parallel`/`--keepdb` — [testing-strategy](../concepts/testing/testing-strategy.md)
explains the scar behind that law. It takes minutes; that's the price of
deterministic money tests.

## 8. First safe commit

1. Branch: `git checkout -b <your-branch>` — never commit to the default branch.
2. Pick something tiny (a kos page fix counts! Law 6 — rewrite freely).
3. Before ANY code change: the owning app's
   [Engineering Checklist](../apps/README.md) + its Change Impact section.
4. Tests for the touched app green → commit (Conventional Commits style —
   look at `git log` for the house voice) → push → PR against `main`.
5. **kos-sync:** if your change touched behavior, the matching LOS page
   updates in the SAME commit. Docs-sync (CLAUDE.md rule 12) likewise for docs/.

## When something here fails

Boot crash naming an env var → §3 (that's fail-fast working) ·
`migrate` errors → [migrations](../concepts/django/migrations.md) +
[page-slow-or-erroring §500 lanes](../debugging/page-slow-or-erroring.md) ·
seed refuses → read its message (scratch-law or scenario guards — they name
the fix).

## Learning Graph

**Before:** nothing — this IS the start. **After:** [START-HERE](../START-HERE.md)
(the time-boxed first day) → [business-story](business-story.md).
