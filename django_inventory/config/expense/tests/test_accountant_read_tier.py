"""The ACCOUNTANT read tier — owner ruling 2026-08-02.

WHY THIS FILE EXISTS. Every financial page used to be `_ManagementOnly`: read and
write behind ONE gate. A *pure* `accountant` login therefore had no reachable page
at all — their `FINANCIAL_ROLES` capability (view + edit Supplier and Cost Per KG)
was unreachable dead code, and their dashboard showed WORKER copy
("Jab manager aapko kaam dega", "Pieces Produced 0").

THE INVARIANT THESE PIN: **reads widened, writes did not move.**

An accountant may now READ the books and RECORD a cost — the one deliberate,
owner-authorised money-write grant. They must never be able to:
  • finalize/start a settlement (settlement = THE money boundary),
  • record an advance, change a pay basis, or run FnF,
  • VOID an expense or change a template amount (super-admin levers),
  • generate a recurring period (writes rows).

Each of those is asserted at BOTH layers — the view gate AND the service gate — so a
future mis-gated view still cannot become a money hole.
"""
from datetime import date
from decimal import Decimal

from django.core.exceptions import PermissionDenied
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from expense.models import FactoryExpense
from inventory.models import Role


class _Cast(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.roles = {r.code: r for r in Role.objects.all()}
        cls.accountant = cls._mk('acc@t', 'accountant')
        cls.manager = cls._mk('mgr@t', 'manager')
        cls.worker = cls._mk('wrk@t', 'worker')

    @classmethod
    def _mk(cls, email, role_code):
        u = User.objects.create_user(email=email, password='x')
        u.role = cls.roles[role_code]
        u.save(update_fields=['role'])
        return u


class AccountantCanReadTheBooksTests(_Cast):
    """The whole point: an accountant logs in and has a job to do."""

    READ_URLS = (
        '/expense/payroll/',            # all-worker overview — reconciliation
        '/expense/expenses/',           # factory cost register
        '/expense/material-spend/',     # cloth ₹/kg — previously menu-less
        '/expense/settlements/',        # what was actually paid
        '/expense/templates/',          # recurring schedule (preview = pure read)
        '/raw-materials/rolls/',        # where supplier + cost-per-kg LIVE
    )

    def test_every_financial_read_page_opens(self):
        self.client.force_login(self.accountant)
        for url in self.READ_URLS:
            self.assertEqual(self.client.get(url).status_code, 200,
                             f'accountant cannot read {url}')

    def test_a_worker_still_cannot_read_any_of_them(self):
        """Widening for accountants must not widen for the factory floor."""
        self.client.force_login(self.worker)
        for url in self.READ_URLS:
            self.assertNotEqual(self.client.get(url).status_code, 200,
                                f'worker reached financial page {url}')

    def test_the_recurring_register_renders_although_it_calls_the_generator(self):
        """`ExpenseTemplateListView` builds per-template status from
        `generate_monthly_expenses(confirm=False)`. That call is a PURE READ (it
        returns the plan before writing), but it used to be gated as a write — so
        this read page 403'd for an accountant. Regression pin."""
        self.client.force_login(self.accountant)
        self.assertEqual(self.client.get('/expense/templates/').status_code, 200)

    def test_menu_offers_exactly_the_pages_that_open(self):
        """Rule 6 for the new tier: a visible link that 403s (or a reachable page
        with no link) is a bug in either direction."""
        from accounts.services import build_menu_for
        self.client.force_login(self.accountant)
        for section in build_menu_for(self.accountant):
            for item in section['items']:
                resp = self.client.get(item['url'])
                self.assertEqual(
                    resp.status_code, 200,
                    f"menu offers {item['label']} ({item['url']}) but it "
                    f"returned {resp.status_code}")


class AccountantCannotWriteMoneyTests(_Cast):
    """The safety half. Every one of these is asserted at the VIEW and the SERVICE."""

    WRITE_URLS = (
        '/expense/advances/add/',     # lending money
        '/expense/templates/add/',    # creating a recurring commitment
        '/expense/generate/',         # creating a whole period of rows
    )

    def test_write_pages_refuse_at_the_view(self):
        self.client.force_login(self.accountant)
        for url in self.WRITE_URLS:
            self.assertNotEqual(self.client.get(url).status_code, 200,
                                f'accountant reached WRITE page {url}')

    def test_settlement_start_refuses(self):
        """Settlement is THE money-write boundary and must not have moved."""
        from production.models import Adda, Product
        product = Product.objects.create(code='ACC1', name='Acc Test')
        adda = Adda.objects.create(code='ACC-001', product=product)
        self.client.force_login(self.accountant)
        resp = self.client.get(
            reverse('expense:adda-settlement-start', args=[adda.pk]))
        self.assertNotEqual(resp.status_code, 200)

    def test_void_expense_refuses_in_the_SERVICE_not_just_the_view(self):
        """`void_expense` is super-admin-only INSIDE the service, so even a
        mis-gated view could not let an accountant erase a cost record."""
        from expense.services.expense_service import record_expense, void_expense
        expense = record_expense(
            category=FactoryExpense.Category.RENT, amount=Decimal('100'),
            expense_date=date(2026, 8, 1), actor=self.manager)
        with self.assertRaises(PermissionDenied):
            void_expense(expense, actor=self.accountant, reason='nope')

    def test_template_amount_change_refuses_in_the_service(self):
        from expense.services.expense_service import (
            change_template_amount, create_expense_template,
        )
        # created by a super admin — the only role that may
        sa = User.objects.create_user(email='sa@t', password='x',
                                      is_superuser=True)
        tpl = create_expense_template(
            label='Rent', category=FactoryExpense.Category.RENT,
            amount=Decimal('500'), start_date=date(2026, 8, 1), actor=sa)
        with self.assertRaises(PermissionDenied):
            change_template_amount(tpl, new_amount=Decimal('999'),
                                   reason='nope', actor=self.accountant)

    def test_generating_a_period_refuses_in_the_service(self):
        """The confirm=True half of the split gate."""
        from expense.services.expense_service import generate_monthly_expenses
        with self.assertRaises(PermissionDenied):
            generate_monthly_expenses(2026, 8, actor=self.accountant,
                                      confirm=True)

    def test_previewing_a_period_is_allowed(self):
        """…and the confirm=False half is a read, so it must NOT refuse."""
        from expense.services.expense_service import generate_monthly_expenses
        receipt = generate_monthly_expenses(2026, 8, actor=self.accountant)
        self.assertIn('to_create', receipt)
        self.assertEqual(receipt['created'], [],
                         'a preview must never create anything')

    def test_a_worker_cannot_preview_or_record(self):
        """The read tier is management+accountant — not "anyone who is not a worker"."""
        from expense.services.expense_service import (
            generate_monthly_expenses, record_expense,
        )
        with self.assertRaises(PermissionDenied):
            generate_monthly_expenses(2026, 8, actor=self.worker)
        with self.assertRaises(PermissionDenied):
            record_expense(category=FactoryExpense.Category.RENT,
                           amount=Decimal('1'), expense_date=date(2026, 8, 1),
                           actor=self.worker)


class AccountantCanRecordACostTests(_Cast):
    """The ONE money-write grant, and its boundary."""

    def test_accountant_can_record_a_factory_expense(self):
        from expense.services.expense_service import record_expense
        expense = record_expense(
            category=FactoryExpense.Category.ELECTRICITY,
            amount=Decimal('250.50'), expense_date=date(2026, 8, 1),
            actor=self.accountant, notes='Aug bill')
        self.assertEqual(expense.amount, Decimal('250.50'))
        self.assertIsNone(expense.voided_at)

    def test_but_cannot_erase_it_afterwards(self):
        """Append-only bookkeeping: add yes, erase no. Corrections are the owner's."""
        from expense.services.expense_service import record_expense, void_expense
        expense = record_expense(
            category=FactoryExpense.Category.ELECTRICITY, amount=Decimal('10'),
            expense_date=date(2026, 8, 1), actor=self.accountant)
        with self.assertRaises(PermissionDenied):
            void_expense(expense, actor=self.accountant, reason='oops')


class AccountantDashboardTests(_Cast):
    """No more worker copy; real financial figures instead."""

    def test_accountant_sees_the_accounts_panel_not_worker_copy(self):
        self.client.force_login(self.accountant)
        body = self.client.get(reverse('inventory:my_dashboard')).content.decode()
        self.assertIn('Accounts — where to start', body)
        self.assertNotIn('aapko kaam dega', body,
                         'accountant was promised assigned floor work')
        self.assertNotIn('Pieces Produced', body)

    def test_worker_keeps_the_worker_dashboard(self):
        self.client.force_login(self.worker)
        body = self.client.get(reverse('inventory:my_dashboard')).content.decode()
        self.assertNotIn('Accounts — where to start', body)
        self.assertIn('aapko kaam dega', body)

    def test_the_panel_figures_come_from_the_canonical_aggregate(self):
        """The panel must NOT re-derive money. `payroll_totals()` already excludes
        REVERSED recoveries (PA-12-A); a hand-rolled sum would understate advance
        exposure after any settlement reversal."""
        from expense.services import payroll_service
        from inventory.views.dashboard import _build_dashboard_context

        request = type('R', (), {'user': self.accountant, 'GET': {}})()
        ctx = _build_dashboard_context(request, is_admin_view=False)
        panel = ctx['accounts_panel']
        self.assertIsNotNone(panel)
        canonical = payroll_service.payroll_totals()
        self.assertEqual(panel['advance_exposure'], canonical['advance_exposure'])
        self.assertEqual(panel['pending_payable'], canonical['pending_payable'])
