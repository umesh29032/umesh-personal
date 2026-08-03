---
id: git-course-36-monorepo-submodules-subtrees
type: lesson
status: active
owner: handwritten
scope: git — monorepo vs submodules vs subtrees; multi-project repository layout and its costs
anchors: .gitignore, .github/workflows/ci.yml, .pre-commit-config.yaml, CONTRIBUTING.md
verified: 2026-08-03
---

# 36 — Monorepo, Submodules & Subtrees (this repo is a monorepo, and it has cost us)

> Part of [Git Course](00_COURSE_OVERVIEW.md). Prev: [35 — Bisect](35_Bisect.md). Next: [37 — Large Files & Repo Performance](37_Large_Files_And_Performance.md).

# Learning Objectives
By the end of this chapter you can:
- explain the three ways to hold multiple projects: monorepo, submodules, subtrees
- explain what a submodule actually stores, and why "detached HEAD" is its normal state
- name the concrete costs a monorepo imposes on tooling — with real examples from this repository
- explain why a `.gitignore` in a subdirectory guards only its own subtree, and what that cost here
- configure CI `paths` filters and per-project tool configs correctly in a monorepo
- choose deliberately, and say what you are trading away

# Purpose
Most git courses cover submodules as a feature and stop. This chapter is different because **this
repository is a monorepo**, and that decision has produced real, traceable bugs — including a security
incident. So the material is not "here are three options"; it is "here is what the choice actually
costs, measured".

The three options:

- **Monorepo** — one repository, several projects in subdirectories.
- **Submodules** — one repository *references* another at a specific commit.
- **Subtrees** — another repository's files are *copied in*, history and all.

They are not interchangeable, and the failure modes differ sharply.

# The Problem
You have several projects. A Django ERP, some DSA practice, an old Flask experiment, notes.

Put them in one repository and you get: one clone, one history, atomic cross-project commits — and a
subtle new class of bug, because **every tool that assumes "repository == project" is now slightly
wrong**. Linters lint the wrong files. Ignore rules cover less than you think. CI runs on changes it
should not care about.

Split them and you get: clean boundaries — and coordination overhead every single time a change spans
two of them.

Neither is free. The mistake is choosing without knowing which bill you have agreed to pay.

# Theory (from zero)

### Monorepo
One repository, several projects as directories:

```
/home/tech/umesh-personal/          ← the git repository
├── django_inventory/               ← the ERP (the real project)
├── Django_app/                     ← an old practice app
├── DSA/                            ← algorithm practice
├── sw obsidian/                    ← notes (gitignored)
├── .github/workflows/ci.yml        ← MUST be at the root
├── CONTRIBUTING.md
└── .gitignore                      ← guards EVERYTHING below it
```

**Buys:** one clone, one history, one issue tracker; atomic commits spanning projects; trivially easy
cross-project refactors; nothing to version-bump between components.

**Costs — and these are the ones nobody warns you about:**

1. **Tool configs must be scoped.** A linter at the root lints *everything*, including projects with
   different standards.
2. **CI must filter by path**, or every commit anywhere triggers every pipeline.
3. **`.gitignore` scoping becomes a hazard** — see below. This is the big one.
4. **`.github/` only works at the root.** GitHub reads workflows from the repository root only, so a
   per-project workflow directory does not exist.
5. **History is mixed.** `git log` shows every project; you need `-- <path>` constantly.
6. **The repo is as large as all projects combined**, forever
   ([Chapter 37](37_Large_Files_And_Performance.md)).

### The `.gitignore` scoping hazard — a real incident
This is worth its own section, because it caused a security incident in this repository
([Chapter 33](33_Secrets_And_Leaks.md)).

**A `.gitignore` file only applies to its own directory and below.** So:

```
django_inventory/.gitignore:114  →  db_backups/     guards django_inventory/** ONLY
```

That rule was correct. It is why the ERP has never leaked a database dump. But `Django_app/` is a
**sibling**, not a child — so it was never covered, and two `pg_dump` files were committed there while
the repository was public.

**The rule was not missing. It was scoped too narrowly.** That is a much more insidious failure than
having no rule, because everything *looks* protected: there is a `.gitignore`, it contains the right
pattern, and it demonstrably works — in one subtree.

The fix is a **root-level** `.gitignore`, which covers every sibling, present and future:

