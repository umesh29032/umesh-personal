"""Phase 7 — the APPROVED LAYOUT LIBRARY (owner persistence rules 1-10).

An Approved Layout is a MANUFACTURING ASSET: immutable, versioned,
append-only, auditable — treated exactly like a Confirmed Pattern
Design. It is a POINTER onto an immutable GeneratedMarkerCandidate
(approval never duplicates layout data — same principle as the ★
designation). History = supersede chains; nothing is ever edited or
deleted. Future Adda consumes layouts ONLY from this library (rule 9).
"""
from django.conf import settings
from django.db import models

from core.models import TimeStampedModel


class ApprovedLayout(TimeStampedModel):
    """One approved manufacturing layout. Rule 4: after approval only
    View / Duplicate / Supersede / Archive exist — the single writer
    (layout_library_service) flips STATUS ONLY; every other field is
    frozen at approval. layout_uid = the immutable ERP/Adda/barcode
    reference; version_no = the human counter (two different concepts,
    owner recommendation)."""

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        SUPERSEDED = 'superseded', 'Superseded'
        ARCHIVED = 'archived', 'Archived'

    product = models.ForeignKey(
        'production.Product', on_delete=models.PROTECT,
        related_name='approved_layouts')
    candidate = models.ForeignKey(
        'patterns_ai.GeneratedMarkerCandidate', on_delete=models.PROTECT,
        related_name='library_approvals',
        help_text='The immutable payload — placements/length/verification '
                  'live THERE; approval points, never copies.')
    layout_uid = models.CharField(
        max_length=40, unique=True, editable=False,
        help_text='Immutable ID (LAY-<product>-NNNNNN) for ERP/Adda/'
                  'barcode/audit references — never changes, never reused.')
    name = models.CharField(max_length=80, blank=True,
                            help_text='Human label; the uid is the truth.')
    version_no = models.PositiveIntegerField(
        help_text='Per-product human counter V1, V2, … (append-only).')
    fabric_group = models.CharField(
        max_length=16,
        help_text='LAW 12: one layout = one fabric group; frozen at save.')
    supersedes = models.ForeignKey(
        'self', on_delete=models.PROTECT, null=True, blank=True,
        related_name='superseded_by_layouts',
        help_text='Lineage: the layout this one replaces (rule 5).')
    status = models.CharField(max_length=16, choices=Status.choices,
                              default=Status.ACTIVE)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='+',
        help_text='Rule 8: only an explicit HUMAN act approves.')
    approved_at = models.DateTimeField()
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = 'approved layout'
        ordering = ['product_id', '-version_no']
        constraints = [
            models.UniqueConstraint(fields=['product', 'version_no'],
                                    name='pai_layout_version_per_product'),
        ]
        indexes = [models.Index(fields=['product', 'status'])]

    _status_transition = False   # set ONLY by layout_library_service

    def save(self, *args, **kwargs):
        # rule 1/4: rows are frozen at approval; the sole legal UPDATE is
        # the service-flagged status transition (supersede / archive).
        if self.pk is not None and not self._status_transition:
            raise ValueError('ApprovedLayout is immutable — supersede with '
                             'a new approval instead (rule 4).')
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError('approved layouts are never deleted — they are '
                         'manufacturing history (rule 5).')

    def __str__(self):
        return f'{self.layout_uid} (V{self.version_no}, {self.status})'


class ApprovedLayoutUsage(TimeStampedModel):
    """Phase 8A — "this Adda manufactures from this approved layout".

    Owner FREEZES: F1 manufacturing history FOREVER (delete refuses;
    wrong choice = VOID + record a new usage — NEVER reassign); F2 a
    POINTER ONLY (no placements/geometry/rotation/utilization here —
    consumers derive from layout.candidate at read; fabric_group is the
    single sanctioned denorm, an immutable attribute of an immutable
    row, copied purely so one-ACTIVE-per-(adda, fabric group) can be a
    DB constraint); F3 once recorded, the layout is the manufacturing
    CONTRACT for that fabric group. Single writer:
    layout_usage_service."""

    layout = models.ForeignKey(
        ApprovedLayout, on_delete=models.PROTECT, related_name='usages')
    adda = models.ForeignKey(
        'production.Adda', on_delete=models.PROTECT,
        related_name='layout_usages')
    stage_record = models.ForeignKey(
        'production.AddaStageRecord', on_delete=models.PROTECT,
        null=True, blank=True, related_name='+',
        help_text='Stamped at pattern-stage completion (8D) — the audit '
                  'join, mirroring MarkerUsage\'s designed shape.')
    fabric_group = models.CharField(
        max_length=16, editable=False,
        help_text='F2 denorm from the layout — constraint key only.')
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='+')
    voided_at = models.DateTimeField(null=True, blank=True)
    void_reason = models.CharField(
        max_length=200, blank=True,
        help_text='Mandatory when voiding — history explains itself.')

    class Meta:
        verbose_name = 'approved layout usage'
        constraints = [
            # exactly ONE active contract per (adda, fabric group) —
            # owner refinement 2 / readiness R-5, structural
            models.UniqueConstraint(
                fields=['adda', 'fabric_group'],
                condition=models.Q(voided_at__isnull=True),
                name='pai_usage_one_active_per_adda_group'),
            models.CheckConstraint(
                name='pai_layout_usage_void_requires_reason',
                check=models.Q(voided_at__isnull=True)
                      | ~models.Q(void_reason='')),
        ]
        indexes = [models.Index(fields=['adda', 'voided_at'])]

    _service_transition = False   # set ONLY by layout_usage_service

    def save(self, *args, **kwargs):
        # F1 + refinement 1: inserts free; the ONLY legal updates are the
        # service-flagged void / stage-record stamp — layout/adda are
        # never reassigned (wrong pick = void + new usage).
        if self.pk is not None and not self._service_transition:
            raise ValueError('ApprovedLayoutUsage is append-only — void '
                             'it and record a new usage instead (F1).')
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError('layout usages are never deleted — they are '
                         'manufacturing history forever (F1).')

    def __str__(self):
        state = 'voided' if self.voided_at else 'active'
        return f'{self.layout.layout_uid} → adda {self.adda_id} ({state})'
