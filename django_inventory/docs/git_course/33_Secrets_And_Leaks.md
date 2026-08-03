---
id: git-course-33-secrets-and-leaks
type: lesson
status: active
owner: handwritten
scope: git — secrets in history, incident triage, rotation, prevention; the real dump leak in this repo
anchors: .gitignore, .env.example, Django_app/myproject/mydb_backup_20250620.sql, .github/pull_request_template.md
verified: 2026-08-03
---

# 33 — Secrets & Leaks (a real incident, audited end to end)

> Part of [Git Course](00_COURSE_OVERVIEW.md). Prev: [32 — Dependabot & Supply Chain](32_Dependabot_And_Supply_Chain.md). Next: [34 — Rewriting History Safely](34_Rewriting_History.md).

# Learning Objectives
By the end of this chapter you can:
- explain why deleting a file does **not** remove a secret, in terms of git's object model
- run a real leak triage: establish *what* leaked, *who could have seen it*, and *how bad it is* — before touching anything
- state the one action that always comes first, and why it is not a git command
- decide rationally whether to rewrite history, and defend either answer
- audit a repository for secrets already committed
- build layered prevention, and say honestly which layers are unavailable on a free private repo

# Purpose
This is the chapter this course exists to be able to write. On 2026-08-03 this repository was found
to have **two PostgreSQL database dumps committed in its history, while the repository was public**.

What follows is not a hypothetical. It is the actual triage: the commands run, the evidence found,
the verdict reached, and the decision made — including the decision *not* to rewrite history, and why
that was correct here.

Most secret-leak guides are a list of tools. This one is a **decision procedure**, because the tools
are the easy part. Knowing that rotation comes before cleanup, and that a "small" leak can be a
non-event while a "clean" repo can be compromised, is the part that takes judgement.

# The Problem
A secret in git is not like a secret in a file. **Git history is append-only.** Deleting the file
creates a *new* commit whose tree omits it — but the blob is still reachable from every earlier
commit's tree ([Chapter 05](05_How_Git_Stores_Everything.md)).

So the intuitive fix does nothing:

```bash
rm .env && git commit -am "remove secrets"    # the secret is still fully readable
git show HEAD~1:.env                          # ...like this
```

Three properties make this worse than an ordinary mistake:

1. **Anyone who cloned has it forever.** You cannot un-distribute a git object.
2. **Removal requires rewriting every descendant commit** — new hashes, a force-push, and every
   clone and fork broken.
3. **`git add` — not `git commit` — is the moment of entry.** Staging writes the blob into
   `.git/objects` immediately, so "I never committed it" is not the same as "it is not in the repo".

# Theory (from zero)

### Why the blob survives
A commit stores a **complete tree**. Deleting a file produces a new tree without that entry; the
blob it pointed to is untouched and still referenced by older trees.

```bash
git log --all --oneline -- path/to/secret     # every commit that touched it
git show <old-commit>:path/to/secret          # still prints the content
```

Objects are immutable and content-addressed. Nothing in git edits or deletes in place. That is a
feature for recovery ([Chapter 16](16_Reflog.md)) and a liability for secrets — the same property,
seen from two sides.

### The triage order (this is the chapter)
Most people reach for a history rewrite first. That is the wrong order, and it wastes the window in
which the damage is actually preventable.

```
1. ROTATE      — invalidate the credential. Nothing else reduces risk.
2. ASSESS      — what leaked, exactly? who could have fetched it?
3. CONTAIN     — stop it happening again (.gitignore, untrack, hooks)
4. DECIDE      — rewrite history, or accept it? Evidence-based, written down.
5. DOCUMENT    — record the decision so a future reader knows it was a judgement.
```

**Step 1 is not a git command.** Once a credential has been published, its secrecy is gone
permanently; scrubbing the repo only removes the *most convenient* copy. Rotate first, always. Every
minute spent on `filter-repo` before rotating is a minute the old credential still works.

### Step 2: what "assess" actually means
Three questions, each answerable with evidence:

| Question | How to answer |
|---|---|
| **What** leaked? | read the historical blob: `git show <commit>:<path>` |
| **Who** could have seen it? | public or private? forks? stars/watchers? clone traffic? |
| **How usable** is it? | plaintext password vs a strong hash vs an expired token |

That third question is where proportionate judgement lives. A leaked `pbkdf2_sha256` hash at a
million iterations is a very different incident from a leaked plaintext API key, and treating them
identically means either over-reacting or under-reacting — reliably one of the two.

