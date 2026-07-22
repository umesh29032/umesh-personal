"""Tracking app ke models — barcodes + per-domain audit history.

YEH FILE KYU HAI?
─────────────────
Do alag domains:
  1. BatchBarcode — piece-level QR codes (Cutting stage generate karta hai)
  2. *History     — per-domain audit log (ClothRoll/Adda/Product)

Discipline:
  • BatchBarcode rows har Adda ke liye ek hi baar bulk_created (one-shot).
  • History tables sirf history_service.log_*() ke through likhe jaate hain.
    NA signals, NA save() overrides, NA view-side create. Single-writer pattern.
"""
from django.conf import settings
from django.db import models

# Shared kernel bases — single source in core (were duplicated per app).
from core.models import AbstractHistoryEntry, FieldChangeMixin, TimeStampedModel


class BarcodeBatch(TimeStampedModel):
    """Barcode range record — contiguous seq block for ek (Adda, Color, Size) combo.

    YEH MODEL KYU HAI?
    ──────────────────
    Cutting stage complete pe har (color, size) ke liye ek contiguous range
    allocate hota hai. e.g.:
        Red S    → seq  1..60   (60 pieces)
        Blue S   → seq 61..110  (50 pieces)
        Green S  → seq 111..160 (50 pieces)
        Blue L   → seq 161..200 (40 pieces)
    Storage: 4 BarcodeBatch rows (not 200 BatchBarcode rows). Performance
    win — 500-piece Adda mein 5 batches vs 500 rows.

    Per-piece state (status / last_scanned_at) `BatchBarcode` mein lazily
    create hota hai jab pehli baar scan ho. Bina scan ke koi row nahi.

    Lookup pattern:
      value = '{ADDA}-{SEQ:04d}'
      → adda + seq parse
      → BarcodeBatch.objects.filter(adda=, start_seq__lte=seq, end_seq__gte=seq).first()
    """

    # PROTECT = Adda delete blocked agar barcode batches hain
    adda = models.ForeignKey(
        'production.Adda', on_delete=models.PROTECT, related_name='barcode_batches',
    )
    # Denormalized FK — adda.product ka redundant copy. Query speed-up
    # (filter by product directly without JOIN through adda).
    product = models.ForeignKey(
        'production.Product', on_delete=models.PROTECT, related_name='+',
    )
    # PR11 (2026-05-28): direct link to source bundle. nullable for legacy
    # batches (NIKKAR-style without bundles). Lets future stages query
    # "all barcodes from Bundle X" without going through adda+size.
    bundle = models.ForeignKey(
        'production.CuttingBundle', on_delete=models.PROTECT,
        null=True, blank=True, related_name='barcode_batches',
    )
    # null=True for legacy NIKKAR-style single-batch with no breakup metadata.
    color = models.ForeignKey(
        'raw_materials.ClothColor', on_delete=models.PROTECT,
        null=True, blank=True, related_name='+',
    )
    size = models.ForeignKey(
        'production.ProductSize', on_delete=models.PROTECT,
        null=True, blank=True, related_name='+',
    )
    # 1-indexed within Adda. Inclusive both ends.
    start_seq = models.PositiveIntegerField()
    end_seq = models.PositiveIntegerField()
    # Denormalized: end_seq - start_seq + 1. Stored for direct query.
    total_pieces = models.PositiveIntegerField()

    class Meta:
        # IDENTITY LAW append (2026-07-11): a late Cutting Stream may add a
        # SECOND batch for the same (color, size) — ranges are the identity
        # truth, so uniqueness moved to (adda, start_seq); non-overlap is
        # guaranteed by the Max(end_seq)+1 allocation under the writers.
        unique_together = [('adda', 'start_seq')]
        indexes = [
            models.Index(fields=['adda', 'start_seq']),
            models.Index(fields=['adda', 'end_seq']),
        ]
        ordering = ['adda', 'start_seq']
        # Range invariants — a batch is a contiguous inclusive seq block, and
        # total_pieces is its denormalized width. These guard the lazy-scan
        # lookup math (filter start_seq<=seq<=end_seq) from corrupt ranges.
        constraints = [
            models.CheckConstraint(
                check=models.Q(end_seq__gte=models.F('start_seq')),
                name='tracking_batch_seq_order',
            ),
            models.CheckConstraint(
                check=models.Q(total_pieces__gt=0),
                name='tracking_batch_pieces_positive',
            ),
            models.CheckConstraint(
                check=models.Q(total_pieces=models.F('end_seq') - models.F('start_seq') + 1),
                name='tracking_batch_pieces_consistent',
            ),
        ]

    def __str__(self):
        bits = [self.adda.code]
        if self.size_id:
            bits.append(self.size.code.upper() if self.size else '?')
        if self.color_id:
            bits.append(self.color.name if self.color else '?')
        bits.append(f"{self.start_seq:04d}..{self.end_seq:04d}")
        return ' · '.join(bits)

    @property
    def start_value(self) -> str:
        return f"{self.adda.code}-{self.start_seq:04d}"

    @property
    def end_value(self) -> str:
        return f"{self.adda.code}-{self.end_seq:04d}"

    def value_for_seq(self, seq: int) -> str:
        """Render the canonical barcode value for a seq inside this batch."""
        if not (self.start_seq <= seq <= self.end_seq):
            raise ValueError(
                f"seq {seq} outside batch range {self.start_seq}..{self.end_seq}"
            )
        return f"{self.adda.code}-{seq:04d}"


