---
id: sql-course-25-interview-master-sheet
type: lesson
status: active
owner: handwritten
scope: sql, postgresql — database fundamentals taught from this ERP
anchors: config/expense/services/settlement_service.py, config/production/services/pool_service.py
verified: 2026-08-01
---

# 25 — Interview Master Sheet

> Part of [SQL From Zero](00_COURSE_OVERVIEW.md). Prev: [24](24_Scaling_And_Limitations.md) · Back to: [Course Overview](00_COURSE_OVERVIEW.md).

# Learning Objectives
By the end of this chapter you can:
- answer the 12 most-asked database questions without notes
- avoid the traps that catch confident candidates
- cite a real number from your own system for every major topic
- deliver two set-piece answers (payroll storage · slow page) under 90 seconds

# Purpose
The whole course, compressed into what an interviewer will actually ask — plus the
thing most candidates lack: **a real system to answer from.** I do not have to
invent examples. I have 28 Addas, 201 ledger rows and a ₹18,254.25 total I can
explain to the paisa.

# The Problem
Two failure modes in database interviews. **One:** knowing syntax but no *why*
("I'd add an index" — to what, and how do you know?). **Two:** knowing theory but
having never run it, so every answer stays abstract. This sheet fixes both by
pairing each answer with a fact from my own factory.

# Theory (from zero)

### The 12 questions asked most often — with my answers

```
   ╔════════════════════════════════════════════════════════════════════╗
   ║  #  QUESTION                    MY ONE-LINE ANSWER          CH     ║
   ╠════════════════════════════════════════════════════════════════════╣
   ║  1  Explain ACID                Atomic/Consistent/Isolated/  17     ║
   ║                                 Durable — settlement finalize      ║
   ║  2  INNER vs LEFT JOIN          matches only vs keep-all-left 07    ║
   ║  3  WHERE vs HAVING             rows before / groups after    08    ║
   ║  4  What is the N+1 problem     1 + one-per-row; eager load   16    ║
   ║  5  Why never float for money   binary can't hold decimals    03    ║
   ║  6  What is an index + cost     sorted signpost; slows writes 14    ║
   ║  7  What is NULL / test it      unknown; IS NULL              04    ║
   ║  8  Primary vs foreign key      identity vs pointer+rule      02/13 ║
   ║  9  Prevent SQL injection       parameterise, never concat    22    ║
   ║ 10  What is a deadlock          mutual wait; consistent order 18    ║
   ║ 11  SQL vs NoSQL                guarantees vs horizontal scale 24   ║
   ║ 12  Query order of execution    FROM→WHERE→GROUP→HAVING→      05    ║
   ║                                 SELECT→ORDER→LIMIT                  ║
   ╚════════════════════════════════════════════════════════════════════╝
```

### The traps — where confident candidates fail

| Trap | The correct answer |
|---|---|
| `WHERE col != 'x'` misses NULL rows | `NULL != 'x'` is NULL; WHERE keeps only **true** (ch 04) |
| Can WHERE use a SELECT alias? | **No** — WHERE runs first. ORDER BY can (ch 05) |
| `NOT IN` returns nothing | one NULL in the list poisons it; use `NOT EXISTS` (ch 09) |
| Composite index `(a,b)` for `WHERE b=?` | **No** — phonebook sorted by surname (ch 14) |
| Indexed column still slow | leading `%`, `func(col)`, tiny table, stale stats (ch 06/14/15) |
| Seq Scan means broken index | often the **right** plan — mine costs 1.31 vs 8.15 (ch 14) |
| `count(*)` vs `count(col)` | rows vs non-NULL values (ch 04/08) |
| Do readers block writers in PG? | **No — MVCC.** Say the word (ch 18) |
| Adding a JOIN changed my `sum()` | row multiplication → double count (ch 07/08) |
| Window function in `WHERE` | impossible; wrap in a CTE (ch 10) |
| A backup you've never restored | not a backup — a hope (ch 20) |
| Money in JSONB | JSON numbers are floats; all guarantees lost (ch 23) |

