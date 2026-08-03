---
id: git-course-24-branching-strategies
type: lesson
status: active
owner: handwritten
scope: git — trunk-based vs GitHub Flow vs git-flow; choosing and defending a branching model
anchors: CONTRIBUTING.md, .github/workflows/ci.yml, git-hooks/pre-push
verified: 2026-08-03
---

# 24 — Branching Strategies (and why we chose the boring one)

> Part of [Git Course](00_COURSE_OVERVIEW.md). Prev: [23 — CODEOWNERS & PR Templates](23_CODEOWNERS_And_Templates.md). Next: [25 — Conventional Commits](25_Conventional_Commits.md).

# Learning Objectives
By the end of this chapter you can:
- describe trunk-based development, GitHub Flow and git-flow, and name what each optimises for
- explain why the number of **long-lived** branches is the variable that matters
- say what a release branch actually buys you, and when you genuinely need one
- defend this project's choice with reasons rather than preference
- explain how feature flags substitute for long-lived branches
- recognise the failure mode of each model before you are living in it

# Purpose
Every team picks a branching model, usually by copying whichever blog post they read first. Then
they inherit that model's failure mode without ever having weighed it.

There are really only three families in common use, and the difference between them reduces to one
number: **how many long-lived branches you maintain.** Everything else — release branches, hotfix
branches, develop branches — is downstream of that.

This chapter explains the three, then states this project's choice and the reasoning, so a future
reader (including you) can tell a deliberate decision from an accident.

# The Problem
Branching sounds like a cosmetic choice until you feel its cost. Three real ones:

- **Long-lived branches diverge.** The merge base recedes daily, conflicts compound, and the
  eventual merge is a multi-hour archaeology session rather than a click.
- **Every long-lived branch is a place bugs must be fixed separately.** Fix it on `main`, then
  cherry-pick to `develop`, then to `release/1.4`. Miss one and the bug reappears in the next
  release, which reads as a regression nobody introduced.
- **A model heavier than your team is pure overhead.** git-flow's five branch types make sense for
  shipping versioned software to customers who upgrade on their own schedule. For one developer
  deploying to one server, they are ceremony with a cost and no payoff.

The failure is rarely "we picked the wrong model". It is "we picked a model for a team we are not".

# Theory (from zero)

### The one variable: long-lived branches
| Model | Long-lived branches | Short-lived branches |
|---|---|---|
| **Trunk-based** | **1** (`main`) | feature branches, hours to days |
| **GitHub Flow** | **1** (`main`) | feature branches, days |
| **git-flow** | **2+** (`main`, `develop`, plus `release/*`, `hotfix/*`) | `feature/*` |

Trunk-based and GitHub Flow are nearly the same thing; the distinction is emphasis, not structure.
git-flow is genuinely different, and every complication it has follows from having two permanent
branches instead of one.

### Trunk-based development
One permanent branch. Short-lived feature branches merge back quickly — ideally within a day.
Releases are **tags** on `main`, not branches.

**Requires:** solid CI (nothing else keeps `main` deployable), small changes, and feature flags for
work that cannot ship yet.

**Buys:** almost no merge pain (short branches barely diverge), one place to fix a bug, and a
`main` you can always deploy.

**Costs:** you must be disciplined about size, and incomplete work needs flags rather than a branch
to hide in.

### GitHub Flow
Trunk-based with the PR as the explicit ritual: branch → commit → PR → review → CI → merge →
deploy. `main` is always deployable, and deployment happens per merge.

This is what most teams on GitHub actually do, and the name is worth knowing simply because it is
what people mean by "the normal workflow".

### git-flow
Two permanent branches plus three temporary types:

```
main      ── only tagged releases live here
develop   ── integration branch; features merge here
feature/* ── branched from develop, merged back to develop
release/* ── branched from develop when preparing a version; stabilise, then merge to BOTH
hotfix/*  ── branched from main for emergencies; merged to BOTH
```

**Buys:** a genuine ability to stabilise release 1.4 while 1.5 development continues, and to support
multiple released versions at once.

**Costs:** every fix must be applied in two or three places; `main` and `develop` diverge
continuously; and the model's own author has since published a note saying it is over-applied and
that continuous-delivery teams should not use it. That is unusually candid and worth taking
seriously.

