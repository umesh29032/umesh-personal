"""Adda (production batch) + AddaStageRecord (polymorphic stage-execution parent).

Subdomain of the production models package. Adda references core (Product,
WorkflowStage); AddaStageRecord is the parent that the typed stage records
(layering/cutting/...) hang off via OneToOne.

Atomic counter pattern: Adda.code service-side atomically banta hai
(`SELECT FOR UPDATE` on Product row). Concurrent create_adda(SAME_PRODUCT) race-safe.
"""
from django.conf import settings
from django.db import models

from core.models import TimeStampedModel

from .core import CostMethod, Product, WorkflowStage


class Adda(TimeStampedModel):
    """Ek production batch.

    Code format: '{Product.code}-{adda_counter:03d}' — e.g. 'T-SHIRT-001'.
    Status IN_PROGRESS rehta hai jab tak last WorkflowStage complete na ho jaaye.
    """

    class Status(models.TextChoices):
        IN_PROGRESS = 'in_progress', 'In Progress'
        ON_HOLD = 'on_hold', 'On Hold'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'

    # editable=False → admin form mein nahi dikhega; sirf service banata hai
    code = models.CharField(max_length=40, unique=True, editable=False)
    # PROTECT = product delete blocked agar koi Adda use kar raha ho
    product = models.ForeignKey(
        Product, on_delete=models.PROTECT, related_name='addas',
    )
    # current_stage NULL hota hai jab Adda COMPLETED (saare stages khatm)
    current_stage = models.ForeignKey(
        WorkflowStage, on_delete=models.PROTECT,
        null=True, blank=True, related_name='+',
    )
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.IN_PROGRESS,
    )
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        null=True, blank=True, related_name='+',
    )

    class Meta:
        indexes = [
            # Dashboards mein in_progress filter common → status index
            models.Index(fields=['status']),
            # Per-product filtered queries (product=X, status=in_progress)
            models.Index(fields=['product', 'status']),
            # Stage-wise grouping
            models.Index(fields=['current_stage']),
        ]
        ordering = ['-started_at']

    def __str__(self):
        return self.code

    @property
    def total_pieces(self) -> int:
        """Total generated barcode pieces across all BarcodeBatch ranges.

        Replaces `adda.barcodes.count()` semantics post-PR6 (per-piece
        BatchBarcode rows are now lazy on scan). Returns 0 if no batches.

        NOTE: this is a per-call aggregate query — when iterating many Addas
        (dashboards/costing), annotate `Sum('barcode_batches__total_pieces')`
        on the queryset instead of reading this property in a loop.
        """
        from django.db.models import Sum
        return self.barcode_batches.aggregate(
            total=Sum('total_pieces'),
        )['total'] or 0


