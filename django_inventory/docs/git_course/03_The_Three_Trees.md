---
id: git-course-03-the-three-trees
type: lesson
status: active
owner: handwritten
scope: git, core model — working directory, index/staging area, HEAD, and the commands that move files between them
anchors: .git/index, .git/HEAD, .gitignore
verified: 2026-08-03
---

# 03 — The Three Trees (the model that explains every git command)

> Part of [Git Course](00_COURSE_OVERVIEW.md). Prev: [02 — Installing & Configuring Git](02_Install_And_Configure.md). Next: [04 — Your First Repository](04_Your_First_Repository.md).

# Learning Objectives
By the end of this chapter you can:
- name the three trees and say what each one physically is
- predict what `git status` will say before you run it
- explain `git add` and `git commit` as *movements between trees*, not as magic verbs
- read `git diff`, `git diff --staged` and `git diff HEAD` and say which pair of trees each compares
- explain why the staging area exists at all, instead of dismissing it as an annoyance
- unstage, discard and inspect without guessing which command is destructive

# Purpose
Most people learn git as four memorised incantations: `add`, `commit`, `push`, `pull`. It works
until something unexpected happens, and then there is no model to reason with — only a
half-remembered Stack Overflow answer.

This chapter installs the model. Git has **three trees**, and almost every command you will
ever run is "copy state from one tree to another". Once you can name the three, commands stop
being vocabulary and start being consequences. `git reset --hard` stops being scary-and-mysterious
and becomes precisely "move all three trees to this commit" — dangerous for an understandable
reason, not a superstitious one.

This is the highest-leverage chapter in Part 1. Everything from [merging](11_Merging.md) to
[reset vs revert vs restore](15_Undo_Reset_Revert_Restore.md) is downstream of it.

# The Problem
You edit three files. You only want to commit one of them, because the other two are
half-finished debugging. In a system that just snapshots your folder, you cannot — it is all or
nothing, so you either commit junk or you stop working to clean up.

Worse, without a model you cannot answer basic questions:

- Why does `git diff` show nothing after I `git add`? *(Did my change vanish?)*
- Why does `git commit` sometimes commit less than I changed?
- What is the actual difference between `git reset`, `git restore` and `git checkout`?

Every one of those is the same missing idea: **there is a third place between your files and
your history**, and commands act on specific pairs of places.

# Theory (from zero)

### The three trees, physically
"Tree" is git's word for "a directory listing with a snapshot of contents". There are three
that matter, and each is a real thing on disk:

| # | Name | Also called | What it physically is |
|---|---|---|---|
| 1 | **Working directory** | working tree, worktree | The actual files you edit. Ordinary files in your folder. |
| 2 | **Index** | **staging area**, cache | **One binary file: `.git/index`.** A list of paths, their blob hashes and metadata. |
| 3 | **HEAD** | the current commit | A pointer. `.git/HEAD` holds a ref like `ref: refs/heads/main`, which holds a commit hash. |

Note how small two of them are. The index is a single file. HEAD is a text file containing one
line. Nothing mystical.

```bash
cat .git/HEAD
# ref: refs/heads/new_flask_app

wc -c < .git/index
# 246513          ← one binary file listing every tracked path
```

### The flow, and the commands that move between trees
```
  working directory  ──git add──►  index  ──git commit──►  HEAD (new commit)
         ▲                          ▲                          │
         │                          │                          │
         └───git restore <f>────────┘                          │
         └───────────────git restore --source=HEAD <f>─────────┘
                                    └──git reset <f>───────────┘
```

Read it as a pipeline:

- **`git add <file>`** — copy the file's current content from the working directory into the
  index. Nothing is committed. Nothing is permanent yet.
- **`git commit`** — take a snapshot **of the index** (never of your working directory) and
  record it as a new commit; move HEAD to it.
- **`git reset <file>`** — copy from HEAD back into the index. Unstages. Your file is untouched.
- **`git restore <file>`** — copy from the index back into the working directory. **Destroys**
  your uncommitted edit to that file.

The crucial sentence, worth memorising: **`git commit` commits the index, not your files.**
That single fact explains "why did git commit less than I changed?" — because you only `add`ed
some of it.

### `git status` is just a two-way diff report
`git status` compares the trees in pairs and labels the results:

```
Changes to be committed:      ← index differs from HEAD      (staged)
Changes not staged for commit: ← working dir differs from index (unstaged)
Untracked files:               ← in working dir, in NO tree at all
```

Three sections, because there are three trees and thus two gaps between them. Once you see
that, `git status` output becomes predictable rather than something to squint at.

### The three diffs — this is where most confusion lives
```bash
git diff             # working directory  vs  index      ("what have I not staged?")
git diff --staged    # index              vs  HEAD       ("what am I about to commit?")
git diff HEAD        # working directory  vs  HEAD       ("everything, staged or not")
```

So the classic panic — *"I ran `git add`, now `git diff` shows nothing, did I lose my work?"* —
resolves instantly. `git diff` compares working directory to index. You just made them
identical. Use `git diff --staged` to see the change you staged. Nothing was lost.

### Why the index exists (the part usually skipped)
Beginners meet the index as an obstacle: why two steps when one would do? Because the index
buys you three things that matter in real work:

1. **Committing less than you changed.** Three files edited, one coherent change among them?
   Stage that one. Commits stay atomic, so any of them can be reverted alone.
2. **Committing *part of a file*.** `git add -p` walks the change hunk by hunk. A bug fix and
   a stray debug print in the same file become two commits.
3. **Building a commit while still working.** Stage the good part now, keep experimenting; the
   staged version is safe from your next edit.

Atomic commits are not a style preference. They are what makes [`git revert`](15_Undo_Reset_Revert_Restore.md)
and [`git bisect`](35_Bisect.md) usable. A commit containing four unrelated things cannot be
reverted without collateral damage.

> 💡 **Samjho aise:** Teen jagah socho — **mez** (working directory) jahan tum kaam kar rahe
> ho, **thaila** (index/staging) jisme jo cheezein bhejni hain wo daalte ho, aur **register**
> (HEAD/history) jisme entry pakki ho jaati hai.
>
> `git add` = mez se thaile mein daalna. `git commit` = **thaile ka** register mein entry —
> mez ka nahi! Isliye agar tumne thaile mein sirf ek cheez daali, register mein sirf wahi
> jaayegi, chahe mez pe daswaan saaman pada ho.
>
> Aur `git diff` khaali kyun dikhta hai add ke baad? Kyunki wo **mez vs thaila** compare karta
> hai — aur tumne dono barabar kar diye. Kaam gaya nahi; `git diff --staged` dekho.

# Real World Example (this repo)
Here is the model doing real work in this repository. On 2026-08-03 two database dumps and
2,952 dependency files had to stop being tracked — **without deleting them from disk**.

That is a pure three-trees operation, and `--cached` is the word that scopes it:

```bash
git rm --cached <paths>
```

`git rm` normally removes from **both** the index and the working directory. `--cached` says
*"remove from the index only"* — so git stops tracking the file while your folder keeps it.
Different tree, entirely different outcome.

The proof, taken at the time:

```
files on disk BEFORE : 44120 bytes  mydb_backup_20250620.sql   ·  node_modules: 27M
files on disk AFTER  : 44120 bytes  mydb_backup_20250620.sql   ·  node_modules: 27M
git status           : 2954 D                 ← 2,954 deletions staged in the INDEX
```

Byte-identical on disk, 2,954 deletions in the index. If you cannot separate the trees, that
result looks like a contradiction — "how is it deleted *and* still there?" With the model it is
obvious: only tree #2 changed.

And the audit command that made it safe to run at all is itself a pure index query:

```bash
git ls-files -i -c --exclude-standard    # tracked files that are ALSO ignored
```

`-c` means "cached" — *look in the index*. It answers "what is git tracking that it should not
be?", which is exactly the question before a cleanup. It returned 2,954 rows, all under
`Django_app/`, and **zero** under `django_inventory/` — so the live ERP was provably untouched
before a single change was made.

