"""
Accounts views — all authentication and user-management endpoints.

Section map:
  Authentication  — LoginView, ResendOTPView, VerifyOTPView, LogoutView
  Home            — HomeView (protected redirect to inventory)
  User management — UserListView, UserCreateView, UserUpdateView, UserDeleteView
  Password login  — PasswordLoginView (extends Django's AuthenticationView)
  Signup          — SignupView, SignupVerifyView, ResendSignupOTPView
  Password reset  — ForgotPasswordView, ResetPasswordVerifyView
  Skill management — SkillListView, SkillCreateView, SkillUpdateView, SkillDeleteView

Every POST endpoint that is an auth action calls check_throttle() near the top
and reset_throttle() on success. See throttle.py for the rate-limit policies.

FILE MAP:
  L53   Authentication  — OTP login (LoginView/Resend/Verify), Logout
  L201  Home redirect
  L211  User management — Super-Admin CRUD (list/create/update/delete)
  L338  Password login  — rate-limited DjangoLoginView subclass
  L377  Signup          — pre-provisioned-only OTP signup + verify
  L506  Password reset  — OTP-based reset flow

RESPONSIBILITY: auth flows + user admin ONLY. Every endpoint is rate-limited
(cache, per IP+email — see services). DELEGATES TO: accounts services (user
writes moved out of views in the 2026-06 remediation; no signals).
INVARIANTS: pre-provisioned users only (no open signup); self-lockout
protection on the rate limiter; permission checks via permission_service.
MUST NOT BE ADDED HERE: domain views (dashboards live in inventory),
role/sidebar editors (inventory/views), any direct domain-model writes.
"""
import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.core import signing
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views import View
from django.views.generic import CreateView, DeleteView, FormView, ListView, UpdateView

from .forms import SignupForm, SkillForm, UserCreateForm, UserEditForm, UserTypeForm
from .models import Skill, User, UserType
from .services import auth_service, user_service
from .throttle import check_throttle, reset_throttle, format_retry
# Centralised RBAC helper — replaces raw `is_superuser` checks (CLAUDE.md rule #6).
from accounts.services.permission_service import (
    user_has_role, ROLE_SUPER_ADMIN, MANAGEMENT_ROLES,
)

security_logger = logging.getLogger("accounts.security")
from .utils import (
    OTP_RESEND_COOLDOWN,
    can_resend_otp,
    check_otp_from_session,
    clear_otp_session,
    generate_otp,
    store_otp_in_session,
)

logger = logging.getLogger(__name__)


# ─── Authentication ────────────────────────────────────────────────────────────