class AddaStageRecord(TimeStampedModel):
    """Stage records ka polymorphic parent.

    Har Adda + WorkflowStage combination ka EK row banta hai (unique_together).
    Money side (ADR-0009): `processing_cost` = STANDARD manufacturing cost,
    frozen at stage advance (price-at-time-of-order) — worker EARNINGS se alag
    measurement hai, kabhi ADD mat karna. NULL = unpriced (honest-NULL), 0 nahi.
    Typed records (LayeringRecord, CuttingRecord) OneToOne se hang karte hain.

    Workers kahan? (V2-1d) — `WorkerStageTask` rows (one per worker, lifecycle
    + cancel-not-delete) are the SOLE assignment truth; the legacy `workers`
    M2M was dropped in migration 0035. Read via `active_workers` /
    `is_worker_assigned` / `active_worker_tasks`.
    """

    # PROTECT = frozen processing_cost snapshots are financial truth. Never let
    # an Adda delete cascade them away — Addas are CANCELLED via status, not
    # hard-deleted. (No code path deletes an Adda; this only guards admin/manual.)
    adda = models.ForeignKey(Adda, on_delete=models.PROTECT, related_name='stage_records')
    workflow_stage = models.ForeignKey(WorkflowStage, on_delete=models.PROTECT, related_name='+')
    # started_at = jab manager ne workers assign kar ke stage kick off ki.
    # null=True kyun? Legacy rows (pre-layering-workspace) sirf complete pe banti thi —
    # unhe NULL hi rakhna safe hai. Naye rows mein service hamesha set karti hai.
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    # Draft state for the stage form. Persisted before completion so user can
    # leave and return. Cleared after complete advances the Adda. Generic enough
    # to be reused by future stages (cutting, packing, ...) — each stage's
    # service reads what it needs.
    draft_layer_length_meters = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True,
    )
    draft_duration_minutes = models.PositiveIntegerField(null=True, blank=True)
    draft_notes = models.TextField(blank=True)
    completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        null=True, related_name='+',
    )
    # ── Frozen manufacturing-cost snapshot (set at advance, cleared at reopen) ─
    # This is the MANUFACTURING COST of the stage execution (product costing +
    # profitability) — NOT worker pay. Worker earnings are allocation-driven and
    # live in the future `expense` app. Frozen so a later cost_rate edit can
    # never rewrite a completed stage's cost. Grouped (billed-elsewhere) stages
    # freeze processing_cost=0.00 (priced-zero); unpriced stages freeze NULL.
    cost_method_snapshot = models.CharField(
        max_length=16, choices=CostMethod.choices, blank=True,
    )
    cost_rate_snapshot = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True,
    )
    # Decimal (not int) so future per_meter/per_kg methods need no widening.
    cost_quantity_snapshot = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
    )
    # STORED frozen result = quantize(rate x quantity, 2). NULL = unpriced
    # (never 0); 0.00 = priced but billed at a grouping payer stage.
    processing_cost = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
    )
    # Strictly advances on every re-freeze (re-complete after reopen).
    cost_frozen_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = [('adda', 'workflow_stage')]
        ordering = ['adda', 'workflow_stage__order']
        # Activity timelines + per-stage KPI dashboards.
        # (adda, -started_at) → "iss Adda ki stage history latest first"
        # (workflow_stage, completed_at) → "iss stage type ke completions"
        indexes = [
            models.Index(fields=['adda', '-started_at']),
            models.Index(fields=['workflow_stage', 'completed_at']),
        ]
        # Frozen cost snapshots are never negative. NULL = unpriced (passes the
        # CHECK); 0.00 = priced-but-billed-elsewhere (grouped). Quantity/rate same.
        constraints = [
            models.CheckConstraint(
                check=models.Q(processing_cost__gte=0),
                name='prod_asr_processingcost_nonneg',
            ),
            models.CheckConstraint(
                check=models.Q(cost_rate_snapshot__gte=0),
                name='prod_asr_costrate_nonneg',
            ),
            models.CheckConstraint(
                check=models.Q(cost_quantity_snapshot__gte=0),
                name='prod_asr_costqty_nonneg',
            ),
        ]

    @property
    def is_active(self) -> bool:
        """In-progress (started but not yet completed)."""
        return self.started_at is not None and self.completed_at is None

    # ── V2-1b: live worker set reads come from WorkerStageTask, not the M2M ──────
    # The `workers` M2M is still dual-written (until V2-1d drops it), but READS now
    # trust the Task lifecycle (cancelled = un-assigned). See docs/archive/reviews/V2_1_REVIEW.md §10.
    def active_worker_tasks(self):
        """Non-cancelled WorkerStageTask rows — the live assignment set."""
        return self.worker_tasks.exclude(status='cancelled')

    @property
    def active_workers(self):
        """Live (non-cancelled) worker Users. Reads the `worker_tasks` relation —
        prefetch `worker_tasks__worker` in loops to avoid N+1; a single-record read
        is one small query. Returns a list (drop-in for the old `workers.all()`)."""
        return [t.worker for t in self.worker_tasks.all() if t.status != 'cancelled']

    def is_worker_assigned(self, user) -> bool:
        """True if `user` has an active (non-cancelled) task on this stage."""
        return self.worker_tasks.filter(worker=user).exclude(status='cancelled').exists()

    @property
    def pending_report_workers(self):
        """P2 (F6-lite): display names of workers whose task is still UNREPORTED
        (assigned/in_progress incl. drafts) — completing the stage would
        auto-cancel them (F3: no pay eligibility). Drives the Mark-Complete
        warning dialog; read-only."""
        pending = self.worker_tasks.filter(status__in=('assigned', 'in_progress'))
        return [t.worker.get_full_name() or t.worker.email
                for t in pending.select_related('worker')]
