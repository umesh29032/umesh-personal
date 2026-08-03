---
id: git-course-13-rebase
type: lesson
status: active
owner: handwritten
scope: git, version control — replaying commits onto a new base, rebase vs merge, the golden rule of shared history
anchors: CONTRIBUTING.md, git-hooks/pre-push, git-hooks/commit-msg, .github/workflows/ci.yml
verified: 2026-08-03
---

# 13 — Rebase (re-recording your commits on top of someone else's work)

> Part of [Git Course](00_COURSE_OVERVIEW.md). Prev: [12 — Merge Conflicts](12_Merge_Conflicts.md). Next: [14 — Interactive Rebase](14_Interactive_Rebase.md).

# Learning Objectives
By the end of this chapter you can:
- explain why a rebase **copies** commits instead of moving them
- choose between `merge` and `rebase` with a reason, not a habit
- rebase onto `main`, resolve conflicts commit-by-commit, and finish with `--continue`
- undo any rebase with `--abort`, `ORIG_HEAD`, or the reflog
- state the golden rule, and push safely with `--force-with-lease`

# Purpose
Rebase is the command that makes junior developers freeze. Its reputation for "destroying history" is half-earned: it *does* rewrite history, but only the history you point it at, and every rewrite is recoverable for about 90 days. This chapter takes it apart until it is boring — what it does to objects, what it does to hashes, when it is right, and the exact recovery command for when it is not.

# The Problem
You branch off `main` on Monday and commit five times. Meanwhile three PRs land on `main`. Now your branch stands on a foundation nobody else has, your PR diff quietly includes *other people's* changes as "context", and CI tests a combination that will never ship. Merging `main` into your branch to catch up gives you a merge commit inside a feature branch — which `CONTRIBUTING.md` §10 forbids outright: *"No merge commits on feature branches. Rebase onto `main` to stay current."*

You need a way to say: **"pretend I started this work from today's `main`."** That is rebase.

# Theory (from zero)

### What a commit actually is
A commit is an immutable object holding four things: a **tree** (snapshot of every tracked file), one or more **parent** pointers (what came before), **metadata** (author, date, message), and its **hash** — a fingerprint computed over all of the above ([Ch 05](05_How_Git_Stores_Everything.md)).

That is the whole chapter. Because the parent is *inside* the thing being hashed, **changing a commit's parent necessarily produces a different hash — a different commit.** Git cannot move a commit onto a new base any more than you can move a brick already baked into a wall. It can only bake a new brick that looks the same.

Four words you need: **base** = the commit your branch was built on · **upstream** = the branch you want to be based on now (usually `main`) · **merge base** = the newest commit both branches share, i.e. where they diverged (`git merge-base main new_flask_app`) · **fast-forward** = your branch is already a straight-line ancestor of the target, so git just slides the pointer and creates nothing.

### What `git rebase main` really does
```
1. find the merge base of HEAD and main
2. collect every commit in (merge base .. HEAD]   — YOUR commits only
3. move HEAD to main's tip
4. for each collected commit, in order:
       apply its CHANGES (not its snapshot) on top of the new tip
       create a NEW commit — same message, same author, NEW parent, NEW hash
5. point your branch label at the last new commit
```
Step 4 is a tiny merge, once per commit. That is why rebase conflicts arrive **one commit at a time**, and why a ten-commit rebase can ask the same question ten times.

The originals are not deleted. They become **unreferenced** — no branch points at them — and sit in the object database until garbage collection prunes them (default: 90 days of reflog, [Ch 16](16_Reflog.md)). That is exactly why every rebase is undoable.

### The confusing bit: merge vs rebase
| | `git merge main` | `git rebase main` |
|---|---|---|
| Creates | one commit with **two parents** | **N copies**, one parent each |
| Your old hashes | unchanged | replaced |
| History shape | a visible fork and join | a straight line |
| Safe on branches others pulled | **yes** | **no** — it rewrites |
| PR diff | polluted with upstream changes | exactly your work |

Neither is "better". The house rule (`CONTRIBUTING.md` §5, §10) is **rebase feature branches, squash-merge at the PR**: rewrite where history is private and cheap; never rewrite the trunk. And note that plain `git pull` = `git fetch` + `git merge`, which is how branches collect "Merge branch 'main' of github.com:…" commits nobody wanted — fix it once with `git config --global pull.rebase true`. On this machine `git config --get pull.rebase` prints nothing (unset), so `git pull` here is still the merging kind.

