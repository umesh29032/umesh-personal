"""Sidebar Access rules — THE writer for SidebarItemRule role/skill assignments.

RCP-1A F1 (2026-07-18): yeh bulk permission write pehle view mein tha (Law-4
violation — service layer owns multi-row writes). Ab service own karta hai;
behaviour byte-same. super_admin roles write-time par EXCLUDE hote hain
(read-time enforcement permission_service.build_menu_for mein pehle se hai —
double wall).
"""
from __future__ import annotations

from django.db import transaction

from accounts.models import Skill
from accounts.services import ROLE_SUPER_ADMIN

from ..models import Role, SidebarItemRule


@transaction.atomic
def save_sidebar_rules(assignments):
    """Bulk-upsert menu visibility. `assignments` = {rule_id: (role_ids, skill_ids)}
    — primitives only (ADR-0006 async-ready signatures). A rule absent from the
    mapping is CLEARED — same semantics as the full-form POST it serves (every
    rule posts its checkbox lists; nothing ticked = empty lists).

    M2M .set() per rule = delete+insert on the two through-tables inside ONE
    transaction (service-owned atomicity, Law 4).
    """
    rules = list(SidebarItemRule.objects.all())
    for rule in rules:
        role_ids, skill_ids = assignments.get(rule.id, ([], []))
        rule.allowed_roles.set(
            Role.objects.filter(id__in=role_ids).exclude(code=ROLE_SUPER_ADMIN)
        )
        rule.allowed_skills.set(Skill.objects.filter(id__in=skill_ids))
    return len(rules)
