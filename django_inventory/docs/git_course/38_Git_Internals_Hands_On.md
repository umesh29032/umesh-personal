---
id: git-course-38-git-internals-hands-on
type: lesson
status: active
owner: handwritten
scope: git — plumbing commands, building a commit by hand, refs and the object database
anchors: .git/objects, .git/refs, .git/HEAD, .git/index
verified: 2026-08-03
---

# 38 — Git Internals, Hands-On (build a commit with your bare hands)

> Part of [Git Course](00_COURSE_OVERVIEW.md). Prev: [37 — Large Files & Repo Performance](37_Large_Files_And_Performance.md). Next: [39 — Disaster Playbook](39_Disaster_Playbook.md).

# Learning Objectives
By the end of this chapter you can:
- distinguish **porcelain** from **plumbing**, and name the plumbing commands that matter
- create a commit using only plumbing — no `git add`, no `git commit`
- explain what `.git/` contains, directory by directory
- compute a git object hash yourself and verify it matches
- read `.git/index`, `.git/HEAD` and `.git/refs/` as the plain data they are
- debug situations where porcelain gives up

# Purpose
Everything in this course has described git's model. This chapter makes you **build** it.

You are going to create a commit without `git add` or `git commit` — writing the blob, assembling the
tree, forging the commit object and moving the ref, by hand. It takes about five minutes and it changes
how git feels permanently. After this, "git is a content-addressed key-value store with four object
types" stops being a sentence you can recite and becomes something you have done.

The practical payoff is real too: when porcelain fails — a corrupt index, a detached state you cannot
reason about, a hook that must inspect the index — plumbing is what you reach for.

# The Problem
Porcelain commands hide the model, which is usually good and occasionally fatal:

- `git add` writes a blob *and* updates the index. Two operations, one verb.
- `git commit` writes a tree, writes a commit, and moves a ref. Three operations, one verb.
- `git checkout` changes branches, restores files, and creates branches. Three unrelated jobs.

So when something goes wrong, you cannot tell which step failed. And some tasks are only expressible in
plumbing at all: computing what a hash *would* be without storing it, reading the index directly, or
constructing a commit with a specific parent.

# Theory (from zero)

### Porcelain versus plumbing
Git's own terms:

- **Porcelain** — the human-facing commands. `add`, `commit`, `log`, `merge`, `status`. Output is meant
  for people and may change between versions.
- **Plumbing** — the low-level commands the porcelain is built from. `hash-object`, `cat-file`,
  `update-index`, `write-tree`, `commit-tree`, `update-ref`, `rev-parse`. Output is stable and designed
  for scripts.

That stability guarantee is the practical reason to know plumbing: **scripts should use plumbing**,
because porcelain output is explicitly allowed to change.

### What is actually in `.git/`
```
.git/
├── HEAD              a one-line text file: "ref: refs/heads/main"
├── index             ONE binary file: the staging area (ch 03)
├── config            this repo's config (remotes, hooks path, …)
├── objects/          THE DATABASE
│   ├── ab/cdef…      loose object: zlib-compressed, named by its own hash
│   ├── pack/         packfiles: many objects, delta-compressed (ch 37)
│   └── info/         commit-graph, alternates
├── refs/
│   ├── heads/main    41 bytes: a commit hash + newline  ← a BRANCH
│   ├── tags/v1.0     a tag
│   └── remotes/origin/main   the cached remote ref (ch 18)
├── logs/             the reflog (ch 16)
└── hooks/            NOT cloned, by design (ch 26)
```

Almost all of it is plain text. `objects/` and `index` are the only binary parts, and both are
readable through plumbing.

### The object hash, computed by hand
Git does not hash the file's bytes. It hashes a **header plus** the bytes:

```
"<type> <byte-length>\0<content>"
```

Which you can verify without git at all:

```bash
printf 'hello git\n' | git hash-object --stdin
# 8d0e41234f24b6da002d962a26c2495ea16a425f

# the same thing, computed manually:
printf 'blob 10\0hello git\n' | sha1sum
# 8d0e41234f24b6da002d962a26c2495ea16a425f
```

