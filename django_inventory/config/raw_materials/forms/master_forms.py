"""Master data CRUD forms — ClothType, ClothColor, StorageLocation.

YEH FILE KYU HAI?
─────────────────
Teen master models ka simple ModelForm — naam + kuch field. UI form-shell pattern
mein render hota hai. ModelForm `Meta.model + fields` se auto-magic karta hai.
"""
from django import forms

from raw_materials.models import ClothType, ClothColor, StorageLocation


# Common widget attrs — `sf-input` class form-shell ka cream + inset-shadow style
# autocomplete='off' = browser ka suggestion popup off (factory data sensitive)
_BASE_INPUT_ATTRS = {
    'class': 'sf-input',
    'autocomplete': 'off',
}


class ClothTypeForm(forms.ModelForm):
    """ClothType ka basic form — sirf naam editable. is_active service ke through change hota hai."""

    class Meta:
        model = ClothType
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={**_BASE_INPUT_ATTRS, 'placeholder': 'e.g. Cotton'}),
        }


class ClothColorForm(forms.ModelForm):
    """ClothColor form. hex_code optional swatch — HTML pattern attribute se browser validate karta hai."""

    class Meta:
        model = ClothColor
        fields = ['name', 'hex_code']
        widgets = {
            'name': forms.TextInput(attrs={**_BASE_INPUT_ATTRS, 'placeholder': 'e.g. Indigo'}),
            # pattern regex = '#' + 6 hex digits. Browser native validation.
            'hex_code': forms.TextInput(attrs={
                **_BASE_INPUT_ATTRS,
                'placeholder': '#1a2b3c (optional)',
                'pattern': r'^#[0-9A-Fa-f]{6}$',
            }),
        }


class StorageLocationForm(forms.ModelForm):
    """StorageLocation form — name + short uppercase code (e.g. ROHINI)."""

    class Meta:
        model = StorageLocation
        fields = ['name', 'code']
        widgets = {
            'name': forms.TextInput(attrs={**_BASE_INPUT_ATTRS, 'placeholder': 'e.g. Rohini Factory'}),
            'code': forms.TextInput(attrs={
                **_BASE_INPUT_ATTRS,
                'placeholder': 'e.g. ROHINI',
                # CSS hint — typing time visually uppercase dikhega
                'style': 'text-transform:uppercase;',
            }),
        }

    def clean_code(self):
        # `clean_<field>` Django form pattern — submit ke time DB save se pehle normalize
        # Uppercase + trimmed — taa-ke future Adda code composition predictable rahe
        return self.cleaned_data['code'].strip().upper()
