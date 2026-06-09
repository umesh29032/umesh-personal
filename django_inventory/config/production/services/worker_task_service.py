"""Dual-write chokepoint for worker assignment (V2-1a).

EVERY write to `AddaStageRecord.workers` routes through here. In V2-1a the M2M
stays the AUTHORITATIVE source of truth; we ALSO maintain `WorkerStageTask` in
lockstep (behind the `WORKER_TASK_DUAL_WRITE` flag) so V2-1b can flip readers to
Task with zero drift.

Reconcile rule: add missing workers as an ACTIVE task; CANCEL tasks whose worker
was removed (never delete — production history is immutable, owner rule). New
tasks copy the stage's own timestamps + status (completed if the stage completed,
else assigned) — identical to the 0032 backfill, so dual-write and backfill agree.

Leaf module: imports only settings + models (lazily), NEVER the services facade —
so stage services can import it without a circular import.

CALL CONTRACT: `set_stage_workers` must run inside the caller's @transaction.atomic
(all 6 callers are) so the M2M write + Task reconcile commit together; it locks
the active tasks with select_for_update. `add_stage_worker` is additive and
lock-free (the skill-sync retro-tag path is not atomic).
"""
import logging

from django.conf import settings

logger = logging.getLogger(__name__)


def _dual_write_enabled() -> bool:
    return getattr(settings, 'WORKER_TASK_DUAL_WRITE', True)


def _seed_status(stage_record) -> str:
    # Mirror 0032 backfill: a completed stage's tasks are 'completed', else 'assigned'.
    return 'completed' if stage_record.completed_at is not None else 'assigned'


def _new_task_kwargs(stage_record):
    # Copy the stage's own timestamps (same as backfill — keeps parity exact).
    return {
        'status': _seed_status(stage_record),
        'started_at': stage_record.started_at,
        'completed_at': stage_record.completed_at,
    }


def set_stage_workers(stage_record, worker_ids):
    """Full-replace the stage's workers. M2M `.set()` (authoritative) + Task reconcile.

    Task reconcile: ensure ONE active task per id in `worker_ids`; CANCEL active
    tasks whose worker is no longer present. Idempotent.
    """
    target = {int(getattr(w, 'pk', w)) for w in (worker_ids or [])}
    stage_record.workers.set(list(target))          # M2M = source of truth in V2-1a
    if not _dual_write_enabled():
        return
    from production.models import WorkerStageTask
    # Lock active tasks for this stage_record (caller is atomic). The partial
    # unique (one active per sr+worker) is the final race backstop.
    active = {
        t.worker_id: t
        for t in WorkerStageTask.objects
        .filter(stage_record=stage_record)
        .exclude(status=WorkerStageTask.Status.CANCELLED)
        .select_for_update()
    }
    for wid in target:
        if wid not in active:                        # missing → new active task
            WorkerStageTask.objects.create(
                stage_record=stage_record, worker_id=wid, **_new_task_kwargs(stage_record))
    for wid, task in active.items():
        if wid not in target:                        # removed → cancel (never delete)
            task.status = WorkerStageTask.Status.CANCELLED
            task.save(update_fields=['status', 'updated_at'])
    logger.info("worker_task.set sr=%s members=%s", stage_record.pk, sorted(target))


def add_stage_worker(stage_record, worker):
    """Additive: add ONE worker (M2M `.add`) + ensure one active task. Does NOT
    cancel others. Used by the layering skill-sync retro-tag (non-atomic)."""
    wid = int(getattr(worker, 'pk', worker))
    stage_record.workers.add(wid)
    if not _dual_write_enabled():
        return
    from production.models import WorkerStageTask
    # Re-activate by creating a fresh active task if none exists (a prior cancelled
    # task does not block — partial unique excludes cancelled).
    has_active = (
        WorkerStageTask.objects
        .filter(stage_record=stage_record, worker_id=wid)
        .exclude(status=WorkerStageTask.Status.CANCELLED)
        .exists()
    )
    if not has_active:
        WorkerStageTask.objects.create(
            stage_record=stage_record, worker_id=wid, **_new_task_kwargs(stage_record))