```gitignore
*.sql
*.dump
db_backups/
node_modules/
```

**Monorepo lesson, stated generally: protective rules belong at the root; permissive exceptions belong
in subdirectories.** Never the other way round.

### Submodules
A submodule is a **pointer**: your repository records another repository's URL and one exact commit.

```bash
git submodule add https://github.com/them/lib.git vendor/lib
```

That creates two things:

```
.gitmodules            ← tracked: the URL and path mapping
vendor/lib             ← a gitlink: a special tree entry storing a COMMIT HASH
```

The crucial detail: **the parent repo stores a commit hash, not a branch.** So a submodule is normally
in **detached HEAD** ([Chapter 10](10_Creating_And_Switching_Branches.md)) — that is not a mistake, it
is the design. You pinned a commit; a commit is not a branch.

Consequences that bite everyone at least once:

```bash
git clone <repo>                       # submodule directories are EMPTY
git clone --recurse-submodules <repo>  # ...unless you ask
git submodule update --init --recursive        # fix an existing clone
git submodule update --remote           # move the pointer to the submodule's latest
```

**Buys:** genuine separation — separate history, separate access control, exact pinning of third-party
code.

**Costs:** every teammate must remember `--recurse-submodules`; a change spanning parent and submodule
is **two commits in two repositories in a required order**; and `git status` in the parent shows only
"submodule modified", not what changed.

**Use when:** you consume a repository you do not control, or you must pin third-party code exactly,
or the components genuinely have different access requirements.

### Subtrees
A subtree **copies** another repository's files (optionally with history) into a subdirectory.

```bash
git subtree add --prefix=vendor/lib https://github.com/them/lib.git main --squash
git subtree pull --prefix=vendor/lib https://github.com/them/lib.git main --squash
git subtree push --prefix=vendor/lib https://github.com/them/lib.git main
```

**Buys:** clones work normally — no extra flags, nothing for teammates to remember. The files are just
files.

**Costs:** merge commits from the vendored history clutter your log (hence `--squash`); pushing changes
back upstream is awkward; and the vendored code's history is now permanently in your repository's size.

**Use when:** you want vendored code that behaves like your own files and you rarely push changes back.

### Comparison
| | Monorepo | Submodule | Subtree |
|---|---|---|---|
| Clone | one command | needs `--recurse-submodules` | one command |
| Extra state | none | `.gitmodules` + a gitlink | none |
| Cross-project atomic commit | ✅ yes | ❌ two repos, ordered | ✅ yes |
| Independent history | ❌ | ✅ | ⚠️ merged in |
| Per-project access control | ❌ | ✅ | ❌ |
| Tooling friction | **paths, configs, CI filters** | detached HEAD, clone flags | log clutter |
| Repo size | all projects, forever | parent stays small | includes vendored history |
| Teammate can get it wrong | rarely | **often** | rarely |

> 💡 **Samjho aise:** **Monorepo** = ek bade ghar mein kai kamre. Ek chaabi se sab khulta hai, ek hi
> jagah sab kuch. Par **safai ka niyam** kamre-kamre ka hota hai — aur yahi humein kaata: `.gitignore`
> sirf **apne kamre aur uske andar** kaam karta hai. ERP ke kamre mein niyam tha, `Django_app` ke kamre
> mein nahi — aur wahin se database dump git mein chala gaya.
>
> Toh monorepo ka pakka niyam: **rokne wale niyam sabse upar (root) rakho**, chhoot dene wale niyam
> neeche. Ulta kabhi nahi.
>
> **Submodule** = doosre ghar ka **pata + kaunsi tareekh ki haalat**. Ghar tumhara nahi, tum sirf likh
> ke rakhte ho "us din wala version chahiye". Isliye clone karne pe wo kamra **khaali** milta hai —
> `--recurse-submodules` bolna padta hai. Aur wo hamesha "detached HEAD" pe rehta hai — kharaabi nahi,
> design hai: tumne commit pin ki thi, branch nahi.
>
> **Subtree** = doosre ghar ka saaman **utha ke apne ghar rakh liya**. Clone normal chalta hai, koi
> flag nahi. Par ab uska poora saamaan tumhare ghar ka wazan ban gaya.

# Real World Example (this repo)
This is a **monorepo**, and the costs are documented rather than theoretical.

