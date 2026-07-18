---
id: l2-request-journeys-worker-reporting
type: request-journey
status: active
owner: handwritten
scope: worker_reporting (request-journey)
anchors: —
verified: 2026-07-13
---

## TL;DR (2 min)
Worker phone reports color/size/qty → WSC (reported_quantity IMMUTABLE). Submit
freezes expected_* (visibility, not money). Gated by assignment AND live Stage Access (C-3); skill alone NOT enough.

# Journey: Worker Reporting (production truth is born)

1. **Screen:** worker phone — "My Dashboard" → "● Report needed" badge → report screen.
2. **Template:** `config/production/templates/production/worker_report.html`
 (+ `worker_report_embedded.html` for the dashboard iframe; schema-driven: chip
 pickers for choice fields, numeric for quantity, sticky Submit/Draft).
3. **URL:** `/production/addas/<code>/report/<stage_type>/` →
 `production:worker-report` (`production/urls.py`).
4. **View:** `production/views/worker_report_views.py` → `WorkerReportView`
 (`_resolve` = assignment gate: must have a non-cancelled WST on this SR;
 skill alone is NOT enough — V2-1c-iv isolation).
5. **Form:** none — lines parsed generically from `handler.contribution_schema(adda)`
 (open-closed; Cutting adds colour+size, base = qty only).
6. **Service:** `production/services/worker_task_service.py` →
 `save_draft_contributions` (Save Draft) / `report_contributions` +
 `complete_worker_task` (Submit). `@transaction.atomic`.
7. **Models READ:** WorkerStageTask (the worker's own), AddaStageRecord, the stage handler schema.
8. **Models WRITTEN:** WorkerStageContribution (INSERT — reported_quantity IMMUTABLE) ·
 on Submit: WST.status=COMPLETED + WSC.expected_rate/expected_earning FROZEN (UPDATE, visibility only).
9. **Transaction boundary:** the service call; no cross-worker locks needed (own task).
10. **Constraints:** WSC `reported_quantity > 0`; WST partial-unique active task; expected_* ≥ 0.
11. **ADRs:** 0005 (expected_* = visibility, never money), 0001 (service writes).
12. **Future:** TM-2 barcode scans will feed the SAME service (C-TM); none-mode
 (TM-1) → tasks resolve participated-without-report instead of auto-cancel.

Chokepoint: [../CHOKEPOINTS/worker_task_service.md](../CHOKEPOINTS/worker_task_service.md).

### How would I debug this in production?
- **First file:** `production/views/worker_report_views.py:WorkerReportView._resolve` (the gate).
- **First breakpoint:** `_resolve` (403 source) or `worker_task_service.report_contributions`.
- **First query:** `SELECT id,status,reported_quantity,verified_quantity FROM production_workerstagecontribution WHERE task_id=<id>;`
- **First log:** `worker_task.report` / `worker_task.complete`.
- **Failure modes:** 403 = no active WST on this SR (assignment) OR stage access revoked in the hub (C-3 freeze closeout — live `user_can_access_stage` check); "report needed" badge stuck = task still assigned/in_progress; lines vanished = stage completed → F3 auto-cancel.
- **Expected DB state:** after submit, WST.status=completed + each WSC has frozen expected_rate/earning.
- **Recovery path:** wrong report → management `set_verified_quantity` (reported stays); stage wrongly completed → reopen (if not settled).

### Confidence
**Verified from code (verified against commit f067daf0, 2026-06-12; re-verify the cited file if it changed)** (worker_task_service set/report/complete; worker_report_views._resolve). Tests: production/tests/test_worker_task.py, test_worker_report_view.py.