### Conflicts, and the three exits
A conflict pauses the rebase mid-flight ([Ch 12](12_Merge_Conflicts.md) covers resolving them):
```bash
git rebase --continue   # I fixed it (git add first) — carry on with the next commit
git rebase --skip       # this commit's change is already upstream — drop it
git rebase --abort      # put everything back exactly as it was. ALWAYS available.
```
Memorise `--abort`. A paused rebase is not a broken repository; it is a repository waiting for one of three words. If the same conflict reappears on every attempt, enable **rerere** ("reuse recorded resolution") — git memorises your fix and replays it: `git config --global rerere.enabled true` (also unset here today).

### The golden rule
> **Never rebase commits that other people have already based work on.**

Not "never rebase pushed commits" — that sloppy version is wrong for the common case: rewriting *your own* pushed branch that nobody pulled is normal. The real test is *has someone built on it*. Rewriting `main` after twelve people pulled it means twelve divergent histories to reconcile by hand.

### Pushing after a rebase
Your branch and its remote copy now disagree about history, so a normal push is refused:
```bash
git push --force-with-lease   # refuse if the remote moved since my last fetch
git push --force              # BANNED here (CONTRIBUTING §10) — overwrites invisible work
```
`--force-with-lease` compares what you *think* the remote is against what it *is*; if a teammate pushed meanwhile it aborts instead of erasing them. Plain `--force` does not look.

> 💡 **Samjho aise:** Merge = do raaste milne pe ek **chowk** ban jaata hai — nakshe pe hamesha dikhega ki yahan do raaste mile the. Rebase = tumne apna raasta **dobara banaya**, aage se, taaki seedha lage — purana raasta mita nahi, sirf naam-patta hat gaya (90 din tak `reflog` mein padha hai). Niyam: **apni gali** dobara bana sakte ho, **main sadak** nahi — us pe aur log chal rahe hain.

# Real World Example (this repo)
PR **#15** merged `new_flask_app` into `main`. `git cat-file -p` prints a commit exactly as git stores it:

```bash
$ git cat-file -p 83a144ba | head -5
tree aa3a236e9a1756d2aaa3bc679cbb459277a88b56
parent fa9507d7d9a39c6de0c8506a87a03f65fd89c09d
parent 7fe2bb0e1b50b5bb2b669e51d9f92191909bae3e
author Umesh chaudhary <44035504+umesh29032@users.noreply.github.com> 1785743474 +0530
committer GitHub <noreply@github.com> 1785743474 +0530
```

**Two `parent` lines** — the entire definition of a merge commit, and the one thing a rebase never produces. Further down the same object sits a `gpgsig` header (GitHub signed it); a rebase across this commit would **not** carry that signature ([Ch 31](31_Signed_Commits.md)).

```bash
$ git reflog -2
42a2ecc4 HEAD@{0}: commit: chore(repo): stop tracking database dumps + node_modules; teach why in the course
83a144ba HEAD@{1}: pull upstream main: Fast-forward

$ git rev-list --count main..new_flask_app
296
```
`HEAD@{1}` is the honest one: pulling `upstream main` needed **no** merge and **no** rebase, because the branch was already a straight-line ancestor — fast-forward is the free case. And 296 is the price of the alternative: rebasing this branch would replay **296** commits, i.e. 296 chances to conflict. That number is the argument for short branches all by itself.

# Visual Diagram
```
BEFORE — you branched at C2, then main moved on          merge-base = C2
                              (main)
        C1 ── C2 ── C3 ── C4 ── C5
               \
                F1 ── F2 ── F3   (feat/my-thing, HEAD)

OPTION A: git merge main            OPTION B: git rebase main
   C1─C2─C3─C4─C5 ────────┐          C1─C2─C3─C4─C5  (main)
        \                  \                         \
         F1─F2─F3 ───────── M         F1'─F2'─F3'  (feat/my-thing)
                     (two parents)     ^ new hashes, same messages, one parent each
   the fork stays in history            F1,F2,F3 survive unreferenced (reflog ~90 days)

AFTER a rebase, main can fast-forward:  C5 ── F1' ── F2' ── F3'   (straight line)
UNDO: --abort (mid-rebase) · reset --hard ORIG_HEAD (after) · reflog (always)
```

