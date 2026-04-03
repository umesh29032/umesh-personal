import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.core import signing
from django.db.models import Q
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views import View
from django.views.generic import CreateView, DeleteView, FormView, ListView, UpdateView

from .forms import SignupForm, SkillForm, UserEditForm
from .models import Skill, User
from .utils import (
    OTP_RESEND_COOLDOWN,
    can_resend_otp,
    check_otp_from_session,
    clear_otp_session,
    generate_otp,
    send_otp_email,
    store_otp_in_session,
)

logger = logging.getLogger(__name__)


# ─── Authentication ────────────────────────────────────────────────────────────

class LoginView(View):
    """
    Step 1: User enters email → OTP is generated and emailed.
    Only sends OTP to existing users to prevent account enumeration.
    """

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("accounts:home")
        return render(request, "accounts/login.html")

    def post(self, request):
        email = request.POST.get("email", "").strip().lower()

        if not email:
            messages.error(request, "Please enter a valid email address.")
            return render(request, "accounts/login.html")

        if not can_resend_otp(request, prefix="otp"):
            return redirect("accounts:verify_otp")

        user, _ = User.objects.get_or_create(email=email)

        otp = generate_otp()
        store_otp_in_session(request, otp, prefix="otp")
        request.session["otp_email"] = email
        request.session.modified = True

        try:
            send_otp_email(email, otp, subject=f"Your Login OTP — {settings.SITE_NAME}")
        except Exception:
            logger.exception("Failed to send login OTP email to %s", email)
            messages.error(request, "Failed to send OTP. Please try again.")
            return render(request, "accounts/login.html")

        return redirect("accounts:verify_otp")


class ResendOTPView(View):
    """Resend login OTP after cooldown expires."""

    def get(self, request):
        email = request.session.get("otp_email")
        if not email:
            return redirect("accounts:login")

        if not can_resend_otp(request, prefix="otp"):
            messages.warning(request, f"Please wait {OTP_RESEND_COOLDOWN} seconds before resending.")
            return redirect("accounts:verify_otp")

        otp = generate_otp()
        store_otp_in_session(request, otp, prefix="otp")
        request.session.modified = True

        try:
            send_otp_email(email, otp, subject=f"Your New Login OTP — {settings.SITE_NAME}")
        except Exception:
            logger.exception("Failed to resend login OTP email to %s", email)
            messages.error(request, "Failed to resend OTP. Please try again.")

        return redirect("accounts:verify_otp")


class VerifyOTPView(View):
    """Step 2: User enters the 6-digit OTP to complete login."""

    def get(self, request):
        if not request.session.get("otp_email"):
            return redirect("accounts:login")
        return render(request, "accounts/otp.html", {"email": request.session.get("otp_email")})

    def post(self, request):
        entered_otp = request.POST.get("otp", "").strip()
        email = request.session.get("otp_email")

        if not email:
            messages.error(request, "Session expired. Please login again.")
            return redirect("accounts:login")

        is_valid, error_msg = check_otp_from_session(request, entered_otp, prefix="otp")

        if not is_valid:
            messages.error(request, error_msg)
            if "expired" in error_msg or "Too many" in error_msg:
                clear_otp_session(request, prefix="otp")
                request.session.pop("otp_email", None)
                request.session.modified = True
                return redirect("accounts:login")
            return redirect("accounts:verify_otp")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, "Account not found. Please sign up.")
            return redirect("accounts:signup")

        login(request, user, backend="django.contrib.auth.backends.ModelBackend")

        clear_otp_session(request, prefix="otp")
        request.session.pop("otp_email", None)
        request.session.modified = True

        return redirect("accounts:home")


@method_decorator(never_cache, name="dispatch")
class LogoutView(View):
    def get(self, request):
        logout(request)
        response = redirect("accounts:login")
        response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response["Pragma"] = "no-cache"
        return response


# ─── Home (protected redirect) ────────────────────────────────────────────────

@method_decorator(login_required(login_url="/"), name="dispatch")
class HomeView(View):
    """Protected entry point — always redirects to the real inventory dashboard."""

    def get(self, request):
        return redirect("inventory:inventory_dashboard")


# ─── User Management ──────────────────────────────────────────────────────────

class SuperuserRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser


class UserListView(LoginRequiredMixin, SuperuserRequiredMixin, ListView):
    model = User
    template_name = "accounts/user_list.html"
    context_object_name = "users"
    paginate_by = 10

    def get_queryset(self):
        qs = super().get_queryset().prefetch_related('skills')
        q = self.request.GET.get("q", "").strip()
        skills = self.request.GET.getlist("skills")

        if q:
            qs = qs.filter(
                Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(email__icontains=q)
            )
        if skills:
            qs = qs.filter(skills__id__in=skills).distinct()
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["skills"] = Skill.objects.all()
        try:
            context["selected_skills"] = [int(x) for x in self.request.GET.getlist("skills")]
        except ValueError:
            context["selected_skills"] = []
        context["search_query"] = self.request.GET.get("q", "")
        return context


class UserUpdateView(LoginRequiredMixin, SuperuserRequiredMixin, UpdateView):
    model = User
    form_class = UserEditForm
    template_name = "accounts/user_form.html"
    success_url = reverse_lazy("accounts:user_list")

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.object == self.request.user and form.cleaned_data.get("new_password"):
            update_session_auth_hash(self.request, self.object)
        messages.success(self.request, "User updated successfully.")
        return response


class UserDeleteView(LoginRequiredMixin, SuperuserRequiredMixin, DeleteView):
    model = User
    template_name = "accounts/user_confirm_delete.html"
    success_url = reverse_lazy("accounts:user_list")

    def form_valid(self, form):
        messages.success(self.request, "User deleted successfully.")
        return super().form_valid(form)


# ─── Password Login ───────────────────────────────────────────────────────────

class PasswordLoginView(DjangoLoginView):
    template_name = "accounts/login_password.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy("accounts:home")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["prefill_email"] = self.request.session.pop("login_prefill_email", "")
        signed_pw = self.request.session.pop("login_prefill_password", "")
        if signed_pw:
            try:
                context["prefill_password"] = signing.loads(signed_pw)
            except signing.BadSignature:
                context["prefill_password"] = ""
        else:
            context["prefill_password"] = ""
        return context

    def form_invalid(self, form):
        messages.error(self.request, "Incorrect email or password. Please try again.")
        return super().form_invalid(form)


# ─── Signup ───────────────────────────────────────────────────────────────────

class SignupView(FormView):
    template_name = "accounts/signup.html"
    form_class = SignupForm
    success_url = reverse_lazy("accounts:signup_verify")

    def form_valid(self, form):
        email = form.cleaned_data["email"]
        # Sign the password before storing in session so it is not stored as plain text.
        # django.core.signing uses the SECRET_KEY — reversible only by the server.
        signed_password = signing.dumps(form.cleaned_data["password"])

        self.request.session["signup_email"] = email
        self.request.session["signup_token"] = signed_password
        self.request.session.modified = True

        otp = generate_otp()
        store_otp_in_session(self.request, otp, prefix="signup")

        try:
            send_otp_email(email, otp, subject=f"Verify your Account — {settings.SITE_NAME}")
        except Exception:
            logger.exception("Failed to send signup OTP email to %s", email)
            messages.error(self.request, "Failed to send verification email. Please try again.")
            return self.form_invalid(form)

        return super().form_valid(form)


class SignupVerifyView(View):
    def get(self, request):
        if not request.session.get("signup_email"):
            return redirect("accounts:signup")
        return render(request, "accounts/signup_otp.html", {"email": request.session.get("signup_email")})

    def post(self, request):
        entered_otp = request.POST.get("otp", "").strip()
        email = request.session.get("signup_email")
        signed_token = request.session.get("signup_token")

        if not email or not signed_token:
            messages.error(request, "Session expired. Please sign up again.")
            return redirect("accounts:signup")

        is_valid, error_msg = check_otp_from_session(request, entered_otp, prefix="signup")

        if not is_valid:
            messages.error(request, error_msg)
            if "expired" in error_msg or "Too many" in error_msg:
                clear_otp_session(request, prefix="signup")
                request.session.pop("signup_email", None)
                request.session.pop("signup_token", None)
                request.session.modified = True
                return redirect("accounts:signup")
            return redirect("accounts:signup_verify")

        try:
            password = signing.loads(signed_token)
        except signing.BadSignature:
            messages.error(request, "Session tampered or expired. Please sign up again.")
            return redirect("accounts:signup")

        user = User.objects.create_user(email=email, password=password)
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")

        clear_otp_session(request, prefix="signup")
        request.session.pop("signup_email", None)
        request.session.pop("signup_token", None)
        request.session.modified = True

        messages.success(request, "Welcome! Your account has been created.")
        return redirect("accounts:home")


