"""V2-2 PR-B: the 10 locked invariants (V2_2_EXECUTION_REVIEW Part 10) as
executable tests, incl. the cross-era guard on a 3-PATTI-001-shaped fixture.
"""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from accounts.models import User
from inventory.models import Role
from expense.models import (
    AddaSettlement, AddaSettlementItem, PayrollSettlementItem,
    StageWorkAssignment, WorkerAdvance, WorkerLedgerEntry,
)
from expense.services import ledger_service
from expense.services.adda_settlement_service import (
    create_draft, finalize_adda_settlement, preview_lines,
)
from production.models import (
    Adda, AddaStageRecord, Product, Stage, WorkflowStage,
    WorkerStageTask, WorkerStageContribution,
)
from production.services.worker_task_service import (
    complete_worker_task, report_contributions, set_stage_workers,
)
from tracking.models import AddaHistory


def _mgmt(email='ast-mgmt@test'):
    u = User.objects.create_user(email=email, password='x')
    u.role = Role.objects.get(code='manager')
    u.save()
    return u


class _Base(TestCase):
    """3-PATTI-001-shaped world: one payable stage (₹3/pc) + one non-payable."""

    def setUp(self):
        self.mgmt = _mgmt()
        self.w1 = User.objects.create_user(email='ast-w1@test', password='x')
        self.w2 = User.objects.create_user(email='ast-w2@test', password='x')
        self.product = Product.objects.create(code='ASV', name='ASV P')
        pay_stage, _ = Stage.objects.get_or_create(
            code='asv_cutting', defaults={'name': 'ASV Cutting'})
        free_stage, _ = Stage.objects.get_or_create(
            code='asv_layering', defaults={'name': 'ASV Layering'})
        self.ws_pay = WorkflowStage.objects.create(
            product=self.product, stage=pay_stage, order=2,
            cost_rate=Decimal('3'), credits_workers=True)
        self.ws_free = WorkflowStage.objects.create(
            product=self.product, stage=free_stage, order=1,
            cost_rate=Decimal('0'), credits_workers=False)
        self.adda = Adda.objects.create(code='ASV-001', product=self.product)
        now = timezone.now()
        # Stage records start OPEN (realistic order: contribute, then the stage
        # completes); _draft() closes them before creating the settlement.
        self.sr_pay = AddaStageRecord.objects.create(
            adda=self.adda, workflow_stage=self.ws_pay, started_at=now)
        self.sr_free = AddaStageRecord.objects.create(
            adda=self.adda, workflow_stage=self.ws_free, started_at=now)

    def _contribute(self, worker, sr, qty, *, complete=True):
        set_stage_workers(sr, [w.pk for w in {worker} | set(
            t.worker for t in sr.worker_tasks.exclude(
                status=WorkerStageTask.Status.CANCELLED))])
        task = WorkerStageTask.objects.get(
            stage_record=sr, worker=worker,
            status__in=('assigned', 'in_progress', 'completed', 'verified'))
        if task.status in ('completed', 'verified'):
            return task
        report_contributions(task, [{'reported_quantity': str(qty)}],
                             actor=worker)
        if complete:
            complete_worker_task(task, actor=worker)
        return task

    def _close_stages(self):
        now = timezone.now()
        for sr in (self.sr_pay, self.sr_free):
            if sr.completed_at is None:
                sr.completed_at = now
                sr.save(update_fields=['completed_at'])

    def _draft(self):
        self._close_stages()
        return create_draft(adda=self.adda, user=self.mgmt)

    def _credits(self, worker):
        return WorkerLedgerEntry.objects.filter(
            worker=worker, entry_type='credit', category='stage_earning')


