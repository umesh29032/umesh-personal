---
id: concept-django-migrations
type: concept
verified: 2026-07-19
knowledge_confidence: verified_against_code
answers: "How does this repo change a live schema carrying real money without ever losing data or trapping itself?"
related: [concept-pg-constraints, concept-append-only-tables, concept-two-truths]
---

# Migrations — schema changes that never betray the data

> 📂 [Django concepts](README.md) · [All concepts](../README.md) · [KOS home](../../README.md)

## 1. The project hook

Migration `production/0035` DROPS a table — the legacy `AddaStageRecord.workers`
M2M, the old production-truth. Dropping data-bearing structure on a system
that pays real wages should be terrifying. This repo made it boring, with
a design worth studying line by line: a **data-aware reverse** that was
rehearsed up→down→up on a clone with exact-set comparison BEFORE it ever
touched a real database. That's the standard this page teaches.

## 2. 💡 Samjho Aise

Migration = ghar ki naksha-badli JAB ghar mein log reh rahe hon. Deewar
todni hai? Pehle poochho: (1) wapas banani padi to bana paunga? (naksha
saath rakho — reverse), (2) todne se pehle saaman nikala? (backfill),
(3) kisi doosre kamre ki chhat is deewar par to nahi tiki? (dependencies).
Aur sabse pakki aadat: pehle DUPLICATE ghar par todkar dekho (clone
rehearsal), phir asli par haath lagao.

## 3. Mental Model

> Every migration is TWO programs: forward and reverse — and the reverse
> is a PROMISE you're making to future-you at 2 AM. Three honesty levels:
> auto-reversible (pure schema) · **data-aware reverse** (you write code
> that reconstructs what forward discarded) · irreversible (say so
> LOUDLY, and gate it behind a soak). Never let Django default you into
> level 3 silently — that's how point-of-no-return happens by accident.

## 4. Technical Deep Dive — the repo's four signature patterns

**Pattern 1 — the data-aware reverse** (`production/0035`, real header):
forward = pure drop of the M2M. Reverse = auto-recreate the join table,
then a `RunPython(noop, rebuild_m2m_from_tasks)` **repopulates membership
from non-cancelled `WorkerStageTask` rows** — which equals the dropped
data exactly *while the parity invariant holds* (dual-write era guaranteed
it). Note the shape: `RunPython(forward=noop, reverse=rebuild)` — code
that ONLY runs on the way back. And the proof standard: *"verified by the
up→down→up clone rehearsal with exact-set comparison."*

**Pattern 2 — one-file backfill + constraint swap** (`production/0039`):
```
RunPython(backfill_good, noop)     # 1. make data valid (good = reported)
RemoveConstraint(old)              # 2. drop the outdated wall
AddConstraint(wsc_gam_nonneg_sum_positive)  # 3. raise the new wall
```
One migration, ordered operations, **no deploy window where either rule is
unenforced** ([pg/constraints](../postgresql/constraints.md) §4).

**Pattern 3 — rename-not-drop (dual-write staging).** `reported_quantity`
wasn't dropped when `good` replaced it — it's dual-written (`reported =
good`) with the actual DROP deferred to S6, **soak-gated post-deploy**.
Irreversible steps get STAGED: new column → dual-write → consumers migrate
→ production soak proves nothing reads the old one → THEN drop. The
point of no return is crossed on purpose, on a date, not by a deploy.

**Pattern 4 — backfill only known facts** (owner standing rule). A
backfill writes what the data PROVES (`good = reported` — the report was
the only fact), never plausible inventions (no "assume rate was X").
History tables don't get retro-fitted events; unknown stays NULL —
[honest-null thinking](../database-design/append-only-tables.md).

**Operational rules that keep multi-app migrations sane here:**
- Cross-app dependencies mean unapply CASCADES — reversing expense may
  drag production; always `migrate` (global), review the plan first.
