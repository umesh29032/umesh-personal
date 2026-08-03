---
id: git-course-27-pre-push-protection
type: lesson
status: active
owner: handwritten
scope: git, GitHub — replacing paid branch protection with a free, honest three-layer scheme
anchors: git-hooks/pre-push, git-hooks/install.sh, CONTRIBUTING.md, .github/workflows/ci.yml
verified: 2026-08-03
---

# 27 — Pre-push Protection (free branch protection, honestly)

> Part of [Git Course](00_COURSE_OVERVIEW.md). Prev: [26 — Pre-commit Hooks](26_Pre_Commit_Hooks.md). Next: [28 — CI with GitHub Actions](28_CI_With_GitHub_Actions.md).

# Learning Objectives
By the end of this chapter you can:
- explain what GitHub's branch protection does, and that it is **paid** on private repositories
- write a `pre-push` hook that refuses a protected branch, including the deletion case
- read the stdin contract git gives `pre-push` (most people get this wrong)
- explain why a **fork plus Read access** is *stronger* protection than branch protection
- state each layer's weakness without hiding it
- decide what belongs client-side, what belongs server-side, and what cannot be enforced at all

# Purpose
`main` must always be deployable. That is the one sentence every rule in this course descends from.

The normal way to guarantee it is GitHub's **branch protection**: a server-side rule saying *"nobody
may push directly to `main`; changes arrive only through a reviewed, CI-green pull request."*

On this project that rule cannot be bought. Server-side branch protection is a **paid feature on
private repositories** (free on public repos only), and the owner's standing ruling is that money
goes to deploy infrastructure, not tool subscriptions.

So protection had to be rebuilt from free parts. This chapter is that rebuild — and, more
importantly, an honest accounting of where the free version is weaker than the paid one. A guide
that pretends the gap does not exist is how people end up surprised.

# The Problem
Without any protection, one absent-minded command undoes the entire workflow:

```bash
git push origin main
```

No CI. No review. No record of why. And if that push is a force-push, it can abandon commits other
people are building on.

The tempting answers both fail:

- **"Just be careful."** Everyone is careful until 11pm on a Friday. Discipline that depends on
  attention is not a control.
- **"Enable branch protection."** Every tutorial says this. On a free private repo the setting is
  simply not available, and the honest response is to say so rather than hand-wave.

# Theory (from zero)

### What branch protection actually is
A **server-side** rule. GitHub evaluates it when a push arrives, and can refuse:

- direct pushes to a branch (all changes must come via a PR)
- merging without N approvals, or without CODEOWNERS approval
- merging while checks are red
- force-pushes and branch deletion

Server-side is the important word: it cannot be bypassed by a client, because the *server* refuses.
That is the property we are trying to reproduce.

### The plan reality, stated plainly
| Feature | Public repo (Free) | **Private repo (Free)** | Pro / Team+ |
|---|---|---|---|
| Branch protection / rulesets | ✅ | ❌ **paid** | ✅ |
| Required reviews | ✅ | ❌ **paid** | ✅ |
| Required status checks | ✅ | ❌ **paid** | ✅ |
| CODEOWNERS auto-request | ✅ | ❌ **paid** | ✅ |
| GitHub Actions | ✅ unlimited | ✅ ~2,000 min/month | ✅ |
| Dependabot | ✅ | ✅ | ✅ |

So on a private free repo the enforcement column is empty, while CI and Dependabot are fully
available. Any scheme has to be built from what is in the last two rows plus whatever runs on your
own machine.

GitHub has been steadily expanding **rulesets** (the newer replacement for branch protection), so
this table is worth re-checking on your own repo's Settings → Rules page. If it lets you in without
an upgrade prompt, use it — and keep the layers below anyway.

### Layer 1 — a `pre-push` hook (client-side, free)
`pre-push` runs before any objects are sent. Non-zero exit aborts the push.

Its contract is where people go wrong. Git passes:

- **`$1`** — the remote name (`origin`)
- **`$2`** — the remote URL
- **stdin** — one line per ref being pushed:
  `<local ref> <local sha> <remote ref> <remote sha>`

