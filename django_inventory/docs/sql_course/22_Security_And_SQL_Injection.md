---
id: sql-course-22-security-and-sql-injection
type: lesson
status: active
owner: handwritten
scope: sql, postgresql — database fundamentals taught from this ERP
anchors: config/expense/services/settlement_service.py, config/production/services/pool_service.py
verified: 2026-08-01
---

# 22 — Security & SQL Injection

> Part of [SQL From Zero](00_COURSE_OVERVIEW.md). Prev: [21](21_Databases_Branching_And_Whats_Not_In_The_DB.md) · Next: [23 — JSONB](23_JSONB.md).

# Learning Objectives
By the end of this chapter you can:
- explain injection as a code/data boundary failure, not a syntax trick
- tell a parameterised query from a concatenated one at a glance
- say what parameters cannot protect (identifiers) and what to do instead
- name the security layers beyond injection, and this system's honest gaps

# Purpose
To understand the most famous vulnerability in software history, why my ERP is
structurally immune to it, and the one place my own code writes raw SQL — plus the
database-side security I inherit and the parts I still owe.

# The Problem
My app takes a search box value and must find matching rows. If that user text is
**glued into** the SQL string, then the user is no longer supplying *data* — they
are supplying **code**, and my database will loyally execute it.

```
   THE CLASSIC DISASTER
   ────────────────────────────────────────────────────────────────────
   code:   "SELECT * FROM users WHERE email = '" + user_input + "'"
   input:  x' OR '1'='1
   result: SELECT * FROM users WHERE email = 'x' OR '1'='1'
                                              └── always TRUE ──┘
   ⇒ every user row returned. Now try:  x'; DROP TABLE users; --
   ────────────────────────────────────────────────────────────────────
```

# Theory (from zero)

**The root cause is one idea:** string concatenation erases the boundary between
*code* and *data*. The fix is to never let them mix.

**Parameterised queries (bind parameters)** — send the SQL **and** the values
**separately**. The driver never builds one string; the server receives a statement
with placeholders plus a list of values, and treats each value as **pure data**,
whatever it contains.

```
   ❌ CONCATENATION — data becomes code
   ┌───────────────────────────────────────┐
   │ "…WHERE email = '" + input + "'"      │  one string, boundary GONE
   └───────────────────────────────────────┘
              │ input: x' OR '1'='1
              ▼
        Postgres parses it as SQL logic.  ☠️

   ✅ PARAMETERISED — data stays data
   ┌────────────────────────┐   ┌──────────────────────┐
   │ "…WHERE email = %s"    │ + │ ["x' OR '1'='1"]     │  two things, always
   └────────────────────────┘   └──────────────────────┘
              │
              ▼
        Postgres looks for a user whose email is LITERALLY
        the 12-character string  x' OR '1'='1  → finds none. Safe. ✅
   The quotes never "close" anything, because they were never in the SQL.
```

⚠️ **`%s` here is not Python string formatting.** It is the driver's placeholder.
`cur.execute(sql % value)` is the vulnerability; `cur.execute(sql, [value])` is the
fix. **One character of punctuation is the whole difference.**

**What parameters cannot do:** they bind *values*, never identifiers. You cannot
parameterise a table or column name. Dynamic identifiers must come from an
**allow-list in your own code**, never from user input.

**The layers of database security, beyond injection:**

| Layer | What it protects |
|---|---|
| Parameterised queries | injection |
| Least-privilege DB roles | limits damage if the app is compromised |
| Password hashing (Argon2 here) | stolen dumps don't reveal passwords |
| Network exposure | Postgres reachable only from the app, never the internet |
| Secrets in `.env`, never git | credentials don't leak via the repo |
| Backup handling | dumps contain everything — treat them as crown jewels |

> 💡 **Samjho aise:** Injection ka poora khel ek hi galti se hota hai —
> **user ki baat ko hukum samajh lena.** Sahi tareeka: SQL alag bhejo, aur user ka
> input **alag** bhejo (`%s` + list). Phir user chaahe `'; DROP TABLE …` likhe, wo
> sirf ek **naam** ban ke jaata hai — hukum nahi. Aur `%s` ko Python ka
> `%` formatting **na samjho**: `sql % value` = darwaza khula, `execute(sql, [value])`
> = darwaza band. Ek punctuation ka farq, poori suraksha ka farq.

# Real World Example (My ERP)
**My app is structurally immune to injection**, for a boring and excellent reason:
the Django ORM parameterises everything. `Adda.objects.filter(code=user_input)`
becomes `WHERE code = %s` with the value bound separately — *always*, with no
discipline required from me.

