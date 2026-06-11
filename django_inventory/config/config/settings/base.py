"""
Base Django settings for the Inventory Management System.
Shared by all environments.

YEH FILE KYU HAI?
─────────────────
Teen settings files hain: base.py (yeh) + local.py + production.py
base.py mein woh settings hain jo DONO environments mein same rahti hain.
local.py aur production.py is file ko `from .base import *` se import karke
sirf apni zarurat ki settings override karte hain.
Pattern ka naam hai: "Split Settings" — ek common mistake avoid karta hai jahan
log production mein DEBUG=True chhod dete hain galti se.
"""

from pathlib import Path
from decouple import config, Csv  # python-decouple: .env file se values padhta hai — credentials code mein hard-code nahi hote
import dj_database_url  # production mein single DATABASE_URL string parse karta hai (Neon/Render/Heroku style)

# BASE_DIR: is file se 3 parent folders upar jaata hai → project ka root folder milta hai
# Path(__file__) = yeh .py file ka path
# .resolve() = relative path ko absolute banata hai
# .parent.parent.parent = settings/ → config/ → config/ → project root
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ─── Secret Key ───────────────────────────────────────────────────────────────
# Django SECRET_KEY: cookies, sessions, CSRF tokens sign karne ke liye use hota hai
# Agar yeh leak ho jaye → attacker fake sessions bana sakta hai
# .env se load hota hai; agar missing hai toh runserver crash karta hai (intentionally)
_SECRET_KEY = config('SECRET_KEY', default='')
if not _SECRET_KEY:
    import sys
    # test/migrate commands ke time crash nahi karte — unhe SECRET_KEY ki zarurat nahi
    if 'test' not in sys.argv and 'makemigrations' not in sys.argv and 'migrate' not in sys.argv:
        raise RuntimeError(
            "SECRET_KEY is not set. Add SECRET_KEY=<random-value> to your .env file."
        )
    _SECRET_KEY = 'django-insecure-dev-only-do-not-use-in-production'
SECRET_KEY = _SECRET_KEY

# ─── Site Identity ────────────────────────────────────────────────────────────
# Used in email subjects, footers, and any place the product name appears.
# Change this in .env or override here — never hardcode in individual views.
SITE_NAME = config('SITE_NAME', default='Kapil Enterprises')  # custom setting — views mein {{ SITE_NAME }} se use hota hai

# ALLOWED_HOSTS: sirf yahi domains pe Django request accept karega
# Agar koi aur domain request kare → 400 Bad Request milega
# Security: "HTTP Host Header Attack" se bachata hai
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=Csv())

# ─── Apps ─────────────────────────────────────────────────────────────────────
# INSTALLED_APPS: Django ko batata hai kaun se apps exist karte hain
# Agar koi app yahan na ho → uske models/migrations/templates kaam nahi karenge
INSTALLED_APPS = [
    'django.contrib.admin',          # /admin/ dashboard
    'django.contrib.auth',           # User model, login/logout, permissions
    'django.contrib.contenttypes',   # generic foreign keys ke liye (permissions use karta hai)
    'django.contrib.sessions',       # DB-backed sessions (login state store karta hai)
    'django.contrib.messages',       # ek-baar dikhne wale flash messages (e.g. "Saved!")
    'django.contrib.staticfiles',    # CSS/JS files serve karna

    # REQUIRED for django-allauth
    'django.contrib.sites',          # allauth ko site ka domain pata hona chahiye (SITE_ID = 1)

    # allauth: Google OAuth + email login handle karta hai
    'allauth',
    'allauth.account',               # email/password login
    'allauth.socialaccount',         # social (Google etc.) login base
    'allauth.socialaccount.providers.google',  # specifically Google OAuth

    # local apps — hamara apna code
    'core',           # shared abstract base models (TimeStampedModel, ActiveManager) — no tables
    'accounts',       # custom User model, RBAC roles
    'inventory',      # RBAC roles + dashboards (production lifecycle moved out 2026-05-19)
    'storefront',     # customer-facing pages
    'raw_materials',  # cloth rolls, types, colors, storage locations
    'production',     # products, Adda batches, workflow stages, stage records
    'tracking',       # piece-level barcodes (QR) + per-domain audit history
    'expense',        # worker payroll: allocation, ledger, advances, payments (downstream of production)
]

# AUTHENTICATION_BACKENDS: Django kaise verify karta hai ki user valid hai
# ModelBackend = username/password (Django default)
# AuthenticationBackend = allauth ka Google OAuth
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
)

# SITE_ID: django.contrib.sites ko batata hai hum kaun sa site hain
# Allauth email links mein domain name yahan se aata hai
SITE_ID = 1

