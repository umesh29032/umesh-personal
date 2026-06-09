"""PAY-4 (M1.4): worker-pay reconciliation control.

Verifies reconcile_stage_pay classifies each completed stage correctly:
ok / unpaid / under_allocated / over_allocated / grouped / unpriced, and that
the summary splits hard defects from the (currently expected) PAY-2 soft gap.
"""
from decimal import Decimal
from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from accounts.models import User
from expense.services import allocate_stage_work, reconcile_stage_pay, reconcile_summarize
from production.models import Adda, AddaStageRecord, Product, Stage, WorkflowStage


class ReconciliationTest(TestCase):
    def setUp(self):
        cut = Stage.objects.get_or_create(code='cutting', defaults={'name': 'Cutting'})[0]
        self.product = Product.objects.create(code='RECON', name='Recon Test')
        self.ws = WorkflowStage.objects.create(
            product=self.product, stage=cut, order=1, cost_rate=Decimal('10'))
        self.adda = Adda.objects.create(
            code='RECON-001', product=self.product, status=Adda.Status.COMPLETED)
        self.mgr = User.objects.create_user(
            email='recon-mgr@test', password='x', is_superuser=True, is_staff=True)
        self.worker = User.objects.create_user(email='recon-worker@test', password='x')

    def _sr(self, *, cost, out_qty):
        """A completed stage record with a frozen cost + output quantity."""
        return AddaStageRecord.objects.create(
            adda=self.adda, workflow_stage=self.ws,
            started_at=timezone.now(), completed_at=timezone.now(), completed_by=self.mgr,
            cost_method_snapshot='per_piece',
            cost_rate_snapshot=Decimal('10') if cost is not None else None,
            cost_quantity_snapshot=out_qty,
            processing_cost=cost,
        )

    def _alloc(self, sr, qty):
        return allocate_stage_work(
            user=self.mgr, stage_record=sr, worker=self.worker, allocated_quantity=qty)

    # unique_together(adda, workflow_stage) means one sr per (adda, ws); each test
    # below uses its own fresh adda via a distinct code to allow multiple srs.
    def _fresh_adda(self, code):
        return Adda.objects.create(code=code, product=self.product, status=Adda.Status.COMPLETED)

    def _row_for(self, adda):
        rows = reconcile_stage_pay(adda=adda)
        self.assertEqual(len(rows), 1)
        return rows[0]

    def test_ok_when_fully_allocated(self):
        sr = self._sr(cost=Decimal('100'), out_qty=Decimal('10'))
        self._alloc(sr, 10)
        self.assertEqual(self._row_for(self.adda)['flag'], 'ok')

    def test_unpaid_when_no_allocations(self):
        self._sr(cost=Decimal('100'), out_qty=Decimal('10'))
        row = self._row_for(self.adda)
        self.assertEqual(row['flag'], 'unpaid')
        self.assertEqual(reconcile_summarize([row])['soft'], 1)

    def test_under_allocated(self):
        sr = self._sr(cost=Decimal('100'), out_qty=Decimal('10'))
        self._alloc(sr, 6)
        row = self._row_for(self.adda)
        self.assertEqual(row['flag'], 'under_allocated')
        self.assertEqual(row['qty_delta'], Decimal('4'))

    def test_over_allocated_is_hard(self):
        sr = self._sr(cost=Decimal('100'), out_qty=Decimal('10'))
        self._alloc(sr, 12)
        row = self._row_for(self.adda)
        self.assertEqual(row['flag'], 'over_allocated')
        self.assertEqual(reconcile_summarize([row])['hard'], 1)

    def test_grouped_and_unpriced_are_clean(self):
        a1 = self._fresh_adda('RECON-GRP')
        AddaStageRecord.objects.create(
            adda=a1, workflow_stage=self.ws, started_at=timezone.now(),
            completed_at=timezone.now(), processing_cost=Decimal('0'))
        a2 = self._fresh_adda('RECON-UNP')
        AddaStageRecord.objects.create(
            adda=a2, workflow_stage=self.ws, started_at=timezone.now(),
            completed_at=timezone.now(), processing_cost=None)
        self.assertEqual(self._row_for(a1)['flag'], 'grouped')
        self.assertEqual(self._row_for(a2)['flag'], 'unpriced')

    def test_command_exits_nonzero_on_hard_defect(self):
        sr = self._sr(cost=Decimal('100'), out_qty=Decimal('10'))
        self._alloc(sr, 12)  # over-allocated -> hard
        with self.assertRaises(SystemExit) as cm:
            call_command('reconcile_pay', stdout=StringIO(), stderr=StringIO())
        self.assertEqual(cm.exception.code, 1)

    def test_command_clean_run_exits_zero(self):
        sr = self._sr(cost=Decimal('100'), out_qty=Decimal('10'))
        self._alloc(sr, 10)  # ok
        out = StringIO()
        call_command('reconcile_pay', '--all', stdout=out, stderr=StringIO())
        self.assertIn('hard: 0', out.getvalue())
