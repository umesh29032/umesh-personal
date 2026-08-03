---
id: git-course-11-merging
type: lesson
status: active
owner: handwritten
scope: git, version control — fast-forward vs three-way merge, squash merges, merge-base, and undoing a merge
anchors: CONTRIBUTING.md, .github/workflows/ci.yml, git-hooks/pre-push, django_inventory/CLAUDE.md
verified: 2026-08-03
---

# 11 — Merging (fast-forward, three-way, and the commit with two parents)

> Part of [Git Course](00_COURSE_OVERVIEW.md). Prev: [10 — Creating & Switching Branches](10_Creating_And_Switching_Branches.md). Next: [12 — Merge Conflicts](12_Merge_Conflicts.md).

# Learning Objectives
By the end of this chapter you can:
- find the **merge base** of two branches and predict, before running anything, whether a merge will fast-forward or create a commit
- read a merge commit's two parents with `git cat-file -p`, and say which parent is which
- choose deliberately between `--ff-only`, `--no-ff` and `--squash`, and name what each does to history
- say precisely what **ours** and **theirs** mean during a merge, without guessing
- undo a merge at every stage: mid-merge, just-completed, and already-pushed

# Purpose
Branching is cheap; the value only arrives when the work comes back together. Merging is that step, and it is the operation people fear most because they have only ever seen it go wrong. This chapter removes the fear by making merges *predictable*: two commands tell you what will happen before you do it, and there is a written undo for every outcome.

# The Problem
You finished `fix/utc-date-in-settlement`. `main` has moved on — four other changes landed while you worked. Now what?

Copy-pasting your files over `main` destroys the four other changes. Committing "merge" by hand loses the record of where the work came from. And the scary version: you run `git merge`, get 30 lines of `CONFLICT`, and the repository looks broken. So people avoid merging, branches live for weeks, and the divergence gets worse — this repo's working branch reached **296 commits** ahead of `main`.

The fix is not courage, it is knowledge. A merge has exactly three possible shapes, and which one you get is decided entirely by one commit: the **merge base**. Once you can find it, merging stops being a coin flip.

# Theory (from zero)

### What a merge actually produces

**Merging** means: take the work on two branches and make one branch contain both. Git does it by combining *snapshots*, not by replaying patches. Two inputs, one output:

- inputs: your current branch (**HEAD**) and the branch you name
- output: either your branch pointer moved forward, or **one new commit with two parents**

A **merge commit** is an ordinary commit that happens to record two parents instead of one. That is the entire definition — no special object type, no magic. [Ch 06](06_The_Commit_Graph.md) called the history a directed graph; a merge is where two lines of that graph join.

### The merge base — the commit that decides everything

The **merge base** is the most recent commit reachable from *both* branches: their common ancestor, the point where they diverged.

```bash
git merge-base main feat/x           # prints the common ancestor's SHA
git merge-base --is-ancestor A B      # exit 0 if A is an ancestor of B (silent; use $?)
```

From the merge base, the shape follows mechanically:

| Situation | What git does | Result |
|---|---|---|
| merge base **==** your branch's tip | **fast-forward**: just move your pointer | no new commit |
| merge base **==** the other tip | nothing to do | `Already up to date.` |
| merge base is **behind both** | **three-way merge** | one merge commit, two parents |

### Case 1 — fast-forward: a pointer moves, nothing is created

If your branch has no commits of its own since the merge base, the other branch's history already contains yours. There is nothing to reconcile, so git simply moves your branch pointer forward. Cheap, and it leaves history perfectly linear.

```bash
git merge --ff-only origin/main   # move forward, or FAIL — never invent a merge commit
git merge --no-ff feat/x          # force a merge commit even when a fast-forward was possible
```

`--ff-only` is a **safety flag, not an optimisation**. On `main` it means "I expect to only ever be behind; if I have somehow gained local commits, stop and tell me". `CONTRIBUTING.md` §9 uses it for exactly that reason: if `git merge --ff-only upstream/main` fails, your `main` has drifted and should be reset to upstream rather than merged, keeping `main` a clean mirror of the remote.

