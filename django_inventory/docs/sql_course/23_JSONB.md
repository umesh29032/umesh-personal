---
id: sql-course-23-jsonb
type: lesson
status: active
owner: handwritten
scope: sql, postgresql — database fundamentals taught from this ERP
anchors: config/expense/services/settlement_service.py, config/production/services/pool_service.py
verified: 2026-08-01
---

# 23 — JSONB: Escaping the Fixed Schema (Carefully)

> Part of [SQL From Zero](00_COURSE_OVERVIEW.md). Prev: [22](22_Security_And_SQL_Injection.md) · Next: [24 — Scaling & Limitations](24_Scaling_And_Limitations.md).

# Learning Objectives
By the end of this chapter you can:
- choose `jsonb` over `json`, and say why
- use `->`, `->>`, `#>`, `@>` and `?` for the right job
- list exactly what you give up by using JSONB
- defend the boundary between a typed column and a blob

# Purpose
To learn Postgres's pressure valve for data that refuses to hold a fixed shape —
and to be very clear about what you **give up** the moment you use it. My own
project uses 25 JSONB columns, all in one app, and that concentration is the lesson.

# The Problem
Chapter 03 said types are promises and chapter 13 said constraints are walls. Both
assume I know the shape in advance. But some data genuinely doesn't have one:
- a pattern-AI run's `verification` blob differs per engine and per version
- a geometry `result` has nested structures that change as the algorithm evolves
- an audit `evidence` payload should record *whatever was relevant* that day

Adding a column per possible key would mean a migration per experiment and a table
of mostly-NULL columns. That is the wrong shape for genuinely variable data.

# Theory (from zero)

**JSON in a column.** Postgres has two types:

| Type | Stores | Verdict |
|---|---|---|
| `json` | the raw text, re-parsed on every read | almost never what you want |
| **`jsonb`** | a decomposed **binary** form: parsed once, indexable | **use this** |

`jsonb` normalises on write (key order not preserved, duplicates removed) and can
be queried and indexed. All 25 of my columns are `jsonb`.

**The operators** — the four you actually need:

```
   ┌──────────┬─────────────────────────────────┬───────────────────────┐
   │  ->      │ get value AS JSON               │ data -> 'x'   → {…}   │
   │  ->>     │ get value AS TEXT               │ data ->> 'x'  → "5"   │
   │  #>      │ get by PATH as JSON             │ data #> '{a,b}'       │
   │  #>>     │ get by PATH as TEXT             │ data #>> '{a,b}'      │
   ├──────────┼─────────────────────────────────┼───────────────────────┤
   │  @>      │ CONTAINS (the indexable one!)   │ data @> '{"ok":true}' │
   │  ?       │ has this key?                   │ data ? 'engine'       │
   └──────────┴─────────────────────────────────┴───────────────────────┘
   Memory hook:  ONE arrow  → JSON out  ·  TWO arrows ->> TEXT out
                 (two arrows = "flattened to text")
```

**Chaining for nested data:**
```sql
SELECT '{"x": {"y": 5}}'::jsonb -> 'x' ->> 'y';    -- '5'  (REAL: returns 5)
--                                 │       └── last hop as TEXT
--                                 └── intermediate hops as JSON
```

### What you give up — the honest ledger

```
   FIXED COLUMN                        JSONB BLOB
   ═══════════════════════════         ═══════════════════════════════
   ✅ type enforced (ch 03)             ❌ any shape, any type, anytime
   ✅ NOT NULL / CHECK (ch 13)          ❌ no per-key constraints
   ✅ FK to other tables                ❌ no FK inside JSON
   ✅ planner statistics accurate       ❌ estimates are guesses
   ✅ index by default (PK/FK)          ⚠️ needs an explicit GIN index
   ✅ a typo is a migration error       ❌ a typo is a silently missing key
   ═══════════════════════════════════════════════════════════════════
   ⇒ Rule of thumb: if you will FILTER, JOIN, SUM or CONSTRAIN it,
     it deserves a real column. JSONB is for the rest.
```

**Indexing JSONB:** a B-tree (ch 14) is useless for "does this blob contain that
key". You need **GIN**:
```sql
CREATE INDEX ... USING GIN (data);              -- supports @>, ?, ?&
CREATE INDEX ... USING GIN (data jsonb_path_ops); -- smaller, @> only
```
My database currently has **772 indexes and every one is B-tree** — meaning none of
my JSONB columns is indexed. That is correct *today* (they are read by primary key,
not searched), and it is exactly the thing to revisit if I ever filter on them.

> 💡 **Samjho aise:** Normal column ek **chhapa hua form** hai — khaane fix, sharth
> fix, galat cheez ghusti hi nahi. JSONB ek **khaali lifafa** hai jisme jo chaaho
> daal do. Lifafa bahut aaram deta hai — par usme daali cheez pe **koi pehra nahi**:
> na type check, na "khaali nahi ho sakta", na doosre register se rishta. Isi liye
> **jis cheez pe hisaab lagana hai, uska apna khaana banao**; lifafa un cheezon ke
> liye hai jinka shape hi tay nahi.

