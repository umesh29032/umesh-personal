"""Seed the SidebarItemRule row for patterns_ai (idempotent, config-as-data).

Without a row, the entry already works via the in-code SIDEBAR predicate
(management-only); this row hands control to the Sidebar Access admin page —
same governance as every other menu item (V1 rule 6: menu + URL co-gated).
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create/refresh the SidebarItemRule for Pattern Intelligence (mgmt roles)."

    def handle(self, *args, **options):
        from accounts.models import Role, SidebarItemRule

        rule, created = SidebarItemRule.objects.update_or_create(
            url_name='patterns_ai:home',
            defaults={'section': 'Production', 'label': 'Pattern Intelligence'},
        )
        roles = Role.objects.filter(code__in=('super_admin', 'manager'))
        rule.allowed_roles.set(roles)
        self.stdout.write(self.style.SUCCESS(
            "SidebarItemRule %s: patterns_ai:home -> roles %s"
            % ('created' if created else 'updated',
               ', '.join(r.code for r in roles))))
