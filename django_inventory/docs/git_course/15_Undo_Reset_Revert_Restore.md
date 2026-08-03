---
id: git-course-15-undo-reset-revert-restore
type: lesson
status: active
owner: handwritten
scope: git, version control — undoing work safely; which of reset, revert, restore and clean to reach for
anchors: CONTRIBUTING.md, .gitignore, git-hooks/pre-push, django_inventory/config/learning/registry.py
verified: 2026-08-03
---

# 15 — Undo: reset vs revert vs restore (three different undos, one wrong choice loses work)

> Part of [Git Course](00_COURSE_OVERVIEW.md). Prev: [14 — Interactive Rebase](14_Interactive_Rebase.md). Next: [16 — Reflog — the time machine](16_Reflog.md).

# Learning Objectives
By the end of this chapter you can:
- name which of the three trees each of `restore`, `reset` and `revert` touches
- pick the right undo from one question: "has anyone else got this commit?"
- use `git reset --soft/--mixed/--hard` knowing exactly what each one throws away
- revert a bad commit on `main` without rewriting history, including a merge commit
- explain why `git clean -fdx` is the most dangerous command in this chapter
- state what is recoverable from the reflog and what is gone forever

# Purpose
"Undo" is not one operation in git, and that is the single biggest source of junior panic. Three commands with confusingly similar names each undo a *different layer*: `restore` fixes files, `reset` moves your branch, `revert` adds a new commit that cancels an old one. This chapter draws the boundaries hard, gives the recovery path for each, and marks the two commands that can destroy work no reflog can bring back.

# The Problem
Real, current state of this monorepo — one modified file and four untracked entries:

```bash
$ git status
On branch new_flask_app
Your branch is ahead of 'origin/new_flask_app' by 1 commit.

Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
	modified:   django_inventory/config/learning/registry.py

Untracked files:
	.github/
	CHANGELOG.md
	CONTRIBUTING.md
	git-hooks/
```

Four commands could be aimed at that output. `git restore .` throws away the 11-line edit to `registry.py`. `git reset --hard` throws away the edit **and** moves the branch. `git revert HEAD` leaves everything alone and writes a new commit. `git clean -fd` deletes `.github/`, `CHANGELOG.md`, `CONTRIBUTING.md` and `git-hooks/` — the entire workflow system, never committed, therefore **not in the reflog and not recoverable**.

Same-looking commands; one of them is a disaster. That is why this chapter exists.

# Theory (from zero)

### The three trees (one-paragraph recap)
Git keeps your work in three places at once ([Ch 03](03_The_Three_Trees.md)): the **working tree** (the real files on disk you edit), the **index** a.k.a. *staging area* (a snapshot you have marked as "goes in the next commit", built by `git add`), and **HEAD** (the commit your current branch points at — the last saved snapshot). Every undo command is defined by which of those three it rewrites.

| Command | Working tree | Index | HEAD / branch | Safe on shared history |
|---|---|---|---|---|
| `git restore <path>` | ✔ overwritten | — | — | yes (only touches files) |
| `git restore --staged <path>` | — | ✔ overwritten | — | yes |
| `git reset --soft <commit>` | — | — | ✔ moved | **no** — rewrites |
| `git reset --mixed <commit>` (default) | — | ✔ reset | ✔ moved | **no** |
| `git reset --hard <commit>` | ✔ **destroyed** | ✔ reset | ✔ moved | **no** |
| `git revert <commit>` | ✔ (via a new commit) | ✔ | ✔ **moves forward** | **yes** |
| `git clean -fd` | ✔ **untracked files deleted** | — | — | n/a — irreversible |

