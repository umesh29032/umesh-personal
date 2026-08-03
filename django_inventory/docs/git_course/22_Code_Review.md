---
id: git-course-22-code-review
type: lesson
status: active
owner: handwritten
scope: git, version control — reading and judging a pull-request diff, and the review standard this repo holds
anchors: CONTRIBUTING.md, .github/pull_request_template.md, .github/CODEOWNERS, django_inventory/CLAUDE.md
verified: 2026-08-03
---

# 22 — Code Review (reading a diff like you are going to co-sign it)

> Part of [Git Course](00_COURSE_OVERVIEW.md). Prev: [21 — Pull Requests](21_Pull_Requests.md). Next: [23 — CODEOWNERS & PR Templates](23_CODEOWNERS_And_Templates.md).

# Learning Objectives
By the end of this chapter you can:
- read a **unified diff** — file header, `index` line, `@@` hunk header — without guessing
- explain why review uses `git diff main...branch` (**three** dots) and history `git log main..branch` (**two**)
- review a branch from the command line: shape → story → substance → proof
- re-review a force-pushed branch with `git range-diff` instead of reading it all again
- apply this repo's six-axis standard, and know when a finding is a **STOP** not a nit

# Purpose
A Pull Request ([Ch 21](21_Pull_Requests.md)) is only a container. **Review** is the work inside it, and the one gate that catches what no test and no linter can: a wrong *intention*, a widened permission, a money write in the wrong place. This chapter teaches the mechanics of reading a diff, the order that makes review fast, and the standard `CONTRIBUTING.md` §5 holds a PR to.

# The Problem
What a reviewer was handed for PR #15 in this repository:

```
$ git rev-list --count main..new_flask_app
296
$ git diff --stat main...new_flask_app | tail -1
 5040 files changed, 336453 insertions(+), 331748 deletions(-)
```

296 commits, 5,040 files (snapshot 2026-08-03). Nobody reviews that. A human scrolls for ninety seconds, feels guilty, and types **LGTM** — a lie with a timestamp on it, attached to the change forever. That is not the reviewer's discipline failing; the **author** built an unreviewable object.

This project has already paid for a missed review. A bug wrote `entry_date` in UTC instead of IST inside the **primary settlement path** (`django_inventory/config/expense/services/adda_settlement_service.py`, lines 438 and 448) — a money record filed under the wrong day. Tests were green: they asserted the *amount*, which was right. One reviewer question — *"which day is that, in whose timezone?"* — catches it in ten seconds.

# Theory (from zero)

### What a diff actually is
A **diff** describes how to turn file A into file B. Git prints the **unified diff** format — here, the real change that puts this course on `/learn/`:

```diff
diff --git a/django_inventory/config/learning/registry.py b/django_inventory/config/learning/registry.py
index 04de1755..a2712fb8 100644
--- a/django_inventory/config/learning/registry.py
+++ b/django_inventory/config/learning/registry.py
@@ -65,6 +65,17 @@ COURSES: tuple[Course, ...] = (
     ),
+    Course(
+        slug='git',
+    ),
 )
```

1. `a/` is **before**, `b/` **after**. Same path both sides ⇒ modified, not renamed.
2. `index 04de1755..a2712fb8 100644` — the **blob** hashes before/after ([Ch 05](05_How_Git_Stores_Everything.md)) plus the file mode. `100644` = ordinary, `100755` = executable. **A flip to `100755` means "this file just became runnable" — always ask why.**
3. `@@ -65,6 +65,17 @@` — the **hunk header**, the most-skipped line in review: *from old line 65, 6 old lines; from new line 65, 17 new lines* ⇒ **11 added, none removed**. The text after the second `@@` is git's guess at the enclosing block: free context.
4. Body: leading **space** = context, `-` removed, `+` added (3 context lines; `-U10` for more).

A hunk with no `-` lines is purely additive and cheap. A `-` beside a `+` is a *change* — a place behaviour can move.

