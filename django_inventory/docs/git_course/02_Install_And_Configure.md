---
id: git-course-02-install-and-configure
type: lesson
status: active
owner: handwritten
scope: git, setup — installing git, identity, SSH keys, host aliases, the two-account problem
anchors: ~/.gitconfig, ~/.ssh/config, git-hooks/install.sh, CONTRIBUTING.md
verified: 2026-08-03
---

# 02 — Installing & Configuring Git (identity, keys, and the two-account trap)

> Part of [Git Course](00_COURSE_OVERVIEW.md). Prev: [01 — What Version Control Is](01_What_Version_Control_Is.md). Next: [03 — The Three Trees](03_The_Three_Trees.md).

# Learning Objectives
By the end of this chapter you can:
- install git and confirm the version you actually have
- explain why `user.name` and `user.email` are *stamped into every commit* and cannot be changed later without rewriting history
- set up SSH key authentication and explain why it replaced passwords
- read and write an SSH **host alias**, and explain the one this repo depends on
- diagnose the "wrong GitHub account" failure that bit this project for real
- pick between `--local`, `--global` and `--system` config without guessing

# Purpose
Git works out of the box, which is exactly the problem: the defaults are wrong in ways you
will not notice for months. Your name will be wrong on 200 commits. Your pushes will ask for
a password that no longer exists. And if you have two GitHub accounts — as the owner of this
repo does — git will cheerfully use the wrong one and give you an error message that names
the wrong cause.

This chapter is the twenty minutes of setup that prevents all of it.

# The Problem
A fresh git install knows nothing about you. Commit anyway and you get this:

```
Author: root <root@laptop.(none)>
```

That is now **permanent**. The author name and email are part of the commit object — they
feed into its hash. Changing them later means rewriting every commit that has them, which
means new hashes for all of them, which means a force-push and every collaborator's clone
breaking. Ten seconds of setup up front; a genuinely painful afternoon later.

The second problem is authentication. GitHub **removed password authentication for git
operations in August 2021**. So the thing every old tutorial tells you to do no longer works
at all, and the error message does not say "passwords were removed" — it says
`Authentication failed`, which sounds like you typed it wrong.

# Theory (from zero)

### What "installing git" actually gives you
Git is a single command-line program plus a pile of subcommands. `git commit`, `git log`,
`git push` are not separate tools — they are one binary dispatching on the first argument.
That is why `git --version` is the only install check you need.

```bash
git --version
# git version 2.34.1
```

Anything 2.23 or newer has `git switch` and `git restore`, which this course uses in
preference to the older overloaded `git checkout`. If you are older than that, upgrade —
`checkout` doing five unrelated jobs is a genuine source of beginner accidents.

### Identity: the two settings that go into every commit
```bash
git config --global user.name  "Umesh Chaudhary"
git config --global user.email "umesh29mar@gmail.com"
```

These are not a login. Git does **not** verify them — you can put any name and any email in
your config and git will stamp it into the commit without complaint. That surprises people,
and it is the reason [Chapter 31 — Signed Commits](31_Signed_Commits.md) exists: if identity
is unverified by design, then proving authorship needs a cryptographic signature, not a
config value.

What the email *does* control is **attribution on GitHub**. GitHub matches the commit's email
against the emails registered on accounts. Match, and the commit shows your avatar and counts
toward your contribution graph. No match, and the commit shows a generic avatar and belongs
to nobody.

### The three config levels
Git reads three files, in order, later winning:

| Level | Flag | File | Use it for |
|---|---|---|---|
| System | `--system` | `/etc/gitconfig` | whole-machine defaults (rare) |
| Global | `--global` | `~/.gitconfig` | **you** — your name, email, editor, aliases |
| Local | `--local` | `<repo>/.git/config` | **this repo only** — remotes, per-repo identity |

`--local` is the default when you omit the flag, which trips people up: `git config user.email x`
sets it for *this repo only*, silently.

