"""
Local development settings.
Use: DJANGO_SETTINGS_MODULE=config.settings.local

YEH FILE KYU HAI?
─────────────────
Yeh file sirf apne laptop pe development karte waqt use hoti hai.
base.py ki sab settings import karta hai, phir kuch development-friendly
overrides karta hai (jaise DEBUG=True).
manage.py mein DEFAULT hai yeh file — isliye `python manage.py runserver`
automatically yahi use karta hai bina kuch aur bataye.
"""

from .base import *  # noqa: F403 — settings-module convention; base.py ki saari settings le lo

# DEBUG=True hone pe:
# - Error page mein full traceback + local variables dikhte hain
# - Static files auto-serve hoti hain bina collectstatic ke
# KABHI bhi production mein True mat karo — attacker ko pure code ka structure dikh jaata hai
DEBUG = True

# Email backend comes from .env (SMTP with Gmail app password).
# If you don't have credentials set up yet, uncomment the line below
# to print emails to the terminal instead of sending them:
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# ACCOUNT_EMAIL_VERIFICATION="none": locally email verify nahi karna padta signup ke baad
# Warna har baar test karte waqt Gmail inbox check karna padta — slow development
ACCOUNT_EMAIL_VERIFICATION = "none"

# ALLOWED_HOSTS=['*']: locally koi bhi domain/IP se access kar sakte ho
# '*' matlab wildcard — production mein yeh dangerous hai (Host header attack)
# local.py mein safe hai kyunki yeh server internet pe nahi hai
ALLOWED_HOSTS = ['*']

# P19A H-3 fix (2026-07-20): CONN_MAX_AGE=0 DEV-ONLY. runserver spawns a thread
# per request and never returns persistent connections — with base.py's 600s
# keep-alive the leaked connections pile up until Postgres max_connections=100
# saturates and random pages 500 with "FATAL: sorry, too many clients already".
# Production (3 SYNC gunicorn workers) keeps base.py's 600 — bounded at 3 conns.
DATABASES['default']['CONN_MAX_AGE'] = 0  # noqa: F405 — DATABASES comes from base via star-import

# devseed: dev-only seeder engine (Campaign Phase 12, SEED-D1 2026-07-17).
# INSTALLED_APPS += : app registry mein SIRF local settings ke through add hota
# hai — production settings mein yeh app EXIST hi nahi karta (structural guard
# factor 5: commands are undiscoverable outside dev). base.py kabhi mat chhedo.
INSTALLED_APPS += ["devseed"]  # noqa: F405 — INSTALLED_APPS comes from base via star-import
