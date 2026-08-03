---
id: sql-course-07-joins
type: lesson
status: active
owner: handwritten
scope: sql, postgresql — database fundamentals taught from this ERP
anchors: config/expense/services/settlement_service.py, config/production/services/pool_service.py
verified: 2026-08-01
---

# 07 — JOINs: How Tables Point at Each Other

> Part of [SQL From Zero](00_COURSE_OVERVIEW.md). Prev: [06](06_Filtering_And_Expressions.md) · Next: [08 — GROUP BY & Aggregates](08_GROUP_BY_And_Aggregates.md).

# Learning Objectives
By the end of this chapter you can:
- read a foreign key and say, out loud, what it points at and why it is a number
- write an INNER and a LEFT JOIN and **predict which rows each will drop**
- spot the row-multiplication trap *before* it silently doubles a report total
- choose `ON` vs `WHERE` correctly in a LEFT JOIN
- explain to an interviewer why a FK is a *rule* and a JOIN is an *act*

# Purpose
To learn the single idea that makes a database "relational": tables point at each
other with numbers, and `JOIN` follows the pointer. This is the chapter that turns
115 separate tables into one connected factory.

# The Problem
`production_adda.product_id` holds `12`. Useless to a human. The product's *name*
lives in a different table. Every real screen in my ERP needs data from several
tables at once — the Adda list shows the product name, the worker's name, the
current stage. Without JOIN I would need one query per pointer (and that road ends
in the N+1 disaster of chapter 16).

# Theory (from zero)

**Foreign key (FK):** a column holding another table's `id`. `adda.product_id` →
`production_product.id`. It is a *stored rule*: Postgres refuses a `product_id`
that doesn't exist, and refuses to delete a product that Addas still point at
(ch 13). Why point with a number and not the name? Because names get renamed;
`id` never does (ch 02).

**JOIN** is the *act* of following that pointer in a query:

```sql
SELECT a.code, p.name
FROM production_adda a                       -- alias: a
JOIN production_product p ON p.id = a.product_id   -- the pointer, followed
```
Read aloud: *"for each Adda row, find the product row whose `id` equals this
Adda's `product_id`, and let me use columns from both."* `a` and `p` are
**aliases** — short nicknames, so `a.code` and `p.code` stay unambiguous.

**The four kinds:**

| JOIN | Keeps | My factory example |
|---|---|---|
| `JOIN` (= `INNER JOIN`) | only rows matching on **both** sides | Addas + their product |
| `LEFT JOIN` | **all** left rows; NULLs where the right has no match | all products + their Addas — *products with zero Addas still appear* |
| `RIGHT JOIN` | mirror of LEFT | rarely used; flip the table order instead |
| `FULL JOIN` | everything from both, NULLs on either side | reconciliation/"what's missing on each side" |

**The trap that inflates reports: row multiplication.** If one left row matches
**two** right rows, the left row appears **twice** in the output. Nothing is
wrong — that's the definition — but if you then `sum()` a left-side column, you
have double-counted it (ch 08). This is the mechanism behind almost every "my
report doubled" bug.

> 💡 **Samjho aise:** Do register hain — Adda-register aur Product-register.
> Adda wale mein sirf product ka **serial number** likha hai, naam nahi (naam
> badal sakta hai, serial nahi). JOIN wo **clerk** hai jo serial dekh kar doosre
> register se poora naam la deta hai. LEFT JOIN zid karta hai: *"doosre register
> mein kuch mile ya na mile, meri HAR entry list mein aayegi — khaali haath sahi."*
> Aur dhyaan: agar doosre register mein ek serial ke **do** entry hain, to pehli
> entry list mein **do baar** aayegi. Ginti tab dhoka de jaati hai.

# Real World Example (My ERP)
Real output, right now, from my database:

```
    code     |  name
 3-PATTI-018 | 3 Patti
 T-SHIRT-004 | T-Shirt
 NIKKAR-002  | Nikkar
```

