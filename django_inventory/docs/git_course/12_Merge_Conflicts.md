---
id: git-course-12-merge-conflicts
type: lesson
status: active
owner: handwritten
scope: git, version control — conflict markers, index stages 1/2/3, ours vs theirs, resolving, aborting, rerere, merge drivers, semantic conflicts
anchors: config/production/migrations/0052_workerstageallocation_allocation_mode.py, .github/workflows/ci.yml, CONTRIBUTING.md, Django_app/myproject/package-lock.json
verified: 2026-08-03
---

# 12 — Merge Conflicts (reading the markers, resolving properly, never panicking)

> Part of [Git Course](00_COURSE_OVERVIEW.md). Prev: [11 — Merging](11_Merging.md). Next: [13 — Rebase](13_Rebase.md).

# Learning Objectives
By the end of this chapter you can:
- explain why `CONFLICT (content)` is a **question**, not an error or a broken repository
- read `<<<<<<<` / `=======` / `>>>>>>>` and say which branch each side came from
- say what `ours` and `theirs` mean in a merge, in a rebase, and why they **swap** — the most expensive trap in git
- read `git status`, the combined `git diff`, and `git show :2:<file>` mid-conflict, and get the **base** with `--conflict=diff3`
- resolve three legitimate ways — edit, `--ours/--theirs`, regenerate — and know which is banned on a source file
- exit at any stage: `git add`, `git merge --abort`, `git rebase --continue/--skip/--abort`
- enable `git rerere`, and recognise a **semantic** conflict that merged cleanly and still broke production

# Purpose
Chapter 11 ended where the fear starts: *both sides changed the same region, so git stops.* This chapter is that stop, in full.

A conflict is the one moment git refuses to decide for you — and the moment most people close the terminal. That reaction is not caused by difficulty. It is caused by the screen **looking like damage**. Nothing is damaged. Git has paused, put both candidate answers in front of you, and asked one question. Learn to read the question and resolving becomes ordinary work.

# The Problem
You rebase onto `main` and get this:

```
Auto-merging svc/settlement.py
CONFLICT (content): Merge conflict in svc/settlement.py
Automatic merge failed; fix conflicts and then commit the result.
```

You open the file and your code has been replaced by this:

```python
def settle(adda):
<<<<<<< HEAD
    total = compute_total(adda, include_alter=True)
=======
    total = round(compute_total(adda), 2)
>>>>>>> feat/rounding
    ledger_credit(adda.worker, total)
    return total
```

The honest questions nobody answers for beginners: which line is **mine**? Did the other get deleted? Is the repo broken — can I still switch branches, still commit? And if I pick wrong, does money get paid wrong?

That last one is not dramatic. Here `settle()` is not a toy: settlement is the **only** money-write boundary in the ERP, and the golden totals ₹344.25 / ₹801 / ₹633 / ₹225 are asserted byte-identically. A resolution that keeps one side and drops the other is a syntactically perfect data bug. Guessing is not an option. Reading is.

# Theory (from zero)

### A conflict is a question, not an error

From [Ch 11](11_Merging.md): a three-way merge compares the **merge base** against **ours** and **theirs**, region by region. Usually one side changed and the other did not, so the answer is obvious and git takes it silently. A **conflict** is the leftover case — **the same region changed differently on both sides** — and git will not pick, because picking wrongly *silently* is worse than stopping. So it:

1. writes **both** versions into your working file, wrapped in markers
2. records base + ours + theirs in the index, unresolved
3. stops and prints the two commands that end it

Nothing is lost, nothing is corrupted, no commit was made. `CONFLICT` means *"two humans disagreed here; you are the tie-breaker."* And note what git compared: **text regions, not meaning.** It has no idea what `include_alter=True` does. That explains both why conflicts appear where they feel unnecessary, and why a clean merge is not proof of correctness.

### The index mid-conflict — stages 1, 2, 3

[Ch 03](03_The_Three_Trees.md) said the index lists each path once. During a conflict one path is listed **three times**, in numbered **stages**. Real output:

```
$ git ls-files -u
100644 79e8e024… 1	svc/settlement.py     ← stage 1 = BASE   (the merge base)
100644 35af6a8f… 2	svc/settlement.py     ← stage 2 = OURS   (HEAD)
100644 d1ec8361… 3	svc/settlement.py     ← stage 3 = THEIRS (incoming)
```

You can read any stage as a **clean file, no markers** — the escape hatch when the markers are unreadable:

```bash
git show :1:svc/settlement.py    # base
git show :2:svc/settlement.py    # ours
git show :3:svc/settlement.py    # theirs
```

And it defines "resolved" mechanically: **collapse those three stages into one stage-0 entry.** That is all `git add` does here.

### Marker anatomy, character by character

```python
<<<<<<< HEAD                                         ← 7 '<' at column 0 + a LABEL
    total = compute_total(adda, include_alter=True)      ← OURS   (stage 2)
=======                                              ← 7 '=' the divider
    total = round(compute_total(adda), 2)                ← THEIRS (stage 3)
>>>>>>> feat/rounding                                ← 7 '>' + a LABEL
```

Seven repeated characters, chosen to be unlikely in real code. **Top = ours = where you stand** (label usually `HEAD`). **Bottom = theirs = what is coming in.** The markers are **plain text in your file** — not metadata. Git will happily commit them if you tell it to.

The conflict is confined to the hunk: `def settle(adda):` and the two lines after it are already the merged result, not one side's copy.

### `ours` vs `theirs` — and the flip that catches everyone

Say it properly: **`ours` = the branch you are currently on. `theirs` = whatever is being applied to you.** On `main`, `git merge feat/x` makes `main` "ours" and *your own work* "theirs". Annoying, but stable.

Now watch it invert. Real rebase of `feat/x` onto `main`, where `main` holds `OURS` and **my own commit** holds `THEIRS`:

```
$ git switch feat/x && git rebase main
CONFLICT (content): Merge conflict in f.txt
error: could not apply f324f40... theirs change

$ cat f.txt
a
<<<<<<< HEAD
OURS
=======
THEIRS
>>>>>>> f324f40 (theirs change)
c
```

I am standing on **my own branch**, and the `HEAD` side contains **`main`'s** line. Because a rebase does not merge into `main` — it **replays my commits on top of `main`**, so at each step the ground I stand on is the growing copy of `main` and the patch being applied is *mine*.

| Operation | `ours` / `HEAD` / `--ours` | `theirs` / `--theirs` |
|---|---|---|
| `git merge feat/x` (on `main`) | `main` | `feat/x` — your work |
| `git rebase main` (on `feat/x`) | `main` — the upstream | **your own commit** — inverted |
| `git cherry-pick <sha>` | current branch | the picked commit |
| `git stash pop` | working tree | the stashed change |

**The rule that survives all four: never resolve by the words.** Read content, or identify the sides with `git log --merge` and `git show :2:` / `:3:`. `-X ours` inside a rebase means *prefer upstream, discard mine* — the opposite of what most people intend when they type it.

