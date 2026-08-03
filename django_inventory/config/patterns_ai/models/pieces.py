"""PatternPiece + PatternPieceVersion — product-scoped pattern identity
(V3 §4 / V2 C2-context / ADR-D). Geometry rows (PieceSizeGeometry) arrive in
the capture block; versions exist now so manual-marker lineage and the
knowledge chain are anchored from day one.
"""
from django.conf import settings
from django.db import models

from core.models import TimeStampedModel


class PatternPiece(TimeStampedModel):
    """Product-SCOPED piece identity. The blocker-fix grain: geometry never
    hangs on the cross-product ProductPattern name-library."""

    class FabricGroup(models.TextChoices):
        BODY = 'body', 'Body'
        RIB = 'rib', 'Rib'
        COLLAR = 'collar', 'Collar'
        TRIM = 'trim', 'Trim'
        OTHER = 'other', 'Other'

    class GrainRule(models.TextChoices):
        STRICT = 'strict', 'On grain (0° only)'
        TWO_WAY = 'two_way', 'Two-way (180° allowed)'
        FREE = 'free', 'Free (any rotation)'

    product = models.ForeignKey(
        'production.Product', on_delete=models.PROTECT,
        related_name='pattern_pieces',
        help_text='Owning product — the permanent home (owner vision).')
    pattern = models.ForeignKey(
        'production.ProductPattern', on_delete=models.PROTECT,
        related_name='+',
        help_text='Name/identity link ONLY into the shared pattern library; '
                  'pieces_count stays on ProductPatternAssignment (never duplicated).')
    assignment = models.OneToOneField(
        'production.ProductPatternAssignment', on_delete=models.PROTECT,
        null=True, blank=True, related_name='patterns_ai_piece',
        help_text='Optional link to the product↔pattern assignment row.')
    fabric_group = models.CharField(
        max_length=16, choices=FabricGroup.choices, default=FabricGroup.BODY,
        help_text='Markers never mix fabric groups (V3 concept model).')
    is_pair = models.BooleanField(
        default=False, help_text='Cut as mirrored pair (e.g. sleeves).')
    # Phase-2 Blueprint rule: placement constraint the future DCT consumes.
    # TWO_WAY default = today's actual behavior (workspace rotates 180° only).
    grain_rule = models.CharField(
        max_length=16, choices=GrainRule.choices, default=GrainRule.TWO_WAY,
        help_text='Blueprint rule: how this piece may rotate vs fabric grain.')
    # Phase-6 M2 additive: pattern-set semantics + documentation
    is_optional = models.BooleanField(
        default=False,
        help_text='Optional pieces (e.g. Pocket) join a layout only when '
                  'their designs exist for the requested sizes; missing '
                  'optional designs never block generation. Default False '
                  '= required (validation cannot silently weaken).')
    reference_image = models.ForeignKey(
        'patterns_ai.CaptureAsset', on_delete=models.PROTECT,
        null=True, blank=True, related_name='reference_for_pieces',
        help_text='Display-only illustration (kind=reference_image) — '
                  'NEVER a geometry source; extraction refuses non-'
                  'pattern-capture kinds structurally.')
    on_fold = models.BooleanField(
        default=False, help_text='Cut on fold — fold-edge semantics land with geometry.')
    # M2 adr-c.2 Blueprint metadata slots (UI freeze §3): pattern-owned,
    # never layout-owned. Expectation/declaration only — geometry carries
    # the actual notch points in features.notches; mismatch = display-only.
    expected_notches = models.PositiveSmallIntegerField(
        null=True, blank=True,
        help_text='Expected notch count per size (advisory — a mismatch '
                  'shows honestly, never blocks).')
    seam_allowance_mm = models.DecimalField(
        max_digits=5, decimal_places=1, null=True, blank=True,
        help_text='Declared seam allowance (mm). Geometry stays the CUT '
                  'line (ADR-C); this is declared metadata, not an offset.')
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        null=True, related_name='+')

    class Meta:
        verbose_name = 'pattern piece'
        # one piece row per (product, pattern) — the product-scoped grain
        constraints = [
            models.UniqueConstraint(fields=['product', 'pattern'],
                                    name='pai_piece_unique_per_product'),
        ]
        indexes = [models.Index(fields=['product', 'fabric_group'])]

    def __str__(self):
        return f'{self.product_id}:{self.pattern_id} [{self.fabric_group}]'


class PatternPieceVersion(TimeStampedModel):
    """Append-only version chain (ADR-D): draft → confirmed | rejected(reason);
    confirmed rows are immutable and superseded, never edited (service-enforced
    from Block 2B; states + constraints live in the schema now)."""

    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        CONFIRMED = 'confirmed', 'Confirmed'
        REJECTED = 'rejected', 'Rejected'
        SUPERSEDED = 'superseded', 'Superseded'

    piece = models.ForeignKey(
        PatternPiece, on_delete=models.PROTECT, related_name='versions')
    version_no = models.PositiveIntegerField(
        help_text='1,2,3… per piece; assigned by the single-writer service.')
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.DRAFT)
    status_reason = models.CharField(
        max_length=200, blank=True,
        help_text='Mandatory on rejection (F2).')
    superseded_by = models.ForeignKey(
        'self', on_delete=models.PROTECT, null=True, blank=True,
        related_name='supersedes_versions',
        help_text='Forward lineage; set when a newer version confirms.')
    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        null=True, blank=True, related_name='+',
        help_text='Human confirmation = the source of truth (owner lock).')
    confirmed_at = models.DateTimeField(null=True, blank=True)
    # P2 additive (ADR-D2 §5): optional graded-set grouping, identity only
    set_label = models.ForeignKey(
        'patterns_ai.PatternSetLabel', on_delete=models.PROTECT,
        null=True, blank=True, related_name='versions')
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        null=True, related_name='+')

    class Meta:
        verbose_name = 'pattern piece version'
        ordering = ['piece_id', 'version_no']
        constraints = [
            models.UniqueConstraint(fields=['piece', 'version_no'],
                                    name='pai_version_unique_per_piece'),
            models.CheckConstraint(
                name='pai_version_rejected_requires_reason',
                check=~models.Q(status='rejected') | ~models.Q(status_reason=''),
            ),
            # confirmed ⇒ confirmer + timestamp recorded (audit spine)
            models.CheckConstraint(
                name='pai_version_confirmed_requires_audit',
                check=~models.Q(status='confirmed')
                      | (models.Q(confirmed_by__isnull=False)
                         & models.Q(confirmed_at__isnull=False)),
            ),
        ]

    def __str__(self):
        return f'piece {self.piece_id} v{self.version_no} ({self.status})'
