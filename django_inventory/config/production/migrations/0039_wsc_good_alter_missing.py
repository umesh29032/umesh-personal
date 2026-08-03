"""Foundation S3 — good/alter/missing split + RC-3 constraint sequencing.

ONE migration (RC-3, master plan): add the three columns, batched-backfill
good_quantity = reported_quantity, make good_quantity NOT NULL, then SWAP the
constraint — drop the legacy `wsc_reported_quantity_positive` (which would block a
fully-alter/missing row's good=0) and add `wsc_gam_nonneg_sum_positive`
(good/alter/missing each ≥ 0 AND sum > 0) in the same transaction.

MT-1: DB backup + restore-test before this runs. The backfill is batched
(`.iterator()` + chunked `bulk_update`) for prod-scale safety.
"""
from django.db import migrations, models

BATCH = 2000


def backfill_good(apps, schema_editor):
    # Dual-write seed: good_quantity = reported_quantity for every existing row
    # (alter/missing default 0). Batched for prod-scale dumps.
    WSC = apps.get_model('production', 'WorkerStageContribution')
    batch = []
    for c in WSC.objects.filter(good_quantity__isnull=True).iterator(chunk_size=BATCH):
        c.good_quantity = c.reported_quantity
        batch.append(c)
        if len(batch) >= BATCH:
            WSC.objects.bulk_update(batch, ['good_quantity'])
            batch = []
    if batch:
        WSC.objects.bulk_update(batch, ['good_quantity'])


class Migration(migrations.Migration):

    dependencies = [
        ('production', '0038_ratecorrectionaudit'),
    ]

    operations = [
        # 1. Add the three columns (good interim-nullable so existing rows don't fail).
        migrations.AddField(
            model_name='workerstagecontribution',
            name='good_quantity',
            field=models.DecimalField(max_digits=12, decimal_places=2, null=True),
        ),
        migrations.AddField(
            model_name='workerstagecontribution',
            name='alter_quantity',
            field=models.DecimalField(max_digits=12, decimal_places=2, default=0),
        ),
        migrations.AddField(
            model_name='workerstagecontribution',
            name='missing_quantity',
            field=models.DecimalField(max_digits=12, decimal_places=2, default=0),
        ),
        # 2. Batched backfill good = reported. Reverse = noop (columns dropped on reverse).
        migrations.RunPython(backfill_good, migrations.RunPython.noop),
        # 3. good_quantity is now populated everywhere → enforce NOT NULL (final state).
        migrations.AlterField(
            model_name='workerstagecontribution',
            name='good_quantity',
            field=models.DecimalField(max_digits=12, decimal_places=2),
        ),
        # 4. RC-3 constraint swap (same migration): drop legacy reported>0 …
        migrations.RemoveConstraint(
            model_name='workerstagecontribution',
            name='wsc_reported_quantity_positive',
        ),
        # … add good/alter/missing each ≥ 0 AND sum > 0.
        migrations.AddConstraint(
            model_name='workerstagecontribution',
            constraint=models.CheckConstraint(
                check=(
                    (models.Q(good_quantity__gte=0)
                     & models.Q(alter_quantity__gte=0)
                     & models.Q(missing_quantity__gte=0))
                    & (models.Q(good_quantity__gt=0)
                       | models.Q(alter_quantity__gt=0)
                       | models.Q(missing_quantity__gt=0))
                ),
                name='wsc_gam_nonneg_sum_positive',
            ),
        ),
    ]
