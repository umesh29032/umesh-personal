---
id: git-course-29-semantic-versioning-and-tags
type: lesson
status: active
owner: handwritten
scope: git, version control — naming a release (SemVer) and pinning it in history (tags)
anchors: CONTRIBUTING.md, CHANGELOG.md, .github/workflows/ci.yml, .github/dependabot.yml
verified: 2026-08-03
---

# 29 — Semantic Versioning & Tags (giving one commit a name you can deploy)

> Part of [Git Course](00_COURSE_OVERVIEW.md). Prev: [28 — CI with GitHub Actions](28_CI_With_GitHub_Actions.md). Next: [30 — CHANGELOG](30_Changelog.md).

# Learning Objectives
By the end of this chapter you can:
- decode `MAJOR.MINOR.PATCH` and say which number a given change bumps — and why
- explain the difference between a **lightweight** and an **annotated** tag, and prove which is which in a repo
- map Conventional Commit types (`feat` / `fix` / `!`) onto a version bump mechanically
- create, push, inspect and delete tags — and say why you must **never move** a released one
- read `git describe` output like `kos-v1.0-18-g42a2ecc4` and state exactly what it tells you

# Purpose
CI ([Ch 28](28_CI_With_GitHub_Actions.md)) proves a commit is *good*. This chapter is about making one good commit **nameable** — so that "what is running in the factory?" has an answer shorter than a 40-character hash, and so "put it back exactly how it was" is one command. A tag is that name; SemVer is the grammar for choosing it.

# The Problem
The factory floor calls you: since this morning, worker settlement totals look wrong. You need to answer three questions fast.

1. **What is running on the server?** If the answer is *"whatever `main` was on Tuesday"*, you have no answer — `main` has moved since.
2. **What changed since the last known-good state?** Without a fixed marker, "since" has no starting point.
3. **How do I go back?** With a marker: one command. Without: you are reading `git log` under pressure, guessing at hashes, at the exact moment your judgement is worst.

And there is a slower, quieter version of the same pain. Somebody asks you to "upgrade Django" and you have no idea whether `5.0.1 → 5.1.0` is a Tuesday-afternoon job or a week of migrations. A version number that follows rules answers that before you open the release notes. A version number invented by feel (`v2-final-new`, `v2-final-really`) answers nothing.

# Theory (from zero)

### What a tag actually IS
[Ch 09](09_What_A_Branch_Really_Is.md) taught that a branch is just a file under `.git/refs/heads/` containing a commit hash — a **sticky note** that *moves* when you commit.

A **tag** is the same idea with the movement removed. It lives in `.git/refs/tags/`, points at one commit, and nothing in normal git ever moves it. Branch = "where I am working". Tag = "this exact point in history, forever".

There are two kinds, and the difference matters more than it looks:

**Lightweight tag** — literally a ref file with a commit hash in it. No author, no date, no message. `git tag kos-v1.0` makes one. It is a bookmark.

**Annotated tag** — `git tag -a`. This creates a **real object** in the database ([Ch 05](05_How_Git_Stores_Everything.md)): a fourth object type alongside blob, tree and commit. It stores the target commit, the tag name, **who** tagged it, **when**, and a **message** — and it can be cryptographically **signed** ([Ch 31](31_Signed_Commits.md)). It is a signed-and-dated record that a release happened.

That is why `CONTRIBUTING.md` §7 says annotated, never lightweight: *"an annotated tag is a real object with an author, date and message, so the release is self-documenting."* A lightweight tag six months later cannot tell you who cut it or why.

### How to tell them apart in one second
```bash
git cat-file -t <tagname>
```
Prints `tag` for annotated (there is an object to inspect) and `commit` for lightweight (the ref points straight at the commit — there is no tag object at all). You will use this on the real repo below, and find one of each.

### Semantic Versioning, from zero
**SemVer** is a public contract encoded in three numbers: `MAJOR.MINOR.PATCH`.

| Bump | When | Promise to whoever consumes your code |
|---|---|---|
| **PATCH** — `1.0.0 → 1.0.1` | a backwards-compatible bug fix | "upgrade blindly, nothing you use changed" |
| **MINOR** — `1.0.0 → 1.1.0` | a new backwards-compatible feature | "upgrade safely, you may ignore the new thing" |
| **MAJOR** — `1.0.0 → 2.0.0` | a **breaking** change | "read the notes, you will have to change something" |

Two extra shapes you will meet:

- **Pre-release:** `1.1.0-rc.1`. Anything after a `-` marks it as *not final*, and it sorts **before** `1.1.0`. Use it for a staging candidate.
- **Build metadata:** `1.1.0+20260803`. Anything after a `+` is ignored for ordering — it is a note to humans and build systems.

