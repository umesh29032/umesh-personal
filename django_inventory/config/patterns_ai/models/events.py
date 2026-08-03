"""MarkerTransitionEvent — the permanent, append-only history of every
marker status change (Block 2C; closes the 2A/2B transition-audit finding).

Immutable-event philosophy: decisions are knowledge (V3 F2). A transition is
never a field edit you can lose — it is a row that exists forever. No updates,
no deletes; the model itself refuses both (belt) on top of the single-writer
rule (braces; I-1 guard covers creation sites).
"""
from django.conf import settings
from django.db import models

from core.models import TimeStampedModel


class MarkerTransitionEvent(TimeStampedModel):
    marker = models.ForeignKey(
        'patterns_ai.Marker', on_delete=models.PROTECT,
        related_name='transition_events',
        help_text='The marker this event belongs to (PROTECT: history outlives intent).')
    from_status = models.CharField(
        max_length=16, blank=True,
        help_text="Previous status; empty string for the CREATION event.")
    to_status = models.CharField(
        max_length=16,
        help_text='New status after the transition.')
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='+',
        help_text='Who performed the transition (F2: attributed decisions).')
    reason = models.CharField(
        max_length=200, blank=True,
        help_text='Mandatory upstream for negative transitions; recorded verbatim.')
    transition_version = models.PositiveSmallIntegerField(
        help_text='Version of the transition rule-set that produced this event '
                  '(marker_service.TRANSITIONS_VERSION at write time).')
    # JSON payload convention (F3): {"schema_version": 1, ...}
    metadata = models.JSONField(
        default=dict, blank=True,
        help_text='Event context (e.g. origin at creation, superseded_by ref).')

    class Meta:
        verbose_name = 'marker transition event'
        ordering = ['marker_id', 'id']            # id = write order within a marker
        indexes = [models.Index(fields=['marker', 'id'])]

    # ── append-only guards (belt; single-writer = braces) ───────────────────
    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise RuntimeError('MarkerTransitionEvent is append-only — events are never updated.')
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise RuntimeError('MarkerTransitionEvent is append-only — events are never deleted.')

    def __str__(self):
        src = self.from_status or '∅'
        return f'{self.marker_id}: {src} → {self.to_status} by {self.actor_id}'