The branch you are pushing **to** is in the *third* field, not the first. A hook that checks the
current branch is wrong: `git push origin HEAD:main` pushes to `main` while you are standing on a
feature branch, and a current-branch check waves it through.

```bash
while read -r local_ref local_sha remote_ref remote_sha; do
    branch="${remote_ref#refs/heads/}"          # ← the DESTINATION
    ...
done
```

Also worth handling: a **deletion** push arrives with `local_sha` all zeros
(`0000000000000000000000000000000000000000`). Deleting `main` is more destructive than pushing to
it, so it deserves its own message.

**The honest limitation:** `.git/hooks/` is not cloned ([Chapter 26](26_Pre_Commit_Hooks.md)). The
hook binds only on machines where it was installed. A fresh clone is unprotected until someone runs
the installer. That is a real hole, and this project writes it into `CONTRIBUTING.md` rather than
leaving it to be discovered.

### Layer 2 — a fork plus Read access (server-side, free, and stronger)
This is the insight worth taking away from the whole chapter.

Give a collaborator **Read** access, not Write. They fork the repository, push to their fork, and
open a cross-repository PR ([Chapter 20](20_Forks_And_The_Fork_Flow.md)).

With Read access there is **no push permission to your repository at all**. Not to `main`, not to
any branch. So for everyone except the owner, "cannot push to `main`" is enforced by GitHub itself,
server-side, for free.

And it is *stronger* than branch protection. Compare the sentences:

- **Branch protection:** "you may push, but not to that branch." A key, with a lock on one door.
- **Fork + Read:** "you have no push." No key was ever handed over.

The free option is the better security posture. The cost is workflow friction — an extra remote,
and PRs come from a fork.

### Layer 3 — CI as the visible gate (server-side, free)
Actions runs on every PR regardless of plan. Four jobs here
([Chapter 28](28_CI_With_GitHub_Actions.md)).

The gap: on a free private repo GitHub will not *mechanically* prevent merging a red PR — that is
"required status checks", which is paid. The signal is fully visible on the PR; refusing to click
merge is a human commitment.

### What each layer catches — and what nothing catches
| Failure | Caught by |
|---|---|
| Owner absent-mindedly types `git push origin main` | Layer 1 (hook) |
| Collaborator tries to push or merge | Layer 2 (fork + Read) — server-side |
| A PR that breaks the tests | Layer 3 (CI), visibly |
| Owner on a fresh clone with no hook installed | ⚠️ **nothing** |
| Owner deliberately runs `--no-verify` | ⚠️ **nothing** (by design) |

The last two rows are the point of this chapter. They are written into `CONTRIBUTING.md` §2 as a
table, because an unstated gap is the one that bites. Onboarding step 1 exists *because* of row 4.

> 💡 **Samjho aise:** GitHub ka asli taala (branch protection) **private repo pe paisa maangta hai**.
> Humne nahi khareeda — toh taala **teen halke taalon** se banaya, aur har taale ki kamzori likh di.
>
> **Taala 1** — `pre-push` hook: tumhare computer pe `main` pe push rok deta hai. Kamzori: hook
> clone ke saath nahi aata, toh naye clone pe install karna padta hai.
>
> **Taala 2** — collaborator ko **Read** do, wo **fork** se kaam kare. Iska matlab uske paas chaabi
> **hi nahi** hai. Ye GitHub ke server pe lagta hai, muft — aur **paid taale se bhi mazboot**, kyunki
> paid taala kehta hai "chaabi hai par us darwaze pe nahi", aur ye kehta hai "chaabi hi nahi di".
>
> **Taala 3** — CI: red PR saaf dikhta hai. Kamzori: free private repo pe merge **rok** nahi sakta,
> sirf dikha sakta hai.
>
> Sabse zaroori baat: **kamzori chhupao mat, likh do.** Jo gap likha nahi hai, wahi kaatta hai.

# Real World Example (this repo)
`git-hooks/pre-push` is real, installed, and tested. Its header states the reasoning rather than
just the rule:

> *"GitHub's server-side branch protection is a PAID feature on private repos (free on public only).
> This repo is private and stays on the free plan, so 'you may not push to main' is enforced here
> instead — on the client, for free. Honest limitation: hooks live in `.git/hooks/`, which git does
> NOT clone."*

**What it does:**

- protects `main` **and** `master`
- reads the **destination** ref from stdin's third field, so `git push origin HEAD:main` is caught
- handles the deletion case (`local_sha` all zeros) with its own message
- prints the *fix*, not just a refusal: how to branch, how to recover if you already committed onto
  `main`, and how to override deliberately

The recovery instructions matter more than the block. A hook that says "no" teaches nothing; this one
says:

```
Already committed onto main by mistake?
  git switch -c feat/my-change      # your commits come with you
  git switch main
  git reset --hard origin/main      # restore main to the remote
```

**Verified end to end, not just by reading it.** Against a throwaway repository with a real
`git push`:

```
git push origin main          → BLOCKED   (git ls-remote showed 0 refs — nothing got through)
git push origin master        → BLOCKED
git push origin feat/allowed  → pushed ✅
git commit -m "broke the thing"     → rejected by commit-msg (ch 25)
git commit -m "fix(test): valid"    → accepted ✅
git commit --no-verify              → bypasses, as documented ✅
```

The `git ls-remote` check is the part that matters: it proves nothing reached the remote, rather than
trusting the hook's own exit code.

**Installation** is `bash git-hooks/install.sh`, which resolves the hooks directory with
`git rev-parse --git-path hooks` (so it works from any subdirectory and inside worktrees), backs up
any pre-existing hook rather than destroying it, and prints exactly what is now enforced.

**And the two other layers, as configured here:** collaborators get **Read** access and work from a
fork (`CONTRIBUTING.md` §9), and CI runs four jobs on every PR — lint, missing-migration check, the
**2,033-test** battery, and a documentation-drift gate.

# Visual Diagram
```
  WHAT WE WANTED                          WHAT WE COULD BUY
  ──────────────                          ─────────────────
  server-side rule:                       branch protection = PAID on private
  "no direct push to main"                required reviews  = PAID
                                          required checks   = PAID
                                                   ↓
                                      rebuild from free parts

  LAYER 1 — pre-push hook            (client, free)
  ─────────────────────────
    git push origin main
        │
        ▼  stdin: <local ref> <local sha> <remote ref> <remote sha>
    branch="${remote_ref#refs/heads/}"      ← DESTINATION, field 3
        │                                     (NOT the current branch —
        │                                      `push origin HEAD:main` would slip past)
        ├─ main / master ──► exit 1 ──► BLOCKED + how to fix + how to override
        └─ feat/*         ──► exit 0 ──► allowed
    ⚠ weakness: .git/hooks/ is NOT cloned ⇒ binds only where installed

  LAYER 2 — fork + Read access       (SERVER-side, free)  ← the strong one
  ──────────────────────────
    collaborator: Read only ⇒ NO push permission to this repo, any branch
      branch protection: "you may push, but not there"   (a key + one lock)
      fork + Read:       "you have no push"              (no key at all)
    ⚠ weakness: none for them. Does not constrain the OWNER.

  LAYER 3 — CI on every PR           (server, free)
  ────────────────────────
    lint → migrations → test(2033) → docs
    ⚠ weakness: merge-on-red not mechanically blocked on free private (paid)

  UNCAUGHT — written down, not hidden
  ───────────────────────────────────
    • owner on a fresh clone, hook not installed   ← onboarding step 1 exists for this
    • owner deliberately runs --no-verify          ← by design
```

