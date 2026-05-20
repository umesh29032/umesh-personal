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


class BatchBarcode(TimeStampedModel):
    """Ek piece-level barcode — QR sticker jo physical piece pe lagta hai.

    Value format: '{ADDA_CODE}-{PIECE_SEQ:04d}' e.g. 'T-SHIRT-001-0042'.
    QR payload: '{BASE_URL}/tracking/scan/{value}/' — phone camera natively scan kar leta hai.
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

    class Meta:
        # Ek Adda mein piece_seq unique — duplicate sticker nahi
        unique_together = [('adda', 'piece_seq')]
        indexes = [
            # Adda + status filter (dashboards mein common)
            models.Index(fields=['adda', 'status']),
            # Status-only KPI counts
            models.Index(fields=['status']),
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
