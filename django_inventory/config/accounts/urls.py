from django.urls import path
from .views import (
    LoginView, VerifyOTPView, HomeView, LogoutView, ResendOTPView, 
    UserListView, UserUpdateView, UserDeleteView, PasswordLoginView,
    SignupView, SignupVerifyView, ForgotPasswordView, ResetPasswordVerifyView, ResendSignupOTPView
)

app_name = "accounts"

urlpatterns = [
    path("", LoginView.as_view(), name="login"),
    path("verify-otp/", VerifyOTPView.as_view(), name="verify_otp"),
    path("home/", HomeView.as_view(), name="home"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("resend-otp/", ResendOTPView.as_view(), name="resend_otp"),



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
