"""Dual-write chokepoint for worker assignment (V2-1a).

EVERY write to `AddaStageRecord.workers` routes through here. In V2-1a the M2M
stays the AUTHORITATIVE source of truth; we ALSO maintain `WorkerStageTask` in
lockstep — V2-1d Step 0: task writes are UNCONDITIONAL (tasks = the always-written store); readers moved to
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
from decimal import ROUND_HALF_UP, Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

logger = logging.getLogger(__name__)


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


def set_stage_workers(stage_record, worker_ids, *, cancel_note: str = ''):
    """Full-replace the stage's workers. M2M `.set()` (authoritative) + Task reconcile.

    Task reconcile: ensure ONE active task per id in `worker_ids`; CANCEL active
    tasks whose worker is no longer present. Idempotent. `cancel_note` (optional)
    is appended to each task cancelled by THIS call — audit trail for auto-cancels
    (F3/F8 stage-completion lifecycle).
    """
    target = {int(getattr(w, 'pk', w)) for w in (worker_ids or [])}
    stage_record.workers.set(list(target))          # M2M = source of truth in V2-1a
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
            if cancel_note:
                task.notes = (f"{task.notes} | {cancel_note}" if task.notes else cancel_note)[:200]
            task.save(update_fields=['status', 'notes', 'updated_at'])
    logger.info("worker_task.set sr=%s members=%s", stage_record.pk, sorted(target))


AUTO_CANCEL_NOTE = "auto-cancelled: stage completed without submitted report"


def resolve_stage_tasks_on_complete(stage_record):
    """F3/F8 (owner-locked 2026-06-11): a completed stage leaves NO unresolved
    active tasks. assigned / in_progress (with or without draft lines) → CANCELLED;
    completed / verified → untouched (immutable work). Draft contribution lines on
    cancelled tasks are RETAINED (evidence of partial work; invisible to business
    reads, which only consume completed tasks).

    Routed through set_stage_workers so the legacy M2M roster syncs in the same
    call — the completed-stage roster then shows only workers who actually
    reported (owner decision: truthful roster > assignment-history display), and
    M2M↔task PARITY holds by construction (check.sh gate [5/5]).
    """
    from production.models import WorkerStageTask
    keep = list(
        WorkerStageTask.objects
        .filter(stage_record=stage_record,
                status__in=(WorkerStageTask.Status.COMPLETED,
                            WorkerStageTask.Status.VERIFIED))
        .values_list('worker_id', flat=True)
    )
    set_stage_workers(stage_record, keep, cancel_note=AUTO_CANCEL_NOTE)
    logger.info("worker_task.resolve_on_complete sr=%s kept=%s",
                stage_record.pk, sorted(keep))


def add_stage_worker(stage_record, worker):
    """Additive: add ONE worker (M2M `.add`) + ensure one active task. Does NOT
    cancel others. Used by the layering skill-sync retro-tag (non-atomic)."""
    wid = int(getattr(worker, 'pk', worker))
    stage_record.workers.add(wid)
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


# ── V2-1c: worker self-report + complete-freeze (Option B: NO ledger here) ──────

def _ensure_task_actor(task, user):
    """The task's own worker (reports/completes own work) OR management."""
    from accounts.services import MANAGEMENT_ROLES, user_has_role
    if user_has_role(user, MANAGEMENT_ROLES):
        return
    if task.worker_id != getattr(user, 'pk', None):
        raise PermissionDenied("not your task")


@transaction.atomic
def report_contributions(task, lines, *, actor):
    """Worker submits reported production lines (append-only) for their task.

    Each line = {reported_quantity, color_id?, size_id?, bundle_item_id?}. Creates
    WorkerStageContribution rows; `expected_*` stay NULL (frozen later at complete —
    Option B, no money here). Moves an `assigned` task to `in_progress`. Rejected
    once the task is completed/verified/cancelled (locked after submit).
    """
    from production.models import WorkerStageContribution, WorkerStageTask
    _ensure_task_actor(task, actor)
    locked = (WorkerStageTask.Status.COMPLETED, WorkerStageTask.Status.VERIFIED,
              WorkerStageTask.Status.CANCELLED)
    if task.status in locked:
        raise ValidationError("Cannot report on a completed or cancelled task.")
    created = []
    for line in lines:
        qty = Decimal(str(line['reported_quantity']))
        if qty <= 0:
            raise ValidationError("reported_quantity must be greater than 0.")
        created.append(WorkerStageContribution.objects.create(
            task=task,
            reported_quantity=qty,
            color_id=line.get('color_id'),
            size_id=line.get('size_id'),
            bundle_item_id=line.get('bundle_item_id'),
        ))
    if task.status == WorkerStageTask.Status.ASSIGNED:
        task.status = WorkerStageTask.Status.IN_PROGRESS
        if task.started_at is None:
            task.started_at = timezone.now()
        task.save(update_fields=['status', 'started_at', 'updated_at'])
    logger.info("worker_task.report task=%s lines=%s", task.pk, len(created))
    return created


@transaction.atomic
def save_draft_contributions(task, lines, *, actor):
    """Save the worker's DRAFT contribution lines — operational convenience, NOT
    business truth. REPLACES the task's current draft lines (so a worker can keep
    editing); allowed only while the task is not completed/cancelled. Drafts are
    excluded from costing/settlement/earnings/readiness (those read only COMPLETED
    tasks via `task.is_draft`). Business truth begins at complete_worker_task().

    Drafts are not history → clearing + rewriting them is safe (unlike completed
    work, which is immutable).
    """
    from production.models import WorkerStageTask
    _ensure_task_actor(task, actor)
    if task.status in (WorkerStageTask.Status.COMPLETED, WorkerStageTask.Status.VERIFIED,
                       WorkerStageTask.Status.CANCELLED):
        raise ValidationError("Cannot edit a completed or cancelled submission.")
    task.contributions.all().delete()           # draft ≠ history → safe to replace
    return report_contributions(task, lines, actor=actor)


@transaction.atomic
def complete_worker_task(task, *, actor):
    """Worker marks their task complete → FREEZE `expected_*` on each contribution
    (`reported_quantity × the stage rate snapshot for this worker`). NO ledger entry
    (Option B — payable is decided at Adda settlement). Immutable: a later rate edit
    never rewrites these. Verification is OPTIONAL and does NOT gate this.
    """
    from production.models import WorkerStageTask
    from production.services import cost_service
    _ensure_task_actor(task, actor)
    if task.status in (WorkerStageTask.Status.COMPLETED, WorkerStageTask.Status.VERIFIED):
        raise ValidationError("Task already completed.")
    if task.status == WorkerStageTask.Status.CANCELLED:
        raise ValidationError("Cannot complete a cancelled task.")
    ws = task.stage_record.workflow_stage
    # Same rate source as allocation_service: per-role override, else the stage rate.
    rate = cost_service.role_rate_for(ws, task.worker.role) or ws.cost_rate or Decimal('0')
    for c in task.contributions.all():
        c.expected_rate = rate
        c.expected_earning = (c.reported_quantity * rate).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP)
        c.save(update_fields=['expected_rate', 'expected_earning', 'updated_at'])
    task.status = WorkerStageTask.Status.COMPLETED
    task.completed_at = timezone.now()
    task.save(update_fields=['status', 'completed_at', 'updated_at'])
    logger.info("worker_task.complete task=%s contributions=%s rate=%s",
                task.pk, task.contributions.count(), rate)
    return task