```bash
cd /home/tech/umesh-personal && ls -d */ | head -6
# DSA/  Django_app/  django_inventory/  ...
git submodule status        # (empty — no submodules here)
```

The layout note lives in `docs/campaign_contracts/PHASE_00_SAFETY_SNAPSHOT.md`:

> *"Git toplevel `/home/tech/umesh-personal` — a personal **MONO-REPO**; the project is the
> `django_inventory/` subdirectory; sibling dirs (`Django_app`, `DSA`, `sw obsidian`, …) are unrelated
> personal content."*

### Cost 1 — the security incident (root cause: `.gitignore` scoping)
Covered above and in [Chapter 33](33_Secrets_And_Leaks.md). Two `pg_dump` files committed in
`Django_app/` because the ignore rule lived in `django_inventory/.gitignore`. Fixed with a root
`.gitignore`, verified as blocking at **five** separate paths.

### Cost 2 — every tool config needs explicit scoping
`.pre-commit-config.yaml` lives in `django_inventory/`, **not** at the root, and says why in its own
comment:

> *"Co-located in `django_inventory/` because the git root is a multi-project monorepo; this config
> never touches sibling projects."*

Which forces an awkward invocation — the config path must be named every time:

```bash
django_inventory/env/bin/pre-commit install \
  --config django_inventory/.pre-commit-config.yaml
```

And the hook's file filters are anchored to the project:

```yaml
files: ^django_inventory/.*\.py$
exclude: ^django_inventory/(.*/migrations/|env/|staticfiles/)
```

Without those anchors, ruff would lint `Django_app/` and `DSA/` — projects with entirely different
standards ([Chapter 26](26_Pre_Commit_Hooks.md)).

### Cost 3 — CI must live at the root and filter by path
GitHub only reads `.github/workflows/` from the **repository root**, so `ci.yml` sits at
`/home/tech/umesh-personal/.github/workflows/ci.yml` while every step runs elsewhere:

```yaml
on:
  pull_request:
    paths: ['django_inventory/**', '.github/workflows/ci.yml']
defaults:
  run:
    working-directory: django_inventory
```

Two monorepo-specific mechanisms in four lines:

- **`paths`** — editing `DSA/` starts **no** run. Without it, every commit anywhere burns free Actions
  minutes ([Chapter 28](28_CI_With_GitHub_Actions.md)).
- **`working-directory`** — every step runs in the project, not the repo root.

There is even a monorepo footgun inside the ratchet step: `ds_lint.sh --changed` runs
`cd "$(git rev-parse --show-toplevel)"` because *"git reports paths repo-root-relative, so we cd there
and keep them consistent"* — then filters with `grep -E '/config/.*\.html$'` to stay inside the project.

### Cost 4 — a dead CODEOWNERS rule, caused by path anchoring
`.github/CODEOWNERS` contained:

```
/deploy/                    @umesh29032        ← DEAD. never matched anything.
/django_inventory/deploy/   @umesh29032        ← the real path
```

A leading slash anchors to the **repository root**, and `deploy/` lives under `django_inventory/`. The
first rule matched nothing, silently — a rule that *reads* as coverage and provides none. GitHub never
warns about this. It was caught by a path-existence check
([Chapter 23](23_CODEOWNERS_And_Templates.md)) and removed with the reason recorded.

### Cost 5 — `.git` carries every project forever
`.git` is **97 MB** with **25,975 packed objects**. A large part of that is `Django_app/` — including
**2,952 `node_modules` files** that were tracked until they were untracked in this session. Those blobs
remain in history permanently, because history is append-only
([Chapter 37](37_Large_Files_And_Performance.md)).

### Why the monorepo is nonetheless the right call here
One developer, personal projects, no per-project access control needed, and no consumer of these
projects as libraries. Submodules would add clone flags and detached-HEAD confusion for zero benefit.
The costs above are all **tooling configuration**, and each has been paid once and documented.

The honest summary: a monorepo trades *boundary enforcement* for *convenience*, and every bug in this
chapter is a boundary that had to be re-established by hand.