# Real World Example (My ERP)
**25 jsonb columns — and 100% of them are in `patterns_ai`:**

```
   patterns_ai_geometryextraction        5   result, params, …
   patterns_ai_markergenerationrun       2
   patterns_ai_calibrationmat            2   board_spec, control_distances
   patterns_ai_generatedmarkercandidate  2   placements, verification
   patterns_ai_manufacturingstrategy     2
   patterns_ai_piecesizegeometry         2
   … plus captureasset.metadata, evidenceitem.params, calibrationmatcheck.evidence
   ─────────────────────────────────────────────────────────────────────
   patterns_ai (experimental AI/geometry) ─▶ 25 jsonb columns
   production · expense · accounts · tracking (the FACTORY + MONEY) ─▶ 0
```

**That distribution is the whole chapter.** The AI/geometry app deals with outputs
whose shape changes as algorithms evolve — a perfect JSONB fit. The money and
production tables use **strict typed columns with 137 CHECK constraints** (ch 13),
because a wage must never be "whatever shape the caller sent".

If wages had been stored as `{"amount": 500}` in a JSONB blob, then:
- `numeric` exactness (ch 03) — **gone** (JSON numbers are doubles!)
- `wsc_expected_earning_nonneg` — **impossible**
- `sum(amount)` — a string-parsing exercise with no index
- my audit's ₹18,254.25 proof — **unprovable**

**JSON numbers deserve their own warning.** In JSON, `0.1` is a floating-point
double — which is precisely the float lie of chapter 03. **Never put money in
JSONB.** My project never does.

# Visual Diagram
```
   WHERE JSONB BELONGS IN MY ARCHITECTURE
   ══════════════════════════════════════════════════════════════════════
   STRICT ZONE  (typed columns, constraints, FKs)     │  FLEXIBLE ZONE
   ─────────────────────────────────────────────────  │  ──────────────────
   expense_workerledgerentry   amount numeric(12,2)   │  patterns_ai.*
   production_workerstage…     good/alter/missing     │    result   jsonb
   production_adda             code varchar UNIQUE    │    params   jsonb
   137 CHECKs · 271 FKs · money provable to the paisa │    evidence jsonb
                                                       │  shape changes per run
   ══════════════════════════════════════════════════════════════════════
              ▲                                              ▲
       things you SUM, FILTER, JOIN,               things you STORE and
       and must never get wrong                    read back whole
   ══════════════════════════════════════════════════════════════════════
   The boundary is deliberate. Drifting money into the right-hand column
   is how an auditable system quietly stops being auditable.
```

# Practical — try it yourself
```sql
-- 1. how much JSONB do I have, and where? (REAL: 25 columns, all patterns_ai)
SELECT table_name, count(*) FROM information_schema.columns
WHERE data_type = 'jsonb' AND table_schema = 'public'
GROUP BY table_name ORDER BY 2 DESC LIMIT 6;

-- 2. build and read JSON — no table needed, totally safe (REAL outputs)
SELECT jsonb_build_object('a', 1, 'b', 'two');        -- {"a": 1, "b": "two"}
SELECT '{"x": {"y": 5}}'::jsonb -> 'x' ->> 'y';       -- 5

-- 3. ONE arrow vs TWO arrows — the distinction that trips everyone
SELECT '{"n": 5}'::jsonb -> 'n'  AS as_json,          -- 5    (jsonb)
       '{"n": 5}'::jsonb ->> 'n' AS as_text,          -- 5    (text)
       pg_typeof('{"n": 5}'::jsonb -> 'n')  AS t1,    -- jsonb
       pg_typeof('{"n": 5}'::jsonb ->> 'n') AS t2;    -- text
--    ^ the VALUES look identical; the TYPES are not. Comparisons care.

-- 4. containment and key tests (the indexable patterns)
SELECT '{"engine":"blf","ok":true}'::jsonb @> '{"ok":true}'  AS contains;  -- t
SELECT '{"engine":"blf"}'::jsonb ? 'engine'                  AS has_key;   -- t

-- 5. the float trap, proven — why money never goes in JSON
SELECT ('{"amt": 0.1}'::jsonb ->> 'amt')::float
     + ('{"amt": 0.2}'::jsonb ->> 'amt')::float AS json_float_path,
       0.1::numeric + 0.2::numeric              AS numeric_path;
--   0.30000000000000004   |   0.3      ← ch 03's lie, re-entering through JSON

-- 6. look at real data in my project (patterns_ai rows may be sparse in dev)
SELECT id, params FROM patterns_ai_evidenceitem LIMIT 3;

-- 7. why my JSONB has no index yet (REAL: 772 indexes, all btree)
SELECT am.amname, count(*) FROM pg_class i JOIN pg_am am ON am.oid = i.relam
WHERE i.relkind = 'i' GROUP BY am.amname;
```

