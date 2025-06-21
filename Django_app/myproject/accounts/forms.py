# accounts/forms.py
from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import AuthenticationForm
# from .models import User
User = get_user_model()
class LoginForm(AuthenticationForm):
    username = forms.EmailField(label="Email")

class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'password')

class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'phone_number', 'birth_date','date_joined', 'bio', 'salary', 'is_active', 'is_staff', 'is_superuser']
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Customize form fields
        self.fields['phone_number'].widget.attrs.update({'placeholder': 'Enter phone number (numbers only)'})
        self.fields['salary'].widget.attrs.update({'step': '0.01', 'placeholder': 'Enter salary (e.g., 5000.00)'})
        self.fields['birth_date'].widget = forms.DateInput(attrs={'type': 'date'})
        self.fields['date_joined'].widget = forms.DateTimeInput(attrs={'type': 'datetime-local'})

    def clean_phone_number(self):
        phone = self.cleaned_data['phone_number']
        if phone and not phone.isdigit():
            raise ValidationError("Phone number must contain only digits.")
        return phone

    def clean_salary(self):
        salary = self.cleaned_data['salary']
        if salary is not None and salary < 0:
            raise ValidationError("Salary cannot be negative.")
        return salary