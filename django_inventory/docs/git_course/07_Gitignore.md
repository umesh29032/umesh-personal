---
id: git-course-07-gitignore
type: lesson
status: active
owner: handwritten
scope: git, version control — which files git must pretend not to see, and why prevention beats surgery
anchors: .gitignore, django_inventory/.gitignore, Django_app/myproject/mydb_backup_20250618.sql, CONTRIBUTING.md
verified: 2026-08-03
---

# 07 — .gitignore (the list of files git must pretend not to see)

> Part of [Git Course](00_COURSE_OVERVIEW.md). Prev: [06 — The Commit Graph](06_The_Commit_Graph.md). Next: [08 — Reading History](08_Reading_History.md).

# Learning Objectives
By the end of this chapter you can:
- explain git's **three file states** (tracked / untracked / ignored) and say which one `.gitignore` actually controls
- write patterns correctly — `*.sql`, `dir/`, `/anchored`, `**/`, `!negation` — and predict which one wins
- prove *which line of which file* is ignoring a path, using `git check-ignore -v`
- untrack an already-committed file without deleting it from disk, and say why that does **not** clean history
- place ignore rules correctly in a **monorepo**, where a subtree `.gitignore` guards only its own subtree

# Purpose
`.gitignore` is the cheapest security control in this repository and the one most often written wrong. It exists so data, secrets, dependencies and build junk never enter history — because git history is **append-only**, and a file committed once stays readable in that commit forever. This chapter teaches the pattern language exactly, then walks the **real incident** here where a correct rule was written in the wrong place and two database dumps sat in public history for a year.

# The Problem
You run `git status` and 2,900 lines of `node_modules/` noise bury your two real changes. So you type `git add .` to make it go away — and now your commit contains a dependency tree, a `.env` with the database password, and a `pg_dump` full of worker salaries and password hashes.

Then it gets worse. You notice, you `git rm` the file, you commit *"remove secret"* — and the secret is **still there**, fully readable, in the earlier commit. Git never forgets. Deleting a file going forward is not the same as it never having existed. The only cheap moment to stop this is *before the first `git add`*, and `.gitignore` is that moment.

# Theory (from zero)

### The three states a file can be in
| State | Meaning | In `git status` |
|---|---|---|
| **Tracked** | in the index/history; git watches it for changes | ` M path`, or silence if unchanged |
| **Untracked** | git sees the file but was never told to care | `?? path` |
| **Ignored** | git was told to stay quiet about it | nothing (`!! path` with `--ignored`) |

**The most important sentence in this chapter: `.gitignore` only affects UNTRACKED files.** Once a file is tracked, git keeps tracking it and the ignore rules are never consulted for it. Adding `*.sql` does *nothing* to a `.sql` you already committed. That single rule causes about half of all "why is git still showing my file?" confusion — and it is the exact shape of the incident below.

### What the file actually is
Plain text, one **pattern** per line. Blank lines skipped, `#` starts a comment. No header, no schema. Comments must be on their **own line** — git does *not* strip a trailing `#`-comment, so `*.sql   # dumps` becomes a pattern containing all that text and matches nothing. That is the first real bug most people write.

### The pattern language, term by term
Git uses **glob** patterns (shell-style wildcards) plus rules of its own.

| Pattern | Matches | Note |
|---|---|---|
| `*.sql` | any name ending `.sql`, **at any depth** | `*` never crosses a `/` |
| `db_backups/` | a **directory** of that name at any depth, and all contents | trailing `/` = "directory only" |
| `/node_modules` | that name **only beside this `.gitignore`** | a leading `/` anchors |
| `docs/*.pdf` | pdfs directly in `docs/`, not `docs/sub/` | a `/` anywhere but the end also anchors |
| `**/vendor/` | `vendor` at any depth, explicitly | `**` *does* cross `/` |
| `?` / `[0-9]` | one character / one char from a set | `file?.txt` |
| `!keep.sql` | **un-ignore** — a negation | has a trap, see below |

