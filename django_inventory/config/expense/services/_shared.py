"""Shared auth gates for the expense app. No DB writes."""
from django.core.exceptions import PermissionDenied

from inventory.services import MANAGEMENT_ROLES, user_has_role


def _ensure_management(user):
    """Only manager / super_admin may write payroll (allocate, advance, pay)."""
    if not user_has_role(user, MANAGEMENT_ROLES):
        raise PermissionDenied("requires manager or super_admin role")