> 💡 **Samjho aise:** Interview mein do tarah ke log aate hain. Ek: *"index laga
> denge"* — par kaun-sa, kis column pe, kaise pata chala? Doosra: theory ratta,
> par kabhi chala ke nahi dekha. **Teesra banna hai** — jiske paas apna chalta
> hua system hai. Jab pooche *"paise ka hisaab kaise sambhalte ho?"*, tumhare paas
> jawaab hai: append-only register, numeric column, ek settlement gate, 5374 ka
> lock, aur ₹18,254.25 jo paai-paai saabit hota hai. **Wahi teesra aadmi hire hota hai.**

# Real World Example (My ERP)
### My story bank — one memorised fact per topic

```
   TOPIC                 MY REAL EVIDENCE (say the numbers — they land)
   ─────────────────────────────────────────────────────────────────────
   exact money           ledger 201 rows → ₹18,254.25, numeric(12,2),
                         audit variance ₹0
   append-only           corrections are REVERSING entries, never edits;
                         ledger_service is the SOLE writer
   atomicity             settlement finalize = one @transaction.atomic:
                         status + earning lines + ledger, or nothing
   a REAL atomicity bug  P19A C-1: a helper slipped between the decorator
                         and the def → TransactionManagementError + partial
                         commits; pinned with TransactionTestCase (a plain
                         TestCase would have HIDDEN it)
   concurrency           advisory lock 5374 (settlement) / 5375 (allocation);
                         row lock + RE-CHECK ⇒ second manager refuses
   constraints           137 CHECKs + 271 FKs; wsc_expected_earning_nonneg
                         says "NULL or >= 0" — unknown allowed, negative never
   honest NULL           cloth cost_per_kg is NULL when unpriced, not ₹0;
                         reports say "unpriced" instead of lying
   planner intelligence  Seq Scan chosen at cost 1.31 over index at 8.15 on
                         28 rows; the SAME query uses the index on 611 rows
   N+1                   measured: 29 queries → 1 with select_related
   schema history        188 migrations rebuild 115 tables on an empty DB
   backups               local pg_dump .sql vs production pg_dump -Fc + restic
                         (DB **and** media), RPO 24h, keep 7/4/6
   the restore bug       psql without ON_ERROR_STOP exits 0 on a PARTIAL
                         restore → a "green tick" over a broken copy
   scale honesty         26 MB, biggest table 611 rows — ~6 orders of
                         magnitude from any Postgres limit
   architecture policy   ADR-0010: multi-factory = one DB + site dimension,
                         NEVER a fork, because two DBs = no shared atomicity
   ─────────────────────────────────────────────────────────────────────
```

### The two set-piece answers worth rehearsing

**"Design a payroll system's storage."**
> Immutable append-only entries, `numeric(12,2)` amounts. Rates frozen onto the
> work at the moment it happens, so later config changes never rewrite history.
> **One** settlement gate that creates money — atomic, row-locked, advisory-locked,
> audited — with everything before it freely editable and everything after it
> append-only. Corrections are reversals carrying a reason and an author. Totals
> proven by independent reconciliation, and pinned in tests as exact rupee values.
> One writer service per money table. *That is my system, and I can show it.*

**"A page is slow. Walk me through it."**
> **Count the queries first** — most "slow page" reports are N+1, not a slow query,
> and no amount of EXPLAIN will find that. If the count is sane, `EXPLAIN ANALYZE`
> the worst one and compare **estimated vs actual rows**: a bad estimate means bad
> statistics or a bad join order. Then check whether the index is doing the work
> (`Index Cond`) or being wasted (`Filter` + `Rows Removed by Filter`). Only then
> consider adding an index — and verify it's actually used afterwards. **Measure,
> fix, re-measure.**

