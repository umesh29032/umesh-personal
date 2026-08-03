---
id: git-course-01-what-version-control-is
type: lesson
status: active
owner: handwritten
scope: git, version control — what a VCS is, what "distributed" buys, and why git is not GitHub
anchors: CONTRIBUTING.md, .gitignore, django_inventory/CLAUDE.md
verified: 2026-08-03
---

# 01 — What Version Control Is (a searchable database of every past state of your project)

> Part of [Git Course](00_COURSE_OVERVIEW.md). Prev: [00 — Course Overview](00_COURSE_OVERVIEW.md). Next: [02 — Installing & Configuring Git](02_Install_And_Configure.md).

# Learning Objectives
By the end of this chapter you can:
- define **version control**, **repository**, **commit** and **history** without hedging
- explain why folder copies fail at exactly the moment you need them
- say what **distributed** means, using this repo's 97 MB `.git` as proof
- state the difference between **git** and **GitHub** in one sentence
- answer "what changed, who, when, and *why*" about a file you have never seen
- say what version control is **not** — not a backup, not a data store, not a deploy tool

# Purpose
Before any command, the idea. Version control is not a tool for *saving* files — your editor saves
files. It keeps every past state of a project **retrievable, attributable and explainable**, so "it
worked yesterday" becomes a question with an answer instead of a feeling. Branches, rebase, reflog
and pull requests are all consequences of that one idea.

# The Problem
Here is how most self-taught developers work. Not stupid — fragile:

```
~/projects/
    inventory/            inventory_final/
    inventory_backup/     inventory_final_WORKING_dont_delete/
    inventory_backup_2/   inventory_final_v2.zip
```

From that listing alone: (1) Which one is deployed? (2) A worker's wage came out wrong last Tuesday —
which folder was live then? (3) `settlement_service.py` rounds to 2 decimals; who added that, and
**why**? (4) You want one file from `inventory_final` and everything else from `inventory` — how?
(5) A second developer joins today — how do you both edit one file?

You cannot answer one. A folder copy records **the bytes and nothing else** — no author, no time, no
reason, no link between copies. This repo has **324 commits**; in the folder-copy world that is 324
folders you had to name, none carrying a reason. Version control exists because *the bytes* are the
least valuable part of a project's history.

# Theory (from zero)

### Definition, precisely
A **VCS** (Version Control System) records the state of a set of files over time with **who** changed
them, **when**, and **why** — and lets you move between any two of those states on demand.

| Word | What it actually is |
|---|---|
| **Repository** ("repo") | A folder containing a `.git/` directory. That hidden directory *is* the database — history lives on your disk, beside your code. |
| **Working tree** | The ordinary files you edit; what your editor and Django see. |
| **Commit** | One snapshot of the whole project **plus** metadata: author, timestamp, message, and a pointer to the commit before it. |
| **History** | The chain of commits — complete snapshots that git *presents* to you as diffs. |

A commit is the atom of this course. Not "a save" — **a fact about the project at a moment, with a
reason attached**.

### Git stores snapshots, but shows you diffs
Ask git what a commit did and it prints added/removed lines, so people conclude git stores diffs. It
does not. Each commit points at a complete snapshot of every tracked file, and git **computes** the
diff against the parent ([Ch 05](05_How_Git_Stores_Everything.md) shows the objects — identical files
are stored once and shared, which is why 324 snapshots of 2,407 files fit in 97 MB). Therefore **no
commit depends on replaying earlier ones**: any commit is checkoutable directly.

### Centralised vs distributed
**CVS** and **Subversion** are **centralised**: the server holds history, your machine holds only
current files, so a server outage means no history and no branches. Git is **distributed** —
`git clone` copies **the entire history**, so your laptop is not a checkout of a repository, it *is* a
repository. That buys: everything except sharing is **offline and instant**; **branching is cheap**,
because a branch is a small file naming one commit ([Ch 09](09_What_A_Branch_Really_Is.md)); and there
is **no single point of failure**. The cost: every clone holds every historical version of every file,
so a committed 50 MB binary — or a `node_modules/` — is permanent weight for everyone
([Ch 37](37_Large_Files_And_Performance.md)).

