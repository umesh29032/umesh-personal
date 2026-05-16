"""
Forms for the accounts app.

Three main forms:
  SignupForm      — public self-registration (email + password only)
  UserCreateForm  — Super Admin creates a user with full profile + role
  UserEditForm    — Super Admin edits an existing user; optional password change

Password security:
  All three forms run Django's AUTH_PASSWORD_VALIDATORS stack via
  `validate_password()`. This enforces min length (8), blocks common passwords,
  blocks all-numeric passwords, and checks similarity to user attributes.
"""
from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import User, Skill


class SkillForm(forms.ModelForm):
    """Simple create/edit form for Skill objects (managed by Super Admin)."""
    class Meta:
        model = Skill
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Enter skill name (e.g., Python, Welding)'})
        }


class UserEditForm(forms.ModelForm):
    """
    Edit an existing user. `new_password` is optional — leave blank to keep
    the current password. Enforces email uniqueness excluding the edited user.
    """
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
            'user_type', 'role', 'is_active', 'is_staff', 'is_superuser',
            'bio', 'skills', 'salary', 'birth_date', 'profile_picture'
        ]

    def clean_email(self):
        # ModelForm doesn't enforce uniqueness automatically on edit because the
        # form is bound to an existing instance — we must exclude self.
        email = (self.cleaned_data.get('email') or '').strip().lower()
        qs = User.objects.filter(email__iexact=email)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("Another user already uses this email.")
        return email

    def clean_new_password(self):
        pwd = self.cleaned_data.get('new_password')
        if pwd:
            # Pass `user=self.instance` so the similarity validator can check
            # the new password against the user's own name and email.
            try:
                validate_password(pwd, user=self.instance)
            except ValidationError as e:
                raise ValidationError(e.messages)
        return pwd

    def save(self, commit=True):
        user = super().save(commit=False)
        new_password = self.cleaned_data.get('new_password')
        if new_password:
            # set_password hashes the password — never store plain text.
            user.set_password(new_password)
        if commit:
            user.save()
            self.save_m2m()  # save_m2m() must be called separately when commit=False was used
        return user


class UserCreateForm(forms.ModelForm):
    """
    Super Admin creates a new user and assigns credentials + role in one step.
    The created user can later change their own password from their profile.
    """
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Set initial password'}),
        label="Password",
        help_text="The user can change this later from their profile.",
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm password'}),
        label="Confirm Password",
    )

    class Meta:
        model = User
        fields = [
            'email', 'first_name', 'last_name', 'phone_number',
            'user_type', 'role', 'is_active', 'is_staff', 'is_superuser',
            'skills', 'salary',
        ]

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip().lower()
        # User.email has unique=True at the DB level, but we validate early
        # so the admin sees a clear form error instead of a 500.
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("A user with this email already exists.")
        return email

    def clean(self):
        cleaned = super().clean()
        pwd = cleaned.get('password')
        confirm = cleaned.get('confirm_password')
        if pwd and confirm and pwd != confirm:
            raise ValidationError("Passwords do not match.")
        if pwd:
            # `add_error` attaches the error to the 'password' field so the
            # template can display it next to that input, not at the top.
            try:
                validate_password(pwd)
            except ValidationError as e:
                self.add_error('password', e)
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        # set_password hashes with Argon2 (first in PASSWORD_HASHERS in base.py).
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
            self.save_m2m()
        return user


class SignupForm(forms.Form):
    """
    Public self-registration form. Stores email + validated password only.
    No profile fields — those can be filled in later.

    Anti-enumeration: clean_email deliberately does NOT check whether the
    email already exists. If it did, an attacker could enumerate registered
    users by submitting emails and observing the error. The duplicate-email
    case is handled silently in SignupVerifyView (catches IntegrityError).
    """
    email = forms.EmailField(widget=forms.EmailInput(attrs={'placeholder': 'Email Address'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Create Password'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Confirm Password'}))

    def clean_email(self):
        # Normalize only — no existence check (see anti-enumeration note above).
        return (self.cleaned_data.get('email') or '').strip().lower()

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            raise ValidationError("Passwords do not match.")
        if password:
            try:
                validate_password(password)
            except ValidationError as e:
                self.add_error('password', e)
        return cleaned_data
