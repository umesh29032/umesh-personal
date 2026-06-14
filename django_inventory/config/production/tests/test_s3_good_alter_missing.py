"""Foundation S3 — good/alter/missing split + RC-3 constraint sequencing.

Proves: settlement pays GOOD (not the raw claim) even when good ≠ reported (the B-1
leak close); the RC-3 constraint swap admits a good=0 (all-alter/missing) row that the
legacy reported>0 check would have blocked; the dual-write invariant; and that the
expected-earning freeze + re-rate run on good. The byte-identical ₹225 gate lives in
test_golden_path / test_adda_settlement_service (good == reported there).
"""
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from accounts.models import User
from expense.services.settlement_resolver import STAGE_GOOD, settlement_quantity
from inventory.models import Role
from production.models import (
    Adda, AddaStageRecord, Product, Stage, WorkflowStage,
    WorkerStageContribution, WorkerStageTask,
)
from production.services import stage_rate_service
from production.services.worker_task_service import (
    complete_worker_task, report_contributions, set_stage_workers,
)


def _task(code='s3'):
    product = Product.objects.create(code='S3' + code, name='S3 ' + code)
    stage, _ = Stage.objects.get_or_create(code=code, defaults={'name': code})
    ws = WorkflowStage.objects.create(product=product, stage=stage, order=1,
                                      cost_rate=Decimal('5'), credits_workers=True)
    adda = Adda.objects.create(code='S3-' + code, product=product, status=Adda.Status.IN_PROGRESS)
    sr = AddaStageRecord.objects.create(adda=adda, workflow_stage=ws, started_at=timezone.now())
    stage_rate_service.ensure_stage_role_rates(sr)
    w = User.objects.create_user(email=f's3-{code}@test', password='x')
    w.role = Role.objects.get(code='worker'); w.save()
    set_stage_workers(sr, [w.pk])
    return sr, WorkerStageTask.objects.get(stage_record=sr, worker=w), w


class ResolverPaysGoodTests(TestCase):
    def test_settlement_pays_good_not_claim(self):
        # Simulate the post-Missing/Alter world: claim 120, good 105, alter 10, missing 5.
        sr, task, w = _task('pg')
        c = WorkerStageContribution.objects.create(
            task=task, reported_quantity=Decimal('120'),   # raw claim
            good_quantity=Decimal('105'), alter_quantity=Decimal('10'),
            missing_quantity=Decimal('5'))
        # Money follows GOOD, never the claim — the B-1 leak (paid 120 vs produced 105) closed.
        self.assertEqual(settlement_quantity(c), Decimal('105'))
        self.assertEqual(settlement_quantity(c, STAGE_GOOD), Decimal('105'))

    def test_verified_trumps_good(self):
        sr, task, w = _task('vt')
        c = WorkerStageContribution.objects.create(
            task=task, reported_quantity=Decimal('120'),
            good_quantity=Decimal('105'), verified_quantity=Decimal('100'))
        self.assertEqual(settlement_quantity(c), Decimal('100'))   # management trump


class RC3ConstraintTests(TestCase):
    def test_good_zero_all_defect_row_is_legal(self):
        # RC-3: a fully alter/missing contribution (good=0) — illegal under the dropped
        # reported>0 check — is now legal (sum>0 via alter+missing). reported dual=0.
        sr, task, w = _task('rc')
        c = WorkerStageContribution.objects.create(
            task=task, reported_quantity=Decimal('0'),
            good_quantity=Decimal('0'), alter_quantity=Decimal('3'),
            missing_quantity=Decimal('2'))
        self.assertEqual(c.good_quantity, Decimal('0'))
        self.assertEqual(settlement_quantity(c), Decimal('0'))     # pays nothing — correct

    def test_all_zero_row_rejected(self):
        sr, task, w = _task('az')
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                WorkerStageContribution.objects.create(
                    task=task, reported_quantity=Decimal('0'), good_quantity=Decimal('0'),
                    alter_quantity=Decimal('0'), missing_quantity=Decimal('0'))


class DualWriteTests(TestCase):
    def test_report_dual_writes_reported_equals_good(self):
        sr, task, w = _task('dw')
        report_contributions(task, [{'reported_quantity': '40'}], actor=w)
        c = task.contributions.get()
        self.assertEqual(c.good_quantity, Decimal('40'))
        self.assertEqual(c.reported_quantity, c.good_quantity)     # RC-3 invariant
        self.assertEqual(c.alter_quantity, Decimal('0'))
        self.assertEqual(c.missing_quantity, Decimal('0'))


class FreezeOnGoodTests(TestCase):
    def test_complete_freezes_expected_on_good_not_reported(self):
        sr, task, w = _task('fg')
        report_contributions(task, [{'reported_quantity': '10'}], actor=w)
        # Simulate good diverging from the claim before complete (future Missing/Alter).
        c = task.contributions.get()
        c.good_quantity = Decimal('7'); c.save(update_fields=['good_quantity'])
        complete_worker_task(task, actor=w)
        c.refresh_from_db()
        self.assertEqual(c.expected_earning, Decimal('35.00'))     # 7 (good) × 5, not 10
