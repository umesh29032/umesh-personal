## TL;DR (2 min)
Sole writer of production truth (WST + WSC). Manager assigns (set_stage_workers,
roster full-replace, cancel-not-delete) → worker reports (report_contributions)
→ submit freezes expected_* (complete_worker_task) → management can correct
(set_verified_quantity, settled lines refuse). CI gate [4/4]. reported_quantity
is immutable forever; expected_* is visibility only, never money.

# Chokepoint: worker_task_service (production truth)

File: `config/production/services/worker_task_service.py`

**Why exists:** sab production "kaam ka sach" yahan se likhta hai — ek hi darwaza
taaki settlement un numbers pe bharosa kar sake.

**Owns / writes:** `WorkerStageTask` (WHO worked — assigned/in_progress/
completed/verified/cancelled) + `WorkerStageContribution` (WHAT — color/size/
qty lines). Also freezes `expected_rate`/`expected_earning` at complete, and
sets `verified_quantity` (P1 management correction). CI gate **[4/4]**.

**Who can call:** stage services + the worker report view (workers only via
their own assigned task — assignment-gated). Never a model `.save` elsewhere.

**Key functions:** `set_stage_workers` (roster full-replace, cancel-not-delete,
`select_for_update` on active tasks) · `report_contributions` · `complete_worker_task`
(freezes expected_*) · `set_verified_quantity` (settled lines REFUSE → reverse
first) · `resolve_stage_tasks_on_complete` (F3 auto-cancel unreported).

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
@transaction.atomic (complete_worker_task, c.save(expected_rate, expected_earning) UPDATE — FREEZE per line (visibility) task.status = COMPLETED ; save UPDATE WST
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