class BatchBarcode(TimeStampedModel):
    """Per-piece scan state — lazy-created on first scan from BarcodeBatch.

    Value format: '{ADDA_CODE}-{PIECE_SEQ:04d}' e.g. 'T-SHIRT-001-0042'.
    QR payload: '{BASE_URL}/tracking/scan/{value}/' — phone camera natively scan kar leta hai.

    Yeh row sirf tab create hota hai jab piece scan ho ya status update ho.
    Untouched pieces ka koi BatchBarcode row nahi — sirf BarcodeBatch range
    cover karta hai.
    """

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'          # barcode generated but piece not yet processed
        PACKED = 'packed', 'Packed'             # sticker attached + packed
        DISPATCHED = 'dispatched', 'Dispatched'
        MISSING = 'missing', 'Missing'

    # PROTECT = Adda delete ko block kar dega agar uske barcodes hain
    adda = models.ForeignKey(
        'production.Adda', on_delete=models.PROTECT, related_name='barcodes',
    )
    # FK back to source batch — populated on lazy create. null=True for
    # legacy rows (pre-PR6) that didn't have batches.
    batch = models.ForeignKey(
        'tracking.BarcodeBatch', on_delete=models.PROTECT,
        null=True, blank=True, related_name='scanned_pieces',
    )
    piece_seq = models.PositiveIntegerField()       # 1..N within an Adda
    value = models.CharField(max_length=60, unique=True)
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.PENDING,
    )
    last_scanned_at = models.DateTimeField(null=True, blank=True)
    last_scanned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        null=True, blank=True, related_name='+',
    )
    # ── Metadata FKs (added 2026-05-28; phase-1 schema only) ────────────────
    # nullable = legacy barcodes (pre-cutting-overhaul) have no breakup row.
    # Future barcodes generated by new generate_for_cutting() set all four.
    # String FKs avoid import cycle (tracking can't import production safely).
    size = models.ForeignKey(
        'production.ProductSize', on_delete=models.PROTECT,
        null=True, blank=True, related_name='+',
    )
    color = models.ForeignKey(
        'raw_materials.ClothColor', on_delete=models.PROTECT,
        null=True, blank=True, related_name='+',
    )
    pattern = models.ForeignKey(
        'production.ProductPattern', on_delete=models.PROTECT,
        null=True, blank=True, related_name='+',
    )
    roll = models.ForeignKey(
        'raw_materials.ClothRoll', on_delete=models.PROTECT,
        null=True, blank=True, related_name='+',
    )

    class Meta:
        # Ek Adda mein piece_seq unique — duplicate sticker nahi
        unique_together = [('adda', 'piece_seq')]
        indexes = [
            # Adda + status filter (dashboards mein common)
            models.Index(fields=['adda', 'status']),
            # Status-only KPI counts
            models.Index(fields=['status']),
            # Per-size/color status breakdown — "kitne medium-red dispatched"
            models.Index(fields=['size', 'color', 'status']),
            # All scanned pieces in a batch (this is the table that grows largest).
            models.Index(fields=['batch', 'status']),
            # Recent-scans activity feed.
            models.Index(fields=['-last_scanned_at']),
        ]
        ordering = ['adda', 'piece_seq']

    def __str__(self):
        return self.value


# ── Per-domain history tables ─────────────────────────────────────────────────
# Sirf history_service.log_*() in tables ko likhta hai. View-side create NAHI.

