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

from .base import *  # base.py ki saari settings le lo — tab overrides karo

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
