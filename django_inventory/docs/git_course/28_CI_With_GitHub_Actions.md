---
id: git-course-28-ci-with-github-actions
type: lesson
status: active
owner: handwritten
scope: git, version control — automated verification of every pull request (CI) with GitHub Actions
anchors: .github/workflows/ci.yml, CONTRIBUTING.md, django_inventory/.pre-commit-config.yaml, django_inventory/scripts/ds_lint.sh, .github/dependabot.yml
verified: 2026-08-03
---

# 28 — CI with GitHub Actions (a robot that runs your tests before you can merge)

> Part of [Git Course](00_COURSE_OVERVIEW.md). Prev: [27 — Pre-push Protection (free branch protection)](27_Pre_Push_Protection.md). Next: [29 — Semantic Versioning & Tags](29_Semantic_Versioning_And_Tags.md).

# Learning Objectives
By the end of this chapter you can:
- define **CI**, **workflow**, **job**, **step**, **runner** and **action** without hand-waving
- read this repo's real `.github/workflows/ci.yml` top to bottom and say what each of its four jobs proves
- explain why `test` declares `needs: [lint, migrations]`, and what that saves in money and minutes
- debug the three classic "green locally, red in CI" failures
- state honestly what CI does **not** buy you on GitHub's free private tier — and what covers the gap

# Purpose
Chapters 26 and 27 put two guards on **your machine**: a pre-commit hook and a pre-push hook. Both are free, both are real — and both are only installed where somebody remembered to install them. CI is the guard that lives on **GitHub's** machines, so it cannot be skipped or forgotten. This chapter walks the actual workflow file in this repository, line by line, and teaches the vocabulary you need to read any other project's CI on your first day.

# The Problem
You finish a feature at 1 a.m., run the tests, they pass, you push, you merge. Next morning the deploy runbook is a loaded gun: `main` is broken and anyone who follows the runbook ships the break.

Why did your green tests lie? Pick any of these — every one has happened to a real developer:

- You ran only the app you touched. The **2,033-test** battery covers **14 apps**; you ran one.
- You edited a model and forgot `makemigrations`. Your local database already had the column from an earlier experiment, so nothing complained. Production has no such luck: it 500s on deploy.
- Your machine has a stale `.pyc`, a leftover `env`, a `DEBUG=True` setting, or a database row from three weeks ago that quietly makes the test pass.
- You *meant* to run the battery and got distracted.

And the sharpest version of the problem, which this project actually lived through: the app `bod` was listed in `INSTALLED_APPS` but was in **no test group**. Its **37 tests** were outside the gate through the `1878` and `1896` baselines, and they were **red** — hiding a real UTC/IST date bug on money records. The battery said "all green" because the battery had never been asked about `bod`.

A human cannot be the gate. A gate must be a machine that runs the same commands, in the same order, in the same clean room, every single time. That machine is CI.

# Theory (from zero)

### What "CI" actually means
**CI = Continuous Integration.** The original idea is not "run tests in the cloud" — it is *integrate your work into the trunk frequently, and verify every integration automatically*. Small merges, each one machine-checked. The opposite is a branch that lives for three weeks and lands as a 2,000-line surprise.

The sibling term you will hear in the same breath: **CD**, which means either **Continuous Delivery** (every green commit is *releasable*) or **Continuous Deployment** (every green commit is *actually deployed*). This project does CI plus **manual, tag-anchored** deploys — see [Ch 29](29_Semantic_Versioning_And_Tags.md).

### The five words of GitHub Actions
GitHub Actions is GitHub's built-in CI system. Its vocabulary, smallest to largest:

| Word | What it is |
|---|---|
| **action** | a reusable, packaged step someone published — e.g. `actions/checkout@v4` clones your repo |
| **step** | one thing to do: either `uses:` an action, or `run:` a shell command |
| **job** | a named list of steps that run **on one machine**, in order |
| **runner** | the machine a job gets — for `runs-on: ubuntu-latest`, a fresh throwaway Ubuntu VM |
| **workflow** | a whole YAML file in `.github/workflows/`, holding one or more jobs and the events that trigger them |

Two properties do most of the teaching work:

