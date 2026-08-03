---
id: git-course-06-the-commit-graph
type: lesson
status: active
owner: handwritten
scope: git — history as a DAG, parents, merge commits, ancestry, reachability, ranges
anchors: .git/refs/heads, .git/HEAD
verified: 2026-08-03
---

# 06 — The Commit Graph (history is a graph, not a list)

> Part of [Git Course](00_COURSE_OVERVIEW.md). Prev: [05 — How Git Stores Everything](05_How_Git_Stores_Everything.md). Next: [07 — .gitignore](07_Gitignore.md).

# Learning Objectives
By the end of this chapter you can:
- explain why history is a **directed acyclic graph** and not a timeline
- read `git log --graph` and say which commit is whose parent
- distinguish `HEAD~1` from `HEAD^1` and know when the difference bites
- explain what a **merge base** is and why merge, rebase and diff all depend on it
- read the range syntaxes `A..B` and `A...B` without guessing
- explain **reachability**, and therefore what "deleting a branch" does and does not destroy

# Purpose
[Chapter 05](05_How_Git_Stores_Everything.md) established that a commit records its `parent`.
That one field is the entire structure of git history — and it makes history a **graph**.

Most people picture history as a list, because `git log` prints a list. That mental model works
right up until two branches exist, and then everything confusing about git traces back to it:
what merge actually does, why rebase produces different commits, why `git log` on a branch does
not show "everything", why `A..B` and `A...B` mean different things.

This chapter replaces the list with the graph. It is the last piece of the mental model before
Part 2 — [branching](09_What_A_Branch_Really_Is.md) is nothing but pointers into this graph.

# The Problem
You branch off `main`, work for a week, and `main` moves on too. Now answer these:

- Which commits are "yours" and which are "theirs"?
- What is the common starting point — and how would git find it without being told?
- If you merge, what exactly gets compared?
- If you delete your branch afterwards, are your commits gone?

A list cannot answer any of them: a list has no notion of divergence. A graph answers all four
mechanically, and the answers stop being folklore.

# Theory (from zero)

### A DAG, one word at a time
Git history is a **directed acyclic graph**:

- **Graph** — nodes (commits) joined by edges (parent links).
- **Directed** — every edge points **backwards in time**. A commit knows its parent; a parent
  never knows its children. This is why `git log` walks backwards, and why finding a commit's
  children is expensive while finding its parent is instant.
- **Acyclic** — no cycles are possible. A commit's hash includes its parent's hash, so pointing
  at a descendant would require knowing a hash that depends on your own. Immutability makes
  cycles arithmetically impossible, not merely forbidden.

```
   A ◄── B ◄── C          arrows point to PARENTS (backwards)
                          C is the newest; A has no parent (root)
```

### Parents: zero, one, or many
| Parents | What it is |
|---|---|
| **0** | the root commit — the first commit in the repository |
| **1** | an ordinary commit |
| **2** | a **merge commit** — the join of two lines of work |
| **3+** | an "octopus" merge; legal, rare, usually a sign of over-cleverness |

A merge commit having two parents is *the* structural fact of collaboration. It is the only
place the graph converges, and it is what preserves the record that two lines of work existed.

### Divergence: what a branch actually looks like
```
              D ◄── E          ← feat/x  (your work)
             ╱
   A ◄── B ◄── C ◄── F         ← main    (moved on without you)
             ▲
             └─ merge base: the newest commit reachable from BOTH
```

`C` is the **merge base** — the most recent common ancestor. Git computes it; you never supply
it. And it is the hinge for three separate operations:

- **merge** — combine the changes each side made *since the merge base*
- **rebase** — replay `D,E` (the commits after the base on your side) onto a new base
- **diff `main...feat/x`** — show what your branch changed relative to the base

So "what did my branch change?" has a precise mechanical answer: everything from the merge base
to your tip. That is the question code review is actually asking.

```bash
git merge-base main feat/x     # prints the hash of C
```

