"""Layering stage forms — Stage 1 of the production workflow.

YEH FILE KYU HAI?
─────────────────
Stage 1 ke saare forms yahan. Pattern: ek file per stage. Future stages
(cutting.py, packing.py, sewing.py, ...) same shape follow karenge:
  • shared widgets from _shared.py
  • <Action>Form classes (Start, AttachRoll, Edit, RemainingCloth, Complete)
  • Forms only — no service / view code.

Why per-stage? Production workflow scales to many stages. Mixing 5 stages'
forms in one file = unmaintainable. Each file ~100 lines tops.

Forms in this file (Layering):
  • StartLayeringForm        — manager assigns workers
  • AttachRollForm           — worker attaches a roll (width + weight)
  • RemainingClothForm       — records leftover cloth piece
  • CompleteLayeringForm     — overall layer length + duration + notes
"""
from __future__ import annotations

from django import forms

from raw_materials.models import WIDTH_CHOICES

from ._shared import (
    _BASE,
    _RollChoiceField,
    _WorkerCheckboxes,
    _WorkerMultipleChoiceField,
    _layering_worker_queryset,
)


class StartLayeringForm(forms.Form):
    """Manager refines workers on the auto-created Layering stage_record."""
    workers = _WorkerMultipleChoiceField(
        queryset=_layering_worker_queryset(),
        widget=_WorkerCheckboxes(),
        required=True,
        help_text="Only users with Cutting Master or Cutting Master Helper skill are shown. At least one Cutting Master must remain.",
    )


class AttachRollForm(forms.Form):
    """Roll picker + verified width/weight. Layer count + leftover collected at Section 04."""
    roll = _RollChoiceField(
        queryset=None,
        widget=forms.Select(attrs={**_BASE}),
        help_text="Pick an unused cloth roll from inventory.",
    )
    width_verified_inch = forms.TypedChoiceField(
        choices=[('', '— select —')] + [(str(v), label) for v, label in WIDTH_CHOICES],
        coerce=int,
        widget=forms.Select(attrs={**_BASE}),
        help_text="Measure with tape; correct if intake entry was wrong.",
    )
    weight_verified_kg = forms.DecimalField(
        min_value=0.01, max_digits=8, decimal_places=2,
        widget=forms.NumberInput(attrs={**_BASE, 'step': '0.01', 'placeholder': 'actual weight in KG'}),
        help_text="Weigh on the floor scale.",
    )
    notes = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={**_BASE, 'placeholder': 'Optional'}),
    )

    def __init__(self, *args, available_rolls_qs=None, **kwargs):
        super().__init__(*args, **kwargs)
        if available_rolls_qs is not None:
            self.fields['roll'].queryset = available_rolls_qs


class RemainingClothForm(forms.Form):
    """Records leftover cloth piece from a roll after layering."""
    remaining_weight_kg = forms.DecimalField(
        min_value=0, max_digits=8, decimal_places=2,
        widget=forms.NumberInput(attrs={**_BASE, 'step': '0.01', 'placeholder': 'leftover weight (KG)'}),
    )
    remaining_length_meters = forms.DecimalField(
        min_value=0, max_digits=8, decimal_places=2,
        widget=forms.NumberInput(attrs={**_BASE, 'step': '0.01', 'placeholder': 'leftover length (m)'}),
    )
    notes = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={**_BASE, 'placeholder': 'Optional'}),
    )


class CompleteLayeringForm(forms.Form):
    """Layering complete form — overall layer length + notes.

    Per-roll breakup (layers + leftover weight) lives on per-row inputs in the
    template, parsed manually in the view. lay_count = sum, computed by service.

    Duration is NOT entered here — it is auto-computed at completion from
    timestamps (now − adda.started_at); see stage-duration-rule. Field-level
    required=False so DRAFT submits can omit values; the view differentiates
    draft vs complete and applies validation accordingly.
    """
    layer_length_meters = forms.DecimalField(
        required=False,
        min_value=0.01, max_digits=8, decimal_places=2,
        widget=forms.NumberInput(attrs={**_BASE, 'step': '0.01', 'placeholder': 'one layer length (m) — same for all rolls'}),
        help_text="Length of a single layer in meters. Same value applies to every roll.",
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={**_BASE, 'rows': 3, 'placeholder': 'Optional'}),
    )
