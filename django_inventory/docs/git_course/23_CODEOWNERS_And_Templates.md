---
id: git-course-23-codeowners-and-templates
type: lesson
status: active
owner: handwritten
scope: GitHub — CODEOWNERS, PR/issue templates, labels; encoding review policy into the repo
anchors: .github/CODEOWNERS, .github/pull_request_template.md, .github/dependabot.yml
verified: 2026-08-03
---

# 23 — CODEOWNERS & PR Templates (encoding policy into the repo)

> Part of [Git Course](00_COURSE_OVERVIEW.md). Prev: [22 — Code Review](22_Code_Review.md). Next: [24 — Branching Strategies](24_Branching_Strategies.md).

# Learning Objectives
By the end of this chapter you can:
- write a `CODEOWNERS` file and predict which rule wins for a given path
- explain why **last matching rule wins**, and why that inverts the usual ordering instinct
- write a PR template that changes reviewer behaviour instead of adding ceremony
- explain what CODEOWNERS does on a *free private* repo — and what it does not
- decide when a policy belongs in a file versus in a person's head
- keep templates short enough that people actually fill them in

# Purpose
[Chapter 22](22_Code_Review.md) covered how to review well. This chapter is about making good
review the **default** rather than something that depends on who is awake.

Two files do most of that work:

- **`.github/CODEOWNERS`** — who must look at which paths
- **`.github/pull_request_template.md`** — what every PR must state before anyone reads the diff

The underlying idea is bigger than either file: **policy that lives only in someone's head is not
policy.** Written down, it survives holidays, onboarding, and your own forgetfulness six months
from now.

# The Problem
Reviews decay toward the easy comments. Left to itself a review becomes naming, formatting and
style — because those are visible in seconds — while the expensive questions go unasked:

- Does this write money outside an approved service?
- Did a permission gate widen?
- Is the *failure* mode tested, or only the happy path?
- Were the docs updated, or is that "later"?
- Does the new UI work at 360px?

Nobody decides to skip those. They just do not come to mind at 6pm on a Friday. And "remember to
check money paths" is not a mechanism — it is a hope.

A second problem, specific to small teams: with one developer, *who reviews what* seems obvious.
It stops being obvious the moment a second person joins, and by then nobody has written it down.

# Theory (from zero)

### CODEOWNERS: a path-to-reviewer map
A plain text file at `.github/CODEOWNERS` (or repo root, or `docs/`). Each line is a
[gitignore-style pattern](07_Gitignore.md) followed by one or more owners:

```
*                                   @umesh29032
/django_inventory/config/expense/   @umesh29032
```

When a PR touches a matching path, GitHub can request that owner's review automatically and — if
branch protection is configured — require it.

### The rule that surprises everyone: LAST match wins
Unlike most config formats, CODEOWNERS is evaluated so that the **last** matching line governs.
So the general rule goes at the **top** and specifics go **below** it:

```
*                    @default-owner          ← general FIRST
/config/expense/     @money-owner            ← specific LAST, so it wins
```

Get the order backwards and your specific rules are silently overridden by the catch-all. Nothing
errors; the wrong person is simply requested. This is the single most common CODEOWNERS mistake.

Pattern notes worth knowing:

| Pattern | Matches |
|---|---|
| `*` | everything |
| `*.py` | any Python file, at any depth |
| `/deploy/` | the `deploy` directory **at the repo root** (leading slash anchors) |
| `deploy/` | any directory named `deploy`, at any depth |
| `/config/*/migrations/` | one directory level between — not a recursive match |
| `docs/**` | everything under `docs`, recursively |

Unlike `.gitignore`, CODEOWNERS has **no negation** — there is no `!pattern`. You cannot say
"everyone except". You can only add a later, more specific rule.

### The honest free-tier limitation
**CODEOWNERS automatic review assignment is a paid feature on private repositories.** It is free
on public repos, and included with Pro/Team/Enterprise. On a private repo on the free plan, GitHub
will not auto-request the owners listed in your file.

That is a real limitation, and this project's response is to commit the file anyway, because it
still does three things:

1. It is the **written record** of who owns which part of the system — exactly what a reviewer
   needs before approving a money path.
2. The PR template **points at it**, so ownership gets checked by a human instead of a robot.
3. The moment the repo goes public, or a plan is ever bought, automatic assignment starts working
   with **zero further changes**.

Writing the limitation into the file's own comments — rather than shipping a file that quietly does
nothing — is the difference between documentation and decoration.

