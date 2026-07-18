"""bod.mixins — the BOD access gate (BOD-D4, owner charter D1.3: v1 =
Owner/Super Admin ONLY; "workers should never access it"; manager = future
versions via dated amendments).

The certified double-gate pattern: this dispatch mixin is the view-side gate
(the house UserPassesTestMixin idiom); the SidebarItemRule row — created by
the owner through the Access Control panel — adds the panel-driven middleware
gate on top (unmanaged URLs fall back to exactly this mixin, per the
SidebarAccessMiddleware pass-through contract)."""

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from accounts.services import ROLE_SUPER_ADMIN, user_has_role


class BODAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Owner/SA only (v1). Anonymous → the login redirect; an authenticated
    non-SA → a clean 403 (never a redirect loop)."""

    def test_func(self):
        return user_has_role(self.request.user, {ROLE_SUPER_ADMIN})

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied
        return super().handle_no_permission()  # → login redirect
