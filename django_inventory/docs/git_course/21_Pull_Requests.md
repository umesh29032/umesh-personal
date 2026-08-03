---
id: git-course-21-pull-requests
type: lesson
status: active
owner: handwritten
scope: git, GitHub — the pull request as the unit of change, its diff, its gates, its merge strategies
anchors: .github/pull_request_template.md, .github/workflows/ci.yml, CONTRIBUTING.md
verified: 2026-08-03
---

# 21 — Pull Requests (the unit of change at every real company)

> Part of [Git Course](00_COURSE_OVERVIEW.md). Prev: [20 — Forks & the Fork-Based Flow](20_Forks_And_The_Fork_Flow.md). Next: [22 — Code Review](22_Code_Review.md).

# Learning Objectives
By the end of this chapter you can:
- explain what a pull request *is* (a GitHub feature, not a git one) and what it adds over `git merge`
- say exactly which diff a PR shows, and why it excludes changes that landed on `main` after you branched
- choose between merge commit, squash and rebase merging, and defend the choice
- size a PR before opening it, and split one that is too big
- write a PR description that survives being read in six months
- explain what "green CI" does and does not prove on a free-tier private repo

# Purpose
`git merge` combines two branches. A **pull request** wraps that merge in a *process*: a diff to
read, a place to argue, automated gates, and a permanent record of why.

That process is the actual unit of work at every company you will work for. Nobody says "I pushed
a commit"; they say "my PR is up". So the skill being taught here is not a command — it is how to
package a change so that someone else can safely say yes to it.

This project runs the full version of it on a **free** GitHub plan, including the parts GitHub
charges for on private repos. Where the free path is weaker, this chapter says so.

# The Problem
Suppose you just merge your own branch into `main` and push. Four things are now missing, and none
of them are obvious until they hurt:

- **No gate.** Nothing ran the tests. `main` may no longer be deployable — and the deploy runbook
  will faithfully ship the break.
- **No record.** The diff survives; the *reasoning* does not. Six months later nobody knows why
  the settlement date logic changed.
- **No second pair of eyes.** In this codebase that means an unreviewed money-write path or a
  widened permission gate.
- **No clean revert point.** If the feature arrived as eleven commits, undoing it is eleven
  reverts and a prayer.

A PR fixes all four at once. That is why it exists, and why "just push to main" is not a shortcut
but a deferred cost.

# Theory (from zero)

### A PR is not a git object
There is no `git pull-request`. A PR is a **hosting-platform feature** (GitHub, GitLab's merge
request, Bitbucket) built on top of two ordinary git refs:

- a **base** — where you want the change to land (`main`)
- a **head** — the branch carrying the change (`feat/x`, possibly on a fork)

The platform then computes the diff, runs your CI, collects comments, and offers a merge button.
Git itself knows nothing about any of it. Which is why a PR can be closed, reopened, or retargeted
without touching a single commit.

The name is a historical artefact: you are asking the maintainer to *pull* from your branch. That
made literal sense in the email-and-`git request-pull` era, and the word stuck.

### Which diff does a PR show? (the question people get wrong)
A PR shows **three-dot** diff — your branch against the **merge base**, not against the tip of
`main`:

```bash
git diff main...feat/x      # what a PR shows   (merge base → your tip)
git diff main..feat/x       # endpoint vs endpoint  ← NOT what a PR shows
```

That is why unrelated commits landing on `main` after you branched **do not** appear in your PR.
The PR is answering exactly one question: *"what did this branch change?"* — which is the only
question review should be asking.

`...` versus `..` is covered properly in [Chapter 06](06_The_Commit_Graph.md), and it is worth
re-reading, because the meanings differ between `log` and `diff`.

### Size, and why it decides review quality
The single strongest predictor of review quality is **diff size**. A 200-line PR gets real
comments; a 2,000-line PR gets "LGTM". This is not laziness — attention does not scale linearly.