### `git restore` — undo at the file level
`git restore` only ever rewrites files. It never moves your branch, so it can never lose a commit.
```bash
git restore django_inventory/config/learning/registry.py   # discard MY EDITS to this file — no undo!
git restore --staged file.py            # un-stage it, keep the edit (index ← HEAD)
git restore --staged --worktree file.py # un-stage AND discard the edit
git restore --source=83a144ba -- file.py # bring this file back as it was at that commit
git restore .                            # every tracked file in the tree. Think first.
```
**The confusing bit:** until git 2.23, all of this was `git checkout`, which *also* switched branches — one command doing two unrelated jobs, which is exactly how people wiped a day's work by mistyping a branch name. Git split it: **`git switch`** changes branches, **`git restore`** changes file contents ([Ch 10](10_Creating_And_Switching_Branches.md)). Use the new names; they say what they do.

`git restore` on a modified file is the one undo in this chapter with **no recovery at all** for uncommitted edits — the old bytes were never in git. That is what `git stash` is for ([Ch 17](17_Stash_And_Worktrees.md)): a parking space instead of a bin.

### `git reset` — move the branch label
`git reset <commit>` says "my branch should point *there* instead". The mode decides how much else follows.

```
current:  A ── B ── C  (main, HEAD)      you run: git reset <mode> B

--soft    branch → B.  index and files UNCHANGED.
          → C's changes are still staged, ready to re-commit differently.
          (This is how CI's design-system ratchet re-presents a whole PR as staged.)

--mixed   branch → B.  index reset to B.  files UNCHANGED.   ← the DEFAULT
          → C's changes are in your working tree, unstaged. Nothing lost.

--hard    branch → B.  index reset.  WORKING TREE OVERWRITTEN.
          → uncommitted work is GONE. C itself is recoverable (reflog); your
            unsaved edits are not.
```
Two more shapes worth knowing:
- `git reset <path>` (a path, not a commit) does **not** move anything — it un-stages that path. The modern spelling is `git restore --staged <path>`; both survive.
- `git reset --hard ORIG_HEAD` is the standard "undo the last big operation". Git writes `ORIG_HEAD` before any merge, rebase or reset, so it is a one-word bookmark to where you just were ([Ch 16](16_Reflog.md)).

**The undo for reset:** the commits are still there. `git reflog` lists every position HEAD has held (~90 days), so `git reset --hard HEAD@{1}` walks it back. What reflog cannot restore is working-tree changes that were never committed — `--hard` is final for those.

### `git revert` — undo by moving forward
`git revert <commit>` computes the inverse of that commit's diff and **commits it**. History grows; nothing is rewritten. That is what makes it the only safe undo for anything already pushed.
```bash
git revert 42a2ecc4                # creates "Revert \"chore(repo): stop tracking…\""
git revert --no-commit 42a2ecc4    # stage the inverse, let me combine it with more work
git revert -m 1 83a144ba           # a MERGE commit has two parents — -m 1 means "keep the first
                                   #   parent's line of history, undo the branch that merged in"
git revert <the revert>            # reverting a revert re-applies the change. Perfectly legal.
```
`git-hooks/commit-msg` deliberately lets `Revert ` messages through (alongside `Merge ` and `fixup!`), so the auto-generated subject is not rejected by the Conventional-Commits gate.

### `git clean` — the one with no undo
`git clean` deletes **untracked** files. Git never had them, so nothing can bring them back.
```bash
git clean -n            # DRY RUN. Always this first. -n = --dry-run
git clean -fd           # delete untracked files (-f) and directories (-d)
git clean -fdx          # ...INCLUDING gitignored files. -x is the dangerous letter.
```
Look again at the real `git status` above: `-fd` today would delete `CONTRIBUTING.md`, `.github/`, `git-hooks/` and `CHANGELOG.md`. And `-fdx` would go further and delete **gitignored** files too — which in this project means `.env` (the secrets) and `env/` (the virtualenv), because the root `.gitignore` blocks `*.sql`, `*.dump`, `*.sql.gz`, `db_backups/`, `backups/` and `node_modules/`, and `django_inventory/.gitignore` hides local config. Type `-n` first, every single time.

