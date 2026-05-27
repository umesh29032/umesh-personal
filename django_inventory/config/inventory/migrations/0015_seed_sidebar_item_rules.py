"""Seed SidebarItemRule rows mirroring the hardcoded SIDEBAR registry in
permission_service.py. Preserves existing visibility so the refactor of
build_menu_for() is a no-op behaviorally on day one.

Super Admin is intentionally NOT seeded into allowed_roles — it's a
service-layer built-in and must not be editable via the page.
"""
from django.db import migrations


# (section, label, url_name, [role_codes])
# Excludes ROLE_SUPER_ADMIN — added implicitly at lookup time.
SEED = [
    ('Main',           'Dashboard',              'inventory:inventory_dashboard', ['manager']),
    ('Main',           'Dashboard',              'inventory:user_dashboard',      ['karigar', 'listing_team', 'accountant']),
    ('Storefront',     'Featured Products',      'storefront:product_list',       ['listing_team']),
    ('Storefront',     'Categories',             'storefront:category_list',      ['listing_team']),
    ('Raw Materials',  'Raw Material Dashboard', 'raw_materials:dashboard',       ['manager', 'karigar']),
    ('Raw Materials',  'Cloth Dashboard',        'raw_materials:cloth-dashboard', ['manager', 'karigar']),
    ('Raw Materials',  'Cloth Rolls',            'raw_materials:roll-list',       ['manager', 'karigar']),
    ('Raw Materials',  'Cloth Types',            'raw_materials:cloth-type-list', ['manager', 'karigar']),
    ('Raw Materials',  'Cloth Colors',           'raw_materials:cloth-color-list', ['manager', 'karigar']),
    ('Raw Materials',  'Storage Locations',      'raw_materials:storage-list',    ['manager', 'karigar']),
    ('Production',     'Adda Dashboard',         'production:dashboard',          ['manager', 'karigar']),
    ('Production',     'Addas',                  'production:adda-list',          ['manager', 'karigar']),
    ('Production',     'Products',               'production:product-list',       ['manager', 'karigar']),
    ('Tracking',       'Barcode Dashboard',      'tracking:dashboard',            ['manager', 'karigar']),
    ('Administration', 'Team Members',           'accounts:user_list',            []),  # super_admin only
    ('Administration', 'User Skills',            'accounts:skill_list',           []),
    ('Administration', 'Roles & Permissions',    'inventory:role_list',           []),
    ('Administration', 'Stage Access',           'production:stage-access',       []),
    ('Administration', 'Sidebar Access',         'inventory:sidebar-access',      []),
]


def seed(apps, schema_editor):
    SidebarItemRule = apps.get_model('inventory', 'SidebarItemRule')
    Role = apps.get_model('inventory', 'Role')

    role_by_code = {r.code: r for r in Role.objects.all()}

    for section, label, url_name, role_codes in SEED:
        rule, _ = SidebarItemRule.objects.update_or_create(
            url_name=url_name,
            defaults={'section': section, 'label': label},
        )
        roles = [role_by_code[c] for c in role_codes if c in role_by_code]
        rule.allowed_roles.set(roles)


def unseed(apps, schema_editor):
    SidebarItemRule = apps.get_model('inventory', 'SidebarItemRule')
    SidebarItemRule.objects.filter(url_name__in=[s[2] for s in SEED]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('inventory', '0014_sidebar_item_rule'),
        ('inventory', '0013_seed_accountant_role'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
