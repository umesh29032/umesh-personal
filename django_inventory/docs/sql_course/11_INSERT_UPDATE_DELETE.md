---
id: sql-course-11-insert-update-delete
type: lesson
status: active
owner: handwritten
scope: sql, postgresql — database fundamentals taught from this ERP
anchors: config/expense/services/settlement_service.py, config/production/services/pool_service.py
verified: 2026-08-01
---

# 11 — INSERT, UPDATE, DELETE

> Part of [SQL From Zero](00_COURSE_OVERVIEW.md). Prev: [10](10_Window_Functions.md) · Next: [12 — The Append-Only Money Philosophy](12_Append_Only_Money.md).

# Learning Objectives
By the end of this chapter you can:
- write INSERT / UPDATE / DELETE and read the affected-row receipt
- state what happens when you forget the WHERE — and why nothing warns you
- use `BEGIN … ROLLBACK` as a seatbelt while learning
- explain why this project routes every write through a service

# Purpose
To learn the three verbs that **change** data — and to learn them with the fear
they deserve. Everything before this chapter was safe. From here on, a missing
word can erase a factory.

# The Problem
`SELECT` asks. Sooner or later I must *tell*: a new cloth colour, a corrected
label, a cancelled row. But unlike a UI, SQL has **no "are you sure?" dialog, no
undo button, and no trash folder.** The statement runs, the rows change, and the
old values are gone. The discipline in this chapter is not optional decoration —
it is the difference between a career and an incident.

# Theory (from zero)

```
        ┌──────────────────────────────────────────────────────────┐
        │  THE THREE WRITE VERBS — and how much they can destroy   │
        ├──────────────────────────────────────────────────────────┤
        │  INSERT   adds a new row          ░░ low risk            │
        │  UPDATE   changes existing rows   ▓▓▓▓▓▓ HIGH — no undo   │
        │  DELETE   removes rows            ████████ HIGHEST        │
        └──────────────────────────────────────────────────────────┘
                     the WHERE clause is the only thing
                     standing between you and "all rows"
```

**INSERT** — add a row:
```sql
INSERT INTO raw_materials_clothcolor (name, hex_code, is_active, created_at, updated_at)
VALUES ('Course Maroon', '#800000', true, now(), now());
```
Postgres bonus: `... RETURNING id;` hands back the new row's id in the same trip.

**UPDATE** — change rows that match:
```sql
UPDATE raw_materials_clothcolor SET hex_code = '#900000' WHERE name = 'Course Maroon';
```

**DELETE** — remove rows that match:
```sql
DELETE FROM raw_materials_clothcolor WHERE name = 'Course Maroon';
```

### The one diagram to burn into memory

```
   UPDATE clothcolor SET hex='#900000' WHERE name='Maroon';
   └──────────────────────────────────┘ └──────────────────┘
            what to change                 WHICH rows
                                                │
                    ┌───────────────────────────┴───────────────────────────┐
                    │  forget this part …                                    │
                    ▼                                                        ▼
   UPDATE clothcolor SET hex='#900000';          ← EVERY colour becomes maroon
   DELETE FROM clothcolor;                       ← EVERY colour is gone
   ─────────────────────────────────────────────────────────────────────────
   no prompt · no undo · no recycle bin · the only route back is a BACKUP (ch 20)
```

**The professional habit — the SELECT-first rule:**

```
   step 1   SELECT * FROM t WHERE <my condition>;   ← LOOK at the rows
   step 2   ...are these EXACTLY the rows I mean?   ← human check
   step 3   swap SELECT * for UPDATE/DELETE, keep the WHERE unchanged
```

**The learner's seatbelt — `BEGIN … ROLLBACK`:** wrap any experiment in a
transaction and take it back (ch 17 explains the machinery):

```
   BEGIN;                          ← open a pencil draft
     DELETE FROM clothcolor;       ← "everything is gone" (only inside my session)
     SELECT count(*) ...;          ← 0
   ROLLBACK;                       ← page torn up; nothing ever happened
     SELECT count(*) ...;          ← all rows back
```

