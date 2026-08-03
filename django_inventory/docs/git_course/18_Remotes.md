---
id: git-course-18-remotes
type: lesson
status: active
owner: handwritten
scope: git — remotes, origin vs upstream, remote-tracking branches, refspecs
anchors: .git/config, .git/refs/remotes, ~/.ssh/config
verified: 2026-08-03
---

# 18 — Remotes (origin, upstream, and the ref that lies to you)

> Part of [Git Course](00_COURSE_OVERVIEW.md). Prev: [17 — Stash & Worktrees](17_Stash_And_Worktrees.md). Next: [19 — Push, Fetch & Pull](19_Push_Fetch_Pull.md).

# Learning Objectives
By the end of this chapter you can:
- explain what a remote actually is (a name for a URL, nothing more)
- distinguish the **three** kinds of branch: local, remote-tracking, and the branch on the server
- explain why `main` and `origin/main` are different refs, and why that difference causes the single most common "git is being weird" moment
- read `.git/config` and say what a refspec does
- set up `origin` + `upstream` for the fork-based flow this project uses
- diagnose a stale remote-tracking ref and prune it

# Purpose
Everything so far has been local. `git init`, commits, branches, the reflog — none of it needs a
network. That is the whole point of a distributed system: your repository is complete on its own.

A **remote** is how two complete repositories exchange objects. And the concept trips people up
for one specific reason: after adding a remote, you suddenly have **two refs with almost the same
name** — `main` and `origin/main` — and nothing on screen explains that they are different things
which update at different times.

This chapter makes that difference concrete, because [Chapter 19](19_Push_Fetch_Pull.md) is
unlearnable without it.

# The Problem
This actually happened in this repository while writing [Chapter 06](06_The_Commit_Graph.md).
A merge had landed on GitHub. I ran a routine range query and got a wrong answer:

```bash
git rev-list --count main..new_flask_app          # 296
git rev-list --count origin/main..new_flask_app   # 1
```

**296 versus 1.** Same repo, same syntax, one wrong by a factor of 296. Nothing was broken. Local
`main` was five commits behind the merge, because **nothing had moved it**. `git fetch` had
updated `origin/main`; local `main` was exactly where it had been left weeks earlier.

If you cannot explain that in one sentence, this chapter is the missing sentence. And the failure
mode is nasty precisely because it is *silent* — no error, just a confidently wrong number.

# Theory (from zero)

### A remote is a name for a URL
That is all. `origin` is not special, not primary, not a server — it is a nickname stored in
`.git/config`:

```bash
git remote -v
# origin  git@github-personal:umesh29032/umesh-personal.git (fetch)
# origin  git@github-personal:umesh29032/umesh-personal.git (push)
```

```ini
[remote "origin"]
    url = git@github-personal:umesh29032/umesh-personal.git
    fetch = +refs/heads/*:refs/remotes/origin/*
```

`origin` is merely the default name `git clone` assigns. You can rename it, delete it, or have
five remotes. Nothing in git privileges the word.

Note the URL uses `github-personal`, not `github.com` — an SSH host alias
([Chapter 02](02_Install_And_Configure.md)) that selects which key and therefore which GitHub
account authenticates.

### The three kinds of branch — the core of this chapter
| Kind | Example | Lives | Who moves it |
|---|---|---|---|
| **Local branch** | `main` | `.git/refs/heads/main` | **you** — by committing, merging, or resetting |
| **Remote-tracking** | `origin/main` | `.git/refs/remotes/origin/main` | **`git fetch`** — it is a cached snapshot of the server |
| **The server's branch** | `main` on GitHub | on the server | whoever pushes |

Three things, two of which are on your disk. Read them directly:

```bash
cat .git/refs/heads/main            # 7c256f50…   ← YOUR main
cat .git/refs/remotes/origin/main   # 83a144ba…   ← the server's main, as of your last fetch
```

