---
id: sql-course-13-constraints
type: lesson
status: active
owner: handwritten
scope: sql, postgresql — database fundamentals taught from this ERP
anchors: config/expense/services/settlement_service.py, config/production/services/pool_service.py
verified: 2026-08-01
---

# 13 — Constraints: Rules Data Cannot Break

> Part of [SQL From Zero](00_COURSE_OVERVIEW.md). Prev: [12](12_Append_Only_Money.md) · Next: [14 — Indexes](14_Indexes.md).

# Learning Objectives
By the end of this chapter you can:
- name every constraint type and what each one refuses
- read a real `CHECK` definition and explain its NULL handling
- choose an FK delete action and defend it for money
- say which invariants constraints *cannot* express, and where those live

# Purpose
To meet the last line of defence in my factory: rules stored **inside the tables
themselves**, which fire no matter who is writing — my code, a script, a tired
human in dbshell at midnight, or a future bug I haven't written yet.

# The Problem
Application code checks things. Application code also has bugs, gets refactored,
grows a new endpoint that forgets a check, and gets bypassed entirely when someone
opens dbshell. If "a wage can never be negative" lives *only* in Python, then it
is true only while every code path remembers it. I need rules that are true
**physically**.

# Theory (from zero)

```
        THE FOUR WALLS — a bad value must pass ALL of them
   ═══════════════════════════════════════════════════════════════
   1. FORM        "is it shaped like a number?"        (Django form)
        ↓ passes
   2. SERVICE     "is it allowed by business rules?"   (service layer)
        ↓ passes
   3. CONSTRAINT  "is it physically permitted?"        ← THE DATABASE
        ↓ passes
   4. stored
   ═══════════════════════════════════════════════════════════════
   Walls 1–2 can be bypassed (scripts, dbshell, a buggy new code path).
   Wall 3 cannot. That is the entire point of this chapter.
```

**The constraint types:**

| Type | Says | My real example |
|---|---|---|
| `NOT NULL` | this column must have a value | `production_adda.code` |
| `UNIQUE` | no two rows share this value | `production_adda_code_key` |
| `PRIMARY KEY` | unique **+** not null, the row's identity | `production_adda_pkey` |
| `FOREIGN KEY` | this number must exist over there | `product_id → production_product(id)` |
| `CHECK` | this expression must be true | `wsc_expected_earning_nonneg` |
| `EXCLUDE` | Postgres-only: no two rows *overlap* (e.g. date ranges) | not used here — worth knowing it exists |

**Foreign keys have a deletion policy** — what happens to children when the parent
is deleted:

```
   DELETE product 12  ──▶  what about the Addas pointing at it?
   ┌──────────────┬────────────────────────────────────────────────┐
   │ RESTRICT     │ refuse the delete  ← the safe default. My money │
   │ / NO ACTION  │                      paths want exactly this.   │
   │ CASCADE      │ delete the children too  ← convenient, lethal   │
   │ SET NULL     │ orphan them (child.parent_id = NULL)            │
   └──────────────┴────────────────────────────────────────────────┘
   For anything financial: RESTRICT. Always. A CASCADE on a ledger is
   a single statement that silently erases a paper trail.
```

> 💡 **Samjho aise:** Constraint register ke khaane pe **chhapi hui sharth** hai —
> "yeh khaana khaali nahi ho sakta", "yeh number do baar nahi aa sakta", "minus
> nahi ho sakta". Munshi naya ho, jaldi mein ho, aadhi neend mein ho — sharth
> chhapi hui hai, entry **wahin ruk jaayegi**. Software bhool sakta hai; chhapa
> hua rule nahi bhoolta. Aur jab ERROR aata hai, wo system ka **kharab hona nahi,
> system ka kaam karna** hai.

# Real World Example (My ERP)
My database carries **137 CHECK constraints** and **271 foreign keys**. Real
definitions, straight from the catalogue:

```sql
wsc_verified_quantity_nonneg
   CHECK ((verified_quantity IS NULL) OR (verified_quantity >= 0))
wsc_expected_rate_nonneg
   CHECK ((expected_rate IS NULL) OR (expected_rate >= 0))
wsc_expected_earning_nonneg
   CHECK ((expected_earning IS NULL) OR (expected_earning >= 0))
wsc_gamd_nonneg_sum_positive
   CHECK (good_quantity >= 0 AND alter_quantity >= 0 AND missing_quant…)
```

