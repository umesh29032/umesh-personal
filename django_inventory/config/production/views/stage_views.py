"""Stage views — the LAYERING + CUTTING operator consoles (the app's biggest view file).

FILE MAP (architecture comment — keep sections in this order):
  L75   Helpers                 — _get_adda, rolls queryset, param parsing
  L128  Layering workspace      — _build_layering_context + GET views
        (StagePanelView serves EVERY stage's embedded panel — shared seam)
  L305  Layering actions (POST) — start/attach/entry-edit/leftovers/complete/reopen
  L857  Cutting legacy complete — single-form NIKKAR-style flow
  L891  Cutting workspace       — _build_cutting_context (breakup, verification,
        bundles, allocation display, barcode preview) + 15 action views
  L1407 Allocation views        — era-A creation (LEVER-gated since V2-3) + void

RESPONSIBILITY: parse request → permission/skill/assignment gate
(ProductionRoleMixin + StageViewAccessMixin) → delegate to ONE service →
redirect+message. DELEGATES TO: production stage services (layering/cutting via
services facade), expense.allocate_stage_work/void_allocation (the allowed
one-way production→expense edge). INVARIANTS RELIED ON: single-writer
chokepoints do the actual writes; era guards live in services, NOT here.

WHAT MUST NOT BE ADDED HERE: business logic, multi-row writes, money math,
direct WST/WSC/SWA mutations — services own all of that (ADR-0001/0002).
New STAGE TYPES don't extend this file: they get their own handler+views
module (open-closed; see barcode_gen_views.py as the template).
PARKED: splitting into per-stage modules = remediation Phase 8 (touch-time).

YEH FILE KYU HAI?
─────────────────
Layering workflow ke saare HTTP entry points yahan hain. Saara business logic
production.services (layering_service / cutting_service) mein hai — views sirf:
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
import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.generic import FormView, TemplateView

from accounts.skills import (
    SKILL_CUTTING_MASTER, SKILL_CUTTING_MASTER_HELPER, user_has_skill,
)
from accounts.services import MANAGEMENT_ROLES, user_has_role
from production.forms import (
    AttachRollForm, CompleteLayeringForm, CuttingDraftForm,
    CuttingForm, CuttingStartForm, StartLayeringForm,
)
from production.constants import STAGE_CUTTING, STAGE_LAYERING
from production.models import (
    Adda, AddaStageRecord, CuttingBundleItem, LayeringRollEntry,
    RemainingClothOfClothRoll,
)
from production.services import (
    add_pieces_to_bundle,
    attach_roll_to_layering, complete_cutting_from_bundles,
    complete_cutting_legacy, complete_layering,
    create_bundle_with_pieces, delete_breakup_row, delete_bundle,
    delete_bundle_item, detach_roll_from_layering, get_cutting_snapshot,
    get_layering_snapshot, get_suggested_breakup, preview_barcode_batches,
    reopen_cutting, reopen_layering,
    save_cutting_draft, save_layering_draft, start_cutting, start_layering,
    upsert_breakup_row,
)
from raw_materials.models import ClothColor, ClothRoll
# FUTURE-STAGE-REDESIGN: these expense imports are the SWA-transitional ALLOCATION
# UI. V2-2 settlement (Option B) moves worker earnings to settlement — revisit/retire
# this production->expense edge then (see docs/ARCHITECTURE_V2.md §11 + V2_1_REVIEW).
from expense.models import StageWorkAssignment
from expense.services import (
    allocate_stage_work, item_allocation_summary, void_allocation,
)

logger = logging.getLogger(__name__)

from .mixins import ProductionRoleMixin, StageViewAccessMixin, embedded_advance_redirect, get_adda


def _is_ajax(request) -> bool:
    """True for debounced auto-save fetch() calls (sets X-Requested-With)."""
    return request.headers.get('x-requested-with') == 'XMLHttpRequest'


# ── Helpers ──────────────────────────────────────────────────────────────────


def prev_admin_snapshot(adda: Adda, stage_type: str):
    """R8 generic snapshot plumbing: the nearest PREVIOUS stage (product flow
    order) whose handler exposes a non-None admin_snapshot. Registry-driven —
    a new stage participates by overriding handler.admin_snapshot, nothing
    else. Returns the snapshot dict or None. Caller gates to management."""
    from production.stages import base as stage_registry
    flow = list(adda.product.workflow_stages
                .select_related('stage').order_by('order'))
    codes = [ws.stage.code for ws in flow]
    if stage_type not in codes:
        return None
    for code in reversed(codes[:codes.index(stage_type)]):
        if stage_registry.has(code):
            snap = stage_registry.get(code).admin_snapshot(adda)
            if snap is not None:
                return snap
    return None


_get_adda = get_adda   # shared lookup (views.mixins) — local alias keeps call sites stable


def _visible_lanes(user, adda, stage_code, lanes):
    """GAP-4 worker lane ISOLATION (owner UI law: 'he should only see Body
    Cycle 1'): management sees every lane; a worker sees ONLY the lanes whose
    stage record for THIS stage carries their assignment (roster or task).
    Legacy NULL-stream records count for every lane (adopt-on-touch parity)."""
    if user_has_role(user, MANAGEMENT_ROLES):
        return lanes
    srs = list(AddaStageRecord.objects.filter(
        adda=adda, workflow_stage__stage__code=stage_code))
    mine = set()
    legacy_assigned = False
    for sr in srs:
        if sr.is_worker_assigned(user):
            if sr.stream_id is None:
                legacy_assigned = True
            else:
                mine.add(sr.stream_id)
    if legacy_assigned:
        return lanes
    return [l for l in lanes if l.pk in mine]


def _scope_console_lanes(request, adda, stage_code, lanes, lane):
    """Apply worker isolation to a console render: returns
    (visible_lanes, lane, forbidden) — a worker asking for a sibling lane is
    REFUSED (forbidden=True); a worker with exactly one visible lane
    auto-selects it (no picker chrome, no stream vocabulary)."""
    visible = _visible_lanes(request.user, adda, stage_code, lanes)
    if lane is not None and len(lanes) > 1 and visible is not lanes \
            and lane.pk not in {l.pk for l in visible}:
        return visible, None, True
    if lane is None and len(visible) == 1:
        lane = visible[0]
    return visible, lane, False


def _request_stream(request, adda, *, for_render=False):
    """Streams redesign: resolve the lane a console is operating on.
    ?stream=<pk> when the Adda has multiple lanes; None resolves the
    single lane (today's products — zero URL churn).

    GAP-3: consoles RENDERING without a lane on a multi-lane Adda must show
    a lane PICKER, never a 500 (the bare URL / A360 embedded tab case) —
    `for_render=True` returns None on ambiguity instead of raising; the
    ambiguity refusal itself stays law for every acting (POST) path."""
    from production.services.adda_service import resolve_stream
    raw = None
    if request is not None:
        raw = request.GET.get('stream') or request.POST.get('stream') or None
    try:
        return resolve_stream(adda, raw)
    except ValidationError:
        if for_render and not raw:
            return None
        raise


def _get_layering_stage_record(adda: Adda, lane=None) -> AddaStageRecord | None:
    """Adda ki Layering stage ka record return karta hai (yet started ho to)."""
    stage = adda.product.workflow_stages.filter(
        stage__code=STAGE_LAYERING
    ).first()
    if stage is None:
        return None
    qs = AddaStageRecord.objects.filter(adda=adda, workflow_stage=stage)
    if lane is not None:
        from django.db.models import Q
        qs = qs.filter(Q(stream=lane) | Q(stream__isnull=True))
    return qs.order_by('stream_id').first()


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
    lane = _request_stream(request, adda, for_render=True)
    from production.models import CuttingStream
    lanes = list(CuttingStream.objects.filter(
        adda=adda, cancelled_at__isnull=True).order_by(
        'fabric_group', 'sequence'))
    # GAP-4 worker isolation: a worker sees only THEIR lanes; single own
    # lane auto-selects (no picker, no lane vocabulary); a sibling lane by
    # URL is refused.
    lanes, lane, forbidden = _scope_console_lanes(
        request, adda, STAGE_LAYERING, lanes, lane)
    if forbidden:
        raise PermissionDenied(
            "That lane isn't assigned to you — open your task from "
            "My Dashboard.")
    if lane is None and len(lanes) > 1:
        # GAP-3: bare multi-lane URL → lane picker, not a 500.
        return {'adda': adda, 'needs_lane_choice': True, 'lanes': lanes,
                'active_lane': None, 'show_lane_switcher': False}
    sr = _get_layering_stage_record(adda, lane)
    user = request.user
    filter_color = _parse_int_param(request, 'fc')
    filter_type = _parse_int_param(request, 'ft')
    filter_width = _parse_int_param(request, 'fw')

    is_management = user_has_role(user, MANAGEMENT_ROLES)
    is_assigned = bool(sr and sr.is_worker_assigned(user))
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
    # Gate via permission_service (CLAUDE.md rule #6) — no raw is_superuser.
    # MANAGEMENT_ROLES includes super_admin + manager, so Super Admin still wins.
    can_complete = sr is not None and sr.completed_at is None and (
        is_management or has_helper_skill
    )

    entries = (
        sr.layering_roll_entries
        .select_related('roll', 'roll__cloth_type', 'roll__cloth_color', 'attached_by')
        .prefetch_related('remaining_pieces')   # per-entry leftover list (no N+1)
        .order_by('attached_at')
        if sr else []
    )

    # Next stage in product flow (used for "Advance to {next}" labels).
    # current_stage may be None on completed Addas — falls back to None safely.
    next_stage = None
    if adda.current_stage is not None:
        next_stage = (
            adda.product.workflow_stages
            .filter(order__gt=adda.current_stage.order)
            .order_by('order')
            .first()
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
    from accounts.services import user_can_edit_financials
    cloth_colors = ClothColor.active.order_by('name')
    cloth_types = ClothType.active.order_by('name')
    storage_locations = StorageLocation.active.order_by('name')
    width_choices = list(range(36, 45))
    can_edit_financials = user_can_edit_financials(user)

    # M6 — the layering edge: ADVISORY recommendation from the Adda's
    # approved-layout contracts (registry provider, wrapped: a provider
    # failure never breaks the layering page; section simply absent).
    layout_recommendation = None
    from production.stages.layering import handler as _layering_handler
    if _layering_handler.LAYOUT_PROVIDER is not None:
        try:
            layout_recommendation = _layering_handler.LAYOUT_PROVIDER(adda)
        except Exception:
            logger.exception('layering layout provider failed for %s',
                             adda.code)

    # V1.1 item-2: leftover pieces available for RE-ISSUE into this Adda —
    # management decision (whole piece, source-priced; consume_leftover owns
    # every guard). Never the Adda's own leftovers.
    available_leftovers = []
    if is_management:
        available_leftovers = list(
            RemainingClothOfClothRoll.objects
            .filter(is_consumed=False)
            .exclude(source_adda=adda)
            .select_related('roll__cloth_color', 'source_adda')
            .order_by('-created_at')[:20])
    used_leftovers = list(
        RemainingClothOfClothRoll.objects
        .filter(consumed_in_adda=adda, is_consumed=True)
        .select_related('roll', 'source_adda'))

    return {
        'available_leftovers': available_leftovers,
        'used_leftovers': used_leftovers,
        'is_management': is_management,
        'lanes': lanes, 'active_lane': lane, 'show_lane_switcher': len(lanes) > 1,
        'adda': adda,
        'stage_record': sr,
        'layout_recommendation': layout_recommendation,
        'entries': entries,
        'total_weight': total_weight,
        'distinct_colors_count': len(distinct_colors),
        'roll_ids': [e.roll.roll_id for e in entries],
        'available_rolls_qs': filtered_rolls,
        'start_form': StartLayeringForm(initial={
            'workers': list(sr.active_worker_tasks().values_list('worker_id', flat=True)) if sr else [],
        }) if can_assign else None,
        'attach_form': AttachRollForm(available_rolls_qs=filtered_rolls) if can_attach else None,
        # Section 04 form rendered for anyone who can draft (= anyone who can attach).
        # Pre-populated from stage_record.draft_* fields persisted by save_layering_draft.
        'complete_form': CompleteLayeringForm(initial={
            'layer_length_meters': sr.draft_layer_length_meters if sr else None,
            'notes': sr.draft_notes if sr else '',
        }) if can_draft else None,
        'can_assign': can_assign,
        'can_attach': can_attach,
        'can_draft': can_draft,
        'can_complete': can_complete,
        # Management-only "Edit Layering" button on the completed-state panel —
        # invokes reopen_layering to unlock corrections.
        'can_reopen': is_management and sr is not None and sr.completed_at is not None,
        'next_stage': next_stage,
        # Snapshot for the top-of-panel summary card (rendered when completed).
        'layering_snap': get_layering_snapshot(adda),
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


class LayeringWorkspaceView(LoginRequiredMixin, ProductionRoleMixin,
                            StageViewAccessMixin, TemplateView):
    """Full-page layering workspace (with nav + hero). Standalone entry point."""

    stage_code = STAGE_LAYERING            # skill-gate the VIEW, not just actions
    template_name = 'production/layering_workspace.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        adda = _get_adda(self.kwargs['code'])
        ctx.update(_build_layering_context(self.request, adda))
        return ctx


@method_decorator(xframe_options_sameorigin, name='dispatch')
class StageAdvancedBounceView(LoginRequiredMixin, TemplateView):
    """F-3: the embedded post-COMPLETE landing — a data-free bounce page.

    Sole job: postMessage the parent window ('stage-advanced') so the Adda
    page reloads its flow state. Login-only, NO stage/adda data rendered and
    NO stage access gates — the completing worker can never 403 here (stage
    complete auto-cancels their unreported task, which makes even the
    completed stage's own panel refusable). Direct (non-iframe) hits get a
    success line + a link back to the Adda page.
    """
    template_name = 'production/stage_advanced_bounce.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['code'] = self.kwargs['code']
        return ctx


@method_decorator(xframe_options_sameorigin, name='dispatch')
class StagePanelView(LoginRequiredMixin, ProductionRoleMixin,
                     StageViewAccessMixin, TemplateView):
    """Per-stage panel — canonical URL for iframe embed + standalone view.

    Skill-gated via StageViewAccessMixin (stage_type kwarg) so a direct hit on
    /addas/<code>/stage/<stage_type>/ obeys the same skill rule as the embedded
    panel — not just the ProductionRole gate.

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
        # J-3: panels show the Stage's DISPLAY name ('Sleeve Join'), never the
        # url-slug code ('sleeve_join') — Stage.name is the ownership-editable
        # business label (R10-C masters).
        from production.models import Stage
        ctx['stage_label'] = (Stage.objects.filter(code=stage_type)
                              .values_list('name', flat=True).first()
                              or stage_type.replace('_', ' ').title())
        ctx['embedded'] = self.request.GET.get('embedded') == '1'
        # R3 (PDD §27-C3): panels gate the completion-override UI on this;
        # the SERVICE re-checks the role — template gating is display-only.
        from accounts.services import ROLE_SUPER_ADMIN, user_has_role
        ctx['is_super_admin'] = user_has_role(self.request.user, {ROLE_SUPER_ADMIN})
        # Per-stage panel context via the stage handler registry (M2.6c — the
        # legacy if/elif was removed once the registry path was proven at parity).
        # Each handler's panel_context owns its stage's render context; an unknown
        # stage (no registered handler) just gets the base context.
        from production.stages import base as stage_registry
        if stage_registry.has(stage_type):
            ctx.update(stage_registry.get(stage_type).panel_context(self.request, adda, None))
        # R8 — GENERIC prev-stage admin snapshot: every panel automatically
        # shows the nearest previous stage's admin_snapshot. MANAGEMENT-ONLY
        # at the ctx level (workers never receive the data — leak-tested);
        # open-closed: a future stage only overrides handler.admin_snapshot.
        if user_has_role(self.request.user, MANAGEMENT_ROLES):
            ctx['prev_admin_snapshot'] = prev_admin_snapshot(adda, stage_type)
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
        lane_q = ''
        if request is not None:
            raw = request.POST.get('stream') or request.GET.get('stream')
            if raw:
                lane_q = f'&stream={raw}'
        if request is not None and request.POST.get('embedded') == '1':
            return reverse('production:stage-panel', kwargs={
                'code': code, 'stage_type': 'layering',
            }) + '?embedded=1' + lane_q
        base = reverse('production:layering-workspace', kwargs={'code': code})
        return base + ('?' + lane_q[1:] if lane_q else '')

    def _service_error(self, exc) -> str:
        # ValidationError aata hai list mein kabhi-kabhi — get a flat string
        msg = getattr(exc, 'messages', None)
        return ' '.join(msg) if msg else str(exc)


class LayeringReopenView(_LayeringActionBase):
    """Management-only: unlock a completed Layering stage for correction.

    UX: Admin clicks "Edit / Reopen" on the completed Layering panel, confirms
    (handled in template), POST hits here. Service refuses if any downstream
    stage has started — see reopen_layering.
    """

    def post(self, request, code):
        adda = _get_adda(code)
        try:
            reopen_layering(adda=adda, user=request.user)
        except (PermissionDenied, ValidationError) as exc:
            messages.error(request, self._service_error(exc))
            return redirect(self.workspace_url(code, request))
        messages.success(request, f"Layering reopened for {adda.code}. Make corrections then Complete again.")
        # On embedded reopen, ping parent to reload — fresh flow state shows
        # Layering as current again, downstream tabs locked.
        if request.POST.get('embedded') == '1':
            return redirect(
                reverse('production:stage-panel', kwargs={
                    'code': adda.code, 'stage_type': STAGE_LAYERING,
                }) + '?embedded=1&advanced=1'
            )
        return redirect('production:adda-detail', code=adda.code)


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
                stream=request.POST.get('stream') or request.GET.get('stream'),
            )
        except (PermissionDenied, ValidationError) as exc:
            messages.error(request, self._service_error(exc))
            return redirect(self.workspace_url(code, request))
        messages.success(request, "Layering stage started — workers assigned.")
        return redirect(self.workspace_url(code, request))


class LayeringConsumeLeftoverView(_LayeringActionBase):
    """V1.1 item-2: MANAGEMENT re-issues a leftover piece into THIS Adda —
    the one missing door to the locked `consume_leftover` writer (whole
    piece, valued at source ₹/kg forever, one-shot, append-only)."""

    def post(self, request, code):
        adda = _get_adda(code)
        from raw_materials.services.roll_service import consume_leftover
        leftover = get_object_or_404(
            RemainingClothOfClothRoll.objects.select_related(
                'roll', 'source_adda'),
            pk=request.POST.get('leftover') or 0)
        try:
            consume_leftover(request.user, leftover=leftover, adda=adda,
                             notes=f'reused in {adda.code}')
        except (PermissionDenied, ValidationError) as exc:
            messages.error(request, self._service_error(exc))
            return redirect(self.workspace_url(code, request))
        messages.success(
            request,
            f"Leftover used: {leftover.remaining_weight_kg} kg "
            f"({leftover.roll.roll_id}, from {leftover.source_adda.code}) — "
            "its cost follows the original roll; the piece is now this "
            "Adda's material.")
        return redirect(self.workspace_url(code, request))


class LayeringAttachRollView(_LayeringActionBase):
    """Assigned worker attaches a cloth roll with verified width/weight."""

    def post(self, request, code):
        adda = _get_adda(code)
        sr = _get_layering_stage_record(adda, _request_stream(request, adda))
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
                user=request.user, stream=(request.POST.get('stream') or request.GET.get('stream')))
        except (PermissionDenied, ValidationError) as exc:
            messages.error(request, self._service_error(exc))
            return redirect(self.workspace_url(code, request))
        messages.success(request, f"Roll {form.cleaned_data['roll'].roll_id} attached.")
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
        sr = _get_layering_stage_record(adda, _request_stream(request, adda))
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
                _date.fromisoformat(purchased_raw) if purchased_raw else timezone.localdate()
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
                user=request.user, stream=(request.POST.get('stream') or request.GET.get('stream')))
        except (PermissionDenied, ValidationError) as exc:
            messages.error(request, f"Roll {new_rolls[0].roll_id} created but attach failed: {self._service_error(exc)}")
            return redirect(self.workspace_url(code, request))

        messages.success(request, f"Created + attached new roll {new_rolls[0].roll_id}.")
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
        notes = form.cleaned_data.get('notes', '')

        per_entry = self._parse_per_entry_data(request)

        # Both actions persist draft state via save_layering_draft so per-row
        # values + header bits are stored before any advance happens.
        per_entry_normalized = {
            pk: data for pk, data in per_entry.items()
        }
        try:
            _, skipped_rolls = save_layering_draft(
                adda=adda,
                layer_length_meters=layer_length,
                duration_minutes=None,            # duration auto-computed at complete
                notes=notes,
                per_entry_data=per_entry_normalized,
                user=request.user,
                stream=(request.POST.get('stream') or request.GET.get('stream')),
            )
        except (PermissionDenied, ValidationError) as exc:
            if _is_ajax(request):
                return HttpResponse(self._service_error(exc), status=400)
            messages.error(request, self._service_error(exc))
            return redirect(self.workspace_url(code, request))

        if action == 'draft':
            if _is_ajax(request):
                return HttpResponse(status=204)   # debounced auto-save
            # F1: partial rows are NOT silently dropped any more — tell the user
            # exactly which rolls still need the layers + leftover-weight pair.
            if skipped_rolls:
                messages.warning(
                    request,
                    f"Draft saved, but {len(skipped_rolls)} row(s) were NOT stored — "
                    f"{', '.join(skipped_rolls)} need both a layer count and a "
                    "leftover weight.")
            else:
                messages.success(request, "Draft saved.")
            return redirect(self.workspace_url(code, request))

        # action == 'complete' path — strict validation + advance
        sr = _get_layering_stage_record(adda, _request_stream(request, adda))
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
        # Duration auto-calculated from timestamps (stage-duration-rule): layering
        # duration = now − adda.started_at, in whole minutes (min 1). No manual input.
        elapsed_min = (timezone.now() - adda.started_at).total_seconds() / 60
        auto_duration = max(1, round(elapsed_min))
        # R3 (PDD §27-C3): optional super-admin override past pending workers.
        # Role + non-empty reason are re-validated in the SERVICE (never trust
        # the form); this only forwards the intent.
        override_reason = (request.POST.get('override_reason', '').strip() or None
                           if request.POST.get('override_pending') else None)
        try:
            complete_layering(
                adda=adda,
                duration_minutes=auto_duration,
                layer_length_meters=layer_length,
                per_entry_layers=per_entry_layers,
                notes=notes,
                user=request.user,
                override_pending_reason=override_reason,
                stream=(request.POST.get('stream')
                        or request.GET.get('stream')),
            )
        except (PermissionDenied, ValidationError) as exc:
            messages.error(request, self._service_error(exc))
            return redirect(self.workspace_url(code, request))

        # Refresh to read the newly-advanced current_stage from DB.
        adda.refresh_from_db()
        next_label = (
            adda.current_stage.get_stage_type_display() if adda.current_stage else "next stage"
        )
        messages.success(request, f"Layering complete for {adda.code}. Advanced to {next_label}.")

        # R2 (PDD §14): reconciliation WARN — worker-reported layers vs breakup
        # lay_count. NON-blocking (complete already succeeded above); mirrors the
        # service-side log so management sees the delta without digging in logs.
        from production.services import worker_layer_reconciliation
        recon = worker_layer_reconciliation(adda)
        if recon and recon['mismatch']:
            messages.warning(
                request,
                f"Layer reconciliation: workers reported {recon['reported']} layers "
                f"but the breakup table totals {recon['lay_count']} "
                f"(delta {recon['delta']:+}). Review worker reports if unexpected.")

        # When complete was POSTed from inside an iframe (embedded mode), the
        # default 'production:adda-detail' redirect would load adda-detail INSIDE
        # the iframe — and Django's default X-Frame-Options blocks that. F-3:
        # redirect to the COMPLETED stage's own panel (viewer-safe for the
        # completing worker) — its ?advanced=1 JS makes the parent reload.
        if request.POST.get('embedded') == '1':
            return embedded_advance_redirect(adda)
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
            cr = complete_cutting_legacy(
                adda=adda,
                pieces_cut=form.cleaned_data['pieces_cut'],
                worker_ids=[u.pk for u in form.cleaned_data.get('workers') or []],
                notes=form.cleaned_data.get('notes', ''),
                user=self.request.user,
            )
        except (ValidationError, PermissionDenied) as exc:
            form.add_error(None, str(exc))
            return self.form_invalid(form)
        adda.refresh_from_db(fields=['current_stage'])
        from production.services.adda_service import PRE_PRODUCTION_STAGE_CODES
        _joined = (adda.current_stage is None
                   or adda.current_stage.stage.code not in PRE_PRODUCTION_STAGE_CODES)
        if _joined:
            messages.success(self.request,
                             f"Cutting complete — all lanes cut. {adda.code} moves on.")
        else:
            messages.success(self.request,
                             f"Lane cut recorded ({cr.pieces_cut} pieces). "
                             "Waiting for the remaining lane(s) before barcodes.")
        return redirect('tracking:barcode-list', adda_code=adda.code)


