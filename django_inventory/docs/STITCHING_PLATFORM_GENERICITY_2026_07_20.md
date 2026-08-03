# Stitching Platform — Genericity Audit & Permanent-Standard Certification

**Date:** 2026-07-20
**Ask:** treat the stitching-stage engine as the permanent manufacturing platform for the ERP. Prove it is truly config-only (only stage name / skill / rate differ), hunt hidden stage-specific logic and duplication across every layer, fix only what improves genericity/maintainability without breaking certification, regression after each change. No browser verification, no commit.
**Method:** three exhaustive read-only census sweeps (backend coupling · views/URLs/templates/JS · duplication/read-model) plus direct verification of the load-bearing mechanisms (registry, skill resolution, flow editor). 4 safe cleanups implemented. 186 tests re-run green.

---

## Headline

**The stitching engine is ALREADY a genuine config-only platform. Zero stitching-stage-identity logic exists anywhere in the engine. Adding a new stitching stage is pure super-admin UI configuration — no code, no migration, no template, no view.** The census found no genericity violation to fix; it found only DRY/dead-code polish, four items of which are now done. This engine is ready to be the permanent standard.

---

## 1. Current stitching platform architecture

One request path serves every stitching stage, dispatching by **stage code** (a lookup key), never branching on stage identity:

```
URL  addas/<code>/stage/<stage_type>/…         (one generic set: panel, start, complete,
                                                 reopen, allocate, alloc-void, report, snapshot)
  → View  GenericStage*View / StagePanelView / WorkerReportView   (parameterized by stage_type)
    → Registry  registry.get(code)  → bespoke handler if registered, else GENERIC FALLBACK
      → Handler  GenericStageHandler(code, name)   (one instance per active Stage, cached)
        → Services  pool_service (allocate/bound/pool) · worker_task_service (report/complete)
                    · bundle_service (read-model) · cost_service · stage_rate_service · settlement
          → Templates  _stage_panel_generic.html (mgr) · _worker_report_body.html (worker)
                       · adda_snapshot.html (super-admin) · my_assigned_work.html (worker)
```

**Per-stage variation is 100% data** on two config models:
- `Stage` — name, `access_by_skill` (M2M → who can work it), `work_type`, `machine_type`.
- `WorkflowStage` — `order`, `allocation_dimensions` (NONE/QUANTITY/COLOR_SIZE = the pool grain), `cost_method`, `cost_rate`, `cost_billed_at`, `credits_workers`.

The registry (`production/stages/base/registry.py`) is **open-closed**: `_generic_fallback` (registry.py:35-53) serves any active `Stage` without a bespoke package via one `GenericStageHandler`; `autodiscover()` self-registers any handler that exists — "no central list to edit." So a new stage needs no registration and no handler.

## 2. Does every stitching stage truly use the same engine? — YES (verified)

All 7 (overlock, leg_binding, elastic_attach, label_attach, thread_cutting, checking, packing) resolve to the **same `GenericStageHandler`**, the same `color_size` grain, and a **byte-identical field schema** `(colour, size, good, alter, missing, damaged)`. Only 4 stages have a bespoke handler — layering, cutting_pattern, cutting, barcode_generation — all pre-production, none stitching. No bespoke stitching handler, partial, URL, view, or template exists anywhere.

## 3. Is every manager screen identical? — YES

Every stitching stage renders through `build_generic_panel_context` (`views_ctx.py:71`) → `_stage_panel_generic.html`. `StagePanelView` dispatches by `registry.get(stage_type).panel_context(...)` (the legacy if/elif was removed) — no stitching fork. The manager always sees: available bundles → skill-filtered workers → assign (whole/partial) → live board. Skill filtering is config-driven (`eligible_stage_workers` reads `Stage.access_by_skill`), so the picker can never offer an unrelated worker.

## 4. Is every worker screen identical? — YES

