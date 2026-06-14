## TL;DR (2 min)
THE piece-pool chokepoint (S4). Single writer of `StagePoolSnapshot` (the frozen good a
stage offers) AND `WorkerStageAllocation` (a worker's allocated slice), and the single reader
of pool good. Cutting's good = `AddaProductSizeColorPieceBreakdown` (single source of truth,
never duplicated); downstream stages use `StagePoolSnapshot`. **Production-truth ONLY — carries
NO money; never touches costing/earning/rate/settlement.** Named `pool_service` (NOT
`allocation_service`) because `expense.services.allocation_service` is the unrelated legacy
era-A earning path.

# Chokepoint: pool_service (piece-pool: snapshot + draw-down)

File: `config/production/services/pool_service.py`

**Why exists:** one door for "how much good each stage offers" + "who is allocated how much of
it," so the pool can never be over-drawn — paid-more-than-produced is prevented at the *source*,
by construction.

**Owns / writes:** `StagePoolSnapshot`, `WorkerStageAllocation` (both production app). Reads the
pool good via the stage HANDLER strategy. Writes NOTHING in expense.

**Key functions:**
- *Snapshot:* `pool_good(sr)` (handler-dispatched: cutting→APSCPB, downstream→SPS) ·
  `materialize_stage_pool(sr)` (write-once at complete; cutting no-op) · `clear_stage_pool(sr)`
  (reopen clears+refreezes).
- *Draw-down:* `allocate(consuming_sr, worker, *, qty, actor, color_id, size_id)` (management;
  refuse if `qty > available`; no money) · `void_allocation(wsa, *, actor)` (append-only; qty
  returns) · `available(consuming_sr, dims)` · `_upstream_pool_source` (nearest non-NONE
  upstream) · `recovered_alter`/`found_missing` (M-7 stubs → 0).

**Lock (D2):** `pg_advisory_xact_lock(_POOL_LOCK_CLASS=5375, objid(source_sr, color, size))` —
TWO-INT advisory namespace, provably disjoint from settlement's single-bigint
`pg_advisory_xact_lock(5374)`. No shared lock object → no deadlock. **Never locks
`AddaStageRecord`.** Deterministic `(color_id, size_id)` order for multi-dim.

**Invariants:** I-3 snapshot immutable write-once; I-4 no over-allocation (under the advisory
lock); I-6 append-only + reverse-first (void not delete; non-voided downstream WSA blocks
upstream source reopen — Era-A guard ships Phase 5); I-7 WSA carries NO money; I-8 recovered/
found accessors → 0.

**🔒 Decoupling contract (owner 2026-06-14):** must NOT import/call `cost_service` /
`stage_rate_service` / settlement; `allocated_quantity` must NOT feed earning/rate/costing/
settlement math. Costing-method behaviour (`per_layer`/`fixed_cost`/`per_piece`) lives on
`WorkflowStage.cost_method` + `cost_service`, independent of allocation. Guarded by
`test_s4_allocation.NoMoneyDecouplingTests`.

**What breaks if bypassed:** a second writer (or money on WSA) = over-drawn pool / allocation
entangled with pay = the paid-more-than-produced failure the foundation exists to prevent.

**Current-flow note:** cutting is the only piece stage and nothing downstream consumes it →
SPS materialises no rows + `allocate` is unreached in the live 4-stage flow (source, no
consumer). Built ahead of future piece-consuming stages (stitching); exercised via tests.

Design: docs/S4_PHASE3_RECEIPT_2026_06_14.md + docs/S4_DESIGN_CORRECTION_ADDENDUM_2026_06_14.md
(C1/C2/D2/D3, Option B). (Distinct from `allocation_service.md` = the legacy expense era-A path.)
