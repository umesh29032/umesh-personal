---
id: git-course-14-interactive-rebase
type: lesson
status: active
owner: handwritten
scope: git, version control — editing your own unpushed history with rebase -i, amend, fixup and autosquash
anchors: CONTRIBUTING.md, git-hooks/commit-msg, .github/workflows/ci.yml, .pre-commit-config.yaml
verified: 2026-08-03
---

# 14 — Interactive Rebase (the history editor: reword, squash, drop, reorder)

> Part of [Git Course](00_COURSE_OVERVIEW.md). Prev: [13 — Rebase](13_Rebase.md). Next: [15 — Undo: reset vs revert vs restore](15_Undo_Reset_Revert_Restore.md).

# Learning Objectives
By the end of this chapter you can:
- open `git rebase -i` and read the todo list without guessing
- use `pick`, `reword`, `edit`, `squash`, `fixup`, `drop`, `break` and `exec` deliberately
- turn a messy branch of "wip" commits into the reviewable commits `CONTRIBUTING.md` §4 asks for
- fix a bad message with `--amend` (last commit) or `reword` (any commit)
- split one commit into two, and reorder commits, without losing work
- abort or undo an interactive rebase at any point

# Purpose
Plain rebase ([Ch 13](13_Rebase.md)) changes *where* your commits sit. Interactive rebase changes *what they are*: their messages, their contents, their order, their number. It is the tool that turns "how I actually worked" (messy, out of order, three typo fixes) into "how the change should be read" (a small number of clean, self-explanatory commits). That translation is what makes a PR reviewable, and reviewability is the whole reason this project uses PRs at all.

# The Problem
Look at this repository's real recent history and count the characters:

```bash
$ git log --format='%s' -12 | awk '{ print length($0)"  "$0 }'
81  chore(repo): stop tracking database dumps + node_modules; teach why in the course
90  feat: accountant read tier, student role, learning platform completion, UTC date-class fix
80  feat(production): super-admin Adda cancel + safe delete with money/earning guard
70  fix(inventory): role form mobile-responsive grids + scoped header type
114 feat(production): bundle allocation engine (AE-1→4) + genericity cleanup + BUG-B1 fix + full certification suite
96  feat(storefront): premium public homepage + login UI — About section, GSAP/Lenis motion system
```
(6 of the 12 lines shown.) **Eight of those twelve subjects are longer than 72 characters**, and the 90-character one bundles four unrelated concerns (`accountant read tier`, `student role`, `learning platform completion`, `UTC date-class fix`) into a single commit with no scope. `git-hooks/commit-msg` now rejects exactly this shape — but the hook arrived after these commits, so history carries the evidence.

Interactive rebase is how that gets fixed *before* it is pushed: four commits with four scopes, each under 72 characters, each revertable on its own. That is the difference between a log you can `git bisect` ([Ch 35](35_Bisect.md)) and a log you can only apologise for.

# Theory (from zero)

### What "interactive" actually means
`git rebase -i <base>` does everything plain rebase does — collect the commits after `<base>`, replay them one at a time onto a new tip ([Ch 13](13_Rebase.md)) — with one addition: **before replaying, it opens a text file and lets you rewrite the plan.** That file is the **todo list**. Nothing happens until you save and close the editor.

```
pick 5b9d1601 fix(inventory): role form mobile-responsive grids
pick 32d8be63 feat(production): surface AE-4 Production Snapshot link
pick 0d45427f feat(production): super-admin Adda cancel

# Rebase 2f1eba0b..0d45427f onto 2f1eba0b (3 commands)
# Commands:  p, pick / r, reword / e, edit / s, squash / f, fixup
#            d, drop / b, break / x, exec / l, label / t, reset / m, merge
```
Two things surprise everyone the first time. **(1) Oldest commit is at the top** — this list reads top-to-bottom in *replay* order, the opposite of `git log`. **(2) Deleting a line deletes the commit.** The list is not a display; it is the instruction set.