1. **A runner is brand new every time.** Nothing from your laptop, nothing from the last run. That is exactly why CI catches "works on my machine": your machine has history, the runner has none. The flip side — nothing is cached unless you ask for it (`cache: pip`).
2. **Jobs are parallel by default.** Independent jobs start at once. `needs:` is how you say "wait for that one first", turning the job list into a small dependency graph (a **DAG** — directed acyclic graph).

### The trigger: `on:`
A workflow does nothing until an **event** matches:

```yaml
on:
  pull_request:
    branches: [main]
    paths: ['django_inventory/**', '.github/workflows/ci.yml']
  push:
    branches: [main]
    paths: ['django_inventory/**', '.github/workflows/ci.yml']
  workflow_dispatch:
```

- `pull_request` — the important one: run before the code can land ([Ch 21](21_Pull_Requests.md)).
- `push: branches: [main]` — belt and braces, in case something lands without a PR.
- `paths:` — a **filter**. This git root is a monorepo, so editing `DSA/` or the old `Django_app/` must not start a Django build. No run started = no minutes spent.
- `workflow_dispatch` — adds a "Run workflow" button in the Actions tab, for running it by hand.

### `concurrency` — stop paying for stale answers
```yaml
concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true
```
`${{ ... }}` is an Actions **expression** — GitHub substitutes a value before the runner sees it; `github.ref` is the branch being built. One in-flight run per branch: push twice in a minute and the first run is **cancelled**, not queued. Its result was worthless anyway — and on a metered plan, its minutes were real money.

### `permissions` — least privilege for the robot
```yaml
permissions:
  contents: read
```
Every job gets an automatic `GITHUB_TOKEN`. By default it can be broad. Narrowing it to `contents: read` means that even if a dependency of a dependency turns hostile, the token it can steal cannot write to your repository. Say this in an interview and you sound like someone who has read a post-mortem ([Ch 32](32_Dependabot_And_Supply_Chain.md)).

### Service containers — a real Postgres, not a fake one
A **service container** is a second Docker container running beside your job, reachable at `localhost`. Here it is `postgres:16.6-alpine` — the *same major version as production* — because this ERP's tests assert exact money totals and real constraint behaviour, and SQLite is a different database with different rules. The `options: --health-cmd pg_isready` block makes the job wait until Postgres is genuinely accepting connections instead of racing it.

### The two ways CI lies to you
Name them, because they are the whole debugging chapter in one line:

- **A check that passes because it inspected nothing.** The design-system ratchet was written for pre-commit, so it lints the **staged index**. In CI nothing is staged — it would exit `0` and prove *nothing*. Green, and meaningless. (The fix is below, and it is beautiful.)
- **A check that fails for an environment reason, not a code reason.** The classic here: `base.py` forces `ssl_require=True` on the `DATABASE_URL` branch, and a plain service container has no TLS. Pass `DB_NAME`/`DB_USER`/`DB_HOST`… instead and the failure disappears, because it was never a real failure.

> 💡 **Samjho aise:** CI factory ke **gate pe khada quality inspector** hai. Tumhare hook (Ch 26–27) tumhare **apne bench** ka inspector hai — accha hai, par sirf us bench pe hai jahan tumne usse baithaya. CI GitHub ke gate pe baitha hai: koi bhi maal (PR) andar aaye, wahi 4 check har baar chalte hain. Aur har baar **naya khaali kamra** milta hai (fresh runner) — isliye "mere laptop pe to chal raha tha" ka bahana khatam. Ek baat yaad rakho: inspector ke haath mein saaman diya hi nahi gaya (kuch bhi staged nahi), to woh "sab theek hai" bol dega — **jhoota green** sabse khatarnaak hota hai.

# Real World Example (this repo)
The workflow is at `.github/workflows/ci.yml` (the git root — GitHub only reads workflows from the **root**, which is why this file sits beside `CONTRIBUTING.md` while every step runs with `working-directory: django_inventory`). Its shape, printed from the real file:

```
$ grep -nE '^(jobs:|  [a-z]+:|    name:|    needs:|    timeout-minutes:)' .github/workflows/ci.yml
49:jobs:
51:  lint:
52:    name: lint (ruff + design-system ratchet)
54:    timeout-minutes: 10
97:  migrations:
98:    name: migrations are complete
100:    timeout-minutes: 10
157:  test:
158:    name: test battery (14 apps, sequential fresh DB)
159:    needs: [lint, migrations]
161:    timeout-minutes: 45
214:  docs:
215:    name: documentation drift (knowledge_sync)
217:    timeout-minutes: 15
```