To see where a value came from — the single most useful config command:
```bash
git config --list --show-origin | grep user\.
# file:/home/tech/.gitconfig    user.name=umesh-personal
# file:/home/tech/.gitconfig    user.email=umesh29mar@gmail.com
```

`--show-origin` is how you answer "why is my commit author wrong?" in one command instead of
guessing.

### SSH keys instead of passwords
An SSH key is a **pair** of files: a private key that never leaves your machine, and a public
key you hand out freely. GitHub stores the public half. When you push, your machine proves it
holds the private half without ever transmitting it.

```bash
ssh-keygen -t ed25519 -C "umesh29mar@gmail.com"
# creates ~/.ssh/id_ed25519       ← PRIVATE. never share, never commit.
#         ~/.ssh/id_ed25519.pub   ← public. paste this into GitHub.
```

`ed25519` over `rsa`: shorter, faster, and modern. `-C` is just a comment label so you can
tell keys apart later on GitHub's key list.

> ⚠️ The private key is exactly the kind of file that must never enter a repository. The
> monorepo-root `.gitignore` blocks `*.pem` and `*.key` patterns for this reason — see
> [Chapter 07](07_Gitignore.md) and [Chapter 33](33_Secrets_And_Leaks.md).

### SSH host aliases — the concept this repo depends on
`~/.ssh/config` lets you invent a **fake hostname** that maps to a real host plus a specific
key. That is how one machine can talk to two GitHub accounts.

```
Host github-personal
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519_personal
    IdentitiesOnly yes
```

Now `git@github-personal:umesh29032/umesh-personal.git` means *"connect to github.com, but
authenticate with the personal key."* The word `github-personal` does not exist on the
internet; it exists only in your SSH config.

`IdentitiesOnly yes` matters more than it looks: without it, SSH offers **every** key it knows
until one works. With two GitHub accounts, the wrong key often wins the race, and GitHub
authenticates you as the wrong person — with a permissions error that blames the repo.

> 💡 **Samjho aise:** SSH key = **ghar ki chaabi**. Public key = taala jo tum GitHub ko de
> dete ho; private key = chaabi jo sirf tumhare paas rehti hai — kabhi kisi ko nahi, kabhi
> git mein nahi. Aur host alias = **speed-dial**. `github-personal` koi asli address nahi hai;
> tumne apni diary mein likh diya "personal" = ye number + ye chaabi. Do accounts ho toh yehi
> bachata hai — warna SSH galat chaabi pehle lagata hai aur GitHub bolta hai "tum wo aadmi
> nahi ho", aur tum repo ka permission dhoondhte reh jaate ho.

# Real World Example (this repo)
This repository authenticates through exactly such an alias. The remote is not
`git@github.com:…` — it is:

```bash
git remote -v
# origin  git@github-personal:umesh29032/umesh-personal.git (fetch)
# origin  git@github-personal:umesh29032/umesh-personal.git (push)
```

And the identity actually stamped on the last commit:

```bash
git log -1 --format='%an <%ae>%n%cn <%ce>'
# umesh-personal <umesh29mar@gmail.com>
# umesh-personal <umesh29mar@gmail.com>
```

Two names there, not one: **author** (who wrote it) and **committer** (who applied it). They
differ when someone rebases or cherry-picks your work — `git log` shows the author by default,
which is why a rebase can look like it "lost" who applied it.

### The two-account failure, as it actually happened
This project hit the real version of this problem on 2026-08-03. `git push` worked perfectly.
Then creating a pull request failed:

```
pull request create failed: GraphQL: must be a collaborator (createPullRequest)
```

"Must be a collaborator" reads like a permissions problem on the repo. It was not. The cause:

- **`git push`** goes over SSH → uses the `github-personal` alias → correct key → correct
  account (`umesh29032`) → works.
