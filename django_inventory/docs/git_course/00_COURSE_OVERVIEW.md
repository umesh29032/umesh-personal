---
id: git-course-00-course-overview
type: lesson
status: active
owner: handwritten
scope: git, GitHub, engineering workflow — this repo's own history, hooks and CI
anchors: CONTRIBUTING.md, git-hooks/pre-push, git-hooks/commit-msg, .github/workflows/ci.yml, .github/CODEOWNERS, .gitignore
verified: 2026-08-03
---

# Git & GitHub From Zero — the workflow, not just the commands

> **Who this is for:** me (Umesh), who has been using git for months by copying three
> commands — `add`, `commit`, `push` — without knowing what any of them actually do.
> **Promise:** if I read only these 40 chapters, I can work the way a team at a real
> engineering company works: branch, commit properly, open a reviewable PR, pass CI,
> release with a tag, and recover from any mistake I make along the way.
> **Rule of this course:** never a generic example. Every chapter is taught on **this
> repository** — its real history, its real hooks, its real CI, and its real incidents,
> including the day two database dumps were found sitting in public git history.

---

> 💡 **Samjho aise:** Git ko log "3 command ka jaadu" samajhte hain — `add`, `commit`,
> `push`. Wo galat nahi hai, par wo **gaadi chalana** hai bina ye jaane ki brake kaam
> kaise karta hai. Ye course brake kholta hai. Pehle 8 chapter mein samajh aayega ki
> git andar se **kya** hai; phir branch, phir team ka tareeka, phir galti se wapas
> aana. Ek hi din mein poora mat padho — order mein padho, aur har command **chala ke**
> dekho. Padhna seekhna nahi hai; chalana seekhna hai.

## How to use this folder

