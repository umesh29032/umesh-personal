---
id: sql-course-10-window-functions
type: lesson
status: active
owner: handwritten
scope: sql, postgresql — database fundamentals taught from this ERP
anchors: config/expense/services/settlement_service.py, config/production/services/pool_service.py
verified: 2026-08-01
---

# 10 — Window Functions

> Part of [SQL From Zero](00_COURSE_OVERVIEW.md). Prev: [09](09_Subqueries_And_CTEs.md) · Next: [11 — INSERT, UPDATE, DELETE](11_INSERT_UPDATE_DELETE.md).

# Learning Objectives
By the end of this chapter you can:
- write a running total with `sum() OVER (PARTITION BY … ORDER BY …)`
- say what changes when you remove the inner `ORDER BY`
- pick between `row_number`, `rank` and `dense_rank` by what ties should do
- get "the latest row per group" using the `row_number() = 1` idiom

# Purpose
To learn the feature that separates people who "know SQL" from people who *use*
SQL — and which happens to answer the single most natural question about a money
ledger: **"what was the running balance after each entry?"**

# The Problem
`GROUP BY` gave me one row per worker (₹6,500 total) — but it **destroyed** the
individual entries. A worker's passbook needs both: every entry *and* the balance
after it. With only the tools from chapter 08, that requires a correlated subquery
per row (slow) or post-processing in Python (wasteful). Window functions do it in
one pass.

# Theory (from zero)

A **window function** computes across a set of related rows **while keeping every
row**. That is the whole idea:

| | `GROUP BY` | window function |
|---|---|---|
| Rows out | one per group (**collapses**) | same as rows in (**keeps**) |
| Use for | totals, summaries | running totals, ranks, comparisons to neighbours |

Syntax:

```sql
sum(amount) OVER (PARTITION BY worker_id ORDER BY id)
│                 │                      │
│                 │                      └─ ORDER BY inside OVER: defines
│                 │                         "rows so far" → running total
│                 └─ PARTITION BY: restart per worker (like GROUP BY, but no collapse)
└─ any aggregate can become a window function
```

- **`PARTITION BY`** = which rows belong together (omit it = the whole result set).
- **`ORDER BY` inside `OVER`** = the sequence, which makes "so far" meaningful.
  With `ORDER BY` → running/cumulative. Without it → the partition's total on
  every row.

**The ranking family** (the difference is a classic interview question):

| Function | On ties (say two rows tie for 2nd) |
|---|---|
| `row_number()` | 1, 2, 3, 4 — always distinct, ties broken arbitrarily |
| `rank()` | 1, 2, 2, **4** — leaves a gap after the tie |
| `dense_rank()` | 1, 2, 2, **3** — no gap |

**Neighbour access:** `lag(col)` = value from the previous row, `lead(col)` = next
row. Perfect for "how much did this change since last time?"

> 💡 **Samjho aise:** `GROUP BY` poori dheri ka **ek jod** deta hai — parchiyaan
> gayab. Window function ek **passbook** hai: har entry apni jagah rehti hai, aur
> uske saamne **us waqt tak ka balance** likh jaata hai. `PARTITION BY worker` =
> har worker ki apni alag passbook. `ORDER BY id` = entries ka sahi kramm, warna
> "us waqt tak" ka koi matlab hi nahi. Ek hi nazar mein: kya hua, aur uske baad
> kitna hua.

# Real World Example (My ERP)
A real worker's passbook from my ledger — `a2.cm1@audit.local`, the audit's
cutting master. **Real output**, running balance and all:

```
 entry id | type   | amount  | running
    264   | credit |  500.00 |  500.00
    265   | credit | 2000.00 | 2500.00
    266   | credit | 2000.00 | 4500.00
    267   | credit | 2000.00 | 6500.00
```

That final `6500.00` is the *same* number chapter 08 got with `GROUP BY` — but now
I can also see **how it got there**, entry by entry. That is precisely what a
worker asking "how did you arrive at my payment?" needs, and it is why
append-only ledgers (ch 12) and window functions are natural partners: the entries
are immutable, so the running balance is reproducible forever.

Leaderboard with ranking — **real output**:

```
 email                  |   total | rank | row_number
 a2.cm1@audit.local     | 6500.00 |  1   |     1
 dev.aud.cm3@test.local | 2565.00 |  2   |     2
 dev.aud.cm2@test.local | 2532.00 |  3   |     3
 dev.aud.cm1@test.local | 1972.50 |  4   |     4
```

(No ties in my data, so `rank` and `row_number` agree here — the Homework makes
them disagree so you can *see* the difference.)

# Visual Diagram
```
  GROUP BY worker              WINDOW sum() OVER (PARTITION BY worker ORDER BY id)
  ┌───────────────┐            ┌──────────────────────────────┐
  │ a2.cm1 6500   │            │ 264  500.00 │ running  500.00│
  └───────────────┘            │ 265 2000.00 │ running 2500.00│
   4 rows → 1 row              │ 266 2000.00 │ running 4500.00│
   entries LOST                │ 267 2000.00 │ running 6500.00│
                               └──────────────────────────────┘
                                4 rows → 4 rows, entries KEPT + total visible
```

# Practical — try it yourself
```sql
-- the passbook (REAL output above)
SELECT l.id, l.entry_type, l.amount,
       sum(l.amount) OVER (PARTITION BY l.worker_id ORDER BY l.id) AS running
FROM expense_workerledgerentry l
JOIN accounts_user u ON u.id = l.worker_id
WHERE u.email = 'a2.cm1@audit.local'
ORDER BY l.id;

-- drop the ORDER BY inside OVER: every row now shows the partition TOTAL, not a
-- running figure. Run both and compare — this is the clearest way to feel it.
SELECT l.id, l.amount,
       sum(l.amount) OVER (PARTITION BY l.worker_id) AS worker_total
FROM expense_workerledgerentry l
JOIN accounts_user u ON u.id=l.worker_id
WHERE u.email='a2.cm1@audit.local' ORDER BY l.id;

-- ranking a leaderboard (REAL output above)
SELECT u.email, sum(l.amount) AS total,
       rank()       OVER (ORDER BY sum(l.amount) DESC) AS rnk,
       row_number() OVER (ORDER BY sum(l.amount) DESC) AS rn
FROM expense_workerledgerentry l JOIN accounts_user u ON u.id=l.worker_id
GROUP BY u.email ORDER BY total DESC LIMIT 4;
--   ^ note: aggregates and window functions coexist — the window sees the
--     GROUPED rows, because windows run AFTER grouping.

-- compare each entry to the previous one for the same worker
SELECT l.id, l.amount,
       lag(l.amount) OVER (PARTITION BY l.worker_id ORDER BY l.id) AS prev_amount,
       l.amount - lag(l.amount) OVER (PARTITION BY l.worker_id ORDER BY l.id) AS delta
FROM expense_workerledgerentry l JOIN accounts_user u ON u.id=l.worker_id
WHERE u.email='a2.cm1@audit.local' ORDER BY l.id;
--   first row's prev_amount is NULL — there IS no previous row (ch 04)

-- top entry per worker, the canonical "greatest-per-group" pattern
WITH ranked AS (
  SELECT worker_id, id, amount,
         row_number() OVER (PARTITION BY worker_id ORDER BY amount DESC) AS rn
  FROM expense_workerledgerentry
)
SELECT worker_id, id, amount FROM ranked WHERE rn = 1 ORDER BY amount DESC LIMIT 5;
```

# Production Walkthrough
A running balance is the *natural* view of an append-only ledger (ch 12):
- Because entries are **immutable**, the running balance is reproducible forever — re-run the query in two years and every intermediate figure is identical. A stored balance column could not promise that.
- This is what answers a worker asking *"how did you arrive at my payment?"*: not just ₹6,500 but 500 → 2,500 → 4,500 → 6,500, each line traceable to work.
- Ranking exposed the ₹100/piece rate anomaly — one worker at rank 1 with a quarter of the entries.

