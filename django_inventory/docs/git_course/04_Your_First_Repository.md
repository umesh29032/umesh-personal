---
id: git-course-04-your-first-repository
type: lesson
status: active
owner: handwritten
scope: git, version control — creating a repository from zero, what `.git` holds, identity config, the first commit
anchors: README.md, CONTRIBUTING.md, git-hooks/install.sh, git-hooks/pre-push, django_inventory/.gitignore
verified: 2026-08-03
---

# 04 — Your First Repository (`git init`, and what those files inside `.git` actually are)

> Part of [Git Course](00_COURSE_OVERVIEW.md). Prev: [03 — The Three Trees](03_The_Three_Trees.md). Next: [05 — How Git Stores Everything](05_How_Git_Stores_Everything.md).

# Learning Objectives
By the end of this chapter you can:
- turn any folder into a repository and explain what `git init` created, file by file
- read `git status --short` correctly — untracked vs unstaged vs staged — and undo each one
- set your identity at the right scope, and say why a wrong email is permanent
- read a commit back out of the database with `git cat-file`
- explain why `.git/hooks/` is never cloned, and undo every step here — including "I ran `git init` in the wrong folder"

# Purpose
Everything later — branches, merges, rebase, reflog, CI — runs *inside* a repository. This chapter builds one from nothing and opens the lid, because most confusing git errors later ("not a git repository", "please tell me who you are", "why isn't my hook running?") are really questions about what `git init` did and did not do.

# The Problem
Before git, a folder has one state: *now*. You try an idea, so you copy it to `project_v2/`, then `project_v2_final_FIXED/`. A week later nobody knows which one is deployed, or why anything changed.

There is a sharper pain, and this repository suffered it: you *do* run `git init` and you *do* commit — but with the wrong identity, and a commit can never be edited. This repo's first commit still says `Umesh <umesh.chaudhary@thesqua.re>` — the owner's **office** email, permanently, in his **personal** repo, 324 commits ago. Fixing it now means rewriting history ([Ch 34](34_Rewriting_History.md)). Two minutes of setup below prevents it.

# Theory (from zero)

### A repository is two things, and only one of them is git's
The **working tree** is `/home/tech/umesh-personal/` — your real, editable files. The **repository** is `/home/tech/umesh-personal/.git/` — git's own database. Delete a file from the working tree and git still has every committed version of it. Delete `.git` and your files survive but **all history is gone instantly, with no undo**. Your files are safe from git; your history is not safe from `rm -rf .git`.

### What `git init` creates
No network, no file changes — one hidden directory:

| Thing | What it is |
|---|---|
| `HEAD` | one line naming the branch you are on |
| `config` | this repo's settings (remotes, identity overrides) |
| `hooks/` | scripts git runs at certain moments; ships as `*.sample` only |
| `info/exclude` | ignore rules **private to you** — never committed, unlike `.gitignore` |
| `objects/` | the content database: every file version and commit ([Ch 05](05_How_Git_Stores_Everything.md)) |
| `refs/` | branch and tag pointers — files whose content is a commit hash ([Ch 06](06_The_Commit_Graph.md)) |

(Plus `description`, used only by the ancient `gitweb` viewer.) Using the repo adds more: `index` (the staging area, [Ch 03](03_The_Three_Trees.md)), `logs/` (the reflog, [Ch 16](16_Reflog.md)), `COMMIT_EDITMSG`, `packed-refs`, `ORIG_HEAD`, `FETCH_HEAD`. `HEAD` really is this simple — this repo's, right now: `ref: refs/heads/new_flask_app`. A pointer to a pointer.

### Identity is stamped into every commit
A commit records who wrote it as plain text *inside the commit object*; git refuses to commit if it cannot tell (`Please tell me who you are`). Most specific scope wins — `git config user.email "…"` writes `.git/config` (this repo only), `--global` writes `~/.gitconfig` (all repos). Better on a work laptop with personal projects is a **conditional include**, which is what this machine uses: an `[includeIf "gitdir:/home/tech/umesh-personal/"]` block whose `path = ~/.gitconfig-personal`. Any repo under that directory picks up the personal identity automatically; everything else keeps the office one.

