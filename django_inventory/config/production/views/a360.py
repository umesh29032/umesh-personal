"""A360 — the Adda-360 management overview context builder (READ-ONLY).

Owner-locked properties (A360 plan v2, 2026-07-05):
  • Aggregates EXISTING business truth only — every number is a frozen value
    or a request-time SUM/COUNT/subtraction of existing rows. No stored
    aggregates, no new money/settlement/ledger logic, no second calculation
    of anything that has a single home (stalled → operations_digest; expected
    → the settlement funnel + effective_pay_rate + settlement_quantity, the
    EXACT trio the settlement queue uses; recon → reconcile_stage_pay).
  • 100% STAGE-GENERIC: this module contains NO stage-name literals — it
    iterates the product's workflow stages and asks the handler registry.
    A future stage (bundling/sewing/checking/packing/dispatch) appears here
    automatically once its handler is registered (test-pinned by source
    inspection in test_a360_overview).
  • Management-only: the VIEW gates the ctx; workers never receive this data.

Honest-metrics rule (owner, 2026-07-05): quantities are STAGE-GRAIN (layers /
pieces / jobs) — cross-stage sums would mix units, so contribution share is
per-stage only and the per-worker rollup lists per-stage numbers instead of
inventing a mixed-unit total.
"""
from __future__ import annotations

from decimal import Decimal

_ZERO = Decimal('0.00')

# Health states — derived at render time, never stored.
HEALTH_DONE, HEALTH_ACTIVE, HEALTH_BLOCKED, HEALTH_WAITING = (
    'done', 'active', 'blocked', 'waiting')