### PR templates: the questions the process asks
`.github/pull_request_template.md` is prefilled into every new PR's description box. Its value is
not the checkboxes; it is that **the risky questions get asked by the process** rather than
remembered by a person.

Two design rules, learned the hard way by every team that has tried this:

- **Short enough to fill in.** A 40-item checklist gets ticked without reading, which is worse than
  no checklist because it manufactures false confidence.
- **Ask for evidence, not assertions.** "Tests pass ✓" is a claim. `Ran 2033 tests … OK` is
  evidence. Design the field so the honest answer requires having actually looked.

A useful third: make **"N/A and why"** an explicit option. An unticked box with no explanation is
ambiguous — did they consider it and decide it does not apply, or never read it? Requiring a reason
removes the ambiguity.

You can also have multiple templates (`.github/PULL_REQUEST_TEMPLATE/feature.md` plus a `?template=`
query parameter) and issue templates with structured YAML forms. For a one-to-two person repo, one
good template beats five that nobody picks between.

> 💡 **Samjho aise:** CODEOWNERS = **"kaunsa kamra kiska hai"** ki list. Koi us kamre ko chhoo raha
> hai? Malik ko bulao. Aur niyam ulta hai jo log sochte hain: **aakhri milta hua line jeetti hai** —
> isliye aam niyam **upar**, khaas niyam **neeche**. Ulta likha toh chup-chaap galat aadmi bulaya
> jaayega, error bhi nahi aayega.
>
> PR template = **sawaal jo process poochta hai**, insaan ke yaad rakhne pe nahi chhodta. Paise
> kahan likhe? Permission kis role ka badla? Mobile pe dekha? Ye sawaal Friday shaam ko dimaag mein
> nahi aate — isliye likhwa liye.
>
> Aur choti list rakho. 40 sawaal ka matlab hai bina padhe tick — jo bilkul na hone se bhi bura hai.

# Real World Example (this repo)
Both files exist here, and both are shaped by what this codebase has actually been bitten by.

### `.github/CODEOWNERS` — ordered general → specific
```
# Default: the owner reviews everything not claimed below.
*                                           @umesh29032

# ── Money. The highest-risk surface in the system. ──
/django_inventory/config/expense/                       @umesh29032
/django_inventory/config/expense/services/              @umesh29032
/django_inventory/config/production/services/           @umesh29032

# ── Access control. A widened gate is a silent, permanent privilege grant. ──
/django_inventory/config/accounts/services/             @umesh29032
/django_inventory/config/inventory/middleware.py        @umesh29032

# ── Migrations. Irreversible against real data. ──
/django_inventory/config/*/migrations/                  @umesh29032

# ── Deploy + CI. A mistake here breaks production or leaks a secret. ──
/deploy/                                                @umesh29032
/.github/                                               @umesh29032
/git-hooks/                                             @umesh29032
/.gitignore                                             @umesh29032

# ── Frozen architecture. Change only with an explicit owner ruling. ──
/django_inventory/docs/PRODUCT_DESIGN_DOCUMENT.md       @umesh29032
/django_inventory/docs/adr/                             @umesh29032
/django_inventory/CLAUDE.md                             @umesh29032
```

Every owner is currently the same person, which looks redundant — and is not. The file's real job
here is **classification**: it names the five categories of change that carry outsized risk in this
system. That list is useful to a reviewer today and to a second developer tomorrow.

Note `/.gitignore` is an owned path. That is not fussiness: a weakened ignore rule is how two
database dumps entered this repository's public history ([Chapter 07](07_Gitignore.md)).

### `.github/pull_request_template.md` — evidence, not assertions
The template asks, in order:

1. **What & why** — the *problem* first, because a reviewer who understands the problem can judge
   whether the solution fits.
2. **How it was verified** — with `Ran ___ tests … OK` as a fill-in-the-number field, plus
   "browser-tested, and say which roles you logged in as".
3. **Project rules** — rule 4 (service-layer writes), 5 (single-writer per ledger table),
   6 (`permission_service`, no raw `is_superuser`), 11 (mobile + tablet + desktop), 12 (docs in the
   same PR).
4. **Money & permissions impact** — two questions answered **explicitly, even when the answer is
   "none"**.
5. **Risk & rollback.**
6. **Screenshots**, including a 360px mobile shot for any UI change.
7. A **reviewer** checklist in a `<details>` block — separated because it is not the author's job.

Point 4 is the local adaptation that matters most. In this codebase settlement is the only
money-write boundary, and a new write path outside an approved single-writer service is a **STOP**,
not a review comment. Silence on that question is indistinguishable from "no impact", so the
template refuses to let it be silent.