Three non-obvious rules:

1. **Last matching pattern wins.** `*.sql` then `!schema.sql` keeps `schema.sql`; swap the lines and it is ignored again.
2. **A negation cannot rescue a file inside an excluded directory.** Ignore `logs/` and git stops *descending into it*, so `!logs/keep.log` is never evaluated. Ignore the contents instead: `logs/*` then `!logs/keep.log`.
3. **Deeper `.gitignore` beats shallower.** Rules are gathered root-downwards, so `sub/.gitignore` is applied after — and therefore wins over — the root file.

### The three places ignore rules live
| Where | Committed? | Use for |
|---|---|---|
| `.gitignore` in any directory | **yes**, shared with every clone | project dangers: dumps, `.env`, deps, build output |
| `.git/info/exclude` | no — this clone only | *your* scratch files (`scratch.py`, `notes.txt`) |
| `core.excludesFile` (`~/.config/git/ignore`) | no — this machine | editor/OS junk: `.DS_Store`, `.idea/`, `*.swp` |

**House rule:** editor/OS junk goes in your *global* ignore — your editor is not the project's business. Project-wide dangers go in the committed `.gitignore`, so every clone is protected.

`git check-ignore -v <path>` prints **which file, which line, which pattern** decided; nothing printed (exit 1) means not ignored. That is the difference between guessing and knowing.

> 💡 **Samjho aise:** `.gitignore` woh list hai jo aap kaamwali bai ko dete ho — *"in cheezon ko chhoona hi nahi."* Par ek pakka niyam hai: jo cheez pehle se almari mein rakh di gayi hai (tracked), list mein naam likhne se woh apne aap bahar nahi aayegi — usse **haath se nikaalna** padega (`git rm --cached`). Aur bahut zaroori: purani photo (history) mein woh cheez ab bhi dikhegi. Isliye asli ilaaj **pehle se rok dena** hai, baad ki safai nahi.

### Untracking something already committed
```bash
git rm -r --cached --dry-run <dir>  # preview only, changes nothing — do this FIRST
git rm --cached path/to/file        # git forgets it; the file STAYS on disk
```
`--cached` is the whole point: **git stops tracking, the disk keeps the bytes.** Without it, `git rm` deletes the file from disk too.

**Undo:** not committed yet → `git reset` (tracked again, unchanged). Already committed → `git revert <commit>` re-adds it. Nothing is lost either way.

**What it does NOT do:** remove the file from *earlier* commits. Anyone can still run `git show <old-commit>:path`. Really erasing it means rewriting history ([Ch 34](34_Rewriting_History.md)) — and if the secret reached a remote, the real fix is to **rotate** it ([Ch 33](33_Secrets_And_Leaks.md)).

### What to ignore — and what to never ignore
**Ignore:** secrets (`.env`, `*.pem`) · data (`*.sql`, `*.dump`, `db_backups/`, media) · dependencies (`node_modules/`, `env/`) · build output (`staticfiles/`, `__pycache__/`) · caches (`.ruff_cache/`, `.coverage`).

