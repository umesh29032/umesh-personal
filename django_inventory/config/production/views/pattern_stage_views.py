"""Cutting-pattern stage views — workspace + actions.

URLs:
  GET  addas/<code>/pattern/                   → workspace (full page)
  POST addas/<code>/pattern/start/             → start stage (manager)
  POST addas/<code>/pattern/save/              → upload/replace video + notes
  POST addas/<code>/pattern/photos/add/        → attach photo (multipart)
  POST addas/<code>/pattern/photos/<pk>/remove/→ detach photo
  POST addas/<code>/pattern/complete/          → finalize + advance

Embedded mode (?embedded=1) returns to the stage-panel iframe URL after POST.
"""
from __future__ import annotations

from django import forms
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.generic import TemplateView

from accounts.skills import (
    SKILL_CUTTING_MASTER, SKILL_CUTTING_MASTER_HELPER, user_has_skill,
)
from inventory.services import MANAGEMENT_ROLES, user_has_role
from production.constants import STAGE_CUTTING_PATTERN
from production.models import (
    Adda, AddaStageRecord, CuttingPatternPhoto, WorkflowStage,
)
from production.services import (
    attach_pattern_photo, complete_pattern_stage,
    get_or_create_pattern_stage_record, save_pattern_record, start_pattern_stage,
)

from .mixins import ProductionRoleMixin


def _get_adda(code: str) -> Adda:
    return get_object_or_404(Adda, code=code)


def _get_pattern_workflow_stage(adda: Adda) -> WorkflowStage | None:
    return adda.product.workflow_stages.filter(stage__code=STAGE_CUTTING_PATTERN).first()


def _get_pattern_stage_record(adda: Adda) -> AddaStageRecord | None:
    wf = _get_pattern_workflow_stage(adda)
    if wf is None:
        return None
    return AddaStageRecord.objects.filter(adda=adda, workflow_stage=wf).first()


