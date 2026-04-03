"""
Production settings.
Use: DJANGO_SETTINGS_MODULE=config.settings.production
"""

from .base import *
from decouple import config

DEBUG = False

# SMTP email in production
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# Email verification enabled in production
ACCOUNT_EMAIL_VERIFICATION = "optional"

# Security hardening
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# In production, SECRET_KEY must be set via environment variable — no insecure default
SECRET_KEY = config('SECRET_KEY')
