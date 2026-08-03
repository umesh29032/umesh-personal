"""ManufacturingStrategy — M4 (owner-frozen concept, plan §4).

A NAMED, REUSABLE Marker Plan preset: manufacturing knowledge as DATA.
UI name: "Marker Recipe" (owner refinement R1) — factory people open
"Body Marker · 42″", not "Strategy 4". The ENGINE never sees the name;
a resolver turns a recipe into pieces/rules/width/layers/ratio and
nothing else (genericity gate).
"""
from django.conf import settings
from django.db import models

from core.models import TimeStampedModel


class ManufacturingStrategy(TimeStampedModel):
    class LayeringType(models.TextChoices):
        SINGLE = 'single', 'Single layer'
        DOUBLE = 'double', 'Double layer (legacy = open)'
        # M4.5 lay split: the factory distinguishes open vs folded
        DOUBLE_OPEN = 'double_open', 'Double — open (2 plies)'
        DOUBLE_FOLDED = 'double_folded', 'Double — folded (crease)'
        TUBULAR = 'tubular', 'Tubular'

    class OptimizeIntent(models.TextChoices):
        FAST = 'fast', 'Fast'
        BALANCED = 'balanced', 'Balanced'
        BEST = 'best', 'Best'

    product = models.ForeignKey(
        'production.Product', on_delete=models.PROTECT,
        related_name='marker_recipes')
    name = models.CharField(
        max_length=80,
        help_text='The factory name: "Body+Pocket · double · 42″". '
                  'A LABEL — the planner never branches on it.')
    fabric_group = models.CharField(max_length=16)
    layering_type = models.CharField(
        max_length=16, choices=LayeringType.choices,
        default=LayeringType.SINGLE)
    piece_ids = models.JSONField(
        default=list, blank=True,
        help_text='Pieces this marker covers (ids) — the SEPARATE_PANEL/'
                  'BODY_PLUS_POCKET decision as data.')
    size_ratio = models.JSONField(
        default=dict, blank=True,
        help_text='{size_id: garments-per-lay} — the size mix.')
    optimize_intent = models.CharField(
        max_length=10, choices=OptimizeIntent.choices,
        default=OptimizeIntent.BALANCED)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(
        default=True,
        help_text='Soft state — recipes are knowledge, never deleted.')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='+')

    class Meta:
        verbose_name = 'marker recipe'
        constraints = [
            models.UniqueConstraint(fields=['product', 'name'],
                                    name='pai_recipe_unique_per_product'),
        ]
        indexes = [models.Index(fields=['product', 'is_active'])]

    def delete(self, *args, **kwargs):
        raise ValueError('marker recipes are never deleted — '
                         'deactivate instead (knowledge law).')

    def __str__(self):
        return f'{self.name} ({self.product_id})'
