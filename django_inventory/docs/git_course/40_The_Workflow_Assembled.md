---
id: git-course-40-the-workflow-assembled
type: lesson
status: active
owner: handwritten
scope: git, GitHub — the complete workflow of this repository, every piece working together
anchors: CONTRIBUTING.md, git-hooks/pre-push, git-hooks/commit-msg, .github/workflows/ci.yml, .github/CODEOWNERS, CHANGELOG.md
verified: 2026-08-03
---

# 40 — The Workflow, Assembled (all of it, as one rulebook)

> Part of [Git Course](00_COURSE_OVERVIEW.md). Prev: [39 — Disaster Playbook](39_Disaster_Playbook.md). Next: — (last chapter)

# Learning Objectives
By the end of this chapter you can:
- trace a change from idea to production, naming every gate it passes
- state which gates are **enforced**, which are **advisory**, and which failures nothing catches
- reproduce this entire workflow on a new repository, on a free plan
- explain each decision's trade-off rather than reciting the rule
- onboard a second developer without handing over merge rights
- say what you would change first if the constraints changed

# Purpose
Thirty-nine chapters have covered pieces. This one assembles them.

The goal is not a summary. It is a **rulebook you could hand to a new developer**, plus the reasoning
behind each rule, plus an honest register of what the free tier cannot enforce. If you read only this
chapter you should be able to work correctly; if you read only this chapter you should also know
exactly where the gaps are.

The rules themselves live in [`CONTRIBUTING.md`](../../../CONTRIBUTING.md). This chapter is the *why*,
end to end.

# The Problem
A workflow assembled from tutorials has three predictable defects:

1. **It assumes paid features.** Almost every guide says "enable branch protection", which is not
   available on a private repository on GitHub's free plan.
2. **It hides its own gaps.** A three-layer scheme is presented as airtight, when one layer is
   bypassable with a flag and another is absent on a fresh clone.
3. **It has rules without reasons.** Rules whose purpose nobody remembers get dropped the first time
   they are inconvenient.

This chapter fixes all three: every gate is labelled *enforced* or *advisory*, the uncaught failures
are listed, and each decision carries its trade-off.

# Theory (from zero)

### The single principle
> **`main` must always be deployable.**

Every rule descends from that sentence. It is worth being concrete about why: this project has a deploy
runbook. If a broken commit reaches `main`, the runbook is a loaded gun — anyone who follows it ships
the break. So "always deployable" is not tidiness, it is the property that makes deployment safe to
delegate to a procedure.

### The pipeline, in order
```
sync → branch → commit → push → PR → CI → review → squash-merge → tag → deploy
```

Nine steps, each with a gate:

| Step | Gate | Enforced? |
|---|---|---|
| **sync** | `git merge --ff-only` refuses divergence | ✅ git itself |
| **branch** | naming convention (`feat/`, `fix/`, …) | ⚠️ convention |
| **commit** | `commit-msg` hook: Conventional Commits, ≤72 chars, no trailing period | ✅ locally |
| **commit** | `pre-commit`: ruff + design-system ratchet on **staged** content | ✅ locally |
| **push** | `pre-push` refuses `main`/`master`, including deletion pushes | ✅ locally |
| **PR** | template asks money/permissions/mobile/docs explicitly | ⚠️ human |
| **CI** | lint → migrations → 2,033 tests → docs BLOCKER=0 | ✅ runs; ⚠️ merge-on-red not blocked |
| **review** | CODEOWNERS documents ownership | ⚠️ auto-assign is paid |
| **merge** | squash → one feature = one commit | ✅ GitHub setting |
| **tag** | annotated, SemVer | ⚠️ convention |

Read the third column honestly. Four gates are mechanically enforced, and five depend on discipline.
That distribution is a *consequence of the free plan*, not of laziness, and knowing which is which is
what lets you compensate.

### Three layers of protection, and each one's weakness
Server-side branch protection is **paid on private repositories**. So:

| Layer | Where | Free? | Weakness |
|---|---|---|---|
| **1. `pre-push` hook** | your machine | ✅ | `.git/hooks/` is **never cloned** — binds only where installed |
| **2. Read access + fork** | GitHub, server-side | ✅ | none for them; does not constrain the owner |
| **3. CI on every PR** | GitHub | ✅ | merge-on-red not mechanically blocked |

**Layer 2 is the insight of this whole course.** Compare the two sentences:

- Branch protection: *"you may push, but not to that branch."* — a key, plus a lock on one door.
- Read + fork: *"you have no push."* — no key was ever handed over.

**The free option is the stronger security posture.** It is not a consolation prize.

### What nothing catches
Written down rather than hidden, because an unstated gap is the one that bites:

| Failure | Caught by |
|---|---|
| Owner on a fresh clone, hooks not installed | ⚠️ **nothing** |
| Owner deliberately runs `--no-verify` | ⚠️ **nothing** (by design) |
| Merging a red PR | ⚠️ nothing mechanical — visible, human commitment |

Row 1 is why `bash git-hooks/install.sh` is **step 1** of onboarding. Row 2 is deliberate: a gate you
cannot bypass gets deleted, whereas one requiring an explicit flag stays installed and makes the bypass
a decision.

### Why each choice, and what it costs
| Decision | Buys | Costs |
|---|---|---|
| **Trunk-based**, one long-lived branch | cheap merges, one place to fix a bug | needs CI + feature flags for unfinished work |
| **Squash-merge** | `main` = list of features; clean revert; useful bisect | loses the branch's internal commits (kept in the PR) |
| **Conventional Commits** (hook-enforced) | derivable CHANGELOG, SemVer signal, searchable log | a format to learn |
| **Releases as tags**, not branches | nothing to maintain; immutable | no parallel version support (not needed) |
| **Feature flags** default OFF | merge unfinished work with CI + review | flags accumulate; each needs an owner + expiry |
| **Read + fork** for collaborators | strongest free enforcement | extra remote; cross-repo PRs |
| **Client-side hooks** | free protection today | per-clone install; bypassable |
| **Full-history CI clone** (`fetch-depth: 0`) | the ratchet gets a merge base | slower clone (trivial at 97 MB) |

Every row is a trade. None is free. That is what makes it engineering rather than dogma.

> 💡 **Samjho aise:** Poora system ek hi vaakya se nikalta hai: **`main` hamesha deploy ke layak rahe.**
>
> Rasta: sync → branch → commit → push → PR → CI → review → squash-merge → tag → deploy. Har padav pe
> ek chowkidar.
>
> Par imaandaari se: **chaar chowkidar asli hain, paanch bharose pe hain.** Kyun? Kyunki GitHub ka asli
> taala private repo pe **paisa maangta hai**. Toh humne muft se banaya — aur har taale ki **kamzori
> likh di**, chhupayi nahi.
>
> Aur ek cheez yaad rakhna: **jo muft wala taala hai (Read + fork), wo paid se bhi mazboot hai.** Paid
> kehta hai "chaabi hai, par us darwaze pe nahi". Muft kehta hai "chaabi hi nahi di". Doosra behtar hai.

# Real World Example (this repo) — the complete rulebook

### 0. Once per clone, per machine
```bash
bash git-hooks/install.sh                 # ← STEP 1. A fresh clone is UNPROTECTED until this runs.
django_inventory/env/bin/pre-commit install \
  --config django_inventory/.pre-commit-config.yaml
```

Two systems: hand-written hooks for push and message policy, the `pre-commit` framework for linting.
Neither travels with a clone ([Chapter 26](26_Pre_Commit_Hooks.md)).

### 1. Sync — and the trap that lives here
```bash
git fetch origin
git switch main && git merge --ff-only origin/main
```

`--ff-only` **refuses** to create a merge commit. If it errors, local `main` has diverged and should be
reset rather than merged, keeping it a clean mirror.

**Why this matters more than it looks:** local `main` in this repository sat at `7c256f50` while
`origin/main` was at `83a144ba`, and a routine range query answered **296** where the truth was **1**.
Nothing was broken — `git fetch` updates `origin/main` and never your local branches
([Chapter 18](18_Remotes.md)).

### 2. Branch — one intent each
```
feat/ fix/ chore/ docs/ refactor/ test/ perf/
```
Lowercase, hyphens, short-lived, deleted after merge. The honest counter-example in this very repo:
`new_flask_app` reached **289 commits** before merging — a long-lived branch by any definition, which
produced exactly the predicted unreviewable diff ([Chapter 24](24_Branching_Strategies.md)).

### 3. Commit — two hooks fire
`git-hooks/commit-msg` rejects non-Conventional-Commits messages, subjects over 72 characters, and
trailing periods — while letting `Merge`/`Revert`/`fixup!` through. Verified: **3 rejected, 6
accepted** ([Chapter 25](25_Conventional_Commits.md)).

`pre-commit` runs ruff (`--fix`, lenient, changed `.py`) and `scripts/ds_lint.sh --changed` on
**staged** templates — a **ratchet** blocking only newly added inline `#hex` / `font-size:Npx`, so
728 existing violations do not block anyone ([Chapter 26](26_Pre_Commit_Hooks.md)).

### 4. Push — `main` is refused
`git-hooks/pre-push` reads the **destination** ref from stdin's third field (so
`git push origin HEAD:main` cannot slip past), handles deletion pushes, and prints the recovery
instructions rather than just refusing.

Verified end to end with a real push: `main` **BLOCKED** with `git ls-remote` showing **0 refs**;
`master` blocked; `feat/allowed` pushed; `--no-verify` bypassed as documented
([Chapter 27](27_Pre_Push_Protection.md)).

### 5. PR — the template asks the questions people forget
`.github/pull_request_template.md`: what & why (problem first) · how verified (**paste the count**) ·
rules 4/5/6/11/12 · **money & permissions answered explicitly even when the answer is none** · risk &
rollback · a 360px mobile screenshot · a separate reviewer checklist.

Size it first — `git rev-list --count origin/main..HEAD`. PR #15 was **289 commits / ~2,100 files /
336,372 insertions**, and the description said so rather than pretending it was reviewable
([Chapter 21](21_Pull_Requests.md)).

### 6. CI — four gates
```
lint  (ruff + design-system ratchet)
migrations  (makemigrations --check + system check)
test  (2,033 tests, real Postgres, sequential, fresh DB — 424 s)   needs: [lint, migrations]
docs  (knowledge_sync BLOCKER=0)
```

Free-minute discipline: `concurrency` cancels superseded runs, `paths` filters to
`django_inventory/**`, every job has a timeout, and cheap jobs gate the expensive one — so a typo costs
3 minutes, not 45. ~2,000 free minutes/month at ~7 min a run ≈ 280 runs
([Chapter 28](28_CI_With_GitHub_Actions.md)).

Three real gotchas solved in that file: **Actions rejects YAML anchors**; `DATABASE_URL` forces
`ssl_require=True` so CI uses `DB_*` vars; and `ds_lint.sh --changed` reads the *staged index*, so CI
runs `git reset --soft $(git merge-base …)` to present the whole PR as staged — one rule, two callers,
no duplicated linter.

### 7. Review — five axes
Money · permissions · tests (is the **failure** pinned?) · docs (rule 12, same PR) · mobile
(360/768/1280). `.github/CODEOWNERS` classifies five risk categories — money, access control,
migrations, deploy/CI, frozen architecture — with a *why* comment each. Auto-assignment is paid on
private repos, so the template points a human at the file
([Chapters 22](22_Code_Review.md)–[23](23_CODEOWNERS_And_Templates.md)).

### 8. Merge — squash
One feature = one commit on `main`. `main` reads as a list of features, each revertable as a unit,
which is also what makes [bisect](35_Bisect.md) useful.

### 9. Release — annotated tags
```bash
git tag -a erp-v1.1.0 -m "erp-v1.1.0 — accountant read tier"
git push origin erp-v1.1.0
```
`erp-v1.0.0` = `90c1f2f3`. `CHANGELOG.md` is **derived** from Conventional Commits, never written from
memory ([Chapters 29](29_Semantic_Versioning_And_Tags.md)–[30](30_Changelog.md)).

### 10. Onboarding a second developer
**Owner:** Settings → Collaborators → Add people → role **Read**. Not Write — Write includes merge, and
there is no role between Triage and Write.

**Them:** fork → clone their fork as `origin` → `git remote add upstream <this repo>` →
**`bash git-hooks/install.sh`** → venv, `.env`, `migrate`, `seed_master_data`.

**Daily:** `git fetch upstream && git merge --ff-only upstream/main` → branch → work → push to *their*
fork → cross-repo PR. They cannot merge, because they hold Read
([Chapter 20](20_Forks_And_The_Fork_Flow.md)).

### What this workflow has already caught
Not hypothetical — found while building it:

| Found | How |
|---|---|
| A **silent content-loss bug** in the learning platform: a column-0 `# ` inside a code fence truncated harvested sections. `# Conflicts:` is git's own output, so a Cheat Sheet quoting it lost everything after it | counting what chapters *claim* against what pages *show*; fixed fence-aware + 2 test pins, pin proven to fail against the old code |
| A **dead `CODEOWNERS` rule**: `/deploy/` is root-anchored, but deploy lives at `django_inventory/deploy/` — matched nothing, silently, while reading as coverage | a path-existence check ([Ch 23](23_CODEOWNERS_And_Templates.md)) |
| **Two committed database dumps** in public history, root cause = `.gitignore` scoping in a monorepo | a file-type scan of all history ([Ch 33](33_Secrets_And_Leaks.md), [Ch 36](36_Monorepo_Submodules_Subtrees.md)) |
| **4 stale "no CI" claims** in the deployment course, false the moment CI landed | docs-sync rule 12 |
| A **wrong constant** inherited from `CLAUDE.md`: "26 CheckConstraints" — actual **147** (71 models + 76 migrations, 0 on the 5.1 API) | fact-checking every number against the live codebase |
| **`bod`** installed but in **no test group** — 37 tests outside the gate through two "all green" baselines, hiding a real UTC/IST money bug | *battery == discovery* as an invariant |

Every one of those is a **silent** failure: no error, no crash, something simply not happening. That is
the class of bug this workflow exists to make visible.

# Visual Diagram
```
                    ONE PRINCIPLE: main must ALWAYS be deployable
  ═══════════════════════════════════════════════════════════════════════════

  ONCE PER CLONE          bash git-hooks/install.sh   ← STEP 1. hooks are NOT cloned.
                          pre-commit install --config django_inventory/…

  0. SYNC        git fetch && git merge --ff-only origin/main   ✅ git refuses divergence
                 ⚠ local main goes stale silently (this repo: 296 vs 1)

  1. BRANCH      feat/ fix/ chore/ docs/ refactor/ test/ perf/  ⚠ convention
                 short-lived  (counter-example here: 289 commits)

  2. COMMIT      ├─ commit-msg  Conventional Commits, ≤72, no period   ✅ local
                 └─ pre-commit  ruff --fix + ds ratchet on STAGED      ✅ local

  3. PUSH        pre-push refuses main/master + deletion pushes        ✅ local
                 destination read from stdin field 3
                 verified: BLOCKED, git ls-remote = 0 refs

  4. PR          template: what&why · verified(count) · rules 4/5/6/11/12
                 · MONEY & PERMISSIONS explicitly · rollback · 360px    ⚠ human
                 size first: git rev-list --count origin/main..HEAD

  5. CI          lint ─┐
                 migr ─┴─► test (2033 / 424 s) ─► docs BLOCKER=0        ✅ runs
                 concurrency · paths · timeouts · cheap gates expensive
                 ⚠ merge-on-red not mechanically blocked (paid)

  6. REVIEW      money · permissions · tests · docs · mobile            ⚠ human
                 CODEOWNERS: 5 risk categories   ⚠ auto-assign is paid

  7. MERGE       squash → 1 feature = 1 commit on main                  ✅ setting

  8. TAG         git tag -a erp-vX.Y.Z ; CHANGELOG derived from commits ⚠ convention

  9. DEPLOY      deliberate human act. CI gates the MERGE, not the deploy.

  ═══════════════════════════════════════════════════════════════════════════
  PROTECTION            1 pre-push hook   client   ⚠ not cloned ⇒ install per clone
  (branch protection    2 Read + fork     SERVER   ✅ strongest — no key ever given
   is PAID on private)  3 CI visible      server   ⚠ cannot block merge on free

  NOTHING CATCHES       • fresh clone without hooks
                        • deliberate --no-verify
                        • merging a red PR
```

# Practical — reproduce this on a new repository
```bash
# ── 1. protection first (root .gitignore covers every sibling — ch 36) ──────
cat > .gitignore <<'EOF'
*.sql
*.dump
db_backups/
node_modules/
.env
EOF
for p in x.sql sub/y.dump .env; do mkdir -p "$(dirname "$p")" 2>/dev/null; : > "$p"
  git check-ignore -q "$p" && echo "✓ BLOCKED $p" || echo "✗ WOULD COMMIT $p"; rm -f "$p"; done

# ── 2. hooks: commit-msg + pre-push, plus an installer (ch 25, 27) ─────────
mkdir -p git-hooks   # copy this project's three files, then:
bash git-hooks/install.sh

# ── 3. CI at the repo ROOT, path-filtered (ch 28, 36) ─────────────────────
mkdir -p .github/workflows
#   on: pull_request: branches:[main]  paths:['project/**']
#   concurrency: {group: ci-${{ github.ref }}, cancel-in-progress: true}
#   jobs: lint · migrations · test(needs:[lint,migrations]) · docs
#   NO YAML ANCHORS — GitHub rejects them.

# ── 4. ownership + PR shape (ch 23) ───────────────────────────────────────
#   .github/CODEOWNERS         general rule FIRST (last match wins!)
#   .github/pull_request_template.md
#   .github/dependabot.yml     free on every plan (ch 32)
awk '!/^#/ && NF {print $1}' .github/CODEOWNERS | while read -r p; do
  c="${p#/}"; c="${c%/}"
  [ -e "$c" ] || [ -n "$(git ls-files "$c*" 2>/dev/null|head -1)" ] || echo "✗ DEAD RULE: $p"
done

# ── 5. the rulebook + changelog ───────────────────────────────────────────
#   CONTRIBUTING.md   §2 MUST state each layer's weakness honestly
#   CHANGELOG.md      Keep a Changelog + SemVer

# ── 6. daily loop ─────────────────────────────────────────────────────────
git fetch origin && git switch main && git merge --ff-only origin/main
git switch -c feat/thing
git add -p && git commit -m "feat(scope): subject"
git rev-list --count origin/main..HEAD          # size it BEFORE opening
git diff origin/main...HEAD                     # exactly what the reviewer sees
git fetch origin && git rebase origin/main      # test the real merge result
git push -u origin feat/thing
gh pr create --base main --fill
gh pr checks
gh pr merge --squash --delete-branch

# ── 7. release ────────────────────────────────────────────────────────────
git tag -a v1.1.0 -m "v1.1.0 — what changed"
git push origin v1.1.0
```

# Production Walkthrough
A real change, end to end, with the reasoning at each step:

1. **Sync.** `git fetch` + `--ff-only`. Skipping this produces a noisy PR diff full of commits that are
   already on `main`.
2. **Branch by intent.** `git switch -c feat/accountant-read-tier`.
3. **Work in atomic commits.** `git add -p` when one file holds two ideas — atomicity is what makes
   `revert` and `bisect` useful later.
4. **Commit; the hooks fire.** Message format enforced; ruff autofixes; the ratchet blocks new inline
   raw values. Re-stage after autofix.
5. **Size it.** `git rev-list --count origin/main..HEAD`. Too big? Split, or say in the PR which part
   needs the attention.
6. **Rebase onto `origin/main`** so CI evaluates the real post-merge state.
7. **Push the branch.** The hook refuses `main`.
8. **Open the PR; fill the template.** The money and permissions questions are mandatory *because*
   silence is indistinguishable from "no impact".
9. **Watch CI.** `lint` and `migrations` gate `test`.
10. **Review on five axes.** Read the gate, not the comment above it.
11. **Squash-merge, delete the branch.**
12. **Update docs in the same PR** (rule 12 — drift is treated as an architecture bug).
13. **Release when it makes sense**: annotated tag + `CHANGELOG.md`.
14. **Deploy deliberately.** A factory pausing production is a human decision.

# Debugging Guide

| Symptom | Cause | Fix |
|---|---|---|
| Hooks do nothing | fresh clone; `.git/hooks/` is never cloned | `bash git-hooks/install.sh` |
| Range query gives absurd numbers | stale local `main` | `git fetch` + `merge --ff-only` |
| Commit rejected | not Conventional Commits, >72 chars, or trailing period | fix the message; `--no-verify` only deliberately |
| Push to `main` refused | working as designed | branch and open a PR |
| PR diff enormous / unrelated files | branched from a stale base | `git rebase origin/main` |
| CI green locally, red in CI | environment: Postgres version, missing env var, timezone | read the failing job; reproduce with the same settings module |
| Ratchet passes CI but proves nothing | nothing staged in CI | the `git reset --soft $(git merge-base …)` line is the fix |
| Workflow will not parse | YAML anchors — **Actions rejects them** | repeat the block by hand |
| CI database SSL error | `DATABASE_URL` forces `ssl_require=True` | use `DB_*` vars |
| CODEOWNERS never requests anyone | auto-assign is **paid** on private repos | expected; the template asks a human |
| A CODEOWNERS rule never fires | leading `/` anchors to repo root | run the dead-rule check |
| `gh pr create` → "must be a collaborator" | `gh`'s token is a different account than SSH | `gh auth status` / `gh auth switch` |
| Ignore rule works in one folder, not a sibling | a `.gitignore` guards only its own subtree | put it at the **root** |
| Lost commits | reflog | `git reflog`; `git branch rescue <hash>` ([Ch 39](39_Disaster_Playbook.md)) |

# Performance Notes
- **Battery: 2,033 tests in 424 s**, sequential on a fresh Postgres. At ~7 min a run, ~2,000 free
  private-repo Actions minutes/month ≈ **280 runs**.
- **Cheap jobs gate the expensive one.** A lint error costs ~3 minutes, not 45.
- **`concurrency: cancel-in-progress`** — pushing twice does not pay twice.
- **`paths` filter** — editing a sibling monorepo folder starts **no** run.
- **`fetch-depth: 0`** deliberately (the ratchet needs a merge base); trivial at 97 MB, a real decision
  at 5 GB.
- **Small PRs are faster end to end**: less rebasing, fewer conflicts, quicker review.
- **`git rev-list --count`** beats `git log | wc -l`.
- **Escape hatch if minutes get tight:** a self-hosted runner on the deploy VPS — free and unlimited.
  Upgrading the plan is last.

# Security Considerations
- **Settlement is the only money-write boundary.** A new money-write path outside an approved
  single-writer service is a **STOP**, not a review comment — and the PR template forces the question.
- **Layer 2 (Read + fork) is the only genuinely enforced layer for non-owners**, and it is free.
- **Client-side hooks stop mistakes, not adversaries.** `--no-verify` exists; hooks are not cloned.
  Never part of a threat model.
- **`git add` is when a secret enters the object store** — before any hook runs. Layer:
  `.gitignore` → hooks → CI → review ([Chapter 33](33_Secrets_And_Leaks.md)).
- **Protective rules at the repository root** in a monorepo. A correct-but-narrow rule is more
  dangerous than a missing one, because it reads as coverage.
- **Secret scanning and push protection are paid** on private repos — substituted by `.gitignore`,
  hooks, and the template's force-add question.
- **`.github/`, `git-hooks/` and `.gitignore` are owned paths**, because editing them can disable every
  other gate.
- **`--force-with-lease`, never plain `--force`** on anything shared.
- **Rotate before cleanup.** Always.

# Architecture Decisions
- **`main` always deployable** — the axiom everything else derives from.
- **Trunk-based**: one long-lived branch, short-lived feature branches, releases as tags. One developer,
  one deploy target, nobody running an old version.
- **Squash-merge**: `main` is a list of features; revert and bisect operate on features.
- **Conventional Commits, hook-enforced**: makes the CHANGELOG derivable and the SemVer bump mechanical.
- **Three protection layers with weaknesses documented**, because branch protection is paid — and Layer
  2 is chosen as the *stronger* option, not a fallback.
- **`--no-verify` deliberately available**: an unbypassable gate gets deleted; one requiring a flag stays.
- **Feature flags default OFF** for unfinished work, and **retired** when done —
  `ENFORCE_ALLOCATION_BOUND` was deleted outright once testing showed its off-default was itself the
  defect.
- **Docs in the same PR** (rule 12): documentation drift is treated as an architecture bug.
- **Mobile + tablet + desktop verified** (rule 11): mobile-first is functional, not polish.
- **Dependabot enabled** — free on every plan, so there is no excuse
  ([Chapter 32](32_Dependabot_And_Supply_Chain.md)).
- **Zero paid tiers**: budget goes to deploy infrastructure, and every gap that creates is written down.

# Best Practices
- Install hooks as **step 1** on every clone.
- `git fetch` + `--ff-only` before branching. Always.
- Size the PR before opening it; read your own diff first.
- Fill the template honestly — "N/A and why" beats an unticked box.
- Paste real evidence (`Ran 2033 tests … OK`), not claims.
- Rebase onto `origin/main` before requesting review.
- `--force-with-lease` for every post-review force-push.
- Protective rules at the repository root; verify at sibling paths.
- Update docs in the same PR.
- Give every feature flag an owner and a removal condition.
- Write down what each layer does **not** catch.

# Beginner Mistakes
- **Skipping the hook install** → the fresh-clone gap, and the one nothing catches.
- **Pushing straight to `main`** → skips CI, review and the record. The hook refuses it.
- **Sizing against local `main`** → stale silently; this repo read 296 instead of 1.
- **Deleting the PR template** → the money and permissions questions are the ones that catch real
  problems.
- **Treating green CI as proof of correctness** → `bod` had 37 tests outside the gate and a live money
  bug.
- **Long-lived feature branches** → 289 commits produced an unreviewable diff.
- **Giving a collaborator Write "to keep it simple"** → Write includes merge.
- **Assuming CODEOWNERS or secret scanning is active** → both paid on private repos.
- **A `.gitignore` in a subdirectory** → guards only its own subtree.
- **Docs "later"** → rule 12 exists because later never arrives.

# Interview Questions
- **Junior:** "Walk me through your workflow." — Sync `main` with `--ff-only`, branch by intent, commit
  in Conventional Commits form (a hook enforces it), push the branch — never `main`, a hook refuses it —
  open a PR with the template filled in, wait for CI, get a review, squash-merge, delete the branch.
  Releases are annotated tags with a CHANGELOG entry.
- **Mid:** "Why squash-merge instead of a merge commit?" — It makes `main` a list of features: one
  commit per feature, so `git revert` undoes a whole feature cleanly and `git bisect` identifies a
  feature rather than a fragment. The cost is losing the branch's internal commits from `main`, which is
  acceptable because the PR keeps them.
- **Senior:** "Branch protection is paid on your plan. How is `main` protected?" — Three layers, each
  with its weakness stated. A `pre-push` hook client-side, which stops mistakes but only binds where it
  was installed since `.git/hooks/` is never cloned. Collaborators on **Read** access working from
  forks — server-side, free, and actually *stronger* than branch protection, because they have no push
  permission at all rather than a permission with an exception. And CI as the visible merge gate,
  accepting that merge-on-red is not mechanically blocked without paid required-checks. Then the two
  uncaught cases get written down: a fresh clone without hooks, and a deliberate `--no-verify`.
