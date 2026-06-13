"""V2-2 PR-A: model/constraint surface only — services come in PR-B.
Locks: XOR parenting on PayrollSettlementItem, status/timestamp coherence,
non-negative checks, recovery-within-outstanding, settlement_line provenance FK.
"""
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from accounts.models import User
from expense.models import (
    AddaSettlement, AddaSettlementItem, PayrollSettlement, PayrollSettlementItem,
    StageWorkAssignment, WorkerAdvance,
)
from production.models import (
    Adda, AddaStageRecord, Product, Stage, WorkflowStage,
    WorkerStageTask, WorkerStageContribution,
)


class AddaSettlementModelTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(code='AST', name='AST P')
        self.stage, _ = Stage.objects.get_or_create(
            code='ast_stage', defaults={'name': 'AST'})
        self.ws = WorkflowStage.objects.create(
            product=self.product, stage=self.stage, order=1,
            cost_rate=Decimal('3'))
        self.adda = Adda.objects.create(code='AST-001', product=self.product)
        self.sr = AddaStageRecord.objects.create(
            adda=self.adda, workflow_stage=self.ws, started_at=timezone.now())
        self.worker = User.objects.create_user(email='ast-w@test', password='x')

    def _settlement(self, **kw):
        defaults = dict(reference='ADST-T001', adda=self.adda)
        defaults.update(kw)
        return AddaSettlement.objects.create(**defaults)

    def test_draft_default_and_no_unique_adda(self):
        s1 = self._settlement()
        self.assertEqual(s1.status, AddaSettlement.Status.DRAFT)
        # Partial settlements legal — second settlement on the same Adda OK.
        self._settlement(reference='ADST-T002')
        self.assertEqual(AddaSettlement.objects.filter(adda=self.adda).count(), 2)

    def test_finalized_requires_settled_at(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self._settlement(status=AddaSettlement.Status.FINALIZED)

    def test_item_recovery_within_outstanding(self):
        s = self._settlement()
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                AddaSettlementItem.objects.create(
                    adda_settlement=s, worker=self.worker,
                    advance_outstanding_before=Decimal('100'),
                    advance_recovered=Decimal('150'),
                )

    def test_recovery_line_xor_parent(self):
        s = self._settlement()
        adv = WorkerAdvance.objects.create(
            worker=self.worker, amount=Decimal('500'),
            advance_date=timezone.now().date(), entered_by=self.worker)
        # both parents → rejected
        pay = PayrollSettlement.objects.create(
            reference='SETL-T001', worker=self.worker,
            settlement_date=timezone.now().date(),
            payable_before=0, advance_outstanding_before=0, amount_paid=0,
            created_by=self.worker)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                PayrollSettlementItem.objects.create(
                    settlement=pay, adda_settlement=s, advance=adv,
                    amount_recovered=Decimal('100'))
        # no parent → rejected
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                PayrollSettlementItem.objects.create(
                    advance=adv, amount_recovered=Decimal('100'))
        # exactly one parent (new world) → OK
        PayrollSettlementItem.objects.create(
            adda_settlement=s, advance=adv, amount_recovered=Decimal('100'))

    def test_contribution_settlement_line_provenance(self):
        task = WorkerStageTask.objects.create(
            stage_record=self.sr, worker=self.worker)
        c = WorkerStageContribution.objects.create(
            task=task, reported_quantity=Decimal('10'))
        self.assertIsNone(c.settlement_line)        # NULL until settled
        swa = StageWorkAssignment.objects.create(
            stage_record=self.sr, worker=self.worker,
            allocated_quantity=Decimal('10'),
            earning_rate_snapshot=Decimal('3'),
            earning_amount_snapshot=Decimal('30'),
            entered_by=self.worker)
        c.settlement_line = swa
        c.save(update_fields=['settlement_line', 'updated_at'])
        self.assertEqual(swa.settled_contributions.get().pk, c.pk)