### Name the confusing bit: git ≠ GitHub
**git** is a program on your computer (**2.34.1** here), written by Linus Torvalds in 2005 for Linux
kernel work: free, offline, no account. **GitHub** is a company hosting a *copy* of your repo, adding
what git lacks — Pull Requests, Issues, review UI, Actions (CI), Releases, permissions. You can use
git for a lifetime with no GitHub account; you cannot use GitHub without git. Here the whole link is
one config line, `origin  git@github-personal:umesh29032/umesh-personal.git` — a **remote**, a
nickname for a repository elsewhere ([Ch 18](18_Remotes.md)).

### What version control is NOT
**Not a backup** — a backup survives a dead disk, git survives bad *decisions*; one `git push` is one
copy on one company's servers ([deployment Ch 28](../deployment_course/28_Backups.md)). **Not a data
store** — git is for code and text **you author**; dumps, `.env`, media and `node_modules/` stay out.
**Not a deploy tool** — a commit on `main` deploys nothing by itself.

> 💡 **Samjho aise:** Folder copy karna = almari mein bees baar wahi kapde thoos dena. Dikhte sab
> same, aur poochho "ye kab ka hai, kisne rakha, kyun rakha?" — koi jawab nahi. Git ek **almari +
> register** hai: jo bhi rakha, uski **tareekh**, **kisne rakha** aur **kyun rakha** register mein
> likha hai, aur kisi bhi din ki almari dobara khol sakte ho. Asli keemat kapdon ki nahi, **register**
> ki hai — aur har aadmi ke paas poore register ki nakal hai (distributed).

# Real World Example (this repo) — reading a history you did not write
All read-only, run in `/home/tech/umesh-personal`.

```bash
git rev-list --count HEAD    # commits reachable from where I stand →  324
git ls-files | wc -l         # files git currently tracks           →  2407
git shortlog -sn --all       # commits per author, all branches
   310	umesh-personal
    11	umesh29032
     5	Umesh chaudhary
     1	Umesh
```
Four author identities — for **one human**. Not four people: an unconfigured laptop, which is the
subject of [Ch 02](02_Install_And_Configure.md).

```bash
git log --reverse --format='%h %ad %s' --date=short | head -3
43f4e3b9 2025-06-12 Initial commit
c3b88c1c 2025-06-12 commit 2
fe3dd7de 2025-06-12 commit 3
```
Read `commit 2` honestly: the snapshot survived, the **reason** is gone forever. Today's newest is
`42a2ecc4 chore(repo): stop tracking database dumps + node_modules`, and **246 of 324** commits now
parse as [Conventional Commits](25_Conventional_Commits.md) because `git-hooks/commit-msg` refuses
anything else. That distance is this course's whole argument.

```bash
git log --oneline -S'localdate' | wc -l   # commits where that string's count changed →  3
```
`-S` is the **pickaxe**: it walks all history for commits where the *number of occurrences* of a
string changed. Three commits touched `localdate` — which is how the UTC-vs-IST money bug stays
traceable years later.

# Visual Diagram
```
FOLDER COPY records: bytes only.  COMMIT records: bytes + author + time + message + parent link.

DISTRIBUTED: every clone is a whole repository, not a checkout
              ┌──────────────────────────────────┐
              │ GitHub: umesh29032/umesh-personal│
              └──────────────────────────────────┘
                  ▲ push        │ fetch / clone
   ┌──────────────────────────┐ │ ┌──────────────────────────┐
   │ THIS laptop              │ └▶│ a collaborator's fork    │
   │ .git = 97 MB, 324 commits│   │ .git = full history too  │
   │ works with WiFi OFF      │   │ works with WiFi OFF      │
   └──────────────────────────┘   └──────────────────────────┘
   No machine is "the real one" — they are peers that agree to sync.
```