The reviewer block also asks a question born of real damage: *"Any secret, dump, `.env` or data file
in the diff? The root `.gitignore` blocks `*.sql`/`*.dump`/`node_modules` — check nothing was
force-added past it."* `git add -f` deliberately still works ([Chapter 07](07_Gitignore.md)), so a
human has to look.

### The third file in `.github/`
`.github/dependabot.yml` belongs to the same family — policy encoded as config rather than
intention. Weekly pip updates, monthly Actions updates, patch bumps **grouped into one PR** so CI
runs once instead of five times, and Django's minor/major upgrades explicitly ignored with the
reason written in a comment (this codebase has 26 `CheckConstraint(check=)` usages, and Django 5.1
renamed that argument to `condition=` — so a 5.1 bump is a code migration, not a version bump).
See [Chapter 32](32_Dependabot_And_Supply_Chain.md).

# Visual Diagram
```
  .github/
  ├── CODEOWNERS                 who must look at which paths
  ├── pull_request_template.md   what every PR must state
  ├── dependabot.yml             dependency policy as config
  └── workflows/ci.yml           the automated gates (ch 28)

  CODEOWNERS EVALUATION — last match wins
  ───────────────────────────────────────
    *                          @owner     ← general FIRST
    /config/expense/           @money     ← specific LAST → WINS for that path
                                             ▲
    reversed order ⇒ `*` silently overrides the specific rule. No error.

    PR touches config/expense/services/expense_service.py
        │
        ├─ matches `*`                  → @owner
        └─ matches /config/expense/     → @money      ← LAST match governs

  FREE PRIVATE REPO REALITY
  ─────────────────────────
    auto-request reviewers from CODEOWNERS ......... PAID  ✗
    the file as a written ownership record ......... FREE  ✓
    template pointing a human at it ................ FREE  ✓
    works instantly if repo goes public / plan bought ✓

  TEMPLATE DESIGN
  ───────────────
    short enough to fill in          long checklist ⇒ ticked unread ⇒ false confidence
    ask for EVIDENCE not assertions  "Ran 2033 tests … OK"  >  "tests pass ✓"
    allow "N/A and why"              unticked + no reason = ambiguous
```

# Practical — build and test both files
```bash
cd /home/tech/umesh-personal

# 1. read what exists
cat .github/CODEOWNERS
cat .github/pull_request_template.md

# 2. which CODEOWNERS rule wins for a given path? reason it out by LAST match
grep -nE '^[^#]' .github/CODEOWNERS

# 3. CODEOWNERS patterns are gitignore-style — test one with git itself
#    (a cheap way to check a pattern matches what you think)
git ls-files 'django_inventory/config/expense/**' | head -3
git ls-files 'django_inventory/config/*/migrations/*' | head -3

# 4. every owned path should actually exist — a typo is a rule that never fires
awk '!/^#/ && NF {print $1}' .github/CODEOWNERS | while read -r p; do
  clean="${p#/}"; clean="${clean%/}"
  if [ -e "$clean" ] || git ls-files --error-unmatch "$clean" >/dev/null 2>&1 \
     || [ -n "$(git ls-files "$clean*" | head -1)" ]; then
    printf '  ✓ %s\n' "$p"
  else
    printf '  ✗ NO MATCH (dead rule): %s\n' "$p"
  fi
done

# 5. does the template load? (it must be at one of GitHub's known paths)
ls .github/pull_request_template.md .github/PULL_REQUEST_TEMPLATE.md 2>/dev/null

# 6. see the template applied for real
gh pr create --base main --head feat/x --web    # opens the browser with it prefilled
```

Step 4 is the check nobody runs: a CODEOWNERS path with a typo is a **silently dead rule**. GitHub
does not warn you, and the owner is simply never requested.

# Production Walkthrough
1. **Add the general rule first.** `*  @owner`, so nothing is unowned.
2. **Identify your genuine risk categories** and give each a section with a one-line comment
   explaining *why* it is risky. Here: money, access control, migrations, deploy/CI, frozen
   architecture.
3. **Order general → specific**, because last match wins.
4. **Verify every path resolves** (step 4 above). Dead rules are worse than no rules — they look
   like coverage.
5. **Write the template around your real failure history**, not a generic checklist. This one asks
   about money and permissions because that is where this project has been bitten.
6. **Keep it short** and require evidence.
7. **State the free-tier limitation in the file's own comments**, so nobody assumes auto-assignment
   is happening.