> 💡 **Samjho aise:** SQL mein `UPDATE`/`DELETE` likhna **register pe seedha
> pen chalane** jaisa hai — koi "pakka?" nahi poochhta, koi rubber nahi hota.
> Aur `WHERE` bhool gaye to pen **poore register** pe chal jaata hai. Isi liye
> pehle **SELECT se dekh lo** kitni entry aati hain, phir wahi `WHERE` rakh ke
> verb badlo. Seekhne ke liye `BEGIN … ROLLBACK` — pencil se likho, phir page
> phaad do.

# Real World Example (My ERP)
Here is the important part: **my ERP almost never uses two of these three verbs
on important data**, and that is a deliberate architectural choice.

```
        WHAT MY CODEBASE ACTUALLY DOES
   ┌────────────────────────┬─────────────────────────────────────────┐
   │ WorkerLedgerEntry (₹)  │ INSERT only. Never UPDATE. Never DELETE │
   │                        │ a mistake → INSERT a reversing entry    │
   ├────────────────────────┼─────────────────────────────────────────┤
   │ records / config       │ soft-state: is_active=false,            │
   │                        │ cancelled_at=now()  — the row SURVIVES  │
   ├────────────────────────┼─────────────────────────────────────────┤
   │ who may write at all   │ services only (config/<app>/services/)  │
   │                        │ views never write · one writer / table  │
   └────────────────────────┴─────────────────────────────────────────┘
```

`ledger_service` is the **only** writer of `WorkerLedgerEntry`; `history_service`
the only writer of the `*History` tables. That is why "let me just fix this row in
dbshell" is nearly always the wrong move here: the service layer *is* where the
rules live, and a hand-edit bypasses every one of them.

# Visual Diagram
```
   MUTABLE style (most apps)          APPEND-ONLY style (my money tables)
   ─────────────────────────          ─────────────────────────────────
   row 7: amount = 500                row 7: amount = 500      ← stays forever
        ↓ UPDATE                      row 8: amount = -500     ← reversal
   row 7: amount = 400                row 9: amount = 400      ← corrected
        ↓ history: GONE               balance = 500-500+400 = 400
   "who changed it, when, why?"       every step visible, auditable, provable
        └── unanswerable              └── ch 12 is entirely about this
```

# Practical — try it yourself
First get a safe playground — never learn writes on real data:
```bash
./scripts/db.sh branch sql_practice --use     # a full copy of my factory
env/bin/python config/manage.py dbshell --settings=config.settings.local
```
```sql
-- INSERT, and get the new id back (Postgres nicety)
INSERT INTO raw_materials_clothcolor (name, hex_code, is_active, created_at, updated_at)
VALUES ('Course Maroon', '#800000', true, now(), now())
RETURNING id, name;

-- SELECT-FIRST discipline, every single time:
SELECT id, name, hex_code FROM raw_materials_clothcolor WHERE name = 'Course Maroon';
-- ...exactly one row, the one I mean? then and only then:
UPDATE raw_materials_clothcolor SET hex_code = '#900000', updated_at = now()
WHERE name = 'Course Maroon';

-- how many rows did that touch? psql tells you: "UPDATE 1"
-- if it ever says "UPDATE 143", you just learned something the hard way.

DELETE FROM raw_materials_clothcolor WHERE name = 'Course Maroon';   -- "DELETE 1"
```
The seatbelt, run for real (safe even on `inventory_db` — nothing persists):
```sql
BEGIN;
  SELECT count(*) FROM raw_materials_clothcolor;    -- e.g. 21
  DELETE FROM raw_materials_clothcolor;             -- "DELETE 21" … terrifying
  SELECT count(*) FROM raw_materials_clothcolor;    -- 0   (only in MY session)
ROLLBACK;
  SELECT count(*) FROM raw_materials_clothcolor;    -- 21  — nothing happened
```
Come home when you are done: `./scripts/db.sh use inventory_db`

# Production Walkthrough
On the live system these verbs are **not** typed by hand:
- Every write goes through a service in `config/<app>/services/`, inside `@transaction.atomic` (ch 17). A view never writes.
- Money tables see **INSERT only** — `ledger_service` is their sole writer (ch 12).
- A hand-edit in `dbshell` bypasses the service's validation, its audit rows, and its transaction boundary. It can leave the system in a state the app believes is impossible.
- The one legitimate raw-SQL write path in this codebase is an advisory lock (`pg_advisory_xact_lock`) — a coordination primitive, not a data change (ch 18).

