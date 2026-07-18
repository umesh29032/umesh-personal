"""Marker · MarkerUsage · MarkerOutcome — the Digital Memory core
(V3 §4 / ADR-D; C2 manual-first, C7 repeats, F6 facts-only outcomes).

Markers are immutable knowledge: change = new row + `supersedes` lineage.
Manual markers (origin=manual_photo) are permanent first-class citizens —
photo assets attach in the upload block; declared width/ratio live here now.
"""
from django.conf import settings
from django.db import models

from core.models import TimeStampedModel

from .pieces import PatternPiece


class Marker(TimeStampedModel):
    class Origin(models.TextChoices):
        MANUAL_PHOTO = 'manual_photo', 'Manual (photo of chalk layout)'
        GENERATED = 'generated', 'Generated'
        IMPORTED = 'imported', 'Imported'
        ADDA_TEMPORARY = 'adda_temporary', 'Adda temporary'

    class Status(models.TextChoices):
        CANDIDATE = 'candidate', 'Candidate'
        VALIDATED = 'validated', 'Validated'
        PROMOTED = 'promoted', 'Promoted'
        SUPERSEDED = 'superseded', 'Superseded'
        RETIRED = 'retired', 'Retired'
        REJECTED = 'rejected', 'Rejected'

    class Construction(models.TextChoices):
        OPEN = 'open', 'Open width'
        TUBULAR = 'tubular', 'Tubular (tube-flat)'
        UNKNOWN = 'unknown', 'Unknown'

    reference = models.CharField(
        max_length=16, unique=True, editable=False,
        help_text="Globally-unique 'MRK-000001' (C14); assigned by marker_service "
                  'via the shared next_reference discipline (Block 2B).')
    product = models.ForeignKey(
        'production.Product', on_delete=models.PROTECT, related_name='markers',
        help_text='Permanent home — the Adda only CONSUMES (owner vision).')
    fabric_group = models.CharField(
        max_length=16, choices=PatternPiece.FabricGroup.choices,
        default=PatternPiece.FabricGroup.BODY,
        help_text='A marker never mixes fabric groups.')
    origin = models.CharField(max_length=16, choices=Origin.choices)
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.CANDIDATE)
    status_reason = models.CharField(
        max_length=200, blank=True,
        help_text='Mandatory when retired/rejected (F2).')
    label = models.CharField(
        max_length=100, blank=True,
        help_text="Floor name, e.g. \"Master's 37in tube layout\".")
    adda = models.ForeignKey(
        'production.Adda', on_delete=models.PROTECT, null=True, blank=True,
        related_name='temporary_markers',
        help_text='ONLY for origin=adda_temporary (D11): the run this marker '
                  'was generated for; promotion clears nothing — history stays.')
    supersedes = models.ForeignKey(
        'self', on_delete=models.PROTECT, null=True, blank=True,
        related_name='superseded_by_markers',
        help_text='Lineage: the marker this one replaces (C20 biography).')
    benchmarked_against = models.ForeignKey(
        'self', on_delete=models.PROTECT, null=True, blank=True,
        related_name='benchmark_children',
        help_text='The baseline (usually manual) this marker competes with (C4).')
    # P3 additive: the immutable candidate a GENERATED marker was promoted from
    candidate = models.ForeignKey(
        'patterns_ai.GeneratedMarkerCandidate', on_delete=models.PROTECT,
        null=True, blank=True, related_name='promoted_markers',
        help_text='Evidence chain for generated markers (D11 promotion).')
    usable_width_mm = models.PositiveIntegerField(
        help_text='Human-confirmed usable lay width in mm — never trusted from '
                  'ClothRoll nominal inches.')
    usable_width_band = models.PositiveIntegerField(
        editable=False,
        help_text='floor(usable_width_mm/10), stamped at creation (C10) — the '
                  'hot resolution-query key.')
    construction = models.CharField(
        max_length=8, choices=Construction.choices, default=Construction.UNKNOWN,
        help_text='Tube-flat vs open width changes every utilization number.')
    # JSON payload convention (F3): {"schema_version":1, "counts":{"S":2,...}}
    ratio = models.JSONField(
        default=dict, blank=True,
        help_text='INTEGER garments per repeat by size code; payload carries '
                  'schema_version. CPSA percentages are prefill hints only.')
    strategy = models.CharField(
        max_length=24, blank=True,
        help_text='Generated markers only (mixed/sectioned/fold-aware); blank '
                  'for manual/imported.')
    photo = models.ForeignKey(
        'patterns_ai.CaptureAsset', on_delete=models.PROTECT,
        null=True, blank=True, related_name='as_marker_photo',
        help_text='The chalk-layout photo (REQUIRED for manual_photo origin — '
                  'service-enforced); one photo backs at most one marker.')
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        null=True, related_name='+')

    class Meta:
        verbose_name = 'marker'
        indexes = [
            # THE resolution query: candidates for this Adda's product/width
            models.Index(fields=['product', 'fabric_group', 'usable_width_band']),
            models.Index(fields=['status']),
            models.Index(fields=['origin']),
        ]
        constraints = [
            # D11: adda set ⇔ origin=adda_temporary
            models.CheckConstraint(
                name='pai_marker_adda_iff_temporary',
                check=(models.Q(origin='adda_temporary', adda__isnull=False)
                       | ~models.Q(origin='adda_temporary')
                       & models.Q(adda__isnull=True)),
            ),
            models.CheckConstraint(
                name='pai_marker_negative_status_requires_reason',
                check=~models.Q(status__in=('retired', 'rejected'))
                      | ~models.Q(status_reason=''),
            ),
            models.CheckConstraint(
                name='pai_marker_width_positive',
                check=models.Q(usable_width_mm__gt=0),
            ),
            # one photo → at most one marker (partial unique; NULLs free)
            models.UniqueConstraint(
                fields=['photo'], condition=models.Q(photo__isnull=False),
                name='pai_marker_photo_used_once'),
        ]

    def __str__(self):
        return f'{self.reference} [{self.origin}/{self.status}]'


