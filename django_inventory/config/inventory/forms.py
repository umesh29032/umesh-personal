from django import forms
from .models import ClothRoll, BatchClothAssignment, BatchUserAssignment, BatchOperation, Product, Stage, Machine


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
        for field_name, field in self.fields.items():
            current_classes = field.widget.attrs.get('class', '')
            if 'form-control' not in current_classes and 'form-select' not in current_classes:
                field.widget.attrs['class'] = 'form-control'


class BatchClothAssignmentForm(forms.ModelForm):
    class Meta:
        model = BatchClothAssignment
        fields = ['cloth_roll', 'reserved_length', 'consumed_length', 'wastage_length', 'status']
        widgets = {
            'cloth_roll': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            current_classes = field.widget.attrs.get('class', '')
            if 'form-control' not in current_classes and 'form-select' not in current_classes:
                field.widget.attrs['class'] = 'form-control'


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
            current_classes = field.widget.attrs.get('class', '')
            if 'form-control' not in current_classes and 'form-select' not in current_classes:
                field.widget.attrs['class'] = 'form-control'


class BatchOperationForm(forms.ModelForm):
    class Meta:
        model = BatchOperation
        fields = ['stage', 'user', 'machine', 'start_time', 'end_time', 'output_quantity', 'notes']
        widgets = {
            'stage': forms.Select(attrs={'class': 'form-select'}),
            'user': forms.Select(attrs={'class': 'form-select'}),
            'machine': forms.Select(attrs={'class': 'form-select'}),
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            current_classes = field.widget.attrs.get('class', '')
            if 'form-control' not in current_classes and 'form-select' not in current_classes:
                field.widget.attrs['class'] = 'form-control'


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['sku', 'name', 'category', 'size', 'color', 'batch', 'quantity', 'price', 'manufacturing_cost', 'location']
        widgets = {
            'batch': forms.Select(attrs={'class': 'form-select'}),
            'location': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            current_classes = field.widget.attrs.get('class', '')
            if 'form-control' not in current_classes and 'form-select' not in current_classes:
                field.widget.attrs['class'] = 'form-control'


class StageForm(forms.ModelForm):
    class Meta:
        model = Stage
        fields = ['name', 'description', 'stage_type', 'is_active']
        widgets = {
            'stage_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            current_classes = field.widget.attrs.get('class', '')
            if 'form-control' not in current_classes and 'form-select' not in current_classes:
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
            current_classes = field.widget.attrs.get('class', '')
            if 'form-control' not in current_classes and 'form-select' not in current_classes:
                field.widget.attrs['class'] = 'form-control'
