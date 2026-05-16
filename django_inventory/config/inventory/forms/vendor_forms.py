from django import forms

from ..models import Vendor, VendorDispatch, Payment


def _bootstrap_classes(form):
    for field in form.fields.values():
        cls = field.widget.attrs.get('class', '')
        if isinstance(field.widget, (forms.Select, forms.SelectMultiple)):
            if 'form-select' not in cls:
                field.widget.attrs['class'] = (cls + ' form-select').strip()
        elif isinstance(field.widget, (forms.CheckboxInput,)):
            field.widget.attrs['class'] = (cls + ' form-check-input').strip()
        else:
            if 'form-control' not in cls:
                field.widget.attrs['class'] = (cls + ' form-control').strip()


class VendorForm(forms.ModelForm):
    class Meta:
        model = Vendor
        fields = ['name', 'contact_person', 'phone', 'email', 'gst_number', 'address', 'is_active']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _bootstrap_classes(self)


class VendorDispatchForm(forms.ModelForm):
    class Meta:
        model = VendorDispatch
        fields = [
            'batch', 'batch_stage', 'vendor', 'vehicle_no',
            'driver_name', 'driver_phone', 'dispatched_qty',
            'transport_cost', 'status', 'dispatched_at',
        ]
        widgets = {
            'dispatched_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _bootstrap_classes(self)


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = [
            'batch', 'vendor', 'dispatch', 'amount', 'mode',
            'reference', 'status', 'received_at', 'notes',
        ]
        widgets = {
            'received_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _bootstrap_classes(self)
