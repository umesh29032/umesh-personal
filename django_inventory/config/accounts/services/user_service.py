"""User-provisioning service — the single home for write-side User invariants.

YEH FILE KYU HAI?
─────────────────
accounts ab baaki apps ki tarah service layer follow karta hai. Security-critical
invariants jo HAR write path (view, Django admin, shell, future API) pe hold karne
chahiye yahan rehte hain, taaki koi path inhe bypass na kare:
  • platform ka aakhri active Super Admin kabhi orphan na ho   → delete_user()
  • Super Admin khud ko demote/deactivate/role-drop na kar paaye → self_edit_blockers()

Plus the skill→layering retro-tag jo pehle `accounts/signals.py` (m2m_changed) mein
tha — ab explicit service call (CLAUDE.md rule #4: no signals). Cross-app write ab
greppable + ek hi jagah, transaction ke andar.
"""
from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import connection, transaction
from django.db.models import Q

from accounts.models import User
from .permission_service import ROLE_SUPER_ADMIN

# Stable 32-bit key for the txn-scoped advisory lock that serializes admin-set
# mutations (delete / demote) so the "last active Super Admin" count can't race
# (mirrors the pattern in expense.settlement_service). Auto-releases on commit.
_ADMIN_SET_LOCK = 0x4B41444D  # 'KADM'


def _is_admin(user) -> bool:
    """A user is an admin if is_superuser OR holds the super_admin role.

    ONE definition so the access gate (role-based) and the last-admin guard
    (was is_superuser-based) can never disagree — previously they could diverge.
    """
    if getattr(user, 'is_superuser', False):
        return True
    role = getattr(user, 'role', None)
    return bool(role and role.code == ROLE_SUPER_ADMIN)


def _active_admin_qs():
    return User.objects.filter(is_active=True).filter(
        Q(is_superuser=True) | Q(role__code=ROLE_SUPER_ADMIN)
    )


def count_active_admins(*, exclude_pk=None) -> int:
    """How many active Super Admins exist (is_superuser OR super_admin role)."""
    qs = _active_admin_qs()
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    return qs.distinct().count()


def self_edit_blockers(actor, *, new_is_superuser, new_is_active, new_role) -> list[str]:
    """Self-lockout rule (pure, no DB): actions a Super Admin must NOT do to
    their OWN profile in one request (would orphan the platform). Returns the
    list of attempted blocked actions — empty means the edit is allowed.
    """
    blockers: list[str] = []
    if getattr(actor, 'is_superuser', False) and not new_is_superuser:
        blockers.append("revoke your own superuser flag")
    if not new_is_active:
        blockers.append("deactivate your own account")
    current_role_code = getattr(getattr(actor, 'role', None), 'code', None)
    if current_role_code == ROLE_SUPER_ADMIN and (
        new_role is None or new_role.code != ROLE_SUPER_ADMIN
    ):
        blockers.append("change your own RBAC role away from Super Admin")
    return blockers


@transaction.atomic
def delete_user(user_to_delete, *, actor) -> None:
    """Delete a user, enforcing self-delete + last-admin invariants atomically.

    Race-safe: a txn-scoped Postgres advisory lock serializes concurrent admin
    deletes/demotions, so two requests can't each see "another admin remains"
    and both delete the last one. Raises ValidationError on refusal; the caller
    surfaces `.messages[0]` to the user.
    """
    if user_to_delete.pk == getattr(actor, 'pk', None):
        raise ValidationError("You cannot delete your own account.")
    # Serialize the check-then-delete against other admin-set mutations.
    with connection.cursor() as cur:
        cur.execute('SELECT pg_advisory_xact_lock(%s)', [_ADMIN_SET_LOCK])
    if _is_admin(user_to_delete) and count_active_admins(exclude_pk=user_to_delete.pk) == 0:
        raise ValidationError(
            "Refused: this is the only active Super Admin. Promote another user first."
        )
    user_to_delete.delete()


def sync_user_skills(user) -> int:
    """Retro-tag `user` onto active Layering rosters for their current skills.

    Replaces the old `accounts/signals.py` m2m_changed signal (CLAUDE.md rule #4).
    Call AFTER skills are saved on a user-management write path (Team Members
    views + Django admin `save_related`). The cross-app write into production is
    now an explicit, greppable call here instead of a hidden signal.
    """
    # Lazy import: production is a higher layer (Phase-5 formalizes the direction).
    from production.services import sync_layering_workers_for_skill
    return sync_layering_workers_for_skill(user)
