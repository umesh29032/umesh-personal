---
id: sql-course-09-subqueries-and-ctes
type: lesson
status: active
owner: handwritten
scope: sql, postgresql — database fundamentals taught from this ERP
anchors: config/expense/services/settlement_service.py, config/production/services/pool_service.py
verified: 2026-08-01
---

# 09 — Subqueries & CTEs

> Part of [SQL From Zero](00_COURSE_OVERVIEW.md). Prev: [08](08_GROUP_BY_And_Aggregates.md) · Next: [10 — Window Functions](10_Window_Functions.md).

# Learning Objectives
By the end of this chapter you can:
- use a scalar subquery, `IN`, `EXISTS` and `NOT EXISTS` for the right question
- explain why `NOT IN` can silently return nothing
- rewrite an inside-out query as a readable top-to-bottom CTE
- use the aggregate-first pattern to make a total immune to duplication

# Purpose
To learn how to use the answer of one query inside another — and then to learn the
tool that makes complicated SQL *readable*: the CTE (`WITH …`). This is where SQL
stops feeling like one-liners and starts feeling like programming.

# The Problem
"Which products have never been used?" cannot be answered by filtering one table —
it needs *the absence of matching rows in another table*. And once a query needs
three or four such steps, writing it as one nested blob makes it unreadable
inside-out. Both problems have clean answers.

# Theory (from zero)

**A subquery is a query inside a query**, in parentheses. Four shapes:

1. **Scalar subquery** — returns exactly one value; usable anywhere a value fits.
   ```sql
   SELECT (SELECT count(*) FROM production_adda) AS addas;   -- 28
   ```
2. **`IN (subquery)`** — "is this value in that result list?"
3. **`EXISTS (subquery)`** — "does *at least one* matching row exist?" Stops at
   the first hit, so it is usually **faster than `IN`** on big sets, and it does
   not care what the subquery selects (convention: `SELECT 1`).
4. **`NOT EXISTS`** — "no matching row exists" — the clean way to ask "never used".

⚠️ **`NOT IN` + NULL = the silent-empty trap.** If the subquery returns even one
NULL, `NOT IN` yields *no rows at all* (because "is x not in {1, NULL}?" is
unknown — ch 04). `NOT EXISTS` is NULL-safe. **Prefer `NOT EXISTS`.**

**Correlated subquery** — one that references the outer row, so it re-runs *per
row*. Sometimes exactly right, sometimes an N+1 in SQL clothing (ch 16).

**CTE — Common Table Expression** — `WITH name AS ( … )`: name a step, then use it
like a table. It turns inside-out SQL into **top-to-bottom SQL**:

```sql
WITH per_product AS (            -- step 1: name it
  SELECT p.code, count(a.id) AS n
  FROM production_product p
  LEFT JOIN production_adda a ON a.product_id = p.id
  GROUP BY p.code
)
SELECT code, n FROM per_product WHERE n >= 2 ORDER BY n DESC;   -- step 2: use it
```

CTEs also solve the ch 07/08 double-count trap: **aggregate first inside the CTE,
then join** — so nothing multiplies before it is summed.

> 💡 **Samjho aise:** Subquery = ek **chhota sawaal jiska jawaab bade sawaal ke
> andar** use hota hai ("jin product ka koi Adda hi nahi bana — unke naam do").
> CTE us chhote sawaal ko ek **naam** de deta hai, jaise munshi kehta hai:
> *"pehle product-wise ginti ki ek alag parchi bana lo… ab us parchi mein se
> 2 se zyada wale chuno."* Ek hi lambi ulti-seedhi line ki jagah **kadam-ba-kadam**.
> Padhne mein aasaan = galti pakadne mein aasaan.

# Real World Example (My ERP)
"Which products are actually in use?" — real output from my database via CTE:

```
 3-PATTI    | 10
 DEV-NICKAR |  3
 NIKKAR     |  2   XFB | 2   T-SHIRT | 2   LOWER | 2
```