Git 2.34.1 here also still names the first branch `master` and prints a hint, *unless* `init.defaultBranch` is set — it is **unset** on this machine, which is why the owner's notes end with `git branch -M main`.

> ⚠️ **The undo is expensive.** Author and email are part of the commit's content, so changing them changes its hash and every hash after it ([Ch 05](05_How_Git_Stores_Everything.md)). Last commit: `git commit --amend --reset-author`. 324 commits back: `git-filter-repo` + force-push ([Ch 34](34_Rewriting_History.md)). Configure first, commit second.

### The commit loop, and the trap in it
`git add` copies the file's **content at that moment** into the index; `git commit` freezes the index into an object with a message, parent, author and timestamp. Edit again *after* `add` and the new edit is **not** staged — everyone is bitten by this once.

### `git status --short` — three states, three different undos
| Status | Meaning | Undo |
|---|---|---|
| `?? file` | untracked: git has never seen it | `rm file`, or ignore it ([Ch 07](07_Gitignore.md)) |
| ` M file` | tracked, edited, **not** staged | `git restore file` — **discards the edit, no recovery** |
| `M  file` | edit is staged in the index | `git restore --staged file` (keeps the edit) |

Two columns, deliberately: **left = index vs last commit, right = working tree vs index.**

### `init` vs `clone`, and what clone refuses to bring
`git clone` copies an existing repo *and* wires up `origin` ([Ch 18](18_Remotes.md)) — but never `.git/hooks/`, because a travelling hook would execute a stranger's script on your machine at clone time. Honest consequence, written into `CONTRIBUTING.md` §2: hook protection is real only **on machines where someone installed the hooks** — hence tracked hooks plus `bash git-hooks/install.sh`.

> 💡 **Samjho aise:** Folder tumhari **dukaan** hai, `.git` uske peeche rakhi **bahi-khata**. `git init` = "naya khaali register kholo" — saaman ko haath nahi lagaya. `git add` = register ke *kacche panne* pe entry, `git commit` = us panne pe **pen se pakki entry + tareekh + naam**. `.git/hooks/` wo staff-rules hain jo register ke saath copy nahi hote — nayi dukaan pe dobara chipkane padte hain (`install.sh`). Register phaad diya (`rm -rf .git`) to saaman bacha rahega, hisaab hamesha ke liye gaya.

# Real World Example (this repo)
The root `README.md` here is not documentation — it is the owner's **actual notes from the day he ran `git init`** (blob `05fdcb8d`, 2,259 bytes):

```bash
$ git cat-file -p HEAD:README.md      # real content, trimmed
git init
git config user.email "umesh.personal@example.com"
git add . && git commit -m "Initial commit - add DSA folder"
git branch -M main
git remote add origin git@github.com-personal:umesh29032/umesh-personal.git
```

And what the repo actually *recorded* as its first commit:

```bash
$ git rev-list --max-parents=0 HEAD     # zero parents = the root commit
43f4e3b93c6aafdb032c7044d43531e98de5079c

$ git cat-file -p 43f4e3b9
tree 15333d0bbc0c3490d1502a1cd696e1f161aea620
author Umesh <umesh.chaudhary@thesqua.re> 1749742883 +0530
committer Umesh <umesh.chaudhary@thesqua.re> 1749742883 +0530

Initial commit
```

Three real things: **no `parent` line** (that absence *is* the definition of a root commit, [Ch 06](06_The_Commit_Graph.md)); the **office email**, because identity was configured *after* the first commit; and `1749742883 +0530` = Unix timestamp + IST offset = **2025-06-12 21:11:23 +0530** — git stores the instant *and* the zone.

