---
id: git-course-17-stash-and-worktrees
type: lesson
status: active
owner: handwritten
scope: git — stash, worktrees, switching context without committing half-finished work
anchors: .git/refs/stash, .git/worktrees, .gitignore
verified: 2026-08-03
---

# 17 — Stash & Worktrees (switching context without committing half-work)

> Part of [Git Course](00_COURSE_OVERVIEW.md). Prev: [16 — Reflog](16_Reflog.md). Next: [18 — Remotes](18_Remotes.md).

# Learning Objectives
By the end of this chapter you can:
- set work aside safely without making a junk commit
- explain what a stash physically **is** (two or three commits and one ref — not a magic clipboard)
- choose correctly between `pop` and `apply`, and recover a stash you dropped
- explain why `git stash` ignores untracked files by default, and what that has cost people
- use `git worktree` to have two branches checked out at once, without a second clone
- say when a worktree is the right answer and when a stash is

# Purpose
You are half-way through a feature. Nothing compiles. Then something urgent arrives — a
production bug, a review comment, a colleague asking you to look at their branch.

You have three options, and two of them are bad:

1. **Commit the mess** — pollutes history with `WIP asdf` commits you must clean up later.
2. **Throw the work away** — obviously unacceptable.
3. **Set it aside cleanly** — `git stash`, or a second `git worktree`.

This chapter is option 3, properly understood. It is a short chapter with an outsized effect
on how pleasant git is to live with day to day.

# The Problem
`git switch` refuses to move when your changes would be overwritten:

```
error: Your local changes to the following files would be overwritten by checkout:
        config/expense/views.py
Please commit your changes or stash them before you switch branches.
```

Note that git *names the solution* in the error, and most beginners still commit junk because
they do not know what "stash them" involves. The error is also slightly misleading: git will
happily let you switch when your changes **do not** conflict with the target branch, which is
why the behaviour feels inconsistent until you know the rule.

The deeper problem is that a stash is usually taught as "a magic clipboard". That framing
makes it feel unsafe, so people avoid it — and then it *does* bite them, because they never
learned the two real traps (untracked files, and `pop` on conflict).

# Theory (from zero)

### A stash is commits. That is the whole trick.
`git stash` does not use a special storage format. It creates real commit objects and points a
ref at them:

| Object | Contains |
|---|---|
| A commit of your **index** (staged state) | what you had staged |
| A commit of your **working directory** | what you had unstaged |
| (optional) a commit of **untracked** files | only with `-u` |

Those are wrapped in a merge-ish commit, and `.git/refs/stash` points at it. The stash *list*
is that ref's **reflog** — which is why entries are named `stash@{0}`, `stash@{1}`: they are
reflog positions, exactly like `HEAD@{2}` in [Chapter 16](16_Reflog.md).

```bash
git stash
git cat-file -t refs/stash        # commit   ← not a special type. Just a commit.
git log --oneline -1 refs/stash
```

Two consequences fall straight out of "it is commits":

1. **A dropped stash is recoverable** — the commit object still exists, unreferenced, until
   garbage collection. `git fsck --unreachable` finds it.
2. **A stash is not a backup.** It lives in *this* clone's `.git`. It is never pushed, never
   fetched, never in a backup of your remote. Delete the clone and every stash dies with it.

### `pop` versus `apply` — the one distinction that matters
```bash
git stash pop     # apply the changes, then DELETE the stash entry
git stash apply   # apply the changes, KEEP the stash entry
```

`pop` is `apply` plus `drop`. And here is the trap that costs people real time:

**If applying causes a conflict, `pop` does not drop the entry** — which is good. But if it
applies *cleanly*, the entry is gone. So the failure mode is: you `pop`, it applies cleanly,
you then realise you popped onto the **wrong branch**, you undo your working directory… and the
stash is no longer in the list.

**Habit worth forming: use `apply`, verify, then `drop` deliberately.** One extra command, and
"where did my stash go" stops happening.