# Production Walkthrough
The 25-vs-0 split is the whole lesson:
- **`patterns_ai` holds all 25 JSONB columns** — geometry results, marker placements, verification evidence. Their shape changes as the algorithms evolve, so a column per key would mean a migration per experiment.
- **Money and production tables hold zero.** They use typed columns plus 137 CHECK constraints, because a wage must never be "whatever shape the caller sent".
- **No GIN index exists yet** — correct today, because nothing *filters* on those blobs; they are fetched by primary key. The moment a query filters on JSON content, that changes (see Performance Notes).

# Debugging Guide
"The JSON value is missing / comparison fails":
1. **A misspelled key returns NULL, not an error.** Print the whole blob first (`SELECT data FROM …`) before trusting a path.
2. **Check `->` vs `->>`.** Comparing `jsonb` to `text` behaves differently from comparing text to text; `pg_typeof()` settles it in one query.
3. **Validate the shape.** A key that is sometimes an object and sometimes an array will break code that assumes one — this is the cost of no schema.
4. **For containment, use `@>`**, not string matching on the serialised form.
5. **If it is slow**, check whether a GIN index exists at all — B-tree cannot help.

# Performance Notes
- `jsonb` is parsed on write, so reads are fast and indexable; `json` re-parses every read.
- **B-tree indexes do not help JSONB lookups** — use **GIN** (`USING GIN (data)`), or `jsonb_path_ops` for containment-only (smaller).
- Large blobs go to **TOAST** storage and are fetched separately; a wide JSONB column can make otherwise-cheap row reads expensive.
- Planner statistics on JSONB are poor — the planner cannot know how many rows contain a key, so estimates (and therefore plans) are weaker than on typed columns.

# Security Considerations
- JSONB is a schemaless input surface: whatever the caller sends is stored. Validate at the application edge, because the database will not.
- Deeply nested or enormous documents are a resource-exhaustion vector; cap size at the edge.
- Do not put secrets in JSONB thinking it is opaque — it is fully readable and appears in every backup (ch 20).
- **Never money in JSONB**: JSON numbers are IEEE doubles, so ch 03's float lie re-enters through the back door.

# Architecture Decisions
- **JSONB quarantined to one experimental app.** The boundary is deliberate and visible in the schema — anyone can audit it with one query.
- **If you filter, join, sum or constrain it, it earns a real column.** That rule is what keeps the blob from spreading.
- **Generated/extracted columns** are the escape hatch when one JSON key becomes hot: pull it into a typed, indexable, constrainable column.

# Best Practices
- Always `jsonb`, never `json`.
- Document the expected shape in the model docstring — the database cannot.
- Add a CHECK on required keys (`CHECK (data ? 'version')`) when partial structure matters.
- Revisit JSONB columns yearly: any key you now filter on should have been promoted.

# Beginner Mistakes
- **Putting money or quantities in JSONB.** No `numeric` exactness, no CHECK, no
  index — every guarantee in this course, discarded at once.
- Using `->` where `->>` was meant: comparing `jsonb` to `text` fails or silently
  behaves oddly. One arrow = JSON, two = text.
- Expecting a B-tree index to help JSONB lookups. You need **GIN**.
- Treating JSONB as a way to avoid designing a schema. Six months later, four
  spellings of the same key exist and nothing can be validated.
