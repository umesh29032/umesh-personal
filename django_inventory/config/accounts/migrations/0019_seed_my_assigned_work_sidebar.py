"""AE-3 (2026-07-20): add the worker "My Assigned Work" nav item.

Idempotent (update_or_create on url_name), mirrors 0017's seed pattern. Managers +
workers see it (super_admin implicit). The SidebarItemRule also makes the sidebar
middleware treat /production/my-work/ as a covered, role-allowed URL.
"""
from django.db import migrations

ITEM = ('Production', 'My Assigned Work', 'production:my-work', ['manager', 'worker'])


def seed(apps, schema_editor):
    SidebarItemRule = apps.get_model('accounts', 'SidebarItemRule')
    Role = apps.get_model('accounts', 'Role')
    role_by_code = {r.code: r for r in Role.objects.all()}
    section, label, url_name, role_codes = ITEM
    rule, _ = SidebarItemRule.objects.update_or_create(
        url_name=url_name, defaults={'section': section, 'label': label})
    rule.allowed_roles.set([role_by_code[c] for c in role_codes if c in role_by_code])


def unseed(apps, schema_editor):
    SidebarItemRule = apps.get_model('accounts', 'SidebarItemRule')
    SidebarItemRule.objects.filter(url_name=ITEM[2]).delete()


class Migration(migrations.Migration):
    dependencies = [('accounts', '0018_worker_sidebar_lockdown')]
    operations = [migrations.RunPython(seed, unseed)]