8. **Revisit after each incident.** A postmortem that does not change a gate or a template question
   will produce the same incident again.

# Debugging Guide

| Symptom | Cause | Fix |
|---|---|---|
| Owners never requested on a private repo | auto-assignment is **paid** there | expected; template asks a human, or make the repo public / upgrade |
| Specific rule ignored, catch-all applied | rules ordered specific → general | **last match wins** — move `*` to the top |
| A rule never fires | path typo, or wrong anchoring | `/deploy/` = root only; `deploy/` = any depth. Run the path-existence check |
| `CODEOWNERS is not valid` in GitHub's UI | unknown user/team, or bad syntax | owners must have repo access; check the error GitHub shows on the file |
| Template not prefilled | wrong filename or location | `.github/pull_request_template.md` (or repo root, or `docs/`) |
| Template filled in but meaningless | too long, or asks for assertions | shorten; convert claims into fill-in-the-number evidence fields |
| Tried to exclude a path from an owner | CODEOWNERS has **no negation** | add a later, more specific rule instead |
| Fork PRs do not request owners | forks cannot always resolve owners | review manually; the fork flow is deliberate here ([Ch 20](20_Forks_And_The_Fork_Flow.md)) |

# Performance Notes
- Both files are read by GitHub, not by git — **zero** cost to clone, checkout or CI time.
- CODEOWNERS is evaluated per changed path on PR open. Thousands of rules on a huge monorepo can
  measurably slow PR creation; a few dozen is free.
- A very large template makes the PR body long, which makes the description harder to scan — a
  human cost rather than a machine one, and the more important of the two.
- Grouping Dependabot patch updates (as `dependabot.yml` does here) is a real CI-minute saving:
  one PR, one battery run, instead of five ([Chapter 28](28_CI_With_GitHub_Actions.md)).
- `.github/` is owned by CODEOWNERS itself, so changes to the policy files are themselves reviewable.

# Security Considerations
- **`.gitignore` is an owned path here** for a concrete reason: a weakened ignore rule is how two
  `pg_dump` files entered this repository's public history. Changing that file should never be a
  drive-by.
- **`.github/workflows/` must be owned.** A workflow edit can exfiltrate secrets, and workflow
  changes in a PR are a known attack path. Anyone who can silently modify CI can bypass every gate.
- **CODEOWNERS is advisory without branch protection.** It requests review; only branch protection
  can *require* it — and that is paid on private repos. Do not confuse a request with a gate.
- **The reviewer checklist explicitly asks for force-added data files**, because `git add -f`
  deliberately bypasses the ignore rules.
- **Migrations are owned** because they are irreversible against real data — the one category where
  "revert the PR" does not undo the damage.
- **An owner must have repo access** or the rule is invalid and silently non-functional.

# Architecture Decisions
- **Commit CODEOWNERS even though auto-assignment is paid here.** It documents ownership, the
  template routes a human to it, and it activates for free if the repo's visibility or plan ever
  changes. The alternative — omitting it — loses the classification benefit for no gain.
- **Classify by risk, not by directory.** The sections are money, access control, migrations,
  deploy/CI, frozen architecture — the categories that actually cause incidents, rather than a
  mechanical mirror of the folder tree.
- **One template, not five.** A one-to-two person repo does not benefit from template selection;
  it benefits from one template short enough to be filled in honestly.
- **Money and permissions are mandatory fields.** Silence is indistinguishable from "no impact",
  and both are places where this project has real scar tissue.
- **Evidence over assertion.** `Ran ___ tests … OK` as a fill-in field rather than a "tests pass"
  checkbox, because a number requires having looked.
- **The reviewer checklist is separated** into a `<details>` block, so the author is not asked to
  do the reviewer's job and the review criteria are still visible to both.
- **State limitations inside the files.** A config file that quietly does nothing is worse than no
  file, because it reads as coverage.

# Best Practices
- General rule first, specific rules after. **Last match wins.**
- Verify every CODEOWNERS path actually resolves; a typo is a dead rule.
- Own `.github/`, `deploy/` and `.gitignore` — the paths that can disable your other protections.
- Keep the template short; convert every assertion into evidence.
- Offer "N/A and why" so an unticked box is never ambiguous.
- Write the *why* for each ownership section, in a comment, for the next reader.
- Update the template after incidents; that is how a postmortem becomes a mechanism.
- Say plainly, in the file, which parts of this need a paid plan.

