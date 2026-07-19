---
id: debug-page-slow-or-erroring
type: debugging
verified: 2026-07-19
knowledge_confidence: verified_against_code
answers: "A page is suddenly slow, 500ing, or a save is deadlocking — where does a senior look first?"
related: [concept-query-performance, concept-pg-locks, concept-django-settings]
---

# Playbook: "Page dheema hai / gir raha hai"

> 📂 [Debugging](README.md) · [LOS home](../README.md)

## Symptoms this playbook covers

- A list page got slow (gradually or suddenly)
- 500 on an action that "worked yesterday"
- Saves hanging / deadlock errors under concurrent use
- Works locally, broken in production

## First Five Minutes

1. **Slow or erroring? Different lanes.** Slow → count queries FIRST
   (`CaptureQueriesContext` / debug toolbar): count exploded = N+1 at the
   call site (code-shape bug, not a DB bug); count normal = ONE expensive
   query → EXPLAIN it. *Never start by adding an index.*
2. **500 → read the actual exception, bottom frame first.** This repo's
   classifier: `ValidationError` text = a REFUSAL working as designed (read
   the message — it names the fix) · `IntegrityError` = the DB wall caught
   bad data (find the writer, never loosen the wall) · `InvalidOperation`/
   type errors at the edge = input parsed past the boundary (PA-07-2 class).
3. **Hanging saves → who holds the lock?** Settlement-adjacent = check the
   documented order (5374 first, always). A NEW operation deadlocking =
   someone took row locks without the gate.
4. **Works-locally-not-prod → config lane:** settings overlay diff, then
   `verify_production` output; the answer is usually an env var, not code.
5. **"Suddenly" is a lie worth interrogating:** what deployed/changed?
   dated receipts + git log answer faster than profilers.

## Decision tree

```
SLOW
├─ query count exploded → N+1: template loop attr / dropped select_related /
│    per-row method → fix at call site → RE-PIN the count (named constant)
├─ count fine, one big query → EXPLAIN (ANALYZE, BUFFERS):
│    est-vs-actual rows way off → stale stats (ANALYZE table)
│    Seq Scan on a NOW-big table → the declared index finally matters
│    (dev-size ≠ prod-size — the planner changed its mind WITH the data)
└─ neither → not the DB: template size? middleware? network?
500
├─ ValidationError → a guard refused; message names the actor/fix — do THAT
├─ IntegrityError → which constraint? (23505 unique / 23514 check) —
│    find the writer that skipped the service path
├─ Decimal/InvalidOperation → unparsed input reached logic — add the
│    edge-parse + the refusal pin
└─ ImproperlyConfigured/KeyError at boot → fail-fast config doing its job —
     fill .env, don't add a default
DEADLOCK / HANG
├─ settlement family → order violated: EVERY money op takes 5374 FIRST;
│    a lighter op holding WSC rows blocks finalize correctly (short wait ≠ deadlock)
└─ new feature → its locks joined the documented order? sorted per-worker?
```

## Which checks, concretely

| Check | How |
|---|---|
| Query count | `CaptureQueriesContext` around the view; diff vs its pin (12 pins exist — is one failing?) |
| The plan | `EXPLAIN (ANALYZE, BUFFERS)` — read bottom-up; Rows Removed = waste ([from-orm-to-sql §4](../concepts/postgresql/from-orm-to-sql.md)) |
| Lock waits | `pg_stat_activity` / `pg_locks` — who waits on whom; advisory 5374/5375 visible there |
| Config parity | production overlay is SHORT — read it; then `verify_production` |
| Template caching | dev runserver caches templates — RESTART after template edits (repeat repo lesson) |

## Known real causes (this repo's scars)

- **SETL reference race** → two clerks, IntegrityError 500 → fixed with the
  global advisory lock (the comment in `create_settlement` tells it).
- **`select_for_update` on nullable-FK join** → PG refuses → `of=('self',)`.
- **RunPython in `dependencies`** → migration crash class.
- **`--keepdb` state poison** → "flaky" tests that were cross-suite
  contamination; sequential fresh-DB law exists because of it.
- **Template edit "not taking"** → dev server template cache, restart.

## Where to learn the concepts

[query-performance](../concepts/postgresql/query-performance.md) ·
[indexes](../concepts/postgresql/indexes.md) · [locks](../concepts/postgresql/locks.md) ·
[settings](../concepts/django/settings.md) · [constraints](../concepts/postgresql/constraints.md)

## Implementation References

- Ops trees: [docs/release/TROUBLESHOOTING.md](../../docs/release/TROUBLESHOOTING.md) (11 field scenarios) · symptom router: [docs/LEARNING_2_0/PROJECT_BRAIN/DEBUGGING_INDEX.md](../../docs/LEARNING_2_0/PROJECT_BRAIN/DEBUGGING_INDEX.md)

## Code References

- Pins: `production/tests/test_perf_baseline.py` · `expense/tests/test_perf_settlement.py` — a slow-page fix ends by re-pinning
- Lock order canon: `expense/services/adda_settlement_service.py` + the chokepoint doc