# ── Cutting workspace (PR3 2026-05-28) ──────────────────────────────────────


def _build_cutting_context(request, adda: Adda) -> dict:
    """Cutting workspace context — mirrors _build_pattern_context shape.

    Returns dict with snapshot, breakup rows, suggestion, pickers, gates.
    """
    user = request.user
    lane = _request_stream(request, adda, for_render=True)
    from production.models import CuttingStream
    from production.services.adda_service import preproduction_joined
    lanes = list(CuttingStream.objects.filter(
        adda=adda, cancelled_at__isnull=True).order_by(
        'fabric_group', 'sequence'))
    # GAP-4 worker isolation (same law as layering).
    lanes, lane, forbidden = _scope_console_lanes(
        request, adda, STAGE_CUTTING, lanes, lane)
    if forbidden:
        raise PermissionDenied(
            "That lane isn't assigned to you — open your task from "
            "My Dashboard.")
    if lane is None and len(lanes) > 1:
        # GAP-3: bare multi-lane URL → lane picker, not a 500.
        return {'adda': adda, 'needs_lane_choice': True, 'lanes': lanes,
                'active_lane': None, 'show_lane_switcher': False}
    _joined = preproduction_joined(adda)
    snapshot = get_cutting_snapshot(adda, stream=lane)
    sr = snapshot.get('stage_record')
    cutting_record = snapshot.get('cutting_record')
    breakup = snapshot.get('breakup') or []
    bundles = snapshot.get('bundles') or []
    breakup_total = snapshot.get('breakup_total', 0)
    bundle_total = snapshot.get('bundle_total', 0)

    # Sizes available on this product
    product_sizes = list(
        adda.product.sizes.filter(is_active=True).order_by('display_order', 'code')
    )
    # Patterns assigned to this product
    pattern_assignments = list(
        adda.product.pattern_assignments.select_related('pattern').order_by('pattern__name')
    )
    patterns = [a.pattern for a in pattern_assignments]
    # Colors from layered rolls (if layering completed)
    layering_wf = adda.product.workflow_stages.filter(stage__code=STAGE_LAYERING).first()
    layered_color_ids: set[int] = set()
    if layering_wf:
        layering_sr = AddaStageRecord.objects.filter(
            adda=adda, workflow_stage=layering_wf,
        ).first()
        layering_record = getattr(layering_sr, 'layering', None) if layering_sr else None
        if layering_record:
            layered_color_ids = set(
                layering_record.rolls_used.values_list('cloth_color_id', flat=True)
            )
    colors = list(ClothColor.objects.filter(id__in=layered_color_ids).order_by('name')) if layered_color_ids else []

    is_management = user_has_role(user, MANAGEMENT_ROLES)
    has_master_skill = user_has_skill(
        user, [SKILL_CUTTING_MASTER, SKILL_CUTTING_MASTER_HELPER],
    )
    has_helper_skill = user_has_skill(user, SKILL_CUTTING_MASTER_HELPER)

    can_start = is_management
    is_assigned = bool(sr and sr.is_worker_assigned(user))
    can_edit_breakup = sr is not None and sr.completed_at is None and (
        is_management or (is_assigned and has_master_skill)
    )
    # PR7: complete now requires actual BUNDLES (not breakup).
    # Streams redesign: the lane's actual = its BREAKUP rows (bundles moved
    # post-join); either source arms the complete button.
    can_complete_workspace = sr is not None and sr.completed_at is None and (
        is_management or has_helper_skill
    ) and (bool(bundles) or bool(breakup))
    can_reopen = is_management and sr is not None and sr.completed_at is not None

    # ── Per-bundle-item worker allocation (PR-6) ────────────────────────────
    # Attach allocation data to each bundle for the template: existing
    # (non-voided) allocations + how much of each item is still unallocated.
    # Form is gated on can_allocate; the display is MANAGEMENT-only (see below).
    # V2-3 PR-B: creation also requires the rollback lever ON — by default
    # earnings book at Adda settlement, so the allocate forms hide. Existing
    # era-A rows stay visible and voidable (historical corrections stay legal).
    from django.conf import settings as dj_settings
    ledger_at_allocation = getattr(dj_settings, 'LEDGER_CREDIT_AT_ALLOCATION', False)
    can_void = is_management and sr is not None and sr.completed_at is None
    can_allocate = can_void and ledger_at_allocation
    allocation_workers = sr.active_workers if sr else []
    for b in bundles:
        ann = []
        # Worker-cert fix (V1.1, 2026-07-12): allocation rows carry OTHER
        # workers' ₹ earning snapshots (era-A) — management-only ctx, like
        # A360: workers never receive a byte (V2-3 visibility = own money only).
        if is_management:
            for it in b.items.select_related('pattern', 'color').all():
                summ = item_allocation_summary(it)
                rows = list(
                    it.work_assignments.filter(voided_at__isnull=True)
                    .select_related('worker')
                )
                ann.append({
                    'item': it,
                    'allocated': summ['allocated'],
                    'remaining': summ['remaining'],
                    'rows': rows,
                })
        b.alloc_items = ann

    # Suggested breakup (pre-fill hint when no rows yet).
    suggestion = get_suggested_breakup(adda) if not breakup else []
    suggested_total = sum(row['count'] for row in suggestion)
    # Phase 8C: the honest source label — approved-layout contract or
    # the classic formula (advisory either way; operator overrides).
    from production.stages.cutting.service import get_suggestion_source
    suggestion_source = get_suggestion_source(adda) if suggestion else None

    # PR13: barcode batch preview — what would generate on Mark Complete?
    barcode_preview = preview_barcode_batches(adda)
    barcode_preview_total = sum(p['total'] for p in barcode_preview)

    next_stage = None
    if adda.current_stage is not None:
        next_stage = (
            adda.product.workflow_stages
            .filter(order__gt=adda.current_stage.order)
            .order_by('order').first()
        )

    return {
        'lanes': lanes, 'active_lane': lane, 'show_lane_switcher': len(lanes) > 1,
        'adda': adda,
        'cutting_snapshot': snapshot,
        'cutting_stage_record': sr,
        'cutting_record': cutting_record,
        'breakup': breakup,
        'bundles': bundles,
        'breakup_total': breakup_total,
        'bundle_total': bundle_total,
        # total_pieces (template legacy) = bundle total (drives barcodes).
        'total_pieces': bundle_total,
        'suggestion': suggestion,
        'suggested_total': suggested_total,
        'suggestion_source': suggestion_source,
        'barcode_preview': barcode_preview,
        'barcode_preview_total': barcode_preview_total,
        'product_sizes': product_sizes,
        'product_patterns': patterns,
        'pattern_assignments': pattern_assignments,
        'layered_colors': colors,
        'is_management': is_management,
        'can_start_cutting': can_start,
        'can_edit_breakup': can_edit_breakup,
        # GAP-5: bundling is POST-JOIN (frozen PROPOSAL §3) — the console's
        # bundle forms render only once every blocking lane is cut; the
        # service refuses earlier anyway (view mirrors the wall honestly).
        'can_edit_bundles': can_edit_breakup and _joined,
        'bundles_locked_until_join': not _joined,
        'can_complete_workspace': can_complete_workspace,
        'can_reopen_cutting': can_reopen,
        'can_allocate': can_allocate,
        'can_void': can_void,
        'ledger_at_allocation': ledger_at_allocation,
        'allocation_workers': allocation_workers,
        'next_stage_after_cutting': next_stage,
        'cutting_start_form': CuttingStartForm(initial={
            'workers': list(sr.active_worker_tasks().values_list('worker_id', flat=True)) if sr else [],
        }) if can_start else None,
        'cutting_draft_form': CuttingDraftForm(initial={
            'notes': cutting_record.notes if cutting_record else '',
        }) if can_edit_breakup else None,
    }


