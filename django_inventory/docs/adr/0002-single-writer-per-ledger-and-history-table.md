# ADR 0002 — Exactly one writer service per ledger / audit table

**Status:** Accepted (CLAUDE.md rule #5)

## Context
Ledger and audit tables are the financial / provenance source of truth. If more than one
code path can `INSERT`/`UPDATE` them, invariants (immutability, balance = Σcredit − Σdebit,
one reversal per entry) can be violated from a forgotten path.

## Decision
Each ledger/audit table has **exactly one writer service**:
- `WorkerLedgerEntry` → `expense.services.ledger_service` (append-only; corrections are a
  REVERSAL row, never an UPDATE/DELETE; amount always positive, direction in `entry_type`).
- `StageWorkAssignment` → `allocation_service`; `WorkerAdvance` → `advance_service`;
  `PayrollSettlement`(+`Item`) → `settlement_service`.
- The `*History` tables (`AddaHistory` / `ClothRollHistory` / `ProductHistory`) →
  `tracking.services.history_service.log_*` only.
- Balances and outstanding amounts are **derived live**, never stored.

## Consequences
- Concurrency safety lives in one place per table (advisory locks, `select_for_update`,
  unique-constraint backstops like `uniq_one_reversal_per_entry`).
- Reversal-netting semantics are defined once; reads can't inflate totals.
- No signals / no `save()` writes to these tables (see [ADR 0001](0001-service-layer-owns-writes-no-signals.md)).
