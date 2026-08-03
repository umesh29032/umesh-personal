---
id: sql-course-03-data-types-and-money
type: lesson
status: active
owner: handwritten
scope: sql, postgresql — database fundamentals taught from this ERP
anchors: config/expense/services/settlement_service.py, config/production/services/pool_service.py
verified: 2026-08-01
---

# 03 — Data Types, and Why Money Is Never a Float

> Part of [SQL From Zero](00_COURSE_OVERVIEW.md). Prev: [02](02_Tables_Rows_Columns_Keys.md) · Next: [04 — NULL](04_NULL.md).

# Learning Objectives
By the end of this chapter you can:
- name the type you would pick for money, time, flags and identifiers — and defend each
- demonstrate the float error in one line, and explain *why* it happens
- read `numeric(12,2)` and state its exact ceiling
- explain why a phone number is text

# Purpose
To learn what a column *type* promises — and to burn in the single most
important database rule in my ERP: **every ₹ is `numeric`, never float**, which
is the only reason my audit could prove the ledger to the paisa.

# The Problem
A column that accepts anything protects nothing. Types are the first wall: a
letter cannot enter a number column, a random string cannot enter a timestamp.
And for money there is a subtler enemy — a "number" type that is *slightly wrong
on purpose* (float), whose errors accumulate silently across thousands of wage
entries until the books don't balance and nobody can say where.

# Theory (from zero)
The types my project actually uses:

| Type | In my DB | The promise |
|---|---|---|
| `bigint` | every `id` | whole numbers, astronomically large |
| `varchar(n)` | `code`, `status` | text with a max length check |
| `text` | notes, reasons | unlimited text |
| `boolean` | `is_active`, `credits_workers` | true/false only |
| `timestamp with time zone` | every `created_at` | exact moment, timezone-safe |
| **`numeric(12,2)`** | **`amount`, `cost_rate`, every ₹** | **exact decimal math** |
| `date` | birth dates | a day, no time |
| `jsonb` | patterns_ai snapshots | structured blob (ch 23) |

**The float lie.** Computers' fast decimal type (float) stores binary fractions;
most decimal fractions can't be represented exactly. `0.1 + 0.2` = `0.30000000000000004`.
One entry: invisible. A thousand settlements: real rupees missing, untraceably.
`numeric` is slower and **exact** — the accountant's type.

### Why float cannot hold ₹0.10 — the actual reason

```
   Decimal 0.1 in binary is 0.0001100110011001100…  ← REPEATING, forever
   ┌──────────────────────────────────────────────────────────────┐
   │  Just like 1/3 in decimal = 0.3333…  you can never write it   │
   │  exactly with a finite number of digits.                      │
   │  A float has 53 bits. It must CHOP. So it stores a number     │
   │  very slightly ≠ 0.1 — and then does arithmetic on the lie.   │
   └──────────────────────────────────────────────────────────────┘
        0.1 (stored)  +  0.2 (stored)  =  0.30000000000000004
        ▲ tiny error      ▲ tiny error      ▲ errors ADD UP

   numeric stores the DIGITS themselves (1, 0 and a decimal position),
   so 0.1 is exactly 0.1. Slower. Correct. Non-negotiable for wages.
```

### The type decision tree — memorise this shape

```
   What am I storing?
        │
        ├── MONEY / anything summed for a human ─────▶ numeric(12,2)   ⚠️ NEVER float
        │
        ├── a moment in time ───────────────────────▶ timestamptz
        │        (a day only, no clock) ────────────▶ date
        │
        ├── a whole number (count, id) ─────────────▶ bigint / integer
        │
        ├── true/false ─────────────────────────────▶ boolean
        │
        ├── text of any length ─────────────────────▶ text
        │        (with a real max) ─────────────────▶ varchar(n)
        │
        ├── digits that are an IDENTIFIER, not maths
        │   (phone, PIN, invoice no.) ──────────────▶ text  ← leading zeros survive
        │
        └── shape genuinely varies ─────────────────▶ jsonb  (ch 23, know the cost)
   ══════════════════════════════════════════════════════════════════════
   float / double appear NOWHERE in this tree for business data.
   They are for physics and graphics, where 1e-16 error is irrelevant.
```