class FinalizeFlowTests(_Base):
    def test_full_finalize_books_credits_and_freezes_snapshot(self):
        self._contribute(self.w1, self.sr_pay, 50)
        self._contribute(self.w2, self.sr_pay, 30)
        s = self._draft()
        finalize_adda_settlement(settlement=s, user=self.mgmt,
                                 variance={self.w1.pk: {'packed': 48, 'missing': 2}})
        s.refresh_from_db()
        self.assertEqual(s.status, AddaSettlement.Status.FINALIZED)
        self.assertEqual(s.expected_total, Decimal('240.00'))   # 50*3 + 30*3
        self.assertEqual(s.missing_total, 2)
        i1 = AddaSettlementItem.objects.get(adda_settlement=s, worker=self.w1)
        self.assertEqual(i1.expected_earning, Decimal('150.00'))
        self.assertEqual(i1.final_payable, Decimal('150.00'))   # factory_absorbs
        self.assertEqual(i1.missing_quantity, 2)
        # ledger: one credit per line, assignment provenance set
        self.assertEqual(self._credits(self.w1).count(), 1)
        c = WorkerStageContribution.objects.get(task__worker=self.w1)
        self.assertIsNotNone(c.settlement_line_id)
        self.assertEqual(
            self._credits(self.w1).get().assignment_id, c.settlement_line_id)
        self.assertEqual(ledger_service.worker_balance(self.w1), Decimal('150.00'))

    def test_history_event_logged(self):
        self._contribute(self.w1, self.sr_pay, 10)
        s = self._draft()
        finalize_adda_settlement(settlement=s, user=self.mgmt)
        ev = AddaHistory.objects.filter(
            adda=self.adda,
            change_type=AddaHistory.ChangeType.SETTLEMENT_FINALIZED)
        self.assertEqual(ev.count(), 1)
        self.assertEqual(ev.get().metadata['reference'], s.reference)


