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
    new_password = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False
    )
    confirm_password = forms.CharField(
        label="Confirm New Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False
    )
    class Meta:
        model = User
        fields = ['email','password', 'first_name', 'last_name', 'phone_number', 'birth_date','date_joined','user_type', 'bio', 'salary', 'is_active', 'is_staff', 'is_superuser']
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Customize form fields
        self.fields['phone_number'].widget.attrs.update({'placeholder': 'Enter phone number (numbers only)'})
        self.fields['salary'].widget.attrs.update({'step': '0.01', 'placeholder': 'Enter salary (e.g., 5000.00)'})
        self.fields['birth_date'].widget = forms.DateInput(attrs={'type': 'date'})
        self.fields['date_joined'].widget = forms.DateTimeInput(attrs={'type': 'datetime-local'})
        self.fields['user_type'].widget = forms.Select(choices=User.USER_TYPE_CHOICES)

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')
        if new_password or confirm_password:
            if not new_password:
                self.add_error('new_password', "New password is required if changing.")
            if not confirm_password:
                self.add_error('confirm_password', "Confirm password is required if changing.")
            if new_password and confirm_password and new_password != confirm_password:
                self.add_error('confirm_password', "Passwords do not match.")
            if new_password and self.instance.check_password(new_password):
                self.add_error('new_password', "New password cannot be the same as the old password.")
        return cleaned_data

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

    def save(self, *args, **kwargs):
        user = super().save(*args, **kwargs)
        new_password = self.cleaned_data.get('new_password')
        if new_password:
            user.set_password(new_password)
            user.save()
        return user