1. Read **in order, 01 → 40**. This course is deliberately sequential: chapter 09
   ("what a branch really is") only makes sense after chapter 05 ("how git stores
   everything"). Skipping ahead is how people end up afraid of `rebase`.
2. Every chapter follows the **same 21-part format** (below), so you always know where to
   look — the commands are in **Cheat Sheet**, the "I broke it" answers are in **Debugging
   Guide**.
3. **Run every command.** Reading git is useless; git is muscle memory. Each chapter's
   **Practice Tasks** are safe to run on a throwaway repo — make one:
   `mkdir /tmp/gitlab && cd /tmp/gitlab && git init`.
4. When you have actually broken something and need help *now*, go straight to
   **[39 — Disaster Playbook](39_Disaster_Playbook.md)** and
   **[16 — Reflog](16_Reflog.md)**. Almost nothing in git is truly lost.
5. The rules this course teaches are enforced in this repo by
   **[CONTRIBUTING.md](../../../CONTRIBUTING.md)**. The course is the *why*; that file is
   the *law*.

## About the numbers in this course — read this once

Every figure here was **measured against this repository**, not invented. That is the
course's main strength and its one maintenance hazard, so it is worth being explicit about
which numbers are permanent and which are snapshots.

**Permanent facts.** These are frozen history and will never change:

| Fact | Value |
|---|---|
| PR #15's size when it merged | **289 commits**, ~2,100 files, 336,372 insertions |
| The merge commit it produced | `83a144ba`, with two parent lines |
| Its feature-branch parent (`^2`) | `7fe2bb0e` |
| The dump-cleanup commit | `42a2ecc4` — **2,954** files untracked, 331,748 deletions, 0 bytes lost |
| Release tag | `erp-v1.0.0` = `90c1f2f3` |
| The leaked dumps' contents | 3 emails · 2 × `pbkdf2_sha256$1000000$` · OAuth tables empty · sessions expired |
| `printf 'blob 10\0hello git\n' \| sha1sum` | `8d0e41234f24b6da002d962a26c2495ea16a425f` — arithmetic, true forever |

**Snapshots, measured 2026-08-03.** These move whenever anyone commits, pushes or runs
`git gc`. They are quoted because a concrete number teaches far better than "some commits",
**not** because the digit itself matters:

| Snapshot | Value on 2026-08-03 | Re-derive it yourself |
|---|---|---|
| local `main` behind the remote | 295 | `git rev-list --left-right --count main...origin/main` |
| stale-`main` divergence | 296 | `git rev-list --count main..new_flask_app` |
| the honest divergence | 1 | `git rev-list --count origin/main..new_flask_app` |
| `.git` size | 97 MB | `du -sh .git` |
| loose / packed objects | 4,873 / 25,975 | `git count-objects -vH` |
| test battery | 2,035 tests / 422 s | `manage.py test <14 apps>` |

**If your numbers differ, nothing is wrong — that is the subject of
[Chapter 18](18_Remotes.md).** Refs move; a snapshot is a photograph, not a promise. The
*lesson* attached to each number is what you are meant to keep:

- **296 versus 1** is not about 296. It is that a range query answers the question you
  *actually asked* — and `main` is not `origin/main`.
- **97 MB unchanged after untracking 2,954 files** is not about 97. It is that history is
  append-only, so `git rm --cached` reclaims nothing.
- **289 commits** is not about 289. It is that a branch left to live becomes unreviewable.

> 💡 **Samjho aise:** yahaan ke number **naapey gaye** hain, banaye nahi. Par kuch number
> **pakke** hain (PR #15 ki 289 commits — wo itihaas hai, kabhi nahi badlega) aur kuch
> **aaj ki photo** hain (296, 97 MB — koi bhi commit karega toh badal jaayenge).
>
> Tumhara number alag aaye? **Kuch galat nahi hai** — wahi to Chapter 18 ka poora sabaq
> hai. Number yaad rakhne ki cheez nahi; uske saath juda **sabaq** yaad rakho.

## The five parts

| Part | Chapters | What you get |
|---|---|---|
| **1. Foundations** | 01–08 | What git *is* — the three trees, objects, the commit graph, `.gitignore`, reading history. The mental model everything else rests on. |
| **2. Branching** | 09–17 | Branches, merging, conflicts, rebase, interactive rebase, the three undo verbs, reflog, stash. Where most people's confidence collapses — and where this course spends the most time. |
| **3. Collaboration** | 18–24 | Remotes, push/fetch/pull, forks, Pull Requests, code review, CODEOWNERS, and choosing a branching strategy. |
| **4. Discipline** | 25–33 | Conventional Commits, hooks, CI, SemVer, CHANGELOG, signed commits, Dependabot, and what to do when a secret leaks. The parts that make a repo *professional* rather than merely working. |
| **5. Recovery & depth** | 34–40 | Rewriting history safely, bisect, monorepo vs submodules, large files, git internals by hand, a disaster playbook, and the whole workflow assembled. |

## All 40 chapters

### Part 1 — Foundations
| # | Chapter | The one thing it teaches |
|---|---|---|
| 01 | [What Version Control Is](01_What_Version_Control_Is.md) | Why `final_v2_FINAL.zip` is a bug, not a habit |
| 02 | [Installing & Configuring Git](02_Install_And_Configure.md) | Identity, SSH keys, and why this repo uses a `github-personal` host alias |
| 03 | [The Three Trees](03_The_Three_Trees.md) | Working directory vs index vs HEAD — the model that explains every command |
| 04 | [Your First Repository](04_Your_First_Repository.md) | `init`, `status`, `add`, `commit` — and what each one really moves |
| 05 | [How Git Stores Everything](05_How_Git_Stores_Everything.md) | Blobs, trees, commits, hashes. Git is a content-addressed database |
| 06 | [The Commit Graph](06_The_Commit_Graph.md) | History is a graph, not a line — the key to merge and rebase |
| 07 | [.gitignore](07_Gitignore.md) | Code in, data out — and the monorepo scoping bug that let two dumps in |
| 08 | [Reading History](08_Reading_History.md) | `log`, `show`, `diff`, `blame` — becoming an archaeologist of your own repo |

### Part 2 — Branching
| # | Chapter | The one thing it teaches |
|---|---|---|
| 09 | [What a Branch Really Is](09_What_A_Branch_Really_Is.md) | A branch is a 41-byte file containing a hash. That's all |
| 10 | [Creating & Switching Branches](10_Creating_And_Switching_Branches.md) | `switch` vs `checkout`, and what "detached HEAD" means |
| 11 | [Merging](11_Merging.md) | Fast-forward vs three-way, and when a merge commit appears |
| 12 | [Merge Conflicts](12_Merge_Conflicts.md) | Reading the markers, resolving properly, and never panicking |
| 13 | [Rebase](13_Rebase.md) | Replaying commits, and the golden rule of rebase |
| 14 | [Interactive Rebase](14_Interactive_Rebase.md) | squash, fixup, reword, drop — cleaning history before review |
| 15 | [Undo: reset vs revert vs restore](15_Undo_Reset_Revert_Restore.md) | Three verbs, three different scopes. Which one is safe when |
| 16 | [Reflog — the time machine](16_Reflog.md) | Why "I lost my commits" is almost always false |
| 17 | [Stash & Worktrees](17_Stash_And_Worktrees.md) | Switching context without committing half-work |

### Part 3 — Collaboration
| # | Chapter | The one thing it teaches |
|---|---|---|
| 18 | [Remotes](18_Remotes.md) | `origin` vs `upstream`, and what a remote actually is |
| 19 | [Push, Fetch & Pull](19_Push_Fetch_Pull.md) | Why `fetch` is safe, `pull` is two commands, and `--force-with-lease` exists |
| 20 | [Forks & the Fork-Based Flow](20_Forks_And_The_Fork_Flow.md) | How this repo gives a collaborator PR rights but not merge rights, for free |
| 21 | [Pull Requests](21_Pull_Requests.md) | The unit of change at every real company |
| 22 | [Code Review](22_Code_Review.md) | Reviewing means co-signing. What to actually look for |
| 23 | [CODEOWNERS & PR Templates](23_CODEOWNERS_And_Templates.md) | Encoding "who must look at this" into the repo |
| 24 | [Branching Strategies](24_Branching_Strategies.md) | trunk-based vs GitHub Flow vs git-flow — and why we chose what we chose |

### Part 4 — Discipline
| # | Chapter | The one thing it teaches |
|---|---|---|
| 25 | [Conventional Commits](25_Conventional_Commits.md) | A message format that generates your changelog and your version number |
| 26 | [Pre-commit Hooks](26_Pre_Commit_Hooks.md) | Catching lint and design-system drift before it reaches a reviewer |
| 27 | [Pre-push Protection](27_Pre_Push_Protection.md) | Replacing GitHub's *paid* branch protection with a free hook — honestly |
| 28 | [CI with GitHub Actions](28_CI_With_GitHub_Actions.md) | The 4-job gate on this repo, and how to not burn free minutes |
| 29 | [Semantic Versioning & Tags](29_Semantic_Versioning_And_Tags.md) | What `erp-v1.0.0` promises, and annotated vs lightweight tags |
| 30 | [CHANGELOG](30_Changelog.md) | Derived from commits, never written from memory |
| 31 | [Signed Commits](31_Signed_Commits.md) | Proving *you* wrote it — free, and mostly unknown |
| 32 | [Dependabot & Supply Chain](32_Dependabot_And_Supply_Chain.md) | A pin is a decision to stay behind until someone acts |
| 33 | [Secrets & Leaks](33_Secrets_And_Leaks.md) | The real dump incident in this repo, start to finish |

### Part 5 — Recovery & depth
| # | Chapter | The one thing it teaches |
|---|---|---|
| 34 | [Rewriting History Safely](34_Rewriting_History.md) | `filter-repo`, force-push-with-lease, and when the answer is "don't" |
| 35 | [Bisect](35_Bisect.md) | Binary-searching 289 commits to find the one that broke it |
| 36 | [Monorepo, Submodules & Subtrees](36_Monorepo_Submodules_Subtrees.md) | Why this repo is a monorepo, and what that costs |
| 37 | [Large Files & Repo Performance](37_Large_Files_And_Performance.md) | Why git never forgets, and what that does to clone time |
| 38 | [Git Internals, Hands-On](38_Git_Internals_Hands_On.md) | Building a commit by hand with plumbing commands |
| 39 | [Disaster Playbook](39_Disaster_Playbook.md) | "I broke main / lost commits / force-pushed" — the recovery recipes |
| 40 | [The Workflow, Assembled](40_The_Workflow_Assembled.md) | Every piece, working together, as one rulebook |

## The standard chapter format (all 21 headings, every file)

Same contract as the [SQL](../sql_course/00_COURSE_OVERVIEW.md) and
[Deployment](../deployment_course/00_COURSE_OVERVIEW.md) courses, so all three read alike:

**Learning Objectives · Purpose · The Problem · Theory · Real World Example · Visual
Diagram · Practical · Production Walkthrough · Debugging Guide · Performance Notes ·
Security Considerations · Architecture Decisions · Best Practices · Beginner Mistakes ·
Interview Questions · Revision Notes · Cheat Sheet · My ERP · Practice Tasks · Homework ·
Further Reading**

The contract is **test-pinned** (`config/learning/tests/test_learning.py`): if a chapter
loses a section, the test suite fails. That is deliberate — this project has three times
written content that the platform then silently failed to show, and a promise nobody
checks is not a promise.

## What makes this course different from every git tutorial

1. **It is honest about money.** GitHub's server-side branch protection and CODEOWNERS
   auto-assignment are **paid features on private repositories**. Most tutorials tell you
   to "just enable branch protection". This course tells you the truth and then shows the
   free path that actually works — and admits where the free path is weaker.
2. **It teaches from a real incident.** Chapter 33 walks the actual day two `pg_dump`
   files were found in this repo's public history: what leaked, what did not, how it was
   audited, why history was *deliberately not* rewritten.
3. **It teaches recovery as a first-class skill**, not an appendix. Chapters 15, 16, 34
   and 39 exist because fear of git is really fear of being unable to undo.
4. **Every claim is checkable.** Real paths, real commit hashes, real command output from
   this repository.

## Related

- **The rules:** [CONTRIBUTING.md](../../../CONTRIBUTING.md) — branch naming, commit
  format, PR flow, review standard, release process, onboarding
- **The hooks:** `git-hooks/pre-push`, `git-hooks/commit-msg`, `git-hooks/install.sh`
- **The CI:** `.github/workflows/ci.yml`
- **Sibling courses:** [SQL & PostgreSQL From Zero](../sql_course/00_COURSE_OVERVIEW.md) ·
  [Deployment From Zero](../deployment_course/00_COURSE_OVERVIEW.md)
- **The platform:** [docs/apps/learning/GUIDE.md](../apps/learning/GUIDE.md)
