---
id: docs-audit-phases-arch-eval-source-prevention-rates-variance
type: receipt
status: active
owner: append-only
scope: audit
anchors: —
verified: 2026-07-18
---

# Architecture Evaluation — Source-Prevention (B-1), Adda Rate Snapshots (A-5), Settlement Basis & Missing/Alter (B-3)

Decision-support. No implementation. All current-state claims are code-verified (file:line).

---

## Part 1 — Adda-level rate snapshots (A-5 + the rate question repeated in B-3)

**Verified current state.** There are TWO rate snapshots today, and neither freezes the *payable* rate at Adda-start:

| Rate | Lives on | Frozen WHEN | Role-aware? | Used for |
|------|----------|-------------|-------------|----------|
| `cost_rate_snapshot` | `AddaStageRecord` | stage **cost-freeze** (on complete) | No (standard) | `processing_cost` (product costing) |
| `expected_rate` | `WorkerStageContribution` | worker task **complete** | Yes (role-aware) | **settlement payout** |

Answers:
1. **Does Adda-level rate snapshotting exist?** Not for the *payable* rate. The payable rate is frozen per-contribution at task-complete, not copied to the Adda at start. (`AddaStageRecord.cost_rate_snapshot` exists but is the role-independent **standard cost** rate, a different number.)
2. **Which model owns payable-rate truth?** `WorkerStageContribution.expected_rate` ([worker_task.py:150](config/production/models/worker_task.py#L150)), set in `complete_worker_task` from `cost_service.role_rate_for(ws, role) or ws.cost_rate` ([worker_task_service.py:216-218](config/production/services/worker_task_service.py#L216)).
3. **Rate source at settlement?** `c.expected_rate` (the frozen contribution value) — [adda_settlement_service.py:315](config/expense/services/adda_settlement_service.py#L315). Settlement does NOT read the live workflow rate.
4. **Can workflow-stage rate edits affect historical Addas?** **Partially YES.** A contribution already *completed* is safe (rate frozen). But a contribution that completes **after** a workflow rate edit — on an old, still-in-progress Adda — picks up the **new** rate. The freeze point is per-contribution-complete, not Adda-start, so mid-Adda rate edits leak into that Adda.
5. **Smallest architecture-safe change for immutable Adda rates:** at Adda creation (or first stage-start), snapshot the payable rate per `(AddaStageRecord, role)` into a new field/table (e.g. `AddaStageRecord.payable_rate_snapshot` or a small `AddaStagePayRate` row), owner-confirmable; then `complete_worker_task` reads **that** instead of the live `ws` rate. Net effect: freeze moves earlier (Adda-start), drift disappears, and the owner gets the review/confirm step they described. This is additive — existing completed contributions keep their `expected_rate`.

**Verdict:** the owner's instinct is correct — the current freeze is **later than ideal** and can drift if rates change mid-Adda. The fix is small and additive. This supersedes the A-5 "block finalize on unpriced" idea's framing: with Adda-start rate snapshots + owner-confirm, an unpriced stage is caught at Adda-start (review step), not silently at settlement.

---

## Part 2 — Prevent over-reporting at source vs settlement-time reconciliation (B-1)

### Is source-prevention architecturally stronger? **Yes — and it would make the settlement reconciliation gate unnecessary.**

The settlement gate (my earlier B-1 recommendation) is **detection after the fact**: bad data already entered the immutable production-truth tables, and you reconcile at the money step. Source-prevention stops bad data from ever entering. Reasons it is the better layer:

1. **Production truth is immutable by design** (`reported_quantity` LOCKED after submit, [worker_task.py:142](config/production/models/worker_task.py#L142)). Detecting an over-report at settlement means you've stored a permanently-wrong "truth" and must paper over it with verified-corrections. Prevention keeps the immutable record correct *by construction*.
2. **Immediate, local feedback.** "You can't report 60 — re-count" at the moment of entry beats a manager discovering a mismatch days later at settlement.
3. **Settlement stays a pure money-freeze** with zero judgment calls — simpler, and matches the existing settlement-first design.
4. **The "never reveal the max" requirement is satisfiable server-side:** enforce `reported ≤ allocated` in the service and return a generic "exceeds your assigned quantity" error **without echoing the cap**. The cap lives in the allocation, never rendered to the worker.

**But** prevention is a bigger build than the gate, and it has real edge cases (below). Recommended stance: **prevention is primary; keep a cheap settlement-side assertion as a backstop** (defense in depth) — if prevention is correct, the backstop never fires, but it guards against bugs.

### What already exists (reusable) vs what's missing

**Exists:**
- **The "available pool" by color/size:** `AddaProductSizeColorPieceBreakdown` — "cutting stage's final verified per-(size,color) piece count snapshot" ([cutting.py:495](config/production/models/cutting.py#L495)). This is exactly the "max available" source-of-truth.
- **Allocation-with-remaining (partial):** `allocate_stage_work` + `item_allocation_summary` track allocated/remaining against a `CuttingBundleItem` ([allocation_service.py:26-144](config/expense/services/allocation_service.py#L26)). But this is the **era-A** path (LEVER-gated off since V2-3 settlement-first) and is bundle-item-grained, not a downstream color/size pool.

**Missing (the gap):**
- `WorkerStageTask` is **stage-level only** — "NOT money, NOT quantity" ([worker_task.py:29](config/production/models/worker_task.py#L29)). No worker↔(color,size,allocated_qty) binding.
- Color/size are **worker-picked at report time** ([worker_task.py:125](config/production/models/worker_task.py#L125)), not assigned.
- `reported_quantity` is bounded only by `> 0` ([worker_task.py:179](config/production/models/worker_task.py#L179)) — **no `≤ available` cap**.
- No per-stage downstream "available pool" that decreases as work flows.

### Data-model changes required (conceptual, not implementation)
1. **Allocation record** — `(stage_record, worker, color, size, allocated_quantity)`. Either a new `WorkerStageAllocation` or fields on `WorkerStageTask` (but the model doc deliberately keeps task quantity-free, so a sibling table is cleaner).
2. **Per-stage available pool** — for each `(stage_record, color, size)`: `available = upstream verified-good count` (cutting breakdown for the first downstream stage; prior stage's completed-good for later stages). Allocations must satisfy `Σ allocated ≤ available`.
3. **Reporting bound** — `reported_quantity ≤ allocation.allocated_quantity`; color/size taken FROM the allocation (locked), not free-picked.
4. **Monotonic-non-increase invariant** — each stage's verified-good output per `(color,size)` becomes the next stage's `available` ceiling. Quantity can drop (missing/alter) but never rise — enforced by the pool, not by a settlement check.

### How assignments / color-size quantities / stage progression should be designed
- **Cutting = source of truth:** writes per-`(color,size)` verified counts (already does, via `AddaProductSizeColorPieceBreakdown`). That snapshot is the initial pool.
- **Manager allocates pool slices** to workers per stage: Worker A → Red/M ≤ 50, Worker B → Blue/M ≤ 30. Allocation draws down the pool; `Σ allocations ≤ pool`.
- **Worker reports** within their slice; color/size fixed; `reported ≤ allocated`; cap never shown.
- **Stage completion** rolls each `(color,size)` verified-good total up as the next stage's pool ceiling → progression carries the non-increase invariant forward automatically.

---

## Part 3 — Missing / Alter integration + settlement basis (B-3)

### Missing & Alter as reporting INPUTS (not stages) — fits cleanly
The worker's report becomes three numbers against their allocation: **completed (good) + missing + alter**, with the invariant `completed + missing + alter ≤ allocated`. Then:
- **Missing** = pieces lost/unaccounted → reduce the pool that flows downstream (implements "quantity may decrease"). Not paid (the piece wasn't produced).
- **Alter** = pieces needing rework → siphoned into an Alter sub-flow; they re-enter the *same* pool when fixed (must be tracked as the SAME piece to avoid double-count).
- **Completed-good** = what flows to the next stage AND what the worker is paid for.

This makes per-stage quantity tracking show exactly where losses occurred (stage-level missing/alter), which is the operational visibility the owner wants (ties to Phase H).

### Settlement basis — recommendation
With source-prevention + Missing/Alter in place, the four candidates resolve cleanly:

| Basis | Verdict |
|-------|---------|
| 1. Worker-reported | ❌ alone, that's today's leak (B-1). Only safe **once bounded by allocation**. |
| 2. Verified | ✅ but redundant if reporting is already bounded — verification becomes the exception, not the rule. |
| 3. Final packed | ❌ as the per-stage pay basis — packing is a late stage; a cutting worker shouldn't wait for packing to be paid, and packed-total can't attribute pay to the right stage/worker. ✅ as a whole-Adda reconciliation total only. |
| **Recommended** | **Pay each stage on its own `completed-good` quantity** (= reported, **capped by allocation**, net of that worker's missing/alter), with `verified_quantity` retained as the management override for disputes. Packed-total reconciles the Adda end-to-end but is not the pay basis. |

**Key consequence:** if source-prevention is built, the **B-1 settlement reconciliation gate is no longer needed** — the production-truth quantity is trustworthy at entry, so settlement just multiplies trusted quantity × frozen Adda-rate. B-3's "deduct rejected" then becomes a clean, well-defined operation on a trustworthy `rejected/alter` count (do NOT deduct on un-reconciled counts — which is why B-3 was correctly flagged as dependent on B-1).

---

## Edge cases the owner may be missing
1. **Legitimate re-cut / over-cut:** cutting sometimes outputs *extra* to cover expected defects → the pool can legitimately exceed the order at cutting only; downstream must never exceed cutting. Need an explicit "cutting is the only stage that can set the ceiling" rule.
2. **Split allocation:** one `(color,size)` worked by multiple workers → pool accounting must sum allocations; partial returns must release pool back.
3. **Rework loop double-count:** an Alter piece goes back upstream then forward again — if not tracked as the same physical piece, it inflates counts. Needs piece-identity or a netting rule.
4. **Under-reporting / shortfall:** worker reports < allocated (genuine) → is the remainder reassigned, marked missing, or left open? Pool must not silently leak.
5. **Concurrency:** two workers drawing the same pool at once → allocation decrement must be atomic (select_for_update), same discipline as settlement.
6. **Granularity mismatch:** allocation at bundle-item vs aggregated `(color,size)` — pick one truth; the existing bundle-item allocation and the `AddaProductSizeColorPieceBreakdown` aggregate are two grains that must be reconciled.
7. **Manager override:** legitimate exceed-cases (re-cut) need an audited override path, or honest workers get blocked.
8. **Decimal quantities:** `reported_quantity` is `DecimalField(2dp)` — half-pieces shouldn't exist for garments; consider integer enforcement per stage.
9. **Rate × Missing/Alter interaction:** if pay = completed-good, ensure missing/alter pieces are excluded from the rate multiply consistently across stages.

---

## Bottom line for the three decisions
- **B-1:** Source-prevention (allocation-bounded reporting) **is architecturally stronger** and would retire the settlement gate. Bigger build; needs the allocation layer + per-stage pool. Keep a cheap settlement-side assertion as a backstop.
- **A-5:** Add **Adda-start payable-rate snapshots** (small, additive) — fixes the real drift gap and gives the owner the review/confirm step. Settlement already uses frozen rates, just frozen too late.
- **B-3:** Define **Missing/Alter as report inputs**; pay each stage on **allocation-capped completed-good**; keep verified as override; packed = Adda reconciliation only. "Deduct rejected" becomes safe **after** source-prevention.

**These three are one architecture, not three patches.** Recommend designing them together as a "production-truth quantity + Adda-frozen rate" layer before TM-1 — TM-1 (per-stage tracking modes) and Missing/Alter both depend on this being right.
