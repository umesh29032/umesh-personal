---
id: sql-course-06-filtering-and-expressions
type: lesson
status: active
owner: handwritten
scope: sql, postgresql — database fundamentals taught from this ERP
anchors: config/expense/services/settlement_service.py, config/production/services/pool_service.py
verified: 2026-08-01
---

# 06 — Filtering & Expressions

> Part of [SQL From Zero](00_COURSE_OVERVIEW.md). Prev: [05](05_SELECT_Basics.md) · Next: [07 — JOINs](07_JOINs.md).

# Learning Objectives
By the end of this chapter you can:
- combine conditions with AND/OR and **parenthesise correctly by reflex**
- choose between `IN`, `BETWEEN`, `LIKE` and `IS NULL` for a given question
- explain why `LIKE '%x%'` cannot use an index
- write a `CASE` expression for a readable report column

# Purpose
To go from "I can list rows" to "I can ask precise questions" — and to meet the
`AND`/`OR` precedence bug that silently corrupts reports in every codebase on earth.

# The Problem
Real questions are compound: *"completed 3-PATTI Addas"*, *"ledger entries above
₹1,000"*, *"Addas that never finished"*. Each extra condition is a chance to write
something that runs fine and answers the **wrong question** — the most dangerous
kind of bug, because nothing errors.

# Theory (from zero)

