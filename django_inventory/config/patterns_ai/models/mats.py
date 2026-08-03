"""CalibrationMat — physical metrology asset registry (ADR-E / V2 C13).

The custody chain starts here: every future CaptureAsset FKs the mat it was
shot on. Commissioning (tape-measured control distances) happens BEFORE first
use; recheck history becomes an append-only child table in the capture block.
"""
from django.conf import settings
from django.db import models

from core.models import TimeStampedModel


class CalibrationMat(TimeStampedModel):
    class Status(models.TextChoices):
        # retired ≠ deleted: mats never leave the registry (F5)
        UNCOMMISSIONED = 'uncommissioned', 'Uncommissioned'
        ACTIVE = 'active', 'Active'
        RETIRED = 'retired', 'Retired'

    mat_code = models.SlugField(
        max_length=32, unique=True,
        help_text="Physical label on the mat, e.g. 'MAT-01'.")
    name = models.CharField(max_length=100, blank=True,
                            help_text='Optional display name.')
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.UNCOMMISSIONED,
        help_text='Uncommissioned mats cannot back a capture (gate at ADR-E).')
    status_reason = models.CharField(
        max_length=200, blank=True,
        help_text='Mandatory when retired (F2: negative transitions carry reasons).')
    commissioned_at = models.DateTimeField(
        null=True, blank=True,
        help_text='Set when tape-measured control distances were recorded.')
    # JSON payload convention (F3): {"schema_version": 1, "distances": [...]}
    control_distances = models.JSONField(
        default=dict, blank=True,
        help_text='Commissioning tape measurements; payload carries schema_version.')
    # P2 additive (ADR-E): the printed ChArUco spec the compute runtime needs
    board_spec = models.JSONField(
        default=dict, blank=True,
        help_text='ChArUco spec: {"schema_version":1,"squares_x":14,'
                  '"squares_y":10,"square_mm":100,"marker_mm":75,'
                  '"aruco_dict":"DICT_5X5_1000"}.')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        null=True, related_name='+')

    class Meta:
        verbose_name = 'calibration mat'
        constraints = [
            # retired ⇒ reason present (F2). CheckConstraint = DB-level wall.
            models.CheckConstraint(
                name='pai_mat_retired_requires_reason',
                check=~models.Q(status='retired') | ~models.Q(status_reason=''),
            ),
        ]

    def __str__(self):
        return f'{self.mat_code} ({self.get_status_display()})'


class CalibrationMatCheck(TimeStampedModel):
    """Append-only commissioning/recheck evidence (ADR-E §2, ADR-D3 §3) —
    the child table this module reserved since Block 2A."""

    class Kind(models.TextChoices):
        COMMISSIONING = 'commissioning', 'Commissioning'
        RECHECK = 'recheck', 'Recheck'

    mat = models.ForeignKey(
        CalibrationMat, on_delete=models.PROTECT, related_name='checks')
    kind = models.CharField(max_length=16, choices=Kind.choices)
    capture = models.ForeignKey(
        'patterns_ai.CaptureAsset', on_delete=models.PROTECT,
        null=True, blank=True, related_name='+',
        help_text='The photo this check ran on (optional for tape-only rows).')
    evidence = models.JSONField(
        default=dict,
        help_text='calibrate.py output: metrics + self-check + gate; '
                  'payload carries pipeline_version.')
    passed = models.BooleanField()
    notes = models.CharField(max_length=200, blank=True)
    checked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        null=True, related_name='+')

    class Meta:
        verbose_name = 'calibration mat check'
        ordering = ['mat_id', 'id']

    def save(self, *args, **kwargs):
        # append-only decision events (F2/F5): inserts only, ever.
        if self.pk is not None:
            raise ValueError('CalibrationMatCheck is append-only.')
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError('CalibrationMatCheck rows are never deleted (F5).')

    def __str__(self):
        return f'{self.mat_id} {self.kind} ({"PASS" if self.passed else "FAIL"})'