class MarkerUsage(TimeStampedModel):
    """THE feedback join key: a human act — 'this Adda cuts with marker M'.
    Append-only; corrections via voided_at + a new row, never edit."""

    marker = models.ForeignKey(
        Marker, on_delete=models.PROTECT, related_name='usages')
    adda = models.ForeignKey(
        'production.Adda', on_delete=models.PROTECT,
        related_name='marker_usages',
        help_text='FK INTO production — the allowed direction.')
    stage_record = models.ForeignKey(
        'production.AddaStageRecord', on_delete=models.PROTECT,
        null=True, blank=True, related_name='+',
        help_text='Optional: the cutting/layering stage record once known.')
    plies = models.PositiveIntegerField(
        help_text='Lay plies this marker was cut over.')
    repeats = models.PositiveIntegerField(
        default=1,
        help_text='Marker repeats along the lay (C7 — outcome math is wrong '
                  'without it).')
    measured_usable_width_mm = models.PositiveIntegerField(
        null=True, blank=True,
        help_text='Taped at the table for THIS lay; honest-NULL when unmeasured.')
    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='+',
        help_text='The human act that writes this row.')
    voided_at = models.DateTimeField(null=True, blank=True)
    void_reason = models.CharField(max_length=200, blank=True)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = 'marker usage'
        indexes = [
            models.Index(fields=['marker', 'adda']),
            models.Index(fields=['adda']),
        ]
        constraints = [
            models.CheckConstraint(name='pai_usage_plies_positive',
                                   check=models.Q(plies__gte=1)),
            models.CheckConstraint(name='pai_usage_repeats_positive',
                                   check=models.Q(repeats__gte=1)),
            models.CheckConstraint(
                name='pai_usage_void_requires_reason',
                check=models.Q(voided_at__isnull=True) | ~models.Q(void_reason=''),
            ),
        ]

    def __str__(self):
        return f'{self.marker_id} @ {self.adda_id} ({self.plies}×{self.repeats})'


class MarkerOutcome(TimeStampedModel):
    """RAW FACTS ONLY per usage (V3 F6): meters/garments/leftover. Every ratio
    (utilization, m/garment, ₹) is DERIVED AT READ by versioned pure functions
    in marker_feedback_service — recompute migrations can never exist."""

    usage = models.OneToOneField(
        MarkerUsage, on_delete=models.PROTECT, related_name='outcome')
    fabric_in_mm = models.PositiveBigIntegerField(
        null=True, blank=True,
        help_text='Linear fabric laid, in mm (plies × lay length). Honest-NULL.')
    garments_cut = models.PositiveIntegerField(
        null=True, blank=True,
        help_text='From APSCPB at recording time. Honest-NULL.')
    garments_packed = models.PositiveIntegerField(null=True, blank=True)
    leftover_mm = models.PositiveBigIntegerField(
        null=True, blank=True,
        help_text='End-of-lay leftover length in mm, if measured.')
    # JSON payload convention (F3): {"schema_version":1, "flags":["dev_fixture",...]}
    quality_flags = models.JSONField(
        default=dict, blank=True,
        help_text='Data-quality flags (confounders, dev-fixture, unmeasured…).')
    facts_schema_version = models.PositiveSmallIntegerField(
        default=1, help_text='Version of THIS row shape (F3).')
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='+',
        help_text="Outcome facts are written by an explicit human 'record "
                  "outcome' action (readiness N-6).")

    class Meta:
        verbose_name = 'marker outcome'

    def __str__(self):
        return f'outcome for usage {self.usage_id}'
