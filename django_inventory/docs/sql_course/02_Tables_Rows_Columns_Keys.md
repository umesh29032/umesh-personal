---
id: sql-course-02-tables-rows-columns-keys
type: lesson
status: active
owner: handwritten
scope: sql, postgresql — database fundamentals taught from this ERP
anchors: config/expense/services/settlement_service.py, config/production/services/pool_service.py
verified: 2026-08-01
---

# 02 — Tables, Rows, Columns, Keys

> Part of [SQL From Zero](00_COURSE_OVERVIEW.md). Prev: [01](01_What_Is_A_Database.md) · Next: [03 — Data Types & Money](03_Data_Types_And_Money.md).

# Learning Objectives
By the end of this chapter you can:
- read `\d <table>` and describe any table's shape out loud
- explain why a primary key is a meaningless number, and defend it
- find the table behind any Django model without asking anyone
- spot a foreign-key column on sight and say what it points at

# Purpose
To read a table's *shape* the way a mechanic reads an engine — using my own
`production_adda` as the engine — and to understand primary keys, the one idea
every later chapter stands on.

# The Problem
"Where is my Adda stored, exactly?" Until I can answer that at the column level,
every debugging session is guesswork. And when tables reference each other, they
need an identifier that never changes — names get renamed; something must not.

# Theory (from zero)
A **table** is one spreadsheet-like grid, fixed columns × unlimited rows.
- **Columns** = the shape, declared once (name + type + rules).
- **Rows** = the facts, one per real-world thing (one Adda, one worker, one ₹ entry).

**Primary key (PK):** the column that uniquely identifies each row — never NULL,
never duplicated. Django gives every table an auto-numbered `id`. Humans say
"3-PATTI-018"; the machine says "row 51". Machines use the number because numbers
are never renamed, retyped, or re-spelled.

**Naming convention:** Django creates tables as `<app>_<modelname>` — so `class
Adda` in the `production` app = table `production_adda`. Knowing this, I can find
ANY model's table without asking anyone.

### Why the machine points with numbers, not names

```
   ❌ POINTING WITH THE NAME               ✅ POINTING WITH THE id
   ─────────────────────────────          ─────────────────────────────
   adda.product = "3-PATTI"               adda.product_id = 12
                                          
   owner renames it to "3 Patti Shorts"   owner renames it to "3 Patti Shorts"
        │                                      │
        ▼                                      ▼
   every Adda now points at a             product row 12 is STILL row 12
   product that no longer exists          nothing else changes. ✅
   → 10 broken rows, silently
   ─────────────────────────────────────────────────────────────────────
   `id` has ONE job: be unique and NEVER change. It carries no meaning,
   and that meaninglessness is exactly what makes it trustworthy.
```

### Anatomy of one row — the vocabulary in a single picture

```
                COLUMNS (the shape — declared once, in the model)
        ┌────┬─────────────┬────────────┬──────────────┬────────────┐
        │ id │ code        │ status     │ completed_at │ product_id │
        ├────┼─────────────┼────────────┼──────────────┼────────────┤
  ROW ──│ 51 │ 3-PATTI-018 │ completed  │ 2026-07-27…  │     12     │
        ├────┼─────────────┼────────────┼──────────────┼────────────┤
        │ 52 │ T-SHIRT-004 │ in_progress│    NULL      │     48     │
        └────┴─────────────┴────────────┴──────────────┴────────────┘
          ▲         ▲                          ▲             ▲
          │         │                          │             │
      PRIMARY   business name             NULL = "not         FOREIGN KEY
      KEY       (UNIQUE, but not          finished yet"       (a pointer to
      (identity) the identity)            not "zero" (ch 04)  another table)
```

> 💡 **Samjho aise:** Table ek **register ka chhapa hua page-format** hai — columns
> pehle se chhape khaane, rows ek-ek entry. `id` har entry ka **serial number** hai:
> kabhi repeat nahi hota, kabhi badalta nahi. Naam badal sakta hai ("3-PATTI" se
> "3 Patti Shorts"), serial nahi — isi liye machine **hamesha serial se** ishaara
> karti hai, naam se kabhi nahi. Naam insaanon ke liye, serial machine ke liye.

# Real World Example (My ERP)
`\d production_adda` in dbshell — its actual shape today:

```
column            type                        meaning
────────────      ─────────────────────       ───────────────────────────
id                bigint                      the primary key
created_at        timestamp with time zone    born when (TimeStampedModel)
updated_at        timestamp with time zone    last touched
code              character varying           "3-PATTI-018" — business name, UNIQUE
status            character varying           in_progress / completed / …
started_at        timestamp with time zone
completed_at      timestamp with time zone    NULL until actually done (ch 04)
created_by_id     bigint                      → accounts_user.id
product_id        bigint                      → production_product.id
current_stage_id  bigint                      → the stage it's currently on
```

