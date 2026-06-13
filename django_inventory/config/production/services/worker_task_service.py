"""THE production-truth chokepoint (V2-1 → V2-3; M2M dropped in 0035).

SOLE writer of WorkerStageTask + WorkerStageContribution (CI gate [4/4]).
WST = participation truth (roster; cancel-not-delete). WSC = production truth:
`reported_quantity` is IMMUTABLE (owner §6); `verified_quantity` is the
management correction (P1) — both preserved forever; `expected_*` freezes at
complete and is VISIBILITY ONLY, never money (ADR-0005 Option B).

C-TM (locked): EVERY capture path — manual report today, barcode scans under
TM-2 tomorrow — must converge through these functions. A second WSC writer =
settlement paying numbers nobody can trust; that is what this gate prevents.

Reconcile rule: add missing workers as an ACTIVE task; CANCEL tasks whose worker
was removed (never delete — production history is immutable, owner rule). New
tasks copy the stage's own timestamps + status (completed if the stage completed,
else assigned) — identical to the 0032 backfill, so dual-write and backfill agree.

Leaf module: imports only settings + models (lazily), NEVER the services facade —
so stage services can import it without a circular import.

CALL CONTRACT: `set_stage_workers` must run inside the caller's @transaction.atomic
(all 6 callers are) so the M2M write + Task reconcile commit together; it locks
the active tasks with select_for_update (Hinglish: roster full-replace hai —
lock ke bina do managers ki save ek doosre ke cancel/create ko khaa jaati). `add_stage_worker` is additive and
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
    """Full-replace the stage's workers (V2-1d: WorkerStageTask is the ONLY store).

    Task reconcile: ensure ONE active task per id in `worker_ids`; CANCEL active
    tasks whose worker is no longer present. Idempotent. `cancel_note` (optional)
    is appended to each task cancelled by THIS call — audit trail for auto-cancels
    (F3/F8 stage-completion lifecycle).
    """
    target = {int(getattr(w, 'pk', w)) for w in (worker_ids or [])}
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

    Routed through set_stage_workers — the completed-stage roster (active tasks)
    then shows only workers who actually reported (owner decision: truthful
    roster > assignment-history display).
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
    """Additive: ensure ONE active task for this worker. Does NOT
    cancel others. Used by the layering skill-sync retro-tag (non-atomic)."""
    wid = int(getattr(worker, 'pk', worker))
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
    # Same rate source as allocation_service: per-role override, else the stage
    # rate. C-1 (ADR-0009): a grouped MEMBER stage freezes rate 0 outright —
    # its labor is paid via the payer stage's grouped rate, never twice.
    if ws.cost_billed_at_id is not None:
        rate = Decimal('0')
    else:
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


@transaction.atomic
def set_verified_quantity(contribution, quantity, *, actor):
    """P1 (F5-lite, ADR-0009-adjacent): management corrects PRODUCTION truth —
    sets/clears `verified_quantity` on a completed contribution. The worker's
    `reported_quantity` is NEVER touched (both preserved — owner §6/§7).
    Settlement reads verified-else-reported, so this is the lever that fixes a
    typo'd report BEFORE money books.

    Guards:
      • management only;
      • task must be completed/verified (reports in flight are the worker's);
      • a settlement-credited line (active settlement_line) REFUSES — money
        already booked on the old number; reverse the settlement first (same
        philosophy as the V2-3 reopen/void armor).
    quantity=None clears the correction (back to reported).
    """
    from django.core.exceptions import PermissionDenied
    from accounts.services import MANAGEMENT_ROLES, user_has_role
    from production.models import WorkerStageContribution, WorkerStageTask

    if not user_has_role(actor, MANAGEMENT_ROLES):
        raise PermissionDenied("Only management can verify quantities.")
    # of=('self',): settlement_line is a nullable FK → LEFT JOIN, and Postgres
    # refuses FOR UPDATE on the nullable side — lock only the WSC row.
    c = (WorkerStageContribution.objects.select_for_update(of=('self',))
         .select_related('task', 'settlement_line')
         .get(pk=contribution.pk))
    if c.task.status not in (WorkerStageTask.Status.COMPLETED,
                             WorkerStageTask.Status.VERIFIED):
        raise ValidationError("Report not submitted yet — nothing to verify.")
    if c.settlement_line_id and c.settlement_line.voided_at is None:
        raise ValidationError(
            "This line was already settled "
            f"({c.settlement_line.adda_settlement.reference}) — reverse that "
            "settlement first, then correct the quantity.")
    if quantity is not None:
        quantity = Decimal(str(quantity))
        if quantity < 0:
            raise ValidationError("Verified quantity cannot be negative.")
    c.verified_quantity = quantity
    c.save(update_fields=['verified_quantity', 'updated_at'])
    logger.info("worker_task.verify_qty wsc=%s task=%s qty=%s by=%s",
                c.pk, c.task_id, quantity, actor.pk)
    return c
