---
id: git-course-09-what-a-branch-really-is
type: lesson
status: active
owner: handwritten
scope: git, version control — refs, HEAD and reachability; the mechanism under every branch operation
anchors: .git/HEAD, .git/refs/heads/new_flask_app, .git/packed-refs, git-hooks/pre-push, CONTRIBUTING.md
verified: 2026-08-03
---

# 09 — What a Branch Really Is (a 41-byte file with a hash in it)

> Part of [Git Course](00_COURSE_OVERVIEW.md). Prev: [08 — Reading History](08_Reading_History.md). Next: [10 — Creating & Switching Branches](10_Creating_And_Switching_Branches.md).

# Learning Objectives
By the end of this chapter you can:
- state exactly what a branch **is** — a **ref**: a file under `.git/refs/heads/` holding one 40-character hash
- explain `HEAD`, why it is a *symbolic* ref, and what "detached HEAD" therefore means
- describe what committing does to a branch (writes objects, then **moves one pointer**) and why that makes branches free
- read `.git/packed-refs`, and say which value wins when a ref exists both loose and packed
- distinguish a **branch**, a **remote-tracking ref** and a **tag**, and peel an annotated tag to its commit
- answer "which branch is this commit on?" in terms of **reachability**, and recover a deleted branch

# Purpose
Every command in the next seven chapters — `switch`, `merge`, `rebase`, `reset`, `push`, `reflog` — is a variation on *moving a pointer*. If you know what a branch physically is, those commands stop being magic incantations you memorise and become obvious consequences. This is the chapter that converts fear into understanding, and it is all verifiable with `cat`.

# The Problem
You have been told to "be careful with branches" and you do not know why. Is deleting one dangerous? Does creating one copy the code? Where does the work *go* when you switch? Why does everyone say a merge is cheap and a force-push is scary?

Without the mechanism, you compensate with ritual: you never delete a branch, you keep 14 of them alive, you copy the whole folder before trying anything, and a "detached HEAD" message ruins your afternoon. With the mechanism — one hash in one small file — every one of those questions answers itself in a sentence.

# Theory (from zero)

### First: the graph exists without branches
A **commit** is an immutable object: a snapshot of the whole project plus metadata plus a pointer to its **parent** ([Ch 05](05_How_Git_Stores_Everything.md), [Ch 06](06_The_Commit_Graph.md)). Chain them by parent pointers and you get history. That chain is the actual data, and it is complete *before any branch is involved*.

The problem branches solve is trivial by comparison: hashes are 40 hex characters and nobody wants to type `42a2ecc4dc77dafc9407f4eaf4840c3ed8bd97fa`. A branch is a **human-readable name for one commit**.

### A ref is a file. A branch is a ref.
A **ref** (reference) is a name that resolves to a hash. Branches live in `refs/heads/`, and in the simplest case each one is literally a file:

```
$ cat .git/HEAD
ref: refs/heads/new_flask_app

$ cat .git/refs/heads/new_flask_app
42a2ecc4dc77dafc9407f4eaf4840c3ed8bd97fa

$ wc -c .git/refs/heads/new_flask_app
41 .git/refs/heads/new_flask_app
```

**41 bytes**: 40 hex characters and a newline. That is the entire branch. Not the commits, not the files — one pointer.

Three facts follow immediately, and they are the whole point of this chapter:

- **Creating a branch is writing 41 bytes.** It is instant regardless of repository size, and it copies nothing.
- **Deleting a branch deletes a pointer, not commits.** The commits stay in the object database; they merely lose their name.
- **"Moving" a branch is overwriting those 41 bytes.** `commit`, `merge`, `rebase`, `reset` all end in exactly that step.

### HEAD — the "you are here" pointer
`HEAD` answers "which branch am I on?". Normally it is a **symbolic ref**: instead of a hash it stores the *name* of a ref, as you saw above — `ref: refs/heads/new_flask_app`. That indirection is what makes committing work:

1. Git writes the new blob/tree/commit objects.
2. Git resolves `HEAD` → `refs/heads/new_flask_app`.
3. Git overwrites that file with the new commit's hash.

Step 3 is why "the branch advances when I commit". Nothing else happened.

**Detached HEAD** is when `.git/HEAD` contains a raw hash instead of `ref: …`. You are then standing on a commit with **no branch to advance**. Commits you make still exist, but nothing points at them, so they are only findable through the reflog ([Ch 16](16_Reflog.md)). It is not an error — `git checkout <tag>` does it deliberately — it is just a state you must leave on purpose (`git switch -c <name>` to keep the work, `git switch main` to abandon it).

```bash
git symbolic-ref HEAD     # refs/heads/new_flask_app   (errors if detached)
git rev-parse HEAD        # 42a2ecc4…  the commit, either way
```