**Never ignore:** lockfiles (`requirements.txt`, `package-lock.json` — the reproducibility contract) · Django **migrations** (code, and the schema's history) · `.env.example` (documents the variables without the values) · CI config.

# Real World Example (this repo) — the dump that sat in public history

`django_inventory/.gitignore` line **114** has ignored `db_backups/` for a long time — which is exactly why the live ERP has **never** leaked a dump. But a `.gitignore` guards only its **own subtree**, and `/home/tech/umesh-personal` is a monorepo with siblings (`Django_app/`, `DSA/`). Two `pg_dump` files from the old practice app sat *outside* that protection, tracked, while the repo was **public**:

```
Django_app/myproject/mydb_backup_20250618.sql
Django_app/myproject/mydb_backup_20250620.sql
```

**Audited before acting** — the right order: `socialaccount_socialapp` **empty** → no OAuth secret; `socialaccount_socialtoken` **empty**; no plaintext passwords; **2** hashes at `pbkdf2_sha256$1000000$…` (1,000,000 iterations — impractical to crack); the primary account row was `!OUUm8Nk…`, Django's *unusable-password* marker (Google-login only); 2 `django_session` rows from June 2025, long expired. **Verdict: mild** — but data has no business in a code repo.

**The fix was prevention, not surgery.** A monorepo-**root** `.gitignore` now blocks `*.sql`, `*.dump`, `*.sql.gz`, `db_backups/`, `backups/`, `node_modules/` everywhere. Verified at five locations — and the attribution proves the precedence rule above:

```
$ for p in x.sql django_inventory/x.sql django_inventory/config/x.sql Django_app/x.sql DSA/x.sql; do git check-ignore -v "$p"; done
.gitignore:14:*.sql	x.sql
django_inventory/.gitignore:115:*.sql	django_inventory/x.sql
django_inventory/.gitignore:115:*.sql	django_inventory/config/x.sql
.gitignore:14:*.sql	Django_app/x.sql
.gitignore:14:*.sql	DSA/x.sql
```

Inside `django_inventory/` the **deeper** file wins the attribution; outside it, the root rule catches everything. Then the untracking, commit **`42a2ecc4`**:

```
$ git show --shortstat --oneline 42a2ecc4
42a2ecc4 chore(repo): stop tracking database dumps + node_modules; teach why in the course
 2956 files changed, 81 insertions(+), 331748 deletions(-)

$ git ls-files -i -c --exclude-standard
  (no output — nothing tracked-but-ignored remains)
```

**2,954** files untracked with `git rm --cached` (2 dumps + 2,952 `node_modules` entries); plus the new `.gitignore` and one course file = 2,956. **331,748 deletions** in the diff and **zero** bytes gone from disk — verified byte-identical, because `--cached` touches only the index. The empty second command is what "done" looks like.

**History was deliberately NOT rewritten.** With 0 forks, the repo going private, and nothing usable inside, a `git-filter-repo` force-push landing right after a merge was judged **more risk than the exposure** — reasoning written into the commit message so the decision stays explicit.

# Visual Diagram
```
   Named in .gitignore?                 Already in the index?
        | NO                                  | YES  ->  TRACKED
        v                                     v   .gitignore has NO effect
   UNTRACKED  (?? in status)             fix: git rm --cached  (disk keeps file)
        | YES
        v
   IGNORED  (!! with --ignored)  ->  git silent; git add refuses; add -f overrides

   RESOLUTION ORDER  (last match wins, deeper file wins)
     ~/.config/git/ignore ............... global, per machine, not shared
       -> /.gitignore ................... monorepo root, broadest
            -> django_inventory/.gitignore ... guards ONLY this subtree
     .git/info/exclude .................. this clone only, never committed

   THE LEAK THAT HAPPENED HERE
     django_inventory/.gitignore:114  db_backups/      OK   ERP protected
     Django_app/myproject/*.sql       (no rule above)  LEAK tracked, public
     ROOT .gitignore:14  *.sql                         OK   covers every sibling
```

# Practical — prove it on this repo (all read-only)
```bash
cd /home/tech/umesh-personal

git check-ignore -v Django_app/myproject/mydb_backup_20250618.sql
  # -> .gitignore:14:*.sql	Django_app/myproject/mydb_backup_20250618.sql
git check-ignore -v django_inventory/db_backups/x.dump
  # -> django_inventory/.gitignore:114:db_backups/	django_inventory/db_backups/x.dump
git check-ignore -v README.md ; echo "exit=$?"
  # -> (nothing) exit=1   i.e. NOT ignored

git status --ignored --short | grep -c '^!!'   # -> 108 ignored entries here
git ls-files -i -c --exclude-standard          # -> empty = no tracked-but-ignored drift
git ls-files | wc -l                           # -> 2407 files actually tracked
```
```bash
git rm -r --cached --dry-run node_modules/   # ALWAYS dry-run first; changes nothing
  #   git rm -r --cached node_modules/       (index only, disk untouched)
  #   UNDO before commit: git reset     UNDO after commit: git revert <commit>
git add -f docs/schema_view.sql              # deliberate override; the -f IS the audit trail
```

# Production Walkthrough
1. **Notice the noise or the risk** — `git status` shows a `.sql`, or `git status --ignored` reveals something suspiciously *not* listed.
2. **Audit before acting.** Real worker data, or an empty table? Ten minutes of looking downgraded the dump incident from panic to "mild" — and that verdict is what justified *not* rewriting history.
3. **Write the rule at the right scope** — data/secret rules at the monorepo **root**; framework noise (`staticfiles/`) in the app folder.
4. **Prove it** with `git check-ignore -v` at several depths. Do not trust the pattern; make git name the line.
5. **Untrack what slipped in** — `git rm -r --cached`, dry-run first — then `git ls-files -i -c --exclude-standard` to prove closure.
6. **Explain it in the commit body**: root cause, what was audited, what you chose *not* to do. Conventional Commits, `chore(repo):` scope (`CONTRIBUTING.md` §4). Then branch → PR → CI → squash-merge (§5), docs in the **same** PR (`CLAUDE.md` rule 12).

# Debugging Guide
| Symptom | Cause | Fix |
|---|---|---|
| Added to `.gitignore`, still shown by `git status` | It is **tracked**; rules apply only to untracked paths | `git rm --cached <path>`, then commit |
| `git add` says "ignored by one of your .gitignore files" | Working as designed | `git add -f <path>` if you genuinely mean it |
| `check-ignore -v` prints nothing | Nothing matches — your pattern is wrong | `*` does not cross `/`; directories need a trailing `/` |
| `!keep.log` has no effect | Parent directory excluded, git never descends | `logs/*` then `!logs/keep.log` |
| Works in one folder, not another | A subtree `.gitignore` guards only its subtree | Move the rule to the repo root |
| Pattern with a trailing comment matches nothing | Git does not strip trailing `#` comments | Comment on its own line |
| Secret "removed" but still in history | History is append-only | Rotate it ([Ch 33](33_Secrets_And_Leaks.md)); rewrite only if justified ([Ch 34](34_Rewriting_History.md)) |
| CI fails on a file that exists locally | It is ignored, so it was never committed | Commit with `-f`, or generate it in CI |

# Performance Notes
- `git status` walks the working tree and compares it to the index. Ignoring a big directory lets git prune the whole subtree instead of stat-ing every file: here, with `node_modules/` ignored, `git status --short` runs in **0.025 s** over 2,407 tracked files. The avoided cost is real — `Django_app/myproject/node_modules` holds **2,904** files on disk, each of which would otherwise be hashed on every `status`, `add` and `checkout`.
- **Committed junk is permanent weight.** Untracking shrinks *future* clones, not past ones: `.git` here is **97 MB** (25,975 objects in-pack, 63.66 MiB of packs) and those blobs stay until history is rewritten. Ignoring on day one is the only cheap version.
- Huge repos can enable `core.untrackedCache` / `core.fsmonitor` to make `status` incremental. At 25 ms this repo needs neither — prefer anchored patterns (`/build/`) for clarity, not speed.

# Security Considerations
- **A `.sql` dump is plaintext**, so committing one publishes *every row*: emails, password hashes, session keys, any OAuth secret in `socialaccount_socialapp`. What a dump contains: [deployment course Ch 28](../deployment_course/28_Backups.md).
- **History is append-only.** A later `git rm` leaves the file fully readable in earlier commits — `git rm --cached` is hygiene, **not remediation**.
- **If a secret reached a remote, treat it as compromised.** Rewriting history does not un-clone it, un-cache it from an API, or un-scrape it from a bot. Rotate first, clean second. And a public repo is a public backup: these dumps were exposed precisely *because* the repo was public.
- **Ignore `.env` before it exists**; commit `.env.example` (names, no values). Ignoring is not encrypting — that file is still plaintext on disk and in every disk backup.
- **Audit for drift** with `git ls-files -i -c --exclude-standard` after every ignore change. Empty output is the pass condition.

# Architecture Decisions
- **Data rules live at the monorepo root**, blocking `*.sql`, `*.dump`, `*.sql.gz`, `db_backups/`, `backups/`, `node_modules/` for every sibling. *Rejected:* one rule per subfolder — precisely the mistake that let `Django_app/` leak while `django_inventory/` was safe.
- **Keep the deeper `django_inventory/.gitignore` too.** Framework noise (`staticfiles/`, `poc/patterns_ai/vendor/`) is the app's own business, and duplicate coverage of the dangerous patterns is deliberate belt-and-braces.
- **Keep `git add -f` working.** *Rejected:* a hook that hard-blocks all `.sql`. Pattern-plus-`-f` makes committing SQL a typed decision; an absolute block gets bypassed with `--no-verify` and teaches nothing.
- **History deliberately NOT rewritten** — 0 forks, repo going private, contents audited harmless, force-push landing right after a merge. The cleanup's risk exceeded the exposure's, and the decision is recorded in `42a2ecc4` so a future reader does not rediscover the dumps and panic.
- **Lockfiles and migrations are never ignored** — they are the reproducibility and schema contracts.

# Best Practices
- Write `.gitignore` **before** the first `git add`, especially for `.env` and any dump directory.
- Put data/secret rules at the **repo root** in a monorepo; app-specific noise in the app folder.
- Prove every new rule with `git check-ignore -v` at two or three depths.
- Dry-run every `git rm --cached` and read the list before committing.
- Keep editor/OS junk in your **global** ignore, not the project's file.
- Run `git ls-files -i -c --exclude-standard` after ignore changes; empty means clean.
- Comment *why* each dangerous rule exists — uncommented rules get deleted by a future you.
- Treat any secret that ever hit a remote as compromised: rotate first, clean second.

# Beginner Mistakes
- **Adding a rule and expecting a tracked file to vanish** → rules apply only to untracked paths, so nothing happens. `git rm --cached <path>`, then commit.
- **`git rm` without `--cached`** → deletes the file from your **disk**, not just the index. Use `--cached`, dry-run first.
- **Thinking `git rm` erases a secret from history** → it stays readable in every earlier commit. Rotate the secret ([Ch 33](33_Secrets_And_Leaks.md)); rewrite history only if justified.
- **Writing the rule in a subfolder of a monorepo** → siblings stay unprotected. This exact mistake put two `pg_dump` files in this repo's public history.
- **`!exception` inside an ignored directory** → never evaluated; git stopped descending. Ignore `dir/*`, then negate the file.
- **A trailing comment on a pattern line** → the comment becomes part of the pattern and nothing matches. Own line only.
- **`git add .` to silence the noise** → that is how `.env`, dumps and `node_modules` get committed. Fix the ignore file, not the symptom.
- **Ignoring `migrations/` "because they're generated"** → they are code and the schema's history. Never ignore them.
- **Assuming ignored means safe** → an ignored `.env` is still plaintext on disk and inside every disk backup.
- **Never running `git status --ignored`** → you lose all visibility into what is hidden, including a file you actually needed committed.

# Interview Questions
- **Junior:** "What does `.gitignore` do?" — It lists patterns for files git should not track, so they stay out of `git status` and `git add` refuses them. Key limit: it applies only to **untracked** files, so anything already committed keeps being tracked until you `git rm --cached` it. Typical entries: secrets (`.env`), data (`*.sql`), dependencies (`node_modules/`), build output.

- **Mid:** "A password file is in `.gitignore` but git still tracks it. Why, and how do you fix it?" — It was committed before the rule existed, and ignore rules are only consulted for untracked paths. Fix: `git rm --cached path` (index only, disk keeps the file), commit, confirm with `git check-ignore -v`. Then the important part: that stops only *future* tracking — the credential is still readable in earlier commits, so **rotate it**, and rewrite history only if the exposure justifies the risk.

- **Senior:** "How do ignore rules resolve when several could match?" — Sources combine: global `core.excludesFile`, then `.gitignore` files from the root downwards, plus `.git/info/exclude` for the local clone. Within a file the **last matching pattern wins**; across files the **deeper** one wins. A negation cannot rescue a path inside an excluded directory because git never descends into it — ignore `dir/*` and negate a child. Rather than reasoning about it, ask git: `git check-ignore -v <path>` names the file, line and pattern that decided.

- **Staff:** "Two database dumps are in the public history of a monorepo. What do you do?" — Assess before acting: what is inside (here: OAuth tables empty, two `pbkdf2_sha256` hashes at 1,000,000 iterations, the primary account on Django's unusable-password marker, sessions a year expired), how exposed it was (public, 0 forks), and whether any live credential is present — if so, rotation comes first, because rewriting history never un-clones a leak. Then fix the *class*, not the instance: root cause was **scope**, a correct `db_backups/` rule sitting in a subtree `.gitignore` inside a monorepo, so the fix is a root-level block verified at multiple depths, `git rm --cached` to untrack, and a tracked-but-ignored audit to prove closure. Rewriting history is a judgement, not a reflex: with 0 forks, a repo going private, harmless contents and a force-push landing right after a merge, the cleanup carried more risk than the exposure — so it was declined, and the reasoning was written into the commit message so it stays a decision instead of becoming a surprise.

### Why interviewers ask these — and the answer that separates levels

| Testing for | Weak answer | What lands |
|---|---|---|
| Do you know ignore covers only untracked files? | "Add it to .gitignore and it's gone." | Name the limit, then the fix: `git rm --cached` untracks while the disk keeps the file. |
| Do you understand history is append-only? | "I deleted the file, we're fine." | Every earlier commit still serves it. Rotate the secret first; rewrite history only if justified. |
| Can you debug a pattern instead of guessing? | "I'd try different wildcards." | `git check-ignore -v` names file, line and pattern. Last match wins; deeper file wins. |
| Do you fix the class or the instance? | "I removed the two files." | Root cause was scope in a monorepo: root-level rule, verified at five depths, plus a drift audit. |

**The killer follow-up:** *"You added `*.sql` to `.gitignore` — is the leaked dump gone now?"* — No. Nothing about `.gitignore` or `git rm` touches earlier commits; the file is still served by `git show <old-commit>:path`. Answering "yes" reveals you have never reasoned about how git stores history.

# Revision Notes
- Three states: **tracked / untracked / ignored**. `.gitignore` controls only the untracked ones.
- Already committed? `git rm --cached` (index only, disk keeps the file) → commit. That is hygiene, **not** remediation — history is append-only, so rotate secrets.
- Trailing `/` = directory. Leading `/` = anchored. `*` never crosses `/`; `**` does.
- **Last matching pattern wins; deeper `.gitignore` wins.** A negation cannot escape an excluded directory.
- In a **monorepo**, data/secret rules go at the **root** — a subtree file guards only its subtree.
- `git check-ignore -v` ends every argument; `git status --ignored` keeps ignoring visible; `git ls-files -i -c --exclude-standard` is the drift audit (empty = clean).
- Never ignore: lockfiles, Django migrations, `.env.example`, CI config.

# Cheat Sheet
- **Who ignored it?** `git check-ignore -v <path>` — prints file:line:pattern; exit 1 = not ignored.
- **What is hidden?** `git status --ignored --short` (`!!` prefix). **How many tracked?** `git ls-files | wc -l`.
- **Drift audit:** `git ls-files -i -c --exclude-standard` — any output = tracked-but-ignored, fix it.
- **Untrack, keep on disk:** `git rm --cached <file>` / `git rm -r --cached <dir>/`; preview with `--dry-run`.
- **Undo:** before commit `git reset` · after commit `git revert <commit>`.
- **Deliberate override:** `git add -f <ignored-file>` — the `-f` is the audit trail.
- **Uncommitted personal rules:** `.git/info/exclude` (this clone) · `core.excludesFile` (this machine).
- **Patterns:** `*.sql` any depth · `db_backups/` directory · `/node_modules` anchored here · `**/vendor/` explicit any-depth · `logs/*` + `!logs/keep.log` for an exception.

# My ERP Section
| Concept | In this repo |
|---|---|
| Monorepo root ignore | `/.gitignore` — `*.sql`, `*.dump`, `*.sql.gz`, `db_backups/`, `backups/`, `node_modules/`, `sw obsidian/`, `.gstack/` |
| App-level ignore | `django_inventory/.gitignore`, 117 lines — **114** `db_backups/`, 115 `*.sql`, 116 `*.dump`, 117 `.env.bak` |
| The leak | `Django_app/myproject/mydb_backup_20250618.sql` + `..._20250620.sql`, tracked while public |
| Root cause | correct rule, wrong **scope** — a subtree `.gitignore` cannot guard a sibling folder |
| Fix commit | **`42a2ecc4`** — 2,956 files changed, 81 insertions, **331,748 deletions**, 0 bytes lost from disk |
| Verified | **2,954** files untracked via `git rm --cached`; blocked at 5 locations; drift audit empty |
| Deliberately not done | history rewrite — 0 forks, going private, contents harmless; recorded in the commit body |
| Rulebook | `CONTRIBUTING.md` §10: *"No committing data. Dumps, `.env`, media, `node_modules` — all gitignored at the monorepo root."* |

# Practice Tasks
1. **Prove precedence.** Run `git check-ignore -v` on `x.sql`, `django_inventory/x.sql` and `DSA/x.sql`. In one sentence, why is the middle one attributed to a different file?
2. **Read the real rule.** Open `/home/tech/umesh-personal/.gitignore` and `django_inventory/.gitignore` lines 112–117. Which patterns overlap deliberately, and why is that duplication a feature?
3. **Simulate the mistake safely.** In a throwaway repo (`git init /tmp/ig-demo`), commit `secret.sql`, *then* add `*.sql` to `.gitignore`. Show with `git status` that nothing changed; fix it with `git rm --cached`; then show `git show HEAD~1:secret.sql` still works.
4. **Negation drill.** In that repo, keep `logs/keep.log` while ignoring everything else under `logs/`. Write down why `logs/` + `!logs/keep.log` fails.
5. **Design.** Write the root `.gitignore` for a monorepo holding a Django app, a React app and a notebooks folder. Justify every line in a comment.

# Homework
- Read `git log -1 --format=%B 42a2ecc4`. It states root cause, audit findings, fix, and one deliberate non-action. Which of those four would *you* have forgotten to write?
- Write the two-paragraph incident note you would send a client: what was exposed, what was verified, what changed, and why history was not rewritten.
- `.git` here is **97 MB**. Using [Ch 05](05_How_Git_Stores_Everything.md), explain why untracking `node_modules` did not shrink it — and what would.
- Set up a **global** ignore file for your editor/OS junk, then explain why that content does not belong in the project's `.gitignore`.
- Find one currently-ignored file a new developer needs to run the project. Where is it documented instead? (Hint: `.env` and `.env.example`.)

---

# Further Reading & Live Resources
- Git docs — *`gitignore` pattern format*, the authoritative rules: https://git-scm.com/docs/gitignore
- Git docs — *`git check-ignore`*, the debugging tool: https://git-scm.com/docs/git-check-ignore
- Git docs — *`git rm`* and what `--cached` really means: https://git-scm.com/docs/git-rm
- GitHub's curated ignore templates (Python, Node, Django): https://github.com/github/gitignore
- GitHub docs — *removing sensitive data from a repository*: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository
- `git-filter-repo`, the supported history-rewriting tool: https://github.com/newren/git-filter-repo