Measure before you open:

```bash
git fetch origin
git rev-list --count origin/main..HEAD      # how many commits
git diff --shortstat origin/main...HEAD     # how many lines
```

Note `origin/main`, not `main`. Bare `main` measures against your possibly-stale local copy —
a real trap demonstrated in [Chapter 18](18_Remotes.md), where the same query read 296 instead of 1.

If it is too big: split by **layer** (model → service → view → template), by **behaviour**
(refactor with no behaviour change, then the change), or open it anyway and say in the description
*which part deserves the attention*. That last option is honest and often correct — a big
mechanical rename plus one real decision is fine if you point at the decision.

### The three merge strategies
| Strategy | Result on `main` | Keeps branch commits? | Good when |
|---|---|---|---|
| **Merge commit** | a two-parent commit joining both lines | yes, all of them | you want the full record of how it was built |
| **Squash** | **one** new commit containing everything | no (they live on in the PR) | the branch's internal commits are noise; you want one revertable unit |
| **Rebase merge** | commits replayed onto `main`, no merge commit | yes, re-hashed | you want linear history *and* individual commits |

**This project squash-merges** (`CONTRIBUTING.md` §5). One feature becomes one commit on `main`,
so `main` reads as a list of features and any feature reverts as a unit. The cost — losing the
branch's internal commit history — is accepted because the PR keeps it forever.

Squash also quietly fixes a real problem: nobody has to write a tidy commit history on their
branch. `wip`, `fix typo`, `actually fix it` all collapse into one clean message at merge time.

### What "green CI" proves — and what it does not
Green CI proves the automated gates passed. On this repository that is four jobs:
lint, missing-migration check, the full 2,033-test battery, and a documentation-drift gate
([Chapter 28](28_CI_With_GitHub_Actions.md)).

It does **not** prove the change is correct, well-designed, or safe. Tests encode what someone
thought to check. This project's own history proves the gap: the `bod` app sat in
`INSTALLED_APPS` but in **no test group** — 37 tests, including a real UTC/IST money bug, outside
the gate while the battery still reported "all green".

And one honest free-tier caveat: on a private repo on the free plan, GitHub will not
*mechanically* block merging a red PR — that enforcement is paid. The signal is fully visible on
the PR; refusing to click merge is a human commitment. `CONTRIBUTING.md` §2 records this as
layer 3 of three, with its weakness stated rather than hidden.

> 💡 **Samjho aise:** PR ek **git ki cheez nahi hai** — GitHub ka feature hai. Do pate deta hai:
> kahan daalna hai (`main`) aur kahan se (`feat/x`). Baaki sab — diff, tests, comments, merge
> button — GitHub ka intezaam hai.
>
> Aur PR ka diff **tumhari branch ne kya badla** dikhata hai, `main` se seedha muqabla nahi. Isliye
> tumhare branch banane ke baad `main` pe aaya kaam PR mein nahi dikhta. Ye galti nahi, yehi sahi
> sawaal hai.
>
> Sabse kaam ki baat: **chhota PR = asli review. Bada PR = "LGTM".** 200 line pe log sochte hain,
> 2000 line pe sirf sar hilate hain.

# Real World Example (this repo)
This repository has exactly one merged pull request, and it is a textbook illustration of *both*
the mechanism and the sizing lesson.

**PR #15**, `new_flask_app` → `main`, merged as commit `83a144ba`:

```bash
git log --graph --oneline -3 83a144ba
```
```
*   83a144ba Merge pull request #15 from umesh29032/new_flask_app
|\
| * 7fe2bb0e feat: accountant read tier, student role, learning platform completion…
```

