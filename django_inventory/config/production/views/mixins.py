"""production app ke view mixins — RBAC gates.

YEH FILE KYU HAI?
─────────────────
CBV pe role-gate apply karne ke liye mixins. UserPassesTestMixin se inherit karte hain —
test_func() False → 403 Forbidden.
"""
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied

from inventory.services import (
    MANAGEMENT_ROLES, PRODUCTION_ROLES, ROLE_SUPER_ADMIN, user_has_role,
)


class StageViewAccessMixin:
    """Skill-gate a stage WORKSPACE/PANEL view (not just its actions).

    Mirrors AddaDetailView's per-panel stage_access_map so a direct-URL hit on a
    stage workspace obeys the same skill rule as the embedded panel: management
    bypasses, skill- or stage-role-holders pass, everyone else 403. Stage code
    comes from the `stage_code` class attr, else the `stage_type` URL kwarg.

    Place AFTER LoginRequiredMixin in the bases so anonymous users redirect to
    login first; calls super().dispatch() so it composes with role mixins.
    """
    stage_code = None

    def dispatch(self, request, *args, **kwargs):
        # Lazy import: production.services pulls in models that import inventory.
        from production.services import user_can_access_stage
        code = self.stage_code or kwargs.get('stage_type')
        if code and not user_can_access_stage(request.user, code):
            raise PermissionDenied(f"You lack the skill to access the '{code}' stage.")
        return super().dispatch(request, *args, **kwargs)


class ProductionRoleMixin(UserPassesTestMixin):
    """Production floor users — Adda + stage views ke liye."""

    def test_func(self):
        return user_has_role(self.request.user, PRODUCTION_ROLES)


class ManagementRoleMixin(UserPassesTestMixin):
    """Management only (super_admin + manager) — catalog/admin reads that the
    shop floor (karigar) should NOT see, e.g. the Products list."""

    def test_func(self):
        return user_has_role(self.request.user, MANAGEMENT_ROLES)


class SuperAdminOnlyMixin(UserPassesTestMixin):
    """Sirf Super Admin — Product CRUD ke liye (high-impact change)."""

    def test_func(self):
        return user_has_role(self.request.user, [ROLE_SUPER_ADMIN])