And one rule people forget: **`0.y.z` means "no promises yet"**. While a project is `0.x`, anything may break at any time. Shipping `1.0.0` is a commitment, not a celebration.

### "Breaking" in a Django ERP — name the surface
SemVer talks about breaking your **public API**. A library's public API is obvious. For an internal factory ERP it is not, so define it explicitly or the numbers become guesswork. Here, a change is **MAJOR** if it breaks any of:

- **URLs / views** an operator has bookmarked or a mobile screen calls
- **the database schema** in a way that is not backwards-compatible (a dropped column, a narrowed constraint) — see the real example below
- **management commands** or their arguments, which a deploy script calls
- **settings / environment variables** the deploy needs (`.env` keys, feature flags)
- **roles and permissions** — a role losing access is a break for the human holding it

A new page, a new report, a new optional flag: **MINOR**. A wrong total corrected, a 500 fixed: **PATCH**.

### From commit message to version number, mechanically
This is the payoff of [Ch 25](25_Conventional_Commits.md). Because every commit here starts with a type, the bump is *derivable* rather than debated:

| In the commits since the last tag | Bump |
|---|---|
| any `!` after the type, or a `BREAKING CHANGE:` footer | **MAJOR** |
| otherwise, any `feat:` | **MINOR** |
| otherwise, any `fix:` | **PATCH** |
| only `docs:` / `chore:` / `test:` / `refactor:` / `style:` / `ci:` | no release needed |

Both spellings of "breaking" are legal: `feat(api)!: drop the v1 endpoint`, or a `BREAKING CHANGE:` line in the footer. The `!` is harder to miss in `git log --oneline`, which is why the `commit-msg` hook's own examples use it.

### The one thing you must never do
**Never move a tag that other people have fetched.** Git deliberately does *not* update a tag you already have when you `git fetch` — it assumes a tag is a fixed point. So if you force a tag to a new commit and force-push it, everyone who fetched the old one keeps the old one. `erp-v1.0.0` then means two different commits on two different machines, and "reproduce the bug from the release" becomes impossible to reason about.

If a release is wrong: **cut the next version.** Tags are cheap; a lying tag is not.

> 💡 **Samjho aise:** Branch **chalti hui bookmark** hai — jitna aage padhoge, utna aage khisak jaayegi. Tag **deewaar pe thok diya hua keel** hai: "1 tarikh ko yahi maal factory gaya tha." Lightweight tag = pencil se naam likh diya. Annotated tag = **stamp-paper wali receipt** — kisne diya, kab diya, kyun diya, sab likha hai. Aur version number ghar ke pate jaisa hai: pehla number badla to **naya ghar** (purani chaabi nahi lagegi = breaking), doosra badla to **naya kamra** (purana sab chalta rahega), teesra badla to sirf **naali theek** hui. Sabse badi galat baat: keel ko chupke se hila dena. Jisne pehle dekh liya uske liye keel wahi purani jagah rahegi — aur do aadmi ek hi naam se do alag jagah samjhenge.

# Real World Example (this repo)
Three tags exist in `/home/tech/umesh-personal`, and they teach three different lessons:

```
$ git for-each-ref --format='%(refname:short) %(objecttype) %(objectname:short) %(taggerdate:short) %(subject)' refs/tags
erp-v1.0.0 tag 0cccb32b 2026-07-19 Kapil Enterprises ERP — Manufacturing V1 production release anchor. …
kos-v1.0 commit 1e042648   KOS v1.0: Engineering Knowledge Operating System
pre-refactor-baseline tag 520923fb 2026-06-09 Pre-refactor baseline: 305 tests green, ~103s. …
```

Read the second column. `erp-v1.0.0` and `pre-refactor-baseline` are `tag` — **annotated**, with a real tagger date. `kos-v1.0` is `commit` — **lightweight**, and notice its empty date column. `CONTRIBUTING.md` §7 says annotated only, so `kos-v1.0` is a live, small, honest inconsistency in this repo: the rule was written after that tag was cut. Do not "fix" it by moving it — the whole point of the previous section.

Now open the annotated one and see what an annotated tag actually stores:

```
$ git cat-file -p erp-v1.0.0
object 90c1f2f31f47c199d83dedb52d202ce3ba63ea11
type commit
tag erp-v1.0.0
tagger umesh-personal <umesh29mar@gmail.com> 1784406128 +0530

Kapil Enterprises ERP — Manufacturing V1 production release anchor.
Release Certificate: GO WITH ACCEPTED RISKS (RELEASE_CERTIFICATION_LOG §9.7, 2026-07-19).
Battery 1878/1878 · 8/8 dimensions certified · commit 90c1f2f3.
```