# Practical — rebase a branch onto today's `main`, safely
Every step is reversible. Do it on a scratch branch first.
```bash
git branch backup/before-rebase          # free insurance: a label on where you are now
git fetch origin                         # fetch NEVER touches your files (Ch 19)
git rev-list --count origin/main..HEAD   # how many commits will be replayed
git rebase --autostash origin/main       # --autostash pockets uncommitted work, restores it after
```
Success prints `Successfully rebased and updated refs/heads/feat/my-thing.` A conflict prints:
```
CONFLICT (content): Merge conflict in django_inventory/config/expense/services/adda_settlement_service.py
error: could not apply 0d45427f... feat(production): super-admin Adda cancel
hint: Resolve all conflicts manually, mark them as resolved with
hint: "git add/rm <conflicted_files>", then run "git rebase --continue".
```
```bash
git add <the conflicted file> && git rebase --continue   # resolve ONE commit, move on
git rebase --abort                       # or bail out: exact pre-rebase state
```
Verify before pushing — a rebase can silently drop a commit:
```bash
git log --oneline origin/main..HEAD      # same subjects and count as before?
git diff backup/before-rebase            # MUST be empty: same tree, new history
env/bin/python config/manage.py test     # the battery: 2033 tests, ~424 s
git push --force-with-lease && git branch -D backup/before-rebase   # publish, then clean up
```

# Production Walkthrough
The real loop, from `CONTRIBUTING.md` §9 and §5:

1. **Start current:** `git fetch upstream && git switch main && git merge --ff-only upstream/main`. `--ff-only` *refuses* to invent a merge commit, so local `main` stays a byte-exact mirror; if it fails, `main` has drifted and should be reset to upstream, not merged.
2. **Branch and commit:** `git switch -c feat/accountant-read-tier` (one branch, one intent, §3), Conventional Commits form — `git-hooks/commit-msg` rejects messages that do not parse, subjects over 72 characters, and trailing periods ([Ch 25](25_Conventional_Commits.md)).
3. **Days pass, `main` moves.** Before the PR: `git fetch origin && git rebase origin/main`, then `git push --force-with-lease`. CI re-runs from scratch because the hashes are new; `.github/workflows/ci.yml` uses `concurrency` to cancel superseded runs so a double push does not burn two slices of the ~2000 free private-repo Actions minutes.
4. **Squash-merge** (§5), then delete the branch: one feature = one commit on `main`, so any feature reverts in one command ([Ch 15](15_Undo_Reset_Revert_Restore.md)). PR #15 preserves the irony — it landed as a *merge* commit with two parents; that was the older habit, and the rulebook now says squash.

One thing CI cannot re-check: `pre-commit` and `commit-msg` hooks do **not** run for commits replayed by a rebase — git treats them as already validated, so a rebase can quietly carry a message the hook would now reject.

# Debugging Guide
| Symptom | Cause | Fix |
|---|---|---|
| `cannot rebase: You have unstaged changes` | dirty working tree | `git rebase --autostash origin/main` ([Ch 17](17_Stash_And_Worktrees.md)) |
| Same conflict in commit after commit | each replay re-applies the same hunk | `rerere.enabled true`; or squash first ([Ch 14](14_Interactive_Rebase.md)) |
| `! [rejected] … (non-fast-forward)` on push | you rewrote history the remote still has | `git push --force-with-lease` — never plain `--force` |
| `stale info` from `--force-with-lease` | someone pushed to your branch since your fetch | `git fetch`, read their commits, then decide — the lease just saved you |
| Fewer commits after the rebase | a commit was already upstream, or you typed `--skip` | `git reset --hard ORIG_HEAD`, then redo carefully |
| "Rebase lost my commits" | the label moved; commits are unreferenced, not deleted | `git reflog` → `git reset --hard HEAD@{n}`, or `git branch rescue <hash>` |
| Signature or merge topology gone | rebase re-creates commits and flattens by default | `rebase.gpgSign true`; `git rebase --rebase-merges` |