### The recoverability ladder — memorise this
```
committed (even on a deleted branch)  → reflog / git fsck   ✔ recoverable ~90 days
staged but never committed            → git fsck --lost-found may find the blob  ~ maybe
edited but never staged               → GONE                �’ nothing to recover from
untracked (never added)               → GONE                ✗ clean deletes it forever
```
Git protects what you *gave* it. `git add` is not bureaucracy; it is the moment your work becomes recoverable.

### The decision rule
> **Has anyone else got this commit?** Yes → `git revert`. No → `git reset`.
> **Is it not a commit at all, just files?** → `git restore`.
> **Is it a file git has never seen?** → `git clean`, and only after `-n`.

> 💡 **Samjho aise:** Teen alag-alag undo hain, teen alag jagah. **`restore`** = copy pe likha hua **mitana** (rubber) — sirf kaagaz badalta hai. **`reset`** = register ka **bookmark peeche khiskana** — likha hua page waise hi hai, sirf "aaj yahan tak" ka nishaan hat gaya; `--hard` bola to mez pe pada kaccha kaam bhi phaad diya. **`revert`** = purani entry ke saamne **ulti entry likhna** — kuch mitaya nahi, hisaab barabar ho gaya (accountant ka tareeka; isliye `main` pe yahi chalta hai). Aur **`clean`** = jo kaagaz register mein hi nahi chadhaya, use **kachre mein daalna** — wo kabhi wapas nahi aata.

# Real World Example (this repo)
Two real undos, one tiny and one enormous.

**1. The pending edit.** There is exactly one unstaged change right now:
```bash
$ git diff --stat
 django_inventory/config/learning/registry.py | 11 +++++++++++
 1 file changed, 11 insertions(+)
```
Eleven added lines that register a course in the learning platform. `git restore django_inventory/config/learning/registry.py` would erase them with no confirmation and no reflog entry, because they were never committed. `git stash` would park them instead. Same keystroke count, completely different consequence.

**2. The 2,954-file undo that was NOT a history rewrite.** Commit `42a2ecc4` is a real, large-scale undo in this repository:
```bash
$ git show --stat 42a2ecc4 | head -4
commit 42a2ecc4dc77dafc9407f4eaf4840c3ed8bd97fa
Author: umesh-personal <umesh29mar@gmail.com>
Date:   Mon Aug  3 14:32:13 2026 +0530

    chore(repo): stop tracking database dumps + node_modules; teach why in the course
```
Two June-2025 `pg_dump` files and 2,952 `node_modules` files were tracked. The fix used `git rm --cached` — an **index-only** removal: **2,954** files untracked, **331,748** deletions in the diff, and every file still sitting on disk, byte-identical before and after. That is the `reset`/`restore` family's real superpower: change what git *tracks* without touching what you *have*.

And the deliberate non-choice: history was **not** rewritten. With 0 forks, the repo going private, and an audit showing nothing usable inside the dumps (`socialaccount_socialapp` and `socialaccount_socialtoken` both empty, no plaintext passwords, 2 hashes at `pbkdf2_sha256$1000000$…`, the primary account row an *unusable password* marker, 2 expired June-2025 sessions), a `git-filter-repo` force-push straight after a merge was judged the bigger risk. So the undo moved **forward** — the `revert` mindset — and the reasoning was written into the commit message. The root `.gitignore` now blocks `*.sql`, `*.dump`, `*.sql.gz`, `db_backups/`, `backups/` and `node_modules/`, verified blocked at 5 locations, with `git add -f` still working on purpose.

