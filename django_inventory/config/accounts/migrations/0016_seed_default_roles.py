"""Seed the default system Roles into accounts (RBAC relocated here 2026-06).

Mirrors the end-state of the old inventory role seeds (0010 super_admin/manager/
karigar, 0011 listing_team, 0013 accountant, 0019 karigar→worker). Roles only —
no migration ever seeded role.permissions (those are granted at runtime via the
role editor; super_admin bypasses perms entirely). Idempotent (update_or_create).
"""
from django.db import migrations


SYSTEM_ROLES = [
    {'code': 'super_admin', 'name': 'Super Admin',
     'description': 'Full access to every feature. User + role management exclusive to this role.'},
    {'code': 'manager', 'name': 'Manager',
     'description': 'Runs day-to-day production: batches, workers, inventory. No role/payment editing.'},
    {'code': 'worker', 'name': 'Worker',
     'description': 'Factory worker. Sees their profile, assigned stages, and own earnings.'},
    {'code': 'listing_team', 'name': 'Listing Team',
     'description': 'Manages storefront product + category listings.'},
    {'code': 'accountant', 'name': 'Accountant',
     'description': 'Can view + edit Supplier and Cost Per KG on cloth rolls.'},
]


def seed(apps, schema_editor):
    Role = apps.get_model('accounts', 'Role')
    for d in SYSTEM_ROLES:
        Role.objects.update_or_create(
            code=d['code'],
            defaults={'name': d['name'], 'description': d['description'], 'is_system': True},
        )


def unseed(apps, schema_editor):
    Role = apps.get_model('accounts', 'Role')
    Role.objects.filter(is_system=True, code__in=[r['code'] for r in SYSTEM_ROLES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0015_role_alter_user_extra_roles_alter_user_role_and_more'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