# Visual Diagram
```
 ┌─────────────────────┐   ┌──────────────────┐   ┌─────────────────────┐
 │  WORKING DIRECTORY  │   │      INDEX       │   │        HEAD         │
 │   your real files   │   │   .git/index     │   │  the current commit │
 │   (edit these)      │   │  (ONE file!)     │   │  .git/HEAD → ref    │
 └─────────────────────┘   └──────────────────┘   └─────────────────────┘
           │                        │                        │
           │──────  git add  ──────►│                        │
           │                        │─────  git commit  ─────►│
           │                        │                        │
           │◄──── git restore ──────│                        │
           │       (DESTRUCTIVE:    │◄──── git reset <f> ─────│
           │        loses your edit)│      (unstage; file OK) │
           │◄──────────── git reset --hard <commit> ──────────│
           │              (moves ALL THREE — destructive)     │

   git status  = the two gaps, labelled:
       staged      = INDEX  ≠ HEAD
       not staged  = WORKDIR ≠ INDEX
       untracked   = in WORKDIR, in no tree

   git diff            WORKDIR vs INDEX     "not staged yet"
   git diff --staged   INDEX   vs HEAD      "about to be committed"
   git diff HEAD       WORKDIR vs HEAD      "everything"
```

# Practical — watch the trees move
Run this whole block in a throwaway repo. The point is to *see* each tree change independently.

```bash
mkdir /tmp/trees && cd /tmp/trees && git init -q
git config user.email t@t && git config user.name t

echo "version 1" > a.txt
git status --short
# ?? a.txt                    ← untracked: in WORKDIR only

git add a.txt
git status --short
# A  a.txt                    ← the A is in COLUMN 1 = the index
git diff                      # (nothing — workdir and index now match)
git diff --staged             # +version 1   ← the staged change IS there

git commit -q -m "feat: add a"
git status --short            # (clean — all three trees agree)

# now make them all differ at once
echo "version 2" > a.txt      # workdir changed
git add a.txt                 # index now has v2
echo "version 3" > a.txt      # workdir changed AGAIN, index still v2

git status --short
# MM a.txt
#  ^^ TWO columns: col1 = index vs HEAD, col2 = workdir vs index
#     both differ — this is the three trees fully visible in two characters

git diff --staged | tail -2   # v1 → v2   (what commit would record)
git diff | tail -2            # v2 → v3   (what you'd lose if you restored)

git commit -q -m "feat: bump a"
git show --stat HEAD | tail -1
cat a.txt                     # version 3  ← still v3 on disk; git committed v2!
```

That last pair of lines is the whole chapter. **Git committed version 2 while your file says
version 3**, because commit takes the index. Nothing is broken; you just watched the model work.

# Production Walkthrough
How the three trees get used deliberately in this project's workflow:

1. **Work broadly, commit narrowly.** A session may touch a service, a template, a test and a
   doc. Stage them as separate coherent commits (`git add -p` when a single file holds two
   ideas) so each commit is revertable alone.
2. **Review your own staged diff before committing.** `git diff --staged` is the last gate
   before history. This is where a stray `print()`, a leftover `.only()` in a test, or a
   debugging change gets caught — cheaper than a reviewer catching it.
3. **The pre-commit hook operates on the index, not your folder.** This repo's ruff and
   design-system gates run against **staged** content. That is why they can pass while your
   working directory still has a violation you have not staged — correct behaviour, surprising
   the first time ([Chapter 26](26_Pre_Commit_Hooks.md)).
4. **Untracking is an index operation.** `git rm --cached` + a `.gitignore` rule is the
   standard "stop tracking, keep the file" move ([Chapter 07](07_Gitignore.md)).
5. **Audit the index, not the folder.** `git ls-files -i -c --exclude-standard` finds
   tracked-but-ignored files. Empty output means clean; anything else is a file that slipped
   past a rule.

# Debugging Guide

| Symptom | Cause | Fix |
|---|---|---|
| `git diff` empty after `git add` | it compares WORKDIR vs INDEX, which now match | `git diff --staged` |
| Commit contains less than you changed | commit snapshots the **index**; you staged part | `git add` the rest, or `git commit -a` for all *tracked* files |
| `git commit -a` missed a new file | `-a` covers tracked files only; new files are untracked | `git add <newfile>` explicitly |
| "I deleted the file but git still tracks it" | you removed it from WORKDIR only | `git rm <file>` (or `git add <file>` to stage the deletion) |
| "I untracked it and it vanished from disk" | you used `git rm` without `--cached` | `git restore <file>` if still in HEAD |
| `git status` shows `MM` | both gaps differ: index≠HEAD **and** workdir≠index | normal; `git add` again to sync the index to workdir |
| Ignored file still shows in `git status` | `.gitignore` does not apply to **already-tracked** files | `git rm --cached <file>` |
| Lost an uncommitted edit | `git restore` overwrote workdir from the index | unrecoverable if never staged — **the index is not a backup** |

