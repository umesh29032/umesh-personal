"""Marker generation models (P3, ADR-A/D): immutable engine runs and
candidates. Candidates hold FACTS of the run (placements, engine length);
utilization/waste are DERIVED AT READ (F6). Promotion to a real Marker is
the human truth boundary — a candidate itself is never used on fabric.
"""
from django.conf import settings
from django.db import models

from core.models import TimeStampedModel


class MarkerGenerationRun(TimeStampedModel):
    """Append-only record of one generation request (params + geometry
    snapshot references). One run -> N candidates (one per engine)."""

    product = models.ForeignKey(
        'production.Product', on_delete=models.PROTECT,
        related_name='marker_generation_runs')
    usable_width_mm = models.PositiveIntegerField()
    # {"schema_version":1, "ratio":{"<size_id>":count}, "spacing_mm":…,
    #  "allow_180":…, "timebox_s":…, "seed":…, "engine":"auto",
    #  "pieces":[{"piece_id","size_id","version_id","geometry_row_id",
    #             "qty","allow_mirror"}]}
    params = models.JSONField(
        help_text='Full request + the exact geometry rows consumed '
                  '(reproducibility spine; payload carries schema_version).')
    pipeline_version = models.CharField(max_length=16)
    errors = models.JSONField(
        default=dict, blank=True,
        help_text='Per-engine refusals, recorded honestly.')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        null=True, related_name='+')

    class Meta:
        verbose_name = 'marker generation run'
        indexes = [models.Index(fields=['product', '-id'])]

    def save(self, *args, **kwargs):
        # append-only (F5): a run happened; it never changes.
        if self.pk is not None:
            raise ValueError('MarkerGenerationRun is append-only.')
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError('MarkerGenerationRun rows are never deleted (F5).')

    def __str__(self):
        return f'run {self.pk} product {self.product_id} ({self.usable_width_mm} mm)'


class GeneratedMarkerCandidate(TimeStampedModel):
    """One engine's complete, INDEPENDENTLY VERIFIED layout. Immutable.
    placements = absolute piece outlines in the lay frame (x = length,
    y = width, mm floats from the engine) — the drawable/cuttable artifact.
    """

    run = models.ForeignKey(
        MarkerGenerationRun, on_delete=models.PROTECT,
        related_name='candidates')
    engine = models.CharField(max_length=16)          # svgnest | blf
    # {"schema_version":1, "placements":[{key,instance,mirrored,
    #   rotation_deg, polygon_mm:[[x,y],…]}]}
    placements = models.JSONField()
    marker_length_mm = models.DecimalField(
        max_digits=9, decimal_places=2,
        help_text='Engine-run FACT, re-measured by the independent verifier.')
    verification = models.JSONField(
        help_text='shapely verdict: overlap / width containment / count — '
                  'computed in the runtime, never trusted from the engine.')
    seed = models.PositiveIntegerField(default=42)
    trials = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        verbose_name = 'generated marker candidate'
        constraints = [
            models.CheckConstraint(name='pai_candidate_length_positive',
                                   check=models.Q(marker_length_mm__gt=0)),
        ]

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise ValueError('GeneratedMarkerCandidate is immutable — '
                             'generate a new run instead.')
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError('candidates are never deleted (F5); they are the '
                         'evidence trail behind promoted markers.')

    def __str__(self):
        return f'candidate {self.pk} ({self.engine}, {self.marker_length_mm} mm)'
