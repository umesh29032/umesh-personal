"""production app ke view mixins — RBAC gates.

YEH FILE KYU HAI?
─────────────────
CBV pe role-gate apply karne ke liye mixins. UserPassesTestMixin se inherit karte hain —
test_func() False → 403 Forbidden.
"""
from django.contrib.auth.mixins import UserPassesTestMixin

from inventory.services import PRODUCTION_ROLES, ROLE_SUPER_ADMIN, user_has_role


class ProductionRoleMixin(UserPassesTestMixin):
    """Production floor users — Adda + stage views ke liye."""

    def test_func(self):
        return user_has_role(self.request.user, PRODUCTION_ROLES)


class SuperAdminOnlyMixin(UserPassesTestMixin):
    """Sirf Super Admin — Product CRUD ke liye (high-impact change)."""

    def test_func(self):
        return user_has_role(self.request.user, [ROLE_SUPER_ADMIN])
