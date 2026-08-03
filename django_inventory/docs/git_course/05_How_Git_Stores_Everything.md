---
id: git-course-05-how-git-stores-everything
type: lesson
status: active
owner: handwritten
scope: git internals — blobs, trees, commits, tags, content addressing, packfiles
anchors: .git/objects, .git/HEAD, .git/refs/heads
verified: 2026-08-03
---

# 05 — How Git Stores Everything (four object types and one big hash table)

> Part of [Git Course](00_COURSE_OVERVIEW.md). Prev: [04 — Your First Repository](04_Your_First_Repository.md). Next: [06 — The Commit Graph](06_The_Commit_Graph.md).

# Learning Objectives
By the end of this chapter you can:
- name git's four object types and say what each one contains
- explain "content-addressed" and why identical content is stored exactly once
- read a real commit object with `git cat-file -p` and identify every field
- explain why changing a commit message changes the commit's hash — and therefore every commit after it
- explain what a packfile is and why `.git` is smaller than the sum of its history
- say precisely what "git never deletes anything" means, and where it stops being true

# Purpose
Git is not a diff tool. It does not store "changes". This surprises almost everyone, because
`git diff` is how we look at it — but diffs are *computed on demand*, not stored.

What git actually is: **a key-value store where the key is the SHA-1 hash of the content.**
Four object types, one hash table, and a handful of pointers. That is the entire database.

Once you see that, a long list of confusing behaviours becomes a single consequence:
why rebase creates *new* commits rather than moving old ones, why a force-push is dangerous,
why a deleted secret is still in your history, why two identical files cost one file of space.
All of it falls out of "the hash is the address".

# The Problem
Without this model you are stuck memorising unrelated rules:

- "Never rebase a shared branch" — *why not, though?*
- "Deleting the file doesn't remove the secret" — *why, if the file is gone?*
- "Amending a commit rewrites history" — *it's just a message, surely?*
- "`git gc` shrank my repo by 60%" — *what was it doing before?*

These look like six facts to remember. They are one fact with six faces, and this chapter is
that fact.

# Theory (from zero)

### Content addressing: the hash IS the filename
Give git some bytes and it does two things: hashes them, and stores them under that hash.

```bash
printf 'hello git\n' | git hash-object --stdin
# 8d0e41234f24b6da002d962a26c2495ea16a425f
```

That is a real hash from this repository's git. Run it on **any** machine, in **any** repo, with
the same bytes, and you get the same 40 hex characters. The hash is a pure function of content.

Three consequences drop straight out:

1. **Deduplication is free.** The same file content in 50 commits is stored **once** — all 50
   trees just point at the same hash.
2. **Integrity is free.** Corrupt a stored object and its content no longer hashes to its own
   name. `git fsck` detects that instantly.
3. **Identity is content.** Change one byte and it is a *different object*, at a different
   address. Nothing is ever "edited in place" — that concept does not exist in git.

Point 3 is the one that matters for the rest of this course.

### The four object types
Everything in `.git/objects` is one of these:

| Type | Contains | Analogy |
|---|---|---|
| **blob** | file *contents* — no name, no path, no permissions | the bytes of a document |
| **tree** | a directory listing: names + modes + hashes of blobs and sub-trees | a folder |
| **commit** | one tree hash + parent hash(es) + author + committer + message | a labelled snapshot |
| **tag** | a pointer to an object + tagger + message (annotated tags only) | a bookmark with a note |

Note what a blob does **not** have: a filename. Names live in trees. That is why moving a file
without editing it costs git nothing — same blob, different entry in a different tree. It is also
why `git log --follow` is needed to track a renamed file: git infers renames by comparing content,
because it never recorded a "rename" event.

### A real commit object, field by field
`git cat-file -p` prints an object exactly as git stores it. This is the real HEAD commit of this
repository:

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

Read every line:

- **`tree`** — the root directory snapshot for this commit. Follow it and you can reconstruct
  every file at that moment. A commit does not store changes; it stores a *complete* tree.
- **`parent`** — the commit before this one. This single field is what makes history a graph
  ([Chapter 06](06_The_Commit_Graph.md)). The very first commit has no parent; a merge commit has
  two or more.
- **`author`** — who wrote the change, and when. `1785747733` is a Unix timestamp; `+0530` is the
  IST offset.
- **`committer`** — who *applied* it. Differs from author after a rebase or cherry-pick.
- **message** — after a blank line, the rest is free text.

