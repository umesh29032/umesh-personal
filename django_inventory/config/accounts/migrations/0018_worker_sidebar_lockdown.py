"""H-3 / J-4 worker visibility lockdown (owner-approved 2026-07-06).

Strip the `worker` role from the sidebar rules that exposed factory-wide pages
(raw-materials suite, Operations, all-Addas list, Tracking). SidebarItemRule
gates the MENU LINK and the URL together (SidebarAccessMiddleware), so this one
data change removes both. Workers keep: My Dashboard (exempt landing),
My Earnings (unmanaged item, worker-predicate), their Adda/report pages
(unmanaged action URLs, gated by access ∩ assignment).

Idempotent; reverse re-adds worker to exactly these rules.
"""
from django.db import migrations

LOCKDOWN_URL_NAMES = [
    'raw_materials:dashboard',
    'raw_materials:cloth-dashboard',
    'raw_materials:roll-list',
    'raw_materials:cloth-type-list',
    'raw_materials:cloth-color-list',
    'raw_materials:storage-list',
    'production:dashboard',
    'production:adda-list',
    'tracking:dashboard',
]


def strip_worker(apps, schema_editor):
    SidebarItemRule = apps.get_model('accounts', 'SidebarItemRule')
    Role = apps.get_model('accounts', 'Role')
    worker = Role.objects.filter(code='worker').first()
    if worker is None:
        return
    for rule in SidebarItemRule.objects.filter(url_name__in=LOCKDOWN_URL_NAMES):
        rule.allowed_roles.remove(worker)


def restore_worker(apps, schema_editor):
    SidebarItemRule = apps.get_model('accounts', 'SidebarItemRule')
    Role = apps.get_model('accounts', 'Role')
    worker = Role.objects.filter(code='worker').first()
    if worker is None:
        return
    for rule in SidebarItemRule.objects.filter(url_name__in=LOCKDOWN_URL_NAMES):
        rule.allowed_roles.add(worker)


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0017_seed_sidebar_rules'),
    ]
    operations = [
        migrations.RunPython(strip_worker, restore_worker),
    ]