### The eight commands you will actually use
- **`pick`** — replay this commit unchanged. The default for every line.
- **`reword`** — replay it, but stop and open the editor for a new message. *(Fixes the 90-character subject problem.)*
- **`edit`** — replay it, then **stop with the commit checked out** so you can change files, `git add`, and even split it into several commits. Continue with `git rebase --continue`.
- **`squash`** — merge this commit into the one above it and let you write a combined message.
- **`fixup`** — same as squash, but **throw this commit's message away** and keep the one above. This is the workhorse for "typo fix" commits.
- **`drop`** — do not replay it at all. (Deleting the line does the same thing; `drop` is louder and safer to review.)
- **`break`** — stop here and hand control back, so you can look around, run a test, then `--continue`.
- **`exec <cmd>`** — run a shell command after that commit lands. `git rebase -i --exec 'ruff check .'` runs it after **every** commit; a red exit code pauses the rebase on the guilty commit.

### The `--amend` shortcut for the last commit only
If the mess is only in the newest commit, you do not need the interactive machinery:
```bash
git commit --amend                 # edit the message (opens the editor)
git commit --amend --no-edit       # keep the message, fold in whatever is staged
```
`--amend` is not "editing" a commit — remember commits are immutable ([Ch 05](05_How_Git_Stores_Everything.md)). It builds a **replacement** commit with a new hash and moves the branch label. The original stays in the reflog. So `--amend` is a one-commit interactive rebase wearing a friendlier name, and it carries the same rule: fine before the push, a rewrite after it.

### `fixup` + `--autosquash`: the professional loop
Reviewers ask for a change on your third commit. Instead of a new "address review comments" commit that makes the history worse:
```bash
git add -p                                  # stage just the fix
git commit --fixup 32d8be63                 # message becomes "fixup! feat(production): surface AE-4 …"
git rebase -i --autosquash origin/main       # git pre-arranges the todo: the fixup sits under its target as `fixup`
```
`--autosquash` reads those `fixup!`/`squash!` prefixes and builds the plan for you — you just save the file. Make it permanent with `git config --global rebase.autosquash true`. Note that `git-hooks/commit-msg` deliberately lets `fixup!` through (alongside `Merge ` and `Revert `), precisely so this workflow is possible under a Conventional-Commits gate.

### Splitting one commit into two
The one operation that looks impossible and is not. Mark the commit `edit`, then when the rebase stops:
```bash
git reset HEAD^                  # un-commit it, keep the changes in the working tree (Ch 15)
git add -p                        # stage only the first half, interactively
git commit -m "feat(expense): add settlement reconciliation evidence"
git add -A && git commit -m "test(expense): pin reconciliation evidence rows"
git rebase --continue
```
`git reset HEAD^` here is a **mixed** reset — it moves HEAD back one commit and leaves your files alone ([Ch 15](15_Undo_Reset_Revert_Restore.md) is the full treatment). Nothing is destroyed; the commit is simply re-cut as two.

### The same golden rule, no exceptions
Interactive rebase rewrites history, so [Ch 13](13_Rebase.md)'s rule applies unchanged: **only rewrite commits nobody has built on.** Squashing your own five unpushed commits: routine. Squashing `main`: an incident. And the undo is identical — `git rebase --abort` mid-flight, `git reset --hard ORIG_HEAD` after, `git reflog` always.

> 💡 **Samjho aise:** Interactive rebase = **kachhe notes ko final report banana**. Din bhar tumne raw notes likhe (wip, typo fix, oops) — client ko raw notes nahi dete. `reword` = heading theek karo · `squash`/`fixup` = do adhoore paragraph jodo · `drop` = galat page phaad do · order badal do taaki kahani seedhi lage. Sirf yaad rakho: report **chhapne se pehle** tak edit karo (unpushed), chhap jaane ke baad edit karna doosron ki copy jhooth bana deta hai.

# Real World Example (this repo)
The 90-character commit from *The Problem* is the perfect case study. It is real, it is already merged, and it shows both the value of the tool and the boundary on using it.

