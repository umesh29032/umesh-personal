# Journey: Stage Completion (+ cost freeze + auto-cancel)

## TL;DR (1 min)
"Mark Complete" → stage closes, Adda advances, processing_cost freezes, unreported
tasks auto-cancel (F3). Settled stage REFUSES reopen.

**URL** per-stage `*-complete` (e.g. `production:cutting-workspace-complete`,
`layering-complete`). **View** the stage *CompleteView (stage_views / pattern /
barcode_gen). **Service** stage service complete_* → `adda_service` advance funnel
→ `cost_service.freeze_stage_cost` + `worker_task_service.resolve_stage_tasks_on_complete`.
**Models read** typed stage record, WorkerStageTask. **Models written**
AddaStageRecord (completed_at, frozen processing_cost), Adda (current_stage / status),
WorkerStageTask (unreported → CANCELLED), AddaHistory (stage advanced). **Tx** atomic.
**RBAC** management/skill. **ADRs** 0009 (cost freeze). **Tables**
production_addastagerecord, production_adda, production_workerstagetask, tracking_addahistory.

### How would I debug this in production?
- **First file:** `production/services/adda_service.py` (advance funnel ~ + the stage's complete_*.
- **First breakpoint:** `freeze_stage_cost` (cost) / `resolve_stage_tasks_on_complete` (auto-cancel).
- **First query:** `SELECT completed_at,processing_cost FROM production_addastagerecord WHERE id=<id>;`
- **First log:** `cost.freeze`, `stage.reopen` (if reopened), stage complete logs.
- **Failure modes:** worker lost pay = reported-after-complete (F3 cancelled them; P2 dialog should have warned); processing_cost NULL = unpriced (honest-NULL); reopen refused = stage is settlement-credited (reverse the ADST first).
- **Expected DB state:** completed_at set; processing_cost frozen-or-NULL; unreported tasks cancelled; completed/verified tasks untouched.
- **Recovery:** reopen (clears cost, re-freezes on re-complete) — only if not settled.

### Confidence
**Verified from code (verified against commit f067daf0, 2026-06-12; re-verify the cited file if it changed)** (adda_service advance funnel; freeze_stage_cost; resolve_stage_tasks_on_complete). Tests: test_reopen_voids_pay.py, test_stage_credit.py. **Architectural interpretation** on exact per-stage complete_* internals (vary by stage).