Four jobs, and each one answers a different question:

| Job | The question it answers |
|---|---|
| `lint` | Is the style clean, and does this PR add **new** raw hex/px values to templates? |
| `migrations` | Did a model change without its migration? (`makemigrations --check --dry-run`) |
| `test` | Does the whole battery still pass — **all 14 apps, named explicitly**? |
| `docs` | Does `knowledge_sync` report **BLOCKER=0**? (`CLAUDE.md` rule 12: code change ⇒ docs change, same PR) |

Two details worth stealing:

**The ratchet trick.** `scripts/ds_lint.sh --changed` reads the staged index. CI stages nothing. So the workflow does this, in the job:

```bash
BASE="$(git merge-base "origin/${{ github.base_ref }}" HEAD)"
git reset --soft "$BASE"
bash django_inventory/scripts/ds_lint.sh --changed
```

`git reset --soft <merge-base>` moves the branch pointer back to where the PR started while leaving the index and working tree untouched — so **every commit in the PR is now presented as staged changes** ([Ch 15](15_Undo_Reset_Revert_Restore.md) explains `--soft` properly). The linter runs *unmodified* and sees exactly the lines this PR adds. One rule, one implementation, two places. That is why the `lint` job checks out with `fetch-depth: 0`: `merge-base` needs history, and a shallow clone has none.

**No YAML anchors.** YAML lets you define `&db` once and reuse it with `*db`. GitHub Actions' parser **rejects anchors**, so the Postgres `env:` block in this file is repeated by hand, four times. Ugly repetition beats a workflow that will not parse.

# Visual Diagram
```
  git push -u origin feat/my-thing        ← pre-commit (Ch26) + pre-push (Ch27) already ran locally
            │
            ▼
   open PR → main   (paths filter: touched django_inventory/** ? if not → NO RUN, 0 minutes)
            │
            ├──────────────► concurrency group ci-<ref> : a 2nd push CANCELS this run
            ▼
   ┌────────────────────┐        ┌──────────────────────────────┐
   │ lint      (10 min) │        │ migrations         (10 min)  │   ← run in PARALLEL
   │ ruff + ds ratchet  │        │ makemigrations --check        │
   │ fetch-depth 0      │        │ + manage.py check            │
   └─────────┬──────────┘        └───────────┬──────────────────┘
             └──────────── needs ────────────┘
                           ▼
                 ┌───────────────────────────────────┐      ┌──────────────────────┐
                 │ test            (45 min timeout)  │      │ docs      (15 min)   │
                 │ 2033 tests · 14 apps named        │      │ knowledge_sync       │
                 │ SEQUENTIAL, FRESH DB, ~424 s      │      │ BLOCKER=0 or fail    │
                 │ postgres:16.6-alpine service      │      └──────────────────────┘
                 └───────────────────────────────────┘        (independent, starts at once)
                           ▼
              all green ──► squash-merge ──► main stays deployable
              any red   ──► fix, push again (old run auto-cancelled)
```

# Practical — run what CI runs, before CI does
CI runs no secret commands. Every gate has a local twin, and running the twin first is how you stop burning free minutes on typos. From `/home/tech/umesh-personal/django_inventory`:

```bash
env/bin/ruff check --force-exclude --exclude '**/migrations/**' --exclude env --exclude staticfiles config/
```
Expected: `All checks passed!` — or a list of files and rule codes.

```bash
env/bin/python config/manage.py makemigrations --check --dry-run --settings=config.settings.local
```
Expected silence (exit `0`). If it prints a proposed migration, the `migrations` job will fail — generate it and commit it in the same PR.

```bash
env/bin/python config/manage.py test core accounts inventory storefront raw_materials production tracking expense machines patterns_ai verification bod learning devseed --settings=config.settings.local
```
Expected tail: `Ran 2033 tests in ~424s` then `OK`. **Never** add `--parallel` and **never** `--keepdb`: this suite asserts exact money totals and golden settlement figures (₹344.25 / ₹801 / ₹633 / ₹225, byte-identical), and both flags make those assertions flaky. A flaky money test is worse than no money test.