# Beginner Mistakes
- **Ordering specific → general** → the catch-all silently wins. No error, wrong reviewer.
- **Assuming CODEOWNERS *requires* review** → it only requests; requiring needs branch protection,
  which is paid on private repos.
- **A 40-line checklist** → ticked without reading, producing confidence nobody earned.
- **Asking for assertions** → "tests pass ✓" tells you nothing; a pasted count does.
- **Typos in paths** → dead rules that look like coverage.
- **Expecting negation** (`!pattern`) → CODEOWNERS has none; add a more specific later rule.
- **Leaving `.github/workflows/` unowned** → the CI files that enforce everything else become
  editable without review.
- **Never revisiting the template** → it ossifies around problems you no longer have while missing
  the ones you do.

# Interview Questions
- **Junior:** "What does a CODEOWNERS file do?" — Maps path patterns to owners so GitHub can
  request their review when a PR touches those paths. Patterns are gitignore-style, and it lives at
  `.github/CODEOWNERS`.
- **Mid:** "Which rule wins when several match?" — The **last** matching rule, which is why general
  patterns go at the top and specific ones below. Reversing that order silently hands the path back
  to the catch-all with no error, and it is the most common mistake with the file.
- **Senior:** "How do you get CODEOWNERS-style guarantees on a free private repo?" — You do not get
  the guarantee, and saying so is the answer. Auto-assignment and required reviews are paid there,
  so I commit the file for its documentation value, have the PR template point a human at it, and
  compensate where enforcement genuinely matters: client-side hooks for push protection,
  contributors on Read access working from forks so they cannot merge at all, and CI as a visible
  gate. Each layer's weakness gets written down — a `pre-push` hook only binds on machines where it
  was installed — because an unstated gap is the one that bites.
- **Staff:** "Design review policy for a team that keeps shipping the same class of bug." — Policy in
  people's heads does not survive Friday evenings, so it has to become mechanism, and the mechanism
  has to be targeted at the failure classes you have actually seen rather than a generic checklist.
  Concretely: make the risky dimensions mandatory template fields so they cannot pass in silence
  (money, permissions), own the paths that can disable other protections (`.github/`, `.gitignore`,
  migrations), and convert each recurring bug into a *gate* rather than a reminder — a
  missing-migration check, a docs-drift check, an AST-based guard for the specific bug shape.
  I would also keep the checklist deliberately short, because a long one is ticked unread and
  manufactures false confidence, and treat every postmortem as owing exactly one change to a gate
  or a template question; if a postmortem changes neither, the same bug is scheduled to recur.

### Why interviewers ask these — and the answer that separates levels
| Testing for | Weak answer | What lands |
|---|---|---|
| Do you know the file's semantics? | "It lists who owns the code." | Gitignore-style patterns, and **last match wins** — so general at the top, specific below, or the catch-all silently overrides. |
| Request versus requirement? | "CODEOWNERS forces a review." | It only requests; requiring needs branch protection, which is paid on private repos — name the gap rather than assume it away. |
| Can you turn policy into mechanism? | "We'd add a checklist." | Mandatory fields for risky dimensions, own the paths that disable other gates, and convert each recurring bug into a check — short list, evidence not assertions. |

**The killer follow-up:** *"Your CODEOWNERS has a path typo. What happens?"* — Nothing visible. The rule never matches, the owner is never requested, and GitHub does not warn you — so the file reads as coverage while providing none. The strong answer adds the fix: verify every path actually resolves in the repo, because a dead rule is more dangerous than a missing one.

# Revision Notes
- `.github/CODEOWNERS` = path patterns → owners; gitignore-style syntax; **no negation**.
- **LAST matching rule wins** ⇒ general at the top, specific below.
- `/deploy/` = root-anchored · `deploy/` = any depth · `/config/*/migrations/` = one level.
- **Auto-assignment is PAID on private repos.** Commit the file anyway: record + template pointer + free activation later.
- CODEOWNERS **requests**; only branch protection **requires**.
- A path typo = a **silently dead rule**. Verify every path resolves.
- Own `.github/`, `deploy/`, `.gitignore`, migrations — the paths that can disable other protections.
- Templates: short · evidence not assertions (`Ran 2033 tests … OK`) · "N/A and why" allowed.
- This repo asks **money & permissions explicitly, even when the answer is none.**

