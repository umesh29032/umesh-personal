"""Generic-stage panel context — shared by StagePanelView + the workspace.

Same ctx-flag pattern as the bespoke builders: display flags mirror the
service-side guards (defence-in-depth; the SERVICE re-checks everything).

OP-1 lenses (blind-reporting rule, owner 2026-07-05):
  MANAGEMENT — full board (roster, per-worker allocated/good/alter/missing/
    verified/expected ₹) + the pool split section (available per dim, allocate
    form, active allocations, void).
  WORKER — own slice ONLY: their dims chips + own totals + report link. No
    other workers, no pool/cutting quantities, no factory totals (the template
    additionally gates every management block on is_management).
"""
from decimal import Decimal

from accounts.services import MANAGEMENT_ROLES, user_has_role


def _pool_section(sr, wf):
    """Management-only bundle allocation data (AE-2). Reads ONLY through the services
    (pool_service single reader + bundle_service read-model — no APSCPB/SPS queries here).

    `bundles` = the AE-2 whole-first list: one row per Manufacturing Bundle (colour,size)
    with total / assigned / remaining (available) / holders (worker · qty · mode · wsa_id
    for inline void). `source_stage`/`grain` unchanged."""
    from production.constants import ALLOC_DIM_NONE
    from production.services import bundle_service, pool_service

    if sr is None or wf is None or wf.allocation_dimensions == ALLOC_DIM_NONE:
        return None
    source = pool_service.upstream_pool_source(sr)
    if source is None:
        return {'bundles': [], 'source_stage': None, 'grain': wf.allocation_dimensions,
                'has_available': False}

    bundles = bundle_service.bundles_for_stage(sr)
    # Stable, human order: colour name then size label (None-safe).
    bundles.sort(key=lambda b: ((b['color'].name if b['color'] else ''),
                                (b['size'].label if b['size'] else '')))
    return {
        'bundles': bundles,
        'has_available': any(b['available'] > 0 for b in bundles),
        'source_stage': source.workflow_stage.stage.name,
        'grain': wf.allocation_dimensions,
    }


def _my_slice(sr, user):
    """The WORKER lens: own allocated dims (labels only — never quantities) +
    own task. Blind rule: allocated_quantity deliberately NOT exposed."""
    from production.models import WorkerStageAllocation
    if sr is None:
        return None
    rows = (WorkerStageAllocation.objects
            .filter(stage_record=sr, worker=user, voided_at__isnull=True)
            .select_related('color', 'size'))
    seen, chips = set(), []
    for a in rows:
        key = (a.color_id, a.size_id)
        if key in seen:
            continue
        seen.add(key)
        label = ' · '.join(p for p in (
            a.color.name if a.color_id else '',
            a.size.label if a.size_id else '') if p)
        chips.append({'label': label or 'Assigned work',
                      'swatch': (a.color.hex_code or '') if a.color_id else ''})
    return {'dims': chips}