# Debugging Guide
"The running total looks wrong":
1. **Check the inner `ORDER BY` exists.** Without it you get the partition *total* on every row, which looks like a bug but is correct behaviour for what you wrote.
2. **Check the order is deterministic.** Ordering by a non-unique column (a date) makes the running figure vary between runs; add `id` as a tiebreak.
3. **Check `PARTITION BY`.** A missing partition means you are running a total across *all* workers.
4. **Remember windows run after `WHERE`.** If you filtered rows out, the running total is over the filtered set — usually not what "balance" means.
5. **`lag()` returning NULL on the first row is correct**, not missing data (ch 04).

# Performance Notes
- A window function needs its partition sorted; an index on `(partition_col, order_col)` lets Postgres skip the sort.
- Windows are computed **after** grouping, so they can wrap aggregates — but that means a heavy `GROUP BY` is paid first.
- The `row_number() = 1` greatest-per-group pattern is usually beaten by Postgres's `DISTINCT ON` for simple cases; know both.
- Large partitions can spill to disk — watch `Sort Method: external merge` in `EXPLAIN` (ch 15).

# Security Considerations
- A window over an unfiltered table can leak *other people's* rows into a computed column even if you only display one row. Filter to the permitted set **before** the window (in a CTE), not after.
- Ranking is a disclosure: "you are 7th of 8 earners" reveals information about the other seven.

# Architecture Decisions
- **Balances are computed, never stored** (ch 12) — the immutable entries plus a window function are the source of truth.
- **Order by a unique tiebreak** as a rule, so any reproduced report is byte-identical (the same discipline the golden tests rely on).
- **Filter first, window second** — implemented by wrapping in a CTE, which also documents the permitted set explicitly.

# Best Practices
- Always give the window a deterministic order (`ORDER BY id`, not just a date).
- Use a CTE when you need to filter on a window result — you cannot do it in `WHERE`.
- Name window columns for what they mean (`running`, `rank_by_earnings`), not `col1`.
- Prefer `row_number()` unless ties genuinely need shared ranks.

# Beginner Mistakes
- Expecting a window function to **filter**. It cannot: windows are computed after
  `WHERE` and cannot be used in `WHERE`. Wrap it in a CTE and filter outside
  (the `rn = 1` pattern above).
- Omitting `ORDER BY` inside `OVER` and wondering why the "running total" is flat —
  without an order, "so far" has no meaning, so you get the partition total.
- Confusing `PARTITION BY` with `GROUP BY`. Partition slices; group collapses.
- Assuming `rank()` and `row_number()` are the same. They differ **only on ties** —
  which is exactly when a leaderboard becomes contentious.
- Forgetting `lag()` returns NULL on the first row of each partition.
- Running a window over an unstable order (e.g. ordering by a non-unique column):
  the running total becomes non-deterministic between runs.

# Interview Questions
- **Junior:** *What is a window function?* — an aggregate computed over related rows that keeps every row, via `OVER (…)`.
- **Junior:** *`GROUP BY` vs `OVER (PARTITION BY …)`?* — collapse vs preserve.
- **Mid:** *`rank()` vs `dense_rank()` vs `row_number()`?* — gaps after ties / no gaps / always distinct. **Very commonly asked.**
- **Mid:** *How do you get a running total?* — `sum(x) OVER (PARTITION BY k ORDER BY seq)`; the inner ORDER BY is what makes it cumulative.
- **Senior:** *Why can't you use a window function in `WHERE`, and what's the workaround?* — windows are evaluated after WHERE/GROUP BY/HAVING; wrap in a CTE or subquery and filter on the computed column (the `row_number() = 1` idiom).
- **Senior:** *Get the latest row per group — how?* — `row_number() OVER (PARTITION BY group ORDER BY time DESC)` then keep `= 1`; alternatives are `DISTINCT ON` (Postgres-specific) or a lateral join.
- **Staff:** *A running balance computed at read time vs a stored balance column — trade-offs?* — computed is always consistent with the immutable entries and cannot drift, but costs CPU per read; a stored balance is fast but becomes a second source of truth that can disagree (and needs its own single writer). This project's append-only design deliberately favours the reproducible computation (ch 12).

### Why interviewers ask these — and the answer that separates levels