# Visual Diagram
```
   THE COURSE AS ONE PICTURE — every chapter in its place
   ══════════════════════════════════════════════════════════════════════
                    ┌──────── WHAT I ASK ─────────┐
     SELECT (05) ─▶ WHERE (06) ─▶ JOIN (07) ─▶ GROUP BY (08)
          └─▶ subqueries/CTE (09) ─▶ window functions (10)
                    └──────────┬──────────────────┘
                               ▼
                    ┌──── WHAT IT SITS IN ────────┐
      tables/keys (02) · types+money (03) · NULL (04) · JSONB (23)
                               ▼
                    ┌──── WHAT PROTECTS IT ───────┐
      constraints (13) · transactions (17) · locks/MVCC (18)
      append-only money (12) · security (22)
                               ▼
                    ┌──── HOW FAST IT RUNS ───────┐
      indexes (14) · EXPLAIN/planner (15) · ORM & N+1 (16)
                               ▼
                    ┌──── HOW I OPERATE IT ───────┐
      migrations (19) · backups (20) · databases/branching (21)
                               ▼
                    ┌──── WHERE IT ENDS ──────────┐
                      limitations & scaling (24)
   ══════════════════════════════════════════════════════════════════════
   If you can redraw this from memory, you know the course.
```

# Practical — try it yourself
A 10-minute self-test. Answer out loud **first**, then run the query to check.

```sql
-- 1. (ch 08) What is my ledger total, and how many rows?          → 201 / 18254.25
SELECT count(*), sum(amount) FROM expense_workerledgerentry;

-- 2. (ch 07) Which products have never been used? Why does INNER JOIN hide them?
SELECT p.code FROM production_product p
WHERE NOT EXISTS (SELECT 1 FROM production_adda a WHERE a.product_id = p.id);

-- 3. (ch 14/15) Predict the plan BEFORE running it. Seq Scan or Index Scan? Why?
EXPLAIN SELECT * FROM production_adda WHERE code = '3-PATTI-018';

-- 4. (ch 04) Predict both numbers, then run:
SELECT count(*), count(completed_at) FROM production_adda;

-- 5. (ch 13) Name three CHECK constraints protecting my money — from memory:
SELECT conname FROM pg_constraint
WHERE conrelid='production_workerstagecontribution'::regclass AND contype='c';

-- 6. (ch 10) Produce a running balance for one worker. Does the last row match #1's
--    per-worker total from chapter 08?
SELECT l.id, l.amount, sum(l.amount) OVER (ORDER BY l.id) AS running
FROM expense_workerledgerentry l JOIN accounts_user u ON u.id=l.worker_id
WHERE u.email='a2.cm1@audit.local' ORDER BY l.id;
```
```bash
# 7. (ch 16) Measure N+1 on my own data — the number you can quote in an interview
env/bin/python config/manage.py shell --settings=config.settings.local -c "
from django.test.utils import CaptureQueriesContext
from django.db import connection
from production.models import Adda
with CaptureQueriesContext(connection) as a:
    [x.product.name for x in Adda.objects.all()]
with CaptureQueriesContext(connection) as b:
    [x.product.name for x in Adda.objects.select_related('product')]
print('without:', len(a), ' with select_related:', len(b))"
```

# Production Walkthrough
What makes this sheet different from a question dump: **every answer has a receipt.**
- Say "exact money" → cite ledger 201 rows / ₹18,254.25 / variance ₹0.
- Say "atomicity" → cite the P19A C-1 lost-decorator bug and the `TransactionTestCase` that pins it.
- Say "the planner is smart" → cite Seq Scan at 1.31 beating Index at 8.15 on 28 rows.
- Say "N+1" → cite the measured 29 → 1 collapse with `select_related`.
Candidates who quote a system they built are believed. Candidates who quote a blog are tested harder.

# Debugging Guide
When an interview question is going badly:
1. **Say what you would measure.** "I'd count the queries first" is a stronger answer than a wrong guess.
2. **Ask a clarifying question** — scale? read/write mix? consistency requirement? Jumping to an answer *is* the failure in design rounds.
3. **Name the trade-off** explicitly; senior answers are always shaped "X buys us A and costs us B".
4. **"I haven't used that, here is how I'd decide"** scores higher than a bluff, every time.
5. **Come back to a real system.** Anchor abstractions in the factory you actually built.