The `|\` and the two parent lines are the merge; the PR was the process around it
([Chapter 06](06_The_Commit_Graph.md) shows the object).

**And the sizing lesson, from the real decision.** Before opening it, the range query said:

```
289 commits, ~2100 files, 336,372 insertions
```

`main` had been stale for months while every piece of work happened on the branch. **289 commits
is not a reviewable diff.** So the recommendation given at the time was explicit: either merge it
as the accepted state of the project while reviewing only the newest commit, or close it and open
narrow per-topic PRs. The PR description led with that warning rather than pretending the diff was
readable.

That is the honest use of a PR: it does not make a large change small, but it makes the size
*visible* so the decision is informed.

**The PR shape this project enforces.** `.github/pull_request_template.md` loads automatically and
asks for:

- **What & why** — the problem first, because a reviewer who understands the problem can judge the
  solution
- **How it was verified** — the battery count pasted, not "it works"
- **Project rules** — rule 4 (service-layer writes), 5 (single-writer), 6 (`permission_service`),
  11 (mobile+tablet+desktop), 12 (docs in the same PR)
- **Money & permissions impact** — answered explicitly *even when the answer is none*, because
  silence is where this project has historically been bitten
- **Risk & rollback**, and a **360px mobile screenshot** for any UI change

The money/permissions question being mandatory is the local adaptation that matters most:
settlement is the only money-write boundary, and a new write path outside an approved service is a
**STOP**, not a review comment.

# Visual Diagram
```
  YOUR BRANCH                                         GITHUB
  ───────────                                         ──────
  git switch -c feat/x
  commit, commit, commit
  git push -u origin feat/x  ───────────────────────►  branch appears
                                                            │
                                                            ▼
                          ┌──────────────── PULL REQUEST ────────────────┐
                          │ base: main        head: feat/x               │
                          │                                              │
                          │ DIFF = git diff main...feat/x                │
                          │        (merge base → your tip)               │
                          │        ⇒ commits that landed on main after   │
                          │          you branched do NOT appear          │
                          │                                              │
                          │ CI: lint → migrations → test(2033) → docs    │
                          │ REVIEW: money · permissions · tests · docs   │
                          │         · mobile                             │
                          │ TEMPLATE: what&why · verified · rules ·      │
                          │           money impact · rollback · 360px    │
                          └───────────────────┬──────────────────────────┘
                                              │ squash-merge (this project)
                                              ▼
                     main:  ──●──────●──────● one commit = one feature
                                              │           reverts as a unit
                                              ▼
                                      tag erp-vX.Y.Z → deploy

  SIZE, measured BEFORE opening:
      git rev-list --count origin/main..HEAD      ← origin/main, not main!
      git diff --shortstat origin/main...HEAD
```

# Practical — open a PR properly, start to finish
```bash
# 0. start from a fresh trunk (ch 18: local main goes stale silently)
git fetch origin
git switch main && git merge --ff-only origin/main

# 1. branch, named by type (CONTRIBUTING.md §3)
git switch -c feat/accountant-read-tier

# 2. work; commit in Conventional Commits form (ch 25 — the hook enforces it)
git add -p                      # stage deliberately, keep commits atomic (ch 03)
git commit -m "feat(expense): add accountant read tier"

# 3. SIZE IT before opening
git rev-list --count origin/main..HEAD          # commits
git diff --shortstat origin/main...HEAD         # files / insertions / deletions

# 4. read your own diff exactly as the reviewer will
git diff origin/main...HEAD

# 5. rebase onto current main so CI tests the real merge result
git fetch origin && git rebase origin/main      # ch 13

# 6. push the BRANCH (never main — the hook refuses; ch 27)
git push -u origin feat/accountant-read-tier

# 7. open the PR
gh pr create --base main --fill                 # or the web UI
gh pr status                                    # CI + review state
gh pr checks                                    # just the CI results
gh pr view --web

