---
id: sql-course-08-group-by-and-aggregates
type: lesson
status: active
owner: handwritten
scope: sql, postgresql — database fundamentals taught from this ERP
anchors: config/expense/services/settlement_service.py, config/production/services/pool_service.py
verified: 2026-08-01
---

# 08 — GROUP BY & Aggregates: My Ledger, Summed

> Part of [SQL From Zero](00_COURSE_OVERVIEW.md). Prev: [07](07_JOINs.md) · Next: [09 — Subqueries & CTEs](09_Subqueries_And_CTEs.md).

# Learning Objectives
By the end of this chapter you can:
- turn rows into per-group answers with `GROUP BY`
- state the GROUP BY law and say *why* the database refuses otherwise
- choose `WHERE` vs `HAVING` without hesitating
- explain how a JOIN can silently corrupt a `sum()` — and prove a total two ways

# Purpose
To turn 201 individual money rows into the sentences a factory owner actually
needs: *"total paid"*, *"per worker"*, *"only those above ₹2,000"*. This is the
chapter behind every report I will ever build.

# The Problem
My ledger has 201 rows. Nobody wants 201 rows — they want **one** number
(₹18,254.25), or **one row per worker**. And the moment a report summarises, the
inputs disappear from view, so a mistake stops being visible. Aggregation is
powerful and it hides its own evidence. Both halves of that matter.

# Theory (from zero)

**Aggregate functions** squeeze many rows into one value:

| Function | Meaning | On my ledger (real) |
|---|---|---|
| `count(*)` | number of rows | 201 |
| `sum(col)` | total | 18254.25 |
| `min(col)` / `max(col)` | smallest / largest | 1.00 / 2000.00 |
| `avg(col)` | mean | 90.82 |
| `count(col)` | non-NULL values only (ch 04) | ≠ `count(*)` when NULLs exist |

**GROUP BY** makes one answer *per group* instead of one for everything. "Group by
worker" = pile the 201 slips into per-worker heaps, then total each heap.

**The GROUP BY law:** every column in `SELECT` must be either inside an aggregate
or listed in `GROUP BY`. Postgres refuses anything else — and it is right to,
because "which single value should I show for a column that varies inside the
group?" has no honest answer.

**HAVING vs WHERE** — the distinction interviewers love:
- `WHERE` filters **rows**, *before* grouping.
- `HAVING` filters **groups**, *after* grouping (so it can test `sum(...)`).

Order of execution (ch 05): FROM → **WHERE** → GROUP BY → **HAVING** → SELECT.