### The untracked-files trap
By default `git stash` saves **tracked** modifications only. A brand-new file you have not
`git add`ed is left sitting in your working directory:

```bash
git stash        # tracked changes only — new files STAY behind
git stash -u     # --include-untracked: new files too
git stash -a     # --all: untracked AND ignored files
```

Why this matters: you stash, switch branch, and your new file is still there — now visible on a
branch it does not belong to. Worse, `git stash -u` followed by `git checkout .` on the other
branch can leave you convinced the file was lost.

And a genuine footgun: **`git stash -a` includes ignored files.** In this repository that means
it would pick up `.env`, `db_backups/`, `node_modules/`. That is almost never what you want, and
on a 27 MB `node_modules` it is slow as well as wrong. Use `-u`, not `-a`, unless you have a
specific reason.

### Stashes are stackable and inspectable
```bash
git stash list                      # stash@{0}, stash@{1}, …  (newest first)
git stash show stash@{1}            # summary of that entry
git stash show -p stash@{1}         # the full patch
git stash push -m "wip: rate table" # NAME it — future-you cannot read "WIP on main: 3a4f2b1"
git stash pop stash@{2}             # apply a specific entry
git stash branch fix/x stash@{0}    # create a branch FROM a stash and apply it there
```

`git stash push -m "…"` is underused and worth the habit. A list of five unnamed stashes from
last week is functionally a list of five mysteries.

`git stash branch` is the elegant escape hatch: if a stash will not apply cleanly because the
branch moved, this creates a branch at the commit the stash was *made* on, where it applies
cleanly by construction.

### Worktrees: the better answer to "I need two branches at once"
A stash sets work aside. A **worktree** avoids needing to:

```bash
git worktree add ../hotfix main
```

That creates a **second working directory** on disk at `../hotfix`, checked out to `main`,
sharing the **same** `.git` object store. Two checkouts, one repository.

| | Stash | Worktree |
|---|---|---|
| Work in progress | must be set aside | **stays exactly as it is** |
| Disk cost | none | a second checkout (objects are shared) |
| Two branches at once | no | **yes** |
| Build artefacts / venv | shared, so they thrash | separate per worktree |
| Good for | a 5-minute interruption | a review, a long-running build, a parallel hotfix |

The shared object store is the point: a worktree is **not** a second clone. No re-download, no
duplicated history, and a commit made in one worktree is instantly visible to the other.

```bash
git worktree list                 # every checkout of this repo
git worktree remove ../hotfix     # clean up (refuses if it has changes)
git worktree prune                # tidy stale admin files after a manual delete
```

One rule: **the same branch cannot be checked out in two worktrees at once.** Git refuses,
because two working directories mutating one branch ref is incoherent. Use a different branch,
or a detached checkout (`git worktree add --detach`).

> 💡 **Samjho aise:** `git stash` = **adha kaam ek thaile mein daal ke almari mein rakh dena**.
> Mez saaf, doosra kaam kar lo, phir thaila kholo. Par yaad rakho: thaila **sirf tumhare ghar**
> mein hai — push nahi hota, backup mein nahi jaata. Ghar (clone) gaya, thaila gaya.
>
> `git worktree` = **doosri mez lagana**. Pehli mez ka kaam chhedna hi nahi pada. Dono mez ka
> saaman **ek hi godown** (`.git`) se aata hai, isliye doosri mez lagana sasta hai — poora naya
> clone nahi.
>
> Aur sabse zaroori: `pop` = thaila khol ke **phaad dena**. `apply` = khol ke **rakh lena**.
> Pehle `apply`, dekho sab theek hai, phir `drop`. Ek command zyada, par "mera stash kahan
> gaya" kabhi nahi hoga.

# Real World Example (this repo)
Two places where this chapter is not theoretical for this project.