Identical. `hello git\n` is 10 bytes, so the header is `blob 10\0`. That is the entire algorithm —
there is no magic in git's content addressing, just SHA-1 over a typed, length-prefixed payload.

The length prefix is not decoration: it makes the type and size part of the identity, which is what
prevents a blob and a tree with the same bytes from colliding.

### The four plumbing commands that build a commit
| Command | Does |
|---|---|
| `git hash-object -w` | write content → a **blob**, print its hash |
| `git update-index --add --cacheinfo <mode>,<hash>,<path>` | put an entry in the **index** |
| `git write-tree` | turn the index into a **tree** object, print its hash |
| `git commit-tree <tree> -p <parent> -m <msg>` | create a **commit** object, print its hash |
| `git update-ref refs/heads/<branch> <commit>` | point a **branch** at it |

Read that list again: it is exactly `git add` + `git commit`, decomposed. Nothing else happens.

### Tree entry modes
```
100644 blob   regular file
100755 blob   executable file
120000 blob   symlink
040000 tree   directory
160000 commit gitlink (a submodule — ch 36)
```

Five modes. Git deliberately stores almost no permission data — only the executable bit — because
reproducing arbitrary POSIX permissions across Linux, macOS and Windows is not achievable
([Chapter 05](05_How_Git_Stores_Everything.md)).

### Reading the index
```bash
git ls-files -s          # mode, hash, stage, path — the index as text
git ls-files -s | head -3
# 100644 8b13789… 0    .gitignore
```

Stage `0` means "no conflict". During a merge conflict the same path appears at stages 1, 2 and 3 —
base, ours, theirs — which is literally how git tracks a conflict
([Chapter 12](12_Merge_Conflicts.md)). That is a satisfying detail: a "conflict" is not a special state,
it is three index entries for one path.

### `rev-parse`: the universal translator
```bash
git rev-parse HEAD                 # a ref → a full hash
git rev-parse --short HEAD
git rev-parse HEAD^{tree}          # the commit's tree
git rev-parse --abbrev-ref HEAD    # the current branch NAME
git rev-parse --show-toplevel      # the repo root
git rev-parse --git-path hooks     # where hooks live (worktree-safe — ch 27)
git rev-parse --is-inside-work-tree
```

`rev-parse` is the command every git script starts with, because it turns anything human into
something exact.

> 💡 **Samjho aise:** Ab tak humne git ka **naksha** padha. Is chapter mein tum **apne haath se ghar
> banaoge** — bina `git add`, bina `git commit`.
>
> Chaar kadam, bas: content ka blob banao → index mein entry daalo → index se tree banao → tree ka
> commit banao → branch ka naam-patta us commit pe laga do. `git add` aur `git commit` **yahi** karte
> hain, sirf ek saath.
>
> Aur hash ka raaz? Koi jaadu nahi: `"blob 10\0hello git\n"` ka SHA-1. `sha1sum` se khud nikaal ke mila
> lo — bilkul wahi aayega. Jis din ye khud kar loge, git dar-avni cheez se **samajh mein aane wali
> cheez** ban jaayegi.

# Real World Example (this repo)
Every claim below is real output from this repository.

**A commit, exactly as git stores it:**

```bash
git cat-file -p HEAD
```
```
tree 9653375af0159933b1aca53bba034d660693db74
parent 83a144ba3fad222bdd3b85d7b5f67a7fb0604ed2
author umesh-personal <umesh29mar@gmail.com> 1785747733 +0530
committer umesh-personal <umesh29mar@gmail.com> 1785747733 +0530

chore(repo): stop tracking database dumps + node_modules; teach why in the course
```

Five parts, all plain text: tree, parent, author, committer, message. That block **is** the input to
the hash — which is why amending anything produces a different commit
([Chapter 34](34_Rewriting_History.md)).

**A branch is 41 bytes:**

```bash
cat .git/refs/heads/new_flask_app
# 42a2ecc4dc77dafc9407f4eaf4840c3ed8bd97fa
wc -c < .git/refs/heads/new_flask_app
# 41                                          ← 40 hex + newline
```

