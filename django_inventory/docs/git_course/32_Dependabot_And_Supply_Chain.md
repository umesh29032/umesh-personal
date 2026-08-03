---
id: git-course-32-dependabot-and-supply-chain
type: lesson
status: active
owner: handwritten
scope: GitHub — Dependabot, dependency pinning, lockfiles, supply-chain risk
anchors: .github/dependabot.yml, requirements.txt, requirements-dev.txt, .github/workflows/ci.yml
verified: 2026-08-03
---

# 32 — Dependabot & Supply Chain (a pin is a decision to stay behind)

> Part of [Git Course](00_COURSE_OVERVIEW.md). Prev: [31 — Signed Commits](31_Signed_Commits.md). Next: [33 — Secrets & Leaks](33_Secrets_And_Leaks.md).

# Learning Objectives
By the end of this chapter you can:
- explain why **pinning** exact versions is correct *and* creates an obligation
- configure Dependabot for pip and GitHub Actions, and explain every field you set
- explain why grouping patch updates saves real money on a free plan
- decide when to **ignore** an update, and why that decision must carry its reason
- name the main supply-chain attack shapes and which ones a version bump does not address
- say which parts of GitHub's supply-chain tooling are free on a private repo and which are not

# Purpose
Your code is a small fraction of what runs in production. This project ships Django, psycopg2,
allauth, Pillow, reportlab, openpyxl and a long tail of transitive dependencies. Every one of them
is code you did not write, running with your database credentials.

Dependencies also decay. Not because they change — pinned versions never change — but because the
world moves: a security advisory lands, and your pinned version is now the vulnerable one.

**Pinning is correct**: it makes deploys reproducible. But a pin is also a **decision to stay on
that version until somebody acts**. Without a mechanism, "somebody acts" means "somebody remembers",
and a published Django security release can sit unapplied for months.

Dependabot is that mechanism, and it is free on every plan.

# The Problem
Two failure modes, opposite in shape.

**Failure 1: never upgrade.** A CVE is published for your Django version. Nobody is watching PyPI.
Six months later you upgrade under pressure, and now you are crossing several minor versions at
once — so the security fix arrives bundled with breaking changes, at exactly the moment you wanted a
small, safe change.

**Failure 2: upgrade blindly.** Auto-merge every bump, and a transitive dependency's behaviour change
reaches production without anyone reading it. Dependency updates *are* code changes; they deserve the
same gate as your own commits.

The correct position is between them: **automated proposals, automated verification, human approval.**
Dependabot opens a PR; CI runs the full battery against it; a green PR is an upgrade with evidence
rather than hope.

# Theory (from zero)

### Pinning, ranges and lockfiles
Three ways to say which version you want:

| Style | Example | Reproducible? | Gets fixes? |
|---|---|---|---|
| Unpinned | `Django` | ❌ every install may differ | accidentally |
| Range | `Django>=5.0,<5.1` | ⚠️ partly | patches, silently |
| **Pinned** | `Django==5.0.1` | ✅ exactly | **only when you act** |

Pinned plus a bot is the good combination. Ranges look like the best of both, but they make your
build non-deterministic: the same commit installs different code on different days, which turns
"works on my machine" into a genuinely unanswerable question.

A **lockfile** (`poetry.lock`, `package-lock.json`, `Pipfile.lock`) goes further by pinning the whole
*transitive* tree — every dependency of every dependency, with hashes. This project uses plain
`requirements.txt` with exact pins for direct dependencies, which pins the top layer but leaves
transitive versions to the resolver. That is a real gap, and worth naming rather than glossing over:
`pip install -r requirements.txt` today and in six months can produce different transitive versions.
`pip-compile` (pip-tools) or `pip freeze` with hashes closes it.

### What Dependabot actually does
A GitHub service that reads your manifest files, compares against upstream releases, and opens a PR
per update — branch, changed manifest, changelog excerpt, compatibility score.

Three things worth knowing:

1. **It is free on every plan**, including private repos. Unlike branch protection or CODEOWNERS
   auto-assignment ([Chapter 27](27_Pre_Push_Protection.md)), there is no paid tier here. This is the
   one piece of supply-chain hygiene with no excuse.
2. **Security updates and version updates are different features.** Security updates fire on
   advisories, regardless of schedule. Version updates are the routine `dependabot.yml` schedule.
3. **It only proposes.** Merging is yours — which is the correct division of labour.

### Configuration, field by field
```yaml
version: 2
updates:
  - package-ecosystem: pip
    directory: /django_inventory        # where the manifest lives (monorepo!)
    schedule:
      interval: weekly
      day: monday
      time: '06:00'
      timezone: Asia/Kolkata
    open-pull-requests-limit: 5
    commit-message:
      prefix: chore                     # Conventional Commits (ch 25)
      include: scope
    groups:
      patch-updates:
        patterns: ['*']
        update-types: [patch]
    ignore:
      - dependency-name: Django
        update-types: [version-update:semver-minor, version-update:semver-major]
```

- **`directory`** — the path *containing* the manifest. In a monorepo this is not `/`, and getting it
  wrong means Dependabot silently finds nothing.
- **`open-pull-requests-limit`** — a cap. Five open dependency PRs is a review queue; twenty is
  noise, and noise gets ignored wholesale.
- **`commit-message.prefix`** — makes Dependabot's commits Conventional Commits, so the `commit-msg`
  hook accepts them and the CHANGELOG generator sees them with no special-casing
  ([Chapters 25](25_Conventional_Commits.md), [30](30_Changelog.md)).
- **`groups`** — bundles many updates into **one** PR. This is a money decision, below.
- **`ignore`** — refuse a class of update. Only defensible **with the reason recorded**.

### Grouping is a free-tier money decision
Ungrouped, five patch bumps mean five PRs — and five CI runs. This project's battery is **2,033 tests
in 424 seconds**, so five runs is ~35 minutes of the ~2,000 free Actions minutes available monthly on
a private repo. Grouped, it is one PR and one run.

Grouping patches is also low-risk by definition: a patch release should be backwards-compatible. Group
patches, review minors individually, and treat majors as projects.

### When to ignore an update — and the obligation that comes with it
`ignore` is legitimate when an upgrade is a **code migration**, not a version bump. But an ignore
without a reason is indistinguishable from neglect, so the reason belongs in a comment next to it.

This project has exactly such a case, and it is a good example: **Django 5.1 renamed
`CheckConstraint(check=)` to `condition=`.** Measured against this codebase right now:

```bash
grep -rn 'CheckConstraint(' config --include=*.py | wc -l          # 147 total
grep -rn 'CheckConstraint(' config --include=*.py | grep -c /migrations/   # 76 in migrations
grep -rn -A2 'CheckConstraint(' config --include=*.py | grep -c 'check='   # 147 using check=
grep -rn -A2 'CheckConstraint(' config --include=*.py | grep -c 'condition=' # 0 using condition=
```

**147 call sites, every one on the 5.0 `check=` API, zero already migrated** — 71 hand-written in
models and 76 inside historical migrations. So a 5.1 bump is not a version change; it is a code
change across 71 model definitions, and the 76 in migrations are frozen history that must keep
working too. It is ignored deliberately, with that written down, until the work is scheduled.

The `CLAUDE.md` note is blunt about the pinning reason too: *"Django==5.0.1 — pinned to
installed/required version; code uses `CheckConstraint(check=)` (5.0 API, renamed `condition=` in
5.1+)."*

Critically, ignoring **minor and major** still lets **patch** security updates through. That is the
right shape: stay on 5.0.x and keep receiving 5.0.x security fixes.

### Supply-chain risk beyond version numbers
A version bump addresses *known vulnerabilities in code you chose*. It does not address:

| Shape | What it is | Version bumps help? |
|---|---|---|
| **Known CVE** | advisory against your version | ✅ yes — this is Dependabot's job |
| **Typosquatting** | `python-dateutil` vs `python-dateutils` | ❌ no — review the name on first add |
| **Account takeover** | maintainer's account compromised, malicious release published | ❌ **no — upgrading is the attack** |
| **Protestware** | maintainer sabotages their own package | ❌ no |
| **Transitive drift** | a dependency-of-a-dependency changes | ❌ not with plain `requirements.txt` |
| **Build-time execution** | `setup.py` runs arbitrary code at install | ❌ no |

The third row is the uncomfortable one: for a compromised release, **upgrading promptly is exactly
how you get hit.** Which is why "green CI on a Dependabot PR" is necessary but not sufficient, and why
a short delay before adopting brand-new releases is a defensible policy rather than laziness.

GitHub's free-on-private tooling: **Dependabot version and security updates, and the dependency
graph.** Not free on private: **secret scanning and push protection** (part of Advanced Security).
That gap is why this project uses `.gitignore` plus local hooks plus review for secrets
([Chapters 07](07_Gitignore.md), [33](33_Secrets_And_Leaks.md)).

> 💡 **Samjho aise:** Version **pin** karna sahi hai — matlab har baar wahi cheez install hogi, koi
> surprise nahi. Par pin ka matlab bhi hai: **jab tak tum khud na badlo, purani hi rahegi.** Aur duniya
> chalti rehti hai — kal koi security fix aayega, aur tumhari pinned version hi kamzor hogi.
>
> Dependabot = wo bandaa jo har Monday aake bolta hai *"ye nayi version aayi hai"*, PR khol deta hai,
> aur CI poora battery chala deta hai. **Khud merge nahi karta** — wo tumhara kaam hai. Sahi bantwara.
>
> Do baatein yaad rakho. Ek: **patch waale saath group karo** — warna 5 PR = 5 CI run = free minute
> khatam. Do: `ignore` karna theek hai, par **wajah likho** — warna wo lapervaahi jaisi dikhegi. Yahan
> Django 5.1 ignore hai kyunki wo version badalna nahi, **26 jagah code badalna** hai.

# Real World Example (this repo)
`.github/dependabot.yml` exists and configures two ecosystems. Its header states the *why* before the
*what*:

> *"FREE on every plan, including private repos. This is the one piece of big-tech supply-chain
> hygiene that costs nothing here, so there is no excuse not to run it… This project pins exact
> versions. Pinning is correct — it makes deploys reproducible — but a pin is also a decision to stay
> on that version until someone acts. Without Dependabot, 'someone acts' means 'someone remembers'."*

**Ecosystem 1 — pip:**
- `directory: /django_inventory` — the manifests are in the subdirectory, not the monorepo root
- weekly, Monday 06:00 **Asia/Kolkata** — updates land at the start of the working week, in local time
- `open-pull-requests-limit: 5` — with the comment: *"five open dependency PRs is a review queue, not
  security"*
- `commit-message.prefix: chore` + `include: scope` — Conventional Commits, so the `commit-msg` hook
  and the CHANGELOG both accept them unmodified
- **`groups.patch-updates`** — all patch bumps in one PR, *"so CI runs once for them instead of five
  times — free minutes are finite"*
- **`ignore` Django minor+major** — with the reason in a comment: `CheckConstraint(check=)` usage
  versus 5.1's `condition=`, so *"a 5.1 bump is a code migration, not a version bump… recorded so a
  future reader knows this is a decision, not neglect"*. Measured today: **147 call sites, all on
  `check=`** (71 in models, 76 in migrations)

**Ecosystem 2 — github-actions:**
- `directory: /` — workflow files live at the monorepo root
- monthly, `prefix: ci`
- because `actions/checkout@v4` and friends go stale too, and a **deprecated action starts failing
  your builds with no code change on your side**

**What verifies the upgrades.** Every Dependabot PR runs the same four gates as any other
([Chapter 28](28_CI_With_GitHub_Actions.md)):

```
lint → migrations (makemigrations --check) → test (2033 tests, real Postgres) → docs (BLOCKER=0)
```