# Performance Notes
- Preparation has diminishing returns per topic and increasing returns on the **method**: measure → hypothesise → fix → re-measure. Interviewers probe method because it generalises.
- Rehearse *out loud*, timed. A 90-second answer you can deliver beats a five-minute one you cannot.
- The two set-pieces (payroll storage, slow page) cover a surprising fraction of backend rounds.

# Security Considerations
- Expect at least one security question. Have three ready: parameterisation (ch 22), least-privilege roles, and what a leaked dump exposes (all your data **plus** password hashes).
- Never describe a real employer's vulnerability in an interview. Talk about the *class* of issue and the fix — which is exactly how this course frames its own findings.

# Architecture Decisions
- **Depth over breadth.** Knowing one production system completely beats naming ten technologies.
- **Own your weaknesses.** "Production still connects as a superuser locally; that is owed work" is a *strong* answer — it shows you audit yourself.
- **Bring the ADR habit.** Saying "we wrote down the decision and its reason" signals seniority faster than any framework name.

# Best Practices
- Keep the story bank to one memorised fact per topic; more than that and none will surface under pressure.
- Practise the traps table until the wrong answers feel wrong.
- Redraw the course map from memory monthly — gaps are your revision list.
- Say the numbers. Numbers are what make an answer sound lived rather than read.

# Beginner Mistakes
- Answering "how would you optimise this?" with a solution instead of a **method**
  (measure → hypothesise → fix → re-measure).
- Claiming to know a technology you have only read about. Say *"I haven't used
  sharding; here is how I'd approach deciding whether we need it"* — that answer
  scores higher than a bluff, every time.
- Reciting ACID without an example. The example is what makes it believable.
- Not asking clarifying questions in a design round (scale? consistency needs?
  read/write mix?). Jumping to an answer is the actual failure.
- Forgetting that "I don't know, but I know how I'd find out" is a **complete**
  senior answer.

# Interview Questions
*(This entire chapter is that section — so here are the four hardest, with the
shape of a strong answer.)*

- **Junior:** *Why did you choose PostgreSQL for this project?* — transactions and
  constraints for money, exact `numeric` arithmetic, mature tooling, and one
  machine is ~6 orders of magnitude more than my factory needs. Also: I know how to
  back it up and restore it, which is part of choosing a database.
- **Mid:** *Walk me through your database schema.* — start with the business:
  a Product has a workflow of Stages; an Adda is a batch of a Product moving
  through those stages; workers report contributions per stage; settlement turns
  expected earnings into ledger entries. 115 tables, but the story is five nouns.
  **Always lead with the domain, never with table names.**
- **Senior:** *Where is your system weakest?* — media lives outside the database so
  a DB dump is not a full backup; production still connects as a superuser role
  locally; a fresh database needs a documented human checklist before it can run.
  *(Naming real weaknesses with the mitigations already written down is the answer
  that builds trust.)*
- **Staff:** *You inherit this system and the owner wants a second factory.* — one
  database with a `site` dimension, never a second deployment: two databases share
  no transaction, so the ledger would split into two unreconcilable sets of books.
  References stay globally unique so a future consolidation is a filter, not a
  renumbering. Then I'd scope the migration additively and gate it behind the
  existing settlement invariants.

### Why interviewers ask these — and the answer that separates levels

| Testing for | Weak answer | What lands |
|---|---|---|
| Can you justify your database choice as an **engineer**? | "Postgres is the best open-source database." | Transactions and constraints **for money**, exact `numeric`, mature tooling — and one machine is orders of magnitude more than one factory needs. Then the line that wins it: **"I also know how to back it up and restore it, which is part of choosing a database."** |
| Can you present a schema without listing tables? | "There are 115 tables — let me walk through them." | **Lead with the domain, never table names.** Five nouns: a Product has a workflow of Stages · an Adda is a batch moving through them · workers report contributions per stage · **settlement** turns expected earnings into ledger entries. 115 tables, one story. |
| Can you name your own weakest point? | "I think it is pretty solid." | Name real ones: **media lives outside the database, so a DB dump is not a full backup** · a fresh database needs a documented human checklist before it can run a batch · enforcement flags still default off pending soak. Volunteering the weakness is what buys credibility for everything else you claimed. |
| Do you know the one thing they will probe hardest? | "They will ask about joins and indexes." | On a money system they probe **how you correct a mistake**. "Update the row" fails the interview; **"post a reversing entry, original untouched, reason and author mandatory"** passes it (ch 12). |

