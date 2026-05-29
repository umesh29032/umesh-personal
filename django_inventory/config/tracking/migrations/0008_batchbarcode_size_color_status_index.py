"""BatchBarcode (size, color, status) index — audit follow-up 2026-05-29.

Adds composite index for per-size/color status breakdown queries:
    "kitne medium-red dispatched", "remaining pending by size/color".

Existing (adda, status) + (status) indexes preserved.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracking', '0007_barcodebatch_bundle'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='batchbarcode',
            index=models.Index(
                fields=['size', 'color', 'status'],
                name='tracking_ba_size_id_0541b6_idx',
            ),
        ),
    ]