**HEAD is one line of text:**

```bash
cat .git/HEAD
# ref: refs/heads/new_flask_app
```

That indirection is the whole mechanism of branch switching: `git switch` rewrites this one line.
A **detached HEAD** is simply this file containing a raw hash instead of a `ref:` line — not a broken
state, a different value ([Chapter 10](10_Creating_And_Switching_Branches.md)).

**The hash algorithm, verified here:**

```bash
printf 'hello git\n' | git hash-object --stdin      # 8d0e41234f24b6da002d962a26c2495ea16a425f
printf 'blob 10\0hello git\n' | sha1sum             # 8d0e41234f24b6da002d962a26c2495ea16a425f
```

**A merge commit has two `parent` lines — that is the entire definition:**

```bash
git cat-file -p 83a144ba | head -3
# tree   …
# parent fa9507d7…      ← ^1 : main's side
# parent 7fe2bb0e…      ← ^2 : the merged feature branch
```

No flag, no special record type. Two parent fields ([Chapter 06](06_The_Commit_Graph.md)).

**The object database, measured:**

```bash
git count-objects -vH
# count: 4873      size: 26.19 MiB        ← loose
# in-pack: 25975   size-pack: 63.66 MiB   ← packed (ch 37)
```

**And plumbing in production, in this very repository.** Two places where the project uses plumbing
because porcelain could not do the job:

1. **`git-hooks/install.sh`** uses `git rev-parse --git-path hooks` rather than hardcoding
   `.git/hooks`, so it works inside a worktree or an unusual layout
   ([Chapters 17](17_Stash_And_Worktrees.md), [27](27_Pre_Push_Protection.md)).
2. **The dump cleanup** used a plumbing pipeline to untrack exactly the right 2,954 files:
   ```bash
   git ls-files -i -c --exclude-standard -z \
     | git rm --cached --quiet --pathspec-from-file=- --pathspec-file-nul
   ```
   `ls-files -i -c` (ignored **and** cached) is a pure index query — there is no porcelain equivalent
   for "what is tracked that my ignore rules say should not be"
   ([Chapter 33](33_Secrets_And_Leaks.md)).

# Visual Diagram
```
  .git/ — mostly PLAIN TEXT
  ────────────────────────
   HEAD                  "ref: refs/heads/new_flask_app"        ← 1 line
   refs/heads/…          "42a2ecc4…"                            ← 41 BYTES
   index                 ONE binary file = the staging area
   objects/ab/cdef…      loose object, zlib, named by its hash
   objects/pack/         25,975 objects, delta-compressed
   logs/                 the reflog          hooks/  NOT cloned

  THE HASH — no magic
  ───────────────────
   "<type> <length>\0<content>"  →  SHA-1
   printf 'blob 10\0hello git\n' | sha1sum
     = 8d0e41234f24b6da002d962a26c2495ea16a425f
     = git hash-object --stdin        ← IDENTICAL

  BUILD A COMMIT BY HAND — this IS add + commit, decomposed
  ────────────────────────────────────────────────────────
   content
      │  git hash-object -w
      ▼
    BLOB ──► git update-index --add --cacheinfo 100644,<blob>,path
                    │
                    ▼
                  INDEX ──► git write-tree
                                │
                                ▼
                              TREE ──► git commit-tree <tree> -p <parent> -m "msg"
                                            │
                                            ▼
                                         COMMIT ──► git update-ref refs/heads/x <commit>
                                                          │
                                                          ▼
                                                    the branch moved

  TREE MODES                    INDEX STAGES
  ──────────                    ────────────
   100644 blob  file             0 = normal
   100755 blob  executable       1 = base    ┐
   120000 blob  symlink          2 = ours    ├ a CONFLICT is just
   040000 tree  directory        3 = theirs  ┘ 3 entries for one path
   160000 commit gitlink (submodule)
```

# Practical — build a commit with no porcelain
Run this whole block. It is the point of the chapter.