# Performance Notes
- Cost is roughly **linear in commits replayed**, and each replay is a three-way merge. Rebasing `new_flask_app` = **296** replays. Three commits is instant; 296 is an afternoon.
- The expensive part is *human*: conflict resolution. `rerere` makes the second and third occurrence cost zero seconds.
- Rebase writes objects, never deletes them. `.git` here is **97 MB**; `git count-objects -vH` reports `count: 4873` loose objects and `size-pack: 63.66 MiB` across 2 packs. Heavy rebasing inflates the loose count until `gc` runs ([Ch 37](37_Large_Files_And_Performance.md)).
- Free-plan CI cost: every force-push re-runs the ~7-minute battery, which is why `concurrency` cancellation matters. `--onto` keeps replay counts small.

# Security Considerations
- **A rebase can delete a commit without saying so.** `--skip` on the wrong commit drops a security fix silently, and a force-push takes the audit trail with it. Always `git diff` the result against your backup label — it must be empty.
- **Force-push is the real weapon, not rebase.** `--force` on a shared branch destroys commits nobody else has copies of; §10 bans it in favour of `--force-with-lease` on your own branches only.
- **Rebasing does not remove a leaked secret** unless the commit's *content* changes — replaying a commit containing an API key produces a new commit containing the same key ([Ch 33](33_Secrets_And_Leaks.md), [Ch 34](34_Rewriting_History.md)). Signatures also do not survive, and hooks are skipped: `83a144ba` carries a `gpgsig` header, a rebase across it yields unsigned children, and `git-hooks/commit-msg` never sees replayed messages.
- **`git-hooks/pre-push` is the last line:** it refuses `main`/`master` (tested: `main` BLOCKED, `master` BLOCKED, `feat/my-thing` ALLOWED), which is what stops a force-push landing on the trunk — but only on machines where `bash git-hooks/install.sh` was run, because git never clones `.git/hooks/`. `CONTRIBUTING.md` §2 writes that gap down rather than hiding it.

# Architecture Decisions
- **Feature branches rebase; the trunk never does** (§10). Private history is cheap to rewrite; `main` is not.
- **Squash-merge at the PR** (§5), not rebase-merge: one commit per feature makes `git revert <sha>` a complete rollback — the property that matters most where settlement is the only money-write boundary.
- **`--ff-only` when syncing `main`** (§9): refusing to invent a merge turns "my main drifted" from a silent mess into a loud error.
- **Rejected: `git-flow`** with long-lived release branches — heavier than a 1–2 person team can justify (§10). Trunk + short branches + tags. **Rejected: plain `--force`** anywhere; the lease costs one word.
- **Rejected: rewriting the published dump history.** When two `pg_dump` files were found in public history, the fix was `git rm --cached` in commit `42a2ecc4` — moving *forward*, not a `git-filter-repo` rewrite. With 0 forks and nothing usable inside, a force-push right after a merge was judged the bigger risk, and that reasoning went into the commit message.

# Best Practices
- Rebase **before** opening the PR, and again if review takes days.
- Keep branches small — commit count *is* the rebase cost.
- `git branch backup/x` before any rebase you are unsure about, and `git diff backup/x` after. Empty diff = the tree survived.
- `git push --force-with-lease`, never `--force`. Never rebase `main` or anything a colleague pulled.
- Set `pull.rebase true` and `rerere.enabled true` once, globally, then forget them; use `--autostash` instead of remembering to stash.
- `--abort` early when a rebase goes badly; nothing is lost by restarting.

# Beginner Mistakes
- **`git pull` on a feature branch, repeatedly** → the branch collects "Merge branch 'main' into feat/x" commits and the PR diff becomes unreadable. Use `git pull --rebase`.
- **Rebasing `main` itself** → every collaborator's history diverges from yours. Only rebase branches nobody built on.
- **Panicking mid-conflict and deleting the repo folder** → total loss. `git rebase --abort` restores the exact pre-rebase state.
- **`git push --force`** → overwrites commits you cannot see. `--force-with-lease` refuses when the remote moved.
- **Assuming rebase deleted the old commits** → it did not; `git reflog` lists them for ~90 days.
- **`git rebase --skip` to make a conflict go away** → you just discarded a whole commit. Skip only when the change is already upstream.
- **Rebasing a 296-commit branch** → 296 conflict opportunities. Squash first ([Ch 14](14_Interactive_Rebase.md)) or use `--onto`.
- **Trusting "Successfully rebased" without checking** → verify with `git log --oneline origin/main..HEAD` and an empty diff against the backup label.

