---
id: git-course-16-reflog
type: lesson
status: active
owner: handwritten
scope: git, version control — the reflog as local safety net, and recovering "lost" commits
anchors: .git/logs/HEAD, .git/ORIG_HEAD, .git/lost-found, git-hooks/pre-push, CONTRIBUTING.md
verified: 2026-08-03
---

# 16 — Reflog — the time machine (git's local undo journal)

> Part of [Git Course](00_COURSE_OVERVIEW.md). Prev: [15 — Undo: reset vs revert vs restore](15_Undo_Reset_Revert_Restore.md). Next: [17 — Stash & Worktrees](17_Stash_And_Worktrees.md).

# Learning Objectives
By the end of this chapter you can:
- explain what the reflog **is** — a per-ref journal on disk — and open the real file
- read a raw reflog line field by field
- tell `HEAD@{2}` from `HEAD~2`, and say why confusing them wastes an afternoon
- recover from a bad `reset --hard`, a bad rebase, and a deleted branch
- state the windows (90 / 30 days) after which recovery stops working
- name the four situations where the reflog **cannot** save you

# Purpose
[Ch 15](15_Undo_Reset_Revert_Restore.md) gave you commands that move branch pointers, including `git reset --hard`, which prints almost nothing and looks like deletion. This chapter is the net underneath them. Once you trust the reflog, every other git command gets less frightening — the real goal, because a developer who fears git writes worse history.

# The Problem
Three commits into a feature you half-remember a command from a blog post and type:

```bash
git reset --hard HEAD~3
```

`git log` now shows your three commits **gone**. `git status` says clean. This morning's code is not on disk. No Recycle Bin, no `Ctrl+Z`, and — because you never pushed — no copy on GitHub.

One of two things is now true about you: you know the reflog exists, and this is a ninety-second problem; or you don't, and you re-type three hours of work and quietly stop trusting git. Nothing was deleted. Git moved a pointer. This chapter finds where the pointer used to be.

# Theory (from zero)

### Three terms, properly
**Commit** — a permanent, **immutable** object in `.git/objects`, named by the hash of its own contents. Once written it is never edited; "changing" a commit ([Ch 14](14_Interactive_Rebase.md)) means writing a new one and pointing at that.

**Ref (reference)** — a name holding one commit hash. A branch is a ref under `refs/heads/`, a tag under `refs/tags/`. That is all a branch is ([Ch 09](09_What_A_Branch_Really_Is.md)): a small file with a hash in it. **HEAD** is the ref saying which ref you are on — usually `ref: refs/heads/new_flask_app`, a pointer to a pointer.

> **`commit`, `reset`, `checkout`, `switch`, `merge`, `rebase` and `pull` all do the same underlying thing — they move a ref.** None deletes commit objects.

### So what is the reflog?
Every time a ref moves, git appends **one line** to a plain text log for it: `.git/logs/HEAD` for HEAD, `.git/logs/refs/heads/<branch>` per branch. That is the **reflog**, and it answers a question ordinary history cannot: *where did this branch point 20 minutes ago?*

Here `.git/logs/HEAD` is **276 lines / 62,604 bytes** and `.git/logs/refs/heads/main` is **0 bytes** — so `git reflog show main` prints *nothing*, because nobody has ever moved local `main` in this clone. Work happens on `new_flask_app`; `main` advances on GitHub via merged PRs. **The reflog records your machine's actions, not the project's history.**

### Reading a raw line
The real last line of `.git/logs/HEAD`:

```
83a144ba3fad222bdd3b85d7b5f67a7fb0604ed2 42a2ecc4dc77dafc9407f4eaf4840c3ed8bd97fa umesh-personal <umesh29mar@gmail.com> 1785747733 +0530	commit: chore(repo): stop tracking database dumps + node_modules
```

Six fields: **old hash** (where the ref pointed before) · **new hash** (after) · **who** (`user.name`/`user.email`, [Ch 02](02_Install_And_Configure.md)) · **when** (Unix seconds + `+0530` IST) · **operation** (`commit`, `reset`, `merge`, `rebase`, `pull`, `checkout`) · **message**. The *old hash* column is the rescue rope: a bad `reset` cannot erase that line, it appends one.

