---
id: git-course-08-reading-history
type: lesson
status: active
owner: handwritten
scope: git, version control — interrogating an existing repository with log, show and blame
anchors: django_inventory/config/expense/services/adda_settlement_service.py, django_inventory/.gitignore, CONTRIBUTING.md
verified: 2026-08-03
---

# 08 — Reading History (git log, show, blame — becoming an archaeologist)

> Part of [Git Course](00_COURSE_OVERVIEW.md). Prev: [07 — .gitignore](07_Gitignore.md). Next: [09 — What a Branch Really Is](09_What_A_Branch_Really_Is.md).

# Learning Objectives
By the end of this chapter you can:
- explain what `git log` actually *does* — a graph traversal, not a list — and shape its output with `--oneline`, `--graph` and `--format`
- narrow history with the five sieves: count, time, person, message, shape (and `--first-parent` to read only merges)
- find the commit that introduced or removed a specific **string** using the pickaxe (`-S`), and say how it differs from `-G` and from `grep`
- read a single file's biography with `git log -- path`, `--follow` and `git show <rev>:<path>`
- use `git blame` correctly, including why its answer is a *starting point* and not a verdict
- translate `HEAD~3` and `HEAD^2` without guessing, and read `A..B` vs `A...B`

# Purpose
Writing history is one skill; **reading** it is the one that pays. Most of your career is spent in code you did not write, asking "why is this line here?" and "when did this break?". Git already stores the answer — this chapter teaches the four tools (`log`, `show`, `blame`, `shortlog`) that get it out, using real commits from this repository.

# The Problem
A worker's earning got dated to the wrong day. Somewhere in **324 commits** across 14 Django apps, someone changed a date calculation. You do not know the file, the author or the month. `grep` can only tell you what the code says **today** — and today's code is correct, because the fix already landed. The evidence you need is *between* two versions, which is precisely what git stores and grep cannot see.

Without history-reading skills, your options are: ask someone (they left), read every commit (324 of them), or guess. With them, this is three commands and about ninety seconds. That gap is the whole chapter.

# Theory (from zero)

### What `git log` actually does
A commit stores a pointer to its **parent** ([Ch 06](06_The_Commit_Graph.md)). `git log` starts at a commit — `HEAD` by default, meaning "where I am now" — and **walks backwards along parent pointers**, printing each commit it reaches. That is the entire mechanism. Two consequences you must internalise:

- **`git log` shows only what is *reachable* from where you start.** A commit on another branch is invisible until you say `git log <that-branch>` or `git log --all`. "It's not in the log" almost never means "it does not exist".
- **Order is topological, not chronological.** Dates come from the commit object and a wrong system clock, or a rebase, can make them non-monotonic. Never treat log order as proof of time.

The default output per commit is: full hash, `Author:` (name + email), `Date:`, then the indented message.

**Author vs committer** — the confusing pair. The **author** wrote the change; the **committer** created this commit object. They differ after a rebase, cherry-pick or applied patch: the author stays the original writer, the committer becomes you. `git log` shows the *author* date by default, which is why a rebased commit can look "old" though it landed today. `--pretty=fuller` shows both.

### Shaping the output
`--oneline` = hash + subject per line · `--graph` = ASCII topology down the left · `--decorate` = which refs point here (on by default now) · `--all` = start the walk from **every** ref, not just `HEAD` · `--date=short` = `2026-08-03` · `--format='%h %ad %an %s'` = your own columns (`%h` short hash, `%an` author, `%ad` author date, `%s` subject, `%b` body, `%d` refs).

`git log --oneline --graph --all --decorate` is the "show me the whole shape of this repository" command. Learn it as one unit.

### The five sieves for selecting commits
You almost never want all of history. Combine these freely — they AND together.