# ─── Middleware ───────────────────────────────────────────────────────────────
# MIDDLEWARE: har HTTP request/response se pehle/baad execute hone wali layers
# Order MATTER karta hai — upar se neeche request jaati hai, neeche se upar response aata hai
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',            # HTTPS redirect, security headers
    'core.observability.RequestIDMiddleware',                   # P0.4: bind request id for log correlation (early)
    'whitenoise.middleware.WhiteNoiseMiddleware',               # static files (CSS/JS) directly serve karta hai bina nginx ke
    'django.contrib.sessions.middleware.SessionMiddleware',     # request.session available karta hai
    'django.middleware.common.CommonMiddleware',                # URL trailing slash, ALLOWED_HOSTS check
    'django.middleware.csrf.CsrfViewMiddleware',               # CSRF token check — form submissions pe fake requests rok ta hai
    'django.contrib.auth.middleware.AuthenticationMiddleware',  # request.user available karta hai
    'allauth.account.middleware.AccountMiddleware',             # allauth ka apna processing
    'django.contrib.messages.middleware.MessageMiddleware',     # request.messages (flash messages) available karta hai
    'django.middleware.clickjacking.XFrameOptionsMiddleware',  # X-Frame-Options header — iframes mein load hone se rokta hai
    # URL-level enforcement of the Access-Control panel (SidebarItemRule): hiding
    # a menu item also blocks its URL (not just the sidebar link). After auth +
    # messages so request.user + flash messages are available.
    'inventory.middleware.SidebarAccessMiddleware',
]

# ROOT_URLCONF: pehli URL config file — yahan se URL routing shuru hoti hai
ROOT_URLCONF = 'config.urls'

# TEMPLATES: HTML files kahan hain aur kaise render hote hain
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',  # Django ka default template engine
        'DIRS': [           # extra folders jahan templates dhundhe jaayenge (app ke bahar)
            BASE_DIR / 'templates',
            BASE_DIR.parent / 'templates',
        ],
        'APP_DIRS': True,   # har app ke andar templates/ folder automatically scan hoga
        'OPTIONS': {
            'context_processors': [
                # context_processors: har template ko automatically kuch variables milte hain
                'django.template.context_processors.debug',    # {{ debug }} variable
                'django.template.context_processors.request',  # {{ request }} object — allauth ko chahiye
                'django.contrib.auth.context_processors.auth', # {{ user }}, {{ perms }} variables
                'django.contrib.messages.context_processors.messages',  # {{ messages }} flash messages
                'inventory.context_processors.sidebar',        # sidebar menu data — har page pe available
            ],
        },
    },
]

# WSGI_APPLICATION: production web server (gunicorn) ko batata hai Django app kahan hai
WSGI_APPLICATION = 'config.wsgi.application'

# ─── Database ─────────────────────────────────────────────────────────────────
# DATABASES: do tarike se config hota hai
#   1. Cloud hosts (Neon/Render/Heroku/Railway) ek single DATABASE_URL dete hain — usko parse karo
#   2. Local dev mein 6 alag-alag DB_* vars from .env (purana tarika)
# Production deploy time pe sirf .env mein DATABASE_URL=postgres://... daal do, baaki same code chalega
# CONN_MAX_AGE: DB connection reuse hoti hai 10 minutes tak — har request pe naya connection nahi banana padta (performance)
DATABASE_URL = config('DATABASE_URL', default='')

if DATABASE_URL:
    # Production path: single connection string. ssl_require=True production providers ke liye safe default
    DATABASES = {
        'default': dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
            ssl_require=True,
        )
    }
else:
    # Local dev path: separate vars, no SSL needed for localhost
    DATABASES = {
        'default': {
            'ENGINE': config('DB_ENGINE', default='django.db.backends.postgresql'),  # PostgreSQL driver
            'NAME': config('DB_NAME', default='inventory_db'),       # database ka naam
            'USER': config('DB_USER', default='postgres'),           # DB user
            'PASSWORD': config('DB_PASSWORD', default='postgres'),   # DB password — .env mein set karo
            'HOST': config('DB_HOST', default='localhost'),          # DB server address
            'PORT': config('DB_PORT', default='5432'),               # PostgreSQL default port
            'CONN_MAX_AGE': 600,  # connection pool: 10 min tak reuse karo, naya connection mat banao
        }
    }

# ─── Feature flags ──────────────────────────────────────────────────────────
# (V2-1d) WORKER_TASK_DUAL_WRITE retired with the M2M dual-write — WorkerStageTask
# is the sole assignment truth (migration 0035). See docs/V2_1D_EXECUTION_REVIEW.md.

