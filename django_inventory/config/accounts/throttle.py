"""
Lightweight cache-backed throttling for auth endpoints.

Two scopes are tracked in parallel for every sensitive request:
  - by IP address — defends against a single host hammering the endpoint.
  - by identifier (email / username) — defends against credential-stuffing
    that spreads across thousands of IPs but targets the same account.

Counters are stored in Django's default cache. With `LocMemCache` (the test
default) they reset per process; in production swap in Redis so the counter
spans all gunicorn workers. The whole module is intentionally dependency-free
— no `django-ratelimit`, no `django-axes` — so we own the threat model.
"""
from __future__ import annotations

import hashlib
import logging
import time
from typing import Optional

from django.core.cache import cache
from django.http import HttpRequest

logger = logging.getLogger("accounts.security")


# ─── Configuration ────────────────────────────────────────────────────────────

class Limit:
    """One rate-limit policy: N hits per WINDOW seconds, then BLOCK seconds out."""
    __slots__ = ("hits", "window", "block")
    def __init__(self, hits: int, window: int, block: int):
        self.hits = hits
        self.window = window
        self.block = block


# Tuned for an internal-team Django app, not a public consumer site:
#   - "ip" curves are wide because a small office may NAT 30 people behind one IP.
#   - "id" (per-email) curves are tighter — that's the real fraud surface.
LIMITS: dict[str, dict[str, Limit]] = {
    # OTP-send endpoints (LoginView POST, ResendOTPView, ForgotPasswordView)
    "otp_send": {
        "ip": Limit(hits=20, window=600, block=900),    # 20/10min per IP, 15min lock
        "id": Limit(hits=5,  window=600, block=900),    # 5 OTP requests / 10min / email
    },
    # OTP-verify endpoints (VerifyOTPView, SignupVerifyView, ResetPasswordVerifyView)
    "otp_verify": {
        "ip": Limit(hits=30, window=600, block=1800),   # 30 verifications / 10min / IP
        "id": Limit(hits=10, window=600, block=1800),   # 10 verifications / 10min / email
    },
    # Password login (PasswordLoginView POST) — tightest curve
    "pw_login": {
        "ip": Limit(hits=20, window=600, block=1800),
        "id": Limit(hits=5,  window=900, block=1800),   # 5 wrong passwords → 30min lock
    },
    # Signup attempts — protects against email enumeration via signup race
    "signup": {
        "ip": Limit(hits=10, window=600, block=900),
        "id": Limit(hits=3,  window=900, block=900),
    },
}


# ─── Internals ────────────────────────────────────────────────────────────────

def _client_ip(request: HttpRequest) -> str:
    """Pull the originating IP, honouring X-Forwarded-For if a proxy set it."""
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "0.0.0.0")


def _hash(value: str) -> str:
    """Cache keys must be ASCII-safe and bounded; hash the identifier."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def _key(scope: str, axis: str, value: str) -> str:
    return f"throttle:{scope}:{axis}:{_hash(value)}"


def _check_one(scope: str, axis: str, value: str, limit: Limit) -> tuple[bool, int]:
    """
    Increment one counter and decide whether the request must be blocked.

    Returns (blocked, retry_after_seconds).
      blocked=True  → caller MUST refuse the request.
      blocked=False → caller proceeds normally.
    """
    key = _key(scope, axis, value)
    block_key = f"{key}:blocked"

    # If a block-window is active, refuse immediately and surface remaining time.
    blocked_until = cache.get(block_key)
    if blocked_until:
        retry = max(0, int(blocked_until - time.time()))
        if retry > 0:
            return True, retry
        cache.delete(block_key)

    # Sliding-ish window: counter resets when the cache key expires.
    try:
        count = cache.incr(key)
    except ValueError:
        cache.set(key, 1, timeout=limit.window)
        count = 1

    if count > limit.hits:
        cache.set(block_key, time.time() + limit.block, timeout=limit.block)
        logger.warning(
            "throttle.block scope=%s axis=%s key=%s count=%d limit=%d block_s=%d",
            scope, axis, _hash(value), count, limit.hits, limit.block,
        )
        return True, limit.block
    return False, 0


# ─── Public API ───────────────────────────────────────────────────────────────

def check_throttle(
    request: HttpRequest,
    scope: str,
    identifier: Optional[str] = None,
) -> tuple[bool, int]:
    """
    Run the configured per-scope checks for this request.

    `identifier` is typically the email/username being attempted. Pass None
    if the request is not yet bound to a specific account.
    """
    if scope not in LIMITS:
        return False, 0

    ip = _client_ip(request)
    blocked, retry = _check_one(scope, "ip", ip, LIMITS[scope]["ip"])
    if blocked:
        return True, retry

    if identifier:
        ident = (identifier or "").strip().lower()
        if ident:
            blocked, retry = _check_one(scope, "id", ident, LIMITS[scope]["id"])
            if blocked:
                return True, retry
    return False, 0


def reset_throttle(scope: str, identifier: Optional[str] = None, request: Optional[HttpRequest] = None) -> None:
    """
    Clear counters after a successful auth event so legitimate retries
    don't accumulate against a user who eventually got it right.
    """
    if scope not in LIMITS:
        return
    if request is not None:
        ip = _client_ip(request)
        cache.delete_many([_key(scope, "ip", ip), _key(scope, "ip", ip) + ":blocked"])
    if identifier:
        ident = (identifier or "").strip().lower()
        if ident:
            cache.delete_many([_key(scope, "id", ident), _key(scope, "id", ident) + ":blocked"])


def format_retry(seconds: int) -> str:
    """Human-readable retry-after for flash messages."""
    if seconds >= 60:
        return f"{seconds // 60} minute{'s' if seconds // 60 != 1 else ''}"
    return f"{seconds} seconds"