Three things hiding in that shape: (1) `id` = PK; (2) the `*_id` columns are
**pointers to rows in other tables** — foreign keys, chapter 07; (3) `created_at`
/`updated_at` on *every* table — that's the shared `TimeStampedModel` from the
`core` app appearing at the SQL level.

# Visual Diagram
```
 production_adda                          production_product
 ┌────┬─────────────┬────────────┬────┐   ┌────┬─────────┬─────────┐
 │ id │ code        │ status     │p_id│   │ id │ code    │ name    │
 ├────┼─────────────┼────────────┼────┤   ├────┼─────────┼─────────┤
 │ 51 │ 3-PATTI-018 │ completed  │ 12 │──▶│ 12 │ 3-PATTI │ 3 Patti │
 │ 52 │ T-SHIRT-004 │ in_progress│ 48 │──▶│ 48 │ T-SHIRT │ T-Shirt │
 └────┴─────────────┴────────────┴────┘   └────┴─────────┴─────────┘
   PK ▲                        pointer uses the NUMBER, never the name
```

# Practical — try it yourself
```
\d production_adda          -- full shape: columns, types, indexes, FKs
\d accounts_user            -- my users table (spot `role_id`, `is_superuser`)
\dt production_*            -- every table the production app owns
SELECT id, code, status FROM production_adda ORDER BY id DESC LIMIT 5;
```
Real output of that SELECT today:
```
 3-PATTI-018 | completed
 T-SHIRT-004 | in_progress
 NIKKAR-002  | in_progress
 ...
```

# Production Walkthrough
The same 115 tables exist on the server — created by the identical migration history, so the shape you learn locally *is* the production shape (ch 19). Two live consequences:
- **`production_adda.code` is UNIQUE**, so two managers creating a batch at the same moment cannot mint the same code. That guarantee is enforced by the database, not by hope (ch 13, 18).
- **Codes are minted under a row lock** on the Product (`adda_service`), which is why they are gap-free per product — a detail that only matters once two people work at once.

# Debugging Guide
"This row looks wrong" — work from identity outwards:
1. **Get its `id`.** Everything else is a lookup from there; business codes can be renamed, `id` cannot.
2. **`\d <table>`** to see what fields even exist before theorising about missing data.
3. **Follow the pointers.** A `*_id` of `NULL` and a `*_id` pointing at a deleted-looking row are different bugs (ch 04, 13).
4. **Check `created_at` / `updated_at`.** They come free from `TimeStampedModel` and often answer "when did this change?" immediately.

# Performance Notes
- Primary keys are indexed automatically, so lookup-by-`id` is the fastest access you have (ch 14).
- Django indexes ForeignKey columns too, which is what makes the JOINs in ch 07 fast without tuning.
- Column *order* costs nothing to query; row *width* does — very wide rows mean fewer per page and more disk reads.

# Security Considerations
- Sequential integer ids are guessable. Any view that takes an id from the URL must check *authorisation*, not just existence — this project's access matrix probes exactly that (300 role×URL probes in the audit).
- Never expose a raw `id` as a secret (a "share by link" feature must not use `?id=51`).

# Architecture Decisions
- **Surrogate key (`id`) + UNIQUE natural key (`code`)** — chosen so renaming a product costs one row instead of a migration across 271 foreign keys.
- **`TimeStampedModel` on every table** — one abstract base in the `core` app rather than 100 copies of two fields.
- **Table-per-model, no clever inheritance tricks** for the money tables: boring shapes are auditable shapes.

# Best Practices
- Read `\d <table>` *before* debugging; guessing a schema wastes more time than checking it.
- Name the FK column `<thing>_id` and let Django do it — consistency is what makes the codebase navigable.
- Never make the business code the primary key.

# Beginner Mistakes
- Using the human name (`code`) as the cross-table pointer. Rename it once and
  every reference breaks. Point with `id`; make the name UNIQUE separately —
  exactly what my Adda table does.
- Assuming column order matters. It doesn't; only names do.
- Confusing a table (the grid) with the model (the Python class). Same thing,
  two languages: model = code-side, table = SQL-side.

# Interview Questions
- **Junior:** *What is a primary key?* — unique, non-NULL identifier per row.
- **Mid:** *Surrogate key (auto `id`) vs natural key (`code`) — which and why?* —
  surrogate: stable forever, meaningless on purpose; enforce the natural key
  with UNIQUE on the side. (My table is the textbook answer.)