**timezone-aware timestamps.** `timestamp with time zone` stores an absolute
moment; display converts to local time. Naive timestamps (without tz) are how
"the report is off by 5:30 hours" bugs are born.

> 💡 **Samjho aise:** Float ek **jaldi-jaldi hisaab karne wala munshi** hai jo har
> entry mein paisa-do-paisa ki galti karta hai. Ek entry mein farq dikhta hi nahi;
> saal bhar baad khaata hi nahi milta — aur sabse buri baat, **pata nahi chalta
> galti kahan hui**. `numeric` dheema munshi hai par **paai-paai sahi**. Tankhwah
> ke register pe hamesha dheema-sahi wala baithao. Speed baad mein, sach pehle.

# Real World Example (My ERP)
- `expense_workerledgerentry.amount` = `numeric(12,2)` → the ledger sums to
  exactly **₹18,254.25**, provable, byte-stable (the golden tests pin such totals).
- `production_workflowstage.cost_rate` = `numeric` — the frozen piece-rate.
- Every table carries `timestamptz` pairs via `TimeStampedModel`.
- `production_adda.status` is `varchar` constrained by application choices —
  and the DB-level version of such rules is chapter 13.

# Visual Diagram
```
float path:    0.1 + 0.2  ──▶ 0.30000000000000004   (fast, WRONG)
numeric path:  0.1 + 0.2  ──▶ 0.3                   (slower, EXACT)

1,000 wage entries later:
float ledger:   ₹18,254.25 ± who-knows      ← unauditable
numeric ledger: ₹18,254.25 exactly          ← my actual audit result
```

# Practical — try it yourself
Pure arithmetic — safe anywhere, touches no table:
```sql
SELECT 0.1::float + 0.2::float AS float_lie,
       0.1::numeric + 0.2::numeric AS numeric_truth;
--        float_lie        | numeric_truth
-- 0.30000000000000004     | 0.3
```
(`::type` means "treat this value as that type" — a cast.)
```sql
-- see a real money column's declared type:
SELECT column_name, data_type, numeric_precision, numeric_scale
FROM information_schema.columns
WHERE table_name = 'expense_workerledgerentry' AND column_name = 'amount';
-- amount | numeric | 12 | 2      → 12 digits total, 2 after the point
```

# Production Walkthrough
Types are why the audit could prove ₹18,254.25 to the paisa on the live system:
- Every ₹ column is `numeric`, so 201 additions carry **zero** accumulated error.
- The golden tests assert exact rupee strings (₹344.25 / ₹801 / ₹633). With floats those tests could not exist — you cannot pin a number that drifts.
- `timestamptz` everywhere means a worker in one timezone and a report in another agree on *when* work happened.

# Debugging Guide
"The total is off by a few paise":
1. **Check the column type first** — `information_schema.columns`. If anything in the chain is `float`/`double precision`, stop; you have found it.
2. **Look for a cast.** `::float` anywhere in a money path re-introduces the error even if the column is `numeric`.
3. **Check the rounding boundary.** `numeric(12,2)` rounds on write; a calculation that should round *at the end* but rounds *per row* gives a different total. Round once, at the edge.
4. **Reconcile two ways** (ch 08) — a mismatch localises the bug faster than reading code.

# Performance Notes
- `numeric` is slower than integer/float arithmetic — correct and irrelevant at this scale. Never trade money correctness for speed.
- If you ever need speed on money at scale, store **integer paise** (an exact integer), not float.
- `text` vs `varchar(n)` is a performance non-issue in Postgres; the length is just a constraint.

