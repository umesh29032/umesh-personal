# S4 Implementation Design Receipt (2026-06-14)

Governed by [S4_DESIGN_CORRECTION_ADDENDUM](S4_DESIGN_CORRECTION_ADDENDUM_2026_06_14.md)
(C1/C2/H1/D1-D3 + reopen) + [PRE_S1_DESIGN_ADDENDUM](PRE_S1_DESIGN_ADDENDUM.md) +
[MASTER_PLAN_V2](IMPLEMENTATION_MASTER_PLAN_V2.md). **Design receipt only — no code.**
Migration cursor: production at **0039** (S4 starts 0040); expense at **0010** (untouched).
Golden ₹225 = merge gate on every phase. Build order is the 6 phases below; each is a
STOP-able commit point.

## Phase order (your sequence)
1. **D1** — `allocation_dimensions` + grain monotonicity (foundation; everything keys off it)
2. **StagePoolSnapshot** materialization (the immutable good anchor)
3. **WorkerStageAllocation** + pool draw-down (the moving ledger)
4. **Crystallization-time allocation enforcement** (the bound at complete)
5. **Era-A reopen guard** (downstream-consumer refusal)

(5 build phases; "6" in the brief = D1 split conceptually from its monotonicity check, kept
together here.)

---

## 1. All new models / schema changes

| # | Entity | Kind | App | Phase | Holds (conceptual — NOT field DDL) |
|---|---|---|---|---|---|
| M0 | `WorkflowStage.allocation_dimensions` | **field** on existing model | production | 1 | enum `{COLOR_SIZE, QUANTITY}`, default `QUANTITY` |
| M1 | `StagePoolSnapshot` | **new model** | production | 2 | `(stage_record, color?, size?)` + frozen `good` + `materialized_at`. Immutable, write-once. `available` is **derived** (not stored). |
| M2 | `WorkerStageAllocation` | **new model** | production | 3 | `(stage_record, worker, color?, size?)` + `allocated_quantity` + `created_by` + `voided_at`. **No money.** Append-only (void, never delete). |
| M3 | enforcement rollout lever | **setting** (not a model) | settings | 4 | `ENFORCE_ALLOCATION_BOUND` (default **False** during rollout, mirrors `LEDGER_CREDIT_AT_ALLOCATION`) — gates Strict enforcement so existing flows don't break before allocation entry exists. |

No new expense models. SWA unchanged. `WorkerStageContribution` unchanged (S3 columns stand).

## 2. All migrations (each MT-1 backup-gated; batched where data-touching)

| Migration | Phase | Operations |
|---|---|---|
| **production 0040** | 1 | AddField `WorkflowStage.allocation_dimensions` (default `QUANTITY`) + **data-seed** RunPython: COLOR_SIZE for stages whose handler captures color/size (cutting), QUANTITY for the rest. Reverse = drop. |
| **production 0041** | 2 | CreateModel `StagePoolSnapshot` + unique `(stage_record, color, size)` + check `good ≥ 0`. **No backfill** of historical Addas (pool only governs forward allocation; completed Addas never allocate). |
| **production 0042** | 3 | CreateModel `WorkerStageAllocation` + check `allocated_quantity > 0` + index `(stage_record, worker)`. |
| (none) | 4 | Enforcement is service logic + a settings flag — no schema. |
| (none) | 5 | Reopen guard is service logic — no schema. |

`makemigrations --check` must show no drift after each; hand-author 0040's data-seed
(mirrors the S3 RC-3 backfill pattern).

## 3. All lock points

**Two DISJOINT domains (the D2 guarantee — they share no row → no deadlock):**

- **Settlement domain (UNCHANGED):** advisory xact lock → `AddaSettlement` → `AddaStageRecord`
  → `WorkerProfile` → `WorkerAdvance`. Never touches SPS/WSA.
- **Production-allocation domain (S4):** `WorkerStageTask` → `AddaStageRoleRate` →
  **`StagePoolSnapshot`** → **`WorkerStageAllocation`** → `WorkerStageContribution`.
  **NEVER locks `AddaStageRecord`** (the D2 rule — lock the SPS row by `stage_record_id`,
  not the stage record).

