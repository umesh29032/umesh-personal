---
id: git-course-37-large-files-and-performance
type: lesson
status: active
owner: handwritten
scope: git — repository size, packfiles, gc, LFS, shallow/partial/sparse clones, performance tuning
anchors: .gitignore, .github/workflows/ci.yml
verified: 2026-08-03
---

# 37 — Large Files & Repo Performance (git never forgets, and that is the problem)

> Part of [Git Course](00_COURSE_OVERVIEW.md). Prev: [36 — Monorepo, Submodules & Subtrees](36_Monorepo_Submodules_Subtrees.md). Next: [38 — Git Internals, Hands-On](38_Git_Internals_Hands_On.md).

# Learning Objectives
By the end of this chapter you can:
- explain why a deleted large file still costs you, forever
- measure a repository properly — objects, packs, and the biggest blobs by size
- explain why **binaries** are uniquely expensive while text is cheap
- choose between shallow, partial (blobless) and sparse clones, and say what each gives up
- explain what Git LFS actually does, and its real costs
- know which commands to run when git feels slow

# Purpose
Git is fast until it is not, and the transition is sudden. A repository grows for months with no
complaint, then one day `git clone` takes eight minutes and `git status` has a noticeable pause.

The cause is almost always the same: **something large is in history, and history is permanent.** Git
never forgets. Every version of every file that was ever committed is still an object in
`.git/objects`, whether or not the file exists today.

This chapter is how to measure that, how to avoid it, and — when it has already happened — what your
actual options are.

# The Problem
Four symptoms with one root cause:

- `git clone` takes minutes for a project whose source is a few megabytes.
- `.git` is 500 MB while the working tree is 20 MB.
- You deleted the 200 MB video file months ago and nothing improved.
- CI spends more time cloning than testing.

That third one is the one people find genuinely surprising, and it follows directly from git's object
model: deleting a file creates a new tree without it, but the **blob** stays reachable from every
earlier commit ([Chapter 05](05_How_Git_Stores_Everything.md)). The file is gone from your working
tree and permanently present in your repository.

# Theory (from zero)

### Why text is cheap and binaries are ruinous
Git stores whole snapshots conceptually, but packfiles **delta-compress similar objects**. That works
brilliantly for text and barely at all for binaries.

| Change | Text (a `.py` file) | Binary (a `.png`, `.xlsx`, `.zip`) |
|---|---|---|
| Edit one line / one pixel | a tiny delta | often a **whole new blob** |
| 20 versions of a 10 MB file | maybe 12 MB total | up to **200 MB** |

Two reasons binaries defeat delta compression: they are usually already compressed (so a one-byte
logical change rewrites the entire byte stream), and git's delta heuristics work on similarity that
compressed formats destroy.

**The rule:** if a file is not text, or is generated, it probably should not be in git. And the cost is
not the file — it is the *number of versions* of it.

### Dedup helps identical content, not versions
Content addressing means identical content is stored **once**
([Chapter 05](05_How_Git_Stores_Everything.md)): ten copies of the same 10 MB file cost 10 MB. But
**twenty edits** to one 10 MB file cost twenty blobs.

That distinction is worth stating precisely, because "git deduplicates" gets misremembered as "git
handles big files fine". Dedup is across *identical content*, never across *versions*.

### Measuring: the two commands that matter
```bash
git count-objects -vH
```
```
count: 4873              ← loose objects (one zlib file each)
size: 26.19 MiB
in-pack: 25975           ← packed objects
packs: 2
size-pack: 63.66 MiB     ← 5× more objects in ~2.4× the space
```

Loose objects are written one-per-file; `git gc` packs them with delta compression. Real numbers from
this repository: **25,975 packed objects in 63.66 MiB** versus **4,873 loose in 26.19 MiB** — packed
storage is roughly **5× denser per object** here.

And the command that finds the actual culprits:

```bash
git rev-list --objects --all \
  | git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' \
  | awk '$1=="blob"' | sort -k3 -n | tail -20
```

Read it as a pipeline: list every object with its path, ask git for each one's type and size in bulk,
keep the blobs, sort by size. `--batch-check` matters — it reads in one process instead of spawning
`cat-file` thousands of times.

### `git gc` — what it actually does
```bash
git gc                      # pack loose objects, prune unreachable ones past their grace period
git gc --aggressive          # recompute deltas from scratch — slow, occasionally worth it
git gc --prune=now           # ignore grace periods (see the warning below)
```

Git runs `gc --auto` automatically during some operations, so most repositories stay reasonably packed
without intervention.

**The grace-period warning:** unreachable objects survive ~2 weeks by default, and that is what makes
[reflog](16_Reflog.md) recovery work. `--prune=now` discards that safety net immediately. Use it only
when you *intend* to destroy recovery — typically right after a deliberate history rewrite
([Chapter 34](34_Rewriting_History.md)).

### Clone strategies: three ways to not download everything
| Strategy | Command | You get | You lose |
|---|---|---|---|
| **Shallow** | `git clone --depth=1` | the tip only | history: `log`, `blame`, `bisect`, merge bases |
| **Partial (blobless)** | `git clone --filter=blob:none` | all commits+trees, blobs on demand | offline access to old file contents |
| **Sparse** | `git sparse-checkout set <dir>` | full history, fewer **files** on disk | files outside the cone |

These solve *different* problems, and conflating them is the common error:

- **Shallow** = "I don't need history." Great for a build; terrible for development, because a shallow
  clone cannot compute a merge base.
- **Partial/blobless** = "I need history but not every old file version." The modern best default for a
  large repo — `git log` works fully, and blobs are fetched when you actually ask for one.
- **Sparse** = "the repo has more projects than I work on." The monorepo mitigation
  ([Chapter 36](36_Monorepo_Submodules_Subtrees.md)).

They compose: `--filter=blob:none` plus `sparse-checkout` is the standard large-monorepo setup.

### Git LFS — what it really is
**Large File Storage** replaces a large file in git with a small **pointer file**, and stores the real
bytes on a separate server.

```
# what git actually tracks:
version https://git-lfs.github.com/spec/v1
oid sha256:4d7a214614ab2935c943f9e0ff69d22eadbb8f32b1258daaa5e2ca24d17e2393
size 12345
```

```bash
git lfs install
git lfs track "*.psd"       # writes a .gitattributes rule
git add .gitattributes      # ← the rule must be committed, or it protects nobody
```

**Buys:** the repository stays small; large files are fetched only when checked out.

**Costs, all real:**

- **Every collaborator needs `git-lfs` installed.** Without it they get pointer files instead of
  content — confusing rather than broken.
- **Storage and bandwidth are metered.** GitHub Free includes 1 GB storage and 1 GB/month bandwidth;
  beyond that it is a paid add-on. On this project's zero-cost constraint, LFS is effectively a small
  free allowance, not a solution.
- **It does not fix existing history.** Migrating requires `git lfs migrate import`, which is a history
  rewrite with all of [Chapter 34](34_Rewriting_History.md)'s consequences.
- **CI must fetch LFS objects**, costing time and bandwidth per run.

**Honest summary:** LFS is right when you genuinely must version large binaries (design files, game
assets). It is not a fix for having committed things that should never have been in git — and it is not
free at scale.

### What makes git slow, and what to do
| Symptom | Cause | Fix |
|---|---|---|
| slow `clone` | large history / big blobs | `--filter=blob:none`, or `--depth=1` for CI |
| slow `status` | huge working tree (file **count**) | `core.fsmonitor true`, `sparse-checkout` |
| slow `log` | no commit-graph | `git commit-graph write --reachable` |
| slow `checkout` | many files to write | `sparse-checkout` |
| slow everything | thousands of loose objects | `git gc` |
| slow `push`/`fetch` | large new objects | do not commit binaries |

> 💡 **Samjho aise:** Git **kuch bhulta nahi**. File aaj delete kar do — kal ke page pe wo likhi hai,
> aur uska poora content `.git` mein pada rehta hai. Isliye *"200 MB ki file hata di, repo halka ho
> jaayega"* galat hai. Kuch nahi hota.
>
> Aur badi baat: **text sasta hai, binary mehenga.** Text ka ek line badla toh git sirf farak rakhta
> hai. Binary ka ek pixel badla toh **poori nayi copy** — 20 baar edit kiya 10 MB ki image ko, 200 MB
> ho gaya.
>
> Log kehte hain "git dedup karta hai" — sahi hai, par **ek jaisi cheez ka**, *versions ka nahi*. Ek
> hi file ki 10 copy = 10 MB. Ek file ke 20 version = 200 MB. Yahi farak hai.
>
> Ilaaj se pehle **naap lo**: `git count-objects -vH`, aur sabse badi blob dhoondho.

# Real World Example (this repo)
Measured, not estimated:

```bash
git count-objects -vH
```
```
count: 4873            size: 26.19 MiB       ← loose
in-pack: 25975         size-pack: 63.66 MiB  ← packed, 2 packs
```

**`.git` is 97 MB** *(2026-08-03 snapshot — [why your number differs](00_COURSE_OVERVIEW.md#about-the-numbers-in-this-course--read-this-once))* while the tracked working tree is a few MB of Python, templates and markdown. The
gap is history — and specifically, history that includes things which never belonged in git.

### The two real offenders, both from the sibling project
**1. 2,952 `node_modules` files.** Tracked in `Django_app/myproject/node_modules/` until they were
untracked in this session. That is 27 MB of third-party JavaScript, in thousands of small files, all of
it reinstallable from a lockfile — the textbook example of what not to commit.

**2. Two `pg_dump` files**, ~86 KB combined ([Chapter 33](33_Secrets_And_Leaks.md)).

Both were untracked together:

```
2,954 files untracked · 331,748 deletions · 0 bytes lost on disk
```

### The lesson that matters: untracking did NOT shrink `.git`
This is the whole chapter in one observation. `git rm --cached` removed those files from the **index**
and from the current tree. It did **not** remove a single object from `.git/objects`, because every
earlier commit's tree still references those blobs.

So the repository is exactly as large as it was. What changed:

- **Future** commits no longer carry them.
- The **class** of bug is closed — a root `.gitignore` now blocks `node_modules/`, `*.sql`, `*.dump`
  in every sibling directory ([Chapter 36](36_Monorepo_Submodules_Subtrees.md)).

Shrinking `.git` would require `git filter-repo` plus a force-push — and that was **deliberately
declined** on evidence ([Chapter 34](34_Rewriting_History.md)). Note *why* size was not an argument:
**97 MB is completely fine.** Clones are fast, `git status` is instant, CI clones in seconds. The
untracking was for hygiene and security, not performance.

That is the honest engineering position: measure first, and do not pay a rewrite's cost for a problem
you do not have.

### CI's deliberate choice: full history, not shallow
`.github/workflows/ci.yml` sets:

```yaml
- uses: actions/checkout@v4
  with:
    fetch-depth: 0        # the ratchet needs history to find the merge base
```

`fetch-depth: 0` means **full history** — the opposite of the usual CI optimisation. It is required
because the design-system ratchet computes
`git merge-base origin/<base> HEAD` ([Chapter 28](28_CI_With_GitHub_Actions.md)), and a shallow clone
has no merge base to find.

**This is the shallow-clone trade-off, made concrete:** `--depth=1` would clone faster and break the
lint job. At 97 MB the full clone costs a few seconds, so the trade is trivially worth it. On a 5 GB
repository it would be a genuine engineering decision.

# Visual Diagram
```
  WHY DELETING DOES NOT SHRINK ANYTHING
  ─────────────────────────────────────
   commit A ──► tree ──► blob(node_modules/*, 27 MB)   ← still reachable
   commit B ──► tree ──► blob(same)
   commit C ──► tree            ← git rm --cached: tree omits them
                    ▲
        .git/objects UNCHANGED. History is append-only.
        Only `filter-repo` + force-push removes them (ch 34).

  THIS REPO, MEASURED
  ───────────────────
   .git                97 MB
   loose               4,873 objects   26.19 MiB
   packed             25,975 objects   63.66 MiB   ← ~5× denser per object
   untracked in session 2,954 files (2,952 node_modules + 2 dumps)
                        331,748 deletions · 0 bytes lost on disk
   .git after           97 MB  ← UNCHANGED. That is the lesson.
   verdict              97 MB is FINE. No rewrite. Hygiene ≠ performance.

  TEXT vs BINARY
  ──────────────
   .py  edit one line   ──► tiny delta
   .png edit one pixel  ──► WHOLE NEW BLOB (already compressed ⇒ no delta)
   20 versions × 10 MB binary ≈ 200 MB, forever
   dedup helps IDENTICAL content, never VERSIONS

  CLONE STRATEGIES — different problems
  ─────────────────────────────────────
   --depth=1                tip only        ✗ no log/blame/bisect/MERGE BASE
   --filter=blob:none       all commits,    ✓ history works; blobs on demand
                            blobs lazily        ← best default for a big repo
   sparse-checkout <dir>    fewer FILES     ✓ full history, smaller worktree
   compose the last two for a large monorepo

   THIS REPO'S CI: fetch-depth: 0 (FULL history) — the ratchet needs a merge base.
   --depth=1 would be faster and would BREAK the lint job.
```

# Practical — measure before you optimise
```bash
cd /home/tech/umesh-personal

# 1. how big, and how well packed?
git count-objects -vH
du -sh .git

# 2. THE command: the biggest blobs in all history
git rev-list --objects --all \
  | git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' \
  | awk '$1=="blob"' | sort -k3 -n | tail -20

# 3. which PATHS have the most objects? (churn, not just size)
git rev-list --objects --all | awk '{print $2}' | grep -v '^$' \
  | sed 's|/[^/]*$||' | sort | uniq -c | sort -rn | head -10

# 4. working tree vs history
git ls-files | wc -l                 # tracked files now
du -sh --exclude=.git .              # working tree size
du -sh .git                          # history size

# 5. pack it and compare
git gc
git count-objects -vH

# 6. speed up ancestry queries (log, merge-base)
git commit-graph write --reachable
git config --global fetch.writeCommitGraph true

# 7. clone strategies — try each on a /tmp copy
git clone --depth=1 . /tmp/shallow            # fast, no history
cd /tmp/shallow && git log --oneline | wc -l  # 1 — and bisect/blame are useless
cd - && git clone --filter=blob:none --no-local . /tmp/blobless
git clone --no-local . /tmp/sparse && cd /tmp/sparse \
  && git sparse-checkout init --cone \
  && git sparse-checkout set django_inventory \
  && git ls-files | wc -l                     # fewer FILES, full history

# 8. is anything large tracked RIGHT NOW that should not be?
git ls-files | xargs -r du -h 2>/dev/null | sort -h | tail -10
git ls-files -i -c --exclude-standard          # tracked BUT ignored ⇒ slipped a rule
```

Command 2 is the one to memorise. It answers "what is actually making this repo big" in one line, and
the answer is frequently a file somebody deleted long ago.

# Production Walkthrough
1. **Measure first.** `git count-objects -vH` and the biggest-blob query. Do not optimise a number you
   have not looked at.
2. **Decide whether you actually have a problem.** 97 MB is fine. 5 GB is not. There is a very wide
   middle where the correct action is nothing.
3. **Prevent the next one** — this is where the value is. Root-level `.gitignore` entries for
   `node_modules/`, `*.sql`, `*.dump`, build output, media
   ([Chapter 07](07_Gitignore.md)).
4. **Untrack what slipped in**: `git rm --cached` plus the ignore rule, committed together. Understand
   that this stops future growth and reclaims **nothing**.
5. **Only then consider a rewrite.** `filter-repo` shrinks history, at the cost of new hashes, a
   force-push and every clone re-cloned ([Chapter 34](34_Rewriting_History.md)).
6. **For genuinely large binaries you must version**, evaluate LFS — and budget for storage and
   bandwidth, because it is metered.
7. **Tune clones per consumer.** CI that only builds can use `--depth=1`; CI that needs a merge base
   (this project's) needs `fetch-depth: 0`. Developers on a huge repo want
   `--filter=blob:none`.
8. **Run `git gc`** occasionally after heavy local churn.

# Debugging Guide

| Symptom | Cause | Fix |
|---|---|---|
| Deleted a huge file; `.git` unchanged | blobs are still reachable from old commits | `filter-repo` + force-push, or accept it ([Ch 34](34_Rewriting_History.md)) |
| `.git` far larger than the working tree | every version of every file, forever | run the biggest-blob query and look |
| `git status` slow | large working tree (file **count**) | `core.fsmonitor true`; `sparse-checkout` |
| `git log` slow on a big history | no commit-graph | `git commit-graph write --reachable` |
| Clone very slow | big history and/or big blobs | `--filter=blob:none`; `--depth=1` for build-only CI |
| `git gc` freed nothing | objects still reachable, or within the grace period | check reachability; `--prune=now` only if you mean it |
| Shallow clone breaks CI lint | no merge base in a shallow clone | `fetch-depth: 0` — exactly this project's case |
| LFS files show as text pointers | `git-lfs` not installed on that machine | `git lfs install && git lfs pull` |
| LFS quota exceeded | storage/bandwidth are metered | prune old LFS objects, or reconsider LFS |
| Repo fine locally, slow in CI | CI clones from scratch every run | shallow or partial clone, plus caching |

# Performance Notes
- **This repo:** `.git` 97 MB · 4,873 loose (26.19 MiB) · **25,975 packed (63.66 MiB)** in 2 packs ⇒
  packed is ~5× denser per object.
- **Packing is why gc matters.** Thousands of loose objects mean thousands of file opens for operations
  that touch many objects.
- **`git status` scales with tracked file **count**, not repo size.** ~2,400 files here is trivial;
  `core.fsmonitor true` is the fix at 100k+.
- **The commit-graph** caches parent relationships and generation numbers, dramatically speeding
  ancestry queries — `log --graph`, `merge-base`, `bisect`. Modern git writes it automatically; you can
  force it.
- **`--filter=blob:none` is usually the best big-repo default**: full commit and tree history, blobs
  fetched on demand, so `git log` is complete while the initial transfer is a fraction.
- **`--depth=1` is a false economy for development** — no merge base means no rebase, no meaningful
  diff against a base branch, and no bisect.
- **CI here deliberately uses `fetch-depth: 0`** because the ratchet needs a merge base; at 97 MB the
  full clone is a few seconds.
- **`gc --aggressive` recomputes every delta** — slow, and rarely worth it outside a one-off cleanup.

# Security Considerations
- **A large file in history often *is* the security problem.** Database dumps are the classic case:
  large, permanent, and full of user data ([Chapter 33](33_Secrets_And_Leaks.md)).
- **Untracking reclaims nothing and hides nothing.** The blob remains readable via
  `git show <old-commit>:<path>`. Treat the content as disclosed.
- **`gc --prune=now` destroys reflog recovery.** That is sometimes the point after a rewrite, and a
  disaster otherwise ([Chapter 16](16_Reflog.md)).
- **Shallow clones hide history from audits.** Searching a shallow clone for a leaked secret will find
  nothing and prove nothing.
- **LFS puts your data on a separate server.** For self-hosted LFS that is another system to secure;
  for hosted LFS it is another vendor holding your files.
- **`node_modules` in history is a supply-chain artefact frozen forever** — including versions with
  known CVEs, still present and still readable ([Chapter 32](32_Dependabot_And_Supply_Chain.md)).

# Architecture Decisions
- **Nothing large is committed by policy.** Root `.gitignore` blocks `node_modules/`, `*.sql`,
  `*.dump`, `*.sql.gz`, `db_backups/`, `backups/` — for **every** sibling project, present and future.
- **No history rewrite for the existing bloat.** 97 MB is comfortable; the untracking was for hygiene
  and security, and paying a rewrite's cost for a non-problem would be poor judgement
  ([Chapter 34](34_Rewriting_History.md)).
- **No Git LFS.** Nothing here genuinely needs versioned large binaries, and LFS storage/bandwidth are
  metered — which conflicts with this project's zero-cost constraint.
- **CI uses `fetch-depth: 0` deliberately**, accepting a slower clone because the design-system ratchet
  requires a real merge base. The trade-off is documented in the workflow itself.
- **`git rm --cached` rather than deletion**, so the owner's files survived while tracking stopped.
- **Media is a backup concern, not a git concern** — user uploads are backed up with the database and
  never committed (`deployment_course/28_Backups.md`).
- **Measure before optimising.** The decision not to act was made from `git count-objects -vH`, not
  from a feeling that the repo was big.

# Best Practices
- **Never commit binaries, generated output, dependencies or dumps.** Prevention is the only cheap fix.
- Put the ignore rules at the **repository root** in a monorepo
  ([Chapter 36](36_Monorepo_Submodules_Subtrees.md)).
- **Measure before optimising**: `git count-objects -vH` and the biggest-blob query.
- Accept that untracking stops growth and reclaims nothing.
- Prefer `--filter=blob:none` over `--depth=1` when you need history at all.
- Use `sparse-checkout` when a monorepo has more projects than you work on.
- Write the commit-graph on large repos; enable `core.fsmonitor` on large working trees.
- Run `git gc` after heavy local churn; reserve `--prune=now` for after a deliberate rewrite.
- If you adopt LFS, commit `.gitattributes` and tell everyone to install `git-lfs`.

# Beginner Mistakes
- **"I deleted the big file, so the repo will shrink"** → it will not. History is append-only.
- **Committing `node_modules`** → thousands of blobs, permanently. This repo carried **2,952**.
- **Committing a database dump** → large, permanent, and a data breach in one file.
- **`--depth=1` for development** → no merge base, so no rebase, no useful diff, no bisect.
- **Assuming dedup handles big files** → it dedupes *identical content*, not *versions*.
- **`gc --prune=now` casually** → destroys reflog recovery.
- **Reaching for LFS to fix existing history** → LFS does not retroactively fix anything; migration is
  a rewrite.
- **Optimising without measuring** → this repo's 97 MB needed no action at all.
- **Forgetting to commit `.gitattributes`** after `git lfs track` → the rule protects nobody.

# Interview Questions
- **Junior:** "You committed a 500 MB file and deleted it. Is the repo smaller?" — No. Deleting creates
  a new commit whose tree omits the file, but the blob is still reachable from every earlier commit, so
  it remains in `.git/objects`. Removing it requires rewriting history.
- **Mid:** "Why are binaries worse than text in git?" — Delta compression works on similarity. A
  one-line text edit stores a tiny delta; a one-pixel change in an already-compressed binary rewrites
  the whole byte stream, so each version is effectively a new full-size blob. Twenty versions of a
  10 MB image can be 200 MB, permanently.
- **Senior:** "`--depth=1` versus `--filter=blob:none`?" — Shallow truncates *history*: you get the tip
  and lose `log`, `blame`, `bisect` and — critically — merge bases, so rebasing and base-branch diffs
  break. Blobless keeps all commits and trees and fetches file contents on demand, so history
  operations work fully while the initial transfer is small. Shallow is for build-only CI; blobless is
  the better default for developers on a large repository. This project's CI actually needs
  `fetch-depth: 0` because its lint ratchet computes a merge base — a shallow clone would be faster and
  would break it.
- **Staff:** "A 4 GB repo, 30-minute clones, team blocked. What do you do?" — Measure before acting:
  `git count-objects -vH` plus the biggest-blob-by-size query, because the answer is usually a handful
  of paths and often files that were deleted years ago. Then split the work by urgency. Immediate
  relief needs no rewrite and no coordination — `--filter=blob:none` for developers and
  `sparse-checkout` if it is a monorepo, plus `--depth=1` for build-only CI jobs; that alone typically
  turns 30 minutes into minutes. Prevention comes next and is permanent: root-level ignore rules and,
  if large binaries are genuinely required, LFS with its metered storage costed honestly. A history
  rewrite is **last**, because it is the only option that imposes new hashes, a force-push, invalidated
  clones and forks, dangling tags and broken SHA references on everyone — so it needs to be worth that,
  and scheduled, not improvised. The judgement I would want to be explicit about is that shrinking
  history is often the *least* valuable of the three: this project untracked 2,954 files and `.git`
  stayed at 97 MB, and that was fine, because the goal was hygiene and the size was never actually
  hurting anyone.

### Why interviewers ask these — and the answer that separates levels
| Testing for | Weak answer | What lands |
|---|---|---|
| Do you know history is permanent? | "I deleted it, so it's gone." | The blob stays reachable from earlier commits; only a history rewrite removes it, and untracking reclaims nothing. |
| Do you know why binaries hurt? | "Binaries are big." | Delta compression fails on already-compressed data, so each version is a full new blob — and dedup covers identical content, not versions. |
| Can you triage without a rewrite? | "Run filter-repo." | Measure, then relieve with partial/sparse/shallow clones per consumer, prevent with root ignore rules, and rewrite last because it costs everyone. |

**The killer follow-up:** *"You untracked 3,000 files and `.git` didn't shrink at all. Is something wrong?"* — No, that is exactly correct behaviour: `git rm --cached` changes the index and the current tree, while every earlier commit still references those blobs. It stops future growth and closes the bug class; it reclaims nothing. Expecting a size change there means you have not internalised that history is append-only — which is the single most consequential fact about git storage.

# Revision Notes
- **Git never forgets.** Deleting a file ⇒ new tree without it; the **blob stays reachable** from older commits.
- **`git rm --cached` reclaims NOTHING.** It stops future growth and closes the class. Proven here: 2,954 files untracked, `.git` still 97 MB.
- **Text cheap (delta), binaries ruinous** (already compressed ⇒ whole new blob each version).
- **Dedup = identical content, NOT versions.** 10 copies of a 10 MB file = 10 MB; 20 versions = 200 MB.
- Measure: **`git count-objects -vH`** + the biggest-blob `rev-list | cat-file --batch-check` query.
- This repo: 4,873 loose / 26.19 MiB · **25,975 packed / 63.66 MiB** (~5× denser) · `.git` **97 MB** = fine.
- Clones: **`--depth=1`** (no history, **no merge base**) · **`--filter=blob:none`** (best big-repo default) · **`sparse-checkout`** (fewer files, full history).
- **This project's CI uses `fetch-depth: 0` on purpose** — the ratchet needs a merge base; `--depth=1` would break it.
- `gc` packs + prunes; **`--prune=now` destroys reflog recovery** — only after a deliberate rewrite.
- **LFS** = pointer in git, bytes elsewhere. Needs `git-lfs` everywhere, **metered** storage/bandwidth, does not fix existing history.

# Cheat Sheet
```bash
git count-objects -vH                  # loose vs packed, human sizes  ← start here
du -sh .git

# THE biggest-blobs query (memorise this one)
git rev-list --objects --all \
  | git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' \
  | awk '$1=="blob"' | sort -k3 -n | tail -20

git ls-files | wc -l                   # tracked file count (drives `status` speed)
git ls-files -i -c --exclude-standard  # tracked BUT ignored ⇒ slipped a rule

git gc                                 # pack loose objects
git gc --aggressive                    # recompute deltas (slow; one-off)
git gc --prune=now                     # ⚠ destroys reflog recovery
git commit-graph write --reachable     # faster log / merge-base / bisect
git config --global core.fsmonitor true       # faster status on huge worktrees
git config --global fetch.writeCommitGraph true

# clone strategies
git clone --depth=1 <url>              # build-only CI. NO merge base ⇒ breaks rebase/lint
git clone --filter=blob:none <url>     # ← best default for a large repo
git clone --filter=blob:none --sparse <url>
git sparse-checkout init --cone
git sparse-checkout set django_inventory
git sparse-checkout disable

# LFS (metered — budget for it)
git lfs install
git lfs track "*.psd" && git add .gitattributes   # the rule MUST be committed
git lfs ls-files
git lfs migrate import --include="*.psd"          # ⚠ this is a history rewrite (ch 34)
```

# My ERP Section

| Measurement | This repository |
|---|---|
| `.git` | **97 MB** |
| Loose objects | **4,873** — 26.19 MiB |
| Packed objects | **25,975** — 63.66 MiB in **2** packs (~5× denser per object) |
| Tracked files | ~2,400 (so `git status` is instant) |
| Offender 1 | **2,952 `node_modules` files** in `Django_app/myproject/` (27 MB of reinstallable JS) |
| Offender 2 | 2 `pg_dump` files, ~86 KB ([Ch 33](33_Secrets_And_Leaks.md)) |
| Action taken | `git rm --cached` — **2,954 files**, 331,748 deletions, **0 bytes lost on disk** |
| **Result on `.git`** | **UNCHANGED at 97 MB** — untracking reclaims nothing. The chapter's central lesson, measured |
| Rewrite? | **No.** 97 MB is comfortable; the untracking was hygiene + security, not performance ([Ch 34](34_Rewriting_History.md)) |
| Prevention | root `.gitignore`: `node_modules/`, `*.sql`, `*.dump`, `*.sql.gz`, `db_backups/`, `backups/` — covers **every** sibling |
| LFS | **not used** — nothing needs versioned large binaries, and LFS is metered (conflicts with the zero-cost constraint) |
| CI clone depth | **`fetch-depth: 0` (full history)** — deliberate: the design-system ratchet needs `git merge-base`, and `--depth=1` would break the lint job |

# Practice Tasks
1. Run `git count-objects -vH` here. Compute the bytes-per-object for loose versus packed and confirm
   packed is denser.
2. Run the biggest-blob query. Identify the largest file in this history and say whether it should ever
   have been committed.
3. Prove the central lesson yourself: in a throwaway repo, commit a 10 MB file, note `.git` size,
   `git rm --cached` it and commit, then check `.git` again. Unchanged.
4. In that same repo, run `git filter-repo --invert-paths --path bigfile`, then
   `git reflog expire --expire=now --all && git gc --prune=now`. **Now** it shrinks. That is the
   difference.
5. Clone this repo three ways into `/tmp` — `--depth=1`, `--filter=blob:none`, and sparse. Then try
   `git log --oneline | wc -l` and `git merge-base origin/main HEAD` in each. Watch shallow fail.
6. Read the `fetch-depth: 0` line in `ci.yml` and explain, in one sentence, why the usual CI
   optimisation is wrong here.

# Homework
- Run the biggest-blob query on every repository you own. Anything above a megabyte that is not source
  deserves an explanation.
- Take the largest repo you have access to and set up `--filter=blob:none` plus `sparse-checkout` for
  just the part you work on. Time the clone before and after.
- Compute what LFS would cost you: total size of large binaries × storage rate, plus bandwidth per
  clone per developer per month. Then decide whether it is worth it.
- Read `git help gc` on `gc.reflogExpireUnreachable` and `gc.pruneExpire`, and write down what you
  would lose by shortening them. That is the reflog-versus-space trade-off, explicitly.

# Further Reading & Live Resources
- [Pro Git — Packfiles](https://git-scm.com/book/en/v2/Git-Internals-Packfiles) — how delta compression actually works; free
- [Pro Git — Maintenance and Data Recovery](https://git-scm.com/book/en/v2/Git-Internals-Maintenance-and-Data-Recovery) — gc, prune, and the "removing objects" section
- [GitHub Blog — Get up to speed with partial clone and shallow clone](https://github.blog/2020-12-21-get-up-to-speed-with-partial-clone-and-shallow-clone/) — the clearest explanation of the clone strategies
- [git-sparse-checkout](https://git-scm.com/docs/git-sparse-checkout) — cone mode and its limits
- [Git LFS](https://git-lfs.com/) — plus [GitHub's LFS billing](https://docs.github.com/en/billing/managing-billing-for-git-large-file-storage/about-billing-for-git-large-file-storage), which is the part that decides it
- [git-commit-graph](https://git-scm.com/docs/git-commit-graph) — why ancestry queries get fast
- [Scaling monorepo maintenance](https://github.blog/2021-04-29-scaling-monorepo-maintenance/) — GitHub's own account of running very large repositories
