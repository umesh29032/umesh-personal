from django.urls import path
from .views import (
    LoginView, VerifyOTPView, HomeView, LogoutView, ResendOTPView, 
    UserListView, UserUpdateView, UserDeleteView, PasswordLoginView,
    SignupView, SignupVerifyView, ForgotPasswordView, ResetPasswordVerifyView, ResendSignupOTPView,
    SkillListView, SkillCreateView, SkillUpdateView, SkillDeleteView
)

app_name = "accounts"

urlpatterns = [
    path("", LoginView.as_view(), name="login"),
    path("verify-otp/", VerifyOTPView.as_view(), name="verify_otp"),
    path("home/", HomeView.as_view(), name="home"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("resend-otp/", ResendOTPView.as_view(), name="resend_otp"),



    path("skills/", SkillListView.as_view(), name="skill_list"),
    path("skills/add/", SkillCreateView.as_view(), name="skill_add"),
    path("skills/<int:pk>/edit/", SkillUpdateView.as_view(), name="skill_edit"),
    path("skills/<int:pk>/delete/", SkillDeleteView.as_view(), name="skill_delete"),

    path("users/", UserListView.as_view(), name="user_list"),
    path("users/<int:pk>/edit/", UserUpdateView.as_view(), name="user_edit"),
    path("users/<int:pk>/delete/", UserDeleteView.as_view(), name="user_delete"),
    path("login/password/", PasswordLoginView.as_view(), name="login_password"),
    
    path("signup/", SignupView.as_view(), name="signup"),
    path("signup/verify/", SignupVerifyView.as_view(), name="signup_verify"),
    path("signup/resend-otp/", ResendSignupOTPView.as_view(), name="signup_resend_otp"),
    
    path("forgot-password/", ForgotPasswordView.as_view(), name="forgot_password"),
    path("reset-password/verify/", ResetPasswordVerifyView.as_view(), name="reset_password_verify"),
]