### Two dots vs three dots — name the confusing bit
| Command | Means | Use for |
|---|---|---|
| `git log main..branch` | commits in `branch`, not in `main` | listing what the PR adds |
| `git diff main..branch` | difference between the two **tips** | almost never in review |
| `git diff main...branch` | `merge-base(main, branch)` → `branch` | **the PR's real diff** |

If `main` moved on after you branched, `git diff main..branch` also shows *other people's* commits — **reversed**, as if your branch deleted them. Three dots asks git for the **merge base** first (the last commit both sides share, [Ch 11](11_Merging.md)) and diffs from there, so you see only your own work. **GitHub's "Files changed" tab is a three-dot diff.** Memorise the asymmetry: **log two, diff three.** In this repo both print the same today, because local `main` is an *ancestor* of `new_flask_app` — the merge base *is* `main`'s tip. Luck, not a rule.

### The reading order — shape, story, substance, proof
1. **Claim** — the PR body. Empty body ⇒ stop and ask ([Ch 23](23_CODEOWNERS_And_Templates.md) makes empty impossible here).
2. **Shape** — `git diff --stat main...branch`. Hunt the *surprise* file: a migration, a settings change, a permission service, anything in `.github/`.
3. **Story** — `git log --oneline --no-merges main..branch`. Decisions in sequence, or a "fix typo" that should have been squashed ([Ch 14](14_Interactive_Rebase.md))?
4. **Substance** — the diff, riskiest file first, never alphabetically.
5. **Proof** — tests; then run anything user-facing in a second working directory: `git worktree add /tmp/review origin/<branch>`, undone by `git worktree remove` ([Ch 17](17_Stash_And_Worktrees.md)).

### `git range-diff` — re-reviewing after a rebase
The author rebases and force-pushes ([Ch 34](34_Rewriting_History.md)); every hash changed. Do not start over: `git range-diff main <old-tip> <new-tip>` pairs the old commit series against the new and prints **a diff of the diffs** — a clean rebase shows almost nothing, a real edit stands out. Get `<old-tip>` from `git reflog show <branch>` ([Ch 16](16_Reflog.md)).

### The standard this repo holds (CONTRIBUTING.md §5)
Six axes, in **risk order**:
- **Correctness** — does it do what the description claims? Read the code, not the description.
- **Money** — settlement is the **only** money-write boundary, and each ledger/audit table has exactly **one** writer service (rules 4 and 5). A money write outside an approved service is a **STOP**.
- **Permissions** — a new ungated view or widened role is a silent, permanent privilege grant. Read the **gate**, not the comment.
- **Tests · Docs · Mobile** — is the *failure mode* pinned or only the happy path; is the `.md` in the **same PR** (rule 12); is the UI verified at mobile + tablet + desktop (rule 11)?