```bash
env/bin/python config/manage.py knowledge_sync --settings=config.settings.local | tail -3
```
Expected: a summary containing `BLOCKER=0` (currently `BLOCKER=0, WARN=17` — WARN is advisory and does not fail CI).

To inspect the ratchet the way CI does it, **without touching your branch**, use a throwaway worktree ([Ch 17](17_Stash_And_Worktrees.md)) instead of running `git reset --soft` on real work — and know the undo in the same breath:

```bash
git worktree add /tmp/ci-probe HEAD     # throwaway checkout; your branch untouched
git reset --soft ORIG_HEAD              # UNDO an accidental soft reset (git saved the old tip here)
git reflog                              # or find the old tip by hand (Ch 16) — nothing is lost
```
`--soft` never touches your files, so it cannot destroy work; only the branch pointer moved.

# Production Walkthrough
How a real change lands here, end to end:

1. `git switch -c feat/accountant-read-tier` — branch naming per `CONTRIBUTING.md` §3.
2. Commit. The `commit-msg` hook ([Ch 25](25_Conventional_Commits.md)) rejects anything that is not Conventional Commits, over 72 chars, or ending in a period.
3. `git push -u origin feat/accountant-read-tier`. The `pre-push` hook ([Ch 27](27_Pre_Push_Protection.md)) would have refused `main`; a `feat/` branch is allowed.
4. Open the PR against `main`. `.github/pull_request_template.md` loads — fill it in. `.github/CODEOWNERS` lists `@umesh29032` for money paths like `/django_inventory/config/expense/services/`.
5. CI starts. `lint` and `migrations` go first; `docs` runs beside them; `test` waits for both cheap jobs.
6. `lint` goes red on an unused import. You fix it, push again — the in-flight run is **cancelled** by `concurrency`, so the 45-minute battery never ran for a two-character typo. This is the whole reason `test` has `needs:`.
7. All four green. Review happens against `CONTRIBUTING.md` §5: correctness, money, permissions, tests, docs, mobile.
8. **Squash-merge**, delete the branch. One feature = one commit on `main`, so it reverts cleanly ([Ch 15](15_Undo_Reset_Revert_Restore.md)).
9. `push: branches: [main]` fires the same workflow once more on the trunk. That green tick is the deploy anchor ([Ch 29](29_Semantic_Versioning_And_Tags.md)).

The honest part: on GitHub's **free private** plan, "a red PR cannot be merged" is not mechanically enforced — required status checks live in the same paid tier as branch protection. So CI here is **Layer 3** of `CONTRIBUTING.md` §2: a loud, visible, unmissable signal sitting in the PR, plus the discipline not to click merge past it. Layer 2 — collaborators get **Read** access and work from a **fork** ([Ch 20](20_Forks_And_The_Fork_Flow.md)) — is the one that is mechanically server-side and free.

# Debugging Guide
| Symptom | Cause | Fix |
|---|---|---|
| `Invalid workflow file … did not find expected alphabetic character` | You used a YAML anchor (`&db` / `*db`) | Actions rejects anchors — repeat the block by hand, as this file does |
| Ratchet job is green but obviously should not be | Nothing was staged, so `--changed` inspected zero files | `git reset --soft $(git merge-base origin/<base> HEAD)` first, and require `fetch-depth: 0` |
| `connection … SSL required` in CI only | `DATABASE_URL` branch of `base.py` forces `ssl_require=True` | Pass `DB_NAME` / `DB_USER` / `DB_PASSWORD` / `DB_HOST` / `DB_PORT` instead |
| `Your models have changes that are not yet reflected in a migration` | Model edited, migration not generated | `makemigrations`, commit it in the **same** PR |
| Money assertion fails only in CI | `--parallel` or `--keepdb` snuck in, or app order changed | Sequential, fresh DB, all 14 apps named explicitly |
| `psycopg2.OperationalError` at job start | Job raced the service container | Keep `--health-cmd pg_isready` with retries |
| A new app's tests never run, yet CI is green | The app is not in the explicit app list | Add it to the `test` step — the `bod` lesson: *battery == discovery* |
| CI never started on a PR | `paths:` filter did not match | Intended for sibling monorepo folders; if it is a real Django change, check the path |
| Job killed at exactly 45 minutes | `timeout-minutes` fired — a hang, not a slow test | Read the last log line before the cut; the cap exists so a hang cannot drain the month |
| Green on your fork's PR but a secret-using step failed | `pull_request` from a fork gets **no secrets**, by design | Do not put secrets on the PR path; the four jobs here need none |

