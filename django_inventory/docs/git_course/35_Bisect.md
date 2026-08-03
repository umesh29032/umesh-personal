---
id: git-course-35-bisect
type: lesson
status: active
owner: handwritten
scope: git — bisect, binary search over history, automated bisection with a test script
anchors: config/learning/tests/test_learning.py, config/core/tests.py
verified: 2026-08-03
---

# 35 — Bisect (binary-search your history for the commit that broke it)

> Part of [Git Course](00_COURSE_OVERVIEW.md). Prev: [34 — Rewriting History Safely](34_Rewriting_History.md). Next: [36 — Monorepo, Submodules & Subtrees](36_Monorepo_Submodules_Subtrees.md).

# Learning Objectives
By the end of this chapter you can:
- explain why bisect is `log₂(n)` and what that means in practice
- run a manual bisect from start to finish without getting lost
- automate it with `git bisect run` and a script that returns the right exit codes
- explain exit code **125** and why it matters more than it looks
- use `skip`, `log`, `replay` and `--first-parent` when history is not cooperative
- say what makes a codebase bisectable — and recognise when yours is not

# Purpose
Something worked last month. It is broken now. There are 289 commits in between.

The instinct is to read the diff, or to reason about which change "looks responsible". Both scale
badly and both are guesswork. Bisect replaces guessing with **binary search**: git checks out a commit
in the middle, you say *good* or *bad*, and the search space halves. Every time.

289 commits becomes **9 tests**. And if you can express "broken" as a script that exits non-zero, git
runs the whole search itself while you do something else.

This is the highest leverage-per-minute skill in the whole course. It takes fifteen minutes to learn
and it will save you days.

# The Problem
"It worked in July" is a real bug report, and the usual approaches are bad:

- **Read the whole diff.** 289 commits, ~2,100 files, 336,372 insertions — nobody reads that.
- **Guess from experience.** Works when the bug is in your own recent code, fails exactly when the
  cause is somewhere unexpected — which is when you needed help.
- **Check commits one at a time.** Linear search: expect ~145 checkouts, each with a test run.

Bisect turns 145 into **9**. And the answer is not an opinion about which commit is suspicious; it is
*the* commit, identified mechanically.

# Theory (from zero)

### Binary search over the commit graph
You supply two points:

- a **good** commit where the behaviour is correct
- a **bad** commit where it is broken (usually `HEAD`)

Git checks out the midpoint. You test and report. Git discards half the range and repeats.

```
289 commits ──► 145 ──► 73 ──► 37 ──► 19 ──► 10 ──► 5 ──► 3 ──► 2 ──► 1
   test 1      2      3      4      5      6      7     8     9
```

**log₂(289) ≈ 8.2, so 9 tests.** The scaling is what makes this remarkable:

| Commits | Tests needed |
|---|---|
| 100 | 7 |
| **289** (this repo) | **9** |
| 1,000 | 10 |
| 10,000 | 14 |
| 1,000,000 | 20 |

Twenty tests to search a million commits. That is why bisect is worth learning properly rather than
half-remembering.

### The manual loop
```bash
git bisect start
git bisect bad                 # HEAD is broken
git bisect good erp-v1.0.0     # this tag was fine
# git checks out the midpoint...
#   test it, then:
git bisect good                # or: git bisect bad
#   ...repeat until git names the culprit
git bisect reset               # ALWAYS: returns you to where you started
```

Git prints its progress, which is reassuring:

```
Bisecting: 144 revisions left to test after this (roughly 8 steps)
```

`git bisect reset` is not optional housekeeping. During a bisect you are on a **detached HEAD**
([Chapter 10](10_Creating_And_Switching_Branches.md)), and forgetting to reset leaves you confused
about which branch you are on.

### `git bisect run`: let git do all of it
If "broken" can be expressed as a command that exits non-zero, git runs the entire search:

```bash
git bisect start HEAD erp-v1.0.0        # bad first, then good — one line
git bisect run ./check.sh
```

Exit-code contract, and the third row is the one people miss:

| Exit code | Meaning |
|---|---|
| **0** | good |
| **1–124, 126, 127** | bad |
| **125** | **cannot test this commit — skip it** |
| 128+ | abort the bisect |

**125 is the important one.** Some commits genuinely cannot be tested: a migration is missing, a
dependency did not exist yet, the file you are testing had not been created. Returning 125 tells git
to skip rather than mark it bad — and a commit wrongly marked bad sends the search down the wrong half
and produces a confidently wrong answer.

