---
id: sql-course-04-null
type: lesson
status: active
owner: handwritten
scope: sql, postgresql — database fundamentals taught from this ERP
anchors: config/expense/services/settlement_service.py, config/production/services/pool_service.py
verified: 2026-08-01
---

# 04 — NULL: "Unknown" Is Not "Zero"

> Part of [SQL From Zero](00_COURSE_OVERVIEW.md). Prev: [03](03_Data_Types_And_Money.md) · Next: [05 — SELECT Basics](05_SELECT_Basics.md).

# Learning Objectives
By the end of this chapter you can:
- explain the difference between NULL, 0 and empty string with a real example
- predict what a `!=` filter does to NULL rows *before* running it
- read a `CHECK (x IS NULL OR x >= 0)` and say why it is written that way
- defend honest-NULL to someone who wants to "just put zero

# Purpose
To understand SQL's third truth value — and to see why my project's
"honest-NULL" policy (`cost_per_kg` unpriced, `completed_at` unset) is a
deliberate engineering decision, not laziness.

# The Problem
A cloth roll arrives; nobody has entered its price yet. Store `0`? Now every
cost report silently computes "this cloth was free" — a lie that flows into
totals nobody questions. The database needs a way to say **"no value recorded"**
that arithmetic and reports cannot mistake for a real number.

# Theory (from zero)
`NULL` = absence of a value. Not 0, not empty string. It has its own algebra:

- `NULL = NULL` → `NULL` (unknown equals unknown? …unknown!)
- `NULL + 5` → `NULL` (unknown plus five is unknown)
- `WHERE` keeps only rows whose test is **true** — NULL results are dropped.
  So `WHERE col != 'x'` does NOT return rows where col IS NULL. (The trap.)
- Test with `IS NULL` / `IS NOT NULL`, never `= NULL`.
- Aggregates **skip** NULLs: `count(col)` counts non-NULLs; `avg` averages only
  the known values.
- `coalesce(a, b)` = "a, unless it's NULL, then b" — the display-time escape hatch.

### Three-valued logic — the table that explains every NULL bug

Most languages have TRUE and FALSE. SQL has **three** values:

```
        A = B  when either side is NULL  ──▶  the answer is NULL ("unknown")

   ┌───────────┬───────┬───────┬─────────┐        WHERE keeps ONLY true.
   │  AND      │ TRUE  │ FALSE │  NULL   │        Rows that evaluate to
   ├───────────┼───────┼───────┼─────────┤        FALSE **or NULL** are
   │ TRUE      │ TRUE  │ FALSE │  NULL   │        both thrown away —
   │ FALSE     │ FALSE │ FALSE │  FALSE  │        and that is why NULL
   │ NULL      │ NULL  │ FALSE │  NULL   │        rows silently vanish
   └───────────┴───────┴───────┴─────────┘        from `!=` filters.

   ┌───────────┬───────┬───────┬─────────┐
   │  OR       │ TRUE  │ FALSE │  NULL   │   Note: TRUE OR NULL = TRUE
   ├───────────┼───────┼───────┼─────────┤   (if one side already wins,
   │ TRUE      │ TRUE  │ TRUE  │  TRUE   │    the unknown doesn't matter)
   │ FALSE     │ TRUE  │ FALSE │  NULL   │
   │ NULL      │ TRUE  │ NULL  │  NULL   │
   └───────────┴───────┴───────┴─────────┘
```

### The three states a column can be in — never confuse them

```
   ┌──────────────┬────────────────────────┬──────────────────────────────┐
   │  VALUE       │  MEANS                 │  MY REAL EXAMPLE              │
   ├──────────────┼────────────────────────┼──────────────────────────────┤
   │  240         │ a real, known number   │ roll priced at ₹240/kg        │
   │  0           │ genuinely ZERO         │ a stage that legitimately     │
   │              │ ("free", "none")       │ pays ₹0                       │
   │  NULL        │ NOT KNOWN / not set    │ roll price never entered      │
   │              │ ⚠️ NOT zero             │ → report says "unpriced"      │
   └──────────────┴────────────────────────┴──────────────────────────────┘
   Storing 0 for "unknown" is a LIE that arithmetic will happily spread.
   Storing NULL is an ADMISSION that reports can handle honestly.
```

> 💡 **Samjho aise:** Register mein ek khaana **khaali** hai. Khaali ka matlab
> "zero" nahi — matlab *"abhi pata nahi / bhara nahi gaya"*. Isi liye khaali ==
> khaali bhi **pata-nahi** hota hai (kya pata dono mein alag cheez aani thi?).
> Aur khaali khaane mein `0` likh dena **jhooth** hai — roll muft mein nahi aaya
> tha, uska daam abhi likha nahi gaya. Jhooth hisaab mein phailta hai; khaali
> khaana report ko sach bolne deta hai: *"unpriced"*.

