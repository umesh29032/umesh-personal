"""Bundle READ-MODEL (AE-1, owner bundle model 2026-07-20).

A *Manufacturing Bundle* is the business identity **(Adda, colour, size)** that flows through
every downstream stage. It is deliberately NOT a table — it is PROJECTED here over the existing
pool (`pool_service`) + `WorkerStageAllocation`. This keeps one source of truth for the quantity
(the per-stage pool) and gives the UI / worker dashboard / manager screen ONE vocabulary
("Red / M / 100"), exactly as approved in the Architecture Design Document (Option B).

Pure reads. No writes, no money math beyond surfacing the ALREADY-frozen
`WorkerStageContribution.expected_earning` (a visibility number, not a new calculation).
Generic — no stage-name conditionals; works for any COLOR_SIZE / QUANTITY pool stage.
"""
from decimal import Decimal

from production.services import pool_service

D0 = Decimal('0')


def _state(total, available):
    """Derived bundle state for the UI badge."""
    if available >= total:
        return 'unassigned'
    if available <= 0:
        return 'fully_assigned'
    return 'partial'


def _dim_rows(consuming_sr):
    """The (color_id, size_id) dims that exist in this stage's upstream pool.
    Empty when there is no upstream pool (pre-piece stage / nothing cut yet)."""
    source = pool_service.upstream_pool_source(consuming_sr)
    if source is None:
        return []
    good = pool_service.pool_good(source)          # {(color_id, size_id): qty}
    return list(good.keys())


def bundles_for_stage(consuming_sr):
    """Every bundle available at this consuming stage, with allocation rollup.

    Returns a list of dicts:
      color_id, size_id, total, assigned, available, state,
      holders = [{worker_id, worker, allocated, mode}]  (active allocations only)
    `total`/`available`/`assigned` reconcile as total = assigned + available (available
    is the authoritative pool figure; total is reconstructed so it always matches)."""
    from production.models import ProductSize, WorkerStageAllocation
    from raw_materials.models import ClothColor

    dims = _dim_rows(consuming_sr)
    # Resolve labels for EVERY dim up-front (an unallocated bundle has no holder row to
    # borrow a label from — the earlier holder-only lookup showed "—" for fresh bundles).
    colors = {c.pk: c for c in ClothColor.objects.filter(
        pk__in=[c for c, _ in dims if c])}
    sizes = {s.pk: s for s in ProductSize.objects.filter(
        pk__in=[s for _, s in dims if s])}

    out = []
    for (color_id, size_id) in dims:
        available = pool_service.available(consuming_sr, color_id, size_id)
        rows = (WorkerStageAllocation.objects
                .filter(stage_record=consuming_sr, color_id=color_id,
                        size_id=size_id, voided_at__isnull=True)
                .select_related('worker'))
        assigned = sum((r.allocated_quantity for r in rows), D0)
        total = assigned + available
        holders = [{
            'wsa_id': r.pk,                 # for the inline void action
            'worker_id': r.worker_id,
            'worker': r.worker,
            'allocated': r.allocated_quantity,
            'mode': r.allocation_mode,
        } for r in rows]
        color = colors.get(color_id)
        size = sizes.get(size_id)
        out.append({
            'color_id': color_id, 'size_id': size_id,
            'color': color, 'size': size,
            'total': total, 'assigned': assigned, 'available': available,
            'state': _state(total, available), 'holders': holders,
        })
    return out


def _bundle_status(*, locked: bool, remaining, completed) -> str:
    """THE single (locked, remaining, completed) → card-status map, shared by
    worker_bundles + stage_snapshot so a worker's card and the super-admin snapshot
    can never label the same bundle differently: 'done' once the task is locked or the
    whole allocation is reported; 'in_progress' if some good is reported; else 'ready'."""
    if locked or remaining <= 0:
        return 'done'
    return 'in_progress' if completed > 0 else 'ready'


