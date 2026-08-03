---
id: fresh-db-requirements
type: topic-canonical
status: active
owner: handwritten
scope: all apps — master data required before a fresh database can run the factory
anchors: config/production/management/commands/seed_master_data.py, scripts/db.sh
verified: 2026-08-01
title: Fresh-Database Requirements — what MUST exist before this app can run
living: LIVING DOCUMENT — update it the moment you find a gap
maintainer: Umesh (owner) + AI agents
created: 2026-07-31
verified_against: measured on a real empty database, twice
human_guide: kos/concepts/testing/local-testing-environment.md
---

# Fresh-Database Requirements

**What this file is.** The single list of everything that must exist in a brand-new
database before this system can actually run a batch of production. Written because
a fresh production database came up **unable to start a single Adda** (AUDIT-2,
2026-07-27) and nobody knew until it was measured.

**The maintenance rule (why this file is LIVING):**

> Every time testing on a clean database reveals something missing, add it here in
> the same session. If it is **platform data** (same in every factory) also add it
> to `seed_master_data` so it becomes automatic. If it is **business data**
> (different per factory) it belongs in the human checklist in §3.
>
> A gap found and not written down here is a gap that will be rediscovered the hard
> way, on a live server, by a person who is waiting to start work.

---

## The three layers

A working database is built in three layers. Only the first two are automatic.

| Layer | Who creates it | Automatic? |
|---|---|---|
| 1. Migrations | `manage.py migrate` | ✅ yes |
| 2. Platform master data | `manage.py seed_master_data` (also runs on deploy) | ✅ yes |
| 3. **Business data** | **a human, through the UI** | ❌ **no — this is §3** |

---

## §1 — What migrations give you (measured on an empty database)

| Object | Count | Note |
|---|---:|---|
| `production.Stage` | **4** | only `layering`, `cutting_pattern`, `cutting`, `barcode_generation` |
| `accounts.Skill` | **2** | only `cutting_master`, `cutting_master_helper` |
| Stage → Skill access links | **7** | and one is WRONG — see §5 |
| `accounts.UserType` | 5 | admin · normal · superadmin · supplier · worker |
| `inventory.Role` | 5 | super_admin · manager · worker · listing_team · accountant |
| `inventory.SidebarItemRule` | 21 | menu/URL gating rows |
| `raw_materials.ClothType` | 4 | starter set |
| `raw_materials.ClothColor` | 6 | starter set |
| `raw_materials.StorageLocation` | 2 | starter set |
| `production.Product` | **5** | ⚠️ skeleton products — see §5 |
| `production.WorkflowStage` | 10 | the 2 stages each of those 5 products |
| **`accounts.User`** | **0** | ⚠️ **you cannot log in at all** |

## §2 — What `seed_master_data` adds (automatic, idempotent, additive-only)

Brings the platform up to a runnable factory. Safe to run any number of times; it
never modifies a row you edited.

| Object | After seeding | Was |
|---|---:|---:|
| `StageCategory` | 5 | 4 |
| `MachineType` | 5 | 1 |
| `accounts.Skill` | **10** | 2 |
| `production.Stage` | **21** | 4 |
| Stage → Skill access links | **24** | 7 |

Command: `python manage.py seed_master_data --repair-access`
(also wired into `deploy/entrypoint.sh`, so a real deploy gets it automatically).

---

## §3 — REQUIRED: what a human must create (the checklist)

**This is the part that is not automatic and never will be — it is your business.**
Do it in this order; each row needs the ones above it to exist.

