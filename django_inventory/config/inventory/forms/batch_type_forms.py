from django import forms

from ..models import BatchType


class BatchTypeForm(forms.ModelForm):
    class Meta:
        model = BatchType
        fields = ['name', 'code', 'description', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            cls = field.widget.attrs.get('class', '')
            if 'form-control' not in cls and 'form-select' not in cls:
                field.widget.attrs['class'] = 'form-control'