Two files, two different hashes. That is the 296-versus-1 bug, visible as bytes on disk.

Three rules that follow, and they are worth memorising:

1. **`git fetch` never touches your local branches.** It only updates `refs/remotes/*`. This is
   why fetch is always safe.
2. **`origin/main` is a cache, not live truth.** It is only as fresh as your last fetch. It can be
   stale, and it will not tell you.
3. **Local `main` moves only when you move it** — `merge`, `rebase`, `reset`, or a commit. There is
   no background sync.

### Upstream (tracking) — what `git status` compares against
A local branch can *track* a remote-tracking branch. That relationship is what produces:

```
Your branch is ahead of 'origin/main' by 2 commits.
```

`git status` is comparing your local branch to its **cached** upstream ref. So "ahead by 2" means
*"ahead of what I last fetched"* — not necessarily ahead of the server right now. Fetch, then
trust it.

```bash
git branch -vv                     # every local branch + its upstream + ahead/behind
git push -u origin feat/x          # -u sets the upstream while pushing
git branch --set-upstream-to=origin/main main
```

**Terminology warning, because this genuinely confuses people.** The word *upstream* means two
different things:

- **`@{upstream}`** — the remote-tracking ref a local branch is configured against (usually
  `origin/<same-name>`).
- **the `upstream` remote** — a *convention*, in fork workflows, for naming the original
  repository you forked from.

Same word, unrelated meanings. Context tells you which.

### Refspecs — the mapping nobody reads
```
fetch = +refs/heads/*:refs/remotes/origin/*
        └── source ──┘ └──── destination ────┘
```

Read it as: *"take every branch on the server, and store it locally under
`refs/remotes/origin/`."* The leading `+` means "allow non-fast-forward updates" — necessary
because the server's branch can be force-pushed, and your cache must be able to follow.

This is also why `git fetch` cannot clobber your work: the destination is `refs/remotes/*`, and
your branches live in `refs/heads/*`. Different namespace, by design.

### The fork flow's two remotes
For the model this project uses for collaborators ([Chapter 20](20_Forks_And_The_Fork_Flow.md)):

```bash
git clone git@github.com:<them>/umesh-personal.git     # origin   = THEIR fork (they can push)
git remote add upstream git@github.com:umesh29032/umesh-personal.git   # upstream = the real repo
```

- **`origin`** — their fork. Push here.
- **`upstream`** — the canonical repo. Fetch here; never push (they have Read access, so they
  could not anyway — that is the point).

The daily sync, and why the flag matters:

```bash
git fetch upstream
git switch main
git merge --ff-only upstream/main
```

**`--ff-only` refuses to create a merge commit.** If it errors, your local `main` has diverged and
you should reset it to upstream rather than merge — keeping `main` a clean mirror instead of
quietly growing its own history.

> 💡 **Samjho aise:** Remote = **kisi ke ghar ka pata, ek naam ke saath**. `origin` koi khaas
> cheez nahi — bas `git clone` ne wo naam rakh diya.
>
> Ab teen cheezein alag samajho: `main` = **tumhari** copy. `origin/main` = **server ki copy ki
> photo**, jo tumne pichhli baar `fetch` pe li thi. Aur server ka asli `main` = wahan.
>
> Photo purani ho sakti hai, aur wo tumhe **batayegi nahi**. Isliye `main..HEAD` ne 296 bola jab
> sach 1 tha. Pehle `git fetch`, phir bharosa. Aur yaad rakho: **`fetch` tumhari branch ko chhoota
> hi nahi** — sirf photo update karta hai. Isliye fetch hamesha safe hai.

# Real World Example (this repo)
The real ref state of this repository, which is the whole chapter in four lines:

```bash
git rev-parse --short main origin/main new_flask_app origin/new_flask_app
```
```
7c256f50      ← local main            (stale: never moved after the merge)
83a144ba      ← origin/main           (has PR #15's merge commit)
42a2ecc4      ← local new_flask_app   (one commit ahead)
83a144ba      ← origin/new_flask_app  (does not have that commit yet)
```

