"""Cutting-pattern stage forms — verification + size allocation.

YEH FILE KYU HAI?
─────────────────
PR2 (Cutting Pattern validation upgrade) ke liye 2 forms chahiye:

  1. PatternVerifyForm     → ek pattern assignment verify karna
                             (optional photo + note)
  2. SizeAllocationForm    → ek size + proportion_pct row
                             (POST body multi-row aata hai;
                              view loop karke set_size_allocation
                              ko clean list pass karta hai)

Style: lightweight forms.Form (not ModelForm) — service layer apna
validation karta hai, form bas POST parsing ka kaam karta hai.
"""
from __future__ import annotations

from django import forms

from production.models import (
    CuttingPatternPhoto, ProductPatternAssignment, ProductSize,
)


class PatternVerifyForm(forms.Form):
    """Pattern assignment verify karna ka chhota form.

    assignment_id required. photo_id + note optional. View `record` aur
    `user` service mein pass karta hai.
    """

    assignment_id = forms.IntegerField(min_value=1)
    photo_id = forms.IntegerField(required=False, min_value=1)
    note = forms.CharField(required=False, max_length=200)

    def __init__(self, *args, record=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._record = record

    def clean_assignment_id(self):
        pk = self.cleaned_data['assignment_id']
        if self._record is None:
            raise forms.ValidationError("Missing record context.")
        try:
            obj = ProductPatternAssignment.objects.get(
                pk=pk, product=self._record.stage_record.adda.product,
            )
        except ProductPatternAssignment.DoesNotExist:
            raise forms.ValidationError("Pattern not configured on this product.")
        self.cleaned_data['assignment'] = obj
        return pk

    def clean_photo_id(self):
        pk = self.cleaned_data.get('photo_id')
        if not pk:
            self.cleaned_data['photo'] = None
            return pk
        if self._record is None:
            raise forms.ValidationError("Missing record context.")
        try:
            ph = CuttingPatternPhoto.objects.get(pk=pk, record=self._record)
        except CuttingPatternPhoto.DoesNotExist:
            raise forms.ValidationError("Photo does not belong to this record.")
        self.cleaned_data['photo'] = ph
        return pk


class SizeAllocationForm(forms.Form):
    """Pattern stage ka size + proportion entry form — bulk view-side use.

    View `set-sizes` POST se array of rows aata hai
    (size_id[] + proportion_pct[]). View loop karke each row ko ye form
    se validate karta hai, phir set_size_allocation service ko clean
    list pass karta hai.
    """

    size_id = forms.IntegerField(min_value=1)
    proportion_pct = forms.IntegerField(min_value=0, max_value=100)

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