- **Staff:** "Design a workflow for a two-person team on a free plan. Justify every choice." — I would
  start from one property — `main` must always be deployable — because a deploy runbook is only safe to
  delegate if that holds, and then ask what can actually be *enforced* versus what merely gets asked
  for. On a free private plan the enforcement column is thin: branch protection, required reviews,
  required status checks and CODEOWNERS auto-assignment are all paid, while Actions and Dependabot are
  free. So the design has to put real enforcement where it is purchasable at zero cost, which is
  **authorisation**: contributors get Read access and work from forks, so "cannot push to main" and
  "cannot merge" are enforced by GitHub itself — a stronger posture than branch protection, since no key
  is handed over at all. Everything else is layered honestly on top: client-side hooks for message
  format and push refusal, which stop mistakes but are bypassable and not cloned; CI as a visible gate
  that cannot mechanically block a merge. Trunk-based with squash-merge, because two people do not need
  a second long-lived branch and squashing makes revert and bisect operate on features. Conventional
  Commits enforced by hook, because that is what makes the changelog derivable rather than remembered.
  Feature flags defaulting off instead of long-lived branches, with an owner and expiry each — and
  retired when done, since an off-default is not neutral; on this project one flag was deleted outright
  once testing showed its off-default was itself permitting the bug. The part I would insist on is the
  **register of what nothing catches** — the fresh-clone gap, `--no-verify`, merge-on-red — written into
  `CONTRIBUTING.md`, because a scheme presented as airtight is how the gap gets discovered in
  production. And I would name the trigger that invalidates the design: a third person with Write
  access, or the repo going public. At that point the plan question reopens rather than the scheme
  quietly degrading.

### Why interviewers ask these — and the answer that separates levels
| Testing for | Weak answer | What lands |
|---|---|---|
| Do you have a workflow or habits? | "I commit and push." | The nine-step pipeline with a gate at each step, and which gates are enforced versus advisory. |
| Do you know what merge strategy buys? | "Squashing keeps history clean." | One commit per feature makes revert and bisect operate on features; the cost is branch-internal commits, kept in the PR. |
| Can you design under constraints? | "Enable branch protection and required reviews." | Those are paid on private repos — so put enforcement in authorisation (Read + fork), layer the rest, and document what nothing catches. |

**The killer follow-up:** *"Which single gate would you keep if you could only have one?"* — CI, because it is the only gate that checks whether the code actually works; every other gate protects *process*. But the honest completion is that on a free private repo CI cannot block a merge, so the one gate I would keep and the one gate that is genuinely enforced are **not the same thing** — and noticing that gap is the whole point of building the scheme deliberately rather than copying it.

# Revision Notes
- **One principle: `main` must always be deployable.** Everything derives from it.
- Pipeline: **sync → branch → commit → push → PR → CI → review → squash-merge → tag → deploy.**
- **4 gates enforced, 5 advisory** — a consequence of the free plan, and knowing which is which is the skill.
- **Branch protection / required reviews / required checks / CODEOWNERS auto-assign = PAID on private.**
- **3 layers:** pre-push hook (client, not cloned) · **Read + fork (SERVER, free, STRONGEST)** · CI (visible, cannot block merge).
- **Nothing catches:** fresh clone without hooks · deliberate `--no-verify` · merging a red PR. **Written down.**
- Hooks are **never cloned** ⇒ `bash git-hooks/install.sh` is onboarding step 1.
- **`--ff-only`** keeps local `main` a mirror; it goes stale silently otherwise (296 vs 1).
- CI: `lint`+`migrations` gate `test` (**2,033 / 424 s**) then `docs`; `concurrency` + `paths` + timeouts protect ~2,000 free min/month.
- Three CI gotchas: **no YAML anchors** · `DB_*` not `DATABASE_URL` (`ssl_require`) · `reset --soft $(merge-base)` so the staged-index ratchet works.
- **Protective rules at the ROOT** in a monorepo — a correct-but-narrow rule reads as coverage.
- Squash-merge ⇒ 1 feature = 1 commit ⇒ clean `revert`, useful `bisect`.

# Cheat Sheet
```bash
# ── ONCE PER CLONE (hooks are never cloned) ────────────────────────────────
bash git-hooks/install.sh
env/bin/pre-commit install --config django_inventory/.pre-commit-config.yaml

# ── DAILY ──────────────────────────────────────────────────────────────────
git fetch origin
git switch main && git merge --ff-only origin/main     # keep main a MIRROR
git switch -c feat/thing                                # feat|fix|chore|docs|refactor|test|perf
git add -p                                              # atomic commits (ch 03)
git commit -m "feat(scope): subject"                    # hook enforces the format
git rev-list --count origin/main..HEAD                  # SIZE it before opening
git diff origin/main...HEAD                             # exactly what the reviewer sees
git fetch origin && git rebase origin/main              # test the real merge result
git push -u origin feat/thing                           # pre-push refuses main
gh pr create --base main --fill
gh pr checks
gh pr merge --squash --delete-branch

# ── RELEASE ────────────────────────────────────────────────────────────────
git tag -a erp-v1.1.0 -m "erp-v1.1.0 — what changed"
git push origin erp-v1.1.0                              # then update CHANGELOG.md

# ── WHEN IT GOES WRONG (ch 39) ─────────────────────────────────────────────
git status ; git branch --show-current ; git reflog -10
git branch rescue-$(date +%s) HEAD
git revert <bad>                                        # shared history
git push --force-with-lease                             # NEVER plain --force

# ── AUDITS WORTH RUNNING ───────────────────────────────────────────────────
git ls-files -i -c --exclude-standard                   # tracked BUT ignored
git check-ignore -v <path>                              # WHICH rule governs it
git count-objects -vH                                   # repo size
```