**You need it if:** you ship versioned software that customers install and upgrade on their own
schedule, and you must patch old versions. If you deploy a web app to your own server, you almost
certainly do not.

### Feature flags: how trunk-based ships unfinished work
The obvious objection to trunk-based is *"what if the feature is not ready?"* The answer is that the
code merges but stays **off**:

```python
# settings/base.py — default OFF; a flag is a decision reversible without a deploy
ENFORCE_SETTLEMENT_RECONCILIATION = config(
    'ENFORCE_SETTLEMENT_RECONCILIATION', default=False, cast=bool)
```

Merged, tested, inert. Turn it on when ready — and, crucially, turn it **off** without a rollback if
it misbehaves.

That is not theoretical here. `ENFORCE_SETTLEMENT_RECONCILIATION` defaults to `False`
(WARN-only), `SETTLEMENT_RECONCILIATION_TOLERANCE` tunes it, and
`LEDGER_CREDIT_AT_ALLOCATION` defaults to `False` as a **rollback lever** for a completed money
migration — era-B by default, era-A restorable by env var. Enforcement code lives on `main`, fully
tested, switched off until a soak period says otherwise. A long-lived branch would have given the
same visibility with none of the testing and all of the divergence.

### Flags must be retired — and this repo has the receipt
The trade-off is honest: flags accumulate, and a flag with no removal date becomes permanent
conditional complexity. So each one needs an **owner and a removal condition** at creation.

This project actually did it. `ENFORCE_ALLOCATION_BOUND` used to exist, defaulting to `False`. It
was **deleted** by owner ruling on 2026-07-20, and the comment left in `settings/base.py` says
exactly why:

> *"the allocation bound is now HARD + ALWAYS enforced (no feature flag). The former
> `ENFORCE_ALLOCATION_BOUND` kill-switch was removed: the FAT proved the soft/off default let
> workers over-report beyond their allocation."*

Read that carefully, because it is the sharpest lesson available about flags: **the off-default was
not neutral — it was the bug.** A flag defaulting to "do not enforce" is a decision to permit the
thing you built the check for. Factory acceptance testing found workers reporting more pieces than
they had been allocated, and the fix was not to flip the flag but to remove the choice.

The honest counterpart survives as `preview_allocation_bound`, a read-only audit for rows that
would now be refused. That is the shape of a well-retired flag: the enforcement became
unconditional, and the diagnostic stayed.

> 💡 **Samjho aise:** Sirf ek sawaal poochho: **kitni branch hamesha zinda rehti hai?**
>
> **Ek** (trunk-based / GitHub Flow) — chhoti branch, jaldi merge, release = tag. Bug ek jagah
> theek karo, bas.
>
> **Do ya zyada** (git-flow) — `main` aur `develop` dono zinda. Ab har bug **do-teen jagah** theek
> karna padta hai, aur ek jagah bhool gaye toh agli release mein bug wapas — jo dikhta hai jaise
> naya bug ho.
>
> Adha kaam ready nahi hai? Branch mein chhupao **nahi** — merge karo par **switch off** rakho
> (feature flag). Is project mein wahi hota hai: `ENFORCE_*` flags default `False`.
>
> Aur yaad rakho: galti "galat model chuna" nahi hoti. Galti hoti hai **apni team se bhaari model**
> chunna.

# Real World Example (this repo)
This project runs **trunk-based development**, and the choice is written down in
[`CONTRIBUTING.md`](../../../CONTRIBUTING.md) §3 and §10 rather than left implicit.

```
main              ← the single long-lived branch; always deployable
feat/* fix/* chore/* docs/* refactor/* test/* perf/*
                  ← short-lived, one intent each, deleted after merge
tags              ← releases: erp-v1.0.0 = 90c1f2f3
```

**What makes it work here:**

- **CI on every PR** — four gates: lint, missing-migration check, the full **2,033-test** battery
  against a real Postgres, and a documentation-drift check
  ([Chapter 28](28_CI_With_GitHub_Actions.md)). Without that, "main is always deployable" is a wish.