Four refs, three distinct hashes, and every "surprising" git answer in this repo right now falls
out of them:

- `main..new_flask_app` = **296** — measured against stale local `main`.
- `origin/main..new_flask_app` = **1** — the truth: one unpushed commit.
- `git status` on `new_flask_app` says *ahead of `origin/new_flask_app` by 1* — correct, because
  `42a2ecc4` has not been pushed.

The one remote configured here:

```bash
git remote -v
# origin  git@github-personal:umesh29032/umesh-personal.git (fetch)
# origin  git@github-personal:umesh29032/umesh-personal.git (push)
```

One remote, `origin`, via the `github-personal` SSH alias. There is no `upstream` remote because
the owner works directly on the canonical repository — the second remote appears only for
collaborators working from a fork.

**The fix for the stale ref, for the record:**
```bash
git fetch origin
git switch main && git merge --ff-only origin/main
git rev-list --count main..new_flask_app     # 1  ✓
```

# Visual Diagram
```
  GITHUB (umesh29032/umesh-personal)
  ┌──────────────────────────────────┐
  │  main          83a144ba          │
  │  new_flask_app 83a144ba          │
  └──────────────┬───────────────────┘
                 │  git fetch  (SAFE: only touches refs/remotes/*)
                 ▼
  YOUR CLONE
  ┌───────────────────────────────────────────────────────────────┐
  │  .git/refs/remotes/origin/main          83a144ba   ← a CACHE   │
  │  .git/refs/remotes/origin/new_flask_app 83a144ba              │
  │  ─────────────────────────────────────────────────────────    │
  │  .git/refs/heads/main                   7c256f50   ← STALE     │
  │  .git/refs/heads/new_flask_app          42a2ecc4   ← +1 local  │
  └───────────────────────────────────────────────────────────────┘
        ▲                                          │
        │  YOU move these (commit/merge/reset)     │  git push
        │  NOTHING else does                       ▼

   main..new_flask_app          = 296   ← against the STALE local ref
   origin/main..new_flask_app   = 1     ← the truth

   refspec:  +refs/heads/*  :  refs/remotes/origin/*
             └─ on server ─┘    └── your cache ──┘
             different namespace ⇒ fetch can never clobber your branches

   FORK FLOW (collaborators)
     origin   = their fork      → push here
     upstream = canonical repo  → fetch here, never push
     sync:  git fetch upstream && git merge --ff-only upstream/main
```

# Practical — see the three refs for yourself
```bash
cd /home/tech/umesh-personal

# 1. what remotes exist, and where do they point?
git remote -v
git remote show origin | head -12          # branches, tracking, push config

# 2. the three kinds of branch, side by side
git branch                # local
git branch -r             # remote-tracking (origin/*)
git branch -a             # both
git branch -vv            # local + upstream + ahead/behind   ← the useful one

# 3. read the refs as FILES — this is the whole lesson
cat .git/refs/heads/main
cat .git/refs/remotes/origin/main
# different hashes = local main is stale

# 4. the refspec that makes fetch safe
git config --get-all remote.origin.fetch
# +refs/heads/*:refs/remotes/origin/*

# 5. prove fetch is non-destructive
git rev-parse main            # note the hash
git fetch origin              # updates refs/remotes/* only
git rev-parse main            # UNCHANGED

# 6. ranges against the right ref
git rev-list --count main..new_flask_app
git rev-list --count origin/main..new_flask_app     # ← the honest one

# 7. remote-tracking refs that no longer exist upstream
git remote prune origin --dry-run
```

Step 5 is the reassurance worth internalising: fetching cannot hurt you. Every dangerous thing
happens at `merge`, `rebase`, `reset` or `push` — never at `fetch`.

