---
id: sql-course-16-orm-to-sql-and-n-plus-1
type: lesson
status: active
owner: handwritten
scope: sql, postgresql — database fundamentals taught from this ERP
anchors: config/expense/services/settlement_service.py, config/production/services/pool_service.py
verified: 2026-08-01
---

# 16 — From ORM to SQL, and the N+1 Problem

> Part of [SQL From Zero](00_COURSE_OVERVIEW.md). Prev: [15](15_EXPLAIN_And_The_Planner.md) · Next: [17 — Transactions & ACID](17_Transactions_And_ACID.md).

# Learning Objectives
By the end of this chapter you can:
- translate common ORM calls into the SQL they generate
- recognise an N+1 in code *before* running it
- choose `select_related` vs `prefetch_related` correctly
- measure query counts, and use that number to diagnose a slow page

# Purpose
To connect the two halves of my own project: the Python I write and the SQL that
actually runs. Then to meet **N+1**, the performance bug that every ORM makes
easy to write by accident — and the one interviewers ask about most.

# The Problem
I have never typed `SELECT * FROM production_adda`. I write
`Adda.objects.filter(status='completed')`. Django translates. That is a gift —
until something is slow, and I cannot fix what I cannot see. Worse: the ORM makes
one specific catastrophic pattern feel completely natural to write.

# Theory (from zero)

**The ORM (Object-Relational Mapper)** is a translator:

```
   PYTHON I WRITE                          SQL POSTGRES RUNS
   ───────────────────────────────         ──────────────────────────────────
   Adda.objects.all()                      SELECT … FROM production_adda
   .filter(status='completed')              WHERE status = 'completed'
   .exclude(code='X')                       AND NOT (code = 'X')
   .order_by('-id')                         ORDER BY id DESC
   [:5]                                     LIMIT 5
   .count()                                 SELECT count(*) …
   .aggregate(Sum('amount'))                SELECT sum(amount) …
   .annotate(n=Count('addas'))              …, count(…) … GROUP BY …
   .select_related('product')               JOIN production_product …
   .prefetch_related('sizes')               a SECOND query: WHERE id IN (…)
```

**Lazy evaluation — the idea that explains a lot.** A queryset builds SQL but
**does not run it** until you iterate, index, `len()`, or `list()` it. So
`qs = Adda.objects.filter(...)` costs nothing; `for a in qs:` is where the trip to
the database happens.

### N+1: the bug in a picture

```
   THE INNOCENT-LOOKING CODE
   for adda in Adda.objects.all():            ← 1 query: fetch 28 addas
       print(adda.product.name)               ← 1 query EACH TIME. 28 more.
                                                ────────────────────────────
                                                TOTAL: 29 round-trips
   ┌──────────────────────────────────────────────────────────────────┐
   │  Django ──▶ Postgres   "give me the addas"            (query 1)  │
   │  Django ──▶ Postgres   "product for adda 1?"          (query 2)  │
   │  Django ──▶ Postgres   "product for adda 2?"          (query 3)  │
   │  Django ──▶ Postgres   "product for adda 3?"          (query 4)  │
   │       …            28 times …                                     │
   └──────────────────────────────────────────────────────────────────┘
   Each round-trip is small. The LATENCY is the killer: 29 × network+plan.
   Every single query looks fast in EXPLAIN. The PAGE is still slow.

   THE FIX  (one JOIN — chapter 07)
   for adda in Adda.objects.select_related('product'):   ← 1 query. Total: 1.
```

At 28 Addas it is invisible. At 5,000 it is a dead page. **The bug does not grow
gradually — it grows with your data, which is exactly when you least want it.**

**The two cures, and when each applies:**

| Cure | SQL it generates | Use for |
|---|---|---|
| `select_related('product')` | one query with a **JOIN** | ForeignKey / OneToOne (the "one" side) |
| `prefetch_related('sizes')` | **two** queries: main + `WHERE id IN (…)` | ManyToMany / reverse FK (the "many" side) |

Why not always JOIN? Because joining a *many* relation multiplies rows (ch 07's
duplication trap) — two clean queries beat one exploded one.

