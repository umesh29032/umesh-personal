from django import forms

from ..models import Stage, Machine


class StageForm(forms.ModelForm):
    class Meta:
        model = Stage
        fields = ['name', 'code', 'category', 'stage_type', 'description', 'default_is_mandatory', 'is_active']
        widgets = {
            'stage_type':  forms.Select(attrs={'class': 'form-select'}),
            'category':    forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            current = field.widget.attrs.get('class', '')
            if 'form-control' not in current and 'form-select' not in current:
                field.widget.attrs['class'] = 'form-control'


class MachineForm(forms.ModelForm):
    class Meta:
        model = Machine
        fields = ['name', 'machine_type', 'stage', 'is_active']
        widgets = {
            'stage': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            current = field.widget.attrs.get('class', '')
            if 'form-control' not in current and 'form-select' not in current:
                field.widget.attrs['class'] = 'form-control'
