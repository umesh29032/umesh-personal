"""Pre-Phase-3 pins (owner-approved 2026-07-06, destruction-audit follow-ups).

A  damaged_quantity — 4th immutable observation: counts as capacity, pays
   nothing, never enters the downstream pool.
B  machine_code snapshot — stamped at report from the worker's open
   MachineAssignment of the stage's machine type; '' when unresolvable.
C  first_report_at — passive worker-time stamp at first draft/report.
D  void_submitted_report — audited manager-only recovery; the ONLY path that
   lets production go UP after submit (verification never increases).
"""
from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase

from accounts.models import Skill, User
from inventory.models import Role
from production.constants import ALLOC_DIM_COLOR_SIZE
from production.models import (
    Adda, ProductSize, Stage, StagePoolSnapshot, WorkerStageTask, WorkflowStage,
)
from raw_materials.models import ClothColor


def _user(email, role_code='worker', skills=()):
    u = User.objects.create_user(email=email, password='x')
    u.role = Role.objects.get(code=role_code)
    u.save()
    for s in skills:
        u.skills.add(Skill.objects.get_or_create(
            name=s, defaults={'label': s.replace('_', ' ').title()})[0])
    return u


class PrePhase3World(TestCase):
    def setUp(self):
        from production.models import MachineType, Product, StageCategory
        skill, _ = Skill.objects.get_or_create(
            name='pp3_operator', defaults={'label': 'PP3 Operator'})
        self.mtype = MachineType.objects.create(code='pp3_machine', name='PP3 Machine')
        self.s_sew = Stage.objects.create(
            code='pp3_sew', name='PP3 Sew', work_type=Stage.WorkType.MACHINE,
            machine_type=self.mtype,
            category=StageCategory.objects.filter(code='stitching').first())
        self.s_next = Stage.objects.create(code='pp3_next', name='PP3 Next')
        for s in (self.s_sew, self.s_next):
            s.access_by_skill.add(skill)

        self.product = Product.objects.create(code='PP3', name='PP3 Tee')
        self.ws1 = WorkflowStage.objects.create(
            product=self.product, stage=self.s_sew, order=1,
            cost_rate=Decimal('5'), credits_workers=True,
            allocation_dimensions=ALLOC_DIM_COLOR_SIZE)
        self.ws2 = WorkflowStage.objects.create(
            product=self.product, stage=self.s_next, order=2,
            cost_rate=Decimal('3'), credits_workers=True,
            allocation_dimensions=ALLOC_DIM_COLOR_SIZE)
        self.adda = Adda.objects.create(
            code='PP3-001', product=self.product,
            current_stage=self.ws1, status=Adda.Status.IN_PROGRESS)
        self.red = ClothColor.objects.create(name='PP3 Red', hex_code='#cc0000')
        self.size_m = ProductSize.objects.create(
            product=self.product, code='m', label='M', display_order=1)
        self.mgr = _user('pp3-mgr@test', 'super_admin')
        self.w1 = _user('pp3-w1@test', skills=['pp3_operator'])

    def _start(self):
        from production.stages.generic_stage.service import start_generic_stage
        return start_generic_stage(adda=self.adda, stage_code='pp3_sew',
                                   worker_ids=[self.w1.pk], user=self.mgr)

    def _task(self, sr):
        return (WorkerStageTask.objects
                .filter(stage_record=sr, worker=self.w1)
                .exclude(status=WorkerStageTask.Status.CANCELLED).latest('pk'))

    def _report(self, sr=None, good='40', alter='0', missing='0', damaged='0'):
        from production.services.worker_task_service import (
            complete_worker_task, report_contributions,
        )
        if sr is None:
            sr = self.adda.stage_records.get(workflow_stage=self.ws1)
        task = self._task(sr)
        report_contributions(task, [{
            'reported_quantity': good, 'alter_quantity': alter,
            'missing_quantity': missing, 'damaged_quantity': damaged,
            'color_id': self.red.pk, 'size_id': self.size_m.pk}], actor=self.w1)
        complete_worker_task(task, actor=self.w1)
        return task

    # ── A: damaged / scrap ─────────────────────────────────────────────────
    def test_damaged_captured_pays_nothing_feeds_no_pool(self):
        from production.stages.generic_stage.service import complete_generic_stage
        sr = self._start()
        task = self._report(good='40', alter='2', missing='1', damaged='3')
        c = task.contributions.get()
        self.assertEqual(c.damaged_quantity, Decimal('3'))
        # pays good-only (₹5 × 40 — damaged never enters money)
        self.assertEqual(c.expected_earning, Decimal('200.00'))
        complete_generic_stage(adda=self.adda, stage_code='pp3_sew', user=self.mgr)
        pool = StagePoolSnapshot.objects.get(stage_record=sr)
        self.assertEqual(pool.good, Decimal('40'))   # not 43 — scrap never pools

    def test_damaged_only_line_is_legal(self):
        sr = self._start()
        from production.services.worker_task_service import report_contributions
        task = self._task(sr)
        report_contributions(task, [{
            'reported_quantity': '0', 'damaged_quantity': '5',
            'color_id': self.red.pk, 'size_id': self.size_m.pk}], actor=self.w1)
        c = task.contributions.get()
        self.assertEqual((c.good_quantity, c.damaged_quantity),
                         (Decimal('0'), Decimal('5')))

    def test_line_observing_nothing_refused(self):
        sr = self._start()
        from production.services.worker_task_service import report_contributions
        with self.assertRaises(ValidationError):
            report_contributions(self._task(sr), [{
                'reported_quantity': '0',
                'color_id': self.red.pk, 'size_id': self.size_m.pk}], actor=self.w1)

    def test_damaged_counts_as_capacity_for_bound_and_void(self):
        from production.services import pool_service
        sr = self._start()
        self._report(good='10', damaged='5')   # produced 15 on this dim
        from production.stages.generic_stage.service import complete_generic_stage
        complete_generic_stage(adda=self.adda, stage_code='pp3_sew', user=self.mgr)
        from production.stages.generic_stage.service import start_generic_stage
        sr2 = start_generic_stage(adda=self.adda, stage_code='pp3_next',
                                  worker_ids=[self.w1.pk], user=self.mgr)
        wsa = pool_service.allocate(sr2, self.w1, qty=Decimal('8'), actor=self.mgr,
                                    color_id=self.red.pk, size_id=self.size_m.pk)
        self._report_on(sr2, good='5', damaged='3')   # produced 8 = exactly allocation
        with self.assertRaisesMessage(ValidationError, 'Cannot void'):
            pool_service.void_allocation(wsa, actor=self.mgr)   # H-2 sum incl. damaged

    def _report_on(self, sr, good='5', damaged='0'):
        from production.services.worker_task_service import (
            complete_worker_task, report_contributions,
        )
        task = (WorkerStageTask.objects
                .filter(stage_record=sr, worker=self.w1)
                .exclude(status=WorkerStageTask.Status.CANCELLED).latest('pk'))
        report_contributions(task, [{
            'reported_quantity': good, 'damaged_quantity': damaged,
            'color_id': self.red.pk, 'size_id': self.size_m.pk}], actor=self.w1)
        complete_worker_task(task, actor=self.w1)
        return task

    # ── B: machine stamp ───────────────────────────────────────────────────
    def test_machine_code_stamped_from_open_assignment(self):
        from machines.services import machine_service
        m = machine_service.create_machine(
            code='PP3-01', name='PP3 #1', machine_type=self.mtype, user=self.mgr)
        sr = self._start()
        machine_service.assign(machine=m, worker=self.w1, adda=self.adda,
                               user=self.mgr)
        task = self._report()
        self.assertEqual(task.contributions.get().machine_code, 'PP3-01')

    def test_machine_code_blank_when_no_assignment(self):
        sr = self._start()
        task = self._report()
        self.assertEqual(task.contributions.get().machine_code, '')

    # ── C: first_report_at ─────────────────────────────────────────────────
    def test_first_report_at_stamped_once(self):
        from production.services.worker_task_service import report_contributions
        sr = self._start()
        task = self._task(sr)
        self.assertIsNone(task.first_report_at)
        report_contributions(task, [{
            'reported_quantity': '10',
            'color_id': self.red.pk, 'size_id': self.size_m.pk}], actor=self.w1)
        task.refresh_from_db()
        first = task.first_report_at
        self.assertIsNotNone(first)
        report_contributions(task, [{
            'reported_quantity': '5',
            'color_id': self.red.pk, 'size_id': self.size_m.pk}], actor=self.w1)
        task.refresh_from_db()
        self.assertEqual(task.first_report_at, first)   # never re-stamped

    # ── D: void submitted report ───────────────────────────────────────────
    def test_void_creates_fresh_task_and_removes_truth_surfaces(self):
        from production.services.worker_task_service import void_submitted_report
        from tracking.models import AddaHistory
        sr = self._start()
        old_task = self._report(good='8')   # fat-finger: meant 80
        new_task = void_submitted_report(old_task, actor=self.mgr,
                                         reason='typed 8 instead of 80')
        old_task.refresh_from_db()
        self.assertEqual(old_task.status, WorkerStageTask.Status.CANCELLED)
        self.assertEqual(new_task.status, WorkerStageTask.Status.ASSIGNED)
        self.assertEqual(new_task.worker, self.w1)
        # voided lines kept (append-only) but off every truth surface
        self.assertEqual(old_task.contributions.count(), 1)
        from production.stages.base import registry
        totals = registry.get('pp3_sew')._totals(sr)
        self.assertEqual(totals['good'], Decimal('0'))
        # audited
        ev = AddaHistory.objects.get(adda=self.adda,
                                     change_type=AddaHistory.ChangeType.REPORT_VOIDED)
        self.assertIn('typed 8 instead of 80', ev.metadata['reason'])
        # worker re-reports the true number through the normal path
        self._report(good='80')
        totals = registry.get('pp3_sew')._totals(sr)
        self.assertEqual(totals['good'], Decimal('80'))

    def test_void_guards(self):
        from production.services.worker_task_service import void_submitted_report
        from production.stages.generic_stage.service import complete_generic_stage
        sr = self._start()
        task = self._report(good='10')
        with self.assertRaises(PermissionDenied):
            void_submitted_report(task, actor=self.w1, reason='self-serve')
        with self.assertRaisesMessage(ValidationError, 'reason'):
            void_submitted_report(task, actor=self.mgr, reason='  ')
        complete_generic_stage(adda=self.adda, stage_code='pp3_sew', user=self.mgr)
        with self.assertRaisesMessage(ValidationError, 'Reopen the stage'):
            void_submitted_report(task, actor=self.mgr, reason='late fix')

    def test_void_refused_on_open_task(self):
        from production.services.worker_task_service import (
            report_contributions, void_submitted_report,
        )
        sr = self._start()
        task = self._task(sr)
        report_contributions(task, [{
            'reported_quantity': '5',
            'color_id': self.red.pk, 'size_id': self.size_m.pk}], actor=self.w1)
        with self.assertRaisesMessage(ValidationError, 'submitted'):
            void_submitted_report(task, actor=self.mgr, reason='not yet submitted')
