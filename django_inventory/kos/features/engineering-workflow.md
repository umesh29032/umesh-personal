---
id: feature-engineering-workflow
type: feature
verified: 2026-08-03
knowledge_confidence: production_verified
answers: "How does code get INTO this repo — and how is `main` protected when GitHub's branch protection is a paid feature?"
related: [feature-learning-courses, concept-testing-strategy, feature-rbac-access]
---

# Engineering Workflow — how code enters this repo

> 📂 [Features](README.md) · [KOS home](../README.md)

## Business Purpose

Before 2026-08-03 there was one developer, one branch, and `git push` straight to whatever
branch was checked out. That works exactly until one of two things happens: a second person
joins, or you ship a broken `main` and the deploy runbook faithfully deploys the break.

This feature is the answer to *"how does a change get into this repo?"* — and the answer is
now the same one a real engineering team would give: **branch → commit properly → PR → CI
green → review → squash-merge → delete branch. Releases are tags.**

The rules live in **[CONTRIBUTING.md](../../../CONTRIBUTING.md)** (the law). The teaching
lives in **[git_course/](../../docs/git_course/00_COURSE_OVERVIEW.md)** (the why, 40
chapters). This page is the human summary of both.

## 💡 Samjho Aise

Socho ki `main` factory ki **chaalu production line** hai. Usme seedha haath daalna mana hai
— na isliye ki tum galat ho, isliye ki line chal rahi hai aur uspe aur log khade hain.

Toh tareeka ye hai: apne **bench** pe banao (branch) → **label thik se lagao** (commit
message) → **quality check** (CI) → **koi dekh le** (review) → phir line pe lagao (merge).

Aur sabse zaroori baat: **ye system mehenga nahi hai.** GitHub paisa maangta hai iske liye,
par humne wahi cheez **muft mein** bana li — thoda alag jagah se.

## The honest bit: protection when the feature is paid

This is the part most guides skip, and it is the most important thing on this page.

**GitHub's server-side branch protection is a PAID feature on private repositories.** Free
on public repos only. Same for CODEOWNERS auto-assignment. Owner ruling: no paid tiers — the
budget is for deploy infrastructure. So *"you may not push to main"* cannot be bought here.

It is instead **three layers**, and each one's weakness is written down rather than hidden:

| Layer | What it is | Where it runs | Honest limit |
|---|---|---|---|
| **1** | `git-hooks/pre-push` refuses `main`/`master` | your machine | Hooks live in `.git/hooks/`, which git **never clones**. Only binding where `git-hooks/install.sh` was run. **This is a real gap** — hence onboarding step 1 |
| **2** | Collaborators get **Read** access and work from a **fork** | GitHub, server-side | None. With Read there is no push permission at all — **stronger** than branch protection, which merely says "not there" |
| **3** | CI on every PR | GitHub Actions | On free, merge-on-red is not mechanically blocked; the signal is visible, the discipline is human |

Layer 2 is the insight worth keeping: the *free* answer is stronger than the paid one. Paid
branch protection hands someone a key and puts a lock on one door. A fork never hands over a
key at all.

> If this repo ever goes public, or a plan is ever bought, turn on server-side protection
> **and keep all three layers.** The hook staying installed costs nothing.

## Mental Model

```
        YOU                                  A COLLABORATOR
         │                                          │
   git switch -c feat/x                       forks the repo
         │                                          │
   commit  ──► commit-msg hook                pushes to THEIR fork
         │     (Conventional Commits or reject)     │
   git push origin feat/x                     opens a PR from the fork
         │     ▲                                    │
         │     └─ pre-push hook blocks              │  (has Read only →
         │        `main`, allows branches           │   cannot push here,
         ▼                                          ▼   cannot merge)
    ┌──────────────────── Pull Request ────────────────────┐
    │  CI: lint → migrations → test (2033) → docs          │
    │  Review: money · permissions · tests · docs · mobile │
    └──────────────────────────┬───────────────────────────┘
                               │ squash-merge (owner only)
                               ▼
                             main  ──► tag erp-vX.Y.Z ──► deploy
```

## The four CI gates

`.github/workflows/ci.yml`, on every PR touching `django_inventory/**`:

| Job | What it refuses to let through |
|---|---|
| `lint` | ruff problems; **new** inline `#hex` / `font-size:Npx` in changed templates (the design-system ratchet) |
| `migrations` | a model changed with no matching migration — the classic "works locally, 500s on deploy" |
| `test` | the full **2033-test** battery, sequential on a fresh Postgres. Measured: **424 s** |
| `docs` | `knowledge_sync` reporting any BLOCKER — rule 12, docs drift is an architecture bug |