```bash
mkdir /tmp/plumbing && cd /tmp/plumbing && git init -q
git config user.email t@t && git config user.name t

# ── 1. CONTENT → BLOB (no `git add`) ───────────────────────────────────────
echo "hand-built" > /dev/null                 # we do not even need a file on disk
BLOB=$(printf 'hand-built\n' | git hash-object -w --stdin)
echo "blob:   $BLOB"
git cat-file -t "$BLOB"                       # blob
git cat-file -p "$BLOB"                       # hand-built

# ── 2. BLOB → INDEX (no `git add`) ─────────────────────────────────────────
git update-index --add --cacheinfo 100644,"$BLOB",hello.txt
git ls-files -s                               # 100644 <blob> 0  hello.txt

# ── 3. INDEX → TREE ────────────────────────────────────────────────────────
TREE=$(git write-tree)
echo "tree:   $TREE"
git cat-file -p "$TREE"                       # 100644 blob <blob>  hello.txt

# ── 4. TREE → COMMIT (no `git commit`) ─────────────────────────────────────
COMMIT=$(git commit-tree "$TREE" -m "feat: built entirely with plumbing")
echo "commit: $COMMIT"
git cat-file -p "$COMMIT"                     # tree / author / committer / message

# ── 5. MOVE THE BRANCH ─────────────────────────────────────────────────────
git update-ref refs/heads/main "$COMMIT"
git log --oneline                             # your hand-built commit, in history
cat .git/refs/heads/main                      # 41 bytes
wc -c < .git/refs/heads/main

# ── 6. make the working tree match what you built ──────────────────────────
git checkout -- . 2>/dev/null || git reset --hard
cat hello.txt                                 # hand-built
git status                                    # clean

# ── 7. a SECOND commit, with a parent — this is how history forms ──────────
BLOB2=$(printf 'second version\n' | git hash-object -w --stdin)
git update-index --add --cacheinfo 100644,"$BLOB2",hello.txt
TREE2=$(git write-tree)
COMMIT2=$(git commit-tree "$TREE2" -p "$COMMIT" -m "feat: second, by hand")
git update-ref refs/heads/main "$COMMIT2"
git log --oneline --graph
git cat-file -p "$COMMIT2" | head -2          # note the `parent` line
```

**You just implemented `git add` and `git commit`.** Five plumbing commands, and nothing was hidden.

```bash
# ── EXPLORE THE REAL REPO ──────────────────────────────────────────────────
cd /home/tech/umesh-personal
git cat-file -p HEAD                          # the commit as stored
git cat-file -p HEAD^{tree} | head            # the root directory listing
git cat-file -p HEAD:CONTRIBUTING.md | head -3 # a file's content, via the tree
git cat-file -s HEAD                          # object size in bytes
git ls-files -s | head -3                     # the index, as text
cat .git/HEAD ; cat .git/refs/heads/new_flask_app
git rev-parse HEAD --short HEAD HEAD^{tree} --abbrev-ref HEAD --show-toplevel
git fsck --no-progress | tail -3              # verify every object hashes to its name

# read a LOOSE OBJECT off disk yourself — zlib only, no git involved.
# This is the proof that .git/objects is not magic: it is zlib-compressed
# "<type> <length>\0<content>", stored under its own hash.
cd /tmp && rm -rf zt && mkdir zt && cd zt && git init -q
H=$(printf 'zz\n' | git hash-object -w --stdin)
python3 - "$H" <<'PYEOF'
import sys, zlib, pathlib
h = sys.argv[1]
raw = zlib.decompress(pathlib.Path(f'.git/objects/{h[:2]}/{h[2:]}').read_bytes())
print(repr(raw))        # b'blob 3\x00zz\n'  ← the header is right there
PYEOF
```

# Production Walkthrough
When plumbing is the right tool in real work:

1. **Scripts and hooks.** Porcelain output can change between git versions; plumbing output is stable.
   Anything committed to the repo should use plumbing.
2. **Index queries with no porcelain equivalent.**
   `git ls-files -i -c --exclude-standard` — "tracked but ignored" — is how this project found the
   2,954 files that should not have been tracked.
