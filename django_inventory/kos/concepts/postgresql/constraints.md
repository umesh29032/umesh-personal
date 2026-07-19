---
id: concept-pg-constraints
type: concept
verified: 2026-07-19
knowledge_confidence: verified_against_code
answers: "Why does this project put 80+ CHECK constraints in PostgreSQL when the services already validate everything?"
related: [concept-append-only-tables, concept-single-writer, feature-ledger]
---

# PostgreSQL Constraints — the wall that stands when code falls

> 📂 [PostgreSQL concepts](README.md) · [All concepts](../README.md) · [KOS home](../../README.md)

## 1. The project hook

Every service validates. Every form validates. So why does the live dev
database carry — counted today, straight from `pg_constraint` — **81 CHECK
constraints, 163 foreign keys, 36 unique constraints** across the expense/
production/tracking tables? Because services are the guards you HIRED;
constraints are the wall you BUILT. Guards call in sick — a forgotten code
path, a raw shell fix, a buggy migration. Walls don't.

## 2. 💡 Samjho Aise

Ghar mein do suraksha: chowkidar (service validation) aur deewar (DB
constraint). Chowkidar samjhata hai, roasta hai, wajah batata hai — par wo
INSAAN hai, chhuk sakta hai. Deewar bewakoof hai, kuch nahi samjhati — par
usse koi nahi langhta, kabhi bhi, kisi bhi raaste se. Paise wale kamre ke
liye dono chahiye.

## 3. Mental Model

> **Tiered invariants.** Ask of every rule: can the DATABASE express it?
> - Yes, single row → CHECK constraint (`amount > 0`)
> - Yes, across rows → UNIQUE / partial unique / FK (`one reversal per entry`)
> - No (needs business context) → the sole-writer service
> The DB tier is your floor: even the worst bug cannot sink below it.
> Never rely on the app tier alone for anything money-shaped.

## 4. Technical Deep Dive — the full chain (Database Page Law)

**Django declaration** (`config/expense/models.py`):

```python
class Meta:
    constraints = [
        models.CheckConstraint(
            check=models.Q(amount__gt=0),           # ⚠ Django 5.0.1: check=,
            name='expense_ledgerentry_amount_positive',  # NOT condition=
        ),
        models.UniqueConstraint(
            fields=['reverses'], condition=models.Q(reverses__isnull=False),
            name='uniq_one_reversal_per_entry',
        ),
    ]
```

**What PostgreSQL actually holds** (queried live from the dev DB today):

```sql
-- pg_get_constraintdef for expense_workerledgerentry:
expense_ledgerentry_amount_positive | CHECK ((amount > (0)::numeric))
```

**The gotcha the live query teaches:** the conditional `UniqueConstraint`
did NOT appear in `pg_constraint` — a partial unique lands in **`pg_indexes`**
as `CREATE UNIQUE INDEX ... WHERE (reverses_id IS NOT NULL)`. Audit scripts
that census only `pg_constraint` under-count your armor. (This repo's
declared-vs-live census checks BOTH catalogs.)

**How PG enforces:** CHECK runs per-row at INSERT/UPDATE inside the same
transaction — violation = statement error = **automatic rollback of the
whole atomic block**. Unique enforcement is index-based, which is why it's
race-proof: two concurrent inserts hit the same btree page; one wins, one
gets `23505`. That's the property no app-level "check if exists first" can
ever have — the check-then-act gap belongs to the index now.

**Repo's greatest hits:**

| Constraint | Table | Protects |
|---|---|---|
| `amount > 0` | ledger · advances | direction stays in `entry_type`; SUMs stay honest |
| `uniq_one_reversal_per_entry` (partial unique) | ledger | double-reversal race |
| `wsc_gam_nonneg_sum_positive` (migration prod 0039) | contributions | good/alter/missing each ≥0, sum > 0 — the S3 data shape |
| `amount_paid + advance_deducted == payable_settled` family | payroll settlement | the cash identity, snapshot-level |
| PROTECT FKs (163 total) | every money anchor | a financial row's parents can never vanish |

**Migration craft note** (prod 0039, the S3 one-file pattern): backfill
`good = reported` → DROP the old constraint → ADD the new one — data made
valid BEFORE the new wall goes up, one migration, no window where either
rule is unenforced.

## 5. Engineering Thinking

*Why not app-validation only?* Because the app is not the only writer in
history — shell sessions, migrations, tomorrow's import script. The DB is
the only chokepoint EVERY write passes. *Why not triggers/stored procs for
the business rules too?* Logic invisible to Python readers and to the test
battery; constraints are declarative enough to audit in one catalog query,
triggers aren't. *The cost:* constraints make bad writes LOUD (500s instead
of silent corruption) — that's a feature; loud-not-silent is a design
principle here. *Assumption:* constraint names are stable and censused —
the certification sweep (10/10 negative probes refused, declared-vs-live
census) treats the wall as a tested artifact, not decoration.

## 6. How THIS project uses it

