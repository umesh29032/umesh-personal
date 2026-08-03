---
id: git-course-19-push-fetch-pull
type: lesson
status: active
owner: handwritten
scope: git, version control — moving commits between your clone and a remote; tracking branches, upstream config, non-fast-forward rejections, safe force-push
anchors: CONTRIBUTING.md, git-hooks/pre-push, git-hooks/install.sh, .github/workflows/ci.yml
verified: 2026-08-03
---

# 19 — Push, Fetch & Pull (three verbs that move commits between repositories)

> Part of [Git Course](00_COURSE_OVERVIEW.md). Prev: [18 — Remotes](18_Remotes.md). Next: [20 — Forks & the Fork-Based Flow](20_Forks_And_The_Fork_Flow.md).

# Learning Objectives
By the end of this chapter you can:
- explain the difference between `main`, `origin/main` and the branch on the server
- predict exactly what `fetch`, `pull` and `push` change — and what they leave alone
- read `git status -sb` / `git branch -vv` and say how far ahead or behind you are
- fix a `non-fast-forward` rejection without losing a commit
- use `--force-with-lease`, and say why plain `--force` is banned on shared branches here

# Purpose
[Ch 18](18_Remotes.md) introduced the *remote* — a second repository somewhere else. This chapter is the traffic between them. Three verbs do all of it: **`fetch`** brings commits down, **`push`** sends them up, and **`pull`** is `fetch` plus an integration step that beginners run blindly and are then confused by. Understanding the third requires learning the first two separately.

# The Problem
You commit for a week, type `git push`, and git shouts:

```
 ! [rejected]        main -> main (non-fast-forward)
error: failed to push some refs to 'github-personal:umesh29032/umesh-personal.git'
hint: Updates were rejected because the tip of your current branch is behind
```

You search, find `git push --force`, run it — and a teammate's afternoon is gone from the server with no error and no warning. Or the quiet version this repo is *living in right now*: local `main` says `7c256f50 add a js of billing` while the server's `main` is **295 commits** further along, and no amount of `git pull` on another branch ever fixed it. Same root cause both times: **not knowing which of the three pointers you are looking at.**

# Theory (from zero)

### There are three pointers, not two
Say `main` out loud and you could mean three different things:

| Pointer | Lives where | Who moves it |
|---|---|---|
| `main` | your clone, `.git/refs/heads/main` | **you** — commit, merge, reset |
| `origin/main` | your clone, `.git/refs/remotes/origin/main` | **`git fetch`** only |
| `refs/heads/main` | on GitHub | **`git push`**, from anyone |

`origin/main` is a **remote-tracking branch** — not on the server, but a **local cache of what the server looked like the last time you talked to it.** You cannot commit onto it, and nothing moves it behind your back. That is why it can be badly stale with no error: it is a photograph, and photographs do not refresh themselves.

### `git fetch` — download, touch nothing you can see
`git fetch origin` asks what refs the remote has, downloads the objects you lack ([Ch 05](05_How_Git_Stores_Everything.md)), and moves your `origin/*` refs to match. It does **not** touch your working directory, your index, or any branch you work on — the only network command in git that cannot destroy state.

### `git push` — upload, then ask the server to move its pointer
`push` sends the objects the server lacks, then asks it to move `refs/heads/<branch>` to your commit. The server agrees **only if that is a fast-forward** — the commit it points at must be an ancestor of yours, so nothing already there is orphaned. If someone else pushed meanwhile, your commit is not a descendant of theirs, the move would lose their work, and it refuses. `non-fast-forward` is git protecting a stranger's commits from you.

### The refspec — the colon nobody explains
`git push origin feat/x` is short for `git push origin feat/x:refs/heads/feat/x` — "make the server's `feat/x` point where mine does". Once you see `<local>:<remote>`, two magical commands turn obvious: `git push origin HEAD:main` pushes your current commit onto the server's `main`, and `git push origin :feat/dead` — empty source — **deletes** the server's branch.

