---
id: git-course-34-rewriting-history
type: lesson
status: active
owner: handwritten
scope: git — amend, rebase, filter-repo, force-with-lease; the cost and the decision to rewrite
anchors: .git/refs, CONTRIBUTING.md, git-hooks/pre-push
verified: 2026-08-03
---

# 34 — Rewriting History Safely (and when the answer is "don't")

> Part of [Git Course](00_COURSE_OVERVIEW.md). Prev: [33 — Secrets & Leaks](33_Secrets_And_Leaks.md). Next: [35 — Bisect](35_Bisect.md).

# Learning Objectives
By the end of this chapter you can:
- explain what "rewriting history" mechanically is, in terms of hashes
- name the four tools by blast radius, from `--amend` to `filter-repo`
- explain why `--force-with-lease` is safe where `--force` is not
- use `git filter-repo` to remove a file from all history, and say what it does **not** achieve
- decide whether a rewrite is worth its cost, and defend either answer
- recover from someone else's force-push

# Purpose
Rewriting history is the most feared operation in git, and the fear is misdirected. The danger is not
that you will lose your work — [reflog](16_Reflog.md) makes that nearly impossible locally. The danger
is that you will **invalidate everyone else's copy**.

This chapter separates the two. Rewriting your *own* unpushed branch is routine and safe, and you
should do it often to produce a reviewable history. Rewriting *shared* history is a coordination
problem disguised as a git command.

And most importantly: this chapter argues that the correct answer is frequently **"do not rewrite"**,
using a real decision from this repository where a rewrite was considered, costed, and declined.

# The Problem
Four situations, escalating:

1. Your last commit message has a typo. Trivial — but the fix technically rewrites history.
2. Your branch has eight `wip` commits and you want one clean commit before review.
3. You accidentally committed a 200 MB file forty commits ago and the repo is now painful to clone.
4. A secret is in history and you have been asked to remove it.

All four are "rewriting history", but their **blast radius** differs by orders of magnitude. Treating
them identically is how people either fear `--amend` unnecessarily or force-push a shared branch
carelessly.

# Theory (from zero)

### What rewriting mechanically is
A commit's hash is computed over its whole content, **including its parent's hash**
([Chapter 05](05_How_Git_Stores_Everything.md)). So changing anything — the message, the author, the
tree, the parent — produces a **different commit object**. Objects are immutable; nothing is edited.

Which gives the one fact that explains everything else:

> **Rewriting history means creating new commits and abandoning the old ones. And because each commit
> names its parent, changing one commit changes every descendant's hash too.**

Rewrite commit #40 of 100 and you have replaced sixty-one commits. The originals still exist,
unreferenced, until garbage collection — which is why *your* recovery is easy and *everyone else's*
situation is not: their refs still point at the hashes you abandoned.

### The four tools, by blast radius
| Tool | Rewrites | Blast radius | Force-push? |
|---|---|---|---|
| `git commit --amend` | the last commit only | 1 commit | only if already pushed |
| `git rebase -i` | a range you choose | those commits + descendants | yes, if pushed |
| `git rebase <base>` | your branch onto a new base | your branch | yes, if pushed |
| **`git filter-repo`** | **all of history** | **everything, all branches, all tags** | **always** |

Reach for the smallest tool that solves the problem. `filter-repo` for a typo is like demolition for
a stuck door.

### `--amend`: the safe one
```bash
git commit --amend -m "fix: better message"      # replaces the last commit
git commit --amend --no-edit                     # add staged changes, keep the message
git commit --amend --reset-author                # fix a wrong author (ch 02)
```

Safe **if you have not pushed**. Check first:

```bash
git status                # "Your branch is up to date with 'origin/x'" ⇒ pushed
git log origin/HEAD..HEAD # commits that exist only locally = safe to rewrite
```

That second command is the general test for "is this safe to rewrite": anything in
`origin/<branch>..HEAD` is yours alone.