A robust script therefore checks its own preconditions first:

```bash
#!/usr/bin/env bash
# 125 = untestable (skip). 0 = good. 1 = bad.
[ -f config/manage.py ] || exit 125          # this commit predates the layout
env/bin/pip install -q -r requirements.txt || exit 125
env/bin/python config/manage.py test learning --settings=config.settings.local || exit 1
exit 0
```

### When history does not cooperate
```bash
git bisect skip                   # this commit cannot be tested (manual equivalent of 125)
git bisect skip v2.1..v2.3        # skip a whole range
git bisect log > bisect.log       # save the session
git bisect replay bisect.log      # resume it later, or share it
git bisect visualize              # see the remaining range in a log view
git bisect --first-parent bad     # follow only first parents — skip merged branch internals
```

`--first-parent` is the flag worth remembering on a squash-merge project: it searches the trunk's
feature commits rather than descending into each merged branch, which is usually where you want the
answer anyway ([Chapter 06](06_The_Commit_Graph.md)).

### `git bisect terms`: bisect is not only for bugs
The words are relabellable, because binary search does not care what you are looking for:

```bash
git bisect start --term-old=fast --term-new=slow
git bisect slow HEAD
git bisect fast erp-v1.0.0
```

Now you are searching for the commit that made something **slow**, or that changed a query count, or
that shrank a bundle. Same machinery.

### What makes a codebase bisectable
Bisect only works if each commit is **individually testable**. Three properties, all of which are
consequences of good habits taught elsewhere in this course:

1. **Every commit builds and runs.** A branch full of `wip` commits that do not run is unbisectable —
   which is one concrete argument for squashing before merge
   ([Chapter 14](14_Interactive_Rebase.md)).
2. **Atomic commits.** One commit, one change. A commit bundling four unrelated things identifies
   *four* candidate causes, so the answer is much less useful
   ([Chapter 03](03_The_Three_Trees.md)).
3. **A deterministic test.** A flaky test makes bisect produce a *random* answer, confidently. This is
   the failure mode that wastes the most time.

Point 3 deserves emphasis. Bisect trusts your verdict absolutely. One wrong `good` and it eliminates
the half containing the real cause, then names something innocent — and you will believe it, because
it was produced mechanically.

> 💡 **Samjho aise:** Dictionary mein shabd dhoondhne jaisa hai. Poori kitaab page-by-page nahi
> padhte — **beech se kholte ho**, dekhte ho aage hai ya peeche, aur aadhi kitaab hata dete ho. Phir
> dobara. 1000 page, **10 baar** kholna.
>
> Yahan bhi wahi: git beech ki commit nikaal deta hai, tum **good/bad** bolte ho, aadha range gayab.
> Is repo ki 289 commits = sirf **9 test**.
>
> Aur agar "toota hai" ek script se pata chal sakta hai, toh `git bisect run` khud poora dhoondh
> lega — tum chai pi lo.
>
> **Ek khatra:** git tumhare jawaab pe aankh band karke bharosa karta hai. Ek galat "good" bol diya,
> toh wo asli galti wale aadhe hisse ko hata dega aur ek **be-kasoor commit** ka naam le lega — aur
> tum maan bhi loge, kyunki machine ne bataya hai. Isliye test **pakka** hona chahiye, flaky nahi.

# Real World Example (this repo)
The 289-commit divergence in this repository is the perfect worked example of the arithmetic, and it
comes from a real number ([Chapter 21](21_Pull_Requests.md)): `main..new_flask_app` was **289
commits** before PR #15 merged.

Suppose a test that passed at `erp-v1.0.0` fails at `HEAD`. Linear search means ~145 test runs; the
battery is **424 seconds**, so that is roughly **17 hours**.

Bisect: `log₂(289) ≈ 9` runs ≈ **64 minutes**. Same answer, 16× faster — and unattended.

**A script sized for this project.** Running the full 2,033-test battery per step is wasteful; bisect
only needs the *one* behaviour that broke:

```bash
#!/usr/bin/env bash
# bisect-check.sh — exit 0 good · 1 bad · 125 untestable(skip)
set -u
cd "$(git rev-parse --show-toplevel)/django_inventory" || exit 125

# preconditions: an old commit may predate the file or the app entirely
[ -f config/manage.py ] || exit 125
grep -q "'learning'" config/config/settings/base.py 2>/dev/null || exit 125

# one targeted test, not the whole battery: 8 s instead of 424 s
env/bin/python config/manage.py test \
  learning.tests.test_learning.ChapterContractTests \
  --settings=config.settings.local >/dev/null 2>&1 || exit 1
exit 0
```

Two deliberate choices, and both are the point of this chapter:

- **The precondition checks return 125.** The `learning` app was only added recently; commits before
  that cannot possibly pass a learning test, and marking them **bad** would corrupt the search. This
  is exactly the case where a naive script produces a confidently wrong culprit.
- **One test class, not the battery.** `learning` alone runs in ~8 s versus 424 s for all 14 apps.
  Across 9 steps that is ~72 seconds instead of ~64 minutes.

**Why this project is bisectable at all** — three properties it has deliberately:

| Property | How this project gets it |
|---|---|
| Every commit runs | CI gates every PR: lint → migrations → **2,033 tests** → docs ([Ch 28](28_CI_With_GitHub_Actions.md)) |
| Atomic commits | **squash-merge**: one feature = one commit on `main`, so a culprit is a whole feature ([Ch 21](21_Pull_Requests.md)) |
| Deterministic tests | the battery runs **sequentially on a fresh database** — never `--parallel`, never `--keepdb`, because money assertions use advisory locks and shared sequences that parallel runs corrupt into false failures |

That last row is a bisect prerequisite that this project happened to get right for a different reason.
A suite that fails randomly under parallelism would make bisect useless, because bisect cannot tell a
flaky failure from a real one.

**And a real bug that bisect would have found instantly.** The UTC-versus-IST date defect
([Chapter 15](15_Undo_Reset_Revert_Restore.md) territory) lived in `bod` — an app that was in
`INSTALLED_APPS` but in **no test group**, so 37 tests sat outside the gate through two "all green"
baselines. Once `bod` was brought into the battery the failure was reproducible, and a reproducible
failure plus a tag known to be good is precisely a bisect. The hard part was never finding the commit;
it was noticing the test existed at all.

# Visual Diagram
```
  BINARY SEARCH OVER HISTORY
  ──────────────────────────
   erp-v1.0.0                                                      HEAD
      GOOD ●───────────────────────────────────────────────────────● BAD
           └──────────────── 289 commits ────────────────┘
                                  ▲
                        test 1: the midpoint
                     good? ⇒ discard the LEFT half
                     bad?  ⇒ discard the RIGHT half

   289 ► 145 ► 73 ► 37 ► 19 ► 10 ► 5 ► 3 ► 2 ► 1     = 9 tests  (log₂ 289 ≈ 8.2)

   linear search : ~145 runs × 424 s ≈ 17 HOURS
   bisect        :    9 runs × 424 s ≈ 64 min   (and unattended)
   bisect + one targeted test (8 s) ≈ 72 SECONDS

  EXIT-CODE CONTRACT for `git bisect run`
  ───────────────────────────────────────
        0        good
        1–124    bad
        126,127  bad
      ► 125      CANNOT TEST — SKIP        ← the one people miss
        128+     abort the bisect

   why 125 matters: an untestable commit marked BAD sends the search
   into the wrong half ⇒ a confidently WRONG culprit

  WHAT MAKES A REPO BISECTABLE
  ────────────────────────────
   every commit runs      ← CI on every PR
   atomic commits         ← squash-merge: 1 feature = 1 commit
   DETERMINISTIC tests    ← sequential, fresh DB, never --parallel/--keepdb
                            (a flaky test makes bisect answer at RANDOM)
```

