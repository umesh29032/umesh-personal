"""RBAC review fix (2026-06-02):

1. Products list is management-only now (ProductListView → ManagementRoleMixin),
   so drop `karigar` from the 'production:product-list' SidebarItemRule — the
   shop floor should NOT see Products (master-spec: Worker ✖).
2. Seed a SidebarItemRule for the new Access Control hub so it's DB-governed
   (super_admin only) instead of falling back to the in-code predicate.

Additive + reversible. Idempotent (no-op if rows are absent).
"""
from django.db import migrations


def forwards(apps, schema_editor):
    SidebarItemRule = apps.get_model('inventory', 'SidebarItemRule')
    Role = apps.get_model('inventory', 'Role')

    # 1. Products → manager only (remove karigar).
    rule = SidebarItemRule.objects.filter(url_name='production:product-list').first()
    if rule is not None:
        mgr = Role.objects.filter(code='manager').first()
        rule.allowed_roles.set([mgr] if mgr else [])

    # 2. Access Control hub rule (super_admin implicit → empty allowed_roles).
    SidebarItemRule.objects.get_or_create(
        url_name='inventory:access-control',
        defaults={'section': 'Administration', 'label': 'Access Control'},
    )


def backwards(apps, schema_editor):
    SidebarItemRule = apps.get_model('inventory', 'SidebarItemRule')
    Role = apps.get_model('inventory', 'Role')

    rule = SidebarItemRule.objects.filter(url_name='production:product-list').first()
    if rule is not None:
        codes = ['manager', 'karigar']
        rule.allowed_roles.set(Role.objects.filter(code__in=codes))

    SidebarItemRule.objects.filter(url_name='inventory:access-control').delete()


class Migration(migrations.Migration):
    dependencies = [
        ('inventory', '0017_rename_stage_access_sidebar_rule'),
    ]
    operations = [
        migrations.RunPython(forwards, backwards),
    ]
