"""Centralized URL-access enforcement for Access-Control-panel items.

The Sidebar Access page (SidebarItemRule) controls which roles/skills SEE each
menu item — but hiding a menu link is NOT security: the view is still reachable
by typing the URL. This middleware closes that gap. For any request whose
resolved url_name has a SidebarItemRule, it enforces the SAME role/skill decision
the sidebar uses (permission_service.can_access_url_name). Denied → flash message
+ redirect to the previous page (or the user's dashboard).

Pass-through (returns None, view runs normally) when:
  • user is anonymous (LoginRequired handles it),
  • the url_name has NO rule (unmanaged — the view's own mixin gates it),
  • Super Admin (always allowed),
  • the url_name is an exempt landing page (dashboards — never block, no loops).

Defense in depth: unmanaged + action URLs keep their existing view mixins; this
only ADDS the panel-driven gate on top for managed page URLs.
"""
from urllib.parse import urlparse

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import Resolver404, resolve, reverse

from inventory.services import MANAGEMENT_ROLES, can_access_url_name, user_has_role

# Landing pages — never blocked. The management vs user dashboard split is
# cosmetic (both @login_required), and exempting them prevents redirect loops
# (the fallback target below is always one of these).
_EXEMPT_URL_NAMES = {
    'inventory:inventory_dashboard',
    'inventory:user_dashboard',
}


def _safe_home(user) -> str:
    """A dashboard the user can always reach (used as the redirect fallback)."""
    if user_has_role(user, MANAGEMENT_ROLES):
        return reverse('inventory:inventory_dashboard')
    return reverse('inventory:user_dashboard')


class SidebarAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return None
        match = request.resolver_match
        if match is None:
            return None
        url_name = match.view_name  # 'namespace:name'
        if not url_name or url_name in _EXEMPT_URL_NAMES:
            return None
        if can_access_url_name(user, url_name):
            return None

        # ── Denied ───────────────────────────────────────────────────────────
        # AJAX/fetch callers get a clean 403 (a redirect would corrupt the call).
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse(
                {'detail': "You don't have the access to this page."}, status=403,
            )

        messages.error(request, "You don't have the access to this page.")

        # Redirect to the previous page IF it's same-host and itself accessible
        # (resolve + re-check to guarantee no redirect loop); else the dashboard.
        target = _safe_home(user)
        referer = request.META.get('HTTP_REFERER')
        if referer:
            p = urlparse(referer)
            if p.netloc == request.get_host() and p.path and p.path != request.path:
                try:
                    ref_match = resolve(p.path)
                    if can_access_url_name(user, ref_match.view_name):
                        target = referer
                except Resolver404:
                    pass
        return redirect(target)
