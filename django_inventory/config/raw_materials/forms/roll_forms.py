"""ClothRoll forms — bulk intake + Adda assignment.

YEH FILE KYU HAI?
─────────────────
BulkRollForm     — bulk add page ka form. Color breakup parallel arrays se aata hai.
AssignRollForm   — roll-to-Adda assignment ka form. Weight + width yahin capture.

Parallel arrays kya hain?
────────────────────────
HTML mein N rows ki `<select name="breakup_color">` + `<input name="breakup_qty">`
hoti hain. POST mein same name ke saare values list ban jaate hain. View getlist()
karke zip karta hai, phir form ke clean() mein structured dict list ban jaati hai.
"""
from datetime import date

from django import forms

from accounts.services import user_can_edit_financials
from raw_materials.models import ClothColor, ClothType, ClothRoll, StorageLocation, WIDTH_CHOICES


# Common widget attrs — har input pe consistent class + autocomplete off
_BASE_INPUT_ATTRS = {'class': 'sf-input', 'autocomplete': 'off'}


class BulkRollForm(forms.Form):
    """Bulk roll intake form.

    Step 1: shared metadata (cloth_type, location, purchased_date, supplier, cost).
    Step 2: N rows of (color, qty) breakup — JS-driven repeating rows.

    Form ne __init__ mein:
      • user role check kar ke supplier/cost_per_kg fields pop kar deta hai
        (non-finance users ko show hi nahi karna — defence in depth)
      • raw_breakup list view se inject hoti hai (parallel arrays se zip ki hui)
    clean() validate karta hai breakup + structured `breakup` list cleaned_data mein daalta hai.
    """

    cloth_type = forms.ModelChoiceField(
        queryset=ClothType.active.all(),   # archived hide via ActiveManager
        widget=forms.Select(attrs=_BASE_INPUT_ATTRS),
    )
    storage_location = forms.ModelChoiceField(
        queryset=StorageLocation.active.all(),
        widget=forms.Select(attrs=_BASE_INPUT_ATTRS),
    )
    purchased_date = forms.DateField(
        initial=date.today,    # default = aaj — user edit kar sakta hai
        widget=forms.DateInput(attrs={**_BASE_INPUT_ATTRS, 'type': 'date'}),
    )
    # Financial fields — non-finance users ke liye __init__ mein pop hote hain
    supplier = forms.CharField(
        required=False, max_length=200,
        widget=forms.TextInput(attrs={**_BASE_INPUT_ATTRS, 'placeholder': 'optional'}),
    )
    # C-1 (ADR-0009): PURCHASE price — a fact, never a market/replacement price.
    # Stays optional (owner: honest-NULL over placeholder prices); unpriced
    # consumed rolls are surfaced loudly on the costing dashboard instead.
    cost_per_kg = forms.DecimalField(
        required=False, max_digits=10, decimal_places=2,
        help_text='Purchase price per kg (leave blank if unknown — never guess)',
        widget=forms.NumberInput(attrs={**_BASE_INPUT_ATTRS, 'step': '0.01', 'placeholder': '0.00'}),
    )

    def __init__(self, *args, user, raw_breakup=None, **kwargs):
        # user kwargs se aata hai — form gating ke liye
        self.user = user
        self.raw_breakup = raw_breakup or []
        super().__init__(*args, **kwargs)
        # Role gate — non-finance users ke liye fields field set se nikal do
        if not user_can_edit_financials(user):
            self.fields.pop('supplier', None)
            self.fields.pop('cost_per_kg', None)

    def clean(self):
        """raw_breakup parallel arrays ko validated `breakup` list of dicts mein convert."""
        cleaned = super().clean()
        breakup: list[dict] = []
        for row in self.raw_breakup:
            color_id = row.get('color')
            qty_raw = row.get('qty')
            # Empty rows skip — JS template empty row dikha sakta hai
            if not color_id or not qty_raw:
                continue
            try:
                qty = int(qty_raw)
            except (TypeError, ValueError):
                raise forms.ValidationError("Each breakup qty must be a positive integer")
            if qty < 1:
                raise forms.ValidationError("Each breakup qty must be at least 1")
            try:
                # ActiveManager — archived color reject (raises DoesNotExist)
                color = ClothColor.active.get(pk=color_id)
            except ClothColor.DoesNotExist:
                raise forms.ValidationError("Selected cloth color is invalid or archived")
            breakup.append({'color': color, 'qty': qty})
        # At-least-one rule — empty breakup invalid
        if not breakup:
            raise forms.ValidationError("Add at least one color row to the breakup")
        cleaned['breakup'] = breakup
        return cleaned