# Practical — build it, then prove it
```bash
cd /home/tech/umesh-personal

# 1. read the real hook and its stated limitation
sed -n '1,25p' git-hooks/pre-push

# 2. install (per clone, per machine — hooks are never cloned)
bash git-hooks/install.sh
ls -l "$(git rev-parse --git-path hooks)"

# 3. feed the hook its real stdin contract, WITHOUT pushing anything
for ref in refs/heads/main refs/heads/master refs/heads/feat/ok; do
  if echo "refs/heads/x aaa111 $ref bbb222" \
       | bash .git/hooks/pre-push origin git@example:x/y.git >/dev/null 2>&1; then
    echo "  ALLOWED  $ref"
  else
    echo "  BLOCKED  $ref"
  fi
done

# 4. the deletion case (local sha all zeros)
echo "refs/heads/x 0000000000000000000000000000000000000000 refs/heads/main bbb222" \
  | bash .git/hooks/pre-push origin git@example:x/y.git 2>&1 | head -3

# 5. end-to-end in a THROWAWAY repo (never against a real remote)
S=/tmp/pushtest; rm -rf $S; mkdir -p $S; cd $S
git init -q --bare upstream.git && git init -q work && cd work
git config user.email t@t && git config user.name t
mkdir -p git-hooks && cp /home/tech/umesh-personal/git-hooks/* git-hooks/
bash git-hooks/install.sh >/dev/null
echo hi > a.txt && git add . && git commit -qm "feat: init" --no-verify
git remote add origin ../upstream.git && git branch -M main
git push origin main            # expect BLOCKED
git ls-remote origin | wc -l    # expect 0  ← PROOF nothing got through
git switch -qc feat/ok && git push -q -u origin feat/ok && git ls-remote origin

# 6. the documented override
git switch -q main
git push --no-verify origin main   # works — deliberately
```

Step 5's `git ls-remote | wc -l` is the honest test. A hook's exit code can be swallowed by a pipe;
an empty remote cannot lie.

# Production Walkthrough
1. **Onboarding step 1 is `bash git-hooks/install.sh`** — before the venv, before `.env`, before
   anything. A fresh clone is unprotected until this runs, and that is stated in `CONTRIBUTING.md` §9.
2. **Collaborators get Read, never Write.** Write includes merge; there is no role between Triage and
   Write. Read plus a fork is the enforcement.
3. **Daily work never touches `main` directly.** Branch → PR → CI → review → squash-merge.
4. **Local `main` stays a mirror**: `git merge --ff-only origin/main`
   ([Chapter 18](18_Remotes.md)).
5. **Releases override deliberately.** Pushing a tag is fine; if a release ever needs a direct push,
   `--no-verify` makes it an explicit act with a paper trail in the shell history.
6. **Re-check the plan periodically.** If the repo goes public — or rulesets become available on free
   private repos — turn on server-side protection **and keep all three layers**. The hook staying
   installed costs nothing.

# Debugging Guide

| Symptom | Cause | Fix |
|---|---|---|
| Hook does nothing after cloning | `.git/hooks/` is never cloned | `bash git-hooks/install.sh` |
| Hook exists but never fires | not executable | `chmod +x`; the installer does this |
| `git push origin HEAD:main` slipped through | hook checked the *current* branch | read the **destination** from stdin field 3 |
| Hook blocks a feature branch | pattern matching too loose (e.g. substring) | compare `"$branch" = "$protected"` exactly |
| Hook fires but the push still succeeds | exit code lost, or `--no-verify` used | verify with `git ls-remote`, not the hook's output |
| Branch protection settings missing on GitHub | private repo on the free plan | expected; use the three layers |
| Collaborator can merge | they were given **Write** | change to **Read**; they fork instead |
| Deletion of `main` not blocked | deletion pushes have `local_sha` all zeros | handle that case explicitly |
| Hook works for you, not a teammate | never installed on their machine | the inherent client-side weakness; CI and Layer 2 are the real gates |

# Performance Notes
- The hook is a bash loop over a handful of stdin lines — **microseconds**. It never touches the
  network or the object store.
- Never put slow checks in `pre-push`. A short test subset is defensible; a 424-second battery is
  not — that belongs in CI ([Chapter 28](28_CI_With_GitHub_Actions.md)).
- `git ls-remote` (used for verification) is one network round trip; fine for a test, not for a hook.
- Layer 2 costs nothing at all: it is an access-level setting.
- CI is the only layer with a real budget — ~2,000 free Actions minutes/month on a private repo, and
  `ci.yml` spends them carefully (cancel superseded runs, `paths` filter, cheap jobs gating the
  expensive one).

