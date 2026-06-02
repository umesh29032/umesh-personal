"""
Root URLConf — Django reads `urlpatterns` and matches request paths top-down.

Primitives used here:
  - path('prefix/', view)          → exact-prefix route
  - include('app.urls')            → mount another URLConf under this prefix
  - admin.site.urls                → Django's built-in /admin/ site
  - static(MEDIA_URL, ...)         → DEV-ONLY: serve uploaded files; in prod
                                     serve them via nginx/whitenoise instead.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from storefront.views import public_home

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", public_home, name="public_home"),
    path("app/", include("accounts.urls")),
    path("accounts/", include("allauth.urls")),       # django-allauth: Google OAuth, signup flow
    path("inventory/", include("inventory.urls")),
    path("storefront/", include("storefront.urls")),  # authenticated storefront management
    path("raw-materials/", include("raw_materials.urls")),  # cloth inventory + master data
    path("production/", include("production.urls")),        # Adda batches + workflow stages
    path("tracking/", include("tracking.urls")),            # barcodes + audit history
    path("expense/", include("expense.urls")),              # worker payroll: earnings, advances, payments
]

if settings.DEBUG:
    # /media/ is mounted only when DEBUG=True — production must serve it
    # via the web server (whitenoise / nginx / S3) not Django.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
