"""History timeline views — ClothRoll aur Adda ke audit logs.

YEH FILE KYU HAI?
─────────────────
ClothRollHistory / AddaHistory rows ko time-ordered timeline render karte hain.
select_related actor/stage FK pe → N+1 query bachi (template har row pe email + stage display use karta hai).
"""
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView

from inventory.services import PRODUCTION_ROLES, user_has_role
from production.models import Adda
from raw_materials.models import ClothRoll
from tracking.models import AddaHistory, ClothRollHistory


class _ProductionRoleMixin(UserPassesTestMixin):
    def test_func(self):
        return user_has_role(self.request.user, PRODUCTION_ROLES)


class RollHistoryView(LoginRequiredMixin, _ProductionRoleMixin, TemplateView):
    template_name = 'tracking/history/roll_history.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        roll = get_object_or_404(ClothRoll, pk=self.kwargs['roll_pk'])
        ctx['roll'] = roll
        ctx['events'] = ClothRollHistory.objects.filter(roll=roll).select_related('actor').order_by('-created_at')
        return ctx


class AddaHistoryView(LoginRequiredMixin, _ProductionRoleMixin, TemplateView):
    template_name = 'tracking/history/adda_history.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        adda = get_object_or_404(Adda, code=self.kwargs['adda_code'])
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