# V2-3 PR-B / ADR-0007 cutover EXECUTED (owner D-V3.1, 2026-06-11): earnings
# book ONLY at Adda settlement by default (era-B). env
# LEDGER_CREDIT_AT_ALLOCATION=True is the ROLLBACK LEVER — restores legacy
# allocation-time crediting (era-A). Symmetric double-credit guard makes BOTH
# directions safe (allocation_service + adda_settlement_service). Physical
# deletion of the legacy path stays soak-gated (separate future PR).
LEDGER_CREDIT_AT_ALLOCATION = config('LEDGER_CREDIT_AT_ALLOCATION', default=False, cast=bool)

# ─── Password Validation ──────────────────────────────────────────────────────
# Yeh validators password set karte waqt check karte hain — weak passwords reject hote hain
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},  # naam jaisi password reject
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
     'OPTIONS': {'min_length': 8}},   # minimum 8 characters
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},  # "password123" jaisi common reject
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},  # sirf numbers wali reject
]

# PASSWORD_HASHERS: passwords DB mein plain text mein nahi store hote — hash hote hain
# Argon2 is the winner of the Password Hashing Competition and is recommended
# by OWASP. Listed first → new passwords use Argon2; older PBKDF2 hashes
# continue to verify, and Django will upgrade them on next successful login.
# Agar DB leak bhi ho jaye → original password crack karna practically impossible hai
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',      # sabse strong — naye passwords yahi use karte hain
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',      # purane passwords ke liye backward compatibility
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
]

# ─── Localisation ─────────────────────────────────────────────────────────────
LANGUAGE_CODE = 'en-us'       # Django UI language (admin panel etc.)
TIME_ZONE = 'Asia/Kolkata'    # IST — DateTimeField values is timezone mein dikhenge
USE_I18N = True               # internationalisation support on
USE_TZ = True                 # DB mein UTC store, display mein TIME_ZONE convert — always keep True

# ─── Static Files (CSS, JS, Images) ──────────────────────────────────────────
# Static files = developer ke likhe CSS/JS — user ke upload nahi
STATIC_URL = '/static/'                       # browser mein URL prefix: /static/main.css
STATICFILES_DIRS = [
    BASE_DIR / "accounts/static",             # development mein yahan se files serve hoti hain
]
STATIC_ROOT = BASE_DIR / 'staticfiles'        # `collectstatic` command sab files yahan copy karti hai (production ke liye)

# Django 5.1+ uses STORAGES instead of deprecated STATICFILES_STORAGE
# whitenoise: static files Python server se serve karta hai — nginx ki zarurat nahi
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",  # user uploads ke liye local disk
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",  # CSS/JS compress + cache-bust karta hai
    },
}

# MEDIA: user ke uploaded files (profile photos, documents etc.)
MEDIA_URL = '/media/'          # browser URL prefix
MEDIA_ROOT = BASE_DIR / 'media'  # disk pe kahan store hoge

# DEFAULT_AUTO_FIELD: naye models ka primary key default type — BigAutoField = 64-bit integer (bahut bada)
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# AUTH_USER_MODEL: Django ko batao ki hamara custom User model use karo, built-in nahi
# Iske baad change karna bahut mushkil hai — isliye project shuru mein hi set karte hain
AUTH_USER_MODEL = 'accounts.User'

# ─── Email ────────────────────────────────────────────────────────────────────
# Email — reads from .env; local.py can override backend if needed
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend')  # SMTP = real emails bhejta hai
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')    # Gmail ka SMTP server
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)       # 587 = TLS port
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)  # encrypted connection
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')        # Gmail address
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')  # Gmail app password (.env mein)

# ─── Django Allauth ───────────────────────────────────────────────────────────
# Allauth: login/signup/Google OAuth handle karta hai
ACCOUNT_USER_MODEL_USERNAME_FIELD = None   # username field nahi hai — sirf email se login
ACCOUNT_AUTHENTICATION_METHOD = "email"    # email = login identifier
ACCOUNT_USERNAME_REQUIRED = False          # signup pe username nahi maangna
ACCOUNT_EMAIL_REQUIRED = True             # email required hai

# AUTO_SIGNUP=False + custom adapter — random Google accounts can't onboard
# themselves; a Super Admin must pre-provision the User row first. See
# accounts/allauth_adapters.py for the enforcement logic.
# Matlab: koi bhi Google account se signup nahi kar sakta — pehle admin ko user banana hoga
SOCIALACCOUNT_AUTO_SIGNUP = False
SOCIALACCOUNT_EMAIL_AUTHENTICATION = True              # Google email se existing account dhundhe
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True  # match mila toh auto-link karo
SOCIALACCOUNT_ADAPTER = "accounts.allauth_adapters.RestrictedSocialAccountAdapter"  # hamara custom check

# Google OAuth credentials — loaded from .env so they're never hard-coded
# Yeh credentials Google Cloud Console se milte hain
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': config('GOOGLE_CLIENT_ID', default=''),      # Google app ID
            'secret': config('GOOGLE_CLIENT_SECRET', default=''),     # Google app secret
            'key': '',
        },
        'SCOPE': ['profile', 'email'],         # Google se sirf name + email maango
        'AUTH_PARAMS': {'access_type': 'online'},  # offline access nahi chahiye
    }
}

