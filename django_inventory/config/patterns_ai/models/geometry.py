"""Geometry-era models (P2, ADR-C/D2/D3): extraction proposals, per-size
canonical geometry, graded-set labels.

Grain (ADR-D2): version chain stays PIECE-level; geometry = per-size child
rows; later sizes copy-forward into a new version, never mutate confirmed.
"""
from django.conf import settings
from django.db import models

from core.models import TimeStampedModel


def evidence_upload_to(instance, filename):
    # name by piece home; extension kept from the sanitized client name
    import posixpath
    ext = (filename.rsplit('.', 1)[-1] if '.' in filename else 'bin')[:8]
    return posixpath.join('patterns_ai', str(instance.piece.product_id),
                          'evidence', f'ev{instance.piece_id}'
                                      f'-{instance.size_id}.{ext.lower()}')


class EvidenceItem(TimeStampedModel):
    """M2 Acquisition Layer (UI freeze §2.4/§4): ONE row per piece-of-
    evidence in a piece×size Evidence Stack. Evidence is a FACT — the
    original file is kept; rows are never deleted; status moves only via
    acquisition_service (single writer). The proposal it yields lives in
    GeometryExtraction (the ONE proposal store for every adapter)."""

    class Kind(models.TextChoices):
        PHOTO = 'photo', 'Photo (calibration mat)'
        # M8: the REAL factory photo — plain table, no mat; scale comes
        # from human-stated tape measurements (Evidence-Set adapter)
        PHOTO_PLAIN = 'photo_plain', 'Photo (plain background)'
        DXF = 'dxf', 'DXF file'
        SVG = 'svg', 'SVG file'
        PDF = 'pdf', 'PDF file'
        PNG = 'png', 'PNG image'
        MANUAL_DIMS = 'manual_dims', 'Manual dimensions'
        AI_API = 'ai_api', 'External AI service'

    class Status(models.TextChoices):
        RECEIVED = 'received', 'Received'
        PROPOSED = 'proposed', 'Proposal created'
        REFUSED = 'refused', 'Adapter refused'

    piece = models.ForeignKey(
        'patterns_ai.PatternPiece', on_delete=models.PROTECT,
        related_name='evidence_items')
    size = models.ForeignKey(
        'production.ProductSize', on_delete=models.PROTECT, related_name='+')
    kind = models.CharField(max_length=16, choices=Kind.choices)
    capture = models.ForeignKey(
        'patterns_ai.CaptureAsset', on_delete=models.PROTECT,
        null=True, blank=True, related_name='evidence_items',
        help_text='Photo evidence wraps the immutable CaptureAsset.')
    file = models.FileField(
        upload_to=evidence_upload_to, max_length=255, null=True, blank=True,
        help_text='Original DXF/SVG bytes — evidence is a kept fact.')
    params = models.JSONField(
        default=dict, blank=True,
        help_text='Adapter input (e.g. manual dims {width_mm, height_mm}).')
    status = models.CharField(max_length=10, choices=Status.choices,
                              default=Status.RECEIVED)
    refusal_reason = models.CharField(
        max_length=300, blank=True,
        help_text='Honest recorded refusal (ladder rule) — mandatory when refused.')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='+')

    class Meta:
        verbose_name = 'evidence item'
        indexes = [models.Index(fields=['piece', 'size', 'status'])]
        constraints = [
            models.CheckConstraint(
                name='pai_evidence_refused_requires_reason',
                check=~models.Q(status='refused') | ~models.Q(refusal_reason=''),
            ),
        ]

    _service_transition = False   # set ONLY by acquisition_service

    def save(self, *args, **kwargs):
        # evidence rows insert freely; updates only via the single writer
        if self.pk is not None and not self._service_transition:
            raise ValueError('EvidenceItem updates go through '
                             'acquisition_service only.')
        self._service_transition = False
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError('evidence is never deleted (F5) — it is a fact.')

    def __str__(self):
        return f'evidence {self.pk} {self.kind} ({self.status})'


class GeometryExtraction(TimeStampedModel):
    """Append-only compute+review record (ADR-E §6 provenance). One row per
    ADAPTER run on a piece of evidence (M2: photo/DXF/SVG/manual-dims all
    propose HERE — the one proposal store); the human review decision is a
    ONE-SHOT transition recorded on the same row (proposed ->
    accepted|rejected)."""

    class Status(models.TextChoices):
        PROPOSED = 'proposed', 'Proposed'
        ACCEPTED = 'accepted', 'Accepted'
        REJECTED = 'rejected', 'Rejected'

    capture = models.ForeignKey(
        'patterns_ai.CaptureAsset', on_delete=models.PROTECT,
        null=True, blank=True, related_name='extractions',
        help_text='Photo custody chain; NULL for non-photo adapters (M2).')
    evidence = models.ForeignKey(
        'patterns_ai.EvidenceItem', on_delete=models.PROTECT,
        null=True, blank=True, related_name='proposals',
        help_text='M2 Evidence Stack link; NULL on pre-M2 photo rows.')
    piece = models.ForeignKey(
        'patterns_ai.PatternPiece', on_delete=models.PROTECT,
        related_name='extractions')
    size = models.ForeignKey(
        'production.ProductSize', on_delete=models.PROTECT, related_name='+',
        help_text='ADR-D2: geometry is per-size; the size this photo captures.')
    backend = models.CharField(max_length=16, default='classical')
    pipeline_version = models.CharField(max_length=16)
    params = models.JSONField(default=dict, blank=True)
    # full reprocessing provenance (ADR-D3): metrics/checks/segmentation
    result = models.JSONField(default=dict, blank=True)
    gate = models.JSONField(
        default=dict, blank=True,
        help_text='ADR-E §3 hard-gate verdict incl. recorded refusal reasons.')
    geometry = models.JSONField(
        null=True, blank=True,
        help_text='Canonical ADR-C proposal payload; NULL when the gate refused.')
    confidence = models.JSONField(
        default=dict, blank=True,
        help_text='Component-visible score; display only, never auto-accept.')
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.PROPOSED)
    status_reason = models.CharField(
        max_length=200, blank=True,
        help_text='Mandatory on rejection (F2).')
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        null=True, blank=True, related_name='+')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        null=True, related_name='+')

    class Meta:
        verbose_name = 'geometry extraction'
        indexes = [models.Index(fields=['piece', 'size', 'status'])]
        constraints = [
            models.CheckConstraint(
                name='pai_extraction_rejected_requires_reason',
                check=~models.Q(status='rejected') | ~models.Q(status_reason=''),
            ),
            models.CheckConstraint(
                name='pai_extraction_review_requires_audit',
                check=models.Q(status='proposed')
                      | (models.Q(reviewed_by__isnull=False)
                         & models.Q(reviewed_at__isnull=False)),
            ),
        ]

    _review_transition = False   # set ONLY by pattern_geometry_service

    def save(self, *args, **kwargs):
        # append-only + one-shot review: inserts free; the sole legal UPDATE
        # is the service-flagged proposed->accepted/rejected transition.
        if self.pk is not None and not self._review_transition:
            raise ValueError(
                'GeometryExtraction is append-only; the only update is the '
                'one-shot review transition via pattern_geometry_service.')
        self._review_transition = False
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError('GeometryExtraction rows are never deleted (F5).')

    def __str__(self):
        return f'extraction {self.pk} piece {self.piece_id} ({self.status})'