The `migrations` job matters more than it looks for dependency PRs: a Django upgrade that changes
model or field behaviour shows up as an unexpected pending migration, caught mechanically rather than
in production.

**The honest gap here.** `requirements.txt` pins **direct** dependencies exactly, but there is no
lockfile, so transitive versions are resolver-decided. Two installs from the same commit can differ
below the top layer. `pip-compile` would close it; it is a known, unaddressed gap rather than a solved
problem.

# Visual Diagram
```
  UPSTREAM                    GITHUB                          YOUR REPO
  ────────                    ──────                          ─────────
  PyPI: Django 5.0.2  ──►  Dependabot (free, all plans)
  advisory published  ──►     │
                              │  reads /django_inventory/requirements*.txt
                              ▼
                       opens a PR:  chore(deps): bump X from a to b
                              │
                              ▼
                    ┌─── SAME CI AS ANY PR ──────────────────────┐
                    │ lint → migrations → test(2033/424s) → docs │
                    └────────────────┬───────────────────────────┘
                                     │ green = evidence, not hope
                                     ▼
                            YOU review + merge     ← Dependabot never merges

  GROUPING = MONEY (free plan: ~2000 Actions min/month, private)
  ─────────────────────────────────────────────────────────────
    ungrouped: 5 patch PRs → 5 × 424 s ≈ 35 min
    grouped  : 1 PR        → 1 × 424 s ≈  7 min

  IGNORE, WITH A REASON
  ─────────────────────
    Django minor/major  IGNORED  ← 26 × CheckConstraint(check=)  vs  5.1's condition=
                                   ⇒ a CODE MIGRATION, not a version bump
    …but PATCH still flows ⇒ 5.0.x security fixes keep arriving

  WHAT A BUMP DOES NOT FIX
  ────────────────────────
    typosquatting · account takeover (upgrading IS the attack) · protestware
    transitive drift (no lockfile here) · install-time code execution
```

# Practical — read, verify, and reason about the config
```bash
cd /home/tech/umesh-personal

# 1. the config, and its stated reasoning
cat .github/dependabot.yml

# 2. does it parse? (a broken file means Dependabot silently does nothing)
django_inventory/env/bin/python -c "
import yaml; d=yaml.safe_load(open('.github/dependabot.yml'))
print('  ecosystems:', [u['package-ecosystem'] for u in d['updates']])
print('  directories:', [u['directory'] for u in d['updates']])
"

# 3. is the directory right? the manifest MUST be there
ls django_inventory/requirements.txt django_inventory/requirements-dev.txt

# 4. what is actually pinned?
head -12 django_inventory/requirements.txt

# 5. the ignore rule's justification — count the call sites yourself
grep -rn "CheckConstraint(" django_inventory/config --include=*.py | wc -l
grep -rn "condition=" django_inventory/config --include=*.py | grep CheckConstraint | wc -l

# 6. installed vs pinned (drift between the file and reality)
django_inventory/env/bin/pip list --outdated 2>/dev/null | head -10

# 7. what is installed but NOT in requirements.txt? (transitive surface)
django_inventory/env/bin/pip freeze | wc -l
wc -l < django_inventory/requirements.txt

# 8. the Actions versions Dependabot also watches
grep -n "uses:" .github/workflows/ci.yml
```

Step 7 is the sobering one: the gap between those two numbers is your transitive dependency surface —
code you run but never chose.

# Production Walkthrough
1. **Monday 06:00 IST** — Dependabot opens PRs: patches grouped into one, minors individually.
2. **CI runs automatically** — same four gates. A red dependency PR is a dependency that does not fit
   your code, discovered for free.
3. **Read the PR body.** Dependabot includes the changelog and release notes. For a patch this is
   30 seconds; do not skip it.
4. **Merge the grouped patch PR** if green. Squash-merge, like anything else.
5. **Handle minors individually.** Read the release notes properly; a minor version can deprecate
   something you use.
