"""SuggestionEvent — AI suggestions as stored, product-homed knowledge
(V2 C8 / owner vision: suggestions are permanent assets, auditable).
"""
from django.conf import settings
from django.db import models

from core.models import TimeStampedModel


class SuggestionEvent(TimeStampedModel):
    class Outcome(models.TextChoices):
        OFFERED = 'offered', 'Offered'
        ACCEPTED = 'accepted', 'Accepted'
        MODIFIED = 'modified', 'Accepted with modifications'
        REJECTED = 'rejected', 'Rejected'

    product = models.ForeignKey(
        'production.Product', on_delete=models.PROTECT,
        related_name='pattern_suggestions',
        help_text='Product-homed (owner vision: suggestions live with the product).')
    source = models.CharField(
        max_length=100,
        help_text="Deterministic mechanism id, e.g. 'garment_template:tshirt@r1' "
                  'or \'copy_from:PRODUCT-CODE\'. FK to GarmentTemplate revision '
                  'lands with that model (later block).')
    # JSON payload convention (F3): {"schema_version":1, "pieces":[...]}
    payload = models.JSONField(
        default=dict,
        help_text='What was suggested; payload carries schema_version.')
    outcome = models.CharField(
        max_length=16, choices=Outcome.choices, default=Outcome.OFFERED)
    outcome_reason = models.CharField(
        max_length=200, blank=True,
        help_text='Mandatory on rejection (F2).')
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        null=True, blank=True, related_name='+')
    decided_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        null=True, related_name='+')

    class Meta:
        verbose_name = 'suggestion event'
        indexes = [models.Index(fields=['product', 'outcome'])]
        constraints = [
            models.CheckConstraint(
                name='pai_suggestion_rejected_requires_reason',
                check=~models.Q(outcome='rejected') | ~models.Q(outcome_reason=''),
            ),
        ]

    _decision_transition = False   # set ONLY by suggestion_service

    def save(self, *args, **kwargs):
        # P4 hardening (append-only decision spine, F5): inserts free; the
        # sole legal UPDATE is the one-shot offered -> decided transition
        # applied by the single-writer service.
        if self.pk is not None and not self._decision_transition:
            raise ValueError(
                'SuggestionEvent is append-only; the only update is the '
                'one-shot human decision via suggestion_service.')
        self._decision_transition = False
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError('SuggestionEvent rows are never deleted (F5).')

    def __str__(self):
        return f'suggestion {self.pk} for product {self.product_id} ({self.outcome})'