Read the first three carefully — they say **"NULL or non-negative"**, not just
`>= 0`. That is chapter 4 and chapter 13 shaking hands: *unknown* is permitted,
*negative* is not. A wage that hasn't been calculated yet is legitimate; a
negative wage is impossible. The schema encodes that distinction exactly.

On `production_adda`:
```
 production_adda_pkey        PRIMARY KEY (id)
 production_adda_code_key    UNIQUE (code)
 …_product_id_…_fk           FOREIGN KEY (product_id)
                             REFERENCES production_product(id)
                             DEFERRABLE INITIALLY DEFERRED     ← see below
```

**Django's `DEFERRABLE INITIALLY DEFERRED`** is worth understanding: FK checks are
postponed to `COMMIT` rather than checked per statement. That lets a transaction
insert rows in an inconvenient order (child before parent) as long as everything
is consistent *by the end*. It is a deliberate Django choice, and a genuinely
senior-level detail to be able to explain.

**A Django 5.0.1 gotcha from my own codebase:** `CheckConstraint` takes
`check=`, **not** `condition=`. Getting this wrong is a migration that won't build.

# Visual Diagram
```
        A NEGATIVE WAGE TRIES TO GET IN
   ────────────────────────────────────────────────────────────
     amount = -500
         │
         ├─▶ FORM        ✗ maybe caught … unless it's a script
         │
         ├─▶ SERVICE     ✗ maybe caught … unless this path forgot
         │
         └─▶ CONSTRAINT  ████ REFUSED ████
                         ERROR: new row violates check constraint
                                "wsc_expected_earning_nonneg"
   ────────────────────────────────────────────────────────────
     the row is NOT written. the transaction fails. the books stay clean.
     even if every layer above had a bug today.
```

# Practical — try it yourself
```sql
-- 1. read the rules on any table (no guessing — ask the catalogue)
SELECT conname, pg_get_constraintdef(oid)
FROM pg_constraint
WHERE conrelid = 'production_workerstagecontribution'::regclass AND contype = 'c';

-- 2. count the walls guarding my whole database (REAL)
SELECT
  (SELECT count(*) FROM pg_constraint WHERE contype='c' AND connamespace='public'::regnamespace) AS checks,
  (SELECT count(*) FROM pg_constraint WHERE contype='f' AND connamespace='public'::regnamespace) AS fkeys;
--  137 | 271

-- 3. WATCH A CONSTRAINT REFUSE YOU — safe, nothing persists:
BEGIN;
  INSERT INTO production_adda (code, status, created_at, updated_at, product_id)
  VALUES ('3-PATTI-018', 'in_progress', now(), now(), 1);
  -- ERROR:  duplicate key value violates unique constraint "production_adda_code_key"
  -- DETAIL: Key (code)=(3-PATTI-018) already exists.
ROLLBACK;
--    ^ that ERROR is the system WORKING. Two Addas can never share a code.

-- 4. try to break referential integrity — also safe:
BEGIN;
  INSERT INTO production_adda (code, status, created_at, updated_at, product_id)
  VALUES ('COURSE-TEST-001', 'in_progress', now(), now(), 999999);
  -- product 999999 does not exist → FK violation (raised at COMMIT, because the
  -- constraint is DEFERRABLE INITIALLY DEFERRED — try COMMIT and watch)
ROLLBACK;

-- 5. see NOT NULL and types together
\d production_adda
```