# Security Considerations
- **A client-side hook is not a security boundary.** `--no-verify` bypasses it, and it is absent on
  any clone where it was not installed. It stops *mistakes*, not *adversaries*. Anything that must
  be guaranteed belongs server-side.
- **Layer 2 is the only genuinely enforced layer for non-owners** — and it is free. Read access means
  no push permission, which no client-side trick can circumvent.
- **Force-push is the real danger, not the ordinary push.** A force-push can abandon commits others
  built on. Without server-side protection the mitigations are the hook plus habitually using
  `--force-with-lease`, which refuses when the remote has moved
  ([Chapter 19](19_Push_Fetch_Pull.md)).
- **`git-hooks/` is an owned path in `CODEOWNERS`**, because an edit there silently disables the gate.
- **Never make a hook the only thing standing between you and a leaked secret** — `git add` already
  wrote the blob ([Chapter 05](05_How_Git_Stores_Everything.md)). Layer: `.gitignore`, then hooks,
  then CI, then review.
- **Write the weaknesses down.** `CONTRIBUTING.md` §2 lists what each layer catches *and* the two
  failures nothing catches. A gap you have documented is a gap you can compensate for.

# Architecture Decisions
- **Three layers instead of one paid rule**, because the paid rule was unavailable and the ruling
  against paid tiers stands. Protection moved; it did not disappear.
- **The hook reads the destination ref from stdin**, not the current branch — the difference between
  a hook that works and one that looks like it works.
- **The hook prints recovery instructions.** A block that does not teach the fix produces a
  `--no-verify` habit.
- **`--no-verify` deliberately left available.** A gate you cannot bypass gets deleted; one that
  requires an explicit flag stays installed and makes the bypass a decision.
- **`git rev-parse --git-path hooks`** in the installer rather than a hardcoded `.git/hooks`, so it
  works in worktrees ([Chapter 17](17_Stash_And_Worktrees.md)) and unusual layouts.
- **The installer backs up an existing hook** instead of overwriting it silently.
- **Collaborators get Read, not Write.** Chosen deliberately as the *stronger* option, not as a
  consolation prize.
- **Weaknesses documented in `CONTRIBUTING.md` §2 as a table**, including the two uncaught cases.

# Best Practices
- Install hooks as onboarding step 1, and say so in writing.
- Read the destination ref from stdin; never trust the current branch.
- Handle the deletion push (all-zero sha) explicitly.
- Print the fix and the override in the refusal message.
- Give collaborators **Read** and let them fork — free, and stronger than the paid rule.
- Use `--force-with-lease`, never plain `--force`, on anything shared.
- Verify a hook with `git ls-remote` against a throwaway remote, not by reading the code.
- Re-check GitHub's Settings → Rules occasionally; if server-side protection becomes available, add
  it and keep the layers.

# Beginner Mistakes
- **"Just enable branch protection"** → unavailable on a free private repo. Check before advising it.
- **Checking the current branch in `pre-push`** → `git push origin HEAD:main` walks straight past.
- **Expecting hooks to travel with the repo** → they never do; a fresh clone is unprotected.
- **Blocking with no explanation** → produces a `--no-verify` reflex.
- **Ignoring the deletion case** → deleting `main` is worse than pushing to it.
- **Giving a collaborator Write "to keep it simple"** → Write includes merge.
- **Believing a client-side hook enforces anything** → it stops mistakes; that is its whole job.
- **Not writing down the weaknesses** → the fresh-clone gap gets discovered the hard way.

# Interview Questions
- **Junior:** "What does a `pre-push` hook do?" — Runs before git sends objects to a remote; a
  non-zero exit aborts the push. A common use is refusing pushes to `main` so changes arrive only
  through a pull request.
- **Mid:** "How does the hook know which branch is being pushed to?" — From stdin, not from the
  current branch. Git supplies one line per ref as
  `<local ref> <local sha> <remote ref> <remote sha>`, and the destination is the **third** field.
  Checking the current branch is wrong, because `git push origin HEAD:main` targets `main` from a
  feature branch.
