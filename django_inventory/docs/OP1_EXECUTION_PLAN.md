---
id: op1-execution-plan
type: receipt
status: active
owner: append-only
scope: campaign/audit evidence
anchors: —
verified: 2026-07-13
---

# OP-1 — Multi-worker dimension-scoped operations (S4 consumer wiring)

> **Status: ✅ IMPLEMENTED 2026-07-05 — gate PASS 864, browser-proven on
> 3-PATTI-011 (§6 receipt). ⏸ awaiting owner approval** (owner strategy order
> 2026-07-05: plan → implement → verify → audit → docs → STOP for approval).
> Governing docs: PRE_S1_DESIGN_ADDENDUM (S4 receipts),
> R10_MACHINE_STAGES_ARCHITECTURE (frozen rules 1-12), PDD v1.0.

## 1) Business process (owner spec 2026-07-05)

Cutting produced Red 50 / Blue 50 / Green 50 / Yellow 50 / Black 50. Manager
assigns Worker A→Red, B→Blue, … (one worker may take several colours). Worker
is **NEVER shown how many pieces were cut** — they blind-enter Good / Alter /
Missing for their colours (honest production validation). Manager sees the
full per-worker picture (assigned · reported G/A/M · verified · expected ₹).
Everything rolls into the existing snapshot → settlement → payroll → costing →
A360 → Operations path. ONE calculation path; no new money.

## 2) Architecture review — verdict: ZERO new models, ZERO migrations

The 2026-06-14 Production-Truth Foundation (S4) built EXACTLY this and left it
inert ("pool source, no consumer"). OP-1 is the consumer:

| Need | Existing foundation piece | Missing |
|---|---|---|
| Per-stage split grain | `WorkflowStage.allocation_dimensions` {NONE/QUANTITY/COLOR_SIZE} (0040) + `flow_service.set_stage_grain` (+ monotonicity guard) | **UI** (flow editor) |
| What's available to split | `pool_service.pool_good/available` — cutting=APSCPB (single source), downstream=`StagePoolSnapshot` (0041) | **materialize wiring** at stage complete |
| Manager assigns colour→worker | `WorkerStageAllocation` (0042) + `pool_service.allocate/void_allocation/worker_allocated` (mgmt-only, over-allocation refused, D2 advisory lock, append-only void) | **UI + endpoints** |
| Worker blind report w/ dims | `WorkerStageContribution.color/size` + schema-driven `WorkerReportView` (parses ANY schema) | generic handler schema lacks colour/size fields |
| Integrity ramp | `bound_soft_warning` (already fires in report view) + `check_allocation_bound` (complete-time, `ENFORCE_ALLOCATION_BOUND=False`) | nothing — stays OFF per runbook |
| Money | expected freeze good×frozen-rate; settlement funnel; verified-else-reported | nothing — untouched |

Frozen-rule fit: manager-assignment-only (allocate = explicit manager action);
settlement-only money (WSA carries NO money — owner-locked + tested);
snapshots read-only; no hidden automation (allocation dropdown = roster
members only; no auto-rostering); config-over-hardcoding (grain per stage in
flow editor; no stage names anywhere); single-writer (pool_service stays sole
WSA/SPS writer; worker_task_service sole WSC writer).

## 3) Blind-rule audit findings (fixed in OP-1)

- **L1** `_stage_panel_generic.html` Output board + roster chips render to ANY
  panel viewer — an assigned worker sees other workers' names + G/A/M.
  views_ctx comment promised a template gate that isn't there. → mgmt-only
  board; worker lens = own card only.
- **L2** `adda_detail.html` Stages Overview gated `is_management or
  has_layering_access` — skilled workers see every stage's totals incl.
  cutting quantities. → tighten to `is_management` (legacy convenience
  predates the frozen visibility rule).
- Already safe: `prev_admin_snapshot` mgmt-gated at ctx level (R8 leak-test);
  worker report resolves own task only; A360/costing/settlement mgmt-only.

## 4) Changes (no migrations)

1. **Flow editor** ([flow_views.py](../config/production/views/flow_views.py) +
   product_flow.html): `set_cost` POST also reads `work_split` select →
   `set_stage_grain` (separate service calls, one Save). Grain tag on the row.
