# Streams redesign 2026-07-11 — DATA backfill (reversible-safe):
# every existing Adda gets ONE derived lane (sequence 1) and its
# pre-production trio stage records join it; existing bundles gain the
# adda anchor. fabric_group is the literal default 'body' — legacy
# single-lane addas carry a cosmetic group label; behavior is
# byte-identical (single-group products always derive one lane).
# NOTE: no patterns_ai import here (ADR-H wall holds in migrations too).
from django.db import migrations

PRE_PRODUCTION_STAGE_CODES = ('layering', 'cutting_pattern', 'cutting')


def forwards(apps, schema_editor):
    Adda = apps.get_model('production', 'Adda')
    CuttingStream = apps.get_model('production', 'CuttingStream')
    AddaStageRecord = apps.get_model('production', 'AddaStageRecord')
    CuttingBundle = apps.get_model('production', 'CuttingBundle')

    for adda in Adda.objects.all().iterator():
        stream, _ = CuttingStream.objects.get_or_create(
            adda=adda, fabric_group='body', sequence=1,
            defaults={'is_blocking': True})
        (AddaStageRecord.objects
         .filter(adda=adda, stream__isnull=True,
                 workflow_stage__stage__code__in=PRE_PRODUCTION_STAGE_CODES)
         .update(stream=stream))

    for bundle in (CuttingBundle.objects
                   .filter(adda__isnull=True,
                           cutting_record__isnull=False)
                   .select_related('cutting_record__stage_record')
                   .iterator()):
        bundle.adda_id = bundle.cutting_record.stage_record.adda_id
        bundle.save(update_fields=['adda'])


def backwards(apps, schema_editor):
    # additive backfill — reversing the schema migration drops the
    # columns; nothing to unwind here.
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('production', '0050_cutting_streams'),
    ]
    operations = [
        migrations.RunPython(forwards, backwards),
    ]