- **Senior:** "Branch protection is paid on your private repo. Design the protection." — Three
  layers, each with its weakness stated. A `pre-push` hook client-side, which stops mistakes but only
  binds where it was installed. Collaborators on **Read** access working from forks, which is
  server-side, free, and actually stronger than branch protection — they have no push permission at
  all rather than a permission with an exception. CI as the visible merge gate, accepting that
  merge-on-red is not mechanically blocked without paid required-checks. Then write the two uncaught
  cases down — a fresh clone without the hook, and a deliberate `--no-verify` — because an unstated
  gap is the one that bites.
- **Staff:** "You cannot buy server-side enforcement. What is your actual risk position?" — I would
  separate *mistakes* from *adversaries*, because the free scheme addresses one and not the other. A
  client-side hook is advisory by construction: `--no-verify` exists, and `.git/hooks/` is not
  cloned, so it cannot be part of a threat model — it is ergonomics for the honest. The genuinely
  enforced control is authorisation: nobody outside the owner holds push access, so the blast radius
  of the missing paid feature is exactly one trusted account. That reframes the question from "how do
  we stop pushes" to "what can that one account do irreversibly", and the answer is force-push and
  history rewrite — so I would mitigate those specifically: `--force-with-lease` as habit, deploy
  from immutable tags rather than a branch name so production identity is a hash, and reliance on the
  fact that abandoned commits survive in reflogs and every other clone. I would also record the
  decision with its date and reasoning, and set a trigger — repo goes public, or a second person gets
  Write — at which point the free scheme is no longer adequate and the plan question gets reopened.
  Documenting the trigger is what stops an accepted risk from silently becoming an unexamined one.

### Why interviewers ask these — and the answer that separates levels
| Testing for | Weak answer | What lands |
|---|---|---|
| Do you know the hook contract? | "It checks the branch before pushing." | Destination comes from stdin field 3; current-branch checks miss `git push origin HEAD:main`, and deletions arrive as an all-zero sha. |
| Do you know what is actually purchasable? | "Just turn on branch protection." | It is paid on private repos — so name the free substitutes and which of them is genuinely server-side. |
| Can you reason about residual risk? | "The hook protects main." | Hooks stop mistakes, not adversaries; the enforced control is authorisation, so scope the risk to what the one privileged account can do irreversibly. |

**The killer follow-up:** *"Which of your three layers would stop a determined developer?"* — Only Layer 2, and only for people who are not the owner: Read access means GitHub itself refuses the push. The hook is bypassable with one flag and absent on any clone where it was never installed, and CI on a free private repo can display a red check but cannot block the merge. Saying that plainly — rather than claiming three layers add up to enforcement — is the whole test.

# Revision Notes
- **Branch protection, required reviews, required checks, CODEOWNERS auto-assign = PAID on private repos** (free on public).
- **Layer 1** `pre-push` hook (client, free): destination ref = **stdin field 3**; handle all-zero sha (deletion). Weakness: hooks aren't cloned.
- **Layer 2** collaborator gets **Read + fork** (server, free): no push permission at all ⇒ **stronger than branch protection**.
- **Layer 3** CI visible on every PR (server, free). Weakness: merge-on-red not mechanically blocked.
- **Uncaught:** fresh clone without the hook · deliberate `--no-verify`. Both written into `CONTRIBUTING.md` §2.
- Verify a hook with `git ls-remote | wc -l` = 0, not by reading it.
- `git rev-parse --git-path hooks` in the installer → worktree-safe.
- `--force-with-lease`, never plain `--force`.
- If the repo goes public or a plan is bought: enable server-side protection **and keep all layers**.

# Cheat Sheet
```bash
# the pre-push contract
#   $1 = remote name   $2 = remote URL
#   stdin, one line per ref:  <local ref> <local sha> <remote ref> <remote sha>
while read -r local_ref local_sha remote_ref remote_sha; do
    branch="${remote_ref#refs/heads/}"        # ← DESTINATION (field 3)
    [ "$local_sha" = "0000000000000000000000000000000000000000" ] && echo "deletion push"
done

bash git-hooks/install.sh                     # install (per clone, per machine)
ls -l "$(git rev-parse --git-path hooks)"     # what is installed here
git rev-parse --git-path hooks                # worktree-safe hooks dir

# test WITHOUT pushing
echo "refs/heads/x aaa refs/heads/main bbb" | bash .git/hooks/pre-push origin url

# prove it end to end (throwaway remote)
git push origin main ; git ls-remote origin | wc -l    # want 0

git push --no-verify origin main              # documented override
git push --force-with-lease                   # safe force: refuses if remote moved
git config --global fetch.prune true
```

