from django.contrib.auth.mixins import UserPassesTestMixin

from ..services import MANAGEMENT_ROLES, ROLE_SUPER_ADMIN, user_has_role


class ManagerOrAdminMixin(UserPassesTestMixin):
    """Restrict write operations to super_admin / manager roles."""

    def test_func(self):
        return user_has_role(self.request.user, MANAGEMENT_ROLES)


class SuperAdminOnlyMixin(UserPassesTestMixin):
    """Restrict access to super_admin role only."""

    def test_func(self):
        return user_has_role(self.request.user, {ROLE_SUPER_ADMIN})
