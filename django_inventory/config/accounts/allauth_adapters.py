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

from allauth.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib import messages
from django.shortcuts import redirect

security_logger = logging.getLogger("accounts.security")


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