That last row deserves emphasis: git can only recover what it has seen. An edit that was never
`add`ed and never committed exists in exactly one place, and `git restore` overwrites it.
`git stash` ([Chapter 17](17_Stash_And_Worktrees.md)) is the safe alternative when you want to
set work aside.

# Performance Notes
- The index exists **for speed**. It caches each file's size and mtime, so `git status` can
  skip reading files whose metadata is unchanged instead of hashing your whole tree.
- Which is why `git status` is fast: it stats files and compares metadata, only hashing when
  something looks changed. This repo tracks ~2,400 files and `git status` is effectively instant.
- The index file here is roughly 240 KB — a few hundred bytes per tracked path. It grows with
  file *count*, not file size.
- `git add .` on a huge tree is slow because it must hash every changed file into a blob. Stage
  paths you mean rather than reflexively adding everything.
- On very large repos (100k+ files) `core.fsmonitor true` lets git watch the filesystem instead
  of scanning it. Unnecessary at this repo's size.
- Deleting `.git/index` is survivable — `git reset` rebuilds it from HEAD. You lose staged
  state, not history.

# Security Considerations
- **`git add` is the moment a secret enters the repository.** Once staged and committed, the
  content is an object in `.git/objects` and history is append-only: deleting the file later
  does not remove it. [Chapter 33](33_Secrets_And_Leaks.md) covers the aftermath.
- **`git add .` is the most common way secrets get committed.** It sweeps `.env`, dumps and
  keys unless a rule blocks them. This repo's two committed database dumps arrived exactly this
  way ([Chapter 07](07_Gitignore.md)).
- **`git diff --staged` is a security review, not just a formatting check.** It is the last
  point at which a credential can be caught for free.
- **`--cached` vs no flag is a genuinely dangerous distinction.** `git rm` deletes from disk;
  `git rm --cached` does not. Read the flag before running it against something you cannot
  regenerate.
- **The index can hold content that is not in any commit.** Staged-but-uncommitted secrets sit
  in `.git/objects` already, so "I never committed it" is not the same as "it is not in the
  repo".

# Architecture Decisions
- **Git chose a three-tree model instead of two.** Mercurial and Subversion effectively commit
  your working directory. Git's extra tree costs a concept but buys atomic, partial, reviewable
  commits — and atomic commits are what make revert and bisect work.
- **The index is one binary file, not a directory of state.** One file means one atomic
  rename to update it and no partial-state recovery problem; it also means it is disposable
  and rebuildable from HEAD.
- **This project prefers explicit `git add <path>` over `git add .`.** Deliberate staging is
  what keeps commits atomic and is the practical defence against sweeping in data files.
- **Hooks operate on the index by design.** `.pre-commit-config.yaml` lints *staged* Python and
  templates, so the gate matches exactly what is about to become history — not whatever else
  happens to be open in your editor.
- **`git restore`/`git switch` are preferred over `git checkout`.** `checkout` overloads both
  jobs onto one command, and conflating "change branch" with "destroy my file edit" is a
  design flaw worth routing around.

# Best Practices
- Read `git status` before **and** after staging. It is a free model check.
- Always `git diff --staged` before `git commit`. Treat it as the review gate it is.
- Prefer `git add <path>` over `git add .`; use `git add -p` when one file holds two ideas.
- Learn the two-column `git status --short` output — it shows both gaps at a glance.
- Use `git restore` and `git switch`, not `git checkout`, so the destructive one is named.
- Before any `git rm`, decide consciously whether you mean `--cached`.
- Never treat the index as a backup. Use [`git stash`](17_Stash_And_Worktrees.md) for work you
  want to keep but not commit.

# Beginner Mistakes
- **Thinking `git commit` snapshots your folder** → then being baffled when it commits less
  than you changed. It snapshots the **index**.
- **Panicking when `git diff` goes empty after `add`** → nothing is lost; you are comparing the
  two trees you just made identical. Use `--staged`.
- **`git add .` reflexively** → sweeps in `.env`, dumps, `node_modules`. How this repo got two
  database dumps into public history.