| # | Create | Required? | What BREAKS without it |
|---|---|---|---|
| 1 | **Superuser login** (`createsuperuser`) | 🔴 **REQUIRED** | You cannot sign in. Nothing else is reachable. |
| 2 | **Product** | 🔴 **REQUIRED** | An Adda *is* a batch of a product — no product, no Adda. |
| 3 | **ProductSize** rows for that product | 🔴 **REQUIRED** | Cutting reports pieces per colour **and size**; with no sizes the size picker is empty and the piece breakdown cannot be entered. |
| 4 | **WorkflowStage** rows (which stages, in what `order`) | 🔴 **REQUIRED** | The Adda has no stages to work through. |
| 5 | **Cost rate on each payable WorkflowStage** (`cost_method` + `cost_rate`, `credits_workers`) | 🔴 **REQUIRED for money** | Stage runs but earns ₹0. Workers do real work for no recorded pay. ⚠️ The rate is **frozen onto the work** when it happens — wrong rate = wrong wage, and correcting it later is a reverse-and-resettle, not an edit. |
| 6 | **ClothType · ClothColor · StorageLocation** | 🟠 usually needed | Starter rows exist (§1) but they are generic. Your real cloth needs your real colours. |
| 7 | **ClothRoll** (with weight; `cost_per_kg` optional) | 🔴 **REQUIRED** | Layering attaches real rolls. No roll = the first stage cannot start. Without `cost_per_kg` the roll is *unpriced* — material cost stays honestly NULL rather than fake-zero. |
| 8 | **Users** with a **Role** | 🔴 **REQUIRED** | A user with no role is a user who can reach almost nothing. |
| 9 | **Workers with SKILLS** matching the stages they must open | 🔴 **REQUIRED** | This is the #1 confusion. Access to a stage = **skill ∩ assignment**. A worker with no matching skill is refused *by design*, and the message looks like a bug. |
| 10 | **Manager assignment** (roster) per stage | 🔴 **REQUIRED per stage** | Manager assignment is the ONLY roster source. Unassigned workers cannot report, even with the right skill. |

### Optional — nice to have, not blocking

| Object | Why it is optional |
|---|---|
| `machines.Machine` rows | A `work_type='machine'` stage runs fine with no Machine row — verified. Machines exist for possession tracking (R10-A), not as a gate. |
| `cost_per_kg` on rolls | Material cost stays NULL (honest) instead of wrong. |
| Barcode / tracking data | Generated by the flow itself, never seeded. |
| Storefront categories / featured products | Only affects the public site. |

---

## §4 — How to verify a fresh database is actually ready

```bash
./scripts/db.sh fresh test_production   # create + switch + login, one step
./scripts/db.sh check                   # <- the tool reports THIS checklist for you
./scripts/db.sh run                     # start the app
```

`db.sh check` reads the database and prints each requirement below as ✓ or ✗ with
the reason (e.g. `3-PATTI (no sizes; 2 stage(s); unrated: cutting)`). **When you add
a requirement to §3, add the matching probe to `cmd_check` in
`scripts/_db_admin.py`** — a checklist nobody can run goes stale.

Other tools while testing:

| Command | Use |
|---|---|
| `db.sh list` | every database + `stages · products · addas · users` so you know which is which |
| `db.sh branch <name> [--use]` | fork the current database — a save-point before something risky. Nests freely. |
| `db.sh save` / `restore` | a `.sql` copy in `db_backups/` (gitignored) |
| `db.sh delete <n> --yes-delete <n>` | removes it, taking a backup first |

Then check, in order:

- [ ] You can log in
- [ ] `/production/stages/` lists **21** stages
- [ ] Your product exists, has sizes, and its flow shows the stages you expect
- [ ] Every payable stage in that flow shows a **₹ rate**
- [ ] A worker account with the right skill can open its stage
- [ ] An Adda can be created and its first stage started
- [ ] The Adda reaches Dispatch
- [ ] Settlement produces the total you expect, and the ledger moves by exactly that

If any box fails, the cause is almost always **something above it is missing** —
not a bug. Add whatever it was to §3 of this file.

---

## §4b — "What if a DIFFERENT factory owner uses this?"

The owner asked the right question: *different owners have different products with
different stages, and their workers do not know each other.* Here is the honest
state, because part of it is already solved and part of it is deliberately not built.

### ✅ Already per-factory — no code change needed

This is the `configuration-over-code` pattern doing its job. A new factory owner
configures all of this themselves, through the UI:

| Thing | Why it is already per-factory |
|---|---|
| **Products** | Every factory creates its own. Nothing hardcodes a product. |
| **Sizes** | Per product, per factory. |
| **Which stages a product uses, and in what order** | `WorkflowStage` rows. Factory A's T-shirt uses shoulder-join + collar-attach; Factory B's lower uses elastic-attach + bottom-fold. **Same library, completely different flows.** |
| **Rates (₹) per stage** | Per product, per factory, frozen onto work when it happens. |
| **NEW stages that don't exist yet** | `StageCreateView`/`UpdateView`/`DeleteView` (permission-gated) let an owner add e.g. *Embroidery*, *Washing*, *Printing*. A newly created stage runs through the **generic stage** machinery (`GenericStageStart/Complete/Allocate`) — **so a new operation needs zero code.** |
| **Cloth, colours, storage, rolls** | All rows, all per factory. |
| **Workers, roles, skills, rosters** | All rows. |
| **Worker-to-worker privacy** | Already enforced and **proven**: AUDIT-2 ran 300 access probes across 8 distinct-skill workers — zero rate/cost leaks, per-skill isolation exact. A worker sees their own stages and their own earnings, never a colleague's. |

