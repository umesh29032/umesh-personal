from django import forms
from django.core.exceptions import ValidationError
from .models import User

class UserEditForm(forms.ModelForm):
    new_password = forms.CharField(
        required=False, 
        widget=forms.PasswordInput(attrs={'placeholder': 'Leave blank to keep current password'}),
        label="Set New Password",
        help_text="Enter a new password to change it for this user."
    )

    class Meta:
        model = User
        fields = [
            'email', 'first_name', 'last_name', 'phone_number', 
            'user_type', 'is_active', 'is_staff', 'is_superuser',
            'bio', 'skills', 'salary', 'birth_date', 'profile_picture'
        ]

    def save(self, commit=True):
        user = super().save(commit=False)
        new_password = self.cleaned_data.get('new_password')
        if new_password:
            user.set_password(new_password)
        if commit:
            user.save()
            self.save_m2m()
        return user

class SignupForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'placeholder': 'Email Address'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Create Password'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Confirm Password'}))

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("A user with this email already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            raise ValidationError("Passwords do not match.")
        return cleaned_data
