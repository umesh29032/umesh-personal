"""Phase-6 M2 — the two-model storage architecture (🔒 owner-locked,
INTEGRATION_DESIGN §3h). Different responsibilities, different
lifecycles, deliberately NOT merged:

- ProductFabricProfile: long-lived product DEFAULTS only. Never
  references a layout; nothing approval-specific; nothing derived.
- ProductionLayout: the CURRENT production designation only — a pointer
  to an existing immutable saved layout. Replacing it moves the pointer;
  no layout row is ever modified. History = the immutable saved layouts
  + these audit fields.
"""
from django.conf import settings
from django.db import models

from core.models import TimeStampedModel


class ProductFabricProfile(TimeStampedModel):
    """Optional per-product manufacturing defaults — prefill values only,
    always editable at use. Single-writer service (M3)."""

    product = models.OneToOneField(
        'production.Product', on_delete=models.PROTECT,
        related_name='fabric_profile')
    default_width_mm = models.PositiveIntegerField(
        null=True, blank=True,
        help_text='Prefills Generate + the editor; never authoritative.')
    default_length_mm = models.PositiveIntegerField(
        null=True, blank=True,
        help_text='Default layer length (fabric height) prefill.')
    default_spacing_mm = models.DecimalField(
        max_digits=4, decimal_places=1, null=True, blank=True,
        help_text='Default piece spacing prefill.')
    fabric_type = models.CharField(
        max_length=60, blank=True,
        help_text='Optional metadata (display + export summary only).')
    gsm = models.PositiveSmallIntegerField(
        null=True, blank=True,
        help_text='Optional fabric weight metadata.')
    lay_mode = models.CharField(
        max_length=40, blank=True,
        help_text='Optional lay metadata (e.g. face-up single-ply).')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        null=True, related_name='+')

    class Meta:
        verbose_name = 'product fabric profile'

    def __str__(self):
        return f'fabric profile for product {self.product_id}'


class ProductionLayout(TimeStampedModel):
    """THE production designation: which immutable saved layout production
    cuts from. OneToOne(product) = exactly one, structurally. The pointer
    moves via the explicit audited Approve act (single-writer, M3) —
    never bundled with Save, never mutating any layout."""

    product = models.OneToOneField(
        'production.Product', on_delete=models.PROTECT,
        related_name='production_layout')
    approved_layout = models.ForeignKey(
        'patterns_ai.GeneratedMarkerCandidate', on_delete=models.PROTECT,
        related_name='production_designations',
        help_text='Pointer to an existing immutable saved layout — '
                  'approval never duplicates layout data.')
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        null=True, related_name='+')
    approved_at = models.DateTimeField()

    class Meta:
        verbose_name = 'production layout designation'

    def __str__(self):
        return (f'production layout for product {self.product_id} '
                f'-> layout {self.approved_layout_id}')
