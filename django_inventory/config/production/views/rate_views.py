"""Stage role-rate correction views (S1.1) — super-admin only.

YEH FILE KYU HAI?
─────────────────
Owner requirement 2026-06-14: super-admin BEFORE settlement ek stage ki payable
rate theek kar sake — saare completed-but-unsettled earnings auto-recalc ho, bina
worker-by-worker manual edit. UI sirf thin wrapper hai; truth stage_rate_service.
rerate_stage_role mein. Per-(stage_record, role) lock (M1) preserved — settled hone
ke baad refuse (reverse/supersede only).

  StageRateListView    — Adda ki stage role-rates (rate / locked / settled) + Correct link
  StageRateCorrectView — current→new rate + mandatory reason + confirm → service call
"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import FormView, TemplateView

from production.forms import StageRateCorrectionForm
from production.models import Adda, AddaStageRecord, AddaStageRoleRate

from .mixins import SuperAdminOnlyMixin


def _is_settled(stage_record, role) -> bool:
    """Any contribution of this (sr, role) actively settled (not voided)?
    Same predicate as the service refuse — drives the UI 'locked by settlement' state."""
    from production.models import WorkerStageContribution
    return (WorkerStageContribution.objects
            .filter(task__stage_record=stage_record, role_snapshot=role,
                    settlement_line__isnull=False,
                    settlement_line__voided_at__isnull=True)
            .exists())


class StageRateListView(LoginRequiredMixin, SuperAdminOnlyMixin, TemplateView):
    template_name = 'production/stage_rate_list.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        adda = get_object_or_404(Adda, code=self.kwargs['code'])
        rows = (AddaStageRoleRate.objects
                .filter(stage_record__adda=adda)
                .select_related('stage_record__workflow_stage__stage', 'role')
                .order_by('stage_record__workflow_stage__order', 'role__name'))
        # Group by stage record for stacked mobile-first cards.
        stages = {}
        for r in rows:
            sr = r.stage_record
            bucket = stages.setdefault(sr.pk, {'stage_record': sr, 'rates': []})
            bucket['rates'].append({
                'role': r.role,
                'rate': r.rate,
                'locked': r.locked_at is not None,
                'settled': _is_settled(sr, r.role),
            })
        ctx['adda'] = adda
        ctx['stages'] = list(stages.values())
        return ctx


class StageRateCorrectView(LoginRequiredMixin, SuperAdminOnlyMixin, FormView):
    template_name = 'production/stage_rate_correct.html'
    form_class = StageRateCorrectionForm

    def _objects(self):
        from accounts.models import Role
        adda = get_object_or_404(Adda, code=self.kwargs['code'])
        sr = get_object_or_404(AddaStageRecord, pk=self.kwargs['sr_id'], adda=adda)
        role = get_object_or_404(Role, pk=self.kwargs['role_id'])
        row = get_object_or_404(AddaStageRoleRate, stage_record=sr, role=role)
        return adda, sr, role, row

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        adda, sr, role, row = self._objects()
        ctx['adda'] = adda
        ctx['stage_record'] = sr
        ctx['role'] = role
        ctx['current_rate'] = row.rate
        ctx['settled'] = _is_settled(sr, role)
        return ctx

    def form_valid(self, form):
        from production.services import stage_rate_service
        adda, sr, role, _row = self._objects()
        try:
            _row, n = stage_rate_service.rerate_stage_role(
                sr, role, form.cleaned_data['new_rate'],
                actor=self.request.user, reason=form.cleaned_data['reason'])
        except (ValidationError, PermissionDenied) as exc:
            form.add_error(None, getattr(exc, 'message', str(exc)))
            return self.form_invalid(form)
        messages.success(
            self.request,
            f"Rate corrected to ₹{form.cleaned_data['new_rate']} — "
            f"{n} earning line(s) recalculated.")
        return redirect('production:stage-rates', code=adda.code)