# Practical — manual, then automated
```bash
cd /home/tech/umesh-personal

# ── MANUAL ──────────────────────────────────────────────────────────────────
git bisect start
git bisect bad                        # HEAD is broken
git bisect good erp-v1.0.0            # this was fine
# Bisecting: 144 revisions left to test after this (roughly 8 steps)
#   ...test the checked-out state, then report:
git bisect good                       # or  git bisect bad
#   ...repeat. git eventually prints:
#   <sha> is the first bad commit
git bisect reset                      # ALWAYS — you are on a detached HEAD until you do

# ── AUTOMATED ───────────────────────────────────────────────────────────────
cat > /tmp/check.sh <<'EOF'
#!/usr/bin/env bash
set -u
cd "$(git rev-parse --show-toplevel)/django_inventory" || exit 125
[ -f config/manage.py ] || exit 125                       # untestable: skip
env/bin/python config/manage.py test learning \
  --settings=config.settings.local >/dev/null 2>&1 || exit 1
exit 0
EOF
chmod +x /tmp/check.sh

git bisect start HEAD erp-v1.0.0      # bad, then good — in one line
git bisect run /tmp/check.sh          # git drives the whole search
git bisect reset

# ── WHEN HISTORY IS AWKWARD ────────────────────────────────────────────────
git bisect skip                       # this commit cannot be tested
git bisect skip v1.0..v1.1            # skip a range
git bisect log > /tmp/bisect.log      # save the session
git bisect replay /tmp/bisect.log     # resume / share it
git bisect visualize                  # view the remaining range
git bisect --first-parent bad         # trunk only, skip merged-branch internals

# ── NOT ONLY FOR BUGS ───────────────────────────────────────────────────────
git bisect start --term-old=fast --term-new=slow
git bisect slow HEAD && git bisect fast erp-v1.0.0
git bisect run /tmp/perf-check.sh     # find the commit that made it slow
```

Note the one-line form `git bisect start <bad> <good>` — it saves two commands and is what you will
actually use once the loop is familiar.

# Production Walkthrough
1. **Reproduce the failure reliably first.** Bisect on an intermittent bug produces a random answer.
   If you cannot reproduce it twice in a row, stop and fix that.
2. **Find a known-good point.** A release tag is ideal — `erp-v1.0.0` here. Do not guess; verify it is
   actually good before starting.
3. **Write the smallest possible check.** One test class, not the battery. 8 seconds versus 424
   compounds over 9 steps.
4. **Handle untestable commits with 125.** Check the file exists, the app is installed, dependencies
   install. This is the step that separates a correct bisect from a plausible one.
5. **`git bisect run`** and go do something else.
6. **Verify the culprit.** Check out the named commit, confirm the failure; check out its parent,
   confirm it passes. Bisect can be wrong if your test was.
7. **`git bisect reset`.**
8. **Then decide the fix:** `git revert` if the commit is self-contained, or a forward fix. And add a
   test that pins the behaviour, so the same commit cannot reintroduce it.

Step 6 is skipped constantly and is worth thirty seconds. A verified culprit is evidence; an
unverified one is a strong hypothesis.

# Debugging Guide

| Symptom | Cause | Fix |
|---|---|---|
| Bisect names an obviously innocent commit | you reported `good`/`bad` wrongly once, or the test is flaky | make the test deterministic, then `git bisect replay` a corrected log |
| "There are only 'skip'ped commits left to test" | too much of the range is untestable | widen the good/bad range; fix the script's preconditions |
| Stuck on a detached HEAD after bisecting | you forgot to reset | `git bisect reset` |
| `git bisect run` marks everything bad | the script exits non-zero for the wrong reason (missing dep, bad path) | run the script by hand on one commit; add `exit 125` preconditions |
| Every commit fails to build | dependencies changed across the range | install deps inside the script; `exit 125` when installation fails |
| Culprit is a merge commit | the range spans merges | `git bisect --first-parent`, or bisect inside the branch |
| Result differs between runs | non-deterministic test | fix determinism; parallel test runs are a common cause |
| Cannot find a good commit | the bug is older than you think | go much further back — a tag from a previous release |
| Bisect is very slow | you are running the whole suite per step | test one behaviour; a targeted test is 50× faster here |

# Performance Notes
- **`log₂(n)`**: 289 → 9 steps; 10,000 → 14; 1,000,000 → 20. The scaling is the entire value
  proposition.
- **Cost per step dominates.** Full battery = 424 s ⇒ ~64 min. One test class ≈ 8 s ⇒ ~72 s. Always
  write the narrowest possible check.
- **Dependency installation can dwarf the test.** If the range crosses a `requirements.txt` change,
  either accept the cost or `exit 125` when installation fails.
- **`--first-parent`** reduces the range on a merge-heavy history by skipping each merged branch's
  internals.
- **`git bisect` checkouts are cheap** — git switches trees, it does not re-download anything.
- **`git bisect log` + `replay`** means an interrupted session costs nothing; you can resume tomorrow.