- **`gh pr create`** goes over the **GitHub API** → uses the `gh` CLI's own stored token →
  which was logged in as **`umesh2030`**, the owner's *office* account → not a collaborator on
  `umesh29032`'s repo → refused.

**Two different auth systems on one machine, pointing at two different accounts.** The lesson:
`git` and `gh` do not share credentials. Check both.

```bash
gh auth status
# ✓ Logged in to github.com as umesh2030      ← the culprit
```

# Visual Diagram
```
   YOUR MACHINE                                        GITHUB
   ───────────                                         ──────

   git push  ──► SSH ──► ~/.ssh/config
                          │ Host github-personal
                          │   HostName github.com
                          │   IdentityFile id_ed25519_personal
                          └──────────────────────────► account: umesh29032  ✅

   gh pr create ──► HTTPS API ──► ~/.config/gh/hosts.yml
                                   │ oauth_token: ghp_…
                                   └───────────────────► account: umesh2030  ❌
                                                          "must be a collaborator"

   SAME machine. SAME repo. DIFFERENT credential stores.
   ───────────────────────────────────────────────────────────
   identity in a COMMIT is a third thing again — just config text:
     git config user.name / user.email   ──► stamped, unverified
```

# Practical — set yourself up from scratch
```bash
# 1. version check
git --version                                  # want >= 2.23 for switch/restore

# 2. identity (global = you, everywhere)
git config --global user.name  "Your Name"
git config --global user.email "you@example.com"

# 3. sane defaults worth setting once
git config --global init.defaultBranch main     # not "master"
git config --global pull.rebase true            # linear history on pull (ch 13)
git config --global push.default current        # push THIS branch, no surprises
git config --global core.editor "code --wait"   # or nano/vim
git config --global rerere.enabled true         # remember conflict resolutions (ch 12)

# 4. SSH key
ssh-keygen -t ed25519 -C "you@example.com"
cat ~/.ssh/id_ed25519.pub                       # paste into GitHub → Settings → SSH keys

# 5. prove it works — this is the ONLY test that matters
ssh -T git@github.com
# Hi <username>! You've successfully authenticated, but GitHub does not provide shell access.
#                ^^^^^^^^^^ CHECK THIS NAME. It is which account you actually are.

# 6. verify every value and where it came from
git config --list --show-origin | grep -E 'user\.|init\.|pull\.'
```

# Production Walkthrough
Setting up a **second machine** for this repo, in order, with the reason for each step:

1. `git --version` — confirm ≥ 2.23.
2. Global identity — same email as the first machine, or your commits split across two
   identities in GitHub's contribution graph.
3. Generate a **new** key for this machine. Do not copy the private key across machines; one
   key per machine means one key to revoke if a laptop is lost.
4. Add the `~/.ssh/config` host alias if this machine also has a work account.
5. `ssh -T git@github-personal` and **read the name it greets you with**.
6. Clone. Then `gh auth status` — if `gh` is installed at all, confirm which account it holds.
7. **`bash git-hooks/install.sh`** — hooks live in `.git/hooks/`, which git never clones, so
   protection does not travel with the repo. On a fresh clone you are unprotected until you
   run this. See [Chapter 27](27_Pre_Push_Protection.md) and `CONTRIBUTING.md` §2.

Step 7 is the one people skip, and it is the one that lets a direct push to `main` through.

# Debugging Guide

| Symptom | Cause | Fix |
|---|---|---|
| `Author: root <root@laptop.(none)>` | no `user.name`/`user.email` set | set them, then `git commit --amend --reset-author` for the last commit |
| `Authentication failed` on push | GitHub removed password auth in 2021 | switch the remote to SSH, or use a Personal Access Token over HTTPS |
| `Permission denied (publickey)` | key not offered or not registered | `ssh -vT git@github.com` and read which key it tried |
| `ssh -T` greets the **wrong username** | SSH offered the wrong key first | add the host alias plus `IdentitiesOnly yes` |
| Push works, `gh` commands fail | `git` uses SSH, `gh` uses its own token | `gh auth status`, then `gh auth switch` or `gh auth login` |
| Commits show a generic avatar on GitHub | commit email not on your GitHub account | add that email to GitHub, or fix the config and re-commit |
| Config change "did nothing" | you set `--local` in the wrong repo | `git config --list --show-origin` |

