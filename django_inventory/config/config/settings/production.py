"""
Production settings.
Use: DJANGO_SETTINGS_MODULE=config.settings.production

YEH FILE KYU HAI?
─────────────────
Yeh file tab use hoti hai jab app live server pe deploy hota hai (internet pe).
base.py ki sab settings import karta hai + security hardening add karta hai.
Server pe environment variable set karo: DJANGO_SETTINGS_MODULE=config.settings.production
Tab Django automatic yahi file padhega, local.py nahi.
"""

from .base import *    # noqa: F403 — settings-module convention (scorecard: benign)
from decouple import config  # .env se values padhne ke liye

# DEBUG=False production mein MUST hai:
# - Error page mein sirf "Server Error 500" dikhega — attacker ko kuch nahi milega
# - Django kuch internal checks bhi tighten karta hai
DEBUG = False

# Production mein real SMTP email bhejta hai (local.py mein bhi yahi tha, but explicitly set karo)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# Production mein email verify karna "optional" hai — user verify kar bhi sakta hai, nahi bhi
# "mandatory" karo toh bina verify ke login nahi hoga
ACCOUNT_EMAIL_VERIFICATION = "optional"

# ─── Security Hardening ───────────────────────────────────────────────────────
# Yeh settings production server ke liye zaroori hain — locally zarurat nahi

# SECURE_SSL_REDIRECT: HTTP request aaye toh automatically HTTPS pe redirect karo
# Bina iske data plain text mein travel karta hai — koi bhi sniff kar sakta hai
SECURE_SSL_REDIRECT = True

# SESSION_COOKIE_SECURE: session cookie sirf HTTPS connection pe hi bhejega browser
# HTTP pe nahi — cookie ka interception impossible ho jaata hai
SESSION_COOKIE_SECURE = True

# CSRF_COOKIE_SECURE: CSRF token cookie bhi sirf HTTPS pe — same reason
CSRF_COOKIE_SECURE = True

# SECURE_CONTENT_TYPE_NOSNIFF: browser ko force karo declared Content-Type maano
# "MIME sniffing attack" rokta hai — browser khud se file type guess nahi karta
SECURE_CONTENT_TYPE_NOSNIFF = True

# X_FRAME_OPTIONS='DENY': yeh site kisi bhi iframe mein load nahi hogi
# "Clickjacking attack" rokta hai — jahan attacker tumhari site invisible iframe mein dikhata hai
X_FRAME_OPTIONS = 'DENY'

# HSTS (HTTP Strict Transport Security): browser ko batao "agli baar seedha HTTPS use karo"
# SECURE_HSTS_SECONDS=31536000: 1 saal tak browser HTTP try hi nahi karega
# INCLUDE_SUBDOMAINS: subdomains pe bhi apply hoga (api.domain.com etc.)
# PRELOAD: browser ki built-in HSTS list mein add hona — pehli request bhi HTTPS
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# In production, SECRET_KEY must be set via environment variable — no insecure default
# config() bina default ke — agar .env mein nahi hai toh crash karo (intentional safety check)
SECRET_KEY = config('SECRET_KEY')

# ─── PD deploy-blocker bundle (2026-06-11) ────────────────────────────────────

# Behind exactly ONE TLS-terminating reverse proxy, trust its forwarded-proto
# header — without this, SECURE_SSL_REDIRECT loops forever behind the proxy.
# NEVER expose gunicorn directly to the internet with this set (header spoofing
# would fake HTTPS).
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Shared cache — REQUIRED in production: the auth rate limiter stores its
# counters in the default cache; per-process LocMem would silently weaken it
# N× under multi-worker gunicorn. Fail-fast if REDIS_URL is unset (same
# policy as SECRET_KEY).
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': config('REDIS_URL'),
    },
}

# Logs → stdout. RotatingFileHandler (base.py) is multi-process unsafe and
# assumes a writable local logs/ dir; in production the platform collects
# stdout. Same request-id format, same logger names, security included.
LOGGING['handlers']['file'] = {  # noqa: F405 — LOGGING comes from base via star-import
    'class': 'logging.StreamHandler',
    'formatter': 'verbose',
    'filters': ['request_id'],
}
LOGGING['handlers']['security_file'] = {  # noqa: F405 — same
    'class': 'logging.StreamHandler',
    'formatter': 'security',
}

# Django rejects HTTPS POSTs whose Origin isn't trusted — required behind the
# TLS proxy (deploy direction C). Comma-separated, scheme-included.
CSRF_TRUSTED_ORIGINS = [
    o.strip() for o in config('CSRF_TRUSTED_ORIGINS').split(',') if o.strip()
]
