"""Adda dashboard — /production/ ka backend.

YEH FILE KYU HAI?
─────────────────
KPI counts: in_progress, on_hold, completed_today, total_completed.
Stage breakdown chips: in-progress Adda count per stage_type.
Recent Addas table: top 12 by started_at DESC.
Date filter: ?from=&to= ke saath created_at range filter.
"""
from datetime import datetime, time

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Exists, OuterRef
from django.utils import timezone
from django.views.generic import TemplateView

from production.models import Adda, Stage

from .mixins import ProductionRoleMixin


def _parse_date(s):
    if not s:
        return None
    try:
        d = datetime.strptime(s, '%Y-%m-%d').date()
    except ValueError:
        return None
    return timezone.make_aware(datetime.combine(d, time.min))


class AddaDashboardView(LoginRequiredMixin, ProductionRoleMixin, TemplateView):
    template_name = 'production/adda_dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        from_dt = _parse_date(self.request.GET.get('from'))
        to_dt = _parse_date(self.request.GET.get('to'))
        if to_dt:
            to_dt = to_dt + timezone.timedelta(days=1)

        addas = Adda.objects.all()
        if from_dt:
            addas = addas.filter(created_at__gte=from_dt)
        if to_dt:
            addas = addas.filter(created_at__lt=to_dt)

        ctx['in_progress'] = addas.filter(status=Adda.Status.IN_PROGRESS).count()
        ctx['on_hold'] = addas.filter(status=Adda.Status.ON_HOLD).count()
        ctx['completed_today'] = Adda.objects.filter(
            status=Adda.Status.COMPLETED,
            completed_at__date=timezone.now().date(),
        ).count()
        ctx['total_completed'] = addas.filter(status=Adda.Status.COMPLETED).count()

        # Single grouped aggregate instead of one COUNT per stage (was N+1):
        # count in-progress Addas grouped by current stage, then map onto the
        # active Stage list.
        stage_counts = {
            r['current_stage__stage']: r['n']
            for r in addas.filter(
                status=Adda.Status.IN_PROGRESS,
                current_stage__stage__isnull=False,
            ).values('current_stage__stage').annotate(n=Count('id'))
        }
        stage_breakdown = [
            {'label': stage.name, 'count': stage_counts.get(stage.id, 0)}
            for stage in Stage.active.order_by('name')
        ]
        ctx['stage_breakdown'] = stage_breakdown

        recent = list(
            addas.select_related('product', 'current_stage')
            .prefetch_related('product__workflow_stages')
            .order_by('-started_at')[:12]
        )
        # Attach layering snapshot per Adda for the dashboard table (P5.1: bulk,
        # N+1-free — was one get_layering_snapshot() call per row).
        from production.services import attach_layering_snapshots
        attach_layering_snapshots(recent)
        ctx['recent'] = recent
        ctx['filter_from'] = self.request.GET.get('from', '')
        ctx['filter_to'] = self.request.GET.get('to', '')
        # Time logs — AddaHistory ke latest 30 events (accordion mein render)
        from tracking.models import AddaHistory
        ctx['adda_events'] = (
            AddaHistory.objects
            .select_related(
                'adda', 'adda__product', 'stage_from', 'stage_to',
                'roll', 'roll__cloth_type', 'roll__cloth_color', 'actor',
            )
            .order_by('-created_at')[:30]
        )

        # Operations digest (P1-1) — management-only morning pulse. This view is
        # the management LANDING (HomeView routes super_admin/manager here); the
        # digest is gated to management so workers who navigate here don't see
        # factory-wide money/pending counts.
        from accounts.services import MANAGEMENT_ROLES, user_has_role
        if user_has_role(self.request.user, MANAGEMENT_ROLES):
            from production.services.operations_digest import operations_digest
            ctx['digest'] = operations_digest()
        else:
            ctx['digest'] = None
        return ctx


class StalledAddaListView(LoginRequiredMixin, ProductionRoleMixin, TemplateView):
    """H-2B drill-down for the digest's Stalled Addas tile. Uses the SAME
    `stalled_stage_records()` as the digest (no second stalled-calc path → the
    tile count and this list always reconcile). Worker isolation: non-management
    see only stalled Addas they hold a live task on (same rule as the dashboard /
    history). Read-only — no settlement / costing / production-truth touch."""
    template_name = 'production/stalled_addas.html'

    def get_context_data(self, **kwargs):
        from django.conf import settings
        from accounts.services import MANAGEMENT_ROLES, user_has_role
        from production.models import WorkerStageTask
        from production.services.operations_digest import stalled_stage_records

        ctx = super().get_context_data(**kwargs)
        srs = stalled_stage_records()
        if not user_has_role(self.request.user, MANAGEMENT_ROLES):
            assigned = WorkerStageTask.objects.filter(
                stage_record__adda_id=OuterRef('adda_id'), worker=self.request.user,
            ).exclude(status=WorkerStageTask.Status.CANCELLED)
            srs = srs.filter(Exists(assigned))

        now = timezone.now()
        threshold = getattr(settings, 'STALLED_ADDA_DAYS', 3)
        seen, rows = set(), []
        for sr in srs:                       # started_at ASC → longest-stalled first
            if sr.adda_id in seen:
                continue                     # one row per Adda (oldest open stage)
            seen.add(sr.adda_id)
            days = (now - sr.started_at).days
            rows.append({
                'adda': sr.adda,
                'stage': sr.workflow_stage.stage.name,
                'status': sr.adda.get_status_display(),
                'days': days,
                'since': sr.started_at,
                'severity': 'critical' if days >= threshold * 2 else 'warning',
            })
        ctx['rows'] = rows
        ctx['threshold'] = threshold
        return ctx