Every field earns its place: `object` is the commit it pins (`90c1f2f3`), `tagger` is who is accountable, the number is a Unix timestamp with the `+0530` IST offset, and the message records the **verdict and the evidence** — the battery count at the time and the certificate section. That is a release you can defend a year later without opening a chat log.

Note also the **prefix convention**: `erp-v1.0.0`, not `v1.0.0`. This git root is a monorepo holding more than one product, and `kos-v1.0` is a different thing versioned on its own clock. Prefixed tags are how one repository carries several release timelines without collisions.

### `git describe` — "where am I, relative to the last tag?"
```
$ git describe --tags
kos-v1.0-18-g42a2ecc4
```
Decode it left to right: **`kos-v1.0`** = the nearest tag reachable *behind* HEAD; **`18`** = HEAD is 18 commits after it; **`g42a2ecc4`** = HEAD's short hash, where the `g` just means "git". So: *"18 commits past `kos-v1.0`, at `42a2ecc4`."*

If HEAD were exactly on a tag, `describe` would print only the tag name — which makes it a perfect build stamp: put it in a footer or a `/health` endpoint and you always know precisely what is deployed. And it explains why `erp-v1.0.0` did not win here: `describe` finds the *nearest ancestor* tag, and `kos-v1.0` is closer.

### What is the next version, then?
```
$ git rev-list --count erp-v1.0.0..HEAD
22
$ git log --pretty='%s' erp-v1.0.0..HEAD | grep -E '^(feat|fix)'
feat: accountant read tier, student role, learning platform completion, UTC date-class fix
feat(production): worker roster picker as searchable multi-select dropdown
feat(production): super-admin Adda cancel + safe delete with money/earning guard
fix(inventory): role form mobile-responsive grids + scoped header type
feat(production): surface AE-4 Production Snapshot link on adda detail
feat(production): bundle allocation engine (AE-1→4) + genericity cleanup + BUG-B1 fix + full certification suite
fix(production): P19A P0 — layering-start 500 + multi-lane report 500 + dev conn leak
feat(storefront): premium public homepage + login UI — About section, GSAP/Lenis motion system
fix(deploy): track deploy.sh executable (operator runs ./deploy/deploy.sh)
```
Twenty-two commits since `erp-v1.0.0`; `feat:` present, no `!` and no `BREAKING CHANGE:` footer. The rules decide for you: the next tag is **`erp-v1.1.0`** — a MINOR bump. No meeting required.

For contrast, the repo's *only* breaking commit in 324, found by looking for the `!`:

```
$ git log --pretty='%h %s' | grep -E '^[0-9a-f]+ [a-z]+(\(.*\))?!:'
e01f0c4b feat(production)!: V2-1d — drop the worker M2M; WorkerStageTask + WorkerStageContribution are the sole production truth
```
*Dropping* a many-to-many table is exactly the "narrowed schema" case from the list above: code and data that relied on it stop working. That is a MAJOR, and the `!` is the marker that would drive it.

# Visual Diagram
```
  BRANCH pointer MOVES with every commit        TAG pointer NEVER moves
  ────────────────────────────────────────────────────────────────────────────

   90c1f2f3 ──► … 22 commits … ──► 1e042648 ──► … 18 commits … ──► 42a2ecc4
      ▲                                ▲                              ▲
      │                                │                              │
  [erp-v1.0.0]                    [kos-v1.0]                   main / HEAD ──► moves
   annotated tag                lightweight tag                        (a branch)
   tag object 0cccb32b          NO tag object:
   ├ object  90c1f2f3…            ref points straight
   ├ tagger  umesh-personal       at the commit
   ├ date    2026-07-19          (no author/date/message)
   └ message "GO WITH ACCEPTED RISKS · battery 1878/1878"

  git describe --tags  ⇒  kos-v1.0-18-g42a2ecc4
                          └──┬───┘ └┬┘ └───┬────┘
                     nearest tag   commits  HEAD's short hash
                      BEHIND HEAD   since    ("g" = git)

  git cat-file -t erp-v1.0.0 ⇒ tag      (annotated)
  git cat-file -t kos-v1.0   ⇒ commit   (lightweight)
```

# Practical — inspect tags now, cut one later
**Read-only, safe to run right now** in `/home/tech/umesh-personal`:

```bash
git tag -n1                         # every tag with the first line of its message
git cat-file -t erp-v1.0.0          # expect: tag      (annotated)
git cat-file -t kos-v1.0            # expect: commit   (lightweight)
git cat-file -p erp-v1.0.0          # the tag object: object/type/tag/tagger/message
git describe --tags                 # expect: kos-v1.0-18-g42a2ecc4
git rev-list --count erp-v1.0.0..HEAD          # expect: 22
git log --oneline erp-v1.0.0..HEAD             # exactly what would go in the release
git tag --points-at HEAD            # any tag on this commit (silence = none)
git tag --contains erp-v1.0.0       # which tags come after that one
git show erp-v1.0.0 --stat | head -20          # tag message, then the commit it pins
```