# Visual Diagram
```
        WORKING TREE            INDEX (staging)            HEAD → branch
        (files you edit)        (git add put it here)       (last commit)
             │                        │                          │
  git restore <path> ◄────────────────┤                          │   files only,
             │        (index → files) │                          │   branch untouched
  git restore --staged <path> ────────► (HEAD → index)           │
             │                        │                          │
  git reset --soft  <c>   ────────────┼──────────────────────────► moves branch ONLY
  git reset --mixed <c>   ────────────► resets index ─────────────► moves branch
  git reset --hard  <c>   ◄─ OVERWRITES files ◄── resets index ──► moves branch  ⚠
             │                        │                          │
  git revert <c>    ── writes a NEW commit whose diff is the inverse ──► branch MOVES FORWARD
             │                                                          (nothing rewritten ✔ safe when shared)
  git clean -fd     ── deletes UNTRACKED files. -x also deletes gitignored (.env, env/). ✗ NO UNDO

  RECOVERY:  committed → git reflog → git reset --hard HEAD@{n}   (~90 days)
             last big op → git reset --hard ORIG_HEAD
             uncommitted edits → nothing. Use git stash instead of git restore.
```

# Practical — the safe drills
Read-only first. None of these change anything:
```bash
git status                  # which tree is each change sitting in
git diff                    # working tree vs index  (what restore would discard)
git diff --staged           # index vs HEAD          (what reset --mixed would unstage)
git clean -n                # exactly which files -fd would delete. NEVER skip this
git reflog -10              # every position HEAD has held — your undo history
```
Reversible undos:
```bash
git restore --staged django_inventory/config/learning/registry.py   # unstage, keep the edit
git reset --soft HEAD~1     # un-commit the last commit, keep everything staged
git reset HEAD~1            # un-commit, keep changes as unstaged edits (mixed, the default)
git revert 42a2ecc4         # add an inverse commit — nothing rewritten
```
Destructive — shown, not run. Each line loses something:
```bash
git restore .               # ⚠ discards EVERY uncommitted edit. No reflog, no recovery.
git reset --hard HEAD~1     # ⚠ drops the commit AND your uncommitted work
git clean -fd               # ⚠ deletes untracked files (here: CONTRIBUTING.md, .github/, git-hooks/)
git clean -fdx              # ⚠⚠ also deletes gitignored files — .env, env/. Rebuild-from-scratch territory
```
The recovery drill, which is the only way to stop fearing all of the above:
```bash
git switch -c practice/undo && echo x > f.txt && git add f.txt && git commit -m "test: scratch commit"
git reset --hard HEAD~1     # the commit is now unreferenced
git reflog -3               # find it: <hash> HEAD@{1}: commit: test: scratch commit
git reset --hard HEAD@{1}   # it is back. Nothing was ever deleted.
```

# Production Walkthrough
A bad commit is on `main`. Here is the whole path under this project's rules:

1. **Do not reset `main`.** `main` is pushed and shared, so rewriting it breaks every clone — and `git-hooks/pre-push` refuses to push `main` at all (tested: `main` BLOCKED, `master` BLOCKED, `feat/my-thing` ALLOWED).
2. **Revert on a branch:** `git switch -c fix/revert-bad-thing && git revert <sha>`. Because PRs are **squash-merged** (`CONTRIBUTING.md` §5), one feature is one commit on `main`, so a single `git revert <sha>` is a complete, reviewable feature rollback. That property is the reason for the squash rule.
3. **Open a PR for the revert.** Same gate as any change: CI runs `lint` · `migrations` · `test` (2033 tests, ~424 s) · `docs`. A revert can break things too — a later migration may depend on the reverted model change, which is exactly what the `migrations` job catches.
4. **Then fix forward.** The revert buys a green `main`; the real fix arrives as its own commit, and reverting the revert is a legitimate way to bring the work back once it is right.
5. **Never "undo" money by editing rows.** Settlement is the only money-write boundary in this ERP; a wrong ledger entry is corrected through the documented reversal path in the service layer, never with a database edit and never by rewriting git history. Git undoes *code*, not *facts* — the project's data principle is immutable, append-only history for work that happened.