### Loose refs versus `packed-refs` — the surprise
Thousands of tiny files are inefficient, so git periodically packs refs into one text file, `.git/packed-refs`. After packing, the loose file **is deleted**. On this repo, right now:

```
$ ls .git/refs/heads/
new_flask_app                       <- main is NOT here

$ git show-ref | head -3
7c256f50f2773d7f8e02d3762a1dd43d19386a3c refs/heads/main
42a2ecc4dc77dafc9407f4eaf4840c3ed8bd97fa refs/heads/new_flask_app
83a144ba3fad222bdd3b85d7b5f67a7fb0604ed2 refs/remotes/origin/main
```

`main` has no file at all, yet git resolves it perfectly — because it is in `packed-refs`. And it gets better. `new_flask_app` exists in **both** places, with **different** values:

```
$ head -3 .git/packed-refs
# pack-refs with: peeled fully-peeled sorted
7c256f50f2773d7f8e02d3762a1dd43d19386a3c refs/heads/main
494040011426eeb5b53d92836af178e9500d2b8b refs/heads/new_flask_app
```

Packed says `49404001…`; the loose file says `42a2ecc4…`; `git show-ref` reports `42a2ecc4…`. **The loose ref always wins** — it is the newer write, and `packed-refs` is a stale snapshot until the next pack.

**The lesson, and it is a rule, not a nuance:** never read refs by `cat`-ing files in a script. Use the plumbing, which handles both storages plus symbolic refs correctly:

```bash
git rev-parse <ref>                  # ref -> hash
git show-ref                         # every ref -> hash
git for-each-ref --format='%(refname:short) %(objectname:short)'
git symbolic-ref HEAD                # which branch HEAD points at
```
`cat .git/refs/...` is a **teaching tool** (it is how you learn the model). `rev-parse` is the **tool** (it is how you write anything real).

### Branches, remote-tracking refs, and tags — three ref namespaces
| Namespace | Example | Who moves it | What it means |
|---|---|---|---|
| `refs/heads/` | `refs/heads/main` | **you**, by committing | a branch you work on locally |
| `refs/remotes/` | `refs/remotes/origin/main` | `git fetch` / `git push` | a **cache** of where the remote's branch was at last contact |
| `refs/tags/` | `refs/tags/erp-v1.0.0` | created once, then frozen | a permanent name for one commit |

**A remote-tracking ref is not a branch you commit on.** `origin/main` is your local memory of GitHub's `main` as of your last `fetch`. It can be stale; it is never updated by someone else pushing — only by *you* fetching ([Ch 19](19_Push_Fetch_Pull.md)).

**Upstream tracking** is the recorded link between your branch and a remote-tracking ref, and it is what lets git print ahead/behind:

```
$ git branch -vv
  main          7c256f50 add a js of billing
* new_flask_app 42a2ecc4 [origin/new_flask_app: ahead 1] chore(repo): stop tracking database dumps…
```
"ahead 1" means one commit exists locally that `origin/new_flask_app` does not have. It is computed, not stored — the underlying question is the range arithmetic from [Ch 08](08_Reading_History.md):

```
$ git rev-list --left-right --count main...origin/main
0	295
```
Local `main` has **0** commits the remote lacks and is **295** behind. Note `main` has no `[upstream]` in `branch -vv` above — no link is configured, so git prints no ahead/behind for it and you must ask explicitly.

**Tags** are refs that do not move. A *lightweight* tag is just a ref pointing at a commit. An **annotated** tag (`git tag -a`, which `CONTRIBUTING.md` §7 requires) creates a whole **tag object** — with its own author, date and message — and the ref points at *that*. So a tag name can resolve to something that is not a commit:

```
$ git rev-parse erp-v1.0.0
0cccb32b174e39343109e06977a2e676ad51275f     <- the TAG OBJECT

$ git rev-parse erp-v1.0.0^{commit}
90c1f2f31f47c199d83dedb52d202ce3ba63ea11     <- the commit it names
```
`^{commit}` is the **peel** operator: "follow this until you reach a commit". This is why the header line of `packed-refs` says `peeled fully-peeled` and why peeled entries appear there as `^<hash>` lines — git caches the peel so it never has to open the tag object twice.

### "Which branch is this commit on?" — reachability, not ownership
A commit does not belong to a branch. The honest question is: *from which branch tips can I reach this commit by walking parents?* Sometimes the answer surprises you:

```
$ git branch --contains 7fe2bb0e
* new_flask_app

$ git merge-base main new_flask_app
7c256f50f2773d7f8e02d3762a1dd43d19386a3c
```
`7fe2bb0e` is not reachable from local `main` — because local `main` is stale at `7c256f50`, which is also their **merge base** (their most recent common ancestor, and the anchor every merge and rebase starts from, [Ch 11](11_Merging.md)). On GitHub the same commit *is* on `main`, via merge `83a144ba`. Reachability is always relative to a ref, and a stale ref gives a stale answer.