### `~` versus `^` — the distinction that bites at merges
Both walk backwards, but along different axes:

- **`~n`** — go back `n` **generations**, always following the **first** parent.
- **`^n`** — select the **nth parent** of *this* commit.

On an ordinary single-parent commit they coincide: `HEAD~1` and `HEAD^1` are the same thing.
At a **merge commit** they diverge sharply:

```
   HEAD^1   → first parent  = the branch you were ON when you merged (usually main)
   HEAD^2   → second parent = the branch you merged IN (the feature)
   HEAD~2   → two generations back along FIRST parents only
```

This is not trivia. `git revert -m 1 <merge>` needs `-m 1` precisely because git cannot guess
which parent's line you want to keep. And `git log --first-parent` — which shows `main` as a
clean list of merged features, ignoring the internals of each — works entirely off this
distinction. On a squash-merge workflow like this project's it is the most useful `log` flag
there is.

### Ranges: `..` and `...`
```bash
git log A..B      # commits reachable from B but NOT from A     ← "what's in B that isn't in A"
git log A...B     # commits reachable from EITHER but not BOTH   ← symmetric difference
```

Two dots is the one you want 95% of the time: *"what does this branch add?"*

```bash
git log main..feat/x        # your commits, excluding everything main already had
git log --oneline main..HEAD | wc -l    # "how many commits is this PR?"
```

Confusingly, `git diff` flips the meaning of `...`:

- `git diff A..B` — compare the two *endpoints* directly
- `git diff A...B` — compare **B against the merge base**, i.e. "what did B change since it
  diverged"

`git diff main...feat/x` is therefore the diff a pull request shows. If you have ever wondered
why a PR diff does not include changes that landed on `main` after you branched — that is why.
It is measuring from the merge base, not from `main`'s tip.

### Reachability — and what "delete a branch" means
A commit is **reachable** if you can walk to it backwards from some ref (a branch, a tag, HEAD,
or the reflog). Reachability, not deletion, is what git actually manages:

- Deleting a branch removes a **41-byte pointer file**. The commits are untouched.
- Those commits may become *unreachable* — but they still exist as objects, and the
  [reflog](16_Reflog.md) keeps a reference for ~90 days.
- Only `git gc` eventually removes unreachable objects, after grace periods.

So `git branch -d` is nearly always recoverable, and "I deleted the branch, my work is gone" is
almost always false. This is the graph explaining a fear away.

> 💡 **Samjho aise:** History ek **seedhi line nahi**, ek **rasta ka jaal** hai — aur har teer
> **peeche** ki taraf ishara karta hai. Bachcha apne baap ko jaanta hai, baap bachche ko nahi.
> Isliye git peeche ki taraf chalta hai.
>
> Do log alag-alag raste chale? Jahan se alag hue wo mod = **merge base**. Git khud dhoondhta
> hai, aur teen kaam usi pe tike hain: merge, rebase, aur "meri branch ne kya badla".
>
> Aur branch delete karna = **naam-patta hatana**, ghar girana nahi. Ghar khada hai (~90 din
> reflog mein) — pata dobara mil sakta hai.

# Real World Example (this repo)
This repository contains a textbook merge in its graph. **PR #15** merged `new_flask_app` into
`main`, producing commit `83a144ba` — a real two-parent merge commit:

```bash
git log --graph --oneline -4 83a144ba
```
```
*   83a144ba Merge pull request #15 from umesh29032/new_flask_app
|\
| * 7fe2bb0e feat: accountant read tier, student role, learning platform completion…
| * af01b9e7 test(production): pin F-4 roster-picker guarantee on generic_stage path
* | …
```

