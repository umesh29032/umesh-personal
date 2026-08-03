"""R5 (roadmap phase) tests — FactoryExpense (PDD §21 + ADR-0011).

Locked semantics under test:
  • append-only: create/void with mandatory audited reason — NO edit path.
  • category set PDD-locked (rent|electricity|salary|other); amount>0 at the DB.
  • P-1: salary REQUIRES a worker (audit-only link); other categories refuse one.
  • P-2: management creates; ONLY super-admin voids.
  • ADR-0011: factory-level — recording/voiding expenses writes ZERO ledger
    rows and never touches settlement/costing.
  • monthly_totals: non-voided, calendar-month bucket, derived live.
"""
from datetime import date
from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from accounts.models import User
from inventory.models import Role
from expense.models import FactoryExpense, WorkerLedgerEntry
from expense.services.expense_service import (
    monthly_totals, record_expense, void_expense,
)


def _role_user(email, role_code, **extra):
    u = User.objects.create_user(email=email, password='x', **extra)
    u.role = Role.objects.get(code=role_code)
    u.save()
    return u


class _Base(TestCase):
    def setUp(self):
        self.super_admin = _role_user('r5-sa@test', 'super_admin',
                                      is_superuser=True, is_staff=True)
        self.mgmt = _role_user('r5-mgmt@test', 'manager')
        self.worker = _role_user('r5-w@test', 'worker')

    def _rent(self, amount='5000', d=date(2026, 7, 1), actor=None):
        return record_expense(category='rent', amount=amount, expense_date=d,
                              actor=actor or self.mgmt)


class RecordExpenseTests(_Base):
    def test_manager_records_all_fields_stamped(self):
        e = self._rent()
        self.assertEqual(e.amount, Decimal('5000'))
        self.assertEqual(e.entered_by, self.mgmt)
        self.assertIsNone(e.voided_at)

    def test_worker_denied(self):
        with self.assertRaises(PermissionDenied):
            self._rent(actor=self.worker)
        self.assertEqual(FactoryExpense.objects.count(), 0)

    def test_amount_and_category_guards(self):
        for bad in ('0', '-5', 'abc'):
            with self.assertRaises(ValidationError):
                self._rent(amount=bad)
        with self.assertRaises(ValidationError):
            record_expense(category='fuel', amount='10',
                           expense_date=date(2026, 7, 1), actor=self.mgmt)
        with self.assertRaises(ValidationError):
            record_expense(category='rent', amount='10', expense_date=None,
                           actor=self.mgmt)

    def test_db_constraint_amount_positive(self):
        # Even a bypassed service can't write a non-positive amount.
        with self.assertRaises(IntegrityError), transaction.atomic():
            FactoryExpense.objects.create(
                category='rent', amount=Decimal('0'),
                expense_date=date(2026, 7, 1), entered_by=self.mgmt)

    def test_salary_requires_worker_others_refuse_one(self):
        with self.assertRaisesMessage(ValidationError, 'salary'):
            record_expense(category='salary', amount='9000',
                           expense_date=date(2026, 7, 1), actor=self.mgmt)
        e = record_expense(category='salary', amount='9000',
                           expense_date=date(2026, 7, 1), actor=self.mgmt,
                           worker=self.worker)
        self.assertEqual(e.worker, self.worker)
        with self.assertRaises(ValidationError):
            record_expense(category='rent', amount='10',
                           expense_date=date(2026, 7, 1), actor=self.mgmt,
                           worker=self.worker)


class VoidExpenseTests(_Base):
    def test_super_admin_void_with_reason(self):
        e = self._rent()
        void_expense(e, actor=self.super_admin, reason='entered twice')
        e.refresh_from_db()
        self.assertIsNotNone(e.voided_at)
        self.assertEqual(e.voided_by, self.super_admin)
        self.assertEqual(e.void_reason, 'entered twice')

    def test_manager_cannot_void(self):
        e = self._rent()
        with self.assertRaises(PermissionDenied):
            void_expense(e, actor=self.mgmt, reason='x')
        e.refresh_from_db()
        self.assertIsNone(e.voided_at)

    def test_empty_reason_and_double_void_refused(self):
        e = self._rent()
        with self.assertRaises(ValidationError):
            void_expense(e, actor=self.super_admin, reason='  ')
        void_expense(e, actor=self.super_admin, reason='dup')
        with self.assertRaisesMessage(ValidationError, 'already voided'):
            void_expense(e, actor=self.super_admin, reason='again')

    def test_no_edit_path_exists(self):
        # The append-only posture is an API surface fact: the service module
        # exposes record/void/totals and nothing that mutates fields.
        from expense.services import expense_service as mod
        public = {n for n in dir(mod) if not n.startswith('_') and callable(getattr(mod, n))}
        self.assertNotIn('edit_expense', public)
        self.assertNotIn('update_expense', public)