1. **Count** — `-5` or `-n 5`.
2. **Time** — `--since='2026-07-20' --until='2026-07-25'`, or human forms like `--since='3 weeks ago'`.
3. **Person** — `--author='umesh29032'` (a regex over the author field), `--committer=` for the other one.
4. **Message** — `--grep='settlement'` (regex; `-i` for case-insensitive). Several `--grep` are OR-ed; `--all-match` requires all.
5. **Shape** — `--no-merges` hides merges, `--merges` shows only them, `--first-parent` follows only the *first* parent of each merge — on a PR-merge trunk that is **one line per feature**.

### Path limiting, and why `--` exists
```bash
git log -- django_inventory/.gitignore        # commits that touched this path
git log --oneline --follow -- path/to/file    # keep following it across renames
```
The bare `--` separates revisions from paths. Git cannot otherwise tell whether `main` means the branch or a file called `main`; `--` says "everything after this is a path". Type it whenever you pass a path.

`--follow` tracks a file through renames (git does not store renames — it *detects* them by content similarity, so `--follow` is a heuristic, and it accepts only one path). For a file that was **deleted**, add `--full-history`, otherwise history simplification can hide the commits you want.

### Content search — the pickaxe
The tool nobody teaches you and everybody needs. `-S'string'` = "which commits **changed the number of occurrences** of this string?" — i.e. added or removed it. `-G'regex'` = "which commits have a diff **containing** this regex?" — wider, includes moves. `--pickaxe-regex` makes `-S` treat its argument as a regex too.

**Name the confusion:** `grep` searches the working tree *now*. `git grep` searches one revision's tree. `git log -S` searches the **space between revisions** — the diffs. Only the last can find code that no longer exists. If a line was deleted two months ago, `-S` finds the deletion; nothing else will.

### Seeing the change itself
`--stat` per-file line counts · `--shortstat` just the totals · `--name-only` / `--name-status` filenames (with A-M-D) · `-p` the full diff · `git show <rev>` one commit's metadata + diff · **`git show <rev>:<path>`** the file's *entire contents* at that revision.

That last one answers "what did this file look like before the refactor?" — and, from [Ch 07](07_Gitignore.md), is why a deleted secret is still readable.

### Revision syntax — `~` versus `^`
The pair everyone gets wrong:

- `HEAD^` = the **first parent** of HEAD. `HEAD^2` = its **second** parent (only meaningful on a merge commit).
- `HEAD~` = the same as `HEAD^`. `HEAD~3` = "walk back 3 generations, always taking the first parent".

So `^` chooses **which** parent; `~` chooses **how far** back. `HEAD~2` is two commits back; `HEAD^2` is the other side of a merge. They mean completely different things.

**Ranges:**
- `A..B` = commits reachable from `B` but not `A` — "what's in B that isn't in A". This is what a PR diff means.
- `A...B` = the **symmetric difference**: commits in either but not both — "how have these two diverged".
- `git rev-list --left-right --count A...B` prints two numbers: behind and ahead.
- `HEAD@{1}`, `main@{yesterday}` = reflog-based, "where the ref pointed then" ([Ch 16](16_Reflog.md)).

> 💡 **Samjho aise:** `git log` ko samjho **register** — factory ke gate ka. Har entry mein: kaun aaya (author), kab (date), kyun (message). `--grep` = register mein naam se dhoondna. `-S` = register nahi, **maal ke andar** dhoondna — "yeh cheez kis din andar aayi ya bahar gayi?" Aur `git blame` = deewaar ke har eent pe likha naam — par yaad rakho, jisne aakhri baar plaster kiya uska naam dikhega, deewaar banane wale ka nahi.

### `git blame` — and its honest limit
`git blame <file>` prints, for **every line**, the commit, author and date that last touched it.

```bash
git blame -L 112,117 -- django_inventory/.gitignore   # only lines 112-117
git blame -w -- file        # -w ignores whitespace-only changes
git blame -C -- file        # -C also detects lines moved from other files
git blame --ignore-rev <hash> -- file    # skip a bulk-reformat commit
```
Blame answers "who touched this **last**", not "who is responsible". A `ruff` reformat, a rename, or a mass indentation change re-blames thousands of lines to whoever ran the tool. So blame is step one: get a commit, then `git show` it and read the *message* — the message is where the reasoning lives. Record noisy commits once in a `.git-blame-ignore-revs` file and set `blame.ignoreRevsFile` so everyone's blame skips them.

