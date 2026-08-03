"""Advance service — sole writer of WorkerAdvance.

An advance is a SEPARATE loan pool. It is NOT posted to the payable ledger
(that was the old monthly-payroll model). Under the settlement model the owner
recovers advances at settlement time, by their own per-advance choice (D3). So
recording an advance only creates the immutable WorkerAdvance row; recovery
happens later in settlement_service.

Advance outstanding is derived (payroll_service.advance_outstanding), never stored.
"""
from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from expense.models import WorkerAdvance
from ._shared import _ensure_management


@transaction.atomic
def record_advance(*, user, worker, amount, advance_date=None, notes='',
                   attachment=None):
    """Record an immutable advance (a loan to the worker). No ledger debit —
    advances are recovered at settlement, not netted against earnings here."""
    _ensure_management(user)
    # ⚠ TEMPORARY business rule (owner, hostile-review M-2, 2026-07-05):
    # monthly workers cannot take advances — BOTH recovery paths are
    # unreachable for them (settlement recovery needs settlement lines they
    # never have; cash recovery needs payable > 0, theirs is always 0), so
    # the money would sit outstanding until F&F write-off. Revisit when the
    # monthly-salary workflow grows a salary-deduction recovery path.
    from expense.services.payroll_service import is_monthly
    if is_monthly(worker):
        raise ValidationError(
            "Advances are not available for monthly-salary workers yet — "
            "there is no recovery path (their pay never flows through "
            "settlement). Handle any loan through their salary for now.")
    amt = Decimal(str(amount))
    if amt <= 0:
        raise ValidationError("Advance amount must be greater than 0.")
    when = advance_date or timezone.localdate()

    return WorkerAdvance.objects.create(
        worker=worker, amount=amt, advance_date=when,
        notes=notes, attachment=attachment, entered_by=user,
    )
