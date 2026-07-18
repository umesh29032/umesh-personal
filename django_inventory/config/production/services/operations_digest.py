"""Operations digest — the management "morning pulse" for the Operations landing
(P1-1). Six tiles, in the owner-locked priority order, ALL derived from data that
exists today (timestamps, tasks, ledger, advances). Foundation-INDEPENDENT: it
reads no allocation / good-alter-missing fields, so it ships before the
Production-Truth Foundation and gains nothing from it (the stage-loss view that
WOULD need the foundation is deliberately NOT here — see Phase H / H-1).

Management-gated by the caller (the view), not here — this is a pure read.
"""
from datetime import timedelta


from django.conf import settings
from django.utils import timezone


def stalled_stage_records():
    """THE single stalled-detection path (H-2B): open stages on in-progress Addas
    that haven't moved in STALLED_ADDA_DAYS, oldest-first (= longest stalled first).
    Shared by the digest tile (count) AND the drill-down view (list), so the two
    ALWAYS reconcile — there is no second stalled-calculation anywhere."""
    from production.models import Adda, AddaStageRecord
    cutoff = timezone.now() - timedelta(days=getattr(settings, 'STALLED_ADDA_DAYS', 3))
    return (
        AddaStageRecord.objects
        .filter(adda__status=Adda.Status.IN_PROGRESS,
                completed_at__isnull=True,
                started_at__isnull=False,
                started_at__lt=cutoff)
        .select_related('adda', 'adda__product', 'workflow_stage__stage')
        .order_by('started_at')
    )


def pending_report_tasks():
    """THE single pending-report path (F-3): actionable worker tasks — assigned or
    in-progress on a still-OPEN stage (a worker is on the hook but hasn't
    submitted). Oldest-first (= longest waiting first). Shared by the digest tile
    (count) AND the drill-down view (list) so the two ALWAYS reconcile. Reuses the
    WorkerStageTask lifecycle only — no allocation logic (foundation scope)."""
    from production.models import WorkerStageTask
    return (
        WorkerStageTask.objects
        .filter(status__in=(WorkerStageTask.Status.ASSIGNED,
                            WorkerStageTask.Status.IN_PROGRESS),
                stage_record__completed_at__isnull=True)
        .select_related('worker', 'stage_record__adda__product',
                        'stage_record__workflow_stage__stage')
        .order_by('created_at')
    )


def adda_status_counts(*, from_dt=None, to_dt=None, fields=None) -> dict:
    """G-4 (BOD-C, 2026-07-18, owner-gated): the Adda dashboard's KPI counts,
    extracted VERBATIM from AddaDashboardView — one calculation, two consumers
    (that page + the BOD on-hold tile). Same filter semantics: from/to bound
    created_at; completed_today is deliberately GLOBAL (today's date, unfiltered),
    exactly as the dashboard always showed it.

    fields (BOD-D, 2026-07-18): optional subset — run ONLY the named counts
    (same expressions, ONE calculation site; a consumer needing one number
    shouldn't pay for four — BOD-D6). None = all four (the dashboard call,
    unchanged)."""
    from production.models import Adda
    addas = Adda.objects.all()
    if from_dt:
        addas = addas.filter(created_at__gte=from_dt)
    if to_dt:
        addas = addas.filter(created_at__lt=to_dt)
    wanted = set(fields) if fields is not None else {
        'in_progress', 'on_hold', 'completed_today', 'total_completed'}
    out = {}
    if 'in_progress' in wanted:
        out['in_progress'] = addas.filter(status=Adda.Status.IN_PROGRESS).count()
    if 'on_hold' in wanted:
        out['on_hold'] = addas.filter(status=Adda.Status.ON_HOLD).count()
    if 'completed_today' in wanted:
        out['completed_today'] = Adda.objects.filter(
            status=Adda.Status.COMPLETED,
            completed_at__date=timezone.now().date(),
        ).count()
    if 'total_completed' in wanted:
        out['total_completed'] = addas.filter(status=Adda.Status.COMPLETED).count()
    return out


def stage_breakdown(*, from_dt=None, to_dt=None) -> list:
    """G-4 (BOD-C, 2026-07-18, owner-gated): in-progress Adda count per stage,
    extracted VERBATIM from AddaDashboardView (single grouped aggregate, no N+1;
    only stages actually holding an in-progress Adda — zero-chips stay hidden)."""
    from django.db.models import Count
    from production.models import Adda, Stage
    addas = Adda.objects.all()
    if from_dt:
        addas = addas.filter(created_at__gte=from_dt)
    if to_dt:
        addas = addas.filter(created_at__lt=to_dt)
    stage_counts = {
        r['current_stage__stage']: r['n']
        for r in addas.filter(
            status=Adda.Status.IN_PROGRESS,
            current_stage__stage__isnull=False,
        ).values('current_stage__stage').annotate(n=Count('id'))
    }
    return [
        {'label': stage.name, 'count': stage_counts.get(stage.id, 0)}
        for stage in Stage.active.order_by('name')
        if stage_counts.get(stage.id, 0) > 0
    ]


def operations_digest() -> dict:
    """Return the six digest tiles (priority order):
      1. stalled Addas   2. pending reports   3. active Addas
      4. completed today 5. pending payable   6. advance exposure
    """
    from production.models import Adda
    from expense.services import payroll_service

    now = timezone.now()
    threshold_days = getattr(settings, 'STALLED_ADDA_DAYS', 3)

    # 1. Stalled — SINGLE source (shared with the drill-down → always reconciles).
    stalled_qs = stalled_stage_records()
    stalled_count = stalled_qs.values('adda').distinct().count()
    stalled_top = list(stalled_qs[:5])

    # 2. Pending reports — SINGLE source (shared with the drill-down → reconciles).
    pending_reports = pending_report_tasks().count()

    # 3. Active + 4. completed today (global, not date-filtered like the KPI cards)
    active_addas = Adda.objects.filter(status=Adda.Status.IN_PROGRESS).count()
    completed_today = Adda.objects.filter(
        status=Adda.Status.COMPLETED,
        completed_at__date=now.date(),
    ).count()

    # 5 + 6. Money (reuses the payroll overview's exact definitions)
    totals = payroll_service.payroll_totals()

    return {
        'stalled_count': stalled_count,
        'stalled_top': stalled_top,
        'stalled_threshold_days': threshold_days,
        'pending_reports': pending_reports,
        'active_addas': active_addas,
        'completed_today': completed_today,
        'pending_payable': totals['pending_payable'],
        'advance_exposure': totals['advance_exposure'],
    }