### Upstream tracking — what `-u` writes
`git push -u origin feat/my-thing` pushes *and* records two `.git/config` lines pairing the branches. In this repo they really exist:
```
branch.new_flask_app.remote origin
branch.new_flask_app.merge refs/heads/new_flask_app
```
That pairing is what makes bare `git push`, bare `git pull`, and the `[ahead 1]` counter possible. Without it: `fatal: The current branch X has no upstream branch.` Push with `-u` **once** and the problem never returns.

### `git pull` = `git fetch` + integrate (the confusing one)
`pull` is not a primitive. It is `fetch`, then an integration whose *kind* depends on config:

| Command | Second half | Result |
|---|---|---|
| `git pull` (default) | `git merge` | a merge commit if both sides moved |
| `git pull --rebase` | `git rebase` | replays your commits on top; linear ([Ch 13](13_Rebase.md)) |
| `git pull --ff-only` | fast-forward or nothing | **refuses** rather than inventing a commit |

Make `--ff-only` the habit: it fails loudly instead of silently creating history you never asked for. `CONTRIBUTING.md` §9 uses exactly that, and a *failure* is information — your `main` drifted and should be reset to the remote, not merged with it.

> 💡 **Samjho aise:** `origin/main` ek **purani photo** hai jo tumne server ki li thi. `git fetch` = nayi photo lena — deewaar pe lagi photo badlegi, par **ghar ka saaman waisa hi rahega**. `git pull` = photo dekhkar ghar ka saaman actually badalna. `git push` = apni photo bhejkar server se kehna "record isse badal do" — server maanega sirf tab jab kisi aur ka saaman gum na ho. Isliye `fetch` kabhi nuksaan nahi karta, aur `push --force` sabse khatarnaak hai.

### ahead / behind, and "diverged"
"Ahead 1, behind 3" = 1 commit you have that the tracking ref lacks, 3 it has that you lack; git walks both tips back to the merge base ([Ch 06](06_The_Commit_Graph.md)). **Both non-zero = diverged**, the only state needing a decision: merge, rebase, or reset.

### `--force` vs `--force-with-lease`
After rewriting your own commits ([Ch 14](14_Interactive_Rebase.md)) a non-fast-forward is *expected*, so you must override:
```bash
git push --force              # "match me, whatever is there"                  ⛔
git push --force-with-lease   # "…ONLY if the server is still where my last
                              #  fetch says it is"                             ✅
```
The lease sends your cached `origin/<branch>` value; if someone pushed since your last fetch it is stale, the push is rejected, and their commit survives. Same power, one guard rail — hence `CONTRIBUTING.md` §10: *"Plain `--force` overwrites work you cannot see."* **Undo a bad force-push:** the commits are unreferenced, not deleted, so on a machine that had them ([Ch 16](16_Reflog.md)) `git reflog show origin/main` gives the old SHA and `git push --force-with-lease origin <that-sha>:main` puts it back.

# Real World Example (this repo)
Local `main` here is a textbook stale bookmark. Real output, today:
```
$ git branch -vv
  main          7c256f50 add a js of billing
* new_flask_app 42a2ecc4 [origin/new_flask_app: ahead 1] chore(repo): stop tracking database dumps
```
`main` has **no bracket at all** — no upstream configured, so git cannot even report its drift. Every pointer, resolved by hand:
```
main            7c256f50      new_flask_app         42a2ecc4
origin/main     83a144ba      origin/new_flask_app  83a144ba     upstream/main  83a144ba

$ git rev-list --count main..origin/main   # behind → 295
$ git rev-list --count origin/main..main   # ahead  → 0
```
**295 behind, 0 ahead** — local `main` is a pure subset of the server's, so nothing local is at risk and a fast-forward is correct: `git merge --ff-only origin/main`. Now proof that a tracking ref is only a cache, by asking the server (a network read that writes nothing locally):
```
$ git ls-remote --heads origin
83a144ba3fad222bdd3b85d7b5f67a7fb0604ed2	refs/heads/main
83a144ba3fad222bdd3b85d7b5f67a7fb0604ed2	refs/heads/new_flask_app
```
`83a144ba` is the merge of **PR #15** (`new_flask_app` → `main`); the server has both branches parked on it.

