"""
URL configuration for the accounts app.

All paths are mounted under /app/ by the root URLconf (config/urls.py).
Use {% url 'accounts:<name>' %} in templates or reverse('accounts:<name>') in Python.

Auth flow:
  /app/            → OTP login step 1 (email entry)
  /app/verify-otp/ → OTP login step 2 (code entry)
  /app/login/password/ → alternative password login

Self-registration: DISABLED (Production Audit PA-02-OPEN-SIGNUP, owner decision
2026-06-14). This is an internal ERP — "pre-provisioned users only". Accounts are
created by a Super Admin (/app/users/add/) or by linking a pre-provisioned Google
address. The SignupView/SignupVerifyView/ResendSignupOTPView classes remain in
views.py (unrouted) so signup can be re-enabled deliberately if invite/allowlist
onboarding is ever scoped — just restore the three routes + imports below.

Password reset flow:
  /app/forgot-password/        → email entry
  /app/reset-password/verify/  → OTP + new password in one step
"""
from django.urls import path
from .views import (
    LoginView, VerifyOTPView, HomeView, LogoutView, ResendOTPView,
    UserListView, UserCreateView, UserUpdateView, UserDeleteView, PasswordLoginView,
    ForgotPasswordView, ResetPasswordVerifyView,
    SkillListView, SkillCreateView, SkillUpdateView, SkillDeleteView,
    UserTypeListView, UserTypeCreateView, UserTypeUpdateView, UserTypeDeleteView,
)
# SignupView, SignupVerifyView, ResendSignupOTPView intentionally NOT imported —
# native self-signup is disabled (PA-02-OPEN-SIGNUP). Classes still live in views.py.

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

    # ── Self-registration: DISABLED (PA-02-OPEN-SIGNUP, owner decision 2026-06-14) ──
    # Internal ERP = pre-provisioned users only. To re-enable, restore the three
    # signup routes + their imports above. Views remain in views.py (unrouted).

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

    # ── User Type management (Super Admin only) ───────────────────────────────
    path("user-types/", UserTypeListView.as_view(), name="usertype_list"),
    path("user-types/add/", UserTypeCreateView.as_view(), name="usertype_add"),
    path("user-types/<int:pk>/edit/", UserTypeUpdateView.as_view(), name="usertype_edit"),
    path("user-types/<int:pk>/delete/", UserTypeDeleteView.as_view(), name="usertype_delete"),
]
