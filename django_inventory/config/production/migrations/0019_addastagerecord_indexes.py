"""Composite indexes for dashboard queries — audit follow-up 2026-05-29.

Adds:
  AddaStageRecord — (adda, -started_at) for activity timelines
                   (workflow_stage, completed_at) for per-stage KPI
  RemainingClothOfClothRoll — (is_consumed, -remaining_length_meters) for
                              leftover dashboard sort

Zero schema change to row data — purely index additions. Safe online migration
on PostgreSQL (CREATE INDEX is blocking only for the brief catalog update;
use CONCURRENTLY in psql if table > 1M rows).
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('production', '0018_cuttingbundleitem_source_breakup_and_more'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='addastagerecord',
            index=models.Index(
                fields=['adda', '-started_at'],
                name='production__adda_id_7592e8_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='addastagerecord',
            index=models.Index(
                fields=['workflow_stage', 'completed_at'],
                name='production__workflo_4764a5_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='remainingclothofclothroll',
            index=models.Index(
                fields=['is_consumed', '-remaining_length_meters'],
                name='production__is_cons_50d954_idx',
            ),
        ),
    ]