# Visual Diagram
```
      YOUR CLONE  (/home/tech/umesh-personal)         GITHUB
  ┌──────────────────────────────────────────┐   ┌──────────────────────┐
  │ working tree · index · local branches    │   │ refs/heads/main      │
  │    main ──► 7c256f50                     │   │      ──► 83a144ba    │
  │    new_flask_app ──► 42a2ecc4            │   │ refs/heads/          │
  │                                          │   │  new_flask_app       │
  │ remote-tracking (a CACHE, not the server)│   │      ──► 83a144ba    │
  │    origin/main          ──► 83a144ba     │   └──────────────────────┘
  │    origin/new_flask_app ──► 83a144ba     │
  └──────────────────────────────────────────┘
       ▲                 │        ▲
 fetch ┘ moves ONLY the  │        └─ push: sends objects, asks the server to move
 origin/* refs. Files &  │           its ref. Allowed only if fast-forward.
 branches untouched.     │
 pull = fetch THEN merge/rebase ← the only step that touches your files
 main is 295 BEHIND origin/main, 0 ahead → merge --ff-only is safe here
```

# Practical — driving all three by hand
```bash
git fetch --all --prune                # safe: moves origin/* only; --prune drops refs
                                       # whose server branch is gone (merged PRs)
git status -sb | head -1               # ## new_flask_app...origin/new_flask_app [ahead 1]
git log --oneline HEAD..origin/main    # what the server has that I don't
git push -u origin feat/my-thing       # first push: uploads AND records the upstream pair
git pull --ff-only                     # integrate only if no new commit is needed
git config pull.ff only                # make --ff-only this repo's default
```
Deletion and tags — the two pushes people get wrong:
```bash
git push origin --delete feat/merged   # remove the SERVER's branch
git branch -d feat/merged              # remove YOUR local branch (a separate act!)
git push --follow-tags                 # plain git push sends NO tags
```

# Production Walkthrough
The real daily loop (`CONTRIBUTING.md` §9), with the network step named at each point:

1. **Sync the trunk** — `git fetch upstream && git switch main && git merge --ff-only upstream/main`. Fetch moves `upstream/main`; the ff-only merge moves `main`. If it refuses, reset to the remote rather than merge.
2. **Branch, work, commit** — no network. The `commit-msg` hook checks Conventional Commits ([Ch 25](25_Conventional_Commits.md)).
3. **First push** — `git push -u origin feat/their-thing`. The `pre-push` hook runs *here*; target `main` by mistake and `git-hooks/pre-push` prints `✖ BLOCKED: direct push to protected branch 'main'.`
4. **Open a PR** ([Ch 21](21_Pull_Requests.md)) — CI runs on the pushed branch, not your laptop.
5. **Review changes** — commit, `git push`. If you rebased first: `--force-with-lease`.
6. **Squash-merge, clean up** — `git push origin --delete feat/their-thing`, then `git fetch --prune`.

# Debugging Guide
| Symptom | Cause | Fix |
|---|---|---|
| `! [rejected] … (non-fast-forward)` | the remote holds commits you lack | `git pull --rebase` (or `--ff-only`), re-push. `--force` is never first |
| `fatal: … has no upstream branch` | never pushed with `-u` | `git push -u origin <branch>` |
| A stray `Merge branch 'main' of …` | default `pull` is a merge | `git config pull.ff only` |
| `origin/main` never moves | `pull` integrates only the current branch | `git fetch --all --prune` |
| `main` shows no ahead/behind | no upstream for `main` (real, here) | `git branch -u origin/main main` |
| `Permission denied (publickey)` | wrong SSH key | check the host alias — this repo uses `github-personal` |
| `✖ BLOCKED: direct push to protected branch` | the `pre-push` hook worked | branch and open a PR |
| `remote: Repository not found` on push | read-only access or wrong account | push to your **fork** ([Ch 20](20_Forks_And_The_Fork_Flow.md)) |

