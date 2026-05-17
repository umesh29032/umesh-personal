from django.db import migrations


LISTING_TEAM_ROLE = {
    'code': 'listing_team',
    'name': 'Listing Team',
    'description': (
        'Can create, edit, and delete storefront product listings and categories. '
        'No access to production, inventory, or financial data. '
        'Typically stacked on top of another role via User.extra_roles.'
    ),
}


def seed(apps, schema_editor):
    Role = apps.get_model('inventory', 'Role')
    Role.objects.update_or_create(
        code=LISTING_TEAM_ROLE['code'],
        defaults={
            'name': LISTING_TEAM_ROLE['name'],
            'description': LISTING_TEAM_ROLE['description'],
            'is_system': True,
        },
    )


def revert(apps, schema_editor):
    Role = apps.get_model('inventory', 'Role')
    Role.objects.filter(code='listing_team', is_system=True).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0010_seed_roles_and_stage_codes'),
    ]

    operations = [
        migrations.RunPython(seed, revert),
    ]
