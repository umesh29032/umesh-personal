import random
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth import login
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.utils.decorators import method_decorator
from django.conf import settings
from django.contrib import messages
import time
from accounts.decorators import login_required_view
from .models import User



class LoginView(View):
    """
    Login with Email + OTP
    """

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("accounts:home")
        return render(request, "accounts/login.html")

    def post(self, request):
        email = request.POST.get("email")

        # 1️⃣ Create user if not exists
        user, created = User.objects.get_or_create(email=email)

        current_time = int(time.time())

        # check resend cooldown (60 sec)
        last_sent = request.session.get("otp_last_sent_at")

        if last_sent and current_time - last_sent < 60:
            return redirect("accounts:verify_otp")

        otp = random.randint(100000, 999999)

        request.session["otp"] = str(otp)
        request.session["email"] = email
        request.session["otp_created_at"] = current_time
        request.session["otp_last_sent_at"] = current_time



        # 4️⃣ Send OTP via Gmail SMTP
        send_mail(
            subject="Your Login OTP",
            message=f"""
                    Hello,
                    Your OTP for login is: {otp}

                    This OTP is valid for a short time.
                    If you did not request this, ignore this email.

                    Thanks,
                    Inventory App
                    """,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[email],
            fail_silently=False,
        )

        # 5️⃣ Redirect to OTP page
        return redirect("accounts:verify_otp")

class ResendOTPView(View):
    """
    Resend OTP after 60 seconds cooldown
    """

    def get(self, request):
        email = request.session.get("email")

        if not email:
            return redirect("accounts:login")

        current_time = int(time.time())
        last_sent = request.session.get("otp_last_sent_at")

        # block resend if within 60 seconds
        if last_sent and current_time - last_sent < 60:
            return redirect("accounts:verify_otp")

        # generate new OTP
        otp = random.randint(100000, 999999)

        request.session["otp"] = str(otp)
        request.session["otp_created_at"] = current_time
        request.session["otp_last_sent_at"] = current_time

        send_mail(
            subject="Your Login OTP (Resent)",
            message=f"Your new OTP is: {otp}",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[email],
            fail_silently=False,
        )

        return redirect("accounts:verify_otp")


class VerifyOTPView(View):

    def get(self, request):
        return render(request, "accounts/otp.html")

    def post(self, request):
        entered_otp = request.POST.get("otp")
        saved_otp = request.session.get("otp")
        otp_time = request.session.get("otp_created_at")
        email = request.session.get("email")

        # 🔒 1️⃣ Validate session data
        if not saved_otp or not otp_time or not email:
            messages.error(request, "Session expired. Please login again.")
            return redirect("accounts:login")


        # OTP valid for 1 minutes (60 seconds)
        if int(time.time()) - otp_time > 60:
            self._clear_otp_session(request)
            messages.error(request, "OTP expired. Please request a new one.")
            return redirect("accounts:login")
        # OTP mismatch
        if entered_otp != saved_otp:
            messages.error(request, "Invalid OTP. Please try again.")
            return redirect("accounts:verify_otp")
        # otp valid ---> login
        user = User.objects.get(email=email)

        login(request,
        user,
        backend="django.contrib.auth.backends.ModelBackend"
        )

        # Clear OTP after success
        self._clear_otp_session(request)

        return redirect("accounts:home")

    def _clear_otp_session(self, request):
        """Utility method to clear OTP-related session data"""
        request.session.pop("otp", None)
        request.session.pop("otp_created_at", None)
        request.session.pop("otp_last_sent_at", None)
        request.session.pop("email", None)

class LogoutView(View):
    """
    Logout user and clear session
    """

    def get(self, request):
        logout(request)
        return redirect("accounts:login")


@method_decorator(login_required(login_url="/"), name="dispatch")
# @method_decorator(login_required_view, name="dispatch")

class HomeView(View):
    """
    Protected Home Page
    """

    def get(self, request):
        return render(request, "accounts/home.html")