**Comparison operators:** `=` equal · `<>` or `!=` not equal · `>` `<` `>=` `<=`.
(SQL uses a single `=` for comparison, unlike Python's `==`.)

**Combining tests:**
- `AND` — both must be true
- `OR` — either may be true
- `NOT` — flips a test
- **`AND` binds tighter than `OR`** — exactly like `×` before `+` in arithmetic.
  So `A OR B AND C` means `A OR (B AND C)`, *not* `(A OR B) AND C`.
  **Always write the parentheses you mean.** This is the bug.

**Set and range shortcuts:**
- `IN ('a','b','c')` — matches any of a list (cleaner than a pile of ORs)
- `BETWEEN 100 AND 500` — inclusive on both ends (watch that: *inclusive*)
- `IS NULL` / `IS NOT NULL` — the only correct NULL test (ch 04)

**Text matching:**
- `LIKE 'prefix%'` — `%` = any run of characters, `_` = exactly one character
- `ILIKE` — same but case-insensitive (**Postgres-specific**; standard SQL has no ILIKE)
- ⚠️ `LIKE '%patti%'` (leading `%`) **cannot use a normal index** — the index is
  sorted from the front, like a phonebook. Prefix search is fast; contains-search
  scans everything (ch 14).

### The operator map — one place to look

```
   ┌─ COMPARE ────────────────────────────────────────────────────────┐
   │  =   <>  !=   >   <   >=   <=            (SQL uses ONE  =  )      │
   ├─ COMBINE ────────────────────────────────────────────────────────┤
   │  AND   OR   NOT        ⚠️ AND binds TIGHTER — parenthesise!        │
   ├─ SHORTCUTS ──────────────────────────────────────────────────────┤
   │  IN ('a','b')          one of a list                              │
   │  BETWEEN 100 AND 500   inclusive BOTH ends                        │
   │  IS NULL / IS NOT NULL the ONLY NULL test (ch 04)                 │
   ├─ TEXT ───────────────────────────────────────────────────────────┤
   │  LIKE  'pre%'          % = any run · _ = exactly one char   FAST  │
   │  LIKE  '%mid%'         leading % ⇒ index useless          SLOW ⚠️  │
   │  ILIKE 'PrE%'          case-insensitive (Postgres-only)           │
   └──────────────────────────────────────────────────────────────────┘
```

### AND/OR precedence — the bug that never errors

```
   I MEANT:   completed 3-PATTI Addas, or completed T-SHIRT Addas
   I WROTE:   WHERE status='completed' AND code LIKE '3-PATTI-%'
                 OR code LIKE 'T-SHIRT-%'

   SQL READS IT AS:
        ( status='completed' AND code LIKE '3-PATTI-%' )
        OR
        ( code LIKE 'T-SHIRT-%' )              ← status IGNORED here!
        └─ every T-SHIRT Adda comes back, finished or not.

   WHAT I NEEDED:
        status='completed'
        AND ( code LIKE '3-PATTI-%' OR code LIKE 'T-SHIRT-%' )
              └─────────── brackets make the intent explicit ──────┘
   ═══════════════════════════════════════════════════════════════════
   Both versions RUN. Both return rows. Only one answers my question.
   No error message will ever tell you which. Hence: always bracket.
```

**Expressions** — you can compute in SELECT and WHERE:
- `lower(code)`, `upper()`, `length()`
- `||` glues text: `code || ' (' || status || ')'`
- `now()` — current moment; timestamps support arithmetic: `now() - interval '7 days'`
- `CASE WHEN … THEN … ELSE … END` — inline if/else, for readable report columns

> 💡 **Samjho aise:** WHERE ek **darwaze ka chowkidar** hai. Ek shart ho to
> aasaan. Do-teen shart mile — "completed HO, aur 3-PATTI ka HO, YA phir naya
> ho" — to **bracket lagana zaroori** hai, warna chowkidar apni marzi se
> samjhega (AND pehle, OR baad mein) aur galat aadmi andar aa jaayega. Galti
> error nahi deti — bas jawaab galat aata hai. Wahi sabse khatarnaak hai.

# Real World Example (My ERP)
- *"Addas still running"* = `WHERE completed_at IS NULL` — no separate flag column
  needed, the NULL **is** the state (ch 04). Real result on my data:
  `3-PATTI-009`, `3-PATTI-010`, `3-PATTI-012`, …
- *"3-PATTI family only"* = `WHERE code LIKE '3-PATTI-%'` — works because my Adda
  codes are minted as `<product code>-<counter>` (`adda_service`), so the product
  is literally the prefix. That prefix search is index-friendly; searching
  `'%PATTI%'` would not be.
- Money filters (`amount > 1000`) run against `numeric` columns, so comparisons
  are exact — no float fuzz (ch 03).

# Visual Diagram
```
  WHERE status='completed' OR code LIKE '3-PATTI-%' AND completed_at IS NOT NULL
                                        └────────── binds first (AND) ─────────┘
  reads as:  status='completed'  OR  ( 3-PATTI...  AND  finished )
  probably MEANT:               ( status='completed' OR 3-PATTI... )  AND finished
                               └── write the brackets and the doubt disappears ──┘
```

# Practical — try it yourself
```sql
-- compound filter (REAL result on my data: 5 rows)
SELECT count(*) FROM production_adda
WHERE status = 'completed' AND code LIKE '3-PATTI-%';       -- 5

-- prefix search, newest first (REAL output)
SELECT code, status FROM production_adda
WHERE code LIKE '3-PATTI-%' ORDER BY id DESC LIMIT 3;
--  3-PATTI-018 | completed
--  3-PATTI-017 | completed
--  3-PATTI-015 | completed

-- a list of allowed values
SELECT count(*) FROM production_adda
WHERE status IN ('completed','in_progress');                 -- 28 (all of them)

-- money threshold, exact arithmetic
SELECT count(*) FROM expense_workerledgerentry WHERE amount > 1000;   -- 3

-- unfinished work (NULL as the state)
SELECT code FROM production_adda WHERE completed_at IS NULL ORDER BY id LIMIT 3;
--  3-PATTI-009 | 3-PATTI-010 | 3-PATTI-012

-- expressions + CASE for a readable report column
SELECT code,
       CASE WHEN completed_at IS NULL THEN 'running' ELSE 'done' END AS state
FROM production_adda ORDER BY id DESC LIMIT 4;

-- time arithmetic: anything created in the last 30 days
SELECT count(*) FROM production_adda WHERE created_at > now() - interval '30 days';
```

# Production Walkthrough
- **`code LIKE '3-PATTI-%'`** works as a *fast prefix search* only because Adda codes are minted `<product>-<counter>` by `adda_service`. The data shape and the query shape were designed together — that is not luck.
- **`completed_at IS NULL`** drives every "in progress" list on the dashboards.
- Money filters run on `numeric`, so `amount > 1000` is exact — no float boundary surprises (ch 03).
- Search boxes in this app filter on indexed prefixes, not `%term%`, precisely to avoid the scan in Performance Notes.

# Debugging Guide
"The filter returns too many / too few rows":
1. **Print the query.** Then read the WHERE aloud, inserting the parentheses SQL will use. Most bugs are audible.
2. **Split the condition.** Run each clause alone and count. The clause whose count surprises you is the bug.
3. **Suspect NULL** on any `!=` / `NOT IN` (ch 04).
4. **Check case.** `LIKE 'patti%'` will not match `'PATTI…'`; decide between `ILIKE` and normalising the data.
5. **Check the boundary.** `BETWEEN` includes both ends; off-by-one totals often start here.

# Performance Notes
- `LIKE 'prefix%'` → index-friendly. `LIKE '%middle%'` → full scan; fix with a `pg_trgm` index or full-text search (ch 24).
- `func(col) = value` cannot use a plain index on `col`; you need an **expression index** on `func(col)`.
- `IN (list)` with a handful of literals is fine; with a large subquery prefer `EXISTS` (ch 09).
- A filter that matches most rows will (correctly) be answered by a sequential scan (ch 14).

# Security Considerations
- Filters are the most common place user input meets SQL. **Parameterise, never concatenate** (ch 22) — `WHERE code = %s` with the value passed separately.
- A filter is not an authorisation check. `WHERE user_id = <from the session>` is security; `WHERE user_id = <from the URL>` is a vulnerability.
- `ILIKE` on unindexed columns is a cheap denial-of-service vector on large tables.

# Architecture Decisions
- **Business codes carry a meaningful prefix**, which makes the common search an indexed prefix scan instead of a wildcard scan.
- **State is expressed as NULL-able timestamps** (`completed_at`) rather than boolean flags, so filters are also the audit trail.
- **Case handling is normalised at write time** (e.g. emails) rather than paid for on every read.

# Best Practices
- Parenthesise every mixed AND/OR. Every time. No exceptions.
- Prefer `IS NULL` over clever tricks; prefer explicit over short.
- Use `CASE` to make report columns readable instead of post-processing in Python.
- When a filter feels complex, name it in a CTE (ch 09) — future-you will thank you.

# Beginner Mistakes
- **Missing parentheses around mixed AND/OR.** Runs perfectly, answers wrong.
  Report is off; nobody notices for months.
- `= NULL` instead of `IS NULL` — returns zero rows, looks like "no data".
- Forgetting that `!=` also **drops NULL rows** (ch 04) — undercounts silently.
- `BETWEEN` assumed exclusive. It includes both endpoints.
- `LIKE '%text%'` on a big table and then wondering why the page is slow.
- Case sensitivity: `LIKE 'patti%'` will not match `'PATTI…'`. Use `ILIKE` or
  `lower(col) LIKE lower(…)` — noting the latter needs an expression index to stay fast.

# Interview Questions
- **Junior:** *`LIKE` vs `ILIKE`?* — pattern match; ILIKE is Postgres's case-insensitive variant. `%` = any run, `_` = one char.
- **Junior:** *Is `BETWEEN` inclusive?* — yes, both ends.
- **Mid:** *`A OR B AND C` — how does SQL group it?* — `A OR (B AND C)`; AND has higher precedence. **A favourite trap question.**
- **Mid:** *Why is `WHERE col LIKE '%x%'` slow even with an index on col?* — B-tree indexes are ordered from the left; a leading wildcard has no prefix to seek, so it degrades to a full scan. Fixes: trigram (pg_trgm) index or full-text search.
- **Senior:** *`WHERE lower(email) = 'x'` is slow despite an index on email — why, and the fix?* — the function makes the indexed value unusable; create an *expression index* on `lower(email)` (or store a normalised column).
- **Staff:** *How do you keep a compound-filter report provably correct?* — parenthesise explicitly, express the intent as a test with known fixtures, and cross-check the total by a second independent path (this project's reconciliation habit, ch 08).

### Why interviewers ask these — and the answer that separates levels

| Testing for | Weak answer | What lands |
|---|---|---|
| Do you know operator precedence, or do you guess? | "`A OR B AND C` reads left to right." | **AND binds tighter than OR**, so it means `A OR (B AND C)`. Favourite trap. The senior move: **always parenthesise** so the reader never has to know. |
| Do you know why a leading wildcard kills an index? | "It is indexed, so LIKE is fast." | A B-tree is ordered **from the left**; `'%x%'` gives no prefix to seek from, so it degrades to a full scan. Fix: **`pg_trgm` trigram index** or full-text search — not "add another index". |
| Do you know a function on the column disables the index? | "There is an index on email, so `lower(email) = ...` uses it." | Wrapping the column makes the stored value unusable. Fix: an **expression index** on `lower(email)`, or store a normalised column. Same rule for `date(created_at)` and casts. |
| Can you prove a compound filter is correct? | "I tested it and the numbers looked right." | Parenthesise explicitly, pin the intent as a **test with known fixtures**, then cross-check the total by a **second independent path**. "Looked right" is not a claim you can defend about money. |

**The killer follow-up:** *"This report's filter is `status = A OR status = B AND created > X`. What does the business think it says, and what does it actually say?"* — the gap between those two sentences is where wrong invoices come from.

# Revision Notes
- `AND` binds tighter than `OR` — **parenthesise**.
- `IN` for lists · `BETWEEN` is inclusive · `IS NULL` for unknown.
- `LIKE 'pre%'` fast; `LIKE '%mid%'` scans everything.
- `func(col)` hides the index → expression index needed.
- A wrong filter **does not error** — it answers the wrong question.

# Cheat Sheet
- `=  <>  >  <  >=  <=` · `AND` before `OR` — **parenthesise**
- `IN (…)` list · `BETWEEN a AND b` inclusive · `IS NULL` only NULL test
- `LIKE 'pre%'` fast · `LIKE '%mid%'` full scan · `ILIKE` = case-insensitive (PG)
- `CASE WHEN … THEN … ELSE … END` for report columns
- `now() - interval '7 days'` for time windows

# My ERP Section
| Filter idea | Where it appears |
|---|---|
| `completed_at IS NULL` = in progress | Adda lists, dashboards, `page-slow` playbook |
| `code LIKE '<PRODUCT>-%'` | works because `adda_service` mints `<product>-<counter>` codes |
| exact money comparisons | `numeric` columns (ch 03) — no float fuzz |
| case-insensitive email login | normalised at the app layer, not by scanning with `lower()` |

# Practice Tasks
1. **Read the code:** find where Adda codes are generated (`config/production/services/adda_service.py`). Explain why that shape makes `LIKE '3-PATTI-%'` fast.
2. **Debug:** write a filter with mixed AND/OR *without* parentheses, then with them, on the same data. Show both counts and explain the gap.
3. **Design:** the owner wants a search box over Adda codes. Design the query so it stays index-friendly. What do you tell him he *cannot* have cheaply?
4. **Architecture:** argue whether case-insensitive search should be solved with `ILIKE`, an expression index, or normalising at write time.

# Homework
1. Write one query for *"completed Addas that are NOT 3-PATTI"*. Then run the same logic with the parentheses moved and explain the difference in results.
2. Count ledger entries `BETWEEN 100 AND 500`. Then re-run with `> 100 AND < 500`. Why do the numbers differ?
3. Add a `CASE` column labelling each Adda `'running'`/`'done'`, and sanity-check the counts against `WHERE completed_at IS NULL`.

# Further Reading & Live Resources
- [SQLBolt lessons on filtering](https://sqlbolt.com/lesson/select_queries_with_constraints)
- [Postgres pattern matching (LIKE / regex)](https://www.postgresql.org/docs/current/functions-matching.html)
- [Postgres date/time functions](https://www.postgresql.org/docs/current/functions-datetime.html)
- [Use The Index, Luke — LIKE and wildcards](https://use-the-index-luke.com/sql/where-clause/searching-for-ranges/like-performance-tuning)
