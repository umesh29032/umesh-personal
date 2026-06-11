# F3/F8 data fix (owner-approved 2026-06-11): apply the new stage-completion
# lifecycle to KNOWN COMPLETED stages only — active (assigned/in_progress) tasks
# on a stage that already has completed_at are cancelled (never deleted) and the
# legacy M2M roster is synced, mirroring worker_task_service semantics. Touches
# nothing else; fabricates no states (owner backfill rule). Reverse = no-op:
# cancellation is recoverable by re-assignment, and un-cancelling would invent
# an active task on a completed stage.
from django.db import migrations

AUTO_CANCEL_NOTE = "auto-cancelled: stage completed without submitted report"
ACTIVE_UNREPORTED = ("assigned", "in_progress")


def cancel_dangling(apps, schema_editor):
    AddaStageRecord = apps.get_model("production", "AddaStageRecord")
    WorkerStageTask = apps.get_model("production", "WorkerStageTask")
    for sr in AddaStageRecord.objects.filter(completed_at__isnull=False):
        dangling = list(
            WorkerStageTask.objects.filter(
                stage_record=sr, status__in=ACTIVE_UNREPORTED)
        )
        if not dangling:
            continue
        for task in dangling:
            task.status = "cancelled"
            task.notes = (
                f"{task.notes} | {AUTO_CANCEL_NOTE}" if task.notes else AUTO_CANCEL_NOTE
            )[:200]
            task.save(update_fields=["status", "notes", "updated_at"])
        # Roster sync — completed-stage roster shows only workers who reported.
        sr.workers.remove(*[t.worker_id for t in dangling])


class Migration(migrations.Migration):
    dependencies = [
        ("production", "0033_workerstagecontribution"),
    ]
    operations = [
        migrations.RunPython(cancel_dangling, migrations.RunPython.noop),
    ]