The single most valuable command here is `ssh -vT git@github.com`. The `-v` prints every key
it offers, in order, so "which key did it actually use" stops being guesswork.

# Performance Notes
- Config reads are trivial — three small files parsed per command.
- SSH connections are the slow part of a push. `ControlMaster auto` in `~/.ssh/config` reuses
  one connection across commands, noticeably faster if you push often.
- `core.fsmonitor true` (git ≥ 2.37) speeds up `git status` in large repos by watching the
  filesystem instead of scanning it. This monorepo tracks ~2,400 files, so it is optional
  here; on a 100k-file repo it is transformative.
- `IdentitiesOnly yes` also *speeds up* auth: without it SSH tries keys in sequence, and each
  rejection costs a round trip.

# Security Considerations
- **The private key never leaves the machine.** Not into a repo, not into chat, not into a
  backup that syncs to a cloud drive. One key per machine.
- **Passphrase-protect the key.** `ssh-keygen` offers it; take it. An unprotected key on a
  stolen laptop is instant push access to everything.
- **`~/.ssh/` must be `700` and keys `600`.** SSH refuses to use a key other users can read —
  a good default that people work around instead of fixing.
- **`user.email` is public.** Every commit carries it, and anyone who clones can read it. Use
  a GitHub `noreply` address if that matters to you.
- **Config identity is not authentication.** Anyone can set your name and email and commit as
  "you". Only [signed commits](31_Signed_Commits.md) prove authorship.
- **Revoking is per-key.** Lost a laptop? Delete that one public key on GitHub; other machines
  keep working. That only holds if you did not share one key across machines.

# Architecture Decisions
- **SSH over HTTPS-with-token for this repo.** Keys are per-machine and revocable individually,
  and there is no token to accidentally paste into a file. HTTPS+PAT is the better choice in
  locked-down networks that block port 22.
- **A host alias rather than juggling `IdentityFile` per command.** The owner has a personal
  and an office GitHub account on one machine. The alias makes the choice part of the remote
  URL — declarative and impossible to forget — rather than a flag someone must remember.
- **`pull.rebase true` globally.** This project prefers a linear history; a merge commit
  created by a routine `git pull` is noise nobody chose. See [Chapter 13](13_Rebase.md).
- **`init.defaultBranch main`.** Matches GitHub's default, so a fresh local repo does not
  start on a branch name the remote does not use.
- **`rerere.enabled true`.** Records how you resolved a conflict so the identical conflict
  resolves itself next time — pure upside on a long-running branch ([Chapter 12](12_Merge_Conflicts.md)).

# Best Practices
- Set `user.name` and `user.email` **before** your first commit, always.
- Run `ssh -T git@github.com` after any key change and **read the username** it returns.
- One SSH key per machine; passphrase on every one.
- Use `git config --list --show-origin` instead of theorising about which config won.
- If `gh` is installed, check `gh auth status` — it is a separate identity from git's.
- On a fresh clone of this repo, `bash git-hooks/install.sh` before your first commit.
- Never copy a private key between machines, however convenient it feels.

# Beginner Mistakes
- **Committing before setting identity** → permanent wrong author on those commits. Fixing
  more than the last one means rewriting history ([Chapter 34](34_Rewriting_History.md)).
- **Following a tutorial that says "enter your GitHub password"** → it cannot work; password
  auth for git was removed in 2021. The error says `Authentication failed`, which misleads.
- **Committing the private key** → total compromise. And git history is append-only, so
  deleting it later does not remove it; you must rotate the key *and* rewrite history.
