# Foundation S4 / D1 — WorkflowStage.allocation_dimensions (piece-pool grain).

from django.db import migrations, models

from production.constants import ALLOC_DIM_COLOR_SIZE, STAGE_CUTTING


def seed_grain(apps, schema_editor):
    # Owner-locked 2026-06-14: the piece-pool starts at CUTTING. Cutting is the sole
    # piece-pool SOURCE (COLOR_SIZE); every other stage stays NONE (the field default
    # — pre-piece layering/cutting_pattern + identity-only barcode). Frozen snapshot;
    # forward writes seed from the handler's pool_grain (flow_service). POOL-ONLY —
    # touches no settlement/costing column.
    WorkflowStage = apps.get_model('production', 'WorkflowStage')
    WorkflowStage.objects.filter(stage__code=STAGE_CUTTING).update(
        allocation_dimensions=ALLOC_DIM_COLOR_SIZE)


class Migration(migrations.Migration):

    dependencies = [
        ('production', '0039_wsc_good_alter_missing'),
    ]

    operations = [
        migrations.AddField(
            model_name='workflowstage',
            name='allocation_dimensions',
            field=models.CharField(choices=[('none', 'Not a piece-pool stage'), ('quantity', 'Quantity (scalar)'), ('color_size', 'Colour + Size')], default='none', max_length=16),
        ),
        # Seed the locked grain; reverse = noop (the column drop on reverse handles it).
        migrations.RunPython(seed_grain, migrations.RunPython.noop),
    ]