Reachability is also the **garbage-collection rule**: an object reachable from any ref (or from the reflog) is kept; one reachable from nothing becomes eligible for pruning once its reflog entry expires — 90 days by default for reachable, 30 for unreachable. That is why deleting a branch is recoverable, and why it is not recoverable *forever*.

> 💡 **Samjho aise:** Kitaab = poori history (commits), जो likhi ja chuki hai. **Branch = ek chipakne wali parchi (sticky note)** jispe page number likha hai — parchi mein kitaab nahi hoti, sirf *page ka number* hota hai. **HEAD = woh ungli** jo bata rahi hai "abhi main is parchi pe khada hoon". Nayi parchi banana = do second ka kaam (41 byte). Parchi phaad dena = page nahi phata, sirf naam gaya — aur `git reflog` mein number 90 din tak likha rehta hai. Detached HEAD = ungli seedha page pe, parchi ke bagair: likhoge to page banega, par uska koi naam nahi hoga.

### Ref names are paths, so they collide like paths
Because a loose ref is a file inside `refs/heads/`, `feat/roster` is a **file** named `roster` inside a **directory** `feat`. So you cannot simultaneously have `feat/roster` and `feat/roster/ui` — the first needs `roster` to be a file, the second needs it to be a directory. Git refuses:

```
$ git branch feat/roster/ui        # while feat/roster exists — DO NOT RUN, shown to explain
fatal: cannot lock ref 'refs/heads/feat/roster/ui': 'refs/heads/feat/roster' exists;
cannot create 'refs/heads/feat/roster/ui'
```
That is not a bug and not a naming policy — it is the filesystem showing through. Rename one of them (`git branch -m`) and it works. This repo sidesteps it with flat `<type>/<short-kebab-description>` names (`CONTRIBUTING.md` §3).

### The other pseudo-refs you will meet
`ORIG_HEAD` — where HEAD was before the last big move (merge, rebase, reset); the fastest undo is often `git reset --hard ORIG_HEAD`. `FETCH_HEAD` — what the last `git fetch` brought. `MERGE_HEAD` — the other side, only during a conflicted merge. All are files directly in `.git/`, all readable with `git rev-parse`.

# Real World Example (this repo)

Everything above, on `/home/tech/umesh-personal`, in the order you would actually run it:

```
$ cat .git/HEAD
ref: refs/heads/new_flask_app

$ cat .git/refs/heads/new_flask_app ; wc -c .git/refs/heads/new_flask_app
42a2ecc4dc77dafc9407f4eaf4840c3ed8bd97fa
41 .git/refs/heads/new_flask_app

$ git show-ref
7c256f50f2773d7f8e02d3762a1dd43d19386a3c refs/heads/main
42a2ecc4dc77dafc9407f4eaf4840c3ed8bd97fa refs/heads/new_flask_app
83a144ba3fad222bdd3b85d7b5f67a7fb0604ed2 refs/remotes/origin/main
83a144ba3fad222bdd3b85d7b5f67a7fb0604ed2 refs/remotes/origin/new_flask_app
83a144ba3fad222bdd3b85d7b5f67a7fb0604ed2 refs/remotes/upstream/main
409321da669956cabbdf3283b064b6735df33c46 refs/stash
0cccb32b174e39343109e06977a2e676ad51275f refs/tags/erp-v1.0.0
1e042648cb8feab51b64f7989a7e29703f10dc25 refs/tags/kos-v1.0
520923fbe5a1c5833c7d4469ae4a769505e95712 refs/tags/pre-refactor-baseline
```

Read that output as a **complete map of every name this repository knows**. Nine refs: two branches, three remote-tracking caches, three tags, and — a nice detail — `refs/stash`, because [the stash](17_Stash_And_Worktrees.md) is *also* just a ref.

Three findings a beginner would miss:

1. **`refs/heads/main` has no file** (only `new_flask_app` is in `.git/refs/heads/`). It resolves from `packed-refs`. If you had scripted `cat .git/refs/heads/main`, your script would be broken and you would blame git.
2. **`new_flask_app` is packed at `49404001…` and loose at `42a2ecc4…`.** The loose value wins. `packed-refs` is a snapshot, not the truth.
3. **The commit object confirms the whole model.** `42a2ecc4` names its own parent — the branch ref is not part of the commit at all:
```
$ git cat-file -p 42a2ecc4 | head -4
tree 9653375af0159933b1aca53bba034d660693db74
parent 83a144ba3fad222bdd3b85d7b5f67a7fb0604ed2
author umesh-personal <umesh29mar@…> 1785747733 +0530
committer umesh-personal <umesh29mar@…> 1785747733 +0530
```
The commit knows its **parent**; it has no idea which branches point at it. Branches are an index built on top, which is exactly why moving one is harmless to history and why two branches can point at the same commit with no conflict.

