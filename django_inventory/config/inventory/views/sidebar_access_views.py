"""Sidebar Access Control — Super Admin edits which roles see which menu item.

YEH FILE KYU HAI?
─────────────────
Pehle sidebar visibility hardcoded thi (permission_service.SIDEBAR predicates).
Ab DB-backed (inventory.models.SidebarItemRule). Yeh view items ko section ke
hisaab se group karke role-checkbox grid render karta hai. Save = bulk upsert.

Super Admin is implicit and not editable — service layer enforces it (in
permission_service.build_menu_for). This page only shows + edits OTHER roles.
"""
from __future__ import annotations

from collections import defaultdict

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import TemplateView

from accounts.models import Skill

from ..models import Role, SidebarItemRule
from ..services import ROLE_SUPER_ADMIN, user_has_role
from ..services.sidebar_service import save_sidebar_rules


class _SuperAdminOnly(UserPassesTestMixin):
    def test_func(self):
        return user_has_role(self.request.user, {ROLE_SUPER_ADMIN})


class SidebarAccessListView(LoginRequiredMixin, _SuperAdminOnly, TemplateView):
    template_name = 'inventory/sidebar_access_list.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        all_roles = list(Role.objects.exclude(code=ROLE_SUPER_ADMIN).order_by('name'))
        all_skills = list(Skill.objects.all())
        rules = list(
            SidebarItemRule.objects.prefetch_related('allowed_roles', 'allowed_skills')
        )

        # Group items by section. Preserve a stable order (Main, Storefront, ...)
        # using a small priority map; unknowns get appended alphabetically.
        section_order = {
            'Main': 0, 'Storefront': 1, 'Raw Materials': 2,
            'Production': 3, 'Tracking': 4, 'Administration': 5,
        }
        grouped: dict[str, list] = defaultdict(list)
        for rule in rules:
            selected_role_ids = set(rule.allowed_roles.values_list('id', flat=True))
            selected_skill_ids = set(rule.allowed_skills.values_list('id', flat=True))
            grouped[rule.section].append({
                'id': rule.id,
                'url_name': rule.url_name,
                'label': rule.label,
                'roles': [
                    {'id': r.id, 'name': r.name, 'selected': r.id in selected_role_ids}
                    for r in all_roles
                ],
                'skills': [
                    {'id': s.id, 'label': s.get_name_display(), 'selected': s.id in selected_skill_ids}
                    for s in all_skills
                ],
            })

        sections = sorted(
            grouped.items(),
            key=lambda kv: (section_order.get(kv[0], 99), kv[0]),
        )
        ctx.update({
            'sections': [{'label': s, 'items': items} for s, items in sections],
            'all_roles': all_roles,
            'all_skills': all_skills,
        })
        return ctx

    def post(self, request, *args, **kwargs):
        # View = parse-only (Law 4, RCP-1A F1): POST checkbox lists → primitive
        # mapping → the service owns the transactional multi-row write.
        assignments = {
            rule_id: (
                [int(x) for x in request.POST.getlist(f'roles_{rule_id}') if x.isdigit()],
                [int(x) for x in request.POST.getlist(f'skills_{rule_id}') if x.isdigit()],
            )
            for rule_id in SidebarItemRule.objects.values_list('id', flat=True)
        }
        save_sidebar_rules(assignments)
        messages.success(request, 'Sidebar access rules saved.')
        return redirect(reverse_lazy('inventory:sidebar-access'))