> 💡 **Samjho aise:** ORM ek **tarjuma karne wala (translator)** hai — main Python
> bolta hoon, wo SQL mein bolta hai. Dikkat tab hoti hai jab main galti se kehta
> hoon: *"50 Adde lao"* … aur phir har Adde ke liye **alag se** *"iska product
> naam kya hai?"* poochhta hoon. 51 baar almirah tak daudna. Sahi tareeka: *"50
> Adde, unke product ke naam ke SAATH, ek hi baar mein lao"* — wahi
> `select_related` hai. **Dheema page aksar dheemi query nahi, ZYADA queries hota hai.**

# Real World Example (My ERP)
My own project already fights this deliberately:
- Panels and lists use `select_related(...)` / `prefetch_related(...)` — e.g. the
  pattern panel fetches photos with `.select_related('uploaded_by')` so rendering
  a photo list does not re-query per photo.
- The kos playbook [page-slow-or-erroring](../../kos/debugging/page-slow-or-erroring.md)
  is built around this exact hunt, and its rule is the one from chapter 15:
  **count the queries first, read code second.**
- `CONN_MAX_AGE = 600` in settings keeps a DB connection alive for 10 minutes so
  each request does not pay a fresh connection handshake. That is the *other* kind
  of per-request overhead, and worth knowing it is already handled.

# Practical — try it yourself

**Seeing the SQL for yourself** — three ways, all real:

```bash
# 1. the SQL a queryset would run (no execution)
env/bin/python config/manage.py shell --settings=config.settings.local -c "
from production.models import Adda
print(Adda.objects.filter(status='completed').order_by('-id')[:5].query)"

# 2. COUNT the queries a block of code makes — the N+1 detector
env/bin/python config/manage.py shell --settings=config.settings.local -c "
from django.test.utils import CaptureQueriesContext
from django.db import connection
from production.models import Adda
with CaptureQueriesContext(connection) as ctx:
    for a in Adda.objects.all():
        _ = a.product.name          # the innocent line
print('queries WITHOUT select_related:', len(ctx))
with CaptureQueriesContext(connection) as ctx2:
    for a in Adda.objects.select_related('product'):
        _ = a.product.name
print('queries WITH select_related:', len(ctx2))"

# 3. the migration-level view: what SQL does a model become? (ch 19)
env/bin/python config/manage.py sqlmigrate production 0001 --settings=config.settings.local | head -20
```
Run #2. The first number will be large; the second will be **1**. That contrast is
the whole chapter.

# Visual Diagram
```
   WHERE THE TIME ACTUALLY GOES
   ═══════════════════════════════════════════════════════════════════
   ONE bad query (ch 15 fixes this)
   ├──────────── 800 ms in Postgres ────────────┤
   EXPLAIN shows it. Indexes/rewrites fix it.

   N+1 (this chapter fixes this)
   │▏│▏│▏│▏│▏│▏│▏│▏│▏│▏│▏│▏│▏│▏│▏│▏│▏│▏│▏│▏│▏│▏│▏│▏│▏│  ← 51 × ~15 ms
   Each bar is FAST. EXPLAIN on any one of them says "0.025 ms, perfect."
   The page still takes 800 ms. **You cannot EXPLAIN your way out of this.**
   ═══════════════════════════════════════════════════════════════════
   Diagnosis order:  ① count queries   ② then read plans
```

# Production Walkthrough
- The panels in this ERP use `select_related(...)` deliberately — e.g. pattern photos fetch `uploaded_by` in the same query, so rendering a photo list does not issue one query per photo.
- `CONN_MAX_AGE = 600` keeps a connection alive for 10 minutes, so a request does not pay a fresh Postgres handshake (each connection is a real OS process — ch 01, 24).
- The one place this codebase deliberately leaves the ORM is `pg_advisory_xact_lock(%s)` — a Postgres feature the ORM cannot express, still parameterised (ch 18, 22).
- The kos playbook `page-slow-or-erroring` codifies the rule: **count queries first, read plans second**.

# Debugging Guide
"The page is slow but every query looks fast":
1. **Count the queries.** `CaptureQueriesContext` in a shell, or django-debug-toolbar in a browser. If the count scales with the number of rows displayed, you have found it.
2. **Find the loop.** The attribute access inside it (`obj.related.field`) is the trigger.
3. **Pick the right cure:** `select_related` for FK/OneToOne (one JOIN), `prefetch_related` for M2M/reverse-FK (a second batched query).
4. **Re-count.** The number should collapse to a small constant. If it does not, there is a second N+1 further down the template.
5. **Only then** look at plans (ch 15).