2. **Engine seam** (adda_service.advance_to_next_stage): after
   `freeze_stage_cost` → `pool_service.materialize_stage_pool(leaving_sr)` —
   the ONE funnel every stage passes; cutting no-op (APSCPB), NONE→0 rows;
   reopen already clears (S4-P5).
3. **Schema** (base + 4 handler overrides): `contribution_schema(self, adda,
   worker=None)`. Generic handler on a pool stage + worker → colour/size
   choice fields whose options = the worker's ACTIVE allocated dims (labels
   only — never quantities); NONE stage → today's 3 fields unchanged.
4. **Report view**: pass `worker=request.user`.
5. **Panel ctx + endpoints + template**: mgmt "Split work" section (available
   per dim + allocate form [roster-member × colour × size × qty] + active
   allocation chips + void), mgmt board columns Allocated/Good/Alter/Missing/
   Verified/Expected ₹; worker lens = own dims chips + own totals + report
   link. New POST routes `generic-stage-allocate` / `generic-stage-alloc-void`.
6. **Leak fixes** L1 + L2.
7. **Tests** `test_op1_operations.py`: grain UI service call; materialize at
   complete + reopen clear; allocate/void/over-allocation via endpoints
   (worker 403); per-worker schema dims (+no-qty assertion); dim-carrying
   report → expected freeze on good; panel ctx worker-lens has no other
   workers/pool numbers; L2 regression; golden ₹225 untouched.

## 5) Non-goals (unchanged scope fences)

Parallel-ops engine (sequential per Adda stands — TM-2/bundle phase), rework/
missing modules (accessors stay 0), `ENFORCE_ALLOCATION_BOUND` flip (staging
runbook owns it), machine costing, barcode, bespoke-stage allocation UI
(cutting = source; bespoke consumers adopt the partial when they exist).

## 6) Result — ✅ IMPLEMENTED 2026-07-05 · gate PASS **864** (854+10) · browser-proven

**Code:** flow editor Work-split select (+`Split:` tag) → `set_stage_grain` · materialize
wired in `advance_to_next_stage` after the F3 task-resolve (statuses final before the pool
sums) · `contribution_schema(adda, worker=None)` across base+4 handlers; generic handler
emits colour/size choice fields scoped to the worker's active `WorkerStageAllocation`
(labels/swatches only) · `WorkerReportView` passes the worker + report chips show
"Nothing assigned to you yet" when unsplit · `generic-stage-allocate`/`-alloc-void`
endpoints → pool_service · panel two lenses (mgmt: roster+Split+board w/ Allocated/
Verified/Expected ₹; worker: own dims+totals+report CTA, own machine only) · L1+L2 leak
fixes · **bonus fix:** `stage_panel_standalone.html` only knew layering/cutting — every
other stage rendered an EMPTY standalone panel; now mirrors the embedded dispatch.

**Tests:** `test_op1_operations.py` ×10 (grain UI+monotonicity · materialize/reopen-clear ·
allocate/void/over-allocation/worker-403 · worker-scoped schema w/ no-quantity assertion ·
blind report view + dims→₹freeze on good · soft-warn · panel lenses · L2 · WSA-no-money).
A360 pin 66→68 (documented: 1 WorkflowStage grain read per generic stage). Synthetic
handler fixture signature widened.

**Browser (3-PATTI-011):** Overlock grain set via flow UI → barcode advanced → Split table
= cutting truth (Red·S1 60 / Red·S2 45) → allocate Red·S1×20 → dev.monthly (available
60→40, chip w/ void) → phone 390px: worker sees ONLY Red+Size 1 chips, zero quantities →
reports 18/1/1 → board: Allocated 20 · Good 18 · Alter 1 · Missing 1 · Expected **₹90**
(18×₹5, good-only) → worker Adda page: no Stages Overview/totals (L2 live).

**Dev-data notes for owner cleanup batch:** `cutting_master` skill wired onto
`barcode_generation` stage (its access list was EMPTY — the barcode workspace requires
≥1 eligible worker, so the stage was un-startable; flag for a proper owner decision) ·
dev.monthly roster+allocation+18/1/1 report on 3-PATTI-011 · Overlock grain=Colour+Size
on the 3-PATTI flow (intended to stay).

**Fences honored:** no migrations · no new money paths (gate 4/4b/4c green) ·
`ENFORCE_ALLOCATION_BOUND` still False (runbook owns the flip) · sequential engine
untouched · golden ₹225 byte-identical inside the gate.