# Debugging Guide
"I changed a row and something broke":
1. **Read the receipt.** psql prints `UPDATE 1` / `DELETE 43`. If the number surprises you, stop and investigate before doing anything else.
2. **Was it inside a transaction?** If yes, `ROLLBACK` now. If you already committed, you need a backup (ch 20).
3. **Did you skip a service?** Then the app's invariants may now be violated — check the related tables the service would also have written (history, ledger).
4. **Check `updated_at`.** A manual UPDATE that forgot it makes the audit trail lie.
5. **FK error on DELETE** is the database protecting you (ch 13) — the fix is almost never to remove the constraint.

# Performance Notes
- Every INSERT/UPDATE/DELETE must also update **every index** on the table — that is the write cost of the indexes you added in ch 14.
- Postgres `UPDATE` writes a **new row version** (MVCC, ch 18); heavily updated tables accumulate dead tuples until autovacuum reclaims them.
- Bulk work: prefer one statement over a loop of statements; `bulk_create` beats N inserts.
- `TRUNCATE` is far faster than `DELETE` for emptying a table — and far less recoverable.

# Security Considerations
- **Never build a write statement from user input** (ch 22). Writes are where injection does permanent damage.
- Authorisation belongs before the write, in the service. A view that trusts an id from the request body can be made to modify someone else's row.
- Destructive statements deserve an approval path, not just a permission bit — this project requires typed confirmation for database deletion (`db.sh delete --yes-delete <name>`).

# Architecture Decisions
- **Services own all multi-row writes** — one enforcement point per table means invariants cannot be forgotten by a new code path.
- **Money is append-only** (ch 12): the correction for a wrong entry is a reversing entry, never an edit.
- **Soft-state over DELETE** for records (`is_active=false`, `cancelled_at`) so the evidence survives.
- **Un-completing a lesson is allowed** in the learning app — a deliberate contrast that shows these rules are *chosen per domain*, not cargo-culted.

# Best Practices
- SELECT-first, always: run the WHERE as a SELECT, eyeball the rows, then swap the verb.
- Learn on a branch (`db.sh branch sql_practice --use`), never on real data.
- Wrap experiments in `BEGIN … ROLLBACK`.
- Use `RETURNING` instead of a second query to fetch what you just wrote.

# Beginner Mistakes
- **`UPDATE`/`DELETE` without `WHERE`.** The single most expensive class of SQL
  accident in history. No prompt, no undo.
- Assuming a `WHERE` matched one row when it matched forty. **Read psql's
  "UPDATE n" / "DELETE n" reply** — it is your receipt.
- Writing on the real database "just this once" instead of on a branch.
- Hand-editing rows that a service owns — bypasses business rules, audit trails
  and single-writer discipline, and leaves the app's assumptions broken.
- Forgetting `updated_at = now()` on a manual UPDATE, so the audit trail lies.
- `DELETE`ing a row other tables point at → FK error (ch 13). The error is the
  database *protecting* you.

# Interview Questions
- **Junior:** *`DELETE` vs `TRUNCATE` vs `DROP`?* — DELETE removes rows (supports WHERE, transactional, fires triggers); TRUNCATE empties the whole table fast (no WHERE); DROP removes the table itself. Escalating destruction.
- **Junior:** *How do you undo a `DELETE`?* — you don't. Either it was inside an uncommitted transaction (ROLLBACK), or you restore from backup. Which is why backups exist (ch 20).
- **Mid:** *How do you safely run a destructive statement in production?* — SELECT the same WHERE first, wrap in an explicit transaction, verify the affected-row count, then COMMIT; take a backup beforehand for anything irreversible.
- **Mid:** *What does `RETURNING` give you?* — the affected rows (e.g. a generated id) without a second round-trip; Postgres supports it on INSERT/UPDATE/DELETE.
- **Senior:** *How do you correct a posted financial transaction?* — never edit it; post a compensating/reversing entry so history stays intact (ch 12). **Strong differentiator answer.**
- **Staff:** *Why route all writes through a service layer instead of letting views write?* — one enforcement point per table means invariants, audit rows, and transaction boundaries cannot be forgotten by a new code path; it makes "who can change this?" answerable. This project's single-writer rule (`ledger_service`, `history_service`) is exactly that.

### Why interviewers ask these — and the answer that separates levels