6. **Treat majors as projects.** Branch, migrate the code, run the battery, then bump — which is
   precisely why Django minor/major is on the ignore list.
7. **Security advisories arrive regardless of schedule.** Treat them as interrupts and check whether
   the vulnerable code path is even reachable from your app.
8. **Monthly**, the Actions PR: bump `actions/checkout` and friends before a deprecation starts
   failing builds.

# Debugging Guide

| Symptom | Cause | Fix |
|---|---|---|
| Dependabot never opens a PR | `directory` does not contain the manifest | monorepo: `/django_inventory`, not `/` |
| Nothing happens at all | config invalid, or Dependabot disabled | check Insights → Dependency graph → Dependabot; validate the YAML |
| Flooded with PRs | no `groups`, limit too high | group patches; `open-pull-requests-limit: 5` |
| Dependabot commits rejected locally | message not Conventional Commits | `commit-message.prefix` ([Ch 25](25_Conventional_Commits.md)) |
| A bump breaks CI | genuine incompatibility | that is the system working; close the PR and add an `ignore` **with the reason** |
| Ignored a dependency, now missing security fixes | you ignored patches too | ignore only `semver-minor`/`semver-major` |
| Two installs from one commit differ | no lockfile; transitive resolution | `pip-compile`, or `pip freeze` with hashes |
| Actions workflow suddenly fails, no code change | a deprecated action version | the monthly `github-actions` ecosystem exists for this |
| `makemigrations --check` fails only on a Django bump | the upgrade changed model/field behaviour | inspect the generated migration; that job caught a real behaviour change |

# Performance Notes
- **Grouping is the main lever.** 5 PRs × 424 s ≈ 35 min versus 1 × 424 s ≈ 7 min against ~2,000 free
  minutes/month.
- **`concurrency: cancel-in-progress`** in `ci.yml` means a rebased Dependabot PR does not pay twice.
- **Cheap jobs gate the expensive one** (`test` needs `lint` and `migrations`), so an incompatible bump
  often fails in ~3 minutes instead of 45.
- `open-pull-requests-limit` bounds *human* cost as much as CI cost — an unreviewed queue is worthless.
- **Weekly, not daily.** Daily produces churn nobody reads; security updates arrive out of band anyway.
- A lockfile would make installs faster *and* deterministic, since the resolver has no work to do.

# Security Considerations
- **A pin is a decision to stay vulnerable until you act.** Correct for reproducibility, dangerous
  without a mechanism. Dependabot is the mechanism.
- **Ignoring minor/major must not ignore patch**, or you have opted out of security fixes for a
  version line you are still running.
- **For a compromised release, prompt upgrading is the attack vector.** Green CI does not detect
  malicious code that behaves normally under test. A short cooling-off period before adopting
  brand-new releases is a real mitigation.
- **`setup.py` and build backends execute code at install time.** `pip install` is not an inert
  operation; that is why CI installs into a disposable runner.
- **No lockfile means transitive versions can drift** between installs of the same commit. Named here
  as a known gap.
- **Fork PRs do not get repository secrets** by design. Dependabot PRs have their own restricted
  secret context; treat `pull_request_target` as a known escalation path and avoid it
  ([Chapter 21](21_Pull_Requests.md)).
- **Secret scanning and push protection are NOT free on private repos** (Advanced Security). Hence
  `.gitignore` + hooks + review as the substitute ([Chapter 33](33_Secrets_And_Leaks.md)).
- **Read what you merge.** A dependency update is a code change with your database credentials in
  scope.

# Architecture Decisions
- **Exact pins over ranges.** Reproducible deploys beat silent patches; the cost is an explicit
  upgrade obligation, discharged by Dependabot.
- **Dependabot enabled** because it is free on every plan — the only supply-chain control here with no
  paid tier and therefore no excuse.
- **Patch updates grouped, minors individual, majors as projects.** Matches risk to review effort and
  to the CI budget.
- **`commit-message.prefix`** so bot commits satisfy the same Conventional Commits gate as human ones —
  no special-casing in the hook or the changelog tooling.