class RollEditForm(forms.ModelForm):
    """Stock-level edit form for a ClothRoll.

    Why ek alag form?
        Bulk intake pe sirf type + color set hote hain. Width/weight blank rehte hain
        (Layering attach time pe verify hote the). Lekin user inventory dashboard se
        chahta hai "ye roll 42 inch / 25 KG ka" — so ek manual edit path zaroori.

    Allowed fields:
        • width_inch, weight_kg, storage_location, purchased_date — sab roles edit kar sakte
        • supplier, cost_per_kg — sirf financial roles ke liye
        • roll_id, cloth_type, cloth_color, status, adda — IMMUTABLE (yahan exclude)

    Service layer (`update_roll_details`) extra guard rakhta hai: USED rolls block
    karta hai taa-ke layering verification ke saath sync na toote.
    """

    class Meta:
        model = ClothRoll
        fields = ['width_inch', 'weight_kg', 'storage_location', 'purchased_date',
                  'supplier', 'cost_per_kg']
        widgets = {
            'width_inch': forms.Select(attrs=_BASE_INPUT_ATTRS),
            'weight_kg': forms.NumberInput(attrs={**_BASE_INPUT_ATTRS, 'step': '0.01', 'placeholder': 'KG'}),
            'storage_location': forms.Select(attrs=_BASE_INPUT_ATTRS),
            'purchased_date': forms.DateInput(attrs={**_BASE_INPUT_ATTRS, 'type': 'date'}),
            'supplier': forms.TextInput(attrs={**_BASE_INPUT_ATTRS, 'placeholder': 'optional'}),
            'cost_per_kg': forms.NumberInput(attrs={**_BASE_INPUT_ATTRS, 'step': '0.01'}),
        }

    def __init__(self, *args, user, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        # Filter dropdowns to active master data via ActiveManager
        self.fields['storage_location'].queryset = StorageLocation.active.all()
        # Role gate financial fields — non-finance users ko form set se nikalo
        if not user_can_edit_financials(user):
            self.fields.pop('supplier', None)
            self.fields.pop('cost_per_kg', None)


class AssignRollForm(forms.Form):
    """Roll-to-Adda assign form. Weight + width yahin capture hote hain (intake pe NHI).

    `adda_code` CharField hai (Adda.code string) — view dropdown choices populate karta hai
    in-progress Layering Addas ka. Form import time pe production app pe depend nahi karta.
    """

    weight_kg = forms.DecimalField(
        max_digits=8, decimal_places=2,
        widget=forms.NumberInput(attrs={**_BASE_INPUT_ATTRS, 'step': '0.01', 'placeholder': 'KG'}),
    )
    width_inch = forms.ChoiceField(
        choices=WIDTH_CHOICES,   # 36..44 inch
        widget=forms.Select(attrs=_BASE_INPUT_ATTRS),
    )
    # CharField (not ModelChoiceField) — production app se decoupled
    # View __init__ mein adda_choices inject karta hai
    adda_code = forms.CharField(
        max_length=40,
        widget=forms.Select(attrs=_BASE_INPUT_ATTRS),
    )

    def __init__(self, *args, adda_choices=(), **kwargs):
        super().__init__(*args, **kwargs)
        # widget.choices dynamic populate — Addas filter on stage type Layering
        self.fields['adda_code'].widget.choices = adda_choices

    def clean_width_inch(self):
        """ChoiceField string return karta hai — int mein convert"""
        return int(self.cleaned_data['width_inch'])
