"""
URL configuration for the accounts app.

All paths are mounted under /app/ by the root URLconf (config/urls.py).
Use {% url 'accounts:<name>' %} in templates or reverse('accounts:<name>') in Python.

Auth flow:
  /app/            → OTP login step 1 (email entry)
  /app/verify-otp/ → OTP login step 2 (code entry)
  /app/login/password/ → alternative password login

Signup flow:
  /app/signup/         → email + password form
  /app/signup/verify/  → OTP verification step

Password reset flow:
  /app/forgot-password/        → email entry
  /app/reset-password/verify/  → OTP + new password in one step
"""
from django.urls import path
from .views import (
    LoginView, VerifyOTPView, HomeView, LogoutView, ResendOTPView,
    UserListView, UserCreateView, UserUpdateView, UserDeleteView, PasswordLoginView,
    SignupView, SignupVerifyView, ForgotPasswordView, ResetPasswordVerifyView, ResendSignupOTPView,
    SkillListView, SkillCreateView, SkillUpdateView, SkillDeleteView
)

app_name = "accounts"

urlpatterns = [
    # ── OTP login ────────────────────────────────────────────────────────────
    path("", LoginView.as_view(), name="login"),               # step 1: email
    path("verify-otp/", VerifyOTPView.as_view(), name="verify_otp"),  # step 2: OTP
    path("resend-otp/", ResendOTPView.as_view(), name="resend_otp"),

    # ── Password login (fallback) ─────────────────────────────────────────────
    path("login/password/", PasswordLoginView.as_view(), name="login_password"),

    # ── Post-login redirect + logout ─────────────────────────────────────────
    path("home/", HomeView.as_view(), name="home"),            # immediately bounces to inventory
    path("logout/", LogoutView.as_view(), name="logout"),      # POST-only (CSRF protection)

    # ── Self-registration ─────────────────────────────────────────────────────
    path("signup/", SignupView.as_view(), name="signup"),
    path("signup/verify/", SignupVerifyView.as_view(), name="signup_verify"),
    path("signup/resend-otp/", ResendSignupOTPView.as_view(), name="signup_resend_otp"),

    # ── Password reset ────────────────────────────────────────────────────────
    path("forgot-password/", ForgotPasswordView.as_view(), name="forgot_password"),
    path("reset-password/verify/", ResetPasswordVerifyView.as_view(), name="reset_password_verify"),

    # ── User management (Super Admin only) ────────────────────────────────────
    path("users/", UserListView.as_view(), name="user_list"),
    path("users/add/", UserCreateView.as_view(), name="user_add"),
    path("users/<int:pk>/edit/", UserUpdateView.as_view(), name="user_edit"),
    path("users/<int:pk>/delete/", UserDeleteView.as_view(), name="user_delete"),

    # ── Skill management (Super Admin only) ───────────────────────────────────
    path("skills/", SkillListView.as_view(), name="skill_list"),
    path("skills/add/", SkillCreateView.as_view(), name="skill_add"),
    path("skills/<int:pk>/edit/", SkillUpdateView.as_view(), name="skill_edit"),
    path("skills/<int:pk>/delete/", SkillDeleteView.as_view(), name="skill_delete"),
]