- **Squash-merge** — one feature becomes one commit on `main`, so `main` reads as a list of features
  and any feature reverts as a unit ([Chapter 21](21_Pull_Requests.md)).
- **Feature flags for unfinished enforcement** — `ENFORCE_SETTLEMENT_RECONCILIATION` defaults
  `False` (WARN-only) and `LEDGER_CREDIT_AT_ALLOCATION` defaults `False` (rollback lever); the code
  is merged and tested but inert. And flags get **retired**: `ENFORCE_ALLOCATION_BOUND` was removed
  outright on 2026-07-20 once testing showed its off-default was itself the defect.
- **Releases are annotated tags**, not branches — `erp-v1.0.0` ([Chapter 29](29_Semantic_Versioning_And_Tags.md)).
- **`git-hooks/pre-push` refuses direct pushes to `main`**, which is the free substitute for paid
  branch protection ([Chapter 27](27_Pre_Push_Protection.md)).

**Why not git-flow?** Because this is one developer deploying a web app to one VPS. There is no
customer running version 1.3 who needs a backport. A `develop` branch would add a second permanent
branch to keep in sync, and a `release/*` branch would stabilise a release nobody is waiting on.
`CONTRIBUTING.md` §10 states it directly: *"No long-lived release branches. Trunk-based: `main` plus
short branches plus tags. `git-flow` is heavier than a 1–2 person team can justify."*

**And the honest counter-example in this very repository.** The branch `new_flask_app` accumulated
**289 commits** before merging in PR #15. That is trunk-based development *not* being followed — a
long-lived branch by any definition, and it produced exactly the predicted symptom: a diff too large
to review, forcing a choice between "merge as the accepted state" and "split into narrow PRs"
([Chapter 21](21_Pull_Requests.md)).

Writing that down matters more than claiming compliance. The model is the target; the 289-commit
branch is the evidence for why the target exists.

# Visual Diagram
```
  TRUNK-BASED / GITHUB FLOW  — 1 long-lived branch          ← THIS PROJECT
  ────────────────────────────────────────────────
    feat/x   ──●──●──┐
                     ▼ squash-merge
    main  ──●────────●────────●────────●──────►
                              │        │
                          tag v1.0  tag v1.1
    fix a bug: ONE place.  release: a TAG.
    unfinished work: merged but FLAG-OFF (ENFORCE_* default False)


  GIT-FLOW — 2+ long-lived branches
  ────────────────────────────────────────────────
    feature/x ──●──●──┐
                      ▼
    develop  ──●──────●──────●──────●──────►
                             │             ╲
                       release/1.4 ──●──●──►╲
                                            ▼
    main     ────────────────────────────────●──────►
                                          tag 1.4
    hotfix/y ──────────────────────────●───┤ merged to BOTH
                                            ▼ ...and back to develop

    a bug fix may need applying in main, develop AND release/1.4
    miss one ⇒ the bug returns next release, looking like a regression


  THE ONLY QUESTION THAT MATTERS
  ────────────────────────────────────────────────
     how many branches live forever?
        1  → cheap merges, one fix location, needs CI + flags
        2+ → parallel version support, paid for in permanent sync work
```

# Practical — inspect and measure your own model
```bash
cd /home/tech/umesh-personal

# 1. how many long-lived branches are there, really?
git branch -a
git branch -r | grep -vE 'HEAD|feat/|fix/|chore/|docs/' # candidates for "permanent"

# 2. releases as tags (trunk-based) or as branches (git-flow)?
git tag -l
git branch -r | grep -iE 'release|develop' || echo "  none → trunk-based shape"

# 3. THE health metric: how far has each branch diverged?
git fetch origin
for b in $(git branch --format='%(refname:short)'); do
  n=$(git rev-list --count origin/main.."$b" 2>/dev/null)
  printf '  %-24s %s commits ahead of origin/main\n' "$b" "${n:-?}"
done

# 4. branch age — anything older than a few days is drifting
git for-each-ref --sort=committerdate --format='%(committerdate:short) %(refname:short)' refs/heads/

# 5. which branches are safely mergeable / already merged?
git branch --merged origin/main
git branch --no-merged origin/main

# 6. this project's feature flags — trunk-based's alternative to a long branch
grep -rn "ENFORCE_SETTLEMENT_RECONCILIATION\|LEDGER_CREDIT_AT_ALLOCATION" \
  django_inventory/config/config/settings/base.py
# and read the comment above line 189 — a RETIRED flag, and why it was removed
sed -n '189,193p' django_inventory/config/config/settings/base.py
```