### Step 4: the rewrite decision, honestly
Rewriting history with `git filter-repo` means: **new hashes for every affected commit and everything
after it**, a force-push, every clone invalidated, every fork divergent, and any build or deploy
referencing an old SHA broken. See [Chapter 34](34_Rewriting_History.md).

Rewrite when:
- the secret is **still usable** and cannot be rotated (rare — usually means a third party's key)
- the repository is public and the content is genuinely sensitive (PII, keys, customer data)
- a compliance obligation requires removal

Do **not** rewrite when:
- the credential has been rotated and the old value is now worthless
- the exposure is audited and mild
- the disruption exceeds the residual risk

Both answers are defensible. What is *not* defensible is choosing without evidence, or choosing and
not writing down why.

### The layers of prevention
| Layer | Free on private repo? | What it stops |
|---|---|---|
| `.gitignore` | ✅ | staging the file at all — **the cheapest and best layer** |
| `.env.example` convention | ✅ | committing real values by making the template obvious |
| pre-commit hook scanning staged content | ✅ | a mistake, sometimes |
| Code review / PR template question | ✅ | a force-added file (`git add -f` bypasses ignore rules) |
| **GitHub secret scanning + push protection** | ❌ **paid** (Advanced Security) | the platform refusing the push |

That last row matters for this project. Secret scanning and push protection are **not free on private
repositories**, so the layers here are `.gitignore` + hooks + a mandatory review question. Naming the
gap is the point; assuming a paid feature is protecting you is how leaks happen.

> 💡 **Samjho aise:** Git ki diary mein likha hua **mitta nahi**. File delete karne se aaj ka page saaf
> hota hai — kal ka page waise ka waisa likha rehta hai. Isliye *"file hata di, ho gaya"* galat hai.
>
> Aur sabse zaroori baat, jo log ulta karte hain: **pehle password badlo (rotate), baad mein safai.**
> Kyunki jo baahar chala gaya, wo wapas nahi aata — jisne clone kiya, uske paas hamesha rahega. Safai
> sirf *sabse aasaan copy* hatati hai. Purana password chalu rehta hai jab tak tum use band na karo.
>
> Teen sawaal poochho: **kya** nikla, **kaun** dekh sakta tha, aur **kaam ka hai ya nahi**. 1,000,000
> iteration wala hash aur plaintext key — dono "leak" hain, par bilkul alag baat hain.

# Real World Example (this repo) — the full incident

### What was found
While checking whether the repository was safe to make private, a scan of committed file *types*
surfaced two files that should never have been in a code repository:

```bash
git log --all --pretty=format: --name-only --diff-filter=A | sort -u \
  | grep -Ei '(^|/)\.env($|\.)|\.pem$|\.key$|id_rsa|\.sql$|\.dump$|credentials|secret'
```
```
Django_app/myproject/mydb_backup_20250618.sql
Django_app/myproject/mydb_backup_20250620.sql
```

Two `pg_dump` files, June 2025, from an **old practice app** (`Django_app/`) — not the ERP. And they
were not merely in history; they were **still tracked**.

### Step 2 — assess, before touching anything
**What leaked.** A dump is plaintext SQL, so the contents were read directly from the historical blob:

```bash
git show b7fe9c89:Django_app/myproject/mydb_backup_20250620.sql | head -3
# -- PostgreSQL database dump
# -- Dumped by pg_dump version 14.18
```

Then the tables it contained:

```bash
git show b7fe9c89:...20250620.sql | grep -oE 'COPY public\.[a-z_]+' | sort -u
```
```
COPY public.accounts_user            ← users, emails, password hashes
COPY public.django_session           ← session keys
COPY public.socialaccount_socialapp  ← ⚠ OAuth client id + SECRET live here
COPY public.socialaccount_socialtoken← ⚠ Google access/refresh tokens
```

The last two are the ones that would have made this serious. So they were checked, not assumed:

```bash
awk '/^COPY public.socialaccount_socialapp /{f=1;next} f&&/^\\\.$/{f=0} f' dump.sql
# \.        ← EMPTY. no OAuth client secret.
awk '/^COPY public.socialaccount_socialtoken /{f=1;next} f&&/^\\\.$/{f=0} f' dump.sql
# \.        ← EMPTY. no Google tokens.
```

Then the user rows:

```
1  pbkdf2_sha256$1000000$3ukT81I82MkArkQvVGRwQU$etmD3r5r…  umesh@gmail.com
3  pbkdf2_sha256$1000000$cbod6nEHXqjYkapcGDV0fG$rKqjtNhN…  Rahul@gmail.com
2  !OUUm8NkB3ml1sU5FK7GnF3aoz7S555Asr2uJjfUc              umesh29mar@gmail.com
```

Three details that decided the verdict:

- **`pbkdf2_sha256$1000000$`** — one **million** iterations. Django's default. Brute-forcing that is
  computationally impractical for any realistic attacker at this scale.
- **`!OUUm8Nk…`** — a leading `!` is Django's marker for an **unusable password**. That account is
  Google-login-only; there is no hash to attack.
- **`django_session`** — two rows, June 2025, long expired.

**Who could have seen it.** The repository was public. But:

```bash
gh api repos/umesh29032/umesh-personal --jq '{forks:.forks_count,stars:.stargazers_count,watchers:.subscribers_count}'
# {"forks":0,"stars":0,"watchers":0}
```

**Zero forks, zero stars, zero watchers.** Nobody had copied it.

And the wider check came back clean:

```bash
git grep -nE "SECRET_KEY\s*=\s*['\"][^'\"]{25,}" -- '*.py' | grep -v 'environ|getenv|config('
# config/settings/base.py:37: _SECRET_KEY = 'django-insecure-dev-only-do-not-use-in-production'
```

A deliberate dev placeholder; production reads `SECRET_KEY` from the environment. No `.env`, `.pem`,
`.key` or `id_rsa` had **ever** been committed.

**Verdict: mild.** Real exposure — three email addresses, two strong hashes, two dead sessions — but
nothing an attacker could use.

### Step 3 — contain, and the root cause
The root cause is the genuinely instructive part, because the rule was **not missing**:

```
django_inventory/.gitignore:114   db_backups/     ✅ present — the ERP never leaked a dump
/home/tech/umesh-personal/        (no such rule)  ❌ the monorepo root was unprotected
```

A `.gitignore` **only guards its own subtree**. This is a monorepo: `Django_app/`, `DSA/` and others
are siblings of `django_inventory/`. The rule was correct and scoped too narrowly — which is a much
more common failure than having no rule at all.

Fix: a monorepo-root `.gitignore`.

```gitignore
*.sql
*.dump
*.sql.gz
db_backups/
backups/
node_modules/
```

Verified as blocking at five separate locations, not assumed:

```
✓ BLOCKED   test_leak.sql                    (repo root)
✓ BLOCKED   django_inventory/test_leak.sql   (the live ERP)
✓ BLOCKED   django_inventory/config/*.dump
✓ BLOCKED   Django_app/test_leak.sql         (where it happened)
✓ BLOCKED   DSA/test_leak.sql
```

Then untracked without deleting:

```bash
git ls-files -i -c --exclude-standard -z | git rm --cached --quiet --pathspec-from-file=- --pathspec-file-nul
```

**2,954 files** left the index (2 dumps + 2,952 `node_modules`), 331,748 deletions — and the files
stayed on disk, verified byte-identical before and after. `--cached` is the whole difference
([Chapter 03](03_The_Three_Trees.md)). Zero files under `django_inventory/` were affected, proven
*before* running it.

An escape hatch was kept deliberately:

```gitignore
# Need to commit a genuinely-code .sql one day? These patterns block `git add`, so force it:
#     git add -f path/to/that.sql
# Being forced to type -f is the point: it makes committing SQL a decision instead of an accident.
```

### Step 4 — the decision NOT to rewrite history
Evidence on the table:

| Factor | Finding |
|---|---|
| Credential still usable? | **No** — 1,000,000-iteration hashes; primary account has no password at all |
| OAuth secrets / tokens? | **None** — both tables empty |
| Anyone cloned it? | **0 forks, 0 stars, 0 watchers** |
| Repository going private? | **Yes** |
| Cost of rewriting | new hashes for all descendants + force-push, immediately after a merge |

**Decision: do not rewrite.** The dumps remain in earlier commits. A `git-filter-repo` force-push
right after PR #15 landed was judged more risk than an audited-mild exposure warranted.

### Step 5 — document it
The decision went into the commit message, verbatim, so it reads as a judgement rather than an
oversight:

> *"History is deliberately NOT rewritten. The dumps remain in earlier commits. With 0 forks, the
> repository going private, and nothing usable inside, a git-filter-repo force-push is more risk than
> the exposure warrants. Recorded here so the decision is explicit rather than forgotten."*

That paragraph is the most important artefact of the whole incident. Without it, the next person to
find those dumps has to redo the entire audit to learn what was already known.

# Visual Diagram
```
  WHY DELETION DOES NOT WORK
  ──────────────────────────
   commit A ──► tree ──► blob(secret)   ← still reachable, still readable
   commit B ──► tree ──► blob(secret)
   commit C ──► tree            (file deleted: tree omits it)
                    ▲
        `git show A:path` prints it in full. Append-only history.
        `git add` — not commit — is when the blob entered .git/objects.

  TRIAGE ORDER (people get this backwards)
  ────────────────────────────────────────
   1. ROTATE    ← NOT a git command. Nothing else reduces risk.
   2. ASSESS    what leaked · who could see it · is it usable
   3. CONTAIN   .gitignore → git rm --cached → hooks
   4. DECIDE    rewrite vs accept — on evidence
   5. DOCUMENT  so nobody re-audits it later

  THIS INCIDENT
  ─────────────
   found : 2 × pg_dump, June 2025, TRACKED, repo PUBLIC
   what  : 3 emails · 2 × pbkdf2_sha256$1000000$ · 2 expired sessions
           socialaccount_socialapp   EMPTY  → no OAuth secret
           socialaccount_socialtoken EMPTY  → no Google tokens
           accounts_user id=2 → "!OUUm8Nk…" = UNUSABLE password (Google-only)
   who   : 0 forks · 0 stars · 0 watchers
   verdict: MILD

   ROOT CAUSE — the rule existed, scoped too narrowly:
     django_inventory/.gitignore:114  db_backups/   ✅  (ERP never leaked)
     monorepo root                    (nothing)     ❌  ← Django_app/ unprotected
     a .gitignore guards ONLY its own subtree

   FIX: root .gitignore → blocked at 5 locations (verified, not assumed)
        git rm --cached → 2,954 files untracked, 0 bytes lost on disk
   DECISION: no rewrite (rotated-irrelevant + 0 forks + going private)
        → written into the commit message
```

# Practical — audit any repository for secrets
```bash
cd /home/tech/umesh-personal

# 1. was a secret-shaped file EVER added, in any branch, ever?
git log --all --pretty=format: --name-only --diff-filter=A | sort -u \
  | grep -Ei '(^|/)\.env($|\.)|\.pem$|\.key$|id_rsa|\.sql$|\.dump$|credentials|secret' \
  | grep -v -E '\.env\.example|/docs/'

# 2. is anything tracked RIGHT NOW that an ignore rule says should not be?
git ls-files -i -c --exclude-standard        # empty output = clean

# 3. a hard-coded secret in tracked code?
git grep -nE "SECRET_KEY\s*=\s*['\"][^'\"]{25,}" -- '*.py' \
  | grep -v -E 'os\.environ|getenv|config\(|test|example'
git grep -nE "(api[_-]?key|password|token)\s*=\s*['\"][A-Za-z0-9_\-]{16,}" -- '*.py'

# 4. read a historical blob — how you establish WHAT leaked
git log --all --oneline -- <path>
git show <commit>:<path> | head -20

# 5. who could have seen it?
gh api repos/<owner>/<repo> --jq '{private:.private,forks:.forks_count,stars:.stargazers_count,watchers:.subscribers_count}'

# 6. do the ignore rules actually work? TEST them, don't assume
for p in x.sql sub/dir/y.dump .env; do
  mkdir -p "$(dirname "$p")" 2>/dev/null; : > "$p"
  git check-ignore -q "$p" && echo "  ✓ BLOCKED $p" || echo "  ✗ WOULD COMMIT $p"
  rm -f "$p"
done

# 7. untrack without deleting from disk
git rm --cached <path>          # then commit the .gitignore rule in the SAME commit

# 8. the biggest blobs in history (dumps and binaries hide here)
git rev-list --objects --all \
  | git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' \
  | awk '$1=="blob"' | sort -k3 -n | tail -10
```

Command 2 is the one to run today, in every repository you own. Empty output means clean; any output
is a file that slipped past a rule.

# Production Walkthrough
The procedure, in order, when you find a secret in history:

1. **Rotate.** Change the password, revoke the key, invalidate the token. Before anything else.
2. **Establish what leaked** by reading the historical blob — not the current file, and not from
   memory.
3. **Establish who could have seen it**: visibility, forks, watchers, and (if the host provides it)
   clone traffic.
4. **Grade usability.** Plaintext credential, or a million-iteration hash? Live token, or one that
   expired in 2025?
5. **Contain**: add the ignore rule, `git rm --cached`, commit both **together** — a rule without
   untracking leaves the file tracked, since `.gitignore` does not apply to already-tracked paths.
6. **Verify the containment** by testing the rule at several paths, not by reading it.
7. **Decide on a rewrite**, on evidence. Write the reasoning down either way.
8. **Close the class, not the instance.** The instructive question is never "how do I delete this
   file" — it is "why was the rule not covering this path".

Step 8 is what turned this incident into a permanent fix: the answer was *monorepo scoping*, so the
rule moved to the root and now covers `DSA/` and every future sibling too.

# Debugging Guide

| Symptom | Cause | Fix |
|---|---|---|
| Deleted the file; secret still in history | blob reachable from older commits | rotate; then decide about a rewrite ([Ch 34](34_Rewriting_History.md)) |
| Added to `.gitignore`, file still shows in `git status` | ignore rules do not apply to **tracked** files | `git rm --cached <path>` |
| `git rm` deleted it from disk too | you omitted `--cached` | `git restore <path>` if still in HEAD |
| Ignore rule works in one folder, not another | a `.gitignore` guards only its own subtree | put the rule at the repo root — **this incident's root cause** |
| Secret committed despite the rule | someone used `git add -f` | that is deliberate; review must catch it ([Ch 23](23_CODEOWNERS_And_Templates.md)) |
| Rewrote history; secret still in a clone | other clones and forks are independent | rotation is the only real remedy |
| `git ls-files -i -c` returns rows | tracked-but-ignored files | untrack them; investigate how they got in |
| Secret scanning not available | Advanced Security is **paid** on private repos | `.gitignore` + hooks + review question |
| Old commits still show the file after rewrite | you did not `gc`/expire reflogs, or clones are stale | `git reflog expire --expire=now --all && git gc --prune=now` locally; everyone re-clones |

# Performance Notes
- **`git log --all --diff-filter=A --name-only`** walks every commit — seconds on this repo's 289,
  minutes on a very large history. Run it once, save the output.
- The blob-size audit (`rev-list --objects` piped to `cat-file --batch-check`) is the fast way to find
  dumps and binaries; `--batch-check` reads in bulk instead of spawning a process per object.
- **A committed dump inflates the repo permanently.** These two are ~86 KB combined — trivial. A 2 GB
  dump would have made every clone painful forever, since git never forgets
  ([Chapter 37](37_Large_Files_And_Performance.md)).
- `git check-ignore -q` is instant, so testing rules at a dozen paths costs nothing.
- A rewrite is the expensive operation: `filter-repo` rewrites every affected commit, then everyone
  re-clones.

# Security Considerations
- **Rotation is the only step that actually removes risk.** Everything else reduces convenience for
  an attacker.
- **`git add` is the moment of entry**, not `git commit`. A staged-then-abandoned secret is already a
  blob in `.git/objects` ([Chapter 05](05_How_Git_Stores_Everything.md)).
- **`git add .` is the most common vector.** It sweeps `.env`, dumps and keys unless a rule blocks
  them. That is exactly how these dumps arrived.
- **A dump is a full data breach in one file** — every row, every hash, every session, in plaintext
  SQL. Treat dumps like keys.
- **Grade the exposure; do not reflex.** A million-iteration `pbkdf2` hash and a plaintext API key are
  not the same incident. Over-reacting burns credibility; under-reacting burns you.
- **Password reuse extends a leak beyond the repo.** Worth stating: the dev credential `Kapil@1234`
  is reused across this project's test accounts. Not in these dumps — but weak and reused, and it
  must not follow the project into production.
- **Secret scanning and push protection are paid on private repos.** The free substitute is
  `.gitignore` + hooks + a mandatory review question, and the PR template here asks explicitly
  whether any `.sql`, `.env` or dump was **force-added** past the ignore rules.
- **Public → private does not un-publish.** Existing clones persist; search caches may linger. It
  stops *new* access.

# Architecture Decisions
- **Prevention at the monorepo root, not per project.** The failure was scoping, so the fix is a root
  `.gitignore` covering every sibling — present and future.
- **`git add -f` deliberately still works.** A rule you cannot override gets deleted; one that
  demands an explicit flag stays, and makes committing SQL a decision.
- **`git rm --cached` rather than deletion.** Untrack while preserving the owner's files; verified
  byte-identical before and after.
- **The ignore rule and the untracking committed together.** Either alone is incomplete.
- **No history rewrite** — decided on evidence (rotation-irrelevant, 0 forks, going private) and
  recorded in the commit message.
- **The lesson written into the course**, not just the commit: `deployment_course/28_Backups.md`
  gained a "what a dump actually IS" section, a security bullet, and a beginner-mistake row, because
  the chapter explained `pg_dump` without ever saying what the artefact it produces contains.
- **The audit is preserved.** Anyone finding these dumps later reads the verdict instead of redoing
  the work.

# Best Practices
- **Rotate first.** Always. Before any git command.
- Read the **historical blob** to establish what leaked; never rely on memory.
- Grade usability before choosing a response.
- Put ignore rules at the **repository root** in a monorepo.
- Commit the ignore rule and the `git rm --cached` **together**.
- **Test** ignore rules with `git check-ignore` at several paths.
- Run `git ls-files -i -c --exclude-standard` periodically; empty is the only acceptable output.
- Keep `.env.example` committed with placeholder values, and `.env` ignored.
- Never commit a database dump. Backups belong in a backup location
  ([`28_Backups.md`](../deployment_course/28_Backups.md)).
- Write the decision down — especially the decision *not* to act.

# Beginner Mistakes
- **`rm secret && git commit`** → the blob is still reachable from every earlier commit.
- **Rewriting history before rotating** → the credential stays valid throughout, which is the actual
  risk.
- **`git add .` habitually** → the single most common way secrets enter a repo.
- **Assuming `.gitignore` hides an already-tracked file** → it applies only to untracked paths.
- **A `.gitignore` in a subdirectory of a monorepo** → guards only its own subtree. This incident.
- **Treating every leak as maximum severity** → a strong hash is not a plaintext key; grade it.
- **Believing "private" undoes a public leak** → existing clones persist.
- **Assuming secret scanning is watching** → it is paid on private repos.
- **Fixing the file and not the rule** → the same class recurs in a different folder.
- **Not writing down a decision not to rewrite** → the next person re-audits from scratch.

# Interview Questions
- **Junior:** "You committed a password. What do you do?" — Change the password first, because once it
  is published its secrecy is gone and cleanup does not restore it. Then add the file to
  `.gitignore`, `git rm --cached` it, and commit both together. Deleting the file does not remove it
  from history.
- **Mid:** "Why doesn't deleting the file remove the secret?" — Commits store complete trees, and
  objects are immutable. Deleting produces a new tree without the entry, but the blob stays reachable
  from every earlier commit — `git show <old-commit>:<path>` prints it. Removal means rewriting those
  commits, which changes their hashes and every descendant's.
- **Senior:** "Walk me through a leak triage." — Rotate, assess, contain, decide, document — in that
  order. Rotation first because nothing else reduces risk. Assess by reading the historical blob for
  *what*, checking visibility and forks for *who*, and grading *usability* — a million-iteration
  `pbkdf2` hash is a very different incident from a live API key. Contain with a root-level ignore
  rule plus `git rm --cached`, committed together, and verify the rule by testing it rather than
  reading it. Only then decide about a rewrite, and write the reasoning down either way — including a
  decision not to, so nobody re-audits it later.
- **Staff:** "A credential was committed a year ago, deleted the next day, repo is public. Response?" —
  Rotate immediately and treat it as fully disclosed, because anyone who cloned in that window has it
  permanently and no repository operation can retract it. Then scope the blast radius on evidence
  rather than instinct: read the historical blob to know exactly what was in it, check forks, stars,
  watchers and clone traffic for who could plausibly hold it, and grade usability, since a strong hash
  and a live token warrant very different responses. A rewrite is a *separate* decision with a real
  cost — new hashes for every descendant, a force-push, invalidated clones and forks, broken deploy
  references — so it is justified only when the value is still live and unrotatable, or an obligation
  demands it; otherwise it is disruption bought with no risk reduction. Then close the **class**, not
  the instance: the interesting question is never "how do I delete this file", it is "why did the rule
  not cover this path". Here the answer was monorepo scoping — a correct rule that only guarded its own
  subtree — so the fix moved to the root and now covers every sibling, present and future. Finally,
  record the decision and its evidence, and be explicit about which preventive layers you do not have:
  secret scanning and push protection are paid on private repos, so `.gitignore`, hooks and a
  mandatory review question are the substitute, and pretending otherwise is how the next one happens.

### Why interviewers ask these — and the answer that separates levels
| Testing for | Weak answer | What lands |
|---|---|---|
| Do you know history is append-only? | "I deleted the file and pushed." | Commits hold complete trees; the blob stays reachable from older commits, so `git show <old>:<path>` still prints it. |
| Do you get the ORDER right? | "I'd use filter-repo to scrub it." | Rotate first — nothing else reduces risk; a rewrite only removes the most convenient copy, and clones already exist. |
| Can you scope proportionately? | "Any leak is critical, rewrite everything." | Grade what leaked and who could hold it: a 1,000,000-iteration hash with 0 forks is not a live key on a popular repo. |

**The killer follow-up:** *"You rewrote history and force-pushed. Is the secret gone?"* — No. Every existing clone and fork still has it, the objects survive locally until reflogs expire and `gc` runs, and the host may retain unreachable objects and PR refs. Rewriting removes the *most convenient* copy from *one* remote — which is why rotation is step 1 and a rewrite is at best step 4. Anyone who answers "yes" has never actually run an incident.

# Revision Notes
- **Git history is append-only.** Deleting a file makes a new tree without it; the **blob stays reachable** from older commits.
- **`git add`** — not commit — writes the blob into `.git/objects`.
- **Triage order: ROTATE → ASSESS → CONTAIN → DECIDE → DOCUMENT.** Rotation is not a git command and always comes first.
- Assess = **what** (read the historical blob) · **who** (visibility, forks, watchers) · **how usable** (hash vs live key).
- Contain = root `.gitignore` **+** `git rm --cached`, committed **together**; `.gitignore` never applies to tracked files.
- **A `.gitignore` guards only its own subtree** — this incident's root cause in a monorepo.
- Rewrite ⇒ new hashes for all descendants + force-push + every clone/fork broken. Decide on evidence; **write it down either way**.
- Secret scanning + push protection are **PAID** on private repos ⇒ substitute `.gitignore` + hooks + review question.
- **Public → private does not un-publish.** Clones persist.
- This incident: 2 dumps · 3 emails · 2 × `pbkdf2_sha256$1000000$` · sessions expired · OAuth tables **empty** · **0 forks** ⇒ **mild**, no rewrite, 2,954 files untracked, 0 bytes lost.

# Cheat Sheet
```bash
# ── AUDIT ───────────────────────────────────────────────────────────────────
git log --all --pretty=format: --name-only --diff-filter=A | sort -u \
  | grep -Ei '\.env|\.pem$|\.key$|id_rsa|\.sql$|\.dump$|credentials|secret'
git ls-files -i -c --exclude-standard          # tracked BUT ignored = slipped a rule
git grep -nE "SECRET_KEY\s*=\s*['\"][^'\"]{25,}" -- '*.py'
git log --all --oneline -- <path>              # every commit that touched it
git show <commit>:<path>                       # READ the historical blob ← what leaked
gh api repos/<o>/<r> --jq '{private:.private,forks:.forks_count,watchers:.subscribers_count}'

# biggest blobs in history (dumps/binaries hide here)
git rev-list --objects --all \
  | git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' \
  | awk '$1=="blob"' | sort -k3 -n | tail -10

# ── CONTAIN ─────────────────────────────────────────────────────────────────
printf '*.sql\n*.dump\ndb_backups/\n.env\n' >> .gitignore    # at the REPO ROOT
git rm --cached <path>                          # untrack, KEEP on disk
git check-ignore -v <path>                      # WHICH rule blocks it (exit 1 = not ignored)
git add -f <path>                               # deliberate override, on purpose

# ── ROTATE FIRST. Then, only if justified: ──────────────────────────────────
git filter-repo --invert-paths --path <secret>  # ch 34 — new hashes + force-push
git reflog expire --expire=now --all && git gc --prune=now --aggressive
```

# My ERP Section

| Fact | This incident |
|---|---|
| Found | `Django_app/myproject/mydb_backup_20250618.sql` and `…20250620.sql` — 2 `pg_dump` files, June 2025, **still tracked**, repo **public** |
| Not the ERP | from an old practice app (`Django_app/`), unrelated to `django_inventory/` |
| Exposed | 3 emails · **2** hashes at `pbkdf2_sha256$1000000$` · 2 `django_session` rows (June 2025, expired) |
| **Not** exposed | `socialaccount_socialapp` **empty** (no OAuth client secret) · `socialaccount_socialtoken` **empty** (no Google tokens) · no plaintext passwords · no `.env`/`.pem`/`.key` ever committed |
| Primary account | `accounts_user` id=2 → `!OUUm8Nk…` = Django **unusable password** (Google-login only) — no hash to attack |
| Reach | **0 forks, 0 stars, 0 watchers** |
| `SECRET_KEY` | `base.py:37` dev placeholder only; production reads it from the environment |
| **Root cause** | `django_inventory/.gitignore:114` already ignored `db_backups/` — so the ERP never leaked one — but a `.gitignore` guards only its own subtree, and this is a **monorepo** |
| Fix | monorepo-root `.gitignore`: `*.sql`, `*.dump`, `*.sql.gz`, `db_backups/`, `backups/`, `node_modules/` — verified blocking at **5** locations |
| Untracked | **2,954** files (2 dumps + 2,952 `node_modules`), 331,748 deletions, **0 bytes lost on disk**, **0** files under `django_inventory/` touched |
| Escape hatch | `git add -f` still works, with the reason written into `.gitignore` |
| **Decision** | **no history rewrite** — rotation-irrelevant + 0 forks + going private; reasoning recorded in the commit message |
| Lesson shipped | `deployment_course/28_Backups.md` gained "What a dump actually IS", a security bullet, and a beginner-mistake row |
| Standing gap | secret scanning + push protection are **paid** on private repos ⇒ `.gitignore` + hooks + the PR template's force-add question |

# Practice Tasks
1. Run audit commands 1 and 2 on **every** repository you own. Any output from command 2 is a file
   that slipped past a rule.
2. In this repo, read the leaked dump's own header:
   `git show b7fe9c89:Django_app/myproject/mydb_backup_20250620.sql | head -5`. Confirm you can read a
   deleted file's content from history.
3. Reproduce the root cause: make a subdirectory `.gitignore` with `*.sql`, then create a `.sql` file
   in the **parent**. Confirm with `git check-ignore -v` that it is not ignored. That is the whole bug.
4. Test containment properly: add a root rule, then run the five-location `check-ignore` loop. Assume
   nothing.
5. Practise untracking safely in a throwaway repo: commit a file, add it to `.gitignore`, confirm
   `git status` still tracks it, then `git rm --cached` and confirm the file survives on disk.
6. Grade three hypothetical leaks — a plaintext Stripe key, a `pbkdf2_sha256$1000000$` hash, an
   OAuth refresh token — and rank them. Justify the order out loud.

# Homework
- Write your own leak-response runbook: the five steps, with the exact commands *you* would run, and
  the rotation procedure for each credential your project holds. Keep it where you would find it at
  3am.
- Add a `pre-commit` hook that refuses staged content matching an obvious secret pattern. Then read
  [Chapter 26](26_Pre_Commit_Hooks.md) again and explain why that hook is **already late**.
- Run the biggest-blob audit on the largest repository you have access to. Find the largest file that
  should never have been committed.
- Read one public post-mortem of a real credential leak (Uber's 2016 GitHub-token incident is
  well-documented) and identify which of the five triage steps they got wrong.

# Further Reading & Live Resources
- [GitHub Docs — Removing sensitive data from a repository](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository) — the official procedure, and its warnings
- [git-filter-repo](https://github.com/newren/git-filter-repo) — the maintained rewrite tool (git's own docs now recommend it over `filter-branch`)
- [Pro Git — Git Objects](https://git-scm.com/book/en/v2/Git-Internals-Git-Objects) — why a deleted file's blob survives
- [gitignore reference](https://git-scm.com/docs/gitignore) — pattern syntax and, crucially, **precedence and scoping**
- [GitHub Docs — About secret scanning](https://docs.github.com/en/code-security/secret-scanning/about-secret-scanning) — including which plans it covers
- [Django — password management](https://docs.djangoproject.com/en/5.0/topics/auth/passwords/) — the `pbkdf2_sha256` format and the `!` unusable-password marker
- [trufflehog](https://github.com/trufflesecurity/trufflehog) · [gitleaks](https://github.com/gitleaks/gitleaks) — free scanners you can run yourself when the paid feature is unavailable