- Forgetting that a misspelled key returns **NULL** rather than an error — a typo
  becomes silent data loss (ch 04's trap, with no compiler to help).
- Using `json` instead of `jsonb`.
- Storing huge blobs and wondering why rows got slow (large values go to TOAST
  storage and are fetched separately).

# Interview Questions
- **Junior:** *`json` vs `jsonb`?* — text-as-stored vs parsed binary; jsonb is indexable and canonicalised, and is the default choice.
- **Junior:** *`->` vs `->>`?* — returns JSON vs returns text. **Very commonly asked.**
- **Mid:** *How do you index a JSONB column?* — a GIN index, supporting `@>`, `?`, `?&`; `jsonb_path_ops` is a smaller variant for containment only.
- **Mid:** *When would you choose JSONB over columns?* — genuinely variable/sparse structures, third-party payloads, evolving experiment output; never for anything you filter, join, aggregate or must constrain.
- **Senior:** *What do you lose with JSONB?* — type enforcement, per-key constraints, foreign keys, reliable planner statistics, and default indexing; plus you gain silent-typo failures.
- **Senior:** *How do you enforce partial structure in a JSONB column?* — a CHECK constraint on extracted keys (e.g. `CHECK ((data ? 'version'))` or a type assertion on `data ->> 'k'`), or a generated column extracting the hot key into a real typed column that can then be indexed and constrained.
- **Staff:** *Design review: a teammate proposes storing settlement line items as JSONB. Your response?* — refuse for the money fields: you lose `numeric` exactness (JSON numbers are doubles), you cannot express the non-negative CHECKs, `sum()` becomes unindexed string parsing, and the append-only audit story (ch 12) collapses. JSONB is acceptable for *ancillary* metadata alongside typed money columns. **This project's 25-vs-0 split is exactly that argument, already made.**

### Why interviewers ask these — and the answer that separates levels

| Testing for | Weak answer | What lands |
|---|---|---|
| `->` vs `->>` — the fastest tell in the chapter. | "They both get the key." | `->` returns **JSON**, `->>` returns **text**. Very commonly asked because chaining the wrong one is the most frequent JSONB bug — and comparing JSON to a string silently fails to match. |
| Do you know how to index JSONB? | "Add a B-tree index on the column." | A **GIN** index, supporting `@>`, `?`, `?&` — with **`jsonb_path_ops`** as a smaller containment-only variant. A plain B-tree on a jsonb column indexes the whole document, which is almost never what you want. |
| Can you say what JSONB **costs**? | "It is flexible, so it is good for evolving data." | You lose **type enforcement, per-key constraints, foreign keys, reliable planner statistics and default indexing** — and you gain **silent typo failures**, because a misspelled key is simply absent rather than an error. |
| Can you enforce structure inside JSONB? | "You cannot constrain JSON." | You can, partially: a **CHECK on extracted keys** (`CHECK (data ? 'version')`, or a type assertion on `data ->> 'k'`), or a **generated column** pulling the hot key into a real typed column that can then be indexed *and* constrained. |

**The killer follow-up:** *"A teammate proposes storing settlement line items as JSONB. Your response?"* — **refuse for the money fields**: JSON numbers are **doubles**, so you lose `numeric` exactness; the non-negative CHECKs become inexpressible; `sum()` turns into unindexed string parsing; and the append-only audit story (ch 12) collapses. JSONB is fine for *ancillary metadata beside* typed money columns — which is exactly this project's 25-jsonb-columns-and-none-in-money split.

# Revision Notes
- Use **`jsonb`** (parsed, indexable), never `json`.
- One arrow `->` returns JSON; two `->>` returns text.
- `@>` contains · `?` has-key · `#>`/`#>>` by path.
- Index with **GIN**; B-tree is useless here.
- You lose types, CHECKs, FKs, good statistics — and **never put money in it**.

# Cheat Sheet
- use **`jsonb`**, never `json` · one arrow `->` = JSON, two `->>` = text
- `#>` / `#>>` for paths · `@>` contains · `?` has-key
- index with **GIN** (B-tree won't help)
- lose: types, CHECKs, FKs, good statistics, typo detection
- **never money in JSONB** — JSON numbers are floats (ch 03)
- filter/join/sum/constrain it? ⇒ it deserves a real column
- my split: patterns_ai = 25 jsonb columns · money & production = 0

# My ERP Section
| Fact | Value |
|---|---|
| JSONB columns | **25**, all in `patterns_ai` |
| Biggest user | `patterns_ai_geometryextraction` (5 columns) |
| Money/production tables | **zero** JSONB — typed columns + 137 CHECKs instead |
| Index status | 772 indexes, **all B-tree** → no GIN yet (correct while nothing filters on JSON) |
| Why the split | evolving AI output vs provable factory money |

# Practice Tasks
1. **Read the code:** open `config/patterns_ai/models/geometry.py` and find a JSONB field. Does a docstring describe its expected shape? If not, that is the cost of no schema.
2. **Debug:** run the JSON-float demo from Practical #5. Write down both numbers and the rule you take from it.
3. **Design:** the owner wants to search pattern runs by engine name. Write the query, then design the index it needs — and argue whether that key should become a real column instead.
4. **Architecture:** a teammate proposes storing settlement line items as JSONB. Write your three-sentence refusal, citing exactness, constraints and auditability.

# Homework
1. Run Practical #1. Confirm every JSONB column lives in `patterns_ai`, then write one sentence on why the money tables have none.
2. Run Practical #3 with `pg_typeof`. Explain the difference between `->` and `->>` in your own words.
3. Run Practical #5 (the JSON float trap). Then state the rule you will never break.

# Further Reading & Live Resources
- [Postgres JSON types](https://www.postgresql.org/docs/current/datatype-json.html)
- [Postgres JSON functions & operators](https://www.postgresql.org/docs/current/functions-json.html)
- [Postgres GIN indexes](https://www.postgresql.org/docs/current/gin-intro.html)
- [Django JSONField](https://docs.djangoproject.com/en/5.0/topics/db/queries/#querying-jsonfield)