@method_decorator(never_cache, name="dispatch")
class LoginView(View):
    """
    Step 1: User enters email → OTP is generated and emailed.
    Only sends OTP to existing users to prevent account enumeration.
    never_cache: keep auth pages out of the bfcache so the back button after
    logout can't redisplay a stale OTP/login screen (PA-02-3).
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

        blocked, retry = check_throttle(request, "otp_send", identifier=email)
        if blocked:
            security_logger.warning("login_throttled email=%s retry=%ss", email, retry)
            messages.error(request, f"Too many requests. Try again in {format_retry(retry)}.")
            return render(request, "accounts/login.html")

        if not can_resend_otp(request, prefix="otp"):
            return redirect("accounts:verify_otp")

        # Anti-enumeration: the OTP page must look identical whether or not the
        # email exists. Real accounts get a REAL OTP emailed; unknown emails get
        # a DECOY OTP stashed in-session (never emailed) so the verify step ALSO
        # behaves identically — a wrong code returns "Invalid OTP" either way,
        # instead of leaking existence via a different message/redirect.
        # email__iexact (not exact) so a mixed-case-local account isn't missed.
        request.session["otp_email"] = email
        if User.objects.filter(email__iexact=email).exists():
            if not auth_service.issue_otp(
                request, email=email, prefix="otp",
                subject=f"Your Login OTP — {settings.SITE_NAME}",
            ):
                messages.error(request, "Failed to send OTP. Please try again.")
                return render(request, "accounts/login.html")
        else:
            # Decoy: random un-emailed OTP hash so a non-existent account is
            # indistinguishable from a real one on the verify page.
            store_otp_in_session(request, generate_otp(), prefix="otp")
            request.session.modified = True

        return redirect("accounts:verify_otp")


class ResendOTPView(View):
    """Resend login OTP after cooldown expires."""

    def get(self, request):
        email = request.session.get("otp_email")
        if not email:
            return redirect("accounts:login")

        blocked, retry = check_throttle(request, "otp_send", identifier=email)
        if blocked:
            security_logger.warning("resend_throttled email=%s retry=%ss", email, retry)
            messages.error(request, f"Too many requests. Try again in {format_retry(retry)}.")
            return redirect("accounts:verify_otp")

        if not can_resend_otp(request, prefix="otp"):
            messages.warning(request, f"Please wait {OTP_RESEND_COOLDOWN} seconds before resending.")
            return redirect("accounts:verify_otp")

        # Only send OTP if the user actually exists — mirrors LoginView logic.
        # For non-existent emails we still redirect to the OTP page (anti-enumeration).
        if User.objects.filter(email__iexact=email).exists():
            if not auth_service.issue_otp(
                request, email=email, prefix="otp",
                subject=f"Your New Login OTP — {settings.SITE_NAME}",
            ):
                messages.error(request, "Failed to resend OTP. Please try again.")

        return redirect("accounts:verify_otp")


@method_decorator(never_cache, name="dispatch")
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

        blocked, retry = check_throttle(request, "otp_verify", identifier=email)
        if blocked:
            security_logger.warning("verify_throttled email=%s retry=%ss", email, retry)
            messages.error(request, f"Too many attempts. Try again in {format_retry(retry)}.")
            return redirect("accounts:verify_otp")

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
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            # Native signup is disabled (PA-02-OPEN-SIGNUP); accounts are
            # admin-provisioned. With the decoy-OTP anti-enumeration this branch
            # is only reachable by guessing a decoy code — send them back to login
            # with a neutral message rather than a (removed) signup page.
            messages.error(request, "Account not found. Contact your administrator.")
            return redirect("accounts:login")

        login(request, user, backend="django.contrib.auth.backends.ModelBackend")

        # Reward successful auth: zero out the rate-limit counters so a
        # legitimate user who eventually got it right is not punished.
        reset_throttle("otp_send", identifier=email, request=request)
        reset_throttle("otp_verify", identifier=email, request=request)
        security_logger.info("login_success email=%s", email)

        clear_otp_session(request, prefix="otp")
        request.session.pop("otp_email", None)
        request.session.modified = True

        return redirect("accounts:home")


@method_decorator(never_cache, name="dispatch")
class LogoutView(View):
    """POST-only logout to prevent CSRF logout attacks via malicious links."""

    def post(self, request):
        logout(request)
        response = redirect("accounts:login")
        response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response["Pragma"] = "no-cache"
        return response

    def get(self, request):
        # Redirect GET requests to home — logout must be POST with CSRF token
        return redirect("accounts:home")


# ─── Home (protected redirect) ────────────────────────────────────────────────

@method_decorator(login_required(login_url="/app/"), name="dispatch")
class HomeView(View):
    """Protected entry point — ROLE-BASED landing (P1-1): management (super_admin
    / manager) lands on the Operations dashboard; everyone else on their personal
    My Dashboard. Fixes owner-lands-on-empty-worker-view (Phase-C C-1)."""

    def get(self, request):
        if user_has_role(request.user, MANAGEMENT_ROLES):
            return redirect("production:dashboard")
        return redirect("inventory:user_dashboard")


# ─── User Management ──────────────────────────────────────────────────────────

class SuperuserRequiredMixin(UserPassesTestMixin):
    """Gate views to Super Admin role. Uses permission_service, not raw is_superuser."""
    def test_func(self):
        return user_has_role(self.request.user, {ROLE_SUPER_ADMIN})


class UserListView(LoginRequiredMixin, SuperuserRequiredMixin, ListView):
    model = User
    template_name = "accounts/user_list.html"
    context_object_name = "users"
    # No server-side pagination — DataTables handles paging client-side. Server-side
    # paginate_by combined with no ORDER BY caused edited users to "vanish":
    # PostgreSQL MVCC writes an UPDATE as a new tuple version, which can shift
    # the row out of the first-N window after save (issue reported 2026-05-20).

    def get_queryset(self):
        # order_by required — without it, PostgreSQL row order is undefined and
        # changes after UPDATE, making any client-side pagination unstable too.
        qs = (
            super().get_queryset()
            .select_related('role')
            .prefetch_related('skills')
            .order_by('-date_joined', 'email')
        )
        q = self.request.GET.get("q", "").strip()
        skills = self.request.GET.getlist("skills")

        if q:
            qs = qs.filter(
                Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(email__icontains=q)
            )
        if skills:
            # PA-13-4: skills come from the querystring; a non-numeric value
            # (?skills=abc, tampered/stale link) made the integer FK lookup raise
            # ValueError → 500. Keep only numeric ids (mirrors the int()-guard the
            # context builder already applies to selected_skills below).
            skill_ids = [s for s in skills if s.isdigit()]
            if skill_ids:
                qs = qs.filter(skills__id__in=skill_ids).distinct()
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["skills"] = Skill.objects.all()
        try:
            context["selected_skills"] = [int(x) for x in self.request.GET.getlist("skills")]
        except ValueError:
            context["selected_skills"] = []
        context["search_query"] = self.request.GET.get("q", "")
        # KPI counts — full queryset (unfiltered) for accurate totals
        all_users = User.objects.all()
        context["total_count"] = all_users.count()
        context["active_count"] = all_users.filter(is_active=True).count()
        context["inactive_count"] = all_users.filter(is_active=False).count()
        return context


class UserCreateView(LoginRequiredMixin, SuperuserRequiredMixin, CreateView):
    """Super Admin creates a new user and assigns a role at the same time."""
    model = User
    form_class = UserCreateForm
    template_name = "accounts/user_create.html"
    success_url = reverse_lazy("accounts:user_list")

    def form_valid(self, form):
        from django.db import IntegrityError
        try:
            response = super().form_valid(form)
        except IntegrityError:
            # PA-05A-5: clean_email validates with iexact but the DB unique is
            # case-sensitive; a concurrent double-submit can pass validation then
            # collide at INSERT. Surface a field error instead of a 500 (mirrors
            # SignupVerifyView's IntegrityError handling).
            form.add_error("email", "A user with this email already exists.")
            return self.form_invalid(form)
        # Skills saved by ModelForm.save_m2m → retro-tag onto active layerings
        # (explicit; replaces the removed m2m_changed signal).
        user_service.sync_user_skills(self.object)
        messages.success(self.request, f"User {self.object.email} created.")
        return response


class UserUpdateView(LoginRequiredMixin, SuperuserRequiredMixin, UpdateView):
    model = User
    form_class = UserEditForm
    template_name = "accounts/user_form.html"
    success_url = reverse_lazy("accounts:user_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["user_skill_ids"] = list(self.object.skills.values_list("id", flat=True))
        ctx["user_extra_role_ids"] = list(self.object.extra_roles.values_list("id", flat=True))
        return ctx

    def form_valid(self, form):
        editing_self = self.object == self.request.user
        # Self-lockout protection — rule lives in user_service (testable, reused).
        # A Super Admin must not demote/deactivate/role-drop themselves in one
        # request and orphan the system (no remaining admin to fix it).
        if editing_self:
            blockers = user_service.self_edit_blockers(
                self.request.user,
                new_is_superuser=form.cleaned_data.get("is_superuser"),
                new_is_active=form.cleaned_data.get("is_active"),
                new_role=form.cleaned_data.get("role"),
            )
            if blockers:
                messages.error(
                    self.request,
                    "Refused: you cannot " + " or ".join(blockers)
                    + " while editing your own profile. Ask another Super Admin to do it.",
                )
                return self.form_invalid(form)

        response = super().form_valid(form)
        # Skills may have changed → retro-tag (explicit; replaces the signal).
        user_service.sync_user_skills(self.object)
        if editing_self and form.cleaned_data.get("new_password"):
            update_session_auth_hash(self.request, self.object)
        messages.success(self.request, "User updated successfully.")
        return response


class UserDeleteView(LoginRequiredMixin, SuperuserRequiredMixin, DeleteView):
    model = User
    template_name = "accounts/user_confirm_delete.html"
    success_url = reverse_lazy("accounts:user_list")

    def form_valid(self, form):
        # Self-delete + last-admin protection live in user_service.delete_user —
        # race-safe (advisory lock) and enforced on every path, not just here.
        try:
            user_service.delete_user(self.object, actor=self.request.user)
        except ValidationError as e:
            messages.error(self.request, e.messages[0] if e.messages else str(e))
            return redirect("accounts:user_edit", pk=self.object.pk)
        messages.success(self.request, "User deleted successfully.")
        return redirect(self.get_success_url())


# ─── Password Login ───────────────────────────────────────────────────────────

@method_decorator(never_cache, name="dispatch")
class PasswordLoginView(DjangoLoginView):
    template_name = "accounts/login_password.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy("accounts:home")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Only prefill the email (safe) — never prefill the password
        context["prefill_email"] = self.request.session.pop("login_prefill_email", "")
        return context

    def post(self, request, *args, **kwargs):
        # Throttle check happens BEFORE Django's auth so we never hash a
        # password for a blocked source — denial-of-service hardening too.
        email = (request.POST.get("username") or request.POST.get("email") or "").strip().lower()
        blocked, retry = check_throttle(request, "pw_login", identifier=email or None)
        if blocked:
            security_logger.warning("pw_login_throttled email=%s retry=%ss", email, retry)
            messages.error(request, f"Too many failed attempts. Try again in {format_retry(retry)}.")
            return self.render_to_response(self.get_context_data(form=self.get_form()))
        return super().post(request, *args, **kwargs)

    def form_invalid(self, form):
        email = (self.request.POST.get("username") or "").strip().lower()
        security_logger.warning("pw_login_failure email=%s", email)
        messages.error(self.request, "Incorrect email or password. Please try again.")
        return super().form_invalid(form)

    def form_valid(self, form):
        email = (form.cleaned_data.get("username") or "").strip().lower()
        reset_throttle("pw_login", identifier=email, request=self.request)
        security_logger.info("pw_login_success email=%s", email)
        return super().form_valid(form)


# ─── Signup — DISABLED (PA-02-OPEN-SIGNUP, owner decision 2026-06-14) ────────────
# These three views are NO LONGER ROUTED (see accounts/urls.py). Native public
# self-signup contradicted the "pre-provisioned users only" invariant on this
# internal ERP, so the routes + login-page links were removed in the Production
# Audit. The classes are kept (unrouted) for a clean, reversible re-enable if
# invite/allowlist onboarding is ever scoped. Do not re-add routes without that.

@method_decorator(never_cache, name="dispatch")
class SignupView(FormView):
    template_name = "accounts/signup.html"
    form_class = SignupForm
    success_url = reverse_lazy("accounts:signup_verify")

    def form_valid(self, form):
        email = form.cleaned_data["email"]

        blocked, retry = check_throttle(self.request, "signup", identifier=email)
        if blocked:
            security_logger.warning("signup_throttled email=%s retry=%ss", email, retry)
            messages.error(self.request, f"Too many signup attempts. Try again in {format_retry(retry)}.")
            return self.form_invalid(form)

        # Sign the password before storing in session so it is not stored as plain text.
        # django.core.signing uses the SECRET_KEY — reversible only by the server.
        signed_password = signing.dumps(form.cleaned_data["password"])

        self.request.session["signup_email"] = email
        self.request.session["signup_token"] = signed_password
        self.request.session.modified = True

        if not auth_service.issue_otp(
            self.request, email=email, prefix="signup",
            subject=f"Verify your Account — {settings.SITE_NAME}",
        ):
            messages.error(self.request, "Failed to send verification email. Please try again.")
            return self.form_invalid(form)

        return super().form_valid(form)


@method_decorator(never_cache, name="dispatch")
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

        blocked, retry = check_throttle(request, "otp_verify", identifier=email)
        if blocked:
            security_logger.warning("signup_verify_throttled email=%s retry=%ss", email, retry)
            messages.error(request, f"Too many attempts. Try again in {format_retry(retry)}.")
            return redirect("accounts:signup_verify")

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

        # Anti-enumeration: clean_email no longer rejects existing addresses, so
        # the race-condition + late-collision case must be handled here. Catch
        # the unique-constraint violation and route the user to login with a
        # neutral message — never reveal "this email is already registered".
        from django.db import IntegrityError
        try:
            user = User.objects.create_user(email=email, password=password)
        except IntegrityError:
            clear_otp_session(request, prefix="signup")
            request.session.pop("signup_email", None)
            request.session.pop("signup_token", None)
            request.session.modified = True
            messages.info(request, "If this email is registered, please sign in.")
            return redirect("accounts:login_password")
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")

        reset_throttle("signup", identifier=email, request=request)
        reset_throttle("otp_verify", identifier=email, request=request)
        security_logger.info("signup_success email=%s", email)

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

        blocked, retry = check_throttle(request, "otp_send", identifier=email)
        if blocked:
            security_logger.warning("signup_resend_throttled email=%s retry=%ss", email, retry)
            messages.error(request, f"Too many requests. Try again in {format_retry(retry)}.")
            return redirect("accounts:signup_verify")

        if not can_resend_otp(request, prefix="signup"):
            messages.warning(request, f"Please wait {OTP_RESEND_COOLDOWN} seconds before resending.")
            return redirect("accounts:signup_verify")

        if not auth_service.issue_otp(
            request, email=email, prefix="signup",
            subject=f"Resend: Verify your Account — {settings.SITE_NAME}",
        ):
            messages.error(request, "Failed to resend OTP.")

        messages.success(request, "OTP resent successfully.")
        return redirect("accounts:signup_verify")


# ─── Password Reset ───────────────────────────────────────────────────────────

@method_decorator(never_cache, name="dispatch")
class ForgotPasswordView(View):
    def get(self, request):
        return render(request, "accounts/forgot_password.html")

    def post(self, request):
        email = request.POST.get("email", "").strip().lower()

        blocked, retry = check_throttle(request, "otp_send", identifier=email)
        if blocked:
            security_logger.warning("forgot_pw_throttled email=%s retry=%ss", email, retry)
            messages.error(request, f"Too many requests. Try again in {format_retry(retry)}.")
            return redirect("accounts:forgot_password")

        # Anti-enumeration: behave identically whether or not the email exists.
        # Real accounts get a REAL reset OTP emailed; unknown emails get a DECOY
        # OTP stashed in-session (never emailed) AND reset_email set, so neither the
        # redirect nor the verify step can distinguish the two. Previously the
        # session key was set only for existing emails, so a non-existent email hit
        # the "Session expired" branch in ResetPasswordVerifyView while a real one
        # reached "Invalid OTP" — a clean enumeration oracle (PA-02-1).
        # email__iexact so a mixed-case-local account isn't missed (PA-02-2).
        request.session["reset_email"] = email
        if User.objects.filter(email__iexact=email).exists():
            if not auth_service.issue_otp(
                request, email=email, prefix="reset",
                subject=f"Password Reset OTP — {settings.SITE_NAME}",
            ):
                messages.error(request, "Failed to send reset email. Please try again.")
                return redirect("accounts:forgot_password")
        else:
            store_otp_in_session(request, generate_otp(), prefix="reset")
        request.session.modified = True

        # Always show the same message regardless of whether email exists
        messages.info(request, "If this email is registered, an OTP has been sent.")
        return redirect("accounts:reset_password_verify")


@method_decorator(never_cache, name="dispatch")
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

        blocked, retry = check_throttle(request, "otp_verify", identifier=email)
        if blocked:
            security_logger.warning("reset_verify_throttled email=%s retry=%ss", email, retry)
            messages.error(request, f"Too many attempts. Try again in {format_retry(retry)}.")
            return redirect("accounts:reset_password_verify")

        is_valid, error_msg = check_otp_from_session(request, entered_otp, prefix="reset")

        if not is_valid:
            messages.error(request, error_msg)
            if "expired" in error_msg or "Too many" in error_msg:
                clear_otp_session(request, prefix="reset")
                request.session.pop("reset_email", None)
                request.session.modified = True
                return redirect("accounts:forgot_password")
            return redirect("accounts:reset_password_verify")

        # Defense in depth — a missing user here means either a tampered session
        # or a decoy-OTP reset for a non-existent email; treat both as bail.
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            request.session.pop("reset_email", None)
            request.session.modified = True
            messages.error(request, "Session expired. Please start again.")
            return redirect("accounts:forgot_password")

        # Run ALL Django password validators (length, common, numeric, similarity)
        try:
            validate_password(password, user=user)
        except ValidationError as e:
            for msg in e.messages:
                messages.error(request, msg)
            return redirect("accounts:reset_password_verify")

        user.set_password(password)
        user.save()

        reset_throttle("otp_send", identifier=email, request=request)
        reset_throttle("otp_verify", identifier=email, request=request)
        reset_throttle("pw_login", identifier=email, request=request)
        security_logger.info("password_reset email=%s", email)

        clear_otp_session(request, prefix="reset")
        request.session.pop("reset_email", None)
        request.session.modified = True

        # Only prefill email (safe) — never store passwords in session
        request.session["login_prefill_email"] = email
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
        # PA-05A-1: Skill→User and Skill→SidebarItemRule are M2M (no FK PROTECT),
        # so a bare delete silently strips the skill from every worker that holds
        # it (losing stage access) and empties any sidebar rule that references it
        # — no warning, no audit. Mirror UserTypeDeleteView: refuse while in use.
        skill = self.get_object()
        blockers = []
        if skill.users.exists():
            blockers.append(f"{skill.users.count()} user(s)")
        if skill.visible_sidebar_items.exists():
            blockers.append(f"{skill.visible_sidebar_items.count()} sidebar rule(s)")
        if blockers:
            messages.error(
                self.request,
                f"Cannot delete '{skill.get_name_display()}' — still used by "
                f"{', '.join(blockers)}. Reassign / update those first.",
            )
            return redirect("accounts:skill_list")
        messages.success(self.request, "Skill deleted.")
        return super().form_valid(form)


# ─── User Type Management ─────────────────────────────────────────────────────
# Super Admin can create/edit/delete User Types from UI — no code changes needed.

class UserTypeListView(LoginRequiredMixin, SuperuserRequiredMixin, ListView):
    model = UserType
    template_name = "accounts/usertype_list.html"
    context_object_name = "user_types"
    ordering = ["label"]


class UserTypeCreateView(LoginRequiredMixin, SuperuserRequiredMixin, CreateView):
    model = UserType
    form_class = UserTypeForm
    template_name = "accounts/usertype_form.html"
    success_url = reverse_lazy("accounts:usertype_list")

    def form_valid(self, form):
        messages.success(self.request, f"User type '{form.instance.label}' created.")
        return super().form_valid(form)


class UserTypeUpdateView(LoginRequiredMixin, SuperuserRequiredMixin, UpdateView):
    model = UserType
    form_class = UserTypeForm
    template_name = "accounts/usertype_form.html"
    success_url = reverse_lazy("accounts:usertype_list")

    def form_valid(self, form):
        messages.success(self.request, f"User type '{form.instance.label}' updated.")
        return super().form_valid(form)


class UserTypeDeleteView(LoginRequiredMixin, SuperuserRequiredMixin, DeleteView):
    model = UserType
    template_name = "accounts/usertype_confirm_delete.html"
    success_url = reverse_lazy("accounts:usertype_list")

    def form_valid(self, form):
        # Block delete if users are assigned to this type
        if self.get_object().users.exists():
            messages.error(self.request, "Cannot delete — users are assigned to this type. Reassign first.")
            return redirect("accounts:usertype_list")
        messages.success(self.request, "User type deleted.")
        return super().form_valid(form)
