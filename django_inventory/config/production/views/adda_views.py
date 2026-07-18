"""Adda ke views — list, create, detail.

YEH FILE KYU HAI?
─────────────────
AddaListView    — filterable batch list, paginated
AddaCreateView  — naya Adda start karne ka form (service per-product counter increment)
AddaDetailView  — Adda ka full view: workflow pills, stage records, rolls, barcodes
"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.generic import DetailView, FormView, ListView

from production.forms import AddaCreateForm
from production.models import Adda
from production.services import create_adda

from .mixins import ManagementRoleMixin, ProductionRoleMixin


class AddaListView(LoginRequiredMixin, ProductionRoleMixin, ListView):
    template_name = 'production/adda_list.html'
    model = Adda
    context_object_name = 'addas'
    paginate_by = 50

    def get_queryset(self):
        qs = Adda.objects.select_related('product', 'current_stage__stage').order_by('-started_at')
        status = self.request.GET.get('status')
        stage_type = self.request.GET.get('stage')
        if status:
            qs = qs.filter(status=status)
        if stage_type:
            qs = qs.filter(current_stage__stage__code=stage_type)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['filters'] = {
            'status': self.request.GET.get('status', ''),
            'stage': self.request.GET.get('stage', ''),
        }
        # Use Stage rows as filter options (replaces hardcoded StageType enum).
        from production.models import Stage
        ctx['stage_types'] = list(
            Stage.active.values_list('code', 'name').order_by('name')
        )
        ctx['status_choices'] = Adda.Status.choices
        return ctx


class AddaCreateView(LoginRequiredMixin, ManagementRoleMixin, FormView):
    # M3 campaign fix 2026-07-11: creation is a MANAGEMENT act — the old
    # ProductionRoleMixin let any worker reach (and POST) this form; the
    # service has no role gate, so the view is the wall.
    template_name = 'production/adda_form.html'
    form_class = AddaCreateForm
    success_url = reverse_lazy('production:adda-list')

    def form_valid(self, form):
        try:
            adda = create_adda(user=self.request.user, product=form.cleaned_data['product'])
        except ValidationError as exc:
            form.add_error(None, str(exc))
            return self.form_invalid(form)
        messages.success(self.request, f"Adda {adda.code} started.")
        return redirect('production:adda-detail', code=adda.code)


@method_decorator(xframe_options_sameorigin, name='dispatch')
class AddaDetailView(LoginRequiredMixin, ProductionRoleMixin, DetailView):
    """Adda detail = tabbed dashboard (Phase 4).

    Each WorkflowStage becomes a tab. Default tab = current stage; if Adda is
    completed, default = last stage. Activity feed at bottom (all users on this Adda).

    All tab content is pre-rendered server-side; JS toggles visibility (decision D12).

    @xframe_options_sameorigin: defense-in-depth — when a stage-panel iframe POSTs
    Complete and its redirect somehow lands here (legacy or fallback path), the
    iframe should be allowed to render the parent page rather than break with
    a "refused to connect" browser error.
    """

    template_name = 'production/adda_detail.html'
    model = Adda
    context_object_name = 'adda'
    slug_field = 'code'
    slug_url_kwarg = 'code'

    def get_object(self, queryset=None):
        # product + current stage are read throughout this view/template
        return get_object_or_404(
            Adda.objects.select_related('product', 'current_stage__stage'),
            code=self.kwargs['code'])

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        adda = self.object
        stages = list(adda.product.workflow_stages.select_related('stage__category', 'stage__machine_type').order_by('order'))

        # Streams redesign: PRE-PRODUCTION LANE CARDS (rendered only when
        # the Blueprint derived >1 live lane — single-lane = zero chrome).
        from production.models import AddaStageRecord, CuttingStream
        from production.services.adda_service import PRE_PRODUCTION_STAGE_CODES
        # GAP-4 (lifecycle §7): cancelled lanes render GREYED with their
        # reason — never hidden; live lanes drive the steps/join as before.
        lanes = list(CuttingStream.objects.filter(adda=adda)
                     .order_by('fabric_group', 'sequence'))
        trio_ws = [s for s in stages
                   if s.stage.code in PRE_PRODUCTION_STAGE_CODES]
        lane_srs = {
            (sr.stream_id, sr.workflow_stage_id): sr
            for sr in AddaStageRecord.objects.filter(
                adda=adda, workflow_stage__in=trio_ws)}
        lane_cards = []
        for lane in lanes:
            steps = []
            for ws in trio_ws:
                sr = lane_srs.get((lane.pk, ws.pk))
                state = ('done' if sr is not None and sr.completed_at
                         else 'open' if sr is not None and sr.started_at
                         else 'pending')
                steps.append({'ws': ws, 'name': ws.stage.name,
                              'state': state})
            lane_cards.append({'lane': lane, 'steps': steps,
                               'blocking': lane.is_blocking,
                               'cancelled': lane.cancelled_at is not None,
                               'can_cancel': (
                                   lane.cancelled_at is None
                                   and lane.sequence > 1
                                   and not AddaStageRecord.objects.filter(
                                       stream=lane).exists())})
        ctx['lane_cards'] = lane_cards
        live_count = sum(1 for c in lane_cards if not c['cancelled'])
        ctx['show_lanes'] = live_count > 1 or any(
            c['cancelled'] for c in lane_cards)
        ctx['fabric_groups'] = sorted({l.fabric_group for l in lanes})
        ctx['can_add_lane'] = (adda.status != Adda.Status.COMPLETED)
        # GAP-5: the join is a derived predicate, not the coarse pointer —
        # non-blocking lanes must never hold the readiness/bundling surface.
        from production.services.adda_service import preproduction_joined
        ctx['preproduction_joined'] = preproduction_joined(adda)
        # Garment Readiness (GAP-5, derive-only — pool_service stores nothing):
        # management, post-join, multi-component products only.
        ctx['garment_readiness'] = None
        from accounts.services import MANAGEMENT_ROLES as _MR, user_has_role as _uhr
        if ctx['preproduction_joined'] and _uhr(self.request.user, _MR):
            from production.services import pool_service
            ctx['garment_readiness'] = pool_service.garment_readiness(adda)

        # ── Per-stage RBAC gate (SKILL-driven via the Stage model) ───────────
        # access_service.stage_access_map reads Stage.access_by_skill (+ optional
        # access_by_role), OR semantics; super_admin + manager always pass
        # (built-in defense). Admins edit access on the Stage library
        # (/production/stages/). (Old StageAccessRule table was dropped in
        # migration 0011.)
        from accounts.services import MANAGEMENT_ROLES, ROLE_SUPER_ADMIN, user_has_role
        from production.services import stage_access_map

        user = self.request.user
        is_management = user_has_role(user, MANAGEMENT_ROLES)
        # S1.1: super-admin "Stage Rates" entry (rate correction) is gated here.
        ctx['is_super_admin'] = user_has_role(user, [ROLE_SUPER_ADMIN])
        access_by_type = stage_access_map(user, [s.stage_type for s in stages])
        has_layering_access = access_by_type.get('layering', False)

        # Annotate each WorkflowStage with .has_access so the template can gate
        # iframes per-stage without redoing the skill check in Django templates.
        for s in stages:
            s.has_access = access_by_type.get(s.stage_type, False)

        can_act_on_current = (
            adda.current_stage is not None
            and access_by_type.get(adda.current_stage.stage_type, False)
        )

        # Stage records keyed by stage_type for template lookup.
        # select_related = forward + reverse OneToOne (single FK join).
        # prefetch_related = M2M + reverse FK (separate query, joined in Python).
        sr_qs = (
            adda.stage_records
            .select_related('workflow_stage', 'completed_by', 'layering', 'cutting')
            .prefetch_related(
                'worker_tasks__worker',   # V2-1b: feeds active_workers (no N+1) — replaces M2M prefetch
                'layering__rolls_used__cloth_type',
                'layering__rolls_used__cloth_color',
                'layering_roll_entries__roll__cloth_type',
                'layering_roll_entries__roll__cloth_color',
                'layering_roll_entries__attached_by',
            )
        )
        sr_by_type = {sr.workflow_stage.stage_type: sr for sr in sr_qs}

        # C-2 (freeze closeout 2026-07-05): the iframe gate must mirror
        # StageViewAccessMixin EXACTLY — access AND (management OR actively
        # assigned to that stage record). `has_access` alone still rendered
        # iframes a skilled-but-UNASSIGNED worker couldn't open (the panel's
        # assignment gate 403s → Chrome paints "refused to connect"). Uses the
        # already-prefetched worker_tasks — zero extra queries.
        for s in stages:
            sr = sr_by_type.get(s.stage_type)
            s.can_open = s.has_access and (
                is_management or (sr is not None and sr.is_worker_assigned(user))
            )

        # Default tab: current stage_type or last stage if completed
        if adda.current_stage is not None:
            default_tab = adda.current_stage.stage_type
        elif stages:
            default_tab = stages[-1].stage_type
        else:
            default_tab = ''

        # Lazy import — activity_service depends on tracking models
        from production.services import adda_activity, get_layering_snapshot, get_pattern_snapshot
        from production.stages import base as stage_registry
        activity = adda_activity(adda, limit=50)

        # Per-stage snapshot map — drives the "Stages Overview" panel above the
        # flow card. Registry-driven (M2.6): every flow stage with a handler
        # contributes its snapshot, so adding a stage needs no edit here. The
        # template renders tiles only for the stages it knows; any extra snapshot
        # is simply unused — rendered output is unchanged.
        snap_by_type = {
            s.stage_type: stage_registry.get(s.stage_type).snapshot(adda)
            for s in stages if stage_registry.has(s.stage_type)
        }
        # Layering/pattern panels consume these directly; the handlers' snapshot()
        # delegates to the SAME functions, so reuse instead of computing twice.
        layering_snap = snap_by_type.get('layering') or get_layering_snapshot(adda)
        pattern_snap = snap_by_type.get('cutting_pattern') or get_pattern_snapshot(adda)
        stages_overview = []
        for s in stages:
            snap = snap_by_type.get(s.stage_type)
            sr = sr_by_type.get(s.stage_type)
            # state = 'completed' | 'in_progress' | 'pending'
            if sr and sr.completed_at:
                state = 'completed'
            elif (s.stage_type in PRE_PRODUCTION_STAGE_CODES
                  and ctx.get('preproduction_joined')):
                # GAP-4 presentation: once the join fired, pre-production IS
                # complete — an untouched non-blocking lane's auto-created
                # record must not hold the phase count open forever.
                state = 'completed'
            elif adda.status == Adda.Status.COMPLETED:
                state = 'completed'
            elif adda.current_stage and adda.current_stage.order == s.order:
                state = 'in_progress'
            elif adda.current_stage and adda.current_stage.order > s.order:
                state = 'completed'
            else:
                state = 'pending'
            stages_overview.append({
                'workflow_stage': s,
                'stage_type': s.stage_type,
                'label': s.get_stage_type_display(),
                'state': state,
                'snap': snap,
                'sr': sr,
                'has_access': s.has_access,
            })

        # R10-B UI philosophy: category grouping (presentation ONLY — the
        # loop above stayed in flow order; single-category flows render flat).
        from production.views.presentation import grouped_or_flat
        overview_groups, overview_grouped = grouped_or_flat(
            stages_overview, stage_of=lambda e: e['workflow_stage'].stage)
        for g in overview_groups:
            g['total'] = len(g['items'])
            g['done'] = sum(1 for e in g['items'] if e['state'] == 'completed')
            g['open'] = any(e['state'] == 'in_progress' for e in g['items'])
        ctx['overview_groups'], ctx['overview_grouped'] = overview_groups, overview_grouped

        # ── A360 (plan v2): the per-Adda management overview — READ-ONLY
        # aggregation of existing truth, stage-generic (see views/a360.py).
        # MANAGEMENT-ONLY ctx: workers never receive a byte of it (leak-tested).
        if is_management:
            from production.views.a360 import build_a360
            _gr = ctx.get('garment_readiness')
            ctx['a360'] = build_a360(
                adda, stages_overview,
                garment_sets=(_gr['total_sets'] if _gr else None))

        # ── R1 (PDD §23): management navigation — state-aware Settlement button.
        # Latest AddaSettlement decides the target: exists → its detail page,
        # none → the settlement start page. READ-ONLY (navigation only, no
        # settlement behavior change). Query gated to management — workers
        # never load settlement data for this page (no leak, no cost).
        adda_settlement = None
        if is_management:
            adda_settlement = adda.settlements.order_by('-created_at').first()

        # ── R1 (PDD §27-D7): "My Work" — the viewing user's OWN tasks on this
        # Adda. PRESENTATION-ONLY (owner clarification: display, never
        # submit/edit — future phases own worker actions). Strictly self-scoped
        # (worker=request.user), so one worker can never see another's numbers
        # here (leak-tested). expected_earning shown is the user's own frozen
        # visibility figure (Option B) — never money.
        from decimal import Decimal
        from production.models import WorkerStageTask
        my_tasks = list(
            WorkerStageTask.objects
            .filter(stage_record__adda=adda, worker=user)
            .exclude(status=WorkerStageTask.Status.CANCELLED)
            .select_related('stage_record__workflow_stage__stage')
            .prefetch_related('contributions__color', 'contributions__size')
            .order_by('stage_record__workflow_stage__order')
        )
        from production.stages import base as stage_registry
        # R4 (PDD §27-D4/P-4): monthly worker → quantities stay (production
        # truth) but the ₹ expectation is suppressed entirely. Deferred import
        # keeps the production→expense edge view-local (services stay clean).
        from expense.services import payroll_service
        viewer_is_monthly = bool(my_tasks) and payroll_service.is_monthly(user)
        my_expected_total = Decimal('0.00')
        for t in my_tasks:
            lines = t.contributions.all()
            t.my_qty = sum((c.good_quantity for c in lines), Decimal('0'))
            t.my_expected = sum(
                (c.expected_earning for c in lines if c.expected_earning is not None),
                Decimal('0.00'))
            my_expected_total += t.my_expected
            # R2: unit label from the stage's contribution schema (layering =
            # "layers", others default "pieces") — registry-driven, no stage names.
            st = t.stage_record.workflow_stage.stage_type
            t.unit_label = 'pcs'
            if stage_registry.has(st):
                qf = [f for f in stage_registry.get(st).contribution_schema(adda)['fields']
                      if f['kind'] == 'quantity']
                if qf:
                    t.unit_label = qf[0].get('unit', 'pcs')

        ctx.update({
            'adda_settlement': adda_settlement,
            'my_tasks': my_tasks,
            'my_expected_total': my_expected_total,
            'viewer_is_monthly': viewer_is_monthly,
            'rolls': (
                adda.rolls.select_related('cloth_type', 'cloth_color').all()
                if hasattr(adda, 'rolls') else []
            ),
            'stages': stages,
            'stage_records': sr_qs.order_by('workflow_stage__order'),
            'sr_by_type': sr_by_type,
            'default_tab': default_tab,
            'activity': activity,
            'layering_snap': layering_snap,
            'pattern_snap': pattern_snap,
            'stages_overview': stages_overview,
            'is_management': is_management,
            'has_layering_access': has_layering_access,
            'can_act_on_current': can_act_on_current,
        })
        return ctx


class AddaBundleSetsView(LoginRequiredMixin, ManagementRoleMixin, DetailView):
    """GAP-5 one-tap slip from the Garment Readiness panel: bundle every
    currently-complete unbundled set of ONE size. POST-only; the service owns
    every gate (post-join, takes ≤ available); the derive owns the number."""
    model = Adda
    slug_field = 'code'
    slug_url_kwarg = 'code'
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        adda = self.get_object()
        from production.stages.cutting.service import bundle_ready_sets
        try:
            size_id = int(request.POST.get('size_id') or 0)
            bundle, sets = bundle_ready_sets(adda=adda, size_id=size_id,
                                             user=request.user)
            messages.success(
                request,
                f"Bundled {sets} complete garment set(s) — bundle "
                f"{bundle.bundle_number or bundle.pk} now holds "
                f"{bundle.total_pieces} pieces.")
        except (ValidationError, ValueError) as e:
            msg = e.messages[0] if hasattr(e, 'messages') else str(e)
            messages.error(request, msg)
        return redirect('production:adda-detail', code=adda.code)


class AddaAddLaneView(LoginRequiredMixin, ManagementRoleMixin, DetailView):
    """GAP-4: the Add-lane form (CUTTING_STREAM_LIFECYCLE §1–§9 verbatim).
    GET = confirm-with-context (existing lanes + live state per §9.1);
    POST = adda_service.add_stream (the sole stream writer — §5 lock, §6
    group-exists, §3 mandatory reason, §9.5 history event)."""
    model = Adda
    template_name = 'production/adda_add_lane.html'
    context_object_name = 'adda'
    slug_field = 'code'
    slug_url_kwarg = 'code'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        adda = self.object
        from production.models import AddaStageRecord, CuttingStream
        from production.services.adda_service import PRE_PRODUCTION_STAGE_CODES
        lanes = list(CuttingStream.objects.filter(adda=adda)
                     .order_by('fabric_group', 'sequence'))
        done_cut = set(AddaStageRecord.objects.filter(
            adda=adda, workflow_stage__stage__code='cutting',
            completed_at__isnull=False).values_list('stream_id', flat=True))
        for lane in lanes:
            lane.live_state = ('cancelled' if lane.cancelled_at
                               else 'cut complete' if lane.pk in done_cut
                               else 'in progress')
        ctx['lanes'] = lanes
        ctx['fabric_groups'] = sorted({l.fabric_group for l in lanes})
        # §3 suggested picks — reasons are DATA; free text always allowed.
        ctx['reason_picks'] = ['Fabric shortage', 'Recut',
                               'Additional production', 'Split lay',
                               'New color lot']
        return ctx

    def post(self, request, *args, **kwargs):
        adda = self.get_object()
        from production.services.adda_service import add_stream
        reason_pick = (request.POST.get('reason_pick') or '').strip()
        reason_text = (request.POST.get('reason') or '').strip()
        reason = (f'{reason_pick} — {reason_text}' if reason_pick and reason_text
                  else reason_pick or reason_text)
        try:
            lane = add_stream(adda,
                              fabric_group=request.POST.get('fabric_group', ''),
                              reason=reason, user=request.user)
            messages.success(
                request,
                f"Lane added: {lane.label} — crews are rostered through the "
                "normal stage forms; nothing that already happened moved.")
            return redirect('production:adda-detail', code=adda.code)
        except (ValidationError, PermissionDenied) as e:
            msg = e.messages[0] if hasattr(e, 'messages') else str(e)
            messages.error(request, msg)
            return redirect('production:adda-add-lane', code=adda.code)


class AddaCancelLaneView(LoginRequiredMixin, ManagementRoleMixin, DetailView):
    """GAP-4: cancel-if-empty (§9.4) — POST-only; the service owns every guard
    (empty-only, never seq-1, mandatory reason, append-only event)."""
    model = Adda
    slug_field = 'code'
    slug_url_kwarg = 'code'
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        adda = self.get_object()
        from production.services.adda_service import cancel_stream
        try:
            lane = cancel_stream(
                adda, stream=int(request.POST.get('stream') or 0),
                reason=(request.POST.get('reason') or '').strip(),
                user=request.user)
            messages.success(request,
                             f"Lane cancelled: {lane.label} — it stays on the "
                             "record, greyed, with its reason.")
        except (ValidationError, PermissionDenied) as e:
            msg = e.messages[0] if hasattr(e, 'messages') else str(e)
            messages.error(request, msg)
        return redirect('production:adda-detail', code=adda.code)