**Writing commands — shown, deliberately not run here.** These change refs, so read them, then run them only when you actually mean to cut a release:

```bash
git tag -a erp-v1.1.0 -m "erp-v1.1.0 — accountant read tier, learning platform, UTC date fix"
git push origin erp-v1.1.0
```
`-a` = annotated (never lightweight, per `CONTRIBUTING.md` §7). Note the second line: **a plain `git push` does not push tags.** You push a tag by name, or use `git push --follow-tags`, which pushes annotated tags reachable from the commits you are already pushing — a safer default than `--tags`, which pushes every tag you happen to have locally.

**The undo, in the same breath:**

```bash
git tag -d erp-v1.1.0                    # delete LOCALLY (harmless, instant)
git push origin --delete erp-v1.1.0      # delete on the REMOTE — only if nobody has used it
```
Deleting a local tag is trivial; deleting a *published* one is a coordination problem, because anybody who already fetched it still has it. And if you deleted a tag you actually needed, the commit is untouched — re-tag it: `git tag -a erp-v1.1.0 <hash>`. Nothing is lost, because a tag was only ever a name for a commit that still exists ([Ch 16](16_Reflog.md)).

**The one to know and refuse:**

```bash
git tag -f erp-v1.0.0 <other-commit>     # move a tag
git push --force origin erp-v1.0.0       # ⚠ DO NOT: clones keep the OLD target
```
Do not. Cut `erp-v1.0.1` instead. The only defensible use of `-f` is a tag you created two minutes ago and have not pushed.

Also worth knowing: `git switch --detach erp-v1.0.0` (or `git checkout erp-v1.0.0`) puts you in **detached HEAD** — you are standing on a commit, not on a branch, so new commits there belong to nothing. That is fine for looking, and `git switch -` brings you back. If you want to *fix* something at a release point, branch from it: `git switch -c fix/hotfix-1.0.1 erp-v1.0.0`.

# Production Walkthrough
Cutting `erp-v1.1.0` in this repo, start to finish:

1. **All work is merged.** `main` holds the squash-merged features ([Ch 21](21_Pull_Requests.md)); nothing sits half-landed.
2. **CI is green on `main`.** The `push: branches: [main]` trigger already ran all four jobs ([Ch 28](28_CI_With_GitHub_Actions.md)). You tag a *verified* commit, never a hopeful one.
3. **Decide the number mechanically.** `git log --pretty='%s' erp-v1.0.0..HEAD` → `feat:` present, no `!` → MINOR → `erp-v1.1.0`.
4. **Update `CHANGELOG.md`** in the release PR: move `[Unreleased]` into a `[erp-v1.1.0] — <date>` section and refresh the compare links at the bottom ([Ch 30](30_Changelog.md)).
5. **Tag, annotated, with evidence in the message** — the shape `erp-v1.0.0` set: what it is, the verdict, the battery count. Today that line would read `battery 2033/2033`.
6. **Push the tag** (`git push origin erp-v1.1.0`) and cut a GitHub Release from it. GitHub attaches auto-generated source archives, so the tag becomes a downloadable artefact for free.
7. **Deploy by tag, not by branch.** The deploy checks out `erp-v1.1.0`. "What is in the factory?" now has a one-word answer, and rollback is `erp-v1.0.0` — a name, not a hash hunt.
8. **Stamp the running app.** `git describe --tags` at build time gives `erp-v1.1.0` exactly on the tag, or `erp-v1.1.0-3-gabc1234` three commits later — instantly telling you whether the server is running a release or a drift.

Honest caveat, same as [Ch 28](28_CI_With_GitHub_Actions.md): on GitHub's free **private** tier, server-side protection rules — the kind that would stop anyone deleting or moving `erp-v1.0.0` — sit in the paid tier alongside branch protection. So tag discipline here is a **habit written in `CONTRIBUTING.md`**, not a lock. The mitigation that *is* free and server-side: collaborators have **Read** access and work from forks ([Ch 20](20_Forks_And_The_Fork_Flow.md)), so nobody but the owner can push a tag at all.