The `|\` is the graph drawing itself: one node, two incoming lines. Confirm the two parents
directly:

```bash
git cat-file -p 83a144ba | head -3
# tree   …
# parent …          ← ^1 : main as it was
# parent 7fe2bb0e   ← ^2 : the feature branch that was merged in
```

**Two `parent` lines.** That is the whole definition of a merge commit — no special flag, no
separate record type, just a second parent field.

And the number that framed a real decision earlier in this project: when I checked what a PR
from `new_flask_app` into `main` would contain, the answer came straight from a range query —
**289 commits**, because `main` had been stale for months while all work happened on the branch.
That single number is why the recommendation was "review the newest commit, or split into narrow
PRs", not "read this diff". A range query turned a vague worry into a reviewable fact.

### The trap that immediately followed — and why it is the best lesson in this chapter

After PR #15 merged, I re-ran the same query while writing this chapter and got a *different*
answer. Here is the real state of the refs at that moment:

```bash
git rev-parse --short main origin/main new_flask_app
# 7c256f50      ← local main
# 83a144ba      ← origin/main  (has the merge)
# 42a2ecc4      ← new_flask_app
```
```bash
git rev-list --count main..new_flask_app          # 296   ← against STALE local main
git rev-list --count origin/main..new_flask_app   # 1     ← the truth
```

**296 versus 1.** Same syntax, same repo, one wrong by a factor of 296.

Nothing is broken. `main` is a **local pointer** and nothing updates it automatically. The merge
happened on GitHub, so `origin/main` moved when I fetched; local `main` stayed where it was last
left — five commits before the merge even existed. Every range query against it was therefore
measuring divergence from history that has since been merged.

Three durable lessons:

1. **`main` and `origin/main` are two different refs.** `git fetch` updates the second, never the
   first. Local `main` only moves when you check it out and merge, or fast-forward it.
2. **Range queries are only as truthful as the ref you name.** `main..HEAD` silently answers a
   question about *your stale copy of main*. Prefer `origin/main..HEAD` when you mean the real
   trunk — and `git fetch` first.
3. **This is why `CONTRIBUTING.md` §9 prescribes `git merge --ff-only upstream/main`.**
   `--ff-only` *refuses* to create a merge commit: it either fast-forwards cleanly or errors,
   which tells you your local branch has drifted instead of quietly papering over it.

```bash
git fetch origin
git switch main && git merge --ff-only origin/main    # now local main is real again
git rev-list --count main..new_flask_app              # 1
```

> A stale local `main` is the single most common cause of "git is behaving strangely". It is not
> strange; it is a pointer nobody moved.

# Visual Diagram
```
                        ┌─ D ◄── E ─┐            new_flask_app
                       ╱             ╲
   A ◄── B ◄── C ◄────╯               ╲
                ▲                      ▼
                │                 ┌─────────────────┐
          merge base              │  MERGE COMMIT   │  83a144ba
          (git merge-base)        │  parent ^1 ─────┼──► main side
                                  │  parent ^2 ─────┼──► 7fe2bb0e (feature side)
                                  └─────────────────┘
                                           │
                                           ▼  main

   NAVIGATION                     RANGES
   ──────────                     ──────
   HEAD~1  1 generation back      A..B    in B, not in A          ← "what this branch adds"
           (FIRST parent only)    A...B   in either, not both     (log: symmetric difference)
   HEAD^1  first parent
   HEAD^2  second parent          git diff A..B    endpoint vs endpoint
           (merge only)           git diff A...B   B vs MERGE BASE  ← what a PR diff shows

   REACHABILITY
   ────────────
   branch delete  = remove a 41-byte pointer.  Commits survive.
   unreachable    ≠ deleted.  reflog holds them ~90 days; only gc removes them.
```

# Practical — read the graph yourself
```bash
cd /home/tech/umesh-personal

# the graph, compactly — the flag combination worth memorising
git log --graph --oneline --decorate --all | head -25

# prove a merge commit has two parents
git cat-file -p 83a144ba | head -3
git log --pretty='%h parents:%p' -1 83a144ba      # two hashes = two parents

# ~ vs ^ on a MERGE commit — watch them differ
git log --oneline -1 83a144ba^1     # first parent : main's side
git log --oneline -1 83a144ba^2     # second parent: the feature branch
git log --oneline -1 83a144ba~1     # same as ^1 (~ always follows first parent)