class ClothRollHistory(FieldChangeMixin, AbstractHistoryEntry):
    """ClothRoll pe har state change ka audit row.

    `actor` AbstractHistoryEntry se, field-diff trio FieldChangeMixin se aata hai.
    """

    class ChangeType(models.TextChoices):
        CREATED = 'created', 'Created'
        STATUS_CHANGED = 'status_changed', 'Status Changed'   # e.g. not_used → used (assign)
        LOCATION_MOVED = 'location_moved', 'Location Moved'
        WEIGHT_UPDATED = 'weight_updated', 'Weight Updated'
        ARCHIVED = 'archived', 'Archived'

    roll = models.ForeignKey(
        'raw_materials.ClothRoll', on_delete=models.PROTECT, related_name='history',
    )
    change_type = models.CharField(max_length=32, choices=ChangeType.choices)
    note = models.CharField(max_length=200, blank=True)

    class Meta:
        # roll-detail timeline ko fast banata hai (roll FK + created_at DESC)
        indexes = [models.Index(fields=['roll', '-created_at'])]
        ordering = ['-created_at']


class AddaHistory(AbstractHistoryEntry):
    """Adda pe stage transitions + state changes ka audit log.

    `actor` AbstractHistoryEntry se. Field-diff trio NAHI (stage transitions log
    karta hai, scalar diffs nahi) — isliye FieldChangeMixin use nahi karta.
    """

    class ChangeType(models.TextChoices):
        CREATED = 'created', 'Created'
        STAGE_ADVANCED = 'stage_advanced', 'Stage Advanced'
        STAGE_REOPENED = 'stage_reopened', 'Stage Reopened'
        STATUS_CHANGED = 'status_changed', 'Status Changed'
        ROLL_ASSIGNED = 'roll_assigned', 'Roll Assigned'
        ROLL_REMOVED = 'roll_removed', 'Roll Removed'
        COMPLETED = 'completed', 'Completed'
        COST_FROZEN = 'cost_frozen', 'Cost Frozen'   # manufacturing cost snapshot at stage advance
        STAGE_STARTED = 'stage_started', 'Stage Started'
        WORKERS_ASSIGNED = 'workers_assigned', 'Workers Assigned'
        BUNDLE_CREATED = 'bundle_created', 'Bundle Created'
        BARCODES_GENERATED = 'barcodes_generated', 'Barcodes Generated'
        EXPORTED = 'exported', 'Exported'
        # V2-2: the financial closing events join the Adda timeline (Part 13).
        SETTLEMENT_FINALIZED = 'settlement_finalized', 'Settlement Finalized'
        SETTLEMENT_REVERSED = 'settlement_reversed', 'Settlement Reversed'
        SETTLEMENT_SUPERSEDED = 'settlement_superseded', 'Settlement Superseded'
        # R3 (PDD §27-C3): super-admin forced a stage complete past pending
        # workers. metadata = {stage, pending_workers, pending_count, reason};
        # actor/created_at carry who/when — audit-complete by itself, never
        # dependent on external logs (owner instruction 2026-07-04).
        COMPLETION_OVERRIDE = 'completion_override', 'Completion Override'
        # R6 (PDD §31.1-F6): management corrected a reported quantity.
        # metadata = {contribution, worker, worker_id, stage, reported, old,
        # new}; new=None means "correction cleared, back to reported". DB-
        # resident audit (owner: investigations never depend on app logs).
        VERIFIED_QTY_CORRECTED = 'verified_qty_corrected', 'Verified Qty Corrected'
        # Pre-Phase-3 D (owner 2026-07-06): manager VOIDED a submitted report so
        # the worker can re-report — the audited path for corrections that would
        # INCREASE production (verification only confirms/reduces). metadata =
        # {task, new_task, worker, worker_id, stage, reason,
        # lines:[{color,size,good,alter,missing,damaged}]}.
        REPORT_VOIDED = 'report_voided', 'Report Voided'
        # GAP-4 (lifecycle §9.5): the two lane-lifecycle events land with the
        # Add-lane flow. metadata = {stream_id, fabric_group, sequence, reason}.
        STREAM_ADDED = 'stream_added', 'Cutting Lane Added'
        STREAM_CANCELLED = 'stream_cancelled', 'Cutting Lane Cancelled'
        # Owner rule 2026-07-22: super_admin ABANDONED the whole batch (soft —
        # status→CANCELLED, record kept). metadata = {reason, prev_status,
        # cancelled_tasks}. Distinct from a hard delete (which leaves no row to
        # log against). The one path that writes Adda.status = CANCELLED.
        ADDA_CANCELLED = 'adda_cancelled', 'Adda Cancelled'

    adda = models.ForeignKey(
        'production.Adda', on_delete=models.PROTECT, related_name='history',
    )
    change_type = models.CharField(max_length=32, choices=ChangeType.choices)
    # Stage transition: NULL-NULL on CREATED, real values on STAGE_ADVANCED
    stage_from = models.ForeignKey(
        'production.WorkflowStage', on_delete=models.PROTECT,
        null=True, blank=True, related_name='+',
    )
    stage_to = models.ForeignKey(
        'production.WorkflowStage', on_delete=models.PROTECT,
        null=True, blank=True, related_name='+',
    )
    # roll FK — sirf ROLL_ASSIGNED events ke liye
    roll = models.ForeignKey(
        'raw_materials.ClothRoll', on_delete=models.PROTECT,
        null=True, blank=True, related_name='+',
    )
    # Execution-row link for single-stage events (started/workers/bundle/cost/
    # barcodes/exported). Binds to the AddaStageRecord, NOT WorkflowStage —
    # two Addas share one WorkflowStage but each has its own execution row.
    # SET_NULL so a rare stage-record delete preserves the audit row.
    stage_record = models.ForeignKey(
        'production.AddaStageRecord', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='+',
    )
    note = models.CharField(max_length=200, blank=True)
    # Sparse per-event payload (jsonb). e.g. COST_FROZEN carries
    # {method, rate, qty, cost}. Queried dimensions stay typed FK columns;
    # JSON holds only event-specific extras. default=dict so existing rows
    # read {} (additive-safe migration).
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['adda', '-created_at']),
            # global recent-events feed on the management landing page
            # (ORDER BY created_at DESC LIMIT n) — adda-led index can't serve it
            models.Index(fields=['-created_at']),
        ]
        ordering = ['-created_at']


