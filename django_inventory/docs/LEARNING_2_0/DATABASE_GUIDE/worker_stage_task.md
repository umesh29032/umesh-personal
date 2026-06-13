# DB: WorkerStageTask (WST) — participation truth

## TL;DR
What: one worker's assignment+lifecycle on a stage. Why: roster = who actually
participated. Writes: worker_task_service ONLY (gate 4/4). Reads: dashboards,
settlement (via WSC), worker report gate. Breaks if removed: no participation
truth; WSC has nothing to hang on. ADRs: 0005/0002. File: `config/production/models/worker_task.py`.

## Every field (key)
stage_record FK→AddaStageRecord, worker FK→User, status (assigned/in_progress/
completed/verified/cancelled), started_at/completed_at/verified_at, verified_by, notes.
**Partial-unique: one ACTIVE (stage_record,worker) WHERE status≠cancelled.**

## Example row
`stage_record=Cutting#9, worker=utest, status=completed, completed_at=…`

## FK chain
`WST → AddaStageRecord → Adda`; `WorkerStageContribution.task → WST`.

## How data reaches / leaves
IN: set_stage_workers (assign) / report+complete (status). OUT: removal = status
CANCELLED (never DELETE). Stage complete → unreported → CANCELLED (F3).

## SQL
```sql
SELECT worker_id,status FROM production_workerstagetask
WHERE stage_record_id=<id> AND status!='cancelled'; -- live roster
```

## Debug in production
403 on report = no active WST (assignment, not skill). Roster shows cancelled =
expected history. Query by stage_record_id.

### Verification Sources
production/models/worker_task.py (constraints) + worker_task_service. **Verified from code (verified against commit f067daf0, 2026-06-12; re-verify the cited file if it changed).** Tests: test_worker_task.py.
