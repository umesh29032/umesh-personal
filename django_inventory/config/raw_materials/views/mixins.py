"""raw_materials ke view mixins — RBAC gates.

YEH FILE KYU HAI?
─────────────────
Class-based views ko role-gate karne ke liye mixins. Pattern inventory app ke
mixins.py se mirror kiya hai. test_func() False return kare to user ko 403 milega.
"""
from django.contrib.auth.mixins import UserPassesTestMixin

from inventory.services import (
    FINANCIAL_ROLES, PRODUCTION_ROLES, ROLE_SUPER_ADMIN, user_has_role,
)


class ProductionRoleMixin(UserPassesTestMixin):
    """Production floor users — Super Admin / Manager / Karigar.

    Roll list, dashboards, master CRUD ke liye sufficient hai.
    """

    def test_func(self):
        # UserPassesTestMixin yahan se True/False le ke decide karta hai
        return user_has_role(self.request.user, PRODUCTION_ROLES)


class SuperAdminOnlyMixin(UserPassesTestMixin):
    """Sirf Super Admin — single-role rule.

    Cloth roll bulk intake pe applied — sensitive irreversible event.
    """

    def test_func(self):
        return user_has_role(self.request.user, [ROLE_SUPER_ADMIN])


class FinancialRoleMixin(UserPassesTestMixin):
    """Finance access — Super Admin / Accountant.

    Future financial views (cost reports, payouts) ke liye reserved.
    Currently Supplier/Cost form fields gate karne ke liye service-level se hota hai.
    """

    def test_func(self):
        return user_has_role(self.request.user, FINANCIAL_ROLES)
