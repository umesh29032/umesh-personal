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

# Stage access reuses the SAME request-cached identity resolver as the sidebar
# (inventory.user_principal) — one definition of "who is this user, RBAC-wise".
from accounts.services import MANAGEMENT_ROLES, user_has_role, user_principal


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

    principal = user_principal(user)
    # `.all()` uses the prefetch_related cache; `.values_list()` would re-query.
    if {s.id for s in stage.access_by_skill.all()} & principal['skill_ids']:
        return True
    if {r.id for r in stage.access_by_role.all()} & principal['role_ids']:
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
    principal = user_principal(user)
    user_skills = principal['skill_ids']
    user_roles = principal['role_ids']

    out: dict[str, bool] = {}
    for code in codes:
        stage = stages.get(code)
        if stage is None:
            out[code] = False
            continue
        # `.all()` uses the prefetch cache (0 extra queries per stage).
        if {s.id for s in stage.access_by_skill.all()} & user_skills:
            out[code] = True
            continue
        out[code] = bool({r.id for r in stage.access_by_role.all()} & user_roles)
    return out


def eligible_stage_workers(stage_code: str):
    """THE shared worker-picker population for a stage (F-4 polish 2026-07-05).

    Active users holding any of the stage's `access_by_skill` skills — i.e.
    exactly the workers `user_can_access_stage` will later admit, so an
    assignment picker can never offer someone the access gate would 403.
    Pure lazy queryset (no DB hit until evaluated) so forms may build it at
    class-definition time. DB-driven via Stage.access_by_skill: a new stage's
    picker follows its Access-Control config with zero picker code.
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()
    return (
        User.objects.filter(
            is_active=True,
            skills__accessible_stages__code=stage_code,
            skills__accessible_stages__is_active=True,
        )
        .distinct()
        .order_by('email')
    )
