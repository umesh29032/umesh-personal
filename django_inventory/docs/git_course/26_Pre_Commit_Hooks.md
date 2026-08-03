---
id: git-course-26-pre-commit-hooks
type: lesson
status: active
owner: handwritten
scope: git — client-side hooks, the pre-commit framework, staged-only linting
anchors: .pre-commit-config.yaml, scripts/ds_lint.sh, .git/hooks
verified: 2026-08-03
---

# 26 — Pre-commit Hooks (catching it before a reviewer has to)

> Part of [Git Course](00_COURSE_OVERVIEW.md). Prev: [25 — Conventional Commits](25_Conventional_Commits.md). Next: [27 — Pre-push Protection](27_Pre_Push_Protection.md).

# Learning Objectives
By the end of this chapter you can:
- name git's client-side hooks and say when each fires
- explain why hooks are **not** cloned, and what that means for enforcement
- explain why a pre-commit hook must lint the **index**, not your working directory
- write a hook that is fast enough that nobody disables it
- explain the "ratchet" pattern — blocking new violations without fixing old ones
- say honestly what a client-side hook can and cannot guarantee

# Purpose
Every problem caught before `git commit` costs nothing. The same problem caught in review costs a
round trip; caught in CI it costs minutes and a re-push; caught in production it costs money.

Hooks are how you move problems left. They are also the most under-used feature in git, mostly
because two facts about them are rarely explained: **hooks are never cloned**, and **a
pre-commit hook that checks the wrong thing is worse than none**.

This chapter fixes both, then shows this project's two real gates.

# The Problem
Without a local gate, a reviewer's time goes to things a machine should have caught: an unused
import, an inconsistent quote style, a hard-coded colour instead of a design token. That is the
worst possible use of the scarcest resource in code review.

CI catches them eventually, but a CI failure means: push, wait for the runner, read the log, fix,
force-push, wait again. On a repo where the test battery takes **424 seconds**, a trailing-whitespace
error costing a full CI cycle is absurd.

There is a subtler problem too. A naive pre-commit hook lints **your files**. But git commits the
**index** ([Chapter 03](03_The_Three_Trees.md)). Those differ the moment you stage part of your work
— so a naive hook can pass a commit that is actually broken, and fail one that is actually fine. It
is checking something that is not what will be recorded.

# Theory (from zero)

### The client-side hooks, in firing order
Hooks are executable files in `.git/hooks/`. Git runs them at defined moments; a **non-zero exit
aborts** the operation.

| Hook | Fires | Typical use |
|---|---|---|
| `pre-commit` | before the commit message is requested | lint, format, quick tests |
| `prepare-commit-msg` | before the editor opens | pre-fill a template |
| `commit-msg` | after the message is written | validate format ([Chapter 25](25_Conventional_Commits.md)) |
| `post-commit` | after the commit is made | notifications; cannot block |
| `pre-rebase` | before a rebase | refuse rebasing a protected branch |
| `pre-push` | before objects are sent | block pushes to `main` ([Chapter 27](27_Pre_Push_Protection.md)) |
| `post-checkout` / `post-merge` | after switching / merging | rebuild dependencies |

Server-side hooks (`pre-receive`, `update`, `post-receive`) run on the host and *can* be
authoritative — but GitHub does not let you install them. That single fact is why so much of this
chapter is about client-side compromises.

### Hooks are never cloned — and that is deliberate
`.git/hooks/` is not part of the repository's content. `git clone` does not bring hooks across.

This is a **security decision**, not an oversight: if cloning a repo could install scripts that run
on your machine at your next commit, every clone would be a remote code execution risk.

The consequence is unavoidable: committed hooks must be **installed deliberately**, once per clone,
per machine. Either an installer script (`bash git-hooks/install.sh`), or:

```bash
git config core.hooksPath git-hooks    # point git at a tracked directory instead
```

`core.hooksPath` is neater — the hooks live in the repo and need no copying — but it is still a
*local config setting*, so it too must be set once per clone. There is no way around the one manual
step, and pretending otherwise is how teams end up with unprotected clones.