# Interview Questions
- **Junior:** "What is the difference between merge and rebase?" — Merge creates one new commit with **two parents**, keeps the fork visible, and leaves existing commits untouched. Rebase replays my commits on top of the target as **new commits with new hashes**, producing a straight line. Merge is safe on shared branches; rebase rewrites history, so it is for private branches.

- **Mid:** "Your branch is five commits behind main and review starts tomorrow. Walk me through it." — `git fetch origin`, `git branch backup/x` for insurance, then `git rebase origin/main`. Conflicts arrive per commit: fix, `git add`, `--continue`; `--abort` puts everything back. Then check `git diff backup/x` is empty, run the battery, and `git push --force-with-lease`. The PR diff is then only my work.

- **Senior:** "Why does a rebase change commit hashes, and what does that imply operationally?" — The hash covers tree, parents, metadata and message, so re-parenting forces a new hash; the originals become unreferenced, not deleted. Operationally: the remote refuses a normal push (`--force-with-lease` needed), CI must re-run, GPG signatures are lost unless re-signed, `pre-commit`/`commit-msg` hooks are skipped on replay, and anyone who pulled the old commits now has divergent history — which is where the golden rule draws its line. Recovery is `ORIG_HEAD` or the reflog for ~90 days.

- **Staff:** "Set the history policy for a two-person team on a money-handling monorepo, and defend it." — Trunk-based: `main` always deployable, short-lived `<type>/<kebab>` branches, rebase onto `main` to stay current, **squash-merge** at the PR so `main` is one commit per feature and `git revert <sha>` is a complete rollback of anything touching settlement. Ban plain `--force`; `--force-with-lease` on own branches only; sync `main` with `--ff-only` so drift is an error. Enforcement is layered because server-side branch protection is paid on private repos: a `pre-push` hook refusing `main` (free, but only where installed — a written-down gap), collaborators on **Read** access working from forks so they have no push permission at all (server-side, free, and stronger than branch protection), and CI as the visible merge gate. Reject `git-flow` — long-lived release branches cost more coordination than two people can pay. The invariant: one `git revert` restores a known-good state.

### Why interviewers ask these — and the answer that separates levels

| Testing for | Weak answer | What lands |
|---|---|---|
| Do you know commits are immutable? | "Rebase moves my commits onto main." | Rebase **copies** — the parent is part of the hash, so a new parent means a new commit; originals go unreferenced and the reflog keeps them ~90 days. |
| Do you know when NOT to rebase? | "Rebase is cleaner, so always rebase." | The golden rule's real boundary: rewrite only history nobody has built on; my own pushed branch is fine, `main` never is. |
| Do you have a recovery reflex? | "I'd try to fix the conflicts." | `--abort` mid-flight, `reset --hard ORIG_HEAD` after, reflog always — plus a backup branch and an empty verification diff before pushing. |
| Do you understand force-push risk? | "I force-push after rebasing." | `--force-with-lease` refuses if the remote moved since my last fetch, so a teammate's commits cannot be silently erased. |

**The killer follow-up:** *"You rebased, force-pushed, and a teammate says their two commits are gone. What now?"* — Do not re-clone. Their local clone is untouched, so recover from their `git reflog` with `git branch rescue <hash>`; on your side `ORIG_HEAD` holds the pre-rebase tip. Then fix the cause — `--force-with-lease` would have refused that push, and a branch someone else had pulled should never have been rebased.

# Revision Notes
- Rebase **copies** commits with new parents ⇒ **new hashes**. It never moves them.
- Merge = one commit, **two parents**. Proof: `git cat-file -p 83a144ba` shows two `parent` lines.
- Conflicts come **one commit at a time**. Three exits: `--continue`, `--skip`, `--abort`.
- Golden rule: rewrite only history **nobody has built on**. Never `main`.
- Undo: `--abort` (during) · `reset --hard ORIG_HEAD` (after) · `git reflog` (always, ~90 days).
- Push with **`--force-with-lease`**; plain `--force` is banned by `CONTRIBUTING.md` §10.
- Rebase runs **no** `pre-commit`/`commit-msg` hooks and keeps **no** GPG signature.
- 296 commits on `new_flask_app` = 296 replays. Short branches *are* a rebase strategy.