> 💡 **Samjho aise:** 201 parchiyaan ek dher mein padi hain. `sum` = sab jod ke
> ek number. `GROUP BY worker` = pehle **worker ke naam se alag-alag dheri**
> lagao, phir har dheri ka jod. `WHERE` dheri banne se **pehle** parchi phekta
> hai; `HAVING` poori dheri ko **baad mein** phekta hai ("2,000 se kam wali dheri
> hatao"). Aur yaad rakho — jod ke baad **parchiyaan dikhna band ho jaati hain**,
> to galti bhi chhup jaati hai. Isi liye har bade total ko **do raaste se** milao.

# Real World Example (My ERP)
The number my whole payroll trust rests on, and its real breakdown:

```sql
SELECT count(*), sum(amount) FROM expense_workerledgerentry;
--  201 | 18254.25          ← proven to the paisa in the audit
```

Split by direction — my ledger's two entry types:

```
 entry_type | count |    sum
 credit     |  170  | 15629.25     ← money earned
 debit      |   31  |  2625.00     ← advances recovered / paid out
```

Per worker, only the significant ones (`HAVING`):

```
 a2.cm1@audit.local     |  4 entries | 6500.00
 dev.aud.cm3@test.local | 27 entries | 2565.00
 dev.aud.cm2@test.local | 30 entries | 2532.00
```

Notice `a2.cm1` earned the most from only **4** entries, while another worker
needed 27 — a business insight that raw rows never show you. (That worker is my
audit's cutting master on the ₹100/piece stage, which is exactly why that rate is
flagged as implausible in [FRESH_DB_REQUIREMENTS](../FRESH_DB_REQUIREMENTS.md).)

**The reconciliation habit.** Because aggregates hide their inputs, this project
never trusts one path to a total. The audit computed settlement totals *and* the
ledger delta independently and required **variance = ₹0**. Any report worth
trusting has a second, independent route to the same number.

# Visual Diagram
```
 201 ledger rows
      │
      ├── sum(amount) ─────────────────▶  18254.25          (one answer)
      │
      └── GROUP BY worker_id
             ├─ a2.cm1     : 4 rows ──▶ 6500.00
             ├─ dev.aud.cm3: 27 rows ─▶ 2565.00      (one answer PER GROUP)
             └─ …
                     │
                     └── HAVING sum(amount) > 2000  ← whole heaps dropped here
```

# Practical — try it yourself
```sql
-- the whole-ledger sentence (REAL)
SELECT count(*), sum(amount), min(amount), max(amount), round(avg(amount),2)
FROM expense_workerledgerentry;
--  201 | 18254.25 | 1.00 | 2000.00 | 90.82

-- by direction (REAL)
SELECT entry_type, count(*), sum(amount)
FROM expense_workerledgerentry GROUP BY entry_type ORDER BY 2 DESC;
--  credit | 170 | 15629.25
--  debit  |  31 |  2625.00
--   ^ ORDER BY 2 = "by the second output column"

-- per worker, filtered by the GROUP's total (REAL)
SELECT u.email, count(*), sum(l.amount) AS earned
FROM expense_workerledgerentry l
JOIN accounts_user u ON u.id = l.worker_id
GROUP BY u.email
HAVING sum(l.amount) > 2000
ORDER BY earned DESC;

-- break the GROUP BY law on purpose, read the error, understand it:
SELECT u.email, l.amount, sum(l.amount)
FROM expense_workerledgerentry l JOIN accounts_user u ON u.id=l.worker_id
GROUP BY u.email;
-- ERROR: column "l.amount" must appear in the GROUP BY clause
--        or be used in an aggregate function

-- WHERE vs HAVING, same question two ways — compare and explain:
SELECT u.email, sum(l.amount) FROM expense_workerledgerentry l
JOIN accounts_user u ON u.id=l.worker_id
WHERE l.amount > 100 GROUP BY u.email;        -- drops small ROWS first
SELECT u.email, sum(l.amount) FROM expense_workerledgerentry l
JOIN accounts_user u ON u.id=l.worker_id
GROUP BY u.email HAVING sum(l.amount) > 100;  -- drops small TOTALS after
```

# Production Walkthrough
This chapter *is* the payroll reporting layer:
- The settlement total for an Adda is a `sum()` over its contribution rows; the ledger delta is a `sum()` over ledger rows. **The audit required those two independent paths to match — variance ₹0.** That is reconciliation, and it is the only reason anyone should trust an aggregate.
- Golden tests pin exact totals (₹344.25 / ₹801 / ₹633 / ₹225). A duplicating join or a changed rate moves a total, so the test fails instead of a wrong payslip shipping.
- `a2.cm1@audit.local` earning ₹6,500 from **4** entries while another worker needed 27 is what exposed the implausible ₹100/piece cutting rate. Aggregates are how you *find* business bugs, not just report numbers.

# Debugging Guide
"The total is wrong":
1. **Count the rows first.** If `count(*)` grew after adding a join, you have row multiplication — the total is inflated, not miscalculated (ch 07).
2. **Drop the aggregate.** Look at the raw rows the group contains. The wrong row is usually visible immediately.
3. **Reconcile a second way.** Compute it by a different route (credit − debit vs `sum(amount)`); agreement is evidence, disagreement localises the bug.
4. **Check NULLs.** `avg()` and `sum()` skip them — the average of "known" is not the average of "all" (ch 04).
5. **Check the grain.** "Per worker" vs "per worker per stage" are different questions; grouping by the wrong key gives a plausible wrong answer.

# Performance Notes
- Grouping needs to sort or hash; a big `GROUP BY` may spill to disk (watch `external merge Disk` in `EXPLAIN`, ch 15).
- An index on the grouping column can let Postgres stream instead of sort.
- `count(*)` is not free at millions of rows (MVCC — ch 18); use an estimate when exactness does not matter (ch 24).
- Aggregate **before** joining when both sides are to-many (ch 09) — smaller inputs, no duplication.

# Security Considerations
- Aggregates leak. "Total payroll" shown to a worker is a disclosure even though no individual row appeared. This project's rule is that money aggregates are gated by role, and the audit probed 300 role×URL combinations for exactly this class of leak.
- Small groups de-anonymise: an average over one person *is* that person's salary.

# Architecture Decisions
- **Reconciliation as a first-class rule** — `reconciliation_service` exists because a single computed total is not trustworthy on its own.
- **Money totals are computed, never cached** in a column (ch 12): a stored balance is a second source of truth that drifts.
- **Golden tests assert exact rupees**, not ranges — a money system either matches or it does not.

# Best Practices
- Always know your **grain** before writing `GROUP BY` — say the sentence out loud first.
- Never trust an important total from one code path.
- Use `HAVING` for group-level filters and `WHERE` for row-level ones; mixing them up changes the answer.
- Alias every aggregate (`AS earned`) — unnamed columns make reports unreadable.

# Beginner Mistakes
- Putting an aggregate in `WHERE` (`WHERE sum(x) > 5`) — impossible; grouping
  hasn't happened yet. That's what `HAVING` is for.
- **Summing after a duplicating JOIN** (ch 07). The total inflates and nothing
  errors. The most expensive mistake in this chapter.
- `avg()` over a NULL-able column and calling it "the average of all" — it is the
  average of the *known* values only (ch 04).
- Assuming `count(*)` and `count(col)` are interchangeable.
- Reporting a single grand total with no independent cross-check.

# Interview Questions
- **Junior:** *`WHERE` vs `HAVING`?* — rows before grouping vs groups after; HAVING can test aggregates. **Near-universal interview question.**
- **Junior:** *`count(*)` vs `count(col)` vs `count(DISTINCT col)`?* — all rows / non-NULL values / distinct non-NULL values.
- **Mid:** *Why must every non-aggregated SELECT column appear in GROUP BY?* — otherwise the value is ambiguous within the group; Postgres refuses rather than guessing (some databases silently pick one — a notorious MySQL footgun).
- **Mid:** *Adding a JOIN changed my `sum()` — what happened?* — row multiplication double-counted the left side; aggregate in a subquery/CTE first, then join.
- **Senior:** *How do you make a financial total trustworthy?* — compute it by two independent paths and assert they match (reconciliation), pin the expected value in a test (golden totals), and keep the inputs immutable so the total is reproducible (ch 12).
- **Staff:** *`sum()` over a `numeric` vs `float` column at scale?* — numeric is exact and slower; float is fast and accumulates error. For money the answer is never float (ch 03) — and know that summation order can matter for floats but not for numeric.

### Why interviewers ask these — and the answer that separates levels

| Testing for | Weak answer | What lands |
|---|---|---|
| WHERE vs HAVING — do you know the *when*, not the *what*? | "HAVING is for aggregates." | It is about **timing**: `WHERE` filters **rows before** grouping, `HAVING` filters **groups after**. So filtering in `WHERE` is cheaper — fewer rows ever reach the grouping step. |
| Do you know why Postgres refuses your query? | "Postgres is stricter than MySQL for no reason." | A non-aggregated column is **ambiguous within the group** — there may be many values. Postgres refuses rather than **silently picking one**, which is the notorious MySQL footgun. Strictness here is a feature. |
| Do you understand how a JOIN corrupts a SUM? | "I added a join and the total changed, so I removed the join." | **Row multiplication double-counted the left side.** Aggregate in a subquery/CTE **first**, then join. Removing the join hides the bug instead of fixing it. |
| Can you make a financial total *trustworthy*? | "I ran it twice and got the same number." | Three things: compute it by **two independent paths and assert they match** (reconciliation), **pin the expected value** as a golden total in a test, and keep inputs **immutable** so the total is reproducible (ch 12). Running it twice only proves it is deterministic, not correct. |

**The killer follow-up:** *"Your dashboard total and your detail page total disagree by ₹50. Which one do you trust?"* — the correct answer is **neither, until one is reconciled against an immutable source**. Picking a favourite is how a wrong number becomes the official number.

# Revision Notes
- Aggregates collapse rows: `count · sum · avg · min · max`.
- `GROUP BY` = one answer per group; every selected column is grouped **or** aggregated.
- `WHERE` filters rows **before**, `HAVING` filters groups **after**.
- A duplicating JOIN inflates `sum()` **silently**.
- Trust a total only when a **second independent path** agrees.

# Cheat Sheet
- `count/sum/avg/min/max` collapse rows; `GROUP BY` = one answer per group
- law: every SELECT column is aggregated **or** grouped
- `WHERE` before grouping · `HAVING` after (can see `sum()`)
- `ORDER BY 2` = order by the 2nd output column
- aggregates hide inputs ⇒ cross-check every important total two ways
- duplicating JOIN + `sum()` = silent double-count

# My ERP Section
| Concept | Where in my project |
|---|---|
| The proven total | ledger 201 rows / ₹18,254.25, variance ₹0 in the audit |
| credit vs debit | `entry_type` on `WorkerLedgerEntry` (append-only, ch 12) |
| Per-worker earnings | worker earnings pages / payroll reports |
| Reconciliation as law | `reconciliation_service`, settlement-vs-ledger checks |
| Money debugging | [kos: money-looks-wrong](../../kos/debugging/money-looks-wrong.md) |

# Practice Tasks
1. **Read the code:** find `reconciliation_service` in `config/expense/services/`. What two numbers does it compare, and what does it do when they disagree?
2. **Debug:** deliberately join the ledger to a to-many table, then `sum(amount)`. Show the inflated total and explain the mechanism in one sentence.
3. **Design:** design the query for "earnings per worker per stage this month". State the grain, then write it. What does `HAVING` add here?
4. **Architecture:** argue whether a worker's running balance should be a stored column or always computed (use ch 12).

# Homework
1. Reproduce `sum(amount) = 18254.25`. Then compute `credit − debit` from the entry_type breakdown and reconcile it against the totals yourself.
2. Find the workers with **more than 20 entries** (HAVING on `count(*)`), and separately those earning over ₹2,000. Are they the same people? What does that tell you about rates?
3. Deliberately break the GROUP BY law, read the exact error, then fix it two ways: by grouping the extra column, and by aggregating it.

# Further Reading & Live Resources
- [PgExercises: aggregates](https://pgexercises.com/questions/aggregates/) — do all of these
- [Postgres aggregate functions](https://www.postgresql.org/docs/current/functions-aggregate.html)
- [Mode: SQL aggregate functions](https://mode.com/sql-tutorial/sql-aggregate-functions/)
