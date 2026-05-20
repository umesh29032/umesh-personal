"""Cutting stage forms — Stage 2 of the production workflow.

Pattern matches forms/layering.py. Future stages drop in similarly.
"""
from __future__ import annotations

from django import forms

from ._shared import _BASE, _WorkerCheckboxes, _WorkerMultipleChoiceField, _worker_queryset


class CuttingForm(forms.Form):
    """Cutting stage complete form. pieces_cut triggers BatchBarcode generation."""

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