class MonthlyTotalsTests(_Base):
    def test_bucketing_and_void_exclusion(self):
        self._rent(amount='5000', d=date(2026, 7, 1))
        record_expense(category='electricity', amount='1200',
                       expense_date=date(2026, 7, 15), actor=self.mgmt)
        record_expense(category='salary', amount='9000',
                       expense_date=date(2026, 7, 20), actor=self.mgmt,
                       worker=self.worker)
        other_month = self._rent(amount='7777', d=date(2026, 6, 30))
        voided = self._rent(amount='999', d=date(2026, 7, 2))
        void_expense(voided, actor=self.super_admin, reason='mistake')

        t = monthly_totals(2026, 7)
        self.assertEqual(t['total'], Decimal('15200'))
        self.assertEqual(t['count'], 3)
        self.assertEqual(t['by_category']['rent']['total'], Decimal('5000'))
        self.assertEqual(t['by_category']['salary']['total'], Decimal('9000'))
        self.assertNotIn('other', t['by_category'])
        self.assertEqual(monthly_totals(2026, 6)['total'], Decimal('7777'))
        self.assertEqual(other_month.voided_at, None)

    def test_adr_0011_zero_ledger_interaction(self):
        """Recording + voiding expenses (incl. salary) writes NO ledger rows."""
        before = WorkerLedgerEntry.objects.count()
        e = record_expense(category='salary', amount='9000',
                           expense_date=date(2026, 7, 20), actor=self.mgmt,
                           worker=self.worker)
        void_expense(e, actor=self.super_admin, reason='test')
        self.assertEqual(WorkerLedgerEntry.objects.count(), before)


class ExpenseViewTests(_Base):
    LIST = '/expense/expenses/'
    ADD = '/expense/expenses/add/'

    def test_worker_blocked_everywhere(self):
        self.client.force_login(self.worker)
        self.assertEqual(self.client.get(self.LIST).status_code, 403)
        self.assertEqual(self.client.get(self.ADD).status_code, 403)

    def test_manager_creates_via_form(self):
        self.client.force_login(self.mgmt)
        resp = self.client.post(self.ADD, {
            'category': 'electricity', 'amount': '1500',
            'expense_date': '2026-07-10', 'notes': 'july bill',
        }, follow=True)
        self.assertContains(resp, 'Expense recorded')
        e = FactoryExpense.objects.get()
        self.assertEqual(e.category, 'electricity')

    def test_list_shows_totals_and_void_gated(self):
        self._rent(amount='5000', d=date(2026, 7, 1))
        self.client.force_login(self.mgmt)
        resp = self.client.get(self.LIST + '?month=2026-07')
        self.assertContains(resp, '5000')
        self.assertNotContains(resp, 'Confirm void')     # manager: no void UI
        self.client.force_login(self.super_admin)
        self.assertContains(self.client.get(self.LIST + '?month=2026-07'),
                            'Confirm void')

    def test_manager_void_post_refused_super_admin_ok(self):
        e = self._rent()
        self.client.force_login(self.mgmt)
        self.client.post(self.LIST, {'expense_id': e.pk, 'void_reason': 'x',
                                     'month': '2026-07'})
        e.refresh_from_db()
        self.assertIsNone(e.voided_at)                   # service refused
        self.client.force_login(self.super_admin)
        self.client.post(self.LIST, {'expense_id': e.pk,
                                     'void_reason': 'wrong amount',
                                     'month': '2026-07'})
        e.refresh_from_db()
        self.assertIsNotNone(e.voided_at)

    def test_garbage_month_param_never_500(self):
        self.client.force_login(self.mgmt)
        for junk in ('zzz', '2026-99', '20-1', ''):
            self.assertEqual(
                self.client.get(self.LIST, {'month': junk}).status_code, 200)


class DashboardPanelTests(_Base):
    def test_panel_management_only(self):
        record_expense(category='rent', amount='5000',
                       expense_date=timezone.now().date(), actor=self.mgmt)
        self.client.force_login(self.mgmt)
        self.assertContains(self.client.get('/inventory/my-dashboard/'),
                            'Expenses ·')
        self.client.force_login(self.worker)
        resp = self.client.get('/inventory/my-dashboard/')
        self.assertNotContains(resp, 'Expenses ·')