class CuttingWorkspaceView(LoginRequiredMixin, ProductionRoleMixin,
                           StageViewAccessMixin, TemplateView):
    stage_code = STAGE_CUTTING             # skill-gate the VIEW, not just actions
    template_name = 'production/cutting_workspace.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(_build_cutting_context(self.request, _get_adda(self.kwargs['code'])))
        return ctx


class _CuttingActionBase(LoginRequiredMixin, ProductionRoleMixin, View):
    http_method_names = ['post']

    def workspace_url(self, code: str, request=None) -> str:
        if request is not None and request.POST.get('embedded') == '1':
            return reverse('production:stage-panel', kwargs={
                'code': code, 'stage_type': STAGE_CUTTING,
            }) + '?embedded=1'
        return reverse('production:cutting-workspace', kwargs={'code': code})

    def _service_error(self, exc) -> str:
        msg = getattr(exc, 'messages', None)
        return ' '.join(msg) if msg else str(exc)


class CuttingStartView(_CuttingActionBase):
    def post(self, request, code):
        adda = _get_adda(code)
        form = CuttingStartForm(request.POST)
        if not form.is_valid():
            messages.error(request, "Select at least one worker.")
            return redirect(self.workspace_url(code, request))
        try:
            start_cutting(
                adda=adda,
                worker_ids=[u.pk for u in form.cleaned_data['workers']],
                user=request.user, stream=(request.POST.get('stream') or request.GET.get('stream')))
        except (PermissionDenied, ValidationError) as exc:
            messages.error(request, self._service_error(exc))
            return redirect(self.workspace_url(code, request))
        messages.success(request, "Cutting stage started.")
        return redirect(self.workspace_url(code, request))


