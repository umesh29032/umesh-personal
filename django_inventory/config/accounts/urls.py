from django.urls import path
from .views import LoginView, VerifyOTPView, HomeView, LogoutView,ResendOTPView

app_name = "accounts"

urlpatterns = [
    path("", LoginView.as_view(), name="login"),
    path("verify-otp/", VerifyOTPView.as_view(), name="verify_otp"),
    path("home/", HomeView.as_view(), name="home"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("resend-otp/", ResendOTPView.as_view(), name="resend_otp"),


]
