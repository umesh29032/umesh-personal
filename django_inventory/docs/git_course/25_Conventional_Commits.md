---
id: git-course-25-conventional-commits
type: lesson
status: active
owner: handwritten
scope: git, version control — the commit-message grammar this repo enforces, and what the grammar buys
anchors: CONTRIBUTING.md, git-hooks/commit-msg, CHANGELOG.md, .github/workflows/ci.yml
verified: 2026-08-03
---

# 25 — Conventional Commits (a commit message with a grammar a machine can read)

> Part of [Git Course](00_COURSE_OVERVIEW.md). Prev: [24 — Branching Strategies](24_Branching_Strategies.md). Next: [26 — Pre-commit Hooks](26_Pre_Commit_Hooks.md).

# Learning Objectives
By the end of this chapter you can:
- name every part of a Conventional Commits message — `type`, `scope`, `!`, subject, body, footer
- explain its payoffs: a generated `CHANGELOG.md`, a derived [SemVer](29_Semantic_Versioning_And_Tags.md) bump, a searchable history
- write a body that answers **why** instead of restating the diff
- predict exactly which messages `git-hooks/commit-msg` rejects, and why
- recover a rejected message without retyping a word

# Purpose
A commit message is the only part of your work a future human reads *before* the code. The diff shows **what** changed; the message is the sole place the **why** can live. This chapter turns it from a free-text apology into a **structured record** that tools parse for releases and `git log --grep` finds three years later. It is enforced here by a real hook, so these are not tips — this is a gate.

# The Problem
Return to a repo after six months, hit a bug in settlement dates, run `git log --oneline`, and read: `fixed some date stuff` / `wip` / `more fixes` / `final fix`. You cannot tell which commit touched money, whether "final fix" added or reverted, or when the break landed.

Not hypothetical. Measured today over all **324** commits reachable from `HEAD`:

```bash
$ git log --pretty=%s | wc -l
324
$ git log --pretty=%s | grep -cE '^(feat|fix|docs|chore|refactor|test|perf|build|ci|style|revert)(\([a-z0-9_,./-]+\))?!?: .+'
229
```

**229** parse; **15** are `Merge …` messages git wrote itself; the other **80** the hook would refuse — `Input F-1 - Canonical --input-* tokens`, `Cards D-2a - Introduce .stat-card--serif`. And **154** subjects exceed 72 characters, the longest **212**. Those are the commits nobody can find.

# Theory (from zero)

### What a commit message *is*
A commit is an object in `.git` ([Ch 05](05_How_Git_Stores_Everything.md)). Print one raw:

```bash
$ git cat-file -p 42a2ecc4 | head -7
tree 9653375af0159933b1aca53bba034d660693db74
parent 83a144ba3fad222bdd3b85d7b5f67a7fb0604ed2
author umesh-personal <umesh29mar@gmail.com> 1785747733 +0530
committer umesh-personal <umesh29mar@gmail.com> 1785747733 +0530

chore(repo): stop tracking database dumps + node_modules; teach why in the course
```

`cat-file -p` = "pretty-print the object with this hash". **tree** = the file snapshot, **parent** = the previous commit, everything after the blank line is the message — **free text**. There is no "type" field; a type is a convention we *encode into the text* so tools read it back out. Git validates nothing.

The one rule git *does* enforce: the **blank line after line 1**. Git splits there — line 1 is the **subject** (`%s`, what `--oneline` prints), the rest is the **body** (`%b`).

### The grammar
[Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) is a tiny spec: put a machine-readable prefix on the subject.

```
<type>(<scope>)!: <subject>
                                   <- blank line, MANDATORY
<body — the WHY, wrapped at 72 chars>

<footer — BREAKING CHANGE:, Co-Authored-By:>
```

- **`type`** — eleven allowed: `feat` `fix` `docs` `chore` `refactor` `test` `perf` `build` `ci` `style` `revert`.
- **`scope`** — optional, the app or area. Real ones here: `production` (25 commits), `audit` (15), `soak` (13), `foundation` (13), `frontend` (12), `expense` (12), `ui` (10).
- **`!`** — optional, right before the colon: this **breaks** something a caller relied on.
- **`subject`** — short and **imperative**: "add", not "added". Read it as *"if applied, this commit will __add accountant read tier__"* — git's own convention, which is why `git revert` generates `Revert "feat: …"` and it still reads correctly.
- **`body`** = the why · **`footer`** = trailers (`BREAKING CHANGE:`, `Co-Authored-By:`).

