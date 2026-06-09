"""Owner decision 2026-06-03: Layering cost = 0, settled via the Cutting stage.

Set every Layering `WorkflowStage.cost_billed_at` to the same product's Cutting
stage (grouped → priced-zero), so layering never freezes a standalone cost.
Fixes the inconsistency where 3-PATTI layering was priced per_layer ₹10 while
T-SHIRT was already grouped-at-cutting. Idempotent + reversible.
"""
from django.db import migrations


def forwards(apps, schema_editor):
    WorkflowStage = apps.get_model('production', 'WorkflowStage')
    layering = WorkflowStage.objects.filter(stage__code='layering').select_related('product')
    for ws in layering:
        cutting = WorkflowStage.objects.filter(
            product=ws.product, stage__code='cutting',
        ).first()
        if cutting is None:
            continue  # product has no cutting stage — leave layering as-is
        ws.cost_billed_at = cutting
        # Clear any standalone rate/method so the grouped (priced-zero) rule is clean.
        ws.cost_method = ''
        ws.cost_rate = None
        ws.save(update_fields=['cost_billed_at', 'cost_method', 'cost_rate'])


def backwards(apps, schema_editor):
    # Un-group layering (back to unpriced). We don't restore the old per-layer
    # rate — that was the inconsistency we removed; unpriced is the safe reverse.
    WorkflowStage = apps.get_model('production', 'WorkflowStage')
    WorkflowStage.objects.filter(stage__code='layering').update(cost_billed_at=None)


class Migration(migrations.Migration):
    dependencies = [
        ('production', '0025_workflowstagerolerate'),
    ]
    operations = [
        migrations.RunPython(forwards, backwards),
    ]