# Visual Diagram
```
  MONOREPO — one repo, sibling projects            ← THIS REPOSITORY
  ─────────────────────────────────────
   /home/tech/umesh-personal/         .git   97 MB · 25,975 packed objects
   ├── .gitignore                     ← guards EVERYTHING below  ✅ (added after the leak)
   ├── .github/workflows/ci.yml       ← MUST be at root; paths: ['django_inventory/**']
   ├── CONTRIBUTING.md · CHANGELOG.md · git-hooks/
   ├── django_inventory/              ← the real project
   │   ├── .gitignore   :114 db_backups/   ← guards THIS SUBTREE ONLY
   │   └── .pre-commit-config.yaml          ← scoped: files: ^django_inventory/.*\.py$
   ├── Django_app/       ← sibling. NOT covered by django_inventory/.gitignore
   │   └── myproject/mydb_backup_*.sql      ← THE LEAK LANDED HERE
   └── DSA/  ·  sw obsidian/ (ignored)

   ⚠ THE RULE:  protective rules at the ROOT.  permissive exceptions below.
                never the reverse.

  SUBMODULE — a POINTER to another repo at one commit
  ──────────────────────────────────────────────────
   parent repo
   ├── .gitmodules        (tracked: url + path)
   └── vendor/lib         → gitlink: stores COMMIT HASH abc123
                            ⇒ normally DETACHED HEAD (by design, not a bug)
   git clone <repo>                    → vendor/lib is EMPTY
   git clone --recurse-submodules       → populated
   cross-cutting change = TWO commits in TWO repos, in order

  SUBTREE — files COPIED IN
  ─────────────────────────
   vendor/lib/  = ordinary files. clone works normally, no flags.
   cost: vendored history inflates YOUR repo; pushing back upstream is awkward
```

# Practical — inspect and configure a monorepo correctly
```bash
cd /home/tech/umesh-personal

# 1. what shape is this repo?
git rev-parse --show-toplevel        # the REAL root (not your cwd)
ls -d */ | head
git submodule status                 # empty = no submodules

# 2. THE monorepo hazard: which .gitignore actually governs a path?
git check-ignore -v django_inventory/x.sql     # names FILE:LINE:PATTERN
git check-ignore -v Django_app/x.sql           # the sibling — is it covered?
git check-ignore -v DSA/x.sql                  # and future siblings?
# no output + exit 1 ⇒ NOT ignored ⇒ that path is unprotected

# 3. every .gitignore in the repo, and therefore every scope
find . -name .gitignore -not -path './*/env/*' -not -path './*/node_modules/*'

# 4. per-project history (you will type `-- <path>` a lot)
git log --oneline -5 -- django_inventory/
git log --oneline -5 -- Django_app/

# 5. size per project — where is .git actually going?
git count-objects -vH
for d in django_inventory Django_app DSA; do
  printf '  %-18s %s files tracked\n' "$d" "$(git ls-files "$d" | wc -l)"
done

# 6. CI path filters — does an unrelated edit trigger a run?
grep -A3 'paths:' .github/workflows/ci.yml

# 7. CODEOWNERS anchoring — find DEAD rules (a leading / means repo root)
awk '!/^#/ && NF {print $1}' .github/CODEOWNERS | while read -r p; do
  c="${p#/}"; c="${c%/}"
  [ -e "$c" ] || [ -n "$(git ls-files "$c*" 2>/dev/null | head -1)" ] \
    || echo "  ✗ DEAD RULE: $p"
done

# ── SUBMODULES (not used here — practise in a scratch repo) ─────────────────
git submodule add https://github.com/them/lib.git vendor/lib
cat .gitmodules
git ls-tree HEAD vendor/lib          # mode 160000 = a gitlink (a commit, not a tree)
git submodule update --init --recursive
git submodule update --remote        # move the pointer to upstream's latest
git submodule foreach 'git switch main'   # escape detached HEAD in every submodule

# ── SUBTREES ────────────────────────────────────────────────────────────────
git subtree add  --prefix=vendor/lib <url> main --squash
git subtree pull --prefix=vendor/lib <url> main --squash
```

Command 2 is the monorepo command. `git check-ignore -v` tells you *which file and which line* governs
a path — the only way to actually know whether a sibling directory is protected.

# Production Walkthrough
Setting up a monorepo so it does not produce this chapter's bugs:

1. **Put protective rules at the root.** `.gitignore` with `*.sql`, `*.dump`, `.env`, `node_modules/`.
   Verify with `git check-ignore -v` at several paths **including a sibling that does not exist yet**.