**That whole block is the input to the hash.** Which gives you the most important inference in
this chapter: change the message, or the author, or the parent — and you get a **different
commit**, with a different hash. The original is not modified, because objects are immutable.

### Why that makes rebase "rewrite" history
[Rebase](13_Rebase.md) replays your commits onto a new base. The new base is a different
`parent`. Different parent ⇒ different hash ⇒ **a new commit object**. Your original commits are
still in `.git/objects`, just unreferenced.

So "rebase moves commits" is wrong in a way that matters. Rebase **copies** them, and the old
copies become garbage. That is why:

- your work is recoverable after a bad rebase (via [reflog](16_Reflog.md)) — the old objects exist;
- rebasing a *shared* branch is antisocial — everyone else still points at hashes you abandoned.

### How a tree points at things
```bash
git cat-file -p HEAD^{tree} | head -4
```
```
100644 blob 8b13789…    .gitignore
040000 tree a1c2f5e…    django_inventory
100644 blob 4d3f8a1…    CONTRIBUTING.md
```

`100644` is a regular file, `100755` executable, `040000` a directory, `120000` a symlink. Git
stores almost no permission data — just the executable bit. That is deliberate: reproducing
arbitrary POSIX permissions across machines is a portability nightmare, and git chose not to try.

### Loose objects vs packfiles
Fresh objects are written **loose**: one zlib-compressed file per object at
`.git/objects/ab/cdef…` (first two hex characters as the directory). One object per file is
simple but wasteful.

Periodically — on `git gc`, and automatically during `git push`/`git clone` — git builds a
**packfile**: many objects in one file, with **delta compression** between *similar* objects.

This is the subtle bit: git's storage model is snapshots, but its *wire and disk* format uses
deltas as an optimisation. Snapshots conceptually, deltas physically. Both statements are true,
at different layers.

Real numbers from this repository:

```bash
git count-objects -vH
```
```
count: 4873                 ← loose objects
size: 26.19 MiB             ← ...taking 26 MB
in-pack: 25975              ← packed objects
packs: 2
size-pack: 63.66 MiB        ← ...taking 64 MB for 5x more objects
```

**25,975 packed objects in 64 MB; 4,873 loose objects in 26 MB.** Packed storage is roughly
5× more efficient per object here. That is delta compression plus a single-file layout doing
their job.

> 💡 **Samjho aise:** Git ek **almari** hai jisme har cheez uske apne *fingerprint* ke naam se
> rakhi jaati hai. Ek hi cheez do baar daalo — dobara jagah nahi lagti, kyunki fingerprint wahi
> hai.
>
> Aur andar sirf **chaar** kism ki cheezein hain: **blob** = file ka andar ka maal (naam nahi!),
> **tree** = folder ki list, **commit** = ek photo + pichhli photo ka pata, **tag** = bookmark.
>
> Sabse badi baat: **kuch bhi badla nahi jaata.** Commit ka message badla? Wo purani commit
> badli nahi — **nayi** ban gayi, naye fingerprint ke saath. Purani almari mein padi hai, bas
> uska naam-patta hat gaya. Isliye galti sudhar sakti hai (reflog), aur isliye doosron ki
> branch dobara likhna badtameezi hai — unke paas purane pate hain.

# Real World Example (this repo)
Two facts from this repository that only make sense with the object model.

**1. A branch is 41 bytes.** Not a copy of your code — a file containing one hash:

```bash
cat .git/refs/heads/new_flask_app
# 42a2ecc4dc77dafc9407f4eaf4840c3ed8bd97fa
wc -c < .git/refs/heads/new_flask_app
# 41                       ← 40 hex characters + one newline
```

That is why branching is instant and free, however large the project.
[Chapter 09](09_What_A_Branch_Really_Is.md) builds on this.

**2. The database dumps are still in history, and the object model says why.** On 2026-08-03,
`git rm --cached` untracked two `pg_dump` files. The files left the index and the current tree.
But the **blobs** — the actual dump contents, emails and password hashes included — remain
objects in `.git/objects`, referenced by every earlier commit's tree.

```bash
git log --all --oneline -- Django_app/myproject/mydb_backup_20250620.sql | tail -1
# b7fe9c89 ...        ← the commit that added it; its tree still points at the blob
git show b7fe9c89:Django_app/myproject/mydb_backup_20250620.sql | head -3
# -- PostgreSQL database dump      ← still fully readable
```