# the merge base between two branches
git merge-base main new_flask_app

# ranges: how big is this branch, really?
git log --oneline main..new_flask_app | wc -l      # 289
git rev-list --count main..new_flask_app           # same, cheaper

# main as a clean list of features, ignoring each branch's internals
git log --first-parent --oneline main | head -10

# what a PR diff actually compares
git diff --stat main...new_flask_app | tail -1

# who can reach this commit?
git branch --contains 7fe2bb0e
```

`git log --graph --oneline --decorate --all` is the single most useful command in this chapter.
Alias it (`git config --global alias.lg "log --graph --oneline --decorate --all"`) and you will
use it daily.

# Production Walkthrough
How graph thinking shows up in this project's real workflow:

1. **Sizing a PR before opening it.** `git rev-list --count main..HEAD`. Two commits is a review;
   289 is a conversation about scope — which is exactly what happened here.
2. **Reviewing what a branch changed, not what main did.** `git diff main...feat/x` measures from
   the merge base, so unrelated commits that landed on `main` meanwhile do not pollute the diff.
3. **Squash-merge keeps the graph readable.** This project squash-merges
   (`CONTRIBUTING.md` §5): one feature becomes one commit on `main`. `main` stays a near-linear
   list where any feature can be reverted as a unit.
4. **`--first-parent` is how you read `main` after squash-merges.** It walks the trunk and skips
   the internals of each merged branch — a release-notes view of history.
5. **Rebasing to stay current.** `git rebase main` replays your post-merge-base commits onto
   `main`'s new tip. Because the parent changes, the commits are new objects
   ([Chapter 13](13_Rebase.md)).
6. **Deleting merged branches confidently.** `git branch --merged main` lists branches whose tips
   are reachable from `main` — safe to delete, because the commits live on in `main`'s history.

# Debugging Guide

| Symptom | Cause | Fix |
|---|---|---|
| `git log` on a branch "misses" commits | log walks backwards from one tip only | `git log --all --graph`, or name a range |
| `HEAD~1` and `HEAD^1` gave different commits | you are on a **merge** commit | `~` follows first parent; `^n` picks the nth parent |
| `git revert <merge>` fails | git cannot guess which parent to keep | `git revert -m 1 <merge>` (mainline = first parent) |
| PR diff omits changes you expected | PRs diff against the **merge base**, not main's tip | `git diff main...HEAD` reproduces it; `main..HEAD` for endpoints |
| "I deleted the branch and lost the work" | you deleted a pointer; commits are unreachable, not gone | `git reflog`, then `git branch <name> <hash>` |
| `git branch -d` refuses | tip is not reachable from the current branch — real data-loss risk | verify with `git log`, then `-D` if you are certain |
| Graph looks like spaghetti | routine `git pull` created merge commits nobody chose | `pull.rebase true` ([Chapter 02](02_Install_And_Configure.md)) |
| A commit seems to be in no branch | it is unreachable but still an object | `git branch --contains <hash>`; if empty, reflog or `fsck --lost-found` |

# Performance Notes
- **Walking to parents is O(1)**; finding *children* means scanning, which is why
  `git branch --contains` is comparatively slow.
- `git rev-list --count A..B` is cheaper than `git log A..B | wc -l` — it counts without
  formatting or paging.
- Git maintains a **commit-graph file** (`.git/objects/info/commit-graph`) caching parent
  relationships and generation numbers. It makes ancestry queries dramatically faster on large
  histories; enable with `git commit-graph write --reachable` (modern git does it automatically).
- Merge-base computation on deeply divergent branches is the expensive part of a merge, and
  generation numbers in the commit-graph are precisely what optimise it.
- 289 commits is trivial for git. These commands stay instant into the hundreds of thousands.
- `git log --graph` costs more than plain `log` because it must lay out the topology; fine
  interactively, avoid it in scripts.

# Security Considerations
- **Unreachable is not deleted.** A commit removed from a branch remains an object, reachable via
  reflog for ~90 days and readable by anyone with the repo. Removing a secret from `main` does not
  remove it from the repository ([Chapter 33](33_Secrets_And_Leaks.md)).
- **`git log` on one branch is not an audit.** Use `--all` (and consider `--reflog`) or you will
  miss commits that exist on other refs.
- **A force-push abandons commits without deleting them**, and can make a reviewed commit
  disappear from a branch while remaining in the repo. `--force-with-lease` at least refuses when
  the remote has moved.
- **Merge commits can hide changes from a careless review.** Reviewing only the merge commit's
  first-parent diff can conceal what came in on the second parent; review the branch's commits
  or the `...` diff.
- **Timestamps are self-reported and not ordering.** Graph topology is the truth; commit dates are
  attacker- and clock-controlled text.

# Architecture Decisions
- **Parent pointers rather than child pointers.** Children would have to be added *after* a commit
  exists, which would mutate it and break immutability and hashing. One-way edges are the price of
  content addressing.
- **Merge commits are preserved, not flattened.** Git records that two lines existed rather than
  hiding it, which is what makes `git log --first-parent` and honest archaeology possible.
- **This project squash-merges PRs.** One feature = one commit on `main`, so `main` is nearly
  linear and each feature reverts cleanly. The cost is losing the branch's internal commit
  history — accepted, because the PR retains it.
- **`pull.rebase true`** so routine syncing does not litter the graph with merge commits nobody
  intended.
- **Trunk-based over git-flow** ([Chapter 24](24_Branching_Strategies.md)): one long-lived branch,
  short-lived feature branches, tags for releases. A 1–2 person team does not need release
  branches, and every extra long-lived branch is another divergence to reconcile.

# Best Practices
- Learn `git log --graph --oneline --decorate --all`; alias it.
- Size a branch with `git rev-list --count main..HEAD` **before** opening the PR.
- Use `A..B` for "what does B add"; use `git diff A...B` to reproduce a PR diff.
- Use `--first-parent` to read `main` as a list of features.
- Keep branches short-lived. Divergence cost grows with distance from the merge base.
- Prefer `git branch --merged` to decide what is safe to delete.
- Reach for `git merge-base` when reasoning about a confusing merge or rebase; it is the hinge.

# Beginner Mistakes
- **Thinking history is a list** → then being unable to explain merge, rebase, or PR diffs.
- **Assuming `HEAD~2` and `HEAD^2` are the same** → true for ordinary commits, wrong at merges,
  and the mistake surfaces at the worst moment.
- **`git revert <merge>` without `-m`** → fails, and the error reads like a bug rather than an
  ambiguity you must resolve.
- **Believing a deleted branch destroys commits** → it removes a 41-byte pointer; reflog holds
  the commits.
- **Reading `git log` on one branch as the whole history** → misses everything on other refs.
- **Confusing `..` and `...`** → and the meanings *swap* between `log` and `diff`, so guessing
  fails twice.
- **Letting a branch live for weeks** → the merge base recedes, and conflicts grow with it.
- **Trusting commit dates as order** → topology is truth; dates are text.

# Interview Questions
- **Junior:** "Why is git history a graph?" — Every commit stores its parent's hash, so commits
  form nodes and parent links form edges. Edges point backwards, and no cycle is possible because
  a commit's hash includes its parent's. A merge commit has two parents, which is where the graph
  branches and rejoins.
- **Mid:** "Difference between `HEAD~1` and `HEAD^1`?" — `~n` walks back n generations always
  following the *first* parent; `^n` selects the nth parent of this commit. Identical on ordinary
  commits, different on a merge: `^2` is the merged-in branch. It is why `git revert -m 1` exists.
- **Senior:** "What is a merge base and why does everything depend on it?" — The most recent commit
  reachable from both tips. Merge uses it as the three-way base; rebase replays the commits after
  it; `git diff A...B` compares B against it, which is exactly what a PR diff shows. Without it,
  git could not tell your changes from theirs. Computing it on deeply divergent branches is the
  costly part of a merge, which is what commit-graph generation numbers optimise.
- **Staff:** "A reviewed commit vanished from `main` after a force-push. Is it gone, and how would
  you prove what happened?" — Almost certainly not gone: force-push moved a ref, leaving the commit
  unreachable but present as an object, recoverable from any clone's reflog or via
  `fsck --lost-found` for the grace period. Proving it means the ref's history — server-side reflog
  if the host keeps one, plus `git reflog` on any developer's clone, plus GitHub's force-push event
  in the PR timeline. The structural fix is not detective work: protect the branch server-side so
  a non-fast-forward push is refused, and require `--force-with-lease` so a stale-ref push fails
  instead of silently winning. That we cannot enforce that server-side on a private free-tier repo
  is exactly why this project uses a `pre-push` hook plus fork-based contribution instead
  ([Chapter 27](27_Pre_Push_Protection.md)).

### Why interviewers ask these — and the answer that separates levels
| Testing for | Weak answer | What lands |
|---|---|---|
| List or graph mental model? | "History is the list of my commits." | A DAG built from parent hashes; edges point backwards, cycles are impossible, merges have two parents. |
| Do you know navigation precisely? | "`~` and `^` both go back one." | Same on ordinary commits; at a merge `^2` is the merged-in side — and that is why `revert -m 1` is required. |
| Can you reason about reachability? | "The branch was deleted so the work is gone." | Deleting a branch removes a pointer; commits stay as objects, reflog holds them ~90 days, only gc reclaims them. |

**The killer follow-up:** *"Why does a PR diff not show changes that landed on main after you branched?"* — Because a PR diffs against the **merge base**, not main's tip — `git diff main...feature`. It answers "what did this branch change", which is the only question review should ask. Knowing that `...` means merge-base in `diff` but symmetric-difference in `log` is the detail that shows you have actually used the syntax rather than read about it.

# Revision Notes
- History = **DAG**. Edges point **backwards** (child knows parent, never the reverse).
- Parents: **0** root · **1** normal · **2** merge · 3+ octopus.
- **`~n`** = n generations back, **first** parent. **`^n`** = the nth parent. Differ only at merges.
- `^1` = branch you were on · `^2` = branch you merged in ⇒ `git revert -m 1 <merge>`.
- **Merge base** = newest common ancestor. Hinge of merge, rebase, and PR diffs.
- `A..B` = in B not A ("what this branch adds"). `A...B` = symmetric difference in `log`, but **B vs merge base** in `diff`.
- **Delete branch = delete a 41-byte pointer.** Commits survive; reflog ~90 days.
- This repo: merge `83a144ba` has two parents (`^2` = `7fe2bb0e`).
- **`main` ≠ `origin/main`.** `git fetch` moves only the remote-tracking ref. Stale local `main` here reported **296** where the truth was **1**. Name `origin/main`, and sync with `git merge --ff-only`.
- `git log --graph --oneline --decorate --all` — alias it.

# Cheat Sheet
```bash
git log --graph --oneline --decorate --all     # THE command. alias it as `lg`.
git log --first-parent --oneline main          # main as a list of features (skips branch guts)

