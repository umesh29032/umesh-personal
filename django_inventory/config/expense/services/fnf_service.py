"""Full & Final settlement — ORCHESTRATION ONLY (R7, PDD §20 / §27-D5 / §31.2).

This module writes NOTHING itself. It sequences the existing audited writers:
  1. preconditions (open tasks / draft-gate blockers) — REFUSE with a checklist
  2. per-Adda settlements scoped to the leaver (adda_settlement_service,
     `only_worker=` — the sole SWA/ADST writer stays the sole writer)
  3. advance clearance: owner-chosen recovery inside those settlements happens
     on the normal settlement screens; the F&F execute recovers from payable
     via the cash event and WRITES OFF the audited residual
     (settlement_service `write_offs=` — sole PSI writer stays sole)
  4. cash payment of the remaining payable (settlement_service)
  5. deactivate (`is_active=False` — §31.2: blocks LOGIN, never money)

NOT one giant transaction: each step is an existing atomic audited event, so
an abort mid-flow leaves a consistent, RESUMABLE state (preview recomputes
what is left; already-finalized settlements simply exist).

🔒 ADR-0011: the line collector is the `_settleable_lines` funnel via
`preview_lines`/`finalize(only_worker=)` — a monthly worker yields ZERO
earning lines by construction (test-pinned).
"""
from __future__ import annotations

import logging
from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError

from accounts.services import ROLE_SUPER_ADMIN, user_has_role

logger = logging.getLogger(__name__)

_ZERO = Decimal('0.00')


def _ensure_super_admin(user):
    # P-4 (owner): the whole F&F flow is super-admin only — a rare,
    # money-sensitive exit event (same posture as D3/D5 corrections).
    if not user_has_role(user, {ROLE_SUPER_ADMIN}):
        raise PermissionDenied("Only a Super Admin can run a Full & Final settlement.")


def fnf_preview(worker, *, user) -> dict:
    """Everything the owner must see/resolve BEFORE executing (read-only).

    Returns {
      open_tasks:      [WorkerStageTask]  — MUST be resolved via existing flows
      blocked_addas:   [{adda, incomplete:[stage names]}] — draft gate not met
      ready_addas:     [{adda, lines, expected}] — will be settled per-Adda
      advances:        [{advance, remaining}] — residuals to write off
      payable_now:     Decimal — ledger balance today (before new settlements)
      is_monthly:      bool
      ready:           bool — True when nothing blocks execution
    }
    """
    _ensure_super_admin(user)
    from production.models import WorkerStageTask
    from expense.services import payroll_service
    from expense.services import ledger_service
    from expense.services.adda_settlement_service import (
        _payable_stage_records, _settleable_lines)
    from production.services.cost_service import effective_pay_rate
    from expense.services.settlement_resolver import settlement_quantity

    open_tasks = list(
        WorkerStageTask.objects
        .filter(worker=worker,
                status__in=(WorkerStageTask.Status.ASSIGNED,
                            WorkerStageTask.Status.IN_PROGRESS))
        .select_related('stage_record__adda',
                        'stage_record__workflow_stage__stage'))

    # Addas holding uncredited lines for this worker — via THE funnel.
    from production.models import Adda
    adda_ids = set(
        WorkerStageTask.objects
        .filter(worker=worker,
                status__in=(WorkerStageTask.Status.COMPLETED,
                            WorkerStageTask.Status.VERIFIED))
        .values_list('stage_record__adda_id', flat=True))
    ready_addas, blocked_addas = [], []
    for adda in Adda.objects.filter(pk__in=adda_ids).select_related('product'):
        payable = _payable_stage_records(adda)
        if not payable:
            continue
        incomplete = [sr.workflow_stage.stage.name for sr in payable
                      if sr.completed_at is None]
        lines, _, _, _ = _settleable_lines(payable)
        mine = [c for c in lines if c.task.worker_id == worker.pk]
        if not mine:
            continue                    # nothing of the leaver's left here
        if incomplete:
            # P-5 (owner): refuse-first — quantities must be final before money.
            blocked_addas.append({'adda': adda, 'incomplete': incomplete})
            continue
        expected = sum(
            (settlement_quantity(c)
             * effective_pay_rate(c.task.stage_record.workflow_stage,
                                  c.expected_rate or _ZERO)
             for c in mine), _ZERO)
        ready_addas.append({'adda': adda, 'lines': len(mine),
                            'expected': expected.quantize(Decimal('0.01'))})

    advances = [
        {'advance': a, 'remaining': payroll_service.advance_remaining(a)}
        for a in payroll_service.WorkerAdvance.objects
                 .filter(worker=worker).order_by('advance_date')
    ]
    advances = [a for a in advances if a['remaining'] > _ZERO]

    return {
        'open_tasks': open_tasks,
        'blocked_addas': blocked_addas,
        'ready_addas': ready_addas,
        'advances': advances,
        'payable_now': ledger_service.worker_balance(worker),
        'is_monthly': payroll_service.is_monthly(worker),
        'ready': not open_tasks and not blocked_addas,
    }