2. **Scope every tool config to its project.** Anchor linter patterns (`^project/.*\.py$`) and
   co-locate configs, naming the reason in a comment.
3. **Filter CI by path** and set `working-directory`. Free minutes are finite.
4. **Anchor CODEOWNERS paths correctly**, and run a dead-rule check — a leading slash means repo root.
5. **Document the layout** somewhere a newcomer will read, because `git clone` gives no hint that the
   project is a subdirectory.
6. **Expect `-- <path>`** in every `git log` you run.
7. **Re-verify after adding a project.** A new sibling directory inherits root rules automatically —
   which is exactly why the rules belong at the root.

For submodules instead: put `--recurse-submodules` in the clone instructions, teach `git submodule
update --init --recursive`, and accept that cross-cutting changes are two ordered commits.

# Debugging Guide

| Symptom | Cause | Fix |
|---|---|---|
| Ignore rule works in one directory, not a sibling | a `.gitignore` guards only its own subtree | move the rule to the **root** — this repo's real incident |
| Linter lints an unrelated project | tool config at the root, or unanchored patterns | anchor `files:` to the project prefix |
| CI runs on every commit anywhere | no `paths` filter | add `paths: ['project/**']` |
| CI cannot find `manage.py` | steps run at the repo root | `working-directory: project` |
| Workflow file ignored entirely | `.github/` must be at the **repository root** | move it; there is no per-project alternative |
| CODEOWNERS rule never fires | leading `/` anchors to repo root; the path is nested | fix the path; run a dead-rule check |
| `git log` is full of unrelated projects | one history for everything | `git log -- <path>` |
| Submodule directory empty after clone | submodules are not fetched by default | `git clone --recurse-submodules`, or `git submodule update --init --recursive` |
| Submodule on a detached HEAD | **normal** — the parent pins a commit, not a branch | `git submodule foreach 'git switch main'` if you intend to develop in it |
| Submodule change "not committed" in the parent | the parent must commit the new gitlink | commit inside the submodule, push it, then commit the parent |
| Repo huge and you only need one project | monorepo size is cumulative | sparse-checkout, or a partial clone ([Ch 37](37_Large_Files_And_Performance.md)) |

# Performance Notes
- **`.git` is the sum of all projects, forever.** 97 MB here, 25,975 packed objects — including
  `Django_app/`'s `node_modules` blobs, which persist in history even after untracking.
- **`git status` scales with tracked file count** across the whole repo, not just your project. Fine at
  ~2,400 files; `core.fsmonitor true` helps at 100k+.
- **CI `paths` filters are the biggest saving.** Without one, editing `DSA/` would run a 424-second
  battery for nothing.
- **`git sparse-checkout`** lets you materialise only one project's files while keeping full history —
  the standard monorepo mitigation:
  ```bash
  git sparse-checkout init --cone
  git sparse-checkout set django_inventory
  ```
- **Submodules keep the parent small** — that is their genuine performance advantage.
- **Subtrees inflate your repo** with the vendored history; `--squash` limits it to one commit's worth.

# Security Considerations
- **The `.gitignore` scoping hazard is a security issue, not a tidiness issue.** It is how two database
  dumps entered this repository's public history. Protective rules go at the **root**
  ([Chapter 33](33_Secrets_And_Leaks.md)).
- **A dead CODEOWNERS rule reads as coverage and provides none.** Path anchoring in a monorepo makes
  this easy to get wrong; verify every rule resolves.
- **One repository means one access boundary.** Anyone with read access reads *every* project. If one
  needs different access, that is the strongest argument for splitting.
- **`git submodule update` executes hooks and can run arbitrary code** from the submodule; git has had
  submodule-related CVEs. Only add submodules you trust.
- **Submodule URLs are tracked in `.gitmodules`** — a malicious PR can repoint a submodule at a
  different repository. Review `.gitmodules` changes as carefully as workflow changes.
- **CI at the root sees every project.** A workflow with secrets triggered by a change in an unrelated
  directory is a wider blast radius than it looks; `paths` filters reduce it.
- **`.github/` is an owned path in `CODEOWNERS`** for this reason.

# Architecture Decisions
- **Monorepo, deliberately.** One developer, personal projects, no per-project access control, nobody
  consuming these as libraries. Submodules would add clone flags and detached-HEAD confusion for no
  benefit.