# Practical — interrogate this repository without changing a byte
```bash
cd /home/tech/umesh-personal
git log --oneline -5                            # 5 newest commits
git show 42a2ecc4 --stat | tail -1              # what ONE commit did, by hash
 2956 files changed, 81 insertions(+), 331748 deletions(-)
git log --oneline -- django_inventory/config/expense/   # history of one folder
git log -p -1 -- django_inventory/CLAUDE.md     # newest change to a file, as a diff
git log --grep='settlement' --oneline | head    # search commit MESSAGES
git log -S'ENFORCE_ALLOCATION_BOUND' --oneline  # search commit CONTENT
```
None of those write. `log`, `show`, `diff`, `status` and `blame` are safe to fire blindly; the
commands that can hurt you are named in [Ch 15](15_Undo_Reset_Revert_Restore.md), and every one gets
an undo in this course.

# Production Walkthrough
One real change through this repository — the pipeline named once, so the next 39 chapters have
somewhere to attach:

1. **Branch** — work on `new_flask_app`, never `main`: `main` must stay deployable because the deploy
   runbook reads it (`CONTRIBUTING.md` §1).
2. **Commit with a parsable reason** — `7fe2bb0e feat: accountant read tier, student role, …`; the
   `commit-msg` hook rejects anything else ([Ch 25](25_Conventional_Commits.md)).
3. **Push the branch, not `main`** — `git-hooks/pre-push` blocks `git push origin main` here and
   prints the branch-plus-PR recipe instead ([Ch 27](27_Pre_Push_Protection.md)).
4. **PR → CI → merge** — **PR #15**, `new_flask_app` → `main`, four jobs in
   `.github/workflows/ci.yml`, merged at `83a144ba` in GitHub's web UI (hence its author is
   `Umesh chaudhary <44035504+umesh29032@users.noreply.github.com>`, its committer `GitHub`).
5. **Release** — annotated tag `erp-v1.0.0` → `90c1f2f3` ([Ch 29](29_Semantic_Versioning_And_Tags.md)).
6. **Follow-up as a decision record** — `42a2ecc4` untracked 2,954 files of committed data and wrote
   the reasoning into the body, including *why history was deliberately not rewritten*.

# Debugging Guide
| Symptom | Cause | Fix |
|---|---|---|
| `fatal: not a git repository` | Outside a repo — the root here is `/home/tech/umesh-personal`, **not** `django_inventory/` | `git rev-parse --show-toplevel`, then `cd` there |
| Almost no history after cloning | Cloned shallow (`--depth 1`) | `git fetch --unshallow` |
| One human, 4 names in `shortlog` | Identity never configured on this machine | [Ch 02](02_Install_And_Configure.md) — `includeIf`, once |
| "I deleted a file and lost my work" | If ever committed, it still exists | `git log --diff-filter=D -- <path>`, then `git restore --source=<hash>^ -- <path>` |
| "I lost work never committed" | Uncommitted work is **not in git at all** | Nothing recovers it — [Ch 16](16_Reflog.md) saves commits, not edits |

# Performance Notes
- **2,407 tracked files, 324 commits, `.git` = 97 MB** (`count-objects -vH`: 4,873 loose, 25,975
  packed, `size-pack: 63.66 MiB`) — objects are zlib-compressed, deduplicated by content hash, then
  delta-packed against each other.
- **`git log` is O(commits walked)**, not O(repo size); the **pickaxe `-S` is the expensive one**
  because it diffs every commit touching the path, so narrow it with `-- <folder>`.
- **What really makes a repo slow:** large binaries (no useful delta) and huge untracked directories
  that `git status` must scan — this repo carried **2,952 tracked `node_modules` files** until
  `42a2ecc4`. Both are permanent once committed ([Ch 07](07_Gitignore.md)).