The **negative probe** discipline: tests don't just prove good data passes —
they prove bad data is REFUSED at the DB (attempt the insert, assert the
IntegrityError). 10/10 negative probes in certification. A constraint
without a refusal test is a rumor. Combine with the census (declared in
models ≡ live in pg_catalog, both catalogs) and you get armor you can PROVE
exists — 81 CHECKs strong today.

## 7. What breaks without it

The exact bugs the services already prevent — but from the paths services
don't cover: a migration that backfills a negative amount; a shell "quick
fix"; a future bulk importer. With the wall: loud 23514/23505 at write
time. Without: quiet corruption discovered at settlement, permanently
recorded in an append-only book.

## 8. Common mistakes (humans)

- Django 5.0.1: writing `CheckConstraint(condition=...)` — it's `check=`
  in this version (repeat repo lesson; renamed in later Django).
- Censusing armor via `pg_constraint` only — partial uniques hide in `pg_indexes`.
- Adding a constraint to dirty data — backfill first, constrain second (0039 pattern).
- Treating IntegrityError as "handle and continue" — it's a bug report, not a flow.

## 9. AI Implementation Pitfalls

- ❌ Dropping/loosening a constraint to make a feature "work" — the
  constraint is the requirement; the feature is wrong.
- ❌ Adding CHECK + backfill as separate deploys — the unprotected window
  is real; use the one-file pattern.
- ❌ Validating in Python and skipping the DB twin for money fields — tiered
  or it isn't armor.
- ✅ Always verify: negative probe added for every new constraint;
  declared-vs-live census stays clean.

## 10. DSA & Complexity

Unique enforcement = btree index property: insert is O(log n) and the
uniqueness check is FREE at the page you were already writing — which is
why constraint-based idempotency beats SELECT-then-INSERT (two operations
with a gap) both in correctness AND complexity. CHECKs are O(1) per row —
81 of them cost microseconds and buy provability.

## 11. Interview corner

*Interview Signal: 🟠 Senior — tiered invariants signal senior data thinking.*

**Q. "Application-level or database-level validation?"**
- *Short:* Both, tiered — app for UX and business context, DB for invariants that must survive every code path.
- *Senior:* Classify each rule by expressibility. DB-expressible invariants (sign, shape, uniqueness, referential existence) go in the schema where they're race-proof and writer-agnostic; business rules needing context live in the sole-writer service. Then TEST the DB tier with negative probes and census declared-vs-live — untested armor drifts.
- *Project example:* ledger `amount > 0` lives in service AND model AND PG; the reversal race is settled by a partial unique that plain app code cannot replicate; 81/163/36 counted live from pg_catalog.
- *Follow-ups:* "Constraint on huge existing table?" (backfill → validate → `NOT VALID`+`VALIDATE CONSTRAINT` staging for zero-lock adds) · "Where do partial uniques live in the catalog?" (pg_indexes — the census gotcha).

## 12. 🧠 Remember This

Service samjhaata hai, deewar rokti hai. Har money rule ke teen ghar:
service (wajah ke saath), model (declare), PostgreSQL (final na). Nayi
deewar se pehle zameen saaf karo (backfill), aur har deewar par ek negative
probe — bina test ki deewar afwaah hai.

## 13. 30-Second Revision

- Live census: 81 CHECK · 163 FK · 36 unique (expense/production/tracking)
- Partial uniques live in `pg_indexes`, NOT `pg_constraint` — census both
- Django 5.0.1: `CheckConstraint(check=...)` not `condition=`
- Unique = index-enforced = race-proof idempotency (23505)
- One-file pattern: backfill → drop old → add new (prod 0039)
- Negative probes: every constraint has a refusal test (10/10 certified)
- IntegrityError = bug report, never a control-flow branch

## 14. What You Should Now Understand

The tiered-invariant model, the ORM→SQL→catalog chain for both constraint
kinds, why unique-by-index beats check-then-act, and how this repo proves
its armor (probes + census). Shaky? Re-read §4 + §6.

**Recommended next topic:** back up to
[append-only-tables](../database-design/append-only-tables.md) if you came
here first — the two pages are one argument. Phase 5 will add
`from-orm-to-sql` + `indexes` for the read side.

## Implementation References

- Baseline: [docs/DB integrity work — PR1+PR2 26 CheckConstraints] via [docs/DOCUMENTATION_INDEX.md](../../../docs/DOCUMENTATION_INDEX.md) · certification negative probes: [docs/RELEASE_CERTIFICATION_LOG.md](../../../docs/RELEASE_CERTIFICATION_LOG.md)

## Code References
- `WorkerLedgerEntry.Meta.constraints` + siblings in `config/expense/models.py` · migration `production/0039` (one-file pattern)

## Further Reading

- Official: [PostgreSQL — Constraints](https://www.postgresql.org/docs/current/ddl-constraints.html) · [ALTER TABLE … NOT VALID](https://www.postgresql.org/docs/current/sql-altertable.html)

## Related

[append-only-tables](../database-design/append-only-tables.md) ·
[single-writer](../architecture/single-writer.md) · [pg/locks](locks.md) ·
[ledger](../../features/ledger.md)