| Testing for | Weak answer | What lands |
|---|---|---|
| Do you know the escalating three? | "DELETE and TRUNCATE both empty a table." | `DELETE` = rows, honours `WHERE`, transactional, fires triggers · `TRUNCATE` = whole table, fast, **no WHERE** · `DROP` = the table itself. Escalating destruction — and only the first is selective. |
| Do you know how to run a destructive statement safely? | "I write the DELETE carefully and check it twice." | The sequence: **`SELECT` the same `WHERE` first** → wrap in an explicit transaction → **verify the affected-row count** → then `COMMIT`. Backup first for anything irreversible. Careful reading is not a control; the row count is. |
| Do you know `RETURNING`? | "I insert, then select it back to get the id." | `RETURNING` gives the affected rows — including a generated id — **without a second round-trip**, and works on INSERT/UPDATE/DELETE in Postgres. Two queries where one would do is a habit worth breaking. |
| Do you know how to correct posted money? | "`UPDATE` the row with the right amount." | **Never edit it — post a reversing/compensating entry** so history stays intact (ch 12). Strong differentiator: most candidates say "update it", which destroys the audit trail you would need to prove the correction. |

**The killer follow-up:** *"Why do all writes go through a service instead of the view?"* — one enforcement point per table means invariants, audit rows and transaction boundaries **cannot be forgotten by a new code path**, and *"who can change this table?"* has a one-word answer. This project names them: `ledger_service`, `history_service`.

# Revision Notes
- `INSERT INTO t (cols) VALUES (…) RETURNING id;`
- `UPDATE t SET c = v WHERE …;` · `DELETE FROM t WHERE …;`
- **No WHERE = every row.** No prompt, no undo.
- Read the `UPDATE n` receipt — it is your only warning.
- In this project: money = INSERT only · records = soft-state · writes = services.

# Cheat Sheet
- `INSERT INTO t (cols) VALUES (…) RETURNING id;`
- `UPDATE t SET c = v WHERE …;` · `DELETE FROM t WHERE …;`
- **no WHERE = every row.** No prompt, no undo, no bin.
- SELECT-first, then swap the verb · read the "UPDATE n" receipt
- learning? `BEGIN; … ROLLBACK;`
- in THIS project: money = INSERT only · records = soft-state · writes = services only

# My ERP Section
| Rule | Where it lives |
|---|---|
| Money is append-only | `WorkerLedgerEntry` + `ledger_service` (sole writer) |
| History is append-only | `*History` tables + `history_service` (sole writer) |
| Soft-state over delete | `is_active`, `cancelled_at`, `voided_*` fields |
| Views never write | all writes in `config/<app>/services/` |
| Safe practice ground | `./scripts/db.sh branch sql_practice --use` |
| Undo of last resort | `./scripts/db.sh save` / `restore` (ch 20) |

# Practice Tasks
1. **Read the code:** open `config/expense/services/ledger_service.py`. List every verb it uses. Is there an UPDATE or DELETE anywhere?
2. **Debug:** on a practice branch, run an UPDATE without a WHERE inside `BEGIN`, read the receipt, then ROLLBACK. Write down the number you saw.
3. **Design:** the owner wants to "fix" a wrong ledger amount. Write the two statements you would actually run (hint: neither is an UPDATE) and the reason field you would require.
4. **Architecture:** argue when soft-delete is wrong — name a case where a real DELETE is the correct choice.

# Homework
1. On a practice branch: INSERT a colour with `RETURNING id`, UPDATE its hex, then DELETE it — reading the row-count receipt after each statement.
2. Run the `BEGIN; DELETE …; ROLLBACK;` seatbelt drill and watch the count go to 0 and back. Say out loud what COMMIT would have done.
3. Try to `DELETE FROM production_product WHERE code='3-PATTI';` on the practice branch. Read the error, and explain which chapter-13 rule saved you.

# Further Reading & Live Resources
- [Postgres INSERT](https://www.postgresql.org/docs/current/sql-insert.html) · [UPDATE](https://www.postgresql.org/docs/current/sql-update.html) · [DELETE](https://www.postgresql.org/docs/current/sql-delete.html)
- [postgresqltutorial: UPDATE](https://www.postgresqltutorial.com/postgresql-tutorial/postgresql-update/)
- [Postgres RETURNING](https://www.postgresql.org/docs/current/dml-returning.html)