### `HEAD@{2}` vs `HEAD~2` — name the confusing bit
```
HEAD~2     two steps back through PARENT links  → walks the commit GRAPH
HEAD@{2}   where HEAD pointed two moves ago     → walks TIME (the reflog)
```
`HEAD~2` is ancestry: same for everyone, present in a fresh clone, part of history. `HEAD@{2}` is about *your keyboard*: different on every machine, absent from a fresh clone, and after a `reset --hard` the only thing that still knows where you were. It also takes time (`'HEAD@{2.hours.ago}'`, `'main@{yesterday}'`). Always quote it — unquoted, zsh turns `HEAD@{1}` into `HEAD@1`.

### Why recovery works: reachability vs existence
Git deletes objects only during **garbage collection** (`git gc`), and only if an object is **unreachable** — no branch, no tag, and **no reflog entry** naming it. That last clause is the net: after `reset --hard HEAD~3` your commits have no branch, but the reflog line still names them, so `gc` leaves them alone. So: *existence ≠ reachability ≠ visible in `git log`.*

Two defaults set the deadline: `gc.reflogExpire` = **90 days** (commits still reachable from a ref), `gc.reflogExpireUnreachable` = **30 days** (commits nothing else points at). Neither is configured here, so **you have roughly 30 days to notice a `reset --hard`**. GC runs opportunistically, so often longer — never plan on it.

### The four things the reflog cannot recover
Work **never committed** (no object exists — two hours of edits then `git restore file` is gone permanently, which is *the* argument for committing early) · files **never added** to git (untracked and ignored files live only on disk) · anything **past expiry plus a real GC**, or after the deliberate nuke in *Security* · anything on a **machine you no longer have**, because reflogs are never pushed, fetched or cloned. It is a local undo journal, **not a backup** ([Ch 39](39_Disaster_Playbook.md)).

> 💡 **Samjho aise:** Reflog ek **CCTV register** hai darwaaze pe — jab bhi pointer hila, ek line likh di gayi: "pehle yahan tha, ab yahan, itne baje, kis command se". `reset --hard` ne kaam **delete nahi kiya**, sirf naam-plate hataayi; purana ghar (commit) waise hi khada hai aur register mein uska address likha hai. Do baatein yaad rakho: register **sirf tumhare laptop ka** hai, aur uski entries **~30 din** baad safai mein hat sakti hain. Footage jaldi dekh lo.

# Real World Example (this repo)
`git reflog --date=iso -n 4` in `/home/tech/umesh-personal`, unedited:

```
42a2ecc4 HEAD@{2026-08-03 14:32:13 +0530}: commit: chore(repo): stop tracking database dumps + node_modules; teach why in the course
83a144ba HEAD@{2026-08-03 13:21:32 +0530}: pull upstream main: Fast-forward
7fe2bb0e HEAD@{2026-08-03 12:46:54 +0530}: commit: feat: accountant read tier, student role, learning platform completion, UTC date-class fix
af01b9e7 HEAD@{2026-07-24 15:21:12 +0530}: commit: test(production): pin F-4 roster-picker guarantee on generic_stage path
```

- **The operation is named, not just the commit.** `pull upstream main: Fast-forward` is how `83a144ba` — the merge of **PR #15** (`new_flask_app` → `main`) — arrived locally. `git log` cannot tell you that.
- **A real reset is on the record.** `HEAD@{21}` reads `63d26ee2 HEAD@{21}: reset: moving to HEAD`, and `git show --stat 63d26ee2` *still* prints its diff today: 1 file changed, 14 insertions, 8 deletions.
- **`.git/ORIG_HEAD`** = `7fe2bb0e…`, where HEAD was before that pull. Git writes it before `merge`/`rebase`/`reset`/`pull`, so `git reset --hard ORIG_HEAD` is a one-word undo — but it holds only the *last* value. And **`.git/lost-found/`** holds **11** commit objects and **261** others from an earlier `git fsck --lost-found`.

# Visual Diagram
```
BEFORE  git reset --hard HEAD~3          new_flask_app ─┐
                                                        ▼
   A ─── B ─── C ─── D ─── E ─── F ─── G            (HEAD)

AFTER   (git printed almost nothing)
              new_flask_app ─┐
                             ▼
   A ─── B ─── C ─── D   ·   E ─── F ─── G   ← STILL IN .git/objects
                       (HEAD)     no branch → invisible to `git log`
                                            → but NAMED by the reflog:
   .git/logs/HEAD   (append-only, 276 lines here)
   ┌────────────────────────────────────────────────────────┐
   │ G_hash  D_hash  umesh  1785747733  reset: moving to …  │ @{0}
   │ F_hash  G_hash  umesh  …           commit: …           │ @{1}
   └────────────────────────────────────────────────────────┘
             ▲ the OLD-hash column is the rescue rope

RECOVER   git switch -c rescue/x 'HEAD@{1}'  → a ref points at G again.
DEADLINE  30d unreachable / 90d reachable. Reflog is LOCAL — never
          pushed, never cloned. NOT a backup.
```

