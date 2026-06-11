"""Barcode-generation stage record + the (stub) label-print queue.

Subdomain of the production models package. Per-piece barcodes themselves live
in the `tracking` app (BarcodeBatch/BatchBarcode); this is the production-side
stage record that drives generation.
"""
from django.db import models

from core.models import TimeStampedModel

from .adda import AddaStageRecord


class BarcodeGenerationRecord(TimeStampedModel):
    """Barcode Generation stage ka typed record.

    Mirror of `LayeringRecord` / `CuttingRecord` / `CuttingPatternRecord` —
    OneToOne `AddaStageRecord` jo `barcode_generation` workflow stage pe hai.

    `total_barcodes` denormalised hota hai = SUM(BarcodeBatch.total_pieces).
    Generation idempotent — re-run pe rows nahi badhte (one-shot in service).

    Lifecycle:
        start_barcode_generation()       → worker tasks set + record exists
        generate_barcodes()              → BarcodeBatch rows + total_barcodes
                                            denorm + generated_at stamp
        complete_barcode_generation()    → count match validation + advance
        reopen_barcode_generation()      → cleared if no scans + no exports
    """

    stage_record = models.OneToOneField(
        AddaStageRecord, on_delete=models.CASCADE,
        related_name='barcode_generation',
    )
    # Denorm SUM(BarcodeBatch.total_pieces) — updated by service on generate
    total_barcodes = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)
    # Set when generate_barcodes() runs successfully; None until then
    generated_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"BarcodeGen · {self.stage_record.adda.code} · {self.total_barcodes}"


class LabelPrintQueue(TimeStampedModel):
    """STUB — future vendor/factory label printing workflow.

    Designed-only-in-PR-A; no service logic yet. Per BARCODE_STAGE_PLAN.md
    §13: "Implement label print queue logic — deferred per user instruction."

    Future flow:
        Barcode generated → Export to vendor → Vendor prints → Labels received
        → Labels stitched → Future Manufacturing Tracking

    When real workflow lands:
        • Service adds rows on export completion (vendor case)
        • Status transitions logged via tracking.AddaHistory
        • Factory-printer integration writes printed_at directly
    """

    # FK to tracking.BarcodeExportBatch — string FK to avoid cycle
    export_batch = models.ForeignKey(
        'tracking.BarcodeExportBatch', on_delete=models.PROTECT,
        related_name='label_print_queue_rows',
    )

    class Status(models.TextChoices):
        QUEUED = 'queued', 'Queued'
        SENT = 'sent', 'Sent to vendor'
        RECEIVED = 'received', 'Labels received'
        PRINTED = 'printed', 'Printed (factory)'
        CANCELLED = 'cancelled', 'Cancelled'

    vendor_name = models.CharField(max_length=120, blank=True)
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.QUEUED,
    )
    sent_at = models.DateTimeField(null=True, blank=True)
    received_at = models.DateTimeField(null=True, blank=True)
    printed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['status', '-created_at'])]

    def __str__(self):
        return f"PrintQueue · {self.export_batch.export_code} · {self.status}"