- **Mid:** *How do you find the table behind a model?* — `<app>_<modelname>`
  lowercased (`production.Adda` → `production_adda`); confirm with `\dt` or
  `Model._meta.db_table`.
- **Senior:** *When would a composite PK make sense?* — pure join/link tables
  (e.g. a user↔skill link) where the pair IS the identity; even then Django
  prefers a surrogate + unique-together for simplicity.
- **Staff:** *Should the business code (`3-PATTI-018`) ever be the primary key?* —
  no. Natural keys leak business meaning into every referencing table, and the day
  the format changes (a prefix, a check digit, a merger) you rewrite every foreign
  key in the system. Use a surrogate `id` for identity and a UNIQUE constraint for
  the business rule — then a rename costs one row, not a migration across 271 FKs.

### Why interviewers ask these — and the answer that separates levels

| Testing for | Weak answer | What lands |
|---|---|---|
| Do you know identity from uniqueness? | "The primary key is the unique column." | A PK is **unique + NOT NULL + the row's identity**, referenced by every FK. Uniqueness alone is a `UNIQUE` constraint — you can have many of those and only one identity. |
| Surrogate vs natural key — do you have a reason? | "Just use the business code, it is already unique." | Surrogate `id` for **identity** (meaningless on purpose, therefore stable forever) + `UNIQUE` on the business code for **the rule**. Then renaming a code costs **one row**, not a migration across every referencing table. |
| Can you get from a model to its real table? | "Django handles the table names." | `<app>_<modelname>` lowercased — `production.Adda` → **`production_adda`**. Confirm with `Model._meta.db_table` or `\dt`. You cannot debug in `psql` without this. |
| Do you know when a composite PK is right? | "Composite keys are bad practice." | Legitimate on a pure **link table** where the pair *is* the identity — but Django prefers surrogate + `unique_together` because a composite PK makes every child FK wider and every join clumsier. |

**The killer follow-up:** *"The business wants to change the code format — add a prefix, a check digit, or merge two factories. What breaks?"* — with a surrogate key: one column update. With a natural key: every foreign key in the schema. This project has **271 FKs**; that is the whole argument.

# Revision Notes
- A table is columns (shape) × rows (facts).
- **PK = `id`**: unique, non-NULL, never reused, meaningless on purpose.
- `*_id` columns are pointers → foreign keys (ch 07).
- `<app>_<modelname>` finds any model's table.
- `\d <table>` is the x-ray. Use it first.

# Cheat Sheet
- table = grid; columns = declared shape; rows = facts
- PK = `id`: unique, non-NULL, never reused, machines point with it
- `<app>_<modelname>` finds any model's table
- `\d <table>` is the x-ray; read it before debugging anything

# My ERP Section
| Concept | Where in my project |
|---|---|
| PK on every table | Django auto `id` (bigint) |
| Natural key kept honest | `production_adda.code` UNIQUE |
| Shared timestamps | `core.TimeStampedModel` → `created_at`/`updated_at` everywhere |
| Table naming | `production_adda`, `expense_workerledgerentry`, `accounts_user` |

# Practice Tasks
1. **Read the code:** find the `Adda` model in `config/production/models/adda.py`. Match three of its fields to columns in `\d production_adda`.
2. **Debug:** pick any Adda's `id` and, using only `\d` output plus JOINs you already know from reading, find its product's name and who created it.
3. **Design:** the owner wants Adda codes to include the year (`3-PATTI-2026-018`). What breaks if `code` were the primary key? What breaks now, with a surrogate key? (This is the whole chapter in one question.)

# Homework
1. `\d expense_workerledgerentry` — find its PK, its two FK pointer columns, and
   the money column's type. Write them down.
2. Predict the table name for model `WorkerStageTask` in app `production`; verify with `\dt production_worker*`.
3. Explain to the wall why `product_id` stores 12 and not "3-PATTI".

# Further Reading & Live Resources
- [SQLBolt lesson on tables](https://sqlbolt.com/lesson/introduction)
- [Postgres docs: table basics](https://www.postgresql.org/docs/current/ddl-basics.html)
- [Postgres docs — Constraints](https://www.postgresql.org/docs/current/ddl-constraints.html) — primary keys, foreign keys, and what each one actually enforces
- [Postgres docs — Inheritance & partitioning](https://www.postgresql.org/docs/current/ddl-partitioning.html) — where "one table" stops being one table
- [Django docs — Models](https://docs.djangoproject.com/en/5.0/topics/db/models/) — how the tables in this chapter are declared in this project
- [Modern SQL — surrogate vs natural keys](https://modern-sql.com/concept/surrogate-key) — the choice this chapter makes, argued properly
- Sibling chapter: [13 — Constraints](13_Constraints.md) — keys are constraints; this is the rest of the family
