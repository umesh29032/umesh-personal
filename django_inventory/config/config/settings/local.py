"""
Local development settings.
Use: DJANGO_SETTINGS_MODULE=config.settings.local
"""

from .base import *

DEBUG = True

# Email backend comes from .env (SMTP with Gmail app password).
# If you don't have credentials set up yet, uncomment the line below
# to print emails to the terminal instead of sending them:
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# No allauth email verification required locally
ACCOUNT_EMAIL_VERIFICATION = "none"

# Allow all hosts in development
ALLOWED_HOSTS = ['*']