And the mirror question, `NOT EXISTS` — products that have **never** had an Adda
(the five skeleton products that migrations seed, logged as finding **F-1** in
[FRESH_DB_REQUIREMENTS](../FRESH_DB_REQUIREMENTS.md)):

```
 1-6 · DEV-HUB · DEV-P3A · DEV-P3B · DEV-TEE
```

That is not a toy query — it is exactly the evidence that a "clean" fresh database
is not actually clean, which is why the finding exists.

# Visual Diagram
```
  WITHOUT a CTE (read inside-out, right to left, painful):
  SELECT … FROM ( SELECT … FROM ( SELECT … ) ) WHERE …
                              ▲ start here?  ▲ or here?

  WITH a CTE (read top-to-bottom, like a recipe):
  WITH per_product AS ( …count per product… )   ← step 1, named
  SELECT * FROM per_product WHERE n >= 2        ← step 2, uses the name
```

# Practical — try it yourself
```sql
-- 1. scalar subqueries side by side (REAL: 28 | 19)
SELECT (SELECT count(*) FROM production_adda)   AS addas,
       (SELECT count(*) FROM production_product) AS products;

-- 2. IN (subquery): every Adda of the 3-PATTI product (REAL)
SELECT code FROM production_adda
WHERE product_id IN (SELECT id FROM production_product WHERE code = '3-PATTI')
ORDER BY id DESC LIMIT 3;
--  3-PATTI-018 | 3-PATTI-017 | 3-PATTI-015

-- 3. NOT EXISTS: products never used (REAL — the five skeletons)
SELECT p.code FROM production_product p
WHERE NOT EXISTS (SELECT 1 FROM production_adda a WHERE a.product_id = p.id)
ORDER BY p.code LIMIT 5;
--  1-6 | DEV-HUB | DEV-P3A | DEV-P3B | DEV-TEE

-- 4. the same, as a CTE (REAL output shown in Real World Example)
WITH per_product AS (
  SELECT p.code, count(a.id) AS n
  FROM production_product p
  LEFT JOIN production_adda a ON a.product_id = p.id
  GROUP BY p.code
)
SELECT code, n FROM per_product WHERE n >= 2 ORDER BY n DESC;

-- 5. aggregate-first pattern: totals per worker, THEN joined to user rows
--    (this shape is immune to the ch 07 duplication trap)
WITH totals AS (
  SELECT worker_id, sum(amount) AS earned, count(*) AS entries
  FROM expense_workerledgerentry GROUP BY worker_id
)
SELECT u.email, t.entries, t.earned
FROM totals t JOIN accounts_user u ON u.id = t.worker_id
ORDER BY t.earned DESC LIMIT 3;

-- 6. multiple CTEs chained — each may use the previous
WITH used AS (
  SELECT DISTINCT product_id FROM production_adda
), unused AS (
  SELECT p.code FROM production_product p
  WHERE p.id NOT IN (SELECT product_id FROM used)
)
SELECT count(*) FROM unused;    -- safe here only because product_id is NOT NULL
```

# Production Walkthrough
- **"Which products were never used?"** — the `NOT EXISTS` query in this chapter is exactly how the five skeleton products (`1-6`, `DEV-HUB`, `DEV-P3A`, `DEV-P3B`, `DEV-TEE`) were found. That became finding **F-1** in `docs/FRESH_DB_REQUIREMENTS.md`: a "clean" fresh database is not actually clean. A subquery produced a real deployment decision.
- **The aggregate-first CTE** is the shape every money report here uses: total per worker in a CTE, *then* join to the user row. One-to-one at the join, so nothing can duplicate.
- Django's `Subquery()` / `Exists()` generate exactly these forms (ch 16).

# Debugging Guide
"The subquery returns nothing / too much":
1. **Run the inner query alone.** Half of subquery bugs are inner-query bugs.
2. **If you used `NOT IN`, switch to `NOT EXISTS`** and compare. A single NULL in the list makes `NOT IN` return zero rows (ch 04).
3. **Check the column count** — a subquery in `IN` must return exactly one column.
4. **For a correlated subquery, ask how many times it runs.** Once per outer row is an N+1 in SQL clothing (ch 16).
5. **Name the steps.** Rewriting as a CTE often makes the bug obvious because you can run each step in isolation.