# Visual Diagram
```
   $ git init          ~/umesh-personal/
                       ├── README.md  DSA/  django_inventory/  ← WORKING TREE (untouched)
                       └── .git/     HEAD · config · objects/ · refs/ · hooks/ · info/
                                     ↑ the database (new). Delete it ⇒ history gone.

   THE FIRST COMMIT (three trees, left to right):
     working tree ──git add──► index ──git commit──► objects/ + refs/heads/main
         edit                 staged             permanent, hashed, immutable
          │                     │                          │
          └ git restore <f>     └ git restore --staged      └ git commit --amend
            (DESTROYS edit)       (keeps edit)                (tip only; older ⇒ Ch 34)
```

# Practical — build a repo from zero, then undo every step
Use a throwaway folder, never a real project.

```bash
mkdir ~/git-practice && cd ~/git-practice
git init          # git 2.34.1 with init.defaultBranch unset prints the 'master' hint, then:
                  # Initialized empty Git repository in /home/tech/git-practice/.git/
git branch -M main                 # rename the branch you already have
git rev-parse --show-toplevel      # /home/tech/git-practice  ← the repo root
ls -A .git                         # HEAD config description hooks info objects refs
git config user.email "you@example.com"   # identity BEFORE the first commit
```
The loop, watching status change, then every undo:
```bash
echo "hello" > notes.md
git status --short        # ?? notes.md   (untracked)
git add notes.md          # ── then ──    A  notes.md   (staged, new file)
git commit -m "docs: add notes"
echo "second line" >> notes.md
git status --short        # AM notes.md   ← A = staged version, M = newer unstaged edit
git diff / git diff --staged        # the unstaged part / what would actually be committed

git restore --staged notes.md       # unstage, keep file and edit            (safe)
git restore notes.md                # discard unstaged edits  (DESTRUCTIVE, no reflog)
git rm --cached notes.md            # stop tracking, keep on disk  (what 42a2ecc4 did)
git commit --amend --reset-author     # rewrite the LAST commit + re-stamp identity
```
And *"I ran `git init` in my home directory"* — symptom: `git status` lists your whole home folder as untracked. The cure deletes that repo's history outright and no reflog undoes it, so check `pwd` twice: `rm -rf <that path>/.git` (shown, not run).

# Production Walkthrough
Nobody runs `git init` here again — it exists. The real-world version is **onboarding** (`CONTRIBUTING.md` §9): a collaborator gets **Read** access, not Write, and works from a fork.
```bash
git clone git@github.com:<their-username>/umesh-personal.git            # 1. THEIR fork
git remote add upstream git@github.com:umesh29032/umesh-personal.git    # 2. track the real repo
bash git-hooks/install.sh                                              # 3. NOT OPTIONAL
cd django_inventory && cp .env.example .env                            # 4. project setup
```
Step 3 is the skipped one, and skipping it hits the gap §2 admits in writing: *"Owner on a fresh clone with no hook installed → **nothing**."* After it, `ls .git/hooks` shows the live `pre-push`, `commit-msg` and `pre-commit` beside git's untouched `*.sample` files: `pre-push` refuses `git push origin main` locally ([Ch 27](27_Pre_Push_Protection.md)) and `commit-msg` rejects a non-Conventional-Commits message ([Ch 25](25_Conventional_Commits.md)).

# Debugging Guide
| Symptom | Cause | Fix |
|---|---|---|
| `fatal: not a git repository … .git` | you are outside any repo | `cd` in; confirm `git rev-parse --show-toplevel` |
| `Please tell me who you are` | no `user.email` at any scope | set it, then `--amend --reset-author` if you already committed |
| Commit shows the wrong email | global identity used before the local override existed | fix config; `--amend` for the tip, else [Ch 34](34_Rewriting_History.md) |
| `git status` lists thousands of files | `git init` ran in `$HOME` or above the project | check `--show-toplevel`, delete that stray `.git` |
| Hook does not run after cloning | `.git/hooks/` is never cloned, by design | `bash git-hooks/install.sh` |
| A file will not stage | it matches an ignore rule | `git check-ignore -v <file>` names the rule; `git add -f` overrides |

