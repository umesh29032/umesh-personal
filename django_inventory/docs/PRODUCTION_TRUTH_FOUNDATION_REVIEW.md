# Production-Truth Foundation Review (design-first; NO implementation)

**Premise (owner, 2026-06-14):** B-1, A-5, B-3 are symptoms of one missing foundation. Three concepts must stay **separate**: **production truth** (quantity actually done — correct *by construction*), **expected earnings** (operational visibility), **settlement truth** (a later, policy-flexible business decision). Settlement must never compensate for bad production data.

All current-state claims below are code-verified. This review proposes a model; it locks nothing.

---

## The one-line diagnosis
Today the system stores **production truth and money on the same row** (`WorkerStageContribution` carries `reported_quantity` + `expected_rate` + `expected_earning`), the **quantity is unbounded** (only `>0`), the **rate freezes too late** (task-complete, from the live workflow), and **loss signals (missing/alter) don't exist until settlement** (manual, on `AddaSettlementItem`). The fix is a thin **allocation + production-truth-quantity layer** plus **Adda-frozen rates**, with earnings and settlement as *read models* over that truth.

---

## 1. Adda-level rate snapshots

**Current (verified):**
- Template rate = `WorkflowStage.cost_rate` (+ `cost_method`, `order`, `credits_workers`).
- `AddaStageRecord` has `cost_rate_snapshot` — but that is the **standard-cost** rate (role-independent, drives `processing_cost`), NOT the payable rate.
- Payable rate = `WorkerStageContribution.expected_rate`, frozen in `complete_worker_task` from `role_rate_for(ws,…) or ws.cost_rate` ([worker_task_service.py:216](config/production/services/worker_task_service.py#L216)) — i.e. at **task-complete**, from the **live** workflow.

**Gap:** no Adda-start payable-rate snapshot. A workflow rate edit **changes the rate** for any contribution that completes afterward on a still-in-progress Adda. No owner review/confirm of rates at Adda start.

**Recommended model:** new **`AddaStageRoleRate`** (or `AddaStagePayRate`) — grain `(adda_stage_record, role) → rate`, copied from the workflow at **Adda creation/start**, **owner-editable until the first task completes**, immutable after. `complete_worker_task` and settlement read THIS, not the live workflow. (Role grain is required — `role_rate_for` is already role-aware.)

**Migration impact:** additive table. Backfill **known facts only** (data-history rule): for historical Addas, derive each `(stage_record,role)` rate from existing `contribution.expected_rate` where present; otherwise the workflow rate at freeze time. Forward-only owner-confirm step for new Addas. No destructive change.

---

## 2. Worker quantity allocation model

**Current (verified):** assignment is **roster-only** — `set_stage_workers(stage_record, worker_ids)` creates one `WorkerStageTask` per worker; the model is explicitly *"NOT money, NOT quantity"* ([worker_task.py:29](config/production/models/worker_task.py#L29)). Color/size are **worker-picked at report time** ([worker_task.py:125](config/production/models/worker_task.py#L125)). A bundle-item allocation with remaining-tracking exists (`allocate_stage_work`/`item_allocation_summary`) but is the **era-A** path (LEVER-off since V2-3) and is bundle-grained, not a downstream color/size pool.

**Missing domain concepts:** (a) a worker↔(color,size,quantity) allocation; (b) a per-stage **available pool** by (color,size); (c) the monotonic-non-increase invariant across stages.

**Recommended allocation model:** new **`WorkerStageAllocation`** — grain `(stage_record, worker, color, size) → allocated_quantity`, `allocated_by`, timestamps. Sits **beside** `WorkerStageTask` (keep the task quantity-free per its design; the allocation is the quantity-bearing sibling). One task → many allocation rows (one per color/size slice).

**Available pool — DERIVE, don't store** (avoids a denormalized counter that drifts):
- First production stage: pool(color,size) = `AddaProductSizeColorPieceBreakdown` (cutting's frozen verified per-(size,color) counts — [cutting.py:495](config/production/models/cutting.py#L495)).
- Stage N: pool(color,size) = stage N-1's **good** output for that (color,size).
- Invariant enforced at allocation time: `Σ allocations(stage,color,size) ≤ pool(stage,color,size)`.

**Interaction with WorkerStageTask / WorkerStageContribution:**
- Task = access + lifecycle (unchanged).
- Allocation = the bound (new).
- Contribution = the report, now **validated against its allocation** (color/size taken FROM the allocation, not free-picked; quantity ≤ allocated).

**TM-1 impact:** TM-1 routes every capture mode (Manual/Barcode/Both) to `WorkerStageContribution` via the single-writer chokepoint. If allocation-bound + good/alter/missing aren't in the contribution model first, TM-1 bakes in the wrong shape (a barcode scan must also draw down an allocation). **This layer must precede TM-1.**

---

## 3. Allocation-bounded reporting

**Business rule:** worker never sees the max; backend rejects over-allocation.

**Recommended (server-authoritative):**
- The worker report form renders **their allocation rows** (color/size), quantity inputs **blank**. The allocated number is **never sent to the client**.
- `save_draft_contributions` / `complete_worker_task` validate per (worker,color,size): `good + alter + missing ≤ allocated`. Over → `ValidationError("Entered quantity exceeds your assigned work for Red/M")` (generic, no number echoed).
- Color/size must match an existing allocation for that worker (reject orphan rows).

**Architecture options considered:**
- **(A) Validate in the existing single-writer service** — recommended. One chokepoint already exists ([worker_task_service.py](config/production/services/worker_task_service.py)); add the bound there. Minimal surface, race-safe with `select_for_update` on allocations.
- (B) DB CheckConstraint — can't express "≤ a value in another table"; rejected.
- (C) Validate in the view — rejected (bypassable; violates service-layer-owns-writes rule 4).

---

## 4. Good / Alter / Missing reporting

**Not stages — reporting outcomes** (matches owner).

**Domain model:** the worker report becomes, per (color,size) allocation: **Good**, **Alter** (optional), **Missing** (optional), **Notes**. Invariant `good + alter + missing ≤ allocated`; each ≥ 0; good ≥ 0 (allow 0-good with alter/missing). Today only `reported_quantity` exists.

**Storage model:** extend `WorkerStageContribution` — keep `reported_quantity` as **Good** (back-compatible: existing rows had no alter/missing, so good = reported), add nullable `alter_quantity`, `missing_quantity` (default 0). Keep `verified_quantity` as the management override. This stays on the production-truth row (one place), separate from money.

**Future compatibility:**
- **Alter/Rework domain** consumes `alter_quantity > 0` contributions → a rework queue; reworked pieces re-enter the **same** pool (must be tracked as the same physical pieces — see edge cases).
- **Missing Pieces domain** consumes `missing_quantity > 0` → loss analytics + investigation. Missing reduces the downstream pool (implements "quantity may decrease, never increase").

---

## 5. Expected earnings vs settlement (separation of concerns)

**Current (already partly right):** `expected_earning` is frozen on the contribution as **visibility only** — Option B, **no ledger until settlement** ([worker_task.py:153](config/production/models/worker_task.py#L153)). Settlement is a separate event that writes the ledger. This separation **already exists and is good.**

**Refinements under the new model:**
- Expected earning = **good_quantity × Adda-frozen-rate** (rate from §1, quantity from §4). Stays visibility-only.
- Worker sees: quantity completed + expected earnings. Never settlement/payment until management settles.
- **Do NOT hardcode the settlement quantity rule.** Today `finalize` hardcodes `qty = verified ?? reported` ([adda_settlement_service.py:314](config/expense/services/adda_settlement_service.py#L314)). Extract a **`settlement_quantity(contribution, policy)` resolver** so the money-write is policy-agnostic (see §7). This is the single change that buys future flexibility without touching the ledger logic.

**Key principle preserved:** production truth (quantity) and expected earnings (qty×rate visibility) are read models; settlement is the only money-writer and stays a separate decision.

---

## 6. Stage-wise production-loss tracking

**Model as a READ-MODEL over production truth — no new accounting tables** (avoids distortion).
- Per stage, per (color,size): output = Σ good; missing = Σ missing; alter = Σ alter.
- Adda shrinkage = cutting total − last-stage good.
- The "Cutting 100 → Stitching 92 → … → Packing 85" view is a pure aggregation query over `WorkerStageContribution` (+ the cutting breakdown as the origin), ordered by `WorkflowStage.order`.

**Why no stored counters:** a denormalized per-stage-loss table would need sync on every report/correction/reversal — a drift bug waiting to happen. Derivation keeps **one source of truth** (the contributions) and matches the existing "processing_cost is a per-stage report, never a sum" philosophy. This becomes a Phase-H operational dashboard for free once good/alter/missing exist.

---

## 7. Future packing-based settlement (evaluate only)

**Goal:** keep architecture flexible for: pay-on-stage-output / pay-on-packed / pay-on-verified / hybrid — **without choosing now.**

**The flexibility hook:** the `settlement_quantity(contribution, policy)` resolver (§5). Policies become strategies:
- `stage_good` → contribution.good (allocation-bounded).
- `verified` → verified ?? good.
- `packed` → distribute the Adda's packed total back to contributions (needs an allocation/attribution rule).
- `hybrid` → e.g. min(good, packed-share).

**Risks / implications to flag now:**
- **Packed-based pay couples a worker's pay to downstream work.** A cutting worker paid on *packed* depends on stitching/finishing/packing done by others, and on later loss — an **attribution problem** + **delayed pay** (can't settle cutting until packing finishes). Document this before any owner picks "packed."
- **Attribution rule required:** packed total → per-worker share needs a defined allocation (pro-rata by good? by allocation?). No correct default; must be a policy input.
- **Settlement must remain idempotent/reversible** regardless of basis — the resolver changes the *quantity*, never the reverse/supersede machinery (which is already correct, Phase-B Part 6).
- **Keep production truth basis-independent:** good/alter/missing are recorded the same way no matter which settlement policy is later chosen — that's what makes multiple policies possible without re-collecting data.

---

## 8. Architecture recommendation

### 8.1 Domain model proposal
A 3-layer separation, each a clean boundary:
1. **Production-truth layer** — Allocation (the bound) → Contribution (good/alter/missing, ≤ allocation, color/size locked). Correct by construction. Immutable.
2. **Visibility layer** — Expected earnings = good × Adda-frozen-rate. Read-only, no money.
3. **Settlement layer** — policy resolver picks the settlement quantity; ledger writes are the only money. Unchanged machinery, pluggable quantity.

### 8.2 Architecture proposal
- Keep the single-writer chokepoint for contributions; **add the allocation bound there**.
- **Derive** pools and loss views (no stored counters).
- **Freeze rates per-Adda at start** (owner-confirmed); read frozen rates everywhere downstream.
- **Extract the settlement-quantity resolver** to decouple money from quantity policy.

### 8.3 Recommended data model (additive)
| Entity | Status | Key fields |
|--------|--------|-----------|
| `AddaStageRoleRate` | **NEW** | (adda_stage_record, role) → rate, locked_at |
| `WorkerStageAllocation` | **NEW** | (stage_record, worker, color, size) → allocated_quantity, allocated_by |
| `WorkerStageContribution` | **EXTEND** | + `alter_quantity`, `missing_quantity` (nullable, default 0); `reported_quantity` now means Good |
| `AddaStageRecord` | unchanged | (rate snapshot lives in the new role-rate table) |
| `WorkerStageTask` | unchanged | stays roster/lifecycle only |
| stage-loss view | **DERIVED** | query, no table |

### 8.4 Required new entities
`AddaStageRoleRate`, `WorkerStageAllocation`. Plus a settlement-quantity **resolver** (code, not a table).

### 8.5 Impact on existing entities
- `WorkerStageContribution`: +2 nullable columns; reporting service gains the allocation bound; semantics of `reported_quantity` clarified to "good".
- `complete_worker_task`: rate source → `AddaStageRoleRate`; earning = good × frozen rate.
- `finalize_adda_settlement`: `qty = verified ?? reported` → `settlement_quantity(c, policy)`.
- Worker report form/schema: render allocations, hide caps.
- Assignment UI: `set_stage_workers` → allocation-aware assignment.

### 8.6 Migration strategy
- **All additive** (new tables + nullable columns) — no destructive migration.
- Backfill **known facts only**: contributions → good = reported, alter/missing = NULL/0; Adda rates → from existing frozen `expected_rate`.
- **Forward-only enforcement:** allocation-bound + good/alter/missing apply to **new Addas**; historical Addas keep working unchanged (no retro-allocation invented — respects work-that-happened immutability).
- Sequence inside the layer: rate snapshot (independent, ship first) → allocation model → bounded reporting → good/alter/missing → settlement resolver.

### 8.7 Risks & tradeoffs
- **Allocation overhead:** management must allocate color/size slices before workers report — new step. Mitigate with sensible defaults (auto-allocate even splits, then adjust).
- **Pool derivation cost:** derived pools mean queries, not counters — fine at this scale; index `(stage_record, color, size)`.
- **Re-cut / legitimate overage:** cutting is the only stage allowed to set/raise the ceiling; downstream never exceeds — needs an explicit rule + audited manager override.
- **Rework double-count:** altered pieces re-entering the pool must be tracked as the same pieces or netted.
- **Concurrency:** allocation draw-down must be atomic (`select_for_update`), same discipline as settlement.
- **Decimal vs integer:** garments are whole pieces — consider integer quantities per stage.
- **Behavior change risk:** existing worker-report UX changes (caps hidden, color/size locked) — needs worker retraining.

### 8.8 Build before TM-1? **YES.**
TM-1 (per-stage Manual/Barcode/Both/None) converges all capture to `WorkerStageContribution`. A barcode scan must also draw down an allocation and carry good/alter/missing. Building TM-1 first would hard-code the pre-foundation contribution shape and force a rework of the chokepoint. **This foundation is a prerequisite for TM-1, Missing Pieces, and Alter/Rework — all three depend on the allocation + good/alter/missing model.**

### 8.9 Postpone Phase C? **Partially — resequence, don't fully postpone.**
- **Proceed** with Phase C for surfaces this foundation does NOT change: sidebar/navigation gaps, permission-denial UX, management dashboards, mobile table strategy, listing/detail flows. Those findings stay valid regardless.
- **Defer** deep UX review of exactly two screens that WILL be redesigned by this foundation: the **worker self-report** screen and the **stage assignment** screen. Review those as part of the foundation's design, not now.
- Net: Phase C runs now with a carve-out, so momentum continues without wasting UX effort on soon-to-change screens.

---

## Bottom line
Build a **production-truth quantity layer** (allocation-bounded Good/Alter/Missing) + **Adda-frozen rates** + a **settlement-quantity resolver**, all additive. This makes production data correct by construction, keeps expected-earnings as pure visibility, and leaves settlement a separate, policy-flexible decision — exactly the three-way separation requested. It dissolves B-1 (no over-report possible), A-5 (rates confirmed at Adda start), and B-3 (trustworthy counts to base any variance/packed policy on). **Sequence: this foundation → TM-1 → Missing/Alter → settlement-policy choice.** Cross-refs: [ARCHITECTURE_V2](ARCHITECTURE_V2.md) §11, [REQUIREMENT_REVIEW_STAGE_TRACKING](REQUIREMENT_REVIEW_STAGE_TRACKING.md) (TM-1).
