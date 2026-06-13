"""Auth service — OTP issuance.

YEH FILE KYU HAI?
─────────────────
Har OTP flow (login / signup / password-reset, + unke resends) ka generate→store
→email block SAME tha, ~5 jagah copy-paste. Ab woh ek jagah: `issue_otp()`. Send
policy (OTP gen, session-stash, email, failure-logging) ko change karna ho to ek
hi function badlo.

Jo cheezein flows ke beech GENUINELY alag hain — throttle, anti-enumeration
(user exists?), per-flow session keys (otp_email/signup_email/reset_email), aur
verify logic — woh deliberately views mein hi rehti hain (yahan force-fit nahi).
"""
from __future__ import annotations

import logging

from ..utils import generate_otp, send_otp_email, store_otp_in_session

logger = logging.getLogger(__name__)


def issue_otp(request, *, email: str, prefix: str, subject: str) -> bool:
    """Generate a fresh OTP, stash it in the session under `prefix`, and email it.

    Returns True on success; False if the email send FAILED — the caller decides
    how to surface that (render / redirect / form_invalid), since the failure
    response varies per flow. Marks the session modified.

    Does NOT throttle, check whether the user exists, or set the per-flow session
    email key — those stay in the view (they differ per flow).
    """
    otp = generate_otp()
    store_otp_in_session(request, otp, prefix=prefix)
    request.session.modified = True
    try:
        send_otp_email(email, otp, subject=subject)
        return True
    except Exception:
        logger.exception("Failed to send OTP (prefix=%s) to %s", prefix, email)
        return False
