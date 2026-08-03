# Contributing — the engineering rulebook

> **Big-tech discipline on GitHub's free tier.** Every rule here exists at Google, Meta,
> Stripe and Netflix in some form. What changes on a free plan is *where* the rule is
> enforced — not *whether* it is. Server-side enforcement costs money; client-side
> enforcement is free and, installed correctly, just as binding.
>
> New to git? Read the course first: **`django_inventory/docs/git_course/`**
> (also live at `/learn/git/`). This file is the *rules*; the course is the *why*.

---

## 0. The one-paragraph version

Never commit to `main`. Branch → commit in Conventional Commits format → push the branch →
open a Pull Request → CI must be green → get a review → squash-merge → delete the branch.
Releases are tags. Money-touching code gets an extra reviewer. Documentation ships in the
same PR as the code, never later.

---

## 1. Why we don't just push to `main`

`main` must be **always deployable**. That is the whole point of a trunk. The moment a broken
commit lands on `main`, the deploy runbook is a loaded gun: anyone who follows it ships the
break.

A Pull Request buys four things a direct push cannot:

| | |
|---|---|
| **A gate** | CI runs the whole test battery before the code can land |
| **A record** | *why* a change happened, permanently, next to the diff |
| **A reviewer** | a second pair of eyes on money paths and permissions |
| **A revert point** | one squashed commit undoes an entire feature cleanly |

💡 **Samjho aise:** `main` factory ki chaalu production line hai. Usme seedha haath nahi
daalte — pehle apne bench pe banao (branch), test karo (CI), koi dekh le (review), phir line
pe lagao (merge).

---

## 2. How `main` is actually protected here — read this properly

This is the honest part, and the part most guides skip.

**GitHub's server-side branch protection is a paid feature on private repositories.** It is
free on public repos only. This project is private and stays on the free plan
(owner ruling: money goes to deploy infrastructure, not tool subscriptions). So we do **not**
have server-side "you may not push to main."

That does not mean we go without protection. It means protection moves to the client, where
it is free. Three layers, and they compose:

### Layer 1 — a `pre-push` hook that refuses `main` *(local, free, enforced)*

```bash
bash git-hooks/install.sh      # run once per machine, per clone
```

After that, `git push origin main` **fails on your machine** before it ever reaches GitHub.
This is the free replacement for branch protection, and it is honest about its one limit:
a hook lives in `.git/hooks/`, which is not cloned. So it is only binding on machines where
it was installed. That is why installing it is step 1 of onboarding, and why
`git-hooks/install.sh` is committed.

### Layer 2 — collaborators physically cannot push *(server-side, free, enforced)*

Collaborators get **Read** access, not Write, and work from a **fork**. With Read access
there is no push permission to this repository at all — so for everyone except the owner,
"cannot push to main" is enforced by GitHub itself, for free, with no plan upgrade.

This is exactly how every large open-source project handles contributors, and it is
*stronger* than branch protection: branch protection says "you may push, but not there";
a fork says "you have no push at all."

### Layer 3 — CI as the merge gate *(server-side, free)*

Actions runs on every PR. A red PR is not merged. On the free plan this is a **discipline**
gate rather than a mechanical block (mechanically blocking merge-on-red is, again, paid) —
but the signal is identical, and it is visible in the PR before anyone clicks merge.

> **If the repo ever goes public, or a Pro plan is ever bought, turn on server-side branch
> protection immediately and keep all three layers.** Belt and braces. The hook staying
> installed costs nothing.

### What each layer catches

| Failure | Caught by |
|---|---|
| Owner absent-mindedly types `git push origin main` | Layer 1 (hook) |
| Collaborator tries to push or merge | Layer 2 (fork/Read) |
| Someone opens a PR that breaks the tests | Layer 3 (CI) |
| Owner on a fresh clone with no hook installed | ⚠️ **nothing** — install the hook first |

That last row is a real gap and is written down rather than hidden. Onboarding step 1 exists
because of it.

---

## 3. Branches

One branch = one intent. Short-lived: open it, land it, delete it. A branch alive for three
weeks is a merge conflict with a countdown timer.

```
<type>/<short-kebab-description>
```

| Prefix | For |
|---|---|
| `feat/` | new capability — `feat/accountant-read-tier` |
| `fix/` | bug fix — `fix/utc-date-in-settlement` |
| `chore/` | tooling, config, deps — `chore/gitignore-dumps` |
| `docs/` | documentation only — `docs/git-course` |
| `refactor/` | behaviour-preserving change |
| `test/` | tests only |
| `perf/` | performance work |

Rules: lowercase, hyphens not underscores, no ticket numbers (this project has no tracker),
never work directly on `main`.

---

## 4. Commits — Conventional Commits, enforced

```
<type>(<scope>): <subject>

<body — the WHY, wrapped at 72 chars>

<footer — Co-Authored-By, BREAKING CHANGE>
```

Types: `feat` · `fix` · `docs` · `chore` · `refactor` · `test` · `perf` · `build` · `ci` ·
`style` · `revert`.

Scope = the app or area: `accounts`, `expense`, `production`, `learning`, `deploy`, `repo`.

The `commit-msg` hook rejects a message that does not parse. That is deliberate: the format
is what lets a CHANGELOG be generated instead of hand-written, and lets `git log --grep`
actually find things years later.

**Subject line:** imperative mood ("add", not "added"), no trailing period, ≤ 72 chars.
*"fix: correct settlement entry_date to IST"* — not *"fixed some date stuff"*.

**Body:** explain **why**, not what. The diff already shows what. Six months from now the
*why* is the only thing you cannot reconstruct.

**Breaking changes** get a `BREAKING CHANGE:` footer — that is what drives a major version
bump in SemVer.