# Security Considerations
- Type checking is a *validation* layer: a `numeric` column refuses `'DROP TABLE'` outright. Types are the cheapest wall you have.
- Over-wide text columns are an abuse surface (someone pastes 10 MB into a notes field). A CHECK on length is legitimate defence.
- Timestamps are audit evidence — `timestamptz` keeps them comparable across servers.

# Architecture Decisions
- **`numeric(12,2)` for money** — exact, and the precision states the business ceiling (±₹9,999,999,999.99) explicitly.
- **`timestamptz`, never naive** — one absolute instant, converted for display.
- **Honest-NULL over sentinel values** — no `-1` or `0` meaning "unknown" (ch 04).
- **`jsonb` quarantined to `patterns_ai`** — schema flexibility only where shape genuinely varies (ch 23).

# Best Practices
- Decide the type from the *question you will ask*: will I sum it, sort it, or just show it?
- Money and identifiers never share a type.
- Store the smallest honest precision; do not invent decimals the business does not have.
- Keep one rounding point in the whole calculation, and put it at the boundary.

# Beginner Mistakes
- Money in float/double "because it's numbers". The career-limiting classic.
- Storing dates as text ("31/07/2026") — unsortable, unmathable, ambiguous.
- Phone numbers in integer columns — leading zeros vanish, "+" impossible.
  Identifiers that aren't math = text.
- Choosing `varchar(20)` casually, then real data needs 25. In Postgres,
  prefer `text` + a CHECK if a limit truly matters.

# Interview Questions
- **Junior:** *Why never float for money?* — binary floats can't represent most
  decimal fractions; errors accumulate silently. Use NUMERIC/DECIMAL. *(Asked in
  practically every backend interview.)*
- **Mid:** *varchar vs text in Postgres?* — same performance; varchar(n) is just
  a length constraint. (In other DBs the difference is real — name the caveat.)
- **Mid:** *timestamp vs timestamptz?* — tz stores an absolute instant and
  converts on display; naive timestamps invite timezone bugs.
- **Senior:** *Precision/scale of numeric(12,2)?* — 12 significant digits, 2
  after the decimal → max ±9,999,999,999.99. Know your ceiling before payroll grows.
- **Staff:** *How do you keep money correct across an entire system, not just one
  column?* — The column type is necessary and nowhere near sufficient. `numeric` stops
  float drift, but the expensive bugs live above it. You need one write path — this
  project has a single-writer service per ledger/audit table, and settlement is the
  *only* money-write boundary, so a new write path elsewhere is a design review, not a
  code review. You need append-only history with reversing entries rather than
  `UPDATE`s, so a correction is auditable instead of invisible. You need database-level
  `CHECK` constraints as the last line of defence, because application validation is
  bypassable by a shell or a migration — there are **71** `CheckConstraint`s declared in
  the models here (147 occurrences once historical migrations are counted, since each one
  is replayed there). You need
  a fixed rounding policy applied at exactly one place, since rounding twice is a real
  source of one-paisa drift. And you need golden tests that assert exact totals, not
  approximations: ₹344.25 must stay byte-identical, because a money test that tolerates
  a delta cannot detect the bug it exists to catch. Finally, get the *date basis* right —
  this project shipped a defect where a UTC-derived date stamped IST ledger rows, wrong
  for 5.5 hours daily and a whole month on the 1st.

### Why interviewers ask these — and the answer that separates levels

