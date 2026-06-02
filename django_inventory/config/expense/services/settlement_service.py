"""Settlement service — sole writer of PayrollSettlement (+ its ledger debits).

The owner settles a worker whenever they decide (no fixed cycle). A settlement:
  • pays cash (settlement_payment debit) and/or
  • recovers advances (advance_recovery debit), owner-controlled per advance (D3)
Both reduce the payable. After a FULL settlement the worker's pending payable
returns to 0 (a "fresh overview"); partial settlements leave the remainder owed.

Immutable: a settlement is never edited. A mistake = reverse its ledger debits +
a fresh settlement (same append-only discipline as the rest of the ledger).

Everything stays derived: we snapshot payable/advance-outstanding onto the row
for audit, but never read those snapshots back as the source of truth.
"""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import ValidationError
from django.db import connection, transaction
from django.utils import timezone

from expense.models import (
    PayrollSettlement, PayrollSettlementItem, WorkerAdvance, WorkerLedgerEntry,
    WorkerProfile,
)
from expense.services import ledger_service, payroll_service
from ._shared import _ensure_management

_ZERO = Decimal('0.00')
_CAT = WorkerLedgerEntry.Category

# Stable 32-bit key for the transaction-scoped advisory lock that serializes
# settlement-reference allocation (see create_settlement). Arbitrary but fixed.
_SETTLEMENT_REF_LOCK = 5374


def _q(amount) -> Decimal:
    """Quantize to paisa (2dp) the same way the ledger does."""
    return Decimal(str(amount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def _next_reference() -> str:
    """SETL-0001, SETL-0002, … — gap-tolerant (max existing + 1)."""
    last = (
        PayrollSettlement.objects.order_by('-id')
        .values_list('reference', flat=True).first()
    )
    n = 0
    if last and last.startswith('SETL-'):
        try:
            n = int(last.split('-', 1)[1])
        except (ValueError, IndexError):
            n = PayrollSettlement.objects.count()
    return f"SETL-{n + 1:04d}"


@transaction.atomic
def create_settlement(*, user, worker, amount_paid, recoveries=None,
                      settlement_date=None, method=PayrollSettlement.Method.CASH,
                      notes=''):
    """Create a settlement: cash payment + owner-chosen advance recoveries.

    `recoveries` = [{'advance': <WorkerAdvance|id>, 'amount': Decimal}, …].
    Each amount must be ≤ that advance's remaining (recomputed under lock).
    Invariant: amount_paid + Σrecoveries ≤ current payable (can't settle more
    than is owed). Equality = full settlement (payable → 0).
    """
    _ensure_management(user)

    # Serialize settlement-reference allocation across ALL workers. _next_reference
    # reads the global max reference with an UNLOCKED select; the per-worker
    # WorkerProfile lock below does NOT serialize two settlements for *different*
    # workers, so both could read 'SETL-0001', both compute 'SETL-0002', and the
    # second INSERT hits the reference unique constraint → IntegrityError → an
    # unhandled 500. A transaction-scoped Postgres advisory lock serializes them;
    # it auto-releases on commit/rollback. (pg_advisory_xact_lock = PG advisory lock.)
    if connection.vendor == 'postgresql':
        with connection.cursor() as cur:
            cur.execute('SELECT pg_advisory_xact_lock(%s)', [_SETTLEMENT_REF_LOCK])

    when = settlement_date or timezone.now().date()
    paid = _q(amount_paid)
    if paid < _ZERO:
        raise ValidationError("Amount paid cannot be negative.")

    # Serialize all settlements for this worker. The over-settle guard below reads
    # payable_before via an unlocked SUM; without a row lock two concurrent
    # settlements (esp. cash-only, where the advance lock matches no rows) both
    # read the same payable and each pay it in full → worker over-paid. Lock a
    # stable per-worker row (WorkerProfile) — select_for_update = Postgres FOR
    # UPDATE — so the second settlement waits and re-reads the reduced payable.
    profile, _ = WorkerProfile.objects.get_or_create(user=worker)
    WorkerProfile.objects.select_for_update().get(pk=profile.pk)

    # Lock the worker's advances so two settlements can't over-recover the same
    # advance concurrently (mirrors allocation_service's select_for_update guard).
    locked = {
        a.id: a for a in
        WorkerAdvance.objects.select_for_update().filter(worker=worker)
    }

    cleaned: list[tuple[WorkerAdvance, Decimal]] = []
    advance_deducted = _ZERO
    for r in (recoveries or []):
        adv = r['advance']
        adv_id = getattr(adv, 'id', adv)
        amt = _q(r['amount'])
        if amt <= _ZERO:
            continue                       # skip blank/zero rows from the form
        adv = locked.get(int(adv_id))
        if adv is None:
            raise ValidationError("Advance does not belong to this worker.")
        remaining = payroll_service.advance_remaining(adv)
        if amt > remaining:
            raise ValidationError(
                f"Recovery {amt} exceeds advance #{adv.id} remaining {remaining}.")
        cleaned.append((adv, amt))
        advance_deducted += amt

    payable_before = ledger_service.worker_balance(worker)
    advance_outstanding_before = payroll_service.advance_outstanding(worker)

    total_settled = paid + advance_deducted
    if total_settled <= _ZERO:
        raise ValidationError("A settlement must pay or recover something.")
    if total_settled > payable_before:
        raise ValidationError(
            f"Settlement {total_settled} exceeds pending payable {payable_before}.")

    settlement = PayrollSettlement.objects.create(
        reference=_next_reference(), worker=worker, settlement_date=when,
        payable_before=payable_before,
        advance_outstanding_before=advance_outstanding_before,
        advance_deducted=advance_deducted, amount_paid=paid,
        method=method, notes=notes, created_by=user,
    )

    for adv, amt in cleaned:
        PayrollSettlementItem.objects.create(
            settlement=settlement, advance=adv, amount_recovered=amt,
        )

    # Two debits against the payable ledger, both linked to the settlement.
    if paid > _ZERO:
        ledger_service.log_debit(
            worker=worker, category=_CAT.SETTLEMENT_PAYMENT, amount=paid,
            entry_date=when, created_by=user, settlement=settlement,
            notes=f"Settlement {settlement.reference} ({method})",
        )
    if advance_deducted > _ZERO:
        ledger_service.log_debit(
            worker=worker, category=_CAT.ADVANCE_RECOVERY, amount=advance_deducted,
            entry_date=when, created_by=user, settlement=settlement,
            notes=f"Advance recovery in {settlement.reference}",
        )
    return settlement