# Performance Notes
- The battery is the cost centre: **2,033 tests, ~424 s ≈ 7 minutes**, plus dependency install.
- Private-repo Actions is metered at roughly **2,000 free minutes/month**; public repos are unlimited. Battery-only arithmetic: `2000 ÷ 7 ≈ 280` runs/month. Be honest with yourself, though — billing sums **every job**, so a full four-job PR run costs the battery *plus* lint, migrations and docs. Budget by the run, not by the battery.
- `needs: [lint, migrations]` is a money optimisation, not an aesthetic one: a lint typo costs ~3 minutes instead of ~10.
- `cancel-in-progress: true` on a branch you push to five times saves four full runs.
- `cache: pip` on `actions/setup-python@v5` turns dependency install from minutes into seconds.
- `fetch-depth: 0` is not free — this `.git` is **97 MB** (`size-pack 63.66 MiB` plus loose objects). Only the `lint` job needs full history; the others use the default shallow fetch. See [Ch 37](37_Large_Files_And_Performance.md).
- If minutes ever get tight, the escape hatch is a **self-hosted runner on the deploy VPS**: free, unlimited, uses hardware you already pay for. Upgrade the plan **last**.

# Security Considerations
- **Least privilege for the token.** `permissions: contents: read` at the top of the workflow. A compromised action then cannot push, tag or open releases.
- **Secrets never appear in this file.** `SECRET_KEY: ci-only-not-a-real-secret` is deliberately a fake — CI needs *a* key, not *the* key. Real values go in GitHub → Settings → Secrets, referenced as `${{ secrets.NAME }}`, and are masked in logs. Never `echo` one ([Ch 33](33_Secrets_And_Leaks.md)).
- **`pull_request` vs `pull_request_target`.** `pull_request` runs the PR's code **without** repository secrets — safe for forks. `pull_request_target` runs with secrets *and* write-ish context; combined with checking out the PR's code it is a well-known remote-code-execution hole. This workflow uses `pull_request`. If you ever feel tempted by `pull_request_target`, stop and read GitHub's own warning first.
- **Third-party actions are dependencies.** `actions/checkout@v4` is a mutable tag; a compromised action runs inside your job. High-security setups pin to a full commit SHA. This repo accepts the `@v4` risk for first-party `actions/*` only, and runs Dependabot on `github-actions` so bumps arrive as reviewable PRs ([Ch 32](32_Dependabot_And_Supply_Chain.md)).
- **Logs are semi-public.** Anyone with repo read access reads them. A test that prints a row of worker earnings has published it. Keep fixtures synthetic.
- **Self-hosted runners must never serve a public repo.** A fork's PR would execute arbitrary code on your VPS. If the self-hosted escape hatch is ever used, keep the repo private.

# Architecture Decisions
- **Four jobs, not one script.** Separate jobs give separate red/green ticks, so the PR tells you *which* promise broke — and lets the cheap ones gate the expensive one.
- **`needs: [lint, migrations]` for `test`.** Deliberate serialisation on a metered plan. Wall-clock cost accepted; minute cost avoided.
- **All 14 apps named explicitly** instead of bare `manage.py test`. Rejected the shorter form because of `bod`: installed, in no test group, 37 tests red and invisible. The invariant is *"battery == discovery"*.
- **Sequential, fresh DB.** `--parallel` and `--keepdb` were rejected outright: the suite asserts exact settlement money. Correct-and-slow beats fast-and-flaky when the assertion is rupees.
- **`DB_*` env vars, not `DATABASE_URL`**, because `base.py` forces `ssl_require=True` on the URL branch, which a service container cannot satisfy — the failure would be TLS noise, never a real defect. And **Postgres 16.6-alpine**, the production major: testing on a different engine tests a different application.
- **`paths` filter + `concurrency` + `timeout-minutes` on every job.** Free-tier discipline written into the config rather than left to good intentions. **No YAML anchors**, because the parser rejects them.
- **Ratchet reused via `git reset --soft`**, rather than forking the linter for CI. One rule, one implementation — a second copy would drift, and this project has already paid for drift.
- **Rejected: merge-on-red blocking.** It is paid on private repos, and the owner's ruling is that money goes to deploy infrastructure. Covered by fork-based Read access (stronger) plus discipline.