Step 3 is the metric to actually watch. A branch 5 commits ahead is healthy; 289 is a different
workflow wearing trunk-based clothing.

# Production Walkthrough
The loop this project follows, and where the model shows up in each step:

1. **Sync** — `git fetch origin && git merge --ff-only origin/main`. Local `main` is a pure mirror;
   `--ff-only` refuses to let it grow its own history ([Chapter 18](18_Remotes.md)).
2. **Branch by intent** — `feat/`, `fix/`, `chore/`, `docs/`, `refactor/`, `test/`, `perf/`. One
   branch, one intent.
3. **Keep it short.** Days, not weeks. If it is growing, ship a slice behind a flag instead.
4. **Rebase onto `origin/main`** before review, so CI evaluates the real merge result
   ([Chapter 13](13_Rebase.md)).
5. **PR → CI → review → squash-merge → delete the branch.**
6. **Release when it makes sense** — annotated tag plus a `CHANGELOG.md` entry
   ([Chapters 29](29_Semantic_Versioning_And_Tags.md)–[30](30_Changelog.md)).
7. **Deploy is a separate, deliberate act.** CI gates the *merge*, not the deploy; a factory pausing
   production is a human decision.

For a collaborator, step 5 differs: they push to their fork and cannot merge, because Read access
plus a fork is the enforcement layer ([Chapter 20](20_Forks_And_The_Fork_Flow.md)).

# Debugging Guide

| Symptom | Cause | Fix |
|---|---|---|
| Merges routinely take hours | branches living too long; merge base receded | shorter branches; rebase onto `origin/main` daily; ship slices behind flags |
| A fixed bug reappears in a release | fix applied to one long-lived branch, not the others | that is git-flow's tax; cherry-pick to every live branch, or reduce to one trunk |
| `main` is not deployable | no CI gate, or merge-on-red | add gates; gate cheap jobs before expensive ones ([Ch 28](28_CI_With_GitHub_Actions.md)) |
| Branch diff is unreviewably large | long-lived branch masquerading as a feature branch | split by layer or behaviour; or say in the PR which part needs attention |
| "We need git-flow for our release" | usually a wish for stabilisation, not multi-version support | ask whether anyone runs an old version; if not, a tag plus a flag is enough |
| Flags never get removed | no owner, no expiry | record owner + removal condition when the flag is created |
| Cannot tell which model you are on | nobody wrote it down | write it in `CONTRIBUTING.md`; the decision is only real if it is readable |
| Long branch full of merge commits from `main` | merging `main` in repeatedly instead of rebasing | `pull.rebase true`; rebase onto `origin/main` |

# Performance Notes
- **Merge cost scales with divergence**, not with repo size. Computing a merge base across deeply
  divergent branches is the expensive part; git's commit-graph generation numbers optimise it, but
  the human resolution cost is the real expense.
- **Short branches are faster end-to-end** despite being more numerous: less rebasing, fewer
  conflicts, quicker review.
- **CI minutes favour trunk-based.** One trunk means one branch to gate. On a private repo
  (~2,000 free Actions minutes/month) with a 424 s battery, ~280 runs/month fit; multiplying that
  across `develop` plus release branches multiplies the spend
  ([Chapter 28](28_CI_With_GitHub_Actions.md)).
- **Squash-merge keeps `main` cheap to read.** `git log --first-parent` on a near-linear trunk is a
  release-notes view; a git-flow trunk needs graph archaeology.
- Deleting merged branches keeps `git branch -r` meaningful — set `fetch.prune true`.
- Feature flags cost a runtime branch per check: negligible, unlike the permanent merge tax of an
  extra long-lived branch.

# Security Considerations
- **Fewer long-lived branches means fewer places a security fix can be forgotten.** A patch applied
  to `main` but not `develop` silently regresses on the next release — the classic git-flow security
  failure.
