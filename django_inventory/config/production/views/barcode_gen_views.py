"""Barcode Generation stage views — workspace + 4 action handlers.

YEH FILE KYU HAI?
─────────────────
Barcode Generation stage ka user-facing layer (PR-C 2026-05-29).
Pattern mirrors pattern_stage_views + cutting workspace views:
   browser POST → view.post() → service function → redirect back

URL TABLE:
  GET  addas/<code>/barcode-gen/                workspace (full page)
  POST addas/<code>/barcode-gen/start/          manager assigns workers
  POST addas/<code>/barcode-gen/generate/       generate BarcodeBatch rows
  POST addas/<code>/barcode-gen/complete/       validate counts + advance
  POST addas/<code>/barcode-gen/reopen/         mgmt unlock (with guards)

EMBEDDED MODE:
  Adda detail page workspace ko iframe me embed karta hai (?embedded=1).
  Action views check `request.POST['embedded']` → embedded redirect target.

SHARED CONTEXT BUILDER:
  `_build_barcode_gen_context` — workspace + StagePanelView ke beech context
  share karta hai (DRY).
"""
from __future__ import annotations

from django import forms
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError
from django.shortcuts import redirect
from django.urls import reverse
from django.views import View
from django.views.generic import TemplateView

from accounts.skills import (
    SKILL_CUTTING_MASTER, SKILL_CUTTING_MASTER_HELPER, user_has_skill,
)
from accounts.services import MANAGEMENT_ROLES, user_has_role
from production.constants import STAGE_BARCODE_GENERATION
from production.forms._shared import _WorkerCheckboxes  # F-5: worker chip widget (presentation)
from production.models import Adda, AddaStageRecord, WorkflowStage
from production.services import (
    complete_barcode_generation, generate_barcodes, get_barcode_snapshot,
    preview_barcode_counts, reopen_barcode_generation, start_barcode_generation,
)

from .mixins import ProductionRoleMixin, StageViewAccessMixin, embedded_advance_redirect, get_adda


_get_adda = get_adda   # shared lookup (views.mixins) — local alias keeps call sites stable


def _bg_workflow_stage(adda: Adda) -> WorkflowStage | None:
    return adda.product.workflow_stages.filter(
        stage__code=STAGE_BARCODE_GENERATION,
    ).first()


def _bg_stage_record(adda: Adda) -> AddaStageRecord | None:
    wf = _bg_workflow_stage(adda)
    if wf is None:
        return None
    return AddaStageRecord.objects.filter(adda=adda, workflow_stage=wf).first()


class BarcodeGenStartForm(forms.Form):
    """Mgmt assigns workers — same skill set as cutting (master + helper)."""

    workers = forms.ModelMultipleChoiceField(
        queryset=None, required=True,
        widget=_WorkerCheckboxes(),  # F-5: chip UI (was CheckboxSelectMultiple); payload identical
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # F-4: THE shared picker source — active users with this stage's access
        # skills (Stage.access_by_skill), so picker == access gate, always.
        from production.services import eligible_stage_workers
        self.fields['workers'].queryset = eligible_stage_workers(STAGE_BARCODE_GENERATION)


def _build_barcode_gen_context(request, adda: Adda) -> dict:
    """Shared context for workspace + embedded panel.

    Computes:
      • stage_record (or None)
      • record (BarcodeGenerationRecord)        → generated_at + total_barcodes
      • preview                                  → dict from preview_barcode_counts
      • snapshot                                 → batches + totals from snapshot
      • can_start / can_generate / can_complete / can_reopen flags
      • start_form                               → Section 1 form (mgmt only)
    """
    user = request.user
    wf = _bg_workflow_stage(adda)
    sr = _bg_stage_record(adda)
    record = getattr(sr, 'barcode_generation', None) if sr else None

    preview = preview_barcode_counts(adda)
    snapshot = get_barcode_snapshot(adda)

    is_management = user_has_role(user, MANAGEMENT_ROLES)
    has_master_skill = user_has_skill(
        user, [SKILL_CUTTING_MASTER, SKILL_CUTTING_MASTER_HELPER],
    )
    has_helper_skill = user_has_skill(user, SKILL_CUTTING_MASTER_HELPER)
    is_assigned = bool(sr and sr.is_worker_assigned(user))

    can_start = is_management and sr is None
    can_generate = (
        sr is not None and sr.completed_at is None
        and (is_management or (is_assigned and has_master_skill))
        and not (record and record.generated_at)
    )
    can_complete = (
        sr is not None and sr.completed_at is None
        and record is not None and record.generated_at is not None
        and (is_management or has_helper_skill)
    )
    can_reopen = is_management and sr is not None and sr.completed_at is not None

    next_stage = None
    if adda.current_stage is not None:
        next_stage = (
            adda.product.workflow_stages
            .filter(order__gt=adda.current_stage.order)
            .order_by('order').first()
        )

    return {
        'adda': adda,
        'workflow_stage': wf,
        'stage_record': sr,
        'record': record,
        'preview': preview,
        'snapshot': snapshot,
        'is_management': is_management,
        'can_start': can_start,
        'can_generate': can_generate,
        'can_complete': can_complete,
        'can_reopen': can_reopen,
        'next_stage': next_stage,
        'start_form': BarcodeGenStartForm(initial={
            'workers': list(sr.active_worker_tasks().values_list('worker_id', flat=True)) if sr else [],
        }) if is_management else None,
    }


class BarcodeGenWorkspaceView(LoginRequiredMixin, ProductionRoleMixin,
                              StageViewAccessMixin, TemplateView):
    stage_code = 'barcode_generation'      # skill-gate the VIEW, not just actions
    template_name = 'production/barcode_gen_workspace.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(_build_barcode_gen_context(
            self.request, _get_adda(self.kwargs['code']),
        ))
        return ctx