# Real World Example (My ERP)
- `raw_materials_clothroll.cost_per_kg` — **NULL until a price is entered.**
  Reports show "unpriced" instead of a fake ₹0 total. CLAUDE.md calls this
  honest-NULL; the audit report praised exactly this ("honest NULLs over
  comfortable zeros").
- `production_adda.completed_at` — NULL *is* the in-progress signal:
  `WHERE completed_at IS NULL` = "still running", no extra flag column needed.
- `expense_workerledgerentry.amount` — **NOT NULL** on purpose: an unknown money
  amount is meaningless, so the column refuses the concept (ch 13).

# Visual Diagram
```
cost_per_kg:  ┌──────┐   ┌──────┐   ┌──────┐
              │ 240  │   │ 185  │   │ NULL │  ← "not entered", NOT free
              └──────┘   └──────┘   └──────┘
sum()   → 425          (skips the NULL — sums only what is KNOWN)
count(*)=3  count(cost_per_kg)=2   ← the difference = unpriced rolls
report  → "2 priced · 1 unpriced"  ← the honest sentence NULL makes possible
```

# Practical — try it yourself
```sql
SELECT NULL = NULL, NULL + 5, coalesce(NULL, 'fallback');
--  (empty) | (empty) | fallback

SELECT count(*) AS rows, count(completed_at) AS finished
FROM production_adda;
-- rows=28, finished=<less> — the gap is my in-progress Addas

SELECT code FROM production_adda WHERE completed_at IS NULL;   -- correct
SELECT code FROM production_adda WHERE completed_at = NULL;    -- always ZERO rows
```

# Production Walkthrough
NULL is a *policy* on the live system, not an accident:
- **Unpriced cloth rolls** carry `cost_per_kg = NULL`. Material-cost reports print "unpriced" rather than adding ₹0 — so the owner can see what is missing instead of trusting a wrong total.
- **`completed_at IS NULL`** is the in-progress signal for every Adda and stage. There is no separate boolean to fall out of sync with it.
- **Money amounts are NOT NULL** — an unknown wage is meaningless, so the column refuses the concept entirely.

# Debugging Guide
"Rows are missing from my report":
1. **Suspect NULL first** if the filter uses `!=`, `NOT IN`, or `<>`. Re-run with `OR col IS NULL` and see if the rows appear.
2. **Compare `count(*)` with `count(col)`** — the gap *is* your NULL count.
3. **Check aggregates.** `avg()` silently averages only known values; state that in the report or it lies by omission.
4. **`NOT IN (subquery)` returning nothing** is the classic (ch 09) — one NULL in the list poisons every comparison.

# Performance Notes
- NULLs are cheap to store (a bitmap, not a value) — using NULL costs less than a sentinel string.
- B-tree indexes *do* index NULLs in Postgres, so `WHERE x IS NULL` can use an index.
- A **partial index** (`WHERE completed_at IS NULL`) is an excellent fit for "find the in-progress rows" on a large table (ch 14).

# Security Considerations
- A NULL in a permission-ish field must never be read as "allowed". Default to denial: absent data is not consent.
- NULL-handling bugs are a real access-control risk — a filter that silently drops rows can equally silently *include* them when inverted.

# Architecture Decisions
- **Honest-NULL over comfortable-zero** — a policy this codebase states out loud. Zero is a *claim* ("free"); NULL is an *admission* ("not entered").
- **NULL as state, not a flag column** — `completed_at IS NULL` beats `is_complete` because two columns can disagree and one cannot.
- **`CHECK (x IS NULL OR x >= 0)`** — the schema permits unknown and forbids impossible. Both halves are deliberate (ch 13).

# Best Practices
- `IS NULL` / `IS NOT NULL`, always. `= NULL` is a silent no-op.
- Decide, per column, what NULL *means* — and write it in the model's docstring.
- Use `coalesce()` at the **display** edge, never to hide a NULL mid-calculation.
- If NULL is never legitimate, make the column `NOT NULL` and let the database enforce it.

# Beginner Mistakes
- `= NULL` instead of `IS NULL` — silently returns nothing, looks like "no data".
- Storing 0 to mean "unknown" — poisons every sum and average downstream.
- Forgetting `!=` filters also drop NULL rows — reports quietly undercount.
- Averaging a NULL-able column and reporting it as the average of *everything*.

# Interview Questions
- **Junior:** *What is NULL and how do you test for it?* — absence of value;
  `IS NULL` / `IS NOT NULL`.
- **Mid:** *Why does `WHERE col != 'x'` miss NULL rows?* — `NULL != 'x'` is
  NULL, and WHERE keeps only true. **This one catches seniors.**
- **Mid:** *count(\*) vs count(col)?* — rows vs non-NULL values.
- **Senior:** *Design question: "unknown" vs "zero" vs "not applicable" — how do
  you model each?* — NULL for unknown; real 0 for a true zero; sometimes a
  separate status column for not-applicable. Cite a real system that shows
  "unpriced" rather than ₹0 (mine).
- **Staff:** *NULL breaks the guarantees people assume. Where does that actually bite,
  and what do you do about it?* — Three places, and they are all silent. **Aggregates:**
  `SUM` and `AVG` skip NULLs, so an average over partially-missing data is an average of
  a different population than the reader believes — `AVG(rate)` across unrated stages is
  not the average rate. **Uniqueness:** in standard SQL, NULLs are distinct for a unique
  constraint, so a `UNIQUE` column happily accepts many NULL rows; if "at most one active
  record" matters, you need a partial unique index (`WHERE deleted_at IS NULL`), not a
  nullable unique column. **Joins and `NOT IN`:** a NULL anywhere in a `NOT IN` subquery
  makes the whole predicate never true, which silently returns zero rows rather than
  erroring — `NOT EXISTS` is the safe form. The structural answer is to make NULL a
  deliberate, documented choice rather than a default: `NOT NULL` plus a default wherever
  absence is not a real state, a `CHECK` constraint when nullability is conditional, and
  the honest three-way distinction (unknown / zero / not-applicable) modelled explicitly.
  This codebase learned the payable version of that: `good` is `NOT NULL` because it is
  what gets paid, while `alter` and `missing` are nullable observations — the money column
  is not allowed to be ambiguous.

### Why interviewers ask these — and the answer that separates levels

| Testing for | Weak answer | What lands |
|---|---|---|
| Do you know NULL is *unknown*, not empty? | "NULL means blank or zero." | NULL is **absence of knowledge**. It is not 0, not `''`, and **not equal to itself** — which is why `IS NULL` exists at all. |
| Do you know NULL breaks your WHERE clause? | "`col != 'x'` returns everything else." | `NULL != 'x'` evaluates to **NULL**, and WHERE keeps only TRUE — so NULL rows silently vanish. **This one catches seniors.** Say three-valued logic. |
| Do you know which aggregates skip NULL? | "count() counts rows." | `count(*)` counts rows; `count(col)` counts **non-NULL values**. Same for `avg`/`sum` — they ignore NULL rather than treating it as 0, which changes the number. |
| Can you model *unknown* vs *zero* vs *not applicable*? | "Default it to 0." | NULL for unknown, real 0 for a true zero, and sometimes a **status column** for not-applicable. Defaulting to 0 invents a fact — my system shows a roll as **"unpriced"** rather than **₹0**, because ₹0 is a claim nobody made. |

**The killer follow-up:** *"Show me a query where adding a row changed an average without changing any existing value."* — a NULL becoming a real 0. If you cannot see why that moves the average, you have not internalised three-valued logic.

# Revision Notes
- NULL = **unknown**, not zero, not empty string.
- Three-valued logic: WHERE keeps only **true**, so NULL rows vanish from `!=`.
- `IS NULL` is the only correct test.
- Aggregates skip NULLs; `count(*)` vs `count(col)` reveals how many.
- Honest-NULL: reports say "unpriced" instead of lying with ₹0.

# Cheat Sheet
- NULL = no value recorded; three-valued logic (true/false/**unknown**)
- `IS NULL`, never `= NULL` · aggregates skip NULLs · `coalesce()` for display
- honest-NULL beats comfortable-zero — zero is a *claim*, NULL is an *admission*

# My ERP Section
| Column | NULL means |
|---|---|
| `clothroll.cost_per_kg` | price not entered — reports say "unpriced" |
| `adda.completed_at` | still in progress |
| `workflowstage.cost_rate` (grouped member stages) | "paid via another stage", not ₹0 — ch 13's C-1 guard |
| `ledgerentry.amount` | forbidden — NOT NULL, money can't be unknown |

# Practice Tasks
1. **Read the code:** open `config/raw_materials/models.py` and find `cost_per_kg`. Is it nullable? Find one comment explaining why.
2. **Debug:** write a query that *wrongly* omits unpriced rolls, then fix it. Show both row counts.
3. **Design:** the owner wants "average cloth price". Write the query, then write the sentence you would put next to the number so it is not misleading.
4. **Architecture:** propose the CHECK constraint you would add to `cost_per_kg` and explain, in one line, why `CHECK (cost_per_kg >= 0)` alone would be wrong.

# Homework
1. Run the count(*) vs count(completed_at) query; state the number of unfinished Addas out loud.
2. `SELECT count(*), count(cost_per_kg) FROM raw_materials_clothroll;` — how many unpriced rolls do I have?
3. Write one sentence: why would `cost_per_kg = 0` have been a lie?

# Further Reading & Live Resources
- [Modern SQL on NULL](https://modern-sql.com/concept/null) — best short treatment on the internet
- [Postgres: comparison & NULL](https://www.postgresql.org/docs/current/functions-comparison.html)
- [Postgres docs — Functions and operators: comparison](https://www.postgresql.org/docs/current/functions-comparison.html) — `IS NULL`, `IS DISTINCT FROM`, and three-valued logic
- [Postgres docs — `coalesce`, `nullif`](https://www.postgresql.org/docs/current/functions-conditional.html) — the two functions that make NULL manageable
- [Postgres docs — partial indexes](https://www.postgresql.org/docs/current/indexes-partial.html) — the fix for "UNIQUE accepts many NULLs"
- [Django docs — `null` vs `blank`](https://docs.djangoproject.com/en/5.0/ref/models/fields/#null) — the distinction that confuses every Django beginner exactly once
- Sibling chapter: [08 — GROUP BY & Aggregates](08_GROUP_BY_And_Aggregates.md) — where NULL silently changes your averages
