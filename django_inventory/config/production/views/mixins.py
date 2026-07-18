"""production app ke view mixins — RBAC gates (+ the shared post-advance redirect).

YEH FILE KYU HAI?
─────────────────
CBV pe role-gate apply karne ke liye mixins. UserPassesTestMixin se inherit karte hain —
test_func() False → 403 Forbidden.
"""
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.urls import reverse

from accounts.services import (
    MANAGEMENT_ROLES, PRODUCTION_ROLES, ROLE_SUPER_ADMIN, user_has_role,
)


def get_adda(code):
    """One lookup rule for every per-Adda view: 404 by unique code."""
    from django.shortcuts import get_object_or_404
    from production.models import Adda
    return get_object_or_404(Adda, code=code)


def embedded_advance_redirect(adda):
    """Post-COMPLETE redirect target for EMBEDDED stage panels (F-3 polish).

    A dedicated login-only BOUNCE page (no stage data, no access gates beyond
    login) whose sole job is to postMessage the parent to reload. Neither the
    next stage's panel nor the completed stage's own panel is safe for the
    completing WORKER: the next stage may not be theirs, and stage completion
    auto-cancels their unreported task, so even the completed panel's
    assignment gate can refuse them. The bounce page can never 403.
    """
    return redirect(
        reverse('production:stage-advanced', kwargs={'code': adda.code})
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
        # V2-1c-iv object-level ASSIGNMENT gate: a worker may open only stages they
        # are ACTIVELY assigned to — skill alone is not enough (the prior leak).
        # Management (super_admin/manager) bypasses, as with the skill gate above.
        adda_code = kwargs.get('code')
        if code and adda_code and not user_has_role(request.user, MANAGEMENT_ROLES):
            from production.models import AddaStageRecord
            srs = list(AddaStageRecord.objects.filter(
                adda__code=adda_code, workflow_stage__stage__code=code,
            ))
            # streams: a trio stage may have one SR PER LANE — assignment
            # on ANY lane of this stage opens the console (the lane
            # switcher + task-scoped reports keep the work honest).
            if not srs or not any(
                    sr.is_worker_assigned(request.user) for sr in srs):
                raise PermissionDenied("You are not assigned to this stage.")
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
