# R8 WP-1 (owner C-2, 2026-07-05): display-name rename "Cutting Pattern" →
# "Pattern Design". DATA ONLY — the identifier Stage.code='cutting_pattern'
# is FROZEN (registry key / URLs / seeds / tests depend on it). Reversible.
from django.db import migrations


def rename_forward(apps, schema_editor):
    Stage = apps.get_model('production', 'Stage')
    Stage.objects.filter(code='cutting_pattern').update(name='Pattern Design')


def rename_backward(apps, schema_editor):
    Stage = apps.get_model('production', 'Stage')
    Stage.objects.filter(code='cutting_pattern').update(name='Cutting Pattern')


class Migration(migrations.Migration):
    dependencies = [('production', '0042_workerstageallocation')]
    operations = [migrations.RunPython(rename_forward, rename_backward)]
