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


class TimeStampedModel(models.Model):
    """Abstract base — tracking rows ke timestamps.

    `created_at` insert pe set, baad mein change nahi.
    `updated_at` mutations track karta hai — BatchBarcode ke liye useful (status badle).
    History rows append-only hain to wahan updated_at = created_at rehta hai (harmless).
    """

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


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
        # Ek Adda mein same (color, size) combo do baar nahi. Legacy null+null
        # batch sirf ek baar (legacy Addas mein only one batch total).
        unique_together = [('adda', 'color', 'size')]
        indexes = [
            models.Index(fields=['adda', 'start_seq']),
            models.Index(fields=['adda', 'end_seq']),
        ]
        ordering = ['adda', 'start_seq']

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
        ]
        ordering = ['adda', 'piece_seq']

    def __str__(self):
        return self.value


# ── Per-domain history tables ─────────────────────────────────────────────────
# Sirf history_service.log_*() in tables ko likhta hai. View-side create NAHI.

class ClothRollHistory(TimeStampedModel):
    """ClothRoll pe har state change ka audit row."""

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
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='+',
    )
    # Audit triple — kya field, kya old/new value
    field_name = models.CharField(max_length=64, blank=True)
    old_value = models.CharField(max_length=200, blank=True)
    new_value = models.CharField(max_length=200, blank=True)
    note = models.CharField(max_length=200, blank=True)

    class Meta:
        # roll-detail timeline ko fast banata hai (roll FK + created_at DESC)
        indexes = [models.Index(fields=['roll', '-created_at'])]
        ordering = ['-created_at']


class AddaHistory(TimeStampedModel):
    """Adda pe stage transitions + state changes ka audit log."""

    class ChangeType(models.TextChoices):
        CREATED = 'created', 'Created'
        STAGE_ADVANCED = 'stage_advanced', 'Stage Advanced'
        STAGE_REOPENED = 'stage_reopened', 'Stage Reopened'
        STATUS_CHANGED = 'status_changed', 'Status Changed'
        ROLL_ASSIGNED = 'roll_assigned', 'Roll Assigned'
        COMPLETED = 'completed', 'Completed'

    adda = models.ForeignKey(
        'production.Adda', on_delete=models.PROTECT, related_name='history',
    )
    change_type = models.CharField(max_length=32, choices=ChangeType.choices)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='+',
    )
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
    note = models.CharField(max_length=200, blank=True)

    class Meta:
        indexes = [models.Index(fields=['adda', '-created_at'])]
        ordering = ['-created_at']


class ProductHistory(TimeStampedModel):
    """Product pe field-level edits ka audit log."""

    class ChangeType(models.TextChoices):
        CREATED = 'created', 'Created'
        UPDATED = 'updated', 'Updated'
        ARCHIVED = 'archived', 'Archived'

    product = models.ForeignKey(
        'production.Product', on_delete=models.PROTECT, related_name='history',
    )
    change_type = models.CharField(max_length=32, choices=ChangeType.choices)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='+',
    )
    field_name = models.CharField(max_length=64, blank=True)
    old_value = models.CharField(max_length=200, blank=True)
    new_value = models.CharField(max_length=200, blank=True)

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