> 💡 **Samjho aise:** Conflict ko **error samjho hi mat** — ye ek **sawaal** hai. Socho do bhai ek hi kadhai mein daal bana rahe the: ek ne namak daala, doosre ne mirchi — dono ne **ek hi hissa** badla. Git munshi hai, chef nahi. Woh dono versions kaagaz pe likh ke saamne rakh deta hai: "ye tumne likha (`ours`), ye unhone (`theirs`) — final kya jaayega?" Ghar nahi jala, khana nahi bigda; bas **faisla baaki hai**.
>
> Aur ek pakka dhoka: `ours` matlab "meri branch" **nahi** — `ours` matlab **jis zameen pe tum khade ho**. Merge mein tum `main` pe khade ho, to tumhara khud ka kaam `theirs` ban jaata hai. Rebase mein tumhare commits **upar se** chipkaye jaate hain, to `HEAD` `main` ban jaata hai aur **tumhara commit** `theirs`. Label pe bharosa mat karo — **content padho**. Aur nikalne ka darwaza hamesha ek command door hai: `git merge --abort`.

### `git status` mid-conflict is your control panel

```
$ git status
On branch main
You have unmerged paths.
  (fix conflicts and run "git commit")
  (use "git merge --abort" to abort the merge)

Unmerged paths:
  (use "git add <file>..." to mark resolution)
	both modified:   svc/settlement.py
```

Two facts, free: **which operation you are inside and how to leave it**, and **every unresolved path**. `Unmerged paths` is your to-do list; when it empties, you are done. Run it after every resolution — the cheapest progress bar in software.

`--short` gives two-letter codes that each name a *kind* of conflict:

```
UU  both modified      the ordinary content conflict
AA  both added         each branch created the same path
UD  deleted by them    you edited it, they deleted it   (DU = the mirror)
```

The delete case has **no markers to read**, which trips people up:

```
CONFLICT (modify/delete): old.py deleted in feat/rm and modified in HEAD.
  Version HEAD of old.py left in tree.
	deleted by them: old.py
```

Git leaves your version on disk and asks a question no marker can express: *should this file exist at all?* Answer with a verb — `git rm old.py` to accept the deletion, `git add old.py` to keep it.

### `git diff` mid-conflict is a *combined* diff

Plain `git diff` switches mode: it shows the file against **both** parents at once (`diff --cc`), with **two** columns of `+`/`-`:

```
$ git diff
diff --cc svc/settlement.py
@@@ -1,4 -1,4 +1,8 @@@
  def settle(adda):
++<<<<<<< HEAD
 +    total = compute_total(adda, include_alter=True)
++=======
+     total = round(compute_total(adda), 2)
++>>>>>>> feat/rounding
      ledger_credit(adda.worker, total)
      return total
```

Column 1 = "differs from parent 1 (ours)", column 2 = "differs from parent 2 (theirs)". A line marked only in column 2 (` +`) came from **ours**. The markers show `++` because they are new to both. The only lines printed are the ones nobody agreed on.

One side at a time, which is far more readable:

```bash
git diff --base      # merged-so-far vs the merge BASE   ← usually the most useful
git diff --ours      # …vs our version
git diff --theirs    # …vs their version
git log --merge      # only the commits that touched the conflicted files
git log --merge -p   # …with patches: what each side intended
```

`git log --merge` is the underrated one:

```
$ git log --merge --oneline
00fae47 feat(expense): include alter pieces in total
c223912 fix(expense): round settlement total to 2dp
```

Two intentions, both legible — and it is instantly clear the right answer is **neither side alone**: you want alter pieces *and* rounding. Conventional Commit subjects ([Ch 25](25_Conventional_Commits.md)) pay for themselves right here.

### The missing third side: `--conflict=diff3`

Default markers hide the **base** — and the base is what tells you *what each side changed*.

```bash
git checkout --conflict=diff3 <file>              # re-mark, base included
git config --global merge.conflictStyle diff3     # make it the default forever
```

```
$ git checkout --conflict=diff3 svc/settlement.py
Recreated 1 merge conflict

<<<<<<< ours
    total = compute_total(adda, include_alter=True)
||||||| base
    total = compute_total(adda)
=======
    total = round(compute_total(adda), 2)
>>>>>>> theirs
```

Now read it as two *edits*: ours **added an argument**, theirs **wrapped the call in `round()`**. Neither touched the other's idea, so the resolution writes itself — `round(compute_total(adda, include_alter=True), 2)` — and you can see it is *correct*, not merely chosen. Without the base you would flip a coin.

Honest note: git here is **2.34.1**, and the nicer `zdiff3` style landed in **2.35**:

```
$ git checkout --conflict=zdiff3 svc/settlement.py
fatal: unknown style 'zdiff3' given for 'merge.conflictstyle'
```

Also: `git checkout -m <file>` (or `git restore --merge <file>`) **re-creates the markers** after you have mangled the file — the undo for "I edited it into nonsense", because stages 1/2/3 are still in the index.

### Resolving — three legitimate methods, and one that is not

**1. Edit the file.** The default, and the only honest option for logic. Delete the marker lines, write the version that is *correct* — frequently a combination, not a choice.

**2. Take one whole side**, when one side is genuinely right:

```
$ git checkout --ours f.txt  && cat f.txt     $ git checkout --theirs f.txt && cat f.txt
a                                            a
OURS                                         THEIRS
c                                            c
```

Two catches. It replaces the **whole file**, so any *other* already-auto-merged change from the far side goes with it. And it is silent. Right tool for a **regenerable** file, wrong tool for source. (`git restore --ours/--theirs` is the modern spelling.)

**3. Regenerate**, for machine-generated files: take either side to get something valid, re-run the generator, commit its output.

**Not legitimate:** `-X theirs` on a source file to make the red text go away. `-X ours`/`-X theirs` auto-resolve *conflicting hunks* toward one side and merge the rest normally:

```
$ git merge -X ours feat/gen
Merge made by the 'ort' strategy.
$ cat build.lock
gen: 2               ← our side won the conflicting hunk, no questions asked
```

Excellent for `build.lock`, quietly destructive on `settlement.py`. Do not confuse it with `-s ours` ([Ch 11](11_Merging.md)), which discards the *entire* other side.

### `git add` means "I have resolved this"

Mid-conflict, `git add <file>` does not mean "stage a change". It means **collapse stages 1/2/3 into one resolved entry**:

```
$ git status --short
UU f.txt                 ← unmerged
$ git add f.txt && git status --short
M  f.txt                 ← ordinary staged modification; the conflict is gone
```

Three consequences worth internalising:

- Git **does not check your work.** `git add` on a file still containing `<<<<<<<` marks it resolved. Only you and CI stand in the way.
- Until every path is added, the commit is refused: `error: Committing is not possible because you have unmerged files.`
- Finish with `git commit` or the clearer `git merge --continue` (identical). Git pre-writes `.git/MERGE_MSG` **listing what conflicted**:

```
Merge branch 'feat/x'

# Conflicts:
#	f.txt
```

Keep those lines. A future reader wants to know this file was hand-decided.