# Debugging Guide
| Symptom | Cause | Fix |
|---|---|---|
| `git push` succeeded but the tag is not on GitHub | plain `git push` never pushes tags | `git push origin <tag>` or `git push --follow-tags` |
| `git describe` says `fatal: No names found` | no reachable tag, or a shallow clone with no tags | `git fetch --tags`; in CI use `fetch-depth: 0`; or `git describe --always` for a bare hash |
| `describe` names an unexpected tag | it finds the nearest **ancestor** tag, not the newest overall | expected: here `kos-v1.0` wins over `erp-v1.0.0`. Use `--match 'erp-v*'` to scope it |
| Teammate's `erp-v1.0.0` points at a different commit | somebody moved a published tag | do not paper over it: agree on truth, delete both sides, re-tag once, and never move again |
| `git fetch` did not update a tag you know changed | git treats tags as fixed and will not clobber one | `git fetch --tags --force` — and treat the need for it as a smell |
| `tag 'erp-v1.1.0' already exists` | that name is taken | pick the next number; only `-f` an unpushed local tag |
| Deleted a tag, panicking | the tag was only a name | the commit is intact: `git tag -a <name> <hash>`, or find it via `git reflog` |
| Committed on a tag, work seems gone | detached HEAD — commits belong to no branch | `git reflog`, then `git switch -c fix/whatever <hash>` |
| Version numbers argued about in review | the surface was never defined | write down what "breaking" means for this app (URLs, schema, commands, env, permissions) |
| Dependabot bump looks scary | it is a SemVer MAJOR on a dependency | read the upstream notes; a MAJOR is the author telling you to expect work ([Ch 32](32_Dependabot_And_Supply_Chain.md)) |

# Performance Notes
- A lightweight tag is one tiny ref file; an annotated tag adds one small object. Tags are effectively free in storage.
- Refs get packed into `.git/packed-refs`, so hundreds of tags cost nothing noticeable. **Tens of thousands** do: every fetch and clone advertises all refs, so a repo with 50k auto-generated tags has slow handshakes. Machine-generated tags are the usual culprit — prefer one tag per release.
- `git describe` walks history backwards to find the nearest tag, so on a 324-commit repo it is instant; on a million-commit monorepo, `--match` and `--first-parent` keep it fast.
- CI: this workflow uses default shallow fetches except for `lint` (`fetch-depth: 0`). A shallow clone has **no tags** — which is exactly why `git describe` fails there unless you ask for depth or `--tags` ([Ch 37](37_Large_Files_And_Performance.md)).
- `git fetch --prune --prune-tags` (or `fetch.pruneTags`) keeps deleted remote tags from lingering locally forever.

# Security Considerations
- **A tag by itself proves nothing about authorship.** Anyone with push access can create `erp-v9.9.9` with any tagger name they like. If a tag is a supply-chain claim ("this is the audited release"), **sign it**: `git tag -s`, verify with `git tag -v` ([Ch 31](31_Signed_Commits.md)). Only annotated tags can be signed — one more reason the rule is annotated-only.
- **Depending on a mutable tag is a supply-chain risk you already met.** `actions/checkout@v4` is a *moving* tag on someone else's repo; if that repo is compromised, your CI runs new code under an old name. Pinning to a commit SHA removes the ambiguity — the same reasoning as "never move a released tag", seen from the consumer's side.
- **Tag messages are permanent and public-ish.** `erp-v1.0.0`'s message cites a certificate section and a test count — good. It must never cite a credential, a customer name, or a live URL with a token in it ([Ch 33](33_Secrets_And_Leaks.md)).
- **A deleted release tag breaks reproducibility.** If the deploy runbook says "check out `erp-v1.0.0`", deleting that tag turns the runbook into fiction and destroys your ability to reproduce a reported bug on the exact shipped code.
- **Version numbers leak information.** Publishing "running Django 5.0.1" tells an attacker which CVEs to try. Fine in a private repo and in your `CHANGELOG`; do not print it on a public page.

# Architecture Decisions
- **SemVer, not dates.** Rejected `v2026.08` calendar versioning: a date tells you *when*, never whether upgrading is safe. Compatibility is the question that matters at deploy time.
- **Annotated tags only** (`CONTRIBUTING.md` §7). The release must carry its own author, date, message — and be signable. `kos-v1.0` is the pre-rule exception, left in place rather than moved, because moving a published tag is worse than an inconsistency.
- **Product-prefixed tags** (`erp-v*`, `kos-v*`). This is a monorepo with more than one deliverable on more than one clock; one shared `v*` namespace would collide immediately.
- **The bump is derived from commit types, not debated.** `feat` → MINOR, `fix` → PATCH, `!` → MAJOR. This is the whole return on the `commit-msg` hook ([Ch 25](25_Conventional_Commits.md)).
- **Tag only CI-green commits on `main`.** A tag is a *promise*; promising an unverified commit is how a rollback target becomes a second outage.
- **Deploy by tag, not by branch.** Branches move; a deploy must be reproducible byte-for-byte months later.
- **No automated release bot.** `semantic-release` and friends were rejected for a 1–2 person team: a bot that tags and publishes on every merge is more machinery than the risk justifies, and the release message here carries a human verdict ("GO WITH ACCEPTED RISKS") that a bot cannot write.
- **Rejected: trusting server-side tag protection.** It sits in the same paid tier as branch protection on private repos, so the free layers do the work — fork-based Read access plus a written rule.
- **No long-lived release branches.** Trunk-based: `main`, short branches, tags. `git-flow` is heavier than this team can justify ([Ch 24](24_Branching_Strategies.md)).