class CuttingBreakupSaveView(_CuttingActionBase):
    """Bulk save of breakup rows — parallel arrays size_id/color_id/pattern_id/count.

    PR14: any incomplete row (missing pattern/size/color or non-numeric count)
    raises a user-facing error instead of silent skip. Count = 0 still treated
    as "delete existing combo" per upsert_breakup_row semantics.
    """

    def post(self, request, code):
        adda = _get_adda(code)
        size_ids = request.POST.getlist('size_id')
        color_ids = request.POST.getlist('color_id')
        pattern_ids = request.POST.getlist('pattern_id')
        counts = request.POST.getlist('count')
        roll_ids = request.POST.getlist('roll_id') or [''] * len(size_ids)

        if not (len(size_ids) == len(color_ids) == len(pattern_ids) == len(counts)):
            messages.error(request, "Form array length mismatch.")
            return redirect(self.workspace_url(code, request))
        if not size_ids:
            messages.error(request, "No rows submitted.")
            return redirect(self.workspace_url(code, request))

        # PA-05B-2: bulk save is all-or-nothing. Previously each row was upserted
        # in its own implicit transaction and the handler returned on the first
        # bad row — leaving earlier rows persisted (partial write). Wrap the whole
        # batch in one transaction and RAISE on any row error so it rolls back.
        from django.db import transaction
        saved = 0
        try:
            with transaction.atomic():
                for row_idx, (sid, cid, pid, cnt, rid) in enumerate(zip(size_ids, color_ids, pattern_ids, counts, roll_ids), start=1):
                    # Reject incomplete rows — surface a clear error to the user.
                    if not (sid and cid and pid):
                        raise ValidationError(
                            f"Row {row_idx}: pattern, size, and color are all required.")
                    try:
                        size_id = int(sid); color_id = int(cid)
                        pattern_id = int(pid); count = int(cnt)
                        roll_id = int(rid) if rid else None
                    except (TypeError, ValueError):
                        raise ValidationError(f"Row {row_idx}: invalid number in form.")
                    upsert_breakup_row(
                        adda=adda, size_id=size_id, color_id=color_id,
                        pattern_id=pattern_id, count=count, roll_id=roll_id,
                        user=request.user, stream=(request.POST.get('stream') or request.GET.get('stream')))
                    saved += 1
        except (PermissionDenied, ValidationError) as exc:
            # Whole batch rolled back — nothing saved, so the form stays consistent.
            messages.error(request, self._service_error(exc))
            return redirect(self.workspace_url(code, request))
        if saved == 0:
            messages.error(request, "Nothing saved — check that all rows are complete.")
        else:
            messages.success(request, f"{saved} breakup row(s) saved.")
        return redirect(self.workspace_url(code, request))