- **Django minor/major ignored, with the reason committed.** 147 `CheckConstraint(check=)` call sites
  (71 in models, 76 in migrations) versus 5.1's `condition=` make it a code migration. Recording the *why* is what distinguishes a
  decision from neglect.
- **Weekly pip, monthly actions.** Application dependencies move faster than CI action versions.
- **`Asia/Kolkata` schedule** so PRs land at the start of the owner's working week, not overnight.
- **No lockfile — accepted and documented.** `requirements.txt` pins the top layer; closing the
  transitive gap with `pip-compile` is unscheduled work, stated rather than hidden.

# Best Practices
- Pin exactly, and pair the pin with a bot. Neither alone is sufficient.
- Group patch updates; review minors one at a time; plan majors.
- Every `ignore` carries a comment explaining why, and what would unblock it.
- Never ignore patch updates for a version line you still run.
- Point `directory` at the manifest — verify it, since a wrong path fails silently.
- Give bot commits a Conventional Commits prefix.
- Read the changelog in the PR body, even for patches.
- Watch the gap between `pip freeze | wc -l` and your requirements file; that is your transitive
  surface.

# Beginner Mistakes
- **Unpinned dependencies** → non-reproducible builds and "works on my machine" becoming unanswerable.
- **Pinning with no upgrade mechanism** → a CVE sits unapplied for months.
- **`directory: /` in a monorepo** → Dependabot silently finds nothing and you assume it is working.
- **No grouping** → PR flood, wasted CI minutes, and a queue nobody reads.
- **Auto-merging everything** → dependency changes are code changes; they need the same gate.
- **`ignore` with no reason** → indistinguishable from neglect six months later.
- **Ignoring patches along with minors** → you have opted out of security fixes.
- **Assuming green CI proves a dependency is safe** → it proves compatibility, not the absence of
  malicious code.
- **Forgetting Actions versions** → a deprecated action fails builds with no change on your side.

# Interview Questions
- **Junior:** "What does Dependabot do?" — Watches your manifest files against upstream releases and
  opens a pull request per available update, with the changelog in the body. It proposes; you review
  and merge. It is free on all plans, including private repos.
- **Mid:** "Why pin exact versions if it means manual upgrades?" — Pinning makes builds reproducible:
  the same commit installs the same code every time, which is what makes a deploy or a test result
  meaningful. The cost is that a pin will not pick up security fixes on its own, so pinning is only
  correct when paired with a mechanism that proposes upgrades — otherwise you have chosen to stay
  vulnerable by default.
- **Senior:** "When do you ignore a dependency update?" — When the upgrade is a code migration rather
  than a version bump. Here Django 5.1 renamed `CheckConstraint(check=)` to `condition=`, and this
  codebase has 147 such call sites — 71 in models, 76 in frozen migrations — so minor and major are ignored with that
  reason committed in the config, while **patch** updates still flow so 5.0.x security fixes keep
  arriving. The reason has to be written down; an undocumented ignore is indistinguishable from
  neglect, and the next reader cannot tell whether it is still valid.
- **Staff:** "Dependabot PRs are green. What supply-chain risk remains?" — Most of it, because a green
  bump only addresses *known vulnerabilities in packages you deliberately chose*. It says nothing about
  typosquatting at the moment of first adding a package, nothing about protestware, and — the
  uncomfortable one — nothing about maintainer account takeover, where **upgrading promptly is
  precisely how you get compromised**, since malicious code that behaves normally under test passes
  CI by construction. It also does not address install-time execution: `setup.py` and build backends
  run arbitrary code during `pip install`, before any test runs. And with plain `requirements.txt`
  there is no lockfile, so transitive versions are resolver-decided and two installs of the same
  commit can differ below the top layer — this project has that gap and names it rather than claiming
  otherwise. Concretely I would add a lockfile with hashes, introduce a short cooling-off window
  before adopting brand-new releases, keep installs confined to disposable CI runners, and be explicit
  that GitHub's secret scanning and push protection are **not** free on private repos, so that layer
  has to be replaced with `.gitignore`, hooks and review rather than assumed present.