def worker_bundles(consuming_sr, worker):
    """The worker's assigned bundles at this stage — the "My Assigned Work" source.

    Per active allocation: bundle identity + allocated + completed (Σ good on the
    worker's completed/verified contributions for that dim) + remaining + expected
    earnings (Σ already-frozen `expected_earning`, display-only) + mode."""
    from production.models import (
        WorkerStageAllocation, WorkerStageContribution, WorkerStageTask,
    )

    rows = (WorkerStageAllocation.objects
            .filter(stage_record=consuming_sr, worker=worker, voided_at__isnull=True)
            .select_related('color', 'size'))
    # If the worker's stage task is already completed/verified, EVERY bundle is final
    # (locked) — the card must say "done", never offer "Continue" into a locked report.
    task = (WorkerStageTask.objects
            .filter(stage_record=consuming_sr, worker=worker)
            .exclude(status=WorkerStageTask.Status.CANCELLED)
            .order_by('-pk').first())
    task_locked = bool(task and task.status in (
        WorkerStageTask.Status.COMPLETED, WorkerStageTask.Status.VERIFIED))
    out = []
    for r in rows:
        # 'completed' here = the worker's OWN reported good for this bundle (display
        # progress) — counts contributions on any non-cancelled task so a per-bundle
        # submit shows immediately, even before the whole stage task completes. This is
        # a visibility number; money still books only from completed tasks at settlement.
        contribs = WorkerStageContribution.objects.filter(
            task__stage_record=consuming_sr, task__worker=worker,
            color_id=r.color_id, size_id=r.size_id).exclude(
            task__status=WorkerStageTask.Status.CANCELLED)
        completed = sum((c.good_quantity for c in contribs), D0)
        expected = sum((c.expected_earning or D0 for c in contribs), D0)
        out.append({
            'color_id': r.color_id, 'size_id': r.size_id,
            'color': r.color, 'size': r.size,
            'allocated': r.allocated_quantity,
            'completed': completed,
            'remaining': r.allocated_quantity - completed,
            'expected_earning': expected,
            'mode': r.allocation_mode,
            'status': _bundle_status(locked=task_locked,
                                     remaining=r.allocated_quantity - completed,
                                     completed=completed),
        })
    return out


def my_assigned_work(user):
    """AE-3 "My Assigned Work" — the worker's active bundle allocations ACROSS every
    in-progress Adda/stage, as independent cards + a workload summary. Pure reads.

    Returns {'cards': [...], 'summary': {...}}. Each card carries adda/stage context so
    the worker never has to think about which Adda — plus a per-bundle report link target
    (adda.code, stage_code, color_id, size_id). One card per active allocation."""
    from production.models import Adda, AddaStageRecord, WorkerStageAllocation

    # Every consuming SR (in-progress Adda, stage not completed) where the worker holds a
    # live allocation. select the SRs first, then reuse worker_bundles per SR.
    sr_ids = (WorkerStageAllocation.objects
              .filter(worker=user, voided_at__isnull=True,
                      stage_record__completed_at__isnull=True,
                      stage_record__adda__status=Adda.Status.IN_PROGRESS)
              .values_list('stage_record_id', flat=True).distinct())
    srs = (AddaStageRecord.objects.filter(pk__in=list(sr_ids))
           .select_related('adda__product', 'workflow_stage__stage'))

    cards = []
    summ = {'bundles': 0, 'allocated': D0, 'completed': D0, 'remaining': D0,
            'expected': D0, 'stages': set()}
    for sr in srs:
        stage_code = sr.workflow_stage.stage.code
        stage_name = sr.workflow_stage.stage.name
        for b in worker_bundles(sr, user):
            b = dict(b)
            b['adda_code'] = sr.adda.code
            b['stage_code'] = stage_code
            b['stage_name'] = stage_name
            b['stream_id'] = sr.stream_id
            cards.append(b)
            summ['bundles'] += 1
            summ['allocated'] += b['allocated']
            summ['completed'] += b['completed']
            summ['remaining'] += b['remaining']
            summ['expected'] += b['expected_earning']
            summ['stages'].add(stage_name)
    # Ready/in-progress first, done last; then by adda + colour for stable order.
    order = {'ready': 0, 'in_progress': 1, 'done': 2}
    cards.sort(key=lambda c: (order.get(c['status'], 9), c['adda_code'],
                              (c['color'].name if c['color'] else ''),
                              (c['size'].label if c['size'] else '')))
    summ['stages'] = sorted(summ['stages'])
    return {'cards': cards, 'summary': summ}


