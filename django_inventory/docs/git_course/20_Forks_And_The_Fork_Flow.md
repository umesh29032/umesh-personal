---
id: git-course-20-forks-and-the-fork-flow
type: lesson
status: active
owner: handwritten
scope: git, version control — forks as a server-side permission boundary; origin/upstream, the triangular workflow, syncing a fork, and what a fork keeps forever
anchors: CONTRIBUTING.md, .github/CODEOWNERS, git-hooks/install.sh, .github/workflows/ci.yml
verified: 2026-08-03
---

# 20 — Forks & the Fork-Based Flow (a permission boundary, not a git feature)

> Part of [Git Course](00_COURSE_OVERVIEW.md). Prev: [19 — Push, Fetch & Pull](19_Push_Fetch_Pull.md). Next: [21 — Pull Requests](21_Pull_Requests.md).

# Learning Objectives
By the end of this chapter you can:
- define a *fork* and explain why git itself has no `git fork` command
- set up `origin` + `upstream` and keep a fork current with `merge --ff-only`
- argue why **Read access + a fork** is stronger than paid branch protection
- say what a fork keeps forever, and how that constrains rewriting history
- diagnose the three classic fork failures: wrong account, stale fork, wrong PR base

# Purpose
[Ch 19](19_Push_Fetch_Pull.md) ended on a problem it could not solve: a `pre-push` hook only binds on machines where it was installed. This chapter is the layer that *is* enforced by the server and still costs nothing — the fork. It is the free half of this project's protection story, and the standard way every large open-source project accepts code from strangers.

# The Problem
You want a second developer on this repo. Two obvious options, both bad:

- Give them **Write** access → they can `git push origin main` on day one. Server-side branch protection would stop them, but on a private repo that is a **paid** feature, and the owner ruling is no paid plans — budget goes to deploy infrastructure. So nothing stops them.
- Give them **nothing** → they cannot contribute at all.

There is a third option that costs ₹0 and is enforced by GitHub itself: give them **Read**, and let them work from a **fork**. And the mechanism is not theoretical — it is live in this repo right now. The local `gh` CLI is authenticated as the owner's *office* account:
```
$ gh auth status
github.com
  ✓ Logged in to github.com as umesh2030
```
…while the repo belongs to `umesh29032`. That is why `gh pr create` fails here with `must be a collaborator`. GitHub's permission model — not git — decides who may write, and it does not care that both accounts belong to the same human.

# Theory (from zero)

### A fork is a GitHub concept, not a git one
Type `git fork` and git says `'fork' is not a git command`. There is no such thing in git, because git has no idea what an "account" is. A **fork** is a *server-side copy of a repository under your own account*, created by GitHub (or GitLab, Gitea, …) when you click **Fork**. Three separate repositories end up in play for a contributor:

| Name | Where it lives | Can they push? |
|---|---|---|
| **upstream** | `umesh29032/umesh-personal` — the real repo | ❌ no (Read access) |
| **fork** (`origin`) | `<their-username>/umesh-personal` — their copy on GitHub | ✅ yes, they own it |
| **clone** | their laptop | ✅ it is their disk |

`git clone` copies a repo **to your disk**. Forking copies it **to your account on the server**. Everything else in this chapter follows from that one distinction.

### `origin` vs `upstream` — the two-remote convention
Nothing in git blesses these names; they are convention, and the convention is worth obeying because every tutorial on earth assumes it:
- **`origin`** = the remote you **push** to = *your fork*.
- **`upstream`** = the remote you **fetch** from = *the real repo*.

`CONTRIBUTING.md` §9 sets it up in exactly two commands — clone the fork, then add upstream:
```bash
git clone git@github.com:<their-username>/umesh-personal.git
git remote add upstream git@github.com:umesh29032/umesh-personal.git
```

### Why the fork is a *stronger* guarantee than branch protection
Branch protection says *"you may push, but not to that branch."* A fork says *"you have no push to this repository at all."* One is a rule about a destination; the other removes the capability. `CONTRIBUTING.md` §2 states it plainly:

> With Read access there is no push permission to this repository at all — so for everyone except the owner, "cannot push to main" is enforced by GitHub itself, for free, with no plan upgrade.