- **Assuming `git` and `gh` share a login** → the exact bug this repo hit: push succeeded,
  `gh pr create` failed with `must be a collaborator`, and the message blamed the wrong thing.
- **Setting `--local` when you meant `--global`** (or the reverse) → config that works in one
  repo and mysteriously not in another.
- **Sharing one SSH key across machines** → losing one laptop means revoking access for all
  of them.
- **Skipping `IdentitiesOnly yes` with two accounts** → SSH authenticates as whichever key
  wins, intermittently, which is the worst kind of bug.

# Interview Questions
- **Junior:** "What do `user.name` and `user.email` do?" — They are stamped into every commit
  object you create and are how GitHub attributes commits to an account. Git does not verify
  them; they are configuration, not credentials.
- **Mid:** "Why can't you just use your GitHub password to push any more?" — GitHub removed
  password authentication for git operations in August 2021. Use SSH keys, or HTTPS with a
  Personal Access Token. SSH is generally preferable because keys are per-machine and
  individually revocable.
- **Senior:** "One laptop, two GitHub accounts. How do you keep them apart?" — An SSH host
  alias per account in `~/.ssh/config`, each with its own `IdentityFile` and
  `IdentitiesOnly yes`, and encode the alias in the remote URL so the choice is declarative.
  Add per-repo `user.email` via `--local` or `includeIf` on a directory, and remember the `gh`
  CLI keeps a *separate* token — its account can differ from SSH's.
- **Staff:** "Commit identity is unverified config. What does that mean for your supply chain?"
  — Author fields are trivially forgeable, so `git log` is attribution, not proof. If provenance
  matters you need commit signing (SSH or GPG) plus a policy that unsigned or unverified commits
  cannot reach a protected branch — and that policy has to be enforced server-side, because a
  client-side hook is advisory. The gap is worth stating explicitly rather than assuming
  `git log` is evidence.

### Why interviewers ask these — and the answer that separates levels
| Testing for | Weak answer | What lands |
|---|---|---|
| Do you know identity is not auth? | "It's my GitHub login for git." | It is unverified config baked into the commit hash; attribution comes from email matching, and real proof needs signing. |
| Have you debugged auth, or only followed steps? | "I re-entered my password." | Name the 2021 password removal, then `ssh -vT` to see which key was offered, then check that `gh` holds a different token entirely. |
| Can you handle multi-account reality? | "I use two computers." | Host aliases plus `IdentitiesOnly yes`, alias encoded in the remote URL, `includeIf` for per-directory email — one machine, unambiguous accounts. |

**The killer follow-up:** *"Your push works but the API tool says you're not a collaborator. What is happening?"* — Two credential stores. Git went over SSH with the right key; the API tool used its own stored OAuth token for a different account. `gh auth status` proves it in one command. Answering this is the difference between having read a setup guide and having actually debugged one.

# Revision Notes
- Identity = `user.name` + `user.email`, **stamped into the commit, unverified**.
- Config precedence: system → global → **local wins**. `--show-origin` tells you which.
- Password auth for git died **August 2021**. SSH keys or PAT.
- SSH key = private (never leaves) + public (give away freely). One per machine, passphrased.
- **Host alias** = fake hostname → real host + specific key. Needs `IdentitiesOnly yes`.
- This repo: `git@github-personal:umesh29032/umesh-personal.git`.
- **`git` and `gh` have separate logins.** Push OK + API fails ⇒ check `gh auth status`.
- Fresh clone ⇒ `bash git-hooks/install.sh`, because `.git/hooks/` is never cloned.

