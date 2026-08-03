---
id: git-course-39-disaster-playbook
type: lesson
status: active
owner: handwritten
scope: git — recovery recipes for the ten situations that make people panic
anchors: .git/logs, git-hooks/pre-push, CONTRIBUTING.md
verified: 2026-08-03
---

# 39 — Disaster Playbook ("I broke it" — the ten recipes)

> Part of [Git Course](00_COURSE_OVERVIEW.md). Prev: [38 — Git Internals, Hands-On](38_Git_Internals_Hands_On.md). Next: [40 — The Workflow, Assembled](40_The_Workflow_Assembled.md).

# Learning Objectives
By the end of this chapter you can:
- recover from the ten situations that most commonly cause panic
- explain the one question that determines whether anything is recoverable
- know exactly what is **genuinely** unrecoverable, and why
- use `reflog` and `fsck --lost-found` as your two recovery tools
- stay calm, because you will know the answer is almost always "yes, it's still there"

# Purpose
This is the chapter to open at 2am. It is deliberately structured as a **lookup table**, not an
argument: find your symptom, run the recipe.

The single most valuable thing to internalise is this: **git almost never loses committed work.**
Commits are immutable, content-addressed objects, and the reflog holds a reference to every position
HEAD has occupied for ~90 days ([Chapters 05](05_How_Git_Stores_Everything.md),
[16](16_Reflog.md)). "I lost my commits" is, in the overwhelming majority of cases, "I cannot see my
commits."

Fear of git is really fear of being unable to undo. This chapter removes it.

# The Problem
Ten situations, all of which feel catastrophic and nine of which are not:

1. Committed to the wrong branch
2. `git reset --hard` and lost work
3. Deleted a branch with unmerged commits
4. A rebase went wrong halfway through
5. Someone force-pushed over your commits
6. Committed a secret
7. Committed a huge file
8. Detached HEAD and confused
9. Merge conflict mess and you want out
10. Broke `main`

Under pressure people reach for `--force` and `--hard` — the two flags that *can* actually destroy
something. This chapter's job is to give you the right command before you reach for the wrong one.

# Theory (from zero)

### The one question that decides everything
> **Was it ever committed (or even staged)?**

- **Committed** → it is an object in `.git/objects`, and the reflog remembers where HEAD was.
  **Recoverable.**
- **Staged but not committed** → `git add` already wrote the blob
  ([Chapter 38](38_Git_Internals_Hands_On.md)). Recoverable with `fsck`, awkwardly.
- **Never staged, never committed** → git has never seen it. **Gone.** No command helps.

That third case is the only genuine data loss in this chapter, and it is why
[`git stash`](17_Stash_And_Worktrees.md) exists.

### Your two recovery tools
**1. `git reflog`** — a local log of every position HEAD has held:

```bash
git reflog
# 42a2ecc4 HEAD@{0}: commit: chore(repo): stop tracking database dumps
# 83a144ba HEAD@{1}: merge: Merge pull request #15
# 7fe2bb0e HEAD@{2}: commit: feat: accountant read tier
```

Every reset, checkout, rebase, merge and commit appends an entry. Default retention is **90 days**
for reachable entries and ~30 for unreachable ones. It is **per-clone and never pushed** — your
reflog cannot help a colleague, and theirs cannot help you.

Every ref has its own reflog, which is often the more precise tool:

```bash
git reflog show main            # just this branch's movements
git reflog show stash           # the stash list IS a reflog (ch 17)
```

**2. `git fsck --lost-found`** — finds objects reachable from nothing at all:

```bash
git fsck --lost-found
# dangling commit 7d3f2a1…
```

Use it when the reflog has been pruned, or when the thing you lost was never on a branch.

### The recovery grammar
```bash
git reset --hard <hash>        # move THIS branch (and worktree) back to a known state
git branch rescue <hash>       # give a lost commit a name so it stops being lost
git switch -c rescue <hash>    # same, and go there
git cherry-pick <hash>         # bring one commit onto the current branch
git checkout <hash> -- <path>  # recover ONE FILE from any commit
```

`git branch rescue <hash>` is the safest first move in almost every scenario: it makes the commit
reachable without changing where you are. Nothing else can then garbage-collect it while you think.

### The three commands that can actually destroy something
Everything else in git is additive. These three are not:

| Command | Destroys |
|---|---|
| `git reset --hard` | **uncommitted** working-tree and index changes |
| `git checkout/restore <path>` | **uncommitted** changes to that file |
| `git push --force` | commits on the **remote** that you do not have |
| `git clean -fd` | **untracked** files — never recoverable |

Notice the pattern: what they destroy is always **uncommitted** work, or work on a **remote**. Commit
first, and the whole category disappears. `git clean -fd` deserves its own mention — untracked files
were never in git, so nothing can bring them back.

> 💡 **Samjho aise:** Ek hi sawaal poochho: **commit hui thi ya nahi?**
>
> **Hui thi** → wo `.git` mein **hai**. Dikh nahi rahi, gayi nahi hai. `git reflog` HEAD ke har purane
> pate ka record rakhta hai — **90 din**. Pata dhoondo, `git branch rescue <hash>` kar do, kaam wapas.
>
> **Nahi hui thi** → tab hi asli nuksaan hai. Git ne wo cheez **dekhi hi nahi**. Koi command nahi
> bacha sakta.
>
> Isliye asli niyam: **darne se pehle commit karo.** Aur ghabराहat mein `--force` / `--hard` mat maaro —
> yehi do cheezein asal mein nuksaan karti hain. Pehle `git reflog`, phir `git branch rescue`. Chai
> peene ke baad sochna.

# Real World Example (this repo)
Two live examples from this repository.

**1. The reflog, right now.** Three positions HEAD has occupied, all still reachable:

```bash
git reflog -3
# 42a2ecc4 commit: chore(repo): stop tracking database dumps + node_modules; teach why…
# 83a144ba pull upstream main: Fast-forward
# 7fe2bb0e commit: feat: accountant read tier, student role, learning platform completion…
```

Note what the middle line records: **the action, not the commit's own message.** `83a144ba` *is* the
PR #15 merge commit, but the reflog says `pull upstream main: Fast-forward` because that is how HEAD
arrived there. The reflog is a log of **movements**, not a second copy of the log — which is exactly
what makes it useful for recovery: it tells you *how* you got somewhere, including the resets and
rebases that `git log` will never show you.

If `42a2ecc4` were reset away right now, `git reset --hard HEAD@{0}` would bring it straight back.
Nothing has been lost in this repository at any point.

**2. A real "I broke it" case that was NOT a git problem.** `main` locally sits at `7c256f50` — five
commits behind `origin/main` at `83a144ba`. That made a routine range query answer **296** when the
truth was **1** ([Chapter 18](18_Remotes.md)).

Nothing was broken. Nothing needed recovery. Local `main` was a pointer nobody had moved, because
`git fetch` updates `origin/main` and never your local branches. The fix is a sync, not a rescue:

```bash
git fetch origin
git switch main && git merge --ff-only origin/main
```

This is worth including in a disaster playbook precisely because **most "git is broken" moments are
this**: a stale ref, a detached HEAD, or work on a branch you forgot you were on. Recovery is rarely
needed; orientation usually is.

**3. What this project has in place so the worst cases cannot happen:**

- `git-hooks/pre-push` refuses a direct push to `main`, **including a deletion push** (all-zero sha)
  — verified with a real `git push` where `git ls-remote` showed **0 refs**
  ([Chapter 27](27_Pre_Push_Protection.md)).
- `CONTRIBUTING.md` §10 mandates `--force-with-lease` and forbids plain `--force` on shared branches
  ([Chapter 34](34_Rewriting_History.md)).
- Collaborators hold **Read** access and work from forks, so they cannot force-push this repository at
  all ([Chapter 20](20_Forks_And_The_Fork_Flow.md)).

The playbook exists anyway, because the owner can still `--no-verify`.

