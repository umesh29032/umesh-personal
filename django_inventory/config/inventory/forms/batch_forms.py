from django import forms

from ..models import BatchClothAssignment, BatchUserAssignment, BatchOperation, Batch
from ..constants import BatchStatus


class BatchForm(forms.ModelForm):
    class Meta:
        model = Batch
        fields = ['batch_number', 'name', 'current_stage', 'status']
        widgets = {
            'current_stage': forms.Select(attrs={'class': 'form-select'}),
            'status':        forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            current = field.widget.attrs.get('class', '')
            if 'form-control' not in current and 'form-select' not in current:
                field.widget.attrs['class'] = 'form-control'


class BatchClothAssignmentForm(forms.ModelForm):
    class Meta:
        model = BatchClothAssignment
        fields = ['cloth_roll', 'reserved_length', 'consumed_length', 'wastage_length', 'status']
        widgets = {
            'cloth_roll': forms.Select(attrs={'class': 'form-select'}),
            'status':     forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            current = field.widget.attrs.get('class', '')
            if 'form-control' not in current and 'form-select' not in current:
                field.widget.attrs['class'] = 'form-control'

    def clean(self):
        cleaned = super().clean()
        reserved = cleaned.get('reserved_length')
        consumed = cleaned.get('consumed_length')
        wastage = cleaned.get('wastage_length')
        cloth_roll = cleaned.get('cloth_roll')

        if reserved is not None and reserved <= 0:
            self.add_error('reserved_length', "Reserved length must be greater than 0.")

        if consumed is not None and consumed < 0:
            self.add_error('consumed_length', "Consumed length cannot be negative.")

        if wastage is not None and wastage < 0:
            self.add_error('wastage_length', "Wastage length cannot be negative.")

        if reserved and consumed is not None and wastage is not None:
            if consumed + wastage > reserved:
                raise forms.ValidationError(
                    f"Consumed ({consumed}m) + wastage ({wastage}m) = {consumed + wastage}m "
                    f"exceeds the reserved length ({reserved}m)."
                )

        if cloth_roll and reserved is not None:
            if reserved > cloth_roll.remaining_length:
                self.add_error(
                    'reserved_length',
                    f"Reserved amount ({reserved}m) exceeds available cloth on this roll "
                    f"({cloth_roll.remaining_length}m)."
                )

        return cleaned


class BatchUserAssignmentForm(forms.ModelForm):
    class Meta:
        model = BatchUserAssignment
        fields = ['user', 'role', 'is_active']
        widgets = {
            'user': forms.Select(attrs={'class': 'form-select'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            current = field.widget.attrs.get('class', '')
            if 'form-control' not in current and 'form-select' not in current:
                field.widget.attrs['class'] = 'form-control'


class BatchOperationForm(forms.ModelForm):
    class Meta:
        model = BatchOperation
        fields = ['stage', 'user', 'machine', 'start_time', 'end_time', 'output_quantity', 'notes']
        widgets = {
            'stage':      forms.Select(attrs={'class': 'form-select'}),
            'user':       forms.Select(attrs={'class': 'form-select'}),
            'machine':    forms.Select(attrs={'class': 'form-select'}),
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'end_time':   forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'notes':      forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            current = field.widget.attrs.get('class', '')
            if 'form-control' not in current and 'form-select' not in current:
                field.widget.attrs['class'] = 'form-control'

    def clean(self):
        cleaned = super().clean()
        start_time = cleaned.get('start_time')
        end_time = cleaned.get('end_time')
        output_qty = cleaned.get('output_quantity')

        if start_time and end_time and end_time <= start_time:
            self.add_error('end_time', "End time must be after start time.")

        if output_qty is not None and output_qty < 0:
            self.add_error('output_quantity', "Output quantity cannot be negative.")

        return cleaned