# Performance Notes
Real numbers here (`git count-objects -vH`): `count: 4873`, `size: 26.19 MiB`, `in-pack: 25975`, `size-pack: 63.66 MiB` — ~90 MiB of objects in a ~97 MB `.git`, against **2,407** tracked files.
- **The first clone is the expensive one** — it transfers the pack (~64 MiB). Later fetches send only missing objects, so fetch cost scales with *new commits*, not repo size.
- **Shallow options are for CI, not humans.** `--depth 1` and `--filter=blob:none` skip history; your laptop needs it for `log`, `blame` and `bisect` ([Ch 35](35_Bisect.md)).
- **Big files drive the cost.** Commit `42a2ecc4` untracked **2,954** files (2 `pg_dump` + 2,952 `node_modules`), 331,748 deletions — yet those objects remain in the pack, because history is append-only ([Ch 37](37_Large_Files_And_Performance.md)).

# Security Considerations
- **A push is publication.** This repo is currently public (`isPrivate: false`), so a pushed secret is public instantly, and deleting it in a later commit does not help ([Ch 33](33_Secrets_And_Leaks.md)).
- **Never put a token in a remote URL.** `https://user:ghp_xxx@github.com/...` sits in plaintext in `.git/config` and prints in `git remote -v`. Use SSH or a credential helper.
- **SSH host aliases are access control.** The remote is `git@github-personal:umesh29032/umesh-personal.git`; `github-personal` is a `~/.ssh/config` alias binding pushes to the personal key, so an office key cannot push here by accident.
- **`--force` is a data-destruction primitive** — it removes other people's commits and exits 0. A lease turns silent loss into a loud rejection. **`--no-verify`** skips every hook including the `main` guard: a documented release override, not a way past a red hook.
- **A rewrite only helps if nobody forked.** Forks and existing clones keep the old objects — exactly why the dump incident was deliberately *not* history-rewritten (0 forks, repo going private, nothing usable inside), with the reasoning recorded in the commit message.