**1. The `.env` / ignored-files hazard is real here.** This repository deliberately ignores
`.env`, `db_backups/`, `backups/`, `*.sql` and `node_modules/` at the monorepo root
([Chapter 07](07_Gitignore.md)). `git stash -a` would sweep all of it into a stash commit —
including a real `.env` with database credentials and, on the old practice app, **27 MB** of
`node_modules`. That stash commit lives in `.git/objects` like any other. Use `-u`.

**2. Worktrees are the right tool for this monorepo's shape.** The git root is
`/home/tech/umesh-personal` and the Django project is the `django_inventory/` subdirectory with
its own `env/` virtualenv, `staticfiles/` and Postgres database. A second worktree gets its own
copy of those working files while sharing history — so you can have `main` checked out to
reproduce a production bug while your feature branch stays untouched, without a 97 MB re-clone.

```bash
git worktree list
# /home/tech/umesh-personal  42a2ecc4 [new_flask_app]
```

One checkout today. Note the practical caveat for this project specifically: a second worktree
needs its **own** `env/` (a virtualenv contains absolute paths) and, if you run tests there, a
**separate database** — the test battery drops and recreates its database, so two worktrees
running tests against the same `DB_NAME` will fight. `scripts/db.sh` exists precisely to switch
databases per checkout.

**3. Why `rerere` and stash are complementary.** This repo sets `rerere.enabled true`
([Chapter 02](02_Install_And_Configure.md)). If a stash conflicts on `apply` and you resolve it,
rerere records the resolution — so re-applying the same stash after another branch move resolves
itself.

# Visual Diagram
```
  STASH — it's commits, and the list is a reflog
  ─────────────────────────────────────────────
    working dir ──┐
                  ├──► stash commit ◄── .git/refs/stash
    index      ───┘         │
    untracked (-u only) ────┘         stash@{0} ─┐
                                      stash@{1} ─┤ ← reflog positions of that ref
                                      stash@{2} ─┘   (same idea as HEAD@{2}, ch 16)

    pop   = apply + drop      (entry GONE if it applied cleanly)
    apply = apply, keep       ← verify, then `drop` deliberately
    dropped by mistake? git fsck --unreachable | grep commit   (ch 16)

    ⚠ default saves TRACKED changes only
      -u  include untracked (new files)          ← usually what you want
      -a  include IGNORED too → .env, node_modules, db_backups/   ← almost never


  WORKTREE — two checkouts, ONE object store
  ─────────────────────────────────────────────
    /home/tech/umesh-personal   [new_flask_app]   ─┐
                                                   ├──► ONE shared .git/objects
    ../hotfix                   [main]            ─┘     (no re-clone, no duplicate history)

    same branch in two worktrees = REFUSED (two dirs mutating one ref)
    per-worktree in THIS project: own env/ (venv has absolute paths), own DB_NAME
```

# Practical — both tools, hands on
```bash
# ── STASH ───────────────────────────────────────────────────────────────────
cd /tmp && rm -rf st && mkdir st && cd st && git init -q
git config user.email t@t && git config user.name t
echo base > a.txt && git add . && git commit -qm "feat: base"

echo "half-finished" >> a.txt      # tracked modification
echo "brand new"     > new.txt     # UNTRACKED

git stash push -m "wip: my experiment"
ls                                 # a.txt  new.txt   ← new.txt STAYED (the trap)
git status --short                 # ?? new.txt

git stash list
# stash@{0}: On main: wip: my experiment      ← the -m message pays off here

git stash show -p stash@{0}        # exactly what is inside
git stash apply                    # apply but KEEP the entry
git stash list                     # still there ✔
git stash drop                     # now remove it, deliberately

# prove a stash is just commits
git stash push -m "proof"
git cat-file -t refs/stash         # commit
git log --oneline -1 refs/stash
git stash drop
git fsck --unreachable 2>/dev/null | grep commit | head -2   # the dropped commit still exists

# ── WORKTREE ────────────────────────────────────────────────────────────────
git switch -qc feat/x && echo x > x.txt && git add . && git commit -qm "feat: x"
git worktree add ../st2 main        # second checkout, branch main
git worktree list
ls ../st2                           # main's files — feat/x untouched over here
git worktree remove ../st2
git worktree list
```

