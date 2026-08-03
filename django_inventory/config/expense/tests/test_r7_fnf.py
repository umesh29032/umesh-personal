"""R7 (roadmap phase) tests — Full & Final settlement (PDD §20/§27-D5/§31.2).

Pins: only_worker scoping (colleagues untouched, era guards both directions,
mixed settled/unsettled lines on ONE stage record) · audited advance write-off
(PSI row, no ledger debit, super-admin + reason, reversible) · fnf preconditions
(open tasks / draft-gate refusals) · full F&F receipt (settle → pay → write off
→ deactivate) · ADR-0011 monthly F&F = ZERO earning lines · reopen armor after
partial settlement.
"""
from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase
from django.utils import timezone

from accounts.models import User
from inventory.models import Role
from expense.models import (
    AddaSettlement, PayrollSettlementItem, WorkerAdvance, WorkerLedgerEntry,
    WorkerProfile,
)
from expense.services.adda_settlement_service import (
    create_draft, finalize_adda_settlement, preview_lines,
)
from expense.services.advance_service import record_advance
from expense.services.fnf_service import fnf_execute, fnf_preview
from expense.services.ledger_service import worker_balance
from expense.services.payroll_service import advance_outstanding
from expense.services.settlement_service import create_settlement
from production.models import (
    Adda, AddaStageRecord, Product, Stage, WorkflowStage,
)
from production.services.worker_task_service import (
    complete_worker_task, report_contributions, set_stage_workers,
)


def _role_user(email, role_code, **extra):
    u = User.objects.create_user(email=email, password='x', **extra)
    u.role = Role.objects.get(code=role_code)
    u.save()
    return u


class _Base(TestCase):
    def setUp(self):
        self.sa = _role_user('r7-sa@test', 'super_admin',
                             is_superuser=True, is_staff=True)
        self.mgmt = _role_user('r7-mgmt@test', 'manager')
        self.leaver = _role_user('r7-leaver@test', 'worker')
        self.stayer = _role_user('r7-stayer@test', 'worker')
        self.product = Product.objects.create(code='R7F', name='R7 FnF P')
        self._stage_n = 0

    def _adda(self, code, *, contributions, complete_stage=True):
        """One payable stage (₹5/pc); contributions = [(worker, qty), …]."""
        self._stage_n += 1
        st, _ = Stage.objects.get_or_create(
            code=f'r7f_st{self._stage_n}', defaults={'name': f'R7F S{self._stage_n}'})
        ws = WorkflowStage.objects.create(
            product=self.product, stage=st, order=self._stage_n,
            cost_rate=Decimal('5'), credits_workers=True)
        adda = Adda.objects.create(code=code, product=self.product)
        sr = AddaStageRecord.objects.create(
            adda=adda, workflow_stage=ws, started_at=timezone.now())
        set_stage_workers(sr, [w.pk for w, _ in contributions])
        for w, q in contributions:
            t = sr.worker_tasks.get(worker=w)
            report_contributions(t, [{'reported_quantity': str(q)}], actor=w)
            complete_worker_task(t, actor=w)
        if complete_stage:
            sr.completed_at = timezone.now()
            sr.save(update_fields=['completed_at'])
        return adda, sr