# Performance Notes
- `git init` is instant: a few small files, zero objects.
- Clone cost is *history*, not checkout. This monorepo's `.git` is **97 MB** for **2,407 tracked files** and **324 commits** — a clone downloads all of it. `git clone --depth 1` (shallow) takes only the latest commit: fine for CI, painful for `log`/`bisect`.
- `git status` cost scales with the files it must `stat`, so untracked junk hurts: commit `42a2ecc4` untracked **2,954** files (2 dumps + 2,952 `node_modules` files) that every earlier `status` had to walk. And a first commit adding 200 MB of binaries is fast today, permanent forever ([Ch 37](37_Large_Files_And_Performance.md)).

# Security Considerations
- **`.git` is the whole repository.** If a web server serves the project directory, `https://site/.git/config` hands over your remote URL and `objects/` your entire source. Deploy built artefacts, never a checkout.
- **`git add .` is how secrets get committed.** Two `pg_dump` files were committed here while the repo was public. Root cause was *not* a missing rule: `django_inventory/.gitignore:114` already ignored `db_backups/` — which is why the live ERP never leaked one — but a `.gitignore` guards **only its own subtree**, and this is a monorepo, so `Django_app/` sat outside it ([Ch 07](07_Gitignore.md), [Ch 33](33_Secrets_And_Leaks.md)).
- **`git rm --cached` un-tracks; it does not un-publish** — the content still exists in every earlier commit. And hooks are trusted code: `install.sh` copies scripts git will execute, so read one before installing it.

# Architecture Decisions
- **One monorepo, not one repo per project.** Root `/home/tech/umesh-personal`; the ERP is `django_inventory/`, with `Django_app`, `DSA` and a gitignored `sw obsidian` as siblings. One clone, one history, one CI config — at the cost of every `.gitignore` needing deliberate scoping, the exact trap the dump incident sprang.
- **Rules for dangerous file *types* live at the monorepo root**: `*.sql`, `*.dump`, `*.sql.gz`, `db_backups/`, `backups/`, `node_modules/`, verified blocked at five locations. `git add -f` still works, deliberately, so a genuine code `.sql` stays committable as a conscious act.
- **Hooks tracked in `git-hooks/` + an installer**, rather than pretending `.git/hooks/` is shareable. Rejected: paying for server-side branch protection (owner ruling — money goes to deploy infrastructure). Accepted in writing: a hook protects only machines where it was installed.
- **Identity by conditional include**, so the office identity cannot leak into this tree again.

# Best Practices
- Set `user.name`, `user.email` and `init.defaultBranch` **before** the first commit.
- Run `git rev-parse --show-toplevel` when unsure where you are — cheaper than deleting a `.git`.
- Write `.gitignore` in the same breath as `git init`, before the first `git add .`.
- Prefer `git add <path>` over `git add .` until `git status` is boring.
- Install hooks as the first command after any clone.
- Never store a secret or database dump in a repo, even a private one. Private today, public later.

# Beginner Mistakes
- **`git init` in `$HOME` or on top of an existing repo** → `git status` lists your whole home directory, or you create a half-ignored nested repo. Check `--show-toplevel`, remove only the stray `.git`.
- **Committing before setting identity** → wrong author forever, exactly like `43f4e3b9`. `--amend --reset-author` fixes only the tip.
- **`git add .` first, `.gitignore` later** → `node_modules`, `.env`, dumps tracked. `git rm --cached` untracks (as `42a2ecc4` did for 2,954 files) but history keeps them.
- **Thinking `.gitignore` is repo-wide** → in a monorepo it guards only its own subtree. That misunderstanding put two `pg_dump` files in a public repo.
- **`rm -rf .git` to "start clean"** → files survive, all history dies, no reflog. You wanted `git rm --cached` or `git restore`.
- **Confusing `git restore <f>` with `git restore --staged <f>`** → the first destroys your edit, the second only unstages.
- **Editing after `git add` and expecting that edit to be committed** → the index holds the *old* content; `status` shows `AM`, so re-`add`.

