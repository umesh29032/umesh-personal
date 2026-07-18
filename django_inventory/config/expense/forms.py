"""Expense forms — advance entry, settlement header, worker profile.

Thin: views call services. The settlement's per-advance recovery rows are
dynamic (one input per outstanding advance) so they're parsed in the view, not
here — this form only carries the header fields (cash paid / date / method).
"""
import re
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


class FactoryExpenseForm(forms.Form):
    """R5 (PDD §21): thin entry form — salary⇒worker rule lives in
    expense_service (single source), the form only carries fields."""
    from expense.models import FactoryExpense as _FE
    category = forms.ChoiceField(choices=_FE.Category.choices)
    amount = forms.DecimalField(max_digits=12, decimal_places=2,
                                min_value=Decimal('0.01'))
    expense_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}))
    # Visible only for category=salary (template JS); service re-validates.
    worker = forms.ModelChoiceField(queryset=_worker_qs(), required=False)
    notes = forms.CharField(required=False,
                            widget=forms.Textarea(attrs={'rows': 2}))


class SettlementForm(forms.Form):
    """Header fields of a settlement. amount_paid defaults to full payable
    (set by the view); per-advance recoveries are parsed from POST in the view."""
    amount_paid = forms.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal('0'))
    settlement_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    method = forms.ChoiceField(
        choices=PayrollSettlement.Method.choices, initial=PayrollSettlement.Method.CASH)
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2}))


class WorkerProfileForm(forms.ModelForm):
    # PA-06-1: opening_advance is a DISPLAYED ₹ figure (WP-A: informational only —
    # no recovery math reads it; recoverable pre-system advances = dated Advance
    # rows via record_advance). Pin >= 0 so the display can't show a negative
    # (mirrors AdvanceForm.amount). Bank/IFSC/account get blank-tolerant format
    # validation so malformed payout details can't be saved (PA-06-2).
    # RCP-1A F3 (2026-07-18): the WRITE goes through
    # payroll_service.update_payout_profile — never a bare form.save() in the view.
    opening_advance = forms.DecimalField(
        max_digits=12, decimal_places=2, min_value=Decimal('0'),
        help_text="Loans given before the system started. Cannot be negative.",
    )

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

    def clean_bank_ifsc(self):
        # Standard Indian IFSC: 4 letters + '0' + 6 alphanumerics. Blank allowed;
        # normalise to upper so 'hdfc0001234' is accepted. Wrong IFSC = failed payout.
        ifsc = (self.cleaned_data.get('bank_ifsc') or '').strip().upper()
        if ifsc and not re.fullmatch(r'[A-Z]{4}0[A-Z0-9]{6}', ifsc):
            raise forms.ValidationError("Enter a valid 11-character IFSC (e.g. HDFC0001234).")
        return ifsc

    def clean_bank_account_number(self):
        acct = (self.cleaned_data.get('bank_account_number') or '').strip()
        if acct and not re.fullmatch(r'\d{9,18}', acct):
            raise forms.ValidationError("Bank account number must be 9–18 digits.")
        return acct

    def clean(self):
        cleaned = super().clean()
        # Half-entered bank details cause failed payouts — require the set together.
        if cleaned.get('bank_account_number') and not (
            cleaned.get('bank_ifsc') and cleaned.get('bank_account_name')
        ):
            raise forms.ValidationError(
                "Bank account number needs both an IFSC and an account holder name.")
        return cleaned


class ExpenseTemplateForm(forms.Form):
    """MEE-C: thin entry form for recurring-expense templates — fields only.
    EVERY rule (SA gate, P-1 pair, window order, one-active-salary-per-worker)
    lives in expense_service.create_expense_template (single source)."""
    from expense.models import FactoryExpense as _FE
    label = forms.CharField(max_length=100)
    category = forms.ChoiceField(choices=_FE.Category.choices)
    amount = forms.DecimalField(max_digits=12, decimal_places=2,
                                min_value=Decimal('0.01'))
    # Visible only for category=salary (template JS); service re-validates.
    worker = forms.ModelChoiceField(queryset=_worker_qs(), required=False)
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(
        required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    notes = forms.CharField(required=False,
                            widget=forms.Textarea(attrs={'rows': 2}))
