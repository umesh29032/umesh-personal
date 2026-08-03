"""
Allauth adapters — close the auto-signup hole.

Why we override the defaults:
- `SOCIALACCOUNT_AUTO_SIGNUP = True` (allauth default) lets ANY Google account
  create a User on first sign-in. For an internal-team factory ERP that is a
  serious authorisation hole — outside Google users could enter the system.

- This adapter inverts the rule:
    - If the email already belongs to a User → allow + auto-link.
    - Otherwise → refuse with a neutral message. A Super Admin must create the
      account first (via `/app/users/add/`), then the worker can sign in with
      Google using the same email.
"""
from __future__ import annotations

import logging

from allauth.account.adapter import DefaultAccountAdapter
from allauth.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib import messages
from django.shortcuts import redirect

security_logger = logging.getLogger("accounts.security")


class RestrictedAccountAdapter(DefaultAccountAdapter):
    """Hard-disable local email/password signup (S2 fix, 2026-07-12).

    PA-02-OPEN-SIGNUP removed the native /app/ signup routes, but the allauth
    mount still exposed /accounts/signup/ with allauth's default adapter
    (is_open_for_signup=True) — any anonymous visitor could create a live,
    active User. This closes the local half the same way
    RestrictedSocialAccountAdapter closes the social half: pre-provisioned
    users only. Everything else (login, password reset emails) stays default.
    """

    def is_open_for_signup(self, request):
        # allauth CloseableSignupMixin: False ⇒ GET *and* POST render
        # account/signup_closed.html — no form processed, no User created.
        return False


class RestrictedSocialAccountAdapter(DefaultSocialAccountAdapter):
    """Only let pre-provisioned users sign in via a social provider."""

    def pre_social_login(self, request, sociallogin):
        # If the socialaccount is already linked to a local User, allauth will
        # log them in straight away — nothing to do here.
        if sociallogin.is_existing:
            return

        from .models import User
        email = (sociallogin.user.email or "").strip().lower()

        if not email:
            security_logger.warning("social_login_no_email provider=%s",
                                    sociallogin.account.provider)
            messages.error(request, "Google did not provide an email address. Sign in another way.")
            raise ImmediateHttpResponse(redirect("accounts:login"))

        # Existing User → auto-link the social account and let allauth log them in.
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            security_logger.warning("social_login_unprovisioned email=%s provider=%s",
                                    email, sociallogin.account.provider)
            messages.error(
                request,
                "No account is provisioned for this Google address. "
                "Ask a Super Admin to create one for you.",
            )
            raise ImmediateHttpResponse(redirect("accounts:login"))

        sociallogin.connect(request, user)
        security_logger.info("social_login_linked email=%s provider=%s",
                             email, sociallogin.account.provider)

    def is_open_for_signup(self, request, sociallogin):
        """Hard-disable socialaccount-driven signup."""
        return False