3. **Location resolution in scripts.** `git rev-parse --show-toplevel` and
   `git rev-parse --git-path hooks` instead of assuming `.git/` — which is what makes
   `git-hooks/install.sh` work inside a worktree.
4. **Reading historical content for an audit.** `git cat-file -p <commit>:<path>` reads a *deleted*
   file's content — the core move in the leak triage ([Chapter 33](33_Secrets_And_Leaks.md)).
5. **Recovery when porcelain refuses.** A corrupt index is fixable by deleting `.git/index` and running
   `git reset`; dangling commits are findable with `git fsck --lost-found`
   ([Chapter 39](39_Disaster_Playbook.md)).
6. **Bulk analysis.** `git rev-list --objects --all` piped to `git cat-file --batch-check` is the only
   sane way to find the biggest blobs ([Chapter 37](37_Large_Files_And_Performance.md)).

# Debugging Guide

| Symptom | Cause | Fix |
|---|---|---|
| `fatal: not a git repository` in a script | wrong working directory assumption | `cd "$(git rev-parse --show-toplevel)"` |
| Hook not found in a worktree | hardcoded `.git/hooks` | `git rev-parse --git-path hooks` |
| `.git/index` corrupt | interrupted operation, disk issue | `rm .git/index && git reset` — rebuilds from HEAD |
| `git write-tree` fails | unmerged index entries (stages 1/2/3) | resolve the conflict, `git add`, retry |
| Object exists but is unreachable | no ref points to it | `git fsck --lost-found`; `git update-ref` to name it |
| `error: object file … is empty` | corruption — content no longer hashes to its name | `git fsck`; fetch the object from another clone |
| Script breaks after a git upgrade | it parsed **porcelain** output | switch to plumbing, or `--porcelain=v2` for `status` |
| `cat-file` says "Not a valid object name" | ref does not exist, or wrong syntax | `git rev-parse <thing>` to resolve it first |
| Detached HEAD confusion | `.git/HEAD` holds a hash, not a `ref:` line | `cat .git/HEAD` to see it; `git switch <branch>` |

# Performance Notes
- **`git cat-file --batch` / `--batch-check`** reads many objects in one process. Spawning `cat-file -p`
  per object in a loop is the classic slow script.
- **Object reads are O(1)** — the hash is the address, so `git log` over 289 commits is instant.
- **Loose versus packed matters**: here 25,975 packed objects in 63.66 MiB versus 4,873 loose in
  26.19 MiB — about 5× denser packed ([Chapter 37](37_Large_Files_And_Performance.md)).
- **`git ls-files` reads one file** (`.git/index`) rather than walking the working tree, which is why
  index queries are fast.
- **`git fsck` verifies every object** — minutes on a large repo, since it decompresses and rehashes
  everything.
- **`hash-object` without `-w`** computes without writing, so it is free to ask "what would this hash
  be".

# Security Considerations
- **`git hash-object -w` writes to the object store immediately** — no commit needed. That is why
  `git add` is the moment a secret enters the repository, not `git commit`
  ([Chapter 33](33_Secrets_And_Leaks.md)).
- **Unreachable objects are readable.** `git fsck --lost-found` and `git cat-file` will happily print
  content from a commit you thought you had discarded.
- **`git cat-file -p <old-commit>:<path>` reads deleted files** — an audit tool, and equally a tool for
  anyone who clones your repository.
- **Content addressing guarantees integrity, not confidentiality.** `git fsck` proves nothing was
  altered; it says nothing about who can read it.
- **Author and committer fields are plain text** and unverified. Only signing proves authorship
  ([Chapter 31](31_Signed_Commits.md)).
- **`update-ref` can move a branch anywhere**, bypassing every porcelain safety check. Powerful, and
  worth respecting.
- **Only the executable bit is tracked.** Never rely on file modes in git for any security property.

# Architecture Decisions
- **Git separates plumbing from porcelain deliberately**, with a stability guarantee on plumbing output.
  That is what makes git scriptable across decades of versions.
- **Content addressing with a typed, length-prefixed header** (`"blob 10\0…"`) so type and size are part
  of identity, preventing cross-type collisions and making integrity checkable.