### The state on disk, and the exits

```
$ ls .git | grep -E 'MERGE|ORIG|AUTO'
AUTO_MERGE      the tree as auto-merged (ort, git ≥2.30)
MERGE_HEAD      the commit being merged → this is what "mid-merge" physically IS
MERGE_MODE
MERGE_MSG       the pre-written message with the # Conflicts: list
ORIG_HEAD       where you were → the target of reset --hard ORIG_HEAD
```

Real proof that retreat is free:

```
$ git status --short
UU f.txt
$ git merge --abort
$ git status --short              ← empty: clean tree
$ cat f.txt
a
OURS                              ← your pre-merge content, exactly
```

Memorise `git merge --abort` **before** you need it. A conflict is never a one-way door, and [Ch 16](16_Reflog.md) still holds every step if you abort and retry.

### Conflicts during a rebase — three words instead of two

A rebase conflicts *per replayed commit*, so it can stop repeatedly. Git prints exactly what it wants:

```
hint: Resolve all conflicts manually, mark them as resolved with
hint: "git add/rm <conflicted_files>", then run "git rebase --continue".
hint: You can instead skip this commit: run "git rebase --skip".
hint: To abort and get back to the state before "git rebase", run "git rebase --abort".
```

- **`--continue`** — after `git add`; replays the next commit. Repeat.
- **`--skip`** — **drops the commit being replayed, entirely.** Correct only when the upstream already contains that change. Data loss when used as an escape from a hard conflict. The dangerous word of the three.
- **`--abort`** — full retreat to the pre-rebase branch. Always available.

`git status` still names your position: `interactive rebase in progress; onto a19ddea` … `Last command done (1 command done): pick f324f40`. Same conflict grammar as a merge — markers, `git add`, one verb — with the labels inverted throughout. Details in [Ch 13](13_Rebase.md).

### `git rerere` — resolve it once, not five times

**rerere** = **re**use **re**corded **re**solution. Off by default. It records the pair *(conflict, your resolution)* and replays your fix when the identical conflict reappears — which is exactly what happens when a long branch is rebased repeatedly (this working branch is **296 commits** ahead of `main`).

```bash
git config --global rerere.enabled true      # record and reuse
git config --global rerere.autoupdate true   # ALSO stage the reused resolution
```

Resolve once, delete the merge, merge again:

```
$ git add f.txt && git commit --no-edit
Recorded resolution for 'f.txt'.
$ ls .git/rr-cache
a666aaaa5d6afc4a047a19c6a2bcd6a97e499023      ← one dir per conflict fingerprint

$ git reset --hard HEAD~1 && git merge feat/x
CONFLICT (content): Merge conflict in f.txt
Resolved 'f.txt' using previous resolution.

$ cat f.txt
OURS+THEIRS            ← my earlier hand-written resolution, replayed
$ git status --short
UU f.txt               ← STILL unmerged: rerere fixed the TEXT, not the STATE
```

Two details that catch people. It **still reports CONFLICT** and the path is **still `UU`** — you must inspect and `git add`, unless you set `rerere.autoupdate true`. That default is deliberate: a replayed resolution is a guess about *your* intent. And it is **local and unshared** — `.git/rr-cache/` is never pushed.

Housekeeping: `git rerere status`, `git rerere diff`, `git rerere forget <path>` (unlearn a wrong fix), `git rerere gc`.

**Honest state here:** `rerere.enabled` is **not set** — not locally, not globally — and `.git/rr-cache/` does not exist. Same for `merge.conflictStyle`. Two one-line, no-risk, high-value config changes recommended back in [Ch 02](02_Install_And_Configure.md) and still unapplied. Also, `git mergetool --tool-help` reports `No suitable tool … found` on this machine: no GUI merge tool, so every resolution here is editor-based.

### `.gitattributes` and merge drivers, briefly

A **merge driver** is a per-path rule for *how* git merges a file. It lives in `.gitattributes`, which is **committed** — so the rule travels with the repo, unlike config.

```gitattributes
CHANGELOG.md   merge=union      keep BOTH sides' lines instead of conflicting
*.lock         -merge           never text-merge; always conflict → regenerate
docs/**        text eol=lf      normalise line endings (the other conflict cause)
```

`merge=union` earns its keep on append-at-the-end files — a CHANGELOG, an `INSTALLED_APPS` list, a `urls.py` — which conflict on the last line every time two branches add an entry. Real proof:

```
$ cat .gitattributes
CHANGELOG.md merge=union
$ git merge feat/u && cat CHANGELOG.md
# Changelog
- feature B          ← ours
- feature A          ← theirs, kept too. No conflict, no editing.
```

The catch: union merge is **dumb**. It never conflicts, so it will happily produce a duplicated or out-of-order list, and on a source file it would emit code that does not compile. Append-only text only, never logic. **This repo has no `.gitattributes` at all** — `git ls-files | grep gitattributes` returns nothing. One with `text eol=lf` would be a cheap addition before a second developer on Windows ever clones.

### Why migration files and lock files conflict constantly

Conflict frequency scales with **how much of a file each edit rewrites** and **how many branches touch it**. Two classes lose on both counts.

**Django migrations — the conflict that is not a git conflict.** Two branches each run `makemigrations`, each takes the next number, both depend on the same parent. This repo's `production` app has **52** migrations, so both branches produce `0053_…`. If the filenames differ, git sees **two unrelated new files** and merges with **zero conflicts**. Both land. The damage appears one layer up — Django's graph now has **two leaf nodes** and refuses to run. Real error, reproduced on Django 5.0.1 with the venv in `env/`:

```
$ python manage.py makemigrations --check --dry-run
CommandError: Conflicting migrations detected; multiple leaf nodes in the
migration graph: (0002_adda_is_active, 0002_adda_notes in shop).
To fix them run 'python manage.py makemigrations --merge'
```

Two fixes, and the choice matters. `makemigrations --merge` writes a **merge migration** depending on both leaves — correct, honest, permanent extra file. Better while the branch is still yours: **rebase onto `main`, delete your migration, re-run `makemigrations`** so it renumbers on top of theirs and the graph stays linear. There are **162** tracked migration files across 10 apps; keeping that linear is worth a minute.

**Lock files — never hand-merge.** The two tracked here are `Django_app/myproject/package-lock.json` and `theme/static_src/package-lock.json`. A lock file is a *generated* dependency graph: adding one package rewrites hundreds of nested lines, so two branches produce an enormous overlapping conflict, and hand-editing yields a file that parses and lies. Fixed procedure:

```bash
git checkout --theirs package-lock.json    # or --ours; you just need something valid
npm install                                 # regenerate from package.json — the real source
git add package-lock.json
```

**The generalisation:** if a file has a **generator**, re-run the generator. If it is **append-only prose**, give it `merge=union`. If it holds **logic**, read the base with `diff3` and resolve by hand. Python-side this project is lucky: `requirements.txt` is hand-pinned line by line, so its conflicts are small and readable — a real argument for hand-pinning over a giant lock file on a small team.