# Best Practices
- Tag from `main`, only when CI is green, only when the `CHANGELOG` entry is in the same PR.
- Always `-a`. Put the *evidence* in the message: verdict, test count, certificate reference.
- Prefix tags per product in a monorepo (`erp-v1.1.0`), and keep the prefix stable forever.
- Push tags explicitly (`git push origin <tag>` or `--follow-tags`) and confirm they appear on the remote.
- Never move or delete a published tag. Cut the next number instead.
- Bake `git describe --tags` into the build so the running app can name its own version.
- Decide and write down what "breaking" means for *your* surface before you need to argue about it.
- Use `-rc.N` pre-releases for staging candidates; keep final numbers clean.
- Read a dependency's MAJOR bump as the author's warning, not as noise.

# Beginner Mistakes
- **`git tag v1.1.0` (lightweight) for a release** → no author, no date, no message, cannot be signed. Use `-a`.
- **Assuming `git push` pushes tags** → the tag exists only on your laptop; the release "does not exist" for everyone else. `git push origin <tag>`.
- **Moving a tag to "fix" it** → two machines, one name, two commits. Cut `1.0.1`.
- **Tagging a commit CI never checked** → your rollback target is unverified, which is how one outage becomes two.
- **Bumping MAJOR for a big feature** → MAJOR means *breaking*, not *important*. A large backwards-compatible feature is MINOR, however proud you are of it.
- **Bumping PATCH for a new feature** → consumers upgrade blindly, expecting no new behaviour. That is a broken promise.
- **Working on a tag in detached HEAD** → commits belong to no branch and look lost. Branch from the tag: `git switch -c fix/x erp-v1.0.0`.
- **`git push --tags`** → pushes every stray local tag, including experiments. Prefer `--follow-tags`.
- **Expecting `git describe` to work in CI** → shallow clones have no tags. `fetch-depth: 0` or `--tags`.
- **Inventing names like `final-v2-new`** → sorts wrong, means nothing, and cannot be compared by a machine. Three numbers and a prefix.

# Interview Questions
- **Junior:** "What is a git tag, and how is it different from a branch?" — Both are refs pointing at a commit, but a branch **moves** as you commit while a tag stays put, so a tag names a fixed point in history. We use annotated tags (`git tag -a`) for releases, which store the tagger, date and a message; a plain `git tag` is lightweight and stores none of that. In this repo `erp-v1.0.0` is the annotated release tag for commit `90c1f2f3`.

- **Mid:** "How do you decide the next version number?" — Semantic Versioning, derived from Conventional Commits since the last tag: any `!` or `BREAKING CHANGE:` → MAJOR, else any `feat:` → MINOR, else any `fix:` → PATCH. Concretely: `git log --pretty='%s' erp-v1.0.0..HEAD` here shows 22 commits with `feat:` and no breaking marker, so the next tag is `erp-v1.1.0`. It is a mechanical decision, which is exactly why the commit format is enforced by a hook.

- **Senior:** "Someone force-moved `v1.2.0` to a new commit and force-pushed it. What breaks, and what do you do?" — Git will not clobber a tag you already have on fetch, so anybody who fetched the old `v1.2.0` still resolves it to the old commit: the name now means two commits across the fleet. Everything downstream is poisoned — a deploy pinned to `v1.2.0` may ship either code, and "reproduce the bug from the release" is no longer meaningful. Recovery: stop the bleeding (freeze deploys), agree on which commit is truth, delete the tag locally and remotely everywhere, re-tag **once** as a *new* version (`v1.2.1`) rather than reusing the poisoned name, and communicate it. Prevention: annotated-and-signed tags, server-side tag protection where it is affordable, and a written rule that a released tag is immutable.