`git shortlog -sn` collapses history to a per-author commit count — useful for "who knows this codebase?" before you go asking questions.

# Real World Example (this repo)

**The shape of the repository, in one command.** The `--graph` column is not decoration — it is the topology from [Ch 06](06_The_Commit_Graph.md) rendered in ASCII:

```
$ git log --oneline --graph -8
* 42a2ecc4 chore(repo): stop tracking database dumps + node_modules; teach why in the course
*   83a144ba Merge pull request #15 from umesh29032/new_flask_app
|\
| * 7fe2bb0e feat: accountant read tier, student role, learning platform completion, UTC date-class fix
| * af01b9e7 test(production): pin F-4 roster-picker guarantee on generic_stage path
| * 01604aa0 feat(production): worker roster picker as searchable multi-select dropdown
| * 0d45427f feat(production): super-admin Adda cancel + safe delete with money/earning guard
```

`83a144ba` has **two** parents — that is what the `|\` fork means. Its first parent is the previous tip of `main`; its second parent is `7fe2bb0e`, the last commit of the `new_flask_app` branch. So `83a144ba^2` **is** `7fe2bb0e`.

**Reading `main` as a list of features.** Because every feature lands through a PR merge (`CONTRIBUTING.md` §5), `--first-parent` skips all the inside-the-branch detail:

```
$ git log --oneline --first-parent origin/main -5
83a144ba Merge pull request #15 from umesh29032/new_flask_app
fa9507d7 Merge pull request #14 from umesh29032/new_flask_app
5bf77da1 Merge pull request #13 from umesh29032/new_flask_app
88f3041c Merge pull request #12 from umesh29032/new_flask_app
b88f9c61 Merge pull request #11 from umesh29032/new_flask_app
```

**Who has touched this codebase** — four identities, one human, which is itself a finding (`umesh-personal` is the local commit identity; `umesh29032` is the GitHub account that creates the merge commits):

```
$ git shortlog -sn HEAD
   307	umesh-personal
    11	umesh29032
     5	Umesh chaudhary
     1	Umesh
