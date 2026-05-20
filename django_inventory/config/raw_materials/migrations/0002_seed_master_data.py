"""Initial master data ka seed migration.

YEH FILE KYU HAI?
─────────────────
Day-zero pe master data populate karta hai — taa-ke user fresh DB pe bhi
turant cloth rolls add kar sake. (Empty dropdowns mein add karna painful hota.)

Data migration discipline:
  apps.get_model() use kiya hai — direct `from raw_materials.models import ...`
  NAHI. Wajah: agar future mein model ka shape badle (e.g. naya required field),
  apps.get_model historical snapshot deta hai — direct import current state se chalega
  (jo migration apply time pe abhi exist NAHI karta).
"""
from django.db import migrations


LOCATIONS = [
    ('Packing Factory', 'PACKING'),
    ('Rohini Factory',  'ROHINI'),
]
CLOTH_TYPES = ['Cotton', 'Polyester', 'Silk', 'Linen']
CLOTH_COLORS = ['Red', 'Blue', 'Green', 'White', 'Black', 'Yellow']


def forwards(apps, schema_editor):
    """Seed rows insert karta hai. get_or_create = idempotent (re-run safe)."""
    # apps.get_model = historical model fetch karo (migration-safe)
    ClothType = apps.get_model('raw_materials', 'ClothType')
    ClothColor = apps.get_model('raw_materials', 'ClothColor')
    StorageLocation = apps.get_model('raw_materials', 'StorageLocation')

    for name, code in LOCATIONS:
        # get_or_create = pehli call create, dusri pe existing return (no duplicate)
        StorageLocation.objects.get_or_create(code=code, defaults={'name': name})
    for n in CLOTH_TYPES:
        ClothType.objects.get_or_create(name=n)
    for n in CLOTH_COLORS:
        ClothColor.objects.get_or_create(name=n)


def reverse(apps, schema_editor):
    """`migrate raw_materials 0001` chala to ye undo hoga — seeded rows delete."""
    apps.get_model('raw_materials', 'StorageLocation').objects.filter(
        code__in=[c for _, c in LOCATIONS]
    ).delete()
    apps.get_model('raw_materials', 'ClothType').objects.filter(name__in=CLOTH_TYPES).delete()
    apps.get_model('raw_materials', 'ClothColor').objects.filter(name__in=CLOTH_COLORS).delete()


class Migration(migrations.Migration):
    # dependencies = ye migration kis pe depend karti hai
    dependencies = [('raw_materials', '0001_initial')]
    # RunPython = data migration (schema migration NAHI). Custom Python chalata hai.
    operations = [migrations.RunPython(forwards, reverse)]
