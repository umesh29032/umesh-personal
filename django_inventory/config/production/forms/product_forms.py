"""Product CRUD form.

YEH FILE KYU HAI?
─────────────────
Product create/edit ka ModelForm. `code` edit pe lock hota hai —
warna existing Adda codes ('T-SHIRT-001') orphan ho jaate.
"""
from django import forms

from production.models import Product


_BASE = {'class': 'sf-input', 'autocomplete': 'off'}


class ProductForm(forms.ModelForm):
    """Product form — code/name/description editable; code edit pe locked."""

    class Meta:
        model = Product
        fields = ['code', 'name', 'description']
        widgets = {
            'code': forms.TextInput(attrs={**_BASE, 'placeholder': 'e.g. T-SHIRT', 'style': 'text-transform:uppercase;'}),
            'name': forms.TextInput(attrs={**_BASE, 'placeholder': 'Display name'}),
            'description': forms.Textarea(attrs={**_BASE, 'rows': 3, 'placeholder': 'Optional notes'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Instance.pk = is form pe edit ho raha hai (na ki create)
        # disabled=True → HTML form submit mein bhi field ignore hoga (DB unchanged)
        # Adda codes stable rakhne ke liye — code change ki jaroorat ho to data migration likho
        if self.instance.pk:
            self.fields['code'].disabled = True
