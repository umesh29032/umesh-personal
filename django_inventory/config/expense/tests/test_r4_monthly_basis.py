"""R4 (roadmap phase) tests — MONTHLY pay basis (PDD §17 + §27-D4).

Owner-locked semantics under test:
  • pay basis = property of the WORKER (WorkerProfile.pay_basis), never the
    stage; absent profile = piece_rate (get_or_create default, no backfill).
  • Monthly workers' contributions are STRUCTURALLY excluded from settlement
    lines at the one funnel (_settleable_lines) — double-pay (salary +
    settlement) is impossible by construction (PDD §29 risk 4).
  • Basis is read at SETTLEMENT time (owner P-1) — switching back to
    piece-rate makes uncredited lines settleable again.
  • set_pay_basis: super-admin only (P-2), append-only WorkerPayBasisAudit
    (P-3), explicit confirmation required when unsettled lines exist (owner
    R4 addendum — warning, not a hard block).
  • Presentation (P-4): monthly worker keeps quantities, loses the ₹
    expectation ENTIRELY (never ₹0.00) + Monthly Salary badge.
"""
from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase
from django.utils import timezone

from accounts.models import User
from inventory.models import Role
from expense.models import (
    AddaSettlementItem, WorkerLedgerEntry, WorkerPayBasisAudit,
    WorkerProfile,
)
from expense.services.adda_settlement_service import (
    create_draft, finalize_adda_settlement, preview_lines, settlement_queue,
)
from expense.services.payroll_service import (
    is_monthly, set_pay_basis, unsettled_contribution_count,
)
from production.models import (
    Adda, AddaStageRecord, Product, Stage, WorkflowStage, WorkerStageTask,
    WorkerStageContribution,
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
    """One payable stage (₹3/pc); w_piece stays default, w_monthly is MONTHLY."""

    def setUp(self):
        self.super_admin = _role_user('r4-sa@test', 'super_admin',
                                      is_superuser=True, is_staff=True)
        self.mgmt = _role_user('r4-mgmt@test', 'manager')
        self.w_piece = _role_user('r4-wp@test', 'worker')
        self.w_monthly = _role_user('r4-wm@test', 'worker')
        WorkerProfile.objects.create(user=self.w_monthly,
                                     pay_basis=WorkerProfile.PayBasis.MONTHLY)
        self.product = Product.objects.create(code='R4M', name='R4 Monthly P')
        stage, _ = Stage.objects.get_or_create(
            code='r4m_cutting', defaults={'name': 'R4M Cutting'})
        self.ws = WorkflowStage.objects.create(
            product=self.product, stage=stage, order=1,
            cost_rate=Decimal('3'), credits_workers=True)
        self.adda = Adda.objects.create(code='R4M-001', product=self.product)
        self.sr = AddaStageRecord.objects.create(
            adda=self.adda, workflow_stage=self.ws, started_at=timezone.now())

    def _contribute(self, worker, qty):
        keep = {worker} | {t.worker for t in self.sr.worker_tasks.exclude(
            status=WorkerStageTask.Status.CANCELLED)}
        set_stage_workers(self.sr, [w.pk for w in keep])
        task = WorkerStageTask.objects.get(
            stage_record=self.sr, worker=worker,
            status__in=('assigned', 'in_progress'))
        report_contributions(task, [{'reported_quantity': str(qty)}],
                             actor=worker)
        complete_worker_task(task, actor=worker)
        return task

    def _draft(self):
        if self.sr.completed_at is None:
            self.sr.completed_at = timezone.now()
            self.sr.save(update_fields=['completed_at'])
        return create_draft(adda=self.adda, user=self.mgmt)

    def _credits(self, worker):
        return WorkerLedgerEntry.objects.filter(
            worker=worker, entry_type='credit', category='stage_earning')


class StructuralExclusionTests(_Base):
    """The roadmap exit test: double-pay impossibility."""

    def test_monthly_excluded_piece_rate_colleague_pays(self):
        self._contribute(self.w_piece, 50)
        self._contribute(self.w_monthly, 30)
        s = self._draft()
        lines, skip_a, skip_b, skip_monthly = preview_lines(s)
        self.assertEqual({c.task.worker_id for c in lines}, {self.w_piece.pk})
        self.assertEqual({c.task.worker_id for c in skip_monthly},
                         {self.w_monthly.pk})
        finalize_adda_settlement(settlement=s, user=self.mgmt)
        # Piece-rate colleague on the SAME stage settles normally…
        self.assertEqual(self._credits(self.w_piece).count(), 1)
        self.assertEqual(
            AddaSettlementItem.objects.get(adda_settlement=s,
                                           worker=self.w_piece).final_payable,
            Decimal('150.00'))
        # …monthly worker: ZERO ledger rows, ZERO items, line never linked.
        self.assertEqual(self._credits(self.w_monthly).count(), 0)
        self.assertFalse(AddaSettlementItem.objects.filter(
            adda_settlement=s, worker=self.w_monthly).exists())
        c = WorkerStageContribution.objects.get(task__worker=self.w_monthly)
        self.assertIsNone(c.settlement_line_id)

    def test_absent_profile_defaults_to_piece_rate(self):
        self.assertFalse(is_monthly(self.w_piece))       # no profile at all
        self._contribute(self.w_piece, 10)
        s = self._draft()
        lines, _, _, skip_monthly = preview_lines(s)
        self.assertEqual(len(lines), 1)
        self.assertEqual(skip_monthly, [])

    def test_monthly_only_adda_nothing_to_settle(self):
        self._contribute(self.w_monthly, 30)
        s = self._draft()
        with self.assertRaisesMessage(ValidationError, 'monthly'):
            finalize_adda_settlement(settlement=s, user=self.mgmt)
        # Queue: not offered as ready (no settleable lines).
        ready_addas = [r['adda'].pk for r in settlement_queue()['ready']]
        self.assertNotIn(self.adda.pk, ready_addas)

    def test_queue_labels_monthly_skips_on_mixed_adda(self):
        self._contribute(self.w_piece, 50)
        self._contribute(self.w_monthly, 30)
        self.sr.completed_at = timezone.now()
        self.sr.save(update_fields=['completed_at'])
        row = next(r for r in settlement_queue()['ready']
                   if r['adda'].pk == self.adda.pk)
        self.assertEqual(row['skipped_monthly'], 1)
        self.assertEqual(row['workers'], 1)              # piece-rate only
        self.assertEqual(row['expected'], Decimal('150.00'))

    def test_switch_semantics_settlement_time_read(self):
        """P-1 pin: basis is read at settlement time, both directions."""
        self._contribute(self.w_monthly, 30)
        s = self._draft()
        self.assertEqual(len(preview_lines(s)[3]), 1)    # monthly → excluded
        # monthly → piece_rate: prior lines become payable (visible in draft).
        set_pay_basis(self.w_monthly, WorkerProfile.PayBasis.PIECE_RATE,
                      actor=self.super_admin, confirmed=True)
        lines, _, _, skip_monthly = preview_lines(s)
        self.assertEqual(len(lines), 1)
        self.assertEqual(skip_monthly, [])
        # …and back: excluded again. Settlement-time read, no snapshot.
        set_pay_basis(self.w_monthly, WorkerProfile.PayBasis.MONTHLY,
                      actor=self.super_admin, confirmed=True)
        self.assertEqual(len(preview_lines(s)[3]), 1)


class SetPayBasisTests(_Base):
    def test_super_admin_change_writes_audit(self):
        profile = set_pay_basis(self.w_piece, WorkerProfile.PayBasis.MONTHLY,
                                actor=self.super_admin)
        self.assertEqual(profile.pay_basis, WorkerProfile.PayBasis.MONTHLY)
        self.assertTrue(is_monthly(self.w_piece))
        audit = WorkerPayBasisAudit.objects.get(worker=self.w_piece)
        self.assertEqual(audit.old_basis, WorkerProfile.PayBasis.PIECE_RATE)
        self.assertEqual(audit.new_basis, WorkerProfile.PayBasis.MONTHLY)
        self.assertEqual(audit.changed_by, self.super_admin)
        self.assertEqual(audit.unsettled_lines_at_change, 0)

    def test_manager_denied_nothing_written(self):
        with self.assertRaises(PermissionDenied):
            set_pay_basis(self.w_piece, WorkerProfile.PayBasis.MONTHLY,
                          actor=self.mgmt)
        self.assertFalse(is_monthly(self.w_piece))
        self.assertEqual(WorkerPayBasisAudit.objects.count(), 0)

    def test_unsettled_lines_require_explicit_confirmation(self):
        self._contribute(self.w_piece, 20)
        self.assertEqual(unsettled_contribution_count(self.w_piece), 1)
        with self.assertRaisesMessage(ValidationError,
                                      '1 unsettled contribution line'):
            set_pay_basis(self.w_piece, WorkerProfile.PayBasis.MONTHLY,
                          actor=self.super_admin)          # confirmed=False
        self.assertFalse(is_monthly(self.w_piece))
        self.assertEqual(WorkerPayBasisAudit.objects.count(), 0)
        # Explicit confirmation → applied; audit records the confirmed-over count.
        set_pay_basis(self.w_piece, WorkerProfile.PayBasis.MONTHLY,
                      actor=self.super_admin, confirmed=True)
        self.assertTrue(is_monthly(self.w_piece))
        self.assertEqual(WorkerPayBasisAudit.objects.get(
            worker=self.w_piece).unsettled_lines_at_change, 1)

    def test_noop_and_invalid_refused(self):
        with self.assertRaises(ValidationError):
            set_pay_basis(self.w_monthly, WorkerProfile.PayBasis.MONTHLY,
                          actor=self.super_admin)          # already monthly
        with self.assertRaises(ValidationError):
            set_pay_basis(self.w_piece, 'weekly', actor=self.super_admin)
        self.assertEqual(WorkerPayBasisAudit.objects.count(), 0)


class PresentationTests(_Base):
    """P-4: quantities stay, ₹ expectation suppressed entirely + badge."""

    def setUp(self):
        super().setUp()
        self._contribute(self.w_piece, 50)     # expected ₹150 frozen
        self._contribute(self.w_monthly, 30)   # expected ₹90 frozen (analytics)

    def test_my_earnings_monthly_suppresses_expected(self):
        self.client.force_login(self.w_monthly)
        resp = self.client.get('/expense/my/')
        self.assertContains(resp, 'Monthly Salary')
        self.assertNotContains(resp, 'Expected (unsettled)')
        self.assertNotContains(resp, '90.00')            # the frozen ₹ never leaks

    def test_my_earnings_piece_rate_unchanged(self):
        self.client.force_login(self.w_piece)
        resp = self.client.get('/expense/my/')
        self.assertContains(resp, 'Expected (unsettled)')
        self.assertContains(resp, '150.00')
        self.assertNotContains(resp, 'Monthly Salary')

    def test_my_work_monthly_qty_without_rupees(self):
        self.client.force_login(self.w_monthly)
        resp = self.client.get(f'/production/addas/{self.adda.code}/')
        self.assertContains(resp, 'My Work on this Adda')
        self.assertContains(resp, 'Monthly Salary')
        self.assertContains(resp, '30')                  # own quantity stays
        self.assertNotContains(resp, 'Expected ₹')       # ₹ fully suppressed

    def test_settlement_draft_labels_monthly_exclusion(self):
        s = self._draft()
        self.client.force_login(self.mgmt)
        resp = self.client.get(f'/expense/settlements/{s.reference}/')
        self.assertContains(resp, 'Excluded — monthly-salary worker')
        self.assertContains(resp, self.w_monthly.email)


class PayBasisViewTests(_Base):
    def test_profile_page_control_gated_by_role(self):
        url = f'/expense/workers/{self.w_piece.pk}/profile/'
        self.client.force_login(self.super_admin)
        self.assertContains(self.client.get(url), 'Change Pay Basis')
        self.client.force_login(self.mgmt)
        resp = self.client.get(url)
        self.assertContains(resp, 'Only a Super Admin')
        self.assertNotContains(resp, 'Change Pay Basis')

    def test_post_change_super_admin_ok_manager_refused(self):
        url = f'/expense/workers/{self.w_piece.pk}/pay-basis/'
        # Manager: outer mixin lets management in, the SERVICE refuses (never
        # trust the form) — message shown, nothing changes.
        self.client.force_login(self.mgmt)
        self.client.post(url, {'pay_basis': 'monthly'}, follow=True)
        self.assertFalse(is_monthly(self.w_piece))
        self.client.force_login(self.super_admin)
        resp = self.client.post(url, {'pay_basis': 'monthly'}, follow=True)
        self.assertTrue(is_monthly(self.w_piece))
        self.assertContains(resp, 'Monthly Salary')

    def test_post_unsettled_needs_confirm_checkbox(self):
        self._contribute(self.w_piece, 20)
        url = f'/expense/workers/{self.w_piece.pk}/pay-basis/'
        self.client.force_login(self.super_admin)
        resp = self.client.post(url, {'pay_basis': 'monthly'}, follow=True)
        self.assertFalse(is_monthly(self.w_piece))
        self.assertContains(resp, 'unsettled contribution line')
        resp = self.client.post(url, {'pay_basis': 'monthly',
                                      'confirm_unsettled': '1'}, follow=True)
        self.assertTrue(is_monthly(self.w_piece))