class ProductHistory(FieldChangeMixin, AbstractHistoryEntry):
    """Product pe field-level edits ka audit log.

    `actor` AbstractHistoryEntry se, field-diff trio FieldChangeMixin se.
    """

    class ChangeType(models.TextChoices):
        CREATED = 'created', 'Created'
        UPDATED = 'updated', 'Updated'
        ARCHIVED = 'archived', 'Archived'

    product = models.ForeignKey(
        'production.Product', on_delete=models.PROTECT, related_name='history',
    )
    change_type = models.CharField(max_length=32, choices=ChangeType.choices)

    class Meta:
        indexes = [models.Index(fields=['product', '-created_at'])]
        ordering = ['-created_at']


# ── Barcode Export tracking (PR-A 2026-05-29) ───────────────────────────────
# YEH MODEL KYU HAI?
# Barcode Generation stage complete hone par vendor / factory ke liye exports
# generate hote hain (CSV / XLSX / PDF). Yeh table sirf manifest header
# track karta hai — actual file content live BarcodeBatch + breakdown data
# se on-the-fly regenerate hota hai (storage bloat avoid).
#
# Audit + re-download: same export_code se baad mein dobara download possible.
# Future LabelPrintQueue iss row se attach hoga (vendor lifecycle tracking).


class BarcodeExportBatch(TimeStampedModel):
    """Barcode export manifest — vendor/factory label printing ke liye.

    Lifecycle:
        Barcode Gen stage complete  → Cutting Master export trigger karta hai
                                       (CSV / XLSX / PDF)
        BarcodeExportBatch row      → manifest stored, file regenerated on
                                       download (idempotent)
        Future: LabelPrintQueue row → vendor send + receive tracking
    """

    class ExportMethod(models.TextChoices):
        CSV = 'csv', 'CSV'
        XLSX = 'xlsx', 'Excel'
        PDF = 'pdf', 'PDF Summary'

    # Stable identifier — 'EXP-2026-001' format generated by service layer
    # via SELECT FOR UPDATE counter (race-safe). Used for re-download URL.
    export_code = models.CharField(max_length=24, unique=True)
    # PROTECT — export history audit-critical
    adda = models.ForeignKey(
        'production.Adda', on_delete=models.PROTECT, related_name='barcode_exports',
    )
    # Denorm — fast dashboard filter without JOIN
    product = models.ForeignKey(
        'production.Product', on_delete=models.PROTECT, related_name='+',
    )
    # Source stage record — barcode generation must be complete before export
    barcode_gen_record = models.ForeignKey(
        'production.BarcodeGenerationRecord', on_delete=models.PROTECT,
        related_name='exports',
    )
    export_method = models.CharField(
        max_length=8, choices=ExportMethod.choices,
    )
    exported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='+',
    )
    # Denorm count — # rows in this export. SUM(BarcodeBatch.total_pieces)
    # at export time. Frozen even if barcode rows later mutate.
    total_labels = models.PositiveIntegerField()

    class Meta:
        indexes = [
            # Per-Adda export history — recent first
            models.Index(fields=['adda', '-created_at']),
            # Global recent-exports dashboard
            models.Index(fields=['-created_at']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.export_code} · {self.adda.code} · {self.export_method}"
