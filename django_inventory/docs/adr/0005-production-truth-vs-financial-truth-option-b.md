# ADR 0005 — Production truth ≠ financial truth; ledger only at settlement (Option B)

**Status:** Accepted for the model; **settlement build (V2 §11) pending** — see
[docs/ARCHITECTURE_V2.md](../ARCHITECTURE_V2.md) §11 (🔒LOCKED) + [docs/archive/reviews/V2_1_REVIEW.md](../archive/reviews/V2_1_REVIEW.md).

## Context
A worker reporting their stage work (production truth) is **not** the same event as the
business deciding to pay them (financial truth). Coupling the two — crediting the money
ledger the moment work is reported/allocated — makes corrections, advances, and settlement
timing tangled, and bakes provisional numbers into the ledger.

## Decision (the worker-tracking layer — BUILT as V2-1a/1b/1c)
- **`WorkerStageTask`** = per-worker assignment lifecycle (assigned→in_progress→completed→
  [verified]/cancelled; ≤1 active per stage_record·worker; cancel never deletes — history is
  immutable). **`WorkerStageContribution`** = dimensional line (color/size/qty) under a task.
- It replaces the read-path of the old `AddaStageRecord.workers` M2M (the M2M is **dual-written**
  behind the `WORKER_TASK_DUAL_WRITE` flag until V2-1d drops it).
- On task complete, `expected_rate`/`expected_earning` are **frozen as visibility only** —
  **no `WorkerLedgerEntry` is written**. This is **Option B**: no ledger until settlement.

## Decision (the settlement layer — DESIGN-ONLY / LOCKED, not built)
- An **Adda-centric `AddaSettlement`** event books earnings + advance recovery at settlement.
  **Settlement ≠ payment**; recovery is owner-controlled per-advance (not auto-FIFO).
- Today (pre-§11) earnings still credit at allocation via `expense` — the documented gap.

## Consequences
- Production records can be corrected without rewriting money.
- Missing-Piece / Alter-Rework become first-class domains whose *summaries* feed settlement.
- The `expense.StageWorkAssignment` allocation edge is **transitional** (tagged
  `FUTURE-STAGE-REDESIGN`); V2 §11 repoints earnings to settlement and retires it.
