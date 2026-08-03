---
id: git-course-30-changelog
type: lesson
status: active
owner: handwritten
scope: git, version control — the human-readable record of what changed between releases
anchors: CHANGELOG.md, django_inventory/CHANGELOG.md, CONTRIBUTING.md, git-hooks/commit-msg
verified: 2026-08-03
---

# 30 — CHANGELOG (the release notes a human reads, derived from commits a machine reads)

> Part of [Git Course](00_COURSE_OVERVIEW.md). Prev: [29 — Semantic Versioning & Tags](29_Semantic_Versioning_And_Tags.md). Next: [31 — Signed Commits](31_Signed_Commits.md).

# Learning Objectives
By the end of this chapter you can:
- explain why a `CHANGELOG.md` exists when `git log` already exists — and who each one is written for
- write an entry in the **Keep a Changelog** format, using its six categories correctly
- **derive** a release draft from Conventional Commits with two commands, instead of remembering
- decide what must never appear in a changelog (and why a `Security` entry has timing rules)
- spot changelog **drift** — and recognise the real instance of it in this repository

# Purpose
[Ch 29](29_Semantic_Versioning_And_Tags.md) gave a release a *name*. A name is useless on its own: `erp-v1.1.0` tells a factory owner nothing. The changelog is where that name gets a meaning a non-developer can read in ninety seconds. This chapter walks this repo's real `CHANGELOG.md`, shows the two commands that draft it from history, and is blunt about the failure mode: a changelog nobody updates is worse than no changelog at all, because people trust it.

# The Problem
Three real requests, none of which `git log` answers well.

**The owner asks: "What did I get for the last three weeks?"** You run `git log --oneline`. It prints 22 commits since the last release. Twelve of them are `docs:`, one is `test(production): pin F-4 roster-picker guarantee on generic_stage path`. He does not know what a roster picker on a generic stage path is, and he should not have to. The information he wants is in there, buried in engineering vocabulary and diluted by internal bookkeeping.

**The operator asks: "It broke after the update — what changed?"** Now you are reading commit subjects under pressure at 9 p.m., trying to decide which of six features touched settlements. A grouped, categorised list would have taken you ten seconds.

**An auditor asks: "You had database dumps in a public repo. What did you do about it?"** The answer exists — the audit, the verdict, the decision not to rewrite history — but it exists in a commit message that nobody will find, and in a chat log that is already gone. Unless somebody wrote it down where decisions live.

And the failure mode that makes all three worse: writing the changelog *later*, from memory. Six weeks after the fact you will remember the two features you were proud of and forget the fix that actually matters. **A changelog written from memory is fiction** — which is precisely why this repo's own changelog says so, in the file.

# Theory (from zero)

### `git log` and `CHANGELOG.md` have different readers
This is the whole idea, and everything else follows from it.

| | `git log` | `CHANGELOG.md` |
|---|---|---|
| Written for | the developer, and the debugger in six months | the user, the operator, the owner, future-you |
| Grain | every commit, including internal churn | only what a reader can *perceive* |
| Vocabulary | `WorkerStageContribution`, `generic_stage` | "workers can now report per-stage output" |
| Produced by | git, automatically and completely | a human, deliberately and selectively |
| Truth type | complete and unarguable | curated — therefore capable of lying |

`git log` is a **register**: everything that happened. The changelog is a **statement**: what it means. You need both, and neither substitutes for the other.

> 💡 **Samjho aise:** `git log` **factory ka andar ka register** hai — har chhoti entry, har kaarigar ki, poori. `CHANGELOG.md` woh **bill** hai jo grahak ke haath mein jaata hai: "yeh naya mila, yeh theek hua, yeh hata diya." Bill mein yeh nahi likhte ki kaarigar ne chai kab pi — par bill mein jhooth bhi nahi likhte. Aur sabse zaroori baat: **bill maal ke saath hi banta hai**, do mahine baad yaad se nahi. Yaad se banaya bill = kahaani, hisaab nahi.

### Keep a Changelog — the format, and why this one
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) is a small convention that has effectively won. Its rules:

- Newest version at the **top**, so the reader never scrolls.
- An **`[Unreleased]`** section at the very top, where entries land *as they are made*. This is the single mechanism that defeats memory-writing.
- One section per released version: `## [erp-v1.0.0] — 2026-07-19`. Absolute dates, ISO order, never "last Tuesday".
- Entries grouped under **six categories**, and only these six:

| Category | Means | ERP example |
|---|---|---|
| **Added** | new capability | a machines app with operator possession windows |
| **Changed** | existing behaviour is different | the root `.gitignore` now applies monorepo-wide |
| **Deprecated** | still works, will be removed | a URL kept alive for one release with a warning |
| **Removed** | gone now | the worker M2M table dropped (`e01f0c4b`) |
| **Fixed** | a bug is fixed | settlement `entry_date` corrected from UTC to IST |
| **Security** | a vulnerability or exposure handled | dumps untracked, exposure audited |

- **Link references at the bottom**, so each version heading is clickable to a diff. That is the trick that makes a changelog navigable:

```
[Unreleased]: https://github.com/umesh29032/umesh-personal/compare/erp-v1.0.0...HEAD
[erp-v1.0.0]: https://github.com/umesh29032/umesh-personal/releases/tag/erp-v1.0.0
```
Those two lines are real, and they are the seam between this chapter and the last one: `compare/<tag>...HEAD` is a URL that only works because tags are fixed points ([Ch 29](29_Semantic_Versioning_And_Tags.md)).

One more convention worth knowing: a release pulled after publication is marked **`[YANKED]`** rather than deleted. You do not erase history from a changelog; you annotate it. Same instinct as never moving a tag.

### Derived, not remembered
Because every commit here is Conventional Commits ([Ch 25](25_Conventional_Commits.md)) and the `commit-msg` hook refuses anything else, a *draft* falls out of history mechanically:

- `feat:` → **Added**
- `fix:` → **Fixed**
- `!` or a `BREAKING CHANGE:` footer → **Removed** or **Changed**, and a MAJOR bump
- `docs:` / `chore:` / `test:` / `refactor:` / `style:` / `ci:` → usually **nothing at all**

That last line is the one beginners get wrong. A refactor no user can perceive does not belong in release notes. Of this repo's 324 commits, **83 are `docs:`** — indispensable to the project, invisible to the changelog.

The hook's own header says this out loud: the format *"is what makes a CHANGELOG generatable instead of hand-written, drives the SemVer bump… and makes `git log --grep` useful years later."* The commit discipline of Ch 25 pays its rent here.

**Derived, not generated.** The machine writes the *draft*; a human writes the *sentence*. `feat(production): worker roster picker as searchable multi-select dropdown` is a commit subject. The changelog line is: *"Managers can now search the worker roster when assigning a stage, instead of scrolling a long checkbox list."* Same change, different reader.

### The changelog as a decision record
The category list above has an unwritten seventh use: recording a **decision you deliberately took**, especially a decision *not* to act. This repo's `Fixed` section carries one, and it is the best example in the whole course:

> "History deliberately **not** rewritten (0 forks, repo going private, nothing usable inside), so the dumps remain in earlier commits by decision, not by oversight."

That sentence is worth a page of explanation. A future reader — an auditor, a new developer, you in two years — will eventually find those dumps in old commits. Without that line they conclude *oversight*. With it they find a judged, documented trade-off ([Ch 34](34_Rewriting_History.md) is where the mechanics of the road not taken live).

### Drift — name the confusing bit
Two changelogs in one repository is not "thorough", it is **one file lying**. This repo has exactly that, right now, and it is worth seeing rather than hiding:

- `/CHANGELOG.md` at the monorepo root — current, Keep a Changelog format, `[Unreleased]` plus `[erp-v1.0.0]`.
- `/django_inventory/CHANGELOG.md` — older, carries doc frontmatter (`id: root-changelog`, `verified: 2026-07-13`), and its newest heading is `## [Unreleased] — 2026-06-02`. It still states that the branch work is *"uncommitted pending owner approval"* — which stopped being true many commits ago.

Two files, two answers, no marker saying which one wins. The rule to take away: **one canonical changelog per shipped product**, and if a second one must survive, its first line says "superseded by …". Documentation drift is treated in this project as an architecture bug (`CLAUDE.md` rule 12), and this is what that looks like in the wild.

# Real World Example (this repo)
The canonical file is `/home/tech/umesh-personal/CHANGELOG.md`. Its header does two jobs — declares the conventions, then explains its own maintenance rule:

```markdown
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

**How this file is maintained.** Commits follow Conventional Commits
(`CONTRIBUTING.md` §4), which is what makes this file *derivable* rather than
remembered: `feat:` → Added, `fix:` → Fixed, `BREAKING CHANGE:` → a MAJOR bump.
Update it in the release PR, not months later — a changelog written from memory
is fiction.
```

The `[Unreleased]` section then shows all three category behaviours at once. **Added** describes the workflow system in reader-facing terms (the hooks, the four CI jobs, the templates). **Changed** records the `.gitignore` widening and, crucially, *why the old one was not enough*:

```markdown
### Changed
- Root `.gitignore` is now monorepo-wide: blocks `*.sql`, `*.dump`, `*.sql.gz`,
  `db_backups/`, `backups/`, `node_modules/` in **every** folder. Previously only
  `django_inventory/.gitignore` carried the rule, so it did not reach sibling
  projects.
```

And **Fixed** carries the incident, with the audit result and the decision:

```markdown
### Fixed
- Untracked 2,954 files that were never code: two `pg_dump` database dumps and
  2,952 `node_modules` files from the old `Django_app/myproject/` practice app
  (`git rm --cached`, files kept on disk). A dump is plaintext, so committing one
  publishes every row.
  Audited before acting — OAuth tables empty, no plaintext passwords, 2 hashes at
  `pbkdf2_sha256` with 1,000,000 iterations, sessions long expired: **exposure
  mild**. History deliberately **not** rewritten …
```

Read what that entry does *not* contain: no hash values, no email addresses, no file contents. It says *what class of thing* was exposed and *how bad*, which is everything a reader needs and nothing an attacker can use. That restraint is the `Security` discipline from further down this chapter, applied.

The `[erp-v1.0.0] — 2026-07-19` section below it is the shipped product in nine bullets — Manufacturing V1, settlement-based payroll, the production-truth foundation, three-concept RBAC, machines, pattern intelligence, the learning platform, the deployment kit — each one a *capability*, none of them a commit subject. That is what "written for the reader" looks like at release scale.

# Visual Diagram
```
   324 commits (git log)  ── the complete register, for developers
        │
        │  filter by TYPE  (Conventional Commits, Ch 25 — enforced by commit-msg hook)
        ▼
   ┌──────────────────────────────────────────────────────────────────┐
   │  feat:  ──────────────────────────────►  Added                   │
   │  fix:   ──────────────────────────────►  Fixed                   │
   │  ! / BREAKING CHANGE: ────────────────►  Removed / Changed  (+MAJOR)
   │  chore:/refactor: (behaviour visible) ►  Changed                 │
   │  security-relevant ───────────────────►  Security                │
   │  docs: chore: test: refactor: style: ─►  (nothing — 83 of 324)   │
   └──────────────────────────────────────────────────────────────────┘
        │   a HUMAN rewrites each line for the reader, not the author
        ▼
   ## [Unreleased]        ← entries land HERE as work merges (defeats memory-writing)
        │
        │   release day: rename the heading, add the date, refresh the two link refs
        ▼
   ## [erp-v1.1.0] — 2026-08-XX          ← matches the annotated tag exactly (Ch 29)
   ## [erp-v1.0.0] — 2026-07-19
   ...
   [Unreleased]: …/compare/erp-v1.1.0...HEAD        ← clickable diffs, only possible
   [erp-v1.1.0]: …/releases/tag/erp-v1.1.0             because tags never move
```

# Practical — draft the next release from history
Read-only, safe to run now, in `/home/tech/umesh-personal`. **Step 1 — what is even in scope:**

```bash
git log --oneline erp-v1.0.0..HEAD | wc -l          # 22 — includes merge commits
git log --no-merges --oneline erp-v1.0.0..HEAD | wc -l   # 16 — the real changes
```
Merge commits are bookkeeping ([Ch 11](11_Merging.md)); `--no-merges` is almost always what you want for release notes.

