"""Tests for the expense/payroll app — allocation-driven earnings + immutable
ledger + advances (separate loan pool) + on-demand settlements + scoping."""
from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase

from accounts.models import Skill, User
from inventory.models import Role
from production.models import AddaStageRecord, Product
from production.services import create_adda
from expense.models import StageWorkAssignment, WorkerLedgerEntry
from expense.services import (
    allocate_stage_work, advance_outstanding, can_view_worker, create_settlement,
    record_advance, reverse_entry, worker_balance, worker_summary,
)


def _manager():
    role = Role.objects.get(code='super_admin')
    u = User.objects.create_user(email='mgr@exp.test', password='x', is_superuser=True, is_staff=True)
    u.role = role
    u.save()
    u.skills.add(Skill.objects.get(name='cutting_master'))
    return u


class ExpenseCoreTests(TestCase):
    def setUp(self):
        self.mgr = _manager()
        self.worker = User.objects.create_user(email='worker@exp.test', password='x')
        self.other = User.objects.create_user(email='other@exp.test', password='x')
        adda = create_adda(self.mgr, product=Product.objects.get(code='NIKKAR'))
        self.sr = AddaStageRecord.objects.get(adda=adda, workflow_stage=adda.current_stage)
        # Price the stage so allocation has a rate.
        ws = self.sr.workflow_stage
        # Layering ships grouped-at-cutting (migration 0026). These earning tests
        # use it as a priced vehicle, so ungroup + price it.
        ws.cost_billed_at = None
        ws.cost_rate = Decimal('2')
        ws.save(update_fields=['cost_billed_at', 'cost_rate'])

    def test_allocation_is_quantity_driven_and_credits_ledger(self):
        a = allocate_stage_work(user=self.mgr, stage_record=self.sr,
                                worker=self.worker, allocated_quantity=10)
        self.assertEqual(a.earning_amount_snapshot, Decimal('20.00'))   # 2 × 10
        self.assertEqual(worker_balance(self.worker), Decimal('20.00'))
        # the credit traces back to its source assignment
        credit = WorkerLedgerEntry.objects.get(worker=self.worker, category='stage_earning')
        self.assertEqual(credit.assignment_id, a.id)

    def test_multiple_allocations_per_worker_same_stage(self):
        allocate_stage_work(user=self.mgr, stage_record=self.sr, worker=self.worker, allocated_quantity=10)
        allocate_stage_work(user=self.mgr, stage_record=self.sr, worker=self.worker, allocated_quantity=5)
        self.assertEqual(StageWorkAssignment.objects.filter(worker=self.worker).count(), 2)
        self.assertEqual(worker_balance(self.worker), Decimal('30.00'))   # 20 + 10

    def test_rate_snapshot_frozen_against_later_edit(self):
        a = allocate_stage_work(user=self.mgr, stage_record=self.sr, worker=self.worker, allocated_quantity=10)
        ws = self.sr.workflow_stage
        ws.cost_rate = Decimal('9')          # edit rate AFTER allocation
        ws.save(update_fields=['cost_rate'])
        a.refresh_from_db()
        self.assertEqual(a.earning_amount_snapshot, Decimal('20.00'))   # unchanged

    def test_advance_does_not_reduce_payable(self):
        # Advance is a SEPARATE loan pool now — it must NOT debit the payable.
        allocate_stage_work(user=self.mgr, stage_record=self.sr, worker=self.worker, allocated_quantity=10)  # +20
        record_advance(user=self.mgr, worker=self.worker, amount=5)
        self.assertEqual(worker_balance(self.worker), Decimal('20.00'))         # unchanged
        self.assertEqual(advance_outstanding(self.worker), Decimal('5.00'))     # tracked separately

    def test_settlement_pays_cash_and_resets_payable(self):
        allocate_stage_work(user=self.mgr, stage_record=self.sr, worker=self.worker, allocated_quantity=10)  # payable 20
        s = create_settlement(user=self.mgr, worker=self.worker, amount_paid=20)
        self.assertEqual(worker_balance(self.worker), Decimal('0.00'))          # fresh overview
        self.assertEqual(s.amount_paid, Decimal('20.00'))
        self.assertEqual(worker_summary(self.worker)['total_settled'], Decimal('20.00'))

    def test_payment_recovery_rejected_post_v2_2(self):
        # V2-2 Model A: recovery RE-HOMED to AddaSettlement.finalize — the
        # payment event refuses it (mechanics covered in
        # test_adda_settlement_service).
        allocate_stage_work(user=self.mgr, stage_record=self.sr, worker=self.worker, allocated_quantity=10)
        adv = record_advance(user=self.mgr, worker=self.worker, amount=15)
        with self.assertRaises(ValidationError):
            create_settlement(user=self.mgr, worker=self.worker, amount_paid=10,
                              recoveries=[{'advance': adv.id, 'amount': 10}])
        # payment-only still works:
        create_settlement(user=self.mgr, worker=self.worker, amount_paid=10)
        self.assertEqual(worker_balance(self.worker), Decimal('10.00'))
        self.assertEqual(advance_outstanding(self.worker), Decimal('15.00'))

    def test_partial_settlement_leaves_remainder(self):
        allocate_stage_work(user=self.mgr, stage_record=self.sr, worker=self.worker, allocated_quantity=10)  # payable 20
        create_settlement(user=self.mgr, worker=self.worker, amount_paid=5)
        self.assertEqual(worker_balance(self.worker), Decimal('15.00'))          # remainder still owed

    def test_settlement_cannot_exceed_payable(self):
        allocate_stage_work(user=self.mgr, stage_record=self.sr, worker=self.worker, allocated_quantity=10)  # payable 20
        with self.assertRaises(ValidationError):
            create_settlement(user=self.mgr, worker=self.worker, amount_paid=25)

    # (V2-2) recovery-bound checks live at AddaSettlement.finalize now —
    # see test_adda_settlement_service.test_over_recovery_rejected.

    def test_settlement_requires_management(self):
        allocate_stage_work(user=self.mgr, stage_record=self.sr, worker=self.worker, allocated_quantity=10)
        with self.assertRaises(PermissionDenied):
            create_settlement(user=self.worker, worker=self.worker, amount_paid=5)

    def test_summary_breakdown(self):
        allocate_stage_work(user=self.mgr, stage_record=self.sr, worker=self.worker, allocated_quantity=10)  # +20
        record_advance(user=self.mgr, worker=self.worker, amount=4)
        create_settlement(user=self.mgr, worker=self.worker, amount_paid=6)
        s = worker_summary(self.worker)
        self.assertEqual(s['total_earnings'], Decimal('20.00'))
        self.assertEqual(s['advance_outstanding'], Decimal('4.00'))
        self.assertEqual(s['total_settled'], Decimal('6.00'))
        self.assertEqual(s['pending_payable'], Decimal('14.00'))   # 20 − 6 (advance does NOT reduce)

    def test_reverse_entry_undoes_balance(self):
        a = allocate_stage_work(user=self.mgr, stage_record=self.sr, worker=self.worker, allocated_quantity=10)
        credit = WorkerLedgerEntry.objects.get(assignment=a)
        reverse_entry(credit, actor=self.mgr)
        self.assertEqual(worker_balance(self.worker), Decimal('0.00'))   # reversed
        # double-reverse refused
        with self.assertRaises(ValidationError):
            reverse_entry(credit, actor=self.mgr)

    def test_allocation_requires_management(self):
        with self.assertRaises(PermissionDenied):
            allocate_stage_work(user=self.worker, stage_record=self.sr,
                                worker=self.worker, allocated_quantity=10)

    def test_unpriced_stage_blocks_allocation(self):
        ws = self.sr.workflow_stage
        ws.cost_rate = None
        ws.save(update_fields=['cost_rate'])
        with self.assertRaises(ValidationError):
            allocate_stage_work(user=self.mgr, stage_record=self.sr,
                                worker=self.worker, allocated_quantity=10)

    def test_worker_scoping(self):
        self.assertTrue(can_view_worker(self.worker, self.worker.pk))   # self
        self.assertFalse(can_view_worker(self.worker, self.other.pk))   # not another worker
        self.assertTrue(can_view_worker(self.mgr, self.worker.pk))      # management sees all

    def test_settlement_reversal_nets_settled_not_earnings(self):
        # Regression (payroll-3 + sibling): reversing a settlement-payment debit
        # writes an OPPOSITE-direction CREDIT/REVERSAL. total_settled must net it
        # out, pending_payable must be restored, and the reversal credit must NOT
        # be miscounted as a new earning.
        allocate_stage_work(user=self.mgr, stage_record=self.sr, worker=self.worker, allocated_quantity=10)  # +20
        create_settlement(user=self.mgr, worker=self.worker, amount_paid=20)
        before = worker_summary(self.worker)
        self.assertEqual(before['total_settled'], Decimal('20.00'))
        pay_debit = WorkerLedgerEntry.objects.get(worker=self.worker, category='settlement_payment')
        reverse_entry(pay_debit, actor=self.mgr)
        after = worker_summary(self.worker)
        self.assertEqual(after['total_settled'], Decimal('0.00'))      # netted
        self.assertEqual(after['pending_payable'], Decimal('20.00'))   # payable restored
        self.assertEqual(after['total_earnings'], Decimal('20.00'))    # NOT inflated by reversal credit

    def test_settlement_references_unique_across_workers(self):
        # Regression (payroll-2): reference allocation stays correct + unique when
        # two different workers are settled (the race fix must not break the
        # sequential path).
        allocate_stage_work(user=self.mgr, stage_record=self.sr, worker=self.worker, allocated_quantity=10)
        allocate_stage_work(user=self.mgr, stage_record=self.sr, worker=self.other, allocated_quantity=10)
        s1 = create_settlement(user=self.mgr, worker=self.worker, amount_paid=5)
        s2 = create_settlement(user=self.mgr, worker=self.other, amount_paid=5)
        self.assertNotEqual(s1.reference, s2.reference)
        self.assertEqual({s1.reference, s2.reference}, {'SETL-0001', 'SETL-0002'})
