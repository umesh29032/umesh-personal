"""Foundation S5 — M-6 settlement reconciliation BLOCK + audited override.

Σ settled good > produced (cost_quantity_snapshot) = the B-1 leak. WARN by default;
BLOCK when ENFORCE_SETTLEMENT_RECONCILIATION on + over beyond tolerance, unless a super-admin
override (reason). Quantity-only; settlement stays the money boundary; golden ₹225 unaffected.
"""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.utils import timezone

from accounts.models import User
from expense.models import AddaSettlement, SettlementReconciliationEvidence
from expense.services.adda_settlement_service import create_draft, finalize_adda_settlement
from inventory.models import Role
from production.models import Adda, AddaStageRecord, Product, Stage, WorkflowStage, WorkerStageTask
from production.services.worker_task_service import (
    complete_worker_task, report_contributions, set_stage_workers,
)


def _user(email, code):
    u = User.objects.create_user(email=email, password='x')
    u.role = Role.objects.get(code=code); u.save()
    return u


class _Base(TestCase):
    def _over_allocated_draft(self, *, produced='5', settled='8', code='s5'):
        """A payable stage that PRODUCED `produced` but SETTLES `settled` (the leak)."""
        self.mgr = _user(f's5-mgr-{code}@t', 'manager')
        self.admin = _user(f's5-adm-{code}@t', 'super_admin')
        self.worker = _user(f's5-w-{code}@t', 'worker')
        product = Product.objects.create(code='S5' + code, name='S5 ' + code)
        stage, _ = Stage.objects.get_or_create(code='s5cut_' + code, defaults={'name': 'Cut'})
        ws = WorkflowStage.objects.create(product=product, stage=stage, order=1,
                                          cost_rate=Decimal('3'), credits_workers=True)
        adda = Adda.objects.create(code='S5-' + code, product=product, status=Adda.Status.IN_PROGRESS)
        sr = AddaStageRecord.objects.create(adda=adda, workflow_stage=ws, started_at=timezone.now())
        set_stage_workers(sr, [self.worker.pk])
        task = WorkerStageTask.objects.get(stage_record=sr, worker=self.worker)
        report_contributions(task, [{'reported_quantity': settled}], actor=self.worker)
        complete_worker_task(task, actor=self.worker)
        # Freeze the produced output (handler qty) + a priced cost, then close the stage.
        sr.processing_cost = Decimal('15')
        sr.cost_quantity_snapshot = Decimal(produced)
        sr.completed_at = timezone.now()
        sr.save(update_fields=['processing_cost', 'cost_quantity_snapshot', 'completed_at'])
        return create_draft(adda=adda, user=self.mgr)


class WarnDefaultTests(_Base):
    def test_flag_off_finalizes_with_warn(self):
        s = self._over_allocated_draft()
        finalize_adda_settlement(settlement=s, user=self.mgr)   # ENFORCE off (default)
        s.refresh_from_db()
        self.assertEqual(s.status, AddaSettlement.Status.FINALIZED)
        ev = SettlementReconciliationEvidence.objects.get(adda_settlement=s)
        self.assertEqual(ev.flag, 'over_allocated')
        self.assertEqual(ev.override_reason, '')          # WARN, not overridden
        self.assertIsNone(ev.overridden_by_id)


@override_settings(ENFORCE_SETTLEMENT_RECONCILIATION=True)
class BlockTests(_Base):
    def test_over_allocation_blocks_finalize(self):
        s = self._over_allocated_draft(produced='5', settled='8')
        with self.assertRaisesMessage(ValidationError, 'settled more than produced'):
            finalize_adda_settlement(settlement=s, user=self.mgr)
        s.refresh_from_db()
        self.assertEqual(s.status, AddaSettlement.Status.DRAFT)   # rolled back, nothing booked
        self.assertFalse(SettlementReconciliationEvidence.objects.filter(adda_settlement=s).exists())

    @override_settings(SETTLEMENT_RECONCILIATION_TOLERANCE='5')
    def test_within_tolerance_finalizes(self):
        s = self._over_allocated_draft(produced='5', settled='8', code='tol')   # over by 3 ≤ 5
        finalize_adda_settlement(settlement=s, user=self.mgr)
        s.refresh_from_db()
        self.assertEqual(s.status, AddaSettlement.Status.FINALIZED)

    def test_super_admin_override_finalizes_and_stamps_audit(self):
        s = self._over_allocated_draft(code='ovr')
        finalize_adda_settlement(settlement=s, user=self.admin,
                                 reconciliation_override='owner accepts — rework recovered offsite')
        s.refresh_from_db()
        self.assertEqual(s.status, AddaSettlement.Status.FINALIZED)
        ev = SettlementReconciliationEvidence.objects.get(adda_settlement=s)
        self.assertEqual(ev.override_reason, 'owner accepts — rework recovered offsite')
        self.assertEqual(ev.overridden_by_id, self.admin.pk)

    def test_non_super_admin_override_still_blocked(self):
        s = self._over_allocated_draft(code='mgr')
        with self.assertRaisesMessage(ValidationError, 'Only a super admin'):
            finalize_adda_settlement(settlement=s, user=self.mgr,
                                     reconciliation_override='manager tries to override')
        s.refresh_from_db()
        self.assertEqual(s.status, AddaSettlement.Status.DRAFT)

    def test_clean_adda_finalizes_under_enforce(self):
        # produced == settled → no over-allocation → finalizes even with ENFORCE on.
        s = self._over_allocated_draft(produced='8', settled='8', code='clean')
        finalize_adda_settlement(settlement=s, user=self.mgr)
        s.refresh_from_db()
        self.assertEqual(s.status, AddaSettlement.Status.FINALIZED)