That is Layer 2 of the three-layer scheme. Layer 1 is the `pre-push` hook (client-side, free, only where installed); Layer 3 is CI as the visible merge gate ([Ch 28](28_CI_With_GitHub_Actions.md)). Layer 2 is the only one that is both **server-side** and **free**.

### Keeping a fork current — and why `--ff-only`
A fork does not update itself. It is a snapshot from the moment you clicked Fork, and it goes stale the instant upstream moves. The daily first command:
```bash
git fetch upstream && git switch main && git merge --ff-only upstream/main
```
`--ff-only` *refuses* to create a merge commit. `CONTRIBUTING.md` §9 explains the intent: *"If it fails, their `main` has drifted and they should reset it to upstream rather than merge — keeping `main` a clean mirror."* Treat your fork's `main` as read-only plumbing, never a place you commit.

If it does refuse, and you are certain nothing unique lives on `main`:
```bash
git switch -c rescue/my-work     # ① park anything unpushed on a branch FIRST
git switch main
git reset --hard upstream/main   # ② make main an exact mirror (⚠ discards main's local commits)
```
**Undo for step ②:** `git reflog` ([Ch 16](16_Reflog.md)) still lists the pre-reset tip — `git reset --hard <that-sha>` restores it. Step ① is what makes ② boring instead of frightening.

### The triangular workflow
Fetch from one place, push to another — git has config for it, so you never have to remember:
```bash
git config remote.pushDefault origin   # bare `git push` always goes to my fork
git config push.default current        # …to a same-named branch, created if needed
```
Now `git fetch upstream` + `git push` do the right thing with no arguments. GitHub calls this the *triangular workflow*: upstream → you → your fork → back to upstream as a Pull Request ([Ch 21](21_Pull_Requests.md)).

> 💡 **Samjho aise:** Upstream = **society ka asli blueprint** — usme pencil chalane ki permission tumhe nahi hai. Fork = wahi blueprint ki **apni photocopy**, jo tumhare naam pe rakhi hai; uspe jitna chaho likho. PR = photocopy pe kiya hua change lekar committee ke paas jaana: *"yeh badlaav asli blueprint mein daal do?"* Committee (owner + CI) haan kahe tabhi asli blueprint badalta hai. Isliye contributor ko *rok* nahi lagayi jaati — usse **asli blueprint pe pen hi nahi diya jaata**.

### What a fork keeps forever (the part that constrains history rewrites)
A fork is a full repository with all the objects. Once it exists, upstream cannot un-publish anything from it: rewriting history and force-pushing (`git-filter-repo`, [Ch 34](34_Rewriting_History.md)) changes only *upstream*. Every fork, and every existing clone, still contains the old commits.

GitHub's documented behaviour makes this sharper: turning a **public** repo **private** does not delete its existing public forks — they are detached into a separate network and stay accessible. So "we'll just make it private" is not a retraction either.

This is exactly why the dump incident's conclusion was defensible. Real, checked today:
```
$ gh repo view umesh29032/umesh-personal --json forkCount,stargazerCount,isPrivate
{"forkCount":0,"stargazerCount":0,"isPrivate":false}
```
**0 forks.** With nobody holding a copy, the two committed `pg_dump` files could be left in history and prevented going forward instead. Had `forkCount` been non-zero, that reasoning collapses and rotation becomes mandatory.

# Real World Example (this repo)
The owner's clone has both remotes — and they are the *same URL*, which is itself instructive:
```
$ git remote -v
origin	git@github-personal:umesh29032/umesh-personal.git (fetch)
origin	git@github-personal:umesh29032/umesh-personal.git (push)
upstream	git@github-personal:umesh29032/umesh-personal.git (fetch)
upstream	git@github-personal:umesh29032/umesh-personal.git (push)
```
The owner needs no fork — he *is* upstream — so `upstream` here is a convenience alias that lets the documented commands in §9 be copy-pasted verbatim on the owner's machine and on a collaborator's. On a collaborator's clone, `origin` would read `<their-username>/umesh-personal` and only `upstream` would say `umesh29032`.
```
$ git branch -r
  origin/main
  origin/new_flask_app
  upstream/main
```
Note `github-personal`: an SSH host alias from `~/.ssh/config` that binds this repo's traffic to the personal key. It matters more in a multi-account setup than the username in the URL does — as the `gh auth status` output above shows, having the *office* account authenticated is exactly what makes `gh pr create` fail with `must be a collaborator`.