# Interview Questions
- **Junior:** "What does `git init` actually do?" — Creates a `.git` directory holding `HEAD`, `config`, `objects/`, `refs/`, `hooks/`, `info/`. It does not modify, move or upload files, and needs no network. Until the first commit, `objects/` and `refs/heads/` are effectively empty and `HEAD` points at a branch that does not exist yet.

- **Mid:** "A colleague's commits show the wrong email. What happened, and how do you fix it?" — Identity resolves repo scope → global → system; they committed before configuring it, so the work address got stamped in. The author is *part of the commit object*, so it cannot be edited in place: fix config, then `--amend --reset-author` for the tip, or `git-filter-repo` + force-push for older commits, which changes every downstream hash and needs coordination. Prevention: an `includeIf "gitdir:…"` block so personal trees pick up the personal identity automatically.

- **Senior:** "Why aren't hooks cloned, and how do you enforce hook policy across a team?" — A cloned hook would execute attacker-supplied code at clone time, so `.git/hooks/` sits outside the transferred data. To make policy real, commit the hooks with an installer that backs up what it replaces and make installing them step 1 of onboarding. Critically, do **not** call client-side hooks a security control — they are fast feedback, and `--no-verify` bypasses them. The binding gate is server-side: collaborators get Read access and work from forks (no push permission at all), with CI as the visible merge gate.

- **Staff:** "You inherit a repo where database dumps were committed while it was public. Walk me through your decision." — Contain, then decide. Rotate every credential in those files immediately, independent of git. Audit real exposure rather than panicking: here the dumps held an empty `socialaccount_socialapp` (no OAuth secret), no plaintext passwords, two `pbkdf2_sha256$1000000$…` hashes and two expired sessions — *mild*. Fix the root cause: the ignore rule existed but was scoped to one subtree of a monorepo, so the fix was root-level `*.sql`/`*.dump` rules, verified at five locations. Untrack with `git rm --cached` (2,954 files, disk byte-identical). Only then weigh a rewrite: with 0 forks and the repo going private, a force-push straight after a merge was more risk than the exposure, so history was left alone **and the decision was written into the commit message**. That is the staff move: an explicit recorded decision beats a heroic irreversible one.

### Why interviewers ask these — and the answer that separates levels

| Testing for | Weak answer | What lands |
|---|---|---|
| Do you know `.git` from the working tree? | "git init starts git in the folder." | Name what appears (`HEAD`, `objects/`, `refs/`, `hooks/`), and that deleting `.git` destroys history while leaving files — history has no undo. |
| Do you understand commit immutability? | "I'll change the author later." | Author lives inside the commit object, so changing it changes the hash and everything after; `--amend` for the tip, filter-repo for older, prevention via config scope. |
| Do you know where enforcement really lives? | "Our pre-commit hook prevents that." | Hooks are client-side, uncloned and `--no-verify`-able; real gates are server-side (fork/Read access, CI). Name which layer catches which failure. |

**The killer follow-up:** *"Your `.gitignore` says `db_backups/` — is that repo safe from committed dumps?"* — Only inside that file's own subtree. In a monorepo the honest answer is "not necessarily; type-level rules belong at the repository root, and I'd verify with `git check-ignore -v` from several directories." That sentence is the bug this project actually shipped.

# Revision Notes
- Repository = **working tree** (your files) + **`.git`** (the database). Deleting `.git` kills history only, permanently.
- `git init` writes `HEAD`, `config`, `description`, `hooks/`, `info/`, `objects/`, `refs/` — no network, no file changes.
- `HEAD` is one line: `ref: refs/heads/<branch>`.
- Identity scopes: repo `.git/config` beats `~/.gitconfig` beats system. The author is baked into the commit — **configure first**.
- `git status --short`: left column = index vs commit, right column = working tree vs index.
- `git restore <f>` destroys edits; `git restore --staged <f>` only unstages; `git rm --cached` untracks but keeps the file.
- `.git/hooks/` is **never cloned** → `bash git-hooks/install.sh` per machine, per clone.
- A `.gitignore` guards **only its own subtree** — the monorepo lesson that cost this repo two public dumps.

