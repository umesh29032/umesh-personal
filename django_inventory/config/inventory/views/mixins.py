from django.contrib.auth.mixins import UserPassesTestMixin

from ..services import MANAGEMENT_ROLES, user_has_role


class ManagerOrAdminMixin(UserPassesTestMixin):
    """Restrict write operations to super_admin / manager roles."""

    def test_func(self):
        return user_has_role(self.request.user, MANAGEMENT_ROLES)