# 8. after review comments: amend or add, then
git push --force-with-lease                     # safe force: refuses if the remote moved
```

Step 8's flag is the important one. `--force-with-lease` checks that the remote is still where you
last saw it, so you cannot silently overwrite a colleague's push. Plain `--force` skips that check.

**Note on `gh` in this repository:** the local `gh` CLI is authenticated as `umesh2030` (the
owner's *office* account) while the repo belongs to `umesh29032`, so `gh pr create` fails with
`must be a collaborator`. That is an authentication mismatch, not a permissions problem —
diagnosed in [Chapter 02](02_Install_And_Configure.md). Use the web UI, or `gh auth switch`.

# Production Walkthrough
The PR lifecycle as this project actually runs it:

1. **Sync, branch, work.** `git fetch` → `--ff-only` → `git switch -c feat/x`.
2. **Size it.** More than a few hundred lines? Split, or name the part that needs attention.
3. **Rebase onto `origin/main`** so CI evaluates the real post-merge state, not a stale base.
4. **Push the branch; the `pre-push` hook refuses `main`** ([Chapter 27](27_Pre_Push_Protection.md)).
5. **Open the PR; fill the template.** Deleting it is not an option — the money/permissions
   questions are the point.
6. **Watch CI.** `lint` and `migrations` gate `test`, so a typo fails in ~3 minutes rather than
   burning 45 ([Chapter 28](28_CI_With_GitHub_Actions.md)).
7. **Review** against the five axes: money, permissions, tests, docs, mobile
   ([Chapter 22](22_Code_Review.md)).
8. **Squash-merge**, then delete the branch.
9. **Release** when appropriate: annotated tag, `CHANGELOG.md` updated
   ([Chapters 29](29_Semantic_Versioning_And_Tags.md)–[30](30_Changelog.md)).

For a collaborator the only difference is step 4: they push to **their fork**, and the PR is
cross-repository. They cannot merge, because they hold Read access — the free, server-side half of
this project's protection ([Chapter 20](20_Forks_And_The_Fork_Flow.md)).

# Debugging Guide

| Symptom | Cause | Fix |
|---|---|---|
| PR diff misses changes you expected | PRs diff against the **merge base**, not `main`'s tip | `git diff main...HEAD` reproduces it; `..` for endpoints |
| PR diff is enormous and full of unrelated files | branched from a stale base, or `main` moved a lot | `git rebase origin/main`, then re-check |
| `gh pr create` → `must be a collaborator` | `gh`'s token is a different GitHub account than SSH | `gh auth status`, `gh auth switch` ([Ch 02](02_Install_And_Configure.md)) |
| CI green locally, red in CI | environment: Postgres version, missing env var, timezone | read the failing job's log; reproduce with the same settings module |
| "This branch has conflicts" | `main` moved and touched your lines | `git fetch && git rebase origin/main`, resolve ([Ch 12](12_Merge_Conflicts.md)) |
| Force-push rejected after review | remote moved since you last fetched | `git fetch`, re-check, then `--force-with-lease` |
| Reviewer sees old code | you amended but did not push | `git push --force-with-lease` |
| Merge button unavailable | required check pending, or base branch protected | `gh pr checks`; wait or resolve |
| Accidentally opened against the wrong base | base chosen at creation | edit the PR's base branch; no commits change |

# Performance Notes
- **`git rev-list --count` is cheaper than `git log | wc -l`** — no formatting, no pager.
- **Rebase before opening**, not after CI fails: a stale base means CI tests a merge result that
  will never exist.
- **Free-minute discipline** matters on a private repo (~2,000 Actions minutes/month). This
  project's `ci.yml` cancels superseded runs via `concurrency`, filters by `paths`, and gates the
  45-minute `test` job behind two ~3-minute jobs. The battery itself is **2,033 tests in 424 s**,
  so ~280 runs/month fit comfortably.
- **Small PRs are faster end-to-end** even though they are more numerous: less rebasing, fewer
  conflicts, faster review turnaround.
- Long-lived branches cost real time — the merge base recedes and conflict likelihood grows with
  distance.
- `gh pr checks` polls the API and is far cheaper than reloading the web UI.

# Security Considerations
- **The PR diff is the last cheap place to catch a secret.** Once merged, history is append-only
  and removal means a rewrite ([Chapters 33](33_Secrets_And_Leaks.md)–[34](34_Rewriting_History.md)).
  The template's reviewer checklist explicitly asks whether any `.sql`, `.env` or dump appears in
  the diff.
- **Money and permission changes get named explicitly**, because silence is indistinguishable from
  "no impact". Settlement is the only money-write boundary; a new write path elsewhere is a STOP.
- **Green CI is not a security review.** Tests check what someone thought to check — the `bod`
  incident is the local proof.
- **A cross-repository PR from a fork is untrusted code.** Workflows triggered by `pull_request`
  run without repository secrets by design; `pull_request_target` does have them and is a known
  escalation path. Do not reach for it casually.
- **On free-tier private repos, merge-on-red is not mechanically blocked.** Written down in
  `CONTRIBUTING.md` §2 rather than assumed away.
- **`--force-with-lease`, never `--force`** on a branch anyone else may have fetched.

# Architecture Decisions
- **Squash-merge as the default.** One feature = one commit on `main`, so revert and
  [bisect](35_Bisect.md) operate on features rather than fragments. The branch's internal commits
  are preserved in the PR, so nothing is truly lost.
- **A committed PR template.** Reviews drift toward style comments unless the important questions
  are asked *by the process*. Money and permissions are mandatory fields for that reason.
- **`test` needs `lint` and `migrations`.** Free Actions minutes are finite; a lint error should
  cost three minutes, not forty-five.
- **CI gates the merge, not the deploy.** Deployment stays a deliberate human act — a factory
  pausing production is a decision, not a side effect of clicking merge.
- **Rebase before opening rather than merging `main` into the branch.** Keeps the branch linear and
  the PR diff honest; `pull.rebase true` is set globally for the same reason.
- **The fork flow instead of paid branch protection.** Read access plus a fork means a collaborator
  physically cannot merge — stronger than a rule saying they may not
  ([Chapter 20](20_Forks_And_The_Fork_Flow.md)).

# Best Practices
- `git fetch` and `--ff-only` your `main` **before** branching. Stale bases produce noisy PRs.
- Size the PR before opening it; split or point at the part that matters.
- Read `git diff origin/main...HEAD` yourself first. Most review comments are things you would
  have caught.
- Fill the template honestly, including "N/A and why" — an unticked box with no explanation reads
  as *not checked*.
- Paste the real test count. "Tests pass" is a claim; `Ran 2033 tests … OK` is evidence.
- Rebase onto `origin/main` before requesting review, so CI tests reality.
- `--force-with-lease` for every post-review force-push.
- Delete the branch on merge; keep `git branch -r` meaningful.

# Beginner Mistakes
- **Opening a 2,000-line PR and expecting a real review** → you will get "LGTM" and a bug in
  production.
- **Deleting the template** → the money and permission questions are the ones that catch real
  problems.
- **Writing "fixed stuff" as the description** → the diff shows *what*; only you can record *why*.
- **Sizing against local `main`** → it goes stale silently; this repo read 296 instead of 1.
- **Expecting the PR diff to show `main`'s new commits** → it diffs the merge base, deliberately.
- **`git push --force` after review** → can obliterate a colleague's push. Use `--force-with-lease`.
- **Treating green CI as proof of correctness** → it proves the gates passed. `bod` had 37 tests
  outside the gate and a live money bug.
- **Merging your own unreviewed money change silently** → if nobody is available, say so in the PR
  and state what you self-reviewed.

# Interview Questions
- **Junior:** "What is a pull request?" — A hosting-platform feature that proposes merging a head
  branch into a base branch. It adds a reviewable diff, automated checks, discussion and a
  permanent record around what would otherwise be a bare `git merge`. Git itself has no concept of
  it.
- **Mid:** "Which diff does a PR show, and why does it exclude some commits?" — The three-dot diff,
  `git diff base...head`: your branch measured from the **merge base**, not from the base branch's
  tip. So commits that landed on `main` after you branched are excluded, because the PR answers
  "what did this branch change" — the only question review should ask.
- **Senior:** "Merge commit, squash, or rebase — and why?" — Merge commit keeps the full topology
  and both parents; squash produces one commit per feature, giving a near-linear `main` where
  revert and bisect operate on features; rebase merge keeps individual commits without a merge
  commit. This project squashes: `main` becomes a list of features, each revertable as a unit, and
  the branch's messy internal commits stay in the PR. The trade-off is losing that granularity in
  `main`'s history, which is acceptable precisely because the PR retains it.
- **Staff:** "Your team's PRs are always green and bugs still ship. What do you change?" — Green
  means "the checks we wrote passed", so I would first measure what the checks *cover*: this
  project found an entire app in `INSTALLED_APPS` but in no test group, 37 tests and a real
  timezone-money bug sitting outside the gate while the battery reported all green — so I would pin
  "tests discovered == tests run" as an invariant. Then I would attack review quality structurally
  rather than exhortation: cap PR size, make the risky dimensions mandatory fields in the template
  so money and permission changes cannot pass silently, and add gates for the failure classes that
  actually bit us — a missing-migration check, a docs-drift check, an AST-based guard for the exact
  bug shape rather than a string grep. And I would be explicit about what the platform cannot
  enforce: on a free-tier private repo merge-on-red is a human commitment, so that weakness gets
  written down and compensated with client-side hooks, not assumed away.

### Why interviewers ask these — and the answer that separates levels
| Testing for | Weak answer | What lands |
|---|---|---|
| Do you know a PR is not git? | "It's how you merge branches in git." | A platform feature over two refs (base, head) adding diff, CI, review and a record; git has no such object. |
| Do you understand the diff? | "It shows my branch versus main." | Three-dot: branch versus **merge base**, which is why post-branch commits on main are absent — and that is correct, not a bug. |
| Can you reason about process quality? | "We require approvals." | Cap size, make risky dimensions mandatory fields, gate the failure classes you have actually seen, and state what the plan cannot enforce. |

**The killer follow-up:** *"CI is green. What has that actually proved?"* — That the checks someone wrote passed on this diff. Nothing about design, nothing about the failure modes nobody encoded, and — on a free private repo — not even that merging is blocked if it were red. The strong answer names a concrete gap from experience: an installed app outside the test gate reporting "all green" while hiding a money bug.

# Revision Notes
- A PR is a **platform feature**, not git: base + head, plus diff, CI, review, record.
- PR diff = **`git diff base...head`** (three dots) = branch vs **merge base** ⇒ post-branch commits on main are excluded by design.
- **Size before opening:** `git rev-list --count origin/main..HEAD` — `origin/main`, never bare `main`.
- Strategies: merge commit (full topology) · **squash** (one commit/feature — this project) · rebase merge (linear, keeps commits).
- **Small PR = real review. Big PR = "LGTM".**
- Green CI = the gates passed. Not correctness. `bod`: 37 tests outside the gate, one real money bug.
- Free private repo: merge-on-red is **not** mechanically blocked (paid). Written down, not assumed away.
- Rebase onto `origin/main` before review so CI tests reality. Push with `--force-with-lease`.
- PR #15 here = 289 commits — the number that changed the recommendation.

# Cheat Sheet
```bash
git fetch origin                                  # ALWAYS first (ch 18)
git switch main && git merge --ff-only origin/main
git switch -c feat/my-thing                       # type/kebab-name (CONTRIBUTING §3)