The two lines worth pausing on: `ls` showing `new.txt` survived the stash, and
`git cat-file -t refs/stash` printing `commit`. Those are the chapter's two core facts,
demonstrated rather than asserted.

# Production Walkthrough
How these get used on real work in this project:

1. **Review interruption, 5 minutes.** `git stash push -m "wip: <what>"` → `git switch main` →
   read the PR → `git switch -` → `git stash apply` → verify → `git stash drop`.
2. **Urgent production bug, unknown duration.** Use a **worktree**, not a stash. Your feature
   checkout stays warm — no rebuild, no re-migrate, and no risk of popping onto the wrong
   branch.
3. **Reviewing someone's branch while your own build runs.** Worktree. Both checkouts share
   objects, so `git fetch` in one makes the branch available in the other immediately.
4. **A stash that will not apply because the branch moved on.**
   `git stash branch fix/salvage stash@{0}` — creates a branch at the commit the stash was made
   on, where it applies cleanly by construction.
5. **Never stash across a `pull.rebase`.** This repo sets `pull.rebase true`; stash first, pull,
   then apply. A rebase with a dirty tree is refused anyway, which is the safe behaviour.
6. **Do not use a stash as a to-do list.** Stashes are invisible to everyone else, absent from
   backups, and die with the clone. Anything you would be upset to lose belongs on a branch —
   which is free ([Chapter 09](09_What_A_Branch_Really_Is.md)).

# Debugging Guide

| Symptom | Cause | Fix |
|---|---|---|
| `git stash` "did not save" a new file | default saves **tracked** changes only | `git stash -u` |
| Stash included `.env` / `node_modules` | you used `-a`, which includes ignored files | use `-u`; `git stash drop` the bad entry |
| "My stash disappeared" | `pop` applied cleanly and dropped the entry | `git fsck --unreachable \| grep commit`, then `git stash apply <hash>` |
| `pop` left the entry behind | it conflicted — deliberate, so you do not lose it | resolve, `git add`, then `git stash drop` |
| Conflict on `apply` and you want out | working tree is mid-merge | `git checkout --theirs/--ours` per file, or `git reset --hard` (loses the applied part; the stash survives if you used `apply`) |
| `fatal: '<branch>' is already checked out` | a branch cannot be in two worktrees | different branch, or `git worktree add --detach` |
| Worktree folder deleted manually, git still lists it | admin files left in `.git/worktrees` | `git worktree prune` |
| Tests fail in the second worktree | shared `DB_NAME`, or a copied `env/` with stale absolute paths | separate database (`scripts/db.sh`), fresh venv per worktree |
| `git worktree remove` refuses | uncommitted changes there | commit/stash them, or `--force` if genuinely disposable |

# Performance Notes
- **`git stash` is cheap** — it writes two small commits and moves a ref. Cost tracks the size
  of your *changes*, not the repo.
- **`git stash -a` is not cheap** — it must hash every ignored file. Against a 27 MB
  `node_modules` that is seconds, and the resulting stash commit bloats `.git` permanently.
- **A worktree is far cheaper than a clone.** Objects are shared, so `git worktree add` copies
  only a working checkout; a fresh clone of this repo would re-transfer 97 MB of history.
- Worktrees do cost **build state**: separate `env/`, separate `staticfiles/`, separate
  `node_modules` if any. That is usually the point, but it is disk.
- `git stash list` is a reflog read — instant, however many entries.
- Stashes never garbage-collect while referenced, so a forgotten stash pins its objects forever.
  `git stash list` occasionally is good hygiene.