A repo-wide search for the dangerous patterns (`.raw(`, `RawSQL`) in my services
and views returns **nothing**. There is no injectable surface, because there is
almost no hand-written SQL.

**The one place my code does write raw SQL — and it does it correctly:**

```python
# config/expense/services/adda_settlement_service.py
with connection.cursor() as cur:
    cur.execute('SELECT pg_advisory_xact_lock(%s)', [_REF_LOCK])
#                                            ▲       ▲
#                          placeholder ──────┘       └── value passed SEPARATELY
```

That is the correct shape, in my own money-critical code path. It exists because
advisory locks (ch 18) are a Postgres feature the ORM cannot express — a legitimate
reason to drop to raw SQL. Note it is **still parameterised**, even though the value
is an internal constant that no user can influence. That is the right instinct:
parameterise by habit, not by risk assessment.

**Security I already have:**
- **Argon2** password hashing (winner of the Password Hashing Competition).
- Per-IP and per-email login rate limiting with lockout (ch 21: those counters live
  in the cache, not the DB).
- Secrets in `.env`, gitignored; `db_backups/` and `*.sql` gitignored too, because a
  dump contains real worker data **and password hashes**.

**Security I still owe** — honestly:
- My local Postgres has exactly **one role: `postgres`, a superuser**. Fine for a
  laptop; on production the app should connect as a least-privileged role that owns
  its tables and nothing more.
- `db.sh` connects using `.env` credentials, and the `.env.example` ships a
  `DATABASE_URL` line — a foot-gun the tool now refuses to run under (ch 21).

# Visual Diagram
```
   MY ACTUAL ATTACK SURFACE  (and why it is small)
   ══════════════════════════════════════════════════════════════════
   user input  ──▶ Django form (validate/coerce)
                        │
                        ▼
                   Django ORM  ──▶ ALWAYS parameterised  ──▶ Postgres
                        │                                       ▲
                        │                                       │
   raw SQL (rare) ──────┴──▶ cur.execute(sql, [params]) ────────┘
                                        ▲
                                        └── the ONLY raw path in my services:
                                            pg_advisory_xact_lock(%s) — bound.
   ══════════════════════════════════════════════════════════════════
   Defence in depth even so:
   form (shape) → service (rules) → CONSTRAINTS (ch 13) → least-privilege role
   Injection would still hit a wall of CHECKs it cannot satisfy.
```

# Practical — try it yourself
```bash
# 1. prove the ORM parameterises — look at the generated SQL
env/bin/python config/manage.py shell --settings=config.settings.local -c "
from production.models import Adda
evil = \"x' OR '1'='1\"
qs = Adda.objects.filter(code=evil)
print(qs.query)            # human-readable form
print('rows found:', qs.count())   # 0 — the whole string was treated as a NAME
"

# 2. confirm there is no injectable raw-SQL surface in my app code
grep -rn "\.raw(\|RawSQL" config/*/services/ config/*/views/ | grep -v test
#    (no output = nothing to audit)

# 3. see the one legitimate raw call, correctly parameterised
grep -n "advisory_xact_lock" config/expense/services/adda_settlement_service.py

# 4. what roles exist on my server? (REAL: only postgres, and it is a superuser)
env/bin/python config/manage.py shell --settings=config.settings.local -c "
from django.db import connection
c=connection.cursor(); c.execute(\"SELECT rolname, rolsuper FROM pg_roles WHERE rolname NOT LIKE 'pg_%'\")
print(c.fetchall())"

# 5. confirm secrets and dumps cannot be committed
git check-ignore -v .env db_backups/probe.sql 2>/dev/null
```
```sql
-- 6. SEE parameterisation work at the SQL level. Both are SAFE — the value
--    is data, not code. Compare with what concatenation WOULD have produced.
SELECT count(*) FROM production_adda WHERE code = 'x'' OR ''1''=''1';   -- 0
--    ^ '' is how SQL escapes a quote inside a literal; the whole thing is ONE value
```

# Production Walkthrough
- **There is essentially no injection surface here**, and it is boring rather than clever: the ORM parameterises everything, and a repo-wide search finds no `.raw(` or `RawSQL` in services or views.
- **The one raw call is correct**: `cur.execute('SELECT pg_advisory_xact_lock(%s)', [_REF_LOCK])` — parameterised even though the value is an internal constant. Parameterise by habit, not by risk assessment.
- **Argon2** hashes passwords, so a leaked dump does not hand over credentials cheaply.
- **Per-IP and per-email rate limiting** with lockout guards the login form; those counters live in the cache (ch 21).
- **The honest gap:** locally there is exactly one role — `postgres`, a superuser. Production should connect as a least-privileged role that owns its tables and nothing more. That is recorded as owed work, not glossed over.