git cat-file -p <merge> | head -3              # see BOTH parent lines
git log --pretty='%h parents:%p' -1 <commit>   # parents, compactly

git merge-base main feat/x                     # the common ancestor hash
git merge-base --is-ancestor A B && echo yes   # is A an ancestor of B? (scriptable)

git log  main..feat/x                          # commits in feat/x not in main
git rev-list --count main..HEAD                # HOW BIG is this branch? (cheap)
git log  A...B                                 # symmetric difference (log)
git diff A...B                                 # B vs MERGE BASE  ← reproduces a PR diff
git diff A..B                                  # endpoint vs endpoint

git branch --contains <hash>                   # which branches can reach this commit
git branch --merged main                       # safe-to-delete branches
git branch --no-merged main                    # branches with unmerged work

HEAD~1  HEAD~3                                 # generations back, first-parent only
HEAD^1  HEAD^2                                 # nth parent (^2 only exists on a merge)
HEAD@{2}                                       # reflog position, NOT the graph (ch 16)
```

# My ERP Section

| Graph fact | Value in this repository |
|---|---|
| A real merge commit | `83a144ba` — "Merge pull request #15 from umesh29032/new_flask_app", **two** parent lines |
| `83a144ba^2` | `7fe2bb0e` — the feature branch that was merged in |
| Branch divergence | Pre-merge: `main..new_flask_app` = **289 commits** — the number that changed the PR recommendation. Post-merge: `origin/main..new_flask_app` = **1**, while *stale local* `main..new_flask_app` still reports **296** — the ref-staleness trap above |
| Merge strategy | **squash-merge** (`CONTRIBUTING.md` §5): one feature = one commit on `main`, reverts cleanly |
| Pull behaviour | `pull.rebase true` — routine syncing does not create merge commits |
| Branch strategy | trunk-based: `main` + short-lived `feat/*` + tags ([Chapter 24](24_Branching_Strategies.md)) |
| Release marker | tag `erp-v1.0.0` = `90c1f2f3` — a tag is another ref into this same graph |
| Why a hook, not branch protection | server-side protection against force-push/direct-push is paid on private repos ⇒ `git-hooks/pre-push` + fork flow ([Chapter 27](27_Pre_Push_Protection.md)) |

# Practice Tasks
1. Run `git log --graph --oneline --decorate --all | head -30` in this repo. Find the `|\` and
   name the two branches it joins.
2. Run `git cat-file -p 83a144ba | head -3` and count the `parent` lines. Two = merge commit,
   proven from the object itself rather than from the log's drawing.
3. Compare `git log --oneline -1 83a144ba^1` with `83a144ba^2`. Then try `~1` and confirm it
   equals `^1`. You have just felt the distinction that breaks people at merges.
4. Run `git rev-list --count main..new_flask_app` and get 289. Then `git rev-list --count new_flask_app..main`
   and explain the difference in one sentence.
5. In a throwaway repo: branch, commit twice, `git switch main`, commit once, then
   `git merge-base main feat/x`. Draw the graph on paper and mark the base.
6. Delete a branch with unmerged commits using `-D`, then recover it with
   `git reflog` + `git branch <name> <hash>`. Feel that deletion removed a pointer, not the work.

# Homework
- Alias the graph command (`git config --global alias.lg "log --graph --oneline --decorate --all"`)
  and use `git lg` instead of `git log` for a week. The topology becomes automatic.
- Take a real branch and produce, from memory, both "what did I add" (`main..HEAD`) and "what will
  the PR diff show" (`git diff main...HEAD`). Confirm they answer different questions.
- Read `git help revisions` — the full grammar of `~`, `^`, `@{}`, `..`, `...`, `^@`, `^!`. It is
  dense and it is the reference you will return to.
- Create an octopus merge in a throwaway repo (`git merge b1 b2 b3`), inspect the parents, and
  then form a view on why almost nobody should do this.

# Further Reading & Live Resources
- [Pro Git — Branching in a Nutshell](https://git-scm.com/book/en/v2/Git-Branching-Branches-in-a-Nutshell) — the graph, drawn well; free
- [Learn Git Branching](https://learngitbranching.js.org/) — an interactive DAG you manipulate with real commands; the best free tool for this chapter
- [git help revisions](https://git-scm.com/docs/gitrevisions) — the complete `~`/`^`/range grammar
- [git-merge-base reference](https://git-scm.com/docs/git-merge-base) — including `--is-ancestor` and octopus behaviour
- [Commit-graph file format](https://git-scm.com/docs/commit-graph) — how generation numbers speed up ancestry queries
- [Visualizing Git](https://git-school.github.io/visualizing-git/) — watch nodes and refs move as you type