# Production Walkthrough
1. **Fetch before you reason.** Any question involving `origin/*` starts with `git fetch`, or the
   answer is about a cached past.
2. **Name `origin/main` explicitly in range queries.** `git rev-list --count origin/main..HEAD` to
   size a PR; `git diff origin/main...HEAD` to reproduce its diff. Using bare `main` asks about
   your local copy, which may be months old.
3. **Keep local `main` a pure mirror.** `git merge --ff-only origin/main`. Never commit directly on
   it — this repo's `pre-push` hook refuses pushing to `main` anyway
   ([Chapter 27](27_Pre_Push_Protection.md)).
4. **Onboarding a collaborator** ([`CONTRIBUTING.md`](../../../CONTRIBUTING.md) §9): they clone
   their fork as `origin`, add the canonical repo as `upstream`, and sync with
   `git fetch upstream && git merge --ff-only upstream/main`.
5. **Prune dead branches periodically.** `git fetch --prune` (or `fetch.prune true`) removes
   `origin/feat/x` after that branch is deleted post-merge. Without it, `git branch -r` slowly
   becomes a graveyard.
6. **Trust `git status`'s ahead/behind only after a fetch.** It compares against the cache.

# Debugging Guide

| Symptom | Cause | Fix |
|---|---|---|
| Range query gives an absurd number | you named local `main`, which is stale | `git fetch`; use `origin/main`; sync with `--ff-only` |
| `git status` says "up to date" but the server has moved | it compares against the **cached** ref | `git fetch`, then re-read |
| `origin/feat/x` still listed after the branch was deleted | remote-tracking refs are not auto-pruned | `git fetch --prune`, or set `fetch.prune true` |
| `fatal: 'origin' does not appear to be a git repository` | no remote, or a typo'd name | `git remote -v`; `git remote add origin <url>` |
| Push asks for a password | HTTPS remote instead of SSH | `git remote set-url origin git@github.com:…` |
| Push rejected: "must be a collaborator" from `gh`, but `git push` works | `git` uses SSH, `gh` uses its own token/account | `gh auth status` ([Ch 02](02_Install_And_Configure.md)) |
| `git merge --ff-only` fails | local branch has commits the remote lacks | inspect with `git log origin/main..main`; reset if `main` should be a mirror |
| Two remotes, wrong one pushed to | `-u` set the upstream to the wrong remote | `git branch -vv`, then `git branch --set-upstream-to=…` |
| Cloned but `git branch` shows one branch | clone creates one local branch; the rest are remote-tracking | `git branch -a`; `git switch <name>` creates a local one |

# Performance Notes
- **`git fetch` transfers only missing objects**, negotiated against what you already have — not
  the whole history. First clone of this repo moves ~97 MB; a daily fetch moves kilobytes.
- `git fetch --prune` costs nothing extra; it only deletes local refs.
- **Shallow clones** (`--depth=1`) are much faster but cripple history operations —
  `git log`, `blame` and `bisect` all need ancestry. Reasonable in CI, poor for development.
  This project's CI uses `fetch-depth: 0` deliberately, because the design-system ratchet needs
  a merge base ([Chapter 28](28_CI_With_GitHub_Actions.md)).
- **`git fetch --all` fetches every remote**; with `origin` plus `upstream` that is two network
  round trips. Fetch the one you need.
- SSH connection setup dominates a small fetch. `ControlMaster auto` in `~/.ssh/config` reuses the
  connection.
- Remote-tracking refs are 41-byte files. Thousands of them cost nothing.

# Security Considerations
- **The remote URL decides which credential is used.** Here, `github-personal` selects an SSH key
  and therefore an account. Change the URL and you silently change identity
  ([Chapter 02](02_Install_And_Configure.md)).
- **A remote can be added by anyone with write access to `.git/config`.** A malicious or careless
  extra remote plus a push is an exfiltration path; `git remote -v` is worth an occasional glance.