And the LEFT JOIN lesson with real numbers: I have **19 products**, but an inner
join of products→addas produces only **28 rows** covering the products that
actually *have* Addas. Five products (`1-6`, `DEV-HUB`, `DEV-P3A`, `DEV-P3B`,
`DEV-TEE`) have **zero** Addas — an INNER JOIN would make them **invisible**.
A "products and their batch counts" report built with the wrong JOIN silently
omits every unused product.

# Visual Diagram
```
 INNER JOIN                          LEFT JOIN
 products   addas                    products   addas
 ┌──────┐   ┌──────┐                 ┌──────┐   ┌──────┐
 │3-PATTI│──▶│  10  │  ✓ shown       │3-PATTI│──▶│  10  │  ✓
 │NIKKAR │──▶│   2  │  ✓ shown       │NIKKAR │──▶│   2  │  ✓
 │DEV-TEE│   │      │  ✗ HIDDEN      │DEV-TEE│   │ NULL │  ✓ shown as 0
 └──────┘   └──────┘                 └──────┘   └──────┘
   "which products are used?"          "which products EXIST?" ← usually the question
```

# Practical — try it yourself
```sql
-- follow the pointer (REAL output above)
SELECT a.code, p.name
FROM production_adda a
JOIN production_product p ON p.id = a.product_id
ORDER BY a.id DESC LIMIT 3;

-- prove the hidden-rows problem (REAL: these five come back with 0)
SELECT p.code, count(a.id) AS addas
FROM production_product p
LEFT JOIN production_adda a ON a.product_id = p.id
GROUP BY p.code ORDER BY addas ASC, p.code LIMIT 5;
--  1-6 | 0 ·  DEV-HUB | 0 ·  DEV-P3A | 0 ·  DEV-P3B | 0 ·  DEV-TEE | 0

-- swap LEFT for JOIN and watch those five vanish:
SELECT p.code, count(a.id) FROM production_product p
JOIN production_adda a ON a.product_id = p.id
GROUP BY p.code ORDER BY 2 ASC LIMIT 5;

-- join two pointers at once: product AND the user who created the Adda
SELECT a.code, p.name, u.email
FROM production_adda a
JOIN production_product p ON p.id = a.product_id
JOIN accounts_user u ON u.id = a.created_by_id
ORDER BY a.id DESC LIMIT 3;
--  3-PATTI-018 | 3 Patti | umesh29mar@gmail.com
--  T-SHIRT-004 | T-Shirt | umesh29mar@gmail.com
--  NIKKAR-002  | Nikkar  | uat.super@factory.local

-- count(a.id) vs count(*) in a LEFT JOIN — the NULL lesson from ch 04:
-- count(*) counts the placeholder row too (giving 1 for zero-adda products);
-- count(a.id) correctly gives 0. Try both.
```

# Production Walkthrough
What a JOIN looks like when it is *live*, not in a tutorial:

- **The Adda list page** joins adda → product → user on every page load. It stays
  fast because both FK columns are indexed (ch 14) and Django fetches them in one
  query via `select_related` instead of one per row (ch 16).
- **The moment it breaks:** add a join to a *many* relation (an Adda's many stage
  records) and the page's row count multiplies. The list looks duplicated, and any
  `sum()` in a footer is now wrong — with no error anywhere.
- **How it is caught here:** the golden settlement tests assert exact rupee totals.
  A duplicating join changes a total, so the test fails loudly instead of a wrong
  number reaching a worker's payslip.

# Debugging Guide
When a JOIN result looks wrong, in this order:

1. **Count first.** `SELECT count(*)` with and without the join. If the count grew,
   you have row multiplication, not a filter bug.
2. **Check the ON column.** `ON p.id = a.product_id` — joining the wrong pair
   (`p.id = a.id`) still runs and returns confident nonsense.
3. **Look for silently dropped rows.** Swap `JOIN` for `LEFT JOIN`; if rows appear,
   your join was hiding them (the five zero-Adda products).
4. **Move right-side filters into `ON`** if you meant to keep unmatched left rows.
5. **Read the plan** (`EXPLAIN`, ch 15) — `Hash Join` vs `Nested Loop` tells you
   whether the planner thinks one side is tiny.

# Performance Notes
- A JOIN needs the FK column indexed on the **many** side. Django does this for
  ForeignKeys automatically, which is why these joins are fast without tuning.