git rev-list --count origin/main..HEAD            # commits in this PR
git diff --shortstat origin/main...HEAD           # files / +lines / -lines
git diff origin/main...HEAD                       # EXACTLY what the reviewer sees

git fetch origin && git rebase origin/main        # test the real merge result
git push -u origin feat/my-thing                  # push the BRANCH (hook blocks main)
git push --force-with-lease                       # after amend/rebase — safe force

gh pr create --base main --fill                   # open it
gh pr status                                      # CI + review state
gh pr checks                                      # just CI
gh pr diff                                        # the diff in the terminal
gh pr view --web
gh pr merge --squash --delete-branch              # this project's strategy
gh auth status                                    # if gh says "must be a collaborator"
```

# My ERP Section

| Fact | This repository |
|---|---|
| PRs merged | **one** — PR #15, `new_flask_app` → `main`, merge commit `83a144ba` |
| Its size | **289 commits**, ~2,100 files, 336,372 insertions — too large to review as one diff, and the description said so |
| Merge strategy | **squash-merge** (`CONTRIBUTING.md` §5) — one feature = one commit on `main` |
| Template | `.github/pull_request_template.md` — what&why · verified (paste the count) · rules 4/5/6/11/12 · **money & permissions answered explicitly** · risk & rollback · 360px mobile shot |
| Ownership | `.github/CODEOWNERS` — money, access-control, migrations and deploy paths flagged. Auto-assignment is **paid** on private repos, so the file documents ownership and the template asks a human to check it |
| CI gates | `lint` → `migrations` → `test` (**2,033 tests / 424 s**) → `docs` (`knowledge_sync` BLOCKER=0) |
| Free-tier honesty | merge-on-red not mechanically blocked; layer 3 of 3 in `CONTRIBUTING.md` §2 |
| `gh` caveat | authenticated as `umesh2030`, repo owned by `umesh29032` ⇒ `must be a collaborator`; use the web UI or `gh auth switch` |

# Practice Tasks
1. In this repo, run `git diff --shortstat origin/main...HEAD` and `git diff --shortstat origin/main..HEAD`.
   Explain the difference in one sentence.
2. Look at PR #15's merge commit: `git log --graph --oneline -3 83a144ba`. Identify the two parents
   and say which is the feature side.
3. Open `.github/pull_request_template.md` and answer every question for the last change you made
   to any project. Notice which questions you cannot answer — those are the gaps.
4. Fork any public repo, push a one-line branch, and open a real PR. Read the diff GitHub shows and
   confirm it matches `git diff main...your-branch` locally.
5. Deliberately branch from a **stale** local `main`, then look at the PR diff. Then
   `git rebase origin/main` and look again. Feel why step 0 exists.
6. Run `gh pr checks` on any open PR in a public repo you have forked, and compare it to the web UI.

# Homework
- Take your next change and open it as **two** PRs instead of one: a behaviour-preserving refactor,
  then the actual change. Compare the review you get on each.
- Write a PR description for a change you made last week, from memory, using the template. If you
  cannot reconstruct the *why*, that is the argument for the template.
- Read GitHub's docs on `pull_request` versus `pull_request_target` workflow triggers and write two
  sentences on why the distinction is a security boundary for fork PRs.
- Configure `gh` for the correct account on your machine (`gh auth switch`) and open a PR entirely
  from the terminal, end to end.

# Further Reading & Live Resources
- [GitHub Docs — About pull requests](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests) — the canonical description
- [GitHub Docs — About merge methods](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/incorporating-changes-from-a-pull-request/about-merge-methods-on-github) — merge vs squash vs rebase, with diagrams
- [gh pr manual](https://cli.github.com/manual/gh_pr) — create, checks, diff, merge from the terminal
- [Google's Code Review Developer Guide — the CL author's guide](https://google.github.io/eng-practices/review/developer/) — the best free writing on PR size and description quality
- [git-diff reference](https://git-scm.com/docs/git-diff) — the `..` versus `...` semantics, precisely
- [GitHub Docs — keeping your actions secure with fork PRs](https://securitylab.github.com/resources/github-actions-preventing-pwn-requests/) — why `pull_request_target` is dangerous