def fnf_execute(worker, *, user, write_off_reason='') -> dict:
    """Run the F&F sequence. Refuses unless the preview is `ready`.

    Steps (each an existing atomic audited event — see module docstring):
    per-Adda `finalize(only_worker=leaver)` → cash payment of the full
    remaining payable + audited write-off of every advance residual →
    deactivate. Returns a receipt dict.
    """
    _ensure_super_admin(user)
    from expense.services import payroll_service, ledger_service
    from expense.services.adda_settlement_service import (
        create_draft, finalize_adda_settlement)
    from expense.services.settlement_service import create_settlement
    from expense.models import AddaSettlement

    pv = fnf_preview(worker, user=user)
    if pv['open_tasks']:
        names = ', '.join(f"{t.stage_record.adda.code}/{t.stage_record.workflow_stage.stage.name}"
                          for t in pv['open_tasks'])
        raise ValidationError(
            f"Cannot run F&F: {len(pv['open_tasks'])} open task(s) — {names}. "
            "Resolve them first (submit the report or cancel the assignment).")
    if pv['blocked_addas']:
        names = ', '.join(
            f"{b['adda'].code} ({', '.join(b['incomplete'])})"
            for b in pv['blocked_addas'])
        raise ValidationError(
            f"Cannot run F&F: payable stage(s) not completed yet on {names}. "
            "Complete those stages (quantities must be final) first.")
    if pv['advances'] and not (write_off_reason or '').strip():
        raise ValidationError(
            "This worker has outstanding advance(s). A write-off reason is "
            "required — the residual is forgiven on record, never silently.")

    # [1] per-Adda settlements, leaver-scoped (colleagues untouched).
    settled = []
    for entry in pv['ready_addas']:
        adda = entry['adda']
        draft = AddaSettlement.objects.filter(
            adda=adda, status=AddaSettlement.Status.DRAFT).first()
        if draft is None:
            draft = create_draft(adda=adda, user=user,
                                 notes=f"F&F {worker.get_full_name() or worker.email}")
        finalize_adda_settlement(settlement=draft, user=user,
                                 only_worker=worker)
        settled.append(draft.reference)

    # [2] cash + write-offs in ONE closure event (payment-only + PSI rows).
    payable = ledger_service.worker_balance(worker)
    write_offs = [{'advance': a['advance'], 'reason': write_off_reason}
                  for a in pv['advances']]
    closure = None
    if payable > _ZERO or write_offs:
        closure = create_settlement(
            user=user, worker=worker, amount_paid=payable,
            write_offs=write_offs,
            notes=f"F&F closure — {worker.get_full_name() or worker.email}")

    # [3] deactivate (§31.2: login only; PROTECT keeps all history/money rows).
    worker.is_active = False
    worker.save(update_fields=['is_active'])

    logger.info("fnf.execute worker=%s settlements=%s paid=%s write_offs=%s by=%s",
                worker.pk, settled, payable, len(write_offs), user.pk)
    return {
        'settlements': settled,
        'closure': closure,
        'paid': payable,
        'write_offs': len(write_offs),
        'advance_outstanding_after': payroll_service.advance_outstanding(worker),
    }
