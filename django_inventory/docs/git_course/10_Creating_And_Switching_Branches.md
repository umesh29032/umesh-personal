---
id: git-course-10-creating-and-switching-branches
type: lesson
status: active
owner: handwritten
scope: git, version control — creating, switching, tracking, renaming and deleting branches safely
anchors: CONTRIBUTING.md, git-hooks/pre-push, git-hooks/install.sh, .git/refs/heads/new_flask_app, .git/packed-refs
verified: 2026-08-03
---

# 10 — Creating & Switching Branches (writing a 41-byte file, and everything that moves with it)

> Part of [Git Course](00_COURSE_OVERVIEW.md). Prev: [09 — What a Branch Really Is](09_What_A_Branch_Really_Is.md). Next: [11 — Merging](11_Merging.md).

# Learning Objectives
By the end of this chapter you can:
- create a branch from any start point (branch, tag, remote branch, raw commit) and say what git wrote to disk
- explain what a switch does to the three trees, and why some uncommitted edits survive it while others are refused
- set and read a branch's **upstream**, and read `ahead`/`behind` correctly
- recognise **detached HEAD** and escape it without losing a commit
- delete, rename and *recover* branches — including one you deleted with `-D`

# Purpose
[Ch 09](09_What_A_Branch_Really_Is.md) established *what* a branch is: a movable name pointing at one commit. This chapter is the verb — how you make one, how you move between them, and what happens to your uncommitted work in the half-second a switch takes. Nearly every "git ate my work" story is really a switching story, so this is where the safety habits get installed.

# The Problem
You are three hours into a feature. Half-finished edits in eight files, nothing committed. The owner messages: *the settlement page is 500-ing, fix it now.*

Without branches you have two bad options: throw the three hours away, or ship the half-finished feature alongside the hotfix. With branches you park the work under a name, switch to a clean `main`, fix, ship, and return to eight files exactly as you left them.

The trap is the sharp edges. `git switch` sometimes **carries** your uncommitted edits along, and sometimes **refuses to move**. `git branch -D` deletes a name whose commits nobody else has. `git checkout <sha>` drops you somewhere that looks like a branch, accepts commits, then loses them. None of it is a bug — it is all obvious once you know a branch is a 41-byte file and HEAD is a one-line pointer.

# Theory (from zero)

### A branch is a 41-byte file; HEAD is one line