def build_a360(adda, stages_overview, garment_sets=None):
    # R10-B UI philosophy: category rollup for the header chips (presentation
    # only; single-category flows keep the flat per-stage chips).
    from production.views.presentation import grouped_or_flat
    _groups, _grouped = grouped_or_flat(
        stages_overview, stage_of=lambda e: e['workflow_stage'].stage)
    category_progress = [
        {'label': g['label'],
         'done': sum(1 for e in g['items'] if e['state'] == 'completed'),
         'total': len(g['items']),
         'active': any(e['state'] == 'in_progress' for e in g['items'])}
        for g in _groups
    ] if _grouped else None

    """Full A360 context. `stages_overview` = the page's existing per-stage
    list (workflow_stage/state/sr/snap) — reused, not recomputed."""
    from django.db.models import Sum
    from production.models import WorkerStageTask
    from production.services.operations_digest import stalled_stage_records
    from production.stages import base as stage_registry
    from tracking.models import AddaHistory
    from expense.models import StageWorkAssignment, WorkerProfile
    from expense.services.adda_settlement_service import (
        _payable_stage_records, _settleable_lines)
    from expense.services.reconciliation_service import reconcile_stage_pay
    from expense.services.settlement_resolver import settlement_quantity
    from production.services.cost_service import effective_pay_rate

    # ── Stage progress + health ──────────────────────────────────────────
    # 🔴 blocked = THE single stalled predicate (H-2B) scoped to this Adda —
    # the digest tile, drill-down and A360 always reconcile by construction.
    stalled_ids = set(
        stalled_stage_records().filter(adda=adda).values_list('id', flat=True))
    progress, done = [], 0
    for entry in stages_overview:
        sr = entry['sr']
        if entry['state'] == 'completed':
            health = HEALTH_DONE
            done += 1
        elif entry['state'] == 'in_progress':
            health = HEALTH_BLOCKED if (sr and sr.pk in stalled_ids) else HEALTH_ACTIVE
        else:
            health = HEALTH_WAITING
        progress.append({'label': entry['label'], 'stage_type': entry['stage_type'],
                         'health': health, 'sr': sr})
    total = len(stages_overview)
    pct = int(done * 100 / total) if total else 0

    # ── Stage timeline — a change-type-filtered render of the EXISTING
    # AddaHistory rows (no new data; the full-history page stays canonical).
    _CT = AddaHistory.ChangeType
    timeline = list(
        AddaHistory.objects
        .filter(adda=adda, change_type__in=(
            _CT.CREATED, _CT.STAGE_STARTED, _CT.STAGE_ADVANCED,
            _CT.STAGE_REOPENED, _CT.COMPLETED))
        .select_related('actor', 'stage_from__stage', 'stage_to__stage')
        .order_by('created_at'))

    # ── Worker board: Progress (status) then Contribution (qty + ₹) ──────
    tasks = list(
        WorkerStageTask.objects
        .filter(stage_record__adda=adda)
        .exclude(status=WorkerStageTask.Status.CANCELLED)
        .select_related('worker', 'stage_record__workflow_stage__stage')
        .prefetch_related('contributions__settlement_line'))
    monthly_ids = set(
        WorkerProfile.objects
        .filter(user_id__in={t.worker_id for t in tasks},
                pay_basis=WorkerProfile.PayBasis.MONTHLY)
        .values_list('user_id', flat=True))

    by_stage: dict[int, dict] = {}
    for entry in stages_overview:
        ws = entry['workflow_stage']
        unit = 'units'
        if stage_registry.has(entry['stage_type']):
            try:
                qf = [f for f in stage_registry.get(entry['stage_type'])
                      .contribution_schema(adda)['fields']
                      if f['kind'] == 'quantity']
                if qf:
                    unit = qf[0].get('unit', 'units')
            except Exception:
                pass
        by_stage[ws.order] = {'label': entry['label'], 'unit': unit,
                              'payable': ws.credits_workers,
                              'counts': {'assigned': 0, 'in_progress': 0,
                                         'completed': 0, 'verified': 0},
                              'stage_good': _ZERO, 'workers': []}
    for t in tasks:
        row = by_stage.get(t.stage_record.workflow_stage.order)
        if row is None:
            continue
        row['counts'][t.status] = row['counts'].get(t.status, 0) + 1
        reported = sum((c.good_quantity for c in t.contributions.all()), _ZERO)
        verified = sum((c.verified_quantity for c in t.contributions.all()
                        if c.verified_quantity is not None), _ZERO)
        is_monthly = t.worker_id in monthly_ids
        # ₹ suppressed for monthly workers (R4) AND on non-payable stages.
        # Since the A360 follow-up, `effective_pay_rate` freezes 0 on
        # non-payable stages system-wide — this branch is defense-in-depth
        # for PRE-RULE frozen rows (mirrors how F2 keeps its guard at every
        # read point rather than trusting old snapshots).
        expected = None if (is_monthly or not row['payable']) else sum(
            (c.expected_earning for c in t.contributions.all()
             if c.expected_earning is not None), _ZERO)
        settled_lines = sum(
            1 for c in t.contributions.all()
            if c.settlement_line_id and c.settlement_line.voided_at is None)
        row['stage_good'] += reported
        row['workers'].append({
            'worker': t.worker, 'status': t.status,
            'status_display': t.get_status_display(),
            'reported': reported, 'verified': verified or None,
            'expected': expected, 'is_monthly': is_monthly,
            'settled_lines': settled_lines,
        })
    for row in by_stage.values():
        for w in row['workers']:
            # Honest per-STAGE share only (mixed units across stages).
            w['share_pct'] = (
                int(w['reported'] * 100 / row['stage_good'])
                if row['stage_good'] > 0 and w['reported'] else None)
    board = [by_stage[k] for k in sorted(by_stage) if by_stage[k]['workers']]

    # Per-worker rollup: active stage + current status + per-stage quantities
    # (no cross-stage total — units differ; owner honest-metrics rule).
    workers_rollup: dict[int, dict] = {}
    for t in sorted(tasks, key=lambda t: t.stage_record.workflow_stage.order):
        w = workers_rollup.setdefault(t.worker_id, {
            'worker': t.worker, 'is_monthly': t.worker_id in monthly_ids,
            'active_stage': None, 'active_status': None, 'stages': []})
        label = t.stage_record.workflow_stage.stage.name
        w['stages'].append(label)
        if t.status in (WorkerStageTask.Status.ASSIGNED,
                        WorkerStageTask.Status.IN_PROGRESS):
            w['active_stage'] = label
            w['active_status'] = t.get_status_display()

    # ── Money strip — EXACT reuse of the settlement-queue computation ────
    payable = _payable_stage_records(adda)
    lines, _, _, _ = _settleable_lines(payable) if payable else ([], [], [], [])
    expected_uncredited = sum(
        ((settlement_quantity(c)
          * effective_pay_rate(c.task.stage_record.workflow_stage,
                               c.expected_rate or _ZERO))
         for c in lines), _ZERO).quantize(Decimal('0.01'))
    swa_by_sr = {
        r['stage_record']: r['s'] for r in
        StageWorkAssignment.objects
        .filter(stage_record__adda=adda, voided_at__isnull=True)
        .values('stage_record')
        .annotate(s=Sum('earning_amount_snapshot'))
    }
    settled_total = sum(swa_by_sr.values(), _ZERO)

    # ── Cost panel — ADR-0009 duality, correctly labeled (P-COST) ────────
    # M12 fix (2026-07-12): Σ over EVERY stage record of a stage — the trio
    # stages carry one record PER CUTTING LANE and this loop used to read only
    # stages_overview's single representative SR (the read-side sibling of
    # GAP-1/2: one arbitrary cycle's frozen cost stood in for all of them —
    # GLDN-001 showed ₹280 here vs ₹1408 on the costing dashboard).
    from production.models import AddaStageRecord as _ASR
    srs_by_ws = {}
    for _sr in _ASR.objects.filter(adda=adda):
        srs_by_ws.setdefault(_sr.workflow_stage_id, []).append(_sr)
    recon_by_stage = {r['stage']: r['flag']
                      for r in reconcile_stage_pay(adda=adda)}
    cost_rows, std_labor, nonpayable_priced = [], _ZERO, _ZERO
    for entry in stages_overview:
        ws = entry['workflow_stage']
        lane_srs = srs_by_ws.get(ws.pk, [])
        priced = [s.processing_cost for s in lane_srs
                  if s.processing_cost is not None]
        cost = sum(priced, _ZERO) if priced else None   # None = honest "unpriced"
        settled_sr = sum((swa_by_sr.get(s.pk, _ZERO) for s in lane_srs), _ZERO)
        if cost is not None:
            if ws.credits_workers:
                std_labor += cost
            else:
                nonpayable_priced += cost
        _method_sr = lane_srs[0] if lane_srs else None
        cost_rows.append({
            'label': entry['label'],
            'method': ((_method_sr.cost_method_snapshot or ws.cost_method)
                       if _method_sr else ws.cost_method),
            'cost': cost,
            'settled': settled_sr,
            'recon': recon_by_stage.get(ws.stage.code, ''),
        })
    # Mobile-density (owner lock 2026-07-05): collapsed sections still answer
    # the business question via their <summary> line — precompute the counts.
    worker_ids_all = {t.worker_id for t in tasks}
    active_count = sum(1 for t in tasks
                       if t.status in (WorkerStageTask.Status.ASSIGNED,
                                       WorkerStageTask.Status.IN_PROGRESS))
    # ── M13 → RMX-C (2026-07-18): the panel's Decision-2 numbers now come
    # from THE one extracted assembly (cost_service.full_costs_for_addas) —
    # this view was the reference implementation; the assembly is its INERT
    # extraction (parity-pinned: material/settled/nonpayable/full_cost values
    # byte-equal). Per-row maps above (swa_by_sr / std_labor / cost_rows)
    # stay view-local — they are display shape, not the assembly.
    from production.services.cost_service import full_costs_for_addas
    _fc = full_costs_for_addas([adda.pk])[adda.pk]
    _mat = _fc['material']
    has_material = _mat['has_material']
    material_net = _mat['net']
    material_remnant = _mat['remnant']
    material_unpriced_rolls = _mat['unpriced_rolls']
    settled_total = _fc['settled_total']
    nonpayable_priced = _fc['nonpayable_priced']
    full_cost = _fc['full_cost']
    cost_per_garment = (
        (full_cost / garment_sets).quantize(Decimal('0.01'))
        if garment_sets else None)

    return {
        'category_progress': category_progress,
        'progress': progress, 'progress_done': done, 'progress_total': total,
        'progress_pct': pct,
        'workers_count': len(worker_ids_all),
        'active_count': active_count,
        'timeline_count': len(timeline),
        'timeline': timeline,
        'board': board,
        'workers_rollup': sorted(workers_rollup.values(),
                                 key=lambda w: w['worker'].pk),
        'expected_uncredited': expected_uncredited,
        'settled_total': settled_total,
        'std_labor': std_labor,
        'variance': std_labor - settled_total,
        'nonpayable_priced': nonpayable_priced,
        'cost_rows': cost_rows,
        'has_material': has_material,
        'material_net': material_net,
        'material_remnant': material_remnant,
        'material_unpriced_rolls': material_unpriced_rolls,
        'full_cost': full_cost,
        'garment_sets': garment_sets,
        'cost_per_garment': cost_per_garment,
    }