```

**One file's biography** — exactly three commits have ever touched the deployment course's backup chapter (creation, a batch edit, the dump incident):

```
$ git log --oneline -- django_inventory/docs/deployment_course/28_Backups.md
42a2ecc4 chore(repo): stop tracking database dumps + node_modules; teach why in the course
7fe2bb0e feat: accountant read tier, student role, learning platform completion, UTC date-class fix
2f1eba0b docs(deployment-course): from-zero DevOps course (46 files) — internet → deploy → ops → scale
```

**The pickaxe, on real money code.** The UTC/IST date bug was fixed by switching to `timezone.localdate(...)`. When did that call enter the settlement service?

```
$ git log --oneline -S'localdate' -- django_inventory/config/expense/services/adda_settlement_service.py
7fe2bb0e feat: accountant read tier, student role, learning platform completion, UTC date-class fix
```

One commit. No grep of today's code could have told you *when* — and if the fix had later been reverted, `-S` would still find both the addition and the removal.

**Blame, on the rule from the last chapter.** Lines 112–117 of the ERP's ignore file — including the `db_backups/` rule whose narrow scope caused the leak:

```
$ git blame -L 112,117 -- django_inventory/.gitignore
7fe2bb0e1 (umesh-personal 2026-08-03 12:46:54 +0530 112) # ── Local database backups (scripts/db.sh save) ──
7fe2bb0e1 (umesh-personal 2026-08-03 12:46:54 +0530 113) # NEVER commit these: a dump contains real worker data and password hashes.
7fe2bb0e1 (umesh-personal 2026-08-03 12:46:54 +0530 114) db_backups/
7fe2bb0e1 (umesh-personal 2026-08-03 12:46:54 +0530 115) *.sql
7fe2bb0e1 (umesh-personal 2026-08-03 12:46:54 +0530 116) *.dump
```

All six lines blame to one commit on one day — the signature of a **block that moved or was rewritten wholesale**, not six separate decisions. This is exactly where blame lies: the rule is older than the commit that last touched it. Blame gave a lead; `git log -S'db_backups'` plus the commit messages give the history.

# Visual Diagram
```
  git log = WALK BACKWARDS along parent pointers from a starting ref

     HEAD -> 42a2ecc4 --> 83a144ba --> (main's old tip) --> ... --> root
                             \                                  (324 commits here)
                              `--> 7fe2bb0e  = 83a144ba^2  (second parent)
     83a144ba~1 = first parent    83a144ba~2 = two generations back (first-parent path)
     --first-parent  => stay on the trunk, one line per merged feature

  THE SIEVE PIPELINE (all AND together)
     all reachable commits
        -> -5 / -n 5 .................. count
        -> --since / --until .......... time
        -> --author / --committer ..... person
        -> --grep=REGEX ............... commit MESSAGE
        -> --no-merges / --first-parent shape
        -> -- <path> .................. touched this file   (--follow across renames)
        -> -S'str' / -G'regex' ........ the DIFF itself  (the pickaxe)
        -> --stat | --shortstat | -p ... how to display what survived

  WHERE EACH TOOL LOOKS
     grep .............. working tree, NOW
     git grep .......... one tree (a snapshot)
     git log -S ........ the SPACE BETWEEN trees (diffs) -> finds deleted code
     git blame ......... per-line last-touch (a starting point, not a verdict)
     git show REV:path . that file's full contents at that revision
```

# Practical — interrogate this repo (all read-only)
```bash
cd /home/tech/umesh-personal

git log --oneline -5                      # newest five, one line each
git log --oneline --graph --all -12       # the whole shape, every branch
git log --oneline --first-parent origin/main -5           # main as a feature list
git rev-list --count HEAD                 # -> 324  (how deep this history is)
git log --pretty=format:'%h %ad %an %s' --date=short -5   # custom columns

git log --oneline --grep='settlement' -6                  # by commit MESSAGE
git log --oneline --author='umesh29032' -5                # by person
git log --oneline --since='2026-07-20' --until='2026-07-25'   # by time window
git shortlog -sn HEAD                     # per-author counts
```
```bash
git log --oneline -- django_inventory/.gitignore    # one path's history
git log --oneline -S'localdate' -- django_inventory/config/expense/services/adda_settlement_service.py
git show --stat --oneline 5b9d1601                  # what one commit touched
git show 42a2ecc4:.gitignore | head -20            # a FILE as of that commit
git log -1 --format=%B 42a2ecc4                    # just the message body
git blame -L 112,117 -- django_inventory/.gitignore   # per-line last touch

git log --oneline main..origin/main | wc -l           # what origin has that I don't
git rev-list --left-right --count main...origin/main  # -> "0  295" = behind 295
```
Pager: `q` quits, `/text` searches, `git --no-pager log …` prints straight to the terminal (what scripts want).

# Production Walkthrough
The real hunt, as it happened here: *a settlement's ledger `entry_date` landed on the wrong calendar day for anything created after ~05:30 IST, because a UTC timestamp was being converted with `.date()`.*

1. **Find the topic in messages first** — cheapest possible search:
   `git log --oneline --grep='settlement' -6` → several candidates, including `7fe2bb0e`.
2. **Suspect the fix's vocabulary, not the bug's.** The correct call is `timezone.localdate`, so ask when that string entered the money service:
   `git log -S'localdate' -- .../adda_settlement_service.py` → exactly `7fe2bb0e`.
3. **Read the diff, not the summary** — `git show 7fe2bb0e -- .../adda_settlement_service.py` shows both sides of the change; the *deleted* lines are the bug.
4. **Read the message body** — `git log -1 --format=%B 7fe2bb0e`. This is where the *why* lives: which sites were affected, which were money-critical. The diff can never tell you that.
5. **Blame the neighbourhood** — `git blame -L <n>,<m> -- <file>` on the surrounding lines, to see whether the wrong pattern was copied in from elsewhere. In this repo it was: the same shape existed at 16 sites.
6. **Widen from one instance to the class** — `git log --oneline -S'.date()'` across the repo. A bug found by pattern is almost never alone; one grep-shaped sweep missed six sites, and only an AST-based sweep caught them all.
7. **Confirm it landed on the trunk** — `git log --oneline --first-parent origin/main | grep -i date`, and `git branch --contains 7fe2bb0e` ([Ch 09](09_What_A_Branch_Really_Is.md)) to check reachability rather than assuming.

Total: about ninety seconds of commands, and the answer includes *why* — which is the part you could never have reconstructed from the code alone.

# Debugging Guide
| Symptom | Cause | Fix |
|---|---|---|
| `git log -- path` shows nothing, but the file has history | It was renamed, or the path is wrong | `git log --follow -- path`; for a deleted file add `--full-history` |
| "That commit isn't in the log" | It is not reachable from `HEAD` | `git log --all`, or name the branch; see also `git reflog` ([Ch 16](16_Reflog.md)) |
| The log is drowning in merge commits | You are reading a merge-based trunk | `--first-parent` (feature list) or `--no-merges` (real work only) |
| Blame credits a reformat commit everywhere | A bulk change re-touched every line | `git blame -w -C`, `--ignore-rev <hash>`, or a `blame.ignoreRevsFile` |
| `--author` finds nothing | It is a regex over "Name <email>", and identities vary | Check `git shortlog -sn` for the real spellings |
| Dates look out of order | Log order is topological; rebase rewrites author dates | `--date-order`, and `--pretty=fuller` to see committer dates |
| `git log main` errors or matches a file | Git cannot tell a ref from a path | Insert `--`: `git log main -- path` |
| Pager seems frozen | You are inside `less` | `q` to quit; `git --no-pager …` to bypass |

# Performance Notes
- **Metadata walks are cheap.** `git log --oneline` over all **324** commits here takes **0.019 s**, because it reads only commit objects — small, and packed together.
- **Diff-based searches are not.** `git log -S'localdate'` over the same history takes **2.464 s** — roughly **130× slower** — because git must diff *every* commit against its parent to count occurrences. Always constrain a pickaxe with a path or a range: adding `-- <one-file>` on this repo makes it effectively instant.
- `-p` on a large range is the most expensive routine thing you can ask for; pair it with `-n`, a path, or `--stat` first.
- `--follow` adds rename detection per commit; `blame -C` adds cross-file move detection. Both are heuristics with a real CPU cost — reach for them when the cheap answer is wrong, not by default.
- Very large repos benefit from `git commit-graph write`, which caches commit reachability so walks stay fast at millions of commits. At 324 commits this repo needs nothing; the habit that matters is *scoping the query*, not tuning git.

# Security Considerations
- **Reading history is how you find a leak.** `git log --oneline -S'SECRET_KEY'` or `git log -p -- .env` will surface a credential that a later commit "removed" — and that is exactly why the removal is not a fix ([Ch 07](07_Gitignore.md), [Ch 33](33_Secrets_And_Leaks.md)).
- **A file deleted today is still served from any old commit**: `git show <old-commit>:path`. Both dumps in this repo's history remain readable that way, which is why the decision not to rewrite history was made **explicitly** after an audit, not by accident.
- **Every commit embeds an author name and email in plaintext** (`git cat-file -p <commit>` shows them raw). On a public repo that is a permanent, scrapable disclosure. Decide what goes in `user.email` *before* your first commit — this repo's commits carry a personal Gmail address forever.
- **Commit messages leak too.** "temporarily disable the permission check on /workers" is a roadmap for an attacker reading a public repo. Write the *why*, not the exploit.
- **Blame output is people data.** Use it to find context and reasoning, never to assign fault in a review — that is a culture bug that stops people from committing honestly.

# Architecture Decisions
- **Conventional Commits are enforced** by `git-hooks/commit-msg` (`CONTRIBUTING.md` §4) *because* it makes history searchable: `--grep='^fix(expense)'` only works if the format is guaranteed. A hook that rejects a malformed subject is buying you a queryable database years later.
- **Squash-merge, one feature per commit on `main`** (§5). The payoff shows up here: `--first-parent origin/main` reads as a list of features, and any single feature reverts cleanly.
- **The commit *body* carries the reasoning** ("explain **why**, not what" — §4). `git show` gives you the what for free; the why is the only thing that cannot be reconstructed, and `git log -1 --format=%B` is how you retrieve it. Commit `42a2ecc4` is the model: root cause, audit findings, fix, and one deliberate non-action.
- **Merge commits from PRs are kept on `main`, not rebased away.** *Rejected:* a fully linear trunk. The merge commit is what makes `--first-parent` a feature list and preserves the PR number as a permanent link to its discussion.
- **Annotated tags for releases** (§7) — an annotated tag is a real object with author, date and message, so `git show erp-v1.0.0` explains the release. A lightweight tag would have been a bare pointer with nothing to read.

# Best Practices
- Start cheap and narrow: `--oneline`, then a sieve, then a path — only then `-p`.
- Reach for `-S'<string>'` the moment the question is "when did this code appear or disappear?", and always scope it with a path or range.
- Type `--` before every path. Two characters, and a whole class of ambiguity errors gone.
- Treat `git blame` as a lead: get the commit, then read the **message**.
- Use `--first-parent` on a merge-based trunk to read features; `--no-merges` to read work.
- Prefer `--all` when hunting; the default `HEAD`-only walk is what hides the commit you want.
- Write commits that will answer questions: Conventional subject, body explaining *why*.
- Add a `.git-blame-ignore-revs` file the first time a bulk reformat pollutes blame.

# Beginner Mistakes
- **Using `grep` to find deleted code** → it only sees the working tree. Only `git log -S` searches the diffs between commits.
- **Assuming a commit does not exist because `git log` did not show it** → the default walk starts at `HEAD` only. Use `--all`, name the branch, or check `git reflog`.
- **Confusing `HEAD~2` with `HEAD^2`** → `~` walks generations back, `^` picks *which* parent. `HEAD^2` on a non-merge commit is an error.
- **Reading `A..B` as "diff of A and B"** → it is "commits in B not in A". Two dots is a range, three dots is the symmetric difference.
- **Blaming a person from `git blame`** → you found who touched the line last, often a reformatter. Read the commit message first.
- **Forgetting `--` before a path** → git may read it as a revision and error out, or silently do the wrong thing.
- **Running `git log -p` on the whole repo** → hundreds of megabytes through a pager. Scope it with `-n`, a path, or `--stat`.
- **Trusting log order as chronological order** → dates live in the commit object and rebases rewrite them. Use `--date-order` when time matters.
- **Ignoring the commit body** → the diff shows *what* changed; the body is the only place the *why* survives.

# Interview Questions
- **Junior:** "How do you find out when a file changed and by whom?" — `git log --oneline -- path/to/file` lists every commit that touched it; `git show <hash>` shows that commit's diff and message; `git blame -- path` shows, per line, the commit and author that last touched it. Add `--follow` if the file was renamed, since git detects renames rather than recording them.

- **Mid:** "A config value used to exist and now doesn't. Find the commit that removed it." — `git log -S'THE_VALUE' -- path` — the pickaxe lists commits where the number of occurrences *changed*, so both the addition and the removal appear. `grep` cannot help because the string is not in the working tree any more. Then `git show <hash>` to read the diff and the message, and `git show <hash>^:path` to see the file as it was just before. Scope it with a path, because `-S` diffs every commit and is roughly two orders of magnitude slower than a metadata walk.

- **Senior:** "Explain `--first-parent`, and when you would use it." — A merge commit has several parents: the first is the branch you merged *into* (the trunk), the rest are the branches merged *in*. `--first-parent` follows only that first pointer, so on a PR-merge workflow the log collapses to one entry per merged feature and hides all intra-branch noise. It is the right lens for release notes, for "what shipped between these tags", and for bisecting at feature granularity. Its complement is `--no-merges`, which shows the real work and hides the merges — different question, opposite filter. Same idea underlies `A..B` for "what does B add over A", which is exactly what a PR is.

- **Staff:** "A money field is wrong for records created after 05:30 IST. Walk me through your investigation." — Cheapest signal first, then widen: `--grep` on the area's vocabulary for candidates; then the pickaxe on the *fix's* vocabulary rather than the bug's — here `-S'localdate'` scoped to the settlement service returned exactly one commit; then read the diff for the deleted lines (the bug) and the body for which sites were money-critical. Blame the neighbourhood to see whether the pattern was copied in. Then deliberately turn one instance into a class: a UTC-vs-local `.date()` bug is never alone — in this repo a literal string sweep found ten sites while an AST-based sweep found **sixteen**, five on money records including the ledger `entry_date` on the primary settlement path. Confirm reachability with `git branch --contains` instead of assuming the fix is on the trunk, and pin the failure mode with a test plus a guard that matches the *shape*, not the spelling: the original guard was a string scan, and that was the real defect.

### Why interviewers ask these — and the answer that separates levels

| Testing for | Weak answer | What lands |
|---|---|---|
| Can you find code that no longer exists? | "I'd grep the repo." | `git log -S'string'` searches diffs, so it finds the commit that *removed* it. Scope it with a path. |
| Do you understand log is a graph walk? | "git log shows all commits." | It walks parents from one ref. Unreachable commits need `--all`, a branch name, or the reflog. |
| Do you know what blame really tells you? | "It shows who wrote the line." | Who touched it **last** — often a reformatter. Get the commit, then read the message. |
| Can you read a merge-based history? | "There's too much noise in the log." | `--first-parent` for a feature list, `--no-merges` for real work, `A..B` for what B adds. |

**The killer follow-up:** *"The line you're blaming was last touched by a formatting commit. Now what?"* — `git blame -w -C` to discount whitespace and moves, `--ignore-rev` (or a committed `.git-blame-ignore-revs`) to skip the reformat, or drop blame entirely and use `git log -S'<the exact code>' -- <file>`. Anyone who stops at "the formatter's author wrote it" has only ever used blame in a web UI.

# Revision Notes
- `git log` **walks parents** from a starting ref. Nothing unreachable appears — that is what `--all` is for.
- Five sieves: **count · time · person · message · shape**. They AND together.
- `--first-parent` = one line per merged feature. `--no-merges` = the real work.
- `-S'str'` searches **diffs** (finds deleted code); `grep` searches only the working tree.
- Always scope a pickaxe: unscoped it took **2.464 s** here versus **0.019 s** for a plain log.
- `~` = generations back; `^` = which parent. `A..B` = in B not A; `A...B` = diverged both ways.
- `git show <rev>:<path>` prints a file's full contents at that revision — including a "deleted" secret.
- `git blame` = last touch, not authorship. Get the commit, read the **message**.
- Type `--` before every path; use `--follow` for renames and `--full-history` for deleted files.

# Cheat Sheet
- **Shape:** `git log --oneline --graph --all --decorate` · custom columns `--pretty=format:'%h %ad %an %s' --date=short`.
- **Sieves:** `-5` · `--since=/--until=` · `--author=` · `--grep=` (`-i`) · `--no-merges` · `--first-parent`.
- **Feature list of the trunk:** `git log --oneline --first-parent origin/main`.
- **One file:** `git log --oneline -- path` · renamed `--follow` · deleted `--full-history`.
- **Find vanished code:** `git log -S'string' -- path` (diff search) · regex form `-G'regex'`.
- **Inspect a commit:** `git show --stat <hash>` · `git show <hash>` · body only `git log -1 --format=%B <hash>`.
- **A file at a revision:** `git show <hash>:path/to/file`.
- **Per line:** `git blame -L 10,40 -- file` · quieter with `-w -C` · skip a reformat `--ignore-rev <hash>`.
- **Compare refs:** `git log --oneline A..B` · divergence `git rev-list --left-right --count A...B`.
- **Counts:** `git rev-list --count HEAD` · per author `git shortlog -sn`.
- **Pager:** `q` quits, `/` searches, `git --no-pager …` bypasses it.

# My ERP Section
| Question | The command, on this repo |
|---|---|
| How deep is history? | `git rev-list --count HEAD` → **324** commits |
| What shipped, feature by feature? | `git log --oneline --first-parent origin/main` → `Merge pull request #15…` back to #11 |
| Who has worked here? | `git shortlog -sn` → 307 `umesh-personal`, 11 `umesh29032`, 5 + 1 as `Umesh…` |
| When did the UTC date fix land? | `git log -S'localdate' -- config/expense/services/adda_settlement_service.py` → **`7fe2bb0e`** |
| Why were the dumps untracked? | `git log -1 --format=%B 42a2ecc4` — root cause, audit, fix, and the deliberate non-rewrite |
| What did `.gitignore` look like then? | `git show 42a2ecc4:.gitignore` |
| Who wrote the `db_backups/` rule? | `git blame -L 112,117 -- django_inventory/.gitignore` → all `7fe2bb0e`, i.e. a moved block |
| How far behind is local `main`? | `git rev-list --left-right --count main...origin/main` → `0  295` |
| What is `83a144ba^2`? | `7fe2bb0e` — the branch side of PR #15's merge |

# Practice Tasks
1. **Read the trunk.** Run `git log --oneline --first-parent origin/main -10`, then the same without `--first-parent`. In two sentences: what are the extra lines, and when do you want them?
2. **Pickaxe drill.** Find the commit that introduced `localdate` anywhere in the repo, then repeat scoped to `django_inventory/config/expense/`. Time both with `time` and explain the difference.
3. **Biography.** Pick any template under `django_inventory/config/templates/`, produce its full history with `--follow`, then `git show <first-hash>:<path>` to read its original version.
4. **Blame honestly.** Blame 20 lines of a file you did not write. For the top commit run `git show` and `git log -1 --format=%B`. Did the message change your interpretation?
5. **Range reading.** Run `git log --oneline main..origin/main | wc -l` and `git rev-list --left-right --count main...origin/main`. Explain what each number means and why they differ.

# Homework
- Find, without asking anyone, **why** history in this repo was not rewritten after the dump incident. Name the command that gave you the answer.
- Take a bug you fixed recently. Write the `git log` invocation that would let a stranger find it in six months. If no invocation works, your commit message was the problem.
- Run `git log -S'.date()'`, then read [Ch 35](35_Bisect.md). When is the pickaxe the right tool, and when is `bisect` better?
- Compare `git show 42a2ecc4:.gitignore` with the current file. What changed, and what does that tell you about how the rule evolved?

---

# Further Reading & Live Resources
- Git docs — *`git log`*, every flag in this chapter: https://git-scm.com/docs/git-log
- Git docs — *`gitrevisions`*, the authoritative `~`/`^`/`..`/`...` reference: https://git-scm.com/docs/gitrevisions
- Git docs — *`git blame`* including `--ignore-rev`: https://git-scm.com/docs/git-blame
- Git docs — *`git show`*: https://git-scm.com/docs/git-show
- *Pro Git*, ch. 2.3 "Viewing the Commit History": https://git-scm.com/book/en/v2/Git-Basics-Viewing-the-Commit-History
- GitHub blog — *ignoring bulk-change commits in blame*: https://github.blog/changelog/2022-03-24-ignore-commits-in-the-blame-view-beta/