- **HEAD is indirection through a text file**, which is why branch switching is a one-line write and why
  a detached HEAD is a *value*, not a failure mode.
- **The index is one binary file** — atomically replaceable, and disposable: delete it and
  `git reset` rebuilds it from HEAD.
- **Almost no permission data is stored** (executable bit only), a portability decision.
- **This project uses plumbing where porcelain cannot express the query** — `ls-files -i -c` for the
  tracked-but-ignored audit, `rev-parse --git-path` for worktree-safe hook installation.
- **Scripts committed to this repo prefer plumbing**, so a git upgrade cannot break them by changing
  human-facing output.

# Best Practices
- Use **plumbing in scripts**, porcelain at the keyboard.
- Start every git script with `git rev-parse --show-toplevel`.
- Use `--git-path` rather than assuming `.git/`.
- Use `cat-file --batch-check` for bulk reads; never loop `cat-file -p`.
- Read `git ls-files -s` when you need to know what the index really holds.
- Remember `hash-object` without `-w` is a pure computation — safe to run anywhere.
- Run `git fsck` occasionally; content addressing makes it meaningful.
- Reach for `--porcelain=v2` if you must parse `git status` in a script.

# Beginner Mistakes
- **Parsing porcelain output in scripts** → breaks on a git upgrade; that is why plumbing exists.
- **Assuming `.git/hooks`** → wrong inside a worktree; use `rev-parse --git-path hooks`.
- **Thinking `.git` is opaque** → HEAD and refs are plain text you can `cat`.
- **Believing a detached HEAD is broken** → it is `.git/HEAD` holding a hash instead of a `ref:` line.
- **Deleting `.git/index` in a panic** → actually fine (`git reset` rebuilds it); deleting
  `.git/objects` is not.
- **Looping `cat-file -p`** over thousands of objects → use `--batch`.
- **Assuming git hashes the file contents** → it hashes `"<type> <len>\0<content>"`.
- **`git update-ref` without understanding it** → moves a branch with no safety checks.

# Interview Questions
- **Junior:** "What is in `.git/`?" — The object database (`objects/`), refs (`refs/heads`, `refs/tags`,
  `refs/remotes`), `HEAD` as a one-line pointer, the `index` binary file that is the staging area, the
  reflog in `logs/`, config, and hooks. Almost all of it is plain text.
- **Mid:** "How does git compute an object's hash?" — SHA-1 over `"<type> <byte-length>\0<content>"`, not
  over the raw bytes. You can reproduce it with `printf 'blob 10\0hello git\n' | sha1sum` and get the
  same value as `git hash-object`. The type and length being inside the hashed payload is what keeps a
  blob and a tree with identical bytes from colliding.
- **Senior:** "Create a commit without `git add` or `git commit`." — Five plumbing steps:
  `git hash-object -w` to store the content as a blob, `git update-index --add --cacheinfo
  <mode>,<hash>,<path>` to place it in the index, `git write-tree` to turn the index into a tree,
  `git commit-tree <tree> -p <parent> -m <msg>` to create the commit, and `git update-ref
  refs/heads/<branch> <commit>` to move the branch. That sequence *is* `add` plus `commit`, decomposed —
  which is the clearest way to show that nothing else is happening under the porcelain.
- **Staff:** "Why does git distinguish plumbing from porcelain, and why should you care?" — Because they
  make opposite promises. Porcelain output is human-facing and explicitly allowed to change between
  versions; plumbing output is a stable interface intended for scripts. So any script that parses
  porcelain is carrying a latent break that arrives with a routine git upgrade, and the failure is
  usually silent — a `grep` that stops matching does not error, it just reports nothing found. Practical
  consequences I would enforce: hooks and CI scripts use plumbing; use `--porcelain=v2` when `status`
  really must be parsed; resolve locations with `rev-parse --show-toplevel` and `--git-path` rather than
  hardcoding `.git/`, so worktrees keep working. And plumbing is not only about stability — some queries
  have no porcelain form at all. `git ls-files -i -c --exclude-standard` answers "what is tracked that my
  ignore rules say should not be", which is exactly the audit that found 2,954 wrongly-tracked files in
  this repository. If you only know porcelain, that question is unaskable.