### Why interviewers ask these — and the answer that separates levels
| Testing for | Weak answer | What lands |
|---|---|---|
| Do you understand pinning's trade-off? | "Pinning is safer." | Pinning buys reproducibility and creates an upgrade obligation; it is only correct paired with a mechanism that proposes updates. |
| Can you justify an exception? | "We skip Django updates, it breaks." | Name the concrete API change and the blast radius (147 call sites, 71 in models), keep patch updates flowing, and commit the reason so it can be re-evaluated. |
| Do you see past CVE lists? | "Dependabot handles supply chain." | Bumps cover known CVEs only; takeover, typosquatting, install-time execution and transitive drift are untouched — and prompt upgrading is the takeover vector. |

**The killer follow-up:** *"A maintainer's account is compromised and a malicious patch release ships. Does Dependabot help or hurt?"* — It hurts: it will promptly open a PR for exactly the poisoned version, CI will pass because malicious code that behaves normally under test is designed to, and the change looks like routine hygiene. The mitigations are not version-based — a cooling-off window, lockfiles with hashes so the artefact is fixed, and reading diffs on anything security-adjacent. Recognising that automation can *accelerate* a supply-chain attack is the whole point of the question.

# Revision Notes
- **Dependabot is FREE on every plan**, private repos included. Unlike branch protection/CODEOWNERS auto-assign.
- **Pin exactly** ⇒ reproducible builds, but *"a pin is a decision to stay on that version until someone acts."*
- **`directory`** must contain the manifest — monorepo: `/django_inventory`, not `/`. Wrong path fails **silently**.
- **Group patch updates**: 5 PRs × 424 s ≈ 35 min vs 1 × 7 min, against ~2,000 free min/month.
- `commit-message.prefix: chore` ⇒ bot commits pass the Conventional Commits hook.
- **`ignore` needs a committed reason.** Here: Django minor/major, because **147** × `CheckConstraint(check=)` (71 models + 76 migrations) vs 5.1's `condition=` = a code migration. **Patch still flows.**
- Also watch **`github-actions`** — a deprecated action fails builds with no code change.
- A bump does **not** address: typosquatting · **account takeover (upgrading IS the attack)** · protestware · install-time code execution · transitive drift.
- **No lockfile here** ⇒ transitive versions can drift. Known, documented gap.
- **Secret scanning + push protection are NOT free on private repos.**

# Cheat Sheet
```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: pip          # pip | npm | github-actions | docker | …
    directory: /django_inventory    # MUST contain the manifest (monorepo!)
    schedule: { interval: weekly, day: monday, time: '06:00', timezone: Asia/Kolkata }
    open-pull-requests-limit: 5     # a queue, not a flood
    commit-message: { prefix: chore, include: scope }   # Conventional Commits (ch 25)
    groups:
      patch-updates: { patterns: ['*'], update-types: [patch] }   # ONE PR, ONE CI run
    ignore:
      - dependency-name: Django     # ALWAYS say why, in a comment
        update-types: [version-update:semver-minor, version-update:semver-major]
  - package-ecosystem: github-actions
    directory: /                    # workflows live at the repo ROOT
    schedule: { interval: monthly }
```
```bash
python -c "import yaml;print(yaml.safe_load(open('.github/dependabot.yml')))"  # does it parse?
pip list --outdated                     # local drift
pip freeze | wc -l                      # installed…
wc -l < requirements.txt                # …vs declared = transitive surface
grep -n "uses:" .github/workflows/*.yml # action versions Dependabot watches
pip-compile requirements.in             # (pip-tools) produce a real lockfile
```

# My ERP Section

