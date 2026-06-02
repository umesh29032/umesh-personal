"""Rename the 'karigar' Role → 'worker' (code + display name), 2026-06-02.

Aligns the RBAC role with the spec terminology + the user_type rename. FK/M2M
references (User.role, Stage.access_by_role, SidebarItemRule.allowed_roles) point
by PK, so they survive the code change untouched — only the Role row's code/name
string changes. Idempotent + reversible.
"""
from django.db import migrations


def forwards(apps, schema_editor):
    Role = apps.get_model('inventory', 'Role')
    Role.objects.filter(code='karigar').update(code='worker', name='Worker')


def backwards(apps, schema_editor):
    Role = apps.get_model('inventory', 'Role')
    Role.objects.filter(code='worker').update(code='karigar', name='Karigar')


class Migration(migrations.Migration):
    dependencies = [
        ('inventory', '0018_tighten_products_seed_access_hub'),
        # accounts 0011 assigned explicit roles (incl. the karigar Role) by code;
        # run after it so the rename lands on a fully-populated Role.
        ('accounts', '0011_alter_user_user_type'),
    ]
    operations = [
        migrations.RunPython(forwards, backwards),
    ]