### Why interviewers ask these — and the answer that separates levels
| Testing for | Weak answer | What lands |
|---|---|---|
| Is `.git` a black box to you? | "It's git's internal folder." | HEAD is one line, a branch is 41 bytes, the index is one binary file, `objects/` is the database — mostly readable text. |
| Do you know the hash algorithm? | "Git hashes the file." | SHA-1 over `"<type> <len>\0<content>"` — reproducible with `sha1sum`, and the prefix is what prevents cross-type collisions. |
| Have you decomposed the porcelain? | "`git commit` makes a commit." | hash-object → update-index → write-tree → commit-tree → update-ref: `add` + `commit`, with nothing hidden. |

**The killer follow-up:** *"Your CI script broke after a git upgrade. Why?"* — Almost certainly it parsed porcelain output, which git explicitly reserves the right to change, and the break is silent because a pattern that no longer matches reports nothing rather than failing. The fix is plumbing, or `--porcelain=v2` for `status` — and the general principle is that anything committed to the repository should use the stable interface, not the human one.

# Revision Notes
- **Porcelain** = human-facing, output may change. **Plumbing** = stable, for scripts.
- `.git/HEAD` = one line (`ref: refs/heads/x`). A branch = **41 bytes**. `index` = one binary file. `objects/` = the database.
- **Hash = SHA-1 of `"<type> <length>\0<content>"`.** `printf 'blob 10\0hello git\n' | sha1sum` == `git hash-object`.
- **Build a commit:** `hash-object -w` → `update-index --add --cacheinfo` → `write-tree` → `commit-tree -p` → `update-ref`. That IS add+commit.
- Tree modes: `100644` file · `100755` exec · `120000` symlink · `040000` tree · `160000` gitlink.
- **Index stages:** 0 normal · 1 base · 2 ours · 3 theirs ⇒ **a conflict is 3 entries for one path**.
- `rev-parse` = the translator: `--show-toplevel`, `--git-path hooks`, `--abbrev-ref`, `HEAD^{tree}`.
- **`hash-object -w` writes immediately** ⇒ `git add` is when a secret enters the repo.
- `cat-file --batch-check` for bulk; never loop `cat-file -p`.
- `.git/index` is disposable (`git reset` rebuilds it). `.git/objects` is not.

# Cheat Sheet
```bash
# INSPECT
git cat-file -t <ref>              # type: blob|tree|commit|tag
git cat-file -s <ref>              # size in bytes
git cat-file -p <ref>              # PRINT as git stores it
git cat-file -p HEAD^{tree}        # root directory listing
git cat-file -p HEAD:path/to/file  # a file's content via the tree
git cat-file --batch-check         # BULK reads (fast)
git ls-files -s                    # the index, as text (mode hash stage path)
git ls-files -i -c --exclude-standard   # tracked BUT ignored ← no porcelain equivalent
cat .git/HEAD ; cat .git/refs/heads/main
git count-objects -vH
git fsck --lost-found              # unreachable objects

# HASH
printf 'x\n' | git hash-object --stdin        # compute, do NOT store
printf 'x\n' | git hash-object -w --stdin     # compute AND store
printf 'blob 2\0x\n' | sha1sum                # the same value, by hand

# BUILD A COMMIT BY HAND
B=$(printf 'content\n' | git hash-object -w --stdin)
git update-index --add --cacheinfo 100644,"$B",file.txt
T=$(git write-tree)
C=$(git commit-tree "$T" -p HEAD -m "msg")
git update-ref refs/heads/main "$C"

# TRANSLATE (start every script with these)
git rev-parse --show-toplevel      # repo root
git rev-parse --git-path hooks     # worktree-safe hooks dir
git rev-parse --abbrev-ref HEAD    # current branch NAME
git rev-parse HEAD^{tree}
git status --porcelain=v2          # the ONLY safe way to parse status
```

# My ERP Section

