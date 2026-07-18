"""CaptureAsset — immutable knowledge-class originals (Block 3A; ADR-G/E).

Immutable-storage philosophy: an original photo is a FACT. After creation its
file, checksum, size and type NEVER change (model save() guard + single-writer
service). Corrections happen by uploading a NEW asset and retiring this one
with a reason — knowledge is never deleted (F5): retired/corrupt rows and
their files remain forever (cold-tier is an ops concern, ADR-G).

Storage layout (ADR-G): media/patterns_ai/<product_id>/originals/<sha16>.<ext>
— name derived from content hash: path traversal is structurally impossible
and duplicate content is visible by name.
"""
import posixpath

from django.conf import settings
from django.db import models

from core.models import TimeStampedModel


def capture_upload_to(instance, filename):
    # filename argument deliberately IGNORED — we name by content hash.
    ext = instance.safe_extension()
    return posixpath.join('patterns_ai', str(instance.product_id),
                          'originals', f'{instance.sha256[:16]}.{ext}')


class CaptureAsset(TimeStampedModel):
    class Source(models.TextChoices):
        CAMERA = 'camera', 'Camera'
        GALLERY = 'gallery', 'Gallery upload'

    class Kind(models.TextChoices):
        MARKER_PHOTO = 'marker_photo', 'Manual marker photo'
        PATTERN_CAPTURE = 'pattern_capture', 'Pattern capture (geometry era)'
        # Phase-6 M2: display-only documentation image — extraction
        # refuses any kind != pattern_capture, so this can never enter
        # geometry or verification (structural, rule 6).
        REFERENCE_IMAGE = 'reference_image', 'Reference image (display only)'

    class Status(models.TextChoices):
        STORED = 'stored', 'Stored'
        CORRUPT = 'corrupt', 'Integrity check failed'
        RETIRED = 'retired', 'Retired'

    _EXT_BY_TYPE = {'image/jpeg': 'jpg', 'image/png': 'png', 'image/webp': 'webp'}

    product = models.ForeignKey(
        'production.Product', on_delete=models.PROTECT,
        related_name='capture_assets',
        help_text='Product-homed (owner vision: capture assets live with the product).')
    kind = models.CharField(max_length=20, choices=Kind.choices,
                            default=Kind.MARKER_PHOTO)
    source = models.CharField(max_length=10, choices=Source.choices)
    file = models.FileField(
        upload_to=capture_upload_to, max_length=255,
        help_text='The immutable original. Never replaced; never served raw at scale (ADR-G).')
    original_filename = models.CharField(
        max_length=200, blank=True,
        help_text='Sanitized client filename, display only (never used for storage).')
    content_type = models.CharField(max_length=40)
    size_bytes = models.PositiveBigIntegerField()
    sha256 = models.CharField(
        max_length=64,
        help_text='Streaming SHA-256 of the stored bytes — the integrity anchor.')
    status = models.CharField(max_length=10, choices=Status.choices,
                              default=Status.STORED)
    status_reason = models.CharField(
        max_length=200, blank=True,
        help_text='Mandatory when retired/corrupt (F2).')
    mat = models.ForeignKey(
        'patterns_ai.CalibrationMat', on_delete=models.PROTECT,
        null=True, blank=True, related_name='captures',
        help_text='Custody chain for pattern captures (geometry era); NULL for marker photos.')
    # JSON payload convention (F3): {"schema_version": 1, ...}
    metadata = models.JSONField(
        default=dict, blank=True,
        help_text='Client-declared context only in Block 3A (no EXIF processing yet).')
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='+')

    class Meta:
        verbose_name = 'capture asset'
        constraints = [
            # duplicate CONTENT per product is refused (friendly, in the service;
            # this is the DB backstop). Same bytes for another product = fine.
            models.UniqueConstraint(fields=['product', 'sha256'],
                                    name='pai_capture_unique_content_per_product'),
            models.CheckConstraint(
                name='pai_capture_negative_status_requires_reason',
                check=~models.Q(status__in=('retired', 'corrupt'))
                      | ~models.Q(status_reason=''),
            ),
            models.CheckConstraint(name='pai_capture_size_positive',
                                   check=models.Q(size_bytes__gt=0)),
        ]
        indexes = [models.Index(fields=['product', 'kind', 'status'])]

    _IMMUTABLE_FIELDS = ('file', 'sha256', 'size_bytes', 'content_type',
                         'product', 'kind', 'source')

    def safe_extension(self):
        return self._EXT_BY_TYPE.get(self.content_type, 'bin')

    def save(self, *args, **kwargs):
        if self.pk is not None:
            # belt: the original is a fact — its identity fields never change.
            old = type(self).objects.get(pk=self.pk)
            for f in self._IMMUTABLE_FIELDS:
                if getattr(old, f) != getattr(self, f):
                    raise RuntimeError(
                        f'CaptureAsset.{f} is immutable — upload a new asset '
                        'and retire this one instead.')
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise RuntimeError('CaptureAsset rows are never deleted — retire with a reason (F5).')

    def __str__(self):
        return f'{self.kind}:{self.sha256[:12]} ({self.status})'