Payoffs: a **`CHANGELOG.md` you do not hand-write** ([Ch 30](30_Changelog.md)); a **version that derives itself** (`fix:`→PATCH, `feat:`→MINOR, `!`→MAJOR — [Ch 29](29_Semantic_Versioning_And_Tags.md)); a **searchable history** (`git log --grep='^fix' -E` = **47** commits here); cheaper review and [bisect](35_Bisect.md), because `fix(production):` names the risk class before anyone opens the diff.

Subject rules, each with a reason: **imperative** (matches git's own messages); **≤ 72 chars** (`--oneline` spends 8 on the hash and GitHub truncates — a 212-char subject renders as an ellipsis); **no trailing period** (a headline, not a sentence; **0** in 324 here); **one intent** (needs "and" ⇒ two commits).

### The body: why, not what
The diff is the *what*, forever, for free. The *why* lives only in your head and evaporates in a week. The best commit here is `42a2ecc4`, which untracked two committed database dumps: its body states the fact, shows audit evidence, names the root cause (`django_inventory/.gitignore:114` ignored `db_backups/`, but a `.gitignore` only guards its own subtree and this is a monorepo) — then records a decision **not** taken:

```
History is deliberately NOT rewritten. With 0 forks, the repository going
private, and nothing usable inside, a git-filter-repo force-push is more risk
than the exposure warrants. Recorded here so the decision is explicit.
```

That paragraph is the highest-value text in the repo's history: it stops a future reader force-pushing a rewrite ([Ch 34](34_Rewriting_History.md)) without knowing the trade-off was weighed.

> 💡 **Samjho aise:** Commit message ek **dawai ki parchi** hai. `type` = kaunsi bimari thi (`fix`), `scope` = kis ang ka ilaaj hua (`production`), subject = kya diya, body = **kyun** diya. "Kuch theek kar diya" wali parchi kisi kaam ki nahi — na agla doctor samjhega, na aap. Aur parchi chhoti likho: 72 akshar se lambi to chemist bhi poori nahi padhta.

### The confusing bits, named
- **Spec vs tool.** *Conventional Commits* is a text format; `commitlint` is a Node tool that checks it; `semantic-release` publishes from it. This repo implements the spec in ~40 lines of bash.
- **`refactor` means behaviour is unchanged.** If behaviour moved at all it is `feat` or `fix` — mislabelling is how a behaviour change sails through review. Likewise `fix:` writes new code, while `revert:` undoes a named earlier commit ([Ch 15](15_Undo_Reset_Revert_Restore.md)).

# Real World Example (this repo)
The type histogram over all 324 commits — a report on the project, not just its prose:

```bash
$ git log --pretty=%s | sed -E 's/^([a-z]+)(\(.*\))?!?:.*/\1/' \
  | grep -E '^(feat|fix|docs|chore|refactor|test|perf)$' | sort | uniq -c | sort -rn
     95 docs
     72 feat
     40 fix
     23 refactor
      7 test
      5 chore
      3 perf
```

`docs` outnumbering `feat` is exactly what `CLAUDE.md` rule 12 (code change ⇒ docs change, same session) is meant to produce. `test` at 7 looks low until you know tests usually ship *inside* the `feat` commit that needs them.

The honest footnote: the newest commit `42a2ecc4` has an **81-character** subject, so the hook now guarding this repo would **reject the repo's own best commit message**. The rule arrived after the commit — a gate protects the future, not the past.

# Visual Diagram
```
  SUBJECT  (git %s — what --oneline prints · <=72 chars · no trailing period)
  +------+---------+-+-+---------------------------+
  | feat |(expense)|!|:| add accountant read tier  |
  +--+---+----+----++--+------------+--------------+
     |        |     |               +- imperative: "add", not "added"
     |        |     +- "!" = BREAKING -> MAJOR bump
     |        +- optional scope -> filtering in git log
     +- type (11 allowed)  feat -> MINOR  fix -> PATCH

  <blank line>  <- MANDATORY, else the body joins the subject
  BODY (%b)     fact -> evidence -> root cause -> decisions NOT taken
  FOOTER        BREAKING CHANGE: <what broke> / Co-Authored-By: <name>

  parses ->  CHANGELOG.md  |  SemVer bump  |  git log --grep
```

# Practical — write one, and test it before you commit
The hook is a script taking a **file path**, so you can rehearse with zero risk to the repo:

```bash
cd /home/tech/umesh-personal
printf 'fixed some date stuff\n' > /tmp/msg.txt
bash git-hooks/commit-msg /tmp/msg.txt ; echo "exit=$?"
```

Real output (trimmed):

```
✖ Commit message is not in Conventional Commits format.
  Got:      fixed some date stuff
  Expected: <type>(<scope>): <subject>
  Your message was NOT lost — fix it with:  git commit --edit --file=.git/COMMIT_EDITMSG
exit=1
```

Four more cases, each run the same way:

| Message in `/tmp/msg.txt` | Hook verdict |
|---|---|
| `fix(production): correct settlement entry_date to IST` | `exit=0` — silence means pass |
| `fix(production): correct settlement entry_date to IST.` | `exit=1` — must not end with a period |
| `Merge pull request #15 from umesh29032/new_flask_app` | `exit=0` — git's own messages pass through |
| `feat(api)!: drop the v1 endpoint` | `exit=0` — `!` marks a breaking change |

**The undo you will actually need** — a rejected commit does not lose your text:

```bash
git commit --edit --file=.git/COMMIT_EDITMSG    ## reopen the exact draft
git commit --amend                              ## rewrite the last message
git commit --no-verify -m "wip"                 ## deliberate bypass (Ch 26)
```

`--amend` **replaces** the last commit with a new object (new hash). Safe while local; once pushed you need `git push --force-with-lease` ([Ch 34](34_Rewriting_History.md)) — never on a shared branch.

# Production Walkthrough
1. **Branch by intent** — `git switch -c fix/utc-date-in-settlement`; prefix and commit type agree by construction ([Ch 24](24_Branching_Strategies.md)).
2. **Commit small typed steps** — `fix(expense): derive entry_date via timezone.localdate`, then `test(expense): pin IST bucketing on the settlement path`. The hook checks each as you go.
3. **The body carries reasoning.** For the real UTC/IST money bug it recorded *why both sides of a date bucket must move together* — a half-fixed date basis is worse than an unfixed one.
4. **Push, open a PR** ([Ch 21](21_Pull_Requests.md)); CI then runs lint, `makemigrations --check`, the **2033-test** battery and `knowledge_sync` at BLOCKER=0 ([Ch 28](28_CI_With_GitHub_Actions.md)).
5. **Squash-merge — the trap:** the commit GitHub creates takes its subject from the **PR title**, not your commits. A non-Conventional title lands a non-Conventional commit on `main` even though every local commit was clean, because the hook runs on your machine and the merge button does not. **Title PRs the way you would title the commit.**
6. **Release** — `git tag -a erp-v1.1.0`; the bump is read off the types since the last tag.

# Debugging Guide
| Symptom | Cause | Fix |
|---|---|---|
| Rejects a message that looks right | Type not in the eleven (`feature:`, `Feat:`), or a space before the colon | Lowercase type from the list, colon, then **one** space |
| Rejected and you fear the text is gone | Nothing is lost; git preserved the draft | `git commit --edit --file=.git/COMMIT_EDITMSG` |
| "Subject line is 108 chars (max 72)" | Whole change described in the subject | Move detail to the body — the body has no limit |
| `main` has a non-conventional commit though local commits were clean | Squash-merge used the **PR title** | Title PRs in Conventional format; check `git log --oneline main -5` |
| Hook never fires | `.git/hooks/commit-msg` missing — hooks are not cloned | `bash git-hooks/install.sh` ([Ch 26](26_Pre_Commit_Hooks.md)) |

# Performance Notes
- `git log --grep` is a **linear scan of messages**, not an index. Here — 324 commits, `.git` at 97 MB, **25975** in-pack objects (`git count-objects -vH`) — it returns instantly. At 100k commits it is still seconds: messages are tiny next to trees.
- **`--grep` searches messages; `-S`/`-G` (the *pickaxe*) searches diff content** and must reconstruct every diff — orders of magnitude slower. Narrow first: `git log --grep='^fix' -E --since=2026-06-01 -- django_inventory/config/expense/`.
- The hook costs milliseconds (one `grep -qE`). A hook slow enough to notice gets bypassed ([Ch 26](26_Pre_Commit_Hooks.md)).

# Security Considerations
- **A message is permanent and effectively public** — copied into every clone and fork, GitHub's API, and notification emails. Removing one means rewriting history and force-pushing ([Ch 34](34_Rewriting_History.md)), the same surgery as removing a leaked file ([Ch 33](33_Secrets_And_Leaks.md)).
- **Never paste a secret into a message.** "It is revoked" is no defence: the message still exposes your naming scheme and infrastructure. And do not name a live vulnerability before the fix ships — in a public repo that is a disclosure with a timestamp.
- **Describe an incident without reproducing it.** `42a2ecc4` states that two dumps were tracked and summarises the audit (`socialaccount_socialapp` **empty**, so no OAuth secret; **2** password hashes at `pbkdf2_sha256$1000000$…`; 2 expired sessions) while pasting **no row of data**. The reader learns severity; nobody learns a credential.

# Architecture Decisions
- **Conventional Commits, not free-form** — the project needs a generated `CHANGELOG.md` and a defensible bump for tags like `erp-v1.0.0` (= `90c1f2f3`). A convention nobody checks is a suggestion.
- **~40 lines of bash, not `commitlint`** — that tool means Node, `package.json` and a `node_modules` tree at the monorepo root, in a repo that just untracked **2,952** `node_modules` files. Rejected `gitmoji` too (unsearchable) and ticket prefixes (no issue tracker — `CONTRIBUTING.md` §3).
- **`Merge `/`Revert `/`fixup!`/`squash!`/`amend!` pass through** — git generates these; a hook blocking git's own messages breaks `merge` and interactive rebase ([Ch 14](14_Interactive_Rebase.md)), the fastest route to an uninstalled hook.
- **72-char cap as an error, not a warning** — a warning that never blocks is decoration; `--no-verify` is the escape hatch and typing it is the point.
- **Deliberately NOT done:** no server-side message check (paid on private repos, [Ch 27](27_Pre_Push_Protection.md)) and **no rewrite of the 80 legacy subjects** — the exact risk `42a2ecc4` declined.

# Best Practices
- Write the subject *before* the code. If it will not fit in 72 chars, the change is too big.
- Answer **why** in the body, and record what you decided *not* to do.
- One intent per commit; split a mixed working tree with `git add -p` ([Ch 03](03_The_Three_Trees.md)).
- Title PRs in Conventional format — squash-merge takes the title, not your commits.
- Rehearse an uncertain message through the hook on a scratch file; wrap the body at 72 columns.

# Beginner Mistakes
- **`git commit -m "fix"`** → a type with no subject; the hook needs `<type>: <something>`. Write `fix(expense): correct IST bucketing on settlement entry_date`.
- **No blank line after the subject** → git treats everything as one subject, `--oneline` becomes soup and `%b` is empty. Use `git commit` with an editor, not stacked `-m` flags.
- **Past tense — `feat: added the roster picker`** → breaks the "if applied, this commit will…" reading. Imperative: `add`.
- **Restating the diff — `fix: changed line 438 in adda_settlement_service.py`** → the diff already says that; the *why* is lost.
- **Panicking when the hook rejects** → the draft is safe: `git commit --edit --file=.git/COMMIT_EDITMSG`.
- **Habitual `--no-verify`** → the gate becomes decoration and the CHANGELOG silently rots. Bypass only in a real emergency, and say so in the body.
- **`refactor:` on a behaviour change** → reviewers skim it as risk-free and the version bump comes out wrong.
- **Assuming clean local commits mean a clean `main`** → squash-merge uses the PR title. Verify with `git log --oneline main -5`.

# Interview Questions
- **Junior:** "What is a Conventional Commit?" — A message with a machine-readable prefix: `type(scope)!: subject`, blank line, body explaining why, optional footers. The type comes from a fixed list (`feat`, `fix`, `docs`, `chore`, `refactor`, `test`, `perf`, `build`, `ci`, `style`, `revert`), the scope is the app or area, `!` marks a breaking change. It matters because the subject is what `git log --oneline` shows — the searchable index of the project's history.

- **Mid:** "What does the format buy you? Why not just write good prose?" — Three things prose cannot: a `CHANGELOG.md` grouped automatically from types instead of hand-maintained; a SemVer bump derived mechanically (`fix`→PATCH, `feat`→MINOR, `BREAKING CHANGE`→MAJOR) so the release number is not a judgement call; and a queryable history — `git log --grep='^fix' -E` gives me the 47 fixes in this repo instantly, and a scope answers "what changed in payroll?" in one line.

- **Senior:** "How do you enforce it, and what did you deliberately not do?" — A `commit-msg` hook: git passes the message file as `$1`, the hook greps the first non-comment line against `^(feat|fix|…)(\([a-z0-9_,./-]+\))?!?: .+`, then checks length ≤ 72 and no trailing period; a non-zero exit aborts the commit and git preserves the draft in `.git/COMMIT_EDITMSG`. `Merge `/`Revert `/`fixup!` pass through — blocking git's own generated messages breaks merges and interactive rebase and gets the hook uninstalled. I did *not* add `commitlint` (Node, in a repo that just untracked 2,952 `node_modules` files) and did not rewrite the 80 legacy subjects (risk with zero behaviour gain). The gap is honest: hooks are client-side, and squash-merge commits the **PR title**.

- **Staff:** "Commit conventions are famously ignored in practice. How do you make one stick, and how do you know it is working?" — Treat it as a system. **Make the happy path cheapest:** a hook that fails in milliseconds printing the exact recovery command, and a PR template mirroring the body so nobody writes the reasoning twice. **Close the gap where it leaks** — the PR title, because that is what squash-merge commits; linting the title in CI costs seconds and covers contributors who never installed a hook. **Keep the escape hatch and watch it:** `--no-verify` must exist for incidents, so measure its use rather than pretend it away. **Measure outcome, not compliance:** not "percent of subjects that parse" but "can we ship release notes with no human editing?" Here that is 229/324, because the convention arrived late. **Never retro-rewrite to make the number pretty** — force-pushes and broken clones for zero behaviour change. Finally, **attach it to something people already want:** the types drive the tag and the CHANGELOG, so following the format is how you get a release, not paperwork.

### Why interviewers ask these — and the answer that separates levels

| Testing for | Weak answer | What lands |
|---|---|---|
| *Why* the format exists, or only the syntax? | "It is the standard, `feat:` and `fix:`." | The three payoffs — generated CHANGELOG, derived SemVer bump, searchable history — plus the query you run. |
| Where enforcement really leaks | "A hook stops bad messages." | Hooks are client-side and never cloned; squash-merge commits the **PR title**, so the gate must also live in review or CI. |
| Can you write a body, not just a subject? | "The subject says what changed." | The body carries the **why**, the evidence, and the options *rejected* — the part no reader can reconstruct from the diff. |
| Judgement about legacy history | "I would rewrite the old messages to match." | Rewriting for cosmetics means a force-push and broken clones for zero gain; gate the future, document the past. |

**The killer follow-up:** *"Every local commit was perfect and `main` still got `Update stuff` — how?"* — Squash-merge used the PR title and the hook never ran on GitHub's servers. Anyone who has shipped with this workflow answers instantly; anyone who memorised the spec goes quiet.

# Revision Notes
- Shape: `type(scope)!: subject` → **blank line** → body (why) → footer. The blank line is the only part git itself cares about.
- Eleven types; `feat`→MINOR, `fix`→PATCH, `!`→MAJOR. Subject: imperative, **≤72 chars**, no trailing period, one intent.
- The body answers **why**, plus the decisions *rejected*. A rejected draft is never lost: `git commit --edit --file=.git/COMMIT_EDITMSG`.
- ⚠️ **Squash-merge commits the PR title**, not your commits.
- This repo: 324 commits · **229** parse · **80** rejected · **154** over 72 chars (longest **212**) · **0** trailing periods.

# Cheat Sheet
- **Shape:** `<type>(<scope>)!: <subject>` · blank line · body (why) · blank line · footer
- **Types:** `feat` `fix` `docs` `chore` `refactor` `test` `perf` `build` `ci` `style` `revert`
- **Bumps:** `fix:`→PATCH · `feat:`→MINOR · `!` or `BREAKING CHANGE:`→MAJOR
- **Write it:** `git commit` (editor, so you get a body) — not a pile of `-m` flags
- **Fix a rejected draft:** `git commit --edit --file=.git/COMMIT_EDITMSG`
- **Fix the last message:** `git commit --amend` (pushed ⇒ `--force-with-lease`, own branch only)
- **Search:** `git log --grep='^feat(expense)' -E` · `git log --oneline --grep='^fix' -E | wc -l`
- **Rehearse:** `printf 'feat(x): y\n' > /tmp/m.txt && bash git-hooks/commit-msg /tmp/m.txt`
- **Inspect raw:** `git cat-file -p <sha> | head -7`

# My ERP Section
| Concept | In this repo |
|---|---|
| Rulebook | `CONTRIBUTING.md` §4 — Conventional Commits, enforced |
| Enforcer | `git-hooks/commit-msg` — regex + ≤72 chars + no trailing period |
| Installer | `git-hooks/install.sh` (hooks are never cloned — [Ch 26](26_Pre_Commit_Hooks.md)) |
| Real scopes | `production` 25 · `audit` 15 · `soak` 13 · `foundation` 13 · `expense` 12 · `ui` 10 |
| Pass-through | `Merge ` · `Revert ` · `fixup! ` · `squash! ` · `amend! ` |
| History | 324 commits · 229 parse · 15 merges · 80 rejected · 154 over 72 chars |
| Gold-standard body | `42a2ecc4` — fact → evidence → root cause → decision *not* taken |
| Feeds | `CHANGELOG.md` ([Ch 30](30_Changelog.md)) · tag `erp-v1.0.0` = `90c1f2f3` |
| Known gap | squash-merge uses the PR title; the hook is client-side only |

# Practice Tasks
1. **Read:** open `git-hooks/commit-msg` and find its three checks. Which rejects `Feat: add thing`, and which rejects `feat: add thing.`?
2. **Rehearse:** write five messages to `/tmp/msg.txt` — bad type, no subject, 80 chars, trailing period, valid — and run the hook on each. Predict the exit code first.
3. **Query:** find every `fix` commit that touched the `expense` app with one `git log` using `--grep` and a pathspec.
4. **Rewrite:** list three of the 80 non-conventional subjects and write what each *should* have said. Change nothing.
5. **Body drill:** read `git log -1 --format=%B 42a2ecc4` and name the four things the body does, in order.

# Homework
- Draft your next real commit here: subject plus a body giving fact, evidence, root cause, and anything you decided *not* to do. Run it through the hook first.
- Take the longest subject in the repo and split it into the two or three commits it should have been.
- Build a CHANGELOG fragment by hand from the last 20 commits, grouped by type. Which could you not classify, and why?
- Argue both sides: should this repo rewrite its 80 legacy subjects? Then read the last paragraph of `42a2ecc4`'s body and see whether you agree with the decision already recorded.
- Design the cheapest check for the one real gap — a non-conventional **PR title** ([Ch 28](28_CI_With_GitHub_Actions.md)).

---

# Further Reading & Live Resources
- Conventional Commits v1.0.0 — *the spec itself, readable in ten minutes*: https://www.conventionalcommits.org/en/v1.0.0/
- `git commit` docs — *subject, body, and the mandatory blank line*: https://git-scm.com/docs/git-commit#_discussion
- `git log` docs — *`--grep`, the `-S`/`-G` pickaxe, `--pretty` placeholders*: https://git-scm.com/docs/git-log
- "How to Write a Git Commit Message" (Chris Beams) — *the classic seven rules*: https://cbea.ms/git-commit/
- Semantic Versioning 2.0.0 — *what the types are bumping*: https://semver.org
