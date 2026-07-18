"""Generic-operation action views (R10-B) — ONE start/complete/reopen set for
EVERY config-only stage, parameterized by stage_type (the same URL pattern as
stage-panel). Closes the §6 gap from the frozen architecture review: after
this, a new operation needs NO endpoints, ever.

parse→gate→delegate only; the generic_stage service owns the guards
(start=mgmt · complete=mgmt or assigned+live-access · reopen=mgmt skeleton).
"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View

from production.models import Adda

from .mixins import ProductionRoleMixin, embedded_advance_redirect


def _err(exc) -> str:
    msg = getattr(exc, 'messages', None)
    return ' '.join(msg) if msg else str(exc)


class _GenericActionBase(LoginRequiredMixin, ProductionRoleMixin, View):
    http_method_names = ['post']

    def panel_url(self, code, stage_type, request):
        if request.POST.get('embedded') == '1':
            return reverse('production:stage-panel', kwargs={
                'code': code, 'stage_type': stage_type}) + '?embedded=1'
        return reverse('production:stage-panel', kwargs={
            'code': code, 'stage_type': stage_type})


class GenericStageStartView(_GenericActionBase):
    def post(self, request, code, stage_type):
        adda = get_object_or_404(Adda, code=code)
        worker_ids = [int(w) for w in request.POST.getlist('workers') if w.isdigit()]
        from production.stages.generic_stage.service import start_generic_stage
        try:
            start_generic_stage(adda=adda, stage_code=stage_type,
                                worker_ids=worker_ids, user=request.user)
        except (PermissionDenied, ValidationError) as exc:
            messages.error(request, _err(exc))
            return redirect(self.panel_url(code, stage_type, request))
        messages.success(request, "Workers assigned.")
        return redirect(self.panel_url(code, stage_type, request))


class GenericStageCompleteView(_GenericActionBase):
    def post(self, request, code, stage_type):
        adda = get_object_or_404(Adda, code=code)
        override_reason = (request.POST.get('override_reason', '').strip() or None
                           if request.POST.get('override_pending') else None)
        from production.stages.generic_stage.service import complete_generic_stage
        try:
            complete_generic_stage(adda=adda, stage_code=stage_type,
                                   user=request.user,
                                   override_pending_reason=override_reason)
        except (PermissionDenied, ValidationError) as exc:
            messages.error(request, _err(exc))
            return redirect(self.panel_url(code, stage_type, request))
        adda.refresh_from_db()
        nxt = (adda.current_stage.get_stage_type_display()
               if adda.current_stage else 'completion')
        messages.success(request, f"Stage complete. Advanced to {nxt}.")
        # F-3: gate-free bounce — the completing worker never lands on a 403.
        if request.POST.get('embedded') == '1':
            return embedded_advance_redirect(adda)
        return redirect('production:adda-detail', code=adda.code)


class GenericStageAllocateView(_GenericActionBase):
    """OP-1: manager splits the upstream pool — one allocation row per submit.
    parse→delegate; pool_service.allocate owns mgmt gate + over-allocation
    refusal + the D2 advisory lock. Worker must already be on the roster
    (dropdown is roster-only; the service itself is roster-agnostic)."""

    def post(self, request, code, stage_type):
        from decimal import Decimal, InvalidOperation

        from accounts.models import User
        from production.services import pool_service
        from production.stages.generic_stage.service import _get_stage_record

        adda = get_object_or_404(Adda, code=code)
        sr = _get_stage_record(adda, stage_type)
        try:
            if sr is None:
                raise ValidationError("Start the stage (assign workers) first.")
            worker_raw = request.POST.get('worker') or ''
            if not worker_raw.isdigit():
                raise ValidationError("Pick a worker.")
            worker = get_object_or_404(User, pk=int(worker_raw))
            try:
                qty = Decimal((request.POST.get('qty') or '').strip())
            except InvalidOperation:
                raise ValidationError("Quantity must be a number.")
            color_raw = request.POST.get('color_id') or ''
            size_raw = request.POST.get('size_id') or ''
            pool_service.allocate(
                sr, worker, qty=qty, actor=request.user,
                color_id=int(color_raw) if color_raw.isdigit() else None,
                size_id=int(size_raw) if size_raw.isdigit() else None)
        except (PermissionDenied, ValidationError) as exc:
            messages.error(request, _err(exc))
            return redirect(self.panel_url(code, stage_type, request))
        messages.success(
            request, f"Work allocated to {worker.get_full_name() or worker.email}.")
        return redirect(self.panel_url(code, stage_type, request))


class GenericStageAllocationVoidView(_GenericActionBase):
    """OP-1: void one allocation (append-only correction — qty returns to the
    pool). pool_service.void_allocation owns the mgmt gate + lock."""

    def post(self, request, code, stage_type):
        from production.models import WorkerStageAllocation
        from production.services import pool_service

        adda = get_object_or_404(Adda, code=code)
        wsa = get_object_or_404(
            WorkerStageAllocation, pk=request.POST.get('allocation_id'),
            stage_record__adda=adda)
        try:
            pool_service.void_allocation(wsa, actor=request.user)
        except (PermissionDenied, ValidationError) as exc:
            messages.error(request, _err(exc))
            return redirect(self.panel_url(code, stage_type, request))
        messages.success(request, "Allocation voided — quantity returned to the pool.")
        return redirect(self.panel_url(code, stage_type, request))


class GenericStageReopenView(_GenericActionBase):
    def post(self, request, code, stage_type):
        adda = get_object_or_404(Adda, code=code)
        from production.stages.generic_stage.service import reopen_generic_stage
        try:
            reopen_generic_stage(adda=adda, stage_code=stage_type, user=request.user)
        except (PermissionDenied, ValidationError) as exc:
            messages.error(request, _err(exc))
            return redirect(self.panel_url(code, stage_type, request))
        messages.success(request, "Stage reopened — make corrections then Complete again.")
        if request.POST.get('embedded') == '1':
            return redirect(reverse('production:stage-panel', kwargs={
                'code': adda.code, 'stage_type': stage_type,
            }) + '?embedded=1&advanced=1')
        return redirect('production:adda-detail', code=adda.code)