# Visual Diagram
```
  THE ONLY QUESTION
  ─────────────────
                 Was it COMMITTED (or even STAGED)?
                        │                    │
                      YES                   NO
                        │                    │
             it is an OBJECT in         git NEVER SAW IT
             .git/objects                     │
                        │                     ▼
              ┌─────────┴─────────┐      ✖ GONE. No command helps.
              ▼                   ▼         (this is why `git stash` exists)
        git reflog          git fsck --lost-found
        (HEAD's history,     (objects reachable
         ~90 days,            from nothing)
         per-clone, never pushed)
              │                   │
              └─────────┬─────────┘
                        ▼
              git branch rescue <hash>     ← SAFEST first move:
                                             names it, changes nothing else

  THE FOUR COMMANDS THAT CAN ACTUALLY DESTROY
  ───────────────────────────────────────────
   git reset --hard        uncommitted worktree + index
   git restore <path>      uncommitted changes to that file
   git clean -fd           UNTRACKED files ← never recoverable
   git push --force        commits on the REMOTE you don't have

   pattern: they destroy UNCOMMITTED work, or work on a REMOTE.
            commit first ⇒ the whole category disappears.

  MOST "GIT IS BROKEN" MOMENTS ARE ORIENTATION, NOT LOSS
  ─────────────────────────────────────────────────────
   stale local main   (this repo: 296 vs 1)  → git fetch + merge --ff-only
   detached HEAD      → cat .git/HEAD ; git switch <branch>
   wrong branch       → git log --oneline -1 ; git branch --show-current
```

# Practical — the ten recipes

### 1. Committed to the wrong branch
```bash
# you are on main, the commits belong on a feature branch
git branch feat/rescue              # name the commits where they are
git reset --hard origin/main        # restore main to the remote
git switch feat/rescue              # your work, on the right branch
```
Nothing is lost: the branch you created still points at the commits.

### 2. `git reset --hard` and lost work
```bash
git reflog                          # find the hash from BEFORE the reset
git reset --hard HEAD@{1}           # go back one reflog position
```
⚠️ Recovers **committed** work only. Uncommitted changes destroyed by `--hard` are gone.

### 3. Deleted a branch with unmerged commits
```bash
git reflog --all | grep -i "branch-name"     # find its last tip
git branch branch-name <hash>                # recreate it
# or, if the reflog was pruned:
git fsck --lost-found
```
Deleting a branch removes a 41-byte pointer file. The commits are untouched
([Chapter 09](09_What_A_Branch_Really_Is.md)).

### 4. A rebase went wrong halfway through
```bash
git rebase --abort                  # DURING the rebase: full restore, no harm
# already finished it?
git reset --hard ORIG_HEAD          # git saved where you were
git reflog                          # or find it manually
```
`ORIG_HEAD` is set by rebase, merge and reset — a free one-step undo.

### 5. Someone force-pushed over your commits
```bash
git reflog                          # YOUR reflog still has them
git branch rescue HEAD@{1}
git log origin/main..rescue         # what the force-push abandoned
git cherry-pick <hash>              # re-apply, then push properly
```
Any clone that fetched before the force-push holds the commits. Prevention:
`--force-with-lease` refuses this push outright ([Chapter 34](34_Rewriting_History.md)).

### 6. Committed a secret
```bash
# 1. ROTATE the credential. This is not a git command, and it comes FIRST.
# 2. then contain:
printf '.env\n*.sql\n' >> .gitignore      # at the REPO ROOT (ch 36)
git rm --cached .env
git commit -m "chore: untrack .env, add ignore rule"
# 3. decide about history — on evidence, not reflex (ch 33, ch 34)
```
Deleting the file does **not** remove it from history. Rotation is the only step that reduces risk.

### 7. Committed a huge file
```bash
git rm --cached bigfile && git commit -m "chore: untrack bigfile"
# ⚠ this reclaims NOTHING — the blob is still in history (ch 37)
# only a rewrite shrinks .git, and only if it is worth the cost (ch 34):
git filter-repo --invert-paths --path bigfile     # on a FRESH clone
git reflog expire --expire=now --all && git gc --prune=now
```
Proven in this repository: 2,954 files untracked, `.git` stayed at **97 MB**.

### 8. Detached HEAD and confused
```bash
cat .git/HEAD                       # a raw hash = detached; "ref: …" = on a branch
git branch --show-current           # empty output = detached
git switch -c rescue                # keep any commits you made here
git switch main                     # or just leave, if you made none
```
Detached HEAD is a *value*, not a fault ([Chapter 38](38_Git_Internals_Hands_On.md)).

### 9. Merge conflict mess and you want out
```bash
git merge --abort                   # during a merge
git rebase --abort                  # during a rebase
git cherry-pick --abort             # during a cherry-pick
# want to keep going but restart one file?
git checkout --conflict=diff3 -- <path>
```
Every conflict-producing operation has an `--abort`. Nothing is half-applied.

### 10. Broke `main`
```bash
git log --oneline -5 main           # find the last good commit
git revert <bad-commit>             # SAFE: a new commit that undoes it (shared history)
# a merge commit needs a mainline:
git revert -m 1 <merge-commit>
# NEVER on shared history:
git reset --hard <good>  # + force-push ⇒ breaks everyone's clone
```
**`revert` for shared history, `reset` for local only.** That single distinction is the most
important line in this chapter.