### `rebase -i`: the workhorse
Covered fully in [Chapter 14](14_Interactive_Rebase.md). The point here is that squashing `wip`
commits before review is a rewrite you should perform **routinely** — on your own branch, before
anyone builds on it.

### `filter-repo`: the demolition tool
For removing a file from **all** history — the only tool that solves problems 3 and 4.

```bash
pip install git-filter-repo

# remove a path from every commit, every branch, every tag
git filter-repo --invert-paths --path Django_app/myproject/mydb_backup_20250620.sql

# or by pattern
git filter-repo --invert-paths --path-glob '*.sql'

# replace secret STRINGS while keeping the files
git filter-repo --replace-text expressions.txt
```

Three things to know before you run it:

1. **It refuses to run on a repo with uncommitted changes or on a non-fresh clone** by default. That
   is deliberate: the recommended workflow is a fresh clone precisely so a mistake costs you nothing.
2. **It removes your remotes** afterwards, on purpose, so you cannot reflexively push.
3. **`git filter-branch` is deprecated.** Git's own documentation now recommends `filter-repo`;
   `filter-branch` is slow and has data-mangling footguns. Ignore any tutorial that still uses it.

### `--force` versus `--force-with-lease`
```bash
git push --force               # "make the remote match me, whatever is there"   ← DANGEROUS
git push --force-with-lease    # "...but ONLY if the remote is still where I last saw it"
```

`--force-with-lease` compares the remote's current value against your remote-tracking ref. If a
colleague pushed since your last fetch, it **refuses** instead of destroying their commit.

The subtlety worth knowing: a plain `git fetch` updates your remote-tracking ref, which *renews the
lease*. So `git fetch && git push --force-with-lease` is close to `--force` in effect. If you want
the protection, inspect the fetched state before pushing.

**Use `--force-with-lease` always.** There is no situation where plain `--force` is better; there are
many where it silently destroys work.

### The real cost of rewriting shared history
| Consequence | Detail |
|---|---|
| Every clone is broken | `git pull` produces a mess; everyone must reset or re-clone |
| Every fork diverges | forks keep the old hashes; PRs from them may become unmergeable |
| Tags may dangle | annotated tags point at old commits unless rewritten too |
| Deploy references break | anything pinned to an old SHA — CI configs, runbooks, changelogs |
| **The secret is still out** | anyone who cloned already has it; other remotes are untouched |
| Reviews lose their anchor | PR comments reference lines in commits that no longer exist |

The fifth row is the one that decides most secret-removal debates. If the goal was "make the secret
inaccessible", a rewrite does not achieve it — which is why **rotation** is step 1 and a rewrite is at
best step 4 ([Chapter 33](33_Secrets_And_Leaks.md)).