class CuttingBreakupDeleteView(_CuttingActionBase):
    def post(self, request, code, pk):
        adda = _get_adda(code)
        try:
            delete_breakup_row(adda=adda, breakup_id=pk, user=request.user, stream=(request.POST.get('stream') or request.GET.get('stream')))
        except (PermissionDenied, ValidationError) as exc:
            messages.error(request, self._service_error(exc))
            return redirect(self.workspace_url(code, request))
        messages.success(request, "Row removed.")
        return redirect(self.workspace_url(code, request))


class CuttingDraftView(_CuttingActionBase):
    def post(self, request, code):
        adda = _get_adda(code)
        form = CuttingDraftForm(request.POST)
        notes = form.data.get('notes', '') if not form.is_valid() else form.cleaned_data.get('notes', '')
        try:
            save_cutting_draft(adda=adda, notes=notes, user=request.user, stream=(request.POST.get('stream') or request.GET.get('stream')))
        except (PermissionDenied, ValidationError) as exc:
            if _is_ajax(request):
                return HttpResponse(self._service_error(exc), status=400)
            messages.error(request, self._service_error(exc))
            return redirect(self.workspace_url(code, request))
        if _is_ajax(request):
            return HttpResponse(status=204)   # debounced auto-save
        messages.success(request, "Draft saved.")
        return redirect(self.workspace_url(code, request))