### The universal first response
```bash
git status                          # where am I, what is staged?
git branch --show-current           # which branch (empty = detached)
git reflog -10                      # where have I been?
git stash                           # park anything uncommitted BEFORE experimenting
git branch rescue-$(date +%s) HEAD  # name your current position, just in case
```

# Production Walkthrough
When something goes wrong, in this order:

1. **Stop.** Do not run another command yet. Most damage happens in the second command, not the first.
2. **Orient**: `git status`, `git branch --show-current`, `git reflog -10`. Half of all "disasters"
   dissolve here — you were on the wrong branch, or a ref was stale.
3. **Park uncommitted work**: `git stash` or a throwaway commit. Now nothing can destroy it.
4. **Name your current position**: `git branch rescue-$(date +%s) HEAD`. Free insurance.
5. **Ask the one question**: was it committed? Yes → reflog or fsck. No → it is gone; move on.
6. **Prefer additive recovery**: `git branch`, `git cherry-pick`, `git revert` — commands that create
   rather than destroy.
7. **Verify before continuing**: `git log`, `git diff`, and check the files are actually right.
8. **Then fix the cause**, not just the symptom. A stale `main` recurs weekly unless you learn
   `--ff-only`.

# Debugging Guide

| Symptom | Recipe |
|---|---|
| "My commits vanished" | `git reflog`; `git branch rescue <hash>` |
| "I reset --hard by mistake" | `git reset --hard HEAD@{1}` (committed work only) |
| "I deleted the branch" | `git reflog --all \| grep <name>`; `git branch <name> <hash>` |
| "Rebase is a mess" | `git rebase --abort`, or `git reset --hard ORIG_HEAD` |
| "Someone force-pushed" | your reflog has it: `git branch rescue HEAD@{1}` |
| "I committed a secret" | **rotate first**, then untrack + ignore ([Ch 33](33_Secrets_And_Leaks.md)) |
| "Repo is huge" | untracking reclaims nothing; measure first ([Ch 37](37_Large_Files_And_Performance.md)) |
| "Detached HEAD" | `git switch -c rescue` if you committed; else `git switch main` |
| "Conflict mess" | `git merge --abort` / `git rebase --abort` |
| "Broke main" | `git revert` (shared) — never `reset --hard` + force-push |
| "`git pull` made a mess" | `git reset --hard ORIG_HEAD`; then set `pull.rebase true` |
| "Deleted an uncommitted file" | if never staged: **gone**. If staged: `git fsck --lost-found` |
| "Ran `git clean -fd`" | untracked files are **unrecoverable** |
| "Amended and lost the old commit" | `git reflog`; the pre-amend commit is still there |
| "Cherry-pick applied the wrong thing" | `git cherry-pick --abort`, or `git reset --hard ORIG_HEAD` |
| "Wrong author on my commits" | `git commit --amend --reset-author` (last one only) |
| "Range query gives absurd numbers" | stale local ref: `git fetch` + `merge --ff-only` — this repo's 296-vs-1 |

# Performance Notes
- **`git reflog` is instant** — it reads `.git/logs/`, a plain text file per ref.
- **`git fsck` is slow** (minutes on a large repo) because it decompresses and rehashes every object.
  Try the reflog first.
- **`git reset --hard` is fast** — it writes the index and working tree from an existing tree object.
- **Recovery is cheap because nothing was deleted.** Objects persist; you are only creating a new ref
  to reach them.
- **Retention matters**: reflog entries expire at ~90 days (30 for unreachable). After that, `fsck`
  is your only option until `gc` prunes the objects too.
- **`git gc --prune=now` destroys this safety net immediately.** Only run it when you intend to.

# Security Considerations
- **`git clean -fd` is the one truly destructive command** for untracked files, and `.gitignore`d
  files with `-x`. There is no recovery. Run `git clean -nd` (dry run) first, always.
- **Recovering a secret is not the same as removing it.** `fsck --lost-found` will happily surface a
  secret from a commit you thought you discarded — which is also how *anyone* with the repo finds it
  ([Chapter 33](33_Secrets_And_Leaks.md)).
- **Rotation before recovery.** If the disaster involves a credential, changing it precedes every git
  command.