**Step 2 — the census, so you know the bump before you write a word:**
```bash
git log --no-merges --pretty=%s erp-v1.0.0..HEAD | grep -oE '^[a-z]+' | sort | uniq -c | sort -rn
```
Real output today:
```
      6 feat
      4 docs
      3 fix
      1 test
      1 chore
```
Six `feat`, no `!` → MINOR → `erp-v1.1.0` ([Ch 29](29_Semantic_Versioning_And_Tags.md)). And note the arithmetic: 6+4+3+1+1 = **15**, but there are **16** commits. One commit — `KOS v1.0: Engineering Knowledge Operating System` — predates the `commit-msg` hook and is not Conventional, so a mechanical grouping **silently drops it**. That is the entire argument for a human pass over the draft: a generator loses what it cannot parse and never tells you.

**Step 3 — the Added section's raw material:**
```bash
git log --no-merges --pretty='%s' erp-v1.0.0..HEAD | grep '^feat'
```
```
feat(storefront): premium public homepage + login UI — About section, GSAP/Lenis motion system
feat(production): bundle allocation engine (AE-1→4) + genericity cleanup + BUG-B1 fix + full certification suite
feat(production): surface AE-4 Production Snapshot link on adda detail
feat(production): super-admin Adda cancel + safe delete with money/earning guard
feat(production): worker roster picker as searchable multi-select dropdown
feat: accountant read tier, student role, learning platform completion, UTC date-class fix
```
Swap `feat` for `fix` and you have the **Fixed** section's raw material. `git shortlog --no-merges erp-v1.0.0..HEAD` groups the same set by author — useful the moment there is more than one contributor.

**Step 4 — translate, one line each.** For every raw subject, ask *"what can the reader now do that they could not before?"* and write that. Drop anything with no answer.