class CuttingWorkspaceCompleteView(_CuttingActionBase):
    """Workspace-mode complete — drives barcode generation from breakup rows."""

    def post(self, request, code):
        adda = _get_adda(code)
        # R3 (PDD §27-C3): super-admin override forwarding — validated in service.
        override_reason = (request.POST.get('override_reason', '').strip() or None
                           if request.POST.get('override_pending') else None)
        # Phase 8C: ADVISORY reconciliation — computed BEFORE completion
        # (bundle rows are live here), reported AFTER success. Warnings
        # explain; they never block, never modify (owner count hierarchy).
        from production.stages.cutting.service import layout_reconciliation
        recon = layout_reconciliation(adda)
        try:
            cr = complete_cutting_from_bundles(
                adda=adda, user=request.user,
                override_pending_reason=override_reason, stream=(request.POST.get('stream') or request.GET.get('stream')))
        except (PermissionDenied, ValidationError) as exc:
            messages.error(request, self._service_error(exc))
            return redirect(self.workspace_url(code, request))
        messages.success(
            request,
            f"Lane cut recorded ({cr.pieces_cut} pieces).",
        )
        if recon and recon['mismatches']:
            uids = ', '.join(recon['uids'])
            for m in recon['mismatches']:
                messages.warning(
                    request,
                    f"Layout check ({uids}): size {m['label']} — expected "
                    f"{m['expected']} (marker × plies), cut {m['actual']}. "
                    "Your numbers stand; verify against the marker if "
                    "unexpected.")
        # F-3: completed stage's own panel — never the next stage's (worker 403).
        if request.POST.get('embedded') == '1':
            return embedded_advance_redirect(adda)
        return redirect('tracking:barcode-list', adda_code=adda.code)


