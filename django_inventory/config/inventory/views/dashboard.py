"""Dashboard views — unified for admin + non-admin.

YEH FILE KYU HAI?
─────────────────
Pehle do alag dashboards the (admin ka khaali "WIP" page + user ka active-addas page).
Ab dono same content render karte hain — single "Dashboard" har user role ke liye.

Role-aware sections:
  • Active Addas list      — sab logged-in users ko dikhta hai
  • Skilled accordion       — sirf cutting_master / _helper / management → iframe inline panel
  • Read-only status card   — non-skilled users ke liye (no buttons)
  • Helper stats             — sirf cutting_master_helper users
  • My Recent Activity       — cross-Adda timeline (sab users)
  • is_admin_view flag       — future admin-only metrics ke liye reserved
"""
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Exists, OuterRef, Q, Sum
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone

from ..services import (
    FINANCIAL_ROLES, MANAGEMENT_ROLES, user_does_production_work, user_has_role,
)


def _build_dashboard_context(request, *, is_admin_view: bool) -> dict:
    """Common context builder. Both admin + user dashboard URLs call this."""
    my_active_stages = []
    helper_data = None
    my_activity = []
    active_addas = []
    broadcast_addas = []
    is_skilled_user = False

    try:
        from production.constants import STAGE_LAYERING
        from production.models import Adda, AddaStageRecord, LayeringRecord, WorkerStageTask
        from production.services import user_activity_across_addas

        # R1: role checked ONCE, reused below (skilled gate + isolation +
        # broadcast) — avoids re-querying extra_roles per check.
        is_mgmt = user_has_role(request.user, MANAGEMENT_ROLES)
        # C-2 (freeze closeout 2026-07-05): visibility derives from the LIVE
        # Stage-Access rows (access_service — the single predicate), never
        # from hardcoded skill constants. Access-hub edits reflect instantly.
        from production.services import stage_access_map

        # In-progress Addas — annotated with rolls count + per-stage pipeline state.
        addas_qs = Adda.objects.filter(status=Adda.Status.IN_PROGRESS)
        # V2-1c-iv isolation: a worker sees ONLY Addas they're actively assigned to
        # (an active WorkerStageTask on any stage). Management sees all. Exists()
        # avoids a join so the rolls_count annotation stays correct.
        if not is_mgmt:
            assigned = WorkerStageTask.objects.filter(
                stage_record__adda=OuterRef('pk'), worker=request.user,
            ).exclude(status=WorkerStageTask.Status.CANCELLED)
            addas_qs = addas_qs.filter(Exists(assigned))
        active_addas = list(
            addas_qs
            .select_related('product', 'current_stage')
            .prefetch_related('stage_records__workflow_stage', 'product__workflow_stages')
            .annotate(rolls_count=Count('rolls'))
            .order_by('-started_at')
        )
        # C-2: workspace accordions render ONLY what the viewer can actually
        # open — the SAME rule the panel gate enforces (access AND, for
        # workers, an active assignment on that stage record). The pipeline
        # CHIPS stay unfiltered on purpose (flow-shape status summary, not a
        # workspace). my_active_stages is fetched HERE so the whole page needs
        # exactly ONE stage_access_map call (perf: one principal+Stage fetch).
        my_active_stages = list(
            AddaStageRecord.objects
            # V2-1b: "assigned to me" = an active WorkerStageTask (not the M2M).
            .filter(worker_tasks__worker=request.user,
                    worker_tasks__status__in=WorkerStageTask.ACTIVE_STATUSES,
                    completed_at__isnull=True,
                    adda__status=Adda.Status.IN_PROGRESS)
            .select_related('adda', 'workflow_stage__stage', 'adda__product')
            .order_by('-created_at')
            .distinct()
        )
        all_types = sorted(
            {ws.stage_type
             for a in active_addas for ws in a.product.workflow_stages.all()}
            | {sr.workflow_stage.stage_type for sr in my_active_stages}
            | {STAGE_LAYERING}
        )
        access_by_type = stage_access_map(request.user, all_types)
        # "Skilled user" kept as the template's variable name; its VALUE is now
        # "may access the layering stage" (management always True via the map).
        is_skilled_user = access_by_type.get(STAGE_LAYERING, False)
        if is_mgmt:
            my_sr_ids = None                       # management opens everything
        else:
            my_sr_ids = set(
                WorkerStageTask.objects
                .filter(stage_record__adda__in=active_addas, worker=request.user)
                .exclude(status=WorkerStageTask.Status.CANCELLED)
                .values_list('stage_record_id', flat=True)
            )
        sr_id_by_adda_type = {
            (sr.adda_id, sr.workflow_stage.stage_type): sr.pk
            for a in active_addas for sr in a.stage_records.all()
        }

        def _can_open(adda, stage_type):
            if not access_by_type.get(stage_type, False):
                return False
            if my_sr_ids is None:
                return True
            sr_id = sr_id_by_adda_type.get((adda.pk, stage_type))
            return sr_id is not None and sr_id in my_sr_ids

        for a in active_addas:
            pipeline = []
            done_stages = []  # (label, stage_type) for revisit links — dashboard accordion
            # Use the prefetched workflow_stages (.all() hits the prefetch cache).
            # `.order_by()` here would issue a FRESH query per Adda (N+1) — sort
            # in Python on the cached rows instead.
            for s in sorted(a.product.workflow_stages.all(), key=lambda ws: ws.order):
                if a.current_stage and a.current_stage.order == s.order:
                    state = 'current'
                elif a.current_stage and a.current_stage.order > s.order:
                    state = 'done'
                else:
                    state = 'pending'
                pipeline.append({
                    'label': s.get_stage_type_display(),
                    'state': state,
                    'stage_type': s.stage_type,
                })
                if state == 'done' and _can_open(a, s.stage_type):
                    done_stages.append({
                        'label': s.get_stage_type_display(),
                        'stage_type': s.stage_type,
                    })
            a.pipeline = pipeline
            a.done_stages = done_stages
            a.current_can_open = (
                a.current_stage is not None
                and _can_open(a, a.current_stage.stage_type)
            )
            # R10-B UI philosophy: workers get CURRENT-OPERATION focus, never
            # the full pipeline (prev ✔ / current / next only).
            cur_i = next((i for i, st in enumerate(pipeline)
                          if st['state'] == 'current'), None)
            a.current_focus = None if cur_i is None else {
                'prev': pipeline[cur_i - 1]['label'] if cur_i > 0 else None,
                'current': pipeline[cur_i]['label'],
                'next': pipeline[cur_i + 1]['label'] if cur_i + 1 < len(pipeline) else None,
            }

        # R1 (PDD §27-D6): "new Adda started" broadcast — every worker sees that
        # production started. Read-only: code/product/start date ONLY (no
        # financials, no task link — the assigned list above stays the
        # actionable set). Management already sees all Addas → worker-only.
        if not is_mgmt:
            broadcast_addas = list(
                Adda.objects.filter(status=Adda.Status.IN_PROGRESS)
                .exclude(pk__in=[a.pk for a in active_addas])
                .select_related('product')
                .order_by('-started_at')[:5]
            )
        # P5.1: the layering snapshot is rendered ONLY in the skilled-user accordion.
        # Bulk-attach it (a fixed handful of queries, N+1-free) for skilled users;
        # skip entirely for everyone else (it's never rendered).
        if is_skilled_user:
            from production.services import attach_layering_snapshots
            attach_layering_snapshots(active_addas)
        else:
            for a in active_addas:
                a.layering_snap = None

        # (my_active_stages was fetched ABOVE, before the single access-map call.)
        # C-2: assignment alone is not visibility — if Stage Access was revoked
        # AFTER assignment, the row must vanish here too (the report/panel
        # gates already refuse it; a dead link would violate minimum-info).
        my_active_stages = [
            sr for sr in my_active_stages
            if access_by_type.get(sr.workflow_stage.stage_type, False)
        ]
        # pt.2c: report badge per assigned stage — ONE extra query for all my
        # tasks (annotate counts lines), then attach in Python. Badge states:
        # submitted (task completed/verified) > draft (has lines) > needed.
        my_report_tasks = (
            WorkerStageTask.objects
            .filter(worker=request.user,
                    stage_record__in=[sr.pk for sr in my_active_stages])
            .exclude(status=WorkerStageTask.Status.CANCELLED)
            .annotate(n_lines=Count('contributions'))
        )
        task_by_sr = {t.stage_record_id: t for t in my_report_tasks}
        for sr in my_active_stages:
            t = task_by_sr.get(sr.pk)
            if t is None:
                sr.report_badge = None
            elif t.status in (WorkerStageTask.Status.COMPLETED,
                              WorkerStageTask.Status.VERIFIED):
                sr.report_badge = 'submitted'
            elif t.n_lines:
                sr.report_badge = 'draft'
            else:
                sr.report_badge = 'needed'
        my_activity = user_activity_across_addas(request.user, limit=30)

        # C-2: the layering board is gated by LIVE layering ACCESS (was a
        # hardcoded helper-skill check), and non-management see only the
        # layerings they're actually assigned to (same isolation rule as the
        # Adda cards — no dead OPEN links to 403 workspaces).
        if is_skilled_user:
            active_layering = (
                AddaStageRecord.objects
                .filter(
                    workflow_stage__stage__code=STAGE_LAYERING,
                    completed_at__isnull=True,
                    started_at__isnull=False,
                    adda__status=Adda.Status.IN_PROGRESS,
                )
                .select_related('adda', 'workflow_stage', 'adda__product')
                .prefetch_related('worker_tasks__worker')   # V2-1b: feeds active_workers (no N+1)
                .annotate(rolls_count=Count('layering_roll_entries'))
                .order_by('-started_at')
            )
            if not is_mgmt:
                active_layering = active_layering.filter(
                    worker_tasks__worker=request.user,
                    worker_tasks__status__in=WorkerStageTask.ACTIVE_STATUSES,
                ).distinct()
            completed_qs = LayeringRecord.objects.filter(
                stage_record__completed_by=request.user,
            )
            active_assigned_qs = active_layering.filter(
                worker_tasks__worker=request.user,
                worker_tasks__status__in=WorkerStageTask.ACTIVE_STATUSES,
            ).distinct()
            stats = completed_qs.aggregate(
                total_layers=Sum('lay_count'),
                total_minutes=Sum('duration_minutes'),
            )
            helper_data = {
                'active_layering': active_layering,
                'completed_count': completed_qs.count(),
                'active_assigned_count': active_assigned_qs.count(),
                'total_layers': stats.get('total_layers') or 0,
                'total_minutes': stats.get('total_minutes') or 0,
            }
    except Exception:
        # Production tables not migrated yet — hide panels gracefully
        my_active_stages = []
        helper_data = None
        my_activity = []
        active_addas = []
        broadcast_addas = []
        is_skilled_user = False

    # R5 (PDD §21/§23): this-month factory-expense digest — management only
    # (workers never load expense data for their dashboard). Read-only ctx,
    # same graceful-degrade posture as the production panels above.
    # Owner ruling 2026-08-02: an ACCOUNTANT gets this digest too — it is the
    # centre of their job, not an admin extra. Same read-only, graceful-degrade
    # posture; no write path is opened by showing a total.
    expense_month = None
    show_expense_digest = is_admin_view or user_has_role(
        request.user, FINANCIAL_ROLES)
    if show_expense_digest:
        try:
            from expense.services import expense_service
            today = timezone.localdate()
            expense_month = expense_service.monthly_totals(today.year, today.month)
            expense_month['month_value'] = f"{today.year:04d}-{today.month:02d}"
        except Exception:
            expense_month = None

    # ── The accountant panel (owner ruling 2026-08-02) ───────────────────────
    # A financial reader who is NOT management previously landed on the WORKER
    # dashboard. Give them the three numbers their job actually starts from, all
    # derived live (never stored), all read-only:
    #   • unpriced rolls  — the honest-NULL policy shows a roll as "unpriced"
    #                       rather than ₹0, and chasing those is bookkeeping work
    #                       nobody currently owned;
    #   • advances outstanding — money lent that must come back;
    #   • settlements this month — what has actually been paid out.
    accounts_panel = None
    if not is_admin_view and user_has_role(request.user, FINANCIAL_ROLES):
        accounts_panel = {}
        try:
            # NOTE: Count/Q/Sum come from the MODULE-level import above. Importing
            # them locally here made Python treat them as function locals for the
            # WHOLE function, breaking two earlier uses (ruff F823 caught it).
            from expense.models import PayrollSettlement
            from expense.services import payroll_service
            from raw_materials.models import ClothRoll
            today = timezone.localdate()
            rolls = ClothRoll.objects.aggregate(
                total=Count('id'),
                unpriced=Count('id', filter=Q(cost_per_kg__isnull=True)),
            )
            accounts_panel['rolls_total'] = rolls['total'] or 0
            accounts_panel['rolls_unpriced'] = rolls['unpriced'] or 0
            # REUSE the canonical aggregate — never re-derive money here. It
            # already excludes REVERSED recoveries (PA-12-A); a hand-rolled
            # "unrecovered advances" sum would understate exposure after any
            # settlement reversal, and `WorkerAdvance` has no is_recovered flag
            # because recovery is derived, not stored.
            totals = payroll_service.payroll_totals()
            accounts_panel['advance_exposure'] = totals['advance_exposure']
            accounts_panel['pending_payable'] = totals['pending_payable']
            paid = PayrollSettlement.objects.filter(
                settlement_date__year=today.year,
                settlement_date__month=today.month,
            ).aggregate(n=Count('id'), total=Sum('amount_paid'))
            accounts_panel['settlements_count'] = paid['n'] or 0
            accounts_panel['settlements_total'] = paid['total']
        except Exception:
            # Same posture as every other panel here: a missing field or a
            # not-ready DB must degrade to "no panel", never a 500 on login.
            accounts_panel = None

    # Owner feedback 2026-08-02: the page had only TWO modes — management, or
    # "everyone else = worker". So an accountant/listing_team/student saw worker
    # copy ("Jab manager aapko kaam dega") and an empty assigned-work panel. This
    # third flag lets the template stay silent instead of speaking to the wrong
    # person. Management is unaffected (they get the admin view either way).
    # Only the NON-admin branch of the template renders worker copy, and the
    # predicate's safety clause costs one EXISTS for a person with no worker role
    # and no skills — i.e. exactly management. Skip it for them: they never see
    # the block it controls. (The sidebar's "My Earnings" predicate computes it
    # lazily and request-caches, so a manager who genuinely has earnings still
    # gets the menu item.)
    does_floor_work = (False if is_admin_view
                       else user_does_production_work(request.user))

    return {
        'is_admin_view': is_admin_view,
        'does_floor_work': does_floor_work,
        'my_active_stages': my_active_stages,
        'helper_data': helper_data,
        'my_activity': my_activity,
        'active_addas': active_addas,
        'broadcast_addas': broadcast_addas,
        'is_skilled_user': is_skilled_user,
        'expense_month': expense_month,
        'accounts_panel': accounts_panel,
    }


@login_required
def user_dashboard(request):
    """THE personal dashboard (canonical url_name `inventory:my_dashboard`).

    F-1 polish (2026-07-05): the historical management/worker URL twins now
    both redirect here — one page, one menu item, same role-aware content
    (`is_admin_view` computed from role, not from which URL was hit).
    """
    ctx = _build_dashboard_context(
        request,
        is_admin_view=user_has_role(request.user, MANAGEMENT_ROLES),
    )
    return render(request, 'inventory/user_dashboard.html', ctx)


@login_required
def dashboard_redirect(request):
    """Backward-compat: old bookmark URLs 301 to the canonical dashboard."""
    # HttpResponsePermanentRedirect via redirect(permanent=True) — browsers
    # update bookmarks; content identical so a permanent redirect is safe.
    return redirect(reverse('inventory:my_dashboard'), permanent=True)