```bash
$ git log --format='%h %s' -1 7fe2bb0e
7fe2bb0e feat: accountant read tier, student role, learning platform completion, UTC date-class fix
```
Four concerns, no scope, 90 characters. Had it still been local, this would have fixed it:
```bash
git rebase -i af01b9e7        # base = the commit BEFORE the one to edit
# mark 7fe2bb0e as `edit`, then split it into four commits:
#   feat(accounts): accountant read-only tier
#   feat(learning): student role and progress layer
#   fix(learning): derive dates with timezone.localdate
#   docs(learning): chapter contract test pins
```
It was **not** done, and that decision is the lesson. By the time the problem was visible, `7fe2bb0e` was already a parent of the merge commit `83a144ba` (PR #15) and pushed to GitHub. Rewriting it means rewriting the merge above it and force-pushing `main` — which `git-hooks/pre-push` blocks and `CONTRIBUTING.md` §10 forbids. The history keeps its scar; the hook stops the next one.

```bash
$ git reflog -3
42a2ecc4 HEAD@{0}: commit: chore(repo): stop tracking database dumps + node_modules; teach why in the course
83a144ba HEAD@{1}: pull upstream main: Fast-forward
7fe2bb0e HEAD@{2}: commit: feat: accountant read tier, student role, learning platform completion, UTC date-class fix
```
Note what the reflog gives you: had that rebase been run, `HEAD@{2}` would still name the pre-rewrite commit for ~90 days. The reflog is what makes interactive rebase a safe experiment rather than a gamble.

# Visual Diagram
```
git rebase -i HEAD~4        (base = HEAD~4; four commits are up for editing)

  TODO LIST (oldest at top)                RESULT
  ────────────────────────────────         ──────────────────────────────────
  pick   a1  feat: add rate resolver   ──►  A' feat(expense): add rate resolver
  reword b2  feat: add reslover typo   ─┐        (message rewritten)
  fixup  c3  oops missing import       ─┴──►  B' feat(expense): resolve rates per role
  drop   d4  debug print statements     ✗        (c3 folded in, message gone)
                                                 (d4 never replayed)

  4 commits in  →  2 commits out, both self-explanatory, each revertable alone

  MID-FLIGHT: --continue (next step) · --edit-todo (change the plan) · --abort (cancel all)
  SAFETY NET: --abort → pre-rebase state · reset --hard ORIG_HEAD → after · reflog → always
  Deleting a line == dropping that commit.   Oldest is TOP (opposite of git log).
```

# Practical — clean up a messy branch before the PR
```bash
git switch -c practice/interactive          # never practise on a branch you care about
git branch backup/pre-cleanup               # free insurance label
git log --oneline origin/main..HEAD         # exactly which commits are in scope
```
```bash
git rebase -i origin/main                   # or: git rebase -i HEAD~4
```
In the editor: change `pick` → `reword` on the badly-worded commit, `pick` → `fixup` on each "oops" commit, and `drop` the debug commit. Save and close. Git then walks the plan:
```
[detached HEAD 9f2c1aa] feat(expense): resolve rates per role
 Date: Mon Aug 3 14:32:13 2026 +0530
 2 files changed, 41 insertions(+), 3 deletions(-)
Successfully rebased and updated refs/heads/practice/interactive.
```
```bash
# If it stops for `edit` or a conflict:
git status                                  # tells you which step you are on
git add <files> && git rebase --continue     # proceed
git rebase --edit-todo                       # change the remaining plan mid-flight
git rebase --abort                           # cancel everything, no trace
```
Verify — this is the step people skip:
```bash
git diff backup/pre-cleanup                 # MUST be empty: same final tree, fewer/cleaner commits
git log --oneline origin/main..HEAD          # the story you actually want reviewed
env/bin/python config/manage.py test         # the battery: 2033 tests, ~424 s
git push --force-with-lease                  # never plain --force (CONTRIBUTING §10)
```
Prove every commit builds, not just the last one (slow but decisive):
```bash
git rebase -i --exec 'env/bin/python config/manage.py makemigrations --check --dry-run' origin/main
```

# Production Walkthrough
How this fits the rulebook, end to end:

1. **Work however you like.** Commit early and often — `wip`, `oops`, `typo`. Local mess is free.
2. **Before pushing, translate.** `git rebase -i origin/main`: reword, fixup, drop, reorder until each commit is one idea with a Conventional-Commits subject under 72 characters (`CONTRIBUTING.md` §4). Then push and open the PR — §5 wants small PRs, because a 200-line PR gets a real review and a 2,000-line PR gets "LGTM".
3. **Review comes back.** `git commit --fixup <sha>` per fix, then `git rebase -i --autosquash origin/main` and `git push --force-with-lease`. `main` never sees "address review comments" noise.
4. **Squash-merge** (§5 step 5). Note the consequence: since the PR is squashed anyway, a tidy branch buys *review quality*, not the shape of `main` — so keep the cleanup proportionate. CI then re-runs on the rewritten branch because every hash changed; `.github/workflows/ci.yml` gates `lint` · `migrations` · `test` · `docs`, and `concurrency` cancels the superseded run so a force-push does not double-spend the ~2000 free private-repo Actions minutes.

One asymmetry to know: `.pre-commit-config.yaml` (ruff on changed Python, design-system ratchet on changed templates) runs when you *make* a commit, but **not** when a rebase replays one — and `git-hooks/commit-msg` is skipped too. CI catches what the replay skipped.

# Debugging Guide
| Symptom | Cause | Fix |
|---|---|---|
| Editor opens and you cannot get out | `core.editor` is an unfamiliar editor (often `vim`) | `:wq` saves, `:q!` cancels; or set `git config --global core.editor nano` |
| Rebase did nothing / a commit disappeared | empty todo list, or a line deleted or marked `drop` | `git reset --hard ORIG_HEAD`; or `git reflog` → `reset --hard HEAD@{n}` ([Ch 16](16_Reflog.md)) |
| `fixup` landed under the wrong commit | todo order is oldest-first, not `git log` order | `git rebase --edit-todo` and move the line, or restart with `--autosquash` |
| `could not apply <sha>` mid-rebase | a conflict on that step | resolve, `git add`, `--continue`; or `--abort` ([Ch 12](12_Merge_Conflicts.md)) |
| "You are currently editing a commit" | you marked a commit `edit` and it stopped | change files, `git commit --amend` or new commits, then `--continue` |
| Push rejected after the cleanup | history rewritten; the remote still has the old chain | `git push --force-with-lease` |
| `--autosquash` did nothing | messages lack the exact `fixup!`/`squash!` prefix | use `git commit --fixup <sha>`, not a hand-typed subject |

# Performance Notes
- Cost is again **linear in commits replayed** — the interactive part is free, the replay is not. Squashing 40 commits still replays 40 patches.
- `--exec` multiplies: the full battery over 10 commits ≈ 10 × ~424 s ≈ **70 minutes**. Use a cheap check (`ruff`, `makemigrations --check`) per commit and save the battery for the tip.
- Reordering commits that touch the same file is where conflicts and time come from. Reorder across *unrelated* files freely; think twice within one file.
- Every rewritten commit adds objects: `.git` here is **97 MB** with `count-objects -vH` reporting `count: 4873` loose objects, until `gc` prunes the unreferenced ones ([Ch 37](37_Large_Files_And_Performance.md)).

# Security Considerations
- **Rewriting a message does not rewrite the content.** If a commit contains a password, `reword` changes nothing that matters — the blob is still reachable. Secret removal is `git-filter-repo` plus rotating the credential ([Ch 33](33_Secrets_And_Leaks.md), [Ch 34](34_Rewriting_History.md)).
- **`drop` deletes evidence.** Dropping a commit that contained a security fix silently un-fixes the code. Diff against your backup label; an empty diff proves nothing was lost.
- **Hooks and signatures are skipped on replay:** `git-hooks/commit-msg` will not validate rewritten messages, and signatures are lost unless `rebase.gpgSign true` ([Ch 31](31_Signed_Commits.md)) — a cleaned branch can carry a message the gate would reject.
- **`exec` runs arbitrary shell commands** once per commit. Never paste an `--exec` line from an untrusted source; it has your shell, your keys and your `.env`.
- **Force-push discipline is the real control:** `--force-with-lease`, own branches only (§10). `git-hooks/pre-push` refuses `main`/`master`, but only where `bash git-hooks/install.sh` was run, because git never clones `.git/hooks/`.

# Architecture Decisions
- **`fixup!` is whitelisted by `git-hooks/commit-msg`** (alongside `Merge ` and `Revert `). A gate that rejected `fixup!` would have made the autosquash workflow impossible; the whitelist is what lets the format be enforced *and* the workflow stay ergonomic.
- **Squash-merge at the PR** (§5) means `main` gets one commit per feature regardless of branch tidiness — so interactive rebase is optimised for **review quality**, not `main`'s shape, which keeps the cleanup effort honest.
- **Enforcement lives in CI, not in replayed hooks.** Since rebase skips `pre-commit`/`commit-msg`, `.github/workflows/ci.yml` re-runs `lint`, `migrations`, `test` and `docs` on the rewritten branch. Hooks are the fast local filter; CI is the gate.
- **Rejected: rewriting merged history** to fix old messages (see `7fe2bb0e`) — force-pushing `main` and invalidating every clone outweighs a cosmetic gain. **Rejected: squash-everything-to-one-commit** on branches — it destroys the reviewable middle steps and `git bisect` granularity inside a feature ([Ch 35](35_Bisect.md)).

# Best Practices
- Rebase interactively **before** the first push; after that, rewrite only your own branch, with `--force-with-lease`.
- One commit = one idea, one scope, subject under 72 characters — what the hook and §4 already require.
- `git commit --fixup <sha>` the moment you notice a flaw; let `--autosquash` file it.
- Set up once: `git config --global rebase.autosquash true`, `rebase.autostash true`, `core.editor nano`.
- Always take `git branch backup/x` first and diff against it afterwards; empty diff = safe.
- `--exec` a *cheap* check per commit; run the full battery once at the tip.
- If it gets confusing, `git rebase --abort` — restarting costs seconds.

# Beginner Mistakes
- **Reading the todo list as `git log` order** → you fixup into the wrong parent. Oldest is at the **top**.
- **Deleting a line "to skip it for now"** → that commit is gone from the plan. Use `break`, or mark `drop` deliberately.
- **Rewriting commits that are already merged** → force-pushing shared history. Only your own unpushed, unbuilt-on commits.
- **`git commit --amend` after pushing, then a normal push** → rejected as non-fast-forward. `--force-with-lease`, own branch only.
- **Squashing everything into one commit** → you throw away the reviewable steps and `git bisect` granularity.
- **Not checking the result** → `git diff backup/x` must be empty; otherwise the cleanup changed the code, not just the history.
- **Assuming `reword` fixes a leaked secret** → it only touches the message; the blob is still there ([Ch 33](33_Secrets_And_Leaks.md)).
- **Trusting hooks to police a rebase** → `pre-commit`/`commit-msg` do not run on replayed commits; CI is the gate.
- **Panicking at "detached HEAD"** → normal mid-rebase. `git rebase --continue` or `--abort`.

# Interview Questions
- **Junior:** "What does `git rebase -i` let you do that `git rebase` does not?" — It opens a todo list before replaying, so I can change each commit instead of only its base: `reword` a message, `squash`/`fixup` commits together, `drop` one, reorder them, or `edit` one to change its contents. It is how I turn "wip / oops / typo" commits into a few clean commits before opening a PR.

- **Mid:** "A reviewer asks for a change to your second of five commits. What do you do?" — `git add -p` the fix, `git commit --fixup <sha of the second commit>`, then `git rebase -i --autosquash origin/main` — git files the fixup under its target automatically — and `git push --force-with-lease`. That keeps the history one-idea-per-commit instead of adding an "address review comments" commit, and it is safe because it is my own branch that nobody has built on.

- **Senior:** "How do you split a commit that does two things, and what are the risks?" — Mark it `edit` in the todo list; when the rebase stops, `git reset HEAD^` (mixed — moves HEAD back, keeps the files), then `git add -p` and commit the halves separately, then `git rebase --continue`. Risks: every later commit is rewritten so hashes change and the push needs `--force-with-lease`; replayed commits skip `pre-commit`/`commit-msg` hooks and lose GPG signatures; and a mistake in the split can silently change the tree — so I diff the result against a backup branch and expect empty, plus CI on the rewritten branch. Undo is `--abort` mid-flight, `reset --hard ORIG_HEAD` after, reflog for ~90 days.

- **Staff:** "Where do you draw the line between honest history and a curated log, on a team you lead?" — At the push: **rewrite freely until a commit is shared, never after.** Before the push history is a draft, and a messy draft is a disservice to reviewers; after, it is a shared fact other clones and CI runs depend on. Concretely: interactive rebase on your own branch, `fixup!` + `--autosquash` for review feedback, squash-merge at the PR so `main` is one revertable commit per feature, `--force-with-lease` only, and no rewriting of merged history — this repo has a 90-character four-concern commit in `main` we deliberately left alone rather than force-push a rewrite. Enforcement sits where it is free: a `commit-msg` hook that whitelists `fixup!` so the workflow survives the gate, plus CI as the real gate because rebase skips hooks. The value is not tidiness — it is that `git log` explains *why*, `git bisect` can find a break, and one `git revert` rolls back a feature.

### Why interviewers ask these — and the answer that separates levels

| Testing for | Weak answer | What lands |
|---|---|---|
| Do you know history is editable *before* sharing? | "You shouldn't change history." | Rewrite freely until it is shared; after that use `revert`. Name the tools: `reword`, `fixup`+`--autosquash`, `drop`. |
| Do you use fixups or pile up noise? | "I add a commit called 'fix review comments'." | `git commit --fixup <sha>` then `rebase -i --autosquash` — the fix lands inside the commit it belongs to. |
| Do you verify a rewrite? | "It said successfully rebased." | Backup branch, then `git diff backup/x` must be empty, plus CI green — because a rebase can change the tree or drop a commit. |
| Do you know what replay skips? | "The hooks protect us." | Replayed commits run **no** `pre-commit`/`commit-msg` hook and lose signatures; CI is the actual gate. |

**The killer follow-up:** *"You squashed ten commits, force-pushed, and then realise one of them contained the only copy of a fix you need. Recover it."* — `git reflog` still lists the pre-squash tip, so `git branch rescue HEAD@{n}` brings the whole old chain back as a branch, then `git cherry-pick <that commit>` onto your current work; `ORIG_HEAD` is the same tip if you have not run anything since. Nothing was deleted — squashing only stopped referencing those commits, and unreferenced objects survive ~90 days of reflog.

# Revision Notes
- `rebase -i <base>` = plain rebase **plus** an editable plan. Nothing happens until you save.
- Todo list is **oldest at the top**; deleting a line **drops** the commit.
- `reword` = message · `edit` = stop and change files · `squash` = combine + merge messages · `fixup` = combine, keep the top message · `drop` = discard · `break` = pause · `exec` = run a command per commit.
- `git commit --amend` = the one-commit case; still a new hash.
- `git commit --fixup <sha>` + `rebase -i --autosquash` = the review-feedback loop. `commit-msg` allows `fixup!` on purpose.
- Split a commit: mark `edit` → `git reset HEAD^` → `add -p` → two commits → `--continue`.
- Undo: `--abort` (during) · `git reset --hard ORIG_HEAD` (after) · `git reflog` (always).
- Replayed commits skip `pre-commit`/`commit-msg` and lose GPG signatures — CI is the gate.
- Verify with an **empty** `git diff` against a backup branch before force-pushing.

# Cheat Sheet
- **Open the editor:** `git rebase -i origin/main` · last 4 only: `git rebase -i HEAD~4` · from the very first commit: `git rebase -i --root`
- **Commands:** `pick` `reword` `edit` `squash` `fixup` `drop` `break` `exec`
- **Last commit only:** `git commit --amend` · keep message: `git commit --amend --no-edit`
- **Review fix loop:** `git commit --fixup <sha>` → `git rebase -i --autosquash origin/main`
- **Split:** mark `edit` → `git reset HEAD^` → `git add -p` → commit twice → `git rebase --continue`
- **Mid-flight:** `git rebase --continue` · `--edit-todo` · `--skip` · `--abort`
- **Test every commit:** `git rebase -i --exec 'ruff check .' origin/main`
- **Verify:** `git branch backup/x` before · `git diff backup/x` after (must be empty)
- **Publish:** `git push --force-with-lease` — never `git push --force`
- **Set once:** `git config --global rebase.autosquash true` · `rebase.autostash true` · `core.editor nano`

# My ERP Section
| Concept | In this repo |
|---|---|
| Message rules | `CONTRIBUTING.md` §4 — Conventional Commits, imperative, ≤ 72 chars, no trailing period |
| Enforcement | `git-hooks/commit-msg` rejects non-conforming messages; **allows `fixup!`**, `Merge `, `Revert ` (tested: 3 rejected, 6 accepted) |
| Install | `bash git-hooks/install.sh` — copies hooks into `.git/hooks/` (git never clones them) |
| The case study | `7fe2bb0e` — 90-char subject, 4 concerns, no scope; 8 of the last 12 subjects exceed 72 chars |
| Deliberately not fixed | rewriting `7fe2bb0e` means force-pushing `main` — refused (§10); the hook stops the next one |
| Local fast filter | `.pre-commit-config.yaml` — ruff on changed Python, design-system ratchet on changed templates |
| Skipped on replay | `pre-commit` and `commit-msg` hooks; GPG signatures |
| Real gate | `.github/workflows/ci.yml` — lint · migrations · test (2033 tests, ~424 s) · docs (`knowledge_sync` BLOCKER=0) |
| Merge style | squash-merge at the PR (§5), so branch tidiness serves **review**, not `main`'s shape |

# Practice Tasks
1. **Read the mess.** Run the `git log --format='%s' -12 | awk '{ print length($0)"  "$0 }'` command from *The Problem* and list every subject over 72 characters. Rewrite three of them properly on paper.
2. **Do the loop.** On `practice/interactive`, make four commits including one typo fix and one debug commit. Then `reword` one, `fixup` the typo, `drop` the debug commit — and prove with `git diff` against a backup branch that the final tree is unchanged.
3. **Split one.** Create a commit that changes two unrelated files, then split it into two commits using `edit` + `git reset HEAD^` + `git add -p`.
4. **Autosquash.** Make a `git commit --fixup <sha>` against your second commit and let `git rebase -i --autosquash` file it. Then explain why `git-hooks/commit-msg` had to whitelist `fixup!`.
5. **Recover.** Squash three commits, then bring the pre-squash chain back with `git reflog` + `git branch rescue HEAD@{n}`.

# Homework
- Take the four concerns bundled in `7fe2bb0e` and write the four Conventional-Commits subjects you would have used, each under 72 characters with a scope. Then argue whether rewriting merged history to apply them is ever worth it.
- Run `git rebase -i --exec 'ruff check .' origin/main` on a practice branch. How long did it take per commit, and what would the full battery (~424 s) have cost?
- Read `git-hooks/commit-msg` and find the lines that let `fixup!` through. What breaks if you remove them?
- Since PRs are squash-merged anyway, write your own rule for *how much* branch cleanup is worth doing — and defend it in three bullets.

---

# Further Reading & Live Resources
- Pro Git — *Rewriting History* (`--amend`, `rebase -i`, splitting commits): https://git-scm.com/book/en/v2/Git-Tools-Rewriting-History
- `git rebase` reference — `-i`, `--autosquash`, `--exec`, `--edit-todo`: https://git-scm.com/docs/git-rebase
- `git commit` reference — `--amend`, `--fixup`, `--squash`: https://git-scm.com/docs/git-commit
- Conventional Commits 1.0.0 — the format the hook enforces: https://www.conventionalcommits.org/en/v1.0.0/
- Pro Git — *Interactive Staging* (`git add -p`, the other half of splitting): https://git-scm.com/book/en/v2/Git-Tools-Interactive-Staging