### Semantic conflicts — clean merge, broken runtime

The most dangerous conflict is the one git never reports.

- **Branch A** renames `WorkerStageContribution.reported_quantity` to `good` and updates all its callers.
- **Branch B** adds a *new* caller reading `reported_quantity`.

No overlapping lines, so nothing to conflict. Git merges cleanly, both branches were green, and `main` now calls a field that no longer exists — failing at **runtime**, on a money report, in front of a user. That is a **semantic conflict**: textually compatible, logically contradictory. And it is not hypothetical here: that rename is real staged foundation work (`reported_quantity` renamed-not-dropped, retirement deferred precisely so both spellings coexist during the transition).

There is one defence, and it is not code review:

- **Tests, run on the merged result** — not on your branch, not on `main`, on the **merge**. The battery is **2033 tests across 14 apps, one command, sequential on a fresh DB, ~424 s**, and the golden totals ₹344.25 / ₹801 / ₹633 / ₹225 are byte-identical assertions. A wrongly-resolved money line fails a **number**, which no reviewer can rationalise away.
- **The corollary this project already paid for:** a test outside the gate defends nothing. The app `bod` (37 tests) was in `INSTALLED_APPS` but in **no test group** — outside the gate through two baselines, red, hiding a real UTC/IST money bug. Hence `.github/workflows/ci.yml` names all 14 apps explicitly, and the invariant is written down: *"battery == discovery"*.

# Real World Example (this repo)

Every conflict-adjacent fact, measured today:

```
$ git --version
git version 2.34.1

$ git config --get rerere.enabled        (no output — UNSET, local and global)
$ ls .git/rr-cache
ls: cannot access '/home/tech/umesh-personal/.git/rr-cache': No such file or directory

$ git ls-files | grep -i gitattributes   (no output — none exists)

$ git rev-list --left-right --count main...new_flask_app
0	296
```

Read together that is a small, honest risk profile: a **296-commit** divergence is the biggest conflict generator in the repo, and the two cheapest mitigations — `rerere.enabled` and `merge.conflictStyle diff3` — are both unconfigured. Nothing is broken; two lines of config are simply unpaid for.

**Why conflicts have been rare, and why that ends soon.** Fifteen PRs, all merged by the merge button, all titled `Merge pull request #N from umesh29032/new_flask_app` — one author, one long branch, no parallel work. One author cannot disagree with themselves in the same hunk. The moment a second developer works from a fork ([Ch 20](20_Forks_And_The_Fork_Flow.md)), `config/production/migrations/` (**52** files, latest `0052_workerstageallocation_allocation_mode.py`) is the first battleground, and CI's `migrations` job — `makemigrations --check --dry-run` — is what catches it.

**And one thing the history proves by omission:** no merge on this trunk carries a `# Conflicts:` block, because they were all made by GitHub's merge button. So **nothing here was ever hand-resolved.** The first time it happens, the commit message must say so.

# Visual Diagram
```
  WHY A CONFLICT HAPPENS                   base = the commit both sides started from

        base:  total = compute_total(adda)
                 ╱                    ╲
     OURS (main)                        THEIRS (feat/rounding)
     …(adda, include_alter=True)         …round(compute_total(adda), 2)
                 ╲                    ╱
                  SAME REGION, BOTH CHANGED → git refuses to pick → CONFLICT

  WHAT THE INDEX HOLDS (git ls-files -u)     WHAT YOUR FILE HOLDS
    stage 1  BASE    ← git show :1:file       <<<<<<< HEAD    7 chars, column 0
    stage 2  OURS    ← git show :2:file           OURS   (stage 2, top)
    stage 3  THEIRS  ← git show :3:file       =======
                                                  THEIRS (stage 3, bottom)
    git add → collapses 3 stages into 1       >>>>>>> feat/rounding
                                              (--conflict=diff3 adds ||||||| base)

  OURS/THEIRS FLIP — the classic trap
    merge feat/x  while on main     ours = main    theirs = YOUR work
    rebase main   while on feat/x   ours = MAIN    theirs = YOUR commit  ← inverted!
    cherry-pick / stash pop         ours = current theirs = incoming
    ⇒ read CONTENT, never the label. `-X ours` in a rebase discards YOUR side.

  THE LOOP                                 THE EXITS
    git status      ← what is unresolved     git merge  --abort
    git diff --base ← what each side did     git rebase --abort
    edit / --ours / --theirs / regenerate    git reset --hard ORIG_HEAD
    git diff --check ← no markers left?      git checkout --conflict=diff3 <f>
    git add <file>  ← "resolved"                (restart ONE file, keep going)
    repeat until status is empty
    git merge --continue | git rebase --continue | --skip (DROPS a commit!)

  WHAT GIT CANNOT SEE
    renamed field + new caller on the other branch = CLEAN MERGE, broken runtime.
    Only the battery (2033 tests, ~424 s, golden ₹ totals) catches that.
```

# Practical — resolve one for real, then abort one

Build the conflict in a throwaway repo. All of this is real and safe:

```bash
mkdir -p /tmp/conflab && cd /tmp/conflab && git init -q -b main
git config user.email t@t && git config user.name t && mkdir -p svc
printf 'def settle(adda):\n    total = compute_total(adda)\n    return total\n' > svc/settlement.py
git add -A && git commit -q -m "feat: settle"

git switch -qc feat/rounding
printf 'def settle(adda):\n    total = round(compute_total(adda), 2)\n    return total\n' > svc/settlement.py
git commit -qam "fix(expense): round settlement total to 2dp"

git switch -q main
printf 'def settle(adda):\n    total = compute_total(adda, include_alter=True)\n    return total\n' > svc/settlement.py
git commit -qam "feat(expense): include alter pieces in total"

git merge feat/rounding
```
Expected — read it as good news, not failure:
```
Auto-merging svc/settlement.py
CONFLICT (content): Merge conflict in svc/settlement.py
Automatic merge failed; fix conflicts and then commit the result.
```
Investigate **before** touching the file. Four read-only commands:
```bash
git status --short                                 # UU svc/settlement.py
git ls-files -u                                    # stages 1, 2, 3 of that path
git log --merge --oneline                          # the two commits that disagreed
git checkout --conflict=diff3 svc/settlement.py    # add the ||||||| base section
```
Resolve as a *combination*, because `git log --merge` showed two compatible intentions:
```bash
printf 'def settle(adda):\n    total = round(compute_total(adda, include_alter=True), 2)\n    return total\n' > svc/settlement.py
git diff --check            # the guard: silent means no markers survived
git add svc/settlement.py
git status --short           # M  svc/settlement.py   ← was UU
git merge --continue         # keeps the "# Conflicts:" list in the message
```
Prove the guard works, because one day you will need it:
```bash
printf 'a\n<<<<<<< HEAD\nb\n=======\nc\n>>>>>>> feat/x\n' > f.txt && git add f.txt
git diff --cached --check
```
```
f.txt:2: leftover conflict marker
f.txt:4: leftover conflict marker
f.txt:6: leftover conflict marker
```
Now rehearse the retreat until it is boring:
```bash
git reset --hard HEAD~1     # throw away the merge you just made
git merge feat/rounding     # conflict again
git merge --abort           # cancel
git status --short          # empty. Nothing lost. This is the muscle memory.
```
Finally, apply the two settings this repo still lacks:
```bash
git config --global merge.conflictStyle diff3    # always show me the base
git config --global rerere.enabled true          # remember my resolutions
```