`test` declares `needs: [lint, migrations]`, so a typo never costs a 45-minute battery.

**Why all 14 apps are named explicitly** instead of a bare `manage.py test`: `bod` was once in
`INSTALLED_APPS` but in **no test group** — 37 tests sitting outside the gate through two
"all green" baselines, hiding a real UTC/IST money bug. *battery == discovery* is the
invariant. See [the date-bug story](../debugging/README.md).

## Free-minute discipline (why the config looks paranoid)

Private-repo Actions ≈ **2,000 minutes/month**; public is unlimited. At ~7 min a run that is
~280 runs — plenty. The config protects it anyway:

- `concurrency: cancel-in-progress` — push twice, pay once
- `paths` filter — editing a sibling monorepo folder starts **no** run
- `timeout-minutes` on every job — a hung job cannot drain the month
- cheap jobs gate the expensive one

If it ever gets tight: a **self-hosted runner on the deploy VPS** is free and unlimited.
**Upgrading the plan is the last resort, not the first.**

## Three gotchas that cost real debugging

Recorded because each one produced a failure that looked like something else:

1. **GitHub Actions rejects YAML anchors** (`&x` / `*x`). The first draft of `ci.yml` used
   them to share the database env block; it would never have parsed. The block is now
   repeated by hand — ugly, but it runs.
2. **`DATABASE_URL` forces `ssl_require=True`** in `config/settings/base.py`, which a plain
   Postgres service container cannot satisfy. CI therefore uses the `DB_*` variables. Using
   `DATABASE_URL` produces an SSL error that reads like a real test failure.
3. **`scripts/ds_lint.sh --changed` inspects the *staged index*** — it was written for
   pre-commit. In CI nothing is staged, so it would exit 0 and prove nothing. Fixed with
   `git reset --soft $(git merge-base origin/<base> HEAD)`, which re-presents the whole PR as
   staged so the linter runs **unmodified**. One rule, one source of truth.

## Onboarding a second developer

**Owner, once:** Settings → Collaborators → Add people → role **Read** (not Write — that *is*
layer 2).

**Them:** fork → clone their fork → `git remote add upstream …` → **`bash git-hooks/install.sh`**
→ set up the venv and `.env` → `migrate` → `seed_master_data`.

**Their daily loop:** `git fetch upstream && git merge --ff-only upstream/main` → branch →
work → push to *their* fork → PR. `--ff-only` on purpose: it **refuses** to create a merge
commit, so their `main` stays a clean mirror instead of quietly diverging.

## What breaks without this

- A broken commit on `main` makes the deploy runbook a loaded gun — anyone following it ships
  the break.
- No PR means no record of *why*. The diff survives; the reasoning does not.
- No commit format means the CHANGELOG must be written from memory, which means it is fiction.
- No CI means "I ran the tests" is a claim, not evidence — and the `bod` incident proves that
  claim can be sincerely wrong.

## Common mistakes

- **Installing the hooks on one machine and assuming you are covered.** Hooks are per-clone.
  Fresh clone ⇒ run the installer again. This is layer 1's stated weakness.
- **Giving a collaborator Write "just to make it easy".** Write includes merge. There is no
  role between Triage and Write, so Write is a merge grant.
- **`git push --force` on a shared branch.** Use `--force-with-lease`, on your own branch only.
- **Committing data.** The monorepo-root `.gitignore` blocks `*.sql`, `*.dump`, `node_modules/`
  everywhere — added after two `pg_dump` files were found in public history. `git add -f`
  still works; having to type `-f` is the point.
- **Merging your own unreviewed money change** without saying so in the PR.

## 🧠 Remember This

- **`main` is always deployable.** Every rule here is downstream of that one sentence.
- **Paid protection was unavailable, so protection moved — it did not disappear.** Three
  layers, weaknesses written down.
- **The free layer (fork + Read) is the strongest one.** No key handed over at all.
- **"go" authorises the work, not the commit.** Owner reviews before anything enters history.

## Implementation References

- The law: [CONTRIBUTING.md](../../../CONTRIBUTING.md)
- The teaching: [docs/git_course/](../../docs/git_course/00_COURSE_OVERVIEW.md) — 40 chapters
- Hooks: `git-hooks/pre-push` · `git-hooks/commit-msg` · `git-hooks/install.sh`
- CI: `.github/workflows/ci.yml` · ownership: `.github/CODEOWNERS` ·
  PR shape: `.github/pull_request_template.md` · deps: `.github/dependabot.yml`
- Releases: [CHANGELOG.md](../../../CHANGELOG.md), SemVer, annotated tags
- Related: [Learning Courses](learning-courses.md) · [RBAC & Access](rbac-access.md)