class PieceSizeGeometry(TimeStampedModel):
    """One canonical ADR-C payload per (version, size) — ADR-D2 grain.
    Mutable ONLY while its version is a draft; confirm freezes it forever."""

    class TrustGrade(models.TextChoices):
        MEASURED = 'measured', 'Measured (tape-accepted)'
        PHOTO_CALIBRATED = 'photo_calibrated', 'Photo-calibrated'
        UNCALIBRATED = 'uncalibrated', 'Uncalibrated'

    version = models.ForeignKey(
        'patterns_ai.PatternPieceVersion', on_delete=models.PROTECT,
        related_name='size_geometries')
    size = models.ForeignKey(
        'production.ProductSize', on_delete=models.PROTECT, related_name='+')
    geometry = models.JSONField(
        help_text='Canonical payload (integer um, y-up, CCW outer; ADR-C).')
    chord_tolerance_um = models.PositiveIntegerField(default=500)
    trust_grade = models.CharField(
        max_length=20, choices=TrustGrade.choices,
        default=TrustGrade.UNCALIBRATED,
        help_text='ADR-E §7; stamped at confirm (tape acceptance => measured).')
    source_extraction = models.ForeignKey(
        GeometryExtraction, on_delete=models.PROTECT, null=True, blank=True,
        related_name='geometry_rows',
        help_text='NULL for DXF imports and manual entry; custody chain otherwise.')
    copied_from = models.ForeignKey(
        'self', on_delete=models.PROTECT, null=True, blank=True,
        related_name='copies',
        help_text='ADR-D2 copy-forward provenance (new version carries rows).')
    tape_acceptance = models.JSONField(
        default=dict, blank=True,
        help_text='Numeric tape acceptance recorded at confirm (ADR-E §5).')
    # Phase-1 frozen-platform law: every geometry row DECLARES which semantic
    # contract its payload satisfies (cut-line/units/orientation = ADR-C).
    # DXF/manual rows bypass extraction.pipeline_version, so it lives here.
    # M4.5 conscious bump: adr-c.3 = c.2 + optional typed
    # features.fold_edge (the half-pattern's fold line); every prior
    # payload remains valid — the stamp exists for exactly these bumps.
    geometry_contract_version = models.CharField(
        max_length=16, default='adr-c.3',
        help_text='Semantic contract of the payload (ADR-C rev); stamped by '
                  'the single-writer service, never edited.')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        null=True, related_name='+')

    class Meta:
        verbose_name = 'piece size geometry'
        constraints = [
            models.UniqueConstraint(fields=['version', 'size'],
                                    name='pai_geometry_unique_version_size'),
        ]

    def _version_is_draft(self):
        from .pieces import PatternPieceVersion
        return (PatternPieceVersion.objects
                .filter(pk=self.version_id,
                        status=PatternPieceVersion.Status.DRAFT).exists())

    def save(self, *args, **kwargs):
        # frozen-with-version: geometry rows are workable while the version
        # is a draft; after confirm/reject the row is immutable knowledge.
        if self.pk is not None and not self._version_is_draft():
            raise ValueError('geometry of a non-draft version is immutable '
                             '(ADR-D); create a new version (copy-forward).')
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if not self._version_is_draft():
            raise ValueError('geometry of a non-draft version is never deleted.')
        return super().delete(*args, **kwargs)

    def __str__(self):
        return f'geometry v{self.version_id} size {self.size_id} ({self.trust_grade})'


class PatternSetLabel(TimeStampedModel):
    """Product-homed label naming a graded cardboard set (master plan P2).
    Identity only — versions reference it; no logic hangs on it in P2."""

    product = models.ForeignKey(
        'production.Product', on_delete=models.PROTECT,
        related_name='pattern_set_labels')
    code = models.SlugField(max_length=32)
    label = models.CharField(max_length=100)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        null=True, related_name='+')

    class Meta:
        verbose_name = 'pattern set label'
        constraints = [
            models.UniqueConstraint(fields=['product', 'code'],
                                    name='pai_setlabel_unique_per_product'),
        ]

    def __str__(self):
        return f'{self.code} ({self.product_id})'