class PatternStartForm(forms.Form):
    workers = forms.ModelMultipleChoiceField(
        queryset=None,  # set in __init__
        required=True,
        widget=forms.CheckboxSelectMultiple,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from django.contrib.auth import get_user_model
        User = get_user_model()
        # Anyone with cutting_master / helper skill is eligible.
        self.fields['workers'].queryset = (
            User.objects.filter(
                skills__name__in=[SKILL_CUTTING_MASTER, SKILL_CUTTING_MASTER_HELPER]
            ).distinct().order_by('email')
        )


def _build_pattern_context(request, adda: Adda) -> dict:
    """Shared context for both standalone workspace + iframe-embedded panel."""
    user = request.user
    sr = _get_pattern_stage_record(adda)
    wf = _get_pattern_workflow_stage(adda)
    record = getattr(sr, 'cutting_pattern', None) if sr else None
    photos = list(record.photos.select_related('uploaded_by').all()) if record else []
    assignments = list(
        adda.product.pattern_assignments
        .select_related('pattern')
        .order_by('pattern__name')
    )

    is_management = user_has_role(user, MANAGEMENT_ROLES)
    has_master_skill = user_has_skill(
        user, [SKILL_CUTTING_MASTER, SKILL_CUTTING_MASTER_HELPER],
    )
    has_helper_skill = user_has_skill(user, SKILL_CUTTING_MASTER_HELPER)

    can_assign = is_management
    is_assigned = bool(sr and sr.workers.filter(pk=user.pk).exists())
    can_upload = sr is not None and sr.completed_at is None and (
        is_management or (is_assigned and has_master_skill)
    )
    can_complete = sr is not None and sr.completed_at is None and (
        is_management or has_helper_skill
    )

    # Next stage label for the complete button.
    next_stage = None
    if adda.current_stage is not None:
        next_stage = (
            adda.product.workflow_stages
            .filter(order__gt=adda.current_stage.order)
            .order_by('order').first()
        )

    return {
        'adda': adda,
        'stage_record': sr,
        'workflow_stage': wf,
        'record': record,
        'photos': photos,
        'assignments': assignments,
        'is_management': is_management,
        'can_assign': can_assign,
        'can_upload': can_upload,
        'can_complete': can_complete,
        'next_stage': next_stage,
        'start_form': PatternStartForm(initial={
            'workers': list(sr.workers.values_list('pk', flat=True)) if sr else [],
        }) if can_assign else None,
    }


class PatternWorkspaceView(LoginRequiredMixin, ProductionRoleMixin, TemplateView):
    template_name = 'production/pattern_workspace.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(_build_pattern_context(self.request, _get_adda(self.kwargs['code'])))
        return ctx


# ── Action views ────────────────────────────────────────────────────────────


class _PatternActionBase(LoginRequiredMixin, ProductionRoleMixin, View):
    http_method_names = ['post']

    def workspace_url(self, code: str, request=None) -> str:
        if request is not None and request.POST.get('embedded') == '1':
            return reverse('production:stage-panel', kwargs={
                'code': code, 'stage_type': STAGE_CUTTING_PATTERN,
            }) + '?embedded=1'
        return reverse('production:pattern-workspace', kwargs={'code': code})

    def _service_error(self, exc) -> str:
        msg = getattr(exc, 'messages', None)
        return ' '.join(msg) if msg else str(exc)


class PatternStartView(_PatternActionBase):
    def post(self, request, code):
        adda = _get_adda(code)
        form = PatternStartForm(request.POST)
        if not form.is_valid():
            messages.error(request, "Select at least one worker.")
            return redirect(self.workspace_url(code, request))
        try:
            start_pattern_stage(
                adda=adda,
                worker_ids=[u.pk for u in form.cleaned_data['workers']],
                user=request.user,
            )
        except (PermissionDenied, ValidationError) as exc:
            messages.error(request, self._service_error(exc))
            return redirect(self.workspace_url(code, request))
        messages.success(request, "Cutting-pattern stage started.")
        return redirect(self.workspace_url(code, request))


class PatternSaveVideoView(_PatternActionBase):
    """Upload (or replace) the pattern video + notes. Video is optional —
    a master can submit notes alone or skip video entirely. Photos route to
    PatternAddPhotoView instead."""

    def post(self, request, code):
        adda = _get_adda(code)
        video = request.FILES.get('video')
        notes = request.POST.get('notes', '')
        if video is None and not (notes or '').strip():
            messages.error(request, "Pick a video file or write notes.")
            return redirect(self.workspace_url(code, request))
        try:
            save_pattern_record(adda=adda, video_file=video, notes=notes, user=request.user)
        except (PermissionDenied, ValidationError) as exc:
            messages.error(request, self._service_error(exc))
            return redirect(self.workspace_url(code, request))
        messages.success(request, "Saved.")
        return redirect(self.workspace_url(code, request))


class PatternAddPhotoView(_PatternActionBase):
    """Upload one or more photos (multipart, name='photos' multiple).

    Service lazily bootstraps the CuttingPatternRecord — no video pre-req.
    """

    def post(self, request, code):
        adda = _get_adda(code)
        # Make sure the stage record exists (bootstraps if it doesn't) so the
        # photo attach has a parent FK target.
        from production.services import get_or_create_pattern_stage_record
        try:
            sr = get_or_create_pattern_stage_record(adda, request.user)
        except (PermissionDenied, ValidationError) as exc:
            messages.error(request, self._service_error(exc))
            return redirect(self.workspace_url(code, request))

        files = request.FILES.getlist('photos')
        caption = request.POST.get('caption', '')
        if not files:
            messages.error(request, "Pick at least one photo.")
            return redirect(self.workspace_url(code, request))
        added = 0
        for f in files:
            try:
                attach_pattern_photo(
                    stage_record=sr, uploaded_image=f, caption=caption,
                    user=request.user,
                )
                added += 1
            except (PermissionDenied, ValidationError) as exc:
                messages.error(request, self._service_error(exc))
                return redirect(self.workspace_url(code, request))
        messages.success(request, f"{added} photo{'s' if added != 1 else ''} added.")
        return redirect(self.workspace_url(code, request))


class PatternRemovePhotoView(_PatternActionBase):
    def post(self, request, code, pk):
        adda = _get_adda(code)
        photo = get_object_or_404(
            CuttingPatternPhoto.objects.select_related('record__stage_record__adda'),
            pk=pk, record__stage_record__adda=adda,
        )
        # Permission: anyone who can upload can remove (workers + management).
        # Once stage completed, removal locked.
        if photo.record.stage_record.completed_at is not None:
            messages.error(request, "Stage already completed — photos locked.")
            return redirect(self.workspace_url(code, request))
        if not user_has_role(request.user, MANAGEMENT_ROLES) and photo.uploaded_by_id != request.user.pk:
            messages.error(request, "Only the uploader or management can remove a photo.")
            return redirect(self.workspace_url(code, request))
        # Delete the file from storage too.
        try:
            photo.image.delete(save=False)
        except Exception:
            pass
        photo.delete()
        messages.success(request, "Photo removed.")
        return redirect(self.workspace_url(code, request))


class PatternCompleteView(_PatternActionBase):
    def post(self, request, code):
        adda = _get_adda(code)
        try:
            complete_pattern_stage(adda=adda, user=request.user)
        except (PermissionDenied, ValidationError) as exc:
            messages.error(request, self._service_error(exc))
            return redirect(self.workspace_url(code, request))

        adda.refresh_from_db()
        next_label = (
            adda.current_stage.get_stage_type_display() if adda.current_stage else "completion"
        )
        messages.success(request, f"Pattern stage complete. Advanced to {next_label}.")

        # Same iframe-safe redirect pattern as Layering: if embedded, route to
        # the new current stage's embedded panel with ?advanced=1 so the
        # embedded JS pings parent to reload.
        if request.POST.get('embedded') == '1' and adda.current_stage is not None:
            return redirect(
                reverse('production:stage-panel', kwargs={
                    'code': adda.code,
                    'stage_type': adda.current_stage.stage_type,
                }) + '?embedded=1&advanced=1'
            )
        return redirect('production:adda-detail', code=adda.code)