# Security Considerations
- **`git stash -a` will happily stash your secrets.** `.env`, dumps and keys are ignored
  precisely so they never enter git; `-a` overrides exactly that protection and writes them into
  `.git/objects` as commits. This is a real hole in a repo that carries a credentials file — which
  this one does.
- **A dropped stash is not deleted.** The commit persists unreferenced until gc, so a stash that
  once contained a secret is still readable via `git fsck --unreachable`.
- **Stashes are local and invisible.** No teammate, reviewer or backup can see them, so a stash is
  the worst possible place for anything important, and a *convenient* place for something to sit
  forgotten for months.
- **Worktrees share the object store.** A commit made in a throwaway worktree is a commit in the
  real repository. There is no sandbox — treat every worktree as the repo it is.
- **A second worktree needs its own database and `.env`.** Pointing two checkouts at one dev
  database means one can drop the other's data mid-test.

# Architecture Decisions
- **Git implements stash on top of commits rather than as a separate store.** One object model
  for everything: stashes are inspectable with `log`/`show`/`cat-file`, and recoverable with
  `fsck`, with no bespoke recovery tooling.
- **The stash list is a reflog.** So `stash@{n}` needed no new syntax, and expiry/gc policy is
  shared with the rest of git.
- **Untracked files excluded by default.** Debatable, but defensible: a new file is not yet part
  of the project's tracked state, and silently sweeping up everything in the directory would be
  worse. The cost is a genuine surprise for beginners, which is why `-u` is worth memorising.
- **Same branch cannot be in two worktrees.** Refusing is correct — two checkouts advancing one
  ref would produce incoherent state. Detached mode is the escape hatch.
- **This project prefers branches over long-lived stashes.** Branches are 41 bytes, pushable,
  reviewable and visible. A stash is none of those. Stash is for minutes; a branch is for work.
- **`rerere.enabled true`** so a conflict resolved once during `stash apply` (or a rebase) is
  replayed automatically next time.

# Best Practices
- Always `git stash push -m "wip: <what>"`. An unnamed stash is a mystery within a week.
- Prefer `apply` → verify → `drop` over bare `pop`.
- Use `-u` when you have new files. Avoid `-a` unless you can say exactly why.
- Anything you would mind losing goes on a **branch**, not a stash.
- Reach for a **worktree** for anything longer than a few minutes, or whenever you need two
  branches simultaneously.
- Give each worktree its own virtualenv and database in this project.
- Check `git stash list` occasionally and clear out what is dead.
- `git worktree remove` rather than `rm -rf`, so git's admin state stays consistent.

# Beginner Mistakes
- **Committing `WIP asdf` instead of stashing** → history you must clean up with an interactive
  rebase later ([Chapter 14](14_Interactive_Rebase.md)).
- **Assuming `git stash` saved a new file** → it does not, without `-u`. The file quietly stays
  in your working directory, on the wrong branch.
- **Using `git stash -a` "to be safe"** → sweeps `.env`, `db_backups/`, `node_modules` into a
  commit. The opposite of safe.
- **Bare `git stash pop`** → applies cleanly, drops the entry, and if you then discover it was
  the wrong branch you are hunting through `git fsck`.
- **Treating stashes as a to-do list** → they are invisible, unpushed, unbacked-up and die with
  the clone.
- **`rm -rf` on a worktree folder** → leaves stale admin files; needs `git worktree prune`.
- **Copying `env/` into a new worktree** → a virtualenv embeds absolute paths and will misbehave.
- **Two worktrees, one dev database** → tests in one destroy the other's data.

# Interview Questions
- **Junior:** "What does `git stash` do?" — Saves your uncommitted changes so the working
  directory returns to a clean HEAD, letting you switch branches. `git stash apply` or `pop`
  brings them back. By default it saves tracked modifications only, so new untracked files need
  `-u`.