class OnlyWorkerScopingTests(_Base):
    def test_scoped_finalize_leaves_colleague_settleable(self):
        adda, sr = self._adda('R7F-001', contributions=[(self.leaver, 10),
                                                        (self.stayer, 20)])
        s1 = create_draft(adda=adda, user=self.mgmt)
        finalize_adda_settlement(settlement=s1, user=self.mgmt,
                                 only_worker=self.leaver)
        self.assertEqual(worker_balance(self.leaver), Decimal('50.00'))
        self.assertEqual(worker_balance(self.stayer), Decimal('0.00'))
        # Mixed state on ONE stage record: leaver settled, stayer settleable.
        s2 = create_draft(adda=adda, user=self.mgmt)
        lines, _, skb, _ = preview_lines(s2)
        self.assertEqual([c.task.worker_id for c in lines], [self.stayer.pk])
        self.assertEqual([c.task.worker_id for c in skb], [self.leaver.pk])
        # Era guard both directions: second scoped finalize refuses (nothing).
        with self.assertRaises(ValidationError):
            finalize_adda_settlement(settlement=s2, user=self.mgmt,
                                     only_worker=self.leaver)
        # Colleague settles normally afterwards — exactly once.
        finalize_adda_settlement(settlement=s2, user=self.mgmt)
        self.assertEqual(worker_balance(self.stayer), Decimal('100.00'))
        self.assertEqual(WorkerLedgerEntry.objects.filter(
            worker=self.leaver, entry_type='credit').count(), 1)

    def test_reopen_armor_engages_on_partial_and_releases_on_reverse(self):
        from production.services._shared import reopen_stage_record
        from expense.services.adda_settlement_service import reverse_adda_settlement
        adda, sr = self._adda('R7F-002', contributions=[(self.leaver, 10),
                                                        (self.stayer, 20)])
        s1 = create_draft(adda=adda, user=self.mgmt)
        finalize_adda_settlement(settlement=s1, user=self.mgmt,
                                 only_worker=self.leaver)
        stage_code = sr.workflow_stage.stage.code
        with self.assertRaisesMessage(ValidationError, 'settled by'):
            reopen_stage_record(adda=adda, stage_code=stage_code,
                                stage_label='R7F', user=self.mgmt)
        reverse_adda_settlement(settlement=s1, user=self.mgmt)
        reopen_stage_record(adda=adda, stage_code=stage_code,
                            stage_label='R7F', user=self.mgmt)  # no raise
        self.assertEqual(worker_balance(self.leaver), Decimal('0.00'))


class WriteOffTests(_Base):
    def test_write_off_audited_no_ledger_debit(self):
        adv = record_advance(user=self.mgmt, worker=self.leaver, amount='500')
        before_rows = WorkerLedgerEntry.objects.filter(worker=self.leaver).count()
        s = create_settlement(user=self.sa, worker=self.leaver,
                              amount_paid='0',
                              write_offs=[{'advance': adv, 'reason': 'left, unrecoverable'}])
        psi = PayrollSettlementItem.objects.get(settlement=s)
        self.assertEqual(psi.amount_recovered, Decimal('500'))
        self.assertEqual(psi.write_off_reason, 'left, unrecoverable')
        self.assertEqual(psi.written_off_by, self.sa)
        self.assertIsNone(psi.ledger_entry_id)
        self.assertEqual(advance_outstanding(self.leaver), Decimal('0'))
        # NO ledger movement — payable untouched by a forgiven loan.
        self.assertEqual(WorkerLedgerEntry.objects.filter(
            worker=self.leaver).count(), before_rows)
        # Reversal restores the outstanding (same stamp as any recovery).
        psi.reversed_at = timezone.now()
        psi.save(update_fields=['reversed_at'])
        self.assertEqual(advance_outstanding(self.leaver), Decimal('500'))

    def test_write_off_guards(self):
        adv = record_advance(user=self.mgmt, worker=self.leaver, amount='500')
        with self.assertRaises(PermissionDenied):        # manager refused
            create_settlement(user=self.mgmt, worker=self.leaver,
                              amount_paid='0',
                              write_offs=[{'advance': adv, 'reason': 'x'}])
        with self.assertRaises(ValidationError):          # empty reason
            create_settlement(user=self.sa, worker=self.leaver,
                              amount_paid='0',
                              write_offs=[{'advance': adv, 'reason': '  '}])
        other = record_advance(user=self.mgmt, worker=self.stayer, amount='100')
        with self.assertRaises(ValidationError):          # foreign advance
            create_settlement(user=self.sa, worker=self.leaver,
                              amount_paid='0',
                              write_offs=[{'advance': other, 'reason': 'x'}])
        self.assertEqual(PayrollSettlementItem.objects.count(), 0)