- **`--force` on a shared branch is the most damaging thing in this chapter**, and on a free private
  repo there is no server-side protection to stop it — hence this project's `pre-push` hook and the
  `--force-with-lease` habit ([Chapter 27](27_Pre_Push_Protection.md)).
- **`revert`, not `reset`, on shared history.** A reset plus force-push destroys other people's
  clones; a revert is a new commit that hurts nobody.
- **The reflog is local and unpushed** — never a backup. Real backups are the remote plus your
  database backups.
- **A rescue branch is not cleanup.** Delete `rescue-*` branches once you have verified the recovery,
  or they pin objects forever.

# Architecture Decisions
- **Git is additive by design**, which is what makes recovery possible: objects are immutable and
  content-addressed, so "losing" work almost always means losing a *reference*.
- **The reflog exists precisely for this**, with generous retention (~90 days) — a deliberate choice
  favouring recoverability over disk.
- **Every conflict-producing operation has `--abort`.** Merge, rebase and cherry-pick are transactional
  from the user's point of view.
- **`ORIG_HEAD` is set automatically** by rebase, merge and reset — a free single-step undo.
- **This project blocks direct pushes to `main`** with a hook that also refuses deletion pushes,
  because branch protection is paid on private repos.
- **`--force-with-lease` mandated, plain `--force` forbidden** (`CONTRIBUTING.md` §10).
- **Collaborators get Read + a fork**, so the highest-damage action is unavailable to them entirely.
- **Squash-merge** makes `git revert` a clean, single-commit operation when `main` does break
  ([Chapter 21](21_Pull_Requests.md)).

# Best Practices
- **Commit early and often.** Committed work is recoverable; uncommitted work is not.
- **`git stash` before experimenting.** Free insurance.
- **`git branch rescue-$(date +%s) HEAD`** before anything risky.
- **Orient before acting**: `status`, `branch --show-current`, `reflog`.
- **Prefer additive commands**: `branch`, `cherry-pick`, `revert`.
- **`revert` on shared history. `reset` only locally.**
- **`--force-with-lease`, never plain `--force`.**
- **`git clean -nd` before `git clean -fd`.** Always.
- **Do not `gc --prune=now`** unless you are deliberately destroying recovery.
- Clean up `rescue-*` branches once verified.

# Beginner Mistakes
- **Panicking and running more commands** → the second command usually causes the real damage.
- **Assuming committed work can be lost** → it almost never can. Check the reflog first.
- **`git reset --hard` to "undo"** → destroys uncommitted work permanently.
- **`git push --force` to fix a rejected push** → can delete a colleague's commits.
- **`reset --hard` + force-push on shared history** → breaks everyone's clone. Use `revert`.
- **`git clean -fd` casually** → untracked files are unrecoverable.
- **Trusting the reflog as a backup** → it is local and never pushed.
- **Deleting a file to "remove" a secret** → history keeps it; rotate.
- **Expecting untracking to shrink `.git`** → it does not (proven here: still 97 MB).
- **Treating a stale ref as corruption** → `git fetch` and `merge --ff-only`.

# Interview Questions
- **Junior:** "You ran `git reset --hard` and lost a commit. Recover it." — `git reflog` to find the
  hash from before the reset, then `git reset --hard HEAD@{1}`. The commit was never deleted; the
  branch pointer just moved. Only *uncommitted* changes are actually lost to `--hard`.
- **Mid:** "What is genuinely unrecoverable in git?" — Work git never saw: files that were never staged
  and never committed, and untracked files removed by `git clean -fd`. Anything committed — or even
  just `git add`ed, since that writes the blob — exists as an object and is reachable via reflog or
  `fsck --lost-found` until garbage collection.
- **Senior:** "A colleague force-pushed and your commits are gone from the remote. Walk me through it." —
  They are not gone: my local reflog still points at them, so `git branch rescue HEAD@{1}` names them
  safely, then `git log origin/main..rescue` shows exactly what the force-push abandoned and I
  cherry-pick or re-push properly. Any other clone that fetched beforehand also holds them. The
  structural fix matters more than the recovery: `--force-with-lease` would have refused that push
  because the remote had moved since their last fetch, and server-side branch protection would refuse
  non-fast-forward pushes outright — which is unavailable on a free private repo, so a client-side hook
  plus the lease habit is the substitute.