- **Staff:** "Design the versioning and release-tagging strategy for this monorepo, and defend it." — Constraints first: one git root with several deliverables (the Django ERP, the KOS docs system, siblings), a 1–2 person team, no paid GitHub plan, and a suite that asserts exact money totals. Strategy: (1) **product-prefixed SemVer tags**, `erp-vX.Y.Z` and `kos-vX.Y`, so each deliverable keeps its own timeline in one repo — a shared `v*` namespace would collide on day one; (2) **annotated, signed tags only**, carrying the verdict and evidence in the message, because the tag is the audit record of a release decision; (3) **the bump is derived** from Conventional Commits, so the number is not a judgement call — and the "public API" is defined explicitly for an ERP as URLs, schema/migrations, management commands, env vars and permissions, since a library's notion of API does not transfer; (4) **tag only CI-green `main` commits**, and deploy by tag so rollback is a name; (5) **`git describe --tags --match 'erp-v*'`** as the build stamp, which also tells you *how far the server has drifted* past a release; (6) **no release bot** at this size — the release message contains a human certification a bot cannot produce — but the CHANGELOG is derived, not remembered. Honest gaps I would write down rather than hide: server-side tag protection is paid on this plan, so immutability is currently a habit plus fork-based Read access; `kos-v1.0` is lightweight, predating the rule, and is deliberately left alone; and the day a *third* consumer of the schema appears, migrations become a versioned contract of their own and MAJOR discipline gets much sharper.

### Why interviewers ask these — and the answer that separates levels

| Testing for | Weak answer | What lands |
|---|---|---|
| Do you know a tag is a fixed ref, not a branch? | "A tag marks a version." | Both are refs; a branch moves on commit, a tag does not. Annotated tags are real objects with tagger, date, message and a signature slot. |
| Can you derive a version instead of guessing? | "We bump when it feels big." | MAJOR only for breaking; `feat` to MINOR, `fix` to PATCH, derived from the commits since the last tag — and say what "breaking" means for your surface. |
| Do you understand tag immutability? | "You can just move the tag." | Fetch will not overwrite an existing tag, so a moved tag means two commits under one name across machines. Cut the next version instead. |
| Do you connect tags to deploys? | "We deploy main." | Deploy by tag so the running version is nameable and rollback is one command, and stamp the build with `git describe`. |

**The killer follow-up:** *"Your deploy is broken and you must go back to the last good release right now. What do you type?"* — With tags: check out `erp-v1.0.0` and redeploy — one name, a verified commit, no guesswork. Without tags you are reading `git log` under pressure, hoping you pick the right hash. And the answer that really lands adds the sentence after: I know it was good because CI was green on that commit *before* it was tagged.

# Revision Notes
- Branch = **moving** ref. Tag = **fixed** ref. Same mechanism, opposite intent.
- `git cat-file -t <tag>` → `tag` = annotated, `commit` = lightweight. Real: `erp-v1.0.0` annotated, `kos-v1.0` lightweight.
- Annotated (`-a`) stores tagger, date, message and can be **signed**. Lightweight stores nothing.
- **MAJOR** = breaking · **MINOR** = new feature, compatible · **PATCH** = fix. `0.y.z` = no promises. `-rc.1` sorts before final; `+meta` is ignored in ordering.
- Bump map: `!`/`BREAKING CHANGE:` → MAJOR · `feat` → MINOR · `fix` → PATCH · docs/chore/test → nothing.
- ⚠️ **Never move or delete a published tag.** Fetch won't update it, so the name splits in two. Cut the next number.
- `git push` does **not** push tags → `git push origin <tag>` or `--follow-tags`.
- `git describe --tags` → `kos-v1.0-18-g42a2ecc4` = nearest ancestor tag + commits since + short hash (`g` = git).
- Real state: 22 commits since `erp-v1.0.0`, `feat` present, no `!` → next is **`erp-v1.1.0`** (MINOR).
- Undo: `git tag -d <name>` locally, `git push origin --delete <name>` remotely — the commit survives either way.

# Cheat Sheet
```bash
git tag -n1                                  # all tags + first line of message
git cat-file -t erp-v1.0.0                   # tag = annotated · commit = lightweight
git cat-file -p erp-v1.0.0                   # the tag object: object/tagger/date/message
git describe --tags                          # <nearest-tag>-<commits-since>-g<short-hash>
git describe --tags --match 'erp-v*'         # scope to one product's timeline
git rev-list --count erp-v1.0.0..HEAD        # how many commits since the release
git log --oneline erp-v1.0.0..HEAD           # exactly what is in the next release
git tag --points-at HEAD                     # is this commit already tagged?
git tag --contains erp-v1.0.0                # tags that come after this one
git tag -a erp-v1.1.0 -m "erp-v1.1.0 — <what + evidence>"   # CUT a release (annotated, always)
git push origin erp-v1.1.0                   # plain `git push` does NOT push tags
git push --follow-tags                       # push commits + their annotated tags
git tag -d erp-v1.1.0                        # UNDO locally (harmless)
git push origin --delete erp-v1.1.0          # UNDO on remote (coordination needed)
git switch -c fix/hotfix erp-v1.0.0          # work FROM a tag without detached HEAD
git tag -s / git tag -v                      # sign / verify (Ch 31)
```
- **Bump rules:** `!` or `BREAKING CHANGE:` → **MAJOR** · `feat` → **MINOR** · `fix` → **PATCH**.
- **Never:** `git tag -f` + `git push --force` on a published tag. Cut the next number.

