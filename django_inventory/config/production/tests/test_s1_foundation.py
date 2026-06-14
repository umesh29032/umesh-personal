"""Foundation S1 — AddaStageRoleRate (resolved-rate snapshot, role_snapshot,
first-completion lock, edit-until-lock, live-fallback) + resolved_payable_rate.

Contracts (addendum): M-5 frozen-at-stage-start + role snapshot; contract 1
(immutable-after-first-completion, lock-serialized edit/complete); contract 2
(snapshot mandatory for S1 records, warn-fallback only for pre-S2); grouped→₹0.
"""
from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase
from django.utils import timezone

from accounts.models import User
from inventory.models import Role
from production.models import (
    Adda, AddaStageRecord, AddaStageRoleRate, Product, Stage,
    WorkflowStage, WorkflowStageRoleRate, WorkerStageTask,
)
from production.services import cost_service, stage_rate_service
from production.services.worker_task_service import (
    complete_worker_task, report_contributions, set_stage_workers,
)


def _worker(email, code='worker'):
    u = User.objects.create_user(email=email, password='x')
    u.role = Role.objects.get(code=code)
    u.save()
    return u


def _stage_record(*, cost_rate='5', grouped=False, code='s1s'):
    product = Product.objects.create(code='S1' + code, name='S1 ' + code)
    stage, _ = Stage.objects.get_or_create(code=code, defaults={'name': code})
    payer = None
    if grouped:
        payer = WorkflowStage.objects.create(
            product=product, stage=Stage.objects.get_or_create(code=code + 'p', defaults={'name': 'payer'})[0],
            order=2, cost_rate=Decimal('9'), credits_workers=True)
    ws = WorkflowStage.objects.create(
        product=product, stage=stage, order=1,
        cost_rate=Decimal(cost_rate), credits_workers=True,
        cost_billed_at=payer)
    adda = Adda.objects.create(code='S1-' + code, product=product, status=Adda.Status.IN_PROGRESS)
    sr = AddaStageRecord.objects.create(adda=adda, workflow_stage=ws, started_at=timezone.now())
    return sr, ws


class ResolvedPayableRateTests(TestCase):
    def test_base_rate(self):
        sr, ws = _stage_record(cost_rate='5')
        self.assertEqual(cost_service.resolved_payable_rate(ws, Role.objects.get(code='worker')), Decimal('5'))

    def test_role_override(self):
        sr, ws = _stage_record(cost_rate='5', code='ovr')
        r = Role.objects.get(code='worker')
        WorkflowStageRoleRate.objects.create(workflow_stage=ws, role=r, cost_rate=Decimal('7'))
        self.assertEqual(cost_service.resolved_payable_rate(ws, r), Decimal('7'))

    def test_grouped_member_is_zero(self):
        sr, ws = _stage_record(cost_rate='5', grouped=True, code='grp')
        # grouped MEMBER → 0 even though cost_rate=5 (paid via payer; never twice)
        self.assertEqual(cost_service.resolved_payable_rate(ws, Role.objects.get(code='worker')), Decimal('0'))


class SnapshotTests(TestCase):
    def test_ensure_creates_resolved_snapshots_per_production_role(self):
        sr, ws = _stage_record(cost_rate='5', code='snap')
        stage_rate_service.ensure_stage_role_rates(sr)
        rows = AddaStageRoleRate.objects.filter(stage_record=sr)
        self.assertEqual(rows.count(), 3)   # super_admin, manager, worker
        self.assertTrue(all(r.rate == Decimal('5') for r in rows))
        self.assertTrue(all(r.locked_at is None for r in rows))

    def test_ensure_is_idempotent(self):
        sr, ws = _stage_record(code='idem')
        self.assertEqual(stage_rate_service.ensure_stage_role_rates(sr), 3)
        self.assertEqual(stage_rate_service.ensure_stage_role_rates(sr), 0)   # no-op second time

    def test_grouped_snapshot_is_zero(self):
        sr, ws = _stage_record(cost_rate='5', grouped=True, code='gsnap')
        stage_rate_service.ensure_stage_role_rates(sr)
        self.assertTrue(all(r.rate == Decimal('0') for r in AddaStageRoleRate.objects.filter(stage_record=sr)))