- **Staff:** "Your team loses work regularly. It is not a training problem. What is wrong?" — Regular
  loss means the *system* permits it, so I would look at where the destructive capability sits rather
  than at people's habits. There are only a handful of commands that can actually destroy anything, and
  they cluster: `reset --hard` and `restore` destroy **uncommitted** work, `clean -fd` destroys
  **untracked** files, and `push --force` destroys work on a **remote**. Everything else in git is
  additive, so the countermeasures are structural. For uncommitted work the fix is that nothing valuable
  should live uncommitted for long — cheap pushed branches instead of long-lived stashes, since a stash
  is per-clone, never pushed, and dies with the laptop. For remote work the fix is authorisation and
  refusal: `--force-with-lease` as policy, contributors on Read access working from forks so the
  highest-damage action is simply unavailable to them, and server-side protection wherever the plan
  allows it. Then I would check the *invisible* prerequisite — whether people can even find lost work —
  because `reflog` has a retention window and `gc --prune=now` deletes the safety net, so a team that
  routinely runs aggressive gc has quietly opted out of recovery. And I would ask what happens after an
  incident: if nobody writes the recipe down, the same loss recurs with a different person. A playbook
  that is *findable at 2am* is a real control, not documentation theatre.

### Why interviewers ask these — and the answer that separates levels
| Testing for | Weak answer | What lands |
|---|---|---|
| Do you know recovery exists? | "I'd try to redo the work." | reflog holds every HEAD position ~90 days; `git branch rescue <hash>` names it without changing anything else. |
| Do you know the real boundary? | "Git can always get it back." | Committed or staged ⇒ recoverable; never-staged and `clean -fd` ⇒ genuinely gone. Name the line precisely. |
| Can you fix the system? | "We'll be more careful." | Only four commands destroy anything, and they cluster on uncommitted work and remotes — so: cheap pushed branches, `--force-with-lease`, Read+fork, and don't prune the reflog. |

**The killer follow-up:** *"Which git command can lose work that no recovery can bring back?"* — `git clean -fd` for untracked files, and `reset --hard` / `restore` for uncommitted changes — because in every case git never had the content, so there is no object to recover. That is the whole boundary: git protects what it has *seen*. Anyone who says "nothing, git keeps everything" has not thought about the staging boundary.

# Revision Notes
- **The one question: was it committed (or staged)?** Yes ⇒ recoverable. Never staged ⇒ **gone**.
- **Two tools:** `git reflog` (every HEAD position, ~90 days, **local, never pushed**) and `git fsck --lost-found`.
- **Safest first move:** `git branch rescue <hash>` — names it, changes nothing else.
- **Only four commands destroy:** `reset --hard` (uncommitted) · `restore <path>` (uncommitted) · **`clean -fd` (untracked — unrecoverable)** · `push --force` (remote).
- **`ORIG_HEAD`** is set by rebase/merge/reset — a free one-step undo.
- Every conflict operation has **`--abort`**.
- **`revert` on shared history; `reset` only locally.** The most important distinction here.
- Secret? **Rotate first** — deleting the file does not remove it from history.
- Untracking does **not** shrink `.git` (proven here: still 97 MB).
- Most "git is broken" = **orientation**, not loss: stale ref (296 vs 1), detached HEAD, wrong branch.

# Cheat Sheet
```bash
# ORIENT FIRST — half of all disasters dissolve here
git status
git branch --show-current            # empty = detached HEAD
git reflog -10                       # where HEAD has been
cat .git/HEAD                        # "ref: …" = on a branch; a hash = detached

# INSURANCE, before anything risky
git stash                            # park uncommitted work
git branch rescue-$(date +%s) HEAD   # name your current position

# FIND LOST WORK
git reflog                           # HEAD's history
git reflog show main                 # one branch's movements
git reflog --all | grep <name>       # a deleted branch's last tip
git fsck --lost-found                # objects reachable from nothing

# RECOVER (additive — prefer these)
git branch rescue <hash>             # name it
git switch -c rescue <hash>          # name it and go there
git cherry-pick <hash>               # bring one commit here
git checkout <hash> -- path/to/file  # one file from any commit
git reset --hard HEAD@{1}            # back one reflog position
git reset --hard ORIG_HEAD           # undo the last rebase/merge/reset

# ABORT anything mid-operation
git merge --abort
git rebase --abort
git cherry-pick --abort

# BROKE SHARED HISTORY
git revert <bad-commit>              # SAFE on shared branches
git revert -m 1 <merge-commit>       # a merge needs a mainline

# ⚠ DESTRUCTIVE — know before you type
git reset --hard          # uncommitted changes GONE
git clean -nd             # DRY RUN first, always
git clean -fd             # untracked files — UNRECOVERABLE
git push --force-with-lease   # never plain --force on shared
```

# My ERP Section

| Protection / fact | This repository |
|---|---|
| Reflog right now | `42a2ecc4` HEAD@{0} · `83a144ba` HEAD@{1} (PR #15 merge) · `7fe2bb0e` HEAD@{2} — nothing has ever been lost here |
| Direct push to `main` | refused by `git-hooks/pre-push`, **including deletion pushes** (all-zero sha); verified with a real push where `git ls-remote` showed **0 refs** ([Ch 27](27_Pre_Push_Protection.md)) |
| Force-push policy | `CONTRIBUTING.md` §10 — `--force-with-lease` on your own branch only; **plain `--force` forbidden** on shared |
| Collaborator blast radius | **Read** access + fork ⇒ they cannot force-push or merge here at all ([Ch 20](20_Forks_And_The_Fork_Flow.md)) |
| Revert is clean | **squash-merge** ⇒ one feature = one commit on `main`, so `git revert` undoes a whole feature ([Ch 21](21_Pull_Requests.md)) |
| Real "broken" case | local `main` at `7c256f50` vs `origin/main` `83a144ba` ⇒ a range query read **296** when the truth was **1**. Fix: `git fetch` + `merge --ff-only` — orientation, not recovery ([Ch 18](18_Remotes.md)) |
| Untracking ≠ shrinking | 2,954 files untracked, `.git` **still 97 MB** ([Ch 37](37_Large_Files_And_Performance.md)) |
| Secret incident | rotate-first was the rule; history deliberately **not** rewritten on evidence ([Ch 33](33_Secrets_And_Leaks.md), [Ch 34](34_Rewriting_History.md)) |
| Why the playbook still matters | the owner can always `--no-verify`; hooks stop mistakes, not intent |

# Practice Tasks
1. In a throwaway repo: commit, `git reset --hard HEAD~1`, then recover with
   `git reset --hard HEAD@{1}`. Do this once and the fear of `reset` goes away.
2. Create a branch with commits, delete it with `git branch -D`, then recover it from the reflog.
3. Start a rebase, hit a conflict, and `git rebase --abort`. Confirm you are exactly where you started.
4. Make an uncommitted change and destroy it with `git restore <path>`. Confirm it is **unrecoverable**.
   That is the boundary, felt.
5. Create an untracked file, run `git clean -nd` (dry run), read the output, then `git clean -fd`.
   Confirm it is gone forever.
6. Reproduce this repo's real "broken" case: leave `main` stale, run
   `git rev-list --count main..HEAD`, then fetch and `merge --ff-only` and run it again.

# Homework
- Write your own one-page playbook, in your own words, and put it where you will find it at 2am. The
  act of writing it is most of the value.
- Practise all ten recipes in a throwaway repo, in order. Muscle memory beats reading when you are
  stressed.
- Read `git help reflog` on `gc.reflogExpire` and `gc.reflogExpireUnreachable`, and decide whether you
  want longer retention. Then explain what it costs.
- Deliberately force-push over your own commit in a scratch repo and recover it. Then do the same with
  `--force-with-lease` and watch it refuse. Feeling both is the lesson.

# Further Reading & Live Resources
- [Pro Git — Maintenance and Data Recovery](https://git-scm.com/book/en/v2/Git-Internals-Maintenance-and-Data-Recovery) — the canonical recovery chapter; free
- [git-reflog reference](https://git-scm.com/docs/git-reflog) — retention settings and `@{n}` syntax
- [git-fsck reference](https://git-scm.com/docs/git-fsck) — `--lost-found`, `--unreachable`, `--dangling`
- [Dangit, Git!?!](https://dangitgit.com/) — the same recipes, profanity-free, in a searchable format
- [Oh Shit, Git!?!](https://ohshitgit.com/) — the original, and still the best-phrased version
- [git-revert](https://git-scm.com/docs/git-revert) — including `-m` for merge commits
- [`git push --force-with-lease`](https://git-scm.com/docs/git-push#Documentation/git-push.txt---force-with-leaseltrefnamegt) — the flag that prevents recipe 5 entirely
