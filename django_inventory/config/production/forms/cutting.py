"""Cutting stage forms — Stage 2 of the production workflow.

Pattern matches forms/layering.py.

LEGACY:
  • CuttingForm — single-shot complete (pieces_cut int). Used by old
    direct-form path for products without cutting_pattern stage.

WORKSPACE (PR3 2026-05-28):
  • CuttingStartForm — manager assigns workers.
  • CuttingBreakupRowForm — one (size, color, pattern, count) row.
    POST data parses multi-row arrays; views loop per row.
  • CuttingDraftForm — notes save.
"""
from __future__ import annotations

from django import forms

from production.models import ProductPattern, ProductSize

from ._shared import _BASE, _WorkerCheckboxes, _WorkerMultipleChoiceField, _worker_queryset


class CuttingForm(forms.Form):
    """Legacy single-shot complete form (back-compat for simple flows)."""

    pieces_cut = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={**_BASE, 'placeholder': 'how many pieces cut'}),
    )
    workers = _WorkerMultipleChoiceField(
        queryset=_worker_queryset(),
        widget=_WorkerCheckboxes(),
        required=False,
        help_text="Tick every worker who actually performed this cutting.",
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={**_BASE, 'rows': 3, 'placeholder': 'Optional'}),
    )


class CuttingStartForm(forms.Form):
    """Manager assigns workers to start cutting stage."""

    workers = _WorkerMultipleChoiceField(
        queryset=_worker_queryset(),
        widget=_WorkerCheckboxes(),
        required=True,
    )


class CuttingBreakupRowForm(forms.Form):
    """One row of the breakup table — size + color + pattern + count.

    View instantiates per-row from POST `size_id[]`, `color_id[]`,
    `pattern_id[]`, `count[]` parallel arrays. Service does the
    cross-product validation.
    """

    size_id = forms.IntegerField(min_value=1)
    color_id = forms.IntegerField(min_value=1)
    pattern_id = forms.IntegerField(min_value=1)
    count = forms.IntegerField(min_value=0)
    roll_id = forms.IntegerField(min_value=1, required=False)

    def __init__(self, *args, product=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._product = product

    def clean_size_id(self):
        pk = self.cleaned_data['size_id']
        if self._product is None:
            raise forms.ValidationError("Missing product context.")
        if not ProductSize.objects.filter(pk=pk, product=self._product).exists():
            raise forms.ValidationError(
                f"Size {pk} not configured on product {self._product.code}.",
            )
        return pk

    def clean_pattern_id(self):
        pk = self.cleaned_data['pattern_id']
        if not ProductPattern.objects.filter(pk=pk).exists():
            raise forms.ValidationError(f"Pattern {pk} not found.")
        return pk


class CuttingDraftForm(forms.Form):
    """Notes save + bulk draft action."""

    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={**_BASE, 'rows': 3, 'placeholder': 'Optional'}),
    )


class CuttingBundleForm(forms.Form):
    """Actual physical bundle entry — PR7 2026-05-28.

    Each row = one rope-tied bundle of cut pieces. Same (pattern, size, color)
    can repeat across rows (each row = separate physical bundle).
    """

    pattern_id = forms.IntegerField(min_value=1)
    size_id = forms.IntegerField(min_value=1)
    color_id = forms.IntegerField(min_value=1)
    count = forms.IntegerField(min_value=1)
    bundle_number = forms.CharField(required=False, max_length=40)

    def __init__(self, *args, product=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._product = product

    def clean_size_id(self):
        pk = self.cleaned_data['size_id']
        if self._product is None:
            raise forms.ValidationError("Missing product context.")
        if not ProductSize.objects.filter(pk=pk, product=self._product).exists():
            raise forms.ValidationError(
                f"Size {pk} not configured on product {self._product.code}.",
            )
        return pk

    def clean_pattern_id(self):
        pk = self.cleaned_data['pattern_id']
        if not ProductPattern.objects.filter(pk=pk).exists():
            raise forms.ValidationError(f"Pattern {pk} not found.")
        return pk
