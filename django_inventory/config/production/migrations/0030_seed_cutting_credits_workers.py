"""Seed credits_workers=True for the cutting stage (PAY-2 / M2.7a).

One-time initial-data seed: cutting is the only stage that allocates worker pay
today, so its WorkflowStage rows are marked payable. This is DATA (initial config),
not runtime logic — the enforcement guard (M2.7c) reads the flag and never hardcodes
a stage name. Admins can change credits_workers per product/stage later, and future
stages flip it True as they gain worker allocation. Reversible (P0.5).
"""
from django.db import migrations


def seed(apps, schema_editor):
    WorkflowStage = apps.get_model('production', 'WorkflowStage')
    WorkflowStage.objects.filter(stage__code='cutting').update(credits_workers=True)


def unseed(apps, schema_editor):
    WorkflowStage = apps.get_model('production', 'WorkflowStage')
    WorkflowStage.objects.filter(stage__code='cutting').update(credits_workers=False)


class Migration(migrations.Migration):

    dependencies = [
        ('production', '0029_workflowstage_credits_workers'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