### The decision framework
**Rewrite when:**
- a large file makes the repository genuinely painful, and nobody has meaningful work in flight
- a legal or compliance obligation requires removal
- the repository is effectively private with no forks and few clones, so coordination is cheap
- the secret **cannot** be rotated (usually means it is someone else's credential)

**Do not rewrite when:**
- the credential has been rotated and the old value is worthless
- the exposure is audited and mild
- many people have clones or forks
- the disruption exceeds the residual risk

Both are professional answers. Choosing without evidence is not, and neither is choosing and failing
to write down why.

> 💡 **Samjho aise:** History "badalna" asal mein **badalna nahi hai** — **nayi commit banana** hai,
> aur purani ko chhod dena. Aur kyunki har commit apne baap ka naam apne andar rakhti hai, ek commit
> badli toh **uske baad ki saari** badal gayi. 100 mein se 40vi badli? 61 nayi ban gayi.
>
> Isliye khud ki, **bina push ki** branch dobara likhna aaram se karo — accha review isi se banta hai.
> Par doosron ki branch? Wo git ka sawaal nahi, **logon ke saath taal-mel** ka sawaal hai: unke paas
> purane pate hain, unka clone toot jaayega.
>
> Aur sabse badi baat: secret hatane ke liye rewrite karna **secret ko safe nahi karta**. Jisne clone
> kar liya, uske paas hai. Isliye **pehle password badlo** — rewrite baad ki baat hai, aur kai baar
> zaroori bhi nahi.

# Real World Example (this repo)
This repository faced the decision for real on 2026-08-03, and **declined the rewrite**. The reasoning
is worth reading as a template, because it is the case most tutorials never show.

**The situation.** Two PostgreSQL dumps sat in history while the repository was public
([Chapter 33](33_Secrets_And_Leaks.md)). The obvious move was `filter-repo` plus a force-push.

**The evidence gathered first:**

| Factor | Finding |
|---|---|
| Is the credential still usable? | **No** — `pbkdf2_sha256$1000000$` hashes (2 of them); the primary account had `!OUUm8Nk…`, Django's *unusable password* marker |
| OAuth secrets or tokens? | **None** — `socialaccount_socialapp` and `socialaccount_socialtoken` both empty |
| Who could have cloned it? | **0 forks, 0 stars, 0 watchers** |
| Repository going private? | **Yes** |
| Timing | PR #15 had **just** merged — a force-push would land on top of a fresh merge |

**The decision, recorded verbatim in the commit message:**

> *"History is deliberately NOT rewritten. The dumps remain in earlier commits. With 0 forks, the
> repository going private, and nothing usable inside, a git-filter-repo force-push is more risk than
> the exposure warrants. Recorded here so the decision is explicit rather than forgotten."*

**Why that is the right call.** A rewrite here would have bought: removal of an unusable hash from one
remote. It would have cost: new hashes for 289 commits' worth of history, a force-push immediately
after a merge, and every future reader wondering why the SHAs in the release log no longer resolve.
The exposure was audited; the disruption was not hypothetical.

**What was done instead** — containment, which is the cheaper and more durable half:

```bash
git rm --cached <2954 paths>      # untrack; files stay on disk
# + a monorepo-root .gitignore blocking *.sql, *.dump, db_backups/, node_modules/
```

**2,954 files** untracked, 331,748 deletions, **0 bytes lost on disk**, and the rule verified as
blocking at five separate paths. The class of bug was closed; the historical instance was accepted,
knowingly.

**And the honest counterpoint.** Had those tables contained a live OAuth client secret, the answer
would have flipped — a rewrite plus rotation, immediately, because an unrotatable third-party
credential is exactly the case where removal has value.

**Smaller rewrites do happen here, routinely.** `CONTRIBUTING.md` §10 permits `--force-with-lease` on
your own branch and forbids plain `--force` on anything shared. Squashing before review is standard;
the project squash-merges every PR, which is itself a rewrite performed by GitHub at merge time
([Chapter 21](21_Pull_Requests.md)).

# Visual Diagram
```
  WHY ONE CHANGE CASCADES
  ───────────────────────
   before:  A ◄─ B ◄─ C ◄─ D          (hashes: a1, b2, c3, d4)
   amend B ──►  A ◄─ B' ◄─ C' ◄─ D'   (hashes: a1, b9, c8, d7)
                     ▲
       B's hash changed ⇒ C's parent changed ⇒ C's hash changed ⇒ …
       ALL DESCENDANTS ARE NEW COMMITS. Originals linger, unreferenced.

  BLAST RADIUS — pick the smallest tool
  ─────────────────────────────────────
   git commit --amend      1 commit           safe if unpushed
   git rebase -i <base>    a chosen range     force-push if pushed
   git rebase <base>       your branch        force-push if pushed
   git filter-repo         ALL history,       ALWAYS force-push
                           all branches+tags   + everyone re-clones

  IS IT SAFE TO REWRITE?
  ──────────────────────
   git log origin/<branch>..HEAD     ← anything listed is YOURS ALONE ⇒ safe

  --force  vs  --force-with-lease
  ───────────────────────────────
   --force            : "match me, whatever is there"      ← can delete a colleague's push
   --force-with-lease : "...only if remote == what I last fetched"  ← REFUSES instead
   caveat: `git fetch` RENEWS the lease. Inspect before pushing.

  THE DECISION THIS REPO MADE
  ───────────────────────────
   rewrite would BUY : removing an unusable hash from ONE remote
   rewrite would COST: 289 commits re-hashed · force-push onto a fresh merge
                       · every SHA reference broken
   evidence          : 0 forks · going private · hashes at 1,000,000 iterations
                       · OAuth tables EMPTY · primary account has NO password
   ⇒ DECLINED, and written into the commit message.
   ⇒ Contained instead: 2,954 files untracked + root .gitignore (5 paths verified)
```

# Practical — rewrite safely, at each scale
```bash
# ── 0. THE SAFETY QUESTION, always first ────────────────────────────────────
git log origin/HEAD..HEAD --oneline    # only these are yours alone
git status                             # "up to date with origin/x" ⇒ already pushed

# ── 1. AMEND — smallest tool ────────────────────────────────────────────────
git commit --amend -m "fix(expense): correct entry_date to IST"
git commit --amend --no-edit           # fold staged changes in, keep the message
git log --oneline -1                   # note the NEW hash — proof it is a new commit

# ── 2. INTERACTIVE REBASE — squash before review ────────────────────────────
git rebase -i origin/main              # pick/squash/reword/drop (ch 14)
git rebase --abort                     # bail out at any point, no harm done

# ── 3. FILTER-REPO — all history. Do it on a FRESH CLONE. ───────────────────
pip install git-filter-repo
git clone --no-local /path/to/repo /tmp/rewrite-work    # work on a copy!
cd /tmp/rewrite-work
git filter-repo --invert-paths --path path/to/secret.sql --dry-run   # inspect first
git filter-repo --invert-paths --path path/to/secret.sql
git log --all --oneline -- path/to/secret.sql          # empty = gone from history
# filter-repo REMOVES your remotes on purpose; re-add deliberately:
git remote add origin git@github.com:you/repo.git
git push --force-with-lease --all
git push --force-with-lease --tags

# ── 4. LOCAL CLEANUP after a rewrite (reclaim space) ────────────────────────
git reflog expire --expire=now --all
git gc --prune=now --aggressive
git count-objects -vH                  # before/after comparison

# ── 5. RECOVERY — someone force-pushed and you lost commits ─────────────────
git reflog                             # your local history of where HEAD was
git reset --hard HEAD@{2}              # back to before the damage
git fsck --lost-found                  # unreferenced commits, if reflog is gone
```

Step 3's `git clone --no-local` is the habit that matters: `filter-repo` on a copy means a mistake
costs you nothing. Running it on your only clone is how people lose an afternoon.

# Production Walkthrough
Rewriting a shared branch is a **coordination** procedure, not a command:

1. **Decide with evidence.** Blast radius versus benefit, written down.
2. **Tell everyone before you push.** A force-push nobody expects is how work gets lost.
3. **Work on a fresh clone** (`git clone --no-local`) so the original is untouched.
4. **`--dry-run` first.** `filter-repo` will tell you what it would change.
5. **Verify the removal**: `git log --all --oneline -- <path>` must be empty.
6. **Rewrite the tags too**, or your releases point at commits that no longer exist.
7. **Push with `--force-with-lease --all --tags`.**
8. **Everyone else re-clones.** Not `git pull` — that merges the old history back in. A fresh clone is
   simpler than teaching six people to reset correctly.
9. **Update anything pinned to a SHA**: CI configs, runbooks, changelogs, release notes.
10. **Rotate the secret anyway** if that was the motivation, because clones already exist.

For this project, steps 2 and 8 are cheap — one developer, zero forks — which is precisely what would
have made a rewrite *feasible* here. It was declined on value, not on difficulty.

# Debugging Guide

| Symptom | Cause | Fix |
|---|---|---|
| `! [rejected] ... non-fast-forward` | remote has commits you lack | `git fetch`, inspect, rebase — **not** blind `--force` |
| `--force-with-lease` rejected | remote moved since your last fetch | `git fetch`, review what changed, then retry |
| Force-pushed and lost a colleague's commit | plain `--force` | their `reflog` has it; or `git fsck --lost-found` on any clone |
| `filter-repo` refuses to run | uncommitted changes, or not a fresh clone | commit/stash; use `git clone --no-local`; `--force` only if you understand why |
| Repo size unchanged after `filter-repo` | reflogs and packed objects still reference old commits | `git reflog expire --expire=now --all && git gc --prune=now` |
| File still in history after a rewrite | it exists under another path or in another ref | `git log --all --oneline -- '*name*'`; check tags |
| Tags point at missing commits | tags were not rewritten | `filter-repo` handles them; verify with `git tag -l` + `git show` |
| Colleagues have a tangled history after your rewrite | they ran `git pull` | have them re-clone, or `git fetch && git reset --hard origin/<branch>` |
| Old PRs unmergeable | their base commits no longer exist | rebase the PR branches, or reopen from a fresh branch |
| "I lost everything" | almost never true | `git reflog`; then `git fsck --lost-found` |

# Performance Notes
- **`filter-repo` is fast for what it does** (Python, single pass) but it rewrites every commit — minutes
  on a large history. `filter-branch` was dramatically slower, one of several reasons it is deprecated.
- **Space is not reclaimed until gc.** Old objects survive in reflogs and packs; `reflog expire` plus
  `gc --prune=now` is what shrinks `.git`.
- **This repo:** `.git` is 97 MB with 25,975 packed objects in 2 packs. The dumps total ~86 KB — so a
  rewrite would have reclaimed effectively nothing. Size was never an argument here
  ([Chapter 37](37_Large_Files_And_Performance.md)).
- **Rebasing many commits costs a merge per commit**; conflicts multiply with range length. Short
  branches rebase in seconds.
- **`--force-with-lease` costs one extra ref comparison** — free, and there is no reason to omit it.
- A rewrite's real cost is **human**: everyone re-cloning, every SHA reference updated.

# Security Considerations
- **A rewrite does not un-publish a secret.** Existing clones and forks retain it, and the host may
  keep unreachable objects and PR refs. **Rotate first**
  ([Chapter 33](33_Secrets_And_Leaks.md)).
- **`--force` can destroy commits that were reviewed and approved**, and on a free private repo there
  is no server-side protection to stop it — which is why this project's `pre-push` hook and the
  `--force-with-lease` habit exist ([Chapter 27](27_Pre_Push_Protection.md)).
- **Rewriting invalidates signatures.** A signed commit's signature covers its content; produce a new
  commit and the signature must be regenerated ([Chapter 31](31_Signed_Commits.md)).
- **Audit trails break.** If history is your record of who changed what and when, rewriting it
  weakens that record — a real consideration in a codebase where money paths are reviewed.
- **`filter-repo --replace-text` alters file contents across history.** Verify the result; a bad
  expression can silently mangle code.
- **Unreferenced objects persist** through gc grace periods, so "removed" is not immediate even
  locally.
- **Declining to rewrite is a legitimate security decision** when the value is rotated and the reach
  is known — provided the reasoning is recorded.

# Architecture Decisions
- **Smallest tool for the job.** `--amend` for the last commit, `rebase -i` for a branch,
  `filter-repo` only for all-history problems.
- **`--force-with-lease` mandated, plain `--force` forbidden on shared branches**
  (`CONTRIBUTING.md` §10). The lease check is free and prevents the one irreversible mistake.
- **Rewrite your own branch freely, before review.** Squashing `wip` commits is expected — history is
  a product for readers, not a keystroke log.
- **Squash-merge at the PR boundary**, which is a rewrite GitHub performs for you: one feature, one
  commit, revertable as a unit.
- **No rewrite for the dump incident** — decided on evidence (rotation-irrelevant, 0 forks, going
  private, ~86 KB), and recorded in the commit message so it reads as judgement.
- **Containment preferred over demolition.** Untracking plus a root ignore rule closes the *class*;
  a rewrite would only have addressed one *instance*.
- **`filter-repo`, never `filter-branch`.** Git's own docs recommend it; `filter-branch` is slow and
  has known footguns.

# Best Practices
- Ask `git log origin/HEAD..HEAD` before rewriting anything. Those commits are yours alone.
- Rewrite your own unpushed branch often; never rewrite shared history without agreement.
- Always `--force-with-lease`. Never plain `--force`.
- Run `filter-repo` on a **fresh clone**, with `--dry-run` first.
- Verify removal with `git log --all --oneline -- <path>` (empty) — not by trusting the tool.
- Rewrite tags alongside branches, or your releases dangle.
- After a rewrite: `reflog expire` + `gc --prune=now`, and have others **re-clone** rather than pull.
- Rotate the credential regardless — a rewrite is not a substitute.
- Write the decision down, especially a decision *not* to rewrite.

# Beginner Mistakes
- **Fearing `--amend`** on an unpushed commit → it is the safest rewrite there is.
- **Plain `git push --force`** → can silently delete a colleague's commit; `--force-with-lease`
  refuses instead.
- **Running `filter-repo` on your only clone** → one mistake and there is no pristine copy.
- **Believing a rewrite removes a secret** → existing clones keep it; rotate.
- **Skipping tags** → releases point at commits that no longer exist.
- **Telling colleagues to `git pull` after a rewrite** → merges the old history back in. Re-clone.
- **Expecting `.git` to shrink immediately** → needs `reflog expire` and `gc --prune=now`.
- **Using `filter-branch`** → deprecated, slow, footgunny. Use `filter-repo`.
- **Rewriting shared history without telling anyone** → the actual cause of "git lost my work".
- **Not recording a decision not to rewrite** → the next person re-audits the whole incident.

# Interview Questions
- **Junior:** "What does `git commit --amend` do?" — Replaces the most recent commit with a new one
  containing your changes or new message. It does not edit the old commit; commits are immutable, so
  amending creates a new object with a new hash. Safe while unpushed.
- **Mid:** "Why does rewriting one commit change all the later ones?" — Each commit's hash is computed
  over its content **including its parent's hash**. Change a commit and its hash changes, so its
  child's parent reference changes, so the child's hash changes, and so on to the tip. Rewriting
  commit 40 of 100 replaces 61 commits; the originals persist unreferenced until gc.
- **Senior:** "Difference between `--force` and `--force-with-lease`?" — `--force` makes the remote
  match you unconditionally, so it can delete commits pushed since your last fetch.
  `--force-with-lease` first checks the remote still matches your remote-tracking ref and **refuses**
  if it moved, turning silent data loss into an error you can inspect. The subtlety is that a plain
  `git fetch` renews the lease, so fetch-then-force-with-lease is nearly as dangerous as `--force`;
  the protection only holds if you inspect the fetched state before pushing.
- **Staff:** "A secret has been in a public repo's history for a year. Do you rewrite?" — Probably
  not, and the reasoning matters more than the verdict. Rotation is step one regardless, because a
  year of public exposure means anyone who cloned has it permanently and no repository operation can
  retract that — so a rewrite cannot restore secrecy, it can only remove the most convenient copy from
  one remote. Then I would cost it honestly: new hashes for every descendant, a force-push, invalidated
  clones and forks, dangling tags, broken SHA references in CI and runbooks, and PR review comments
  losing their anchor. Against that, the benefit is real only when the value cannot be rotated —
  typically someone else's credential — or when a compliance obligation demands removal. And the
  decision is not the deliverable: closing the **class** is. On this project the equivalent case came
  down to a genuinely mild audited exposure with zero forks, so the rewrite was declined and the
  reasoning written into the commit message, while the actual fix was a root-level ignore rule that
  made the whole category impossible in every sibling directory — present and future. A rewrite fixes
  one instance; a rule fixes the pattern.

### Why interviewers ask these — and the answer that separates levels
| Testing for | Weak answer | What lands |
|---|---|---|
| Do you know the mechanism? | "Amend edits my last commit." | Commits are immutable; amend creates a new object, and because the parent hash is hashed in, every descendant is replaced too. |
| Do you understand the lease? | "`--force-with-lease` is the safe force." | It refuses when the remote moved since your last fetch — and `git fetch` renews the lease, so it only protects you if you inspect first. |
| Can you cost a rewrite? | "Run filter-repo and force-push." | Rotate first; rewriting cannot un-publish. Then weigh re-hashed descendants, broken clones/forks/tags/SHA refs against a benefit that only exists if the value is unrotatable. |

**The killer follow-up:** *"You force-pushed and deleted a colleague's commit. Recover it."* — It is not lost: their reflog has it, and any other clone still references the abandoned commit, so `git reflog` on their machine or `git fsck --lost-found` recovers it — then re-apply and push properly. The follow-up answer is the prevention: `--force-with-lease` would have refused the push outright, which is why plain `--force` has no legitimate use on a shared branch.

# Revision Notes
- Rewriting = **creating new commits and abandoning old ones**. Nothing is edited; objects are immutable.
- Parent hash is part of the hash ⇒ **change one commit, every descendant is replaced**.
- Safety test: **`git log origin/HEAD..HEAD`** — those commits are yours alone.
- Blast radius: `--amend` (1) → `rebase -i` (range) → `rebase` (branch) → **`filter-repo` (ALL history)**.
- **`--force-with-lease` always**; plain `--force` never on shared. Caveat: **`git fetch` renews the lease**.
- `filter-repo` on a **fresh clone**, `--dry-run` first; it removes your remotes on purpose. `filter-branch` is **deprecated**.
- Verify removal: `git log --all --oneline -- <path>` must be **empty**. Rewrite **tags** too.
- Space needs `reflog expire --expire=now --all` + `gc --prune=now`.
- **A rewrite does NOT un-publish a secret.** Rotate first, always.
- This repo **declined** a rewrite: 0 forks · going private · 1,000,000-iteration hashes · OAuth tables empty · ~86 KB ⇒ contained instead (2,954 untracked + root `.gitignore`), decision in the commit message.

# Cheat Sheet
```bash
# is it safe to rewrite?
git log origin/HEAD..HEAD --oneline        # yours alone ⇒ safe
git status                                  # "up to date with origin/x" ⇒ pushed

# smallest → largest
git commit --amend -m "msg"                 # last commit only
git commit --amend --no-edit                # fold in staged changes
git commit --amend --reset-author           # fix a wrong author
git rebase -i origin/main                   # squash/reword/drop a range (ch 14)
git rebase --abort                          # bail out safely

# ALL history — on a FRESH CLONE
pip install git-filter-repo
git clone --no-local /path/to/repo /tmp/work && cd /tmp/work
git filter-repo --invert-paths --path secret.sql --dry-run
git filter-repo --invert-paths --path secret.sql
git filter-repo --invert-paths --path-glob '*.sql'
git filter-repo --replace-text expressions.txt      # scrub STRINGS, keep files
git log --all --oneline -- secret.sql        # EMPTY = gone
git remote add origin <url>                  # filter-repo removed it on purpose
git push --force-with-lease --all
git push --force-with-lease --tags

# reclaim space locally
git reflog expire --expire=now --all && git gc --prune=now --aggressive
git count-objects -vH

# recovery
git reflog                                   # where HEAD has been
git reset --hard HEAD@{2}
git fsck --lost-found                        # unreferenced commits
```

# My ERP Section

| Fact | This repository |
|---|---|
| Rewrite considered | yes — 2 committed `pg_dump` files, repo public ([Ch 33](33_Secrets_And_Leaks.md)) |
| **Decision** | **DECLINED.** Recorded verbatim in the commit message so it reads as judgement, not oversight |
| Evidence for declining | 0 forks / 0 stars / 0 watchers · going private · `pbkdf2_sha256$1000000$` × 2 · primary account `!OUUm8Nk…` (no password) · OAuth tables empty · dumps ~86 KB |
| Cost avoided | re-hashing history, a force-push immediately after PR #15 merged, every SHA reference broken |
| Done instead | `git rm --cached` **2,954** files (331,748 deletions, 0 bytes lost) + monorepo-root `.gitignore` verified blocking at **5** paths |
| Class vs instance | the ignore rule closes the whole category in every sibling directory; a rewrite would have addressed one instance |
| Space argument | none — `.git` is 97 MB / 25,975 packed objects; the dumps are ~86 KB |
| Policy | `CONTRIBUTING.md` §10 — `--force-with-lease` on your own branch only; **plain `--force` forbidden** on anything shared |
| Routine rewrites | squash before review, and **squash-merge** at the PR boundary (a rewrite GitHub performs) |
| Why no server-side guard | force-push protection is paid on private repos ⇒ `git-hooks/pre-push` + the `--force-with-lease` habit ([Ch 27](27_Pre_Push_Protection.md)) |
| Would have flipped if… | the OAuth tables had held a live client secret — an unrotatable third-party credential is exactly when removal has value |

# Practice Tasks
1. In a throwaway repo, commit, then `git commit --amend --no-edit`, and compare `git log --oneline -1`
   before and after. The hash changed — proof it is a new commit.
2. Make three commits, amend the **first** with `rebase -i`, then observe that all three hashes
   changed. That is the cascade.
3. Run `git log origin/HEAD..HEAD --oneline` in this repo. Those are the commits you could safely
   rewrite right now.
4. Simulate the `--force-with-lease` refusal: clone a repo twice, push from clone A, then try
   `--force-with-lease` from clone B. Read the refusal, then `git fetch` and notice the lease renew.
5. Practise `filter-repo` properly: `git clone --no-local` this repo to `/tmp`, remove `*.sql` from all
   history there, and confirm `git log --all --oneline -- '*.sql'` is empty. **Never** on the real
   clone.
6. In that same `/tmp` copy, run `git count-objects -vH` before and after `reflog expire` + `gc
   --prune=now`. Watch when space is actually reclaimed.

# Homework
- Write your own decision checklist for "should I rewrite history", then apply it to this repo's dump
  incident and see whether you reach the same verdict. If you disagree, write down why — that is a
  legitimate outcome.
- Read `git help filter-repo` (or the project README) on `--replace-text` and construct an expressions
  file that would scrub a specific token from all history. Test it on a `/tmp` clone.
- Force-push over your own commit deliberately in a throwaway repo, then recover it from the reflog.
  Do it once so the fear goes away permanently.
- Find a public repository that has been rewritten (a `git filter-repo`/BFG note in its history or
  README) and read how the maintainers communicated it. Communication is most of the work.

# Further Reading & Live Resources
- [git-filter-repo](https://github.com/newren/git-filter-repo) — the maintained tool, with an excellent README and a `filter-branch` comparison
- [Pro Git — Rewriting History](https://git-scm.com/book/en/v2/Git-Tools-Rewriting-History) — amend, rebase, filter, in order; free
- [`git push --force-with-lease`](https://git-scm.com/docs/git-push#Documentation/git-push.txt---force-with-leaseltrefnamegt) — the exact semantics, including the lease-renewal caveat
- [GitHub Docs — Removing sensitive data](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository) — the official procedure and its warnings
- [git-filter-branch (deprecated)](https://git-scm.com/docs/git-filter-branch) — read the warning at the top; it is why `filter-repo` exists
- [BFG Repo-Cleaner](https://rtyley.github.io/bfg-repo-cleaner/) — a faster alternative for the narrow case of deleting big files
- [Pro Git — Maintenance and Data Recovery](https://git-scm.com/book/en/v2/Git-Internals-Maintenance-and-Data-Recovery) — gc, prune, and recovering what you thought was gone
