"""Seed SidebarItemRule rows into accounts (RBAC relocated here 2026-06).

Replicates the END state of the old inventory sidebar seeds (0015 base + 0017
stage-access→stage-list rename + 0018 product-list tightened to manager-only +
access-control added + karigar→worker rename). No allowed_skills were ever
seeded. Super Admin is intentionally NOT listed (service-layer bypass).
Idempotent (update_or_create + set).
"""
from django.db import migrations


# (section, label, url_name, [role_codes])  — super_admin implicit, never seeded.
SEED = [
    ('Main', 'Dashboard', 'inventory:inventory_dashboard', ['manager']),
    ('Main', 'Dashboard', 'inventory:user_dashboard', ['worker', 'listing_team', 'accountant']),
    ('Storefront', 'Featured Products', 'storefront:product_list', ['listing_team']),
    ('Storefront', 'Categories', 'storefront:category_list', ['listing_team']),
    ('Raw Materials', 'Raw Material Dashboard', 'raw_materials:dashboard', ['manager', 'worker']),
    ('Raw Materials', 'Cloth Dashboard', 'raw_materials:cloth-dashboard', ['manager', 'worker']),
    ('Raw Materials', 'Cloth Rolls', 'raw_materials:roll-list', ['manager', 'worker']),
    ('Raw Materials', 'Cloth Types', 'raw_materials:cloth-type-list', ['manager', 'worker']),
    ('Raw Materials', 'Cloth Colors', 'raw_materials:cloth-color-list', ['manager', 'worker']),
    ('Raw Materials', 'Storage Locations', 'raw_materials:storage-list', ['manager', 'worker']),
    ('Production', 'Adda Dashboard', 'production:dashboard', ['manager', 'worker']),
    ('Production', 'Addas', 'production:adda-list', ['manager', 'worker']),
    ('Production', 'Products', 'production:product-list', ['manager']),  # worker dropped — mgmt-only
    ('Tracking', 'Barcode Dashboard', 'tracking:dashboard', ['manager', 'worker']),
    ('Administration', 'Access Control', 'inventory:access-control', []),
    ('Administration', 'Team Members', 'accounts:user_list', []),
    ('Administration', 'User Skills', 'accounts:skill_list', []),
    ('Administration', 'Roles & Permissions', 'inventory:role_list', []),
    ('Administration', 'Stages', 'production:stage-list', []),
    ('Administration', 'Sidebar Access', 'inventory:sidebar-access', []),
]


def seed(apps, schema_editor):
    SidebarItemRule = apps.get_model('accounts', 'SidebarItemRule')
    Role = apps.get_model('accounts', 'Role')
    role_by_code = {r.code: r for r in Role.objects.all()}
    for section, label, url_name, role_codes in SEED:
        rule, _ = SidebarItemRule.objects.update_or_create(
            url_name=url_name, defaults={'section': section, 'label': label},
        )
        rule.allowed_roles.set([role_by_code[c] for c in role_codes if c in role_by_code])


def unseed(apps, schema_editor):
    SidebarItemRule = apps.get_model('accounts', 'SidebarItemRule')
    SidebarItemRule.objects.filter(url_name__in=[s[2] for s in SEED]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0016_seed_default_roles'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
