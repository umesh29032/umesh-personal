"""Payment service — sole writer of PayrollSettlement (+ its ledger debits).

V2-2 NARROWED THIS TO PAYMENT-ONLY (Model A: settlement ≠ payment).
A PayrollSettlement now means exactly one thing: CASH was paid
(settlement_payment debit). Advance RECOVERY moved to the Adda settlement
(adda_settlement_service) — owner-chosen per advance at finalize; any
`recoveries` passed here is loudly REFUSED, by design (old-habit guard).

WHY: earnings + recovery are an APPROVAL decision (Adda-scoped, reviewable,
reversible via the settlement lifecycle); cash is fungible and worker-scoped.
Mixing them again would re-couple money creation with money handover — the
exact ambiguity V2-2 removed. See docs/ARCHITECTURE_V2.md §11 + ADR-0005.

Immutable: a settlement is never edited. A mistake = reverse its ledger debits +
a fresh settlement (same append-only discipline as the rest of the ledger).

Everything stays derived: we snapshot payable/advance-outstanding onto the row
for audit, but never read those snapshots back as the source of truth.
"""
from __future__ import annotations

import logging
from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection, transaction
from django.utils import timezone

from expense.models import (
    PayrollSettlement, PayrollSettlementItem, WorkerAdvance, WorkerLedgerEntry,
    WorkerProfile,
)
from expense.services import ledger_service, payroll_service
from expense.services._shared import next_reference, q_paisa
from ._shared import _ensure_management

# Module logger — debuggability for money writes (settlement + ledger debits).
logger = logging.getLogger(__name__)

_ZERO = Decimal('0.00')
_CAT = WorkerLedgerEntry.Category

# Stable 32-bit key for the transaction-scoped advisory lock that serializes
# settlement-reference allocation (see create_settlement). Arbitrary but fixed.
_SETTLEMENT_REF_LOCK = 5374


# One rounding rule + one reference generator for BOTH settlement services
# (expense/services/_shared.py) — local names kept so call sites stay stable.
def _q(amount) -> Decimal:
    return q_paisa(amount)


def _next_reference() -> str:
    """SETL-0001, SETL-0002, … — gap-tolerant (max existing + 1)."""
    return next_reference(PayrollSettlement, 'SETL')


@transaction.atomic
def create_settlement(*, user, worker, amount_paid, recoveries=None,
                      settlement_date=None, method=PayrollSettlement.Method.CASH,
                      notes='', write_offs=None):
    """Create a settlement: cash payment + owner-chosen advance recoveries.

    `recoveries` = [{'advance': <WorkerAdvance|id>, 'amount': Decimal}, …].
    Each amount must be ≤ that advance's remaining (recomputed under lock).
    Invariant: amount_paid + Σrecoveries ≤ current payable (can't settle more
    than is owed). Equality = full settlement (payable → 0).

    write_offs (R7, PDD §27-D5): [{'advance': <WorkerAdvance|id>,
    'reason': str}, …] — F&F forgives each advance's REMAINING amount as an
    audited PSI row with NO ledger debit (a forgiven loan is not a payment;
    payable untouched, outstanding derives to 0). Super-admin only, mandatory
    reason, reversible via the same `reversed_at` stamp as any recovery.

    Side effects (money / multi-write):
      • Acquires a PG transaction-scoped advisory lock (settlement-ref serialization).
      • Row-locks WorkerProfile (get_or_create may INSERT it) + the worker's WorkerAdvance rows (FOR UPDATE).
      • Writes PayrollSettlement (1 row) + PayrollSettlementItem (1 per recovery / write-off).
      • Calls ledger_service.log_debit → writes WorkerLedgerEntry (settlement_payment and/or advance_recovery debit).
      • Reads (no write) ledger_service.worker_balance + payroll_service.advance_remaining/advance_outstanding.
    """
    _ensure_management(user)
    write_offs = write_offs or []
    if write_offs:
        # D5 posture: forgiving money = super-admin + reason, like void/rerate.
        from accounts.services import ROLE_SUPER_ADMIN, user_has_role
        if not user_has_role(user, {ROLE_SUPER_ADMIN}):
            raise PermissionDenied(
                "Only a Super Admin can write off an advance.")

    # V2-2 (Model A, §11.2): advance recovery RE-HOMED to the AddaSettlement
    # finalize. This event is PAYMENT-ONLY now — cash debit, nothing else.
    if recoveries:
        raise ValidationError(
            "Advance recovery now happens at Adda settlement (finalize), not at "
            "payment. Settle the Adda first; pay cash here afterwards.")

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

    # R7: validate write-offs under the SAME advance locks. Each forgives the
    # advance's full remaining (partial write-off = YAGNI until asked).
    cleaned_write_offs: list[tuple[WorkerAdvance, Decimal, str]] = []
    for w in write_offs:
        adv = w['advance']
        adv = locked.get(int(getattr(adv, 'id', adv)))
        if adv is None:
            raise ValidationError("Write-off advance does not belong to this worker.")
        reason = (w.get('reason') or '').strip()
        if not reason:
            raise ValidationError("A reason is required to write off an advance.")
        residual = payroll_service.advance_remaining(adv)
        # Recoveries in THIS settlement are ledger-side; PSI rows not yet
        # written, so subtract this call's own recoveries from the residual.
        residual -= sum(amt for a, amt in cleaned if a.pk == adv.pk)
        if residual <= _ZERO:
            raise ValidationError(
                f"Advance #{adv.id} has nothing left to write off.")
        cleaned_write_offs.append((adv, residual, reason))

    payable_before = ledger_service.worker_balance(worker)
    advance_outstanding_before = payroll_service.advance_outstanding(worker)

    total_settled = paid + advance_deducted
    if total_settled <= _ZERO and not cleaned_write_offs:
        raise ValidationError("A settlement must pay, recover, or write off something.")
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
    # R7 write-offs: PSI rows with NO ledger debit — outstanding derives to 0,
    # payable untouched (D5: audited on the row, reversible via reversed_at).
    for adv, residual, reason in cleaned_write_offs:
        PayrollSettlementItem.objects.create(
            settlement=settlement, advance=adv, amount_recovered=residual,
            write_off_reason=reason[:200], written_off_by=user,
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
    logger.info(
        "expense.settle ref=%s settlement_id=%s worker_id=%s paid=%s "
        "advance_recovered=%s total_settled=%s payable_before=%s recoveries=%s",
        settlement.reference, settlement.id, worker.id, paid, advance_deducted,
        total_settled, payable_before, len(cleaned),
    )
    return settlement