- **`git fetch` executes no code from the server** — it transfers objects. But `git submodule
  update` and some hooks can, so a repository is not automatically inert
  ([Chapter 36](36_Monorepo_Submodules_Subtrees.md)).
- **Fetching is safe; merging is a decision.** `git pull` bundles both, which is why this repo sets
  `pull.rebase true` and prefers explicit fetch-then-merge for anything important.
- **Never push to `upstream` in a fork flow.** With Read access you cannot — and that is precisely
  the free, server-side protection this project relies on instead of paid branch protection
  ([Chapter 27](27_Pre_Push_Protection.md)).
- **A stale `origin/main` can make a security review look clean.** Auditing "what changed" against
  a cached ref is auditing the past. Fetch first.

# Architecture Decisions
- **Remote-tracking refs live in a separate namespace** (`refs/remotes/*` vs `refs/heads/*`). That
  single decision is what makes `git fetch` unconditionally safe, and it is why git can offer a
  read-only network operation at all.
- **No automatic synchronisation.** Git never moves your branches behind your back. The cost is
  the stale-ref confusion this chapter exists to prevent; the benefit is that no network event can
  ever change your working state.
- **`origin` is a convention, not a keyword.** Nothing in git privileges it, which is what allows
  the fork flow's `origin`/`upstream` pair to exist without special support.
- **This project uses one remote for the owner, two for collaborators.** The owner pushes to the
  canonical repo; collaborators cannot, because Read access plus a fork is the enforcement layer
  ([Chapter 20](20_Forks_And_The_Fork_Flow.md)).
- **An SSH host alias in the remote URL** rather than per-command key flags: the account choice
  becomes declarative and impossible to forget, which matters on a machine with two GitHub
  accounts.
- **`--ff-only` for syncing `main`.** Refusing to merge is a feature: it surfaces drift instead of
  hiding it inside a merge commit nobody chose.

# Best Practices
- `git fetch` before any question about the remote. Cheap, safe, and prevents wrong answers.
- Write `origin/main` explicitly in range queries; bare `main` means your local copy.
- Keep local `main` a mirror: `git merge --ff-only origin/main`, never commit on it.
- Set `fetch.prune true` globally so dead remote branches disappear on their own.
- Use `git branch -vv` to see, in one screen, every branch's upstream and drift.
- Check `git remote -v` when authentication behaves oddly — the URL is the credential selector.
- In a fork flow, push to `origin`, fetch from `upstream`, and never mix them up.

# Beginner Mistakes
- **Thinking `main` and `origin/main` are the same ref** → the 296-versus-1 error in this very
  repository.
- **Believing `git fetch` changes your files** → it cannot; it writes only to `refs/remotes/*`.
- **Trusting "up to date" without fetching** → `git status` compares against a cache.
- **Assuming `origin` is special** → it is a nickname; rename it and nothing breaks.
- **Using `git pull` reflexively** → that is fetch **plus** merge, so it makes a decision for you.
  See [Chapter 19](19_Push_Fetch_Pull.md).
- **Committing directly on local `main` in a fork flow** → `--ff-only` then fails and the mirror is
  broken.
- **Never pruning** → `git branch -r` fills with branches deleted months ago.
- **Confusing the two meanings of "upstream"** → the tracking ref versus the fork's parent remote.

# Interview Questions
- **Junior:** "What is a remote?" — A named URL for another copy of the repository, stored in
  `.git/config`. `origin` is just the default name `git clone` assigns; nothing in git treats it
  specially.
- **Mid:** "Difference between `main` and `origin/main`?" — `main` is your local branch, which only
  you move. `origin/main` is a *remote-tracking* ref: a cached snapshot of the server's branch,
  updated by `git fetch` and nothing else. They routinely differ, and `git status`'s ahead/behind
  compares against the cache, so it is only as fresh as your last fetch.