- **"Always deployable" is a security property**, not just convenience: an urgent patch can ship
  immediately, without stabilising an unrelated half-finished branch first.
- **Feature flags default OFF.** A flag defaulting on is an untested code path enabled in
  production; `ENFORCE_*` here default `False` deliberately, and are enabled only after a soak
  period.
- **A flag is also a rollback lever.** `LEDGER_CREDIT_AT_ALLOCATION` exists so a completed money
  migration can be reversed without a deploy — valuable precisely when something is going wrong.
- **Long-lived branches accumulate unreviewed drift.** A 289-commit branch is a large surface that
  never received proportionate review; the honest response is to say so in the PR.
- **Every long-lived branch needs its own protection.** Two permanent branches means two sets of
  rules — and on a free private repo, where server-side protection is paid, twice as much to
  enforce by convention ([Chapter 27](27_Pre_Push_Protection.md)).

# Architecture Decisions
- **Trunk-based, one permanent branch.** One developer, one deployment target, no customer running
  an old version. `develop` would be a second branch to keep in sync for no benefit.
- **Releases are annotated tags, not branches.** A tag is an immutable pointer with an author and a
  message; a release branch is a thing to maintain. `erp-v1.0.0` = `90c1f2f3`.
- **Squash-merge**, so `main` is a list of features and each reverts as a unit — which is also what
  makes [`git bisect`](35_Bisect.md) useful.
- **Feature flags instead of long-lived branches** for work that cannot ship: merged, tested, inert.
  Both `ENFORCE_*` flags default `False`.
- **Branch names carry intent** (`feat/`, `fix/`, `chore/`, …) so the branch list is self-describing
  and `--author`/prefix filtering works.
- **The model is written into `CONTRIBUTING.md`**, including §10's explicit *"no long-lived release
  branches"*. A model nobody can read is not a model.
- **The 289-commit branch is documented as a deviation**, not quietly reclassified as normal.

# Best Practices
- Keep the number of permanent branches at **one** unless you can name the customer who needs the
  second.
- Measure divergence weekly: `git rev-list --count origin/main..<branch>`.
- Merge within days. If a branch is growing, ship a slice behind a flag.
- Rebase onto `origin/main` rather than merging `main` into your branch.
- Give every feature flag an **owner and a removal condition** at creation time.
- Delete merged branches; set `fetch.prune true`.
- Write your model down, with its reasoning, in `CONTRIBUTING.md`.
- Record deviations honestly instead of redefining them as compliance.

# Beginner Mistakes
- **Adopting git-flow by default** because it appears in the most search results, without needing
  multi-version support.
- **Letting a feature branch live for weeks** → conflicts compound and the PR becomes unreviewable.
  This repo's own 289-commit branch is the example.
- **Trunk-based without CI** → "always deployable" becomes a slogan; nothing enforces it.
- **Merging `main` into a feature branch repeatedly** → a tangle of merge commits nobody chose.
  Rebase.
- **Using a long-lived branch to hide unfinished work** → use a flag; the branch gets no CI, no
  review and no testing.
- **Feature flags that default ON** → an untested path live in production.
- **Never removing flags** → permanent conditional complexity; every flag needs an expiry.
- **Not writing the model down** → the next person guesses, and guesses differently.

# Interview Questions
- **Junior:** "What is trunk-based development?" — One long-lived branch (`main`), short-lived
  feature branches merged back quickly, and releases marked with tags rather than branches. It
  depends on CI to keep `main` deployable and on feature flags for work that is not ready to be
  visible.
- **Mid:** "Difference between GitHub Flow and git-flow?" — GitHub Flow has one permanent branch
  and treats the PR as the ritual; git-flow has `main` **and** `develop` plus `release/*` and
  `hotfix/*`. The consequence is that git-flow requires applying fixes in several places and keeping
  two permanent branches in sync, which is worthwhile only if you must support multiple released
  versions simultaneously.
- **Senior:** "When would you actually choose git-flow?" — When customers install the software and
  upgrade on their own schedule, so you must patch 1.3 while 1.5 is in development. That genuinely
  needs a release branch. For a web app deployed to your own infrastructure it is overhead: the
  author himself published a note saying it is over-applied and that continuous-delivery teams
  should not use it. The decision reduces to one question — does anyone run an old version you must
  patch?