# My ERP Section
| Concept | In this repo |
|---|---|
| Release tag | `erp-v1.0.0` — **annotated** (tag object `0cccb32b`) → commit `90c1f2f3`, tagged 2026-07-19 |
| Its message | "Manufacturing V1 production release anchor · GO WITH ACCEPTED RISKS · battery 1878/1878 · 8/8 dimensions certified" |
| Second product | `kos-v1.0` → `1e042648` — **lightweight** (predates the annotated-only rule; left alone, not moved) |
| Baseline marker | `pre-refactor-baseline` → `520923fb`, annotated, 2026-06-09: "305 tests green, ~103s" |
| Prefix convention | product-prefixed (`erp-v*`, `kos-v*`) because one monorepo ships several deliverables |
| Rule of record | `CONTRIBUTING.md` §7 — SemVer, annotated tags only, then update `CHANGELOG.md` and cut a GitHub Release |
| Current position | `git describe --tags` → `kos-v1.0-18-g42a2ecc4`; 22 commits since `erp-v1.0.0` |
| Next version | `erp-v1.1.0` — `feat:` present, no `!`, no `BREAKING CHANGE:` → MINOR |
| Only breaking commit | `e01f0c4b feat(production)!: V2-1d — drop the worker M2M` (dropping a table = MAJOR) |
| Commit-type census | 324 commits: 83 `docs` · 68 `feat` · 40 `fix` · 21 `refactor` · 6 `test` · 5 `chore` · 1 each `perf`/`ci`/`style`/`feat!` |
| Free-tier truth | server-side tag protection is paid on private repos → discipline + fork-based Read access instead |
| Downstream | `CHANGELOG.md` sections and compare links are keyed to these tags ([Ch 30](30_Changelog.md)) |

# Practice Tasks
1. **Prove the difference:** run `git cat-file -t` on all three tags and explain, from the output alone, which one cannot ever be signed.
2. **Read the record:** `git cat-file -p erp-v1.0.0`. List every field and say what question each one answers a year from now.
3. **Derive a version:** from `git log --pretty='%s' erp-v1.0.0..HEAD`, decide the next number and defend it in one sentence using only the bump rules.
4. **Decode:** explain `kos-v1.0-18-g42a2ecc4` word by word, then say why `erp-v1.0.0` is *not* the tag it names.
5. **Classify:** for each change, name the bump and the reason — (a) a new mobile report page, (b) renaming an env var the deploy reads, (c) fixing a settlement total, (d) dropping a model field, (e) rewording a template.

# Homework
- Write this project's **breaking-change definition** in five bullets (URLs, schema, commands, env, permissions) with one concrete ERP example each. Then re-classify `e01f0c4b` against your own list.
- Draft the exact `git tag -a erp-v1.1.0 -m "…"` message you would ship today, in the same shape as `erp-v1.0.0`'s — with today's real evidence (2,033 tests, 14 apps).
- Argue in writing whether `kos-v1.0` should be re-cut as annotated. Decide, and state what would break if you moved it.
- Add `git describe --tags --match 'erp-v*'` to your mental model of a deploy: where in the app would you surface it so an operator can read it, and what does a `-3-g…` suffix mean when they do?
- Read one real MAJOR release note from a dependency you pin (Django, psycopg2) and write down what *you* would have had to change. That is what a MAJOR is telling consumers of *your* code.

---

# Further Reading & Live Resources
- **Semantic Versioning 2.0.0** — the whole spec, short enough to read in ten minutes: https://semver.org/
- Pro Git — *Git Basics: Tagging* (annotated vs lightweight, pushing, deleting): https://git-scm.com/book/en/v2/Git-Basics-Tagging
- `git-tag` manual (every flag, including `-s` and `--points-at`): https://git-scm.com/docs/git-tag
- `git-describe` manual (`--match`, `--always`, `--first-parent`): https://git-scm.com/docs/git-describe
- Conventional Commits — the `!` and `BREAKING CHANGE:` rules that drive the bump: https://www.conventionalcommits.org/en/v1.0.0/
- GitHub Docs — *managing releases from tags* (and the auto-generated archives): https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository
- Django's own release policy — a real example of SemVer-ish promises and LTS windows: https://docs.djangoproject.com/en/dev/internals/release-process/