| Internal | Value in this repository |
|---|---|
| `.git/HEAD` | `ref: refs/heads/new_flask_app` — one line of text |
| `.git/refs/heads/new_flask_app` | `42a2ecc4dc77dafc9407f4eaf4840c3ed8bd97fa` — **41 bytes** |
| HEAD commit object | tree `9653375a…`, parent `83a144ba…`, author/committer `umesh-personal <umesh29mar@gmail.com> 1785747733 +0530` |
| A real merge commit | `83a144ba` — **two** `parent` lines: `fa9507d7` (^1) and `7fe2bb0e` (^2) |
| Hash verified | `printf 'hello git\n' \| git hash-object --stdin` = `printf 'blob 10\0hello git\n' \| sha1sum` = `8d0e4123…` |
| Object database | 4,873 loose (26.19 MiB) · **25,975 packed** (63.66 MiB) in 2 packs |
| Plumbing in production 1 | `git-hooks/install.sh` uses `git rev-parse --git-path hooks` — worktree-safe rather than hardcoding `.git/hooks` |
| Plumbing in production 2 | the cleanup pipeline `git ls-files -i -c --exclude-standard -z \| git rm --cached --pathspec-from-file=- --pathspec-file-nul` untracked exactly **2,954** files — a pure index query with no porcelain equivalent |
| Audit via plumbing | `git cat-file -p <commit>:<path>` read the *deleted* dump's contents during the leak triage ([Ch 33](33_Secrets_And_Leaks.md)) |

# Practice Tasks
1. Run the whole Practical block. Building a commit with five plumbing commands is the single most
   clarifying five minutes in this course.
2. Verify the hash by hand: `printf 'blob 10\0hello git\n' | sha1sum` and compare with
   `git hash-object`. Then do it for content of your own — remember the length must be exact.
3. `git cat-file -p HEAD^{tree}`, pick a `tree` entry, and `cat-file -p` it. Keep descending until you
   reach a blob. You have walked the database by hand.
4. `cat .git/HEAD`, then `git switch --detach HEAD`, then `cat .git/HEAD` again. One file, two forms —
   that is all "detached" means.
5. Create a conflict in a throwaway repo and run `git ls-files -s`. Find the same path at stages 1, 2
   and 3.
6. Delete `.git/index`, run `git status` (alarming), then `git reset` and confirm full recovery. The
   index is disposable; history is not.

# Homework
- Write a shell script that creates a commit using only plumbing, takes the message as an argument, and
  works from any subdirectory (`rev-parse --show-toplevel`). You now understand `git commit`.
- Read a loose object off disk yourself with Python:
  `zlib.decompress(open('.git/objects/ab/cdef…','rb').read())`. Find the `"blob <len>\0"` header in the
  output. No git involved.
- Take any script you have that parses `git status` or `git log` output and convert it to plumbing or
  `--porcelain=v2`. That is the concrete payoff of this chapter.
- Read the [Pro Git internals chapter](https://git-scm.com/book/en/v2/Git-Internals-Plumbing-and-Porcelain)
  and then explain, without notes, what `git add` does in terms of plumbing. If you can, the model is
  permanently yours.

# Further Reading & Live Resources
- [Pro Git — Plumbing and Porcelain](https://git-scm.com/book/en/v2/Git-Internals-Plumbing-and-Porcelain) — the canonical chapter this one is built on; free
- [Pro Git — Git Objects](https://git-scm.com/book/en/v2/Git-Internals-Git-Objects) — blobs, trees, commits, built by hand
- [Pro Git — Git References](https://git-scm.com/book/en/v2/Git-Internals-Git-References) — HEAD, refs, packed-refs
- [Git from the Bottom Up](https://jwiegley.github.io/git-from-the-bottom-up/) — the classic essay that starts at the object store
- [Write yourself a Git!](https://wyag.thb.lt/) — implement git in Python; the deepest possible version of this chapter
- [git-cat-file](https://git-scm.com/docs/git-cat-file) · [git-update-index](https://git-scm.com/docs/git-update-index) · [git-commit-tree](https://git-scm.com/docs/git-commit-tree) — the plumbing references
- [Git index format](https://git-scm.com/docs/index-format) — what is actually inside `.git/index`