# Production Walkthrough
1. **Prevent, don't resolve.** Conflicts scale with divergence. `git fetch origin && git rebase origin/main` daily (`CONTRIBUTING.md` §10: *no merge commits on feature branches*) means one small conflict at a time instead of a **296-commit** cliff. Small PRs are a conflict strategy, not just a review preference — §5 says a 200-line PR gets a real review and a 2,000-line PR gets "LGTM".
2. **When it stops, read before typing.** `git status` (paths + operation), `git log --merge` (the two intentions), `git diff --base` (what each side changed). Thirty seconds, zero risk.
3. **Classify the file first.** Generated (`package-lock.json`) → regenerate. Append-only (`CHANGELOG.md`) → both lines. Migration → renumber or `--merge`. Logic (`services/*.py`) → read the base, resolve by hand. **Money path** (settlement, ledger, earning, rate) → resolve, then re-read it as a stranger's patch: §5 calls a new money-write path outside an approved service a **STOP**, and a careless resolution is exactly how one appears.
4. **Mark resolved deliberately.** `git diff --check` before every `git add`, then `git status` again. Empty `Unmerged paths` means done.
5. **Say what you decided.** Keep the `# Conflicts:` block, and add a line on *why* if the call was non-obvious. Six months later that sentence is the only evidence a decision was made rather than stumbled into.
6. **Let CI judge the merged state.** `.github/workflows/ci.yml` runs `lint`, `migrations` (the two-leaf catcher), `test` (`needs: [lint, migrations]`) and `docs` (`knowledge_sync` BLOCKER=0). Green on both branches proves nothing about the merge.
7. **Re-verify the trunk after landing:** 2033 tests, 14 apps, ~424 s, sequential on a fresh DB — never `--parallel`, never `--keepdb`, because it asserts exact money totals.
8. **Docs-sync, same session** (`CLAUDE.md` rule 12). Merges are where doc updates get dropped, because a conflicting doc paragraph is the thing people delete to move on.

# Debugging Guide

| Symptom | Cause | Fix |
|---|---|---|
| `CONFLICT (content)` | same region changed both sides | `git diff --base`, edit, `git add`, `git merge --continue` |
| `CONFLICT (add/add)` · `AA` | both branches created the same path | Merge the two files by hand into one, then `git add` |
| `CONFLICT (modify/delete)` · `UD` | you edited it, they deleted it | Decide existence: `git rm <f>` or `git add <f>` |
| `Committing is not possible because you have unmerged files` | a path is still at stage 1/2/3 | `git status` lists them; add or rm each, then commit |
| `You have not concluded your merge (MERGE_HEAD exists)` | merge abandoned half-done | Finish it, or `git merge --abort` |
| Markers committed and shipped | `git add` never validates content | `git diff --check` before adding; `git grep -n '^<<<<<<<'` to sweep |
| Resolution looks right, money tests fail | you kept one side, dropped the other's intent | `git show :2:<f>` and `:3:<f>`, re-resolve as a combination |
| I edited the file into nonsense | markers gone, stages 1/2/3 intact | `git checkout -m <f>` or `--conflict=diff3 <f>` |
| `--ours` gave me the *upstream's* code | you are in a **rebase**; labels are inverted | Read content, not labels; `git status` names the operation |
| Same conflict on every rebase attempt | each replayed commit re-hits the hunk | `rerere.enabled true`; or squash first ([Ch 14](14_Interactive_Rebase.md)) |
| rerere replayed my fix but status is `UU` | it resolves the file, not the index state | Inspect then `git add`, or set `rerere.autoupdate true` |
| rerere keeps replaying a **wrong** fix | a bad resolution is cached in `.git/rr-cache/` | `git rerere forget <path>`, then resolve correctly |
| `fatal: unknown style 'zdiff3'` | needs git ≥ 2.35; this machine is 2.34.1 | Use `diff3`, or upgrade git |
| `Conflicting migrations detected; multiple leaf nodes` | both branches added a migration on one parent | Rebase and renumber yours, or `makemigrations --merge` |
| `package-lock.json` conflict, thousands of lines | generated file, overlapping rewrites | `git checkout --theirs`, `npm install`, `git add`. Never hand-edit |
| Whole-file changes vanished after `--ours` | it replaces the **entire file**, not the hunk | `git checkout -m <f>` to restore stages, redo properly |
| Merged clean, broke at runtime | **semantic** conflict — git merges text, not meaning | Only tests on the merged state catch it |
| Every file conflicts on every line | CRLF vs LF line endings | `.gitattributes` with `text eol=lf`; inspect with `--ignore-all-space` |

# Performance Notes
- **Conflict detection is free** — the same three-way tree comparison a clean merge does (`ort`, default since 2.34, over 2,407 tracked files). The cost of a conflict is entirely **human**.
- **Cost scales with divergence, not repo size.** One day of drift is a one-line decision; the **296-commit** gap here is a session. `git rev-list --left-right --count main...HEAD` is the cheapest risk metric you own.
- **rerere makes repeats ~0 s.** Rebasing a 20-commit branch that hits the same hunk each time is the pathological case; one cached resolution kills it. This repo has no `rr-cache`, so it pays that cost in full.
- **`diff3` costs nothing and saves minutes** — it removes the guesswork that produces a wrong resolution, and a wrong resolution costs a **~424 s** battery run to discover.
- **Verification dominates the budget.** Locally ~424 s; in CI ~7 minutes, and a private repo's ~2,000 free Actions minutes/month is roughly 280 runs. `concurrency` in `ci.yml` cancels superseded runs so a resolve-push-resolve-push loop does not burn the month.
- **Never `--parallel`/`--keepdb` to speed up a post-resolution run.** The suite asserts exact money totals on a fresh sequential DB; a faster run with different semantics is not a verification.

# Security Considerations
- **`git add` does not validate.** A resolution can commit `<<<<<<< HEAD` into a settings file or a workflow YAML. Make `git diff --check` reflexive and sweep with `git grep -n '^<<<<<<<'` before pushing.
- **A conflict resolution is the perfect place to hide a change.** The diff is already noisy and attention is on "did the merge work", not "what landed". Review your own resolution with `git diff <base> -- <file>`, and treat someone else's resolution commit like any other code.
- **Money paths are the high-value target.** `CLAUDE.md` rule 4 (services own multi-row writes), rule 5 (one writer per ledger/audit table) and rule 6 (permissions via `permission_service`) are exactly what a "keep both sides" resolution breaks — two writers where each branch had one.
- **A permission fix can be un-fixed by resolution.** If one branch tightened a gate and the other refactored around it, `--ours`/`--theirs` can restore the pre-fix version with no diff noise anywhere.
- **Secrets ride in on `--theirs`.** Taking a whole file from an incoming branch can bring a hard-coded key with it ([Ch 33](33_Secrets_And_Leaks.md)).
- **`.gitattributes` is executable policy.** `merge=<driver>` points at a command via config; a committed `.gitattributes` arriving in a fork's PR is a file to actually read, alongside `.github/workflows/*`.
- **`rerere` caches decisions you may regret.** `.git/rr-cache/` is local and unreviewable; a wrong fix replays silently forever until `git rerere forget`.
- **`git rebase --skip` is silent data loss.** It drops the commit being replayed. Never as an escape from a hard conflict.