# Practical — the recovery drills
Recovery commands are safe to run. Destructive ones are shown and **not run**.

```bash
git reflog -n 20                 # last 20 HEAD moves, newest first
git reflog --date=iso -n 20      # real timestamps instead of @{0}
git log -g --oneline -n 5        # same data as commits (takes log flags)
```

**Recover from a bad reset** (damage: `git reset --hard HEAD~3`).
```bash
git reflog -n 5                              # find the line ABOVE the reset entry
git show 'HEAD@{1}' --stat                   # LOOK FIRST — is that your work?
git switch -c rescue/lost-work 'HEAD@{1}'    # safest: a NEW branch; nothing else moves
```
`switch -c` is purely additive — wrong entry? delete the branch, try another. `git reset --hard 'HEAD@{1}'` also works and is itself undoable via a fresh reflog entry, but why risk two moves.

**Recover a deleted branch, or undo a bad rebase.**
```bash
git branch -D feat/old-thing            # forced delete: removes the REF, not the commits
git reflog -n 40 | grep -i old-thing    # its last hash is still in the journal
git switch -c feat/old-thing 4d5e6f7    # re-create the ref
git fsck --no-reflogs --lost-found      # reflog already pruned? → .git/lost-found/
git rebase --abort                      # mid-rebase, always try this first
git reset --hard ORIG_HEAD              # after a bad merge/rebase/pull
```

# Production Walkthrough
1. **Work on a branch, never on `main`** — `CONTRIBUTING.md` §1 plus `git-hooks/pre-push`, which refuses `main`/`master` (tested: `main` BLOCKED, `master` BLOCKED, `feat/my-thing` ALLOWED). The 0-byte `main` reflog is the evidence: shared history never depends on one laptop's journal.
2. **Something goes wrong**, then **stop typing** — further commands don't destroy the entry you need, but they bury it.
3. **`git reflog --date=iso -n 20`** and read the *operation* column: `commit:` is your work, `reset:`/`rebase`/`merge` is the accident. Confirm with `git show 'HEAD@{n}' --stat`.
4. **`git switch -c rescue/<what> 'HEAD@{n}'`** — the commits have a ref again, off the 30-day clock. Cherry-pick what you need, delete the rescue branch, resume the normal flow (`CONTRIBUTING.md` §5).
5. **The real fix is upstream of all this: push early** — a pushed branch is a copy on another machine, and that, not the reflog, survives a dead laptop ([Ch 19](19_Push_Fetch_Pull.md)).