- **Staff:** "Team says they cannot do trunk-based because features take three weeks. Response?" —
  Three-week features are the problem the branching model is being asked to hide, so I would not
  start with branching. I would attack decomposition: ship the schema, then the service, then the
  UI, each behind a flag that defaults off — merged, CI-tested, inert — which is exactly how this
  project ships enforcement code (`ENFORCE_*` default `False`, enabled after a soak period, with a
  rollback lever kept for a completed money migration). That converts a three-week branch into
  three one-week merges with no divergence. I would also make the cost visible rather than argued:
  track `rev-list --count origin/main..branch` and review-time-per-line, because a long branch's
  price shows up as unreviewable diffs — this repo's own 289-commit branch forced a choice between
  merging unreviewed and splitting after the fact. And flags need governance: an owner and a removal
  condition at creation, or you have traded merge debt for permanent conditional complexity.

### Why interviewers ask these — and the answer that separates levels
| Testing for | Weak answer | What lands |
|---|---|---|
| Do you know the models? | "We use feature branches." | Name the variable: how many branches live forever — 1 for trunk-based/GitHub Flow, 2+ for git-flow, and every complication follows from that. |
| Can you justify, not just recite? | "git-flow is more professional." | git-flow buys parallel version support, paid for in multi-place fixes and permanent sync; choose it only if someone runs an old version. |
| Do you solve the real constraint? | "We'd need longer branches." | Decompose behind flags that default off; make divergence measurable, and give every flag an owner and expiry. |

**The killer follow-up:** *"Trunk-based means merging unfinished work. How is that safe?"* — Because merged is not the same as enabled. The code ships behind a flag defaulting off, so it gets CI, review and integration testing while being inert in production — and the flag doubles as a rollback lever that does not require a deploy. The weak answer treats a branch as the safety mechanism; a branch is the *opposite* of safety, since it is the one place code gets neither CI nor review.

# Revision Notes
- **The only variable that matters: how many branches live forever.** 1 = trunk-based/GitHub Flow; 2+ = git-flow.
- **Trunk-based:** one `main`, short branches, releases = **tags**. Needs CI + feature flags.
- **git-flow:** `main` + `develop` + `release/*` + `hotfix/*`. Fixes must be applied in 2–3 places; miss one ⇒ bug returns as a "regression".
- Choose git-flow **only** if someone runs an old version you must patch.
- Unfinished work ⇒ **merge behind a flag defaulting OFF**, not hide in a branch (branches get no CI, no review).
- This project: trunk-based, squash-merge, tags (`erp-v1.0.0` = `90c1f2f3`), `ENFORCE_SETTLEMENT_RECONCILIATION` default `False`, `pre-push` blocks `main`.
- **A flag defaulting OFF is not neutral.** `ENFORCE_ALLOCATION_BOUND` was **deleted** because its off-default let workers over-report — the enforcement became unconditional, the diagnostic stayed.
- Watch divergence: `git rev-list --count origin/main..<branch>`. 5 = healthy, **289 = this repo's own deviation**.
- Every flag needs an **owner and a removal condition**.

# Cheat Sheet
```bash
# measure your model
git branch -a                                   # how many permanent branches, really?
git tag -l                                       # releases as tags = trunk-based shape
git branch -r | grep -iE 'develop|release'       # ...as branches = git-flow shape

git fetch origin
git rev-list --count origin/main..feat/x         # DIVERGENCE — the health metric
git for-each-ref --sort=committerdate \
  --format='%(committerdate:short) %(refname:short)' refs/heads/   # branch AGE
git branch --merged   origin/main                # safe to delete
git branch --no-merged origin/main               # still carrying work

# trunk-based daily loop
git fetch origin && git switch main && git merge --ff-only origin/main
git switch -c feat/thing                         # feat|fix|chore|docs|refactor|test|perf
git fetch origin && git rebase origin/main       # stay current, stay linear
git push -u origin feat/thing                    # PR → CI → review → squash-merge → delete

# releases are tags, not branches
git tag -a erp-v1.1.0 -m "erp-v1.1.0 — accountant read tier"
git push origin erp-v1.1.0

git config --global pull.rebase true             # no unintended merge commits
git config --global fetch.prune true             # dead branches disappear
```