Every stitching stage renders through `WorkerReportView` → `GenericStageHandler.contribution_schema` → `_worker_report_body.html`. Schema-driven, no stage names. The worker sees stage name + bundle (colour·size) + four number fields (Good/Alter/Missing/Damaged). The allocated quantity **never enters the schema or the template** (no `max=`, no "remaining") — the blind-accountability rule holds identically on all stages.

## 5. Is every Super Admin screen identical? — YES

One snapshot surface (`bundle_service.stage_snapshot` → `adda_snapshot.html`, `AddaSnapshotView`) iterates all pool stages generically: per bundle (total/assigned/available/completed/progress/holders) + per worker×bundle (mode/allocated/completed/remaining/expected ₹/status/started/updated). No per-stage dashboard, no custom page.

## 6. Hidden stage-specific logic? — NONE in the stitching path

Full backend census (production/services, production/stages, expense/services): **0 stitching-identity violations.** Every stage-name occurrence is one of:
- **Pre-production** (allowed bespoke zone): `PRE_PRODUCTION_STAGE_CODES = (layering, cutting_pattern, cutting)`, `STAGE_LAYERING`, `STAGE_CUTTING`, `STAGE_BARCODE_GENERATION` in adda_service / _shared / the four bespoke handlers.
- **Policy-switch on config** (correct — that IS the config): `allocation_dimensions`, `cost_method == FIXED`, `credits_workers`, `cost_billed_at_id`, `work_type`.
- **Non-branching**: display/grouping/error-text using `stage.name`/`code` (never changes money or flow).

Earning (`good × frozen rate`) and settlement are fully stage-agnostic — the only money gates are `credits_workers` + `cost_billed_at_id`, both config.

## 7. Unnecessary complexity?

The engine core is lean. The one honest smell is **read-model surface count**, not correctness: ~9 public projections + helpers, and the low-level "Σ a contribution field over a filtered set" primitive was hand-rolled in several places at different grains. These are *legitimately different projections* (stage-grain / per-bundle / per-worker×bundle / per-task / cross-Adda), not truth divergence — money never enters them (they read the already-frozen `expected_earning`; costing/settlement keep their own single homes).

## 8. Opportunities to simplify (found)

| # | Item | file | Action |
|---|---|---|---|
| 1 | Over-report sum `good+alter+missing+damaged` re-implemented in `check_allocation_bound` AND `preview_bound_violations` | pool_service.py | **FIXED** — extracted `_contribution_load` |
| 2 | Card-status ternary duplicated in `worker_bundles` + `stage_snapshot` | bundle_service.py | **FIXED** — extracted `_bundle_status` |
| 3 | `whole_holders`/`partial_holders` per-bundle fields — zero consumers | bundle_service.py | **FIXED** — deleted |
| 4 | `unassigned_bundles()` — no production consumer (dropdown uses `bundles_for_stage` filtered in-template) | bundle_service.py + services/__init__ + test | **FIXED** — deleted |
| 5 | Per-task Σ good/verified/expected duplicated across `views_ctx` + `a360` | views_ctx.py / a360.py | **DEFERRED** — a360 is a separate committed dashboard with ₹-suppression on top; a `_task_rollup` helper is a real DRY win but touching a360 widens blast radius against "must not break certification." Recommended, not done. |
| 6 | `adda_service.py:615` bare `'cutting'` literal vs `STAGE_CUTTING` const | adda_service.py | **DEFERRED** — cosmetic, pre-production zone (not the stitching platform). |
| — | `reported_quantity` dual-write | worker_task_service.py | **LEFT** — S6 planned irreversible migration (soak-gated), NOT a no-behavior cleanup. |

## 9. Improvements implemented