# Performance Notes
- N+1 is a **latency** problem, not a CPU one: 51 fast queries still cost 51 round-trips plus 51 planning passes.
- `select_related` on a *many* relation multiplies rows (ch 07); that is why `prefetch_related` exists.
- `qs.count()` runs `SELECT count(*)`; `len(qs)` fetches every row into Python. `qs.exists()` beats `if qs:`.
- Querysets are **lazy** — building one is free; iterating is the cost. Re-iterating the same queryset variable may re-query.
- `only()` / `defer()` trim columns, and `values()` skips model instantiation entirely for read-only reports.

# Security Considerations
- The ORM's biggest security contribution is **automatic parameterisation** — the reason this codebase has essentially no injection surface (ch 22).
- The escape hatches (`.raw()`, `.extra()`, `cursor.execute(f"…")`) re-open that door. There are none in this app's services or views.
- Eager-loading a relation can pull columns a user must not see; the permission check belongs in the service, not in the template that happens not to print them.

# Architecture Decisions
- **ORM by default, raw SQL by exception, always parameterised.** The exception is documented at the call site.
- **Services own queries that carry business meaning**, so access rules travel with the query rather than living in a template.
- **Measured optimisation only** — `select_related` is added where a query count proved it was needed, not speculatively.

# Best Practices
- Any `for` loop over a queryset that touches a relation needs eager loading. Check every time.
- Use `.query` while developing to see what you are really sending.
- Prefer `count()` / `exists()` over Python-side equivalents.
- Keep the query count for a page in your head as a budget; if it grows, ask why.

# Beginner Mistakes
- Touching `obj.related.field` inside a loop with no `select_related`. The canonical N+1.
- Using `select_related` on a many-relation (it raises, or explodes rows) instead of `prefetch_related`.
- `len(qs)` to count → fetches every row into Python. Use `qs.count()` (a `SELECT count(*)`).
- `if qs:` to test emptiness → evaluates the whole queryset. Use `qs.exists()`.
- Re-using a queryset variable in several loops — each iteration may re-query
  (cache it with `list(qs)` when you truly need it repeatedly).
- Optimising a plan for 30 minutes when the real problem was 51 queries.
- Believing the ORM is "slow". It generates fine SQL; it just also lets you ask 51 times.

# Interview Questions
- **Junior:** *What is an ORM?* — a layer mapping classes/objects to tables/rows, generating SQL for you.
- **Junior:** *What is the N+1 query problem?* — one query for a list plus one per item for a relation; fix with eager loading (`select_related`/`prefetch_related` in Django, `includes` in Rails, `JOIN FETCH` in JPA). **The single most-asked ORM question in interviews.**
- **Mid:** *`select_related` vs `prefetch_related`?* — JOIN in one query for to-one relations vs a second `IN (…)` query for to-many relations (avoiding row multiplication).
- **Mid:** *When is a queryset actually executed?* — lazily: on iteration, slicing with a step, `len()`, `list()`, `bool()`, or pickling. Building it is free.
- **Senior:** *An endpoint is slow but every query is fast — what now?* — count queries (`CaptureQueriesContext`, django-debug-toolbar, `pg_stat_statements`); latency is usually round-trips, not plans. Then fix eagerly-loadable relations.
- **Senior:** *When would you drop the ORM for raw SQL?* — complex analytics, window-heavy reports, bulk operations, or database features the ORM cannot express (like `pg_advisory_xact_lock`, which my settlement service calls with a raw parameterised cursor — ch 18/22).
- **Staff:** *Trade-offs of ORM vs raw SQL in a money system?* — ORM gives safety (parameterisation, migrations, one model of truth) and readability; raw SQL gives control and access to engine-specific features. The mature answer is *both*, with the boundary drawn explicitly — and every raw call still parameterised (ch 22).

### Why interviewers ask these — and the answer that separates levels