| Testing for | Weak answer | What lands |
|---|---|---|
| The money question. Do you know *why*, not just the rule? | "Use decimal for money, float is inaccurate." | Binary floating point **cannot represent most decimal fractions** (0.1 has no exact binary form), so error accumulates silently across additions. Use `NUMERIC`/`DECIMAL` — or **integer paisa**, which is what this system does, because an integer cannot drift at all. |
| Do you know the Postgres-specific truth about varchar? | "varchar is faster than text." | In **Postgres they perform identically** — `varchar(n)` is just a length **constraint**. Say that, then add the caveat that in other engines the difference is real. Naming the caveat is what reads as senior. |
| Do you understand timestamptz? | "timestamptz stores the timezone." | It stores an **absolute instant** (UTC) and converts on display — it does **not** store your zone. A naive `timestamp` invites exactly the bug this repo shipped: a UTC date used as a local one, wrong for 5.5h every day. |
| Do you know your numeric ceiling before it bites? | "numeric(12,2) is plenty." | 12 **significant** digits with 2 after the point → max **±9,999,999,999.99**. Overflow raises, it does not silently wrap. Know the ceiling before payroll grows into it. |

**The killer follow-up:** *"Show me where rounding happens in your money path, and who rounds first."* — if rounding happens in two places (display and storage) they will disagree by paise, and a ledger that disagrees with its own total is unauditable.

# Revision Notes
- Money → `numeric`. Never float. This is the chapter's whole point.
- Float can't hold most decimals exactly; errors **accumulate silently**.
- Time → `timestamptz`. Flags → `boolean`. Identifiers-that-aren't-maths → `text`.
- `numeric(12,2)` = 12 digits, 2 after the point.
- Types are the first validation wall (ch 13 is the last).

# Cheat Sheet
- type = promise about what can live in the column
- money → `numeric`, always; time → `timestamptz`; flags → `boolean`
- identifiers that aren't math (phones, pins) → text
- `SELECT 0.1::float + 0.2::float;` — the one-line proof to remember

# My ERP Section
| Rule | Where enforced |
|---|---|
| ₹ = numeric(12,2) | `WorkerLedgerEntry.amount`, `cost_rate`, `expected_earning`… |
| tz-aware everywhere | `USE_TZ` in settings + timestamptz columns |
| exact totals pinned | golden tests (₹344.25 / ₹801 / ₹633 byte-identical) |

# Practice Tasks
1. **Read the code:** find `amount` on `WorkerLedgerEntry` in `config/expense/models.py`. What are its `max_digits` and `decimal_places`, and what business ceiling do they imply?
2. **Debug:** compute `SELECT sum(amount::float) FROM expense_workerledgerentry;` and compare with `sum(amount)`. Are they identical here? Explain why the risk is still real at 100× the rows.
3. **Design:** the factory wants to record cloth width to the nearest 1/8 inch. Pick a type and justify it. What breaks with float? What breaks with integer?
4. **Architecture:** argue for and against storing money as integer paise instead of `numeric`.

# Homework
1. Run the float-lie SELECT. Then compute `SELECT (0.1::float * 3) = 0.3::float;` — explain the answer.
2. Find the type of `raw_materials_clothroll.cost_per_kg` via `information_schema.columns`.
3. List three real-world values that look numeric but must be stored as text, and say why.

# Further Reading & Live Resources
- [Postgres numeric types](https://www.postgresql.org/docs/current/datatype-numeric.html)
- [0.30000000000000004.com](https://0.30000000000000004.com/) — the float lie, visualised, every language
- [Postgres date/time types](https://www.postgresql.org/docs/current/datatype-datetime.html)
- [Postgres docs — Numeric types](https://www.postgresql.org/docs/current/datatype-numeric.html) — the exact precision/scale rules for `numeric`
- [Postgres docs — Date/Time types](https://www.postgresql.org/docs/current/datatype-datetime.html) — `timestamp` vs `timestamptz`, from the source
- [Floating-point guide — why 0.1 + 0.2 ≠ 0.3](https://floating-point-gui.de/) — the arithmetic behind "never float for money"
- [Django docs — DecimalField](https://docs.djangoproject.com/en/5.0/ref/models/fields/#decimalfield) — how this project declares money
- Sibling chapter: [12 — Append-Only Money](12_Append_Only_Money.md) — the right type is necessary but nowhere near sufficient