- **`git rm` when you meant `git rm --cached`** → the file leaves your disk too.
- **`git restore <file>` to "undo staging"** → wrong direction: that overwrites your working
  file from the index and **destroys the edit**. Unstaging is `git reset <file>`.
- **Expecting `.gitignore` to hide an already-tracked file** → ignore rules only apply to
  untracked paths. Untrack it first ([Chapter 07](07_Gitignore.md)).
- **`git commit -a` and assuming everything went in** → `-a` stages tracked modifications only;
  brand-new files are silently excluded.

# Interview Questions
- **Junior:** "What is the staging area?" — A middle tree (`.git/index`) between your files and
  your history. `git add` copies content into it; `git commit` snapshots **it**, not your
  working directory. It exists so a commit can contain less than you changed.
- **Mid:** "You ran `git add`, and now `git diff` shows nothing. Explain." — `git diff` compares
  working directory to index, and `add` made them identical. The change is staged, not lost:
  `git diff --staged` shows index vs HEAD, and `git diff HEAD` shows everything.
- **Senior:** "Why does git have three trees when Subversion effectively has two?" — To make
  commits *composable*. Partial and hunk-level staging let one work session produce several
  atomic commits, and atomicity is a prerequisite for `revert` and `bisect` being usable. The
  index also doubles as a metadata cache, which is why `git status` is fast. The cost is one
  extra concept that beginners initially experience as friction.
- **Staff:** "Untrack a file across a team without deleting anyone's copy, and say what you
  cannot fix." — `git rm --cached` plus a `.gitignore` rule, committed together, so the file
  leaves the index while every working directory keeps it; teammates see a deletion on pull but
  their file survives because it is now ignored. What you cannot fix that way is **history**:
  the content stays in every prior commit, so if it was a secret, untracking is containment,
  not remediation — you rotate the credential, and only then decide whether a `filter-repo`
  rewrite and force-push is worth the disruption.

### Why interviewers ask these — and the answer that separates levels
| Testing for | Weak answer | What lands |
|---|---|---|
| Do you have a model or four memorised commands? | "Staging is where files go before commit." | Name it as `.git/index`, one file, and say commit snapshots the index — then predict `git status`'s three sections from the two gaps. |
| Can you debug from the model? | "The diff disappeared so I re-added it." | Identify *which pair of trees* each diff compares, and reach for `--staged` rather than re-running commands hopefully. |
| Do you know why the design is like this? | "Git just works that way." | Atomic commits are the payoff; revert and bisect depend on them. The index is also a stat cache, hence fast `status`. |

**The killer follow-up:** *"Is a staged-but-uncommitted secret safe because you never committed it?"* — No. `git add` already wrote the content into `.git/objects` as a blob. It is unreferenced rather than absent, and it survives until garbage collection. Treat `git add` — not `git commit` — as the moment a secret enters the repository.

# Revision Notes
- Three trees: **working directory** (your files) → **index** (`.git/index`, one file) → **HEAD** (current commit).
- **`git commit` commits the INDEX, not your folder.** The single most important sentence.
- `git add` = workdir → index. `git reset <f>` = HEAD → index (unstage). `git restore <f>` = index → workdir (**destroys your edit**).
- `git status` = the two gaps: staged (index≠HEAD), not staged (workdir≠index), untracked (nowhere).
- `git diff` = workdir vs index · `--staged` = index vs HEAD · `HEAD` = workdir vs HEAD.
- Empty `git diff` after `add` is **correct**, not data loss.
- `git rm --cached` = untrack, keep on disk. Proven here: 2,954 index deletions, 0 bytes lost.
- The index is a **stat cache** too — that is why `git status` is fast.
- `git add` is when a secret enters `.git/objects`. Not commit. **`add`.**