- Join order is the planner's choice, not your `FROM` order — do not try to
  outsmart it; give it indexes and accurate statistics instead (ch 15).
- The real cost at scale is usually not the join but **how many times you run it**
  (ch 16's N+1).

# Security Considerations
- A join can **widen** what a query returns. If a page shows Adda rows a worker may
  see, joining in a money table can leak rates they must not see — the audit found
  exactly this class of risk and probed 300 role×URL combinations for it.
- Never build a join clause from user input (table/column names cannot be
  parameterised — ch 22). Whitelist, or don't do it.
- Row-level access is an application concern: a JOIN has no idea who is asking.

# Architecture Decisions
- **Point with `id`, not the business code.** Chosen so renaming a product is one
  row, not a migration across 271 foreign keys (ch 02).
- **Keep FKs even though they cost a check on write.** The alternative — trusting
  every code path forever — is how orphaned money rows appear. `RESTRICT` on
  delete, always, for anything financial (ch 13).
- **Prefer two clean queries over one exploded join** for to-many relations; that
  is exactly what `prefetch_related` does (ch 16).

# Best Practices
- Always alias tables (`a`, `p`) and qualify every column.
- Write the `ON` clause before the `SELECT` list — it is the part that decides
  correctness.
- Default to `LEFT JOIN` when the question is "which X exist"; use `count(right.id)`
  not `count(*)`.
- Aggregate **before** joining when both sides are to-many (ch 09).

# Beginner Mistakes
- Using `JOIN` when the question is "which X exist" — silently drops the empty ones.
- In a LEFT JOIN, `count(*)` instead of `count(right.id)` — reports `1` where the
  truth is `0`, because the padded NULL row still counts as a row.
- Putting a right-side filter in `WHERE` instead of `ON` in a LEFT JOIN: it
  re-hides the very rows you kept (`WHERE a.status='x'` also kills the NULL rows).
- Forgetting the `ON` clause entirely → a **cross join**: every row × every row.
  28 × 19 = 532 rows of nonsense (and on big tables, a hung server).
- Summing after a duplicating join. Nothing errors; the total is simply wrong.
- Ambiguous columns without aliases (`code` exists in both tables → error).

# Interview Questions
- **Junior:** *INNER vs LEFT JOIN?* — inner keeps only matches; left keeps all left rows, padding with NULLs. **Asked in virtually every data interview.**
- **Junior:** *What is a foreign key?* — a column referencing another table's key, enforced by the database.
- **Mid:** *A JOIN made my row count grow — why?* — one-to-many matching duplicates the left row per match; the fix is to aggregate before joining (ch 09) or accept and de-duplicate deliberately.
- **Mid:** *Difference between filtering in `ON` vs `WHERE` for a LEFT JOIN?* — `ON` restricts what counts as a match (unmatched left rows still survive as NULLs); `WHERE` runs after and removes those NULL rows, turning your LEFT JOIN back into an inner one.
- **Senior:** *FK vs JOIN — same thing?* — no: FK is a persistent integrity rule; JOIN is a per-query operation. You can JOIN without an FK, and have FKs you never JOIN on.
- **Staff:** *When would you deliberately skip a foreign key?* — extremely high-insert-rate tables, sharded/split data where the referent lives elsewhere, or import staging — accepting that integrity then becomes application-owned. This project keeps FKs precisely because money must not point at nothing.

### Why interviewers ask these — and the answer that separates levels

| Testing for | Weak answer | What lands |
|---|---|---|
| INNER vs LEFT — can you say what LEFT is *for*? | "LEFT JOIN gets more rows." | LEFT preserves **every left row**, padding unmatched ones with NULL — so it answers *"who has none?"*. That question is unanswerable with an INNER JOIN, and that is the point. |
| Do you know why row counts grow? | "The join duplicated the data." | **One-to-many matching multiplies the left row once per match.** So any `sum()` after that join **double-counts**. Cure: aggregate in a CTE keyed by the entity first, then join one-to-one (ch 09). |
| `ON` vs `WHERE` on a LEFT JOIN — the real senior filter question. | "Same thing, just style." | `ON` decides **what counts as a match** (unmatched left rows survive as NULL). `WHERE` runs **after** and deletes those NULL rows — **silently turning your LEFT JOIN back into an INNER one.** Single most common cause of "my LEFT JOIN is not working". |
| FK vs JOIN — do you know they are unrelated? | "A JOIN needs a foreign key." | An FK is a **persistent integrity rule**; a JOIN is a **per-query operation**. You can join without an FK and have FKs you never join on. This system keeps FKs because **money must not point at nothing**. |

**The killer follow-up:** *"When would you deliberately NOT add a foreign key?"* — very high insert rates, sharded data whose referent lives elsewhere, or import staging — and you must then say out loud that **integrity becomes the application's job**. Anyone who says "never skip FKs" has not run one at scale; anyone who skips them casually has not lost data yet.

# Revision Notes
- FK = a stored **rule** (must exist, cannot be orphaned). JOIN = a per-query **act**.
- INNER drops non-matches on either side; LEFT keeps every left row, NULL-padded.
- One-to-many match ⇒ the left row **repeats** ⇒ later `sum()` double-counts.
- Filter in `ON` to keep unmatched left rows; filter in `WHERE` to remove them.
- "Which X exist?" is almost always a LEFT JOIN question.

# Cheat Sheet
- FK = number pointing at another table's `id` (a stored rule)
- `JOIN … ON right.id = left.right_id` follows the pointer
- INNER = matches only · LEFT = keep all left, NULL-padded
- "which X exist?" → LEFT JOIN, and `count(right.id)` not `count(*)`
- one-to-many match ⇒ left row duplicates ⇒ later `sum()` double-counts
- missing `ON` = cross join = row explosion

# My ERP Section
| Pointer | Table → table |
|---|---|
| `adda.product_id` | `production_adda` → `production_product` |
| `adda.created_by_id` | `production_adda` → `accounts_user` |
| `adda.current_stage_id` | `production_adda` → the stage it sits on |
| `ledgerentry.worker_id` | `expense_workerledgerentry` → `accounts_user` (ch 08) |
| ORM equivalent | `select_related('product')` = this JOIN, written in Python (ch 16) |

# Practice Tasks
1. **Read the code:** find a `select_related(...)` in `config/production/views/` and
   write out the SQL JOIN it produces.
2. **Debug:** on a practice branch, write a query joining `production_adda` to
   `production_workerstagecontribution`. Count rows before and after. Explain the
   number.
3. **Design:** you must show "every product, its batch count, and its total settled
   money". Sketch the query. Where does row multiplication threaten the money
   total, and how do you prevent it? (Hint: ch 09's aggregate-first CTE.)
4. **Architecture:** argue both sides of "should we add a FK from a ledger row to a
   stage record?" — what does it buy, what does it cost on write and on delete?

# Homework
1. Write "every product with its number of Addas, including zeros", then break it by switching to INNER JOIN and name the five products that disappear.
2. In that LEFT JOIN, compare `count(*)` and `count(a.id)`. Explain the difference in one sentence.
3. Join Addas to `accounts_user` and list who created the three newest. Then add the product name so three tables are joined at once.

# Further Reading & Live Resources
- [Visual JOIN explainer](https://joins.spathon.com/) — drag the circles, see the rows
- [PgExercises: joins](https://pgexercises.com/questions/joins/) — the best free drills
- [Postgres JOIN docs](https://www.postgresql.org/docs/current/queries-table-expressions.html#QUERIES-JOIN)
- [Postgres docs — Joins between tables](https://www.postgresql.org/docs/current/tutorial-join.html) — the official walkthrough
- [Use The Index, Luke — join operations](https://use-the-index-luke.com/sql/join) — nested loop vs hash vs merge join, and when each is chosen
- [Postgres docs — `LATERAL`](https://www.postgresql.org/docs/current/queries-table-expressions.html#QUERIES-LATERAL) — the join people reach for once they know it exists
- Sibling chapter: [16 — ORM to SQL & N+1](16_ORM_To_SQL_And_N_Plus_1.md) — `select_related` is a join; `prefetch_related` is not