# Best Practices
- Run the local twin of every gate before pushing; CI is a safety net, not your test runner.
- Give every job a `timeout-minutes`. An unbounded hang is a bill.
- Pin the same tool versions locally and in CI. A rule that fires only in CI trains people to ignore CI.
- Name new apps/test groups in the workflow the day you create them.
- Keep `permissions:` as narrow as the job needs, at the top of the file.
- Make CI failures *readable*: `::error::` annotations and a `tee`'d log beat scrolling 4,000 lines.
- Never let a check that inspected nothing count as a pass — assert that it looked at something.
- Comment the *why* in the YAML. This project's `ci.yml` opens with a 30-line header explaining free-minute discipline; six months later that header is the only reason the constraints survive.

# Beginner Mistakes
- **"It passed on my laptop"** → your laptop has state; the runner does not. Run the *full* battery, or let CI be the truth.
- **Committing a model change without its migration** → deploy-time 500. `makemigrations --check` exists precisely to fail earlier.
- **Adding `--parallel` to make CI faster** → money assertions go flaky and you learn to ignore red. Sequential is a correctness decision.
- **Running the whole battery on a lint error** → seven wasted minutes per typo. Use `needs:`.
- **Using a YAML anchor to DRY up the env block** → the workflow will not parse at all; a broken workflow is *no* gate.
- **Believing a green check that inspected zero files** → the ratchet-in-CI trap. Green is only meaningful if the check had input.
- **Putting a real secret in the workflow file** → the file is in git forever ([Ch 33](33_Secrets_And_Leaks.md)). Use repository secrets; keep CI's key fake.
- **Switching to `pull_request_target` to "fix" missing secrets on forks** → you just handed fork authors your token. Redesign instead.
- **A new app in `INSTALLED_APPS` but not in the test list** → the `bod` incident, exactly. Silent, red, and hiding a money bug.
- **Assuming a green PR cannot be merged when red** → on this plan it can. The signal is mechanical; the block is human.

# Interview Questions
- **Junior:** "What is CI and why bother, when you already run tests locally?" — CI runs the project's checks automatically on every pull request, on a **fresh machine** GitHub provides. Local runs are partial and forgettable; CI is complete and unskippable. In this repo it runs four gates — lint, missing-migration check, the 2,033-test battery on a real Postgres, and a docs-drift check — so `main` stays deployable.

- **Mid:** "Walk me through your workflow's structure and why `test` has `needs:`." — Trigger on `pull_request`/`push` to `main`, filtered by `paths` because this is a monorepo; `concurrency` cancels superseded runs; `permissions: contents: read`. Four jobs: `lint` (ruff + design-system ratchet, `fetch-depth: 0`), `migrations` (`makemigrations --check` + `manage.py check`), `test` (14 apps named explicitly, sequential, fresh Postgres 16.6 service container), `docs` (`knowledge_sync` BLOCKER=0). `test` declares `needs: [lint, migrations]` so a 45-minute-capped battery never runs to tell me about a lint error a 3-minute job already caught — on a metered free plan that is real money.

- **Senior:** "Your design-system linter reads the staged index, but CI stages nothing. How did you keep one implementation?" — In the job I compute `git merge-base origin/$BASE HEAD` and `git reset --soft` to it. `--soft` moves only the branch pointer, so the whole PR is re-presented as *staged* changes and `ds_lint.sh --changed` runs unmodified, seeing exactly the lines the PR adds. That needs `fetch-depth: 0` for the merge base. The alternative — a CI-only fork of the linter — would drift from the pre-commit rule, and a rule with two implementations eventually has two behaviours. Also worth saying out loud: before this, the check would have exited `0` with nothing staged — a green tick that proved nothing, which is the worst failure mode in CI.