# Architecture Decisions
- **Fast-forward-only for `main`.** §9 uses `merge --ff-only`: it refuses rather than inventing a merge commit, so drift becomes an error instead of a surprise.
- **Client-side push protection, because server-side costs money.** Branch protection is paid on private repos, so `git-hooks/pre-push` does the job free — tested: `main` BLOCKED, `master` BLOCKED, `feat/my-thing` ALLOWED. Plain `--force` is rejected outright by §10.
- **…and the gap is written down, not hidden.** Hooks live in `.git/hooks/`, which git never clones (deliberate upstream security: cloning must not execute a repo's code). So the hook binds only where `git-hooks/install.sh` ran, and §2 lists "owner on a fresh clone with no hook" as caught by **nothing**.
- **Two remotes on one clone.** `origin` and `upstream` are both `umesh29032/umesh-personal` here; the convention exists so a *collaborator's* clone keeps identical muscle memory with `origin` = their fork ([Ch 20](20_Forks_And_The_Fork_Flow.md)).

# Best Practices
- `git fetch` before forming an opinion — free, and it cannot break anything.
- Push with `-u` the first time; bare `git push` for the rest of the branch's life.
- Default to `--ff-only`; reach for `--rebase` consciously.
- Read `git status -sb` before every push: two numbers, one line, no surprises.
- `--force-with-lease` always. Treat plain `--force` as a typo.
- `git fetch --prune` weekly; push tags with `--follow-tags` ([Ch 29](29_Semantic_Versioning_And_Tags.md)).

# Beginner Mistakes
- **Thinking `origin/main` is the server** → you act on a stale photo and cannot explain the numbers. It is a local cache, moved only by `fetch`.
- **`git pull` as a reflex** → history full of "Merge branch 'main' of github.com…" commits nobody meant. Use `--ff-only`, or `--rebase` on purpose.
- **Reaching for `--force` at the first rejection** → you delete a colleague's commits with exit code 0. Fetch, look, integrate; if you must overwrite, use a lease.
- **Believing `git pull` updates every branch** → it integrates only the *current* one. Local `main` here sat **295 commits behind** exactly this way.
- **Forgetting `-u`** → re-typing the long form forever, and hitting `no upstream branch` on the next new branch anyway.
- **Expecting `git push` to send tags** → it does not, so releases silently never ship. `--follow-tags`.
- **Deleting the remote branch and assuming the local one went too** → separate refs: `git push origin --delete X` *and* `git branch -d X`.
- **Assuming a force-push erases a leaked secret** → forks and clones keep the objects. Rotate the credential; the push is not the fix.

# Interview Questions
- **Junior:** "Difference between `git fetch` and `git pull`?" — `fetch` downloads new commits and moves the remote-tracking refs (`origin/*`) only; it never touches my files or my branch, so it is always safe. `pull` is `fetch` plus an integration step — merge by default, rebase with `--rebase` — and that second half is what can change my working tree or conflict. I fetch to look, pull to integrate.

- **Mid:** "Your push is rejected as non-fast-forward. Walk me through it." — The remote holds commits my branch lacks, so moving its pointer to mine would orphan them. I `fetch`, read the ahead/behind from `git status -sb`, then integrate: `--rebase` on my own feature branch for linear history, a merge if the branch is shared. Then push normally. `--force` "fixes" it by deleting their commits, so it is never first; if I had deliberately rewritten my own branch, the right tool is `--force-with-lease`.

- **Senior:** "Protect `main` on a private repo on GitHub's free plan, where branch protection is paid." — Three layers, honestly labelled. (1) A committed `pre-push` hook refusing `main`/`master`, installed per clone — free and effective, but binding only where it was installed, so running the installer is onboarding step 1. (2) Collaborators get **Read** access and work from a fork: with no push permission at all, "cannot push to main" is enforced by GitHub for free, and that is *stronger* than branch protection, which only says "not there". (3) CI on every PR as the visible merge gate — blocking merge-on-red is paid, so it is a discipline gate with an identical signal. Then write the residual gap down rather than pretend it is closed.

- **Staff:** "A junior force-pushed over three days of a colleague's work on a shared branch. Handle it, and make it unrepeatable." — Recovery first: the objects are unreferenced, not deleted, so `git reflog show origin/<branch>` on any machine that had them yields the previous tip; restore with `git push --force-with-lease origin <old-sha>:<branch>` and verify by diffing against the colleague's clone. Then remove the class of failure rather than blame the person: wrap `push` so plain `--force` becomes a lease; make ownership explicit — feature branches individually owned, integration branches append-only; keep branches short-lived so the blast radius is hours, not days. The systemic point: git hands destructive remote operations to everyone, so protection must be *designed*, and on a free plan the cheapest strong layer is a permission boundary — a fork — not a paid setting.

### Why interviewers ask these — and the answer that separates levels

| Testing for | Weak answer | What lands |
|---|---|---|
| Do you know a tracking branch is a local cache? | "origin/main is the branch on GitHub." | Name three pointers — local branch, tracking ref, server ref — and which command moves each. Then explain a stale `main` with it. |
| Do you understand *why* a push is rejected? | "You pull and push again." | Fast-forward is the safety rule: the server refuses any move that would orphan commits it already holds. |
| Do you respect destructive remote commands? | "I force push when it complains." | A lease sends your cached remote SHA, so a concurrent push loses the race instead of the data — plus the reflog recovery path. |
| Do you know `pull` is two commands? | "Pull gets the latest code." | `fetch` then merge-or-rebase, configurable; `--ff-only` fails loudly instead of inventing a merge commit. |

**The killer follow-up:** *"You pushed a `.env` to a public repo an hour ago, then force-pushed it away. Are you safe?"* — No. It was compromised the moment it was published: forks, clones and caches keep the object, and the push proves nothing was rotated. Rotate the credential first, then clean history, then add the `.gitignore` rule.

# Revision Notes
- **Three pointers:** `main` (you move it) · `origin/main` (only `fetch`) · the server's ref (only `push`).
- `fetch` = download + move `origin/*`; **never touches your files** — the one always-safe network command.
- `pull` = `fetch` + merge/rebase. `git config pull.ff only` makes it fail loudly instead of inventing commits.
- A push is allowed only as a **fast-forward**; the rejection means the server holds commits you lack.
- `-u` writes `branch.X.remote` + `branch.X.merge` — that powers bare `push`/`pull` and `[ahead 1]`.
- ⚠️ **`--force-with-lease`, never plain `--force`.** Recovery = `git reflog show origin/<branch>`. Tags need `--follow-tags`.
- Real state here: `main` `7c256f50` is **295 behind** `origin/main` `83a144ba`, 0 ahead.

# Cheat Sheet
- **Look, safely:** `git fetch --all --prune` · `git ls-remote --heads origin` (writes nothing) · `git status -sb`
- **Where am I:** `git branch -vv` · `git rev-list --count main..origin/main` (behind) · `origin/main..main` (ahead)
- **What differs:** `git log --oneline HEAD..origin/main` (theirs) · `origin/main..HEAD` (mine)
- **First push:** `git push -u origin feat/my-thing`, then bare `git push`
- **Integrate:** `git pull --ff-only` · `git pull --rebase` · `git config pull.ff only`
- **Refspec:** `git push origin HEAD:main` · `git push origin --delete feat/x` · `git push --follow-tags`
- **Rewrite own branch:** `git push --force-with-lease` — ⛔ never plain `--force` on anything shared
- **Undo a bad force-push:** `git reflog show origin/<branch>` → `git push --force-with-lease origin <old-sha>:<branch>`

# My ERP Section
| Concept | In this repo |
|---|---|
| Remote URL | `git@github-personal:umesh29032/umesh-personal.git` (SSH alias carries the personal key) |
| Remotes present | `origin` **and** `upstream` — both this URL here; a collaborator's `origin` is their fork |
| Server state today | `refs/heads/main` and `refs/heads/new_flask_app` both at `83a144ba` (the PR #15 merge) |
| Local drift | `main` = `7c256f50`, **295 behind**, 0 ahead → `git merge --ff-only origin/main` |
| Upstream config | `branch.new_flask_app.remote origin` · `branch.new_flask_app.merge refs/heads/new_flask_app` |
| Push guard | `git-hooks/pre-push` refuses `main`/`master`; installed by `git-hooks/install.sh` |
| Object size | 4,873 loose (26.19 MiB) + 25,975 packed (63.66 MiB), 2,407 tracked files |

# Practice Tasks
1. **Read the pointers.** Run `git branch -vv` and `git rev-parse --short main origin/main`. Explain why the SHAs differ and which command changes each.
2. **Measure the drift.** Run `git rev-list --count` both directions on `main`. Which number decides whether `merge --ff-only` can succeed?
3. **Prove `fetch` is safe.** Note `git status` and `git log --oneline -1`, run `git fetch --all --prune`, re-check both. What changed — and what did not?
4. **Ask the server.** Run `git ls-remote --heads origin` and compare with your `origin/*` refs. If they disagree, what does that tell you?
5. **Design the recovery.** Without running them, write the two commands that restore a shared branch after a plain `--force`.

# Homework
- Set `git config pull.ff only` and live with it for a week. Each refusal: write down the real situation (merge, rebase, or reset) and whether it saved you a junk merge commit.
- Give local `main` an upstream (`git branch -u origin/main main`), re-run `git branch -vv`, and explain what the bracket now shows that it could not before.
- Read `.github/workflows/ci.yml` and find where it checks out code. Would `--depth 1` break any job here? Which one, and why?
- Argue both sides: this project deliberately did **not** rewrite history to remove two committed `pg_dump` files. When would you rewrite instead, and what would the force-push cost every existing clone?

---

# Further Reading & Live Resources
- Pro Git — *Working with Remotes* (canonical fetch/push/tracking): https://git-scm.com/book/en/v2/Git-Basics-Working-with-Remotes
- Pro Git — *Remote Branches* (why `origin/main` is a cache): https://git-scm.com/book/en/v2/Git-Branching-Remote-Branches
- `git push` reference — refspec grammar and every force variant: https://git-scm.com/docs/git-push
- `git fetch` reference — `--prune`, `--all`, default refspecs: https://git-scm.com/docs/git-fetch
- GitHub Docs — *Managing remote repositories* (SSH vs HTTPS, host aliases): https://docs.github.com/en/get-started/git-basics/managing-remote-repositories