- `RunPython` goes in `operations`, NOT `dependencies` — a real crash
  this repo logged (chokepoint doc's "common mistakes").
- Migrations run in the SAME transaction as their DDL on PostgreSQL —
  a failed backfill rolls back its schema changes too (transactional DDL
  is a PG superpower; respect it by not mixing in nontransactional ops).
- Sequential fresh-DB test law: the 1878-test battery builds the schema
  from ZERO every run — every migration executes forward on every CI run,
  so a broken chain can't hide.

## 5. Engineering Thinking

*Why insist on reverses when "we'd never roll back"?* Because the reverse
is ALSO the rehearsal tool — up→down→up on a clone is how you PROVE the
forward is safe, even if production never rolls back. A migration you
can't reverse is a migration you can't rehearse. *Why stage irreversibles
instead of just being careful?* Because "careful" is a mood and soak is a
MEASUREMENT — S6 waits for production evidence that nothing reads
`reported_quantity`. *When is auto-reverse a lie?* `RemoveField` on data:
Django happily recreates the COLUMN, empty — schema-reversible,
data-irreversible. That gap is exactly what pattern 1 closes with code.
*The deeper principle:* migrations are append-only history too — you never
edit an applied migration; you write the next one
([append-only](../database-design/append-only-tables.md), applied to the
schema itself).

## 6. How THIS project uses it

The 0035 story end-to-end is the masterclass: (V2-1a) new models built
alongside → (dual-write flag `WORKER_TASK_DUAL_WRITE`) both worlds kept in
parity → (reads migrated) consumers repointed → (parity verified) → (0035)
old world dropped WITH a data-aware reverse that leans on the parity
invariant → (rehearsed on clone, exact-set compare) → executed. Every
risky cutover in this repo follows that ladder — the same one ADR-0007
used for the money-era cutover with its `LEDGER_CREDIT_AT_ALLOCATION`
rollback lever. **Schema courage comes from staging, not confidence.**

## 7. What breaks without it

The generic disasters: a RemoveField deployed, bug found, "just roll
back" — column returns empty, data gone. A constraint added before
backfill — deploy fails at midnight on the first dirty row. A backfill
inventing plausible history — audits now contain fiction that can't be
distinguished from fact. Each pattern above is a scar-shaped bandage.

## 8. Common mistakes (humans)

- Editing an applied migration (it already ran elsewhere — write a new one).
- `makemigrations` noise committed unreviewed — every operation in the
  file is a production event; read it like code, because it is.
- Forgetting `elidable=True` questions on RunPython when squashing.
- Testing only forward — up→down→up is the rehearsal that finds reverse lies.
- Assuming SQLite-dev parity — this repo is PG-only in ALL environments
  partly so migrations rehearse on the real dialect.

## 9. AI Implementation Pitfalls

- ❌ Writing `RunPython` without a reverse function — defaulting to
  irreversible SILENTLY; use noop or a real reverse, deliberately.
- ❌ Dropping a column in the same PR that stops writing it — stage it
  (rename-not-drop, soak the drop).
- ❌ Backfilling computed "probable" values into money/history tables —
  backfill only known facts (owner law).
- ❌ Data migrations that import models directly (`from production.models
  import ...`) instead of `apps.get_model` — breaks against historical
  schema states.
- ✅ Always verify: `migrate` plan reviewed both directions · battery green
  (fresh-DB = full forward replay) · reverse rehearsed on scratch for
  anything data-bearing.

## 10. DSA & Complexity

The migration graph is a **DAG** (dependencies = edges; `migrate` =
topological sort; unapply = reverse-topological — which is WHY cross-app
reverses cascade). Squashing = path compression on that DAG. And the
dual-write ladder is the distributed-systems classic: expand → migrate →
contract — the safe schema-change protocol, here in single-node clothes.

## 11. Interview corner

**Q. "How do you drop a column that production code still might read?"**
- *Short:* You don't — expand/contract: add new, dual-write, migrate readers, soak with evidence, THEN drop, with the drop as its own gated deploy.
- *Senior:* Classify the change's reversibility honestly and stage the irreversible part behind a measurement, not a belief. Rehearse up→down→up on a clone with data comparison for anything data-bearing. Keep backfills to provable facts, in the same migration as the constraint they enable, ordered so no unprotected window exists.
- *Project example:* `reported_quantity` → `good` (dual-write, S6 soak-gated drop); 0035's data-aware reverse rebuilt from WST with exact-set rehearsal; 0039's backfill→swap in one file.
- *Follow-ups:* "Zero-downtime constraint on a big table?" (`NOT VALID` + `VALIDATE`) · "Why apps.get_model in RunPython?" (historical model states) · "What makes a migration untestable?" (no reverse — can't rehearse).

## 12. 🧠 Remember This

Har migration do program hai — jaana AUR lautna. Lautna likh nahi sakte to
CHILLA ke bolo aur soak ke peeche rakho. Todne se pehle bharna (backfill →
swap, ek file), girane se pehle dual-write, aur asli se pehle clone par
up→down→up. Naksha-badli mein himmat nahi, seedhi chahiye.

## 13. 30-Second Revision

- 3 honesty levels: auto-reversible · data-aware reverse (0035: rebuild from WST, clone-rehearsed) · loud irreversible (soak-gated, S6)
- One-file law: backfill → RemoveConstraint → AddConstraint (0039) — no unprotected window
- Expand→dual-write→migrate readers→soak→contract (reported→good)
- Backfill ONLY known facts; apps.get_model in RunPython; never edit applied migrations
- migrate = DAG toposort; cross-app unapply cascades; fresh-DB battery replays every forward, every run

## 14. What You Should Now Understand

The four patterns and which risk each kills, why reverses matter even
without rollbacks (rehearsal!), and how staged irreversibility converts
courage into procedure. Shaky? Open `production/0035` and read its header
— the best-commented migration in the repo.

**Recommended next topic:** [django/settings](settings.md) — the other
place where "boring and explicit" keeps production alive.

## Implementation References

- Cutover twin: [ADR-0007](../../../docs/adr/0007-allocation-era-ledger-cutover.md)
- Law source: owner data-principles (backfill-known-facts) — reflected in every RunPython here

## Code References
- `config/production/migrations/0035_*.py` (data-aware reverse + rehearsal note) · `0039_*.py` (one-file pattern) · S6 register: [docs/PENDING_BACKLOG.md](../../../docs/PENDING_BACKLOG.md)

## Further Reading

- Official: [Django — Migrations](https://docs.djangoproject.com/en/5.0/topics/migrations/) · [Data migrations](https://docs.djangoproject.com/en/5.0/howto/writing-migrations/)

## Related

[pg/constraints](../postgresql/constraints.md) · [append-only-tables](../database-design/append-only-tables.md) ·
[two-truths](../architecture/two-truths.md) · [settings](settings.md)
