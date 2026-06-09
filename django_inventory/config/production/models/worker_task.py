"""WorkerStageTask — per-worker lifecycle + object-level Assignment (V2-1a).

Subdomain of the production models package. This is the V2 production-truth
replacement for the bare `AddaStageRecord.workers` M2M: one row per
(stage_record, worker) carrying a real lifecycle (assigned → in_progress →
completed → [verified], or cancelled) and the per-worker timestamps the M2M
never recorded.

V2-1a scope: the model + a reversible backfill from the M2M, written behind a
dual-write chokepoint while the M2M stays authoritative (readers repoint in
V2-1b). NO money here — Option B books earnings only at settlement.
See docs/ARCHITECTURE_V2.md §2 + docs/V2_1_REVIEW.md §10.

`WorkerStageContribution` (quantity + frozen expected_*) is deferred to V2-1c,
where its writer (worker self-report + complete-time freeze) lands.
"""
from django.conf import settings
from django.db import models

from core.models import TimeStampedModel


class WorkerStageTask(TimeStampedModel):
    """One worker's assignment + lifecycle on a specific AddaStageRecord.

    Owns lifecycle + the object-level Assignment access layer (worker stage
    access = Skill AND an active task here). NOT money, NOT quantity.
    `cancelled` is terminal — un-assigning a worker cancels their task (never
    deletes it), so production history stays immutable (owner rule).
    """

    class Status(models.TextChoices):
        # TextChoices = DB-stored string + human label; forward-only lifecycle.
        ASSIGNED = 'assigned', 'Assigned'
        IN_PROGRESS = 'in_progress', 'In Progress'
        COMPLETED = 'completed', 'Completed'
        VERIFIED = 'verified', 'Verified'      # OPTIONAL — never a stage-advance gate
        CANCELLED = 'cancelled', 'Cancelled'   # terminal (un-assign)

    # Live (non-cancelled) statuses — for read filters that replace the M2M (V2-1b).
    ACTIVE_STATUSES = ('assigned', 'in_progress', 'completed', 'verified')

    # PROTECT mirrors SWA/AddaStageRecord: never orphan a task that may carry
    # contributions / feed a settlement later.
    stage_record = models.ForeignKey(
        'production.AddaStageRecord', on_delete=models.PROTECT,
        related_name='worker_tasks',
    )
    worker = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='stage_tasks',
    )
    status = models.CharField(
        max_length=12, choices=Status.choices, default=Status.ASSIGNED,
    )
    # Per-worker timeline. null=True: backfilled rows inherit only the stage-level
    # timestamps; legacy stages may have null started_at even when completed.
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    # null=True (DB) but NOT blank — required at form level, matches created_by posture.
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        null=True, related_name='+',
    )
    notes = models.CharField(max_length=200, blank=True)

    class Meta:
        constraints = [
            # ≤1 ACTIVE task per (stage_record, worker). Partial: cancelled rows are
            # excluded, so a cancelled worker can be re-assigned (a fresh active task).
            # Django 5.0.1: condition= on partial UniqueConstraint (NOT check=).
            models.UniqueConstraint(
                fields=['stage_record', 'worker'],
                condition=~models.Q(status='cancelled'),
                name='uniq_active_worker_task_per_stage',
            ),
            # DB backstop for the status enum (check= per Django 5.0.1).
            models.CheckConstraint(
                check=models.Q(status__in=[
                    'assigned', 'in_progress', 'completed', 'verified', 'cancelled',
                ]),
                name='workerstagetask_status_valid',
            ),
        ]
        indexes = [
            models.Index(fields=['stage_record']),
            models.Index(fields=['worker', 'status']),
        ]
        ordering = ['stage_record', 'worker']

    def __str__(self):
        return f'{self.worker_id} @ {self.stage_record_id} ({self.status})'