# Production Walkthrough
The live schema carries **137 CHECK constraints and 271 foreign keys**. What they do in practice:
- **They hold when code is wrong.** The audit's P0 bug (multi-lane Pattern Design unstartable) was a *code* bug; no bad data reached the tables, because the constraints had nothing invalid to accept.
- **`production_adda_code_key`** is what makes concurrent Adda creation safe — two managers cannot mint one code even in the same millisecond.
- **`wsc_gamd_nonneg_sum_positive`** enforces the good/alter/missing invariant at the row level, which is why quantity reports can be trusted without re-validating in every view.
- FKs are `DEFERRABLE INITIALLY DEFERRED` (Django's default), so a transaction can insert children before parents as long as it ends consistent.

# Debugging Guide
"I got a constraint error":
1. **Read the constraint name.** It was named deliberately (`wsc_expected_earning_nonneg`) and tells you the rule you broke.
2. **`pg_get_constraintdef()`** prints the exact expression — no guessing.
3. **Decide who is wrong: you or the rule.** Nine times out of ten the rule is right and your data is wrong. Removing a constraint to make an error go away is how corrupt data enters a system.
4. **FK violation on insert?** The parent does not exist (or not yet — remember deferred checks fire at COMMIT).
5. **FK violation on delete?** Something still points at this row. That is the constraint doing its job (ch 12's soft-state is usually the right answer).

# Performance Notes
- Constraints cost a check on **write**, not on read — cheap, and the correctness is free at read time.
- FKs need an index on the referencing column to make deletes fast; Django creates it.
- Adding a constraint to a big table validates every existing row and takes a strong lock. Use `NOT VALID` then `VALIDATE CONSTRAINT` to split that into a fast add plus a gentler scan (ch 19).
- UNIQUE constraints are backed by an index — you get lookup speed as a bonus.

# Security Considerations
- Constraints are the **last** wall in the validation chain and the only one an attacker cannot bypass by finding an unguarded code path. A successful injection still cannot write a negative wage here (ch 22).
- Never disable constraints "temporarily" on a live money table; that window is exactly when bad data arrives.
- FK `RESTRICT` prevents an attacker (or a bug) from erasing a parent row to orphan its audit trail.

# Architecture Decisions
- **Both app-level and DB-level validation** — the app gives good messages, the database gives guarantees.
- **`RESTRICT` on financial references, never `CASCADE`** — one delete must not silently take a paper trail with it.
- **"NULL or non-negative"** rather than plain `>= 0`, so *unknown* stays legal and *impossible* stays illegal (ch 04).
- **Cross-row invariants live in services + reconciliation**, not in constraints, because a CHECK cannot see other rows.

# Best Practices
- Name constraints for the rule, not the table — the name is the error message.
- Write the CHECK when you write the column, not "later".
- Treat a constraint error in a test as a *pass* for the constraint.
- In Django 5.0.1 use `CheckConstraint(check=…)`, not `condition=`.

# Beginner Mistakes
- Treating a constraint error as "the database is broken". It is the database
  doing its only job.
- Validating **only** in application code — fine until a script, a shell, or a new
  endpoint skips it.
- `ON DELETE CASCADE` on financial or historical tables. One parent delete quietly
  erases the audit trail.
- Using `CHECK (x >= 0)` where NULL is legitimate — you accidentally forbid
  "unknown". My schema's `(x IS NULL) OR (x >= 0)` is the correct shape (ch 04).
- Adding a constraint to a huge live table without thinking about the lock — every
  existing row must be validated (ch 19).
- In Django 5.0.1: `CheckConstraint(condition=…)` instead of `check=…`.

# Interview Questions
- **Junior:** *Name the constraint types.* — PRIMARY KEY, FOREIGN KEY, UNIQUE, NOT NULL, CHECK (+ EXCLUDE in Postgres for the bonus point).
- **Junior:** *Difference between PRIMARY KEY and UNIQUE?* — a PK is unique **and** not-null and there is one per table; UNIQUE columns may allow NULLs and you can have many.
- **Mid:** *What happens when you delete a row that others reference?* — depends on the FK action: RESTRICT/NO ACTION refuses, CASCADE deletes children, SET NULL orphans them. For money: RESTRICT.
- **Mid:** *Validate in the app or the database?* — **both**. The app gives good error messages; the database guarantees the invariant when app code is wrong or bypassed. Cite a real system (mine: 137 CHECKs behind a service layer).
- **Senior:** *What does DEFERRABLE INITIALLY DEFERRED mean and why does Django use it?* — FK checks happen at COMMIT instead of per statement, so a transaction can write rows in any order provided it ends consistent; it makes ORM insert ordering and fixture loading practical.
- **Senior:** *How do you add a NOT NULL/CHECK constraint to a large table with minimal downtime?* — add it `NOT VALID` first (new rows checked, existing rows not), backfill offending rows, then `VALIDATE CONSTRAINT` (which takes a weaker lock than a full add).
- **Staff:** *Which invariants can constraints NOT express, and where do those live?* — anything spanning many rows or tables ("settlement total = sum of its lines", "only one active task per worker per stage" partially yes via partial unique indexes, but cross-aggregate rules no). Those belong in the service layer plus reconciliation checks — exactly the split this project uses.

### Why interviewers ask these — and the answer that separates levels

| Testing for | Weak answer | What lands |
|---|---|---|
| App-level or database-level validation? | "We validate in the app, so the DB does not need to." | **Both, for different jobs.** The app gives a good error message; **the database guarantees the invariant when app code is wrong or bypassed** — a shell, a script, a migration, a second service. This system has **137 CHECKs** *behind* a service layer, not instead of one. |
| Do you know what an FK does on delete? | "It stops you deleting the parent." | It depends on the **action**: `RESTRICT`/`NO ACTION` refuses · `CASCADE` deletes children · `SET NULL` orphans them. **For money: RESTRICT** — a cascade that silently deletes ledger rows is unrecoverable. |
| Do you know DEFERRABLE, and why Django wants it? | "FK checks always happen immediately." | `DEFERRABLE INITIALLY DEFERRED` moves the check to **COMMIT**, so a transaction may write rows in **any order** provided it ends consistent. That is what makes ORM insert ordering and fixture loading practical at all. |
| Can you add a constraint to a big table without downtime? | "Add the constraint and wait." | Add it **`NOT VALID`** first (new rows checked, existing rows not) → backfill the offenders → **`VALIDATE CONSTRAINT`**, which takes a **weaker lock** than a full add. Otherwise you hold a lock over a full table scan. |

**The killer follow-up:** *"Which invariants can a constraint NOT express?"* — anything spanning many rows or tables: *"settlement total = sum of its lines"*, cross-aggregate rules, "at most N of X" beyond what a partial unique index covers. Those live in the **service layer plus reconciliation**. Someone who thinks constraints can express everything has not tried to constrain a total.

# Revision Notes
- Types: NOT NULL · UNIQUE · PRIMARY KEY · FOREIGN KEY · CHECK (· EXCLUDE).
- FK actions: **RESTRICT** for money · CASCADE is dangerous · SET NULL orphans.
- Allow unknown, forbid impossible: `CHECK (x IS NULL OR x >= 0)`.
- Chain: form → service → **constraint** (the wall that always holds).
- Cross-row rules cannot be constraints — they belong in services.

# Cheat Sheet
- NOT NULL · UNIQUE · PRIMARY KEY · FOREIGN KEY · CHECK (· EXCLUDE)
- FK actions: **RESTRICT** (money!) · CASCADE (dangerous) · SET NULL
- constraint errors = the system working, not failing
- allow unknown, forbid impossible: `CHECK (x IS NULL OR x >= 0)`
- validation chain: form → service → **constraint** (the wall that always holds)
- read rules with `pg_get_constraintdef()`; Django 5.0.1 wants `check=`

# My ERP Section
| Rule | Where |
|---|---|
| 137 CHECKs / 271 FKs | the live schema (`pg_constraint`) |
| Non-negative money | `wsc_expected_earning_nonneg`, `wsc_expected_rate_nonneg` |
| Quantity sanity | `wsc_gamd_nonneg_sum_positive` (good/alter/missing) |
| One code per Adda | `production_adda_code_key` (UNIQUE) |
| Constraints as the last wall | [kos: validation-chain](../../kos/concepts/patterns/validation-chain.md) · [constraints](../../kos/concepts/postgresql/constraints.md) |
| Declared in code as | `CheckConstraint(check=…)` in `Meta.constraints` |

# Practice Tasks
1. **Read the code:** find a `CheckConstraint` in `config/production/models/worker_task.py`. Match it to the live definition via `pg_get_constraintdef()`.
2. **Debug:** inside `BEGIN … ROLLBACK`, violate three different constraints (unique, FK, check). Collect the three error texts — that is your future debugging vocabulary.
3. **Design:** propose a constraint for "a stage cannot be completed before it was started". Write it, then say why it *can* be a CHECK (hint: same row).
4. **Architecture:** "settlement total must equal the sum of its lines" cannot be a CHECK. Explain why, and say exactly where that rule lives instead.

# Homework
1. List every CHECK constraint on `production_workerstagecontribution` with its definition. Which ones say "NULL or non-negative", and why does that matter?
2. Inside `BEGIN … ROLLBACK`, try inserting a duplicate Adda code. Copy the exact error text into your notes — that is what a working system sounds like.
3. Count CHECKs and FKs in the whole database. Then pick one FK and describe, in words, exactly which delete it would refuse.

# Further Reading & Live Resources
- [Postgres constraints docs](https://www.postgresql.org/docs/current/ddl-constraints.html) — readable, with examples
- [Postgres ALTER TABLE (NOT VALID / VALIDATE)](https://www.postgresql.org/docs/current/sql-altertable.html)
- [Django constraints](https://docs.djangoproject.com/en/5.0/ref/models/constraints/)