| Testing for | Weak answer | What lands |
|---|---|---|
| Do you know the three ranking functions apart? | "rank() numbers the rows." | `row_number()` **always distinct**; `rank()` leaves **gaps** after ties; `dense_rank()` **no gaps**. Very commonly asked because the difference only shows up when there are ties — which is exactly when reports go wrong. |
| Do you know what makes a window *cumulative*? | "`sum() OVER (PARTITION BY k)` gives a running total." | Without an inner `ORDER BY` that is a **partition-wide total repeated on every row**. The `ORDER BY seq` **inside** `OVER (…)` is what makes it accumulate. One clause is the whole difference. |
| Do you know windows cannot be filtered directly? | "`WHERE row_number() = 1` should work." | Windows are evaluated **after** WHERE/GROUP BY/HAVING, so the column does not exist yet. Wrap in a **CTE or subquery** and filter there — the `row_number() = 1` idiom. |
| Latest-row-per-group — do you know more than one way? | "I would sort and take the first in Python." | `row_number() OVER (PARTITION BY g ORDER BY t DESC)` then `= 1`; or **`DISTINCT ON`** (Postgres-specific, often fastest); or a lateral join. Doing it in Python means fetching every row first. |

**The killer follow-up:** *"Running balance: compute it at read time, or store a balance column?"* — computed can never drift from the immutable entries but costs CPU per read; **a stored balance is a second source of truth** that can disagree and needs its own single writer. This project deliberately chooses the reproducible computation (ch 12) — say which you chose and why.

# Revision Notes
- `agg() OVER (PARTITION BY k ORDER BY seq)` keeps rows and adds a column.
- Inner `ORDER BY` present ⇒ **running**; absent ⇒ partition total.
- `row_number` distinct · `rank` gaps on ties · `dense_rank` no gaps.
- `lag()`/`lead()` reach the previous/next row (NULL at edges).
- Cannot filter a window in `WHERE` → wrap in a CTE (`WHERE rn = 1`).

# Cheat Sheet
- `agg() OVER (PARTITION BY k ORDER BY seq)` — keeps rows, adds a column
- inner `ORDER BY` present ⇒ running/cumulative; absent ⇒ partition total
- `row_number` distinct · `rank` gaps on ties · `dense_rank` no gaps
- `lag()` / `lead()` = previous / next row (NULL at the edges)
- cannot filter on a window in `WHERE` → wrap in a CTE (`WHERE rn = 1`)
- windows run **after** GROUP BY, so they can wrap aggregates

# My ERP Section
| Idea | Where it fits in my project |
|---|---|
| Running balance | a worker's ledger/earnings history — entries are immutable (ch 12), so the balance is reproducible |
| Leaderboard / top earner | payroll analysis; `a2.cm1` at ₹6,500 exposed the implausible ₹100/piece rate |
| Latest-per-group | "current state per Adda/stage" style reads |
| ORM equivalent | `django.db.models.Window` + `RowNumber`/`Rank`/`Sum` (ch 16) |

# Practice Tasks
1. **Read the code:** find where worker earnings are listed in `config/expense/`. Would a running balance improve that page? Write the query it would need.
2. **Debug:** run a running total ordered by a *non-unique* column, twice. Are the intermediate values stable? Fix it with a tiebreak.
3. **Design:** design "each worker's biggest single jump in earnings" using `lag()`. What does a large jump tell the owner about rates?
4. **Architecture:** a stored `balance` column would make the page faster. Argue against it in three sentences using ch 12.

# Homework
1. Produce the running balance for `dev.aud.cm3@test.local` (27 entries). Does the last row equal ₹2,565.00 — the `GROUP BY` total from chapter 08?
2. Create a tie: rank workers by `count(*)` of entries instead of amount. Now compare `rank()`, `dense_rank()` and `row_number()` side by side and describe the difference in your own words.
3. Use `lag()` to find each worker's biggest jump between consecutive entries. Which worker has the largest single delta?

# Further Reading & Live Resources
- [Postgres window functions tutorial](https://www.postgresql.org/docs/current/tutorial-window.html) — official, gentle, excellent
- [Modern SQL: window functions](https://modern-sql.com/feature/over) — the best conceptual treatment
- [PgExercises: window functions](https://pgexercises.com/questions/aggregates/) — the harder aggregate set
- [Postgres window function reference](https://www.postgresql.org/docs/current/functions-window.html)
