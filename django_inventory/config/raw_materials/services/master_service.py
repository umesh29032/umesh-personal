"""Master data CRUD ka service layer.

YEH FILE KYU HAI?
─────────────────
ClothType / ClothColor / StorageLocation ka archive/restore/hard_delete yahan se hota hai.
Views direct .save() / .delete() nahi karte — service call karte hain.

Soft vs hard delete?
────────────────────
Soft (archive)   = is_active=False — historical rolls intact rehte hain
Hard (delete)    = SQL DELETE — sirf jab koi FK reference NA ho. PROTECT FK exception throw kar de
                   to ValidationError mein convert karte hain taa-ke 500 na de.
"""
from django.db import transaction
from django.core.exceptions import ValidationError, PermissionDenied
from django.db.models import ProtectedError

from inventory.services import PRODUCTION_ROLES, user_has_role


def _ensure_can_manage(user):
    """Production roles (super_admin/manager/karigar) check — service-side gate."""
    if not user_has_role(user, PRODUCTION_ROLES):
        raise PermissionDenied("requires production role")


@transaction.atomic
def archive_master(user, instance):
    """Soft-delete: is_active=False. ClothType/Color/Location teeno yahan se archive hote hain.

    Idempotent — already archived row pe call kiya to no-op.
    """
    _ensure_can_manage(user)
    if not getattr(instance, 'is_active', True):
        return instance  # already inactive — nothing to do
    instance.is_active = False
    # update_fields = sirf ek column UPDATE hoga, baaki untouched
    instance.save(update_fields=['is_active'])
    return instance


@transaction.atomic
def restore_master(user, instance):
    """Archived row ko wapas active karta hai. UI mein dropdowns mein dikhne lagta hai."""
    _ensure_can_manage(user)
    instance.is_active = True
    instance.save(update_fields=['is_active'])
    return instance


@transaction.atomic
def hard_delete_master(user, instance):
    """Permanent delete. Sirf jab koi cloth roll iss row ko reference NA kar raha ho.

    on_delete=PROTECT ki wajah se agar references hain to Django ProtectedError throw karega.
    Use ham ValidationError mein wrap kar dete hain — views user-friendly message render kar paayein
    instead of 500 error page.
    """
    _ensure_can_manage(user)
    try:
        instance.delete()
    except ProtectedError as exc:
        raise ValidationError(
            "Cannot delete — this record is still referenced by other rows. "
            "Archive it instead."
        ) from exc