# Security Considerations
- **`git bisect run` executes code from every commit it checks out.** On an untrusted repository —
  a fork, a PR from a stranger — that is arbitrary code execution on your machine. Bisect in a
  container or a disposable VM for anything you did not write.
- **Old commits have old dependencies**, which means old vulnerabilities. `pip install` inside a
  bisect script pulls historical versions with known CVEs; keep it isolated
  ([Chapter 32](32_Dependabot_And_Supply_Chain.md)).
- **A bisect script with credentials in it** ends up in your shell history and possibly in
  `.git/BISECT_LOG`. Read them from the environment.
- **Historical commits may contain secrets that current commits do not** — bisecting through the
  window when a secret was committed puts it in your working tree
  ([Chapter 33](33_Secrets_And_Leaks.md)).
- **Do not point a bisect script at production.** Checking out arbitrary old code and running
  migrations against a real database is how a bisect becomes an incident. Use a scratch database —
  this project has `scripts/db.sh` for exactly that.
- **Bisect result as evidence:** verify the culprit by checking out the commit and its parent.
  Attributing a security regression to the wrong commit misdirects the whole investigation.

# Architecture Decisions
- **Squash-merge makes bisect useful here.** One commit per feature means the culprit is a *feature*,
  not a fragment of one — and it reverts cleanly ([Chapter 21](21_Pull_Requests.md)).
- **CI on every PR keeps commits bisectable.** If broken commits could land on `main`, bisect would
  hit unbuildable states constantly and spend its steps on `skip`.
- **Sequential, fresh-database tests.** Chosen for money-assertion correctness, and it is a bisect
  prerequisite: `--parallel` or `--keepdb` would make failures non-deterministic, and bisect cannot
  distinguish flaky from real.
- **Release tags are annotated** (`erp-v1.0.0`), giving stable, meaningful known-good anchors
  ([Chapter 29](29_Semantic_Versioning_And_Tags.md)).
- **Targeted tests over the full battery** in bisect scripts — 8 s versus 424 s, ~50× per step.
- **`exit 125` treated as mandatory, not optional.** This project's app list has changed over time
  (`learning`, `bod`, `machines` were all added), so a large part of any long range genuinely cannot
  run a modern test.
- **`scripts/db.sh` exists** so a bisect can use a scratch database instead of the dev one.

# Best Practices
- Reproduce the bug **twice** before bisecting.
- Use a **release tag** as the known-good point, and verify it really is good.
- Write the **narrowest** check that detects the bug.
- Always handle untestable commits with **`exit 125`**.
- Prefer `git bisect run` — it is faster and removes human error from the good/bad calls.
- **Verify the culprit** against its parent before believing it.
- `git bisect reset` every time, without exception.
- `git bisect log > file` before anything risky, so the session is resumable.
- Bisect untrusted code in a container.
- After the fix, add a test that pins the behaviour so it cannot silently return.

# Beginner Mistakes
- **Reading the whole diff instead of bisecting** → hours for what nine tests would answer.
- **Marking untestable commits as `bad`** → sends the search into the wrong half and yields a
  confidently wrong culprit. Use `skip` / `exit 125`.
- **Bisecting a flaky test** → a random answer that looks authoritative.
- **Forgetting `git bisect reset`** → stranded on a detached HEAD, confused about the current branch.
- **Running the full suite per step** → 64 minutes where 72 seconds would do.
- **Believing the result without verifying** against the parent commit.
- **Guessing the good commit** → if it was already broken, every conclusion is wrong.
- **Running `bisect run` on an untrusted repo** → arbitrary code execution.
- **Pointing the script at the dev or production database** → migrations from arbitrary commits
  against real data.

# Interview Questions
- **Junior:** "What does `git bisect` do?" — Binary-searches your history for the commit that
  introduced a change in behaviour. You mark a known-good and a known-bad commit; git checks out the
  midpoint, you report good or bad, and the range halves each time until one commit remains.
- **Mid:** "How many tests for 1,000 commits, and why?" — About 10, because each verdict halves the
  search space, so it is `log₂(n)`. That is the whole point: linear search would be ~500 tests. It also
  means the cost per test matters far more than the range length — narrowing the test from 424 seconds
  to 8 saves more than shrinking the range would.