# Cheat Sheet
- `git init` — create `.git` here · `git init -b main` — and name the branch (git ≥ 2.28)
- `git config --global init.defaultBranch main` — stop the `master` hint forever
- `git config user.email "you@x.com"` — this repo only; add `--global` for all repos
- `git rev-parse --show-toplevel` — where is this repo's root · `cat .git/HEAD` — which branch
- `git status --short` — `??` untracked · ` M` unstaged · `M ` staged · `AM` both
- `git add <path>` — stage · `git add -p` — stage hunk by hunk
- `git commit --amend --reset-author` — fix the last commit's message, content or identity
- `git restore --staged <f>` — unstage, keep edit · `git restore <f>` — **discard edit, no undo**
- `git rm --cached <f>` — untrack, keep on disk · `git check-ignore -v <f>` — which rule ignored it
- `git cat-file -p HEAD` — read your commit back out of the database
- `bash git-hooks/install.sh` — install this project's hooks (first command after any clone)
- ⚠️ `rm -rf .git` — deletes all history, no reflog, no recovery. Check `pwd` twice.

# My ERP Section
| Concept | In this repo (real facts) |
|---|---|
| Git root | `/home/tech/umesh-personal` — a monorepo; the ERP is `django_inventory/` |
| Root commit | `43f4e3b93c6aafdb032c7044d43531e98de5079c`, 2025-06-12 21:11 +0530, `Initial commit`, **no parent line** |
| Its author | `Umesh <umesh.chaudhary@thesqua.re>` — the **office** email, permanently, in the personal repo |
| Identity now | global = office; this tree overridden via `.git/config` **and** `includeIf "gitdir:/home/tech/umesh-personal/"` |
| Root `README.md` | blob `05fdcb8d`, 2,259 bytes — literally the `git init` → `push -u origin main` notes |
| Current tip | `42a2ecc4` on `new_flask_app`; 324 commits; 2,407 tracked files; `.git` = **97 MB** |
| The untrack commit | `42a2ecc4` — `git rm --cached` on **2,954** files, 331,748 deletions, disk byte-identical |

# Practice Tasks
1. **Read the code:** open the root `README.md` and map each command to a section of this chapter. Which step did the owner do *out of order*, and what did it cost?
2. **Do it:** create `~/git-practice`, set identity locally, make one commit, run `git cat-file -p HEAD`. Point at the author line and the missing `parent` line.
3. **Break and fix:** commit with a deliberately wrong `user.email`, verify with `git log --format='%an <%ae>'`, repair with `git commit --amend --reset-author`.
4. **Undo drill:** stage a file, add another line, then (a) unstage keeping both lines, (b) discard the unstaged line, (c) untrack but keep on disk. Name each command before running it.
5. **Debug:** run `git check-ignore -v django_inventory/db_backups/x.sql`, then the same from `DSA/`, and explain the difference in one sentence.

# Homework
- Read `~/.gitconfig` and predict which identity a repo in `/tmp` uses versus one under `/home/tech/umesh-personal/`. Prove it with `git config --get user.email` in each.
- Run `ls -A .git` here and in your practice repo. List every file the real repo has that the fresh one lacks, and say what created each.
- Read `CONTRIBUTING.md` §2 and §9 — which single onboarding step, if skipped, silently removes a protection layer, and what server-side thing still holds?

---

# Further Reading & Live Resources
- Pro Git, *Getting a Git Repository* (free, canonical): https://git-scm.com/book/en/v2/Git-Basics-Getting-a-Git-Repository
- `git init` reference — what each created file is for: https://git-scm.com/docs/git-init
- `git config` — scopes and `includeIf` conditional includes: https://git-scm.com/docs/git-config#_conditional_includes
- `git status` short-format decoder ring: https://git-scm.com/docs/git-status#_short_format
- Pro Git, *Git Hooks* — why they are local and what each fires on: https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks
