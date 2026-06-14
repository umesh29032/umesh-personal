"""Foundation S1 — settlement_quantity resolver + M-6 reconciliation (WARN)."""
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from accounts.models import User
from expense.models import StageWorkAssignment
from expense.services import reconciliation_service
from expense.services.settlement_resolver import STAGE_GOOD, settlement_quantity
from inventory.models import Role
from production.models import Adda, AddaStageRecord, Product, Stage, WorkflowStage


class _C:
    """Minimal contribution stand-in for the pure resolver (no DB needed)."""
    def __init__(self, reported, verified=None):
        self.reported_quantity = Decimal(reported)
        self.verified_quantity = None if verified is None else Decimal(verified)


class ResolverTests(TestCase):
    def test_default_uses_reported_when_unverified(self):
        self.assertEqual(settlement_quantity(_C('60')), Decimal('60'))

    def test_default_uses_verified_when_set(self):
        self.assertEqual(settlement_quantity(_C('60', '45')), Decimal('45'))

    def test_explicit_stage_good_same_as_default(self):
        self.assertEqual(settlement_quantity(_C('60', '45'), STAGE_GOOD), Decimal('45'))

    def test_unknown_policy_raises(self):
        with self.assertRaises(ValueError):
            settlement_quantity(_C('60'), 'packed')


class ReconciliationTests(TestCase):
    def test_over_allocated_is_flagged(self):
        # Stage output recorded 5, but a worker is credited (SWA) for 8 → the B-1
        # leak. reconcile_stage_pay must flag it 'over_allocated' (a HARD flag).
        product = Product.objects.create(code='RC', name='RC')
        stage, _ = Stage.objects.get_or_create(code='rc_s', defaults={'name': 'RC'})
        ws = WorkflowStage.objects.create(product=product, stage=stage, order=1,
                                          cost_rate=Decimal('3'), credits_workers=True)
        adda = Adda.objects.create(code='RC-1', product=product, status=Adda.Status.IN_PROGRESS)
        sr = AddaStageRecord.objects.create(
            adda=adda, workflow_stage=ws,
            started_at=timezone.now(), completed_at=timezone.now(),
            processing_cost=Decimal('15.00'), cost_quantity_snapshot=Decimal('5'))
        w = User.objects.create_user(email='rc-w@test', password='x')
        w.role = Role.objects.get(code='worker'); w.save()
        StageWorkAssignment.objects.create(
            stage_record=sr, worker=w, entered_by=w, allocated_quantity=Decimal('8'),
            earning_rate_snapshot=Decimal('3'), earning_amount_snapshot=Decimal('24'))
        rows = reconciliation_service.reconcile_stage_pay(adda=adda)
        row = next(r for r in rows if r['stage'] == 'rc_s')
        self.assertEqual(row['flag'], 'over_allocated')
        self.assertIn('over_allocated', reconciliation_service.HARD_FLAGS)
        self.assertEqual(row['qty_delta'], Decimal('-3'))   # 5 output − 8 settled