# ── Action views (POST only) ────────────────────────────────────────────────


class _BarcodeGenActionBase(LoginRequiredMixin, ProductionRoleMixin, View):
    """Common action helpers — workspace URL builder + ValidationError flatten."""

    http_method_names = ['post']

    def workspace_url(self, code: str, request=None) -> str:
        if request is not None and request.POST.get('embedded') == '1':
            return reverse('production:stage-panel', kwargs={
                'code': code, 'stage_type': STAGE_BARCODE_GENERATION,
            }) + '?embedded=1'
        return reverse('production:barcode-gen-workspace', kwargs={'code': code})

    def _service_error(self, exc) -> str:
        msg = getattr(exc, 'messages', None)
        return ' '.join(msg) if msg else str(exc)


class BarcodeGenStartView(_BarcodeGenActionBase):
    def post(self, request, code):
        adda = _get_adda(code)
        form = BarcodeGenStartForm(request.POST)
        if not form.is_valid():
            messages.error(request, "Select at least one worker.")
            return redirect(self.workspace_url(code, request))
        try:
            start_barcode_generation(
                adda=adda,
                worker_ids=[u.pk for u in form.cleaned_data['workers']],
                user=request.user,
            )
        except (PermissionDenied, ValidationError) as exc:
            messages.error(request, self._service_error(exc))
            return redirect(self.workspace_url(code, request))
        messages.success(request, "Barcode Generation stage started.")
        return redirect(self.workspace_url(code, request))


class BarcodeGenGenerateView(_BarcodeGenActionBase):
    """Trigger BarcodeBatch creation from breakdown. One-shot per stage."""

    def post(self, request, code):
        adda = _get_adda(code)
        try:
            rec = generate_barcodes(adda=adda, user=request.user)
        except (PermissionDenied, ValidationError) as exc:
            messages.error(request, self._service_error(exc))
            return redirect(self.workspace_url(code, request))
        except IntegrityError:
            # Race / re-submit guard — informative message.
            messages.error(request, "Barcodes already exist. Reopen stage to regenerate.")
            return redirect(self.workspace_url(code, request))
        messages.success(
            request, f"Generated {rec.total_barcodes} barcodes.",
        )
        return redirect(self.workspace_url(code, request))


class BarcodeGenCompleteView(_BarcodeGenActionBase):
    """Validate count match + advance. Iframe-safe redirect (same pattern as
    layering/cutting/pattern completions)."""

    def post(self, request, code):
        adda = _get_adda(code)
        # R3 (PDD §27-C3): super-admin override forwarding — validated in service.
        override_reason = (request.POST.get('override_reason', '').strip() or None
                           if request.POST.get('override_pending') else None)
        try:
            complete_barcode_generation(adda=adda, user=request.user,
                                        override_pending_reason=override_reason)
        except (PermissionDenied, ValidationError) as exc:
            messages.error(request, self._service_error(exc))
            return redirect(self.workspace_url(code, request))

        adda.refresh_from_db()
        next_label = (
            adda.current_stage.get_stage_type_display() if adda.current_stage else "completion"
        )
        messages.success(
            request, f"Barcode Generation complete. Advanced to {next_label}.",
        )

        # F-3: gate-free bounce — never the next stage's panel (worker 403).
        if request.POST.get('embedded') == '1':
            return embedded_advance_redirect(adda)
        return redirect('production:adda-detail', code=adda.code)


class BarcodeGenReopenView(_BarcodeGenActionBase):
    """Mgmt unlock — refused if scanned OR exported (service-side guards)."""

    def post(self, request, code):
        adda = _get_adda(code)
        try:
            reopen_barcode_generation(adda=adda, user=request.user)
        except (PermissionDenied, ValidationError) as exc:
            messages.error(request, self._service_error(exc))
            return redirect(self.workspace_url(code, request))
        messages.success(
            request,
            f"Barcode Generation reopened for {adda.code}.",
        )
        if request.POST.get('embedded') == '1':
            return redirect(
                reverse('production:stage-panel', kwargs={
                    'code': adda.code, 'stage_type': STAGE_BARCODE_GENERATION,
                }) + '?embedded=1&advanced=1'
            )
        return redirect('production:adda-detail', code=adda.code)
