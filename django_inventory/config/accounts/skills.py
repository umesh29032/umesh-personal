"""Skill-based access helpers.

YEH FILE KYU HAI?
─────────────────
Skill checks alag se rakhe hain RBAC se. `inventory.services.permission_service`
role-based gating handle karta hai — yahan `accounts.Skill` M2M ke checks.

Future stage transitions (layering → cutting, cutting → packing, ...) skill
type pe depend karte hain (production's stage services yeh helpers call karte hain).
"""
from __future__ import annotations

from typing import Iterable


# Skill name constants — string literals scatter na ho, isliye ek hi jagah.
# Values must match the `Skill.name` slug stored in the DB (Skill is a model now,
# not the old SKILL_TYPE_CHOICES enum).
SKILL_CUTTING_MASTER = 'cutting_master'
SKILL_CUTTING_MASTER_HELPER = 'cutting_master_helper'


def user_skill_names(user) -> set[str]:
    """User ke saare skill names (Skill.name) ka set return karta hai.

    Anonymous / no user → empty set. M2M ek SELECT karti hai; agar same request
    mein baar-baar chahiye to caller cache kar le.
    """
    if not user or not getattr(user, 'is_authenticated', False):
        return set()
    skills_qs = getattr(user, 'skills', None)
    if skills_qs is None:
        return set()
    try:
        # values_list(flat=True) → list of strings directly, koi tuple wrapping nahi
        return set(skills_qs.values_list('name', flat=True))
    except (AttributeError, TypeError):
        # Test doubles jo real M2M descriptor expose nahi karte
        return set()


def user_has_skill(user, skill_names: str | Iterable[str]) -> bool:
    """True if user has ANY of the given skill name(s).

    Single string ya iterable dono accept karta hai. Stage-transition gates
    isi se use karenge:
        user_has_skill(user, SKILL_CUTTING_MASTER_HELPER)
        user_has_skill(user, [SKILL_CUTTING_MASTER, SKILL_CUTTING_MASTER_HELPER])
    """
    if isinstance(skill_names, str):
        wanted = {skill_names}
    else:
        wanted = set(skill_names)
    return bool(user_skill_names(user) & wanted)