class CuttingReopenView(_CuttingActionBase):
    def post(self, request, code):
        adda = _get_adda(code)
        try:
            reopen_cutting(adda=adda, user=request.user)
        except (PermissionDenied, ValidationError) as exc:
            messages.error(request, self._service_error(exc))
            return redirect(self.workspace_url(code, request))
        messages.success(request, f"Cutting reopened for {adda.code}.")
        if request.POST.get('embedded') == '1':
            return redirect(
                reverse('production:stage-panel', kwargs={
                    'code': adda.code, 'stage_type': STAGE_CUTTING,
                }) + '?embedded=1&advanced=1'
            )
        return redirect('production:adda-detail', code=adda.code)


class CuttingBundleCreateView(_CuttingActionBase):
    """Bundle create — atomic header + initial pieces (PR12).

    POST: size_id + bundle_number + parallel breakup_id[] + take_count[].
    If no take_count > 0, creates empty bundle header (PR9 back-compat).
    Otherwise atomic create header + consume pieces in one tx.
    """

    def post(self, request, code):
        adda = _get_adda(code)
        try:
            size_id = int(request.POST.get('size_id') or 0)
        except (TypeError, ValueError):
            messages.error(request, "Invalid size.")
            return redirect(self.workspace_url(code, request))
        if size_id <= 0:
            messages.error(request, "Bundle size is required.")
            return redirect(self.workspace_url(code, request))
        bundle_number = request.POST.get('bundle_number', '')

        # Parse multi-select breakup picker (PR12).
        breakup_ids = request.POST.getlist('breakup_id')
        take_counts = request.POST.getlist('take_count')
        selections: list[dict] = []
        if breakup_ids and len(breakup_ids) == len(take_counts):
            for bid, tc in zip(breakup_ids, take_counts):
                try:
                    breakup_id = int(bid); take_count = int(tc)
                except (TypeError, ValueError):
                    continue
                if take_count <= 0:
                    continue
                selections.append({
                    'breakup_id': breakup_id, 'take_count': take_count,
                })
        try:
            bundle = create_bundle_with_pieces(
                adda=adda, size_id=size_id,
                bundle_number=bundle_number, selections=selections,
                user=request.user, stream=(request.POST.get('stream') or request.GET.get('stream')))
        except (PermissionDenied, ValidationError) as exc:
            messages.error(request, self._service_error(exc))
            return redirect(self.workspace_url(code, request))
        if selections:
            messages.success(
                request,
                f"Bundle created with {len(selections)} piece row(s) "
                f"({bundle.total_pieces} pieces).",
            )
        else:
            messages.success(request, "Empty bundle created. Add pieces below.")
        return redirect(self.workspace_url(code, request))