### The critical detail: lint the INDEX, not your files
`git commit` snapshots the index. So a pre-commit hook must check **staged** content:

```bash
git diff --cached --name-only --diff-filter=ACM     # staged Added/Copied/Modified
```

Not `git status`, not the filesystem. Consider the failure this prevents: you fix a bug (staged) and
leave a debug `print()` unstaged in the same file. A hook linting your *files* fails the commit for
a line that will not be committed. A hook linting the *index* passes — correctly.

The reverse case is worse: a violation is staged, but your working copy has been cleaned up. A
naive hook passes; the broken version is committed.

This also explains a behaviour that surprises people: the hook can pass while your working directory
still has a violation. That is correct. The gate protects **history**, not your desk.

### Speed is a feature
A hook that adds five seconds to every commit gets bypassed with `--no-verify` within a week, and
then it protects nothing. Two rules:

1. **Only check what changed.** Never lint the whole repo in a hook — that is CI's job.
2. **Budget under ~2 seconds.** If a check cannot fit, move it to `pre-push` or CI.

### The ratchet pattern
Adopting a rule on an existing codebase has a chicken-and-egg problem: 728 existing violations, and
a hook that blocks them all means nobody can commit anything.

The **ratchet** solves it: block only **newly added lines**.

```bash
git diff --cached --unified=0 -- "$f" | grep '^+' | grep -v '^+++'   # added lines only
```

Existing code is untouched, new drift is impossible, and the count can only fall. This is how you
adopt a standard mid-project without a big-bang migration — and it is exactly what this repository
does for its design system.

### `--no-verify` and why it should exist
`git commit --no-verify` skips `pre-commit` and `commit-msg`. `git push --no-verify` skips
`pre-push`.

That is a feature. A hook is a **helper**, not a security boundary: anyone can bypass it, and
sometimes should — a genuine emergency, or a commit of deliberately non-conforming content. Having
to type `--no-verify` makes the bypass a *decision* rather than an accident.

Which leads to the honest statement of what a client-side hook is: **advisory**. It catches
mistakes, not adversaries. Anything that must be guaranteed belongs in CI or in server-side
protection.

> 💡 **Samjho aise:** Hook = **darwaze pe khada chowkidar**. `pre-commit` commit se pehle rokta hai,
> `commit-msg` message dekhta hai, `pre-push` bhejne se pehle.
>
> Do baatein yaad rakho. Pehli: **chowkidar clone ke saath nahi aata** — `.git/hooks/` copy nahi
> hoti, aur ye jaan-boojh kar hai (warna kisi ka repo clone karne se uska script tumhare computer pe
> chal jaata). Isliye naye clone pe **installer chalana padta hai**.
>
> Doosri, aur zyada zaroori: chowkidar ko **thaila** (index) check karna chahiye, **mez** (working
> directory) nahi. Kyunki commit thaile ka hota hai. Mez dekhega toh galat faisla dega — kabhi sahi
> commit rok dega, kabhi galat commit jaane dega.
>
> Aur `--no-verify` ka rasta khula hai — jaan-boojh kar. Chowkidar madadgar hai, taala nahi.

