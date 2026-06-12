# Django concepts — as actually used in this project

## Models = tables
A Django model class is a PostgreSQL table; each instance is a row.
`TimeStampedModel` (core app, abstract) gives every child `created_at` /
`updated_at` columns — abstract matlab: columns COPY ho jaate hain child ki
table mein, koi extra JOIN nahi.

## ForeignKey + on_delete — the deletion contract
- **PROTECT** (our default for money/history anchors): parent delete = ERROR.
  Ledger row ke peeche ka worker/Adda/SWA kabhi gayab nahi ho sakta.
- **CASCADE**: child is meaningless without parent (e.g. LayeringRollEntry
  dies with its stage record — it was per-stage scratch).
- **SET_NULL**: optional reference (e.g. evidence link) — parent ja sakta
  hai, child reh jata hai.
Rule of thumb yahan: paise ya history touch karta hai? → PROTECT.

## Constraints — DB as the last guard
`UniqueConstraint(condition=...)` (partial unique): ≤1 ACTIVE task per
(stage_record, worker) while cancelled history accumulates.
`CheckConstraint`: `finalized ⇒ settled_at`, `recovered ≤ outstanding`,
XOR exactly-one-parent. App bug ho bhi jaye, DB jhooth store nahi karega.
(Django 5.0.1 note: partial unique uses `condition=`, checks use `check=`.)

## Managers
`.objects` = default; `.active` (ActiveManager) = opt-in soft-delete filter.
Default ko override NAHI kiya — warna rows chupke se gayab dikhte.

## Frozen snapshot vs live SUM (the project's signature pattern)
Snapshot column = "us waqt kya tha" (expected_rate, processing_cost,
AddaSettlementItem) — write-once, kabhi recompute nahi.
Balance = "abhi kya hai" — HAMESHA ledger SUM. Dono mix karoge to ya audit
tootega ya accuracy.

## Migrations
Schema changes = migration files (append-only history of the schema itself).
Data migrations backfill ONLY known facts (owner rule) — states kabhi invent
nahi karte. Destructive ones get clone rehearsal first.

## No signals (ADR-0001)
`inventory/signals.py` is a tombstone. Everything happens explicitly inside
service functions — "yeh kab chala?" ka jawab hamesha stack trace deta hai.