So the 21 seeded stages are a **starter library of operations, not a fixed
pipeline.** Picking from it (and extending it) is exactly what setup means.

### ⚠️ NOT built: factory-to-factory isolation in one deployment

There is **no `Factory` / `Tenant` / `Site` model today.** Verified: no such model
exists in any app. Which means:

> **Today, one deployment + one database = one factory.** All the data in a
> database belongs to one business. Two factory owners cannot share a deployment
> and be hidden from each other — there is nothing to hide them behind.

### 🔒 And the future is already decided — read this before designing anything

[ADR-0010 Decision 2](adr/0010-growth-and-identity-policy.md) is **ACCEPTED and
locked**, and it forbids the obvious approach:

> *"Multi-factory = one database + a site dimension. **Never a fork.** If factory
> #2 arrives, it is implemented as a `site` dimension (FK on Adda, scoped
> queues/dashboards) inside the SAME PostgreSQL database — never as a second
> deployment. A forked deployment splits `WorkerLedgerEntry` (the financial crown
> jewel) into two unmergeable ledgers. Workers/roles/skills stay global (one User
> table — people move between sites). Nothing is built now."*

Two consequences worth understanding:

- **Do not plan "a separate deployment per factory owner"** as the growth path.
  Two deployments means two ledgers, and two ledgers can never be reconciled into
  one set of books. That is the exact mistake the ADR exists to prevent.
- **References are one global namespace** (Decision 1): a second factory shares
  the same `ADST-XXXX` / `SETL-XXXX` / roll-ID sequences and never restarts at 1,
  precisely so a future consolidation is a *filter*, not a renumbering.

### What this means for you today

- Deploying for **your own factory**: nothing missing. Follow §3.
- Handing a copy to **another factory owner as their own separate system**: works
  today (their own server, own database, own superadmin), and is fine **as long as
  you never need the two factories' books in one place**.
- Wanting **both factories in one system**: that is the `site` dimension, and it is
  a future phase gated by ADR-0010 — not something to improvise.

**Every deployment needs its own superadmin.** That is why `createsuperuser` is
row 1 of §3: a fresh database has zero users, and there is no default account by
design (a shipped default password is how systems get breached).

---

## §5 — Known issues on a fresh database (open)

### F-6 — a renamed stage keeps its old name until restart (found 2026-08-01)

`production/stages/base/registry.py` `_generic_fallback()` builds a `GenericStageHandler`
from the `Stage` row and caches it in the **module-level `_REGISTRY` dict**, which is never
invalidated. Consequences:

- **Product:** renaming a stage through the UI leaves stale labels until the process restarts.
- **Tests:** the cache leaks across tests in one process. Running `devseed` and
  `production.tests` in the *same* invocation makes 3 `test_r10b_generic_stage` assertions
  fail, because `seed_master_data` creates `overlock` as **"Panel Join"** (which matches the
  owner's real data) and the cached handler wins over the test's own fixture.
  **The standard battery grouping is unaffected — each app is green run normally.**

*Status:* **reported, NOT fixed.** R10-B is frozen (frozen-foundation rule: no refactor
without explicit approval), and the practical workaround is "restart after renaming a stage".
A real fix would invalidate `_REGISTRY` on `Stage` save, or drop the cache.

**F-1 · The 5 skeleton products are noise for a new factory.**
Migrations seed `1-6`, `3-PATTI`, `NIKKAR`, `PAJAMA`, `T-SHIRT`, each with only
2 workflow stages (`layering`, `cutting`) and **zero sizes**. So a brand-new
factory opens the app and sees five products it did not create, none of which can
actually run. Not harmful, but "clean" should mean clean.
*Status:* **open — owner decision.** Removing them is a data migration, and this
project gates every migration behind explicit owner approval. Options: (a) leave
them and document, (b) a data migration that deletes them when no Adda references
them, (c) keep them but mark inactive.

**F-2 · One migration-seeded access link is wrong.**
The `cutting` stage ships with `cutting_master` but **not**
`cutting_master_helper`, so a cutting helper silently cannot open Cutting.
*Status:* **worked around.** `seed_master_data --repair-access` adds it, and the
command prints a loud `ACTION NEEDED` block when it detects the gap. The migration
itself is still wrong; fixing it at the source needs a migration.

**F-4 · Uploaded media lives OUTSIDE the database — and all databases share it.**
`MEDIA_ROOT = config/media/` (13 FileField/ImageField columns across 5 apps). A
`db.sh save` backup contains paths, never files; all local databases share one
media tree with colliding, Adda-code-keyed paths; the pattern-photo remove view
physically deletes the shared file (the only media-deleting call site), which can
break another database/backup pointing at the same path; `db.sh delete` orphans a
database's media forever (no `django-cleanup` installed — deliberate, consistent
with append-only posture). Production restic backup (`deploy/backup.sh`) covers
DB + media together, which is why it, not `db.sh save`, is the go-live backup.
*Status:* accepted + taught (kos local-testing-environment "What a database does
NOT contain"). Rule of thumb recorded: don't delete photos on test databases.

**F-5 · Tooling hardening from the 2026-07-31 hostile review (all fixed).**
Four confirmed bugs in `scripts/_db_admin.py`, all repaired + re-tested:
(1) restore ran psql without `ON_ERROR_STOP` → a partially-failed restore (and
therefore a *branch*) reported ✓ over an incomplete database; now stops on first
error and drops the half-restored target. (2) a failed `pg_dump` left a 0-byte
`.sql` masquerading as a backup; now unlinked, and restore refuses files <1 KB.
(3) `check` used the wrong payability predicate — a cost-grouped member stage
(`credits_workers=True, cost_billed_at=<payer>`, legitimately rate-less per the
C-1 double-pay guard) was flagged "unrated", inviting the owner to *add* the
forbidden rate; now mirrors `credit.py` (`cost_billed_at_id is None`, and
`cost_rate is None` so a ₹0 rate is legal. (4) `createsuperuser` assigns no Role,
so the owner's own fresh login permanently failed the "users have roles" probe;
superusers are now excluded. Plus: `DATABASE_URL` in `.env`/env now makes the
tool refuse to run at all (Django would ignore `DB_NAME`, so every command would
act on the wrong database — and `.env.example` ships the line uncommented).

**F-3 · Starter cloth master data is generic.**
4 cloth types / 6 colours / 2 storage locations arrive from migrations. Harmless,
but they are not any real factory's list. *Status:* accepted; §3 row 6 covers it.

---

## §6 — Maintenance log

Append a line whenever this file changes. This is how we prove the list is alive.

| Date | Change | Found how |
|---|---|---|
| 2026-07-27 | File's subject discovered: fresh DB had 4/21 stages, 2/10 skills, 0 users → could not start an Adda | AUDIT-2 measurement on a throwaway empty database |
| 2026-07-27 | `seed_master_data` created (layer 2) + wired into `deploy/entrypoint.sh` | same |
| 2026-07-31 | This file created as the living registry; §3 checklist written; F-1/F-2/F-3 recorded | owner asked for a maintained "required objects for a fresh DB" list |
| 2026-07-31 | 31-agent hostile review of the db tooling: 4 tool bugs fixed (F-5), media/session/pg-version truths recorded (F-4), kos page gained "What a database does NOT contain" | ultracode review workflow, every finding adversarially verified |
| 2026-07-31 | SQL/PostgreSQL course written from this project's own tables: **[docs/sql_course/](sql_course/00_COURSE_OVERVIEW.md)** — 26 files, 25 chapters, deployment-course format, all outputs real | owner asked to learn SQL deeply from his own factory data, then to restructure it chapter-wise like the deployment course |

---

## Related

- **Human teaching version:** [kos/concepts/testing/local-testing-environment.md](../kos/concepts/testing/local-testing-environment.md)
- Seed command: `config/production/management/commands/seed_master_data.py`
- DB tool: `scripts/db.sh` (`fresh` · `list` · `use` · `save` · `restore` · `delete`)
- Audit that exposed the gap: [AUDIT2_PRODUCTION_ACCESS_FINANCIAL_2026_07_27.md](AUDIT2_PRODUCTION_ACCESS_FINANCIAL_2026_07_27.md)
