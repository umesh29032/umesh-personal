"""Access Control hub — ONE Super-Admin page that surfaces the whole RBAC
picture in cross-functional matrices that no single page showed before:

  1. Roles × Sidebar Pages  — who sees which menu item (from SidebarItemRule).
  2. Skills × Stages        — which skill/role unlocks each production stage.
  3. Users roster           — user_type + role + extra_roles + skills per user.
  4. Roles summary          — permission count per role.

It is READ-ONLY by design: each matrix deep-links to the existing, well-tested
CRUD page that edits it (Sidebar Access / Stages / Team Members / Roles). This
fills the "single admin surface" gap without rewriting battle-tested editors.

Three concepts stay strictly separate (and the page explains them):
  • User Type — 1:1, display/baseline only (never gates access).
  • Role      — M2M, grants module/page/admin access.
  • Skill     — M2M, grants production-stage work capability.
"""
from __future__ import annotations

from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from production.models import Stage

from ..models import Role, SidebarItemRule
from ..services import ROLE_SUPER_ADMIN
from ..services.permission_service import SIDEBAR
from .mixins import SuperAdminOnlyMixin

User = get_user_model()


class AccessControlHubView(LoginRequiredMixin, SuperAdminOnlyMixin, TemplateView):
    template_name = 'inventory/access_control.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # Columns for the visibility matrix = every role EXCEPT super_admin
        # (super_admin is hardcoded-always-visible at the service layer).
        roles = list(Role.objects.exclude(code=ROLE_SUPER_ADMIN).order_by('name'))

        # ── Matrix 1: Roles × Sidebar Pages ──────────────────────────────────
        # Walk the in-code SIDEBAR registry (the source of truth for menu items)
        # and join each item to its SidebarItemRule (the DB override the Sidebar
        # Access page edits). Items with no rule are "code-gated" — surfaced
        # explicitly so coverage gaps are visible, not silent.
        rules = {
            r.url_name: r for r in
            SidebarItemRule.objects.prefetch_related('allowed_roles', 'allowed_skills')
        }
        page_sections: list[dict] = []
        for section in SIDEBAR:
            item_rows = []
            for item in section.items:
                rule = rules.get(item.url_name)
                if rule is not None:
                    allowed_role_ids = set(rule.allowed_roles.values_list('id', flat=True))
                    cells = [{'role': r, 'on': r.id in allowed_role_ids} for r in roles]
                    skills_on = [s.get_name_display() for s in rule.allowed_skills.all()]
                    governed = 'db'
                else:
                    cells = [{'role': r, 'on': None} for r in roles]
                    skills_on = []
                    governed = 'code'
                item_rows.append({
                    'label': item.label, 'url_name': item.url_name,
                    'cells': cells, 'skills_on': skills_on, 'governed': governed,
                })
            if item_rows:
                page_sections.append({'label': section.label, 'rows': item_rows})

        # ── Matrix 2: Skills/Roles × Stages ──────────────────────────────────
        stage_rows = []
        for st in Stage.objects.prefetch_related('access_by_skill', 'access_by_role').order_by('name'):
            stage_rows.append({
                'name': st.name, 'code': st.code, 'is_active': st.is_active,
                'skills': [s.get_name_display() for s in st.access_by_skill.all()],
                'roles': [r.name for r in st.access_by_role.all()],
            })

        # ── Matrix 3: Users roster ───────────────────────────────────────────
        user_rows = []
        for u in (
            User.objects.select_related('role')
            .prefetch_related('extra_roles', 'skills').order_by('email')
        ):
            user_rows.append({
                'email': u.email,
                'user_type': u.get_user_type_display(),
                'role': u.role.name if u.role_id else None,
                'extra_roles': [r.name for r in u.extra_roles.all()],
                'skills': [s.get_name_display() for s in u.skills.all()],
                'is_superuser': u.is_superuser,
                'is_active': u.is_active,
            })

        # ── Matrix 4: Roles summary ──────────────────────────────────────────
        role_summary = [
            {'name': r.name, 'code': r.code, 'is_system': r.is_system,
             'perm_count': r.permissions.count()}
            for r in Role.objects.order_by('name')
        ]

        ctx.update({
            'roles': roles,
            'page_sections': page_sections,
            'stage_rows': stage_rows,
            'user_rows': user_rows,
            'role_summary': role_summary,
        })
        return ctx