# Debugging Guide
| Symptom | Cause | Fix |
|---|---|---|
| Commits vanished after `reset --hard` | branch ref moved; objects untouched | `git reflog -n 20` → `git switch -c rescue 'HEAD@{n}'` |
| `git reflog show main` prints nothing | that branch never moved in this clone | use `git reflog` (HEAD's log) |
| `fatal: ambiguous argument 'HEAD@1'` | shell ate the braces | quote it: `git show 'HEAD@{1}'` |
| Reflog line exists, `git show` fails | pruned by a real GC after expiry | `git fsck --lost-found`; else gone |
| Deleted branch missing from `git branch -a` | ref deleted, commits dangling | `git reflog \| grep <name>` → `switch -c` |
| Unstaged edits gone | never became an object | unrecoverable — commit early |
| Dropped stash entry | `refs/stash` moved | `git fsck --unreachable \| grep commit` ([Ch 17](17_Stash_And_Worktrees.md)) |

# Performance Notes
- **Writing is free** — one append per ref move. **Reading is linear** in file size; 62,604 bytes / 276 lines here is instant. In a CI clone that moved HEAD 50,000 times, pipe through `head`/`grep`.
- **The real cost is disk, indirectly** — reflog entries keep objects reachable, so `gc` cannot compact them. This clone: **4,873** loose objects (26.19 MiB) + **25,975** packed (63.66 MiB), `.git` = **97 MB** for **2,407** tracked files. A deliberate trade: 97 MB is cheap against re-typing a day's work ([Ch 37](37_Large_Files_And_Performance.md)).
- **Don't trim the reflog to save space** — size comes from large blobs, not log lines.

# Security Considerations
- **The reflog defeats naive secret removal.** Commit `.env`, notice, `git commit --amend`. `git log` is clean — but the old commit *containing the secret* stays reachable via the reflog and present in `.git/objects` for 30–90 days, readable by anyone with filesystem access. Amending is not deletion ([Ch 33](33_Secrets_And_Leaks.md)).
- **The nuke, shown deliberately and not run:**
  ```bash
  git reflog expire --expire=now --expire-unreachable=now --all
  git gc --prune=now --aggressive
  ```
  It drops every reflog entry, then collects everything unreachable. **No undo — the one command here that truly destroys work**, including abandoned commits you wanted. Justified only right after a deliberate rewrite, with a verified copy elsewhere. (This repo shows a past rewrite: `.git/filter-repo/`, `already_ran` dated Jun 21 2025 — [Ch 34](34_Rewriting_History.md).)
- **A leaked secret must be rotated, not scrubbed.** Anything that reached a commit — even one you reset away — is compromised. Cleaning history reduces *future* exposure only.
- **It protects you, not the project.** The reflog is also a work diary (branch names, timestamps, your name and email), and is never pushed — so a commit that exists only in one laptop's journal has no redundancy.

# Architecture Decisions
- **Default expiry kept (90 / 30 days), not tuned** — the defaults are generous, and a shortened window is a foot-gun with no upside for a solo developer. `gc --prune=now` is in no routine here.
- **History deliberately *not* rewritten for the committed database dumps.** Two `pg_dump` files (`Django_app/myproject/mydb_backup_20250618.sql`, `..._20250620.sql`) sat in public history. Audited first: `socialaccount_socialapp` and `socialaccount_socialtoken` **empty** (no OAuth secret), no plaintext passwords, **2** hashes at `pbkdf2_sha256$1000000$…`, the primary account row carrying Django's *unusable password* marker (Google-login only), 2 expired sessions. Verdict **mild**. Commit **`42a2ecc4`** did the reachability fix instead — `git rm --cached` on **2,954** files, 331,748 deletions, files kept on disk, tree byte-identical — because a `git-filter-repo` force-push right after a merge was judged more risk than the exposure (0 forks, repo going private). **The reasoning went into the commit message so it is explicit, not folklore.** Reflog angle: a rewrite invalidates every local reflog and every clone's refs at once.
- **Prevention beat recovery.** Root cause was *scope*: `django_inventory/.gitignore:114` already ignored `db_backups/` — why the live ERP never leaked one — but a `.gitignore` guards only its own subtree, and this is a monorepo. The root `.gitignore` now blocks `*.sql`, `*.dump`, `*.sql.gz`, `db_backups/`, `backups/`, `node_modules/`, verified at 5 locations, with `git add -f` deliberately still working.
- **The client-side hook is the primary net for `main`,** because server-side branch protection is **paid on private repos** (`CONTRIBUTING.md` §2). Honest limit: hooks live in `.git/hooks/`, which git never clones.

# Best Practices
- **Look before you leap:** `git show 'HEAD@{n}' --stat` before any `reset`.
- **Recover onto a new branch** (`git switch -c rescue/x`), never by resetting the branch you're on.
- **Stop typing after an accident** — extra commands bury the entry you need.
- **Commit small and often, and push daily** — only committed work is recoverable, only pushed work survives the laptop.
- **Reach for `ORIG_HEAD`** after a bad merge/rebase/pull: one word, no counting.
- **Quote `@{…}`** in every shell, and never routinely run `gc --prune=now`.

# Beginner Mistakes
- **Believing `reset --hard` deleted the commits** → it moved a pointer. `git reflog` → `git switch -c rescue 'HEAD@{1}'`.
- **Confusing `HEAD@{2}` with `HEAD~2`** → you recover the wrong commit and blame the reflog. `~` walks parents; `@{}` walks your keystrokes.
- **Panicking and typing more commands** → the entry you need sinks. Read first.
- **Expecting uncommitted edits back** → no object was ever written. Unrecoverable.
- **Assuming a teammate can recover your work** → reflogs are never pushed. Push the branch.
- **Running `git gc --prune=now` to "clean up"** → the one command that really destroys abandoned work.
- **Treating `--amend` as deletion of a secret** → the pre-amend commit stays reachable for weeks. Rotate it.
- **Not quoting braces** → zsh sends `HEAD@1`; git reports an ambiguous argument.
- **Calling the reflog a backup** → local, laptop-bound, expiring.

# Interview Questions
- **Junior:** "What does `git reflog` show?" — A local, append-only journal of every time a ref moved on this machine: old hash, new hash, who, when, which operation, and a message. It recovers commits that a `reset`, a bad rebase, or a branch deletion made invisible to `git log`. It is per-clone and never pushed.

- **Mid:** "You ran `git reset --hard HEAD~3` and lost three commits. Recover them." — Nothing was deleted; only the branch ref moved. `git reflog -n 10`, find the entry immediately above the `reset: moving to` line, confirm with `git show 'HEAD@{1}' --stat`, then recover additively with `git switch -c rescue 'HEAD@{1}'` rather than resetting the current branch. For a merge/rebase/pull, `git reset --hard ORIG_HEAD` is the shortcut. Unreachable entries expire around 30 days by default, so notice quickly.

- **Senior:** "Why does reflog recovery work, and when does it stop working?" — Commits are immutable content-addressed objects; branches are refs holding a hash; `reset` rewrites a ref, not history. `gc` deletes an object only when it is unreachable from *any* ref **including reflog entries**, so a reflog line keeps abandoned commits alive. It stops working in four cases: work never committed; untracked/ignored files; 30d/90d expiry plus a real GC (or an explicit `reflog expire --expire=now --all` + `gc --prune=now`); and any machine but yours, since reflogs are never transferred. `git fsck --lost-found` is the fallback while objects still exist.

- **Staff:** "Design a recovery policy for a small team with no paid branch protection, and say where reflog fits." — Reflog is layer zero: free, automatic, local, ~30-day window, single-machine — never a policy on its own. Layer it: (1) a committed `pre-push` hook refusing `main`, with the honest gap that `.git/hooks/` is never cloned, so hook installation is onboarding step 1; (2) collaborators on **Read** access working from **forks** — server-side, free, and stronger than branch protection, because "you have no push at all" beats "you may push, but not there"; (3) CI as the visible merge gate; (4) push-early culture so every branch has an off-box copy; (5) off-site backups for what git does not hold. On rewriting history to remove a leak, decide with evidence — audit the contents first, then choose — and rotate the secret regardless.

### Why interviewers ask these — and the answer that separates levels

| Testing for | Weak answer | What lands |
|---|---|---|
| Refs vs objects, or memorised commands? | "reflog undoes a reset." | "`reset` moves a **ref**; commits are immutable objects. The reflog keeps the old hash, which keeps the object **reachable**, so `gc` won't collect it." |
| Do you know the limits, or oversell the net? | "Git never loses anything." | Name all four gaps: uncommitted work, untracked files, expiry (30/90 days) plus GC, and other machines — reflogs are never pushed. |
| Would you make it worse under pressure? | "I'd try another reset and see." | "Stop typing. Read `git reflog --date=iso`, confirm with `git show --stat`, recover **additively** with `git switch -c rescue`." |

**The killer follow-up:** *"You amended a commit to remove a leaked API key and `git log` is clean. Is the key gone?"* — No. The pre-amend commit is still reachable through the reflog and still in `.git/objects` for 30–90 days, so anyone with filesystem access can read it; a fresh clone won't have it, but that is luck, not safety. Rotate the key first, clean history second. "Yes, it's gone" means you have never looked inside `.git`.

# Revision Notes
- Reflog = **per-ref journal of pointer moves**, plain text in `.git/logs/`. Local; never pushed or cloned.
- Six fields: **old hash · new hash · who · when · operation · message**. The old hash is the rescue rope.
- **`HEAD~2` = graph** (parents). **`HEAD@{2}` = time** (reflog). Unrelated. Quote the braces.
- `reset` moves a ref; commits are immutable. Invisible in `git log` ≠ deleted from `.git/objects`.
- Recovery, safest first: `git switch -c rescue 'HEAD@{n}'` › `git reset --hard ORIG_HEAD` › `git fsck --lost-found`.
- Windows **90d / 30d**. Cannot recover: uncommitted edits · untracked files · post-expiry+GC · another machine.
- ⚠️ `git reflog expire --expire=now --all && git gc --prune=now` is the **one truly destructive** command here.

# Cheat Sheet
- **Look:** `git reflog -n 20` · `git reflog --date=iso -n 20` · `git reflog show <branch>` · `git log -g --oneline`
- **Inspect first:** `git show 'HEAD@{3}' --stat` · `git diff 'HEAD@{1}' HEAD`
- **Time syntax (quoted):** `HEAD@{5}` · `HEAD@{2.hours.ago}` · `main@{yesterday}`
- **Recover:** `git switch -c rescue/x 'HEAD@{1}'` (safe) · `git reset --hard 'HEAD@{1}'` (blunt)
- **Undo merge/rebase/pull:** `git reset --hard ORIG_HEAD` · mid-rebase: `git rebase --abort`
- **Deleted branch:** `git reflog | grep <name>` → `git switch -c <name> <hash>`
- **Pruned:** `git fsck --no-reflogs --lost-found` · **dropped stash:** `git fsck --unreachable | grep commit`
- **☢️ Never routinely:** `git reflog expire --expire=now --all && git gc --prune=now`

# My ERP Section
| Concept | In this repo (measured 2026-08-03) |
|---|---|
| Git root | `/home/tech/umesh-personal` — monorepo; the Django ERP is `django_inventory/` |
| HEAD reflog | `.git/logs/HEAD` — **276** lines, 62,604 bytes |
| Branch reflogs | `new_flask_app` 62,286 bytes · `main` **0 bytes** (never moved locally) |
| `ORIG_HEAD` | `7fe2bb0e…`, set by the `pull upstream main: Fast-forward` |
| Recorded reset | `HEAD@{21}`: `63d26ee2 reset: moving to HEAD` — still shows a full diff today |
| Dangling objects | `.git/lost-found/` — **11** commits, **261** others, from an earlier `git fsck` |
| Object store | 4,873 loose + 25,975 packed; `.git` **97 MB**; 2,407 tracked files |
| `main` protection | `git-hooks/pre-push` refuses `main`/`master`; install with `bash git-hooks/install.sh` |
| Why local `main` is quiet | work on `new_flask_app`; `main` advances via PRs — **PR #15** landed at `83a144ba` |

# Practice Tasks
1. **Read the raw file:** `wc -l .git/logs/HEAD`, then `head -1 .git/logs/HEAD`. Name all six fields aloud and convert the Unix timestamp to a date.
2. **Prove the two axes differ:** run `git show --oneline -s HEAD~2` and `git show --oneline -s 'HEAD@{2}'`; explain in one sentence each why the commits differ.
3. **Prove nothing was deleted:** take the hash off a `reset:` line in `git reflog -n 40` and run `git show --stat <hash>`. Why does an abandoned commit still print a diff?
4. **Do the rescue drill safely:** `git switch -c scratch/reflog-drill`, make three tiny commits, `git reset --hard HEAD~3`, recover with `git switch -c rescue/drill 'HEAD@{1}'`, verify, delete both branches.
5. **Find the limit:** create a file, type into it, do **not** stage it, then `git restore <file>`. Try to recover it from the reflog and say why you cannot.

# Homework
- On a scratch branch, try to break your own recovery: reset, rebase, delete the branch, recover from each. Note which command you reached for first and whether it was the safest available.
- Read `CONTRIBUTING.md` §2 and §10. The reflog is your net on *your* branch — which layer is the net for `main`, and what is its written-down gap?
- Argue both sides in writing: for the two committed `pg_dump` files, was `git rm --cached` (`42a2ecc4`) right versus a `filter-repo` rewrite plus force-push? Use the audit findings, then say what would flip your answer.
- If your laptop died right now, which of your current work would survive, and where? Anything with no answer — push it.

---

# Further Reading & Live Resources
- Pro Git — *Data Recovery* (canonical reflog + `fsck` walkthrough): https://git-scm.com/book/en/v2/Git-Internals-Maintenance-and-Data-Recovery
- `git reflog` — *official reference*: https://git-scm.com/docs/git-reflog
- `gitrevisions(7)` — *the `@{…}` and `~`/`^` syntax, defined precisely*: https://git-scm.com/docs/gitrevisions
- `git gc` — *what pruning deletes, and the expiry settings*: https://git-scm.com/docs/git-gc
- *Oh Shit, Git!?!* — short recipes for panic moments, most of them reflog: https://ohshitgit.com/