# ─── Redirect URLs ────────────────────────────────────────────────────────────
LOGIN_URL = "/app/"               # login page ka URL — @login_required decorator yahan redirect karta hai
LOGIN_REDIRECT_URL = "/app/home/" # login ke baad kahan jaana hai
LOGOUT_REDIRECT_URL = "/"         # logout ke baad kahan jaana hai

# ─── Session Security ─────────────────────────────────────────────────────────
# Session = server pe store hota hai ki kaunsa user logged in hai
# DB-backed sessions: revocable server-side (better than cookie-only)
# Browser cookie mein sirf ek ID hota hai — actual data DB mein — admin revoke kar sakta hai
SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_AGE = 60 * 60 * 8      # 8 ghante baad session expire — dobara login karna padega
SESSION_EXPIRE_AT_BROWSER_CLOSE = False  # browser band karne pe logout nahi (True karo "remember me" nahi chahiye toh)
SESSION_COOKIE_HTTPONLY = True    # JavaScript session cookie nahi padh sakta — XSS attack se bachata hai
SESSION_COOKIE_SAMESITE = "Lax"   # cookie sirf same-site requests pe jaayegi — CSRF attack rokta hai
# Only write session to DB when data actually changes (not on every GET request).
# This avoids one extra DB write per request. Views/services must set
# request.session.modified = True whenever they mutate session data.
SESSION_SAVE_EVERY_REQUEST = False  # performance: sirf tab DB write karo jab session data badla ho

# ─── Logging ──────────────────────────────────────────────────────────────────
# Logging — ensure the logs directory exists before Django tries to write to it
_LOG_DIR = BASE_DIR / 'logs'
_LOG_DIR.mkdir(exist_ok=True)  # logs/ folder create karo agar exist nahi karta — warna FileHandler crash karega

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,  # Django ke built-in loggers band mat karo
    'filters': {
        # P0.4: stamp every record with the request id (see core.observability).
        'request_id': {'()': 'core.observability.RequestIDFilter'},
    },
    'formatters': {
        # formatter = log line ka format decide karta hai
        'verbose': {
            # [{request_id}] correlates all lines of one request (P0.4).
            'format': '{levelname} {asctime} {module} [{request_id}] {message}',
            'style': '{',
        },
        # Security log gets its own line format — flat key=value pairs are
        # easier for grep / Loki / Splunk than nested message text.
        'security': {
            'format': '{asctime} {levelname} security {message}',
            'style': '{',
        },
    },
    'handlers': {
        # handler = log kahan jaayega (console? file?)
        'console': {
            'class': 'logging.StreamHandler',   # terminal mein print karo
            'formatter': 'verbose',
            'filters': ['request_id'],
        },
        # P0.4: RotatingFileHandler so logs don't grow unbounded (5MB × 5 backups).
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',  # sab app + Django logs yahan
            'maxBytes': 5 * 1024 * 1024,
            'backupCount': 5,
            'formatter': 'verbose',
            'filters': ['request_id'],
        },
        'security_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'security.log',  # sirf login/rate-limit events yahan
            'maxBytes': 5 * 1024 * 1024,
            'backupCount': 5,
            'formatter': 'security',
        },
    },
    'root': {
        # P0.4: app/service loggers (logging.getLogger(__name__)) propagate here →
        # now persisted + rotated in django.log, not just console.
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],  # Django framework logs → terminal + file
            'level': 'INFO',
            'propagate': False,  # root logger ko forward mat karo — duplicate entries avoid
        },
        # Dedicated stream for auth/rate-limit events. Set to WARNING in
        # production .env if INFO chatter becomes too noisy; failures will
        # still surface because they log at WARNING.
        'accounts.security': {
            'handlers': ['console', 'security_file'],  # login attempts → security.log
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# ─── Error aggregation (P0.4, OPTIONAL) ─────────────────────────────────────────
# Activated ONLY when SENTRY_DSN is set AND sentry-sdk is installed — neither is
# added speculatively (no DSN today). To switch on in production: add `sentry-sdk`
# to requirements + set SENTRY_DSN in .env. Off = zero overhead, zero dependency.
SENTRY_DSN = config('SENTRY_DSN', default='')
if SENTRY_DSN:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.django import DjangoIntegration
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            integrations=[DjangoIntegration()],
            traces_sample_rate=0.0,      # errors only; no perf tracing overhead by default
            send_default_pii=False,
        )
    except ImportError:
        import logging as _logging
        _logging.getLogger('django').warning(
            "SENTRY_DSN is set but sentry-sdk is not installed — skipping error aggregation."
        )