- **Mid:** "Difference between `pop` and `apply`, and why does it matter?" — `pop` is `apply`
  plus `drop`. If application conflicts, `pop` keeps the entry; if it succeeds, the entry is
  gone. So `apply` → verify → `drop` is the safer habit, because a clean pop onto the wrong
  branch leaves nothing in `git stash list` to retry from.
- **Senior:** "What *is* a stash, physically?" — Real commit objects: one for the index, one for
  the working tree, optionally one for untracked files, wrapped together and pointed at by
  `.git/refs/stash`. The stash *list* is that ref's reflog, which is why entries are
  `stash@{n}`. Two implications: a dropped stash is recoverable via `git fsck --unreachable`
  until gc, and a stash is purely local — never pushed, never backed up, dies with the clone.
- **Staff:** "Team keeps losing work in stashes. What do you change?" — Stop treating stash as
  storage. It is per-clone, invisible to everyone, absent from any backup of the remote, and
  `pop` is destructive on success — so it is structurally unsuited to holding anything valuable.
  The fix is policy plus ergonomics: work in progress goes on a cheap pushed branch (41 bytes
  locally, and then it is reviewable and backed up); stash is for interruptions measured in
  minutes; and for anything longer, worktrees remove the need to set work aside at all. I would
  also ban `stash -a` outright in a repo that ignores a credentials file, since it writes exactly
  the files `.gitignore` exists to keep out into the object store.

### Why interviewers ask these — and the answer that separates levels
| Testing for | Weak answer | What lands |
|---|---|---|
| Do you know the mechanism or the metaphor? | "It's a clipboard for my changes." | Real commits plus a ref whose reflog is the stash list — hence `stash@{n}`, hence `fsck` recovery, hence local-only. |
| Have you been bitten, or only read? | "`pop` and `apply` are basically the same." | `pop` = apply + drop; keeps the entry on conflict, removes it on success — so `apply`/verify/`drop` avoids the real failure mode. |
| Do you understand the blast radius? | "`-a` saves everything, so it's safest." | `-a` includes **ignored** files, so it writes `.env` and `node_modules` into the object store — the exact opposite of safe. |

**The killer follow-up:** *"Your laptop dies with three stashes on it. What is recoverable?"* — Nothing. Stashes live in that clone's `.git`, are never pushed, and appear in no backup of the remote. That single question is why work-in-progress belongs on a pushed branch and why `stash` is for interruptions, not storage — and it separates people who have reasoned about stash from people who merely use it.

# Revision Notes
- A stash is **real commits** + `.git/refs/stash`; the **list is that ref's reflog** ⇒ `stash@{n}`.
- **`pop` = apply + drop.** Keeps the entry on conflict, deletes it on success. Prefer `apply` → verify → `drop`.
- Default stashes **tracked changes only**. `-u` adds untracked. **`-a` adds IGNORED** — `.env`, `node_modules`. Avoid.
- Dropped a stash? `git fsck --unreachable | grep commit`, then `git stash apply <hash>`.
- **Stashes are local**: never pushed, never backed up, die with the clone. Not storage.
- Name them: `git stash push -m "wip: …"`.
- `git stash branch <name> stash@{0}` — when a stash will not apply because the branch moved.
- **Worktree** = second checkout, **one shared object store**. Not a clone. Same branch twice = refused.
- In this project each worktree needs its **own `env/` and database**.

# Cheat Sheet
```bash
git stash push -m "wip: rate table"   # ALWAYS name it
git stash push -u -m "wip: with new files"   # -u = include untracked  ← usually right
git stash list                        # stash@{0} newest first (a reflog)
git stash show -p stash@{0}           # full patch of an entry
git stash apply                       # apply, KEEP entry   ← safer default
git stash pop                         # apply + DROP entry
git stash drop stash@{0}              # remove one entry
git stash clear                       # remove ALL (no confirmation!)
git stash branch fix/x stash@{0}      # branch at the stash's origin, then apply
git stash push -- path/to/file        # stash only these paths
git cat-file -t refs/stash            # "commit" — proof it is not magic
git fsck --unreachable | grep commit  # find a stash you dropped

git worktree add ../hotfix main       # second checkout, branch main, shared .git
git worktree add --detach ../tmp HEAD # detached, when the branch is taken
git worktree list                     # every checkout of this repo
git worktree remove ../hotfix         # clean removal (refuses if dirty)
git worktree prune                    # tidy after a manual rm -rf
```