# Architecture Decisions
- **Rebase feature branches, squash-merge into `main`** (`CONTRIBUTING.md` §10 and §5). Conflicts get resolved *on the branch*, by the author, before review — never on the trunk by whoever pressed merge. Accepted cost: rebasing rewrites commit IDs, so `--force-with-lease` is required.
- **Small PRs as the primary conflict control** (§5: 200 lines gets a real review). Cheaper than any tooling.
- **CI's `migrations` job exists because migration conflicts are invisible to git.** `makemigrations --check --dry-run` turns a two-leaf graph — which merges with zero conflicts — into a red build, and it runs *before* `test` so the cheap check fails fast.
- **Hand-pinned `requirements.txt` over a lock file** on the Python side: a line-per-package file conflicts small and readable, while the two tracked `package-lock.json` files demonstrate the alternative — regenerate-only, never hand-merge.
- **Tests are the semantic-conflict defence, not review.** Byte-identical golden totals mean a wrong money resolution fails a number. After the `bod` incident — 37 tests in `INSTALLED_APPS` but no test group, red and unseen through two baselines — CI names all **14** apps explicitly.
- **Rejected: a merge driver for migrations.** Tempting and wrong: the correct resolution is a renumber or an explicit merge migration, both needing judgement about dependency order that automation would hide.
- **Rejected: `-X theirs` as a default policy.** It would make merges never stop — by silently deleting one side's work. Reserved for genuinely regenerable files.
- **Not yet decided, honestly:** no `.gitattributes` exists (no `eol=lf`, no `merge=union`), and `rerere.enabled` and `merge.conflictStyle` are unset. Three cheap wins recorded here rather than pretended away.

# Best Practices
- Rebase onto `origin/main` **daily** on a live branch. Divergence is the raw material of conflicts.
- Set `merge.conflictStyle diff3` and `rerere.enabled true` once, globally, then forget them.
- Read before you edit: `git status`, `git log --merge`, `git diff --base`.
- Resolve by **content**, never by the words `ours`/`theirs` — they invert under rebase.
- Prefer a **combination** over a choice; two commits usually had two compatible intentions.
- `git diff --check` before every `git add`. Never ship a marker.
- Classify the file first: generated → regenerate · append-only → `merge=union` · logic → hand-resolve · money → hand-resolve **and** re-review.
- Use `git show :1:` / `:2:` / `:3:` when markers are hard to read. Three clean files beat one messy one.
- Keep the `# Conflicts:` block in the merge message, plus a line on *why* if the call was non-obvious.
- Run the tests on the **merged** state. Green on both sides proves nothing about the middle.
- When lost, `--abort`. Retreating is free; guessing is not.

# Beginner Mistakes
- **Thinking a conflict means the repo is broken** → it is a paused operation with both answers on screen. `git status` names the operation and its exit.
- **Assuming `theirs` is "the other person's code"** → `theirs` is whatever is being applied to you. After `git switch main && git merge feat/x`, *your own* work is `theirs`.
- **Using `-X ours` during a rebase to "keep my code"** → it keeps the **upstream** and discards yours. The most expensive single mistake in this chapter.
- **Deleting one side to make the red go away** → you just reverted a colleague's fix with a clean diff and no trace. Read `git log --merge` first.
- **Committing the markers** → `git add` never validates. `git diff --check` costs nothing.
- **Expecting `git checkout --ours <file>` to affect only the conflicted hunk** → it replaces the **whole file**, discarding the far side's already-merged changes in it.
- **Hand-editing `package-lock.json`** → produces a file that parses and lies. Take a side, re-run the generator, add.
- **Using `git rebase --skip` to escape a hard conflict** → it silently drops the commit you were replaying. `--abort` is the safe exit.
- **Running `makemigrations` again after a migration conflict without rebasing** → you get a *third* leaf. Rebase and renumber, or `--merge`.
- **Believing a clean merge means a correct merge** → semantic conflicts merge perfectly and fail at runtime.
- **Thinking rerere finished the job** → after `Resolved '<f>' using previous resolution.` the path is still `UU`. Inspect, then `git add`.
- **Resolving on the trunk instead of on the branch** → a broken `main` blocks everyone.

# Interview Questions
- **Junior:** "What is a merge conflict, and what do the `<<<<<<<` markers mean?" — Git telling me both sides changed the same region of a file differently, so it will not choose for me. It writes both versions in: above `=======` is `ours` (HEAD, where I am standing), below is `theirs` (what I am merging in), and the `>>>>>>>` line labels that side. It is not an error and nothing is lost — I edit the file to the correct version, `git add` it to mark it resolved, and finish with `git merge --continue`. If I want out, `git merge --abort` puts me back exactly where I was.

- **Mid:** "During a rebase you run `git checkout --ours <file>` and get your teammate's code. Explain." — Because a rebase replays *my* commits on top of the upstream, so at each step the thing I stand on is the copy of the upstream and the patch being applied is my own commit. `ours` therefore means the upstream and `theirs` means my work — inverted from a merge. That is why I never resolve by the labels: I read content, or use `git show :2:<file>` and `:3:<file>` to get each side as a clean file, or `git log --merge` for the two commits' intentions. `git status` also names which operation I am inside, which is the tell.

- **Senior:** "Your team hits the same conflict on every rebase of a long branch, and lock files conflict constantly. Fix both, structurally." — Three moves. Remove the cause first: rebase daily and keep PRs small, because conflict volume tracks divergence, not repo size — a 296-commit gap is a session of resolution, a one-day gap is a line. Second, `rerere.enabled true` so a repeating conflict is resolved once and replayed, plus `merge.conflictStyle diff3` so every conflict shows the base and I can see *what each side changed* rather than guessing between two lines. Third, encode policy per file class in a committed `.gitattributes`: generated files like `package-lock.json` are never hand-merged — take either side and re-run the generator, since `package.json` is the real source; append-only prose gets `merge=union`; logic stays hand-resolved. What I would *not* do is add a merge driver for Django migrations, because the correct fix is renumbering or an explicit merge migration, and both need judgement about dependency order that automation would hide.

