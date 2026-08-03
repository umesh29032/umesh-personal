"""MEE-A (Phase 16) — the engine tables' DB-level laws, proven both ways.
Migration 0015 is ADDITIVE-ONLY; at MEE-A no service writer exists yet, so
tests exercise the constraints directly via the ORM (the purity test that
locks writes to the service family lands with the writers at MEE-B)."""

from datetime import date
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from django.utils import timezone

from accounts.models import User
from inventory.models import Role
from expense.models import (
    ExpenseGenerationRecord, ExpenseTemplate, ExpenseTemplateAmountAudit,
)
from expense.services import expense_service


def _sa(email='mee-sa@test'):
    u = User.objects.create_user(email=email, password='x', is_superuser=True)
    u.role = Role.objects.get(code='super_admin')
    u.save()
    return u


class _Base(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.sa = _sa()
        cls.worker = User.objects.create_user(email='mee-w@test', password='x')

    def _tpl(self, **over):
        kw = dict(label='Rent — Main', category='rent', amount=Decimal('1500'),
                  start_date=date(2026, 7, 1), created_by=self.sa)
        kw.update(over)
        return ExpenseTemplate.objects.create(**kw)


class TemplateConstraintTests(_Base):
    def test_amount_floor(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            self._tpl(amount=Decimal('0'))

    def test_salary_requires_worker_both_directions(self):
        # salary without worker → refused at the DB
        with self.assertRaises(IntegrityError), transaction.atomic():
            self._tpl(label='Sal', category='salary', worker=None)
        # non-salary WITH worker → refused at the DB (biconditional)
        with self.assertRaises(IntegrityError), transaction.atomic():
            self._tpl(worker=self.worker)
        # both legal shapes pass
        self._tpl()
        self._tpl(label='Sal', category='salary', worker=self.worker,
                  amount=Decimal('9000'))

    def test_end_date_not_before_start(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            self._tpl(end_date=date(2026, 6, 30))
        self._tpl(end_date=date(2026, 7, 31))   # same-month end is legal

    def test_one_active_salary_template_per_worker(self):
        self._tpl(label='S1', category='salary', worker=self.worker,
                  amount=Decimal('9000'))
        with self.assertRaises(IntegrityError), transaction.atomic():
            self._tpl(label='S2', category='salary', worker=self.worker,
                      amount=Decimal('9500'))
        # deactivate the first → a new active one is legal (soft-state flow)
        ExpenseTemplate.objects.filter(label='S1').update(is_active=False)
        self._tpl(label='S2', category='salary', worker=self.worker,
                  amount=Decimal('9500'))

    def test_active_manager_soft_state(self):
        t = self._tpl()
        self._tpl(label='Old rent', is_active=False)
        self.assertEqual(list(ExpenseTemplate.active.all()), [t])
        self.assertEqual(ExpenseTemplate.objects.count(), 2)

    def test_template_protected_against_user_delete(self):
        self._tpl()
        with self.assertRaises(ProtectedError):
            self.sa.delete()


class GenerationRecordConstraintTests(_Base):
    def _expense(self):
        # THE certified writer even in tests — no direct FactoryExpense ORM.
        return expense_service.record_expense(
            category='rent', amount=Decimal('1500'),
            expense_date=timezone.localtime().date(), actor=self.sa,
            notes='MEE-A constraint fixture')

    def _cover(self, tpl, expense, **over):
        kw = dict(template=tpl, period_key='2026-07', expense=expense,
                  generated_by=self.sa)
        kw.update(over)
        return ExpenseGenerationRecord.objects.create(**kw)

    def test_one_current_coverage_per_template_period(self):
        tpl = self._tpl()
        self._cover(tpl, self._expense())
        with self.assertRaises(IntegrityError), transaction.atomic():
            self._cover(tpl, self._expense())

    def test_superseded_row_frees_the_period(self):
        tpl = self._tpl()
        first = self._cover(tpl, self._expense())
        first.superseded_at = timezone.now()
        first.save(update_fields=['superseded_at'])
        second = self._cover(tpl, self._expense(), supersedes=first,
                             regeneration_reason='voided wrong amount')
        self.assertEqual(second.supersedes_id, first.pk)

    def test_regeneration_requires_reason(self):
        tpl = self._tpl()
        first = self._cover(tpl, self._expense())
        first.superseded_at = timezone.now()
        first.save(update_fields=['superseded_at'])
        with self.assertRaises(IntegrityError), transaction.atomic():
            self._cover(tpl, self._expense(), supersedes=first,
                        regeneration_reason='')

    def test_expense_one_to_one(self):
        tpl = self._tpl()
        e = self._expense()
        self._cover(tpl, e)
        tpl2 = self._tpl(label='Rent — Annex')
        with self.assertRaises(IntegrityError), transaction.atomic():
            self._cover(tpl2, e)   # one coverage row per generated money row


class AmountAuditConstraintTests(_Base):
    def _audit(self, **over):
        kw = dict(template=self._tpl(), old_amount=Decimal('1500'),
                  new_amount=Decimal('1800'), changed_by=self.sa,
                  reason='rent revised by landlord')
        kw.update(over)
        return ExpenseTemplateAmountAudit.objects.create(**kw)

    def test_reason_required(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            self._audit(reason='')

    def test_amounts_must_differ(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            self._audit(new_amount=Decimal('1500'))

    def test_amounts_positive(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            self._audit(old_amount=Decimal('0'))

    def test_valid_audit_row(self):
        row = self._audit()
        self.assertEqual((row.old_amount, row.new_amount),
                         (Decimal('1500'), Decimal('1800')))