# My ERP Section

| Fact | This project |
|---|---|
| Current worktrees | one: `/home/tech/umesh-personal` on `new_flask_app` (`git worktree list`) |
| Why `-a` is dangerous **here** | root `.gitignore` blocks `.env`, `db_backups/`, `backups/`, `*.sql`, `node_modules/` — `stash -a` would write all of it into `.git/objects`, including real DB credentials and 27 MB of `node_modules` |
| Per-worktree needs | its own `env/` (virtualenvs embed absolute paths) and its own `DB_NAME` — the battery drops/recreates its database, so two worktrees sharing one DB will fight |
| DB switching tool | `scripts/db.sh` — exists so a second checkout can have its own database |
| Conflict memory | `rerere.enabled true` ⇒ a conflict resolved once during `stash apply` replays automatically |
| Preferred alternative | branches: 41 bytes, pushable, reviewable, backed up — everything a stash is not ([Ch 09](09_What_A_Branch_Really_Is.md)) |
| Recovery net | [Chapter 16 — Reflog](16_Reflog.md): the stash list *is* a reflog, and `fsck --unreachable` finds dropped entries |

# Practice Tasks
1. Run the Practical block. Stop after `git stash push` and confirm with `ls` that the untracked
   file **stayed**. That is the trap, felt rather than read.
2. `git cat-file -t refs/stash` and get `commit`. Then `git log --oneline -1 refs/stash`. A stash
   is not magic.
3. Deliberately `git stash drop` a stash you care about, then recover it:
   `git fsck --unreachable | grep commit`, then `git stash apply <hash>`.
4. Create a conflict on `apply` (stash a change, commit a different change to the same line, then
   apply). Confirm the entry is **not** dropped. That is `pop` protecting you.
5. `git worktree add ../wt2 main`, edit a file in each checkout, and confirm they are independent.
   Then `git log` in one and see the other's commit — shared object store.
6. Try `git worktree add ../wt3 main` while `main` is already checked out. Read the refusal and
   explain why it is correct.

# Homework
- Go a full week without `git stash pop`. Use `apply` → verify → `drop`. Notice how often the
  verification step catches something.
- Set up a second worktree for this project properly: its own `env/`, its own database via
  `scripts/db.sh`, and run the test battery in it while your main checkout stays untouched. This
  is the setup that makes parallel work genuinely pleasant.
- Audit your stashes across every repo you own (`git stash list`). Anything older than a week
  either belongs on a branch or should be dropped. Decide which, for each.
- Read `git help stash` on `--keep-index` and work out when staging-only stashing is useful —
  it is the tool for testing exactly what you are about to commit.

# Further Reading & Live Resources
- [Pro Git — Stashing and Cleaning](https://git-scm.com/book/en/v2/Git-Tools-Stashing-and-Cleaning) — the canonical chapter, free
- [git-stash reference](https://git-scm.com/docs/git-stash) — every flag, including `--keep-index` and `--staged`
- [git-worktree reference](https://git-scm.com/docs/git-worktree) — add, list, remove, prune, and the locking rules
- [Atlassian — git stash tutorial](https://www.atlassian.com/git/tutorials/saving-changes/git-stash) — clear diagrams of the stash stack
- [git-fsck reference](https://git-scm.com/docs/git-fsck) — `--unreachable` and `--lost-found`, the stash recovery tools
- [Learn Git Branching](https://learngitbranching.js.org/) — practise branch juggling interactively, free