# My ERP Section

| Layer | Configuration here |
|---|---|
| **1. `pre-push`** | `git-hooks/pre-push` — protects `main` **and** `master`; reads destination from stdin field 3; handles all-zero-sha deletion; prints how to branch, how to recover from a wrong-branch commit, and how to override |
| Install | `bash git-hooks/install.sh` — uses `git rev-parse --git-path hooks` (worktree-safe), backs up any existing hook, prints what is now enforced |
| Verified | real `git push origin main` **BLOCKED** with `git ls-remote` showing **0 refs**; `master` blocked; `feat/allowed` pushed; `--no-verify` bypassed as documented |
| **2. Fork + Read** | collaborators get **Read** access and work from a fork (`CONTRIBUTING.md` §9) — server-side, free, no push permission at all |
| **3. CI** | `.github/workflows/ci.yml` — lint → migrations → **2,033 tests / 424 s** → docs BLOCKER=0 |
| Documented gaps | `CONTRIBUTING.md` §2 table: owner on a fresh clone with no hook installed; deliberate `--no-verify`. Both listed as **uncaught** |
| Companion hook | `git-hooks/commit-msg` — Conventional Commits, ≤72-char subject, no trailing period ([Ch 25](25_Conventional_Commits.md)) |
| Ownership | `git-hooks/` is an owned path in `.github/CODEOWNERS` — editing a hook can silently disable a gate |
| Re-check trigger | repo goes public, or rulesets become free on private ⇒ enable server-side protection **and keep all three layers** |

# Practice Tasks
1. Read `git-hooks/pre-push`. Find the line that extracts the destination branch and explain why it
   uses `remote_ref` rather than the current branch.
2. Run the stdin test from the Practical section for `main`, `master` and `feat/ok`. Confirm two
   blocks and one allow — without pushing anything.
3. Feed it a deletion push (all-zero `local_sha`) and read the different message.
4. Do the full throwaway-repo test. The line that matters is `git ls-remote origin | wc -l` → `0`.
5. Uninstall the hook (`rm "$(git rev-parse --git-path hooks)/pre-push"`), confirm the push would now
   be allowed in the throwaway repo, then reinstall. You have just demonstrated Layer 1's weakness.
6. Open your own repo's Settings → Rules → Rulesets. Report whether it lets you configure a rule or
   prompts for an upgrade — that is the paid/free line, on your account.

# Homework
- Write a `pre-push` hook that additionally refuses a **force**-push to any branch. Hint: compare
  `remote_sha` against `git merge-base` to detect a non-fast-forward. Then decide whether you want it.
- Set up the fork flow for real with a second GitHub account or a willing friend: Read access, fork,
  cross-repo PR. Confirm they genuinely cannot push to your repository.
- Read GitHub's rulesets documentation and write down exactly which of the four protections you would
  enable first if this repo went public.
- Write your own version of `CONTRIBUTING.md` §2 for a project of your own: the layers, and the
  failures nothing catches. The second list is the valuable one.

# Further Reading & Live Resources
- [githooks manual — `pre-push`](https://git-scm.com/docs/githooks#_pre_push) — the exact stdin contract
- [GitHub Docs — About protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches) — including the plan requirements
- [GitHub Docs — About rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets) — the newer replacement; check availability on your own repo
- [GitHub Docs — Repository roles](https://docs.github.com/en/organizations/managing-user-access-to-your-organizations-repositories/managing-repository-roles/repository-roles-for-an-organization) — why Write includes merge
- [Pro Git — Git Hooks](https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks) — hooks in general; free
- [`git push --force-with-lease`](https://git-scm.com/docs/git-push#Documentation/git-push.txt---force-with-leaseltrefnamegt) — the safe force, and why plain `--force` is not