def stage_snapshot(consuming_sr):
    """AE-4 management snapshot for ONE pool stage: three views over the SAME truth —
    per-bundle rollup, per-worker×bundle allocation detail (with times/status/expected),
    and stage totals. Pure reads (money = the already-frozen expected_earning). Returns
    {'bundles': [...], 'allocations': [...], 'totals': {...}}."""
    from production.models import (
        WorkerStageAllocation, WorkerStageContribution, WorkerStageTask,
    )

    # Per-worker task (started time + lock state) — one task per (worker, stage).
    tasks = {t.worker_id: t for t in (
        WorkerStageTask.objects.filter(stage_record=consuming_sr)
        .exclude(status=WorkerStageTask.Status.CANCELLED))}
    locked_states = (WorkerStageTask.Status.COMPLETED, WorkerStageTask.Status.VERIFIED)

    # Bundle rollup (reuse bundles_for_stage) + per-bundle completed + progress.
    bundles = bundles_for_stage(consuming_sr)
    for b in bundles:
        c = WorkerStageContribution.objects.filter(
            task__stage_record=consuming_sr, color_id=b['color_id'], size_id=b['size_id']
        ).exclude(task__status=WorkerStageTask.Status.CANCELLED)
        b['completed'] = sum((x.good_quantity for x in c), D0)
        b['progress'] = (int((b['completed'] / b['total']) * 100)
                         if b['total'] else 0)

    # Per-worker×bundle allocation detail.
    allocs = (WorkerStageAllocation.objects
              .filter(stage_record=consuming_sr, voided_at__isnull=True)
              .select_related('worker', 'color', 'size')
              .order_by('worker__email', 'pk'))
    detail = []
    for a in allocs:
        contribs = list(WorkerStageContribution.objects.filter(
            task__stage_record=consuming_sr, task__worker_id=a.worker_id,
            color_id=a.color_id, size_id=a.size_id
        ).exclude(task__status=WorkerStageTask.Status.CANCELLED))
        completed = sum((c.good_quantity for c in contribs), D0)
        expected = sum((c.expected_earning or D0 for c in contribs), D0)
        updated = max([c.updated_at for c in contribs], default=None) or a.updated_at
        task = tasks.get(a.worker_id)
        remaining = a.allocated_quantity - completed
        locked = bool(task and task.status in locked_states)
        detail.append({
            'worker': a.worker, 'color': a.color, 'size': a.size,
            'mode': a.allocation_mode, 'allocated': a.allocated_quantity,
            'completed': completed, 'remaining': remaining,
            'expected_earning': expected,
            'status': _bundle_status(locked=locked, remaining=remaining,
                                     completed=completed),
            'started_at': (task.started_at if task else None) or a.created_at,
            'updated_at': updated,
        })

    totals = {
        'bundles': len(bundles),
        'whole': sum(1 for a in allocs if a.allocation_mode == 'whole'),
        'partial': sum(1 for a in allocs if a.allocation_mode == 'partial'),
        'allocated': sum((a.allocated_quantity for a in allocs), D0),
        'completed': sum((b['completed'] for b in bundles), D0),
        'unassigned': sum((b['available'] for b in bundles), D0),
        'workers': len({a.worker_id for a in allocs}),
    }
    totals['remaining'] = totals['allocated'] - totals['completed']
    return {'bundles': bundles, 'allocations': detail, 'totals': totals}
