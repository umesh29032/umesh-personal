"""raw_materials ke view mixins — RBAC gates.

YEH FILE KYU HAI?
─────────────────
Class-based views ko role-gate karne ke liye mixins. Pattern inventory app ke
mixins.py se mirror kiya hai. test_func() False return kare to user ko 403 milega.
"""
from django.contrib.auth.mixins import UserPassesTestMixin

from accounts.services import (
    PRODUCTION_ROLES, ROLE_SUPER_ADMIN, user_has_role,
)


class ProductionRoleMixin(UserPassesTestMixin):
    """Production floor users — Super Admin / Manager / Karigar.

    Roll list, dashboards, master CRUD ke liye sufficient hai.
    """

    def test_func(self):
        # UserPassesTestMixin yahan se True/False le ke decide karta hai
        return user_has_role(self.request.user, PRODUCTION_ROLES)


class ProductionOrAccountantMixin(UserPassesTestMixin):
    """Production floor **or** accountant — the cloth-roll LIST only.

    Owner ruling 2026-08-02. The accountant's FINANCIAL_ROLES capability (view +
    edit Supplier and Cost Per KG) is DEFINED on cloth rolls, so gating the roll
    list to the production floor left that capability as unreachable dead code —
    a pure accountant could not open the one page their role exists for.
    RBAC.md's earlier "pure accountant: dispatch-blocked from rm pages BY DESIGN"
    is superseded for this one view.

    Read only in practice: bulk-add / edit / damage / assign keep their stricter
    gates, and the financial FIELDS stay governed by `user_can_view_financials` /
    `user_can_edit_financials` — unchanged.
    """

    def test_func(self):
        from accounts.services import ROLE_ACCOUNTANT
        return user_has_role(self.request.user,
                             PRODUCTION_ROLES | {ROLE_ACCOUNTANT})


class SuperAdminOnlyMixin(UserPassesTestMixin):
    """Sirf Super Admin — single-role rule.

    Cloth roll bulk intake pe applied — sensitive irreversible event.
    """

    def test_func(self):
        return user_has_role(self.request.user, [ROLE_SUPER_ADMIN])

class ManagementRoleMixin(UserPassesTestMixin):
    """Management only (super_admin + manager) — roll MASTER-DATA writes
    (edit/assign) mutate stock + cost truth; the floor works through the
    layering console, never here (campaign M9 fix, mirrors the M3
    AddaCreateView remedy)."""

    def test_func(self):
        from accounts.services import MANAGEMENT_ROLES, user_has_role
        return user_has_role(self.request.user, MANAGEMENT_ROLES)

