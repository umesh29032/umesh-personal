"""ClothRoll composite index — audit follow-up 2026-05-29.

Adds (adda, status) to support "iss Adda ke kaunse status ke rolls hain"
dashboard query without a full table scan. PostgreSQL CREATE INDEX is brief
catalog lock; safe online migration.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('raw_materials', '0008_phase6_draft_and_denormalized_leftover'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='clothroll',
            index=models.Index(
                fields=['adda', 'status'],
                name='raw_materia_adda_id_d54e55_idx',
            ),
        ),
    ]
