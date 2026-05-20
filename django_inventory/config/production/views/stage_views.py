"""Stage views — Layering workspace + Cutting completion.

YEH FILE KYU HAI?
─────────────────
Layering workflow ke saare HTTP entry points yahan hain. Saara business logic
production.services.stage_service mein hai — views sirf:
  1. Form render karna
  2. POST validate karna
  3. Service call karna
  4. Success/error message + redirect

Layering URL structure:
  GET  addas/<code>/layering/                  → workspace (assign workers, attach rolls, complete)
  POST addas/<code>/layering/start/            → assign workers
  POST addas/<code>/layering/attach-roll/      → add a roll with verified width/weight
  POST addas/<code>/layering/entries/<pk>/     → edit a roll entry (width/weight/notes)
  POST addas/<code>/layering/entries/<pk>/remove/  → detach a roll
  POST addas/<code>/layering/complete/         → finalize → advance to Cutting

Cutting URL: addas/<code>/cutting/  (single submit, unchanged)
"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.generic import FormView, TemplateView

from accounts.skills import (
    SKILL_CUTTING_MASTER, SKILL_CUTTING_MASTER_HELPER, user_has_skill,
)
from inventory.services import MANAGEMENT_ROLES, user_has_role
from production.forms import (
    AttachRollForm, CompleteLayeringForm, CuttingForm,
    EditRollEntryForm, StartLayeringForm,
)
from production.models import (
    Adda, AddaStageRecord, LayeringRollEntry,
    RemainingClothOfClothRoll, WorkflowStage,
)
from production.services import (
    attach_roll_to_layering, complete_cutting, complete_layering,
    detach_roll_from_layering, remove_remaining_cloth,
    save_layering_draft, start_layering,
    update_layering_roll_entry,
)
from raw_materials.models import ClothRoll

from .mixins import ProductionRoleMixin


# ── Helpers ──────────────────────────────────────────────────────────────────


def _get_adda(code: str) -> Adda:
    return get_object_or_404(Adda, code=code)


def _get_layering_stage_record(adda: Adda) -> AddaStageRecord | None:
    """Adda ki Layering stage ka record return karta hai (yet started ho to)."""
    stage = adda.product.workflow_stages.filter(
        stage_type=WorkflowStage.StageType.LAYERING
    ).first()
    if stage is None:
        return None
    return AddaStageRecord.objects.filter(adda=adda, workflow_stage=stage).first()


def _available_rolls_qs(*, color_id: int | None = None,
                        type_id: int | None = None,
                        width: int | None = None):
    """Layering picker ka roll source — sirf NOT_USED rolls + optional filters.

    Filters cascade by AND. Empty values are ignored.
      • color_id = ClothColor pk
      • type_id  = ClothType pk
      • width    = width_inch integer
    """
    qs = (
        ClothRoll.objects.filter(status=ClothRoll.Status.NOT_USED)
        .select_related('cloth_type', 'cloth_color', 'storage_location')
        .order_by('-created_at')
    )
    if color_id:
        qs = qs.filter(cloth_color_id=color_id)
    if type_id:
        qs = qs.filter(cloth_type_id=type_id)
    if width:
        qs = qs.filter(width_inch=width)
    return qs


def _parse_int_param(request, key: str) -> int | None:
    """Safe int param parse — empty / non-numeric → None."""
    raw = request.GET.get(key) or ''
    raw = raw.strip()
    if not raw:
        return None
    try:
        return int(raw)
    except (ValueError, TypeError):
        return None


# ── Layering workspace (GET) ─────────────────────────────────────────────────


def _build_layering_context(request, adda: Adda) -> dict:
    """Shared layering panel context — used by workspace + StagePanelView + dashboard accordion.

    Returns the context dict the layering partial template expects. Permission
    flags (`can_assign`, `can_attach`, `can_complete`) drive UI gating; matched
    by service-side guards (defence-in-depth).

    GET filter params (?fc=, ?ft=, ?fw=) narrow the roll picker queryset and are
    surfaced back to the template so dropdowns retain their selection on reload.
    """
    sr = _get_layering_stage_record(adda)
    user = request.user
    filter_color = _parse_int_param(request, 'fc')
    filter_type = _parse_int_param(request, 'ft')
    filter_width = _parse_int_param(request, 'fw')

    is_management = user_has_role(user, MANAGEMENT_ROLES)
    is_assigned = bool(sr and sr.workers.filter(pk=user.pk).exists())
    has_master_skill = user_has_skill(
        user, [SKILL_CUTTING_MASTER, SKILL_CUTTING_MASTER_HELPER]
    )
    has_helper_skill = user_has_skill(user, SKILL_CUTTING_MASTER_HELPER)

    can_assign = is_management
    can_attach = sr is not None and sr.completed_at is None and (
        is_management or (is_assigned and has_master_skill)
    )
    # Anyone who can attach can also Save Draft — draft = same surface as attach,
    # just persists Section 04 inputs. Complete remains strict helper-skill gate.
    can_draft = can_attach
    can_complete = sr is not None and sr.completed_at is None and (
        user.is_superuser or has_helper_skill
    )

    entries = (
        sr.layering_roll_entries
        .select_related('roll', 'roll__cloth_type', 'roll__cloth_color', 'attached_by')
        .prefetch_related('remaining_pieces')   # per-entry leftover list (no N+1)
        .order_by('attached_at')
        if sr else []
    )
    total_weight = sum((e.weight_verified_kg or 0) for e in entries)
    distinct_colors = {e.roll.cloth_color_id for e in entries} if sr else set()

    # Filtered roll queryset — drives the attach picker AND the "no match" detection
    # that toggles the inline "Create new roll" panel.
    filtered_rolls = (
        _available_rolls_qs(
            color_id=filter_color, type_id=filter_type, width=filter_width,
        )
        if can_attach else ClothRoll.objects.none()
    )
    has_filter_active = bool(filter_color or filter_type or filter_width)

    # Master data for filter dropdowns + quick-create form pre-fill
    from raw_materials.models import ClothColor, ClothType, StorageLocation
    from inventory.services import user_can_edit_financials
    cloth_colors = ClothColor.objects.filter(is_active=True).order_by('name')
    cloth_types = ClothType.objects.filter(is_active=True).order_by('name')
    storage_locations = StorageLocation.objects.filter(is_active=True).order_by('name')
    width_choices = list(range(36, 45))
    can_edit_financials = user_can_edit_financials(user)

    return {
        'adda': adda,
        'stage_record': sr,
        'entries': entries,
        'total_weight': total_weight,
        'distinct_colors_count': len(distinct_colors),
        'roll_ids': [e.roll.roll_id for e in entries],
        'available_rolls_qs': filtered_rolls,
        'start_form': StartLayeringForm(initial={
            'workers': list(sr.workers.values_list('pk', flat=True)) if sr else [],
        }) if can_assign else None,
        'attach_form': AttachRollForm(available_rolls_qs=filtered_rolls) if can_attach else None,
        # Section 04 form rendered for anyone who can draft (= anyone who can attach).
        # Pre-populated from stage_record.draft_* fields persisted by save_layering_draft.
        'complete_form': CompleteLayeringForm(initial={
            'layer_length_meters': sr.draft_layer_length_meters if sr else None,
            'duration_minutes': sr.draft_duration_minutes if sr else None,
            'notes': sr.draft_notes if sr else '',
        }) if can_draft else None,
        'can_assign': can_assign,
        'can_attach': can_attach,
        'can_draft': can_draft,
        'can_complete': can_complete,
        'stages': adda.product.workflow_stages.order_by('order'),
        # Filter state — template uses to preselect dropdowns + toggle "no match" UX
        'filter_color': filter_color,
        'filter_type': filter_type,
        'filter_width': filter_width,
        'has_filter_active': has_filter_active,
        'filtered_rolls_count': filtered_rolls.count() if can_attach else 0,
        # Filter dropdown options + quick-create form sources
        'cloth_colors': cloth_colors,
        'cloth_types': cloth_types,
        'storage_locations': storage_locations,
        'width_choices': width_choices,
        'can_edit_financials': can_edit_financials,
    }


class LayeringWorkspaceView(LoginRequiredMixin, ProductionRoleMixin, TemplateView):
    """Full-page layering workspace (with nav + hero). Standalone entry point."""

    template_name = 'production/layering_workspace.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        adda = _get_adda(self.kwargs['code'])
        ctx.update(_build_layering_context(self.request, adda))
        return ctx


@method_decorator(xframe_options_sameorigin, name='dispatch')
class StagePanelView(LoginRequiredMixin, ProductionRoleMixin, TemplateView):
    """Per-stage panel — canonical URL for iframe embed + standalone view.

    `?embedded=1` strips chrome (hero/nav) so panel fits inside iframe.
    Picks layering or cutting partial based on `stage_type` URL kwarg.

    @xframe_options_sameorigin: Django's default X-Frame-Options is `DENY` which
    blocks the iframe in adda_detail / user_dashboard from loading this URL. We
    explicitly downgrade to SAMEORIGIN for this view so same-origin iframes work.
    """

    def get_template_names(self):
        # Embedded = no base template chrome; standalone = full page
        if self.request.GET.get('embedded') == '1':
            return ['production/stage_panel_embedded.html']
        return ['production/stage_panel_standalone.html']

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        adda = _get_adda(self.kwargs['code'])
        stage_type = self.kwargs['stage_type']
        ctx['adda'] = adda
        ctx['stage_type'] = stage_type
        ctx['embedded'] = self.request.GET.get('embedded') == '1'
        if stage_type == WorkflowStage.StageType.LAYERING:
            ctx.update(_build_layering_context(self.request, adda))
        elif stage_type == WorkflowStage.StageType.CUTTING:
            # Cutting needs current Adda + management gate + CuttingForm
            ctx['cutting_form'] = CuttingForm()
            ctx['can_complete_cutting'] = (
                user_has_role(self.request.user, MANAGEMENT_ROLES)
                and adda.current_stage is not None
                and adda.current_stage.stage_type == WorkflowStage.StageType.CUTTING
            )
        return ctx


# ── Action views (POST only) ────────────────────────────────────────────────


class _LayeringActionBase(LoginRequiredMixin, ProductionRoleMixin, View):
    """Shared base — workspace URL build + standard service-error to messages funnel.

    Embedded mode: forms set hidden `embedded=1` input. We honor it on redirect
    so iframe / accordion content keeps showing the embedded panel after POST
    instead of jumping out to the full workspace page.
    """

    http_method_names = ['post']

    def workspace_url(self, code: str, request=None) -> str:
        """Redirect target — stage-panel embedded if request came from iframe, else full workspace."""
        if request is not None and request.POST.get('embedded') == '1':
            return reverse('production:stage-panel', kwargs={
                'code': code, 'stage_type': 'layering',
            }) + '?embedded=1'
        return reverse('production:layering-workspace', kwargs={'code': code})

    def _service_error(self, exc) -> str:
        # ValidationError aata hai list mein kabhi-kabhi — get a flat string
        msg = getattr(exc, 'messages', None)
        return ' '.join(msg) if msg else str(exc)


class LayeringStartView(_LayeringActionBase):
    """Manager assigns workers → start Layering stage."""

    def post(self, request, code):
        adda = _get_adda(code)
        form = StartLayeringForm(request.POST)
        if not form.is_valid():
            messages.error(request, "Select at least one worker.")
            return redirect(self.workspace_url(code, request))
        try:
            start_layering(
                adda=adda,
                worker_ids=[u.pk for u in form.cleaned_data['workers']],
                user=request.user,
            )
        except (PermissionDenied, ValidationError) as exc:
            messages.error(request, self._service_error(exc))
            return redirect(self.workspace_url(code, request))
        messages.success(request, "Layering stage started — workers assigned.")
        return redirect(self.workspace_url(code, request))


class LayeringAttachRollView(_LayeringActionBase):
    """Assigned worker attaches a cloth roll with verified width/weight."""

    def post(self, request, code):
        adda = _get_adda(code)
        sr = _get_layering_stage_record(adda)
        if sr is None:
            messages.error(request, "Start the Layering stage first.")
            return redirect(self.workspace_url(code, request))
        form = AttachRollForm(request.POST, available_rolls_qs=_available_rolls_qs())
        if not form.is_valid():
            errs = '; '.join(f"{f}: {e[0]}" for f, e in form.errors.items())
            messages.error(request, f"Fix the entries: {errs}")
            return redirect(self.workspace_url(code, request))
        try:
            attach_roll_to_layering(
                stage_record=sr,
                roll=form.cleaned_data['roll'],
                width_verified_inch=form.cleaned_data['width_verified_inch'],
                weight_verified_kg=form.cleaned_data['weight_verified_kg'],
                notes=form.cleaned_data.get('notes', ''),
                user=request.user,
            )
        except (PermissionDenied, ValidationError) as exc:
            messages.error(request, self._service_error(exc))
            return redirect(self.workspace_url(code, request))
        messages.success(request, f"Roll {form.cleaned_data['roll'].roll_id} attached.")
        return redirect(self.workspace_url(code, request))


class LayeringEntryUpdateView(_LayeringActionBase):
    """Edit verified width/weight/notes/layers on an existing LayeringRollEntry.

    Two POST shapes converge here:
      • Full edit (EditRollEntryForm): width + weight + notes from the row's
        Correct/remove details block.
      • Mini per-row save from Section 04 breakup: only `layers_on_roll`.
        Detected when only that key is present.
    """

    def post(self, request, code, pk):
        entry = get_object_or_404(
            LayeringRollEntry.objects.select_related('stage_record__adda', 'roll'),
            pk=pk, stage_record__adda__code=code,
        )
        # Detect per-row layer-save shortcut (only layers_on_roll in POST besides csrf/embedded)
        meaningful_keys = {k for k in request.POST.keys()
                          if k not in {'csrfmiddlewaretoken', 'embedded'}}
        is_layer_save = meaningful_keys == {'layers_on_roll'}

        if is_layer_save:
            raw = (request.POST.get('layers_on_roll') or '').strip()
            try:
                layers = int(raw) if raw else 0
            except (ValueError, TypeError):
                messages.error(request, f"Invalid layer count for {entry.roll.roll_id}.")
                return redirect(self.workspace_url(code, request))
            if layers < 1:
                messages.error(request, "Layer count must be ≥ 1.")
                return redirect(self.workspace_url(code, request))
            try:
                update_layering_roll_entry(
                    entry=entry,
                    width_verified_inch=None,
                    weight_verified_kg=None,
                    notes=None,
                    layers_on_roll=layers,
                    user=request.user,
                )
            except (PermissionDenied, ValidationError) as exc:
                messages.error(request, self._service_error(exc))
                return redirect(self.workspace_url(code, request))
            messages.success(request, f"Saved {layers} layers for {entry.roll.roll_id}.")
            return redirect(self.workspace_url(code, request))

        # Full edit form path
        form = EditRollEntryForm(request.POST)
        if not form.is_valid():
            messages.error(request, "Could not update entry — check the values.")
            return redirect(self.workspace_url(code, request))
        try:
            update_layering_roll_entry(
                entry=entry,
                width_verified_inch=form.cleaned_data.get('width_verified_inch'),
                weight_verified_kg=form.cleaned_data.get('weight_verified_kg'),
                notes=form.cleaned_data.get('notes') or None,
                user=request.user,
            )
        except (PermissionDenied, ValidationError) as exc:
            messages.error(request, self._service_error(exc))
            return redirect(self.workspace_url(code, request))
        messages.success(request, f"Updated entry for {entry.roll.roll_id}.")
        return redirect(self.workspace_url(code, request))


class LayeringEntryRemoveView(_LayeringActionBase):
    """Detach a roll — entry deleted, ClothRoll back to NOT_USED."""

    def post(self, request, code, pk):
        entry = get_object_or_404(
            LayeringRollEntry.objects.select_related('stage_record__adda', 'roll'),
            pk=pk, stage_record__adda__code=code,
        )
        roll_id = entry.roll.roll_id
        try:
            detach_roll_from_layering(entry=entry, user=request.user)
        except (PermissionDenied, ValidationError) as exc:
            messages.error(request, self._service_error(exc))
            return redirect(self.workspace_url(code, request))
        messages.success(request, f"Roll {roll_id} detached.")
        return redirect(self.workspace_url(code, request))


class LayeringRemoveRemainingClothView(_LayeringActionBase):
    """POST handler — delete a leftover entry (only if not yet consumed)."""

    def post(self, request, code, pk):
        leftover = get_object_or_404(
            RemainingClothOfClothRoll.objects.select_related(
                'layering_entry__stage_record__adda', 'roll',
            ),
            pk=pk, source_adda__code=code,
        )
        try:
            remove_remaining_cloth(leftover=leftover, user=request.user)
        except (PermissionDenied, ValidationError) as exc:
            messages.error(request, self._service_error(exc))
            return redirect(self.workspace_url(code, request))
        messages.success(request, "Leftover entry removed.")
        return redirect(self.workspace_url(code, request))


class LayeringQuickCreateAndAttachView(_LayeringActionBase):
    """Inline 'create new roll + attach to layering' flow.

    Used when assigned worker filters the picker and finds zero matching rolls —
    they enter the missing details and create+attach in one shot. qty hard-coded
    to 1 (per spec). Cloth type + color come from the filter (pre-filled in form).

    Service flow:
      1. bulk_create_rolls(qty=1, color, cloth_type, location, purchased_date) → ClothRoll
      2. attach_roll_to_layering(stage_record, roll, width, weight, ...)
    """

    def post(self, request, code):
        from datetime import date as _date
        from decimal import Decimal, InvalidOperation
        from raw_materials.models import ClothColor, ClothType, StorageLocation
        from raw_materials.services import bulk_create_rolls

        adda = _get_adda(code)
        sr = _get_layering_stage_record(adda)
        if sr is None:
            messages.error(request, "Start the Layering stage first.")
            return redirect(self.workspace_url(code, request))

        # Parse + validate inputs
        try:
            cloth_type = ClothType.objects.get(pk=request.POST.get('cloth_type'), is_active=True)
            cloth_color = ClothColor.objects.get(pk=request.POST.get('cloth_color'), is_active=True)
            location = StorageLocation.objects.get(pk=request.POST.get('storage_location'), is_active=True)
        except (ClothType.DoesNotExist, ClothColor.DoesNotExist, StorageLocation.DoesNotExist):
            messages.error(request, "Pick a valid cloth type, color, and storage location.")
            return redirect(self.workspace_url(code, request))
        try:
            width_inch = int(request.POST.get('width_inch') or 0)
            weight_kg = Decimal(request.POST.get('weight_kg') or '0')
        except (ValueError, InvalidOperation):
            messages.error(request, "Width and weight must be valid numbers.")
            return redirect(self.workspace_url(code, request))
        if width_inch < 1 or weight_kg <= 0:
            messages.error(request, "Width and weight must be > 0.")
            return redirect(self.workspace_url(code, request))

        purchased_raw = (request.POST.get('purchased_date') or '').strip()
        try:
            purchased_date = (
                _date.fromisoformat(purchased_raw) if purchased_raw else _date.today()
            )
        except ValueError:
            messages.error(request, "Purchased date must be YYYY-MM-DD.")
            return redirect(self.workspace_url(code, request))

        # Step 1 — create exactly one roll. financial fields skipped (form omits them).
        try:
            new_rolls = bulk_create_rolls(
                user=request.user,
                cloth_type=cloth_type,
                storage_location=location,
                purchased_date=purchased_date,
                breakup=[{'color': cloth_color, 'qty': 1}],
            )
        except (PermissionDenied, ValidationError) as exc:
            messages.error(request, self._service_error(exc))
            return redirect(self.workspace_url(code, request))

        # Step 2 — immediately attach the newly created roll to this layering
        try:
            attach_roll_to_layering(
                stage_record=sr,
                roll=new_rolls[0],
                width_verified_inch=width_inch,
                weight_verified_kg=weight_kg,
                notes=request.POST.get('notes', '') or '',
                user=request.user,
            )
        except (PermissionDenied, ValidationError) as exc:
            messages.error(request, f"Roll {new_rolls[0].roll_id} created but attach failed: {self._service_error(exc)}")
            return redirect(self.workspace_url(code, request))

        messages.success(request, f"Created + attached new roll {new_rolls[0].roll_id}.")
        return redirect(self.workspace_url(code, request))


class LayeringFullCreateAndAttachView(_LayeringActionBase):
    """Full-intake variant of quick-create — creates 1 roll with FULL details
    (including financial supplier + cost_per_kg) then attaches to layering.

    Used when an uncatalogued physical roll arrives on the floor and needs to
    go into inventory + the active Adda in one step. Single roll only (qty=1).

    POST inputs (vs quick-create):
      + supplier, cost_per_kg   — only honored if user passes finance gate;
                                  bulk_create_rolls service raises PermissionDenied otherwise.

    Backend = same as quick-create: bulk_create_rolls(qty=1) → attach_roll_to_layering.
    """

    def post(self, request, code):
        from datetime import date as _date
        from decimal import Decimal, InvalidOperation
        from raw_materials.models import ClothColor, ClothType, StorageLocation
        from raw_materials.services import bulk_create_rolls

        adda = _get_adda(code)
        sr = _get_layering_stage_record(adda)
        if sr is None:
            messages.error(request, "Start the Layering stage first.")
            return redirect(self.workspace_url(code, request))

        try:
            cloth_type = ClothType.objects.get(pk=request.POST.get('cloth_type'), is_active=True)
            cloth_color = ClothColor.objects.get(pk=request.POST.get('cloth_color'), is_active=True)
            location = StorageLocation.objects.get(pk=request.POST.get('storage_location'), is_active=True)
        except (ClothType.DoesNotExist, ClothColor.DoesNotExist, StorageLocation.DoesNotExist):
            messages.error(request, "Pick a valid cloth type, color, and storage location.")
            return redirect(self.workspace_url(code, request))
        try:
            width_inch = int(request.POST.get('width_inch') or 0)
            weight_kg = Decimal(request.POST.get('weight_kg') or '0')
        except (ValueError, InvalidOperation):
            messages.error(request, "Width and weight must be valid numbers.")
            return redirect(self.workspace_url(code, request))
        if width_inch < 1 or weight_kg <= 0:
            messages.error(request, "Width and weight must be > 0.")
            return redirect(self.workspace_url(code, request))

        purchased_raw = (request.POST.get('purchased_date') or '').strip()
        try:
            purchased_date = _date.fromisoformat(purchased_raw) if purchased_raw else _date.today()
        except ValueError:
            messages.error(request, "Purchased date must be YYYY-MM-DD.")
            return redirect(self.workspace_url(code, request))

        # Financial fields — passed through; service enforces role gate
        supplier = (request.POST.get('supplier') or '').strip()
        cost_raw = (request.POST.get('cost_per_kg') or '').strip()
        cost_per_kg = None
        if cost_raw:
            try:
                cost_per_kg = Decimal(cost_raw)
                if cost_per_kg < 0:
                    raise InvalidOperation('negative')
            except InvalidOperation:
                messages.error(request, "Cost per KG must be a valid non-negative number.")
                return redirect(self.workspace_url(code, request))

        # Step 1 — create one roll with full intake details
        try:
            new_rolls = bulk_create_rolls(
                user=request.user,
                cloth_type=cloth_type,
                storage_location=location,
                purchased_date=purchased_date,
                breakup=[{'color': cloth_color, 'qty': 1}],
                supplier=supplier,
                cost_per_kg=cost_per_kg,
            )
        except (PermissionDenied, ValidationError) as exc:
            messages.error(request, self._service_error(exc))
            return redirect(self.workspace_url(code, request))

        # Step 2 — attach with verified width + weight
        try:
            attach_roll_to_layering(
                stage_record=sr,
                roll=new_rolls[0],
                width_verified_inch=width_inch,
                weight_verified_kg=weight_kg,
                notes=request.POST.get('notes', '') or '',
                user=request.user,
            )
        except (PermissionDenied, ValidationError) as exc:
            messages.error(request, f"Roll {new_rolls[0].roll_id} created but attach failed: {self._service_error(exc)}")
            return redirect(self.workspace_url(code, request))

        messages.success(request, f"Created + attached full-detail roll {new_rolls[0].roll_id}.")
        return redirect(self.workspace_url(code, request))


class LayeringCompleteView(_LayeringActionBase):
    """Single-form Section 04 handler. Two button paths via POST `action` field:
      • action=draft    → save_layering_draft  (lax, no advance)
      • action=complete → complete_layering    (strict, advance)

    POST shape:
      action               'draft' | 'complete'
      layer_length_meters  decimal (optional for draft, required for complete)
      duration_minutes     int     (optional for draft, required for complete)
      notes                str
      entry_<pk>_layers              per LayeringRollEntry
      entry_<pk>_leftover_len        per LayeringRollEntry
      entry_<pk>_leftover_wt         per LayeringRollEntry
    """

    def _parse_per_entry_data(self, request) -> dict[int, dict]:
        """Build {pk: {layers, leftover_length, leftover_weight}} from POST keys."""
        from decimal import Decimal as _D, InvalidOperation
        data: dict[int, dict] = {}
        for key, val in request.POST.items():
            if not key.startswith('entry_'):
                continue
            # Match patterns entry_<pk>_layers / _leftover_len / _leftover_wt
            for suffix, field in (
                ('_layers', 'layers'),
                ('_leftover_len', 'leftover_length'),
                ('_leftover_wt', 'leftover_weight'),
            ):
                if key.endswith(suffix):
                    try:
                        pk = int(key[len('entry_'):-len(suffix)])
                    except (ValueError, TypeError):
                        break
                    raw = (val or '').strip()
                    if not raw:
                        parsed = None
                    elif field == 'layers':
                        try:
                            parsed = int(raw)
                        except (ValueError, TypeError):
                            parsed = None
                    else:
                        try:
                            parsed = _D(raw)
                        except (InvalidOperation, ValueError, TypeError):
                            parsed = None
                    data.setdefault(pk, {})[field] = parsed
                    break
        return data

    def post(self, request, code):
        adda = _get_adda(code)
        action = (request.POST.get('action') or 'draft').strip().lower()
        form = CompleteLayeringForm(request.POST)
        # Form validation is lax (all fields optional on the form). Strict checks
        # only apply on action=complete and are enforced server-side below.
        form.is_valid()
        layer_length = form.cleaned_data.get('layer_length_meters')
        duration = form.cleaned_data.get('duration_minutes')
        notes = form.cleaned_data.get('notes', '')

        per_entry = self._parse_per_entry_data(request)

        # Both actions persist draft state via save_layering_draft so per-row
        # values + header bits are stored before any advance happens.
        per_entry_normalized = {
            pk: data for pk, data in per_entry.items()
        }
        try:
            save_layering_draft(
                adda=adda,
                layer_length_meters=layer_length,
                duration_minutes=duration,
                notes=notes,
                per_entry_data=per_entry_normalized,
                user=request.user,
            )
        except (PermissionDenied, ValidationError) as exc:
            messages.error(request, self._service_error(exc))
            return redirect(self.workspace_url(code, request))

        if action == 'draft':
            messages.success(request, "Draft saved.")
            return redirect(self.workspace_url(code, request))

        # action == 'complete' path — strict validation + advance
        sr = _get_layering_stage_record(adda)
        if sr is None:
            messages.error(request, "Layering stage hasn't been started.")
            return redirect(self.workspace_url(code, request))
        entries = list(
            sr.layering_roll_entries
            .select_related('roll')
            .prefetch_related('remaining_pieces')
            .all()
        )
        if not entries:
            messages.error(request, "Attach at least one cloth roll before completing.")
            return redirect(self.workspace_url(code, request))
        missing_layers = [e for e in entries if not e.layers_on_roll]
        missing_leftover = [e for e in entries if not e.remaining_pieces.all()]
        if missing_layers or missing_leftover:
            bits = []
            if missing_layers:
                bits.append("layer count: " + ', '.join(e.roll.roll_id for e in missing_layers))
            if missing_leftover:
                bits.append("leftover: " + ', '.join(e.roll.roll_id for e in missing_leftover))
            messages.error(
                request,
                "Fill the breakup for every roll before completing. Missing — " + " · ".join(bits),
            )
            return redirect(self.workspace_url(code, request))

        per_entry_layers = {e.pk: e.layers_on_roll for e in entries}
        try:
            complete_layering(
                adda=adda,
                duration_minutes=duration,
                layer_length_meters=layer_length,
                per_entry_layers=per_entry_layers,
                notes=notes,
                user=request.user,
            )
        except (PermissionDenied, ValidationError) as exc:
            messages.error(request, self._service_error(exc))
            return redirect(self.workspace_url(code, request))
        messages.success(request, f"Layering complete for {adda.code}. Advanced to Cutting.")
        return redirect('production:adda-detail', code=adda.code)


# ── Cutting (unchanged) ──────────────────────────────────────────────────────


class CuttingCompleteView(LoginRequiredMixin, ProductionRoleMixin, FormView):
    """POST: write CuttingRecord, generate BatchBarcode rows, advance (→ COMPLETED)."""

    template_name = 'production/cutting_form.html'
    form_class = CuttingForm

    def get_adda(self):
        return get_object_or_404(Adda, code=self.kwargs['code'])

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['adda'] = self.get_adda()
        return ctx

    def form_valid(self, form):
        adda = self.get_adda()
        try:
            cr = complete_cutting(
                adda=adda,
                pieces_cut=form.cleaned_data['pieces_cut'],
                worker_ids=[u.pk for u in form.cleaned_data.get('workers') or []],
                notes=form.cleaned_data.get('notes', ''),
                user=self.request.user,
            )
        except (ValidationError, PermissionDenied) as exc:
            form.add_error(None, str(exc))
            return self.form_invalid(form)
        messages.success(self.request, f"Cutting complete. {cr.pieces_cut} barcodes generated for {adda.code}.")
        return redirect('tracking:barcode-list', adda_code=adda.code)
