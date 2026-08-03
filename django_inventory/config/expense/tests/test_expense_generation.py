"""MEE-B (Phase 16) — the engine writers, proven per the §B.0 owner-approved
package: idempotency (0-write re-runs) · void→regenerate supersession · M-3
collision BOTH directions · Q13 worker-inactive auto-stop · whole-period
rollback on real failure · concurrent-duplicate serialization · the B.0.6
amount timeline · the purity pin · ADR-0011 proof set v1."""

import re
from datetime import date
from decimal import Decimal
from pathlib import Path

import unittest.mock as mock

from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Sum
from django.test import TestCase
from django.utils import timezone

from accounts.models import User
from inventory.models import Role
from expense.models import (
    ExpenseGenerationRecord, ExpenseTemplate, ExpenseTemplateAmountAudit,
    FactoryExpense, WorkerLedgerEntry,
)
from expense.services import expense_service
from expense.services.expense_service import (
    change_template_amount, create_expense_template,
    deactivate_expense_template, generate_monthly_expenses, record_expense,
    regenerate_period, void_expense,
)


def _user(email, code, super_=False):
    u = User.objects.create_user(email=email, password='x', is_superuser=super_)
    u.role = Role.objects.get(code=code)
    u.save()
    return u


class _Base(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.sa = _user('gen-sa@test', 'super_admin', super_=True)
        cls.mgr = _user('gen-mgr@test', 'manager')
        cls.worker = User.objects.create_user(email='gen-w@test', password='x')

    def _rent(self, amount='1500', **over):
        kw = dict(label='Rent — Main', category='rent',
                  amount=Decimal(amount), start_date=date(2026, 7, 1),
                  actor=self.sa)
        kw.update(over)
        return create_expense_template(**kw)

    def _salary(self, **over):
        kw = dict(label='Salary — W', category='salary',
                  amount=Decimal('9000'), start_date=date(2026, 7, 1),
                  worker=self.worker, actor=self.sa)
        kw.update(over)
        return create_expense_template(**kw)

    def _counts(self):
        return (FactoryExpense.objects.count(),
                ExpenseGenerationRecord.objects.count(),
                WorkerLedgerEntry.objects.count())


class TemplateLifecycleTests(_Base):
    def test_sa_only_gates(self):
        for fn in (lambda: self._rent(actor=self.mgr),
                   lambda: deactivate_expense_template(self._rent(), actor=self.mgr),
                   lambda: change_template_amount(self._rent(label='R2'),
                                                  new_amount=Decimal('2'),
                                                  reason='x', actor=self.mgr)):
            with self.assertRaises(PermissionDenied):
                fn()

    def test_create_validations(self):
        with self.assertRaises(ValidationError):
            self._rent(amount='0')
        with self.assertRaises(ValidationError):
            self._rent(category='salary', worker=None)   # P-1
        with self.assertRaises(ValidationError):
            self._rent(worker=self.worker)               # non-salary w/ worker
        with self.assertRaises(ValidationError):
            self._rent(end_date=date(2026, 6, 1))
        inactive = User.objects.create_user(email='gen-in@test', password='x',
                                            is_active=False)
        with self.assertRaises(ValidationError):
            self._salary(worker=inactive)

    def test_one_active_salary_template_friendly_error(self):
        self._salary()
        with self.assertRaises(ValidationError):
            self._salary(label='Salary dup')

    def test_deactivate_idempotent(self):
        t = self._rent()
        deactivate_expense_template(t, actor=self.sa)
        t2 = deactivate_expense_template(t, actor=self.sa)   # no-op, no error
        self.assertFalse(t2.is_active)

    def test_amount_change_writes_indivisible_audit(self):
        t = self._rent()
        change_template_amount(t, new_amount=Decimal('1800'),
                               reason='rent revised', actor=self.sa)
        audit = ExpenseTemplateAmountAudit.objects.get(template=t)
        self.assertEqual((audit.old_amount, audit.new_amount),
                         (Decimal('1500'), Decimal('1800')))
        with self.assertRaises(ValidationError):   # reason mandatory
            change_template_amount(t, new_amount=Decimal('2000'), reason=' ',
                                   actor=self.sa)
        with self.assertRaises(ValidationError):   # no-op change refused
            change_template_amount(t, new_amount=Decimal('1800'), reason='x',
                                   actor=self.sa)


class GenerationTests(_Base):
    def test_preview_is_a_pure_read(self):
        self._rent()
        before = self._counts()
        receipt = generate_monthly_expenses(2026, 7, actor=self.mgr)
        self.assertEqual(len(receipt['to_create']), 1)
        self.assertEqual(self._counts(), before)     # ZERO writes

    def test_first_run_then_idempotent_second_run(self):
        t = self._rent()
        r1 = generate_monthly_expenses(2026, 7, actor=self.mgr, confirm=True)
        self.assertEqual(len(r1['created']), 1)
        fe = r1['created'][0].expense
        self.assertEqual(fe.amount, Decimal('1500'))
        self.assertEqual(fe.expense_date, date(2026, 7, 1))
        before = self._counts()
        r2 = generate_monthly_expenses(2026, 7, actor=self.mgr, confirm=True)
        self.assertEqual(len(r2['created']), 0)
        self.assertIn("already generated",
                      dict((tpl.pk, why) for tpl, why in r2['skipped'])[t.pk])
        self.assertEqual(self._counts(), before)     # converged, 0 writes

    def test_window_and_month_end_clamp(self):
        self._rent(label='EOM', start_date=date(2026, 1, 31))  # 31st anchor
        r = generate_monthly_expenses(2026, 2, actor=self.mgr, confirm=True)
        self.assertEqual(r['created'][0].expense.expense_date,
                         date(2026, 2, 28))          # Feb clamp (non-leap)
        # expired template skips
        t2 = self._rent(label='Old', start_date=date(2026, 1, 1),
                        end_date=date(2026, 5, 31))
        r2 = generate_monthly_expenses(2026, 7, actor=self.mgr)
        reasons = dict((tpl.pk, why) for tpl, why in r2['skipped'])
        self.assertIn("expired", reasons[t2.pk])

    def test_q13_inactive_worker_stops_salary_generation(self):
        self._salary()
        self.worker.is_active = False
        self.worker.save(update_fields=['is_active'])
        r = generate_monthly_expenses(2026, 7, actor=self.mgr, confirm=True)
        self.assertEqual(len(r['created']), 0)
        self.assertTrue(any("worker is inactive" in why for _, why in r['skipped']))

    def test_m3_manual_first_skips_template_and_period_continues(self):
        self._salary()
        self._rent()
        record_expense(category='salary', amount=Decimal('9000'),
                       expense_date=date(2026, 7, 5), actor=self.mgr,
                       worker=self.worker, notes='manual')
        r = generate_monthly_expenses(2026, 7, actor=self.mgr, confirm=True)
        # rent generated; salary skipped with the M-3 reason; nothing raised
        self.assertEqual([c.template.category for c in r['created']], ['rent'])
        self.assertTrue(any("manual salary exists" in why
                            for _, why in r['skipped']))

    def test_m3_generated_first_blocks_manual(self):
        self._salary()
        generate_monthly_expenses(2026, 7, actor=self.mgr, confirm=True)
        with self.assertRaises(ValidationError) as ctx:
            record_expense(category='salary', amount=Decimal('9000'),
                           expense_date=date(2026, 7, 20), actor=self.mgr,
                           worker=self.worker, notes='manual after')
        self.assertEqual(ctx.exception.code, 'duplicate_salary')

    def test_real_failure_rolls_back_the_whole_period(self):
        self._rent()
        self._rent(label='Rent — Annex', amount='700')
        before = self._counts()
        real = expense_service.record_expense
        calls = {'n': 0}

        def explode_on_second(**kw):
            calls['n'] += 1
            if calls['n'] == 2:
                raise RuntimeError("injected mid-period failure")
            return real(**kw)

        with mock.patch.object(expense_service, 'record_expense',
                               side_effect=explode_on_second):
            with self.assertRaises(RuntimeError):
                generate_monthly_expenses(2026, 7, actor=self.mgr, confirm=True)
        self.assertEqual(self._counts(), before)     # NOTHING landed

    def test_concurrent_duplicate_serializes_on_the_constraint(self):
        t = self._rent()
        resolved = expense_service._resolve_month(2026, 7)
        # Freeze a stale resolution (template still "due"), then land coverage
        # as the concurrent winner would — the loser must fail CLEANLY.
        generate_monthly_expenses(2026, 7, actor=self.mgr, confirm=True)
        before = self._counts()
        with mock.patch.object(expense_service, '_resolve_month',
                               return_value=resolved):
            with self.assertRaises(ValidationError) as ctx:
                generate_monthly_expenses(2026, 7, actor=self.mgr, confirm=True)
        self.assertIn("concurrently", str(ctx.exception))
        self.assertEqual(self._counts(), before)     # loser fully rolled back


class RegenerationTests(_Base):
    def _generated(self):
        self._rent()
        r = generate_monthly_expenses(2026, 7, actor=self.mgr, confirm=True)
        return r['created'][0]

    def test_void_does_not_free_the_period(self):
        rec = self._generated()
        void_expense(rec.expense, actor=self.sa, reason='wrong amount')
        r = generate_monthly_expenses(2026, 7, actor=self.mgr, confirm=True)
        self.assertEqual(len(r['created']), 0)
        self.assertTrue(any("regenerate explicitly" in why
                            for _, why in r['skipped']))

    def test_regenerate_requires_voided_expense_and_reason(self):
        rec = self._generated()
        with self.assertRaises(ValidationError):     # not voided yet
            regenerate_period(rec.template, year=2026, month=7,
                              reason='x', actor=self.sa)
        void_expense(rec.expense, actor=self.sa, reason='wrong amount')
        with self.assertRaises(ValidationError):     # reason mandatory
            regenerate_period(rec.template, year=2026, month=7,
                              reason='  ', actor=self.sa)
        with self.assertRaises(PermissionDenied):    # SA lever
            regenerate_period(rec.template, year=2026, month=7,
                              reason='x', actor=self.mgr)

    def test_amount_change_timeline_b06(self):
        # Jul at 1500 → change to 1800 → Aug at 1800 → Jul unchanged →
        # void Jul + regenerate → new Jul row at CURRENT 1800 (owner policy).
        rec = self._generated()                              # Jul @ 1500
        change_template_amount(rec.template, new_amount=Decimal('1800'),
                               reason='rent revised', actor=self.sa)
        aug = generate_monthly_expenses(2026, 8, actor=self.mgr, confirm=True)
        self.assertEqual(aug['created'][0].expense.amount, Decimal('1800'))
        rec.expense.refresh_from_db()
        self.assertEqual(rec.expense.amount, Decimal('1500'))  # frozen history
        void_expense(rec.expense, actor=self.sa, reason='wrong rent')
        new = regenerate_period(rec.template, year=2026, month=7,
                                reason='corrected rent', actor=self.sa)
        self.assertEqual(new.expense.amount, Decimal('1800'))  # CURRENT amount
        self.assertEqual(new.supersedes_id, rec.pk)
        rec.refresh_from_db()
        self.assertIsNotNone(rec.superseded_at)              # chain recorded
        rec.expense.refresh_from_db()
        self.assertEqual(rec.expense.amount, Decimal('1500'))  # still visible
        # converged: Jul now covered by the new record
        r = generate_monthly_expenses(2026, 7, actor=self.mgr, confirm=True)
        self.assertEqual(len(r['created']), 0)


class CommandTests(_Base):
    """MEE-D4: the command is a THIN wrapper — same path, same gates."""

    def test_preview_default_writes_nothing_and_confirm_creates(self):
        from io import StringIO
        from django.core.management import call_command
        self._rent()
        out = StringIO()
        call_command('generate_monthly_expenses', '2026-07',
                     actor=self.mgr.email, stdout=out)
        self.assertIn('PREVIEW (nothing written)', out.getvalue())
        self.assertEqual(FactoryExpense.objects.count(), 0)
        out = StringIO()
        call_command('generate_monthly_expenses', '2026-07',
                     actor=self.mgr.email, confirm=True, stdout=out)
        self.assertIn('created=1', out.getvalue())
        self.assertEqual(FactoryExpense.objects.count(), 1)

    def test_command_refuses_bad_month_and_non_management_actor(self):
        from django.core.management import call_command
        from django.core.management.base import CommandError
        with self.assertRaises(CommandError):
            call_command('generate_monthly_expenses', 'garbage',
                         actor=self.mgr.email)
        with self.assertRaises(PermissionDenied):   # service gate, not the shell
            call_command('generate_monthly_expenses', '2026-07',
                         actor=self.worker.email)


class PurityAndAdrTests(_Base):
    GUARDED = ("FactoryExpense", "ExpenseTemplate", "ExpenseGenerationRecord",
               "ExpenseTemplateAmountAudit")
    WRITE = r"\.objects\.(create|update|delete|get_or_create|update_or_create|bulk_create)"

    def test_purity_no_writes_outside_the_service_family(self):
        app = Path(__file__).resolve().parent.parent
        offenders = []
        files = [app / 'views.py', app / 'forms.py', app / 'admin.py',
                 *(app / 'management').rglob('*.py')]
        for f in files:
            text = f.read_text()
            for model in self.GUARDED:
                if re.search(model + self.WRITE, text):
                    offenders.append(f"{f.name}:{model}")
        self.assertEqual(offenders, [])

    def test_adr_0011_engine_fk_targets_are_bounded(self):
        # The engine family may reference ONLY User/FactoryExpense/itself —
        # no production/settlement/costing reachability, by schema.
        allowed = {'accounts.user', 'expense.factoryexpense',
                   'expense.expensetemplate', 'expense.expensegenerationrecord'}
        for model in (ExpenseTemplate, ExpenseGenerationRecord,
                      ExpenseTemplateAmountAudit):
            for f in model._meta.get_fields():
                rel = getattr(f, 'related_model', None)
                if rel is not None and f.concrete:
                    self.assertIn(rel._meta.label_lower, allowed,
                                  f"{model.__name__}.{f.name}")

    def test_generation_never_touches_the_ledger(self):
        self._rent()
        self._salary()
        before = (WorkerLedgerEntry.objects.count(),
                  WorkerLedgerEntry.objects.aggregate(s=Sum('amount'))['s'])
        generate_monthly_expenses(2026, 7, actor=self.mgr, confirm=True)
        after = (WorkerLedgerEntry.objects.count(),
                 WorkerLedgerEntry.objects.aggregate(s=Sum('amount'))['s'])
        self.assertEqual(after, before)
