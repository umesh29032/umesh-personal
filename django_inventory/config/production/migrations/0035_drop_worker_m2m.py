# V2-1d (owner-approved cutover; C2 formally amended 2026-06-11): drop the
# legacy AddaStageRecord.workers M2M — WorkerStageTask + WorkerStageContribution
# are the sole production-truth models from here.
#
# DATA-AWARE REVERSE (the design that softens the point of no return): migrating
# backwards recreates the join table (auto-inverse of RemoveField) and then
# repopulates membership from non-cancelled WorkerStageTask sets — which equals
# the dropped data exactly while the parity invariant holds (verified by the
# up→down→up clone rehearsal with exact-set comparison before this ever touched
# a real DB). Forward = pure drop; only meaningless join-table row ids are lost.
from django.db import migrations


def rebuild_m2m_from_tasks(apps, schema_editor):
    """REVERSE only: repopulate the recreated M2M from task truth."""
    AddaStageRecord = apps.get_model('production', 'AddaStageRecord')
    WorkerStageTask = apps.get_model('production', 'WorkerStageTask')
    for sr in AddaStageRecord.objects.all():
        ids = list(
            WorkerStageTask.objects.filter(stage_record=sr)
            .exclude(status='cancelled')
            .values_list('worker_id', flat=True)
        )
        sr.workers.set(ids)


class Migration(migrations.Migration):
    dependencies = [
        ('production', '0034_cancel_dangling_tasks_on_completed_stages'),
    ]
    operations = [
        # Reverse order note: backwards runs RemoveField's auto-inverse (AddField,
        # empty table) FIRST, then this RunPython's reverse repopulates it.
        migrations.RunPython(migrations.RunPython.noop, rebuild_m2m_from_tasks),
        migrations.RemoveField(model_name='addastagerecord', name='workers'),
    ]