- **Protective rules at the root, exceptions below.** Adopted *after* the leak; the root `.gitignore`
  now covers every sibling, present and future.
- **Tool configs co-located and anchored.** `.pre-commit-config.yaml` in `django_inventory/` with the
  reason in its own comment, plus `files:`/`exclude:` anchors so siblings are never linted.
- **CI at the root with `paths` + `working-directory`.** Forced by GitHub for the location; the filters
  are the deliberate part.
- **CODEOWNERS paths fully qualified**, with a dead-rule check documented in
  [Chapter 23](23_CODEOWNERS_And_Templates.md) after `/deploy/` was found matching nothing.
- **No submodules, no subtrees.** No third-party code is vendored, so neither mechanism earns its
  complexity.
- **The layout is documented** in `PHASE_00_SAFETY_SNAPSHOT.md`, because a clone gives no hint that the
  project is a subdirectory.

# Best Practices
- **Protective rules at the repository root.** Always. Exceptions can live deeper.
- Verify ignore coverage with `git check-ignore -v` on **sibling** paths, not just your own.
- Anchor every tool config to its project prefix; comment why.
- Filter CI by `paths` and set `working-directory`.
- Fully qualify CODEOWNERS paths, and check for dead rules.
- Document the layout where a newcomer will find it.
- Use `git log -- <path>` habitually.
- For submodules: put `--recurse-submodules` in the README, and review `.gitmodules` changes closely.
- Consider `sparse-checkout` when the repo outgrows the project you work on.

# Beginner Mistakes
- **Assuming a subdirectory `.gitignore` protects the whole repo** → the actual root cause of this
  repository's dump leak.
- **A linter config at the root of a monorepo** → lints projects with different standards.
- **No CI `paths` filter** → every commit anywhere burns minutes.
- **Forgetting `working-directory`** → CI cannot find `manage.py`.
- **Putting `.github/` inside a project** → GitHub reads it from the root only; it is silently ignored.
- **CODEOWNERS paths not root-anchored** → dead rules that read as coverage.
- **`git clone` without `--recurse-submodules`** → empty submodule directories and confusion.
- **Treating a submodule's detached HEAD as a bug** → it is the design; the parent pins a commit.
- **Committing inside a submodule and expecting the parent to know** → the parent must commit the new
  gitlink, after you push the submodule.
- **Choosing submodules for projects you own and change together** → you have bought coordination
  overhead for nothing.

# Interview Questions
- **Junior:** "What is a monorepo?" — One repository containing several projects as subdirectories. You
  get one clone, one history and atomic cross-project commits; the cost is that tooling which assumes
  "one repo, one project" must be configured explicitly — linters, CI path filters, ignore rules.
- **Mid:** "What does a submodule actually store?" — A **gitlink**: a tree entry (mode `160000`) holding
  one commit hash, plus the URL and path in `.gitmodules`. Because it pins a commit rather than a
  branch, the submodule is normally in detached HEAD — that is the design. And submodules are not
  fetched by default, hence `--recurse-submodules`.
- **Senior:** "Monorepo, submodules or subtrees — how do you choose?" — By what the boundary is *for*.
  Submodules when you consume code you do not control or need per-component access control and exact
  pinning; you pay clone flags and two-repo ordered commits. Subtrees when you want vendored code that
  behaves like your own files and rarely push back; you pay repository size and log clutter. A monorepo
  when the components change together and are owned by the same people; you pay tooling configuration
  — and that bill is bigger than people expect, because every rule that was implicitly per-repository
  now has to be scoped by hand.
- **Staff:** "A monorepo team keeps having 'the rule didn't apply' bugs. Diagnose." — That is almost
  always **scope inversion**, and it has one general shape: a protective rule placed in a subdirectory,
  where it silently covers only its own subtree while appearing to cover the project. This repository
  hit exactly that: `django_inventory/.gitignore` correctly ignored `db_backups/`, which is why the ERP
  never leaked a dump, but `Django_app/` is a *sibling* — so two `pg_dump` files with user emails and
  password hashes were committed while the repo was public. The rule was not missing; it was correct
  and narrow, which is far more dangerous than absent, because everything looks protected. The same
  inversion produced a dead `CODEOWNERS` rule — a leading slash anchors to the repository root, so
  `/deploy/` matched nothing while reading as coverage, and GitHub never warns. So the policy I would
  impose is directional: **protective rules at the root, permissive exceptions below, never the
  reverse** — and then make it verifiable rather than aspirational, because a rule you have not tested
  at a *sibling* path is a rule you are guessing about. Concretely that means `git check-ignore -v` at
  several paths including one that does not exist yet, a dead-rule check for CODEOWNERS, and treating
  each such bug as owing a check rather than a fix.

