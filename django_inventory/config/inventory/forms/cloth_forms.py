from django import forms
from django.core.exceptions import ValidationError

from ..models import ClothRoll


class ClothRollForm(forms.ModelForm):
    class Meta:
        model = ClothRoll
        fields = [
            'purchased_date', 'roll_number', 'cloth_type', 'color', 'width', 'gsm',
            'total_length', 'remaining_length', 'cost_per_meter', 'supplier',
            'location', 'status', 'exhaustion_date', 'batch_alloted',
        ]
        widgets = {
            'purchased_date':  forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'exhaustion_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'batch_alloted':   forms.Select(attrs={'class': 'form-select'}),
            'status':          forms.Select(attrs={'class': 'form-select'}),
            'cloth_type':      forms.Select(attrs={'class': 'form-select'}),
            'color':           forms.Select(attrs={'class': 'form-select'}),
            'location':        forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            current = field.widget.attrs.get('class', '')
            if 'form-control' not in current and 'form-select' not in current:
                field.widget.attrs['class'] = 'form-control'

    def clean(self):
        cleaned = super().clean()
        total_length = cleaned.get('total_length')
        remaining_length = cleaned.get('remaining_length')
        cost_per_meter = cleaned.get('cost_per_meter')
        width = cleaned.get('width')

        if total_length is not None and total_length <= 0:
            self.add_error('total_length', "Total length must be greater than 0.")

        if cost_per_meter is not None and cost_per_meter <= 0:
            self.add_error('cost_per_meter', "Cost per meter must be greater than 0.")

        if width is not None and width <= 0:
            self.add_error('width', "Width must be greater than 0.")

        if total_length and remaining_length is not None:
            if remaining_length < 0:
                self.add_error('remaining_length', "Remaining length cannot be negative.")
            elif remaining_length > total_length:
                self.add_error('remaining_length', "Remaining length cannot exceed total length.")

        purchased = cleaned.get('purchased_date')
        exhaustion = cleaned.get('exhaustion_date')
        if purchased and exhaustion and exhaustion < purchased:
            self.add_error('exhaustion_date', "Exhaustion date cannot be before the purchased date.")

        return cleaned