A **branch** is a file whose entire content is the 40-character hexadecimal ID of one commit plus a newline — 41 bytes. `git branch feat/x` resolves the start point to a commit ID (default: whatever `HEAD` points at) and writes it into `.git/refs/heads/feat/x`. That is all: no files copied, nothing in your working tree changed. Branching is **O(1)** — the same cost with 5 files or the 2,407 this repo tracks, which is why git branches for everything while SVN and Perforce treated a branch as an expensive server-side copy people avoided. (A **commit ID** — SHA, hash, object name — is the fingerprint of a commit's content, [Ch 05](05_How_Git_Stores_Everything.md).)

`.git/HEAD` also holds one line, normally a **symbolic ref** — not a commit ID but the *name of a branch*: `ref: refs/heads/new_flask_app`. That indirection is the design: when you commit, git writes the commit then updates whatever branch HEAD names, so *the branch follows you*. Two pointers, two jobs — **HEAD** = which branch am I on; **the branch file** = which commit is that branch at.

### `git switch` vs `git checkout` — the confusing bit, named

`git checkout` does two unrelated jobs: move between commits, **and** overwrite files from a commit. That overload has destroyed real work — `git checkout .` silently discards edits, while `git checkout main` is harmless. Git 2.23 (2019) split it: **`git switch`** moves HEAD (replacing `git checkout <branch>`), **`git restore`** overwrites files (replacing `git checkout -- <path>`). Use those two; learn to *read* `checkout`, because every old tutorial uses it. This repo's git is **2.34.1**, so both exist.

```bash
git switch -c feat/accountant-read-tier     # create + switch (modern)
git checkout -b feat/accountant-read-tier   # same thing (old form)
git branch feat/accountant-read-tier        # create WITHOUT switching
```

### What a switch does to the three trees

From [Ch 03](03_The_Three_Trees.md): **HEAD** (last commit), the **index** (staging area), the **working tree** (files on disk). A switch diffs the current commit's tree against the target's, rewrites **only the files that differ** on disk and in the index, then rewrites `.git/HEAD`. It applies a diff — it does not re-extract the project. Hence: fast, and **untracked** files are never touched.

Git allows a switch when your edits collide with nothing that must change:

```
$ git switch main
M  django_inventory/config/expense/services/adda_settlement_service.py
Switched to branch 'main'
```

Your edit came along — useful when you started on the wrong branch (`git switch -c feat/right-name` carries it over), dangerous because it is easy to assume a switch "resets" you and then commit onto the wrong branch. If a file you edited *must* change, git refuses and stays put:

```
error: Your local changes to the following files would be overwritten by checkout:
        django_inventory/config/production/services/pool_service.py
Please commit your changes or stash them before you switch branches.
```

Three honest answers: commit, `git stash` ([Ch 17](17_Stash_And_Worktrees.md)), or `git switch -m` to three-way-merge your edits into the destination (can produce conflict markers — [Ch 12](12_Merge_Conflicts.md)). Do **not** reach for `--force`: it discards those edits, and no reflog can restore a change that was never committed.

> 💡 **Samjho aise:** Branch banana matlab naya register kholna **nahi** hai — sirf ek parchi pe likhna: *"kaam yahaan se shuru"*. `HEAD` woh ungli hai jo kehti hai *"main is parchi pe hoon"*. Switch karne pe git poora ghar nahi badalta — sirf woh saaman badalta hai jo dono kamron mein **alag** hai. Aur jo saaman register mein likha hi nahi (untracked), woh jahan tha wahin pada rehta hai.

### Start points, and upstream

The second argument is the **start point** — anything naming a commit:

```bash
git switch -c fix/utc-date origin/main    # from the remote's main — usually the right choice
git switch -c hotfix/base erp-v1.0.0      # from a release tag: patch what actually shipped
git switch -c rescue/work 42a2ecc4        # from a raw commit ID (or HEAD~3)
```

Branching off your **local** `main` gives you whatever your last fetch left there — here, local `main` is **296 commits behind**. Fetch first, then branch off `origin/main` ([Ch 19](19_Push_Fetch_Pull.md)).

A branch can also record which remote branch it corresponds to: its **upstream**, in `.git/config` as `[branch "x"] remote = origin` / `merge = refs/heads/x`. Set it on the first push with `git push -u origin feat/x`; then bare `push`/`pull` know where to go, `@{u}` is shorthand, and `git branch -vv` prints counts. **`ahead 1` = I have one commit the remote does not** — computed against your **last-fetched** copy, so without a fresh fetch "up to date" only means "up to date with what I knew this morning" ([Ch 18](18_Remotes.md)).

### Detached HEAD — not broken, just unnamed

`git switch --detach <commit>` (or plain `git checkout <commit>`) puts a raw commit ID in `.git/HEAD` instead of `ref: refs/heads/…`. You are on a commit, not a branch. Everything works — build, test, even commit — but new commits move *nothing*, because there is no branch name to update. Leave, and they are unreachable, alive only in the reflog ([Ch 16](16_Reflog.md)) until garbage collection.

```bash
git switch -                     # leave (nothing committed = nothing risked)
git switch -c rescue/experiment  # KEEP commits made here by giving them a name
```

It is genuinely useful — inspecting a tag, and `git bisect` ([Ch 35](35_Bisect.md)) lives in it. It is only a trap if you commit and walk away.

### Deleting, renaming, and the undo for both

```bash
git branch -d feat/done              # safe: REFUSES if not merged
git branch -D feat/scrapped          # force
git branch -m old-name new-name      # rename
git push origin --delete feat/done   # delete it on the remote too
```

`-d` checks the commits are reachable from the upstream or HEAD, else `error: the branch 'feat/x' is not fully merged`. **The undo for `-D`:** it deleted *the 41-byte file*, never the commits — `git reflog` for the tip SHA, then `git branch feat/x <sha>`. Two edges: you cannot delete the branch you are standing on, and because refs are files in directories you cannot have both `feat` and `feat/login` (`cannot lock ref`).

### Naming — this project's rule, and why

`CONTRIBUTING.md` §3: `<type>/<short-kebab-description>`, lowercase, hyphens not underscores, no ticket numbers, one branch = one intent, short-lived. The prefixes are deliberately the **same vocabulary as Conventional Commits** ([Ch 25](25_Conventional_Commits.md)) — `feat/ fix/ chore/ docs/ refactor/ test/ perf/` — so branch name and commit type agree. "Short-lived" is not aesthetics: a three-week branch is a merge conflict with a countdown timer.

# Real World Example (this repo)

All read-only, real output:

```
$ git branch -vv
  main          7c256f50 add a js of billing
* new_flask_app 42a2ecc4 [origin/new_flask_app: ahead 1] chore(repo): stop tracking database dumps + node_modules; teach why in the course

$ git symbolic-ref HEAD
refs/heads/new_flask_app

$ wc -c .git/refs/heads/new_flask_app
41 .git/refs/heads/new_flask_app

$ ls .git/refs/heads/
new_flask_app
```

Measured: **41 bytes** — 40 hex characters plus a newline. That file *is* the branch. And `main` has no file at all; it lives only in the packed store, `.git/packed-refs`:

```
7c256f50f2773d7f8e02d3762a1dd43d19386a3c refs/heads/main
494040011426eeb5b53d92836af178e9500d2b8b refs/heads/new_flask_app
```

Refs come in two forms: **loose** (one file each) and **packed** (all in one file, written by `git gc`). Note `new_flask_app` appears in both **with different values** — `4940400…` packed, `42a2ecc4` loose. The loose file always wins; the packed entry is a stale leftover. That is exactly why you read refs with `git rev-parse` / `git for-each-ref`, never by `cat`-ing a path that may not exist.

**The honest part.** The branch this ERP was built on is `new_flask_app`: underscores, no prefix, describing a Flask app in a Django repo, and long-lived — `git rev-list --left-right --count main...new_flask_app` reports `0  296`. It breaks §3 on every count and predates the rulebook; the rule exists *because* of it. Fifteen merged PRs all read `Merge pull request #N from umesh29032/new_flask_app`, so `main`'s history cannot say what any of them were *for* — the cost of a bad branch name, paid fifteen times.

# Visual Diagram
```
  git switch -c feat/rate-fix   →   one new 41-byte file + one rewritten line

  BEFORE                            AFTER
  HEAD = "ref: …/new_flask_app"     HEAD = "ref: …/feat/rate-fix"
  C1─C2─C3─C4 ◄ new_flask_app       C1─C2─C3─C4 ◄ new_flask_app, main, feat/rate-fix
              ◄ main (packed)                     (three names, ONE commit)
  nothing on disk changed           nothing on disk changed

  DETACHED HEAD:  git switch --detach C2   →   HEAD = "c2c2c2c2…" (raw SHA)

  C1─C2─C3─C4 ◄ new_flask_app
      └─ C5*   commit here → NOTHING moves. Leave → reflog-only.
               Escape: git switch -c rescue/x    (keeps C5)

  git branch -D feat/x deletes 41 BYTES; the commits stay in .git.
  Undo:  git reflog  →  git branch feat/x <sha>
```

# Practical — create, switch, track, delete, recover

```bash
git switch main && git fetch origin                    # refresh the tracking cache FIRST
git switch -c feat/accountant-read-tier origin/main
```
Expected:
```
branch 'feat/accountant-read-tier' set up to track 'origin/main'.
Switched to a new branch 'feat/accountant-read-tier'
```
```bash
git branch -vv                                  # where am I, what tracks what
git push -u origin feat/accountant-read-tier    # publish AND set upstream (once per branch)
```
Prove the carried-edits behaviour on a file you are happy to lose, then undo it:
```bash
echo "" >> django_inventory/README.md
git switch main                            # watch for the " M …/README.md" line
git restore django_inventory/README.md     # the undo, in the same breath
```
Land it, clean up, recover:
```bash
git merge --ff-only origin/main             # sync the trunk, refusing a merge commit
git branch -d feat/accountant-read-tier     # safe delete (refuses if unmerged)
git push origin --delete feat/accountant-read-tier
git reflog                                  # after any -D: find the tip SHA…
git branch feat/oops <sha>                  # …name restored, same commit
```
**Shown, deliberately not run** — the two switching commands with no undo:
```bash
git switch --force main    # discards local modifications to reach main
git checkout .             # overwrites every tracked file from the index
```
The reflog remembers **commits**; an edit never committed has no entry anywhere. `git stash` first — one second turns "gone" into "gone but retrievable".

# Production Walkthrough
1. **Sync the trunk.** `git fetch upstream && git switch main && git merge --ff-only upstream/main`. `--ff-only` *refuses* a merge commit; if it fails, your `main` has drifted and should be reset to upstream, keeping `main` a clean mirror ([Ch 11](11_Merging.md)).
2. **Branch with intent.** `git switch -c fix/utc-date-in-settlement` — one intent, because the PR must be reviewable and revertible as one unit.
3. **Work and publish.** `git-hooks/commit-msg` rejects non-Conventional messages; `git push -u origin fix/…` is allowed while `git push origin main` is **blocked** by `git-hooks/pre-push` ([Ch 27](27_Pre_Push_Protection.md)).
4. **PR → CI green → review → squash-merge → delete the branch**, remotely *and* locally ([Ch 21](21_Pull_Requests.md)). Dead names make `git branch` unreadable, and an unreadable branch list is how you build on stale work.

Interruption case — hotfix mid-feature:
```bash
git stash push -m "wip: roster picker"
git switch main && git fetch origin && git merge --ff-only origin/main
git switch -c fix/settlement-500                  # fix, commit, push, PR
git switch feat/roster-picker && git stash pop    # exactly where you left off
```

# Debugging Guide

| Symptom | Cause | Fix |
|---|---|---|
| `Your local changes … would be overwritten by checkout` | A file you edited must change to complete the switch | `git stash`, or commit, or `git switch -m` |
| `'feat/x' is not a commit and a branch cannot be created from it` | Start point does not resolve — usually an unfetched remote branch | `git fetch origin`, then `git switch -c feat/x origin/feat/x` |
| `You are in 'detached HEAD' state` | You switched to a commit or tag, not a branch | `git switch -` to leave, `git switch -c name` to keep commits |
| `the branch 'feat/x' is not fully merged` | `-d` protecting unmerged commits | Confirm it is disposable, then `-D` |
| `Cannot delete branch 'feat/x' checked out at …` | You are standing on it | `git switch main`, then delete |
| No `[origin/…]` in `git branch -vv` | No upstream set | `git push -u origin <branch>` |
| Says `ahead 3`, GitHub shows more | Ahead/behind compares against your **last fetch** | `git fetch origin`, re-read |
| Commits vanished after leaving detached HEAD | No branch was moved, so nothing referenced them | `git reflog`, then `git branch rescue <sha>` |

# Performance Notes
- **Creating a branch is O(1)** — one 41-byte write, independent of the 2,407 tracked files.
- **Switching costs the diff, not the repo.** Neighbouring commits are instant; `main` ↔ `new_flask_app` (296 commits apart) rewrites a large slice of the tree.
- Measured here: `git status --porcelain` **0.02 s**, `git branch --list` **0.00 s**, `.git` **97 MB** (`git count-objects -vH`: 25,975 in-pack objects, 63.66 MiB of packs). Branch operations are not where git gets slow — [Ch 37](37_Large_Files_And_Performance.md) is.
- The real cost of a switch in a Django project is downstream: `__pycache__` invalidation, dev-server reload, a `pip install` when branches disagree about dependencies. Switching all day? `git worktree add` gives a second directory on a second branch sharing one `.git` ([Ch 17](17_Stash_And_Worktrees.md)).

# Security Considerations
- **Hooks are not cloned.** `.git/hooks/` never comes with a clone — a deliberate git decision, otherwise `git clone` would execute a stranger's code. So a fresh clone has **no** `pre-push` protection until someone runs `bash git-hooks/install.sh`. `CONTRIBUTING.md` §2 writes that gap into a table row rather than hiding it; it is why installing hooks is onboarding step 1.
- **Branch names are public metadata** — they land in PR titles, CI logs and notification emails. `fix/acme-refuses-to-pay` publishes something you may not have meant to. Describe the change, not the customer.
- **Deleting a branch does not delete its commits.** They live in `.git` and the reflog for months, and in any clone that fetched them. A secret committed on a scrapped branch is leaked — rotate it ([Ch 33](33_Secrets_And_Leaks.md)).
- **Checking out an untrusted branch is not neutral.** The checkout runs nothing, but the files it lays down include `.pre-commit-config.yaml` and `.github/workflows/*` that your *next* command may execute. Read a fork's `.github/` diff before running its tests locally.
- **Never `--force` a switch to escape a warning** — the one branch operation with no undo, because uncommitted work has no object in the database and so no reflog entry.

# Architecture Decisions
- **Trunk-based: `main` + short branches + tags.** `git-flow` (permanent `develop`, `release/*`, `hotfix/*`) is explicitly rejected in `CONTRIBUTING.md` §10 as heavier than a 1–2 person team can justify ([Ch 24](24_Branching_Strategies.md)).
- **Branch prefixes mirror Conventional Commit types**, so branch name and commit type never disagree and squashed `main` history reads as a list of features.
- **No ticket numbers in branch names** — this project has no tracker, and a convention pointing at something non-existent decays into noise.
- **`--ff-only` for syncing `main`**, so a drifted local `main` fails *loudly* instead of silently growing a merge commit. `main` is a mirror, not a workplace.
- **Collaborators branch inside their own fork** (§2 layer 2): with Read access there is no push permission at all, so accidental pushes to shared branches are structurally impossible — free, server-side, and stronger than the paid branch-protection feature this project deliberately does not buy.
- **Rejected: a hook enforcing branch names.** `commit-msg` already enforces the vocabulary where it matters (the commit that lands); a second guardrail on the *name* would mostly annoy the one person it applies to.

# Best Practices
- Branch off a **freshly fetched `origin/main`**, never off whatever your local `main` happens to be.
- One branch, one intent. If the description needs an "and", make it two branches.
- `git push -u` on the first push, always — one flag buys working bare `push`/`pull` forever.
- Name to `CONTRIBUTING.md` §3, lowercase kebab-case; delete merged branches the same day.
- Read `git status -sb` before *and* after a switch; `git stash` before any risky one.

# Beginner Mistakes
- **`git branch feat/x` then committing** → you created the name but never switched, so the commit lands on the old branch. Use `git switch -c`.
- **Assuming a switch discards your edits** → git often carries them over, and you commit a half-finished feature onto `main`. Read the ` M …` lines the switch prints.
- **`git switch --force` to get past a warning** → uncommitted work destroyed, no reflog entry, no recovery. Stash instead.
- **Committing in detached HEAD, then switching away** → the commits belong to no branch. Name them *before* leaving: `git switch -c rescue/x`.
- **Branching off a stale local `main`** → you build on 296-commit-old code and inherit conflicts that were never yours. Fetch, then branch off `origin/main`.
- **`git branch -D` as a habit** → it skips the "not fully merged" check that exists for exactly the branch you are about to regret. Use `-d` and let it argue.
- **Deleting locally and assuming the remote branch is gone** → `git push origin --delete <branch>`.
- **Trusting `ahead`/`behind` without fetching** → those numbers compare you to a local cache, not to GitHub.
- **Underscores, capitals or spaces in names** → underscores fight the convention, capitals collide on case-insensitive filesystems, spaces fail. Check with `git check-ref-format --branch`.

# Interview Questions
- **Junior:** "What is the difference between `git branch feat/x` and `git switch -c feat/x`?" — Both create the branch, which means writing one 41-byte file containing a commit ID. Only `git switch -c` also moves `HEAD` to it, so with `git branch` alone your next commit still lands on the branch you were already on.

- **Mid:** "I have uncommitted changes and I run `git switch other`. What happens?" — Git diffs the two commits' trees. If none of the files you edited need to change, it carries your edits over and prints them as ` M path`. If one does, it refuses with "your local changes would be overwritten" and aborts, leaving you where you were. Then: commit, `git stash`, or `git switch -m` to three-way-merge the edits in. Never `--force` — uncommitted work has no object in the database, so the reflog cannot recover it.

- **Senior:** "Explain detached HEAD, when you'd want it, and how to recover work from it." — `.git/HEAD` normally holds `ref: refs/heads/<branch>`, a symbolic ref; detached means it holds a raw commit ID. Commits still succeed but move no branch, so on leaving they are unreachable — alive in the object database and reflog until `gc` prunes them. It is the right state for inspecting a tag, and `git bisect` uses it by design. Recovery: `git reflog` for the SHA, then `git branch rescue <sha>`. Prevention: `git switch -c <name>` before committing.

- **Staff:** "Enforce branch hygiene across a team on GitHub's free tier, on private repos." — Accept up front that server-side branch protection and CODEOWNERS auto-assignment are paid on private repos, then compose free layers. (1) A committed `pre-push` hook refusing `main`, plus an installer — and write down its real limit: `.git/hooks` is not cloned, so it binds only where installed. (2) Give collaborators **Read** access and have them work from forks; with no push permission at all, "cannot push to main" is enforced server-side for free, and it is stronger than branch protection, which grants push and merely restricts the target. (3) CI on every PR as the visible merge gate, with `concurrency` cancellation and `paths` filters to respect the ~2,000 free minutes. Then make the convention cheap to follow — prefixes matching commit types, `push -u` in the documented loop, same-day deletion, branches living days not weeks — because divergence, not naming, is what costs money at merge time.

### Why interviewers ask these — and the answer that separates levels

| Testing for | Weak answer | What lands |
|---|---|---|
| Do you know a branch is a pointer, not a copy? | "A branch is a copy of the code you work on." | "A 41-byte file under `refs/heads/` holding one commit ID. Creating it is O(1) and touches no working file; HEAD separately says which one I am on." |
| Have you been burned by switching with dirty state? | "Git saves my changes when I switch." | "Git carries edits over only if they do not collide; otherwise it refuses and aborts. Stash or commit — never `--force`, because uncommitted work has no reflog entry." |
| Do you understand detached HEAD instead of fearing it? | "Detached HEAD means the repo is broken." | "HEAD holds a raw SHA instead of a branch ref. Commits there move nothing and go unreachable when you leave; `git switch -c name` keeps them, reflog rescues them." |

**The killer follow-up:** *"You force-deleted a branch with two unpushed commits. Get them back."* — `git reflog` (or `git fsck --lost-found`) for the tip SHA, then `git branch <name> <sha>`; `-D` deleted a 41-byte file, never the commits. Anyone who answers "they're gone" has never needed the reflog — and will tell a teammate to redo a day's work.

# Revision Notes
- A branch is a **41-byte file** in `.git/refs/heads/`; creating one is O(1) and changes nothing on disk.
- **HEAD** = which branch you are on; **the branch file** = which commit that branch is at.
- `git switch` moves HEAD, `git restore` overwrites files — `git checkout` was both, which is why Git 2.23 split it.
- A switch rewrites **only differing files**; untracked files are never touched. Edits are **carried** if they do not collide, **refused** if they do; `--force` destroys them with no undo.
- **Detached HEAD** = a raw SHA in `.git/HEAD`; commits there move no branch. Escape with `git switch -c <name>`.
- `-d` refuses unmerged, `-D` forces — either way the commits survive: `git reflog` + `git branch <name> <sha>`.
- Refs are **loose files** or entries in `.git/packed-refs`; loose wins. Read with `git rev-parse`, not `cat`.
- Ahead/behind is measured against your **last fetch**, not against GitHub.

# Cheat Sheet
- **Create + switch:** `git switch -c feat/x` · from a start point: `git switch -c fix/y origin/main` · name only: `git branch feat/x`
- **Move:** `git switch main` · previous branch: `git switch -` · detach: `git switch --detach <sha>`
- **Look:** `git branch -vv` · `git status -sb` · `git for-each-ref refs/heads` · `git symbolic-ref HEAD`
- **Upstream:** `git push -u origin feat/x` · later: `git branch -u origin/feat/x` · shorthand `@{u}`
- **Rename / delete:** `git branch -m old new` · `git branch -d feat/x` (safe) / `-D` (force) · `git push origin --delete feat/x`
- **Sync the trunk:** `git fetch origin && git switch main && git merge --ff-only origin/main`
- **Dirty tree, must switch:** `git stash push -m "wip"` → switch → `git stash pop`
- **Undo a delete:** `git reflog` → `git branch feat/x <sha>` · **undo a bad switch:** `git switch -`
- ⚠️ **No undo for** `git switch --force` or `git checkout .` — they discard uncommitted work. Stash first.

# My ERP Section

| Concept | In this repo |
|---|---|
| Git root | `/home/tech/umesh-personal` (monorepo; the ERP is `django_inventory/`) |
| Default branch | `main` — `7c256f50`, currently **296 commits behind** the remote |
| Working branch | `new_flask_app` — `42a2ecc4`, `[origin/new_flask_app: ahead 1]` |
| The branch file | `.git/refs/heads/new_flask_app`, **41 bytes** |
| Packed refs | `main` exists only in `.git/packed-refs`; `new_flask_app` has a stale packed entry (`4940400…`) plus a live loose file |
| Naming rule | `CONTRIBUTING.md` §3 — `feat/ fix/ chore/ docs/ refactor/ test/ perf/`, lowercase kebab-case |
| Violation on record | `new_flask_app`: underscores, no prefix, 296 commits long-lived, 15 merge commits named after it |
| Push protection | `git-hooks/pre-push` refuses `main`/`master`; installed per clone by `bash git-hooks/install.sh` |
| Tags to branch from | `erp-v1.0.0`, `kos-v1.0`, `pre-refactor-baseline` |

# Practice Tasks
1. **Prove the 41 bytes.** `git symbolic-ref HEAD`, then `wc -c .git/refs/heads/<that branch>`. Explain the number without using the word "copy".
2. **Find the stale ref.** Compare `head -4 .git/packed-refs` with `git rev-parse new_flask_app`. Which wins — and which command should you have used all along?
3. **Branch from a tag.** `git switch -c study/v1-baseline erp-v1.0.0`, confirm with `git log --oneline -1`, then `git switch -` and `git branch -d study/v1-baseline`.
4. **Feel the detach.** `git switch --detach HEAD~2`, read the warning in full, `git status -sb`, then `git switch -`.
5. **Recover from `-D`.** Create `chore/throwaway`, commit once, `git switch -`, `git branch -D chore/throwaway` — then bring it back from `git reflog`.
6. **Break it on purpose.** `git switch -c feat`, then `git switch -c feat/login`. Explain the error in terms of files and directories.

# Homework
- Read `CONTRIBUTING.md` §3 and §9. Rewrite `new_flask_app`'s name as it *should* have been, and justify each character.
- Run `git branch -vv`, state each branch's upstream, then `git fetch origin` and see whether any number changed — and what that says about the numbers you trusted before.
- Read `git-hooks/install.sh`. Why can git not do this at clone time? Answer in terms of what a hook may execute.
- 296 commits of divergence: name three concrete costs this project pays at merge time, and one thing that would have prevented it.

---

# Further Reading & Live Resources
- `git switch` — official reference (`-c`, `-`, `--detach`, `-m`): https://git-scm.com/docs/git-switch
- `git branch` — official reference (`-vv`, `-d` vs `-D`, `-m`, `-u`): https://git-scm.com/docs/git-branch
- Pro Git, *Branching in a Nutshell* — the canonical explanation, free and short: https://git-scm.com/book/en/v2/Git-Branching-Branches-in-a-Nutshell
- Pro Git, *Git References* — loose refs, `packed-refs`, HEAD as a symbolic ref: https://git-scm.com/book/en/v2/Git-Internals-Git-References
- Git 2.23 release notes — why `switch`/`restore` were split out of `checkout`: https://github.blog/open-source/git/highlights-from-git-2-23/