# My ERP Section

| Decision | This project |
|---|---|
| Model | **Trunk-based** — `CONTRIBUTING.md` §3 and §10 |
| Long-lived branches | **one**: `main` |
| Short-lived prefixes | `feat/` `fix/` `chore/` `docs/` `refactor/` `test/` `perf/` |
| Releases | annotated **tags** — `erp-v1.0.0` = `90c1f2f3` ([Ch 29](29_Semantic_Versioning_And_Tags.md)) |
| Merge strategy | **squash** — one feature = one commit on `main`, reverts as a unit |
| What keeps `main` deployable | CI: lint → migrations → **2,033 tests / 424 s** → docs BLOCKER=0 |
| Unfinished work | feature flags: `ENFORCE_SETTLEMENT_RECONCILIATION` (default `False`, WARN-only) + `SETTLEMENT_RECONCILIATION_TOLERANCE`; `LEDGER_CREDIT_AT_ALLOCATION` (default `False`) as a **rollback lever** for a completed money migration |
| Flag **retirement** | `ENFORCE_ALLOCATION_BOUND` **removed** 2026-07-20 — the bound is now hard and always enforced, because the FAT proved the soft/off default let workers over-report. `preview_allocation_bound` remains as a read-only audit |
| Why not git-flow | one developer, one VPS, nobody running an old version. `CONTRIBUTING.md` §10: *"git-flow is heavier than a 1–2 person team can justify."* |
| Push protection | `git-hooks/pre-push` refuses `main`; collaborators get Read + a fork ([Ch 27](27_Pre_Push_Protection.md)) |
| Honest deviation | `new_flask_app` reached **289 commits** before PR #15 — a long-lived branch, producing exactly the predicted unreviewable diff |

# Practice Tasks
1. Run the divergence loop from the Practical section in this repo. Which branch is furthest from
   `origin/main`, and is that healthy?
2. Run `git tag -l` and `git branch -r | grep -iE 'develop|release'`. From those two outputs alone,
   name this project's model.
3. Find the two `ENFORCE_*` flags in `config/config/settings/base.py`. Explain what a long-lived
   branch would have given instead — and what it would have cost.
4. Read `CONTRIBUTING.md` §10 and list every practice it forbids. For each, name the failure it
   prevents.
5. Draw git-flow on paper, then trace a single security fix that must reach `main`, `develop` and
   `release/1.4`. Count the places you could forget.
6. For a project of your own, write down the model in one paragraph with its reasoning. If you
   cannot, you do not have a model — you have a habit.

# Homework
- Take a feature you would normally branch for two weeks and decompose it into three
  flag-protected merges. Write the flag's owner and removal condition for each.
- Read Vincent Driessen's original git-flow post **and** the note he later added at the top about it
  being over-applied. Form your own view; that pairing is the most instructive reading in this
  chapter.
- Audit every branch in every repo you own by age and divergence. Anything older than a week either
  merges this week or becomes a flag.
- Write the `CONTRIBUTING.md` branching section for a hypothetical five-person team shipping a
  mobile app with app-store review delays. Notice that the answer changes — that is the point of
  choosing rather than copying.

# Further Reading & Live Resources
- [Trunk Based Development](https://trunkbaseddevelopment.com/) — the canonical, opinionated reference; free
- [GitHub Flow](https://docs.github.com/en/get-started/using-github/github-flow) — the short official description
- [A successful Git branching model](https://nvie.com/posts/a-successful-git-branching-model/) — the original git-flow post, **including the author's later caveat that it is over-applied**
- [Martin Fowler — Patterns for Managing Source Code Branches](https://martinfowler.com/articles/branching-patterns.html) — the most thorough free analysis of the trade-offs
- [Martin Fowler — Feature Toggles](https://martinfowler.com/articles/feature-toggles.html) — flag types, lifecycle, and how to retire them
- [Atlassian — Comparing workflows](https://www.atlassian.com/git/tutorials/comparing-workflows) — side-by-side diagrams of all three models