def build_generic_panel_context(request, adda, stage_code: str, stage_name: str) -> dict:
    from production.models import Stage, WorkerStageTask
    from production.services import eligible_stage_workers, user_can_access_stage
    from .service import _get_stage_record, _workflow_stage

    user = request.user
    sr = _get_stage_record(adda, stage_code)
    wf = _workflow_stage(adda, stage_code)
    stage = Stage.objects.select_related('machine_type', 'category').filter(
        code=stage_code).first()

    is_management = user_has_role(user, MANAGEMENT_ROLES)
    is_assigned = bool(sr and sr.is_worker_assigned(user))
    can_assign = is_management
    can_complete = (
        sr is not None and sr.completed_at is None
        and adda.current_stage_id == (wf.id if wf else None)
        and (is_management or (is_assigned and user_can_access_stage(user, stage_code)))
    )
    can_reopen = is_management and sr is not None and sr.completed_at is not None

    # Per-worker report board — MANAGEMENT ONLY (OP-1 L1: a worker must never
    # see other workers' names/quantities). The worker lens gets my_task below.
    tasks, my_task = [], None
    if sr is not None:
        rows = list(
            WorkerStageTask.objects
            .filter(stage_record=sr)
            .exclude(status=WorkerStageTask.Status.CANCELLED)
            .select_related('worker')
            .prefetch_related('contributions')
        )
        for t in rows:
            t.good_total = sum((c.good_quantity or 0) for c in t.contributions.all())
            t.alter_total = sum((c.alter_quantity or 0) for c in t.contributions.all())
            t.missing_total = sum((c.missing_quantity or 0) for c in t.contributions.all())
            t.damaged_total = sum((c.damaged_quantity or 0) for c in t.contributions.all())
            # OP-1 board money column: Σ frozen expected (visibility-only field;
            # None until the task completes). Verified = Σ corrections set so far.
            t.expected_total = sum(
                (c.expected_earning for c in t.contributions.all()
                 if c.expected_earning is not None), Decimal('0'))
            t.verified_total = sum(
                (c.verified_quantity for c in t.contributions.all()
                 if c.verified_quantity is not None), Decimal('0'))
            t.has_verified = any(
                c.verified_quantity is not None for c in t.contributions.all())
            if t.worker_id == user.pk:
                my_task = t
        if is_management:
            tasks = rows

    # OP-1: per-worker allocated totals for the board (capacity, not money).
    if is_management and sr is not None and tasks:
        from production.models import WorkerStageAllocation
        from django.db.models import Sum
        alloc_by_worker = dict(
            WorkerStageAllocation.objects
            .filter(stage_record=sr, voided_at__isnull=True)
            .values_list('worker_id')
            .annotate(q=Sum('allocated_quantity'))
            .values_list('worker_id', 'q'))
        for t in tasks:
            t.allocated_total = alloc_by_worker.get(t.worker_id, Decimal('0'))

    machine_holders = []
    if stage is not None and stage.work_type == 'machine' and stage.machine_type_id:
        try:
            from machines.models import MachineAssignment
            holders_qs = (MachineAssignment.objects
                          .filter(adda=adda, end_at__isnull=True,
                                  machine__machine_type_id=stage.machine_type_id)
                          .select_related('machine', 'worker'))
            if not is_management:
                # Blind rule: a worker sees only THEIR machine, never colleagues'.
                holders_qs = holders_qs.filter(worker=user)
            machine_holders = list(holders_qs)
        except Exception:
            machine_holders = []

    pool = _pool_section(sr, wf) if is_management else None
    # AE-2: worker context for the allocation dropdown — each active worker's CURRENT
    # load on THIS stage (bundle count + Σ pieces) so a manager can balance at a glance.
    alloc_workers = []
    if is_management and pool is not None and sr is not None:
        from django.db.models import Count, Sum
        from production.models import WorkerStageAllocation
        load = {
            row['worker_id']: row for row in (
                WorkerStageAllocation.objects
                .filter(stage_record=sr, voided_at__isnull=True)
                .values('worker_id')
                .annotate(bundles=Count('pk'), pieces=Sum('allocated_quantity')))
        }
        for w in sr.active_workers:
            ld = load.get(w.pk, {})
            alloc_workers.append({
                'worker': w,
                'bundles': ld.get('bundles', 0),
                'pieces': ld.get('pieces', Decimal('0')) or Decimal('0'),
            })
    # Panel section numbers (conditional sections shift them; templates can't count).
    sec, n = {}, 1
    sec['workers'] = n; n += 1
    if pool is not None:
        sec['split'] = n; n += 1
    if stage is not None and stage.work_type == 'machine':
        sec['machine'] = n; n += 1
    sec['output'] = n; n += 1
    sec['complete'] = n

    return {
        'generic_stage_code': stage_code,
        'generic_stage_name': stage_name,
        'stage_row': stage,
        'stage_record': sr,
        'workflow_stage': wf,
        'is_management': is_management,
        'can_assign': can_assign,
        'can_complete': can_complete,
        'can_reopen': can_reopen,
        'worker_tasks': tasks,
        'my_task': my_task,
        'my_slice': None if is_management else _my_slice(sr, user),
        'pool': pool,
        'sec': sec,
        'eligible_workers': eligible_stage_workers(stage_code) if can_assign else [],
        'alloc_workers': alloc_workers,
        # UX: after an allocation the panel reloads with ?worker=<pk> so the picker
        # keeps the same worker selected (assign many bundles to one worker, pick once).
        'preselect_worker': request.GET.get('worker') or '',
        'machine_holders': machine_holders,
    }
