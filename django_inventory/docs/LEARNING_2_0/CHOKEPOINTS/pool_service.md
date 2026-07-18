---
id: l2-chokepoints-pool-service
type: chokepoint
status: active
owner: handwritten
scope: pool_service (chokepoint)
anchors: —
verified: 2026-07-13
---

## TL;DR (2 min)
**HARDENING (2026-07-06, owner-approved):** (J-1) `materialize_stage_pool` now freezes
**Σ verified-else-good** (was Σ good) — verification is the final business truth, so the
next operation receives the manager-corrected number (same resolver rule as settlement,
computed with SQL `Coalesce(verified_quantity, good_quantity)`; still no money in the pool).
(H-2) `void_allocation` REFUSES once the worker's submitted production (Σ verified-else-good
+ alter + missing on the dim) would no longer fit the allocation left after the void — the
explicit correction flow is Report Review (`set_verified_quantity`), then void. Void before
any report stays free.

**OP-1 (2026-07-05): the pool has its FIRST LIVE CONSUMER.** `materialize_stage_pool` is
wired into `advance_to_next_stage` (the one complete funnel — cutting no-op, NONE-grain 0
rows); the generic stage panel's management "Split the work" section calls
`allocate`/`void_allocation` via `generic-stage-allocate`/`-alloc-void`; the worker report
schema scopes choice options to `WorkerStageAllocation` dims (blind reporting — labels
only, never quantities); `upstream_pool_source` is the public read alias. Grain is
flow-editable ("Work split" select on the flow editor → `set_stage_grain`).

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

**Verified-else-good (owner rule 2026-07-06):** the pool a stage OFFERS downstream is
`Coalesce(verified_quantity, good_quantity)` per contribution — identical resolver to
`expense.services.settlement_resolver.settlement_quantity`, applied independently in each
concern (pool = production capacity; settlement = money). A manager correction in Report
Review therefore flows to BOTH the next operation's pool and the money, from one truth.
`void_allocation` refuses after production no longer fits the post-void allocation (H-2).

**Key functions:**
- *Snapshot:* `pool_good(sr)` (handler-dispatched: cutting→APSCPB, downstream→SPS) ·
  `materialize_stage_pool(sr)` (write-once at complete; cutting no-op) · `clear_stage_pool(sr)`
  (reopen clears+refreezes).
- *Draw-down:* `allocate(consuming_sr, worker, *, qty, actor, color_id, size_id)` (management;
  refuse if `qty > available`; no money) · `void_allocation(wsa, *, actor)` (append-only; qty
  returns) · `available(consuming_sr, dims)` · `_upstream_pool_source` (nearest non-NONE
  upstream) · `recovered_alter`/`found_missing` (M-7 stubs → 0).
- *Bound (Phase 4):* `worker_allocated(sr, worker, color, size)` = Σ active (non-voided) WSA
  for that worker/dims; `check_allocation_bound(task)` (called by `complete_worker_task`) —
  refuses if `Σ(good+alter+missing+damaged) > Σ active allocated` per REPORTED dimension (under-
  consume passes; unallocated reported dim fails). Gated by `ENFORCE_ALLOCATION_BOUND`
  (default False); pool-participant stages only; reads NO verified/settlement/rate/cost.
- *Rollout safety (S5/S4-005):* `preview_bound_violations(adda=None)` (over_bound + unallocated
  completions — the pre-flip audit, behind `preview_allocation_bound` mgmt command) +
  `bound_soft_warning(task)` (non-blocking worker-report hint, works with the flag OFF). See the
  [enforcement rollout runbook](../../ENFORCEMENT_ROLLOUT_RUNBOOK_2026_06_14.md).

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

## GAP-1 fix (production-hardening 2026-07-11, ratified formula)
- `_upstream_pool_sources()` (plural) = EVERY lane's stage record at the
  nearest upstream pool-participant ORDER — the frozen "Σ-over-streams read"
  (lifecycle §2) finally implemented; `.first()` had been picking ONE
  id-lucky lane (LOWER-002: available(S)=0 while recut pieces 81–82 existed;
  NKS: 160 of 600 visible). `_upstream_pool_source` (singular) retained as
  the deterministic first source (panel label + allocate lock anchor).
- `available()` = Σ pool_good over ALL sources ↓grain − draws, and for
  MULTI-COMPONENT products additionally capped at **garment-equivalent sets
  per SIZE**: min over mandatory components of (Σ breakup across lanes ÷
  pieces-per-garment) − Σ allocations at that size, every colour (a garment
  spans colours — cloth colour is a component attribute; BUNDLE review Q4).
  Sewing hears 45 sets, never 143 pieces.
- Mandatory-ness crosses the ADR-H wall via **registry #6**:
  `MANDATORY_PATTERNS_PROVIDER` ← patterns_ai
  `mandatory_patterns_provider.mandatory_pattern_ids_for_product` (a pattern
  is mandatory when ANY of its Blueprint pieces is non-optional — mirror of
  lane blocking). Provider absent / failing / <2 mandatory patterns ⇒ legacy
  per-dim math (fail-open; single-component products byte-identical — min
  over one pattern IS its piece count).
- Capacity only, as ever (S4 decoupling contract untouched): no verified /
  settlement / rate / cost reads added. Tests: `test_gap1_pool` (Σ-across-
  lanes · sets cap w/ ÷2 multiples · optional excluded · size-grain draw-down
  · fail-open) + S4 suite green. Live re-probe: LOWER-002 S→2.00 (was 0);
  SHA-001 → 40 sets both colours across 5 lanes.