- **Staff:** "Assess this CI design's risks and how you would harden it for a financial system." — Strengths: real Postgres at the production major, deterministic sequential money tests, migration-drift and docs-drift gated, least-privilege token, explicit app list born from a real incident, and free-tier costs controlled by `paths` + `concurrency` + per-job timeouts. Gaps and hardening, in priority order: (1) **merge-on-red is not mechanically blocked** on this plan — mitigated by fork-based Read access, but the honest fix is server-side required checks when the repo goes public or a plan is bought; (2) a ~7-minute battery will grow — I would split it into a fast money/permissions subset on every push and the full battery pre-merge and nightly, never dropping the full run; (3) `actions/*@v4` is a mutable reference — pin to commit SHAs and let Dependabot bump them; (4) add coverage and migration-safety checks (no destructive DDL without an explicit review label) plus artifact upload of failures for triage; (5) alert on *no* successful run, not just on failure — a workflow silently disabled by a `paths` change looks identical to "nothing to do"; (6) keep a self-hosted runner as the minutes escape hatch, but only while the repo is private. The invariant to defend: **every app in `INSTALLED_APPS` is inside the gate** — battery == discovery.

### Why interviewers ask these — and the answer that separates levels

| Testing for | Weak answer | What lands |
|---|---|---|
| Do you know CI is a *gate*, not a chore? | "GitHub runs my tests." | Name the gates and what each one *proves*, and say what happens on red — who cannot merge, and how that is enforced on your plan. |
| Do you understand the runner is stateless? | "It runs the tests in the cloud." | Fresh VM every run, so no local state can hide a bug; nothing is cached unless you ask; a service container gives the real database at the production major version. |
| Can you spot a check that proves nothing? | "All checks are green." | Green only counts if the check had input. Give the ratchet example: nothing staged means zero files inspected and a meaningless pass. |
| Do you respect the budget? | "Minutes are free." | Free on public, ~2,000/month on private. `paths` filter, `concurrency` cancel, `needs` gating, per-job timeouts — and a self-hosted runner before a plan upgrade. |

**The killer follow-up:** *"Your CI is green. Name something it still would not catch."* — A real answer, not a boast: an app missing from the explicit test list (the `bod` incident), anything not asserted (mobile layout, visual regressions, performance), a migration that is valid but locks a table on production data, and behaviour that only appears with production data volume. CI proves the checks you wrote — it never proves the checks you forgot.

# Revision Notes
- **CI = integrate often, verify automatically.** A fresh runner is why it catches "works on my machine".
- Vocabulary: **action** ⊂ **step** ⊂ **job** (one runner) ⊂ **workflow**; `needs:` makes jobs a DAG.
- This repo: **4 jobs** — `lint`, `migrations`, `test` (`needs: [lint, migrations]`), `docs`.
- **All 14 apps named explicitly.** The `bod` lesson: installed but ungated = 37 red tests hiding a money bug. *Battery == discovery.*
- **Never `--parallel`, never `--keepdb`** — the suite asserts exact rupee totals.
- Ratchet in CI = `git reset --soft $(git merge-base origin/<base> HEAD)` + `fetch-depth: 0`.
- ⚠️ **A check that inspected nothing is a false green** — the most dangerous colour in CI.
- Free tier: `paths` + `concurrency` + `timeout-minutes`; ~2,000 private min/month; self-hosted runner before a plan upgrade.
- **Actions rejects YAML anchors.** Repeat the block.
- Merge-on-red blocking is paid → Layer 2 (fork + Read access) is the free, server-side teeth.

# Cheat Sheet
```bash
env/bin/ruff check --force-exclude --exclude '**/migrations/**' --exclude env --exclude staticfiles config/   # lint job, locally
env/bin/python config/manage.py makemigrations --check --dry-run --settings=config.settings.local            # migrations job
env/bin/python config/manage.py test core accounts inventory storefront raw_materials production tracking expense machines patterns_ai verification bod learning devseed --settings=config.settings.local   # the battery: 2033 tests, ~424 s
env/bin/python config/manage.py knowledge_sync --settings=config.settings.local | tail -3                    # docs job → BLOCKER=0
git merge-base origin/main HEAD          # the commit the PR branched from (what CI resets to)
git worktree add /tmp/ci-probe HEAD      # experiment like CI does, without touching your branch
git reset --soft ORIG_HEAD               # UNDO an accidental soft reset (files never touched)
```
- **Job keys to know:** `runs-on` · `needs` · `timeout-minutes` · `services` · `env` · `defaults.run.working-directory` · `permissions` · `concurrency` · `paths` · `workflow_dispatch`.
- **`actions/checkout@v4` + `fetch-depth: 0`** whenever a step needs history (`merge-base`, `describe`, blame).
- **`${{ secrets.NAME }}`** for real secrets; keep CI's `SECRET_KEY` an obvious fake.
- **`pull_request`** = no secrets on forks (safe). **`pull_request_target`** = danger, read the docs first.

