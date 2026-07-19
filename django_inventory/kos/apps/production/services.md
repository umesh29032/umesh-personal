---
id: app-production-services
type: app
verified: 2026-07-19
knowledge_confidence: verified_against_code
answers: "14 production services + 6 stage handlers — who owns which responsibility, who calls whom, how does each fail?"
related: [app-production, concept-single-writer]
---

# production — service knowledge

> 📂 [production app](README.md) · [Apps](../README.md) · [LOS home](../../README.md)
> Two layers here: **domain services** (`config/production/services/`) and
> **stage handlers** (`config/production/stages/<stage>/service.py` — one
> package per built-in stage + `generic_stage` + shared `base/`).

## The sole-writer table

| Service | Sole writer of | Called by |
|---|---|---|
| `worker_task_service` | WST + WSC (**C-TM: every capture path, CI gate 4/4**) | worker report + review views · roster (stage panels) |
| `pool_service` | SPS + WSA (**no money, ever — owner-locked ⊥**) | generic allocate/void views · `advance_to_next_stage` funnel |
| `flow_service` | WorkflowStage (order/rates/grain/grouping) | flow editor |
| `stage_rate_service` | AddaStageRoleRate (freeze) + RateCorrectionAudit (rerate) | adda_service (at ASR creation) · StageRateCorrectView |
| `adda_service` | Adda + AddaStageRecord | Adda create/lanes views |
| `product_service` / `product_size_service` | Product masters / size charts | product views (SA) |
| stage handlers (below) | their stage's records (Layering*/CuttingPattern*/Cutting*/Barcode* chains + APSCPB) | workspace views · generic dispatch |

**Read-only:** `access_service` (the ONE visibility predicate + rosters) ·
`cost_service` (ADR-0009 cost reads + `effective_pay_rate` grouped→0 guard)
· `activity_service` / `operations_digest` (dashboards/A360) ·
`reconciliation_service` (paid-vs-produced drift) · `_shared`
(cross-service guards: `_downstream_consumer_guard` — helpers WITHOUT
becoming second writers).

## The two chokepoints (read their docs before touching)

**`worker_task_service.py`** — verbs: `set_stage_workers` (THE roster
source) · `report_contributions` / `save_draft_contributions` ·
`complete_worker_task` (five guards: P0-5 lock-and-reread → bound check →
FIXED-pay once → role/rate freeze → NO ledger) · `set_verified_quantity`
(red pen; settled refuses) · `void_submitted_report` ·
`resolve_stage_tasks_on_complete` (C3 companion).
Failure modes = designed refusals: cancelled/completed states, fixed-pay
second report (names who), settled line (names ADST), bound (flag-gated).
Deep: [stage-tracking](../../features/stage-tracking.md).

**`pool_service.py`** — verbs: `pool_good` (handler-dispatched: cutting→
APSCPB, downstream→SPS) · `materialize_stage_pool` (write-once,
verified-else-good) · `clear_stage_pool` (reopen) · `allocate` /
`void_allocation` / `available` · `check_allocation_bound` ·
`upstream_pool_source`. Locks: (5375, objid) — disjoint from money's 5374.
Failure modes: over-draw refused ALWAYS · H-2 void refusal (reports would
strand) · reopen guard names furthest downstream blocker.
Deep: [allocation](../../features/allocation.md) + the
[chokepoint doc](../../../docs/LEARNING_2_0/CHOKEPOINTS/pool_service.md).
⚠ Naming trap: `expense.services.allocation_service` = the UNRELATED era-A
money lane.

## The stage-handler layer (`stages/`)

`base/` = the shared handler contract; each package
(`layering/` · `cutting_pattern/` · `cutting/` · `barcode_generation/` ·
`generic_stage/`) implements its stage's operations; the generic views +
pool dispatch by stage handler — **no stage-name conditionals** anywhere.
- `layering/service.py` — attach/quick-create rolls, leftovers mandatory at complete.
- `cutting_pattern/service.py` — checklist/evidence lifecycle, verify, sizes.
- `cutting/service.py` — breakups→bundles→**`_materialize_breakdown` (APSCPB)**;
  `layout_reconciliation` + `get_suggested_breakup` (typo-catchers);
  `preview_barcode_batches`; skill gates `_ensure_cutting_skill`.
- `barcode_generation/service.py` (+`assembly`/`export_service`) — APSCPB →
  BarcodeBatch ranges; printed = permanent.
- `generic_stage/service.py` — R10-B config-only lifecycle riding the same funnel.

## Cross-app calls (directions that matter)

OUT: `tracking.history_service` (timeline events) · reads
`raw_materials` rolls at layering. IN: `expense` settlement READS WST/WSC/
rates at finalize (never writes); its interlocks (settled-line, reopen
armor) are honored HERE. External APIs: none.

## Adding/changing a verb here — the checklist

Which concern? (capacity/production-truth/config — if money, WRONG APP) →
the owning service or stage handler only → docstring side-effects →
refusals that name the fix → respect lock namespaces (5375 pool; join 5374
only for settlement-racing ops like basis flips) → tests: S3/S4-style +
refusal pins → kos-sync (this file + feature page Change Impact).

## Required Knowledge (this page)

- [ ] Lock namespaces + ordering (5375 vs 5374) → [locks](../../concepts/postgresql/locks.md)
- [ ] Single-writer + C-TM convergence → [single-writer](../../concepts/architecture/single-writer.md)
- [ ] The resolver + four-concern orthogonality → [two-truths](../../concepts/architecture/two-truths.md)

## Learning Graph

**Before:** [views.md](views.md) (the callers). **After:** the two
chokepoint deep-docs → [urls-adda.md](urls-adda.md) generic-complete/reopen
sections → modify code.