- **Senior:** "What is exit code 125 and why does it matter?" — It tells `git bisect run` that this
  commit **cannot be tested**, so git skips it instead of classifying it. It matters because marking an
  untestable commit as bad eliminates the half that contains the real cause, and bisect then names an
  innocent commit with total confidence. In a repo where apps were added over time, a long range
  legitimately contains commits that predate the code under test, so the preconditions in the script
  are what make the result trustworthy.
- **Staff:** "Your team says bisect does not work on their repo. Diagnose." — That is almost always a
  statement about the repository's hygiene rather than the tool, and there are three distinct causes
  worth separating. First, commits that do not individually build or run: bisect spends its steps on
  `skip`, which happens when broken commits can reach the trunk, so the fix is a CI gate on every PR,
  not a different debugging tool. Second, non-atomic commits: if one commit bundles four changes,
  bisect correctly identifies it and the answer is still nearly useless — squash-merging one feature
  per commit is what makes a culprit actionable. Third, and most damaging, non-deterministic tests:
  bisect trusts each verdict absolutely, so a flaky test makes it eliminate the wrong half and produce
  a **confidently wrong** answer, which is worse than no answer because people act on it. This project
  runs its suite sequentially on a fresh database specifically because money assertions use advisory
  locks and shared sequences that parallel runs corrupt into false failures — a determinism decision
  taken for correctness that happens to be a bisect prerequisite. So I would ask to see a failing
  bisect log: whether it is full of skips, or produced an unverifiable culprit, tells you which of the
  three you have.

### Why interviewers ask these — and the answer that separates levels
| Testing for | Weak answer | What lands |
|---|---|---|
| Do you know the tool exists? | "It helps find bugs." | Binary search over commits; you supply good and bad, git halves the range each verdict. |
| Do you understand the scaling? | "It's faster than checking each one." | `log₂(n)`: 289 → 9, a million → 20 — so cost *per test* dominates, and narrowing the test beats narrowing the range. |
| Do you know the failure modes? | "You mark commits good or bad." | 125 for untestable commits, because a misclassification eliminates the correct half; and a flaky test makes bisect answer at random. |

**The killer follow-up:** *"Bisect named a commit that obviously cannot be the cause. What happened?"* — One verdict was wrong: either the test is non-deterministic, or an untestable commit was marked bad instead of skipped. Bisect never doubts you, so a single bad call eliminates the half containing the real cause and it then reports an innocent commit with full confidence. The fix is `git bisect log`, correct the mistaken entry, and `git bisect replay` — after making the test deterministic. Reaching for "my input was wrong" rather than "the tool is broken" is the entire test.

# Revision Notes
- Bisect = **binary search over history**. You give **good** + **bad**; git halves the range per verdict.
- **`log₂(n)` steps.** 289 → **9** · 1,000 → 10 · 1,000,000 → 20.
- Manual: `bisect start` → `bad` → `good <ref>` → test → `good`/`bad` → … → **`bisect reset`** (you are on a detached HEAD until then).
- One-liner: **`git bisect start <bad> <good>`**, then **`git bisect run ./check.sh`**.
- Exit codes: **0 good · 1–124/126/127 bad · 125 = UNTESTABLE (skip) · 128+ abort.**
- **125 is the one that matters:** an untestable commit marked *bad* ⇒ a confidently wrong culprit.
- Narrow the test, not the range: 8 s vs 424 s over 9 steps = 72 s vs 64 min.
- `skip` · `log`/`replay` (resume a session) · `visualize` · **`--first-parent`** (trunk only) · `--term-old/--term-new` (find "slow", not just "broken").
- Bisectable needs: **every commit runs** (CI) · **atomic commits** (squash-merge) · **deterministic tests** (sequential, fresh DB).
- **A flaky test makes bisect answer at random.** Always verify the culprit against its parent.

# Cheat Sheet
```bash
git bisect start                     # begin
git bisect bad                       # current commit is broken
git bisect good erp-v1.0.0           # this ref was fine
git bisect start HEAD erp-v1.0.0     # ...or both in one line (bad, then good)

git bisect good | bad                # report the checked-out commit
git bisect skip                      # cannot test this one
git bisect skip v1.0..v1.1           # skip a range
git bisect reset                     # ALWAYS finish with this

git bisect run ./check.sh            # fully automated
#   exit 0 = good · 1..124,126,127 = bad · 125 = SKIP · 128+ = abort

git bisect log > bisect.log          # save the session
git bisect replay bisect.log         # resume / share / correct a mistake
git bisect visualize                 # view the remaining range
git bisect --first-parent bad        # trunk only, skip merged-branch internals

git bisect start --term-old=fast --term-new=slow   # find a PERF regression
git bisect slow HEAD && git bisect fast erp-v1.0.0
```
```bash
#!/usr/bin/env bash
# check.sh — the shape that makes bisect trustworthy
set -u
cd "$(git rev-parse --show-toplevel)/django_inventory" || exit 125
[ -f config/manage.py ] || exit 125                    # commit predates the layout
grep -q "'learning'" config/config/settings/base.py || exit 125   # app not installed yet
env/bin/python config/manage.py test learning \
  --settings=config.settings.local >/dev/null 2>&1 || exit 1
exit 0
```

