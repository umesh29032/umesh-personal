"""Seed `barcode_generation` Stage row + attach cutting_master skills.

YEH MIGRATION KYU HAI?
─────────────────────
PR-A 2026-05-29: barcode generation ab apna alag stage hai (cutting se
extract kiya). Stage rows admin-managed hote hain, par well-known codes
(STAGE_LAYERING, STAGE_CUTTING, STAGE_CUTTING_PATTERN, ab
STAGE_BARCODE_GENERATION) services mein hardcoded — pre-seeding ensures
fresh DBs ko admin manual setup ki zaroorat nahi.

IDEMPOTENT:
  get_or_create — re-run pe duplicate row nahi banta. Reverse intentionally
  no-op (stage rows manually managed; deletion destructive).

ACCESS:
  Cutting Master + Helper skills attached. Sirf wahi log barcode generation
  trigger karenge.

NOT AUTO-ATTACHED TO PRODUCTS:
  Default product workflows mein yeh stage NHI add hoti. Admin per-product
  flow editor se opt-in karega (`/production/products/<pk>/flow/`).
"""
from django.db import migrations


SKILL_CUTTING_MASTER = 'cutting_master'
SKILL_CUTTING_MASTER_HELPER = 'cutting_master_helper'


def seed_barcode_generation_stage(apps, schema_editor):
    Stage = apps.get_model('production', 'Stage')
    Skill = apps.get_model('accounts', 'Skill')

    stage, _ = Stage.objects.get_or_create(
        code='barcode_generation',
        defaults={
            'name': 'Barcode Generation',
            'description': (
                "Generates BarcodeBatch rows from the verified cutting "
                "breakdown. Consumes AddaProductSizeColorPieceBreakdown; "
                "produces tracking.BarcodeBatch ranges. Optional per "
                "product workflow."
            ),
            'is_active': True,
        },
    )

    for code in [SKILL_CUTTING_MASTER, SKILL_CUTTING_MASTER_HELPER]:
        sk = Skill.objects.filter(name=code).first()
        if sk is not None:
            stage.access_by_skill.add(sk)


def unseed_barcode_generation_stage(apps, schema_editor):
    """No-op reverse — Stage rows are admin-managed; deletion destructive."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('production', '0021_labelprintqueue_export_batch_and_more'),
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            seed_barcode_generation_stage,
            unseed_barcode_generation_stage,
        ),
    ]
