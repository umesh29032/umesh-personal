"""Seed the `cutting_pattern` Stage row + attach cutting_master skills.

Why a data migration:
The Stage model is admin-managed but a few well-known codes
(STAGE_LAYERING, STAGE_CUTTING, now STAGE_CUTTING_PATTERN) are referenced
directly by services. Pre-seeding ensures fresh DBs work out of the box.

Backwards compat: this migration is purely additive and idempotent —
re-running won't duplicate rows (get_or_create). On rollback the row
stays (we keep stage rows on reverse; deletion is destructive).
"""
from django.db import migrations


SKILL_CUTTING_MASTER = 'cutting_master'
SKILL_CUTTING_MASTER_HELPER = 'cutting_master_helper'


def seed_cutting_pattern_stage(apps, schema_editor):
    Stage = apps.get_model('production', 'Stage')
    Skill = apps.get_model('accounts', 'Skill')

    stage, _ = Stage.objects.get_or_create(
        code='cutting_pattern',
        defaults={
            'name': 'Cutting Pattern',
            'description': (
                "Cutting master draws the pattern on the layered cloth and "
                "records the design via video + photos. Required between "
                "Layering and Cutting for products that use cut-pattern flows."
            ),
            'is_active': True,
        },
    )

    # Attach access by skill — same skills that gate layering/cutting.
    skill_codes = [SKILL_CUTTING_MASTER, SKILL_CUTTING_MASTER_HELPER]
    for code in skill_codes:
        sk = Skill.objects.filter(name=code).first()
        if sk is not None:
            stage.access_by_skill.add(sk)


def unseed_cutting_pattern_stage(apps, schema_editor):
    # Reverse is a no-op by design — see module docstring.
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('production', '0012_productpattern_alter_stage_id_cuttingpatternrecord_and_more'),
        ('accounts', '0001_initial'),
    ]
    operations = [
        migrations.RunPython(seed_cutting_pattern_stage, unseed_cutting_pattern_stage),
    ]