# My ERP Section

| Piece | This repository |
|---|---|
| Rulebook | [`CONTRIBUTING.md`](../../../CONTRIBUTING.md) — 10 sections; §2 states each protection layer's **weakness** |
| Hooks | `git-hooks/commit-msg` (Conventional Commits, ≤72, no period — 3 rejected / 6 accepted) · `git-hooks/pre-push` (refuses `main`+`master`+deletions; **verified BLOCKED, `git ls-remote` = 0 refs**) · `git-hooks/install.sh` (worktree-safe, backs up existing hooks) |
| Lint gates | `.pre-commit-config.yaml` — ruff (`--fix`, lenient, changed `.py`) + `scripts/ds_lint.sh --changed` **ratchet** (728 existing violations untouched) |
| CI | `.github/workflows/ci.yml` — lint · migrations · **test (2,033 / 424 s)** · docs BLOCKER=0; `concurrency` · `paths` · timeouts · `test needs:[lint,migrations]` · `fetch-depth: 0` |
| Ownership + PR | `.github/CODEOWNERS` (5 risk categories, dead-rule check) · `pull_request_template.md` (money & permissions **explicit**, 360px shot) · `dependabot.yml` (free on every plan) |
| Branching | trunk-based; `feat/ fix/ chore/ docs/ refactor/ test/ perf/`; **squash-merge**; tags (`erp-v1.0.0` = `90c1f2f3`) |
| Releases | annotated tags + `CHANGELOG.md` **derived** from Conventional Commits |
| Collaborators | **Read** access + fork ⇒ cannot push or merge here at all |
| Free-tier gaps, documented | branch protection · required reviews · required checks · CODEOWNERS auto-assign · secret scanning + push protection |
| Uncaught, documented | fresh clone without hooks · deliberate `--no-verify` · merging a red PR |
| Honest deviation | `new_flask_app` reached **289 commits** — a long-lived branch, producing the predicted unreviewable diff |
| Project rules a PR is judged against | 4 service-layer writes · 5 single-writer · 6 `permission_service` · 11 mobile+tablet+desktop · 12 docs same PR · settlement = the only money boundary |

# Practice Tasks
1. Read `CONTRIBUTING.md` §2 and, without looking here, list the three layers and each one's weakness.
2. Trace one real commit through all nine steps: which gate would have caught a bad message? A push to
   `main`? A missing migration? A missing doc?
3. Run the two audits — `git ls-files -i -c --exclude-standard` and the CODEOWNERS dead-rule loop. Both
   should be clean; make one dirty deliberately and confirm it is caught.
4. Set this workflow up on a scratch repository of your own using the Practical section. Verify the
   ignore rules at sibling paths and check for dead CODEOWNERS rules.
5. Deliberately break each local gate: a bad commit message, a push to `main`, a new inline `#hex` in a
   template. Read each refusal.
6. Write your own version of the "nothing catches" table for a project of your own. That list is more
   valuable than the list of things that do work.

# Homework
- Take a repository you own and add, in order: root `.gitignore`, hooks + installer, path-filtered CI,
  CODEOWNERS, PR template, `CONTRIBUTING.md` with an honest §2. Then have someone else clone it and see
  what they get wrong — that is your real gap list.
- Write the onboarding instructions for a second developer on your project and test them by following
  them yourself on a clean machine or container.
- Pick the one gate your project most needs and add it this week. Then write down what it does not catch.
- Revisit this chapter after a month of using the workflow and record what you actually skipped. That
  list tells you which rules are too expensive — and a rule people skip is a design problem, not a
  discipline problem.

# Further Reading & Live Resources
- [`CONTRIBUTING.md`](../../../CONTRIBUTING.md) — this project's rulebook, the authoritative version of this chapter
- [Trunk Based Development](https://trunkbaseddevelopment.com/) — the model, in depth; free
- [Conventional Commits](https://www.conventionalcommits.org/) · [Semantic Versioning](https://semver.org/) · [Keep a Changelog](https://keepachangelog.com/) — the three conventions this workflow rests on
- [Google's Code Review Developer Guide](https://google.github.io/eng-practices/review/) — the best free writing on review as a system
- [GitHub Docs — About protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches) — including the plan requirements that shaped every decision here
- [GitHub Actions billing](https://docs.github.com/en/billing/managing-billing-for-github-actions/about-billing-for-github-actions) — the free-minute arithmetic
- [Martin Fowler — Patterns for Managing Source Code Branches](https://martinfowler.com/articles/branching-patterns.html) — the most thorough free analysis of the trade-offs
