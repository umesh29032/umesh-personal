from django import forms
from .models import ClothRoll

class ClothRollForm(forms.ModelForm):
    class Meta:
        model = ClothRoll
        fields = [
            'purchased_date', 'roll_number', 'cloth_type', 'color', 'width', 'gsm',
            'total_length', 'remaining_length', 'cost_per_meter', 'supplier',
            'location', 'status', 'exhaustion_date', 'batch_alloted'
        ]
        widgets = {
            'purchased_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'exhaustion_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'batch_alloted': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'cloth_type': forms.Select(attrs={'class': 'form-select'}),
            'color': forms.Select(attrs={'class': 'form-select'}),
            'location': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply strict styling to all fields to ensure consistency
        for field_name, field in self.fields.items():
            current_classes = field.widget.attrs.get('class', '')
            if 'form-control' not in current_classes and 'form-select' not in current_classes:
                 field.widget.attrs['class'] = 'form-control'
