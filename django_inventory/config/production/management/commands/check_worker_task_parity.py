"""V2-1d precondition (R0 C2 / SOAK_TRACKER §3): M2M ↔ WorkerStageTask parity.

While WORKER_TASK_DUAL_WRITE is on, the legacy `AddaStageRecord.workers` M2M and
the WorkerStageTask table must agree: for every stage record,
    set(M2M workers)  ==  set(non-cancelled task workers).
Divergence means a write bypassed the `worker_task_service` chokepoint (or the
kill-switch was flipped mid-flight) — and the V2-1d drop migration must NOT run
until it is explained and repaired.

Run against the DEV/real DB at soak end and immediately before V2-1d:
    env/bin/python config/manage.py check_worker_task_parity
Exit code 0 = parity holds; 1 = divergence (listed per stage record).
"""
from django.core.management.base import BaseCommand
from django.db.models import Prefetch

from production.models import AddaStageRecord, WorkerStageTask


class Command(BaseCommand):
    help = "Assert AddaStageRecord.workers M2M == non-cancelled WorkerStageTask sets (V2-1d precondition)."

    def handle(self, *args, **options):
        records = (
            AddaStageRecord.objects
            .select_related('adda', 'workflow_stage__stage')
            .prefetch_related(
                'workers',
                Prefetch(
                    'worker_tasks',
                    queryset=WorkerStageTask.objects.exclude(
                        status=WorkerStageTask.Status.CANCELLED),
                    to_attr='parity_tasks',
                ),
            )
        )
        checked = 0
        diverged = []
        for sr in records:
            checked += 1
            m2m = {u.pk for u in sr.workers.all()}
            tasks = {t.worker_id for t in sr.parity_tasks}
            if m2m != tasks:
                diverged.append((sr, m2m, tasks))

        if not diverged:
            self.stdout.write(self.style.SUCCESS(
                f"PARITY OK — {checked} stage records, M2M == task sets everywhere."))
            return

        for sr, m2m, tasks in diverged:
            self.stdout.write(self.style.ERROR(
                f"DIVERGED sr={sr.pk} adda={sr.adda.code} "
                f"stage={sr.workflow_stage.stage.code} "
                f"m2m_only={sorted(m2m - tasks)} task_only={sorted(tasks - m2m)}"
            ))
        self.stdout.write(self.style.ERROR(
            f"PARITY FAILED — {len(diverged)}/{checked} stage records diverged. "
            "Do NOT run V2-1d until repaired (re-run 0032-style backfill / "
            "reconcile via worker_task_service)."))
        raise SystemExit(1)