- **Staff:** "A merge resolved cleanly, CI was green on both branches, and settlement paid the wrong amount in production. Explain how, and design the prevention." — That is a semantic conflict, git's structural blind spot: it merges text regions, not meaning. Branch A renames a field and updates its callers; branch B adds a new caller using the old name. No overlapping lines, clean merge, broken runtime — and a money bug specifically, because each branch held a self-consistent view of the same model. The softer version: someone resolved a hunk with `--theirs` and dropped the other side's rounding, which is syntactically perfect and financially wrong. Prevention is four layers, none of them code review. One, test the **merge**, not the branches — a green branch describes a state that will never ship. Two, make assertions numeric and exact: the golden settlement totals ₹344.25 / ₹801 / ₹633 / ₹225 are byte-identical, so a wrong resolution fails a number instead of a reviewer's attention, and the suite runs sequentially on a fresh DB precisely so those totals mean something. Three, guarantee the gate is complete — `bod` had 37 tests in `INSTALLED_APPS` but in no test group, so it sat outside the gate through two baselines while red, hiding a real UTC/IST money bug; the fix was naming all 14 apps explicitly in CI and adopting "battery == discovery" as an invariant, because a test outside the gate defends nothing. Four, shrink the exposure structurally: rebase-and-squash so conflicts are resolved on the branch by the author, keep PRs small enough to genuinely review, and treat any resolution touching a ledger, settlement, earning or rate as STOP-class, since single-writer discipline is exactly what "keep both sides" breaks. And I would state the residue honestly: mechanically blocking merge-on-red is paid on private repos here, so the free composition is collaborators on Read access working from forks plus CI as the visible gate.

### Why interviewers ask these — and the answer that separates levels

| Testing for | Weak answer | What lands |
|---|---|---|
| Do you fear conflicts or read them? | "I delete the arrows and pick the one that looks right." | "It is a question, not an error. `git log --merge` for both intentions, `--conflict=diff3` for the base, then usually resolve to a **combination** — and `--abort` is always there." |
| Do you actually understand ours/theirs? | "Ours is my code, theirs is theirs." | "`ours` is where I stand; the labels **invert** under rebase because my commits are the thing being applied. So I read content, or `git show :2:` and `:3:` as clean files." |
| Do you know git's blind spot? | "If it merges cleanly, it is fine." | "Semantic conflicts merge perfectly and break at runtime — renamed field plus new caller. Tests on the **merged** state are the only defence, with exact numeric money assertions." |
| Do you fix causes or symptoms? | "I resolve them as they come." | "Conflict volume tracks divergence: rebase daily, keep PRs small, `rerere` for repeats, `.gitattributes` policy per file class — regenerate lock files, union-merge append-only prose." |

**The killer follow-up:** *"Which is more dangerous — a conflict, or a merge that resolved cleanly?"* — The clean one, every time. A conflict is git refusing to guess, so a human necessarily looks; the risk is bounded and visible. A clean merge asserts only that no two text regions overlapped, which is a far weaker claim than "the result is correct" — two individually-valid changes can compose into a broken whole with no marker, no warning, and green on both sides. That is why the gate is tests on the merged state, and why "it merged cleanly" is never an argument in a review.

# Revision Notes
- A conflict is a **question**, not an error: same region, both sides changed, git refuses to guess. Nothing is lost.
- Markers: **7 chars at column 0**. Above `=======` is **ours** (HEAD), below is **theirs**. Both are plain text in your file.
- The index holds **three stages**: 1 = base, 2 = ours, 3 = theirs. Read them with `git show :1:` / `:2:` / `:3:`.
- **`git add` = "resolved"** — it collapses the three stages into one. It does **not** check your work.
- **`ours` = where you stand.** Merge: your branch. **Rebase: `ours` = the upstream, `theirs` = your own commit.** Read content, never labels.
- `git status` mid-conflict names the operation, its exit, and every unresolved path. Empty list = done. `UU` / `AA` / `UD` are the kinds.
- `git diff` becomes a **combined diff** (`diff --cc`, two `+`/`-` columns). `--base` / `--ours` / `--theirs` are the readable views.
- **`--conflict=diff3` adds the base** (`||||||| base`) and usually makes the answer obvious. `zdiff3` needs git ≥ 2.35; this machine is 2.34.1.
- `git checkout --ours/--theirs <file>` takes the **whole file**, not the hunk. Generated files only.
- Exits: `git merge --abort` · `git rebase --abort` · `git reset --hard ORIG_HEAD` · restart one file with `git checkout -m <f>`.
- Rebase verbs: `--continue` (after add) · `--skip` (**drops the commit** — data loss) · `--abort` (safe).
- **rerere** records and replays a resolution, but still leaves the path `UU` unless `rerere.autoupdate true`. Local only; unset here.
- `.gitattributes`: `merge=union` for append-only text, `-merge` for lock files, `text eol=lf` for line endings. **This repo has none.**
- Migrations conflict **without a git conflict** — two leaves: `Conflicting migrations detected; multiple leaf nodes`. Rebase and renumber, or `--merge`. CI catches it.
- Lock files: take a side, **re-run the generator**, add. Never hand-merge.
- **Semantic conflicts merge cleanly and break at runtime.** Tests on the merged state are the only defence — and `bod` proved a test outside the gate defends nothing.

# Cheat Sheet

**See what happened**
```bash
git status                     ## which operation, which paths, how to exit
git status --short             ## UU both modified · AA both added · UD deleted by them
git ls-files -u                ## the three stages of every unmerged path
git show :1:<file>             ## BASE, clean (":2:" = ours, ":3:" = theirs)
git log --merge                ## only commits that touched the conflicted files
git log --merge -p             ## …with patches: what each side intended
git diff                       ## combined diff (diff --cc) — TWO +/- columns
git diff --base                ## merged-so-far vs the merge base  <- most useful
git diff --ours / --theirs     ## one side at a time
```

**Show the base inside the file**
```bash
git checkout --conflict=diff3 <file>            ## re-mark WITH ||||||| base
git config --global merge.conflictStyle diff3   ## make that the default
git checkout -m <file>                          ## re-create markers after mangling
git restore --merge <file>                      ## same, modern spelling
```

**Resolve**
```bash
$EDITOR <file>                 ## remove markers, write the CORRECT (often combined) version
git checkout --ours <file>     ## take OUR whole file   (generated files only)
git checkout --theirs <file>   ## take THEIR whole file (generated files only)
git rm <file>                  ## accept a deletion (modify/delete conflict)
git diff --check               ## ALWAYS: prints "leftover conflict marker" if you slipped
git add <file>                 ## "I have resolved this" — collapses stages 1/2/3
```

**Finish or retreat**
```bash
git merge --continue           ## = git commit; keeps the "Conflicts:" list
git merge --abort              ## cancel the merge, exactly back to before
git reset --hard ORIG_HEAD     ## blunter equivalent (also discards local edits)
git rebase --continue          ## after git add — replay the next commit
git rebase --skip              ## DROPS the commit being replayed
git rebase --abort             ## cancel the whole rebase
```

**Automate the repeats**
```bash
git config --global rerere.enabled true      ## record + replay resolutions
git config --global rerere.autoupdate true   ## …and stage them automatically
git rerere status / diff                     ## what it is tracking right now
git rerere forget <path>                     ## unlearn a wrong resolution
git merge -X ours   feat/x                   ## prefer OUR hunks   (generated files)
git merge -X theirs feat/x                   ## prefer THEIR hunks (generated files)
```

