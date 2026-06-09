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
from django.db.models import Count, Exists, OuterRef, Sum
from django.shortcuts import render

from ..services import MANAGEMENT_ROLES, user_has_role


def _build_dashboard_context(request, *, is_admin_view: bool) -> dict:
    """Common context builder. Both admin + user dashboard URLs call this."""
    my_active_stages = []
    helper_data = None
    my_activity = []
    active_addas = []
    is_skilled_user = False

    try:
        from production.constants import STAGE_LAYERING
        from production.models import Adda, AddaStageRecord, LayeringRecord, WorkerStageTask
        from production.services import user_activity_across_addas
        from accounts.skills import (
            SKILL_CUTTING_MASTER, SKILL_CUTTING_MASTER_HELPER, user_has_skill,
        )

        # "Skilled user" = layering skill OR management role.
        # Drives accordion vs status-card decision in template.
        is_skilled_user = (
            user_has_skill(request.user, [SKILL_CUTTING_MASTER, SKILL_CUTTING_MASTER_HELPER])
            or user_has_role(request.user, MANAGEMENT_ROLES)
        )

        # In-progress Addas — annotated with rolls count + per-stage pipeline state.
        addas_qs = Adda.objects.filter(status=Adda.Status.IN_PROGRESS)
        # V2-1c-iv isolation: a worker sees ONLY Addas they're actively assigned to
        # (an active WorkerStageTask on any stage). Management sees all. Exists()
        # avoids a join so the rolls_count annotation stays correct.
        if not user_has_role(request.user, MANAGEMENT_ROLES):
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
        from production.services import get_layering_snapshot
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
                if state == 'done':
                    done_stages.append({
                        'label': s.get_stage_type_display(),
                        'stage_type': s.stage_type,
                    })
            a.pipeline = pipeline
            a.done_stages = done_stages
            # Layering snapshot per Adda for per-stage info on user dashboard
            a.layering_snap = get_layering_snapshot(a)

        my_active_stages = (
            AddaStageRecord.objects
            # V2-1b: "assigned to me" = an active WorkerStageTask (not the M2M).
            .filter(worker_tasks__worker=request.user,
                    worker_tasks__status__in=WorkerStageTask.ACTIVE_STATUSES,
                    completed_at__isnull=True,
                    adda__status=Adda.Status.IN_PROGRESS)
            .select_related('adda', 'workflow_stage', 'adda__product')
            .order_by('-created_at')
            .distinct()
        )
        my_activity = user_activity_across_addas(request.user, limit=30)

        if user_has_skill(request.user, SKILL_CUTTING_MASTER_HELPER):
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
        is_skilled_user = False

    return {
        'is_admin_view': is_admin_view,
        'my_active_stages': my_active_stages,
        'helper_data': helper_data,
        'my_activity': my_activity,
        'active_addas': active_addas,
        'is_skilled_user': is_skilled_user,
    }


@login_required
def dashboard(request):
    """Unified dashboard URL for management roles.

    Same content as user_dashboard — just flagged is_admin_view=True so the
    template can show admin-only sections in the future. Both URLs are kept for
    backward-compat (sidebar uses one canonical link).
    """
    ctx = _build_dashboard_context(
        request,
        is_admin_view=user_has_role(request.user, MANAGEMENT_ROLES),
    )
    return render(request, 'inventory/user_dashboard.html', ctx)


@login_required
def user_dashboard(request):
    """Non-management dashboard URL. Renders the same unified template + content."""
    ctx = _build_dashboard_context(
        request,
        is_admin_view=user_has_role(request.user, MANAGEMENT_ROLES),
    )
    return render(request, 'inventory/user_dashboard.html', ctx)
