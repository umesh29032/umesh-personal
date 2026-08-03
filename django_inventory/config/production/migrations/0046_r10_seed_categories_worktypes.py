# R10 frozen architecture (2026-07-05) — owner-specified seeds + defaults:
# 4 StageCategories, the Cutting Machine type, and per-stage work_type/
# machine_type/category defaults for the four existing stages. Reversible.
from django.db import migrations


CATEGORIES = [
    ('pre_production', 'Pre Production', 10),
    ('stitching', 'Stitching', 20),
    ('finishing', 'Finishing', 30),
    ('dispatch', 'Dispatch', 40),
]

# stage code → (work_type, machine_type code or None, category code)
STAGE_DEFAULTS = {
    'layering': ('manual', None, 'pre_production'),
    'cutting_pattern': ('manual', None, 'pre_production'),
    'cutting': ('machine', 'cutting_machine', 'pre_production'),
    'barcode_generation': ('manual', None, 'pre_production'),
}


def seed(apps, schema_editor):
    StageCategory = apps.get_model('production', 'StageCategory')
    MachineType = apps.get_model('production', 'MachineType')
    Stage = apps.get_model('production', 'Stage')

    cats = {}
    for code, name, order in CATEGORIES:
        cats[code], _ = StageCategory.objects.get_or_create(
            code=code, defaults={'name': name, 'display_order': order})

    cutting_mt, _ = MachineType.objects.get_or_create(
        code='cutting_machine', defaults={'name': 'Cutting Machine'})

    for code, (work_type, mt_code, cat_code) in STAGE_DEFAULTS.items():
        Stage.objects.filter(code=code).update(
            work_type=work_type,
            machine_type=cutting_mt if mt_code == 'cutting_machine' else None,
            category=cats[cat_code],
        )


def unseed(apps, schema_editor):
    # Reverse = detach defaults, drop seeded masters (only if unused elsewhere).
    Stage = apps.get_model('production', 'Stage')
    Stage.objects.filter(code__in=STAGE_DEFAULTS).update(
        work_type='manual', machine_type=None, category=None)
    apps.get_model('production', 'MachineType').objects.filter(
        code='cutting_machine', stages__isnull=True).delete()
    apps.get_model('production', 'StageCategory').objects.filter(
        code__in=[c[0] for c in CATEGORIES], stages__isnull=True).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('production', '0045_r10_stage_operations_model'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