- **Senior:** "Why is `git fetch` safe when `git pull` is not?" — Fetch writes only to
  `refs/remotes/*`, a different namespace from your branches in `refs/heads/*`, so it cannot alter
  your working tree or local refs. Pull is fetch **plus** an integration step — merge or rebase —
  and that second half can conflict, create commits, or rewrite your branch. Separating them means
  you can always look before deciding.
- **Staff:** "A teammate says a security-relevant change 'isn't in main'. How do you verify?" — Do
  not trust any local ref: `git fetch --prune`, then check against `origin/main`, and ideally
  confirm on the host itself, because a remote-tracking ref is a cache and a local branch is
  whatever that person last left it as. Then verify with reachability rather than a file diff —
  `git branch -r --contains <sha>` and `git merge-base --is-ancestor <sha> origin/main` — because a
  commit can exist in the repo, be visible in `git log --all`, and still not be reachable from the
  deployed branch. The structural fix is to stop asking humans: gate it in CI against
  `origin/main`, and deploy from an immutable tag rather than a branch name, so "what is in
  production" is a hash and not an opinion.

### Why interviewers ask these — and the answer that separates levels
| Testing for | Weak answer | What lands |
|---|---|---|
| Do you know refs from magic? | "`origin` is the server." | A name for a URL in `.git/config`; `origin` is only `clone`'s default and can be renamed freely. |
| The three-branch model? | "`origin/main` is main on GitHub." | It is a local **cache** of the server's branch, moved only by fetch; the server's actual branch is a third thing you have not looked at. |
| Why fetch is safe? | "Fetch just downloads stuff." | Separate namespace: `refs/remotes/*` vs `refs/heads/*`, so fetch cannot touch your branches — every risk lives in the integration step. |

**The killer follow-up:** *"`git status` says up to date. Is it?"* — Only relative to your last fetch. It compares your branch against the cached remote-tracking ref, not the server, so the answer is "up to date with what I last saw." Fetch, then re-read. Anyone who has been burned by a stale ref answers this immediately; anyone who has not says "yes".

# Revision Notes
- A remote = **a name for a URL** in `.git/config`. `origin` is just `clone`'s default.
- **Three branch kinds:** local (`refs/heads/*`, you move it) · remote-tracking (`refs/remotes/*`, **fetch** moves it) · the server's (elsewhere).
- **`git fetch` is always safe** — different namespace, so it cannot touch `refs/heads/*`.
- **`origin/main` is a CACHE.** Stale until you fetch, and it will not warn you.
- Nothing moves local `main` automatically. Sync with `git merge --ff-only origin/main`.
- Refspec `+refs/heads/*:refs/remotes/origin/*` — `+` allows non-fast-forward cache updates.
- This repo, right now: `main` `7c256f50` (stale) · `origin/main` `83a144ba` · `new_flask_app` `42a2ecc4` ⇒ **296 vs 1**.
- Fork flow: `origin` = your fork (push) · `upstream` = canonical (fetch only).
- "upstream" means two things: the tracking ref `@{upstream}`, and the fork's parent remote.

# Cheat Sheet
```bash
git remote -v                              # names → URLs (fetch + push)
git remote show origin                     # branches, tracking, push config
git remote add upstream <url>              # fork flow: the canonical repo
git remote set-url origin <url>            # e.g. HTTPS → SSH
git remote rename origin upstream          # it's just a name
git remote prune origin --dry-run          # dead remote-tracking refs

git branch                                 # local
git branch -r                              # remote-tracking
git branch -a                              # both
git branch -vv                             # + upstream + ahead/behind   ← the useful one
git branch --set-upstream-to=origin/main main

git fetch origin                           # SAFE: updates refs/remotes/* only
git fetch --prune                          # ...and delete refs for branches that are gone
git fetch upstream                          # fork flow
git config --global fetch.prune true       # prune automatically, forever

git merge --ff-only origin/main            # keep local main a pure mirror (refuses to diverge)
git rev-list --count origin/main..HEAD     # size a PR against the REAL trunk
git diff origin/main...HEAD                # reproduce the PR diff (merge-base)

cat .git/refs/heads/main                   # your main
cat .git/refs/remotes/origin/main          # the cached server main
git config --get-all remote.origin.fetch   # the refspec
```