# Security Considerations
- **History is append-only. Deleting a file in a later commit does not remove it** — it stays fully
  readable in every earlier commit. The most expensive thing beginners do not know.
- **It already happened here.** Two `pg_dump` files were tracked while this repo was **public**:
  `Django_app/myproject/mydb_backup_20250618.sql` and `..._20250620.sql`. A dump is plaintext SQL, so
  committing one publishes every row.
- **Audit before panicking.** What was inside: `socialaccount_socialapp` and `socialaccount_socialtoken`
  both **empty**, **no** plaintext passwords, **2** hashes at `pbkdf2_sha256$1000000$…` (1,000,000
  iterations — impractical to crack), the primary account row `!OUUm8Nk…` = Django's
  **unusable-password** marker, **2** expired June-2025 sessions. **Verdict: mild** — mechanism real.
- **Root cause:** `django_inventory/.gitignore:114` already ignored `db_backups/`, which is why the
  live ERP never leaked a dump — but **a `.gitignore` only guards its own subtree**, and this is a
  monorepo, so `Django_app/` sat outside it. The rule was right; its **scope** was wrong.
- **Prevention beats surgery:** a `*.sql` line in the **root** `.gitignore` costs nothing; removing a
  secret costs `git-filter-repo` + force-push + every collaborator re-cloning
  ([Ch 33](33_Secrets_And_Leaks.md)). Note also that every commit publishes your email address.

# Architecture Decisions
- **One monorepo, not one repo per project** — `/home/tech/umesh-personal` holds `django_inventory/`
  (the ERP), `Django_app/`, `DSA/`, and a gitignored `sw obsidian/`. *Why:* one clone, one history,
  docs that cannot drift apart. *Rejected:* separate repos — better isolation, but three remotes and
  three sets of hooks for a one-person team. *The bill:* a subtree `.gitignore` was silently
  insufficient, so the **root** one now blocks `*.sql`, `*.dump`, `*.sql.gz`, `db_backups/`,
  `backups/`, `node_modules/` at 5 verified locations — `git add -f` still works, deliberately.
- **Trunk-based: `main` + short-lived branches + tags.** *Rejected:* `git-flow` with permanent
  `develop` and `release/*` branches — heavier than a 1–2 person team can justify
  (`CONTRIBUTING.md` §10, [Ch 24](24_Branching_Strategies.md)).
- **History deliberately NOT rewritten** after the dump discovery: 0 forks, 0 stars, repo going
  private, nothing usable inside — a `filter-repo` force-push right after a merge was judged **more**
  risk than the exposure, and that reasoning lives in the commit message.
- **Enforced by committed files, not memory:** `CONTRIBUTING.md`, `git-hooks/*`,
  `.github/workflows/ci.yml`, `.github/CODEOWNERS`.

# Best Practices
- Commit **small and often** — uncommitted work is the only work git cannot save.
- Write the **why** in the body; the diff already shows the what.
- **Never commit data or secrets.** `.gitignore` them at the **root** on day one.
- Configure identity **before** your first commit on a machine ([Ch 02](02_Install_And_Configure.md)).
- Treat `main` as always-deployable; reach it through a branch and a PR, never a direct push.
- Learn `git log` properly before anything clever — reading history is 80 % of the value.

# Beginner Mistakes
- **Keeping `project_final2/` "just in case" beside a git repo** → two truths, and one day you edit
  the wrong one. Delete the copies; branches and tags exist for this.
- **Writing `commit 2` / `wip` / `update`** → snapshot survives, reason gone forever. This repo has
  **2** commits literally named `commit N` ([Ch 25](25_Conventional_Commits.md)).
- **Believing "git deleted my file"** → git deletes nothing that was committed;
  `git log --diff-filter=D -- <path>` finds the deleting commit, restore from its parent.