# Visual Diagram
```
                       UPSTREAM  (GitHub)
                 umesh29032/umesh-personal
                 default branch: main   forks: 0
                    ▲                        │
      ③ Pull Request│                        │① fork (one click, server-side)
        (needs review + green CI)            ▼
                    │              FORK  (GitHub) = "origin"
                    │        <their-username>/umesh-personal
                    │                   ▲        │
                    │      ② git push   │        │ git clone
                    │       (they own it)│       ▼
                    └────────────── THEIR LAPTOP (clone)
                                     main   ← mirror only, never commit here
                                     feat/x ← all work happens here

  git fetch upstream  ──────────────────────►  updates upstream/main in the clone
  git merge --ff-only upstream/main         →  fast-forwards local main (refuses to merge)

  Read access ⇒ NO push to upstream at all  ← Layer 2: server-side and free
  A fork keeps every object forever         ⇒ an upstream history rewrite cannot reach it
```

# Practical — set it up exactly as `CONTRIBUTING.md` §9 does
Owner, once, in the browser: **Settings → Collaborators → Add people → role Read.** Read, not Write — that *is* the protection.

Contributor:
```bash
git clone git@github.com:<their-username>/umesh-personal.git   # ① clone THEIR fork
cd umesh-personal
git remote add upstream git@github.com:umesh29032/umesh-personal.git   # ② the real repo
bash git-hooks/install.sh          # ③ NOT optional — Layer 1 (Ch 26/27)
git remote -v                      # verify: origin = fork, upstream = umesh29032
```
Daily loop:
```bash
git fetch upstream && git switch main && git merge --ff-only upstream/main
git switch -c feat/their-thing
git push -u origin feat/their-thing    # origin = THEIR fork
gh pr create --repo umesh29032/umesh-personal --base main --fill
```
Verify the sync is real, not assumed:
```bash
git rev-parse --short main upstream/main   # identical = fork's main is a true mirror
git log --oneline main..upstream/main      # empty = nothing left to pull
```

# Production Walkthrough
1. **Owner adds the collaborator with Read** and sends them `CONTRIBUTING.md`. Nothing else grants access; there is no second switch to forget.
2. **They fork and clone the fork**, add `upstream`, and run `bash git-hooks/install.sh`. Layers 1 and 2 are now both in place.
3. **They set the project up** (`venv`, `pip install`, `cp .env.example .env`, `migrate`, `seed_master_data`) — the `.env` is never in git, so this step cannot be skipped.
4. **Sync, branch, work, push to their fork.** Their `main` stays a mirror.
5. **They open a PR from the fork** into `umesh29032/umesh-personal`. CI runs on it with a **read-only** token and **no repository secrets** — GitHub's default for fork PRs, and the reason a fork PR cannot exfiltrate credentials.
6. **Owner reviews** against §5's standard — correctness, money paths, permissions, tests, docs (rule 12), mobile — and **squash-merges**. The contributor never needed push access to `main` at any point.

# Debugging Guide
| Symptom | Cause | Fix |
|---|---|---|
| `gh pr create` → `must be a collaborator` | `gh` is authenticated as the wrong account (here: `umesh2030` vs repo owner `umesh29032`) | `gh auth switch`, or open the PR in the browser |
| `remote: Permission to …denied` on push | you pushed to **upstream**, not your fork | `git remote -v`; push to `origin`, or fix `remote.pushDefault` |
| PR shows hundreds of unrelated commits | your fork's `main` is stale, so the diff is against ancient history | sync `main` from upstream, then rebase your branch onto it |
| `merge --ff-only` refuses on `main` | you committed onto your fork's `main` | park the work on a branch, then `git reset --hard upstream/main` |
| Fork's `main` says "1 commit behind/ahead" on GitHub | the fork does not auto-sync | `git fetch upstream` + ff-only merge (or GitHub's **Sync fork** button) |
| CI on a fork PR cannot see a secret | fork PRs get a read-only token and no secrets, by design | do not paper over it with `pull_request_target` — see *Security* |
| `upstream/feat/x` still listed after the PR merged | your clone caches deleted remote branches | `git fetch --all --prune` |
| A collaborator "can't find" the repo | Read access was never actually granted | re-check Settings → Collaborators |

