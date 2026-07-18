"""Shared auth gates + money primitives for the expense app. No DB writes."""
from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import PermissionDenied

from accounts.services import MANAGEMENT_ROLES, user_has_role


def _ensure_management(user):
    """Only manager / super_admin may write payroll (allocate, advance, pay)."""
    if not user_has_role(user, MANAGEMENT_ROLES):
        raise PermissionDenied("requires manager or super_admin role")


def q_paisa(amount) -> Decimal:
    """THE expense rounding rule: str() first (no float binary-expansion leaks),
    quantize to paisa, HALF_UP — every money row is exactly 2dp."""
    return Decimal(str(amount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def next_reference(model, prefix) -> str:
    """PREFIX-0001, … — gap-tolerant (max existing + 1). Caller must hold the
    settlement-reference advisory lock; `reference` is the model's unique field."""
    last = model.objects.order_by('-id').values_list('reference', flat=True).first()
    n = 0
    if last and last.startswith(prefix + '-'):
        try:
            n = int(last.split('-', 1)[1])
        except (ValueError, IndexError):
            n = model.objects.count()
    return f"{prefix}-{n + 1:04d}"