### Why interviewers ask these — and the answer that separates levels
| Testing for | Weak answer | What lands |
|---|---|---|
| Do you know the trade-off? | "A monorepo keeps everything together." | Atomic cross-project commits and one clone, paid for in tooling scope: linters, CI `paths`, and ignore-rule reach. |
| Do you know what a submodule is? | "A repo inside a repo." | A gitlink storing one commit hash plus `.gitmodules`; hence detached HEAD by design and empty dirs without `--recurse-submodules`. |
| Can you diagnose systemic bugs? | "They should be more careful." | Scope inversion: protective rules must live at the root; a correct-but-narrow rule is more dangerous than a missing one, and must be verified at sibling paths. |

**The killer follow-up:** *"Your `.gitignore` has `*.sql` and a `.sql` file still got committed. Explain."* — Either the file was already tracked, since ignore rules never apply to tracked paths; or someone used `git add -f`; or — the monorepo answer — the rule lives in a subdirectory and the file is in a sibling, so it was never in scope. `git check-ignore -v <path>` settles it in one command by naming the file and line that governs. This repository was bitten by the third case, which is why the rule now lives at the root.

# Revision Notes
- **Monorepo** = one repo, sibling projects. Buys atomic cross-project commits + one clone; costs **tooling scope**.
- **A `.gitignore` guards ONLY its own directory and below.** ⇒ protective rules at the **ROOT**, exceptions below. **Never the reverse.**
- This repo's leak: `django_inventory/.gitignore:114` was correct but narrow; `Django_app/` is a **sibling** ⇒ 2 dumps committed publicly.
- **`.github/` only works at the repo root.** Use `paths:` + `working-directory:`.
- CODEOWNERS: a **leading `/` anchors to repo root** ⇒ `/deploy/` was a **dead rule** (real path `django_inventory/deploy/`). GitHub never warns.
- Tool configs must be anchored: `files: ^django_inventory/.*\.py$`.
- **Submodule** = a **gitlink** (mode `160000`) storing ONE commit hash + `.gitmodules`. **Detached HEAD is normal.** Empty without `--recurse-submodules`.
- **Subtree** = files copied in. Clone works normally; your repo carries the vendored history.
- `git check-ignore -v <path>` = the monorepo debugging command (names FILE:LINE:PATTERN).
- Mitigation for size: **`git sparse-checkout set <project>`**.

# Cheat Sheet
```bash
git rev-parse --show-toplevel              # the REAL repo root
git check-ignore -v <path>                 # WHICH file:line:pattern governs it  ← the monorepo one
find . -name .gitignore                    # every ignore scope in the repo
git log --oneline -- <path>                # per-project history
git ls-files <dir> | wc -l                 # tracked files per project
git count-objects -vH                      # total size (all projects, forever)

# monorepo CI (root .github/ only)
# on: pull_request: paths: ['django_inventory/**']
# defaults: run: working-directory: django_inventory

# only materialise one project (full history, fewer files)
git sparse-checkout init --cone
git sparse-checkout set django_inventory
git sparse-checkout disable

# submodules
git submodule add <url> vendor/lib
cat .gitmodules
git ls-tree HEAD vendor/lib                # mode 160000 = gitlink (a commit)
git clone --recurse-submodules <url>
git submodule update --init --recursive    # fix an existing clone
git submodule update --remote              # move the pointer to upstream latest
git submodule foreach 'git switch main'    # leave detached HEAD
git submodule status

# subtrees
git subtree add  --prefix=vendor/lib <url> main --squash
git subtree pull --prefix=vendor/lib <url> main --squash
git subtree push --prefix=vendor/lib <url> main
```

# My ERP Section