# Performance Notes
- **Forking a big repo is instant and free** because GitHub does not copy the objects — forks in a network **share** storage server-side. This repo carries ~90 MiB of objects (63.66 MiB packed) and 2,407 tracked files; the fork costs the server almost nothing.
- **Your clone still pays full price** — the pack transfer is identical whether you clone upstream or a fork. Time it once and stop worrying.
- **Two remotes ≈ two fetches.** `git fetch --all` talks to both; on a slow link, fetch `upstream` only when you actually intend to sync.
- **CI is where clone cost shows up.** Shallow (`--depth 1`) checkouts are standard for that reason — but note this project's design-system ratchet needs a real merge base (`git merge-base origin/<base> HEAD`), so its checkout cannot be depth-1 ([Ch 28](28_CI_With_GitHub_Actions.md)).

# Security Considerations
- **Read + fork removes a capability rather than restricting one.** No push permission means no push to any branch, protected or not. That is why it survives an unconfigured hook, a new laptop, or a forgotten setting.
- **A fork PR's CI is deliberately powerless.** On the `pull_request` event GitHub gives the workflow a **read-only** `GITHUB_TOKEN` and withholds repository secrets, because the code being tested is written by someone who cannot be trusted with them.
- **`pull_request_target` is the trap.** It runs in the *base* repo's context with secrets available. Combining it with a checkout of the PR's head is a well-known critical vulnerability — untrusted code with your credentials. If you do not fully understand it, do not use it.
- **A fork is a permanent copy.** Upstream can rewrite history or go private; the fork keeps the objects. Making a public repo private detaches existing public forks into their own network rather than deleting them.
- **Therefore: leaked secret ⇒ rotate, always.** A rewrite is cleanup, not containment. This repo's dump decision only held because `forkCount` was **0** and the contents were audited harmless — empty OAuth tables, two `pbkdf2_sha256$1000000$…` hashes, expired sessions.
- **Never grant Write "just for now."** It is a permanent capability granted for a temporary reason, and it silently disables Layer 2 for that person.

# Architecture Decisions
- **Read + fork chosen over a paid plan.** Owner ruling: no tool subscriptions; money goes to deploy infrastructure. The fork gives a *server-side* guarantee for free, so the paid feature buys convenience, not safety.
- **`CONTRIBUTING.md` documents the honest ordering** — Layer 1 hook (free, local, only where installed), Layer 2 fork (free, server-side), Layer 3 CI (free, visible). It also names the one uncovered case: owner on a fresh clone with no hook, caught by **nothing**.
- **The owner's clone keeps a redundant `upstream`** so §9's commands are literally copy-pasteable for both roles. A one-line waste that removes a whole class of "that command doesn't work for me".
- **`CODEOWNERS` is committed even though it is inert here.** Automatic reviewer assignment is paid on private repos; the file still records who owns money paths, access control and migrations, the PR template points at it, and it starts working the moment the repo is public or a plan is bought.
- **Trunk-based, not `git-flow`** (§10): `main` plus short-lived branches plus tags. A fork adds an account boundary, not a branching model.

# Best Practices
- Name the remotes `origin` (your fork) and `upstream` (the real repo). Never improvise.
- Treat your fork's `main` as read-only plumbing. All work happens on a branch.
- Sync **before** branching, not after — it is the cheapest conflict prevention there is.
- Keep `--ff-only`, so a refusal tells you something instead of hiding it in a merge commit.
- Set `remote.pushDefault origin` once; bare `git push` can then never reach upstream.
- Run `git remote -v` before your first push on a new clone. Two seconds, whole class of mistakes gone.
- Delete a merged branch on your fork too — a fork accumulates dead branches faster than upstream does.

# Beginner Mistakes
- **Confusing fork with clone** → "I forked it but the files aren't on my machine." Fork = server-side copy under your account; clone = the copy on your disk. You need both.
- **Committing onto the fork's `main`** → the next `merge --ff-only` refuses and syncing turns into an argument. Branch first, always.
- **Never adding `upstream`** → the fork silently rots, and the PR diff eventually shows hundreds of unrelated commits.
- **Pushing to `upstream` by habit** → `Permission denied`. Check `git remote -v`; set `remote.pushDefault`.
- **Opening the PR against your own fork** → it merges into your copy and upstream never sees it. Base = `umesh29032/umesh-personal` `main`.
- **Assuming the wrong `gh` account is a git problem** → `must be a collaborator` is a *GitHub permission* message. `gh auth status` first.
- **Believing a private-repo switch un-publishes forks** → existing public forks are detached, not deleted. Rotate the secret.
- **Granting Write to make a problem go away** → you have just removed the only free server-side protection for that person.

