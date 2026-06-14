## TL;DR (2 min)
Sole writer of production truth (WST + WSC). Manager assigns (set_stage_workers,
roster full-replace, cancel-not-delete) → worker reports (report_contributions)
→ submit freezes expected_* (complete_worker_task) → management can correct
(set_verified_quantity, settled lines refuse). CI gate [4/4]. reported_quantity
is immutable forever; expected_* is visibility only, never money.
**S3 (good/alter/missing):** report_contributions now DUAL-WRITES `good_quantity =
reported_quantity` (RC-3; worker UI still submits one qty = good; alter/missing default
0). Settlement pays `good_quantity` (resolver); expected_earning freezes on good. The
legacy `reported_quantity` is kept + dual-written through S3→S5, renamed-not-dropped at
S6. DB constraint swapped: `wsc_reported_quantity_positive` → `wsc_gam_nonneg_sum_positive`
(each ≥ 0 AND sum > 0; a good=0 all-defect row is now legal).

# Chokepoint: worker_task_service (production truth)

File: `config/production/services/worker_task_service.py`

**Why exists:** sab production "kaam ka sach" yahan se likhta hai — ek hi darwaza
taaki settlement un numbers pe bharosa kar sake.

**Owns / writes:** `WorkerStageTask` (WHO worked — assigned/in_progress/
completed/verified/cancelled) + `WorkerStageContribution` (WHAT — color/size/
qty lines). Also freezes `expected_rate`/`expected_earning` at complete, and
sets `verified_quantity` (P1 management correction). CI gate **[4/4]**.
**Foundation S2:** complete freezes the worker's `role_snapshot` and pays the rate
FROZEN on `AddaStageRoleRate[(stage_record, role)]` (`stage_rate_service`), NOT the
live workflow — so a later workflow-rate edit or worker role change never re-prices
the work (addendum M-5). Reads the frozen row under lock (order: task → AddaStageRoleRate,
contract 1); live-fallback + WARN only when no snapshot exists (pre-S2 / contract 2).
**S1.1:** a super-admin can correct a rate UNTIL settlement via
`stage_rate_service.rerate_stage_role` — it OVERRIDES this completion lock (M1 per-
(stage,role) is preserved for normal edits), recalcs completed-but-unsettled
expected_*, refuses once actively settled, and writes an append-only
`RateCorrectionAudit`. Full lock order: task → AddaStageRoleRate → WorkerStageContribution
(disjoint from the settlement lock domain — no deadlock).
**S4/Phase 4:** `complete` calls `pool_service.check_allocation_bound(task)` BEFORE any freeze
(refused → freezes nothing) — Strict bound `Σ(good+alter+missing) ≤ Σ active allocated` per
reported dim on pool-participant stages, gated by `ENFORCE_ALLOCATION_BOUND` (default False).
Production-capacity only (no verified/settlement/rate/cost read).

**Who can call:** stage services + the worker report view (workers only via
their own assigned task — assignment-gated). Never a model `.save` elsewhere.

**S4/Phase 5 reopen:** the shared `reopen_stage_record` skeleton now refuses upstream reopen
while a downstream consumer (non-voided `WorkerStageAllocation` / completed contribution /
future AlterCase) exists (`_shared._downstream_consumer_guard`, uniform across stages,
actionable error) + clears the reopened stage's `StagePoolSnapshot` (`pool_service.clear_stage_pool`).
**F4 reopen contract (symmetric):** reopen re-resolves + unlocks the worker-rate snapshot
(`stage_rate_service.refloat_rates_on_reopen`) right after `clear_stage_cost` re-floats the
manufacturing cost — re-complete re-freezes the rate at the current resolved value (grouped→0
via the F2 guard). Cost-freeze and worker-rate-freeze behave consistently; settlement stays the
final money boundary (a settled stage can't reopen).

**Key functions:** `set_stage_workers` (roster full-replace, cancel-not-delete,
`select_for_update` on active tasks) · `report_contributions` · `complete_worker_task`
(freezes expected_*; **locks the task row + re-checks DB status — race-safe vs a
concurrent stage-complete cancel, P0-5**) · `set_verified_quantity` (settled lines
REFUSE → reverse first) · `resolve_stage_tasks_on_complete` (F3 auto-cancel unreported).

**Invariants protected:** reported_quantity IMMUTABLE (owner §6) · roster =
who actually participated (cancel, never delete) · ≤1 ACTIVE task per
(stage_record, worker) (partial-unique constraint) · **C-TM: every capture
path — manual today, barcode scans (TM-2) tomorrow — converges HERE**.

**What breaks if bypassed:** a second WSC writer = production numbers settlement
can't trust = pay computed on unverifiable data. The partial-unique + the gate
exist precisely so this can't happen.

Lessons: [../../LEARNING/05_PRODUCTION_TRUTH.md](../../LEARNING/05_PRODUCTION_TRUTH.md).
Journey: [../REQUEST_JOURNEYS/worker_reporting.md](../REQUEST_JOURNEYS/worker_reporting.md).

---
## v2 — VERIFIED execution trace 

Source: `config/production/services/worker_task_service.py`. Two real paths:

**A) Manager assigns workers** — `set_stage_workers`:
```
[caller's @transaction.atomic — CALL CONTRACT,] WorkerStageTask.objects.select_for_update lock active tasks (roster) WorkerStageTask.objects.create(...) INSERT new assignees task.status = CANCELLED ; save UPDATE removed (cancel, not delete)
```

**B) Worker reports + completes** — `report_contributions` → `complete_worker_task`:
```
@transaction.atomic (report_contributions, WorkerStageContribution.objects.create(...) INSERT lines (reported_quantity) task.status = IN_PROGRESS ; save UPDATE WST
@transaction.atomic (complete_worker_task, WorkerStageTask.select_for_update lock + re-check DB status (P0-5: refuse if CANCELLED/COMPLETED) c.save(expected_rate, expected_earning) UPDATE — FREEZE per line (visibility) task.status = COMPLETED ; save UPDATE WST
```

**C) Management correction** — `set_verified_quantity`:
```
@transaction.atomic WSC.select_for_update(of=('self',)) lock (of=self: nullable settlement_line join)
 refuse if task not completed/verified; refuse if settled line (reverse first) c.save(verified_quantity) UPDATE — reported untouched
```

**Models touched:** WorkerStageTask, WorkerStageContribution. **Tx boundary:**
each public fn is atomic (set_stage_workers requires the caller's atomic — see call contract). **Before→after:** assign → WST(assigned); report →
WSC(reported, WST in_progress); complete → WSC.expected_* frozen + WST completed.

**Common mistakes:** writing WSC outside this service (gate 4/4 fails); editing
reported_quantity (use verified_quantity); `select_for_update` without
`of=('self',)` on the nullable settlement_line join (Postgres refuses).

### Verification Sources
- Read: worker_task_service.py (set_stage_workers, report, complete, verify. Models: production/models/worker_task.py.
- ADRs: 0001, 0002, 0005. Confidence: **High** — verified against commit f067daf0 (2026-06-12); re-verify the cited file if it changed (line-level trace, current code).
