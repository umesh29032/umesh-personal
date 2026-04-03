"""
OTP Utilities — Secure generation, hashing, and verification.

Design decisions:
- secrets.randbelow() instead of random.randint() — cryptographically secure RNG
- SHA-256 hashing before session storage — plain OTP never persisted
- hmac.compare_digest() for verification — prevents timing-side-channel attacks
- Max attempt tracking per OTP — stops brute-force of 6-digit codes
"""

import hashlib
import hmac
import secrets
import time

from django.conf import settings
from django.core.mail import send_mail


# ─── Constants ───────────────────────────────────────────────────────────────
OTP_EXPIRY_SECONDS = 300        # 5 minutes
OTP_RESEND_COOLDOWN = 60        # 1 minute between resends
OTP_MAX_ATTEMPTS = 3            # Lock after 3 wrong guesses


# ─── Core OTP functions ───────────────────────────────────────────────────────

def generate_otp() -> str:
    """Return a random 6-digit OTP using the OS CSPRNG."""
    return str(secrets.randbelow(900_000) + 100_000)  # 100000–999999


def hash_otp(otp: str) -> str:
    """SHA-256 hash of the OTP — store this, not the raw OTP."""
    return hashlib.sha256(otp.encode("utf-8")).hexdigest()


def verify_otp(entered: str, stored_hash: str) -> bool:
    """
    Constant-time comparison to prevent timing attacks.
    Returns True only when the entered OTP matches the stored hash.
    """
    return hmac.compare_digest(hash_otp(entered), stored_hash)


# ─── Session helpers ──────────────────────────────────────────────────────────

def store_otp_in_session(request, otp: str, prefix: str = "otp") -> None:
    """
    Hash the OTP and persist timing metadata in the session.
    prefix differentiates login / signup / reset OTP namespaces.
    """
    now = int(time.time())
    request.session[f"{prefix}_hash"] = hash_otp(otp)
    request.session[f"{prefix}_created_at"] = now
    request.session[f"{prefix}_last_sent_at"] = now
    request.session[f"{prefix}_attempts"] = 0


def check_otp_from_session(request, entered: str, prefix: str = "otp") -> tuple[bool, str]:
    """
    Validate an OTP from session. Returns (is_valid, error_message).

    Checks in order:
    1. Session data exists
    2. OTP not expired (OTP_EXPIRY_SECONDS)
    3. Attempt count not exceeded (OTP_MAX_ATTEMPTS)
    4. OTP matches
    """
    stored_hash = request.session.get(f"{prefix}_hash")
    created_at = request.session.get(f"{prefix}_created_at")
    attempts = request.session.get(f"{prefix}_attempts", 0)

    if not stored_hash or not created_at:
        return False, "Session expired. Please request a new OTP."

    elapsed = int(time.time()) - created_at
    if elapsed > OTP_EXPIRY_SECONDS:
        clear_otp_session(request, prefix)
        return False, f"OTP expired (valid for {OTP_EXPIRY_SECONDS // 60} minutes). Please request a new one."

    if attempts >= OTP_MAX_ATTEMPTS:
        clear_otp_session(request, prefix)
        return False, "Too many incorrect attempts. Please request a new OTP."

    if not verify_otp(entered, stored_hash):
        request.session[f"{prefix}_attempts"] = attempts + 1
        remaining = OTP_MAX_ATTEMPTS - attempts - 1
        return False, f"Invalid OTP. {remaining} attempt{'s' if remaining != 1 else ''} remaining."

    return True, ""


def can_resend_otp(request, prefix: str = "otp") -> bool:
    """Return True if cooldown has passed and a resend is allowed."""
    last_sent = request.session.get(f"{prefix}_last_sent_at")
    if not last_sent:
        return True
    return int(time.time()) - last_sent >= OTP_RESEND_COOLDOWN


def clear_otp_session(request, prefix: str = "otp") -> None:
    """Remove all OTP-related keys for the given prefix from the session."""
    for key in (f"{prefix}_hash", f"{prefix}_created_at",
                f"{prefix}_last_sent_at", f"{prefix}_attempts"):
        request.session.pop(key, None)


# ─── Email helpers ────────────────────────────────────────────────────────────

def send_otp_email(recipient_email: str, otp: str, subject: str = "Your Login OTP") -> None:
    """Send a formatted OTP email. Raises on SMTP failure."""
    site_name = getattr(settings, 'SITE_NAME', 'Inventory System')
    message = (
        f"Hello,\n\n"
        f"Your one-time password (OTP) is:\n\n"
        f"    {otp}\n\n"
        f"This OTP is valid for {OTP_EXPIRY_SECONDS // 60} minutes. "
        f"Do not share it with anyone.\n\n"
        f"If you did not request this, please ignore this email.\n\n"
        f"— {site_name}"
    )
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[recipient_email],
        fail_silently=False,
    )
