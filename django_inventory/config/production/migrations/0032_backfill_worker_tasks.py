"""V2-1a backfill: AddaStageRecord.workers M2M → WorkerStageTask rows.

Reversible RunPython (P0.5). Backfills ONLY facts the M2M recorded (owner rule —
never fabricate states that were never recorded):
  • status   = 'completed' if the stage completed, else 'assigned'
               (a roster member of an active stage proves assignment, NOT that
                they started work → 'assigned', never 'in_progress').
  • timestamps = the stage-level started_at/completed_at (no per-worker timeline
                 existed; legacy completed stages may carry null started_at).
  • verified_* = null (no historical verification concept).

Idempotent: get_or_create on (stage_record, worker). The M2M stays authoritative
in V2-1a (readers repoint in V2-1b), so the reverse is a clean delete-all.
On the dev DB this is a no-op today (0 M2M rows) — proven via clone rehearsal.
"""
from django.db import migrations


def backfill(apps, schema_editor):
    AddaStageRecord = apps.get_model('production', 'AddaStageRecord')
    WorkerStageTask = apps.get_model('production', 'WorkerStageTask')
    for sr in AddaStageRecord.objects.prefetch_related('workers').all():
        status = 'completed' if sr.completed_at is not None else 'assigned'
        for worker in sr.workers.all():
            # get_or_create = idempotent; backfill creates only ACTIVE rows so it
            # never collides with the partial-unique (which excludes cancelled).
            WorkerStageTask.objects.get_or_create(
                stage_record=sr,
                worker=worker,
                defaults={
                    'status': status,
                    'started_at': sr.started_at,
                    'completed_at': sr.completed_at,
                },
            )


def unbackfill(apps, schema_editor):
    # M2M is still authoritative in V2-1a, so dropping the shadow tasks loses
    # nothing. Clean delete makes a down→up cycle idempotent.
    WorkerStageTask = apps.get_model('production', 'WorkerStageTask')
    WorkerStageTask.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('production', '0031_workerstagetask'),
    ]

    operations = [
        migrations.RunPython(backfill, unbackfill),
    ]