# My ERP Section

| Fact | This repository |
|---|---|
| Remotes | one: `origin` → `git@github-personal:umesh29032/umesh-personal.git` |
| SSH alias in the URL | `github-personal` — selects the personal key, hence account `umesh29032` |
| `main` (local) | `7c256f50` — **stale**, never fast-forwarded after PR #15 |
| `origin/main` | `83a144ba` — has the merge |
| `new_flask_app` | `42a2ecc4` local vs `83a144ba` on origin ⇒ 1 unpushed commit |
| The consequence | `main..new_flask_app` = **296**, `origin/main..new_flask_app` = **1** |
| Collaborator setup | `origin` = their fork, `upstream` = this repo; Read access means they cannot push here ([Ch 20](20_Forks_And_The_Fork_Flow.md)) |
| Sync command of record | `git fetch upstream && git merge --ff-only upstream/main` — `CONTRIBUTING.md` §9 |
| CI note | `actions/checkout` with `fetch-depth: 0`, because the ratchet needs a real merge base ([Ch 28](28_CI_With_GitHub_Actions.md)) |

# Practice Tasks
1. In this repo, `cat .git/refs/heads/main` and `cat .git/refs/remotes/origin/main`. Two files,
   two hashes. Say out loud which one `git fetch` updates.
2. Run both range queries (`main..new_flask_app` and `origin/main..new_flask_app`) and explain the
   difference in one sentence without looking at this chapter.
3. `git rev-parse main`, then `git fetch origin`, then `git rev-parse main` again. Confirm it did
   **not** move. That is why fetch is safe.
4. `git branch -vv` and read the ahead/behind for every branch. Note that those numbers are
   relative to your cache.
5. Rename your remote (`git remote rename origin upstream`), run `git fetch upstream`, confirm
   everything works, then rename it back. `origin` is not magic.
6. Fix the stale ref for real: `git fetch origin && git switch main && git merge --ff-only origin/main`,
   then re-run task 2 and watch 296 become 1.

# Homework
- Set `fetch.prune true` globally, then run `git branch -r` in your oldest repository and see how
  many dead branches disappear.
- Simulate the fork flow properly: fork any public repo, clone your fork as `origin`, add the
  original as `upstream`, and practise `git fetch upstream && git merge --ff-only upstream/main`.
  This is the exact loop a collaborator on this project will run.
- Read `git help config` on `remote.<name>.fetch` and write a refspec that fetches **only** `main`
  into a custom local namespace. Then explain why the default uses a wildcard.
- Make `git merge --ff-only` fail on purpose: commit something on local `main`, then try to sync.
  Read the error and decide what you would do in a real fork flow.

# Further Reading & Live Resources
- [Pro Git — Working with Remotes](https://git-scm.com/book/en/v2/Git-Basics-Working-with-Remotes) — add, inspect, fetch, prune; free
- [Pro Git — Remote Branches](https://git-scm.com/book/en/v2/Git-Branching-Remote-Branches) — the clearest explanation of remote-tracking refs anywhere
- [git-fetch reference](https://git-scm.com/docs/git-fetch) — refspecs, `--prune`, `--depth`
- [The refspec, explained](https://git-scm.com/book/en/v2/Git-Internals-The-Refspec) — the `+refs/heads/*:refs/remotes/origin/*` line, decoded
- [GitHub Docs — configuring a remote for a fork](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/configuring-a-remote-repository-for-a-fork) — the `origin`/`upstream` convention
- [git-remote reference](https://git-scm.com/docs/git-remote) — every subcommand, including `set-url --push`