class ResendSignupOTPView(View):
    def get(self, request):
        email = request.session.get("signup_email")
        if not email:
            messages.error(request, "Session expired.")
            return redirect("accounts:signup")

        if not can_resend_otp(request, prefix="signup"):
            messages.warning(request, f"Please wait {OTP_RESEND_COOLDOWN} seconds before resending.")
            return redirect("accounts:signup_verify")

        otp = generate_otp()
        store_otp_in_session(request, otp, prefix="signup")
        request.session.modified = True

        try:
            send_otp_email(email, otp, subject=f"Resend: Verify your Account — {settings.SITE_NAME}")
        except Exception:
            logger.exception("Failed to resend signup OTP to %s", email)
            messages.error(request, "Failed to resend OTP.")

        messages.success(request, "OTP resent successfully.")
        return redirect("accounts:signup_verify")


# ─── Password Reset ───────────────────────────────────────────────────────────

class ForgotPasswordView(View):
    def get(self, request):
        return render(request, "accounts/forgot_password.html")

    def post(self, request):
        email = request.POST.get("email", "").strip().lower()

        # Don't reveal whether the email exists (prevents account enumeration)
        if User.objects.filter(email=email).exists():
            otp = generate_otp()
            store_otp_in_session(request, otp, prefix="reset")
            request.session["reset_email"] = email
            request.session.modified = True
            try:
                send_otp_email(email, otp, subject=f"Password Reset OTP — {settings.SITE_NAME}")
            except Exception:
                logger.exception("Failed to send password reset OTP to %s", email)
                messages.error(request, "Failed to send reset email. Please try again.")
                return redirect("accounts:forgot_password")

        # Always show the same message regardless of whether email exists
        messages.info(request, "If this email is registered, an OTP has been sent.")
        return redirect("accounts:reset_password_verify")


class ResetPasswordVerifyView(View):
    def get(self, request):
        return render(request, "accounts/reset_otp.html")

    def post(self, request):
        entered_otp = request.POST.get("otp", "").strip()
        password = request.POST.get("password", "")
        email = request.session.get("reset_email")

        if not email:
            messages.error(request, "Session expired. Please start again.")
            return redirect("accounts:forgot_password")

        is_valid, error_msg = check_otp_from_session(request, entered_otp, prefix="reset")

        if not is_valid:
            messages.error(request, error_msg)
            if "expired" in error_msg or "Too many" in error_msg:
                clear_otp_session(request, prefix="reset")
                request.session.pop("reset_email", None)
                request.session.modified = True
                return redirect("accounts:forgot_password")
            return redirect("accounts:reset_password_verify")

        min_length = getattr(settings, 'PASSWORD_MIN_LENGTH', 8)
        if len(password) < min_length:
            messages.error(request, f"Password must be at least {min_length} characters.")
            return redirect("accounts:reset_password_verify")

        user = User.objects.get(email=email)
        user.set_password(password)
        user.save()

        clear_otp_session(request, prefix="reset")
        request.session.pop("reset_email", None)
        request.session.modified = True

        # Store prefill data so login_password page can pre-populate the fields
        request.session["login_prefill_email"] = email
        request.session["login_prefill_password"] = signing.dumps(password)
        request.session.modified = True

        messages.success(request, "Password reset successfully. Please sign in.")
        return redirect("accounts:login_password")


# ─── Skill Management ─────────────────────────────────────────────────────────

class SkillListView(LoginRequiredMixin, SuperuserRequiredMixin, ListView):
    model = Skill
    template_name = "accounts/skill_list.html"
    context_object_name = "skills"
    ordering = ["name"]


class SkillCreateView(LoginRequiredMixin, SuperuserRequiredMixin, CreateView):
    model = Skill
    form_class = SkillForm
    template_name = "accounts/skill_form.html"
    success_url = reverse_lazy("accounts:skill_list")

    def form_valid(self, form):
        messages.success(self.request, "Skill added.")
        return super().form_valid(form)


class SkillUpdateView(LoginRequiredMixin, SuperuserRequiredMixin, UpdateView):
    model = Skill
    form_class = SkillForm
    template_name = "accounts/skill_form.html"
    success_url = reverse_lazy("accounts:skill_list")

    def form_valid(self, form):
        messages.success(self.request, "Skill updated.")
        return super().form_valid(form)


class SkillDeleteView(LoginRequiredMixin, SuperuserRequiredMixin, DeleteView):
    model = Skill
    template_name = "accounts/skill_confirm_delete.html"
    success_url = reverse_lazy("accounts:skill_list")

    def form_valid(self, form):
        messages.success(self.request, "Skill deleted.")
        return super().form_valid(form)