# Cheat Sheet
```bash
git status --short              # XY per file: X = index vs HEAD, Y = workdir vs index
git status                      # the same, in three labelled sections

git add <path>                  # WORKDIR ──► INDEX
git add -p <path>               # ...hunk by hunk (split one file into two commits)
git commit                      # INDEX ──► new commit; HEAD moves
git commit -a                   # stage tracked MODIFICATIONS only (misses new files!)

git diff                        # WORKDIR vs INDEX   — "not staged yet"
git diff --staged               # INDEX  vs HEAD     — "about to be committed"  ← review this
git diff HEAD                   # WORKDIR vs HEAD    — "everything"

git reset <path>                # unstage: HEAD ──► INDEX   (file on disk untouched)
git restore <path>              # DESTRUCTIVE: INDEX ──► WORKDIR (loses your edit)
git restore --source=HEAD <path>  # DESTRUCTIVE: HEAD ──► both

git rm <path>                   # remove from index AND disk
git rm --cached <path>          # remove from index ONLY — untrack, keep the file

git ls-files                    # what the INDEX tracks
git ls-files -i -c --exclude-standard   # tracked BUT ignored = files that slipped a rule
cat .git/HEAD                   # "ref: refs/heads/<branch>" — one line
```

# My ERP Section

| Where the three trees show up | In this project |
|---|---|
| Index file | `.git/index`, ~240 KB for ~2,400 tracked paths |
| HEAD | `.git/HEAD` → `ref: refs/heads/new_flask_app` → `42a2ecc4…` |
| Untrack-but-keep | `git rm --cached` removed **2,954** files (2 dumps + 2,952 `node_modules`) — 331,748 deletions, **0 bytes lost on disk** |
| Index audit | `git ls-files -i -c --exclude-standard` found all 2,954, and **0** under `django_inventory/` — proof the live ERP was untouched |
| Hooks act on the index | `.pre-commit-config.yaml` lints **staged** Python (ruff) and **staged** templates (design-system ratchet) |
| CI reproduces staging | `ci.yml` runs `git reset --soft $(git merge-base …)` so the whole PR appears *staged*, letting the pre-commit-era ratchet script run unmodified ([Chapter 28](28_CI_With_GitHub_Actions.md)) |

That last row is the three-trees model used as a *tool*: the linter only knows how to read the
index, so CI moves the PR into the index rather than rewriting the linter.

# Practice Tasks
1. Run the Practical block above. Stop at `MM a.txt` and say out loud what each `M` means.
2. Create a file, `git add` it, then **change it again** without re-adding. Commit. Confirm the
   committed content is the staged version, not the file on disk. This is the chapter in one
   experiment.
3. Stage two changes in one file with `git add -p`, choosing `y` for one hunk and `n` for the
   other. Then `git diff` and `git diff --staged` and confirm they show *different* hunks.
4. Track a file, add it to `.gitignore`, and confirm `git status` **still** shows changes to it.
   Then `git rm --cached` it and confirm it goes quiet. You have just reproduced this repo's
   real bug class.
5. Delete `.git/index`, run `git status` (it will look alarming), then `git reset` and confirm
   full recovery. The index is disposable; history is not.

# Homework
- Take your next real change and deliberately split it into three atomic commits using
  `git add -p`. Then `git revert` the middle one and confirm the other two survive intact.
  That is the payoff the index exists for.
- Write out, from memory, the three trees and the command that moves between each pair. Check
  it against the cheat sheet. Repeat tomorrow. This model is worth having cold.
- Run `git ls-files -i -c --exclude-standard` in every repo you own. Any output is a file that
  slipped past an ignore rule — exactly the audit that preceded this repo's cleanup.
- Read `git help reset` and map its `--soft`, `--mixed` and `--hard` modes onto the three trees:
  which trees does each one move? Then predict what `--hard` destroys before reading
  [Chapter 15](15_Undo_Reset_Revert_Restore.md).

# Further Reading & Live Resources
- [Pro Git — Reset Demystified](https://git-scm.com/book/en/v2/Git-Tools-Reset-Demystified) — the canonical three-trees explanation, by the people who named it
- [Pro Git — Recording Changes](https://git-scm.com/book/en/v2/Git-Basics-Recording-Changes-to-the-Repository) — status, add, diff, commit in sequence
- [Learn Git Branching](https://learngitbranching.js.org/) — interactive, in the browser, free; the fastest way to build intuition
- [git-add reference](https://git-scm.com/docs/git-add) — including `-p` interactive staging
- [Git index format](https://git-scm.com/docs/index-format) — what is actually inside `.git/index`, if you want to see it is not magic
- [Visualizing Git](https://git-school.github.io/visualizing-git/) — watch the trees and refs move as you type commands