**This is the whole reason "delete the file" is not "remove the secret".** Removal means either
rewriting every commit whose tree references that blob (`git filter-repo`, a force-push, and
everyone re-cloning — [Chapter 34](34_Rewriting_History.md)), or accepting it and rotating the
credential. This project chose the second, deliberately, and recorded why: 0 forks, repo going
private, audit showed nothing usable inside (1,000,000-iteration hashes, empty OAuth tables,
expired sessions). See [Chapter 33](33_Secrets_And_Leaks.md).

# Visual Diagram
```
  .git/HEAD                     "ref: refs/heads/new_flask_app"
       │
       ▼
  .git/refs/heads/new_flask_app  ── 41 bytes: "42a2ecc4…"
       │
       ▼
  ┌──────────── COMMIT 42a2ecc4 ────────────┐
  │ tree     9653375a…                      │──────┐
  │ parent   83a144ba… ──► the commit before │      │
  │ author   umesh <…> 1785747733 +0530     │      │
  │ committer …                              │      │
  │                                          │      │
  │ chore(repo): stop tracking dumps…        │      │
  └──────────────────────────────────────────┘      │
        ▲ every byte above feeds the hash            │
        └── change ANY of it ⇒ different hash        │
            ⇒ a NEW commit, old one untouched        ▼
                                          ┌──── TREE 9653375a ────┐
                                          │ 100644 blob 8b13789 .gitignore
                                          │ 040000 tree a1c2f5e django_inventory ──► more trees
                                          │ 100644 blob 4d3f8a1 CONTRIBUTING.md
                                          └────────────────────────┘
                                                     │
                                                     ▼
                                             BLOB — pure content.
                                             NO name. NO path.
                                             (names live in trees)

  STORAGE:  loose  4,873 objects / 26 MB    ← one zlib file each
            packed 25,975 objects / 64 MB   ← delta-compressed, ~5x denser
```

# Practical — dig into the objects yourself
```bash
cd /home/tech/umesh-personal

# 1. hash some content WITHOUT storing it
printf 'hello git\n' | git hash-object --stdin
# 8d0e41234f24b6da002d962a26c2495ea16a425f   (deterministic everywhere)

# 2. what type is an object?
git cat-file -t HEAD          # commit
git cat-file -t HEAD^{tree}   # tree

# 3. print objects as git stores them
git cat-file -p HEAD          # the commit: tree, parent, author, committer, message
git cat-file -p HEAD^{tree} | head    # the root directory listing

# 4. walk down to actual file content
git cat-file -p HEAD:CONTRIBUTING.md | head -3

# 5. prove identical content is ONE object
echo same > x.txt && echo same > y.txt
git hash-object x.txt y.txt   # two identical hashes ⇒ one object
rm x.txt y.txt

# 6. storage reality
git count-objects -vH

# 7. the biggest objects in your history (see ch 37)
git rev-list --objects --all | head -3

# 8. integrity check — content addressing makes this possible
git fsck --no-progress | tail -3
```

Step 5 is worth pausing on: two files, one object. Content addressing means storage cost tracks
*distinct content*, not file count.

# Production Walkthrough
Where the object model changes a real decision:

1. **Auditing a leak.** `git log --all -- <path>` finds commits touching a file;
   `git show <commit>:<path>` prints the blob. This is how the dump audit was done — reading the
   *historical* blob, not the current file, to establish what actually leaked.
2. **Deciding whether to rewrite history.** Rewriting means new hashes for every affected commit
   and everything after it, a force-push, and every clone breaking. The object model tells you the
   cost precisely, so the decision is informed rather than fearful. Here: not worth it.
3. **Understanding why CI caches work.** `actions/setup-python` with `cache: pip` keys on a
   content hash of the requirements file. Same idea as git's: content in, address out.
4. **Trusting recovery.** After a bad rebase or reset, the old commits still exist as
   unreferenced objects. [Reflog](16_Reflog.md) finds them. Recovery is reading objects that were
   never deleted, which is why "I lost my commits" is almost always false.
5. **Explaining repo size.** 97 MB of `.git` here is history, not the checkout. Objects
   accumulate forever unless history is rewritten ([Chapter 37](37_Large_Files_And_Performance.md)).

# Debugging Guide

| Symptom | Cause | Fix |
|---|---|---|
| Deleted a secret; it is still in history | the blob is referenced by older commits' trees | rotate the credential; rewrite only if truly required ([Ch 34](34_Rewriting_History.md)) |
| Amend/rebase "lost" my commits | new objects were made; old ones are unreferenced | `git reflog`, then `git reset --hard <old-hash>` |
| `.git` far bigger than the checkout | every version of every file is still an object | `git count-objects -vH`; then [Ch 37](37_Large_Files_And_Performance.md) |
| `error: object file … is empty` | disk corruption; content no longer matches its hash | `git fsck`; re-clone, or fetch the object from another clone |
| `git log` loses a file's history at a rename | renames are *inferred*, never recorded | `git log --follow -- <path>` |
| Two hashes for what looks like one file | content differs by a byte — line endings, trailing newline | `git diff` the two blobs; check `core.autocrlf` |
| `git gc` freed a lot of space | loose objects were packed and delta-compressed | expected; that is packfiles working |

# Performance Notes
- **Reading an object is O(1)** — the hash is its address. That is why `git log` on 289 commits
  is instant.
- **Loose vs packed matters:** here, 25,975 packed objects fit in 64 MB while 4,873 loose ones
  take 26 MB. Roughly 5× denser packed.
- `git gc` (automatic during push/clone, or manual) packs loose objects. Safe and usually worth
  running on a repo that has done a lot of local churn.
- **Blob dedup means file count is cheaper than file churn.** A 10 MB binary edited 20 times is
  20 blobs ≈ 200 MB of history. Ten identical 10 MB files are one blob.
- Git switched from SHA-1 to allowing SHA-256 for new repos. SHA-1's collision weakness is not a
  practical attack on git (it adds type+length prefixes and has collision detection), but the
  migration exists for long-term safety.
- `git cat-file --batch` is the fast way to read many objects; spawning `cat-file -p` per object
  in a loop is the slow way.

# Security Considerations
- **`git add` — not `git commit` — is when content enters the object store.** Staging writes the
  blob immediately. "I never committed it" does not mean "it is not in `.git`".
- **Objects are immutable and history is append-only.** Deleting a file creates a *new* tree
  without it; the blob stays reachable from older commits. Any secret ever committed must be
  treated as disclosed and **rotated**, whatever you do to the repo afterwards.
- **Unreferenced objects survive until garbage collection**, and `git gc` has grace periods
  (default ~2 weeks for unreachable objects). "I reset it away" is not deletion.
- **Content addressing is an integrity guarantee, not a confidentiality one.** `git fsck` proves
  nothing was silently altered; it says nothing about who can read it.
- **A blob has no permissions.** Git records only the executable bit, so do not rely on file
  modes to protect anything.
- **Signing exists because object *content* is verifiable but object *authorship* is not.** The
  author field is plain text. See [Chapter 31](31_Signed_Commits.md).

# Architecture Decisions
- **Snapshots, not deltas, at the conceptual layer.** Older systems (RCS, Subversion) stored
  change-sets, making "give me the state at commit X" a replay operation. Git stores complete
  trees, so any checkout is a direct read. Deltas exist only inside packfiles as compression.
- **Content addressing rather than sequential revision numbers.** Costs human-readable versions
  ("r1234" became "42a2ecc4"), buys distributed operation with no central authority to allocate
  numbers, plus free dedup and free integrity checking.
- **Blobs carry no filename.** Names belong to trees. Renames therefore cost nothing to store,
  at the price of having to *infer* them when reading history.
- **Immutability everywhere.** Nothing is edited in place, which is what makes recovery possible
  at all — and what makes "rewriting history" genuinely mean "producing different objects".
- **Only the executable bit is tracked.** Full POSIX permission fidelity across Linux, macOS and
  Windows is not achievable, so git stores the one bit that changes behaviour.
- **This project accepted history rather than rewriting it** for the dump incident — a decision
  the object model makes explicit rather than vague: rewrite = new hashes + force-push +
  everyone re-clones, against an audited-mild exposure.

# Best Practices
- Use `git cat-file -p <ref>` when you want to know what git *actually* recorded.
- Treat any committed secret as disclosed. **Rotate first**, decide about history second.
- Run `git count-objects -vH` before worrying about repo size, and again after `git gc`.
- Never commit large binaries you will edit repeatedly — each version is a whole new blob.
- Use `git log --follow` for files that have been renamed.
- Remember `git add` writes objects, so review with `git diff --staged` before that becomes
  history.
- Prefer `--force-with-lease` over `--force`: it checks the remote still points at the hash you
  think it does.

# Beginner Mistakes
- **"Git stores diffs."** It stores complete snapshots; diffs are computed when you ask.
- **"Deleting the file removes it from the repo."** It removes it from the *current* tree only.
- **"Rebase moves my commits."** Rebase **copies** them to new hashes; the originals linger
  unreferenced.
- **"Amending is just editing a message."** The message is hashed input, so amending produces a
  different commit object entirely.
- **Committing generated artefacts** (`node_modules`, dumps, build output) → every version
  becomes a permanent blob. This repo carried 2,952 `node_modules` files for exactly this reason.
- **Assuming `git gc` deletes your mistakes.** Grace periods keep unreachable objects around for
  weeks, and that is a feature — it is how reflog recovery works.
- **Trusting `git log`'s author field as proof.** It is unverified text; only signatures prove
  authorship.

# Interview Questions
- **Junior:** "What are git's object types?" — blob (file contents, no name), tree (a directory
  listing pointing at blobs and sub-trees), commit (one tree + parent(s) + author/committer +
  message), and tag (an annotated pointer). Everything in `.git/objects` is one of those four.
- **Mid:** "Why does changing a commit message change its hash?" — The hash is computed over the
  commit object's whole content, message included. Objects are immutable, so an "edit" is really
  a new object; and because each commit names its parent by hash, every descendant's hash changes
  too. That is what "rewriting history" means mechanically.
- **Senior:** "Git stores snapshots, but packfiles use deltas. Contradiction?" — No: two layers.
  The data model is complete trees per commit, so any checkout is a direct read rather than a
  replay. Packfiles then delta-compress *similar* objects purely as a storage and transfer
  optimisation, invisible to the model. In this repo that is 25,975 packed objects in 64 MB
  versus 4,873 loose in 26 MB.
- **Staff:** "A credential was committed a year ago and deleted the next day. What is your
  response?" — Rotate the credential immediately; that is the only step that actually removes
  risk, because the blob is reachable from every commit whose tree references it and anyone who
  cloned already has it. Then decide about history separately, on evidence: who could have
  fetched it, was the repo public, is there anything usable in it. Rewriting with `filter-repo`
  means new hashes for all descendants, a force-push, invalidated clones and forks, and broken
  build references — sometimes worth it, often not. Document the decision either way, so a future
  reader knows it was a judgement and not an oversight.

### Why interviewers ask these — and the answer that separates levels
| Testing for | Weak answer | What lands |
|---|---|---|
| Do you know the storage model at all? | "Git saves the changes I make." | Four object types, content-addressed by hash; commits hold complete trees and diffs are computed on demand. |
| Do you understand immutability's consequences? | "Rebase moves commits onto main." | Hash covers all content including the parent, so rebase *copies* to new objects; originals persist unreferenced, which is exactly why reflog can recover them. |
| Can you reason about a real leak? | "I deleted the file and force-pushed." | Rotate first, because clones already have it; then weigh a rewrite against its blast radius and write the decision down. |

**The killer follow-up:** *"Two identical 10 MB files in one commit — how much does git store?"* — One blob, about 10 MB compressed, because the address *is* the content hash. Then the real test: the same 10 MB file edited 20 times is 20 distinct blobs, roughly 200 MB of permanent history. Dedup is across identical content, not across versions — which is precisely why binaries belong in artefact storage rather than git.

# Revision Notes
- Git = **content-addressed key-value store**. Key = SHA of content. Identical content ⇒ one object.
- Four types: **blob** (contents, no name) · **tree** (directory listing) · **commit** (tree + parent + author + message) · **tag**.
- **Commits store complete trees, not diffs.** Diffs are computed on demand.
- Hash covers *everything* in the object ⇒ change message/author/parent ⇒ **new commit**, old one untouched.
- Rebase and amend **copy**; originals become unreferenced but still exist ⇒ [reflog](16_Reflog.md) recovery works.
- **A branch is 41 bytes** — one hash plus a newline.
- Loose objects → **packfiles** (delta-compressed). Here: 25,975 packed/64 MB vs 4,873 loose/26 MB.
- **`git add` writes objects.** A staged secret is already in `.git/objects`.
- Deleting a file makes a new tree without it; the blob stays reachable from older commits. **Rotate secrets.**

# Cheat Sheet
```bash
git hash-object --stdin < file      # what hash would this content get? (no write)
git hash-object -w file             # ...and store it as an object

git cat-file -t <ref>               # type: blob | tree | commit | tag
git cat-file -s <ref>               # size in bytes
git cat-file -p <ref>               # PRINT the object as git stores it  ← the main one
git cat-file -p HEAD                # commit: tree, parent, author, committer, message
git cat-file -p HEAD^{tree}         # root directory listing
git cat-file -p HEAD:path/to/file   # a file's content at HEAD
git cat-file -p <commit>:<path>     # ...at any commit — how a leak gets audited

git count-objects -vH               # loose vs packed, with human sizes
git gc                              # pack loose objects (delta-compress)
git fsck                            # verify every object hashes to its own name

git rev-list --objects --all        # every object with its path (feeds size audits)
git log --all --oneline -- <path>   # every commit that touched a path, ever
git log --follow -- <path>          # ...surviving renames (inferred, not recorded)
cat .git/HEAD                       # "ref: refs/heads/<branch>"
cat .git/refs/heads/<branch>        # 41 bytes: the commit hash
```

# My ERP Section

| Object-model fact | Value in this repository |
|---|---|
| `.git` total | **97 MB** — history, not the checkout |
| Loose objects | **4,873** taking **26.19 MiB** |
| Packed objects | **25,975** taking **63.66 MiB** in **2** packs (~5× denser) |
| HEAD commit | `42a2ecc4` — tree `9653375a`, parent `83a144ba` |
| Branch file size | `.git/refs/heads/new_flask_app` = **41 bytes** |
| Commit identity | `umesh-personal <umesh29mar@gmail.com>`, timestamp `1785747733 +0530` (IST) |
| The leak, in object terms | dump blobs remain reachable from commits `4b6655f5` / `b7fe9c89`; untracking changed the *current* tree only |
| Decision recorded | history **not** rewritten — 0 forks, going private, audited exposure mild ([Ch 33](33_Secrets_And_Leaks.md), [Ch 34](34_Rewriting_History.md)) |

# Practice Tasks
1. Run `printf 'hello git\n' | git hash-object --stdin` on your machine. Confirm you get
   `8d0e41234f24b6da002d962a26c2495ea16a425f` — the same hash printed in this chapter. Content
   addressing, demonstrated.
2. `git cat-file -p HEAD` in any repo and name all five parts out loud: tree, parent, author,
   committer, message.
3. Make two files with identical content, `git hash-object` both, and confirm one hash. Then
   change one byte and confirm the hash is completely different — not "similar".
4. `git cat-file -p HEAD^{tree}` and follow one `tree` entry down with another `cat-file -p`.
   Keep going until you reach a blob. You have just walked the database by hand.
5. `git commit --amend -m "different message"` on a throwaway commit, then `git reflog`. Two
   hashes for "the same" commit — proof that amend creates rather than edits.
6. Run `git count-objects -vH`, then `git gc`, then run it again. Watch loose objects move into
   the pack.

# Homework
- Reconstruct a file's content **without** using `git show`: start at `git cat-file -p HEAD`,
  follow the tree hashes down by hand, and `cat-file -p` the final blob. Do it once and the
  model is yours permanently.
- Find the largest blobs in a repo you own with
  `git rev-list --objects --all | git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' | awk '$1=="blob"' | sort -k3 -n | tail -10`.
  Then decide whether any of them should ever have been committed.
- Read the [Pro Git internals chapter](https://git-scm.com/book/en/v2/Git-Internals-Git-Objects)
  and write your own two-paragraph summary. If you cannot explain content addressing without
  notes, you have not got it yet.
- Look up git's SHA-256 support and form a view on whether it matters for a private project like
  this one. Being able to say "not urgent, and here is why" is a real skill.

# Further Reading & Live Resources
- [Pro Git — Git Objects](https://git-scm.com/book/en/v2/Git-Internals-Git-Objects) — blobs, trees, commits, built up by hand; free
- [Pro Git — Packfiles](https://git-scm.com/book/en/v2/Git-Internals-Packfiles) — how delta compression actually works
- [Git from the Bottom Up](https://jwiegley.github.io/git-from-the-bottom-up/) — the classic essay that starts at the object store and works upward
- [git-cat-file reference](https://git-scm.com/docs/git-cat-file) — including `--batch` for bulk reads
- [Git internals: transfer protocols](https://git-scm.com/book/en/v2/Git-Internals-Transfer-Protocols) — how packfiles move over the network
- [SHA-1 collision detection in git](https://github.blog/2017-03-20-sha-1-collision-detection-on-github-com/) — why git's SHA-1 use is not the vulnerability it sounds like