# Cheat Sheet
```bash
git --version                                   # >= 2.23 for switch/restore
git config --global user.name  "Name"           # who you are, everywhere
git config --global user.email "you@x.com"      # must match a GitHub account email
git config --list --show-origin                 # WHICH file set WHICH value  ← the debug one
git config --global init.defaultBranch main
git config --global pull.rebase true            # linear history on pull
git config --global rerere.enabled true         # remember conflict resolutions

ssh-keygen -t ed25519 -C "you@x.com"            # new key pair (passphrase it)
cat ~/.ssh/id_ed25519.pub                       # public half → GitHub settings
ssh -T git@github.com                           # READ the username it greets you with
ssh -vT git@github.com                          # which keys were offered, in order

gh auth status                                  # gh's token is a SEPARATE identity
git remote -v                                   # is the URL using your host alias?
bash git-hooks/install.sh                       # per-clone: hooks are never cloned

git commit --amend --reset-author                # fix author on the LAST commit only
```

# My ERP Section

| Thing | Value in this project |
|---|---|
| Git root | `/home/tech/umesh-personal` — a **monorepo**; the Django ERP is `django_inventory/` |
| Remote | `git@github-personal:umesh29032/umesh-personal.git` |
| SSH alias | `github-personal` → `github.com` with the personal key |
| GitHub account | **`umesh29032`** |
| `gh` CLI account | **`umesh2030`** — the owner's *office* account. Wrong for this repo; the cause of the `must be a collaborator` failure |
| Commit identity | `umesh-personal <umesh29mar@gmail.com>` |
| Default branch | `main`; working branch `new_flask_app` |
| Per-clone setup | `bash git-hooks/install.sh` — see `CONTRIBUTING.md` §9 |

The `gh`/SSH split is recorded in the project's memory as a standing note, because the error
message actively points at the wrong cause and cost real time once already.

# Practice Tasks
1. Run `git config --list --show-origin | grep user\.` and say out loud which file each value
   came from and why that file won.
2. Make a throwaway repo, unset your identity locally
   (`git config --local --unset user.email`), commit, then look at `git log`. See the bad
   author. Fix it with `git commit --amend --reset-author`. Confirm the commit **hash changed**
   — that is the proof identity is part of the hash.
3. Run `ssh -vT git@github.com` and find the line naming the key it offered. Count how many
   keys it tried before one worked.
4. Write a `~/.ssh/config` alias called `github-test` pointing at `github.com` with an explicit
   `IdentityFile`, then `ssh -T git@github-test`. Same greeting, different route.
5. Run `gh auth status` (if installed). If the account differs from your SSH account, you have
   reproduced this repo's real bug on your own machine.

# Homework
- Set up a **second** SSH key and a second host alias, and clone the same repo twice — once
  through each alias. Confirm with `ssh -T` that each route authenticates as the intended
  account. This is the multi-account skill that comes up the moment you have a job and a
  side project.
- Read `~/.gitconfig` top to bottom and delete anything you cannot explain. A config you
  copied from a blog is a config that will surprise you.
- Investigate `includeIf` in `git config` and set it so any repo under a `work/` directory
  automatically uses your work email. This is the clean fix for per-repo identity.
- Look up how GitHub's `noreply` email works and decide whether you want your real address in
  every public commit of this repository.

# Further Reading & Live Resources
- [Pro Git — First-Time Git Setup](https://git-scm.com/book/en/v2/Getting-Started-First-Time-Git-Setup) — the canonical chapter, free
- [GitHub Docs — Connecting with SSH](https://docs.github.com/en/authentication/connecting-to-github-with-ssh) — key generation, agent, testing, per platform
- [GitHub Blog — Token authentication requirements](https://github.blog/2020-12-15-token-authentication-requirements-for-git-operations/) — the announcement that killed password auth
- [`ssh_config` manual](https://man.openbsd.org/ssh_config) — `Host`, `IdentityFile`, `IdentitiesOnly`, `ControlMaster`
- [git-config reference](https://git-scm.com/docs/git-config) — every option, including `includeIf`
- [`gh auth` reference](https://cli.github.com/manual/gh_auth) — because it is a separate identity from git's
