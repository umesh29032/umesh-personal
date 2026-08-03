"""Hostile-review fixes (owner decisions 2026-07-05, R5_HOSTILE_REVIEW doc).

H-1: ADR-0011 holds REGARDLESS of feature flags — the era-A allocation path
     refuses monthly workers even with LEDGER_CREDIT_AT_ALLOCATION=True.
M-2: TEMPORARY rule — advances blocked for monthly workers (no recovery path).
M-3: duplicate salary (worker+month) = warn-and-confirm, server-enforced.
M-4: Payroll Overview always shows monthly workers, badged, without Settle.
"""
from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.utils import timezone

from accounts.models import User
from inventory.models import Role
from expense.models import (
    FactoryExpense, WorkerAdvance, WorkerLedgerEntry, WorkerProfile,
)
from expense.services.advance_service import record_advance
from expense.services.allocation_service import allocate_stage_work
from expense.services.expense_service import record_expense, void_expense
from production.models import Adda, AddaStageRecord, Product, Stage, WorkflowStage


def _role_user(email, role_code, **extra):
    u = User.objects.create_user(email=email, password='x', **extra)
    u.role = Role.objects.get(code=role_code)
    u.save()
    return u


class _Base(TestCase):
    def setUp(self):
        self.super_admin = _role_user('hf-sa@test', 'super_admin',
                                      is_superuser=True, is_staff=True)
        self.mgmt = _role_user('hf-mgmt@test', 'manager')
        self.w_piece = _role_user('hf-wp@test', 'worker')
        self.w_monthly = _role_user('hf-wm@test', 'worker')
        WorkerProfile.objects.create(user=self.w_monthly,
                                     pay_basis=WorkerProfile.PayBasis.MONTHLY)
        product = Product.objects.create(code='HFX', name='HF P')
        stage, _ = Stage.objects.get_or_create(
            code='hfx_stage', defaults={'name': 'HFX Stage'})
        ws = WorkflowStage.objects.create(
            product=product, stage=stage, order=1,
            cost_rate=Decimal('5'), credits_workers=True)
        adda = Adda.objects.create(code='HFX-001', product=product)
        self.sr = AddaStageRecord.objects.create(
            adda=adda, workflow_stage=ws, started_at=timezone.now())


class H1EraALeverGuardTests(_Base):
    """ADR-0011 must hold even under the ADR-0007 rollback lever."""

    @override_settings(LEDGER_CREDIT_AT_ALLOCATION=True)
    def test_lever_on_monthly_refused_zero_money(self):
        with self.assertRaisesMessage(ValidationError, 'monthly salary'):
            allocate_stage_work(user=self.mgmt, stage_record=self.sr,
                                worker=self.w_monthly, allocated_quantity=5)
        self.assertEqual(
            WorkerLedgerEntry.objects.filter(worker=self.w_monthly).count(), 0)

    @override_settings(LEDGER_CREDIT_AT_ALLOCATION=True)
    def test_lever_on_piece_rate_still_works(self):
        # The guard is monthly-scoped — the lever path itself stays intact.
        a = allocate_stage_work(user=self.mgmt, stage_record=self.sr,
                                worker=self.w_piece, allocated_quantity=4)
        self.assertEqual(a.earning_amount_snapshot, Decimal('20.00'))
        self.assertEqual(
            WorkerLedgerEntry.objects.filter(worker=self.w_piece).count(), 1)

    def test_lever_off_monthly_gets_the_adr_0011_message(self):
        # Guard runs BEFORE the lever check: the refusal names the real rule,
        # not the flag — the invariant is basis-driven, not flag-driven.
        with self.assertRaisesMessage(ValidationError, 'monthly salary'):
            allocate_stage_work(user=self.mgmt, stage_record=self.sr,
                                worker=self.w_monthly, allocated_quantity=5)


class M2AdvanceBlockTests(_Base):
    def test_monthly_advance_refused_piece_rate_ok(self):
        with self.assertRaisesMessage(ValidationError, 'monthly-salary'):
            record_advance(user=self.mgmt, worker=self.w_monthly, amount='500')
        self.assertEqual(
            WorkerAdvance.objects.filter(worker=self.w_monthly).count(), 0)
        record_advance(user=self.mgmt, worker=self.w_piece, amount='500')
        self.assertEqual(
            WorkerAdvance.objects.filter(worker=self.w_piece).count(), 1)


class M3DuplicateSalaryTests(_Base):
    def _salary(self, d, **kw):
        return record_expense(category='salary', amount='9000',
                              expense_date=d, actor=self.mgmt,
                              worker=self.w_monthly, **kw)

    def test_same_month_requires_confirmation(self):
        self._salary(date(2026, 7, 5))
        with self.assertRaises(ValidationError) as ctx:
            self._salary(date(2026, 7, 28))
        self.assertEqual(ctx.exception.code, 'duplicate_salary')
        self.assertEqual(FactoryExpense.objects.count(), 1)
        # Explicit confirmation → allowed (components/corrections legitimate).
        self._salary(date(2026, 7, 28), confirmed_duplicate=True)
        self.assertEqual(FactoryExpense.objects.count(), 2)

    def test_other_month_and_voided_do_not_warn(self):
        e = self._salary(date(2026, 6, 30))
        self._salary(date(2026, 7, 5))                     # other month — free
        void_expense(FactoryExpense.objects.get(expense_date=date(2026, 7, 5)),
                     actor=self.super_admin, reason='redo')
        self._salary(date(2026, 7, 6))                     # voided ⇒ no warn
        self.assertEqual(e.voided_at, None)

    def test_view_rerenders_with_confirm_checkbox(self):
        self._salary(date(2026, 7, 5))
        self.client.force_login(self.mgmt)
        resp = self.client.post('/expense/expenses/add/', {
            'category': 'salary', 'amount': '9000',
            'expense_date': '2026-07-28', 'worker': self.w_monthly.pk,
        })
        self.assertContains(resp, 'confirm_duplicate')     # checkbox appears
        self.assertEqual(FactoryExpense.objects.count(), 1)
        resp = self.client.post('/expense/expenses/add/', {
            'category': 'salary', 'amount': '9000',
            'expense_date': '2026-07-28', 'worker': self.w_monthly.pk,
            'confirm_duplicate': '1',
        }, follow=True)
        self.assertContains(resp, 'Expense recorded')
        self.assertEqual(FactoryExpense.objects.count(), 2)


class M4OverviewVisibilityTests(_Base):
    def test_monthly_worker_listed_badged_without_settle(self):
        self.client.force_login(self.mgmt)
        html = self.client.get('/expense/payroll/').content.decode()
        self.assertIn(self.w_monthly.email, html)          # visible with 0 money
        row = html[html.index(self.w_monthly.email):][:1500]
        self.assertIn('badge-monthly', row)
        self.assertIn('Salary →', row)
        self.assertNotIn('>Settle<', row)