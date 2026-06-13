"""
Root URLConf — Django reads `urlpatterns` and matches request paths top-down.

Primitives used here:
  - path('prefix/', view)          → exact-prefix route
  - include('app.urls')            → mount another URLConf under this prefix
  - admin.site.urls                → Django's built-in /admin/ site
  - django.views.static.serve      → file serving for /media/ (see PD note below)
"""
from django.conf import settings
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.urls import include, path
from django.views.static import serve as _media_serve

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
    path("tracking/", include("inventory.tracking_urls")),  # barcodes + audit history (P4.2: inventory-owned views, tracking namespace preserved)
    path("expense/", include("expense.urls")),              # worker payroll: earnings, advances, payments
]

# ── Media serving (PD bundle, 2026-06-11 — owner-approved Option 1) ──────────
# Two tiers, same in dev and prod (no DEBUG branch → identical behavior + testable):
#   /media/storefront/*  PUBLIC — homepage assets (logo, category/product images)
#                        rendered on the anonymous storefront.
#   /media/*             LOGIN-REQUIRED — everything else is business evidence
#                        (pattern photos/videos, advance attachments, profile
#                        pics). Upgrade over the old DEBUG-only static(): media
#                        is no longer world-readable.
# Future exits (recorded, not built): S3 = STORAGES swap + delete these routes;
# nginx X-Accel = swap serve() for an X-Accel-Redirect response. Known limit:
# django serve() has no HTTP Range support — pattern videos play without
# scrubbing; acceptable at current scale (exit triggers in PD PR description).
urlpatterns += [
    path('media/storefront/<path:path>', _media_serve,
         {'document_root': settings.MEDIA_ROOT / 'storefront'},
         name='media-public'),
    path('media/<path:path>', login_required(_media_serve),
         {'document_root': settings.MEDIA_ROOT},
         name='media-protected'),
]

# ─── Error handlers (P0-2) ────────────────────────────────────────────────────
# Explicit so intent is discoverable. These point at Django's DEFAULT views,
# which render the matching branded template (templates/403.html, 404.html,
# 500.html) when DEBUG=False. We keep the default views deliberately: server_error
# renders 500.html with an EMPTY context (no DB/context processors), so a 500 can
# never cascade into another error — the templates carry the branding, the views
# stay minimal. Replaces Django's bare unstyled 403/404/500 (Phase-G G-UX-1).
handler403 = 'django.views.defaults.permission_denied'
handler404 = 'django.views.defaults.page_not_found'
handler500 = 'django.views.defaults.server_error'
