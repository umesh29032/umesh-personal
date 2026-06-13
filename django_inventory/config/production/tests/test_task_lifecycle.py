"""F3/F8 (owner-locked 2026-06-11): stage completion resolves the task lifecycle —
unreported active tasks auto-cancel (never delete) via the chokepoint. Plus F1: partial layering-draft
rows are reported back, never silently dropped.
"""
from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from accounts.models import User
from inventory.models import Role
from production.models import (
    Adda, AddaStageRecord, Product, Stage, WorkflowStage,
    WorkerStageTask,
)
from production.services import complete_layering, create_adda, start_layering
from production.services.worker_task_service import (
    AUTO_CANCEL_NOTE, report_contributions, resolve_stage_tasks_on_complete,
    save_draft_contributions, set_stage_workers, complete_worker_task,
)
from production.stages.layering.service import (
    attach_roll_to_layering, record_remaining_cloth, reopen_layering,
    save_layering_draft,
)
from raw_materials.models import ClothColor, ClothType, StorageLocation
from raw_materials.services import bulk_create_rolls


def _user(email, *, role_code='super_admin', is_super=True, skills=()):
    from accounts.models import Skill
    role = Role.objects.get(code=role_code)
    u = User.objects.create_user(email=email, password='x',
                                 is_superuser=is_super, is_staff=is_super)
    u.role = role
    u.save()
    for s in skills:
        u.skills.add(Skill.objects.get(name=s))
    return u


class LayeringCompletionLifecycleTests(TestCase):
    """Through the REAL funnel: complete_layering → advance_to_next_stage →
    resolve_stage_tasks_on_complete."""

    def setUp(self):
        self.admin = _user('lcl-admin@test',
                           skills=['cutting_master', 'cutting_master_helper'])
        self.reporter = _user('lcl-rep@test', role_code='worker', is_super=False,
                              skills=['cutting_master'])
        self.idle = User.objects.create_user(email='lcl-idle@test', password='x')
        cotton = ClothType.objects.get(name='Cotton')
        red = ClothColor.objects.get(name='Red')
        loc = StorageLocation.objects.get(code='ROHINI')
        self.rolls = bulk_create_rolls(
            user=self.admin, cloth_type=cotton, storage_location=loc,
            purchased_date=date.today(), breakup=[{'color': red, 'qty': 1}])
        self.adda = create_adda(self.admin, product=Product.objects.get(code='T-SHIRT'))
        self.sr = start_layering(
            adda=self.adda,
            worker_ids=[self.reporter.pk, self.idle.pk],
            user=self.admin)
        entry = attach_roll_to_layering(
            stage_record=self.sr, roll=self.rolls[0],
            width_verified_inch=42, weight_verified_kg=Decimal('25'),
            user=self.admin)
        record_remaining_cloth(entry=entry, remaining_weight_kg=Decimal('0'),
                               remaining_length_meters=Decimal('0'), user=self.admin)
        self.entry = entry

    def _complete(self):
        return complete_layering(
            adda=self.adda, duration_minutes=15,
            layer_length_meters=Decimal('1.5'),
            per_entry_layers={self.entry.pk: 3}, notes='', user=self.admin)

    def _task(self, user):
        return (WorkerStageTask.objects
                .filter(stage_record=self.sr, worker=user)
                .order_by('-pk').first())

    def test_unreported_tasks_autocancel_and_roster_syncs(self):
        # reporter submits work; idle never reports.
        rep_task = self._task(self.reporter)
        report_contributions(rep_task, [{'reported_quantity': '3'}], actor=self.reporter)
        complete_worker_task(rep_task, actor=self.reporter)

        self._complete()

        rep_task.refresh_from_db()
        idle_task = self._task(self.idle)
        self.assertEqual(rep_task.status, WorkerStageTask.Status.COMPLETED)   # untouched
        self.assertEqual(idle_task.status, WorkerStageTask.Status.CANCELLED)  # auto-cancel
        self.assertIn(AUTO_CANCEL_NOTE, idle_task.notes)                      # audit note
        # Active roster (tasks) = only the worker who actually reported.
        self.assertEqual({u.pk for u in self.sr.active_workers}, {self.reporter.pk})

    def test_draft_lines_retained_on_autocancelled_task(self):
        rep_task = self._task(self.reporter)
        report_contributions(rep_task, [{'reported_quantity': '3'}], actor=self.reporter)
        complete_worker_task(rep_task, actor=self.reporter)
        idle_task = self._task(self.idle)
        save_draft_contributions(idle_task, [{'reported_quantity': '7'}],
                                 actor=self.idle)   # draft, never submitted

        self._complete()

        idle_task.refresh_from_db()
        self.assertEqual(idle_task.status, WorkerStageTask.Status.CANCELLED)
        # Draft evidence retained — and still invisible to business reads
        # (everything money/readiness reads filters COMPLETED tasks).
        lines = list(idle_task.contributions.all())
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0].reported_quantity, Decimal('7'))
        self.assertIsNone(lines[0].expected_rate)

    def test_task_truth_consistent_after_autocancel(self):
        rep_task = self._task(self.reporter)
        report_contributions(rep_task, [{'reported_quantity': '3'}], actor=self.reporter)
        complete_worker_task(rep_task, actor=self.reporter)
        self._complete()
        # Post-M2M world: the invariant is task-internal — every task terminal-or-
        # completed on a completed stage, and active_workers mirrors that.
        statuses = set(WorkerStageTask.objects.filter(
            stage_record=self.sr).values_list('status', flat=True))
        self.assertTrue(statuses <= {WorkerStageTask.Status.COMPLETED,
                                     WorkerStageTask.Status.VERIFIED,
                                     WorkerStageTask.Status.CANCELLED})
        self.assertEqual({u.pk for u in self.sr.active_workers}, {self.reporter.pk})

    def test_no_reports_at_all_cancels_everyone_roster_empty(self):
        self._complete()
        for u in (self.reporter, self.idle):
            self.assertEqual(self._task(u).status, WorkerStageTask.Status.CANCELLED)
        self.assertEqual(len(self.sr.active_workers), 0)

    def test_reopen_then_reassign_creates_fresh_active_task(self):
        self._complete()
        reopen_layering(adda=self.adda, user=self.admin)
        # Manager re-assignment is the recovery path after auto-cancel.
        set_stage_workers(self.sr, [self.idle.pk])
        tasks = WorkerStageTask.objects.filter(
            stage_record=self.sr, worker=self.idle).order_by('pk')
        self.assertEqual(tasks.count(), 2)            # cancelled + fresh
        self.assertEqual(tasks.first().status, WorkerStageTask.Status.CANCELLED)
        self.assertNotEqual(tasks.last().status, WorkerStageTask.Status.CANCELLED)


class ResolveFnUnitTests(TestCase):
    """Direct unit coverage incl. the F8 shape: a system-work stage (e.g.
    barcode_generation) whose mandatory worker never reports."""

    def setUp(self):
        self.product = Product.objects.create(code='TLC', name='TLC P')
        self.stage, _ = Stage.objects.get_or_create(
            code='barcode_generation', defaults={'name': 'Barcode Generation'})
        self.ws = WorkflowStage.objects.create(
            product=self.product, stage=self.stage, order=1,
            cost_rate=Decimal('0'))
        self.adda = Adda.objects.create(code='TLC-001', product=self.product)
        self.sr = AddaStageRecord.objects.create(
            adda=self.adda, workflow_stage=self.ws, started_at=timezone.now())
        self.worker = User.objects.create_user(email='tlc-w@test', password='x')
        set_stage_workers(self.sr, [self.worker.pk])

    def test_f8_idle_worker_on_system_stage_autocancels(self):
        self.sr.completed_at = timezone.now()
        self.sr.save(update_fields=['completed_at'])
        resolve_stage_tasks_on_complete(self.sr)
        t = WorkerStageTask.objects.get(stage_record=self.sr, worker=self.worker)
        self.assertEqual(t.status, WorkerStageTask.Status.CANCELLED)
        self.assertIn(AUTO_CANCEL_NOTE, t.notes)
        self.assertEqual(len(self.sr.active_workers), 0)

    def test_idempotent(self):
        resolve_stage_tasks_on_complete(self.sr)
        resolve_stage_tasks_on_complete(self.sr)
        self.assertEqual(
            WorkerStageTask.objects.filter(stage_record=self.sr).count(), 1)


class LayeringDraftSkippedFeedbackTests(TestCase):
    """F1: partial rows are reported, complete rows persist, blank rows silent."""

    def setUp(self):
        self.admin = _user('f1-admin@test',
                           skills=['cutting_master', 'cutting_master_helper'])
        cotton = ClothType.objects.get(name='Cotton')
        red = ClothColor.objects.get(name='Red')
        loc = StorageLocation.objects.get(code='ROHINI')
        self.rolls = bulk_create_rolls(
            user=self.admin, cloth_type=cotton, storage_location=loc,
            purchased_date=date.today(), breakup=[{'color': red, 'qty': 2}])
        self.adda = create_adda(self.admin, product=Product.objects.get(code='T-SHIRT'))
        self.sr = start_layering(adda=self.adda, worker_ids=[self.admin.pk],
                                 user=self.admin)
        self.e1 = attach_roll_to_layering(
            stage_record=self.sr, roll=self.rolls[0],
            width_verified_inch=42, weight_verified_kg=Decimal('25'),
            user=self.admin)
        self.e2 = attach_roll_to_layering(
            stage_record=self.sr, roll=self.rolls[1],
            width_verified_inch=42, weight_verified_kg=Decimal('25'),
            user=self.admin)

    def _draft(self, per_entry):
        return save_layering_draft(
            adda=self.adda, layer_length_meters=None, duration_minutes=None,
            notes=None, per_entry_data=per_entry, user=self.admin)

    def test_partial_row_reported_complete_row_saved(self):
        _, skipped = self._draft({
            self.e1.pk: {'layers': 5, 'leftover_weight': None},      # partial
            self.e2.pk: {'layers': 4, 'leftover_weight': Decimal('1'),
                         'leftover_length': Decimal('0')},           # complete
        })
        self.assertEqual(skipped, [self.e1.roll.roll_id])
        self.e1.refresh_from_db(); self.e2.refresh_from_db()
        self.assertIsNone(self.e1.layers_on_roll)
        self.assertEqual(self.e2.layers_on_roll, 4)

    def test_blank_row_is_silent(self):
        _, skipped = self._draft({
            self.e1.pk: {'layers': None, 'leftover_weight': None,
                         'leftover_length': None},
        })
        self.assertEqual(skipped, [])


class CompleteTaskRaceTests(TestCase):
    """P0-5: complete_worker_task locks + re-reads the task row, so a worker
    complete cannot race a manager stage-complete (which cancels open tasks)."""

    def setUp(self):
        self.worker = _user('ctr-w@test', role_code='worker', is_super=False,
                            skills=['cutting_master'])
        product = Product.objects.create(code='CTR', name='CTR P')
        stage, _ = Stage.objects.get_or_create(
            code='ctr_cut', defaults={'name': 'CTR Cut'})
        ws = WorkflowStage.objects.create(
            product=product, stage=stage, order=1,
            cost_rate=Decimal('3'), credits_workers=True)
        self.adda = Adda.objects.create(code='CTR-001', product=product)
        self.sr = AddaStageRecord.objects.create(
            adda=self.adda, workflow_stage=ws, started_at=timezone.now())
        set_stage_workers(self.sr, [self.worker.pk])
        self.task = WorkerStageTask.objects.get(
            stage_record=self.sr, worker=self.worker)
        report_contributions(self.task, [{'reported_quantity': '10'}],
                             actor=self.worker)   # → in_progress + 1 contribution

    def test_stale_complete_refuses_after_concurrent_cancel(self):
        # Worker holds a task loaded BEFORE the manager closed the stage. Simulate
        # the manager's cancel landing first (bypass save → DB-only, in-memory stale).
        stale = WorkerStageTask.objects.get(pk=self.task.pk)   # in_progress in memory
        WorkerStageTask.objects.filter(pk=self.task.pk).update(
            status=WorkerStageTask.Status.CANCELLED)
        with self.assertRaisesMessage(ValidationError, 'cancelled'):
            complete_worker_task(stale, actor=self.worker)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, WorkerStageTask.Status.CANCELLED)  # NOT resurrected
        # contributions were never frozen (no stranded expected_*)
        self.assertFalse(
            self.task.contributions.exclude(expected_rate=None).exists())

    def test_completed_task_survives_stage_resolve_no_strand(self):
        complete_worker_task(self.task, actor=self.worker)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, WorkerStageTask.Status.COMPLETED)
        # Manager closes the stage: resolve keeps completed/verified tasks.
        resolve_stage_tasks_on_complete(self.sr)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, WorkerStageTask.Status.COMPLETED)  # not stranded
        self.assertTrue(   # frozen contribution remains visible to settlement
            self.task.contributions.exclude(expected_rate=None).exists())