---

## 5. Pull Requests

1. Push your branch: `git push -u origin feat/my-thing`
2. Open the PR against `main`. The template loads automatically — **fill it in**, don't
   delete it.
3. Wait for CI. Green or explain why not.
4. Request review. `CODEOWNERS` assigns the owner automatically.
5. **Squash-merge.** One feature = one commit on `main`, so `main`'s history reads as a list
   of features and any one of them reverts cleanly.
6. Delete the branch.

**Keep PRs small.** A 200-line PR gets a real review; a 2,000-line PR gets "LGTM". If it is
big, split it — or say in the PR body which part deserves the attention.

### The review standard

A review is not a rubber stamp. Reviewing means you are **co-signing** the change. Look for:

- **Correctness** — does it do what the description claims?
- **Money** — any write to a ledger, settlement, earning or rate. This project has a
  single-writer discipline; a new money-write path outside an approved service is a **STOP**,
  not a nitpick.
- **Permissions** — new view without a gate? Widened role? Read the gate, not the comment.
- **Tests** — is the *failure mode* pinned, or only the happy path?
- **Docs** — see rule 12 below. A PR that changes behaviour and no `.md` is incomplete.
- **Mobile** — new UI verified at mobile, tablet and desktop widths, or it is not done.

---

## 6. CI (`.github/workflows/ci.yml`)

Runs on every PR touching `django_inventory/**`:

| Job | Gate |
|---|---|
| `lint` | `ruff` on changed Python; design-system ratchet on changed templates |
| `migrations` | `makemigrations --check` — a model change with no migration fails here |
| `test` | the full battery against a real Postgres service container |
| `docs` | `knowledge_sync` must report **BLOCKER=0** |

**Free-minute discipline** (this matters on a free plan):

- private-repo Actions is metered at ~2,000 min/month; public is unlimited
- `concurrency` cancels superseded runs when you push twice — no paying for stale work
- `paths` filter means edits to unrelated monorepo folders start no run at all
- every job has a `timeout-minutes` so a hung job cannot drain the month
- if it ever gets tight: a **self-hosted runner on the deploy VPS** is free and unlimited.
  Upgrade the plan last, not first.

---

## 7. Releases

[SemVer](https://semver.org): `MAJOR.MINOR.PATCH`.

- **MAJOR** — a breaking change (`BREAKING CHANGE:` footer present)
- **MINOR** — a new backwards-compatible feature (`feat:`)
- **PATCH** — a backwards-compatible fix (`fix:`)

```bash
git tag -a erp-v1.1.0 -m "erp-v1.1.0 — accountant read tier"
git push origin erp-v1.1.0
```

An **annotated** tag (`-a`), never lightweight: an annotated tag is a real object with an
author, date and message, so the release is self-documenting. Then update `CHANGELOG.md` and
cut a GitHub Release from the tag.

---

## 8. Project rules a PR is also judged against

These live in `django_inventory/CLAUDE.md` and are not optional:

- **Rule 4 — service layer owns all multi-row writes.** Views call services. No signals.
- **Rule 5 — single-writer discipline.** Each ledger/audit table has exactly one writer.
- **Rule 6 — permissions via `permission_service`.** No raw `is_superuser` in views.
- **Rule 11 — mobile-first is functional**, not polish. Mobile + tablet + desktop verified.
- **Rule 12 — docs-sync.** Code change ⇒ its `.md` updated **in the same PR**. Documentation
  drift is treated as an architecture bug, not a chore.
- **Settlement is the only money boundary.** Nothing else writes money.

---

## 9. Onboarding a new developer — the exact steps

**Owner does (once, in the browser):**
1. Settings → Collaborators → **Add people** → their username → role **Read**
   *(Read, not Write — this is Layer 2 of §2, and it is what makes "cannot merge" real)*
2. Send them this file.

**They do:**
```bash
# 1. Fork on GitHub (their own private copy), then clone THEIR fork
git clone git@github.com:<their-username>/umesh-personal.git
cd umesh-personal

# 2. Point "upstream" at the real repo so they can stay current
git remote add upstream git@github.com:umesh29032/umesh-personal.git

# 3. Install the hooks — THIS IS NOT OPTIONAL (see §2 Layer 1)
bash git-hooks/install.sh

# 4. Set up the project
cd django_inventory
python3 -m venv env && env/bin/pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env          # then fill it in
env/bin/python config/manage.py migrate
env/bin/python config/manage.py seed_master_data
```

**Their daily loop:**
```bash
git fetch upstream && git switch main && git merge --ff-only upstream/main
git switch -c feat/their-thing
# ... work, commit ...
git push -u origin feat/their-thing     # origin = THEIR fork
# then open a PR from their fork → umesh29032/umesh-personal
```

`--ff-only` on purpose: it *refuses* to create a merge commit. If it fails, their `main` has
drifted and they should reset it to upstream rather than merge — keeping `main` a clean mirror.

---

## 10. Things we deliberately do NOT do

Written down so nobody "helpfully" adds them later:

- **No `git push --force` to a shared branch.** Use `--force-with-lease` on your own branch
  only. Plain `--force` overwrites work you cannot see.
- **No merge commits on feature branches.** Rebase onto `main` to stay current.
- **No committing data.** Dumps, `.env`, media, `node_modules` — all gitignored at the
  monorepo root. A `.sql` file has been committed to this repo once already; the root
  `.gitignore` now makes it impossible.
- **No long-lived release branches.** Trunk-based: `main` plus short branches plus tags.
  `git-flow` is heavier than a 1–2 person team can justify.
- **No merging your own unreviewed money change.** If nobody is available, say so in the PR
  and note what was self-reviewed.
