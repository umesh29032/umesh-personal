"""Accountant role seed migration.

YEH FILE KYU HAI?
─────────────────
ROLE_ACCOUNTANT raw_materials app ke financial gates use karte hain
(Supplier + Cost Per KG fields). Day-zero pe ye role DB mein hona chahiye.

`is_system=True` flag → Super Admin bhi UI se delete nahi kar paayega.
"""
from django.db import migrations


ACCOUNTANT_ROLE = {
    'code': 'accountant',
    'name': 'Accountant',
    'description': (
        'Can view and edit financial fields (Supplier, Cost Per KG) on cloth rolls. '
        'Read-only on production data. Super Admin retains universal access by default.'
    ),
}


def seed(apps, schema_editor):
    """Accountant role create karo. update_or_create = re-run safe (idempotent)."""
    Role = apps.get_model('inventory', 'Role')
    # update_or_create = code match karke existing row update karo, na ho to create
    Role.objects.update_or_create(
        code=ACCOUNTANT_ROLE['code'],
        defaults={
            'name': ACCOUNTANT_ROLE['name'],
            'description': ACCOUNTANT_ROLE['description'],
            'is_system': True,    # system role — delete-protected in UI
        },
    )


def revert(apps, schema_editor):
    """`migrate inventory 0012` se ye undo — Accountant role DELETE."""
    Role = apps.get_model('inventory', 'Role')
    Role.objects.filter(code='accountant', is_system=True).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0012_remove_batchclothassignment_batch_and_more'),
    ]

    operations = [
        migrations.RunPython(seed, revert),
    ]