| Fact | This repository |
|---|---|
| Shape | **monorepo** — root `/home/tech/umesh-personal`; the ERP is `django_inventory/` |
| Siblings | `Django_app/` (old practice app), `DSA/`, `sw obsidian/` (gitignored) |
| Submodules | **none** (`git submodule status` is empty) |
| Documented in | `docs/campaign_contracts/PHASE_00_SAFETY_SNAPSHOT.md` |
| **Cost 1 — security** | `django_inventory/.gitignore:114` ignored `db_backups/` but a `.gitignore` guards only its subtree ⇒ 2 `pg_dump` files committed in the **sibling** `Django_app/` while public ([Ch 33](33_Secrets_And_Leaks.md)) |
| The fix | monorepo-root `.gitignore`: `*.sql`, `*.dump`, `*.sql.gz`, `db_backups/`, `backups/`, `node_modules/` — verified blocking at **5** paths |
| **Cost 2 — configs** | `.pre-commit-config.yaml` co-located in `django_inventory/`, *"never touches sibling projects"*; anchors `files: ^django_inventory/.*\.py$` |
| **Cost 3 — CI** | `.github/` must be at root ⇒ `paths: ['django_inventory/**']` + `working-directory: django_inventory`; `ds_lint.sh` does `cd "$(git rev-parse --show-toplevel)"` then filters `/config/.*\.html$` |
| **Cost 4 — dead rule** | `.github/CODEOWNERS` had `/deploy/` (root-anchored) while deploy is `django_inventory/deploy/` — matched nothing, silently. Removed, reason recorded ([Ch 23](23_CODEOWNERS_And_Templates.md)) |
| **Cost 5 — size** | `.git` **97 MB**, **25,975** packed objects; includes `Django_app/`'s 2,952 `node_modules` blobs, permanent in history ([Ch 37](37_Large_Files_And_Performance.md)) |
| Verdict | correct choice for one developer with no per-project access needs — the costs are tooling configuration, each paid once and documented |

# Practice Tasks
1. Run `git check-ignore -v django_inventory/x.sql` and `git check-ignore -v Django_app/x.sql`. Both
   should be blocked now — then read which file and line does it.
2. Reproduce the incident: in a scratch repo, put `*.sql` in `sub/.gitignore`, then create
   `other/x.sql`. Confirm with `check-ignore` that it is **not** ignored. That is the whole bug, in
   thirty seconds.
3. Run the CODEOWNERS dead-rule loop. Then add a deliberately wrong path and confirm it is caught.
4. Count tracked files per top-level directory (Practical step 5) and see how much of this repo is not
   the ERP.
5. Try `git sparse-checkout set django_inventory` in a `/tmp` clone. Note the working tree shrinks
   while `git log` still shows everything.
6. In a scratch repo, add a real submodule. Run `git ls-tree HEAD <path>` and find mode `160000`. Then
   clone that repo *without* `--recurse-submodules` and observe the empty directory.

# Homework
- Write the monorepo checklist for a project of your own: root protective rules, anchored tool configs,
  CI `paths`, qualified CODEOWNERS, documented layout. Then verify each item rather than assuming it.
- Take one repository you own that uses submodules and write down honestly what the boundary buys you.
  If the answer is "nothing", converting to a subtree or a plain directory is a real simplification.
- Read `git help submodule` on `--recurse-submodules` for `fetch`, `pull` and `checkout`, and set
  `submodule.recurse=true` globally. Then explain why it is not the default.
- Estimate what fraction of this repo's 97 MB `.git` belongs to `Django_app/`. Then read
  [Chapter 37](37_Large_Files_And_Performance.md) and decide whether it is worth acting on.

# Further Reading & Live Resources
- [Pro Git — Submodules](https://git-scm.com/book/en/v2/Git-Tools-Submodules) — the canonical treatment, including the pitfalls; free
- [git-submodule reference](https://git-scm.com/docs/git-submodule) — every subcommand, and `submodule.recurse`
- [git-subtree reference](https://git-scm.com/docs/git-subtree) — add, pull, push, `--squash`
- [git-sparse-checkout](https://git-scm.com/docs/git-sparse-checkout) — the standard monorepo size mitigation
- [gitignore reference](https://git-scm.com/docs/gitignore) — **precedence and scoping**, which is what this chapter's incident turned on
- [GitHub Docs — workflow paths filters](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions#onpushpull_requestpaths) — the CI half of monorepo hygiene
- [Monorepo tools overview](https://monorepo.tools/) — a fair survey of the tooling ecosystem if a monorepo grows past one team
