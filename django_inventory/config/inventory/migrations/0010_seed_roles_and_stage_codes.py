from django.db import migrations
from django.utils.text import slugify


SYSTEM_ROLES = [
    {
        'code': 'super_admin',
        'name': 'Super Admin',
        'description': 'Full access to every feature. Orders, payments, roles, and user management are exclusive to this role.',
    },
    {
        'code': 'manager',
        'name': 'Manager',
        'description': 'Runs day-to-day production: creates batches, assigns workers/machines, manages inventory. No role or payment editing.',
    },
    {
        'code': 'karigar',
        'name': 'Karigar',
        'description': 'Factory worker. Sees only their profile, their assigned stages, and batches they have worked on.',
    },
]


def seed_roles_and_backfill_codes(apps, schema_editor):
    Role = apps.get_model('inventory', 'Role')
    Stage = apps.get_model('inventory', 'Stage')

    for defn in SYSTEM_ROLES:
        Role.objects.update_or_create(
            code=defn['code'],
            defaults={
                'name': defn['name'],
                'description': defn['description'],
                'is_system': True,
            },
        )

    # Backfill stage.code for pre-existing rows created before the column existed.
    used = set(Stage.objects.exclude(code__isnull=True).values_list('code', flat=True))
    for stage in Stage.objects.filter(code__isnull=True):
        base = slugify(stage.name) or f'stage-{stage.pk}'
        candidate, n = base, 1
        while candidate in used:
            n += 1
            candidate = f'{base}-{n}'
        stage.code = candidate[:64]
        used.add(stage.code)
        stage.save(update_fields=['code'])


def revert(apps, schema_editor):
    Role = apps.get_model('inventory', 'Role')
    Role.objects.filter(is_system=True, code__in=[r['code'] for r in SYSTEM_ROLES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0009_batchstagemachineassignment_batchtype_batchtypestage_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_roles_and_backfill_codes, revert),
    ]
