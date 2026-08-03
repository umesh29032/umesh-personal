---
id: s4-phase3-receipt-2026-06-14
type: receipt
status: active
owner: append-only
scope: campaign/audit evidence
anchors: —
verified: 2026-07-13
---

# S4 Phase 3 Design Receipt — WorkerStageAllocation + pool draw-down (2026-06-14)

Governed by [S4_DESIGN_CORRECTION_ADDENDUM](S4_DESIGN_CORRECTION_ADDENDUM_2026_06_14.md)
(C1/C2/D2/D3, Option B) + [S4_IMPLEMENTATION_RECEIPT](S4_IMPLEMENTATION_RECEIPT_2026_06_14.md).
**Design receipt only — no code, no migration authored yet.** Service + tests only (no UI).
`ENFORCE_ALLOCATION_BOUND` stays **False**. Migration cursor: production at **0041** → Phase 3
= **0042**.

## Where WSA sits (the mental model)
The pool flows stage→stage. `WorkerStageAllocation` (WSA) belongs to the **CONSUMING**
stage and draws a slice of the **upstream pool source's** good:
```
available(consuming stage S, dims) =
    pool_good(source) aggregated to S's grain [dims]
  + recovered_alter(source, dims)        # M-7 accessor, returns 0 until Rework ships
  − Σ non-voided WorkerStageAllocation(S, dims)
```
- **source** = the nearest preceding stage in the same Adda's flow (by `workflow_stage.order`)
  with `allocation_dimensions != NONE` — resolved by `_upstream_pool_source(S)`, skipping
  pre-piece NONE stages. (For a future `cutting → stitching` flow, stitching's source = cutting.)
- **`pool_good(source)`** is the Phase-2 handler-dispatched read (cutting→APSCPB, downstream→SPS).
- **Grain aggregation:** monotonicity (D1) guarantees `grain(S) ≤ grain(source)`, so the source
  good only ever **coarsens** down to S's grain (sum the finer dims). `QUANTITY` S drawing from
  `COLOR_SIZE` cutting → available = Σ over all (colour,size) of cutting good. Never re-fines.

## 1. WorkerStageAllocation lifecycle (create · consume · void · reallocate)
- **CREATE (allocate):** management allocates worker W a `qty` slice of stage S's available
  upstream pool at S's grain → `allocation_service.allocate(consuming_sr, worker, dims, qty,
  actor)`. Under the D2 advisory lock it computes `available` and **refuses if `qty > available`**
  (pool integrity — always on, independent of `ENFORCE_ALLOCATION_BOUND`), else writes one WSA
  row. Pre-work, **no money**.
- **CONSUME:** worker files `WorkerStageContribution` under S. The bound `Σ(good+alter+missing)
  ≤ Σ allocated(W, S, dims)` is enforced at **complete** in **Phase 4** (gated by
  `ENFORCE_ALLOCATION_BOUND`, default False). Phase 3 only records the allocation; it does not
  yet gate completion.
- **VOID:** `void_allocation(wsa, actor)` sets `voided_at` (never deletes — append-only,
  owner data-history rule). Its qty leaves the `Σ non-voided` term → the pool is credited back
  automatically (§2).
- **REALLOCATE:** void the old WSA + `allocate` a new one. Both happen under the advisory lock;
  the freed qty is immediately re-drawable. No edit-in-place.

## 2. Pool-credit-back on void / reassignment
`available` is **derived**, never stored — it subtracts only **non-voided** WSA. Voiding a row
therefore **returns its qty to `available` with no compensating write** (the snapshot/source
good is immutable; allocations are the moving ledger). Correctness is guaranteed by computing
`available` and inserting/voiding **inside the same D2 advisory-lock-held transaction**, so a
concurrent allocate always sees the committed void. No double-credit, no leak.

## 3. Reopen interaction with non-voided allocations (M-4 contract)
Reopening the **source** stage (e.g. cutting) changes its `pool_good` (APSCPB cleared on cutting
reopen; SPS cleared via `clear_stage_pool`), which would **invalidate downstream allocations**
drawn against it. So the **Era-A reopen guard (Phase 5)** must **REFUSE** upstream reopen while a
**non-voided downstream `WorkerStageAllocation`** exists (alongside the existing settled-block and
the downstream good/alter/missing condition). Phase 3 creates the WSA data the Phase-5 guard
checks; the relationship is defined here, the guard ships in Phase 5. Reverse-first: void the
downstream allocations (audited) before reopening the source.

## 4. Concurrency proof — simultaneous allocations, same pool dim
Two allocations against the same `(source, colour, size)` race:
- Both call `pg_advisory_xact_lock(classid=<POOL>, hash(source_stage_record_id, color_id,
  size_id))`. **Distinct `classid` from settlement's `5374`** → the two lock domains share no lock
  object → no cross-domain deadlock; D2's "never lock `AddaStageRecord`" holds.
- The lock **serializes** the read-compute-write: TX-A acquires, reads available=100, writes
  WSA(60), commits, releases. TX-B blocks on the lock, then reads available=**40** (sees A's
  committed row), requests 50 → **refused** (50 > 40). **No over-allocation possible.**
- The advisory lock (not a row lock) is correct here because the source good is immutable
  (read lock-free) and the thing needing serialization is the *aggregate* `Σ allocations` for the
  dim — which has no single row to lock (APSCPB is multi-row; WSA rows don't exist yet at first
  draw). Multi-dim allocates lock dims in deterministic `(color_id, size_id)` order.
- Test strategy: Django tests can't truly parallelize, so the proof is (a) assert the advisory
  lock is taken with the right key, and (b) a sequential `allocate(60)` then `allocate(50)` on a
  pool of 100 → second **refused**. The serialization argument covers the true race.

## 5. Future compatibility (stitching + real piece-consuming stages)
When a real consumer (e.g. stitching) is added — **no allocation-service code change**:
- Declare stitching's `allocation_dimensions` (its OUTPUT grain) + order after cutting; flow-edit
  monotonicity (D1) enforces `grain(stitching) ≤ grain(cutting)`.
- `_upstream_pool_source(stitching)` resolves to cutting (nearest non-NONE upstream); `pool_good`
  reads cutting's APSCPB; the aggregation coarsens to stitching's grain.
- Stitching also **produces** a pool for the next stage (packing): base `materialize_pool` writes
  its `StagePoolSnapshot` at complete; `pool_good(stitching)` reads SPS. All via the existing
  Phase-2 strategy.
- Recovered-alter / found-missing from a future Rework/Missing module top up the source pool via
  the **stable accessors** (`recovered_alter`/`found_missing`, signatures defined now, return 0)
  → a populate-not-redesign (M-7). A recovered piece = a pool top-up → a new downstream allocation.

## 6. 🔒 WorkerStageAllocation is production-truth ONLY — never money-bearing
Explicit confirmation + how it's guaranteed:
- WSA carries **no** rate, no earning, no ledger reference, no settlement FK. Fields are
  capacity-only: `stage_record`, `worker`, `color?`, `size?`, `allocated_quantity`, `created_by`,
  `voided_at`. Lives in the **production** app (expense gains no new writer).
- Money still appears **only at settlement** (`StageWorkAssignment`, born at finalize, from
  `settlement_quantity` (= good) × frozen `expected_rate`). `finalize` never reads WSA; a WSA void
  touches no money; `reverse_adda_settlement` voids the SWA only, WSA untouched.
- A test asserts WSA has no money fields and the **golden ₹225 chain is byte-identical** (Phase 3
  adds nothing to the settlement path).

---

## Enumerations

**New model:** `WorkerStageAllocation` (production app) — capacity/bound only, append-only
(void-not-delete), no money. Migration **production 0042** (CreateModel + check
`allocated_quantity > 0` + index `(stage_record, worker)`; partial-index on non-voided optional).

**New service:** `allocation_service.py` (production) — `allocate(consuming_sr, worker, dims, qty,
actor)`, `void_allocation(wsa, actor)`, `available(consuming_sr, dims)` (read), internal
`_upstream_pool_source(consuming_sr)`, `_aggregate_to_grain(...)`, and the M-7 stubs
`recovered_alter(...)`/`found_missing(...)` → `Decimal('0')`.

**Lock points:** advisory `pg_advisory_xact_lock(<POOL classid>, hash(source_sr_id, color_id,
size_id))` per dim, deterministic multi-dim order; **never** `AddaStageRecord`; distinct classid
from settlement `5374`. Domain order unchanged: `WorkerStageTask → AddaStageRoleRate →
[advisory pool lock] → WorkerStageAllocation → WorkerStageContribution`; disjoint from settlement.

**Production-truth invariants (add to S4 set):** I-4 no-over-allocation (under the advisory lock);
I-6 append-only + reverse-first (WSA voided not deleted; upstream reopen refused while non-voided
WSA exist — guard in Phase 5); I-7 WSA carries no money; I-8 recovered/found accessors → 0.

**Settlement-boundary guarantees:** finalize never reads/locks WSA; money = good × frozen rate;
SWA unchanged; golden ₹225 byte-identical; lock domains disjoint.

**Rollback:** additive + reversible — `git revert` + reverse migration drops WSA; production
reverts to Phase-2 state (pool readable, no allocations). No data stranded (S1–S3 truth untouched).
Allocate is inert in the current flow (no consumer stage) → reverting affects nothing live.

**Test strategy:** allocate-within-available · refuse-over-allocation · void-credits-back ·
reallocate · source-resolution (nearest upstream non-NONE) · grain-aggregation (QUANTITY draws
Σ over cutting colour/size) · concurrency (sequential over-allocation refused + advisory-lock
asserted) · WSA-no-money-fields · golden ₹225 byte-identical · migration-drift clean.

**DOCS-SYNC:** FILE_MAP, GUIDE (model + service rows), **NEW
`docs/LEARNING_2_0/CHOKEPOINTS/allocation_service.md`** (the pool draw-down chokepoint: lock,
invariants, source resolution), PENDING_BACKLOG (Phase 3 done-log), CLAUDE.md pointer, the design
addendum (mark Phase 3 implements D2/C2).

**NOT in Phase 3:** the complete-time bound enforcement (Phase 4, `ENFORCE_ALLOCATION_BOUND`); the
Era-A reopen guard + `clear_stage_pool` wiring (Phase 5).

---
**STOP — awaiting approval of this receipt before any Phase 3 code.** On approval I implement the
WSA model + `allocation_service` + tests (golden gate green) + DOCS-SYNC, then STOP for review
before Phase 4.
