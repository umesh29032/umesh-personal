"""Expense forms — advance entry, settlement header, worker profile.

Thin: views call services. The settlement's per-advance recovery rows are
dynamic (one input per outstanding advance) so they're parsed in the view, not
here — this form only carries the header fields (cash paid / date / method).
"""
from decimal import Decimal

from django import forms
from django.contrib.auth import get_user_model

from expense.models import PayrollSettlement, WorkerProfile

User = get_user_model()


def _worker_qs():
    return User.objects.filter(is_active=True).order_by('first_name', 'email')


class AdvanceForm(forms.Form):
    worker = forms.ModelChoiceField(queryset=_worker_qs())
    amount = forms.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal('0.01'))
    advance_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2}))
    attachment = forms.FileField(required=False)


class SettlementForm(forms.Form):
    """Header fields of a settlement. amount_paid defaults to full payable
    (set by the view); per-advance recoveries are parsed from POST in the view."""
    amount_paid = forms.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal('0'))
    settlement_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    method = forms.ChoiceField(
        choices=PayrollSettlement.Method.choices, initial=PayrollSettlement.Method.CASH)
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2}))


class WorkerProfileForm(forms.ModelForm):
    class Meta:
        model = WorkerProfile
        fields = [
            'phone', 'bank_account_name', 'bank_account_number', 'bank_ifsc',
            'upi_id', 'joining_date', 'opening_advance', 'is_active', 'notes',
        ]
        widgets = {
            'joining_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }
