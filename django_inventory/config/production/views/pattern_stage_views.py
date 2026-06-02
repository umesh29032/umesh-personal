"""Cutting-pattern stage views — workspace + 6 action handlers.

YEH FILE KYU HAI?
─────────────────
Cutting-pattern stage ka user-facing layer. Service layer ko HTTP se connect
karta hai. Pattern:
   browser POST → view.post() → service function → redirect back

URL TABLE:
  GET  addas/<code>/pattern/                    → workspace (full page)
  POST addas/<code>/pattern/start/              → manager assigns workers
  POST addas/<code>/pattern/save/               → upload/replace video + notes
  POST addas/<code>/pattern/photos/add/         → attach 1+ photos (multipart)
  POST addas/<code>/pattern/photos/<pk>/remove/ → detach photo
  POST addas/<code>/pattern/complete/           → finalize + advance

EMBEDDED MODE:
  Adda detail page workspace ko iframe me embed karta hai
  (`?embedded=1`). Action views check karte hain `request.POST['embedded']`
  → agar set hai to redirect target stage-panel embedded URL hota hai (not
  full workspace). Iframe me iframe na ho jaaye.

SHARED CONTEXT BUILDER:
  `_build_pattern_context` — workspace + StagePanelView ke between context
  share karta hai (DRY). next_stage label, can_assign/upload/complete
  flags, photos list ye sab yahin compute hote hain.
"""
from __future__ import annotations

from django import forms
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View
from django.views.generic import TemplateView

from accounts.skills import (
    SKILL_CUTTING_MASTER, SKILL_CUTTING_MASTER_HELPER, user_has_skill,
)
from inventory.services import MANAGEMENT_ROLES, user_has_role
from production.constants import STAGE_CUTTING_PATTERN
from production.forms import PatternVerifyForm
from production.models import (
    Adda, AddaStageRecord, CuttingPatternPhoto, ProductPatternAssignment,
    WorkflowStage,
)
from production.services import (
    attach_pattern_photo, complete_pattern_stage, ensure_pattern_record,
    get_or_create_pattern_stage_record, reopen_pattern_stage,
    save_pattern_record, set_size_allocation, start_pattern_stage,
    unverify_pattern, verify_pattern,
)

from .mixins import ProductionRoleMixin, StageViewAccessMixin


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
    """Start-stage form — manager workers select karta hai.

    queryset __init__ mein set kyu hota hai (class body mein nahi)?
    Class body Django startup pe execute hoti hai — us waqt DB ready
    nahi hoti. Lazy init via __init__ safer hai.
    """

    workers = forms.ModelMultipleChoiceField(
        queryset=None,  # __init__ mein set
        required=True,
        widget=forms.CheckboxSelectMultiple,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # get_user_model() = lazy User reference; settings.AUTH_USER_MODEL ko
        # honor karta hai (custom User model project me hai).
        from django.contrib.auth import get_user_model
        User = get_user_model()
        # Eligible workers = cutting_master ya cutting_master_helper skill
        # wale users. distinct() M2M JOIN ke duplicates remove karta hai.
        self.fields['workers'].queryset = (
            User.objects.filter(
                skills__name__in=[SKILL_CUTTING_MASTER, SKILL_CUTTING_MASTER_HELPER]
            ).distinct().order_by('email')
        )


def _build_pattern_context(request, adda: Adda) -> dict:
    """Workspace + embedded panel ke beech common context dictionary banaye.

    Yeh function DRY ka kaam karta hai: same template (`_stage_panel_
    cutting_pattern.html`) full-page workspace + iframe me reuse hota hai.
    Dono jagah same context chahiye.

    Computes:
      • stage_record (or None)              → workers, completed_at status
      • record (CuttingPatternRecord)       → video + notes
      • photos (list)                       → photo grid render karne ke liye
      • assignments (ProductPatternAssignment list) → Section 01 checklist
      • can_assign / can_upload / can_complete flags → button visibility
      • next_stage                          → Complete button label
      • start_form                          → Section 02 form (management only)
    """
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

    # Verification map: {assignment_id: CuttingPatternVerification}
    # Template loop uses `verifications_by_assignment.<a.id>` lookup pattern
    # via `default_if_none`. assignment_id ko string key bana kar dict mein.
    verifications_by_assignment: dict = {}
    if record:
        for v in record.verifications.select_related('verified_by', 'photo').all():
            verifications_by_assignment[v.assignment_id] = v

    # Assignment list with attached verification (for easier template render).
    # Each row gets a `.verification` attribute monkey-patched (cheap).
    for a in assignments:
        a.verification = verifications_by_assignment.get(a.id)

    # Size allocations on this record. Sum may differ from 100 mid-edit.
    allocations = list(record.size_allocations.select_related('size').all()) if record else []
    allocation_sum = sum(a.proportion_pct for a in allocations)
    # Available sizes on this product (for picker). Filtered to active only.
    product_sizes = list(
        adda.product.sizes.filter(is_active=True).order_by('display_order', 'code')
    )
    allocated_size_ids = {a.size_id for a in allocations}

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
    # Verify + size allocation = same skill scope as upload (master/helper or mgmt).
    can_verify = can_upload
    can_set_sizes = can_upload
    # Management-only reopen on the completed-state panel.
    can_reopen = is_management and sr is not None and sr.completed_at is not None

    # Next stage label for the complete button.
    next_stage = None
    if adda.current_stage is not None:
        next_stage = (
            adda.product.workflow_stages
            .filter(order__gt=adda.current_stage.order)
            .order_by('order').first()
        )

    verified_count = len(verifications_by_assignment)
    expected_count = len(assignments)

    return {
        'adda': adda,
        'stage_record': sr,
        'workflow_stage': wf,
        'record': record,
        'photos': photos,
        'assignments': assignments,
        'verifications_by_assignment': verifications_by_assignment,
        'verified_count': verified_count,
        'expected_pattern_count': expected_count,
        'allocations': allocations,
        'allocation_sum': allocation_sum,
        'product_sizes': product_sizes,
        'allocated_size_ids': allocated_size_ids,
        'is_management': is_management,
        'can_assign': can_assign,
        'can_upload': can_upload,
        'can_verify': can_verify,
        'can_set_sizes': can_set_sizes,
        'can_complete': can_complete,
        'can_reopen': can_reopen,
        'next_stage': next_stage,
        'start_form': PatternStartForm(initial={
            'workers': list(sr.workers.values_list('pk', flat=True)) if sr else [],
        }) if can_assign else None,
    }


class PatternWorkspaceView(LoginRequiredMixin, ProductionRoleMixin,
                           StageViewAccessMixin, TemplateView):
    stage_code = 'cutting_pattern'         # skill-gate the VIEW, not just actions
    template_name = 'production/pattern_workspace.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(_build_pattern_context(self.request, _get_adda(self.kwargs['code'])))
        return ctx


# ── Action views ────────────────────────────────────────────────────────────


class _PatternActionBase(LoginRequiredMixin, ProductionRoleMixin, View):
    """Saari pattern action views ka base — common helpers.

    LoginRequiredMixin   → unauthenticated user /app/ pe redirect
    ProductionRoleMixin  → 403 agar user PRODUCTION_ROLES me nahi
    http_method_names    → sirf POST allowed (GET disabled)

    Helpers:
      • workspace_url    → redirect target compute (embedded vs standalone)
      • _service_error   → ValidationError ki messages list ko flat string banaye
    """

    http_method_names = ['post']

    def workspace_url(self, code: str, request=None) -> str:
        """Redirect ke baad kahan jaaye:
          • embedded=1 POST       → stage-panel embedded URL (iframe ke andar)
          • normal POST           → pattern-workspace standalone page
        """
        if request is not None and request.POST.get('embedded') == '1':
            return reverse('production:stage-panel', kwargs={
                'code': code, 'stage_type': STAGE_CUTTING_PATTERN,
            }) + '?embedded=1'
        return reverse('production:pattern-workspace', kwargs={'code': code})

    def _service_error(self, exc) -> str:
        """Service layer ValidationError ki list ko flat string banaye —
        messages.error() string accept karta hai (not list).
        """
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
        is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
        video = request.FILES.get('video')
        notes = request.POST.get('notes', '')
        if video is None and not (notes or '').strip():
            if is_ajax:
                return HttpResponse("Nothing to save.", status=400)
            messages.error(request, "Pick a video file or write notes.")
            return redirect(self.workspace_url(code, request))
        try:
            save_pattern_record(adda=adda, video_file=video, notes=notes, user=request.user)
        except (PermissionDenied, ValidationError) as exc:
            if is_ajax:
                return HttpResponse(self._service_error(exc), status=400)
            messages.error(request, self._service_error(exc))
            return redirect(self.workspace_url(code, request))
        if is_ajax:
            return HttpResponse(status=204)   # debounced notes auto-save
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


class PatternReopenView(_PatternActionBase):
    """Management-only: unlock a completed Cutting Pattern stage for correction.

    Mirror of LayeringReopenView. On embedded reopen, redirect to the pattern
    stage's embedded panel with ?advanced=1 so parent reloads.
    """

    def post(self, request, code):
        adda = _get_adda(code)
        try:
            reopen_pattern_stage(adda=adda, user=request.user)
        except (PermissionDenied, ValidationError) as exc:
            messages.error(request, self._service_error(exc))
            return redirect(self.workspace_url(code, request))
        messages.success(
            request,
            f"Cutting Pattern reopened for {adda.code}. Make corrections then Complete again.",
        )
        if request.POST.get('embedded') == '1':
            return redirect(
                reverse('production:stage-panel', kwargs={
                    'code': adda.code, 'stage_type': STAGE_CUTTING_PATTERN,
                }) + '?embedded=1&advanced=1'
            )
        return redirect('production:adda-detail', code=adda.code)


class PatternVerifyView(_PatternActionBase):
    """Pattern assignment verify karna — toggle ON.

    POST data:
      assignment_id (required), photo_id (optional), note (optional)
    """

    def post(self, request, code):
        adda = _get_adda(code)
        try:
            sr = get_or_create_pattern_stage_record(adda, request.user)
            record = ensure_pattern_record(stage_record=sr, user=request.user)
        except (PermissionDenied, ValidationError) as exc:
            messages.error(request, self._service_error(exc))
            return redirect(self.workspace_url(code, request))

        form = PatternVerifyForm(request.POST, record=record)
        if not form.is_valid():
            messages.error(request, "Invalid verification payload.")
            return redirect(self.workspace_url(code, request))
        try:
            verify_pattern(
                record=record,
                assignment=form.cleaned_data['assignment'],
                photo=form.cleaned_data.get('photo'),
                note=form.cleaned_data.get('note', ''),
                user=request.user,
            )
        except (PermissionDenied, ValidationError) as exc:
            messages.error(request, self._service_error(exc))
            return redirect(self.workspace_url(code, request))
        messages.success(request, "Pattern verified.")
        return redirect(self.workspace_url(code, request))


class PatternUnverifyView(_PatternActionBase):
    """Pattern assignment ki verification hatao — toggle OFF.

    POST data: assignment_id
    """

    def post(self, request, code):
        adda = _get_adda(code)
        sr = _get_pattern_stage_record(adda)
        if sr is None:
            messages.error(request, "Stage not started.")
            return redirect(self.workspace_url(code, request))
        record = getattr(sr, 'cutting_pattern', None)
        if record is None:
            messages.error(request, "Nothing to unverify yet.")
            return redirect(self.workspace_url(code, request))
        try:
            assignment_id = int(request.POST.get('assignment_id') or 0)
        except (TypeError, ValueError):
            assignment_id = 0
        if assignment_id <= 0:
            messages.error(request, "Missing assignment id.")
            return redirect(self.workspace_url(code, request))
        try:
            assignment = ProductPatternAssignment.objects.get(
                pk=assignment_id, product=adda.product,
            )
        except ProductPatternAssignment.DoesNotExist:
            messages.error(request, "Pattern not configured on this product.")
            return redirect(self.workspace_url(code, request))
        try:
            unverify_pattern(record=record, assignment=assignment, user=request.user)
        except (PermissionDenied, ValidationError) as exc:
            messages.error(request, self._service_error(exc))
            return redirect(self.workspace_url(code, request))
        messages.success(request, "Verification removed.")
        return redirect(self.workspace_url(code, request))


class PatternSetSizesView(_PatternActionBase):
    """Size allocations full-replace.

    POST data (multi-row):
      size_id  → list of ints (`size_id` multiple values)
      proportion_pct → parallel list of ints

    HTML form sends both lists same length. Sum != 100 OK at draft;
    complete_pattern_stage enforces sum=100.
    """

    def post(self, request, code):
        adda = _get_adda(code)
        try:
            sr = get_or_create_pattern_stage_record(adda, request.user)
            record = ensure_pattern_record(stage_record=sr, user=request.user)
        except (PermissionDenied, ValidationError) as exc:
            messages.error(request, self._service_error(exc))
            return redirect(self.workspace_url(code, request))

        size_ids = request.POST.getlist('size_id')
        pcts = request.POST.getlist('proportion_pct')
        if len(size_ids) != len(pcts):
            messages.error(request, "Size/proportion mismatch in form.")
            return redirect(self.workspace_url(code, request))

        allocations: list[dict] = []
        for sid, p in zip(size_ids, pcts):
            try:
                allocations.append({
                    'size_id': int(sid),
                    'proportion_pct': int(p),
                })
            except (TypeError, ValueError):
                messages.error(request, "Invalid number in size allocations.")
                return redirect(self.workspace_url(code, request))

        try:
            set_size_allocation(
                record=record, allocations=allocations, user=request.user,
            )
        except (PermissionDenied, ValidationError) as exc:
            messages.error(request, self._service_error(exc))
            return redirect(self.workspace_url(code, request))
        messages.success(request, "Size proportions saved.")
        return redirect(self.workspace_url(code, request))


class PatternCompleteView(_PatternActionBase):
    """Stage finalize karke agle stage pe advance.

    IFRAME-SAFE FLOW (important):
      Agar embedded iframe se call ho, redirect target = NEW current stage
      ka embedded panel + `?advanced=1` query flag. Embedded panel ka JS
      yeh flag detect karke parent ko postMessage `stage-advanced` bhejta
      hai. Parent (adda_detail/user_dashboard) listen karke
      `window.location.reload()` chala deta hai — fresh pipeline state
      dikhe.

      Yeh kyun zaroori? Django ka default X-Frame-Options DENY hota hai.
      Iframe ke andar full adda-detail load karna "refused to connect"
      error de deta tha (2026-05-28 bug).
    """

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
