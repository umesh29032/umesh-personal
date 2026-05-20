"""Shared service primitives — authorization helpers across stages.

YEH FILE KYU HAI?
─────────────────
Stages (layering, cutting, future) share role/skill auth gates. Common code
lives here so per-stage service files stay focused on the stage's own state
transitions.

Pattern (per-stage service file):
    from production.services._shared import (
        _ensure_can_manage, _ensure_management, _ensure_assigned_worker, ...
    )
"""
from __future__ import annotations

from django.core.exceptions import PermissionDenied

from accounts.skills import SKILL_CUTTING_MASTER, SKILL_CUTTING_MASTER_HELPER, user_has_skill
from inventory.services import MANAGEMENT_ROLES, PRODUCTION_ROLES, user_has_role
from production.models import AddaStageRecord


def _ensure_can_manage(user):
    """Production role gate (super_admin / manager / karigar)."""
    if not user_has_role(user, PRODUCTION_ROLES):
        raise PermissionDenied("requires production role")


def _ensure_management(user):
    """Management role gate ({super_admin, manager}). For worker assignment etc."""
    if not user_has_role(user, MANAGEMENT_ROLES):
        raise PermissionDenied("requires management role (super_admin/manager)")


def _ensure_assigned_worker(stage_record: AddaStageRecord, user):
    """User is assigned worker OR management. Super_admin bypasses via role."""
    if user_has_role(user, MANAGEMENT_ROLES):
        return
    if not stage_record.workers.filter(pk=user.pk).exists():
        raise PermissionDenied("not assigned to this stage")


def _ensure_layering_skill(user):
    """Cutting_master or cutting_master_helper required. Management bypass."""
    if user_has_role(user, MANAGEMENT_ROLES):
        return
    if not user_has_skill(user, [SKILL_CUTTING_MASTER, SKILL_CUTTING_MASTER_HELPER]):
        raise PermissionDenied("requires cutting_master or cutting_master_helper skill")


def _ensure_can_complete_layering(user):
    """Layering→Cutting transition: only cutting_master_helper (super_admin bypass)."""
    if user_has_role(user, {'super_admin'}):
        return
    if not user_has_skill(user, SKILL_CUTTING_MASTER_HELPER):
        raise PermissionDenied("only cutting_master_helper can complete Layering stage")