# My ERP Section
| Concept | In this repo |
|---|---|
| Workflow file | `.github/workflows/ci.yml` (git root — GitHub reads workflows only from the root) |
| Monorepo handling | `paths: ['django_inventory/**', '.github/workflows/ci.yml']` + `working-directory: django_inventory` |
| Jobs | `lint` (10 min) · `migrations` (10 min) · `test` (45 min, `needs: [lint, migrations]`) · `docs` (15 min) |
| Battery | 2,033 tests · 14 apps named explicitly · sequential, fresh DB · ~424 s |
| Apps gated | `core accounts inventory storefront raw_materials production tracking expense machines patterns_ai verification bod learning devseed` |
| Database in CI | `postgres:16.6-alpine` service container, `--health-cmd pg_isready`, `DB_*` env (not `DATABASE_URL`) |
| Docs gate | `knowledge_sync` must report `BLOCKER=0` (currently `BLOCKER=0, WARN=17`) — `CLAUDE.md` rule 12 |
| Ratchet reuse | `git reset --soft $(git merge-base origin/<base> HEAD)` + `scripts/ds_lint.sh --changed` |
| Local twins | `django_inventory/.pre-commit-config.yaml` (ruff + `ds_lint.sh` on changed files) |
| Budget controls | `concurrency: cancel-in-progress` · `paths` · `timeout-minutes` on all 4 jobs |
| Free-tier truth | merge-on-red blocking is paid → Layer 2 = collaborators get **Read** + work from a fork |
| Companions | `.github/CODEOWNERS`, `.github/pull_request_template.md`, `.github/dependabot.yml` |

# Practice Tasks
1. **Read the file:** open `.github/workflows/ci.yml` and, without scrolling back, write down what each of the four jobs would let through if it were deleted.
2. **Run the twins:** run all four local equivalents from the Cheat Sheet. Time the battery. Does your number land near ~424 s?
3. **Find the false green:** explain, in two sentences, why `ds_lint.sh --changed` would exit `0` in CI without the `git reset --soft` line — and how you would *prove* in the log that it inspected files.
4. **Budget it:** using ~2,000 private minutes/month, estimate how many full four-job PR runs fit. Then say which single config line saves the most minutes in a normal week.
5. **Design:** you add a 15th app tomorrow. List every file you must touch so it lands inside the gate — and name the incident that makes this non-optional.

# Homework
- Add a deliberate failure locally (an unused import, or a model field with no migration) and predict *which job* catches it and *what the error text will be*. Then check yourself with the local twin.
- Read `.github/dependabot.yml`. When a Django security bump PR opens, which of the four jobs is the one that makes merging it safe? Why is that the entire argument for CI ([Ch 32](32_Dependabot_And_Supply_Chain.md))?
- The battery grows to 40 minutes. Write the split you would ship: what runs on every push, what runs pre-merge, what runs nightly — and what you refuse to move out of the pre-merge set.
- Open GitHub's docs on `pull_request_target` and write three sentences on why this workflow does not use it.
- Argue both sides in writing: pin `actions/checkout` to a commit SHA, or keep `@v4`? Decide, and record the decision the way `ci.yml`'s header records its own.

---

# Further Reading & Live Resources
- GitHub Actions — *workflow syntax reference* (every key used above): https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions
- GitHub Actions — *service containers* (the Postgres pattern): https://docs.github.com/en/actions/using-containerized-services/about-service-containers
- GitHub Actions — *security hardening* (including the `pull_request_target` warning): https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions
- GitHub Actions — *billing and included minutes*: https://docs.github.com/en/billing/managing-billing-for-github-actions/about-billing-for-github-actions
- GitHub Actions — *self-hosted runners* (the free escape hatch): https://docs.github.com/en/actions/hosting-your-own-runners/managing-self-hosted-runners/about-self-hosted-runners
- Martin Fowler — *Continuous Integration* (the original idea, still the clearest): https://martinfowler.com/articles/continuousIntegration.html
- Django docs — *testing tools and `--parallel`/`--keepdb` semantics*: https://docs.djangoproject.com/en/5.0/topics/testing/advanced/