# Real World Example (this repo)
This repository runs **two** pre-commit gates through the [`pre-commit`](https://pre-commit.com)
framework, configured in `django_inventory/.pre-commit-config.yaml`. Both illustrate the theory
above.

### Gate 1 — ruff on changed Python
```yaml
- id: ruff
  name: ruff (changed files · autofix · lenient F set)
  entry: django_inventory/env/bin/ruff check --force-exclude --fix
  language: system
  types: [python]
  files: ^django_inventory/.*\.py$
  exclude: ^django_inventory/(.*/migrations/|env/|staticfiles/)
```

Three deliberate choices:

- **`--fix`** — autofix what is mechanically fixable, so the hook *helps* rather than merely
  complaining.
- **A lenient rule set** — a strict linter on a large existing codebase produces noise, and noise
  produces `--no-verify`.
- **Migrations, `env/` and `staticfiles/` excluded** — generated code should not be judged by
  hand-written standards.

Note the config file lives in `django_inventory/`, not the monorepo root, with the reason written
in its own comment: the git root is a multi-project monorepo, and this config must never touch
sibling projects. Hence the invocation names the config explicitly:

```bash
django_inventory/env/bin/pre-commit install \
  --config django_inventory/.pre-commit-config.yaml
```

### Gate 2 — the design-system ratchet
```yaml
- id: ds-lint
  name: design-system lint (ratchet · new inline raw values)
  entry: bash django_inventory/scripts/ds_lint.sh --changed
  language: system
  pass_filenames: false
  files: ^django_inventory/config/.*\.html$
```

`scripts/ds_lint.sh` has two modes, and the split is the whole idea:

- **`--changed`** (the hook): scan only **added lines** in **staged** `.html` files. Block a new
  inline `#hex`, `font-size:Npx` or `border-radius:Npx`.
- **no argument** (reporting): count violations across all templates to track progress, and
  **always exit 0**.

The script's own comment states the intent: *"Existing code is NOT touched → safe to adopt
mid-migration (stops new drift without forcing a full migration)."* That is the ratchet, in the
project's own words. It also exempts the styleguide demo page, which intentionally showcases raw
values — an exemption worth having because the alternative is a rule people learn to ignore.

### The CI half — and the trick that makes it work
CI must enforce the same rule, or the hook is optional in practice. But `ds_lint.sh --changed`
reads the **staged index**, and in CI **nothing is staged** — so it would exit 0 and prove nothing.

`.github/workflows/ci.yml` solves that without forking the script:

```yaml
BASE="$(git merge-base "origin/${{ github.base_ref }}" HEAD)"
git reset --soft "$BASE"
bash django_inventory/scripts/ds_lint.sh --changed
```

`git reset --soft <merge-base>` re-presents **every commit in the PR as staged changes**
([Chapter 03](03_The_Three_Trees.md)). The linter then runs unmodified and sees exactly the lines
the PR adds. One rule, one implementation, two callers — instead of a second copy of the rule that
would drift.

That is the three-trees model used as a tool rather than merely understood.

# Visual Diagram
```
  git commit
      │
      ├─► pre-commit ──────► ruff --fix on STAGED *.py       ─┐
      │                      ds_lint.sh --changed on STAGED   │ non-zero
      │                      *.html (ADDED LINES only)        │ exit
      │                                                       ▼
      ├─► (message editor)                              COMMIT ABORTED
      │
      ├─► commit-msg ──────► Conventional Commits check (ch 25)
      │
      └─► commit created ──► post-commit (cannot block)

  git push
      └─► pre-push ────────► refuse `main` (ch 27)

  WHY THE INDEX, NOT YOUR FILES
  ─────────────────────────────
    working dir : bug fixed + a stray debug print()
    index       : bug fix ONLY                        ← this is what gets committed
    naive hook  : lints working dir → fails on a line that will NOT be committed
    correct hook: git diff --cached  → passes. Gate protects HISTORY, not your desk.

  THE RATCHET
  ───────────
    existing 728 violations   ──► untouched (blocking them = nobody can commit)
    newly ADDED lines         ──► blocked
    count can only go DOWN

  HOOKS ARE NOT CLONED (a security decision)
  ──────────────────────────────────────────
    clone ⇒ no hooks ⇒ unprotected until:
        bash git-hooks/install.sh        (copy them in)
      or git config core.hooksPath git-hooks   (point at a tracked dir)
    either way: ONCE PER CLONE. There is no way around the manual step.
```

# Practical — install, test, and understand the gates
```bash
cd /home/tech/umesh-personal

# 1. what gates exist?
cat django_inventory/.pre-commit-config.yaml

# 2. install the framework hook (note: config path is explicit — monorepo)
django_inventory/env/bin/pre-commit install \
  --config django_inventory/.pre-commit-config.yaml

# 3. and this repo's own hand-written hooks (ch 25, ch 27)
bash git-hooks/install.sh
ls -l "$(git rev-parse --git-path hooks)"

# 4. run every gate against everything (what CI effectively does)
django_inventory/env/bin/pre-commit run \
  --config django_inventory/.pre-commit-config.yaml --all-files

# 5. run them against only what is staged (what a commit does)
django_inventory/env/bin/pre-commit run \
  --config django_inventory/.pre-commit-config.yaml

# 6. SEE the index-vs-worktree distinction for yourself
echo 'import os' >> django_inventory/config/core/tests.py   # unused import (a ruff F401)
git add django_inventory/config/core/tests.py               # STAGED → the hook will see it
git diff --cached --name-only                               # exactly what the hook inspects
git restore --staged django_inventory/config/core/tests.py
git restore django_inventory/config/core/tests.py           # undo

# 7. the ratchet in reporting mode (all templates, always exit 0)
bash django_inventory/scripts/ds_lint.sh | tail -5

# 8. the deliberate escape hatch
git commit --no-verify -m "chore: bypass, and I know why"
```

Step 6 is the one to actually run. `git diff --cached --name-only` is *precisely* the hook's input,
and seeing that makes the whole chapter concrete.

# Production Walkthrough
1. **On every fresh clone**: `bash git-hooks/install.sh` **and** `pre-commit install`. Two systems —
   hand-written hooks for push/message policy, the framework for linting. Neither travels with the
   clone.
2. **Commit normally.** ruff autofixes trivia; the ratchet blocks new inline raw values.
3. **If a hook fails**, read the message. Autofixed files need re-staging (`git add`) because the
   hook changed them after you staged.
4. **If you must bypass**, use `--no-verify` and say why in the commit body. A silent bypass is the
   thing that erodes the gate.
5. **CI re-runs the same rules** — ruff plus the ratchet via the `reset --soft` trick — so the hook
   is a convenience, not the enforcement.
6. **Adopting a new rule**: add it in ratchet mode first (block new violations only), then reduce
   the backlog over time. A big-bang migration is how rules get abandoned.

# Debugging Guide

| Symptom | Cause | Fix |
|---|---|---|
| Hooks do nothing after cloning | `.git/hooks/` is never cloned | `bash git-hooks/install.sh`; `pre-commit install` |
| Hook not executable | missing `+x` | `chmod +x .git/hooks/<name>` (the installer does it) |
| Hook fails on a line you did not stage | it is linting the worktree, not the index | use `git diff --cached`; that is the bug |
| Autofix ran, commit still failed | the hook modified files after staging | `git add` the fixed files and re-commit |
| `pre-commit` cannot find the config | monorepo: config lives in `django_inventory/` | pass `--config django_inventory/.pre-commit-config.yaml` |
| Ratchet passes locally, fails in CI | CI stages the whole PR via `reset --soft` | run the same range locally: `git diff origin/main...HEAD` |
| Ratchet passes in CI, fails nothing ever | nothing staged in CI ⇒ silent exit 0 | that was the real bug; the `reset --soft` line is the fix |
| Everyone uses `--no-verify` | the hook is too slow or too noisy | narrow the rules, only check changed files, budget under 2 s |
| Hook works for you, not a colleague | they never installed it | that is the inherent limit; CI is the real gate |

# Performance Notes
- **Only check changed files.** `types: [python]` plus `files:` plus `exclude:` narrows the hook to
  a handful of paths per commit.
- **Budget ~2 seconds.** Beyond that, people bypass, and a bypassed hook has zero value.
- `pre-commit` caches its environments in `~/.cache/pre-commit`; the first run is slow, later runs
  are not.
- **`language: system`** here (using the project's own `env/bin/ruff`) avoids the framework building
  isolated environments — faster, at the cost of requiring the venv to exist.
- **The ratchet is cheap by construction**: it greps only added lines of staged HTML, not whole
  files, not the repo.
- Never put the test battery in `pre-commit` — 424 seconds per commit would be intolerable. That is
  what `pre-push` and CI are for.

# Security Considerations
- **Hooks are advisory, not a boundary.** `--no-verify` bypasses them, and `.git/hooks/` is local.
  Anything that must be guaranteed belongs in CI or server-side protection.
- **Hooks not being cloned is a security *feature*.** If cloning installed executable scripts,
  every clone would be an RCE risk. The manual install step is the price of that safety.
- **Never let a hook print a secret.** Hook output lands in terminals, CI logs and screenshots.
- **A hook is a poor secret-scanner but better than nothing.** A staged `.env` or `*.sql` is best
  blocked by `.gitignore` ([Chapter 07](07_Gitignore.md)); note `git add -f` bypasses that
  deliberately, which is why the PR template asks a human to check
  ([Chapter 23](23_CODEOWNERS_And_Templates.md)).
- **Review hook changes like code.** `git-hooks/` is an owned path in `CODEOWNERS`; a hook edit can
  disable a gate silently.
- **`git add` is when content enters the object store**, so a pre-commit hook is already *late* for
  secrets — the blob exists before the hook runs
  ([Chapter 05](05_How_Git_Stores_Everything.md)).

# Architecture Decisions
- **The `pre-commit` framework for linting, hand-written hooks for policy.** The framework handles
  file filtering, caching and autofix well; push and message policy are ten lines of bash and need
  no dependency.
- **Config lives in `django_inventory/`, not the monorepo root**, with the reason in its own
  comment: sibling projects must never be linted by this project's rules.
- **`language: system`** using the project's own `env/bin/ruff`, so local and CI run the *same*
  binary and version. A rule that fires in CI but not locally trains people to ignore CI.
- **A lenient rule set with `--fix`.** Adoption beats strictness: an autofixing, quiet hook survives;
  a noisy one gets bypassed.
- **The ratchet instead of a big-bang migration.** 728 existing violations could not block commits,
  so only new drift is blocked and the count can only fall.
- **`reset --soft` in CI rather than a second linter.** One rule, one implementation. A duplicated
  rule is a rule that will drift — and this project's core law is precisely "never duplicate
  knowledge".
- **`--no-verify` deliberately left available.** Making the bypass explicit is better than making it
  impossible; people who cannot bypass a bad gate delete it instead.

# Best Practices
- Install hooks as **step 1** of onboarding, and say so in `CONTRIBUTING.md`.
- Always inspect `git diff --cached`, never the working tree.
- Keep hooks under ~2 seconds. Move slow checks to `pre-push` or CI.
- Autofix where possible; a helpful hook is a kept hook.
- Adopt new rules in **ratchet** mode first.
- Mirror every hook rule in CI, and share the *same* implementation.
- Exempt generated code (migrations, `staticfiles/`, `env/`) explicitly.
- Treat `--no-verify` as legitimate but explain it in the commit body.

# Beginner Mistakes
- **Assuming hooks arrive with a clone** → they never do. New clone means unprotected.
- **Linting the working directory** → the hook judges content that will not be committed.
- **Forgetting to re-stage after autofix** → the hook fixed the file *after* you staged it.
- **Putting slow checks in `pre-commit`** → everyone bypasses within a week.
- **Blocking all existing violations when adopting a rule** → nobody can commit; the rule is
  reverted.
- **Hook rules stricter than CI's** → confusing; CI must be the authority.
- **Believing a hook enforces anything** → it is advisory. CI and server-side rules enforce.
- **Editing `.git/hooks/` directly** → untracked and lost on re-clone. Edit `git-hooks/` and
  reinstall.

# Interview Questions
- **Junior:** "What is a git hook?" — An executable script in `.git/hooks/` that git runs at a
  defined moment; a non-zero exit aborts the operation. `pre-commit` runs before a commit,
  `commit-msg` validates the message, `pre-push` runs before objects are sent.
- **Mid:** "Why are hooks not shared automatically?" — `.git/hooks/` is not repository content, and
  that is a security decision: if cloning installed runnable scripts, every clone would be a remote
  code execution risk. So hooks must be installed per clone, via an installer or
  `core.hooksPath` — and either way it is a manual step.
- **Senior:** "Your pre-commit hook lints the working directory. What breaks?" — It checks something
  other than what will be committed. Git commits the index, so a partially staged file makes the
  hook both over- and under-strict: it can fail a commit for an unstaged debug line, and pass a
  commit whose staged version is broken while your worktree is clean. The fix is
  `git diff --cached --name-only --diff-filter=ACM`, and the consequence to accept is that the hook
  may pass while your working directory still has a violation — correct, because the gate protects
  history.
- **Staff:** "Introduce a formatting standard to a 200k-line codebase without stopping the team." —
  Not with a big-bang reformat, because that destroys `git blame` and collides with every open
  branch. I would use a ratchet: block only newly **added** lines, leaving existing code untouched,
  so the violation count can only fall and nobody is blocked — this project does exactly that for
  its design system, and the script says so in its own comments. Then I would enforce the same rule
  in CI using the *same* implementation rather than a second copy, which for a staged-index-based
  script means making CI present the PR as staged (`git reset --soft $(git merge-base …)`) instead of
  forking the linter — two callers, one rule, no drift. And I would keep it fast and autofixing,
  because the real failure mode is not a missed violation, it is `--no-verify` becoming muscle memory;
  if bypass is common, the gate is the problem, not the people. Optionally
  `.git-blame-ignore-revs` for any one-off bulk reformat, so history stays readable.

### Why interviewers ask these — and the answer that separates levels
| Testing for | Weak answer | What lands |
|---|---|---|
| Do you know the mechanism? | "Hooks run scripts automatically." | Named hooks, defined firing points, non-zero exit aborts — and `.git/hooks/` is not cloned, by security design. |
| Index versus worktree? | "It checks my files before committing." | Commit snapshots the index, so the hook must read `git diff --cached`; otherwise it judges content that will not be recorded. |
| Can you roll out a standard? | "Reformat everything and enforce it." | Ratchet on added lines only, same implementation in CI, fast and autofixing — bypass frequency is the real metric. |

**The killer follow-up:** *"Can a pre-commit hook stop a secret entering the repository?"* — Not reliably, and it is already late: `git add` writes the blob into `.git/objects` before the hook ever runs, so the content is in the repo even if the commit is aborted. Layer it instead — `.gitignore` to prevent staging, a hook as a reminder, and CI plus review as the real gate — while remembering `git add -f` deliberately bypasses ignore rules. Naming the *ordering* problem is what separates people who have thought about hooks from people who have installed one.

# Revision Notes
- Hooks = executables in `.git/hooks/`; **non-zero exit aborts**. `pre-commit` · `commit-msg` · `pre-push`.
- **Hooks are NEVER cloned** — a security decision (clone would otherwise be RCE). Install per clone: `install.sh` or `core.hooksPath`.
- **Lint the INDEX**: `git diff --cached --name-only --diff-filter=ACM`. Commit snapshots the index, not your files.
- Consequence: the hook may pass while your worktree still has a violation. **Correct.**
- **Speed is a feature.** >2 s ⇒ `--no-verify` becomes habit ⇒ zero protection.
- **Ratchet** = block only newly ADDED lines; existing violations untouched; count can only fall.
- This repo: ruff (`--fix`, lenient, changed `.py`) + `ds_lint.sh --changed` (new inline `#hex`/`font-size:Npx`).
- CI reuses the SAME script via `git reset --soft $(git merge-base …)` — one rule, two callers.
- Hooks are **advisory**. CI and server-side rules are enforcement.

# Cheat Sheet
```bash
ls -l "$(git rev-parse --git-path hooks)"        # what is installed HERE
bash git-hooks/install.sh                        # this repo's hand-written hooks
git config core.hooksPath git-hooks              # alternative: point at a tracked dir

# the pre-commit framework (config lives in django_inventory/ — monorepo)
env/bin/pre-commit install   --config django_inventory/.pre-commit-config.yaml
env/bin/pre-commit run       --config django_inventory/.pre-commit-config.yaml            # staged only
env/bin/pre-commit run --all-files --config django_inventory/.pre-commit-config.yaml      # everything
env/bin/pre-commit uninstall

# what a hook must inspect
git diff --cached --name-only --diff-filter=ACM  # STAGED added/copied/modified
git diff --cached --unified=0 -- <file> \
  | grep '^+' | grep -v '^+++'                   # ADDED LINES only (the ratchet)

bash scripts/ds_lint.sh --changed                # ratchet mode (hook)
bash scripts/ds_lint.sh                          # report mode (always exit 0)

git commit --no-verify                           # skip pre-commit + commit-msg
git push   --no-verify                           # skip pre-push
```

# My ERP Section

| Gate | What it does here |
|---|---|
| Config | `django_inventory/.pre-commit-config.yaml` — deliberately **not** at the monorepo root, so sibling projects are never linted by this project's rules |
| `ruff` | `--force-exclude --fix`, lenient F set, `types: [python]`, on `^django_inventory/.*\.py$`, excluding `migrations/`, `env/`, `staticfiles/` |
| `ds-lint` | `bash scripts/ds_lint.sh --changed` on staged `config/**/*.html` — blocks **newly added** inline `#hex`, `font-size:Npx`, `border-radius:Npx`; styleguide page exempt |
| Ratchet rationale | the script's own comment: *"Existing code is NOT touched → safe to adopt mid-migration (stops new drift without forcing a full migration)"* |
| Report mode | `bash scripts/ds_lint.sh` with no argument counts violations across all templates and **always exits 0** |
| Hand-written hooks | `git-hooks/commit-msg` (Conventional Commits, ≤72-char subject, no trailing period) and `git-hooks/pre-push` (refuses `main`) — installed by `git-hooks/install.sh` |
| CI mirror | `.github/workflows/ci.yml` runs ruff, then `git reset --soft $(git merge-base origin/<base> HEAD)` so `ds_lint.sh --changed` sees the whole PR as staged and runs **unmodified** |
| Why not the battery | 2,033 tests take **424 s**; that belongs in CI, never in `pre-commit` |
| Ownership | `git-hooks/` and `.github/` are owned paths in `CODEOWNERS` — a hook edit can silently disable a gate |

# Practice Tasks
1. Run `ls -l "$(git rev-parse --git-path hooks)"`. Which hooks are installed on **this** clone?
2. Stage a file with an unused import, run `git diff --cached --name-only`, and confirm that is
   exactly what the hook would inspect. Then unstage and undo.
3. Create the index-versus-worktree situation deliberately: stage a clean fix, then add a `print()`
   without staging it. Commit. Confirm the hook does **not** complain about the unstaged line.
4. Run `bash scripts/ds_lint.sh` (report mode) and note the violation count. Then add a new inline
   `style="color:#fff"` to a template, stage it, and try to commit. Watch the ratchet fire.
5. Bypass it with `--no-verify`, then immediately `git reset --soft HEAD~1` to undo. Feel how easy
   the bypass is — that is why CI exists.
6. Read `.pre-commit-config.yaml` and explain every `files:` and `exclude:` pattern out loud.

# Homework
- Write a `pre-commit` hook from scratch (no framework) that rejects a staged file containing the
  string `TODO:` on an added line. Make it read the index only, and time it.
- Set `core.hooksPath` on a scratch clone and confirm the hooks work without copying. Then explain
  why this still does not make hooks travel with a clone.
- Pick a rule your own code violates and adopt it as a **ratchet**: block new violations only, and
  count the backlog. Watch the count fall over a week.
- Read `git help hooks` and find one hook this chapter did not cover that would be useful to you.
  `post-checkout` for rebuilding dependencies is a good candidate.

# Further Reading & Live Resources
- [Pro Git — Git Hooks](https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks) — every hook and when it fires; free
- [githooks manual](https://git-scm.com/docs/githooks) — the exact contract, arguments and exit-code behaviour of each hook
- [pre-commit.com](https://pre-commit.com/) — the framework: hook config, file filtering, caching
- [ruff documentation](https://docs.astral.sh/ruff/) — the linter used here, including `--fix` behaviour
- [Ratcheting in software engineering](https://qntm.org/ratchet) — a short, clear essay on the pattern
- [`.git-blame-ignore-revs`](https://docs.github.com/en/repositories/working-with-files/using-files/viewing-and-understanding-files#ignore-commits-in-the-blame-view) — how to keep `git blame` useful after a bulk reformat