# Cheat Sheet
```bash
# CODEOWNERS — .github/CODEOWNERS (or repo root, or docs/)
*                         @owner        # general FIRST (last match wins!)
*.py                      @py-owner     # any depth
/deploy/                  @ops          # ROOT-anchored
deploy/                   @ops          # any depth
/config/*/migrations/     @dba          # exactly one directory level
docs/**                   @docs-team    # recursive
# no negation: there is no !pattern — add a more specific later rule

cat .github/CODEOWNERS                      # read it
grep -nE '^[^#]' .github/CODEOWNERS         # just the active rules, in order
git ls-files '<pattern>' | head             # does this pattern match what you think?

# templates GitHub recognises
.github/pull_request_template.md            # the one
.github/PULL_REQUEST_TEMPLATE/feature.md    # multiple, chosen via ?template=feature.md
.github/ISSUE_TEMPLATE/bug.yml              # structured issue forms

gh pr create --base main --web              # see the template prefilled
gh pr create --base main --fill             # reuse commit messages as the body
```

# My ERP Section

| File | What it encodes here |
|---|---|
| `.github/CODEOWNERS` | Five risk categories with a *why* comment each: **money** (`config/expense/`, `production/services/`), **access control** (`accounts/services/`, `inventory/middleware.py`), **migrations** (`config/*/migrations/`), **deploy+CI** (`deploy/`, `.github/`, `git-hooks/`, `.gitignore`), **frozen architecture** (PDD, `adr/`, `CLAUDE.md`) |
| Why `.gitignore` is owned | a weakened ignore rule is how two `pg_dump` files entered public history ([Ch 07](07_Gitignore.md)) |
| Free-tier note | auto-assignment is paid on private repos — stated in the file's own comments so it never reads as active coverage |
| `.github/pull_request_template.md` | what&why · verified (`Ran ___ tests … OK` + which roles browser-tested) · rules 4/5/6/11/12 · **money & permissions answered explicitly** · risk & rollback · 360px mobile shot · reviewer checklist in `<details>` |
| The money question | settlement is the only money-write boundary; a new write path outside an approved single-writer service is a **STOP**, not a comment |
| The secret question | reviewer must confirm no `.sql`/`.env`/dump was **force-added** past `.gitignore` (`git add -f` still works by design) |
| `.github/dependabot.yml` | weekly pip · monthly actions · patch bumps grouped into one PR (one CI run) · Django minor/major **ignored** with the reason in a comment (26 `CheckConstraint(check=)` vs 5.1's `condition=`) |

# Practice Tasks
1. Read `.github/CODEOWNERS` and, for `django_inventory/config/expense/services/expense_service.py`,
   list every rule that matches and name the one that **wins**.
2. Run the path-existence check from the Practical section. Confirm no dead rules — then add a
   deliberately misspelled path, re-run, and watch it get caught.
3. Reverse two rules (put `*` last) in a scratch copy and explain, out loud, what would now happen
   to the money paths.
4. Open `.github/pull_request_template.md` and fill it in for the last change you made anywhere.
   Note which questions you cannot answer — those are your real gaps.
5. Write a CODEOWNERS rule that owns every migration file in the project. Verify it with
   `git ls-files`.
6. Try to write a rule meaning "all of `docs/` except `docs/archive/`". Discover there is no
   negation, then solve it the CODEOWNERS way.

# Homework
- Write a CODEOWNERS file for a project of your own, ordered correctly, with a one-line *why*
  comment per section. Then verify every path resolves.
- Shorten this project's PR template by three questions without losing coverage. Defend each cut.
  Being able to argue *against* process is part of designing it.
- Read GitHub's docs on issue forms (`.github/ISSUE_TEMPLATE/*.yml`) and design a bug form whose
  required fields would have caught a bug you personally shipped.
- For each of the last three bugs you fixed anywhere, write the one template question or CI gate
  that would have caught it. That exercise is how policy gets built from evidence rather than
  imitation.

# Further Reading & Live Resources
- [GitHub Docs — About code owners](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners) — syntax, precedence, and the plan requirements stated plainly
- [GitHub Docs — Creating a pull request template](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/creating-a-pull-request-template-for-your-repository) — locations and multiple templates
- [GitHub Docs — Syntax for issue forms](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms) — structured YAML forms
- [Google's Code Review Developer Guide](https://google.github.io/eng-practices/review/) — the best free writing on making review a system rather than a habit
- [Dependabot configuration options](https://docs.github.com/en/code-security/dependabot/dependabot-version-updates/configuration-options-for-the-dependabot.yml-file) — grouping, ignoring, scheduling
- [gitignore pattern format](https://git-scm.com/docs/gitignore) — the pattern syntax CODEOWNERS borrows (minus negation)
