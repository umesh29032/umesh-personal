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

    @property
    def is_draft(self) -> bool:
        """True while the worker's submission is still a DRAFT (not yet completed).
        Draft lines are operational convenience only — EXCLUDED from business truth
        (costing/settlement/earnings/readiness, which read only completed tasks).
        Business truth begins at complete (verification keeps it truth too)."""
        return self.status not in (self.Status.COMPLETED, self.Status.VERIFIED)

    def __str__(self):
        return f'{self.worker_id} @ {self.stage_record_id} ({self.status})'


class WorkerStageContribution(TimeStampedModel):
    """Dimensional production line under a WorkerStageTask (≥1 per task).

    Owns the worker-reported QUANTITY + the FROZEN expected-earning snapshot.
    NEVER money (Option B): `expected_*` is operational visibility only — frozen
    at task-complete and never re-derived, NO ledger entry. Real money is decided
    at Adda settlement. See docs/ARCHITECTURE_V2.md §5 + §11.

    color/size are captured at report time (un-backfillable — the dimensional
    grain of variance/settlement later). One worker can report many lines per
    stage (Red-M:120, Blue-L:80), so this is a line table, not a single FK.
    """

    # PROTECT: a contribution that fed a settlement must never be orphaned.
    task = models.ForeignKey(
        WorkerStageTask, on_delete=models.PROTECT, related_name='contributions',
    )
    color = models.ForeignKey(
        'raw_materials.ClothColor', on_delete=models.PROTECT,
        null=True, blank=True, related_name='+',
    )
    size = models.ForeignKey(
        'production.ProductSize', on_delete=models.PROTECT,
        null=True, blank=True, related_name='+',
    )
    # Worker-entered; LOCKED after submit. Corrections go to verified_quantity.
    reported_quantity = models.DecimalField(max_digits=12, decimal_places=2)
    # Manager/supervisor/super_admin only; null until reviewed.
    verified_quantity = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
    )
    # FROZEN at task-complete = WorkflowStage rate snapshot (4dp, matches
    # earning_rate_snapshot). null until the task completes.
    expected_rate = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True,
    )
    # FROZEN at complete = reported_quantity × expected_rate. VISIBILITY ONLY.
    expected_earning = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
    )
    # Optional piece-precision source line (cutting today; any stage later).
    bundle_item = models.ForeignKey(
        'production.CuttingBundleItem', on_delete=models.PROTECT,
        null=True, blank=True, related_name='+',
    )

    class Meta:
        indexes = [models.Index(fields=['task'])]
        ordering = ['task', 'pk']
        constraints = [
            # reported quantity is a real claim → strictly positive.
            models.CheckConstraint(
                check=models.Q(reported_quantity__gt=0),
                name='wsc_reported_quantity_positive',
            ),
            # nullable money/qty snapshots are non-negative WHEN set.
            models.CheckConstraint(
                check=models.Q(verified_quantity__isnull=True) | models.Q(verified_quantity__gte=0),
                name='wsc_verified_quantity_nonneg',
            ),
            models.CheckConstraint(
                check=models.Q(expected_rate__isnull=True) | models.Q(expected_rate__gte=0),
                name='wsc_expected_rate_nonneg',
            ),
            models.CheckConstraint(
                check=models.Q(expected_earning__isnull=True) | models.Q(expected_earning__gte=0),
                name='wsc_expected_earning_nonneg',
            ),
        ]

    def __str__(self):
        return f'contrib task={self.task_id} qty={self.reported_quantity}'