class CuttingBundleAddPiecesView(_CuttingActionBase):
    """Multi-select bulk consume (PR10).

    POST parallel arrays:
      breakup_id[], take_count[]
    Each non-zero take_count → CuttingBundleItem in this bundle with
    source_breakup FK + breakup.consumed_count incremented.
    """

    def post(self, request, code, pk):
        adda = _get_adda(code)
        breakup_ids = request.POST.getlist('breakup_id')
        take_counts = request.POST.getlist('take_count')
        if len(breakup_ids) != len(take_counts):
            messages.error(request, "Form array length mismatch.")
            return redirect(self.workspace_url(code, request))

        selections: list[dict] = []
        for row_idx, (bid, tc) in enumerate(zip(breakup_ids, take_counts), start=1):
            try:
                breakup_id = int(bid); take_count = int(tc)
            except (TypeError, ValueError):
                # PR14: surface parse errors instead of silent skip.
                messages.error(
                    request,
                    f"Row {row_idx}: invalid number — check breakup id / take count.",
                )
                return redirect(self.workspace_url(code, request))
            if take_count <= 0:
                continue
            selections.append({'breakup_id': breakup_id, 'take_count': take_count})

        if not selections:
            messages.error(request, "Tick at least one piece row with Take > 0.")
            return redirect(self.workspace_url(code, request))

        try:
            items = add_pieces_to_bundle(
                adda=adda, bundle_id=pk, selections=selections,
                user=request.user, stream=(request.POST.get('stream') or request.GET.get('stream')))
        except (PermissionDenied, ValidationError) as exc:
            messages.error(request, self._service_error(exc))
            return redirect(self.workspace_url(code, request))
        messages.success(request, f"{len(items)} piece row(s) consumed into bundle.")
        return redirect(self.workspace_url(code, request))


class CuttingBundleItemDeleteView(_CuttingActionBase):
    """Remove a single bundle line item. Bundle auto-deletes if last item."""

    def post(self, request, code, pk):
        adda = _get_adda(code)
        try:
            delete_bundle_item(adda=adda, item_id=pk, user=request.user, stream=(request.POST.get('stream') or request.GET.get('stream')))
        except (PermissionDenied, ValidationError) as exc:
            messages.error(request, self._service_error(exc))
            return redirect(self.workspace_url(code, request))
        messages.success(request, "Item removed.")
        return redirect(self.workspace_url(code, request))


class CuttingBundleDeleteView(_CuttingActionBase):
    """Remove an entire bundle (size group)."""

    def post(self, request, code, pk):
        adda = _get_adda(code)
        try:
            delete_bundle(adda=adda, bundle_id=pk, user=request.user, stream=(request.POST.get('stream') or request.GET.get('stream')))
        except (PermissionDenied, ValidationError) as exc:
            messages.error(request, self._service_error(exc))
            return redirect(self.workspace_url(code, request))
        messages.success(request, "Bundle removed.")
        return redirect(self.workspace_url(code, request))


class CuttingBundleItemAllocateView(_CuttingActionBase):
    """Allocate a CuttingBundleItem's pieces to a worker (PR-6 payroll).

    POST: worker_id + allocated_quantity + notes (optional). Resolves the
    cutting AddaStageRecord, then books the earning via expense.allocate_stage_work
    (which freezes the rate + credits the worker's ledger). pk = bundle_item id.
    """

    def post(self, request, code, pk):
        adda = _get_adda(code)
        item = get_object_or_404(
            CuttingBundleItem, pk=pk, bundle__cutting_record__stage_record__adda=adda,
        )
        sr = item.bundle.cutting_record.stage_record
        try:
            worker_id = int(request.POST.get('worker_id') or 0)
            qty = int(request.POST.get('allocated_quantity') or 0)
        except (TypeError, ValueError):
            messages.error(request, "Invalid number in form.")
            return redirect(self.workspace_url(code, request))
        if worker_id <= 0:
            messages.error(request, "Pick a worker.")
            return redirect(self.workspace_url(code, request))
        if qty < 1:
            messages.error(request, "Quantity must be >= 1.")
            return redirect(self.workspace_url(code, request))
        from accounts.models import User
        worker = User.objects.filter(pk=worker_id).first()
        if worker is None:
            messages.error(request, "Worker not found.")
            return redirect(self.workspace_url(code, request))
        try:
            allocate_stage_work(
                user=request.user, stage_record=sr, worker=worker,
                bundle_item=item, allocated_quantity=qty,
                notes=request.POST.get('notes', ''),
            )
        except (PermissionDenied, ValidationError) as exc:
            messages.error(request, self._service_error(exc))
            return redirect(self.workspace_url(code, request))
        messages.success(request, f"Allocated {qty} to {worker.email}.")
        return redirect(self.workspace_url(code, request))


class CuttingAllocationDeleteView(_CuttingActionBase):
    """Void a worker allocation — reverses its ledger credit (audit-preserving).
    pk = StageWorkAssignment id. Management-only (enforced in void_allocation)."""

    def post(self, request, code, pk):
        adda = _get_adda(code)
        assignment = get_object_or_404(
            StageWorkAssignment, pk=pk, stage_record__adda=adda,
        )
        try:
            void_allocation(assignment, user=request.user)
        except (PermissionDenied, ValidationError) as exc:
            messages.error(request, self._service_error(exc))
            return redirect(self.workspace_url(code, request))
        messages.success(request, "Allocation removed.")
        return redirect(self.workspace_url(code, request))