# Debugging Guide
"Is this query safe?" — a three-step audit you can run on any code:
1. **Look for string building.** f-strings, `+`, `%`, `.format()` anywhere near SQL is the smell.
2. **Check the execute call shape.** `execute(sql, [params])` ✅ · `execute(sql % params)` ☠️ — one character of punctuation is the whole difference.
3. **Check for identifiers from input.** Table/column names cannot be parameterised; if one comes from a request, it must be validated against a hard-coded allow-list.
4. **Then check authorisation**, which injection-safety does not give you: is the filter using an id from the *session* or from the *URL*?
5. **Finally, check the constraints** (ch 13) — they are the wall that holds even if everything above failed.

# Performance Notes
- Parameterised queries are **faster**, not slower: Postgres can reuse a prepared plan instead of re-parsing a new string every time.
- Argon2 is *deliberately* slow and memory-hard — that is the security property. Tuning it too low to "speed up login" is a real mistake.
- Rate limiting protects performance as well as security: it caps the cost an attacker can impose.

# Security Considerations
Beyond injection, in rough order of blast radius:
- **Least-privilege database role** — the app should not be able to DROP anything.
- **Network isolation** — Postgres never exposed to the internet; only the app's private network.
- **Secrets in `.env`**, gitignored, never in code or migrations.
- **Backups are crown jewels** — every row plus password hashes (ch 20).
- **Authorisation ≠ authentication.** Being logged in is not permission; this project's audit probed 300 role×URL combinations precisely because that is where real leaks live.
- **Aggregates leak too** (ch 08): a total shown to the wrong role is a disclosure even though no row was displayed.

# Architecture Decisions
- **ORM-first** so parameterisation is the default and injection is structurally unlikely rather than carefully avoided.
- **Raw SQL only where the ORM cannot express the feature**, documented at the call site, still parameterised.
- **Defence in depth**: form → service → constraint → database role. Any single failure is survivable.
- **Refuse rather than guess** — the DB tooling stops when configuration is ambiguous (`DATABASE_URL` present) instead of acting on the wrong target.

# Best Practices
- Never build SQL with user input. There is no "safe" concatenation.
- Parameterise even internal constants; habits beat judgement under deadline.
- Whitelist identifiers; never interpolate a column name from a request.
- Treat every dump and every non-production copy of production data as sensitive.

# Beginner Mistakes
- Building SQL with f-strings/`+`/`%` and user input. The one mistake that matters.
- Thinking "escaping quotes myself" is equivalent to parameterising. It is not —
  encodings, edge cases and dialects will beat you. Let the driver do it.
- Believing an ORM makes you immune *no matter what* — `.raw()`, `extra()` and
  `cursor.execute(f"…")` re-open the door.
- Trying to parameterise a **table or column name** (impossible) and falling back
  to concatenation — use a hard-coded allow-list instead.
- Running the app as a Postgres **superuser** in production.
- Committing a dump or `.env`; emailing a dump around. Dumps hold password hashes.
- Exposing port 5432 to the internet.