**The killer follow-up:** *"What would you do differently if you started again?"* — the trap is answering "nothing". A real answer from this project: **decide the local-vs-UTC date primitive on day one** — a `timezone.now().date()` habit put a UTC date on money records in 10 places, and it was only caught by a cross-check test on a month boundary.

# Revision Notes
- 12 core questions · 12 traps · one real number per topic.
- Juniors name tools; seniors name **responsibilities, trade-offs and failure modes**.
- Method beats trivia: measure → hypothesise → fix → re-measure.
- "I don't know, but here's how I'd find out" is a complete senior answer.
- Your edge is a **real production system** — use it in every answer.

# Cheat Sheet
- money → `numeric`, append-only, one writer, one atomic gate
- reads → SELECT/JOIN/GROUP BY; advanced → CTE + window functions
- correctness → constraints + transactions + locks (and re-check inside the lock)
- speed → count queries first (N+1), then EXPLAIN, then index; measure both ends
- operations → migrations rebuild schema · backups need a **tested restore**
- honesty → know the limits: files, cross-DB atomicity, search, extreme analytics
- **always answer with a real number from your own system**

# My ERP Section
| For this question… | Cite this |
|---|---|
| ACID / atomicity | settlement finalize + the P19A C-1 partial-commit bug |
| Concurrency | advisory 5374/5375, `select_for_update` + re-check |
| Exact money | 201 rows → ₹18,254.25, `numeric(12,2)`, variance ₹0 |
| Constraints | 137 CHECKs / 271 FKs, `wsc_expected_earning_nonneg` |
| Index/planner nuance | 1.31 (seq) vs 8.15 (index) on 28 rows |
| N+1 | 29 queries → 1 with `select_related` |
| Ops maturity | 188 migrations · restic (DB+media) · RPO 24h · tested restores |
| Architecture judgement | ADR-0010 one-database rule |

# Practice Tasks
1. **Read the code:** pick any three topics from the story bank and locate the code or doc that proves each. If you cannot find it, you cannot claim it.
2. **Debug:** do the 10-minute self-test answering out loud *before* running each query. Score yourself; every miss is a chapter to re-read.
3. **Design:** deliver "design a payroll system's storage" from memory, timed, under 90 seconds. Record it once and listen back.
4. **Architecture:** write your honest three-item weakness list for this system, each with the mitigation you would propose. That list is an interview asset, not a liability.

# Homework
1. Do the 10-minute self-test **answering out loud before each query**. Score yourself honestly; re-read any chapter you missed.
2. Rehearse the two set-piece answers ("design a payroll store", "a page is slow") until each runs under 90 seconds without notes.
3. Redraw the Visual Diagram above from memory on paper. Every gap is a chapter to revisit.

# Further Reading & Live Resources
- [PgExercises](https://pgexercises.com/) — finish every section; the single best free practice
- [SQLBolt](https://sqlbolt.com/) — for any basics that still feel shaky
- [Use The Index, Luke](https://use-the-index-luke.com/) — free book; makes you the indexes person on any team
- [Postgres official tutorial](https://www.postgresql.org/docs/current/tutorial.html)
- [CMU Intro to Database Systems (free full course)](https://www.youtube.com/playlist?list=PLSE8ODhjZXjbj8BMuIrRcacnQh20hmY9g) — when you want to know how the engine is built
- [Designing Data-Intensive Applications](https://dataintensive.net/) — the book for the Staff-level questions (paid, worth it)
