"""V2-1a: WorkerStageTask model constraints + the 0032 M2M→Task backfill logic.

The dev DB is empty of production rows, so the clone rehearsal only proves
migration mechanics. THIS is where the backfill logic is exercised with synthetic
fixtures (completed / active / legacy-null-started) per V2_1_REVIEW §10.7.
"""
import importlib
from decimal import Decimal

from django.apps import apps as django_apps
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings
from django.utils import timezone

from accounts.models import User
from production.models import (
    Adda, AddaStageRecord, Product, Stage, WorkflowStage,
    WorkerStageTask, WorkerStageContribution,
)
from production.services.worker_task_service import (
    add_stage_worker, complete_worker_task, report_contributions,
    save_draft_contributions, set_stage_workers,
)


def _active_task_workers(sr):
    return set(
        WorkerStageTask.objects.filter(stage_record=sr)
        .exclude(status=WorkerStageTask.Status.CANCELLED)
        .values_list('worker_id', flat=True))


def _m2m_workers(sr):
    return set(sr.workers.values_list('pk', flat=True))

# 0032's module name starts with a digit → import via importlib (not `import`).
_backfill_mod = importlib.import_module(
    'production.migrations.0032_backfill_worker_tasks')


class WorkerStageTaskModelTest(TestCase):
    def setUp(self):
        self.product = Product.objects.create(code='WST', name='WST Product')
        self.stage = Stage.objects.create(code='wst_stage', name='WST Stage')
        self.ws = WorkflowStage.objects.create(
            product=self.product, stage=self.stage, order=1, cost_rate=Decimal('0'))
        self.adda = Adda.objects.create(code='WST-001', product=self.product)
        self.sr = AddaStageRecord.objects.create(
            adda=self.adda, workflow_stage=self.ws, started_at=timezone.now())
        self.worker = User.objects.create_user(email='wst-worker@test', password='x')

    def test_one_active_task_per_stage_worker(self):
        """Partial unique: a second ACTIVE task for the same (sr, worker) is rejected."""
        WorkerStageTask.objects.create(stage_record=self.sr, worker=self.worker)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                WorkerStageTask.objects.create(stage_record=self.sr, worker=self.worker)

    def test_cancelled_does_not_block_reassign(self):
        """Cancel → re-assign is allowed (the partial unique excludes cancelled)."""
        t = WorkerStageTask.objects.create(stage_record=self.sr, worker=self.worker)
        t.status = WorkerStageTask.Status.CANCELLED
        t.save(update_fields=['status'])
        # A fresh active task for the same pair must NOT collide.
        again = WorkerStageTask.objects.create(stage_record=self.sr, worker=self.worker)
        self.assertEqual(again.status, WorkerStageTask.Status.ASSIGNED)
        self.assertEqual(
            WorkerStageTask.objects.filter(stage_record=self.sr, worker=self.worker).count(), 2)

    def test_invalid_status_rejected(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                WorkerStageTask.objects.create(
                    stage_record=self.sr, worker=self.worker, status='bogus')


class BackfillLogicTest(TestCase):
    def setUp(self):
        self.product = Product.objects.create(code='BF', name='BF Product')
        # 3 distinct stages → 3 distinct WorkflowStages → 3 stage records under one Adda.
        self.s1 = Stage.objects.create(code='bf_done', name='BF Done')
        self.s2 = Stage.objects.create(code='bf_active', name='BF Active')
        self.s3 = Stage.objects.create(code='bf_legacy', name='BF Legacy')
        ws = lambda s, o: WorkflowStage.objects.create(
            product=self.product, stage=s, order=o, cost_rate=Decimal('0'))
        self.adda = Adda.objects.create(code='BF-001', product=self.product)
        now = timezone.now()
        # completed stage → expect task 'completed'
        self.sr_done = AddaStageRecord.objects.create(
            adda=self.adda, workflow_stage=ws(self.s1, 1), started_at=now, completed_at=now)
        # active stage → expect 'assigned' (roster ≠ started work)
        self.sr_active = AddaStageRecord.objects.create(
            adda=self.adda, workflow_stage=ws(self.s2, 2), started_at=now)
        # legacy completed stage with NULL started_at → 'completed', started_at None
        self.sr_legacy = AddaStageRecord.objects.create(
            adda=self.adda, workflow_stage=ws(self.s3, 3), started_at=None, completed_at=now)
        self.w1 = User.objects.create_user(email='bf-w1@test', password='x')
        self.w2 = User.objects.create_user(email='bf-w2@test', password='x')
        for sr in (self.sr_done, self.sr_active, self.sr_legacy):
            sr.workers.add(self.w1, self.w2)

    def _run_backfill(self):
        _backfill_mod.backfill(django_apps, None)

    def test_backfill_creates_tasks_with_correct_status_and_timestamps(self):
        self._run_backfill()
        # 3 stage records × 2 workers = 6 tasks
        self.assertEqual(WorkerStageTask.objects.count(), 6)
        done = WorkerStageTask.objects.get(stage_record=self.sr_done, worker=self.w1)
        active = WorkerStageTask.objects.get(stage_record=self.sr_active, worker=self.w1)
        legacy = WorkerStageTask.objects.get(stage_record=self.sr_legacy, worker=self.w1)
        self.assertEqual(done.status, 'completed')
        self.assertIsNotNone(done.completed_at)
        self.assertEqual(active.status, 'assigned')      # roster of active stage ≠ in_progress
        self.assertIsNone(active.completed_at)
        self.assertEqual(legacy.status, 'completed')
        self.assertIsNone(legacy.started_at)             # don't fabricate a start time
        self.assertIsNotNone(legacy.completed_at)

    def test_backfill_is_idempotent(self):
        self._run_backfill()
        self._run_backfill()                              # second run must not duplicate
        self.assertEqual(WorkerStageTask.objects.count(), 6)

    def test_unbackfill_clears_tasks(self):
        self._run_backfill()
        _backfill_mod.unbackfill(django_apps, None)
        self.assertEqual(WorkerStageTask.objects.count(), 0)

    def test_empty_roster_creates_no_tasks(self):
        """A stage record with no M2M members yields no tasks."""
        empty_sr = AddaStageRecord.objects.create(
            adda=self.adda,
            workflow_stage=WorkflowStage.objects.create(
                product=self.product,
                stage=Stage.objects.create(code='bf_empty', name='BF Empty'),
                order=4, cost_rate=Decimal('0')),
            started_at=timezone.now())
        self._run_backfill()
        self.assertFalse(WorkerStageTask.objects.filter(stage_record=empty_sr).exists())


class DualWriteChokepointTest(TestCase):
    """V2-1a dual-write: set_stage_workers / add_stage_worker keep WorkerStageTask
    in lockstep with the M2M (the authoritative source in V2-1a)."""

    def setUp(self):
        self.product = Product.objects.create(code='DW', name='DW Product')
        self.stage = Stage.objects.create(code='dw_stage', name='DW Stage')
        self.ws = WorkflowStage.objects.create(
            product=self.product, stage=self.stage, order=1, cost_rate=Decimal('0'))
        self.adda = Adda.objects.create(code='DW-001', product=self.product)
        self.sr = AddaStageRecord.objects.create(
            adda=self.adda, workflow_stage=self.ws, started_at=timezone.now())
        self.w1 = User.objects.create_user(email='dw1@test', password='x')
        self.w2 = User.objects.create_user(email='dw2@test', password='x')
        self.w3 = User.objects.create_user(email='dw3@test', password='x')

    def _assert_parity(self):
        self.assertEqual(_m2m_workers(self.sr), _active_task_workers(self.sr))

    def test_set_creates_matching_active_tasks(self):
        set_stage_workers(self.sr, [self.w1.pk, self.w2.pk])
        self.assertEqual(_active_task_workers(self.sr), {self.w1.pk, self.w2.pk})
        self._assert_parity()

    def test_set_cancels_removed_never_deletes(self):
        set_stage_workers(self.sr, [self.w1.pk, self.w2.pk])
        set_stage_workers(self.sr, [self.w1.pk])          # drop w2
        self._assert_parity()
        self.assertEqual(_active_task_workers(self.sr), {self.w1.pk})
        # w2's task is CANCELLED, not deleted — production history is immutable.
        w2_task = WorkerStageTask.objects.get(stage_record=self.sr, worker=self.w2)
        self.assertEqual(w2_task.status, WorkerStageTask.Status.CANCELLED)

    def test_set_idempotent(self):
        set_stage_workers(self.sr, [self.w1.pk, self.w2.pk])
        set_stage_workers(self.sr, [self.w1.pk, self.w2.pk])
        self.assertEqual(
            WorkerStageTask.objects.filter(stage_record=self.sr).count(), 2)

    def test_set_reactivates_after_cancel(self):
        set_stage_workers(self.sr, [self.w1.pk, self.w2.pk])
        set_stage_workers(self.sr, [self.w1.pk])          # cancel w2
        set_stage_workers(self.sr, [self.w1.pk, self.w2.pk])  # re-add w2
        self._assert_parity()
        # w2 now has 1 cancelled + 1 active row (re-assign allowed by partial unique).
        self.assertEqual(
            WorkerStageTask.objects.filter(stage_record=self.sr, worker=self.w2).count(), 2)

    def test_add_is_additive_and_ensures_task(self):
        set_stage_workers(self.sr, [self.w1.pk])
        add_stage_worker(self.sr, self.w2)                # additive — does NOT drop w1
        self.assertEqual(_active_task_workers(self.sr), {self.w1.pk, self.w2.pk})
        self._assert_parity()

    def test_add_reactivates_after_cancel(self):
        set_stage_workers(self.sr, [self.w1.pk, self.w2.pk])
        set_stage_workers(self.sr, [self.w1.pk])          # cancel w2
        add_stage_worker(self.sr, self.w2)                # re-tag w2
        self.assertIn(self.w2.pk, _active_task_workers(self.sr))
        self._assert_parity()

    def test_completed_stage_seeds_completed_status(self):
        self.sr.completed_at = timezone.now()
        self.sr.save(update_fields=['completed_at'])
        set_stage_workers(self.sr, [self.w1.pk])
        t = WorkerStageTask.objects.get(stage_record=self.sr, worker=self.w1)
        self.assertEqual(t.status, WorkerStageTask.Status.COMPLETED)

    @override_settings(WORKER_TASK_DUAL_WRITE=False)
    def test_flag_off_writes_no_tasks(self):
        set_stage_workers(self.sr, [self.w1.pk, self.w2.pk])
        add_stage_worker(self.sr, self.w3)
        self.assertEqual(WorkerStageTask.objects.filter(stage_record=self.sr).count(), 0)
        # M2M still updated (authoritative) even with dual-write off.
        self.assertEqual(_m2m_workers(self.sr), {self.w1.pk, self.w2.pk, self.w3.pk})


class ReadHelpersTest(TestCase):
    """V2-1b: AddaStageRecord read helpers trust WorkerStageTask, not the M2M."""

    def setUp(self):
        self.product = Product.objects.create(code='RH', name='RH Product')
        self.stage = Stage.objects.create(code='rh_stage', name='RH Stage')
        self.ws = WorkflowStage.objects.create(
            product=self.product, stage=self.stage, order=1, cost_rate=Decimal('0'))
        self.adda = Adda.objects.create(code='RH-001', product=self.product)
        self.sr = AddaStageRecord.objects.create(
            adda=self.adda, workflow_stage=self.ws, started_at=timezone.now())
        self.w1 = User.objects.create_user(email='rh1@test', password='x')
        self.w2 = User.objects.create_user(email='rh2@test', password='x')

    def test_is_worker_assigned_reflects_active_task(self):
        self.assertFalse(self.sr.is_worker_assigned(self.w1))      # no task
        set_stage_workers(self.sr, [self.w1.pk])
        self.assertTrue(self.sr.is_worker_assigned(self.w1))
        set_stage_workers(self.sr, [])                              # cancel w1
        self.assertFalse(self.sr.is_worker_assigned(self.w1))       # cancelled ≠ assigned

    def test_active_workers_excludes_cancelled(self):
        set_stage_workers(self.sr, [self.w1.pk, self.w2.pk])
        set_stage_workers(self.sr, [self.w1.pk])                    # cancel w2
        actives = self.sr.active_workers
        self.assertIn(self.w1, actives)
        self.assertNotIn(self.w2, actives)                          # only w1 is live

    def test_active_worker_tasks_excludes_cancelled(self):
        set_stage_workers(self.sr, [self.w1.pk, self.w2.pk])
        set_stage_workers(self.sr, [self.w1.pk])
        self.assertEqual(
            set(self.sr.active_worker_tasks().values_list('worker_id', flat=True)),
            {self.w1.pk})


class ContributionModelTest(TestCase):
    """V2-1c-i: WorkerStageContribution model + constraints (no UI/freeze yet)."""

    def setUp(self):
        self.product = Product.objects.create(code='CN', name='CN Product')
        self.stage = Stage.objects.create(code='cn_stage', name='CN Stage')
        self.ws = WorkflowStage.objects.create(
            product=self.product, stage=self.stage, order=1, cost_rate=Decimal('0'))
        self.adda = Adda.objects.create(code='CN-001', product=self.product)
        self.sr = AddaStageRecord.objects.create(
            adda=self.adda, workflow_stage=self.ws, started_at=timezone.now())
        self.worker = User.objects.create_user(email='cn-worker@test', password='x')
        self.task = WorkerStageTask.objects.create(stage_record=self.sr, worker=self.worker)

    def test_reported_quantity_must_be_positive(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                WorkerStageContribution.objects.create(
                    task=self.task, reported_quantity=Decimal('0'))

    def test_multiple_lines_per_task(self):
        WorkerStageContribution.objects.create(task=self.task, reported_quantity=Decimal('120'))
        WorkerStageContribution.objects.create(task=self.task, reported_quantity=Decimal('80'))
        self.assertEqual(self.task.contributions.count(), 2)

    def test_expected_fields_null_until_frozen(self):
        c = WorkerStageContribution.objects.create(task=self.task, reported_quantity=Decimal('5'))
        # Option B: no money at report time — expected_* freeze only at complete (V2-1c-ii).
        self.assertIsNone(c.expected_rate)
        self.assertIsNone(c.expected_earning)
        self.assertIsNone(c.verified_quantity)

    def test_verified_quantity_negative_rejected(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                WorkerStageContribution.objects.create(
                    task=self.task, reported_quantity=Decimal('5'),
                    verified_quantity=Decimal('-1'))


class LifecycleServiceTest(TestCase):
    """V2-1c-ii: report_contributions + complete_worker_task (expected_* freeze).
    Option B — completion freezes a visibility snapshot, NEVER a ledger entry."""

    def setUp(self):
        self.product = Product.objects.create(code='LC', name='LC Product')
        self.stage = Stage.objects.create(code='lc_stage', name='LC Stage')
        self.ws = WorkflowStage.objects.create(
            product=self.product, stage=self.stage, order=1, cost_rate=Decimal('10'))
        self.adda = Adda.objects.create(code='LC-001', product=self.product)
        self.sr = AddaStageRecord.objects.create(
            adda=self.adda, workflow_stage=self.ws, started_at=timezone.now())
        self.worker = User.objects.create_user(email='lc-worker@test', password='x')
        self.other = User.objects.create_user(email='lc-other@test', password='x')
        self.task = WorkerStageTask.objects.create(stage_record=self.sr, worker=self.worker)

    def test_report_creates_lines_and_sets_in_progress(self):
        report_contributions(self.task, [{'reported_quantity': '120'},
                                         {'reported_quantity': '80'}], actor=self.worker)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, WorkerStageTask.Status.IN_PROGRESS)
        self.assertEqual(self.task.contributions.count(), 2)

    def test_report_non_actor_denied(self):
        with self.assertRaises(PermissionDenied):
            report_contributions(self.task, [{'reported_quantity': '5'}], actor=self.other)

    def test_report_zero_qty_rejected(self):
        with self.assertRaises(ValidationError):
            report_contributions(self.task, [{'reported_quantity': '0'}], actor=self.worker)

    def test_complete_freezes_expected_no_ledger(self):
        report_contributions(self.task, [{'reported_quantity': '5'}], actor=self.worker)
        complete_worker_task(self.task, actor=self.worker)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, WorkerStageTask.Status.COMPLETED)
        self.assertIsNotNone(self.task.completed_at)
        c = self.task.contributions.get()
        self.assertEqual(c.expected_rate, Decimal('10.0000'))
        self.assertEqual(c.expected_earning, Decimal('50.00'))   # 5 × 10

    def test_frozen_expected_immutable_to_rate_change(self):
        report_contributions(self.task, [{'reported_quantity': '5'}], actor=self.worker)
        complete_worker_task(self.task, actor=self.worker)
        # Owner edits the rate-card LATER — the frozen snapshot must NOT move.
        self.ws.cost_rate = Decimal('99')
        self.ws.save(update_fields=['cost_rate'])
        c = self.task.contributions.get()
        c.refresh_from_db()
        self.assertEqual(c.expected_rate, Decimal('10.0000'))
        self.assertEqual(c.expected_earning, Decimal('50.00'))

    def test_report_rejected_after_complete(self):
        report_contributions(self.task, [{'reported_quantity': '5'}], actor=self.worker)
        complete_worker_task(self.task, actor=self.worker)
        with self.assertRaises(ValidationError):
            report_contributions(self.task, [{'reported_quantity': '3'}], actor=self.worker)

    def test_complete_twice_rejected(self):
        complete_worker_task(self.task, actor=self.worker)
        with self.assertRaises(ValidationError):
            complete_worker_task(self.task, actor=self.worker)


class DraftTest(TestCase):
    """V2-1c-iii: lightweight drafts (no engine). Draft = task not completed →
    editable + excluded from business truth; truth begins at Submit & Complete."""

    def setUp(self):
        self.product = Product.objects.create(code='DR', name='DR Product')
        self.stage = Stage.objects.create(code='dr_stage', name='DR Stage')
        self.ws = WorkflowStage.objects.create(
            product=self.product, stage=self.stage, order=1, cost_rate=Decimal('10'))
        self.adda = Adda.objects.create(code='DR-001', product=self.product)
        self.sr = AddaStageRecord.objects.create(
            adda=self.adda, workflow_stage=self.ws, started_at=timezone.now())
        self.worker = User.objects.create_user(email='dr-worker@test', password='x')
        self.task = WorkerStageTask.objects.create(stage_record=self.sr, worker=self.worker)

    def test_draft_saves_lines_and_is_draft(self):
        save_draft_contributions(self.task, [{'reported_quantity': '5'}], actor=self.worker)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, WorkerStageTask.Status.IN_PROGRESS)
        self.assertTrue(self.task.is_draft)                       # not business truth yet
        self.assertEqual(self.task.contributions.count(), 1)

    def test_draft_replaces_not_appends(self):
        save_draft_contributions(self.task, [{'reported_quantity': '5'}], actor=self.worker)
        save_draft_contributions(self.task, [{'reported_quantity': '7'},
                                             {'reported_quantity': '9'}], actor=self.worker)
        # Replaced, not appended — only the latest draft survives.
        qs = self.task.contributions.all()
        self.assertEqual(qs.count(), 2)
        self.assertEqual(set(qs.values_list('reported_quantity', flat=True)),
                         {Decimal('7'), Decimal('9')})

    def test_submit_after_draft_freezes_and_locks(self):
        save_draft_contributions(self.task, [{'reported_quantity': '5'}], actor=self.worker)
        complete_worker_task(self.task, actor=self.worker)       # Submit & Complete
        self.task.refresh_from_db()
        self.assertFalse(self.task.is_draft)                      # now business truth
        c = self.task.contributions.get()
        self.assertEqual(c.expected_earning, Decimal('50.00'))    # frozen 5 × 10
        with self.assertRaises(ValidationError):                  # locked
            save_draft_contributions(self.task, [{'reported_quantity': '1'}], actor=self.worker)


class IsolationGateTest(TestCase):
    """V2-1c-iv: a skilled worker may open a stage view ONLY if actively assigned
    (skill alone is not enough). Management bypasses. (The HIGH leak fix.)"""

    def setUp(self):
        from django.test import RequestFactory
        from inventory.models import Role
        from accounts.models import Skill
        from production.views.stage_views import StagePanelView
        self.factory = RequestFactory()
        self.View = StagePanelView
        self.product = Product.objects.create(code='IG', name='IG Product')
        self.stage = Stage.objects.get_or_create(code='cutting', defaults={'name': 'Cutting'})[0]
        self.ws = WorkflowStage.objects.create(
            product=self.product, stage=self.stage, order=1, cost_rate=Decimal('0'))
        self.adda = Adda.objects.create(code='IG-001', product=self.product)
        self.sr = AddaStageRecord.objects.create(
            adda=self.adda, workflow_stage=self.ws, started_at=timezone.now())
        cm = Skill.objects.get_or_create(name='cutting_master', defaults={'label': 'Cutting Master'})[0]
        # Non-management production worker WITH the cutting skill.
        self.worker = User.objects.create_user(email='ig-worker@test', password='x')
        self.worker.role = Role.objects.get(code='worker')
        self.worker.save()
        self.worker.skills.add(cm)
        # Super-admin (management) — should bypass the assignment gate.
        self.admin = User.objects.create_user(
            email='ig-admin@test', password='x', is_superuser=True, is_staff=True)
        self.admin.role = Role.objects.get(code='super_admin')
        self.admin.save()
        self.admin.skills.add(cm)

    def _get_panel(self, user):
        req = self.factory.get(f'/addas/{self.adda.code}/stage/cutting/')
        req.user = user
        return self.View.as_view()(req, code=self.adda.code, stage_type='cutting')

    def test_skilled_but_unassigned_worker_denied(self):
        with self.assertRaises(PermissionDenied):
            self._get_panel(self.worker)

    def test_assigned_worker_allowed(self):
        set_stage_workers(self.sr, [self.worker.pk])     # active task created
        resp = self._get_panel(self.worker)              # must NOT raise PermissionDenied
        self.assertEqual(resp.status_code, 200)

    def test_cancelled_task_worker_denied(self):
        set_stage_workers(self.sr, [self.worker.pk])
        set_stage_workers(self.sr, [])                   # cancel the worker's task
        with self.assertRaises(PermissionDenied):
            self._get_panel(self.worker)

    def test_management_bypasses_assignment(self):
        resp = self._get_panel(self.admin)               # not assigned, but management
        self.assertEqual(resp.status_code, 200)
