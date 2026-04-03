from django import forms

from ..models import Product


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'sku', 'name', 'category', 'size', 'color',
            'batch', 'quantity', 'price', 'manufacturing_cost', 'location',
        ]
        widgets = {
            'batch':    forms.Select(attrs={'class': 'form-select'}),
            'location': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            current = field.widget.attrs.get('class', '')
            if 'form-control' not in current and 'form-select' not in current:
                field.widget.attrs['class'] = 'form-control'

    def clean(self):
        cleaned = super().clean()
        quantity = cleaned.get('quantity')
        price = cleaned.get('price')
        manufacturing_cost = cleaned.get('manufacturing_cost')

        if quantity is not None and quantity < 0:
            self.add_error('quantity', "Quantity cannot be negative.")

        if price is not None and price < 0:
            self.add_error('price', "Selling price cannot be negative.")

        if manufacturing_cost is not None and manufacturing_cost < 0:
            self.add_error('manufacturing_cost', "Manufacturing cost cannot be negative.")

        return cleaned