# Cheat Sheet
- **Where did we diverge:** `git merge-base main HEAD` · **how many:** `git rev-list --count origin/main..HEAD`
- **Rebase onto latest:** `git fetch origin && git rebase --autostash origin/main`
- **Mid-rebase:** `git add <file>` → `--continue` · drop this commit `--skip` · **undo all** `--abort`
- **Undo a finished rebase:** `git reset --hard ORIG_HEAD` · or `git reflog` → `git reset --hard HEAD@{n}`
- **Insurance:** `git branch backup/x` before · `git diff backup/x` after (must be empty)
- **Last 3 commits only:** `git rebase --onto origin/main HEAD~3` · **keep merges:** `--rebase-merges`
- **Push:** `git push --force-with-lease` — **never** `git push --force`
- **Set once:** `git config --global pull.rebase true` · `git config --global rerere.enabled true`

# My ERP Section
| Concept | In this repo |
|---|---|
| Rulebook | `CONTRIBUTING.md` §10 — "No merge commits on feature branches. Rebase onto `main`." |
| Force policy | `--force-with-lease` on your own branch only; plain `--force` banned (§10) |
| Trunk sync / merge style | `git merge --ff-only upstream/main` (§9); **squash-merge** at the PR (§5) |
| Real merge commit | `83a144ba` (PR #15, `new_flask_app` → `main`) — two parents, GPG-signed by GitHub |
| Real fast-forward | reflog `HEAD@{1}: pull upstream main: Fast-forward` |
| Rebase cost here | `git rev-list --count main..new_flask_app` = **296** commits to replay |
| Repo weight | `.git` = **97 MB**; `count-objects -vH`: 4873 loose, `size-pack: 63.66 MiB` |
| Push guard | `git-hooks/pre-push` blocks `main`/`master`; install via `bash git-hooks/install.sh` |
| CI gate | `.github/workflows/ci.yml` — lint · migrations · test (2033 tests, ~424 s) · docs |
| Config gap today | `pull.rebase` and `rerere.enabled` are both **unset** on this machine |

# Practice Tasks
1. **Read the object.** `git cat-file -p 83a144ba | head -5` — point at the evidence that this is a merge. Then run it on `7fe2bb0e` and count the `parent` lines.
2. **Measure.** `git merge-base main new_flask_app` and `git rev-list --count main..new_flask_app`. Explain in one sentence why the second number is the rebase cost.
3. **Do it safely.** `git switch -c practice/rebase`, three tiny commits, rebase onto `main`, then prove with `git diff` against a backup branch that only the hashes changed.
4. **Break it on purpose.** Cause a conflict during that rebase, recover with `--abort`, and confirm with `git log --oneline -3`. Then redo it, finish it, and undo the finished rebase with `git reset --hard ORIG_HEAD`.

# Homework
- Read `CONTRIBUTING.md` §9 and §10 and write, in your own words, why `--ff-only` is used for `main` but rebase for feature branches.
- PR #15 landed as a merge commit while §5 mandates squash-merge. Argue both styles in a paragraph each, then say which you would enforce and how.
- Rebase a practice branch, then check whether `git-hooks/commit-msg` validated the replayed messages. What does that tell you about where message discipline actually lives?
- A teammate pulls your branch to test it; you then rebase and force-push. Write the exact recovery instructions you would send them.

---

# Further Reading & Live Resources
- Pro Git — *Rebasing* (canonical, including the perils section): https://git-scm.com/book/en/v2/Git-Branching-Rebasing
- `git rebase` reference — every flag, `--onto`, `--rebase-merges`: https://git-scm.com/docs/git-rebase
- `git rerere` — reuse recorded resolution: https://git-scm.com/docs/git-rerere
- Atlassian — *Merging vs Rebasing* (good diagrams, opinionated): https://www.atlassian.com/git/tutorials/merging-vs-rebasing
- Pro Git — *Data Recovery* (why nothing is really gone): https://git-scm.com/book/en/v2/Git-Internals-Maintenance-and-Data-Recovery