And the tag peel, on the real release tag:
```
$ git rev-parse erp-v1.0.0            -> 0cccb32b174e39343109e06977a2e676ad51275f   (tag object)
$ git rev-parse erp-v1.0.0^{commit}   -> 90c1f2f31f47c199d83dedb52d202ce3ba63ea11   (the commit)
```

# Visual Diagram
```
  THE OBJECT GRAPH (immutable; exists with or without any branch)

     ... --> 7c256f50 --> ... --> 83a144ba --> 42a2ecc4
                 ^                    ^  \          ^
                 |                    |   `-- 2nd parent --> 7fe2bb0e
   refs/heads/main                    |                          (PR #15's branch side)
   (STALE: 295 behind)     refs/remotes/origin/main   refs/heads/new_flask_app  <-- HEAD
                           refs/remotes/upstream/main

  A REF IS A FILE                      HEAD IS A SYMBOLIC REF
   .git/refs/heads/new_flask_app        .git/HEAD
     "42a2ecc4dc77...fa\n"  = 41 bytes    "ref: refs/heads/new_flask_app"
   commit => write objects, then OVERWRITE those 41 bytes
   detached HEAD => .git/HEAD holds a raw hash: no branch to advance

  TWO STORAGES, ONE ANSWER (loose beats packed)
   .git/refs/heads/new_flask_app  ->  42a2ecc4   <-- WINS
   .git/packed-refs               ->  49404001   (stale snapshot)
   .git/refs/heads/main           ->  (no file)  resolved from packed-refs
   ALWAYS ask: git rev-parse / git show-ref / git for-each-ref   NEVER cat in a script

  NAMESPACES        refs/heads/*   you move these by committing
                    refs/remotes/* moved only by fetch/push (a cache, can be stale)
                    refs/tags/*    frozen; annotated tag -> tag OBJECT -> peel with ^{commit}
```

# Practical — verify the model yourself (all read-only)
```bash
cd /home/tech/umesh-personal

cat .git/HEAD                       # -> ref: refs/heads/new_flask_app
git symbolic-ref HEAD               # -> refs/heads/new_flask_app  (errors if detached)
cat .git/refs/heads/new_flask_app   # -> 42a2ecc4dc77dafc9407f4eaf4840c3ed8bd97fa
wc -c .git/refs/heads/new_flask_app # -> 41   (40 hex + newline: the whole branch)
ls .git/refs/heads/                 # -> new_flask_app only; main is packed
head -4 .git/packed-refs            # -> the packed snapshot, incl. a stale new_flask_app
```
```bash
git show-ref                        # every ref, both storages, correctly merged
git for-each-ref --format='%(refname:short) -> %(objectname:short) [%(upstream:short)]'
git rev-parse HEAD new_flask_app main               # names -> hashes
git rev-parse erp-v1.0.0 erp-v1.0.0^{commit}        # tag object, then the peeled commit
git branch -vv                      # tips, upstreams and ahead/behind
git branch --contains 7fe2bb0e      # which tips can REACH this commit
git merge-base main new_flask_app   # their most recent common ancestor
git rev-list --left-right --count main...origin/main   # -> 0  295
git cat-file -p HEAD | head -4      # the commit names its PARENT, never a branch
```
**Destructive commands — shown, not run.** Each with its undo:
```bash
git branch -d feat/old        # refuses if unmerged  -> safe
git branch -D feat/old        # force: deletes the ref regardless
  # UNDO: git reflog  (find the hash)  then  git branch feat/old <hash>
  #       or one step: git branch feat/old "feat/old@{1}"     (reflog syntax)

git push --force origin main  # OVERWRITES the remote ref; someone else's work can vanish
  # SAFER:  git push --force-with-lease   (refuses if the remote moved since your fetch)
  # In THIS repo: git-hooks/pre-push refuses main/master outright (override: --no-verify)

git reset --hard <hash>       # moves the branch ref AND rewrites your working tree
  # UNDO: git reset --hard ORIG_HEAD   (or the hash from git reflog)
```

# Production Walkthrough
The state of this repository *is* the walkthrough, and it shows both the workflow working and drift happening.

1. **Work happened on a branch.** `new_flask_app` was the working branch; its tip reached `7fe2bb0e`.
2. **A PR merged it.** `83a144ba` — *"Merge pull request #15 from umesh29032/new_flask_app"* — has two parents: `main`'s previous tip, and `7fe2bb0e`. That is the merge commit ([Ch 11](11_Merging.md)), and it is why `83a144ba^2` is `7fe2bb0e`.
3. **The remote-tracking refs moved on fetch.** `origin/main`, `origin/new_flask_app` and `upstream/main` all read `83a144ba` — caches of GitHub, updated by *your* fetch, never by someone else's push.
4. **Local `main` did not move.** It still points at `7c256f50` — **295 commits behind**, and with no upstream configured, so `git branch -vv` prints no warning about it. Nothing is broken: a ref is just a pointer, and this one was never updated.
5. **Which is exactly why `CONTRIBUTING.md` §9 opens the daily loop with:** `git fetch upstream && git switch main && git merge --ff-only upstream/main`. **`--ff-only` refuses to create a merge commit**: it either fast-forwards (slides the `main` pointer forward, since local `main` has nothing of its own) or fails. A failure is information — it means your `main` has drifted and should be reset to upstream, not merged. That keeps `main` a clean mirror.
6. **New work then starts from a fresh ref:** `git switch -c feat/their-thing` — 41 bytes, instant, copies nothing.
7. **Pushing is a ref update, and it is gated.** `git-hooks/pre-push` inspects the ref being pushed and **refuses `main` and `master`** (tested: `main` blocked, `master` blocked, `feat/my-thing` allowed; override `git push --no-verify`). That is client-side, therefore free, therefore only binding where it is installed — which is why `bash git-hooks/install.sh` is onboarding step 1, and why the gap is written down rather than hidden.
8. **The release is a frozen ref.** `erp-v1.0.0` → tag object `0cccb32b` → commit `90c1f2f3`. Annotated on purpose (§7), so `git show erp-v1.0.0` explains the release.

# Debugging Guide
| Symptom | Cause | Fix |
|---|---|---|
| "You are in 'detached HEAD' state" | `.git/HEAD` holds a raw hash, not `ref: …` — usually after checking out a tag or hash | Keep the work: `git switch -c <name>`. Abandon it: `git switch main` |
| Committed in detached HEAD, then switched away — work gone | The commits exist but no ref points at them | `git reflog`, then `git branch <name> <hash>` ([Ch 16](16_Reflog.md)) |
| `cat .git/refs/heads/main` → No such file | The ref is packed in `.git/packed-refs` | Use `git rev-parse main` / `git show-ref`; never `cat` refs in a script |
| A ref file's hash disagrees with `packed-refs` | Loose ref is newer; packed is a stale snapshot | Trust `git rev-parse`; loose always wins |
| `fatal: cannot lock ref 'refs/heads/a/b': 'refs/heads/a' exists` | Ref names are paths: `a` cannot be both file and directory | Rename one: `git branch -m a a-base` |
| Deleted a branch by mistake | Only the pointer went; commits survive until GC | `git branch <name> "<name>@{1}"`, or the hash from `git reflog` |
| `branch -vv` shows `[origin/x: gone]` | The remote branch was deleted (merged PR) | Delete the local one: `git branch -d x`; tidy caches with `git fetch --prune` |
| No ahead/behind shown for a branch | No upstream configured | `git branch -u origin/<name>`, or ask directly with `git rev-list --left-right --count` |
| `git branch --contains <hash>` misses a branch you expected | That local ref is **stale** — reachability is relative to a ref | Fetch first, then ask about `origin/main` instead of `main` |
| Someone's commits vanished from a shared branch | A plain `--force` push overwrote the remote ref | Recover from their reflog/PR; always use `--force-with-lease` |

# Performance Notes
- **Branch creation is O(1) and tiny**: 41 bytes written, no object copied, no working-tree change. A 100-branch repo carries about 4 KB of refs. There is no size argument against branching — only a *review* argument against long-lived ones.
- **`packed-refs` exists for filesystem efficiency.** One text file beats thousands of 41-byte files, each of which would otherwise cost a full block on disk and a syscall to read. On repos with tens of thousands of refs, packing is the difference between fast and unusable; `git gc` does it for you.
- **Ref lookup is not the cost of switching branches** — updating `HEAD` is trivial; materialising a different set of files in the working tree is the expensive part. Switching between two nearby commits is near-instant; switching across a large refactor rewrites many files.
- **Use `git for-each-ref` when scripting**, not a shell loop over `git branch` output. One process, one pass, `--format` gives you exactly the fields you need — and it reads both loose and packed refs correctly, which a `cat` loop cannot.
- Reachability queries (`branch --contains`, `merge-base`) walk the commit graph, so they scale with history depth, not with the number of branches. At **324** commits here they are instant; at millions, `git commit-graph write` is the fix.

# Security Considerations
- **A ref is an ordinary file.** Anyone who can write `.git/` can point `main` at any commit, with no audit trail in the repository itself. Disk access to a clone is repository write access.
- **A force-push destroys a remote ref's old value.** Plain `--force` overwrites blindly, and the overwritten commits are only recoverable from someone's reflog or a PR page. `--force-with-lease` refuses unless the remote is still where your last fetch said — always prefer it, and never force-push a shared branch (`CONTRIBUTING.md` §10).
- **Protection is ref-update policy, and on GitHub's free tier it is limited.** Server-side branch protection is paid on private repos, so this project uses three free layers: `git-hooks/pre-push` refusing `main`/`master` locally (installed per machine — a real, documented gap); collaborators on **Read** access working from a **fork**, so they have no push permission at all (server-side, free, and *stronger* than branch protection); and CI as the visible merge gate.
- **A hook is a local file, not a guarantee** — `.git/hooks/` is never cloned (a deliberate git security decision: cloning a repo must not run its author's code), and `--no-verify` bypasses it. Treat hooks as ergonomics for the honest, not as a control against the determined.
- **Tags are refs, so they can be moved too.** Moving a release tag silently changes what "v1.0.0" means for everyone who fetches later. Treat published tags as immutable; if a release is wrong, cut a new version.

# Architecture Decisions
- **Trunk-based, short-lived branches** (`CONTRIBUTING.md` §3: "One branch = one intent… A branch alive for three weeks is a merge conflict with a countdown timer"). *Rejected:* `git-flow` with long-lived `develop`/`release` branches — heavier than a 1–2 person team can justify (§10). Cheap refs are what make this affordable: branch, land, delete.
- **`<type>/<short-kebab-description>` names**, flat and lowercase (§3) — readable, greppable, and they avoid the file/directory ref collision described above.
- **Squash-merge, one commit per feature on `main`** (§5): `main`'s history reads as a list of features, any one of which reverts cleanly, and `--first-parent` becomes a release-notes tool ([Ch 08](08_Reading_History.md)).
- **`--ff-only` in the daily update loop** (§9) — chosen precisely *because* it fails loudly. It cannot create a merge commit, so a drifted local `main` surfaces as an error instead of silently becoming a divergent history.
- **Annotated tags for releases** (§7) — a real object with author, date and message, hence the two-step peel (`erp-v1.0.0` → `0cccb32b` → `90c1f2f3`). *Rejected:* lightweight tags, which are a bare pointer with nothing to read.
- **Honest note on the current state:** `new_flask_app` is a long-lived working branch that predates this rulebook, and local `main` sits **295** commits behind. Both are exactly what the rules above exist to prevent; they are recorded here rather than tidied away, because a course that only shows the clean case teaches nothing about drift.

# Best Practices
- Learn the model with `cat`; do the work with `git rev-parse` / `show-ref` / `for-each-ref`.
- Treat branches as disposable: one intent, land it, delete it. They cost 41 bytes.
- Never fear `git branch -d` — it refuses unmerged work, and `git reflog` recovers the rest.
- Leave detached HEAD deliberately: `git switch -c <name>` to keep the work, `git switch <branch>` to abandon it.
- Prefer `--force-with-lease` over `--force`, and never force-push a branch anyone else uses.
- Fetch before asking reachability questions; a stale ref gives a confidently wrong answer.
- Keep `main` a pure mirror of upstream and update it with `merge --ff-only`.
- Set an upstream (`git branch -u`) so ahead/behind is visible without extra commands.
- Treat a published tag as immutable; ship a new version instead of moving it.

# Beginner Mistakes
- **Thinking a branch contains commits or a copy of the code** → it is one hash in a 41-byte file. Nothing is copied when you create one.
- **Thinking `git branch -D` deletes commits** → it deletes a *pointer*. `git reflog` + `git branch <name> <hash>` brings the name back.
- **Panicking at "detached HEAD"** → it just means `HEAD` holds a hash instead of a branch name. `git switch -c <name>` keeps whatever you did.
- **Scripting `cat .git/refs/heads/<name>`** → breaks the moment the ref is packed, which is exactly what happened to `main` here. Use `git rev-parse`.
- **Trusting `packed-refs`** → it is a snapshot; a loose ref overrides it. Here `new_flask_app` differs between the two.
- **Believing `origin/main` is GitHub's live state** → it is a cache from your last fetch. Fetch, *then* compare.
- **Committing on a remote-tracking ref** → you cannot; `refs/remotes/*` is not a workspace. Create a local branch from it.
- **Expecting `git branch --contains` to be absolute** → reachability is relative to each ref, and a stale local `main` gives a stale answer.
- **Using plain `git push --force`** → it overwrites the remote ref and other people's commits. `--force-with-lease`.
- **Assuming an installed hook protects everyone** → `.git/hooks/` is never cloned, and `--no-verify` skips it. Fork + Read access is the layer that actually holds.

# Interview Questions
- **Junior:** "What is a git branch?" — A movable name for one commit: a **ref**, stored as a file under `.git/refs/heads/` containing that commit's 40-character hash (41 bytes with the newline). It holds no code and no commits. When you commit, git writes the new objects and then overwrites that file with the new hash, which is why the branch "advances". `HEAD` records which branch you are on.

- **Mid:** "What is detached HEAD, and how do you get out of it safely?" — Normally `.git/HEAD` is a *symbolic* ref holding `ref: refs/heads/<name>`; detached means it holds a raw commit hash, so there is no branch for a new commit to advance. Commits you make are real but unreferenced, so they are reachable only via the reflog and are eventually garbage-collected. To keep them: `git switch -c <new-branch>`, which creates a ref at the current commit. To discard them: switch back to a branch. It is a normal state — checking out a tag does it — not an error.

- **Senior:** "How does git resolve a ref, and where can it disagree with itself?" — Names resolve through `.git/HEAD` and the `refs/` namespaces, with two physical storages: loose files under `.git/refs/`, and one packed text file, `.git/packed-refs`. When a ref exists in both, the **loose** value wins — packed is a snapshot written by `gc`. So `cat`-ing a ref path is unreliable in two directions: the file may not exist (this repo's `main` is packed-only) or it may be shadowed by a newer loose write (this repo's `new_flask_app` differs between the two). Always go through `git rev-parse` / `show-ref` / `for-each-ref`, which also peel annotated tags — a tag ref can point at a *tag object*, so you need `^{commit}` to reach the commit.

- **Staff:** "Design branch protection for a private repo on a free plan, and be honest about the gaps." — Recognise the primitive first: protection is a policy on **ref updates**, and on GitHub that server-side policy is a paid feature for private repos. So compose free layers. (1) A client-side `pre-push` hook that refuses `main`/`master` — free and effective, but `.git/hooks/` is never cloned and `--no-verify` bypasses it, so it binds only on machines where it was installed; that gap gets written into onboarding, not hidden. (2) The layer that actually holds: give collaborators **Read** access and have them work from **forks**, so they have no push permission to the repository at all — server-side, free, and strictly stronger than branch protection, because "you cannot push anywhere" beats "you cannot push there". (3) CI on every PR as the visible merge gate — on a free plan a discipline gate rather than a mechanical block, but the signal is identical and it is in front of the reviewer. State the residual risk plainly: the owner on a fresh clone with no hook installed is unprotected. And when the repo goes public or a paid plan appears, turn on server-side protection and keep all three layers — the hook costs nothing to leave installed.

### Why interviewers ask these — and the answer that separates levels

| Testing for | Weak answer | What lands |
|---|---|---|
| Do you know the physical thing? | "A branch is a copy of the code you work on." | A ref: 41 bytes under `refs/heads/` holding one hash. Committing overwrites it. |
| Is detached HEAD scary to you? | "Something broke, I re-clone." | `HEAD` holds a hash, not a branch name. `git switch -c` keeps the work; reflog is the net. |
| Do you know refs have two storages? | "The branch file is in .git/refs." | Loose *or* packed, and loose wins. Use `rev-parse`, never `cat`, in anything real. |
| Can you reason about reachability? | "The commit is on main." | Reachable *from* a ref, and a stale local ref answers wrongly. Fetch, then ask. |

**The killer follow-up:** *"`cat .git/refs/heads/main` says No such file. Is the branch gone?"* — No: it is in `.git/packed-refs`, and `git rev-parse main` resolves it fine. Anyone who says the branch is gone has learned refs from a diagram instead of from a repository.

# Revision Notes
- A branch is a **ref**: `.git/refs/heads/<name>` = 40 hex + newline = **41 bytes**. No code, no commits.
- Commit = write objects, then **overwrite the ref**. That is the entire "branch advanced".
- `HEAD` is a *symbolic* ref (`ref: refs/heads/…`); **detached** = it holds a raw hash, so nothing advances.
- Deleting a branch deletes a pointer. Recover with `git reflog` + `git branch <name> <hash>`.
- Refs live **loose or packed**, and **loose wins**. Here `main` is packed-only; `new_flask_app` differs between the two. Never `cat` a ref in a script — `git rev-parse`.
- `refs/heads/*` = yours · `refs/remotes/*` = a **fetch cache**, can be stale · `refs/tags/*` = frozen.
- Annotated tag → tag **object**; peel with `^{commit}`: `erp-v1.0.0` → `0cccb32b` → `90c1f2f3`.
- "On a branch" means **reachable from that ref**. Stale ref ⇒ stale answer; `merge-base` gives the common ancestor.
- Ref names are paths: `feat/x` and `feat/x/y` cannot coexist ("cannot lock ref").
- `ORIG_HEAD` is the pre-move position — `git reset --hard ORIG_HEAD` is the fast undo.

# Cheat Sheet
- **Where am I?** `cat .git/HEAD` · `git symbolic-ref HEAD` (errors if detached) · `git rev-parse HEAD`.
- **What is a branch, physically?** `cat .git/refs/heads/<name>` · `wc -c` → 41 bytes.
- **Every ref:** `git show-ref` · scriptable `git for-each-ref --format='%(refname:short) %(objectname:short) %(upstream:short)'`.
- **Name → hash:** `git rev-parse <ref>` · annotated tag → commit: `git rev-parse <tag>^{commit}`.
- **Packed vs loose:** `ls .git/refs/heads/` · `head .git/packed-refs` — **loose wins**; never `cat` in scripts.
- **Tips + tracking:** `git branch -vv` · set upstream `git branch -u origin/<name>`.
- **Reachability:** `git branch --contains <hash>` · `git merge-base A B` · `git rev-list --left-right --count A...B`.
- **Delete:** `git branch -d <name>` safe · `-D` force. **Undo:** `git branch <name> "<name>@{1}"` or a hash from `git reflog`.
- **Undo a big move:** `git reset --hard ORIG_HEAD`.
- **Push safely:** `--force-with-lease`, never plain `--force`, never on a shared branch.

# My ERP Section
| Concept | In this repo, verbatim |
|---|---|
| `HEAD` | `.git/HEAD` = `ref: refs/heads/new_flask_app` |
| The branch file | `.git/refs/heads/new_flask_app` = `42a2ecc4dc77dafc9407f4eaf4840c3ed8bd97fa`, **41 bytes** |
| Packed-only ref | `refs/heads/main` = `7c256f50` — **no loose file**, resolved from `.git/packed-refs` |
| Loose beats packed | `new_flask_app`: packed `49404001…`, loose `42a2ecc4…` → `show-ref` reports the loose one |
| Remote-tracking caches | `origin/main`, `origin/new_flask_app`, `upstream/main` all = `83a144ba` (PR #15's merge) |
| Drift | `git rev-list --left-right --count main...origin/main` → `0  295` (local `main` 295 behind) |
| Tracking line | `git branch -vv` → `new_flask_app … [origin/new_flask_app: ahead 1]`; `main` has no upstream |
| Tags | `erp-v1.0.0` → tag object `0cccb32b` → commit `90c1f2f3` · also `kos-v1.0`, `pre-refactor-baseline` |
| Stash is a ref too | `refs/stash` = `409321da` |
| Reachability | `git branch --contains 7fe2bb0e` → `new_flask_app` only; `merge-base main new_flask_app` = `7c256f50` |
| Ref-update policy | `git-hooks/pre-push` refuses `main`/`master` (tested; `feat/my-thing` allowed; `--no-verify` bypasses) |

# Practice Tasks
1. **Prove the 41 bytes.** Run `cat .git/HEAD`, then `cat` and `wc -c` the branch file it names. Explain in one sentence why the number is 41 and not 40.
2. **Find the missing file.** `ls .git/refs/heads/`, then `git rev-parse main`. Where did the value come from, and what would a `cat`-based script have done?
3. **Catch the disagreement.** Compare `head -4 .git/packed-refs` with `.git/refs/heads/new_flask_app`. Which value does `git show-ref` print, and why is that the correct choice?
4. **Peel a tag.** Run `git rev-parse erp-v1.0.0` and `git rev-parse erp-v1.0.0^{commit}`, then `git cat-file -t` on both hashes. Explain the two object types.
5. **Reachability drill.** Run `git branch --contains 7fe2bb0e` and `git merge-base main new_flask_app`. Why is `7fe2bb0e` "not on main" locally but on `main` at GitHub?
6. **Safe delete and recover.** In a throwaway repo: make a branch, commit on it, `git branch -D` it, then restore it from `git reflog`. Write down the exact recovery command.

# Homework
- Draw this repository's nine refs from `git show-ref` as labels on a commit graph. Mark which are yours to move, which only `fetch` moves, and which are frozen.
- Explain to a teammate, in five sentences and no jargon, why creating a branch is free but a force-push is dangerous. Use the word "pointer" exactly once.
- Read `git-hooks/pre-push`. Which ref names does it refuse, how is it bypassed, and why is `CONTRIBUTING.md` §2 Layer 2 (fork + Read access) described as *stronger* than a hook?
- Local `main` is 295 commits behind. Write the exact commands from `CONTRIBUTING.md` §9 that would fix it, and say what `--ff-only` would do if `main` had one local commit of its own.
- Using [Ch 16](16_Reflog.md), work out how long a deleted branch's commits survive here, and which config values decide that.

---

# Further Reading & Live Resources
- Git docs — *`git-branch`* (`-d` vs `-D`, `-vv`, `--contains`): https://git-scm.com/docs/git-branch
- Git docs — *`gitrepository-layout`*, what every file in `.git/` is: https://git-scm.com/docs/gitrepository-layout
- Git docs — *`git-for-each-ref`*, the scripting-safe way to read refs: https://git-scm.com/docs/git-for-each-ref
- Git docs — *`git-symbolic-ref`* and how `HEAD` works: https://git-scm.com/docs/git-symbolic-ref
- *Pro Git*, ch. 10.3 "Git References" — refs, HEAD, packed-refs from the inside: https://git-scm.com/book/en/v2/Git-Internals-Git-References
- *Pro Git*, ch. 3.1 "Branches in a Nutshell": https://git-scm.com/book/en/v2/Git-Branching-Branches-in-a-Nutshell