| Testing for | Weak answer | What lands |
|---|---|---|
| The most-asked ORM question. Can you name AND fix it? | "N+1 is when you make too many queries." | One query for the list **plus one per item** for a relation. Fix by eager loading: **`select_related`** (to-one, JOIN) / **`prefetch_related`** (to-many, second `IN (…)` query). Naming the fix per relation type is the actual answer. |
| Do you know why there are two eager-loading methods? | "prefetch_related is the newer one." | `select_related` **JOINs** — safe for to-one. `prefetch_related` runs a **second query** — necessary for to-many precisely because a JOIN would **multiply rows** and corrupt any aggregate (ch 07/08). |
| Do you know when a queryset actually hits the database? | "When you build it." | **Lazily** — on iteration, `len()`, `list()`, `bool()`, slicing with a step, or pickling. Building and chaining filters is **free**, which is why you can pass querysets around and compose them. |
| When would you leave the ORM? | "Raw SQL is faster, so for anything slow." | For **window-heavy reports, complex analytics, bulk operations**, and engine features the ORM cannot express — like **`pg_advisory_xact_lock`**, which this settlement service calls through a raw **parameterised** cursor. Speed alone is rarely the reason. |

**The killer follow-up:** *"ORM or raw SQL for a money system?"* — the mature answer is **both, with the boundary drawn explicitly**: ORM for safety (parameterisation, migrations, one model of truth), raw SQL where the engine has something the ORM lacks — and **every raw call still parameterised** (ch 22). "Always ORM" and "real engineers write SQL" are both junior answers.

# Revision Notes
- ORM = Python → SQL translator; querysets are **lazy**.
- **N+1** = 1 query + one per row. The classic ORM bug.
- `select_related` = JOIN (to-one) · `prefetch_related` = second query (to-many).
- `qs.count()` not `len(qs)` · `qs.exists()` not `if qs:`.
- Slow page ⇒ **count queries first**, plans second.

# Cheat Sheet
- ORM = Python → SQL translator; querysets are **lazy**
- `.query` prints the SQL · `sqlmigrate` prints DDL
- **N+1** = 1 + one-per-row; fix with `select_related` (FK/JOIN) or `prefetch_related` (M2M/2 queries)
- `qs.count()` not `len(qs)` · `qs.exists()` not `if qs:`
- slow page ⇒ **count queries first**, read plans second
- `CONN_MAX_AGE=600` already saves per-request connection cost

# My ERP Section
| Concept | Where in my project |
|---|---|
| Eager loading in practice | `select_related('uploaded_by')` on pattern photos, and similar across panels |
| N+1 playbook | [kos: page-slow-or-erroring](../../kos/debugging/page-slow-or-erroring.md) |
| ORM ↔ SQL bridge doc | [kos: from-orm-to-sql](../../kos/concepts/postgresql/from-orm-to-sql.md) · [orm-and-managers](../../kos/concepts/django/orm-and-managers.md) |
| Connection reuse | `CONN_MAX_AGE = 600` (settings/base.py) |
| Deliberate raw SQL | advisory locks in `adda_settlement_service` (parameterised) |

# Practice Tasks
1. **Read the code:** find a `select_related` in `config/production/views/` and explain which N+1 it prevents.
2. **Debug:** run the `CaptureQueriesContext` comparison from Practical #2. Write down both numbers — that gap is your own N+1, measured.
3. **Design:** the A360 page shows Addas with product, creator and stage count. Which relations need `select_related` and which need `prefetch_related`? Justify each.
4. **Architecture:** when is dropping to raw SQL the right call in this codebase? Give one concrete example that already exists.

# Homework
1. Run Practical #2. Write down both query counts. That gap is N+1, measured on your own data.
2. Print `.query` for `Adda.objects.filter(status='completed').select_related('product')`. Find the JOIN in the output and name the ON condition.
3. Compare `len(Adda.objects.all())` with `Adda.objects.all().count()` using `CaptureQueriesContext`. Which one is cheaper, and *why*?

# Further Reading & Live Resources
- [Django: database access optimization](https://docs.djangoproject.com/en/5.0/topics/db/optimization/) — the official checklist
- [Django: select_related / prefetch_related](https://docs.djangoproject.com/en/5.0/ref/models/querysets/#select-related)
- [Django: when querysets are evaluated](https://docs.djangoproject.com/en/5.0/ref/models/querysets/#when-querysets-are-evaluated)
- [django-debug-toolbar](https://django-debug-toolbar.readthedocs.io/) — shows the query count per page