4 behavior-neutral cleanups (all in the engine's own service files, riding the same uncommitted AE change):
1. **`pool_service._contribution_load(c)`** — single definition of a contribution's load (good+alter+missing+damaged); both the enforcement (`check_allocation_bound`) and the legacy-row audit (`preview_bound_violations`) now sum this one helper, so the over-report bound can never silently diverge.
2. **`bundle_service._bundle_status(locked, remaining, completed)`** — single (state)→card-status map shared by the worker card and the super-admin snapshot, so they can never label the same bundle differently.
3. Removed dead `whole_holders` / `partial_holders` fields.
4. Removed dead `unassigned_bundles()` (function + export + a redundant test assertion).

Docs-sync: `docs/apps/production/GUIDE.md` bundle_service row updated to match.

## 10. Regression results

**186 relevant tests green after the cleanup** (behavior-neutral confirmed):
- 148 engine tests (allocation, pool, generic-stage, worker-task, report-view, AE1/AE3/AE4, S4 suite: allocation/bound/grain/pool/reopen-guard, gap1/gap5).
- 34 settlement + money tests (adda_settlement_service, adda_settlement_models, devseed money).
- 4 golden ₹ journeys — **₹801 finalize byte-identical**, ₹344.25/₹633 goldens intact.

Baseline before cleanup was the same 148 engine → 148, i.e. no test lost behavior (the deleted `unassigned_bundles` assertion was redundant with the `available()==0` assert on the line above).

## 11. Architecture score — **9.5 / 10**

Genuinely generic, open-closed registry, config-only per stage, one dispatch path, money isolated to single-writer services. −0.5 only for the read-model surface count (a maintainability smell, not a correctness or genericity defect).

## 12. Maintainability score — **9 / 10**

Over-report rule single-source; one WSC writer; one panel/report/snapshot dispatch; the two intra-file dups are now extracted helpers. −1 for the one remaining cross-file duplicate (per-task Σ in views_ctx + a360, deferred) and the general read-model breadth. Neither risks truth.

## 13. Future scalability score — **9.5 / 10**

Adding 20 more stitching stages = 20 `Stage` rows + 20 `WorkflowStage` rows via the super-admin flow editor (name, skill, rate, grain). Touches none of the ~9 read-model surfaces or any engine code — they iterate the flow and dispatch by code. Per-stage marginal code cost is effectively zero. This is proven, not asserted: skill = `Stage.access_by_skill`, handler = generic fallback, grain/rate/cost = flow editor UI, all config.

## 14. Ready to become the permanent stitching platform? — **YES**

## 15. Why

- **One engine, provably.** All 7 stitching stages share one handler, one schema, one URL set, one view set, one template set, one validator, one WSC writer. Verified by exhaustive census (0 violations) and by direct reading of the registry, skill resolver, and flow editor.
- **Config-only is real, via UI.** A new stitching stage is created and wired entirely from the super-admin flow editor + Access-Control; no developer action. This is the definition of the permanent platform you asked for.
- **Accountability, earnings, settlement are stage-agnostic and single-source** — the rules you care about (blind worker, `good+alter+missing+damaged ≤ allocated`, good-only pays, settlement-only money) live in exactly one place each and apply identically to every stage.
- **The debt was minor and is now paid** — the only genuine duplications (two sum/status re-implementations) are extracted to shared helpers; dead code removed; 186 tests green.

**Nothing prevents adoption.** The one deferred item (a360 per-task Σ dedup) is a maintainability nicety on a pre-production-adjacent dashboard, not a platform blocker; it can ride a future a360 change safely.

---

### Recommendations (future, non-blocking)
1. Extract `_task_rollup(task)` shared by `views_ctx` + `a360` when a360 is next touched (removes the last cross-file per-task Σ duplicate).
2. Swap `adda_service.py:615` `'cutting'` → `STAGE_CUTTING` for constant-consistency (pre-prod, cosmetic).
3. When the S6 migration is scheduled, retire `reported_quantity` (drops the dual-write; separate soak-gated change).

*Evidence: 3 read-only census sweeps + direct verification of registry.py / access_service.py / flow_views.py. 4 cleanups implemented in pool_service.py + bundle_service.py + services/__init__.py + one test. 186 tests re-run green. No commit; no browser verification (per instruction).*
