"""Stage access control — reads Stage model (production.models.Stage).

YEH FILE KYU HAI?
─────────────────
Pehle hardcoded `_access_for(stage_type)` adda_views.py mein tha, phir
StageAccessRule alag table thi. Ab Stage hi pehla-class model hai aur
access controls usi pe baithe hain (access_by_skill, access_by_role).

Defense-in-depth: Super Admin + Manager hardcoded grant — Stage row corrupt
ho jaye toh bhi unka access bana rehta hai (otherwise system unmanageable).
"""
from __future__ import annotations

from typing import Iterable

from inventory.services import MANAGEMENT_ROLES, user_has_role


def _user_skill_ids(user) -> set[int]:
    if not user or not user.is_authenticated:
        return set()
    return set(user.skills.values_list('id', flat=True))


def _user_role_ids(user) -> set[int]:
    """Primary role + extra_roles M2M combined into one set."""
    if not user or not user.is_authenticated:
        return set()
    ids: set[int] = set()
    if user.role_id:
        ids.add(user.role_id)
    ids.update(user.extra_roles.values_list('id', flat=True))
    return ids


def user_can_access_stage(user, stage_code: str) -> bool:
    """Returns True if user can view the embedded stage panel + records.

    Logic order:
      1. unauthenticated → False
      2. Super Admin / Manager → always True (built-in, not editable)
      3. Lookup Stage by code
         - missing or inactive → False (fail-closed)
         - skill overlap → True
         - role overlap (primary or extra) → True
      4. else False
    """
    if not user or not user.is_authenticated:
        return False
    if user_has_role(user, MANAGEMENT_ROLES):
        return True

    # Lazy import to avoid circular: production.models imports inventory.Role.
    from production.models import Stage

    stage = (
        Stage.objects
        .filter(code=stage_code, is_active=True)
        .prefetch_related('access_by_skill', 'access_by_role')
        .first()
    )
    if stage is None:
        return False

    allowed_skill_ids = set(stage.access_by_skill.values_list('id', flat=True))
    if allowed_skill_ids & _user_skill_ids(user):
        return True

    allowed_role_ids = set(stage.access_by_role.values_list('id', flat=True))
    if allowed_role_ids & _user_role_ids(user):
        return True

    return False


def stage_access_map(user, stage_codes: Iterable[str]) -> dict[str, bool]:
    """Batched helper for templates: {stage_code: bool} for a list of codes.

    Avoids re-querying Stage per stage when adda_detail.html iterates over
    7+ stages in the product flow.
    """
    codes = list(stage_codes)
    if not user or not user.is_authenticated:
        return {c: False for c in codes}
    if user_has_role(user, MANAGEMENT_ROLES):
        return {c: True for c in codes}

    from production.models import Stage

    stages = {
        s.code: s
        for s in Stage.objects
        .filter(code__in=codes, is_active=True)
        .prefetch_related('access_by_skill', 'access_by_role')
    }
    user_skills = _user_skill_ids(user)
    user_roles = _user_role_ids(user)

    out: dict[str, bool] = {}
    for code in codes:
        stage = stages.get(code)
        if stage is None:
            out[code] = False
            continue
        allowed_skills = set(stage.access_by_skill.values_list('id', flat=True))
        if allowed_skills & user_skills:
            out[code] = True
            continue
        allowed_roles = set(stage.access_by_role.values_list('id', flat=True))
        out[code] = bool(allowed_roles & user_roles)
    return out