**Policy per file, in a committed `.gitattributes`** — `CHANGELOG.md merge=union` keeps both sides' lines (append-only prose only) · `*.lock -merge` never text-merges, forcing a regenerate · `docs/** text eol=lf` stops CRLF/LF whole-file conflicts.

**Sweep before pushing**
```bash
git grep -n -E '^(<<<<<<<|=======|>>>>>>>)'    ## markers anywhere in the tree
git rev-list --left-right --count main...HEAD  ## divergence = your conflict risk
```

# My ERP Section

| Conflict fact | In this repo, measured 2026-08-03 |
|---|---|
| git version | **2.34.1** — `--conflict=diff3` works; `zdiff3` fails with `unknown style 'zdiff3'` |
| `rerere.enabled` | **unset** (local and global); `.git/rr-cache/` does not exist |
| `merge.conflictStyle` | **unset** — default style, base hidden. One line to fix, still unpaid |
| `.gitattributes` | **none exist** — no `eol=lf`, no `merge=union` anywhere |
| GUI merge tool | none: `git mergetool --tool-help` reports `No suitable tool … found` |
| Divergence = risk | `git rev-list --left-right --count main...new_flask_app` → `0  296` |
| Repo size | 2,407 tracked files; `.git` is 97 MB |
| Migration pressure | **162** tracked migration files; `production` alone has **52**, latest `0052_workerstageallocation_allocation_mode.py` — two branches would both make `0053_…` |
| Migration catcher | `ci.yml` job `migrations` → `makemigrations --check --dry-run`, runs before `test` |
| Real Django error (5.0.1) | `CommandError: Conflicting migrations detected; multiple leaf nodes in the migration graph` |
| Lock files to regenerate | `Django_app/myproject/package-lock.json` · `theme/static_src/package-lock.json` |
| Python side, deliberately | hand-pinned `requirements.txt` + `requirements-dev.txt` — small readable conflicts by design |
| Semantic-conflict defence | 2033 tests · 14 apps · one command · ~424 s · sequential fresh DB · goldens ₹344.25 / ₹801 / ₹633 / ₹225 |
| Why CI names all 14 apps | `bod` (37 tests) was in `INSTALLED_APPS` but no test group — red and unseen through two baselines. *"battery == discovery"* |
| Money rule a bad fix breaks | `CLAUDE.md` rule 5 — single writer per ledger/audit table; settlement is the **only** money-write boundary |
| Policy preventing trunk conflicts | `CONTRIBUTING.md` §10 rebase feature branches, no merge commits · §5 squash-merge, keep PRs small |
| Conflicts hand-resolved so far | **zero** — 15 merge-button merges, one author, no `# Conflicts:` block in any message |

# Practice Tasks
1. **Build one and read it.** Run the Practical block. Before editing, run `git ls-files -u` and `git show :1:`, `:2:`, `:3:`. Write down which stage is the base and how you know.
2. **Add the base.** Run `git checkout --conflict=diff3` on that file and state in one sentence each what *ours* changed and what *theirs* changed. Then resolve to a combination, not a choice.
3. **Prove `git add` does not validate.** Leave a `<<<<<<<` line in, add, commit. Then find it with `git diff --check` and `git grep -n '^<<<<<<<'`. This is why the guard is a habit.
4. **Feel the flip.** Cause the *same* conflict twice — once with `git merge`, once with `git rebase`. Note which side `HEAD` is each time, then predict what `-X ours` would do in each case *before* running it.
5. **Rehearse the retreat three times:** `git merge --abort`, `git rebase --abort`, `git reset --hard ORIG_HEAD`. Confirm with `git status` each time. Aim for boredom.
6. **Turn on rerere and prove it.** Enable it, resolve a conflict, `git reset --hard HEAD~1`, re-merge. Confirm you see `Resolved '<file>' using previous resolution.` **and** that `git status --short` still says `UU`. Then `git rerere forget` it.
7. **Union-merge a CHANGELOG.** Add `CHANGELOG.md merge=union` to `.gitattributes`, add a different entry on two branches, merge, confirm both survive. Then explain in one sentence why that rule would be dangerous on a `.py` file.
8. **Reproduce the migration trap.** In a scratch Django project make two migrations both depending on `0001_initial`, run `makemigrations --check --dry-run`, read the error. Fix it once with `--merge` and once by renumbering; say which you would use on an unpushed branch.

# Homework
- Set `merge.conflictStyle diff3` and `rerere.enabled true` globally, then write two sentences on what each changes about the *next* conflict you hit. These are the two settings this repo measurably lacks.
- Design the `.gitattributes` this monorepo should have. Justify every line — which paths get `text eol=lf`, whether `CHANGELOG.md` gets `merge=union`, what the two `package-lock.json` files should be marked. Then argue *against* a merge driver for `config/*/migrations/`.
- Construct a **semantic conflict** on paper: name a real model field, a branch that renames it, and a second change that adds a caller of the old name. Then name the test that would fail, and why review would not have caught it.
- Take the `bod` lesson seriously: check that every installed app is named in `.github/workflows/ci.yml`. Write down what "battery == discovery" costs you if it is ever false again.
- Read `CONTRIBUTING.md` §5 and §10, then state the project's conflict policy in three sentences: where conflicts are resolved, who resolves them, and what proves the resolution was correct.
- Measure your own risk daily for a week: `git rev-list --left-right --count origin/main...HEAD`. Decide what number is your personal "rebase now" threshold.

---

# Further Reading & Live Resources
- `git merge` — `--abort`, `--continue`, `-X ours/theirs`, and how conflicts are presented: https://git-scm.com/docs/git-merge
- Pro Git, *Advanced Merging* — the canonical walkthrough of markers, `--ours/--theirs` and `rerere`: https://git-scm.com/book/en/v2/Git-Tools-Advanced-Merging
- `git rerere` — reuse recorded resolution, including `forget` and `gc`: https://git-scm.com/docs/git-rerere
- `git checkout` — `--conflict=<style>` and `-m` for re-creating markers: https://git-scm.com/docs/git-checkout
- `gitattributes` — merge drivers, `merge=union`, `text eol=lf`: https://git-scm.com/docs/gitattributes
- `git diff` — the combined-diff (`--cc`) format explained: https://git-scm.com/docs/git-diff#_combined_diff_format
- Git 2.35 release notes — `zdiff3`, the improved conflict style this machine cannot yet use: https://github.blog/open-source/git/highlights-from-git-2-35/
- Django docs — *Migrations*, including `makemigrations --merge` for conflicting leaf nodes: https://docs.djangoproject.com/en/5.0/topics/migrations/#version-control
- GitHub docs — *Resolving a merge conflict using the command line*: https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/addressing-merge-conflicts/resolving-a-merge-conflict-using-the-command-line
- Learn Git Branching — practise merge and rebase conflicts interactively, free: https://learngitbranching.js.org/