Label every comment: `nit:` (cosmetic) · `question:` (not blocking until answered) · `suggestion:` (author's call) · `blocking:` (say why, and what would satisfy you).

> 💡 **Samjho aise:** Review matlab **guarantor banna** — kisi ke loan pe apna naam likh dena. "LGTM" ka matlab hai "kuch galat nikla to meri bhi zimmedari". Isliye reviewer teen sawaal poochta hai: *paisa kahan likha ja raha hai? · kaun dekh sakta hai? · toota to pata kaise chalega?* Aur yaad rakho — **500 line ka diff padha jaata hai, 5000 line ka sirf scroll hota hai.**

# Real World Example (this repo)
**The unreviewable one.** PR #15 merged `new_flask_app` → `main` at `83a144ba`, and its own message admits the problem — `git show --no-patch --format="%b" 83a144ba` prints `ERP: accountant read tier, student role, learning platform, UTC date-class fix (+288 prior commits)`. The honest verdict on *"+288 prior commits"* is not approve or reject — it is **"split this."**

**The reviewable one.** Two minutes of work:
```
$ git show --stat --format="%h %s" 5b9d1601
5b9d1601 fix(inventory): role form mobile-responsive grids + scoped header type
 .../config/templates/inventory/role_form.html      | 22 ++++++++++++++++++----
 1 file changed, 18 insertions(+), 4 deletions(-)
```
One file, +18/−4, and the body names the rule it satisfies (mobile-first, rule 11). **Imitate this shape.**

**Size is not risk.** `git show --stat --format="%s" 42a2ecc4 | tail -1` gives `2956 files changed, 81 insertions(+), 331748 deletions(-)` — reviewable in a minute, because the message explains the shape: `git rm --cached` on two `pg_dump` files and 2,952 `node_modules` files, deletions only, files kept on disk. **Judge a diff by its number of distinct *decisions*, not its lines.** That one holds exactly one.

# Visual Diagram
```
                   merge-base (last commit both sides share)
                            |
  main   --A--B--C----------o--D--E          (main moved on after the branch)
                            |
  branch                    +--X--Y--Z   <- tip

  git log  main..branch   ->  X Y Z              (commits added — TWO dots)
  git diff main..branch   ->  o+X+Y+Z vs o+D+E   => shows D,E REVERSED. WRONG for review.
  git diff main...branch  ->  o       vs o+X+Y+Z => exactly what the PR adds. THREE dots.
                              (= GitHub's "Files changed" tab)

  ORDER: claim -> shape(--stat) -> story(log) -> substance(risky first) -> proof(tests, RUN it)
  AXES:  correctness · MONEY(stop) · PERMISSIONS(stop) · tests · docs(r12) · mobile(r11)
  force-pushed?  git range-diff main OLD_TIP NEW_TIP   (a diff OF the diffs)
```

# Practical — review a branch from the command line
```bash
git fetch origin                                                 # never review a stale copy
git log --oneline --no-merges origin/main..origin/new_flask_app | head
git diff --stat origin/main...origin/new_flask_app | tail -1      # THREE dots: the shape
git diff origin/main...origin/new_flask_app -- 'django_inventory/config/expense/**'  # money first
git diff origin/main...origin/new_flask_app -- '*/migrations/*'                      # then migrations
git diff --stat origin/main...origin/new_flask_app -- .github git-hooks              # then CI + hooks
git diff -w --find-renames origin/main...HEAD   # ignore whitespace churn; detect moved files
```
Expected shape line today: `5040 files changed, 336453 insertions(+), 331748 deletions(-)`. Path-limiting is the trick on a big PR: review the risky subtrees properly, then say in the PR which parts you read.

⚠️ Two commands a reviewer must never reach for:
```bash
git push --force origin their-branch   # DESTROYS their commits. --force-with-lease, own branch only.
git reset --hard origin/main           # throws away YOUR uncommitted work
```
Undo for the second: `git reflog` → `git reset --hard HEAD@{1}` restores the commit pointer, but **uncommitted** changes are gone forever ([Ch 15](15_Undo_Reset_Revert_Restore.md)). Stash first, or review in a worktree.

# Production Walkthrough
1. Author pushes `feat/their-thing` and opens the PR; the template forces the *why*, the verification evidence and explicit money/permission answers ([Ch 23](23_CODEOWNERS_And_Templates.md)).
2. CI runs `lint` → `migrations` → `test` (`needs: [lint, migrations]`) → `docs`. The reviewer does **not** read until it is green — otherwise you review code that is about to change.
3. Reviewer: `git fetch`, three-dot `--stat`, choose the risk order, read, comment with weights. If the author rebases, re-review with `range-diff`.
4. Approve → **squash-merge** → delete the branch: one feature = one commit on `main`, so any feature reverts cleanly.

**Two honest free-plan limits:** nothing *mechanically* blocks merging a red PR — "require checks to pass" is paid on private repos, so CI is a **visible** gate held by discipline. And the local `gh` CLI is authenticated as **`umesh2030`** (the owner's office account) while this repo lives under **`umesh29032`**, so `gh pr create` fails with `must be a collaborator`.

# Debugging Guide
| Symptom | Cause | Fix |
|---|---|---|
| Diff shows other people's commits as deletions | Two dots, and `main` moved | Three dots: `git diff main...branch` |
| Your `--stat` differs from GitHub's | Local `main`/`origin/main` is stale | `git fetch origin`, diff against `origin/main` |
| `warning: exhaustive rename detection was skipped` | More paths than `diff.renameLimit` | Path-limit, or `git -c diff.renameLimit=3000 diff …` |
| Whole file changed, nothing looks different | Whitespace / reformat churn | `git diff -w`; ask for the reformat as its own commit |
| Force-push wiped your review context | Author rebased ([Ch 13](13_Rebase.md)) | `git range-diff main <old-tip> <new-tip>` |

# Performance Notes
- **Human throughput is the bottleneck, not git.** A ~200-line PR gets a genuine review; a 2,000-line PR gets "LGTM" — that sentence is in `CONTRIBUTING.md` §5 because it is measurable.
- `--stat` over 5,040 paths prints in about a second, but git **abandons exhaustive rename detection** and says so, suggesting `diff.renameLimit` ≥ 2940 — detection costs roughly *added × deleted*, hence the cap.
- Object store here: `size-pack: 63.66 MiB`, `in-pack: 25975` objects, `.git` ≈ 97 MB — every review command is instant (`git count-objects -vH`, [Ch 37](37_Large_Files_And_Performance.md)). CI should be the slow part: the battery is **2033 tests across 14 apps in ~424 s**, sequential on a fresh DB. Review while it runs.

# Security Considerations
- **Review the gate, not the comment.** A diff can say `# super-admin only` above a view that checks nothing. Permissions go through `permission_service`; a raw `is_superuser` check in a view is a finding by rule (rule 6). A widened permission is silent and permanent — which is why `.github/CODEOWNERS` names `config/accounts/services/` and `config/inventory/middleware.py`.
- **Look for data in the diff:** `.env`, `*.sql`, `*.dump`, media, `node_modules`. The monorepo-root `.gitignore` blocks those and `git add -f` deliberately still works, so a force-added file is possible and a reviewer should spot it. This repo learned it the hard way: `Django_app/myproject/mydb_backup_20250618.sql` and `..._20250620.sql` sat tracked in public history until `42a2ecc4` untracked them ([Ch 33](33_Secrets_And_Leaks.md)).
- **A diff touching `.github/workflows/` is a privilege change, not a config change** — CI runs with repository credentials, so a workflow edit can print secrets into a log. `ci.yml` declares `permissions: contents: read`; widening it needs a stated reason.
- **Money paths get a second reviewer** (`CONTRIBUTING.md` §10). If nobody is available, say so in the PR.

# Architecture Decisions
- **Squash-merge, always.** One feature = one commit on `main`, so history reads as a list of features and any one reverts cleanly. Rejected: merge commits on `main` (history becomes a braid) and rebase-merge (keeps every "fix typo" forever).
- **Small PRs over heroic reviewers.** The fix for an unreviewable diff is smaller diffs, not more stamina. PR #15 is the recorded counter-example.
- **Six named axes instead of "use your judgement."** Money and permissions are where this project has been bitten, so the template asks them *explicitly*.
- **A money write outside an approved service is a STOP**, not a follow-up ticket: single-writer discipline only holds if it is never once broken.
- **CI as a visible gate rather than a paid mechanical block** — owner ruling: budget goes to deploy infrastructure, not subscriptions. The gap is documented, not pretended away.

# Best Practices
- Fetch before you review; a stale `main` reviews the wrong thing.
- Three dots for the diff, two for the log.
- Read `--stat` first and choose your own order — never alphabetical.
- Money, permissions, migrations and `.github/` first; formatting last.
- Label every comment: `nit:` / `question:` / `suggestion:` / `blocking:`.
- Ask "does this test fail without the change?" — that is the whole tests question.
- If a PR is too big to review, say so and ask for a split. That is a valid outcome.

# Beginner Mistakes
- **`git diff main..branch` for review** → you see other people's commits reversed. Use `main...branch`, which is what GitHub shows.
- **Reviewing without `git fetch`** → you compare against last week's `main`.
- **Skipping the `@@` header** → you read an 11-line insertion as an edit. It is free context.
- **"LGTM" on a 2,000-line diff** → a signature on something unread. Path-limit and state what you read, or ask for a split.
- **Reviewing the comment instead of the gate** → an ungated view with a reassuring comment passes review.
- **`git reset --hard` on the review copy** → your uncommitted work is destroyed, and `reflog` cannot recover what was never committed. Stash, or use a worktree.
- **Treating "tests pass" as "reviewed"** → the UTC settlement-date bug had green tests. Green CI clears only failure modes someone already imagined.

# Interview Questions
- **Junior:** "What is the difference between `git diff main..branch` and `git diff main...branch`?" — Two dots diffs the two branch **tips**, so if `main` moved you also see other people's commits, reversed. Three dots diffs from the **merge base** to the branch tip — exactly what the branch adds, and exactly GitHub's "Files changed" tab. For review, always three dots; for `git log`, two. *Log two, diff three.*

- **Mid:** "Walk me through reviewing a 40-file pull request." — PR body for the claim; `git fetch`; `git diff --stat origin/main...branch` for the shape; `git log --oneline` for the story. Then pick a risk order — money, permissions, migrations, workflow files — and path-limit the diff to each. Read the tests and ask whether they fail without the change; run it in a `git worktree` if it touches UI. Comment with weights, and state which parts I actually read.

- **Senior:** "The author force-pushes after your review. How do you re-review without redoing the work?" — `git range-diff <base> <old-tip> <new-tip>` pairs the old series against the new and shows a diff of the diffs, so a clean rebase shows almost nothing and any real edit stands out; get the old tip from `git reflog show <branch>`. I check that no commit was dropped and that no *new* change hid inside the rebase — the classic way an unreviewed hunk lands — then re-run CI, because a rebased state is code no test has ever seen.

- **Staff:** "Our reviews are rubber stamps. Design the fix." — Rubber-stamping is a symptom of unreviewable PRs, not lazy people, so I attack size first: split-by-default, plus a template that forces the *why* and explicit money/permission answers so silence is not an option. Then route the high-risk surfaces mechanically (a `CODEOWNERS` naming money, permission, migration and CI paths) and move everything mechanical off humans — lint, `makemigrations --check`, the full battery, a docs-drift check — so attention goes only to intent. Then close the loop with evidence: the PR states what was verified, and reviewers state what they did **not** read, which makes partial review honest instead of invisible. And be honest about the platform: on a free private plan "block merge on red" is paid, so the gate is discipline plus a `pre-push` hook plus Read-only collaborator access, with the one real gap (a fresh clone, no hook) written down. The invariant: **a review is a co-signature; if a reviewer cannot describe the failure mode they cleared, the review did not happen.**

### Why interviewers ask these — and the answer that separates levels

| Testing for | Weak answer | What lands |
|---|---|---|
| Do you know diff *mechanics*, or just the GitHub button? | "I look at the Files changed tab." | Name **three-dot vs two-dot**, the **merge base**, and read a `@@ -65,6 +65,17 @@` header out loud. |
| Do you have a review *order*, or do you scroll? | "I read the whole diff carefully." | Claim → shape → story → substance, risk-first: **money, permissions, migrations, workflow files**. |
| Do you know what review catches that CI cannot? | "CI runs the tests, so review is a formality." | Intent, a widened permission, a money write in the wrong service, a wrong timezone basis — all green in CI. |
| Can you review a *rebased* branch? | "I read it again." | `git range-diff` against the old tip from the reflog, then re-run CI because the rebased state is untested. |

**The killer follow-up:** *"Tell me about a bug that passed review — and what you changed about reviewing afterwards."* — Naming a real miss (green tests, wrong timezone on a money record) and the process change it caused separates someone who has reviewed from someone who has read about reviewing.

# Revision Notes
- **log two dots, diff three dots.** `git diff main...branch` = merge base → tip = what GitHub shows.
- `@@ -a,b +c,d @@` = old start/count, new start/count, plus the enclosing block for free.
- Order: claim → shape → story → substance → proof. Risk order inside the diff: **money · permissions · migrations · `.github/` · everything else**.
- A money write outside an approved single-writer service is a **STOP** (rules 4 & 5).
- After a force-push: `git range-diff <base> <old> <new>`; old tip from `git reflog show <branch>`.
- ⚠️ A 2,000-line PR does not get reviewed. Asking for a split is a valid review outcome.

# Cheat Sheet
- **Fetch first:** `git fetch origin` — never review a stale `main`.
- **What it adds:** `git log --oneline --no-merges origin/main..branch` *(two dots)*.
- **The PR diff:** `git diff origin/main...branch` *(three dots = merge base → tip)*.
- **Shape:** `git diff --stat origin/main...branch | tail -1` · **ratios:** `git show --numstat --format="" <sha>`.
- **Risk slices:** `… -- 'django_inventory/config/expense/**'` · `… -- '*/migrations/*'` · `… -- .github git-hooks`.
- **Noise filters:** `-w` whitespace · `--word-diff` prose · `--find-renames` moves · `-U10` more context.
- **After a force-push:** `git range-diff origin/main <old-tip> <new-tip>`.
- **Run it safely:** `git worktree add /tmp/review origin/branch` → `git worktree remove /tmp/review`.
- ⚠️ **Never** force-push someone else's branch; **never** `git reset --hard` over uncommitted work.

# My ERP Section
| Review concern | How it shows up here |
|---|---|
| Rulebook | `CONTRIBUTING.md` §5 — PR flow + the six-axis review standard |
| Forcing function | `.github/pull_request_template.md` — why, verification, money & permissions answered explicitly |
| Who reviews what | `.github/CODEOWNERS` — `config/expense/`, `production/services/`, `accounts/services/`, `*/migrations/`, `.github/`, `git-hooks/` |
| Automated half | CI `lint` → `migrations` → `test` → `docs` (`knowledge_sync` BLOCKER=0); battery 2033 tests / 14 apps / ~424 s |
| Counter-example vs model | PR #15 (`83a144ba`) 296 commits — refuse; `5b9d1601` 1 file +18/−4 — imitate |

# Practice Tasks
1. **Read a hunk header.** Run `git show af01b9e7 -- django_inventory/docs/apps/production/GUIDE.md` and turn its `@@` line into a sentence: which old lines, which new, how many added, how many removed.
2. **Prove the dots.** Run the two-dot and three-dot `--stat` for `main`/`new_flask_app`. They match — explain why using `git merge-base main new_flask_app`, then say what changes if `main` gains one commit.
3. **Judge two diffs.** Compare `git show --stat 5b9d1601` with `git show --stat 42a2ecc4 | tail -1`. Which is riskier, and why is it not the bigger one?

# Homework
- Fill in `.github/pull_request_template.md` honestly for commit `5b9d1601` as if it were a PR. Which boxes can you tick with evidence, and which must be N/A?
- `CONTRIBUTING.md` §10 forbids merging your own unreviewed money change. Write exactly what you would put in the PR when you are the only person available.
- The UTC settlement-date bug lived at `adda_settlement_service.py:438,448` with green tests. Write the one review question that catches it, in under fifteen words.

---

# Further Reading & Live Resources
- Git docs — `git diff` (two-dot vs three-dot, `--stat`, `--numstat`, `-w`): https://git-scm.com/docs/git-diff
- Git docs — `git range-diff` (re-reviewing a rebased series): https://git-scm.com/docs/git-range-diff
- Google — *Code Review Developer Guide*, the standard most companies copy: https://google.github.io/eng-practices/review/
- Conventional Comments — the `nit:` / `blocking:` labelling scheme: https://conventionalcomments.org/