| Setting | Value here |
|---|---|
| Config | `.github/dependabot.yml`, two ecosystems |
| pip | `directory: /django_inventory` · weekly Monday 06:00 **Asia/Kolkata** · limit **5** · `prefix: chore` + scope |
| Grouping | `patch-updates` — all patch bumps in one PR, *"so CI runs once for them instead of five times — free minutes are finite"* |
| Ignored | **Django** minor + major, reason committed: `CheckConstraint(check=)` vs 5.1's `condition=` ⇒ a code migration. **Measured: 147 call sites — 71 in models, 76 in migrations — 0 already on `condition=`.** Patch still flows |
| github-actions | `directory: /` · monthly · `prefix: ci` — a deprecated action fails builds with no code change |
| What verifies a bump | the same four gates: lint → **migrations** → test (**2,033 / 424 s**) → docs BLOCKER=0 |
| Why `migrations` matters here | a Django upgrade changing model/field behaviour surfaces as an unexpected pending migration, caught mechanically |
| Pinned examples | `Django==5.0.1`, `psycopg2-binary==2.9.9`, `django-allauth==0.61.1`, `Pillow==10.2.0` |
| **Known gap** | **no lockfile** — `requirements.txt` pins direct deps only; transitive versions are resolver-decided. `pip-compile` would close it; unscheduled |
| Not available free | secret scanning + push protection (Advanced Security) ⇒ substituted by `.gitignore` + hooks + review ([Ch 33](33_Secrets_And_Leaks.md)) |

# Practice Tasks
1. Read `.github/dependabot.yml` and explain every field out loud, including why `directory` differs
   between the two ecosystems.
2. Validate it parses (Practical step 2). Then break the YAML deliberately and confirm your check
   catches it — a broken config means Dependabot does nothing, silently.
3. Count the `CheckConstraint(` call sites yourself (Practical step 5). You should get **147**, split
   71 models / 76 migrations, with **0** on `condition=`. Note that `CLAUDE.md` says "26" — that was
   one specific PR's additions, not the total. Does the real number justify the ignore rule more or
   less strongly?
4. Run `pip freeze | wc -l` and `wc -l < requirements.txt`. The difference is your transitive surface.
   Sit with that number.
5. Work out the CI cost of *not* grouping: multiply 424 s by the number of patch bumps you would
   expect monthly, against 2,000 free minutes.
6. Find the `uses:` lines in `ci.yml`. Those are what the `github-actions` ecosystem watches.

# Homework
- Convert a project of your own from unpinned or ranged dependencies to exact pins, then add a
  `dependabot.yml` with grouped patches. Notice that pinning without the bot would be a downgrade in
  safety.
- Read a real Dependabot PR body on any public repo. Note how much of the changelog it surfaces — and
  ask yourself whether you would have read that changelog otherwise.
- Investigate `pip-compile` (pip-tools) and produce a hash-pinned lockfile for this project's
  requirements. That is the concrete fix for the documented transitive gap.
- Read one published post-mortem of a real supply-chain attack (`event-stream`, `ua-parser-js`, or
  `xz-utils`) and write two sentences on whether Dependabot would have helped, hurt, or been
  irrelevant.

# Further Reading & Live Resources
- [Dependabot configuration options](https://docs.github.com/en/code-security/dependabot/dependabot-version-updates/configuration-options-for-the-dependabot.yml-file) — every field, including `groups` and `ignore`
- [About Dependabot security updates](https://docs.github.com/en/code-security/dependabot/dependabot-security-updates/about-dependabot-security-updates) — how they differ from version updates
- [GitHub Advisory Database](https://github.com/advisories) — the source of the advisories, browsable and free
- [pip-tools](https://github.com/jazzband/pip-tools) — `pip-compile` for real lockfiles with hashes
- [PyPA — Secure installs](https://pip.pypa.io/en/stable/topics/secure-installs/) — hash-checking mode and why it matters
- [OpenSSF — Concise Guide for Developers](https://best.openssf.org/Concise-Guide-for-Developing-More-Secure-Software) — supply-chain practices beyond version bumps
- [SLSA framework](https://slsa.dev/) — the vocabulary for build provenance, if you want to go deeper than version numbers
