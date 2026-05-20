"""Adda creation form.

YEH FILE KYU HAI?
─────────────────
Naya Adda banane ka simple form — sirf product picker. Baaki sab (code, counter,
current_stage) service create_adda() handle karta hai.
"""
from django import forms

from production.models import Product


_BASE = {'class': 'sf-input', 'autocomplete': 'off'}


class AddaCreateForm(forms.Form):
    """User sirf Product chunta hai. Adda code service-side allocate hota hai."""

    # ModelChoiceField = FK ka form widget. queryset filter archived products hide kar deta hai
    product = forms.ModelChoiceField(
        queryset=Product.objects.filter(is_active=True),
        widget=forms.Select(attrs=_BASE),
    )