class CompleteFreezeTests(TestCase):
    def setUp(self):
        self.sr, self.ws = _stage_record(cost_rate='5', code='cmp')
        stage_rate_service.ensure_stage_role_rates(self.sr)
        self.w = _worker('s1-cmp@test')
        set_stage_workers(self.sr, [self.w.pk])
        self.task = WorkerStageTask.objects.get(stage_record=self.sr, worker=self.w)
        report_contributions(self.task, [{'reported_quantity': '10'}], actor=self.w)

    def test_complete_freezes_rate_role_and_locks(self):
        complete_worker_task(self.task, actor=self.w)
        c = self.task.contributions.get()
        self.assertEqual(c.expected_rate, Decimal('5'))           # frozen from snapshot
        self.assertEqual(c.expected_earning, Decimal('50.00'))    # 10 × 5
        self.assertEqual(c.role_snapshot, self.w.role)            # role frozen
        row = AddaStageRoleRate.objects.get(stage_record=self.sr, role=self.w.role)
        self.assertIsNotNone(row.locked_at)                       # first completion → immutable

    def test_role_change_after_lock_does_not_reprice(self):
        # M-10 integrity: freeze, then change the live workflow rate — frozen stays.
        complete_worker_task(self.task, actor=self.w)
        self.ws.cost_rate = Decimal('999')
        self.ws.save(update_fields=['cost_rate'])
        c = self.task.contributions.get()
        c.refresh_from_db()
        self.assertEqual(c.expected_rate, Decimal('5'))           # NOT 999
        # and the frozen snapshot is unchanged
        self.assertEqual(AddaStageRoleRate.objects.get(stage_record=self.sr, role=self.w.role).rate, Decimal('5'))

    def test_live_fallback_warns_when_snapshot_absent(self):
        # Simulate a pre-S2 record: delete snapshots → complete must still pay the
        # resolved rate (live fallback) and not crash.
        AddaStageRoleRate.objects.filter(stage_record=self.sr).delete()
        with self.assertLogs('production', level='WARNING') as cm:
            complete_worker_task(self.task, actor=self.w)
        self.assertEqual(self.task.contributions.get().expected_rate, Decimal('5'))
        self.assertTrue(any('snapshot_missing_at_complete' in m or 'live_fallback' in m for m in cm.output))


class EditUntilLockTests(TestCase):
    def setUp(self):
        self.sr, self.ws = _stage_record(cost_rate='5', code='edit')
        stage_rate_service.ensure_stage_role_rates(self.sr)
        self.mgr = _worker('s1-mgr@test', code='manager')
        self.worker_role = Role.objects.get(code='worker')

    def test_edit_before_lock(self):
        stage_rate_service.edit_until_lock(self.sr, self.worker_role, Decimal('8'), actor=self.mgr)
        self.assertEqual(AddaStageRoleRate.objects.get(stage_record=self.sr, role=self.worker_role).rate, Decimal('8'))

    def test_edit_refuses_non_management(self):
        with self.assertRaises(PermissionDenied):
            stage_rate_service.edit_until_lock(self.sr, self.worker_role, Decimal('8'), actor=_worker('s1-w2@test'))

    def test_edit_refuses_negative(self):
        with self.assertRaises(ValidationError):
            stage_rate_service.edit_until_lock(self.sr, self.worker_role, Decimal('-1'), actor=self.mgr)

    def test_edit_refuses_after_lock(self):
        row = AddaStageRoleRate.objects.get(stage_record=self.sr, role=self.worker_role)
        stage_rate_service.mark_locked(row)
        with self.assertRaisesMessage(ValidationError, 'locked'):
            stage_rate_service.edit_until_lock(self.sr, self.worker_role, Decimal('8'), actor=self.mgr)

    def test_edited_rate_is_what_complete_freezes(self):
        stage_rate_service.edit_until_lock(self.sr, self.worker_role, Decimal('8'), actor=self.mgr)
        w = _worker('s1-ew@test')
        set_stage_workers(self.sr, [w.pk])
        t = WorkerStageTask.objects.get(stage_record=self.sr, worker=w)
        report_contributions(t, [{'reported_quantity': '10'}], actor=w)
        complete_worker_task(t, actor=w)
        self.assertEqual(t.contributions.get().expected_rate, Decimal('8'))   # edited, not 5