# Performance Notes
- `EXISTS` short-circuits on the first match; `IN` may materialise the whole list. Prefer `EXISTS` for "does a related row exist".
- **CTEs are not automatically an optimisation fence.** Before Postgres 12 they always were; from 12 they may be inlined. Use `MATERIALIZED` only when you truly want it computed once.
- A correlated subquery inside `SELECT` over many rows is the classic accidental quadratic.
- Aggregate-first CTEs are usually *faster* as well as safer — they shrink the data before the join.

# Security Considerations
- A subquery can widen a result set past what the outer query's permissions intended. Check what the *combined* query exposes, not just the outer table.
- Never build a subquery from user input; parameterise values and whitelist identifiers (ch 22).

# Architecture Decisions
- **Readability is an engineering criterion.** A CTE that reads top-to-bottom is chosen over a nested subquery even at equal performance, because the next person debugging it is the real cost.
- **Aggregate-first is the house pattern** for any per-entity money total — it removes an entire class of double-count bug by construction.
- **`NOT EXISTS` is preferred over `NOT IN`** as a standing rule, not case by case.

# Best Practices
- Name every CTE for the *question* it answers (`per_product`, `totals`), not its mechanics.
- Run each CTE alone while building it.
- Reach for `EXISTS` on relationships, `IN` only on short literal lists.
- If a query needs a comment to be understood, it probably needs a CTE instead.

# Beginner Mistakes
- **`NOT IN` against a NULL-able column** — returns zero rows and looks like "no
  results". Use `NOT EXISTS`. (Example 6 above is only safe because `product_id`
  is NOT NULL — say *why* before you copy that pattern.)
- A correlated subquery inside a `SELECT` over thousands of rows — it re-runs per
  row; that is an N+1 written in SQL (ch 16).
- Believing a CTE is always an optimisation fence. In modern Postgres (12+) CTEs
  can be *inlined* by the planner; add `MATERIALIZED` only when you truly want it
  computed once.
- Using a subquery where a JOIN reads better (and vice versa) — clarity is a real
  engineering criterion.
- Forgetting a subquery in `IN` must return **one column**.

# Interview Questions
- **Junior:** *What is a subquery?* — a query nested in another, supplying a value or a row set.
- **Junior:** *What does a CTE give you?* — a named intermediate result; readability and reuse within one statement.
- **Mid:** *`IN` vs `EXISTS` — which and when?* — `EXISTS` short-circuits on the first match and handles NULLs sanely; `IN` is fine for small literal lists. For "does a related row exist", prefer EXISTS.
- **Mid:** *Why can `NOT IN` return nothing unexpectedly?* — a NULL in the list makes the comparison unknown for every row. **Classic senior-level trap.**
- **Senior:** *Are CTEs materialised in Postgres?* — before 12 they were an optimisation fence (always materialised); from 12 they may be inlined, with `MATERIALIZED`/`NOT MATERIALIZED` for explicit control. Knowing the version boundary marks real experience.
- **Staff:** *How would you compute per-entity totals and then join them without double-counting?* — aggregate in a CTE/derived table keyed by the entity, then join one-to-one (example 5 above). This is the standard cure for inflated report totals.

### Why interviewers ask these — and the answer that separates levels

| Testing for | Weak answer | What lands |
|---|---|---|
| `IN` vs `EXISTS` — do you have a rule? | "They are interchangeable." | `EXISTS` **short-circuits on the first match** and handles NULLs sanely; `IN` is fine for small literal lists. For *"does a related row exist"*, prefer **EXISTS**. |
| Do you know the `NOT IN` NULL trap? | "`NOT IN` excludes those values." | **One NULL in the list makes the comparison unknown for every row — so you get zero rows back.** Classic senior-level trap. Use `NOT EXISTS`, or filter NULLs out of the subquery explicitly. |
| Do you know CTE behaviour changed? | "CTEs are always materialised, so they are slower." | True **before Postgres 12** — they were an optimisation fence. **From 12 they may be inlined**, with `MATERIALIZED` / `NOT MATERIALIZED` for explicit control. Naming the version boundary is what marks real experience. |
| Can you fix an inflated report total? | "I will add DISTINCT." | `DISTINCT` masks the symptom and can drop legitimate duplicates. **Aggregate in a CTE keyed by the entity, then join one-to-one.** That is the standard cure for double-counted report totals. |