# Debugging Guide
| Symptom | Cause | Fix |
|---|---|---|
| "I lost my last commit" | `reset --hard` moved the branch | `git reflog` → `git reset --hard HEAD@{n}`, or `git reset --hard ORIG_HEAD` |
| "I lost my uncommitted edits" | `restore`/`reset --hard` overwrote the working tree | nothing in git can help; check editor local history. Next time `git stash` |
| Deleted files are back after `git clean` | they were **tracked** — `clean` only touches untracked | `git restore <path>` brings tracked files back from HEAD |
| `git revert` says "commit is a merge" | a merge has two parents; git will not guess | `git revert -m 1 <sha>` (keep the first parent's line) |
| Revert produced a conflict | later commits changed the same lines | resolve, `git add`, `git revert --continue`; or `git revert --abort` |
| `git reset <path>` did not move my branch | with a path, `reset` only un-stages | that is correct — use `git restore --staged <path>` for clarity |
| Untracked file reappears in `git status` after a commit | it is not gitignored | add the pattern to `.gitignore`; `git rm --cached` if it was tracked |
| `git revert` on a squashed PR undid everything | that is the design — one squashed commit = one whole feature | revert only what you meant to; re-apply the good parts as a new commit |

# Performance Notes
- `git reset --hard` and `git restore .` rewrite the working tree for every affected file. This repo tracks **2,407** files (`git ls-files | wc -l`), so a full-tree reset is thousands of writes — seconds on SSD, painfully slow over a network mount.
- `git revert` of a huge commit is a huge diff: reverting `42a2ecc4` means re-adding **331,748** lines. Fast for git, brutal for a code review.
- `git clean -fdx` on a Django repo also deletes `env/` and any `node_modules/` — cheap to run, expensive to recover (`pip install -r requirements.txt` and a fresh `npm install`).
- `git status` slows down as untracked directories grow, which is why `node_modules/` in `.gitignore` is a performance fix as well as a hygiene one ([Ch 07](07_Gitignore.md)).
- Undo commands only rewrite refs and files; the objects stay. `.git` here is **97 MB** and reset/revert cycles do not shrink it ([Ch 37](37_Large_Files_And_Performance.md)).

# Security Considerations
- **`git clean -fdx` deletes gitignored files, which is where the secrets live.** `.env` holds the DB credentials and (in the deploy stack) the backup encryption password; it is gitignored, so `-x` sweeps it away with no copy anywhere. That is why `.env` belongs in a password manager, not only on disk.
- **`git revert` does not remove data from history.** Reverting a commit that leaked a key leaves the key fully readable in the original commit. Removal means rewriting history *and* rotating the credential ([Ch 33](33_Secrets_And_Leaks.md), [Ch 34](34_Rewriting_History.md)).
- **`git rm --cached` un-tracks without deleting** — right for stopping a leak going forward (commit `42a2ecc4`), wrong if you believe the file must vanish from history. Know which problem you are solving.
- **`reset --hard` can silently un-fix a vulnerability** by discarding an uncommitted patch. Commit security work immediately, even to a scratch branch, so it is inside the reflog's protection.
- **Reverting on `main` still needs a review.** A revert is a code change with its own blast radius; `CONTRIBUTING.md` §5's review standard (money paths, permissions, tests, docs, mobile) applies to it exactly as to the change it undoes.

# Architecture Decisions
- **Squash-merge so that revert is trivial** (`CONTRIBUTING.md` §5). One commit per feature on `main` means the rollback command is `git revert <sha>` — no hunting for a range, no partial undo.
- **Chose `git rm --cached` over a history rewrite** for the tracked-dumps incident (`42a2ecc4`): forward motion, files kept on disk, 0 forks, nothing usable inside, decision recorded in the commit message. Rejected `git-filter-repo` + force-push as more risk than the exposure.
- **Prevention over undo:** the root `.gitignore` now blocks `*.sql`, `*.dump`, `*.sql.gz`, `db_backups/`, `backups/`, `node_modules/` — verified blocked at 5 locations, while `git add -f` still works deliberately for the rare intentional case. The earlier rule existed at `django_inventory/.gitignore:114` but a `.gitignore` only guards its own subtree, and this is a monorepo: the rule was right, the scope was too narrow.
- **`revert` over `reset` on anything shared** (§10, which also bans plain `--force`). Client-side, `git-hooks/pre-push` makes the safe path the only path by refusing `main`.
- **Money is never undone with git.** Settlement is the only money-write boundary; corrections go through the service layer's documented reversal, and work that happened stays as immutable append-only history.

# Best Practices
- Run `git status` before *and* after any undo. It is the cheapest habit in this course.
- `git clean -n` before `git clean -f`, always. No exceptions, no "I know what's there".
- Prefer `git stash` over `git restore` when you might want the change back ([Ch 17](17_Stash_And_Worktrees.md)).
- `git add` early — staging is what makes work recoverable.
- On shared history use `revert`; keep `reset` for local-only commits.
- Learn `git reset --hard ORIG_HEAD` as the standard "undo that last operation".
- Use the modern names: `git switch` for branches, `git restore` for files.
- Commit before any risky operation, even a throwaway `wip` commit you will squash later ([Ch 14](14_Interactive_Rebase.md)).

# Beginner Mistakes
- **`git reset --hard` to "clean up"** → your uncommitted work is gone with no reflog entry. Commit or stash first.
- **`git clean -fdx` to fix a weird state** → deletes `.env` and `env/`. Run `-n` first and read the list.
- **Using `reset` on a pushed branch** → history diverges for everyone. `revert` is the shared-history undo.
- **Thinking `revert` deletes the bad commit** → it adds an inverse commit; the original stays visible, which is the point.
- **`git revert` on a merge without `-m`** → git refuses because it cannot guess the mainline. `-m 1` keeps the first parent.
- **Believing `git rm` and `git rm --cached` are the same** → `--cached` un-tracks and keeps the file; plain `git rm` deletes it from disk too.
- **Assuming the reflog saves everything** → it only knows commits. Unstaged edits and untracked files were never in git.
- **`git restore .` in a hurry** → discards every uncommitted change in the tree, not just the file you were looking at.
- **Reverting a squashed feature commit to undo one line** → you undo the whole feature. Make a small forward fix instead.

# Interview Questions
- **Junior:** "What is the difference between `git reset` and `git revert`?" — `reset` moves my branch pointer to an earlier commit, so the later commits stop being part of the branch — it *rewrites* history and is only safe locally. `revert` creates a **new** commit containing the inverse diff, so history moves forward and nothing anyone else has is invalidated — that is the one to use on a shared branch like `main`.

- **Mid:** "You staged a file by accident, and separately you want to throw away an edit. Which commands?" — Un-stage with `git restore --staged <file>` (keeps the edit; the old spelling was `git reset <file>`). Discard the edit with `git restore <file>` — and I would check `git diff` first, because that one has no undo: the bytes were never committed, so the reflog has nothing. If I might want it back I `git stash` instead.

- **Senior:** "Explain the three reset modes in terms of the three trees, and what each one can lose." — `--soft` moves HEAD only: index and working tree untouched, so the commit's changes are still staged — useful for re-committing differently. `--mixed` (default) also resets the index, leaving the changes as unstaged edits. `--hard` additionally overwrites the working tree, which is the only destructive one: the commit itself is still recoverable via reflog for ~90 days, but uncommitted edits are gone forever because git never had them. In all three the branch label moves, so all three are history rewrites and none belongs on a shared branch.

- **Staff:** "Design the rollback story for a production Django deploy on a small team." — Make revert the primary path and make it cheap: squash-merge so `main` is one commit per feature and `git revert <sha>` is a complete, reviewable rollback; put the revert through the normal PR gate, because a revert is a code change and the `migrations` job is what catches a later migration depending on the reverted model. Forbid `reset`/force-push on shared branches, and enforce it where it is free — a `pre-push` hook refusing `main`, collaborators on Read access working from forks, CI as the visible gate. Separate the three failure classes: code rolls back with `revert`, schema rolls back with a compensating migration (never by deleting one), and **data never rolls back with git at all** — money corrections go through the single-writer service that owns that ledger, as an append-only reversal. Then rehearse it: an untested rollback is a hypothesis, same as an untested backup.

### Why interviewers ask these — and the answer that separates levels

| Testing for | Weak answer | What lands |
|---|---|---|
| Do you know the three trees? | "They both undo things." | Map each command to a tree: `restore` = files, `reset` = branch (+index/tree by mode), `revert` = a new forward commit. |
| Do you know what is unrecoverable? | "The reflog saves everything." | Reflog only knows commits: unstaged edits and untracked files were never in git, so `restore`/`clean` are final. |
| Do you pick by blast radius? | "I'd reset to the last good commit." | Ask first whether the commit is shared: shared ⇒ `revert`, local ⇒ `reset`. Rewriting shared history breaks every clone. |
| Do you separate code from data? | "We'd roll back the deploy." | Code reverts, schema needs a compensating migration, money needs an append-only reversal through its owning service. |

**The killer follow-up:** *"You ran `git reset --hard` and lost both a commit and two hours of uncommitted edits. Exactly what can you get back?"* — The **commit**: yes — `git reflog` (or `git reset --hard ORIG_HEAD`) still names it for ~90 days, and `git fsck --lost-found` finds it even if the reflog is gone. The **uncommitted edits**: no — they were never in the object database, so there is nothing to recover; only the editor's local history might have them. The lesson is the fix: `git add` and a scratch `wip` commit cost nothing and move work into the recoverable half.

# Revision Notes
- Three undos, three layers: **`restore`** = files · **`reset`** = branch pointer · **`revert`** = new inverse commit.
- Shared/pushed ⇒ **`revert`**. Local only ⇒ **`reset`**. Just files ⇒ **`restore`**.
- `reset --soft` = HEAD only · `--mixed` (default) = HEAD + index · `--hard` = + working tree ⚠.
- `git reset <path>` un-stages; it does not move the branch. Modern form: `git restore --staged <path>`.
- `git revert -m 1 <merge>` is required for merge commits; reverting a revert re-applies the change.
- `git clean -fd` deletes untracked files; **`-x` also deletes gitignored** (`.env`, `env/`). `-n` first, always.
- Recoverable: commits (reflog ~90 days, `ORIG_HEAD`). Not recoverable: unstaged edits, untracked files.
- `git rm --cached` un-tracks and keeps the file — commit `42a2ecc4`, 2,954 files, 331,748 deletions, disk untouched.
- Money is never undone with git: settlement is the only money-write boundary.

# Cheat Sheet
- **See before you undo:** `git status` · `git diff` (tree vs index) · `git diff --staged` (index vs HEAD) · `git clean -n`
- **Un-stage:** `git restore --staged <f>` · **discard edit:** `git restore <f>` ⚠ · **both:** `git restore --staged --worktree <f>`
- **One file from an old commit:** `git restore --source=<sha> -- <path>`
- **Un-commit, keep staged:** `git reset --soft HEAD~1` · **keep unstaged:** `git reset HEAD~1` · **drop everything:** `git reset --hard HEAD~1` ⚠
- **Undo the last operation:** `git reset --hard ORIG_HEAD` · **any past position:** `git reflog` → `git reset --hard HEAD@{n}`
- **Safe shared undo:** `git revert <sha>` · **merge commit:** `git revert -m 1 <sha>` · **stage only:** `git revert --no-commit <sha>`
- **Untracked cleanup:** `git clean -n` → `git clean -fd` ⚠ (`-x` also removes gitignored: `.env`, `env/`) ⚠⚠
- **Stop tracking, keep the file:** `git rm --cached <path>` (then add it to `.gitignore`)
- **Park work instead of discarding:** `git stash push -m "wip"` → `git stash pop`

# My ERP Section
| Concept | In this repo |
|---|---|
| Live example of `restore` risk | `git diff --stat` = `config/learning/registry.py | 11 insertions` — uncommitted, so `git restore` = permanent loss |
| Live example of `clean` risk | untracked right now: `.github/`, `CHANGELOG.md`, `CONTRIBUTING.md`, `git-hooks/` — `clean -fd` deletes the workflow system |
| `-x` blast radius | root `.gitignore` blocks `*.sql`, `*.dump`, `*.sql.gz`, `db_backups/`, `backups/`, `node_modules/`; `.env`/`env/` are ignored too |
| Real index-only undo | `42a2ecc4` — `git rm --cached`, **2,954** files untracked, **331,748** deletions, files byte-identical on disk |
| Deliberate non-rewrite | history NOT rewritten (0 forks, nothing usable in the dumps); reasoning recorded in the commit message |
| Why `revert` is cheap here | squash-merge (§5) ⇒ one commit per feature ⇒ one `git revert <sha>` = full feature rollback |
| Hook support | `git-hooks/commit-msg` allows `Revert `, `Merge `, `fixup!` through the Conventional-Commits gate |
| Reset used in CI | `git reset --soft $(git merge-base origin/<base> HEAD)` re-presents the whole PR as **staged** so `ds_lint.sh --changed` works unmodified |
| Scale of a reset | **2,407** tracked files (`git ls-files | wc -l`); `.git` = **97 MB** |
| Money rule | settlement is the only money-write boundary — corrections are append-only reversals, never a git undo |

# Practice Tasks
1. **Classify.** For each of `git restore file.py`, `git reset --soft HEAD~1`, `git reset --hard HEAD~1`, `git revert HEAD`, `git clean -fd`: write which of the three trees it changes and what it can lose.
2. **Dry run.** Run `git clean -n` in this repo and list what it would delete. Explain why the reflog could not bring any of it back.
3. **Recovery drill.** On a scratch branch: commit, `git reset --hard HEAD~1`, then recover the commit with `git reflog`. Do it until it feels boring.
4. **Un-track without deleting.** Create a junk file, commit it, then `git rm --cached` it and add it to `.gitignore`. Confirm with `ls` that the file is still on disk — the same move as commit `42a2ecc4`.
5. **Revert for real.** Commit a small change on a branch, `git revert` it, then read `git log --oneline -3` and explain why two commits exist instead of zero.

# Homework
- Write the three-line decision rule you will actually use (`restore` / `reset` / `revert`) and stick it above your desk. Then justify each branch of it in one sentence.
- Read `CONTRIBUTING.md` §10 and explain why "no `git push --force` to a shared branch" and "prefer `revert` on `main`" are the same rule wearing two hats.
- The dump incident chose `git rm --cached` over rewriting history. List the three facts that made that the right call, and name the one fact that would have flipped it.
- Try `git clean -n` and then look up what `-x` adds. Write down exactly which files in *your* clone would be destroyed, and where a replacement copy of each lives.

---

# Further Reading & Live Resources
- Pro Git — *Undoing Things* (`--amend`, unstaging, unmodifying): https://git-scm.com/book/en/v2/Git-Basics-Undoing-Things
- Pro Git — *Reset Demystified* (the three trees, mode by mode — read this twice): https://git-scm.com/book/en/v2/Git-Tools-Reset-Demystified
- `git restore` reference (the modern file-level undo): https://git-scm.com/docs/git-restore
- `git revert` reference, including `-m` for merges: https://git-scm.com/docs/git-revert
- `git clean` reference — read `-n`, `-d`, `-x` before you ever type `-f`: https://git-scm.com/docs/git-clean
