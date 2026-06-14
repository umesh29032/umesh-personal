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


class SettlementWarnScopeTests(TestCase):
    """S1.1 H1: the settlement WARN is the B-1 leak ONLY — not every HARD flag."""

    def test_warn_flags_are_over_allocated_only(self):
        self.assertEqual(reconciliation_service.SETTLEMENT_WARN_FLAGS, frozenset({'over_allocated'}))
        # subset of HARD_FLAGS (still a real defect) but narrower (no noise).
        self.assertTrue(reconciliation_service.SETTLEMENT_WARN_FLAGS <= reconciliation_service.HARD_FLAGS)

    def test_no_output_qty_is_hard_but_not_a_settlement_warn(self):
        # A priced stage with NO frozen output qty classifies 'no_output_qty' — a
        # HARD flag, but NOT a B-1 leak → must NOT surface as a settlement WARN.
        product = Product.objects.create(code='NOQ', name='NOQ')
        stage, _ = Stage.objects.get_or_create(code='noq_s', defaults={'name': 'NOQ'})
        ws = WorkflowStage.objects.create(product=product, stage=stage, order=1,
                                          cost_rate=Decimal('3'), credits_workers=True)
        adda = Adda.objects.create(code='NOQ-1', product=product, status=Adda.Status.IN_PROGRESS)
        AddaStageRecord.objects.create(
            adda=adda, workflow_stage=ws, started_at=timezone.now(), completed_at=timezone.now(),
            processing_cost=Decimal('15.00'), cost_quantity_snapshot=None)   # priced, no qty
        rows = reconciliation_service.reconcile_stage_pay(adda=adda)
        row = next(r for r in rows if r['stage'] == 'noq_s')
        self.assertEqual(row['flag'], 'no_output_qty')
        self.assertIn('no_output_qty', reconciliation_service.HARD_FLAGS)
        self.assertNotIn(row['flag'], reconciliation_service.SETTLEMENT_WARN_FLAGS)


class ReconciliationEvidenceTests(TestCase):
    """S1.1 H2: over-allocation persists an append-only evidence row at finalize."""

    def _over_allocated_adda(self, code):
        from expense.models import AddaSettlement
        product = Product.objects.create(code=code, name=code)
        stage, _ = Stage.objects.get_or_create(code=code.lower() + '_s', defaults={'name': code})
        ws = WorkflowStage.objects.create(product=product, stage=stage, order=1,
                                          cost_rate=Decimal('3'), credits_workers=True)
        adda = Adda.objects.create(code=code + '-1', product=product, status=Adda.Status.IN_PROGRESS)
        sr = AddaStageRecord.objects.create(
            adda=adda, workflow_stage=ws, started_at=timezone.now(), completed_at=timezone.now(),
            processing_cost=Decimal('15.00'), cost_quantity_snapshot=Decimal('5'))
        w = User.objects.create_user(email=f'{code}-w@test', password='x')
        w.role = Role.objects.get(code='worker'); w.save()
        settlement = AddaSettlement.objects.create(
            reference='ADST-' + code, adda=adda, status=AddaSettlement.Status.DRAFT)
        return adda, sr, w, settlement

    def test_evidence_written_for_over_allocation(self):
        from expense.models import SettlementReconciliationEvidence
        from expense.services import adda_settlement_service as adst
        adda, sr, w, settlement = self._over_allocated_adda('EVD')
        StageWorkAssignment.objects.create(
            stage_record=sr, worker=w, entered_by=w, allocated_quantity=Decimal('8'),
            earning_rate_snapshot=Decimal('3'), earning_amount_snapshot=Decimal('24'))
        n = adst.record_reconciliation_evidence(settlement, adda)
        self.assertEqual(n, 1)
        ev = SettlementReconciliationEvidence.objects.get(adda_settlement=settlement)
        self.assertEqual(ev.flag, 'over_allocated')
        self.assertEqual(ev.stage_record_id, sr.pk)
        self.assertEqual(ev.qty_delta, Decimal('-3'))      # 5 − 8
        self.assertEqual(ev.allocated_qty, Decimal('8'))

    def test_no_evidence_when_clean(self):
        from expense.models import SettlementReconciliationEvidence
        from expense.services import adda_settlement_service as adst
        adda, sr, w, settlement = self._over_allocated_adda('CLN')
        StageWorkAssignment.objects.create(   # allocated == output → clean
            stage_record=sr, worker=w, entered_by=w, allocated_quantity=Decimal('5'),
            earning_rate_snapshot=Decimal('3'), earning_amount_snapshot=Decimal('15'))
        n = adst.record_reconciliation_evidence(settlement, adda)
        self.assertEqual(n, 0)
        self.assertFalse(SettlementReconciliationEvidence.objects.filter(adda_settlement=settlement).exists())