- **Believing work is safe before it is committed** → uncommitted edits live only on disk; `reflog`
  recovers commits, never unsaved work ([Ch 16](16_Reflog.md)).
- **Committing a secret then deleting it next commit** → append-only history keeps it readable.
  Rotate the credential first ([Ch 33](33_Secrets_And_Leaks.md)).
- **Treating `git push` as a backup** → one copy, one provider, excluding your `.env` and database.
- **Confusing git with GitHub** → then every network error looks like a git bug.

# Interview Questions
- **Junior:** "What is version control and why not just copy folders?" — A VCS records every state of
  a project with who changed it, when and why, and lets you move between those states. Folder copies
  keep the bytes but lose author, time, reason and the link between versions, so they cannot answer
  "who wrote this line and why", cannot merge two people's work, and cannot be searched.

- **Mid:** "What does *distributed* mean, and what does it buy you day to day?" — Every clone has the
  complete history, so it is a fully valid repository on its own: `log`, `diff`, `blame` and `commit`
  are local and instant, branching is cheap because a branch is a pointer, and there is no single
  point of failure. The price is that every clone carries every historical version of every file,
  which is why committed large binaries are permanent for everyone.

- **Senior:** "Git stores snapshots, not diffs — so why does everything show me a diff, and why does
  the distinction matter?" — Each commit points at a complete tree, identical content is stored once
  and addressed by its content hash, and diffs are *computed* against the parent on demand. It matters
  because no commit depends on replaying earlier ones: any commit is checkoutable directly, merge and
  rebase reason about *states* rather than a patch stack, and deduplication is what makes 324 full
  snapshots of a 2,407-file project fit in 97 MB.

- **Staff:** "A database dump is found in public git history. Walk me through your response and what
  you change structurally." — Audit before acting: what is inside, are any credentials live, how strong
  are the hashes, how many forks exist. Rotate any live secret immediately and unconditionally. Only
  then decide about rewriting history, because `filter-repo` plus a force-push invalidates every clone
  and every open PR, and with 0 forks that is often more risk than the exposure. Structurally: the
  `.gitignore` belongs at the *monorepo root*, because a subtree ignore file cannot guard siblings; add
  secret scanning to CI; record the decision in the commit message so the next engineer inherits
  reasoning, not a mystery. Append-only history means the only reliable control is what you refuse to
  commit at all.

### Why interviewers ask these — and the answer that separates levels

| Testing for | Weak answer | What lands |
|---|---|---|
| History as *data*, or just a save button? | "Git saves my code so I don't lose it." | Name what a commit records — author, time, message, parent — then a question only history answers, like a pickaxe search for the commit that introduced a line. |
| Why *distributed* changes your workflow | "You push to GitHub so others can see it." | Every clone is a complete repository, so commit, branch, log and blame are offline and instant; the trade-off is that all historical bytes travel with every clone forever. |
| Do you know history is append-only? | "I deleted the file and committed, so it's gone." | A later delete leaves it readable in every earlier commit. Rotate the secret first, then choose between filter-repo plus force-push and accepting the exposure. |

**The killer follow-up:** *"Show me a commit whose message you would be embarrassed by, and tell me
what was lost."* — Anyone who has read their own history points at one instantly (here: `commit 2`,
`commit 3`) and names what is unrecoverable: **the reason**. Memorisers describe git in the abstract;
users have read their own log.

# Revision Notes
- **VCS = bytes + who + when + why + parent link.** Folder copies keep only the bytes.
- **Commit = a full snapshot with a reason.** Snapshots stored; diffs computed.
- **Distributed = every clone is a whole repo** → offline and instant; cost = all historical bytes
  travel with every clone.