### Case 2 — three-way merge: base + ours + theirs

When both branches have moved, git needs three snapshots: the **base** (merge base), **ours** (HEAD) and **theirs** (the named branch). For every file it asks: who changed this relative to the base?

- only ours changed → take ours
- only theirs changed → take theirs
- both changed, in **different** regions → combine both, automatically
- both changed **the same region differently** → **conflict**, and git stops ([Ch 12](12_Merge_Conflicts.md))

The base is what makes this smart. Without it git could only see "these two files differ" and would have to ask you about every difference. With it, git can tell a *change* from an *unchanged inheritance* — which is why most merges need no human at all.

### `ours` vs `theirs` — the confusing bit, named

**`ours` = the branch you are standing on. `theirs` = the branch named in the command.** So after `git switch main && git merge feat/x`, "ours" is `main` and "theirs" is your feature work — the opposite of what most people assume, because you *authored* "theirs".

Worse, the labels **flip during a rebase** ([Ch 13](13_Rebase.md)): rebase replays your commits on top of the upstream, so the upstream becomes "ours" and your own commits become "theirs". Never resolve a conflict by trusting the words. Look at the content, or use `git log --merge -p` to see both sides.

> 💡 **Samjho aise:** Merge = **do register ek karna**. Git pehle woh page dhoondta hai jahaan se dono alag hue (merge base) — jaise do bhai ek hi ghar se nikle the. Agar aapne apne register mein kuch likha hi nahi, to bas apni parchi aage sarka do (**fast-forward**) — naya kuch banane ki zarurat nahi. Aur agar dono ne likha hai, to git ek **naya page** banata hai jispe **do baap ke naam** likhe hote hain (two parents). Yaad rakho: `ours` matlab jis branch pe aap **khade** ho, `theirs` matlab jise aap **merge kar rahe** ho — ulta lagta hai, par yahi sach hai.

### Case 3 — squash merge: one commit, one parent

`git merge --squash feat/x` computes the same merged content but **stages** it instead of committing, so your next `git commit` produces an ordinary **single-parent** commit. GitHub's "Squash and merge" button does the same server-side.

`CONTRIBUTING.md` §5 mandates squash-merge for PRs, and the reason is operational: one feature = one commit on `main`, so `main` reads as a list of features and any one of them reverts with a single `git revert`. The trade-off is real and worth stating — the intermediate commits (and their individual messages) never reach `main`, and because the feature branch's commits are *not* ancestors of `main`, `git branch -d` will still call it unmerged. After a squash-merge you delete the local branch with `-D`, which is safe precisely because the *content* landed under a new commit.

### merge vs rebase — named now, resolved in Ch 13

Both make your branch current with `main`. **Merge** preserves what really happened and adds a merge commit. **Rebase** rewrites your commits on top of `main`, producing linear history but new commit IDs. `CONTRIBUTING.md` §10 chooses: *no merge commits on feature branches — rebase onto `main` to stay current*, while `main` itself only ever receives squashed PR commits. So this project rebases *into* a branch and squashes *out of* it. Full treatment in [Ch 13](13_Rebase.md).

### Reading merges afterwards

```bash
git log --oneline --merges           # only merge commits
git log --oneline --no-merges        # exclude them
git log --oneline --first-parent     # follow only the mainline — the trunk's story
git log --graph --oneline -15        # see where lines joined
git cat-file -p <merge-sha>          # the raw object: two "parent" lines
```

**First parent is where you were; second parent is what you merged.** `--first-parent` is the flag that makes a merge-heavy history readable, because it treats each merge as a single step on the trunk.

### Strategies and options (short version)

Git 2.34 made **`ort`** ("Ostensibly Recursive's Twin") the default merge strategy — faster and more correct than the old `recursive`, especially with renames. This repo runs git **2.34.1**, so `ort` is what you get. Two option families you will meet:

- **`-X ours` / `-X theirs`** — still a real merge, but auto-resolve *conflicting hunks* in favour of one side. Useful for generated files.
- **`-s ours`** — a *strategy*, not an option: record the merge but keep your content and **discard the other side entirely**. Almost never what you want; it silently throws away a colleague's work while looking like a successful merge.
- **`--no-commit`** — perform the merge, stop before committing, so you can inspect or test first.

# Real World Example (this repo)

**A real merge commit, raw.** PR #15 merged the working branch into `main`:

```
$ git cat-file -p 83a144ba
tree aa3a236e9a1756d2aaa3bc679cbb459277a88b56
parent fa9507d7d9a39c6de0c8506a87a03f65fd89c09d
parent 7fe2bb0e1b50b5bb2b669e51d9f92191909bae3e
author Umesh chaudhary <44035504+umesh29032@users.noreply.github.com> 1785743474 +0530
committer GitHub <noreply@github.com> 1785743474 +0530
gpgsig -----BEGIN PGP SIGNATURE-----
…
Merge pull request #15 from umesh29032/new_flask_app
```

**Two `parent` lines** — that is the whole difference between a merge commit and a normal one. `fa9507d7` is the first parent (`main` before the merge, itself the PR #14 merge); `7fe2bb0e` is the second (the feature branch tip). The `committer` is `GitHub` because the merge was made by the merge button, and `gpgsig` is GitHub's signature over it ([Ch 31](31_Signed_Commits.md)).

**A real fast-forward.** The reflog records one, verbatim:

```
$ git reflog -2
42a2ecc4 HEAD@{0}: commit: chore(repo): stop tracking database dumps + node_modules; teach why in the course
83a144ba HEAD@{1}: pull upstream main: Fast-forward
```

That `pull … Fast-forward` had nothing to reconcile, so no merge commit was created — the branch pointer just moved to `83a144ba`.

**Predicting the next merge without running it:**

```
$ git merge-base main new_flask_app
7c256f50f2773d7f8e02d3762a1dd43d19386a3c

$ git rev-parse main
7c256f50f2773d7f8e02d3762a1dd43d19386a3c

$ git merge-base --is-ancestor main new_flask_app && echo "FF possible"
FF possible

$ git rev-list --left-right --count main...new_flask_app
0	296
```

The merge base **equals `main`'s tip**, and `main` is 0 ahead / 296 behind. So `git switch main && git merge new_flask_app` would be a **pure fast-forward of 296 commits** — no merge commit, no conflict possible, nothing to resolve. Three read-only commands, and the outcome was known in advance.

**The history's own honesty.** `main` here is full of real merge commits, not squashes:

```
$ git log --merges --oneline -4
83a144ba Merge pull request #15 from umesh29032/new_flask_app
fa9507d7 Merge pull request #14 from umesh29032/new_flask_app
5bf77da1 Merge pull request #13 from umesh29032/new_flask_app
88f3041c Merge pull request #12 from umesh29032/new_flask_app
```

Fifteen of these, every one titled after the branch. The squash-merge rule in `CONTRIBUTING.md` §5 is *newer than this history* — it was written because of it. This is what "one feature = one commit with a real subject" is meant to replace.

# Visual Diagram
```
  FAST-FORWARD               main's tip IS the merge base → just move the pointer
    before:  A─B─C ◄main            D─E ◄feat
             (base = C)
    after :  A─B─C─D─E ◄main, feat        no new commit · linear · no conflict possible

  THREE-WAY MERGE            both sides moved past the base → ONE commit, TWO parents
    before:        ┌─ D─E ◄feat                after:        ┌─ D─E ◄feat
             A─B─C ┤                                   A─B─C ┤        ╲
             (base)└─ F ◄main                                └─ F ───── M ◄main
                                                                       ▲
                              parent1 = F (where you were = "ours")────┘
                              parent2 = E (what you merged = "theirs")

  SQUASH MERGE               same content, ONE parent, feature commits not on main
    before:  A─B─C─F ◄main  +  D─E ◄feat
    after :  A─B─C─F─S ◄main        S has one parent; D,E are NOT ancestors of main
                                    → git branch -d feat still says "not fully merged"

  UNDO LADDER
    mid-merge (MERGE_HEAD exists) ....... git merge --abort
    finished, not pushed ................ git reset --hard ORIG_HEAD
    already pushed ...................... git revert -m 1 <merge-sha>   (new commit, safe)
```

# Practical — predict, merge, verify, undo

Predict first. These three are read-only and cost nothing:
```bash
git fetch origin
git merge-base --is-ancestor HEAD origin/main && echo "a merge into me would fast-forward"
git rev-list --left-right --count HEAD...origin/main    # <mine> <theirs>
git log --oneline HEAD..origin/main                     # what would arrive
```
Sync the trunk the strict way:
```bash
git switch main
git merge --ff-only origin/main      # succeeds silently, or fails loudly. No third outcome.
```
Expected on success — note it says `Fast-forward`, not "Merge made":
```
Updating fa9507d7..83a144ba
Fast-forward
```
Merge a feature deliberately, keeping the join visible:
```bash
git switch main
git merge --no-ff --no-commit feat/x   # do the work, but stop before committing
git status                             # inspect what is staged
env/bin/python config/manage.py test   # test the MERGED result, not either side
git commit                             # write a real message, not the default
```
The three undos, in order of how late you are:
```bash
git merge --abort                 # mid-merge (conflicts on screen): back to before, exactly
git reset --hard ORIG_HEAD        # merge finished, NOT pushed. ORIG_HEAD = pre-merge tip
git revert -m 1 <merge-sha>       # already pushed: a NEW commit that undoes the merge
```
`-m 1` means "keep the first parent's line of history" — reverting a merge is ambiguous without it, which is why git refuses a bare `git revert <merge>`.

**Shown, deliberately not run:**
```bash
git merge -s ours feat/x          # records a merge but DISCARDS the other side's content
git push --force origin main       # rewrites shared history; CONTRIBUTING §10 forbids it
```
`-s ours` is the quietest data-loss command in git: the log says merged, the diff says nothing arrived. If you find one in history, `git show <sha> --stat` against `git diff <parent2> <sha>` reveals it.

# Production Walkthrough
1. **Rebase, don't merge, on the feature branch.** `git fetch origin && git rebase origin/main` keeps the branch current with no merge commits (`CONTRIBUTING.md` §10, [Ch 13](13_Rebase.md)).
2. **Push, open the PR, let CI decide.** `.github/workflows/ci.yml` runs four jobs — `lint`, `migrations` (`makemigrations --check`), `test` (the full battery, `needs: [lint, migrations]`), and `docs` (`knowledge_sync` must report BLOCKER=0). A merge does **not** run tests; CI is the only thing standing between a green branch and a broken trunk.
3. **Review with money in mind.** Reviewing means co-signing. Any write to a ledger, settlement, earning or rate gets extra scrutiny: `CLAUDE.md` rule 5 is single-writer-per-table, and settlement is the **only** money-write boundary. A new money path outside an approved service is a **STOP**, not a nitpick.
4. **Squash-merge** (§5), so `main` gains one commit with a real subject, then delete the branch — locally with `-D`, because a squash leaves it "unmerged" in git's eyes.
5. **Verify the trunk.** `git switch main && git merge --ff-only origin/main`, then run the battery: **2033 tests across 14 apps, one command, ~424 s**, sequential on a fresh DB. The golden settlement figures (₹344.25 / ₹801 / ₹633 / ₹225) are byte-identical assertions — a merge that resolved a money file wrongly fails there, not in review.

# Debugging Guide

| Symptom | Cause | Fix |
|---|---|---|
| `Already up to date.` but you expected changes | The other branch's tip is already an ancestor — or you never fetched | `git fetch origin`, then re-check `git log HEAD..origin/main` |
| `fatal: Not possible to fast-forward, aborting.` | `--ff-only` and you have local commits the other side lacks | Inspect with `git log origin/main..HEAD`; then rebase, merge normally, or reset |
| `fatal: refusing to merge unrelated histories` | The two branches share no merge base (separate `git init`s) | Only if truly intended: `git merge --allow-unrelated-histories` |
| `Automatic merge failed; fix conflicts and then commit` | Both sides changed the same region | Resolve ([Ch 12](12_Merge_Conflicts.md)) or `git merge --abort` |
| `error: Your local changes … would be overwritten by merge` | Dirty working tree before merging | `git stash` or commit first, then merge |
| `fatal: You have not concluded your merge (MERGE_HEAD exists)` | A previous merge was left half-done | Finish it (`git commit`) or `git merge --abort` |
| `error: commit … is a merge but no -m option was given` | Reverting a merge is ambiguous | `git revert -m 1 <sha>` to keep the first parent's line |
| `main` history is unreadable after months of merges | Every PR merge is a commit on the trunk | Read with `git log --first-parent`; adopt squash-merge going forward |
| Merge "succeeded" but the changes are missing | `-s ours`, or a bad conflict resolution that kept one side | `git diff <merge>^2 <merge>` shows what the second parent contributed |

# Performance Notes
- **Merging compares trees, not commits.** A fast-forward of **296 commits** costs one tree diff and one pointer write — the number of commits between the two tips is nearly irrelevant.
- `ort` (default since git 2.34; this repo is 2.34.1) is markedly faster than the old `recursive` on large trees and handles renames better, which is what matters in a 2,407-file repo.
- A merge commit adds **one object**. The expensive artefact is not the merge, it is the divergence that made it necessary: 296 commits of drift means a huge review diff and a higher chance of conflict.
- The real post-merge cost is verification: the battery is **~424 s**. Budget it into every merge; skipping it is how a green branch produces a red trunk.
- CI-side: `concurrency` in `.github/workflows/ci.yml` cancels superseded runs, and `paths` filters skip runs entirely for unrelated monorepo folders — on a private repo's ~2,000 free Actions minutes, a ~7-minute battery is about 280 runs a month.

# Security Considerations
- **A merge is a code-execution decision, not a text operation.** Merging a fork's branch brings in its `.github/workflows/*`, `.pre-commit-config.yaml` and `Makefile`. Review those paths in a PR diff specifically; a workflow change from an outside contributor deserves more suspicion than application code.
- **`-s ours` is silent data loss.** History says "merged", the content says otherwise. Never use it to "resolve" a conflict.
- **Merging does not test.** Green on the branch plus green on `main` does not imply green on the *merge* of the two — that is the whole reason CI runs on the merge result and why the battery is re-run after landing.
- **Money paths deserve a hostile read at merge time.** `CLAUDE.md` rules 4–6 (service layer owns multi-row writes, one writer per ledger/audit table, permissions via `permission_service`) are exactly the invariants a careless conflict resolution breaks, because a "take both sides" merge can produce a second writer that neither branch ever had.
- **Squash-merge erases intermediate authorship.** If a colleague's commit is inside a squashed PR, their name survives only in `Co-Authored-By` trailers. Keep them.
- **Never `--force` push a merge onto a shared branch.** `CONTRIBUTING.md` §10: `--force-with-lease`, on your own branch, only.

# Architecture Decisions
- **Squash-merge for PRs** (`CONTRIBUTING.md` §5) — one feature = one commit on `main`, so the trunk reads as a feature list and any feature reverts cleanly. Accepted cost: intermediate commits do not reach `main`, and local branches need `-D`.
- **`--ff-only` for syncing `main`** (§9) — chosen so drift *fails loudly* instead of silently growing a merge commit. `main` is a mirror of the remote, not a place work happens.
- **Rebase feature branches, never merge into them** (§10) — keeps the PR diff honest and the branch history linear before it is squashed anyway.
- **`git revert -m 1` is the rollback story, not `reset`** — reverting is additive and safe on shared history; resetting a pushed branch requires a force-push, which §10 forbids.
- **Rejected: `git-flow` with long-lived release branches** — permanent `develop`/`release/*` branches multiply merges for a 1–2 person team ([Ch 24](24_Branching_Strategies.md)).
- **Rejected: merge-on-red as a mechanical block.** Blocking merge until checks pass is a paid feature on private repos. The free composition is CI as a *visible* gate plus collaborators on Read access working from forks, so nobody but the owner can merge at all ([Ch 27](27_Pre_Push_Protection.md)).

# Best Practices
- Run `git merge-base --is-ancestor` and `git log HEAD..origin/main` **before** merging. Predict, then act.
- Use `--ff-only` on `main` always; use `--no-ff` when you deliberately want the join recorded.
- Merge into a **clean** working tree — stash or commit first.
- `--no-commit` on anything risky, then test the merged result before committing it.
- Test *after* the merge, not just before: the merge is a new state neither branch had.
- Never resolve by trusting the words `ours`/`theirs`; read the content.
- Prefer `git revert -m 1` over history rewriting for anything already pushed.

# Beginner Mistakes
- **Thinking every merge makes a merge commit** → fast-forwards make none, which is why `git log` sometimes shows nothing new after a "merge". Check for the word `Fast-forward` in the output.
- **Assuming `theirs` means "the other person's code"** → `theirs` is whatever branch you named; after `git switch main && git merge feat/x`, *your own* work is "theirs". Read the content.
- **`git pull` as a reflex** → `pull` = fetch + merge, so it can create a merge commit you never asked for. Prefer `git fetch` then an explicit merge ([Ch 19](19_Push_Fetch_Pull.md)).
- **Merging with a dirty working tree** → git refuses, or your uncommitted work gets entangled with the merge. Stash first.
- **Using `git reset --hard` on a merge that was already pushed** → the commit is gone locally but not remotely; the next push demands `--force`. Use `git revert -m 1`.
- **`git revert <merge-sha>` without `-m`** → git refuses, because it cannot know which parent's line you want kept.
- **Trusting a green branch after merging** → the merged state was never tested. Re-run the battery; the golden money assertions exist for this.
- **`-X theirs` on a source file to "make the conflict go away"** → you silently discarded your own change. That flag is for generated files, not logic.
- **`git branch -d` after a squash-merge, then panicking at "not fully merged"** → expected: the branch's commits are not ancestors of `main`. Confirm the content landed, then `-D`.

# Interview Questions
- **Junior:** "What is a fast-forward merge?" — When your branch has no commits of its own since the merge base, the other branch's history already contains yours, so git just moves your branch pointer forward. No merge commit is created and no conflict is possible. `git merge --ff-only` demands this outcome and fails otherwise.

- **Mid:** "How does a three-way merge work, and what makes it better than diffing two files?" — Git finds the **merge base** (the common ancestor) and compares base→ours and base→theirs. Only-one-side-changed regions are taken automatically; both-sides-changed-in-different-places are combined; the same region changed differently is a conflict. The base is what lets git distinguish a *change* from an unchanged inheritance — a plain two-file diff would have to ask about every difference.

- **Senior:** "Contrast merge, squash-merge and rebase, and say which you'd put on a trunk." — A merge preserves both lines and records a commit with two parents, so history is complete but noisy. A squash-merge produces one single-parent commit with all the content: the trunk reads as a feature list and reverts cleanly, at the cost of losing intermediate commits and leaving the branch technically unmerged. A rebase rewrites your commits on top of the target — linear history, new commit IDs, dangerous on shared branches. My policy: rebase feature branches to stay current, squash-merge into the trunk, and never merge into a feature branch — which is precisely what this project's `CONTRIBUTING.md` §5 and §10 codify.

- **Staff:** "A merge landed on `main` two days ago and broke settlement money. Ship a fix without rewriting history, and prevent recurrence." — First contain: `git revert -m 1 <merge-sha>` creates a new commit undoing the merge while keeping the first parent's line, so no force-push touches a shared branch, and the revert is itself reviewable. Then diagnose with `git log --first-parent` to read the trunk as single steps, `git diff <merge>^2 <merge>` to see what the second parent actually contributed, and `git bisect` if the culprit is unclear ([Ch 35](35_Bisect.md)). Prevention has three layers: (1) test the *merge result*, not either side — CI runs on the merge, and the battery of 2033 tests re-runs after landing, with byte-identical golden settlement totals so a bad money resolution fails a number rather than a code review; (2) make the trunk revertible by construction — squash-merge means one feature is one commit; (3) treat money files as a review class of their own, because single-writer discipline is exactly the invariant a "take both sides" resolution breaks. Structural gap to state honestly: mechanically blocking merge-on-red is paid on private repos here, so the free equivalents are collaborators on Read access working from forks (no merge permission at all) plus CI as the visible gate.

### Why interviewers ask these — and the answer that separates levels

| Testing for | Weak answer | What lands |
|---|---|---|
| Do you know what decides a merge's shape? | "Git merges the two branches and sometimes makes a merge commit." | "The **merge base**. If it equals my tip it fast-forwards; if both sides moved I get one commit with two parents. `git merge-base --is-ancestor` tells me before I run anything." |
| Do you understand ours/theirs, or guess? | "Theirs is the other developer's code." | "`ours` is the branch I am on, `theirs` is the one I named — and the labels invert under rebase, so I resolve by reading content, never by the words." |
| Can you undo a merge at the right altitude? | "I'd reset hard and force-push." | "Mid-merge `--abort`; finished but unpushed `reset --hard ORIG_HEAD`; already pushed `revert -m 1` — additive, reviewable, no force-push on shared history." |

**The killer follow-up:** *"Your merge succeeded and the tests passed on both branches. Why might `main` still be broken?"* — Because the merged state is a third state neither branch ever tested: git resolves text, not semantics, so two individually-correct changes can combine into a broken whole (a renamed function on one side, a new caller on the other). That is why CI runs on the merge result and why the battery re-runs after landing.

# Revision Notes
- A **merge commit** is just a commit with **two parents**. First parent = where you were, second = what you merged.
- The **merge base** decides everything: equals your tip → **fast-forward**; both sides moved → **three-way merge**.
- `--ff-only` = safety (fail instead of inventing a commit). `--no-ff` = force the join to be recorded.
- Three-way merge inputs: **base + ours + theirs**. Only same-region-different-change is a conflict.
- **`ours` = branch you are on, `theirs` = branch you named** — and they invert during rebase.
- **Squash-merge** = one single-parent commit; the branch's commits are not ancestors of `main`, so `-d` refuses and `-D` is correct.
- Undo ladder: `--abort` (mid-merge) → `reset --hard ORIG_HEAD` (unpushed) → `revert -m 1` (pushed).
- `-s ours` records a merge but **discards** the other side. Silent data loss.
- Merging never runs tests. The merged state is new; re-verify it.

# Cheat Sheet
- **Predict:** `git merge-base A B` · `git merge-base --is-ancestor A B` · `git rev-list --left-right --count A...B` · `git log --oneline A..B`
- **Merge:** `git merge feat/x` · strict: `git merge --ff-only origin/main` · keep the join: `git merge --no-ff feat/x`
- **Inspect first:** `git merge --no-commit feat/x` → `git status` → test → `git commit`
- **Squash:** `git merge --squash feat/x && git commit` (one parent, one message)
- **Read:** `git log --graph --oneline` · `--merges` / `--no-merges` / `--first-parent` · `git cat-file -p <merge-sha>`
- **What did the second parent bring?** `git diff <merge>^2 <merge>`
- **Undo:** `git merge --abort` · `git reset --hard ORIG_HEAD` · `git revert -m 1 <merge-sha>`
- **Options:** `-X ours` / `-X theirs` (hunk preference, generated files only) · `--allow-unrelated-histories` (rare)
- ⚠️ **Avoid:** `git merge -s ours` (discards the other side) · `git push --force` on a shared branch

# My ERP Section

| Concept | In this repo |
|---|---|
| A real merge commit | `83a144ba` — `parent fa9507d7` (main) + `parent 7fe2bb0e` (branch), committer `GitHub`, GPG-signed |
| A real fast-forward | reflog `HEAD@{1}: pull upstream main: Fast-forward` → `83a144ba` |
| Merge base of the two branches | `git merge-base main new_flask_app` = `7c256f50` = **`main`'s own tip** → a merge would fast-forward |
| Divergence | `git rev-list --left-right --count main...new_flask_app` → `0  296` |
| Merge style on record | 15 merge-button commits, all titled `Merge pull request #N from umesh29032/new_flask_app` |
| Policy going forward | `CONTRIBUTING.md` §5 squash-merge · §9 `--ff-only` sync · §10 rebase feature branches, no force-push |
| Merge gate | `.github/workflows/ci.yml` — `lint`, `migrations`, `test` (`needs: [lint, migrations]`), `docs` (BLOCKER=0) |
| Post-merge verification | 2033 tests, 14 apps, ~424 s, sequential fresh DB; goldens ₹344.25 / ₹801 / ₹633 / ₹225 |
| Money rule a bad merge can break | `CLAUDE.md` rule 5 single-writer per ledger/audit table; settlement is the only money-write boundary |
| Merge strategy in use | `ort` (git 2.34.1 default) |

# Practice Tasks
1. **Predict, then verify.** Run `git merge-base main new_flask_app` and `git rev-parse main`. Explain in one sentence why a merge would fast-forward — before running any merge.
2. **Read a merge object.** `git cat-file -p 83a144ba`. Point at the two `parent` lines and say which is "ours". Then `git log --oneline -1 83a144ba^1` and `…^2` to confirm.
3. **Second-parent diff.** Run `git diff 83a144ba^2 83a144ba --stat | tail`. What does this tell you that `git show --stat` does not?
4. **First-parent reading.** Compare `git log --oneline -12` with `git log --oneline --first-parent -12`. Which is readable, and why?
5. **Rehearse the undo.** In a scratch clone, merge one branch into another, then undo it three ways: `--abort` (mid-conflict), `reset --hard ORIG_HEAD`, and `revert -m 1`. Write down which is safe on a pushed branch.
6. **Find the ff/no-ff difference.** Merge a branch twice in a scratch repo — once plain, once `--no-ff` — and compare `git log --graph --oneline`.

# Homework
- Read `CONTRIBUTING.md` §5, §9 and §10 together. State the project's three merge rules in one sentence each, and which chapter of this course each depends on.
- `git log --merges --oneline | wc -l` — count the merge commits on this history. Then argue whether squash-merge would have made `main` more or less useful, using a specific example title.
- Explain why `git revert -m 1` needs the `-m` and `git revert` on a normal commit does not. Answer in terms of the commit graph.
- CI runs the battery on the merge result. Name a concrete two-change scenario where both branches are green and the merge is red, then say which test in this project would catch it.

---

# Further Reading & Live Resources
- `git merge` — official reference (`--ff-only`, `--no-ff`, `--squash`, `-X`, `-s`): https://git-scm.com/docs/git-merge
- `git merge-base` — the command that predicts the merge shape: https://git-scm.com/docs/git-merge-base
- Pro Git, *Basic Branching and Merging* — fast-forward vs three-way, with diagrams: https://git-scm.com/book/en/v2/Git-Branching-Basic-Branching-and-Merging
- Pro Git, *Advanced Merging* — `ours`/`theirs`, `-X`, and reverting a merge: https://git-scm.com/book/en/v2/Git-Tools-Advanced-Merging
- Git 2.34 release notes — `ort` becomes the default merge strategy: https://github.blog/open-source/git/highlights-from-git-2-34/
- GitHub docs — *About merge methods* (merge commit vs squash vs rebase): https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/incorporating-changes-from-a-pull-request/about-merge-methods-on-github