**Step 5 — the release-day edit**, done by hand in the release PR:
1. Rename `## [Unreleased]` to `## [erp-v1.1.0] — 2026-08-XX` (today's real date).
2. Add a fresh empty `## [Unreleased]` above it.
3. Update the bottom link refs: `[Unreleased]` now compares `erp-v1.1.0...HEAD`, and add an `[erp-v1.1.0]` release link.

**The undo**, since this is a file like any other: a changelog mistake is fixed by editing the file and committing, or `git restore CHANGELOG.md` before you commit ([Ch 15](15_Undo_Reset_Revert_Restore.md)). Nothing here is dangerous — which is exactly why it is inexcusable to skip.

# Production Walkthrough
Where the changelog sits in this project's real flow:

1. **During normal work** — a PR that adds a user-visible capability adds its line to `[Unreleased]` **in the same PR**. Not later. This is `CLAUDE.md` rule 12 (docs ship with code) applied to release notes, and it is the only reliable defence against memory-writing.
2. **Review** — a reviewer reads the changelog line as part of the diff, per `CONTRIBUTING.md` §5. If the line is unreadable to a non-developer, that is a review comment, not a nitpick.
3. **Release day** — `CONTRIBUTING.md` §7's order matters: tag, then *"update `CHANGELOG.md` and cut a GitHub Release from the tag."* The `[Unreleased]` section becomes the version section, and its text becomes the **body of the GitHub Release** — written once, used twice.
4. **Deploy** — the operator reads the version section, not the diff. If something misbehaves, that section is the shortlist of suspects, which is why "only what a reader can perceive" is a *practical* rule and not a stylistic one.
5. **Audit, months later** — somebody asks about the dumps in old commits. The `Fixed` entry answers with the audit result and the deliberate decision. No chat log required.

The honest gap, stated rather than hidden: the second changelog at `django_inventory/CHANGELOG.md` is stale (newest heading `2026-06-02`, `verified: 2026-07-13`). Until it is retired or marked superseded, a new developer can read the wrong file first. Written down as debt beats pretending it is clean.

# Debugging Guide
| Symptom | Cause | Fix |
|---|---|---|
| Changelog written weeks after the release, missing things | no `[Unreleased]` habit | add the line in the same PR as the code; a release-day rename is then trivial |
| Two changelogs disagree | no canonical file declared | one per product; the other gets a "superseded by …" first line or is deleted |
| Entries read like commit subjects | copy-pasted from `git log` | rewrite per reader: what can they now do that they could not? |
| Release notes swamped by internal churn | `docs`/`refactor`/`test` included | those types produce no entry — 83 of 324 commits here are `docs` |
| A real change is missing from the generated draft | its commit is not Conventional, so the grouping dropped it | the `KOS v1.0` case — always human-check the count against `--no-merges` |
| Version heading is not clickable | link refs at the bottom not updated | maintain both lines every release: `[Unreleased]` compare and `[<tag>]` release |
| Heading date disagrees with the tag date | tagged and edited on different days | the changelog date is the **release** date; take it from the tag, not your memory |
| Merge commits padding the list | `git log` without `--no-merges` | always `--no-merges` for release notes: 22 commits versus 16 real ones |
| Security entry published before the fix is deployed | disclosure timing not considered | land and deploy the fix first, then describe the class of issue, never the exploit |
| Nobody reads it | it is either empty or unreadable | make it the GitHub Release body — a changelog with an audience gets maintained |

# Performance Notes
- Every command here is O(commits since the last tag). On 22 commits it is instant; `git log` is designed to walk far more than this.
- `--no-merges` cuts the working set by more than a quarter in this repo (22 → 16) and removes the entries you would delete anyway.
- On a repo with thousands of commits per release, `git shortlog --no-merges` plus type-grouping is the scalable draft; that is what GitHub's own "auto-generated release notes" button does, only grouped by PR label instead of commit type.
- The *human* pass is the real cost, and it scales with **entries kept**, not commits scanned. Ruthless filtering is a performance optimisation for the reader.
- Frequent small releases keep each changelog section short and each release reviewable — the same argument as small PRs ([Ch 21](21_Pull_Requests.md)).

# Security Considerations
- **A `Security` entry has timing.** Describe a vulnerability *after* the fix is released, never while users are exposed. Say the class and the impact; never publish a reproduction.
- **Say what, not how much detail.** The real entry here names *categories* — OAuth tables empty, hashes at 1,000,000 pbkdf2 iterations, sessions expired — and prints **no hash, no email, no row**. Copy that restraint.
- **A changelog is public the moment the repo is.** This repository is public at the time of writing and going private; anything written into `CHANGELOG.md` should be assumed already read. Write with that assumption and you never need to redact.
- **Never paste secrets, tokens, internal hostnames or customer names** into an entry, even "temporarily". It is a tracked file: once committed, it lives in history whatever you do next ([Ch 33](33_Secrets_And_Leaks.md), [Ch 34](34_Rewriting_History.md)).
- **Version numbers are reconnaissance.** "Now on Django 5.0.1" tells an attacker exactly which CVE list to try. Fine in a private changelog; think twice before putting it on a public page.
- **Record decisions, not blame.** "History deliberately not rewritten, because 0 forks and nothing usable inside" is a defensible engineering record. "X committed a dump" is a liability with no upside.

# Architecture Decisions
- **Keep a Changelog + SemVer**, declared at the top of the file. A named convention means a new contributor needs no explanation, and the reader knows what a MINOR bump promises.
- **`[Unreleased]` maintained continuously**, edited in the same PR as the code. Rejected "write it at release time": that is memory-writing, and the file itself calls memory-writing fiction.
- **Hand-curated, derived from commits — no release bot.** `semantic-release` and friends were rejected for a 1–2 person team for the same reason as in [Ch 29](29_Semantic_Versioning_And_Tags.md): the entries a bot writes are commit subjects, and the sentence a reader needs is not a commit subject. The mechanical part (the census, the bump) is scripted; the sentence is human.
- **The monorepo root file is canonical** for the shipped ERP, because releases are tagged at the root (`erp-v1.0.0`) and the changelog must live at the same grain as the tag.
- **Plain markdown at the root, frontmatter in `docs/`.** The root file is read on GitHub; the `docs/` tree carries `id`/`owner`/`verified` frontmatter for the knowledge-graph tooling. Different audiences, different headers.
- **Only Keep a Changelog's six categories.** Rejected inventing project-specific ones ("Performance", "Internal"): a category nobody else recognises is a category the reader has to learn.
- **Open debt, recorded not hidden:** `django_inventory/CHANGELOG.md` is stale and should be retired or marked superseded. Naming it here is the honest position until it is done.

# Best Practices
- Add the entry in the **same PR** as the change. Always.
- Write for the reader: capability, not implementation. Name the *user*, name the *new ability*.
- Keep the six categories; keep newest-first; keep dates absolute and ISO.
- Maintain the bottom link refs so every heading is a clickable diff.
- Let the machine draft (`--no-merges`, type census) and a human write the sentence.
- Reuse the version section as the GitHub Release body — one text, two homes.
- Record deliberate *inaction* as a decision, with its reasoning.
- Declare one canonical changelog per product and mark anything else superseded.
- For a security entry: fix, deploy, *then* describe — class and impact only.

# Beginner Mistakes
- **Pasting `git log --oneline` into the file** → a wall of internal vocabulary the reader cannot use. Translate every line.
- **Writing it at release time from memory** → the fix you forgot is the one the operator needed. `[Unreleased]`, continuously.
- **Including `docs:` / `refactor:` / `test:` entries** → 83 of this repo's 324 commits are `docs`. Real work; not release notes.
- **Keeping two changelogs** → one is lying and the reader cannot tell which. Declare a canonical file.
- **Relative dates ("last month")** → meaningless the moment anyone reads it later. ISO dates, taken from the tag.
- **Forgetting the bottom link refs** → headings stop being clickable and the file quietly rots.
- **Counting merge commits as changes** → 22 versus 16 here. `--no-merges`.
- **Trusting a generated draft blindly** → the one non-Conventional commit (`KOS v1.0`) vanishes silently. Check the count.
- **Deleting a bad release's section** → readers who deployed it lose their record. Mark it `[YANKED]`.
- **Publishing a vulnerability before the fix ships** → you have written an exploit guide with a date on it.
- **A version heading that does not match the tag** → the changelog and the deployable artefact now disagree on names, which is the one thing a changelog exists to prevent.

# Interview Questions
- **Junior:** "Why keep a CHANGELOG when you have `git log`?" — Different readers. `git log` is the complete register for developers, in developer vocabulary, including internal churn like docs and refactors. `CHANGELOG.md` is a curated statement for users and operators: what was added, changed and fixed, in language they can act on. In this repo the changelog also matches the release tags, so each version heading links to the exact diff.

- **Mid:** "How do you produce it without it becoming a chore?" — Two halves. The machine drafts: `git log --no-merges` since the last tag, grouped by Conventional Commit type — `feat:` to Added, `fix:` to Fixed, `!` to Removed/Changed, and `docs`/`chore`/`test` to nothing. Then a human rewrites each kept line as a capability the reader can perceive. Entries land in `[Unreleased]` in the *same PR* as the code, so release day is just renaming a heading, adding a date, and refreshing two link references. The reason drafting works at all is that a `commit-msg` hook refuses non-Conventional messages.

- **Senior:** "Your generated draft has 15 grouped commits but 16 commits exist. What do you do?" — Find the missing one and understand *why* it was invisible before I trust the tool again. Here it is a commit whose subject predates the hook and is not Conventional, so a `^[a-z]+` type grouping silently skips it. That is a **silent content-loss defect**: the pipeline produced a plausible, wrong result with no error, which is the worst class of bug in any generator. The fixes, in order: always reconcile the grouped count against `git log --no-merges | wc -l`; treat "unparsed" as a visible bucket in the tool rather than a dropped row; enforce the format at commit time so the corpus stays parseable; and never let a fully automated changelog be the only artefact — the human pass is the check.

- **Staff:** "Design the release-notes practice for this project and defend the trade-offs." — Constraints: one owner plus occasional collaborators, a monorepo with several deliverables, tagged releases, no paid tooling, and a product whose users are factory staff rather than developers. Design: (1) **one canonical `CHANGELOG.md` at the grain of the tag** — the root, because releases are `erp-v*` at the root; anything else is marked superseded, because two changelogs means one lies, and this repo currently *has* that drift and it is recorded as debt rather than hidden; (2) **`[Unreleased]` maintained per-PR**, enforced in review alongside the docs-sync rule, since post-hoc writing loses precisely the unglamorous fixes; (3) **derive the draft, hand-write the sentence** — accept the human cost because the value of the file is translation, which is the one thing automation cannot do; (4) **the version section is also the GitHub Release body**, so the file has a real audience and therefore stays maintained; (5) **the changelog doubles as a decision record** for deliberate inaction — the untracked-dumps entry states the audit result *and* that history was intentionally not rewritten, which is what stops a future auditor reading a judged trade-off as an oversight; (6) **security entries follow disclosure discipline** — fix and deploy first, then publish class and impact with no reproducible detail. What I would add as the team grows: a CI check that a user-facing diff touches the changelog, and PR labels so the draft can be grouped by label instead of commit type. What I would still refuse: a bot that publishes release notes unread, because the certification sentence a release carries here ("GO WITH ACCEPTED RISKS") is a human judgement.

### Why interviewers ask these — and the answer that separates levels

| Testing for | Weak answer | What lands |
|---|---|---|
| Do you know who actually reads it? | "It lists the commits." | Name the reader — operator, owner, future-you — then say what you deliberately *exclude* and why (83 of 324 commits here are docs). |
| Process discipline: when is it written? | "At release time, from the log." | `[Unreleased]`, edited in the same PR as the code. A changelog written from memory is fiction, and the fix you forget is the one that mattered. |
| Tooling judgement: derive or generate? | "A bot generates it for us." | Machine drafts the census and the bump; a human writes the sentence. Reconcile counts, because a generator silently drops what it cannot parse. |
| Security judgement: timing and detail | "We document the vulnerability." | Fix, deploy, then publish class and impact only — never a reproduction, never a hash, an email or a row. |

**The killer follow-up:** *"Show me your last release's entry and tell me what you left out."* — Anyone can show the file. The answer that lands names the exclusions and the rule behind them — internal refactors, doc churn, merge commits — and then names one thing kept *because a reader would feel it*, such as a settlement date fix. Knowing what to leave out is the whole skill.

# Revision Notes
- `git log` = complete register **for developers**. `CHANGELOG.md` = curated statement **for readers**. Both, never one.
- **Keep a Changelog**: newest first, `[Unreleased]` on top, ISO dates, six categories — Added, Changed, Deprecated, Removed, Fixed, Security.
- Bottom **link refs** make headings clickable: `compare/<tag>...HEAD` and `releases/tag/<tag>` — they work only because tags never move (Ch 29).
- Mapping: `feat` → Added · `fix` → Fixed · `!` → Removed/Changed + MAJOR · `docs`/`chore`/`test`/`refactor` → **nothing**.
- Write the entry in the **same PR** as the code. *A changelog written from memory is fiction.*
- Draft with `--no-merges` (22 commits → 16 real), then census the types; **6 feat, 3 fix** here → MINOR → `erp-v1.1.0`.
- ⚠️ **A generator silently drops what it cannot parse** — one non-Conventional commit vanished (15 grouped vs 16 real). Always reconcile counts.
- Two changelogs = one lying. Real drift here: `django_inventory/CHANGELOG.md` stops at `2026-06-02`.
- The changelog is also a **decision record**: "history deliberately not rewritten" turns a future auditor's "oversight" into "judged trade-off".
- Security entries: **fix, deploy, then describe** — class and impact only, no reproduction, no hashes, no emails.

# Cheat Sheet
```bash
git log --oneline erp-v1.0.0..HEAD                       # everything since the release (22)
git log --no-merges --oneline erp-v1.0.0..HEAD           # real changes only (16)
git log --no-merges --pretty=%s erp-v1.0.0..HEAD         # bare subjects — the draft's raw material
git log --no-merges --pretty=%s erp-v1.0.0..HEAD | grep '^feat'   # → the Added section
git log --no-merges --pretty=%s erp-v1.0.0..HEAD | grep '^fix'    # → the Fixed section
git log --no-merges --pretty=%s erp-v1.0.0..HEAD | grep -oE '^[a-z]+' | sort | uniq -c | sort -rn   # type census → the bump
git shortlog --no-merges erp-v1.0.0..HEAD                # grouped by author (multi-contributor)
git log --grep='BREAKING CHANGE' erp-v1.0.0..HEAD        # any MAJOR trigger hiding in a footer
git restore CHANGELOG.md                                 # UNDO uncommitted changelog edits
```
- **Section skeleton:** `## [Unreleased]` → `### Added` / `### Changed` / `### Deprecated` / `### Removed` / `### Fixed` / `### Security`.
- **Release day:** rename `[Unreleased]` → `## [erp-v1.1.0] — YYYY-MM-DD`, add a fresh empty `[Unreleased]`, update both link refs, paste the section into the GitHub Release.
- **Pulled release:** mark it `[YANKED]`; never delete the section.

# My ERP Section
| Concept | In this repo |
|---|---|
| Canonical file | `/CHANGELOG.md` at the monorepo root — same grain as the `erp-v*` tags |
| Format declared | Keep a Changelog 1.1.0 + Semantic Versioning 2.0.0, stated in the header |
| Maintenance rule | "Update it in the release PR, not months later — a changelog written from memory is fiction" |
| Sections today | `[Unreleased]` (Added / Changed / Fixed) and `[erp-v1.0.0] — 2026-07-19` |
| Link refs | `compare/erp-v1.0.0...HEAD` and `releases/tag/erp-v1.0.0` under `umesh29032/umesh-personal` |
| What feeds it | Conventional Commits, enforced by `git-hooks/commit-msg` (Ch 25) |
| Draft scope | 22 commits since the tag, **16** non-merge; census 6 `feat` · 4 `docs` · 3 `fix` · 1 `test` · 1 `chore` |
| Parser gap | `KOS v1.0: …` is not Conventional → grouped count 15 versus 16 real commits |
| Decision record | the untracked-dumps entry: audit verdict **exposure mild**, history **deliberately not rewritten** |
| Known drift | `django_inventory/CHANGELOG.md` — stale (`## [Unreleased] — 2026-06-02`, `verified: 2026-07-13`), needs retiring |
| Release order | `CONTRIBUTING.md` §7 — annotated tag → update `CHANGELOG.md` → cut the GitHub Release |
| Docs law it obeys | `CLAUDE.md` rule 12 — docs ship in the same PR as the code |

# Practice Tasks
1. **Read both:** open `/CHANGELOG.md` and `/django_inventory/CHANGELOG.md`. In three sentences, prove which is canonical using only evidence in the files.
2. **Draft it:** run the Step 2 and Step 3 commands. Produce a real `## [erp-v1.1.0]` section with Added and Fixed, every line rewritten for a factory owner.
3. **Find the dropped commit:** reconcile the type census against `--no-merges | wc -l`, name the commit the grouping loses, and explain why no error was printed.
4. **Classify:** for each, give the category or say "no entry" — (a) settlement date corrected from UTC to IST, (b) `ds_lint.sh` refactored, (c) a worker role losing a page, (d) the git course added, (e) dumps untracked from a public repo.
5. **Redact:** rewrite the dumps entry as a `### Security` entry for a *public* changelog. What must you remove, and what must stay for it to remain honest?

# Homework
- Write the `[Unreleased]` line you would have added for `feat(production): worker roster picker as searchable multi-select dropdown`, then show it to someone non-technical. If they cannot say what changed, rewrite it.
- Decide the fate of `django_inventory/CHANGELOG.md`: retire, merge, or mark superseded. Write the one-line notice you would put at its top, and say which `CLAUDE.md` rule your choice satisfies.
- Draft a CI check that fails a PR touching `config/**/views/` with no `CHANGELOG.md` change. Then argue whether you would actually ship it, given four jobs already run ([Ch 28](28_CI_With_GitHub_Actions.md)).
- Read the Django project's own release notes for a MINOR version. List three habits worth stealing, and one thing that only makes sense for a public library.
- Write a `### Security` entry for a hypothetical exposed API key: fix, deploy, then publish. What is the shortest honest sentence that helps users without helping an attacker ([Ch 33](33_Secrets_And_Leaks.md))?

---

# Further Reading & Live Resources
- **Keep a Changelog 1.1.0** — the convention this file declares, including `[YANKED]`: https://keepachangelog.com/en/1.1.0/
- Semantic Versioning 2.0.0 — what a MINOR heading promises the reader: https://semver.org/
- Conventional Commits 1.0.0 — the input format that makes a draft derivable: https://www.conventionalcommits.org/en/v1.0.0/
- `git-shortlog` manual — grouping history by author for release notes: https://git-scm.com/docs/git-shortlog
- `git-log` manual — `--no-merges`, `--pretty`, `--grep`, revision ranges: https://git-scm.com/docs/git-log
- GitHub Docs — *automatically generated release notes* (label-grouped, the hosted version of this pipeline): https://docs.github.com/en/repositories/releasing-projects-on-github/automatically-generated-release-notes
- Django release notes — a long-running, disciplined example to imitate: https://docs.djangoproject.com/en/5.0/releases/
