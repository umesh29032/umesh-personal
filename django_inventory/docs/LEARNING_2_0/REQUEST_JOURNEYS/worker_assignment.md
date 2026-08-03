---
id: l2-request-journeys-worker-assignment
type: request-journey
status: active
owner: handwritten
scope: worker_assignment (request-journey)
anchors: —
verified: 2026-07-13
---

# Journey: Worker Assignment (roster)

## TL;DR (1 min)
Manager ticks workers on a stage → set_stage_workers (full-replace; cancel-not-delete).

**URL** stage workspace (e.g. `production:cutting-start` / layering-start) POST.
**View** the stage's *StartView / workspace action (production/views/stage_views.py).
**Form** worker checkbox→chip widget (`production/forms/_shared.py`). **Service**
`worker_task_service.set_stage_workers(sr, ids)`. **Models read** WorkerStageTask
(existing active). **Models written** WorkerStageTask (INSERT new; UPDATE removed→
CANCELLED). **Tx** caller's @atomic; `select_for_update` on active tasks.
**RBAC** management + stage skill. **ADRs** 0001/0002 (gate 4/4). **Tables**
production_workerstagetask. **Payload** `workers=3&workers=7`. **Before→after**
unticked worker's task → status=CANCELLED (notes kept), new tick → INSERT assigned.

### How would I debug this in production?
- **First file:** `worker_task_service.py:set_stage_workers`.
- **First breakpoint:** the create/cancel loop/.
- **First query:** `SELECT worker_id,status,notes FROM production_workerstagetask WHERE stage_record_id=<id>;`
- **First log:** `worker_task.set`.
- **Failure modes:** worker missing from pool = no SKILL (Access Control), not a bug; "roster shows cancelled" = expected (history). Concurrent saves → second waits (select_for_update).
- **Expected DB state:** ≤1 ACTIVE task per (sr,worker); removed = cancelled rows present.
- **Recovery:** re-tick a cancelled worker → fresh active task (partial-unique allows it).

### Confidence
**Verified from code (verified against commit f067daf0, 2026-06-12; re-verify the cited file if it changed)** (worker_task_service). Tests: test_worker_task.py.
