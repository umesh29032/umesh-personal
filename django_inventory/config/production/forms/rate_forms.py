"""Stage role-rate correction form (S1.1).

YEH FILE KYU HAI?
─────────────────
Super-admin "Correct Rate" action ka thin form — service (stage_rate_service.
rerate_stage_role) hi truth hai; yeh sirf input + mandatory reason + confirm
collect karta hai. NOT a ModelForm (re-rate ek service action hai, na ki direct
model write).
"""
from decimal import Decimal

from django import forms

_BASE = {'class': 'sf-input', 'autocomplete': 'off'}


class StageRateCorrectionForm(forms.Form):
    """new rate + mandatory reason + explicit confirm. Owner requirement 2026-06-14."""

    new_rate = forms.DecimalField(
        max_digits=10, decimal_places=4, min_value=Decimal('0'),
        widget=forms.NumberInput(attrs={**_BASE, 'step': '0.0001', 'inputmode': 'decimal'}),
        label='New rate (₹)',
    )
    reason = forms.CharField(
        # Mandatory — a rate correction is a financial event; reason is audited.
        widget=forms.Textarea(attrs={**_BASE, 'rows': 3,
                                     'placeholder': 'Why is this rate being corrected?'}),
        label='Reason (required)',
    )
    confirm = forms.BooleanField(
        required=True,
        label='I confirm this rate correction and understand all completed-but-unsettled '
              'earnings on this stage/role will be recalculated.',
    )

    def clean_reason(self):
        reason = (self.cleaned_data.get('reason') or '').strip()
        if not reason:
            raise forms.ValidationError('A reason is required.')
        return reason
