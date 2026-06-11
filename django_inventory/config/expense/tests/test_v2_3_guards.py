"""V2-3 PR-A (D-V3.2): settlement-money armor.

The new invariant: settlement money is only ever mutated by
adda_settlement_service. The two legacy correction doors are closed:
  H1 — reopen of a settlement-credited stage is BLOCKED (names the ADST refs);
       the PAY-3 void sweep narrows to era-A (allocation) lines only.
  H2 — void_allocation refuses era-B (settlement) earning lines.
Reverse-the-settlement-first restores both doors — proven here.
"""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.test import TestCase
from django.utils import timezone

from accounts.models import User
from inventory.models import Role
from expense.models import WorkerLedgerEntry
from expense.services.adda_settlement_service import (
    create_draft, finalize_adda_settlement, reverse_adda_settlement,
)
from expense.services.allocation_service import allocate_stage_work, void_allocation
from production.models import (
    Adda, AddaStageRecord, Product, Stage, WorkflowStage, WorkerStageTask,
)
from production.services._shared import reopen_stage_record
from production.services.worker_task_service import (
    complete_worker_task, report_contributions, set_stage_workers,
)


class _Base(TestCase):
    def setUp(self):
        self.mgmt = User.objects.create_user(email='g-mgmt@test', password='x')
        self.mgmt.role = Role.objects.get(code='manager')
        self.mgmt.save()
        self.w1 = User.objects.create_user(email='g-w1@test', password='x')
        self.product = Product.objects.create(code='GRD', name='GRD P')
        stage, _ = Stage.objects.get_or_create(
            code='grd_cutting', defaults={'name': 'GRD Cutting'})
        self.ws = WorkflowStage.objects.create(
            product=self.product, stage=stage, order=1,
            cost_rate=Decimal('3'), credits_workers=True)
        self.adda = Adda.objects.create(code='GRD-001', product=self.product)
        self.sr = AddaStageRecord.objects.create(
            adda=self.adda, workflow_stage=self.ws, started_at=timezone.now())

    def _contribute_and_close(self, qty=10):
        set_stage_workers(self.sr, [self.w1.pk])
        task = WorkerStageTask.objects.get(stage_record=self.sr, worker=self.w1)
        report_contributions(task, [{'reported_quantity': str(qty)}], actor=self.w1)
        complete_worker_task(task, actor=self.w1)
        self.sr.completed_at = timezone.now()
        self.sr.save(update_fields=['completed_at'])

    def _settle(self):
        s = create_draft(adda=self.adda, user=self.mgmt)
        finalize_adda_settlement(settlement=s, user=self.mgmt)
        return s

    def _reopen(self):
        # Skeleton owns the invariant; guard/teardown None = pure-skeleton path.
        with transaction.atomic():
            return reopen_stage_record(
                adda=self.adda, stage_code='grd_cutting',
                stage_label='GRD Cutting', user=self.mgmt)


class VoidGuardTests(_Base):
    def test_void_refuses_settlement_earning_line(self):
        self._contribute_and_close()
        s = self._settle()
        line = s.earning_lines.get()
        with self.assertRaisesMessage(ValidationError, s.reference):
            void_allocation(line, user=self.mgmt)
        line.refresh_from_db()
        self.assertIsNone(line.voided_at)                 # untouched
        # ledger untouched: exactly the one settlement credit
        self.assertEqual(WorkerLedgerEntry.objects.filter(
            worker=self.w1).count(), 1)

    def test_void_still_works_for_era_a(self):
        swa = allocate_stage_work(user=self.mgmt, stage_record=self.sr,
                                  worker=self.w1, allocated_quantity=Decimal('5'))
        void_allocation(swa, user=self.mgmt)
        swa.refresh_from_db()
        self.assertIsNotNone(swa.voided_at)


class ReopenGuardTests(_Base):
    def test_reopen_blocked_when_settled_names_reference(self):
        self._contribute_and_close()
        s = self._settle()
        with self.assertRaisesMessage(ValidationError, s.reference):
            self._reopen()
        self.sr.refresh_from_db()
        self.assertIsNotNone(self.sr.completed_at)        # still closed
        # nothing reversed, nothing voided
        self.assertEqual(WorkerLedgerEntry.objects.count(), 1)
        self.assertTrue(s.earning_lines.filter(voided_at__isnull=True).exists())

    def test_reopen_before_settlement_voids_era_a_only(self):
        # era-A allocation while the stage is open, then close WITHOUT settling.
        swa = allocate_stage_work(user=self.mgmt, stage_record=self.sr,
                                  worker=self.w1, allocated_quantity=Decimal('5'))
        self._contribute_and_close()
        self._reopen()
        swa.refresh_from_db()
        self.assertIsNotNone(swa.voided_at)               # PAY-3 preserved
        # credit + its reversal
        self.assertEqual(WorkerLedgerEntry.objects.filter(
            worker=self.w1).count(), 2)

    def test_reverse_settlement_then_reopen_succeeds(self):
        self._contribute_and_close()
        s = self._settle()
        reverse_adda_settlement(settlement=s, user=self.mgmt)
        sr = self._reopen()
        self.assertIsNone(sr.completed_at)
        # the (already-voided) settlement lines were NOT touched again by the
        # sweep: still exactly credit + reversal in the ledger.
        self.assertEqual(WorkerLedgerEntry.objects.filter(
            worker=self.w1).count(), 2)

    def test_reopen_with_mixed_eras_after_reversal_voids_era_a_only(self):
        # era-A line + settled era-B line, settlement reversed → reopen voids
        # ONLY the era-A line; voided era-B lines stay untouched.
        swa_a = allocate_stage_work(user=self.mgmt, stage_record=self.sr,
                                    worker=self.w1, allocated_quantity=Decimal('5'))
        # second worker contributes so the settlement has an uncredited line
        w2 = User.objects.create_user(email='g-w2@test', password='x')
        set_stage_workers(self.sr, [self.w1.pk, w2.pk])
        task = WorkerStageTask.objects.get(stage_record=self.sr, worker=w2)
        report_contributions(task, [{'reported_quantity': '7'}], actor=w2)
        complete_worker_task(task, actor=w2)
        self.sr.completed_at = timezone.now()
        self.sr.save(update_fields=['completed_at'])
        s = self._settle()
        reverse_adda_settlement(settlement=s, user=self.mgmt)
        self._reopen()
        swa_a.refresh_from_db()
        self.assertIsNotNone(swa_a.voided_at)
        # era-B line voided exactly once (by the reversal, not the sweep):
        line_b = s.earning_lines.get()
        self.assertIsNotNone(line_b.voided_at)
        # w2 ledger: settlement credit + reversal only (no double reversal)
        self.assertEqual(WorkerLedgerEntry.objects.filter(worker=w2).count(), 2)
