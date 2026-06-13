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


def operations_digest() -> dict:
    """Return the six digest tiles (priority order):
      1. stalled Addas   2. pending reports   3. active Addas
      4. completed today 5. pending payable   6. advance exposure
    """
    from production.models import Adda, AddaStageRecord, WorkerStageTask
    from expense.services import payroll_service

    now = timezone.now()
    threshold_days = getattr(settings, 'STALLED_ADDA_DAYS', 3)
    stalled_cutoff = now - timedelta(days=threshold_days)

    # 1. Stalled — in-progress Addas whose CURRENT open stage started before the
    #    cutoff (hasn't moved in `threshold_days`). Count distinct Addas; surface
    #    the oldest few for the drill list.
    stalled_qs = (
        AddaStageRecord.objects
        .filter(adda__status=Adda.Status.IN_PROGRESS,
                completed_at__isnull=True,
                started_at__isnull=False,
                started_at__lt=stalled_cutoff)
        .select_related('adda', 'workflow_stage__stage')
        .order_by('started_at')
    )
    stalled_count = stalled_qs.values('adda').distinct().count()
    stalled_top = list(stalled_qs[:5])

    # 2. Pending reports — assigned/in-progress tasks on still-open stages (a
    #    worker is on the hook but hasn't submitted). Surfacing this before the
    #    stage auto-cancels them (F3) is the point.
    pending_reports = (
        WorkerStageTask.objects
        .filter(status__in=(WorkerStageTask.Status.ASSIGNED,
                            WorkerStageTask.Status.IN_PROGRESS),
                stage_record__completed_at__isnull=True)
        .count()
    )

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