class FnFFlowTests(_Base):
    def test_preconditions_refuse_with_names(self):
        adda, sr = self._adda('R7F-010', contributions=[(self.leaver, 10)],
                              complete_stage=False)
        # open task on another adda (stage still OPEN — a completed stage
        # seeds re-added workers as 'completed', the 0032-parity behavior)
        adda2, sr2 = self._adda('R7F-011', contributions=[(self.stayer, 5)],
                                complete_stage=False)
        set_stage_workers(sr2, [self.stayer.pk, self.leaver.pk])
        with self.assertRaises(PermissionDenied):
            fnf_preview(self.leaver, user=self.mgmt)      # P-4: super-admin only
        pv = fnf_preview(self.leaver, user=self.sa)
        self.assertFalse(pv['ready'])
        with self.assertRaisesMessage(ValidationError, 'open task'):
            fnf_execute(self.leaver, user=self.sa)
        # resolve the open task (audited cancel via existing chokepoint)
        set_stage_workers(sr2, [self.stayer.pk])
        with self.assertRaisesMessage(ValidationError, 'not completed'):
            fnf_execute(self.leaver, user=self.sa)        # draft gate (P-5)

    def test_full_fnf_multi_adda_receipt(self):
        a1, _ = self._adda('R7F-020', contributions=[(self.leaver, 10),
                                                     (self.stayer, 20)])
        a2, _ = self._adda('R7F-021', contributions=[(self.leaver, 4)])
        record_advance(user=self.mgmt, worker=self.leaver, amount='30')
        receipt = fnf_execute(self.leaver, user=self.sa,
                              write_off_reason='exit — residual forgiven')
        self.assertEqual(len(receipt['settlements']), 2)
        # ₹50 + ₹20 earned; advance 30 written off (NOT recovered from payable);
        # full payable paid in cash → balance 0, outstanding 0, deactivated.
        self.assertEqual(receipt['paid'], Decimal('70.00'))
        self.assertEqual(worker_balance(self.leaver), Decimal('0.00'))
        self.assertEqual(advance_outstanding(self.leaver), Decimal('0'))
        self.leaver.refresh_from_db()
        self.assertFalse(self.leaver.is_active)
        # Colleague fully unaffected and still settleable.
        s = create_draft(adda=a1, user=self.mgmt)
        lines, _, _, _ = preview_lines(s)
        self.assertEqual([c.task.worker_id for c in lines], [self.stayer.pk])
        # Deactivated leaver can still be displayed/settled later (§31.2):
        # reverse of one settlement re-arms their line without any user gate.
        from expense.services.adda_settlement_service import reverse_adda_settlement
        s1 = AddaSettlement.objects.get(adda=a1,
                                        status=AddaSettlement.Status.FINALIZED)
        reverse_adda_settlement(settlement=s1, user=self.mgmt)
        self.assertEqual(worker_balance(self.leaver), Decimal('-50.00'))

    def test_monthly_fnf_zero_lines_adr_0011(self):
        monthly = _role_user('r7-monthly@test', 'worker')
        WorkerProfile.objects.create(user=monthly,
                                     pay_basis=WorkerProfile.PayBasis.MONTHLY)
        self._adda('R7F-030', contributions=[(monthly, 25), (self.stayer, 5)])
        # Legacy advance (pre-M-2 block simulation): create directly.
        adv = WorkerAdvance.objects.create(worker=monthly, amount=Decimal('200'),
                                           advance_date=timezone.now().date(),
                                           entered_by=self.mgmt)
        receipt = fnf_execute(monthly, user=self.sa,
                              write_off_reason='monthly exit')
        self.assertEqual(receipt['settlements'], [])      # ZERO earning lines
        self.assertEqual(receipt['paid'], Decimal('0.00'))
        self.assertEqual(WorkerLedgerEntry.objects.filter(
            worker=monthly).count(), 0)
        self.assertEqual(advance_outstanding(monthly), Decimal('0'))
        self.assertEqual(PayrollSettlementItem.objects.filter(
            advance=adv).get().write_off_reason, 'monthly exit')
        monthly.refresh_from_db()
        self.assertFalse(monthly.is_active)
        # Colleague's line untouched by the monthly F&F.
        self.assertEqual(worker_balance(self.stayer), Decimal('0.00'))

    def test_fnf_zero_payable_with_advance(self):
        """PDD edge case: nothing earned, advance outstanding — write-off-only."""
        record_advance(user=self.mgmt, worker=self.leaver, amount='150')
        receipt = fnf_execute(self.leaver, user=self.sa,
                              write_off_reason='no work recorded, exited')
        self.assertEqual(receipt['settlements'], [])
        self.assertEqual(receipt['paid'], Decimal('0.00'))
        self.assertEqual(advance_outstanding(self.leaver), Decimal('0'))
        self.leaver.refresh_from_db()
        self.assertFalse(self.leaver.is_active)

    def test_fnf_requires_write_off_reason_when_advances_exist(self):
        record_advance(user=self.mgmt, worker=self.leaver, amount='150')
        with self.assertRaisesMessage(ValidationError, 'reason is required'):
            fnf_execute(self.leaver, user=self.sa)
        self.leaver.refresh_from_db()
        self.assertTrue(self.leaver.is_active)            # nothing happened