class InvariantTests(_Base):
    # I-3: no cash at finalize
    def test_no_settlement_payment_at_finalize(self):
        self._contribute(self.w1, self.sr_pay, 10)
        finalize_adda_settlement(settlement=self._draft(), user=self.mgmt)
        self.assertFalse(WorkerLedgerEntry.objects.filter(
            category='settlement_payment').exists())

    # I-4: drafts carry no money / no frozen rows
    def test_draft_carries_no_money(self):
        self._contribute(self.w1, self.sr_pay, 10)
        self._draft()
        self.assertFalse(WorkerLedgerEntry.objects.exists())
        self.assertFalse(AddaSettlementItem.objects.exists())

    # I-2 era-B exact: second settlement finds nothing; partial settles only new
    def test_era_b_guard_blocks_resettle_and_allows_partial(self):
        self._contribute(self.w1, self.sr_pay, 50)
        finalize_adda_settlement(settlement=self._draft(), user=self.mgmt)
        with self.assertRaises(ValidationError):
            finalize_adda_settlement(settlement=self._draft(), user=self.mgmt)
        # new work arrives later (stage reopened for it) → only IT settles
        self.sr_pay.completed_at = None
        self.sr_pay.save(update_fields=['completed_at'])
        self._contribute(self.w2, self.sr_pay, 30)
        s2 = self._draft()
        finalize_adda_settlement(settlement=s2, user=self.mgmt)
        s2.refresh_from_db()
        self.assertEqual(s2.expected_total, Decimal('90.00'))
        self.assertEqual(self._credits(self.w1).count(), 1)     # untouched

    # I-2 era-A coarse + NET: allocation-credited worker excluded until voided
    def test_era_a_guard_and_net_counting(self):
        self._contribute(self.w1, self.sr_pay, 45)
        self._contribute(self.w2, self.sr_pay, 30)
        era_a = StageWorkAssignment.objects.create(      # allocation-era credit
            stage_record=self.sr_pay, worker=self.w1,
            allocated_quantity=Decimal('45'),
            earning_rate_snapshot=Decimal('3'),
            earning_amount_snapshot=Decimal('135'),
            entered_by=self.mgmt)
        lines, skip_a, skip_b = preview_lines(self._draft())
        self.assertEqual({c.task.worker_id for c in lines}, {self.w2.pk})
        self.assertEqual({c.task.worker_id for c in skip_a}, {self.w1.pk})
        # NET counting: void the era-A SWA → w1 becomes settleable
        era_a.voided_at = timezone.now()
        era_a.save(update_fields=['voided_at'])
        s = AddaSettlement.objects.filter(status='draft').first()
        lines2, skip_a2, _ = preview_lines(s)
        self.assertEqual({c.task.worker_id for c in lines2},
                         {self.w1.pk, self.w2.pk})
        self.assertEqual(skip_a2, [])

    # I-5: quantity-freeze — verified used at finalize; later edits don't move money
    def test_quantity_freeze(self):
        task = self._contribute(self.w1, self.sr_pay, 50)
        c = task.contributions.get()
        c.verified_quantity = Decimal('45')
        c.save(update_fields=['verified_quantity'])
        s = self._draft()
        finalize_adda_settlement(settlement=s, user=self.mgmt)
        swa = WorkerStageContribution.objects.get(pk=c.pk).settlement_line
        self.assertEqual(swa.allocated_quantity, Decimal('45'))   # verified won
        self.assertEqual(swa.earning_amount_snapshot, Decimal('135.00'))
        # later correction: booked money unchanged; re-settle blocked (era-B)
        c.refresh_from_db(); c.verified_quantity = Decimal('40')
        c.save(update_fields=['verified_quantity'])
        swa.refresh_from_db()
        self.assertEqual(swa.earning_amount_snapshot, Decimal('135.00'))
        with self.assertRaises(ValidationError):
            finalize_adda_settlement(settlement=self._draft(), user=self.mgmt)

    # I-6: tie-out — frozen final_payable equals net ledger effect of THIS settlement
    def test_tie_out_with_recovery(self):
        self._contribute(self.w1, self.sr_pay, 50)
        adv = WorkerAdvance.objects.create(
            worker=self.w1, amount=Decimal('2000'),
            advance_date=timezone.now().date(), entered_by=self.mgmt)
        s = self._draft()
        finalize_adda_settlement(settlement=s, user=self.mgmt,
                                 recoveries={adv.pk: Decimal('500')})
        item = AddaSettlementItem.objects.get(adda_settlement=s)
        self.assertEqual(item.expected_earning, Decimal('150.00'))
        self.assertEqual(item.advance_recovered, Decimal('500.00'))
        # factory floor reality: recovery may exceed this Adda's earning —
        # final_payable floors at 0 on the snapshot; the LEDGER stays exact:
        self.assertEqual(ledger_service.worker_balance(self.w1),
                         Decimal('-350.00'))
        self.assertEqual(item.advance_outstanding_before, Decimal('2000.00'))
        recovery_line = PayrollSettlementItem.objects.get(adda_settlement=s)
        self.assertEqual(recovery_line.amount_recovered, Decimal('500.00'))

    # I-7: over-recovery rejected under lock
    def test_over_recovery_rejected(self):
        self._contribute(self.w1, self.sr_pay, 10)
        adv = WorkerAdvance.objects.create(
            worker=self.w1, amount=Decimal('100'),
            advance_date=timezone.now().date(), entered_by=self.mgmt)
        with self.assertRaises(ValidationError):
            finalize_adda_settlement(settlement=self._draft(), user=self.mgmt,
                                     recoveries={adv.pk: Decimal('150')})

    # I-8 (sequential form): double-finalize rejected by status under row lock
    def test_double_finalize_rejected(self):
        self._contribute(self.w1, self.sr_pay, 10)
        s = self._draft()
        finalize_adda_settlement(settlement=s, user=self.mgmt)
        with self.assertRaises(ValidationError):
            finalize_adda_settlement(settlement=s, user=self.mgmt)

    # I-9: expected_* never rewritten by settlement
    def test_expected_untouched(self):
        task = self._contribute(self.w1, self.sr_pay, 50)
        c = task.contributions.get()
        before = (c.expected_rate, c.expected_earning)
        finalize_adda_settlement(settlement=self._draft(), user=self.mgmt)
        c.refresh_from_db()
        self.assertEqual((c.expected_rate, c.expected_earning), before)

    # I-10: payability is data — non-payable stage produces no lines
    def test_non_payable_stage_excluded(self):
        self._contribute(self.w1, self.sr_free, 25)   # layering-like, credits=False
        self._contribute(self.w1, self.sr_pay, 10)
        s = self._draft()
        finalize_adda_settlement(settlement=s, user=self.mgmt)
        s.refresh_from_db()
        self.assertEqual(s.expected_total, Decimal('30.00'))    # only the payable 10×3
        self.assertEqual(self._credits(self.w1).count(), 1)

    # draft gate: incomplete payable stage blocks
    def test_draft_gate_requires_completed_payable_stages(self):
        # sr_pay still open (no _close_stages) → gate must refuse.
        with self.assertRaises(ValidationError):
            create_draft(adda=self.adda, user=self.mgmt)

    # non-management blocked
    def test_permission_gate(self):
        from django.core.exceptions import PermissionDenied
        self._contribute(self.w1, self.sr_pay, 10)
        with self.assertRaises(PermissionDenied):
            create_draft(adda=self.adda, user=self.w1)


class ReversalLifecycleTests(_Base):
    """PR-C: 'if an accountant makes a mistake today, what restores truth
    tomorrow without editing history?'"""

    def _settled_with_recovery(self):
        self._contribute(self.w1, self.sr_pay, 50)        # 150 expected
        adv = WorkerAdvance.objects.create(
            worker=self.w1, amount=Decimal('2000'),
            advance_date=timezone.now().date(), entered_by=self.mgmt)
        s = self._draft()
        finalize_adda_settlement(settlement=s, user=self.mgmt,
                                 recoveries={adv.pk: Decimal('500')})
        return s, adv

    def test_reverse_restores_ledger_and_advance(self):
        from expense.services.adda_settlement_service import reverse_adda_settlement
        from expense.services import payroll_service
        s, adv = self._settled_with_recovery()
        self.assertEqual(ledger_service.worker_balance(self.w1), Decimal('-350.00'))
        self.assertEqual(payroll_service.advance_outstanding(self.w1),
                         Decimal('1500.00'))

        reverse_adda_settlement(settlement=s, user=self.mgmt, notes='wrong qty')

        s.refresh_from_db()
        self.assertEqual(s.status, AddaSettlement.Status.REVERSED)
        # Money truth restored — compensating rows, never edits:
        self.assertEqual(ledger_service.worker_balance(self.w1), Decimal('0.00'))
        self.assertEqual(payroll_service.advance_outstanding(self.w1),
                         Decimal('2000.00'))
        # Append-only proof: original rows still exist + reversal rows added.
        self.assertEqual(WorkerLedgerEntry.objects.filter(
            worker=self.w1).count(), 4)   # credit + recovery + 2 reversals
        # Frozen snapshot untouched (audit of what was approved):
        item = AddaSettlementItem.objects.get(adda_settlement=s)
        self.assertEqual(item.expected_earning, Decimal('150.00'))
        # SWA voided → guard re-armed → contribution settleable again:
        c = WorkerStageContribution.objects.get(task__worker=self.w1)
        self.assertIsNotNone(c.settlement_line.voided_at)
        s2 = self._draft()
        lines, skip_a, skip_b = preview_lines(s2)
        self.assertEqual(len(lines), 1)
        self.assertEqual(skip_b, [])

    def test_supersede_chain_and_resettle(self):
        from expense.services.adda_settlement_service import (
            finalize_adda_settlement as fin, reverse_adda_settlement)
        task = self._contribute(self.w1, self.sr_pay, 50)
        s1 = self._draft()
        fin(settlement=s1, user=self.mgmt)
        # correction: verified says 45 — reverse+supersede, fix, re-finalize
        c = task.contributions.get()
        old, successor = reverse_adda_settlement(
            settlement=s1, user=self.mgmt, supersede=True, notes='verify 45')
        self.assertEqual(old.status, AddaSettlement.Status.SUPERSEDED)
        self.assertEqual(successor.supersedes_id, old.pk)
        c.refresh_from_db()
        c.verified_quantity = Decimal('45')
        c.save(update_fields=['verified_quantity'])
        fin(settlement=successor, user=self.mgmt)
        successor.refresh_from_db()
        self.assertEqual(successor.expected_total, Decimal('135.00'))
        self.assertEqual(ledger_service.worker_balance(self.w1), Decimal('135.00'))
        # provenance repointed to the NEW line; old line voided
        c.refresh_from_db()
        self.assertIsNone(c.settlement_line.voided_at)
        self.assertEqual(c.settlement_line.adda_settlement_id, successor.pk)

    def test_reverse_after_full_payment_goes_negative(self):
        from expense.services.adda_settlement_service import reverse_adda_settlement
        from expense.services.settlement_service import create_settlement
        self._contribute(self.w1, self.sr_pay, 50)
        s = self._draft()
        finalize_adda_settlement(settlement=s, user=self.mgmt)
        create_settlement(user=self.mgmt, worker=self.w1,
                          amount_paid=Decimal('150'))      # cash out
        self.assertEqual(ledger_service.worker_balance(self.w1), Decimal('0.00'))
        reverse_adda_settlement(settlement=s, user=self.mgmt)
        # paid cash stands; earnings reversed → worker owes the factory:
        self.assertEqual(ledger_service.worker_balance(self.w1),
                         Decimal('-150.00'))
        # payment guard: cannot pay against a negative balance
        with self.assertRaises(ValidationError):
            create_settlement(user=self.mgmt, worker=self.w1,
                              amount_paid=Decimal('10'))

    def test_mixed_era_reversal_never_touches_era_a(self):
        from expense.services.adda_settlement_service import reverse_adda_settlement
        # era-A credit for w2 (allocation path)
        StageWorkAssignment.objects.create(
            stage_record=self.sr_pay, worker=self.w2,
            allocated_quantity=Decimal('45'),
            earning_rate_snapshot=Decimal('3'),
            earning_amount_snapshot=Decimal('135'),
            entered_by=self.mgmt)
        ledger_service.log_credit(
            worker=self.w2, category='stage_earning', amount=Decimal('135'),
            entry_date=timezone.now().date(), created_by=self.mgmt)
        self._contribute(self.w1, self.sr_pay, 50)
        s = self._draft()
        finalize_adda_settlement(settlement=s, user=self.mgmt)
        reverse_adda_settlement(settlement=s, user=self.mgmt)
        # w2's allocation-era money untouched by the era-B reversal:
        self.assertEqual(ledger_service.worker_balance(self.w2), Decimal('135.00'))

    def test_double_reverse_rejected_and_history_logged(self):
        from expense.services.adda_settlement_service import reverse_adda_settlement
        self._contribute(self.w1, self.sr_pay, 10)
        s = self._draft()
        finalize_adda_settlement(settlement=s, user=self.mgmt)
        reverse_adda_settlement(settlement=s, user=self.mgmt)
        with self.assertRaises(ValidationError):
            reverse_adda_settlement(settlement=s, user=self.mgmt)
        self.assertTrue(AddaHistory.objects.filter(
            adda=self.adda,
            change_type=AddaHistory.ChangeType.SETTLEMENT_REVERSED).exists())

    def test_payment_recovery_now_rejected(self):
        from expense.services.settlement_service import create_settlement
        self._contribute(self.w1, self.sr_pay, 50)
        finalize_adda_settlement(settlement=self._draft(), user=self.mgmt)
        adv = WorkerAdvance.objects.create(
            worker=self.w1, amount=Decimal('100'),
            advance_date=timezone.now().date(), entered_by=self.mgmt)
        with self.assertRaises(ValidationError):
            create_settlement(user=self.mgmt, worker=self.w1,
                              amount_paid=Decimal('50'),
                              recoveries=[{'advance': adv.id, 'amount': 10}])


class Phase11SettlementAuditTests(_Base):
    """PA-11: settlement-audit fixes."""

    def test_outstanding_advances_excludes_reversed_recovery(self):
        """PA-11-1: a reversed recovery must NOT count as recovered in
        outstanding_advances (it already doesn't in advance_remaining/outstanding).
        After reversing a settlement that fully recovered an advance, the advance
        must reappear as outstanding so the owner can re-recover it."""
        from expense.services.payroll_service import outstanding_advances
        from expense.services.adda_settlement_service import reverse_adda_settlement
        self._contribute(self.w1, self.sr_pay, 50)            # ₹150 earning
        adv = WorkerAdvance.objects.create(
            worker=self.w1, amount=Decimal('100'),
            advance_date=timezone.now().date(), entered_by=self.mgmt)
        s = self._draft()
        finalize_adda_settlement(settlement=s, user=self.mgmt,
                                 recoveries={adv.pk: Decimal('100')})
        # fully recovered → drops out of the outstanding list
        self.assertEqual(outstanding_advances(self.w1), [])
        # reverse → advance restored everywhere, incl. the recovery UI source
        reverse_adda_settlement(settlement=s, user=self.mgmt)
        out = outstanding_advances(self.w1)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]['advance'].pk, adv.pk)
        self.assertEqual(out[0]['remaining'], Decimal('100'))

    def test_grouped_after_complete_preview_matches_finalize_zero(self):
        """PA-11-2: a stage grouped AFTER its workers completed has a stale non-zero
        frozen expected_rate. The settlement preview/queue must apply the grouped→0
        effective_pay_rate guard (mirror finalize), not the raw frozen rate."""
        from expense.services.adda_settlement_service import settlement_queue
        self._contribute(self.w1, self.sr_pay, 50)            # expected_rate frozen = 3
        self._close_stages()
        # Group the payable stage after completion (billed at the other stage).
        self.ws_pay.cost_billed_at = self.ws_free
        self.ws_pay.save(update_fields=['cost_billed_at'])
        # Queue preview must show 0 (grouped member pays at the payer), matching finalize.
        q = settlement_queue()
        row = next(r for r in q['ready'] if r['adda'].pk == self.adda.pk)
        self.assertEqual(row['expected'], Decimal('0.00'))
        # And finalize books 0 — preview now agrees with the money write.
        s = create_draft(adda=self.adda, user=self.mgmt)
        finalize_adda_settlement(settlement=s, user=self.mgmt)
        s.refresh_from_db()
        self.assertEqual(s.expected_total, Decimal('0.00'))