# My ERP Section

| Fact | This repository |
|---|---|
| Range that made the arithmetic real | `main..new_flask_app` = **289 commits** before PR #15 ⇒ `log₂(289) ≈ 9` tests |
| Linear vs bisect | ~145 runs × 424 s ≈ **17 hours** versus 9 × 424 s ≈ **64 min** |
| Bisect with a targeted test | `learning` alone ≈ 8 s ⇒ ~**72 seconds** total |
| Known-good anchor | annotated tag **`erp-v1.0.0`** = `90c1f2f3` |
| Why `exit 125` is mandatory here | `learning`, `bod` and `machines` were all added over time, so older commits genuinely cannot run a modern test |
| Bisectable because — every commit runs | CI on every PR: lint → migrations → **2,033 tests** → docs |
| Bisectable because — atomic commits | **squash-merge**: one feature = one commit on `main` |
| Bisectable because — deterministic | battery runs **sequentially on a fresh DB**, never `--parallel`/`--keepdb` (money assertions use advisory locks + shared sequences) |
| Scratch database | `scripts/db.sh` — so a bisect never touches the dev DB |
| Related real bug | the UTC/IST date defect hid in `bod`, which was installed but in **no test group** — 37 tests outside the gate through two "all green" baselines. Bisect needs a test to exist before it can help |

# Practice Tasks
1. Compute `log₂` for your own repo's commit count. That number is how many tests a bisect will cost.
2. Run a manual bisect in this repo between `erp-v1.0.0` and `HEAD`, answering `good` every time.
   Watch the "revisions left" number halve. Then `git bisect reset`.
3. Write a `check.sh` that returns **125** when `config/manage.py` does not exist, and confirm by hand
   that it exits 125 on an old enough commit.
4. Run a real `git bisect run` with a test you know passes at both ends. Confirm git terminates
   sensibly rather than naming a culprit.
5. Deliberately mismark one commit, let bisect produce a wrong answer, then use `git bisect log`,
   edit the log, and `git bisect replay` to correct it. This is the recovery skill.
6. Use `--term-old=fast --term-new=slow` and bisect for a performance change instead of a bug. Same
   machinery, different question.

# Homework
- Introduce a bug deliberately in a throwaway repo, twenty commits deep, then find it with
  `git bisect run`. Time yourself against reading the diff.
- Write a bisect script for **this** project that checks one specific money invariant (a golden
  settlement figure), with proper `exit 125` preconditions. That is the script you would actually want
  during a real incident.
- Read `git help bisect` fully — particularly `--no-checkout`, which bisects without touching the
  working tree and is useful for very large repos.
- Audit your own test suite for determinism: run it three times and diff the results. If they differ,
  bisect cannot help you, and that is a more urgent problem than whatever bug you were chasing.

# Further Reading & Live Resources
- [Pro Git — Debugging with Git](https://git-scm.com/book/en/v2/Git-Tools-Debugging-with-Git) — bisect and blame together; free
- [git-bisect reference](https://git-scm.com/docs/git-bisect) — every subcommand, including `terms`, `replay`, `--no-checkout`
- [git-bisect-lk2009](https://git-scm.com/docs/git-bisect-lk2009) — a deep, readable explanation of the algorithm and its heuristics
- [Learn Git Branching](https://learngitbranching.js.org/) — practise the history navigation bisect relies on
- [`git blame`](https://git-scm.com/docs/git-blame) — the complementary tool: bisect finds *when*, blame finds *who and which line*
- [Google Testing Blog — flaky tests](https://testing.googleblog.com/2016/05/flaky-tests-at-google-and-how-we.html) — why determinism is a prerequisite, not a nicety