Specific acquisitions:
- **Materialize (phase 2):** writes SPS rows inside the existing **stage-completion** atomic
  transaction. No new cross-row lock (the stage record is already the caller's context).
- **Draw-down / allocate (phase 3):** `select_for_update` the `StagePoolSnapshot` row(s) by
  `(stage_record_id, color, size)`; multiple dims locked in **deterministic order
  (color_id, then size_id)** to avoid intra-domain deadlock between concurrent allocates.
  `available` is computed under that lock; WSA insert + (implicit) draw-down commit together.
- **Bound check (phase 4):** `complete_worker_task` extends its existing lock chain (task →
  AddaStageRoleRate) with the worker's `WorkerStageAllocation` rows (`select_for_update`) +
  the relevant SPS row — same domain order; still never locks `AddaStageRecord`.
- **Reopen (phase 5):** existing SR `select_for_update`; the downstream-consumer scan is a
  **read** (runs before mutate) — no new lock.

`finalize` reads frozen `good` + `expected_rate` only → never enters the production-allocation
domain → the two domains never interleave.

## 4. All production-truth invariants

- **I-1 (grain monotonicity):** declared grain may only **coarsen** downstream
  (`COLOR_SIZE → QUANTITY` ok; `QUANTITY → COLOR_SIZE` rejected). Enforced at flow-edit.
- **I-2 (grain capture):** a `COLOR_SIZE` stage **requires** color+size on every contribution
  (chokepoint-enforced); a `QUANTITY` stage keeps them NULL. Legacy rows grandfathered +
  audited, never back-invented (H1).
- **I-3 (snapshot truth):** `StagePoolSnapshot.good = Σ WorkerStageContribution.good_quantity`
  at the producing stage's grain; **write-once** at stage-complete; immutable until reopen
  clears+refreezes. Source is worker good, **never `cost_quantity_snapshot`** (D3).
- **I-4 (no over-allocation):** `Σ non-voided WorkerStageAllocation(stage, dims) ≤
  StagePoolSnapshot.good(dims) + recovered_alter(dims)` — checked under the SPS row lock.
- **I-5 (bound):** `Σ (good+alter+missing)` for `(worker, dims)` `≤ Σ allocated(worker, dims)`
  — hard-gate at **complete**, soft-warn at draft (Strict model; gated by
  `ENFORCE_ALLOCATION_BOUND`).
- **I-6 (append-only + reverse-first):** WSA is voided, never deleted; upstream reopen is
  refused while a downstream consumer (WSA / good-alter-missing contribution / future
  AlterCase) exists.
- **I-7 (no money in production):** `WorkerStageAllocation` carries no rate/earning/ledger.
- **I-8 (accessor stubs):** `recovered_alter(stage, dims)` / `found_missing(stage, dims)`
  return **0** until Rework/Missing ships (M-7 contract) — defined now, populate later.

## 5. All settlement-boundary guarantees

- `finalize_adda_settlement` **never reads or locks** `StagePoolSnapshot` or
  `WorkerStageAllocation`. Settlement money still derives from `settlement_quantity` (= good)
  × frozen `expected_rate`.
- `StageWorkAssignment` (settlement earning line) is **unchanged** — still born at finalize.
- WSA void / pool credit changes touch **no money**; `reverse_adda_settlement` voids the SWA
  only — the WSA (production allocation) is untouched.
- **Golden ₹225 supersede chain byte-identical** on every S4 phase (S4 adds nothing to the
  settlement path). This is the merge gate.
- The two lock domains stay disjoint → settlement concurrency behavior unchanged.

## 6. Rollback strategy

- **Phase-additive + reversible.** Each phase = its own commit; revert = `git revert` + the
  reverse migration (drop field / drop model). Production reverts to S3 behavior (no
  allocation) with nothing stranded — S3's good/reported are untouched.
- **Phase 4 is flag-gated:** `ENFORCE_ALLOCATION_BOUND=False` (default) → `complete` behaves
  exactly as pre-S4 (no bound check) → instant disable with **no migration**, even after
  deploy. This is the live kill-switch for the one behavior change to the chokepoint.
- **No irreversible step in S4** (unlike S6's column drop). Snapshots/allocations are forward
  data; dropping them loses allocation history but not production/settlement truth.
- Golden gate per phase guarantees a revert never desyncs money.

## 7. Test strategy

- **Per phase (unit):**
  - P1: monotonicity accept/reject at flow-edit; grain seed correctness; default QUANTITY.
  - P2: materialize at stage-complete (COLOR_SIZE grouped + QUANTITY scalar); `good = Σ good`;
    reopen clears+refreezes; write-once idempotence.
  - P3: allocate within pool; **refuse over-allocation**; void credits the pool back;
    accessor stubs return 0; WSA has no money fields.
  - P4: bound accept/refuse at complete; soft-warn at draft; Strict requires allocation;
    **flag off ⇒ no enforcement (back-compat)**.
  - P5: reopen refused with downstream WSA; refused with downstream good/alter/missing;
    allowed after void/reverse; uniform across all stages.
- **Concurrency:** two concurrent `allocate` on the same SPS row → serialized, no
  over-allocation (the I-4 race). Lock-order assertion: `complete` + `finalize` on the same
  Adda do not deadlock (disjoint domains).
- **Integration:** full Adda — cutting (COLOR_SIZE) → downstream (QUANTITY) → pool composes by
  aggregation → allocate → bounded report → settle. Asserts the pool ceiling = upstream good.
- **Golden ₹225 byte-identical** every phase (merge blocker).
- **Migration:** `makemigrations --check` no drift; apply on dev; MT-1 backup before prod.

## 8. DOCS-SYNC impact (per CLAUDE rule 12 — implementation incomplete until updated)

- `docs/LEARNING_2_0/APPS/production/FILE_MAP.md` — new models + the allocation service.
- `docs/apps/production/GUIDE.md` — model table rows (StagePoolSnapshot, WorkerStageAllocation,
  WorkflowStage.allocation_dimensions) + services row.
- **NEW** `docs/LEARNING_2_0/CHOKEPOINTS/allocation_service.md` — the pool draw-down chokepoint
  (sole writer of WSA + SPS draw-down; lock order; invariants I-3..I-7).
- `docs/LEARNING_2_0/CHOKEPOINTS/worker_task_service.md` — the complete-time bound (I-5).
- `_shared.reopen_stage_record` doc + comment — the unified downstream-consumer guard (I-6).
- `docs/ARCHITECTURE_V2.md` — allocation/pool model (production-truth, no money).
- `docs/PENDING_BACKLOG.md` — S4 phase done-log; `docs/PROJECT_KNOWLEDGE_MAP.md` truth-flow.
- `CLAUDE.md` — S4 pointer; `config/config/settings/base.py` — `ENFORCE_ALLOCATION_BOUND` doc.
- RBAC: if "allocate" is a new gated action, `docs/production/RBAC.md` + permission wiring.

## 9. Open decisions to confirm at approval (2)

1. **Allocation entry UI scope.** Your 6 steps are all backend (models → enforcement → guard).
   WSA still needs *some* entry point to create allocations. **Service + tests only now**
   (UI a follow-on, like the rate-correction split), or **a minimal manager allocation UI in
   S4**? (Recommend: service+tests first; UI as a scoped follow-on so the backend invariants
   land + soak before UI.)
2. **Strict enforcement rollout.** Confirm `ENFORCE_ALLOCATION_BOUND` default **False** with a
   per-stage/opt-in ramp (mirrors the ledger lever) — so existing flows keep completing until
   allocations actually exist. (Recommend: yes — it's the RC-5 floor-discipline safety + the
   rollback kill-switch.)

---
**STOP — awaiting approval of this receipt + the 2 decisions before any S4 code.** On
approval I implement **Phase 1 (D1)** first, as its own gated commit (golden gate green),
then STOP for review before Phase 2.