# Interview Questions
- **Junior:** "What is a fork, and how is it different from a clone?" — A fork is a copy of the repository under **my account on the server**, created by GitHub; a clone is a copy on **my disk**, created by git. Git has no `fork` command because git knows nothing about accounts. In the fork workflow I use both: fork on GitHub, clone the fork, add the original as `upstream`, push to `origin` (my fork), and open a Pull Request back.

- **Mid:** "How do you keep a fork current, and why `--ff-only`?" — `git fetch upstream && git switch main && git merge --ff-only upstream/main`. `--ff-only` refuses to create a merge commit, so my fork's `main` stays a byte-exact mirror of upstream. If it fails, that is a real signal — I committed onto `main` — and the fix is to park that work on a branch and `git reset --hard upstream/main`, not to merge. I sync before branching, so my feature starts from current code and conflicts stay small.

- **Senior:** "Why is Read + fork stronger than branch protection?" — Branch protection restricts a capability the person still has: "you may push, but not there," and it can be bypassed by an admin, or simply not be available — it is paid on private repos. Read + fork **removes the capability**: with no push permission, there is nothing to protect against. It is also the model every large open-source project runs on, so contributors already know it, and it composes with client-side hooks and CI rather than replacing them. The trade-off is process weight — every change needs a PR, and the maintainer becomes the throughput limit.

- **Staff:** "A secret was committed to a public repo. Assess containment when the repo has forks." — Containment is already lost at the moment of publication; the only true remediation is **rotating the credential**, and everything else is cleanup. Forks make that concrete: each fork and each clone is a complete object store, so an upstream `git-filter-repo` + force-push cannot reach them, and turning the repo private detaches existing public forks rather than deleting them — GitHub's own documented behaviour. So I would (1) rotate and audit for use, (2) enumerate exposure — fork count, clone traffic, whether search engines and mirror sites indexed it, (3) decide on a rewrite by weighing benefit against cost, since a force-push breaks every collaborator's clone and invalidates open PRs, and (4) close the hole at the source with a `.gitignore` rule and a secret scanner in CI. This project's decision is a clean worked example: **0 forks**, contents audited (empty OAuth tables, 1,000,000-iteration hashes, expired sessions), repo going private — so prevention was chosen over surgery, and the reasoning was written into the commit message so it survives.

### Why interviewers ask these — and the answer that separates levels

| Testing for | Weak answer | What lands |
|---|---|---|
| Do you know a fork is a permission construct? | "A fork is your own copy of the repo." | It is a *server-side* copy under your account; a contributor holds three repos, and the point is that they have no push to upstream at all. |
| Have you actually maintained a fork? | "I click Sync fork." | Name the commands and why `--ff-only`, plus what you do when it refuses — park work on a branch, reset `main` to upstream. |
| Do you understand the CI trust boundary? | "CI runs the tests on the PR." | Fork PRs get a read-only token and no secrets; `pull_request_target` plus a head checkout is the classic critical hole. |
| Do you know what a fork keeps? | "We rewrote history, so it's gone." | Forks and clones keep every object; going private only detaches existing forks. Rotate the secret — a rewrite is cleanup. |

**The killer follow-up:** *"Your collaborator says they cannot push. Is that a bug?"* — No, that is the design working. Read access has no push permission, which is precisely how "cannot touch `main`" is enforced for free. They push to their fork and open a PR.

# Revision Notes
- **Fork = server-side copy under your account** (GitHub concept). **Clone = your disk** (git concept). No `git fork` exists.
- Convention: **`origin` = your fork** (push) · **`upstream` = the real repo** (fetch).
- Sync = `git fetch upstream && git merge --ff-only upstream/main`. A refusal means you committed onto `main`.
- Read + fork = **Layer 2**: the only protection here that is both server-side and free — it removes push, not just a destination.
- Triangular workflow: `remote.pushDefault origin` + `push.default current`.
- ⚠️ **A fork keeps every object forever**; going private only *detaches* existing public forks. Leak ⇒ **rotate**.
- Fork PRs in CI: **read-only token, no secrets**. `pull_request_target` + head checkout = critical hole.
- Real here: `forkCount 0`, `stargazerCount 0`, `isPrivate false` — which is why the dump decision held.