# Interview Questions
- **Junior:** *What is SQL injection?* — untrusted input treated as SQL code because it was concatenated into the query string.
- **Junior:** *How do you prevent it?* — parameterised queries / bind parameters; never string-build SQL with user input.
- **Mid:** *Does an ORM guarantee safety?* — mostly yes, because it parameterises; but raw escape hatches (`.raw()`, `cursor.execute` with formatting, `extra()`) bypass it.
- **Mid:** *Can you parameterise a table name?* — no, only values. Use a validated allow-list for identifiers (or the driver's identifier-quoting helper).
- **Senior:** *Beyond injection, how do you harden a database?* — least-privilege roles (the app should not be superuser and should not own DDL rights in production), network isolation, TLS, secrets management, encryption at rest, audited backups, and treating dumps as sensitive artefacts.
- **Senior:** *Why hash passwords with Argon2/bcrypt rather than SHA-256?* — password hashes must be *deliberately slow* and memory-hard with per-user salts, to make offline brute force from a stolen dump impractical; fast general-purpose hashes are the wrong tool.
- **Staff:** *An attacker gets read access to a nightly dump. Assess the blast radius.* — every row, including PII and password hashes (survivable only because Argon2 makes cracking expensive) — so dumps need encryption at rest, restricted access, retention limits, and anonymisation for any non-production copy. This is exactly why `db_backups/` is gitignored here rather than "probably fine".

### Why interviewers ask these — and the answer that separates levels

| Testing for | Weak answer | What lands |
|---|---|---|
| Does an ORM make you safe? | "We use the ORM, so injection is impossible." | **Mostly** — because it parameterises. But `.raw()`, `extra()`, and `cursor.execute` **with string formatting** bypass it entirely. The honest answer names its own escape hatches; this repo uses a raw cursor for advisory locks and **still parameterises it**. |
| Can you parameterise a table name? | "Yes, same as a value." | **No — only values can be bound.** Identifiers need a **validated allow-list** (or the driver's identifier-quoting helper). This is the exact spot where a "dynamic ORDER BY" feature becomes an injection. |
| Why Argon2/bcrypt and not SHA-256? | "They are more secure hashes." | Password hashes must be **deliberately slow and memory-hard, with a per-user salt**, so offline brute force from a stolen dump is impractical. SHA-256 is *fast* — which is precisely the wrong property. Fast general-purpose hashes are the wrong tool, not a weaker one. |
| Do you harden beyond injection? | "We parameterise queries and use HTTPS." | **Least-privilege roles** (the app is not superuser and does not own DDL in production), network isolation, TLS, secrets management, encryption at rest, and **treating dumps as sensitive artefacts**. Injection is one door in a building. |

**The killer follow-up:** *"An attacker gets read access to one nightly dump. Assess the blast radius."* — **every row**: PII, wages, receipts, and password hashes — survivable only because Argon2 makes cracking expensive. So dumps need **encryption at rest, restricted access, retention limits and anonymisation for non-production copies**. That is why `db_backups/` is gitignored here rather than "probably fine".

# Revision Notes
- Injection = data treated as code; cure = **parameterise**, always.
- `execute(sql, [value])` ✅ · `execute(sql % value)` ☠️
- Parameters bind **values only** — identifiers need an allow-list.
- ORM parameterises by default; `.raw()`/`.extra()`/f-strings re-open the door.
- **A dump = all your data + password hashes.** Treat it as a secret.

# Cheat Sheet
- injection = data treated as code · cure = **parameterise**, always
- `cur.execute(sql, [value])` ✅ · `cur.execute(sql % value)` ☠️
- ORM parameterises by default; `.raw()`/`extra()`/f-strings re-open the door
- parameters bind **values only** — identifiers need an allow-list
- Argon2 for passwords · least-privilege role in production · never expose 5432
- **a dump = all your data + password hashes** — treat it as a secret
- constraints (ch 13) are a second wall even against a successful injection

# My ERP Section
| Control | Status here |
|---|---|
| ORM parameterisation | everywhere (no `.raw`/`RawSQL` in services or views) |
| The one raw SQL call | `pg_advisory_xact_lock(%s)` — correctly bound (`adda_settlement_service`) |
| Password hashing | Argon2 (settings/base.py) |
| Login abuse | per-IP + per-email rate limit and lockout (cache-backed) |
| Secrets | `.env` gitignored; `db_backups/`, `*.sql`, `.env.bak` gitignored |
| ⚠️ Owed | production should use a **least-privilege role** — locally only `postgres` (superuser) exists |
| Related | [kos: auth-hardening](../../kos/concepts/security/auth-hardening.md) |

# Practice Tasks
1. **Read the code:** run `grep -rn "\.raw(\|RawSQL" config/` and then find the one legitimate raw call. Explain why it is safe.
2. **Debug:** run the injection payload from Practical #1 and confirm it returns 0 rows. Explain, in one sentence, why the quotes never "escaped".
3. **Design:** you must add a user-selectable sort column to a report. Write the safe implementation (hint: not a parameter) and say what makes it safe.
4. **Architecture:** write the least-privilege role you would create for production — which grants it needs, and which it must never have.

# Homework
1. Run Practical #1 with the payload `x' OR '1'='1`. It returns 0 rows. Explain, in one sentence, why the quotes did not "escape".
2. Run Practical #2 and #3. Write down every raw-SQL site in my app code and confirm each passes values separately.
3. Run Practical #4. Given that only a superuser role exists, write down what an attacker with the app's credentials could do — and what a least-privilege role would have prevented.

# Further Reading & Live Resources
- [OWASP SQL Injection](https://owasp.org/www-community/attacks/SQL_Injection) — the canonical reference
- [OWASP: Query Parameterization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Query_Parameterization_Cheat_Sheet.html)
- [Bobby Tables (parameterised queries per language)](https://bobby-tables.com/)
- [Postgres roles & privileges](https://www.postgresql.org/docs/current/user-manag.html)
- [Django: SQL injection protection & raw queries](https://docs.djangoproject.com/en/5.0/topics/security/#sql-injection-protection)
