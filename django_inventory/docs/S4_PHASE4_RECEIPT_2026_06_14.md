# S4 Phase 4 Design Receipt — complete-time allocation bound (2026-06-14)

Governed by [S4_DESIGN_CORRECTION_ADDENDUM](S4_DESIGN_CORRECTION_ADDENDUM_2026_06_14.md) +
[S4_IMPLEMENTATION_RECEIPT](S4_IMPLEMENTATION_RECEIPT_2026_06_14.md). **Design receipt only —
no code.** Service + tests only. Gated by **`ENFORCE_ALLOCATION_BOUND` (default `False`)**.
Migration cursor: production at **0042** → Phase 4 adds **no schema** (a setting + service
logic only).

## 🔒 The bound rule (owner-locked, explicit)

At `complete_worker_task`, for a worker W completing their task on a pool-participant stage
S, **per grain dimension `(color, size)`**:
```
Σ (good_quantity + alter_quantity + missing_quantity)         ← W's contributions on S at (c,s)
        ≤
Σ active (non-voided) WorkerStageAllocation.allocated_quantity ← for (W, S, c, s)
```

### What the bound validates against — and what it NEVER touches
- **Validates against ONLY:** `WorkerStageContribution.{good_quantity, alter_quantity,
  missing_quantity}` (production observations) on the LHS, and
  `WorkerStageAllocation.allocated_quantity` (production capacity) on the RHS.
- **NEVER against:** `verified_quantity`, `settlement_quantity`, `expected_rate`,
  `expected_earning`, any rate, any `cost_method`, or any money. **It is a production-
  CAPACITY rule only.** (`verified_quantity` is a settlement-time management correction —
  irrelevant to capacity; the bound deliberately ignores it.) No costing/earning/rate/
  settlement code is imported or read by the bound — same decoupling contract as
  `pool_service` (Phase 3), guarded by a test.

### 🔒 "Total active allocated", not a single row (owner-locked, explicit)
The RHS is the **SUM of ALL non-voided `WorkerStageAllocation` rows** for `(worker,
stage_record, color, size)` — **never a single allocation row**. Consequences:
- **Multiple active allocations** (a worker allocated in several tranches) → they **sum**.
- **Partial voids** → each voided row leaves the sum; the bound uses the **remaining**
  active total.
- **Reallocation history** (void old + create new) → the sum reflects the **current**
  capacity; superseded (voided) rows never count.
- One read: `Σ allocated_quantity WHERE stage_record=S AND worker=W AND color=c AND size=s
  AND voided_at IS NULL`. This is the same `_allocated_for`-shaped sum used by the pool's
  `available` (Phase 3), now per-worker.

## Scope + gating
- **Applies ONLY to pool-participant stages** (`allocation_dimensions != NONE`). A `NONE`
  stage (layering, cutting_pattern, barcode) is **never** bounded — its workers self-report
  freely (their pay is `cost_method`-driven, independent). Cutting (COLOR_SIZE) never reaches
  this code (it's a workspace, not a self-report stage).
- **`ENFORCE_ALLOCATION_BOUND` (default `False`)** — when `False`, `complete_worker_task`
  behaves **exactly** as today (no bound; the kill-switch + back-compat for every existing
  flow). When `True`, the bound is enforced on pool-participant stages.
- **Strict model** (Open deferred): under `ENFORCE=True`, a pool-stage contribution at a
  dimension with **no covering active allocation** (`allocated = 0`) and reported `> 0` is
  **refused** (you must be allocated before you can complete that work).
- **Per dimension, independently:** a worker who reports `(red,M)` and `(red,L)` is checked
  against their `(red,M)` and `(red,L)` allocations separately; an unallocated dimension
  reported against → refused.

## Where it runs + lock
- In `complete_worker_task`, after the contributions' good/alter/missing are known, before
  the task is marked COMPLETED. Reuses a `pool_service` helper (e.g. `worker_allocated(
  stage_record, worker, color_id, size_id)` + a `check_allocation_bound(task)`); the bound
  logic lives in `pool_service` (production-truth domain), called from the chokepoint.
- **Lock:** the check acquires the **D2 advisory pool lock** `(source_sr, dims)` (the same
  lock `allocate`/`void` use) so the bound is evaluated against a consistent active-allocation
  total even under a concurrent allocate/void. Lock order unchanged: task → AddaStageRoleRate
  → [advisory pool lock] → WorkerStageContribution; never `AddaStageRecord`; disjoint from
  settlement. (Semantics: the bound is judged at complete-time; a *later* void is a separate
  correction handled reverse-first, never retroactive.)
- **Optional soft-warn at draft** (`save_draft_contributions`): a non-blocking over-allocation
  hint (addendum M decision). The HARD gate is at complete. I will include the soft-warn only
  if it stays trivial; otherwise note it as a tiny follow-on.

## Enumerations
- **New model / migration:** NONE (Phase 4 is logic + a setting).
- **Setting:** `ENFORCE_ALLOCATION_BOUND = False` in `config/config/settings/base.py`
  (documented as the Strict-bound kill-switch; env-overridable; mirrors
  `LEDGER_CREDIT_AT_ALLOCATION`).
- **Service:** `pool_service.worker_allocated(...)` + `check_allocation_bound(task)`;
  `worker_task_service.complete_worker_task` calls the latter (gated). No new writer.
- **Invariant added:** I-5 `Σ(good+alter+missing) per (W,S,dims) ≤ Σ active allocated` —
  hard-gated at complete (when `ENFORCE=True`); production-capacity only.
- **Settlement-boundary:** unchanged — the bound reads no money; settlement still = good ×
  frozen rate; golden ₹225 byte-identical.
- **Rollback:** flip `ENFORCE_ALLOCATION_BOUND=False` → instant disable, no migration. Code
  revert is additive. Inert in the current flow regardless (no pool-consuming self-report
  stage).
- **Test strategy:** with a synthetic pool-consuming stage (cutting source → QUANTITY/
  COLOR_SIZE consumer with WSA) + worker contributions —
  - `ENFORCE=False` → completes regardless of allocation (back-compat). 
  - `ENFORCE=True`: within bound → completes; `good+alter+missing > Σ active allocated` →
    refused; **multiple active allocations sum**; **partial void reduces the total**;
    **reallocation (void+new) uses current active**; `allocated=0` + reported>0 → refused;
    per-(color,size) independence; NONE stage → never bounded.
  - **Decoupling proof:** a contribution with `verified_quantity` set to a value that *would*
    flip the result if used → bound result **unchanged** (uses good+alter+missing only);
    bound never reads rate/earning/cost.
  - Golden ₹225 byte-identical (the bound touches no settlement path).
- **DOCS-SYNC:** `pool_service.md` chokepoint (add the bound + I-5), `worker_task_service.md`
  chokepoint (complete-time bound), FILE_MAP, PENDING_BACKLOG, CLAUDE.md, settings doc.

**NOT in Phase 4:** Era-A reopen guard + `clear_stage_pool` wiring (Phase 5).

---
**STOP — awaiting approval before any Phase 4 code.** On approval: `ENFORCE_ALLOCATION_BOUND`
setting + the gated bound in `complete_worker_task` (via `pool_service`) + tests (golden gate)
+ DOCS-SYNC, then STOP for review before Phase 5.