# Cheat Sheet
- **Set up:** `git clone <your-fork>` · `git remote add upstream git@github.com:umesh29032/umesh-personal.git` · `bash git-hooks/install.sh`
- **Check wiring:** `git remote -v` (origin = fork, upstream = real) · `git branch -r`
- **Sync:** `git fetch upstream && git switch main && git merge --ff-only upstream/main`
- **Verify sync:** `git rev-parse --short main upstream/main` (identical = true mirror)
- **Rescue a dirtied `main`:** `git switch -c rescue/x` → `git switch main` → `git reset --hard upstream/main` (undo: `git reflog`)
- **Triangular:** `git config remote.pushDefault origin` · `git config push.default current`
- **Work:** `git switch -c feat/x` → `git push -u origin feat/x` → `gh pr create --repo umesh29032/umesh-personal --base main --fill`
- **Wrong account?** `gh auth status` → `gh auth switch` (`must be a collaborator` is a permission error, not git)

# My ERP Section
| Concept | In this repo |
|---|---|
| Upstream | `umesh29032/umesh-personal` — monorepo; the ERP is the `django_inventory/` subdirectory |
| Fork count | **0** (`gh repo view`) — the fact the dump decision rested on |
| Collaborator role | **Read** (`CONTRIBUTING.md` §9) — Layer 2, server-side and free |
| Owner's remotes | `origin` **and** `upstream`, both `git@github-personal:umesh29032/umesh-personal.git` |
| `gh` CLI account | `umesh2030` (office) → `gh pr create` fails `must be a collaborator` |
| Sync rule | `git fetch upstream && git switch main && git merge --ff-only upstream/main` |
| Onboarding step 1 | `bash git-hooks/install.sh` — not optional (Layer 1) |
| Review ownership | `.github/CODEOWNERS` — money, access control, migrations, deploy, frozen docs |

# Practice Tasks
1. **Draw the triangle.** From memory, draw upstream / fork / clone and label which arrow is `fetch`, which is `push`, and which is the PR.
2. **Read the wiring.** Run `git remote -v` and `git branch -r`. Which remote would a bare `git push` reach, and which config setting decides that?
3. **Prove the mirror.** Run `git rev-parse --short main upstream/main`. If they differ, say precisely why and which command fixes it.
4. **Test the boundary.** Read `CONTRIBUTING.md` §2. For each of its four failure rows, name the layer that catches it — and the one caught by nothing.
5. **Reason about forks.** If `forkCount` were 3 instead of 0, which sentences of the dump-incident decision stop being true?

# Homework
- Fork any public repo, clone your fork, add `upstream`, and sync it with `--ff-only`. Then deliberately commit onto your fork's `main`, watch the refusal, and recover with the rescue sequence.
- Set `remote.pushDefault` and `push.default` in that clone. Explain what a bare `git push` now does, and how you would prove it without pushing.
- Read GitHub's docs on `pull_request` vs `pull_request_target`. Write three sentences on why a fork PR must not see secrets, and what breaks when someone "fixes" that.
- Read `.github/CODEOWNERS`. It admits it is inert on this plan — argue whether committing it anyway was right, using its own three stated reasons.

---

# Further Reading & Live Resources
- GitHub Docs — *Fork a repository* (the canonical fork + upstream setup): https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/fork-a-repo
- GitHub Docs — *Syncing a fork*: https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/syncing-a-fork
- GitHub Docs — *Repository roles* (what Read actually permits): https://docs.github.com/en/organizations/managing-user-access-to-your-organizations-repositories/managing-repository-roles/repository-roles-for-an-organization
- GitHub Security Lab — *Preventing `pull_request_target` compromise*: https://securitylab.github.com/resources/github-actions-preventing-pwn-requests/
- Pro Git — *Contributing to a Project* (fork flow in context): https://git-scm.com/book/en/v2/Distributed-Git-Contributing-to-a-Project
