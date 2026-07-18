"""History timeline views — ClothRoll aur Adda ke audit logs.

YEH FILE KYU HAI?
─────────────────
ClothRollHistory / AddaHistory rows ko time-ordered timeline render karte hain.
select_related actor/stage FK pe → N+1 query bachi (template har row pe email + stage display use karta hai).
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView

from accounts.services import (
    MANAGEMENT_ROLES, user_can_view_financials, user_has_role,
)
from inventory.views.mixins import ProductionRoleMixin as _ProductionRoleMixin
from production.models import Adda, WorkerStageTask
from raw_materials.models import ClothRoll
from tracking.models import AddaHistory, ClothRollHistory


def _assigned_to_adda(user, adda) -> bool:
    """Worker holds a live (non-cancelled) task on this Adda — the SAME isolation
    the dashboard applies (V2-1c-iv)."""
    return (WorkerStageTask.objects
            .filter(stage_record__adda=adda, worker=user)
            .exclude(status=WorkerStageTask.Status.CANCELLED)
            .exists())


def _require_adda_history_access(user, adda):
    """G-AUTH-1: management sees every Adda's history; a worker only Addas they
    are assigned to. Denial → branded 403 (handler403)."""
    if user_has_role(user, MANAGEMENT_ROLES):
        return
    if not _assigned_to_adda(user, adda):
        raise PermissionDenied("You can only view history for Addas you're assigned to.")


def _require_roll_history_access(user, roll):
    """Same principle for a roll: management always; a worker only if the roll
    touched an Adda they are assigned to (roll↔Adda via AddaHistory events)."""
    if user_has_role(user, MANAGEMENT_ROLES):
        return
    touched_adda_ids = (AddaHistory.objects.filter(roll=roll)
                        .values_list('adda_id', flat=True).distinct())
    allowed = (WorkerStageTask.objects
               .filter(stage_record__adda_id__in=touched_adda_ids, worker=user)
               .exclude(status=WorkerStageTask.Status.CANCELLED)
               .exists())
    if not allowed:
        raise PermissionDenied("You can only view history for rolls on Addas you're assigned to.")


class RollHistoryView(LoginRequiredMixin, _ProductionRoleMixin, TemplateView):
    template_name = 'tracking/history/roll_history.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        roll = get_object_or_404(ClothRoll, pk=self.kwargs['roll_pk'])
        _require_roll_history_access(self.request.user, roll)
        ctx['roll'] = roll
        events = ClothRollHistory.objects.filter(roll=roll).select_related('actor').order_by('-created_at')
        # PA-03-1: supplier + cost_per_kg are FINANCIAL fields (view-gated to
        # FINANCIAL_ROLES on the roll list/detail). Their CHANGE history exposes
        # the same values, so drop those rows server-side for non-financial users
        # — otherwise a worker/manager reads cost_per_kg via the audit timeline.
        if not user_can_view_financials(self.request.user):
            events = events.exclude(field_name__in=('supplier', 'cost_per_kg'))
        ctx['events'] = events
        return ctx


class AddaHistoryView(LoginRequiredMixin, _ProductionRoleMixin, TemplateView):
    template_name = 'tracking/history/adda_history.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        adda = get_object_or_404(Adda, code=self.kwargs['adda_code'])
        _require_adda_history_access(self.request.user, adda)
        ctx['adda'] = adda
        # roll__cloth_type + roll__cloth_color needed because template now shows
        # type/color/width alongside roll_id in event rows (no N+1).
        ctx['events'] = (
            AddaHistory.objects
            .filter(adda=adda)
            .select_related(
                'actor', 'stage_from', 'stage_to',
                'roll', 'roll__cloth_type', 'roll__cloth_color',
            )
            .order_by('-created_at')
        )
        return ctx