**The killer follow-up:** *"You reach for DISTINCT to fix a wrong total. What is it hiding?"* — a fan-out you have not understood. `DISTINCT` on a money query is a red flag, because it makes a wrong number look plausible instead of making it right.

# Revision Notes
- Subquery = a query inside a query; scalar / `IN` / `EXISTS` / `NOT EXISTS`.
- **`NOT EXISTS` over `NOT IN`** — NULL-safe.
- CTE (`WITH x AS (…)`) names a step → read top-to-bottom.
- **Aggregate inside the CTE, then join** ⇒ no duplication, no double-count.
- Correlated subquery = runs per row = possible N+1.

# Cheat Sheet
- scalar `( SELECT one_value )` · `IN (…)` · `EXISTS (SELECT 1 …)` · `NOT EXISTS`
- **`NOT EXISTS` over `NOT IN`** — NULL-safe
- `WITH name AS ( … ) SELECT … FROM name` = named step, top-to-bottom reading
- aggregate **inside** the CTE, then join ⇒ no duplication, no double-count
- correlated subquery = re-runs per row = possible N+1

# My ERP Section
| Question | Query shape | Where it matters |
|---|---|---|
| "products never used" | `NOT EXISTS` | finding F-1 in [FRESH_DB_REQUIREMENTS](../FRESH_DB_REQUIREMENTS.md) |
| "per-product batch counts" | CTE + LEFT JOIN | product usage reporting |
| "per-worker totals, joined safely" | aggregate-first CTE | payroll/earnings reports |
| ORM equivalent | `.annotate()`, `Subquery()`, `Exists()` | ch 16 |

# Practice Tasks
1. **Read the code:** find a use of `Exists()` or `Subquery()` in this repo (`grep -rn "Exists(\|Subquery(" config/`). Write out the SQL it generates.
2. **Debug:** build a `NOT IN` query against a nullable column so it returns zero rows, then fix it with `NOT EXISTS`. This is a bug you will meet again.
3. **Design:** "every worker with their total earnings and their number of bookmarked chapters" — sketch it with two CTEs. Where would a naive join have double-counted?
4. **Architecture:** when would you store a computed aggregate rather than recompute it via CTE? Name the cost you accept.

# Homework
1. Write, with `NOT EXISTS`, "users who have **no** ledger entries". How many are there out of 106?
2. Rewrite the per-product count query as a CTE **and** as a plain grouped JOIN. Which reads better to you? Say why out loud.
3. Build the aggregate-first CTE for per-worker totals, then deliberately write the naive version that joins first and sums after. Compare the two totals and explain any difference.

# Further Reading & Live Resources
- [Postgres WITH / CTE docs](https://www.postgresql.org/docs/current/queries-with.html)
- [Modern SQL: WITH](https://modern-sql.com/feature/with) — including the materialisation history
- [PgExercises: aggregates & subqueries](https://pgexercises.com/questions/aggregates/)
- [Postgres docs — WITH queries (CTEs)](https://www.postgresql.org/docs/current/queries-with.html) — including recursive CTEs and `MATERIALIZED`
- [Postgres 12 release notes — CTEs are no longer always materialised](https://www.postgresql.org/docs/12/release-12.html) — the change that made "CTEs are slow" outdated advice
- [Use The Index, Luke — `NOT IN` and NULL](https://use-the-index-luke.com/sql/where-clause/null) — why `NOT EXISTS` is the safe form
- Sibling chapter: [04 — NULL](04_NULL.md) — the reason `NOT IN` can return zero rows without erroring