- **git ≠ GitHub.** Git owns commits and branches locally; GitHub hosts a copy, adds PR/review/CI.
- ⚠️ **History is append-only** — a later delete removes nothing. Prevent with a root `.gitignore`.
- ⚠️ **Uncommitted work is not in git.** `reflog` rescues commits, never unsaved edits.
- This repo: **324 commits · 2,407 files · `.git` 97 MB · `erp-v1.0.0` = `90c1f2f3` · PR #15 = `83a144ba`.**

# Cheat Sheet
```bash
git rev-parse --show-toplevel        # repo root (here: /home/tech/umesh-personal)
git rev-list --count HEAD            # how many commits reachable from HEAD
git ls-files | wc -l                 # how many files are tracked
git shortlog -sn --all               # commits per author
git log --oneline -10                # compact recent history
git log --graph --oneline --all      # the SHAPE of history (Ch 06)
git log -p -1 -- <path>              # newest change to a file, as a diff
git log --grep='settlement'          # search commit MESSAGES
git log -S'localdate'                # search commit CONTENT (pickaxe)
git log --diff-filter=D -- <path>    # which commit DELETED this file
git show <hash> --stat               # what one commit did
git count-objects -vH                # repo size, loose vs packed
```
- **Safe to run blind:** `log`, `show`, `diff`, `status`, `blame`, `ls-files`, `count-objects`.
- **Find the root first:** this monorepo's git root is one level **above** `django_inventory/`.

# My ERP Section
| Concept | In this repo, concretely |
|---|---|
| Repository | `/home/tech/umesh-personal` — a monorepo; the ERP is `django_inventory/` |
| History size | **324** commits, **2,407** tracked files, `.git` = **97 MB** |
| Remote | `origin` = `git@github-personal:umesh29032/umesh-personal.git` |
| Branches | default `main`; work happened on `new_flask_app`; **PR #15** merged at **`83a144ba`** |
| Release | annotated tag **`erp-v1.0.0`** = **`90c1f2f3`** |
| Message quality | **246 / 324** parse as Conventional Commits; **2** are literally `commit N` |
| The rulebook | `CONTRIBUTING.md` at the repo root — the law; this course is the *why* |
| The incident | `42a2ecc4` untracked **2,954** files (2 dumps + 2,952 `node_modules`), −331,748 lines |
| Quality gate | battery **2033 tests, 14 apps, ~424 s**, sequential on a fresh DB — CI runs it per PR |

# Practice Tasks
1. From `django_inventory/config/`, run `git rev-parse --show-toplevel` and say in one sentence why
   the answer is not the folder you are standing in.
2. `git log --reverse --oneline | head -10` — pick the worst message and write down what information
   was permanently lost.
3. Pick a line in `django_inventory/config/expense/services/adda_settlement_service.py`, find its
   commit with `git log -S'<distinctive string>' --oneline`, then read `git show <hash> --quiet`.
4. With WiFi off run `git log`, `git show HEAD`, `git status`, then `git fetch`. Which failed, and
   what does that prove about where history lives?

# Homework
1. Read `CONTRIBUTING.md` §0 and §1, then write in your own words the four things a Pull Request buys
   that a direct push cannot.
2. Read `git show --quiet 42a2ecc4` — a deliberate decision record. List the three decisions in it.
3. Open-ended: had this repo used version control properly from commit 1, which of the five questions
   in *The Problem* would have been answerable on day one — and which still would not?

---

# Further Reading & Live Resources
- *Pro Git*, Ch 1 "About Version Control" (free, canonical): https://git-scm.com/book/en/v2/Getting-Started-About-Version-Control
- *Pro Git*, Ch 1.3 "What is Git?" — snapshots vs deltas, the part most tutorials skip: https://git-scm.com/book/en/v2/Getting-Started-What-is-Git%3F
- GitHub Docs — *About Git* (where git ends and GitHub begins): https://docs.github.com/en/get-started/using-git/about-git
- `git log` reference — the pickaxe (`-S`), `--grep`, `--diff-filter`: https://git-scm.com/docs/git-log
