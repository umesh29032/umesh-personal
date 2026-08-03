"""MEE-C (Phase 16) — the recurring-expense surfaces: gating matrix, thin-view
law (every write lands via the MEE-B service layer — asserted by OUTCOME
through the service-owned constraints/audit rows), and the preview→confirm →
review flow end-to-end through the real pages."""

from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from inventory.models import Role
from expense.models import (
    ExpenseGenerationRecord, ExpenseTemplate, ExpenseTemplateAmountAudit,
    FactoryExpense,
)
from expense.services.expense_service import (
    create_expense_template, generate_monthly_expenses, void_expense,
)


def _user(email, code, super_=False):
    u = User.objects.create_user(email=email, password='x', is_superuser=super_)
    u.role = Role.objects.get(code=code)
    u.save()
    return u


class _Base(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.sa = _user('sur-sa@test', 'super_admin', super_=True)
        cls.mgr = _user('sur-mgr@test', 'manager')
        cls.worker = _user('sur-w@test', 'worker')

    def _tpl(self):
        return create_expense_template(
            label='Rent — Main', category='rent', amount=Decimal('1500'),
            start_date=date(2026, 7, 1), actor=self.sa)


class SurfaceGatingTests(_Base):
    URLS = ('expense:expense-template-list', 'expense:expense-template-add',
            'expense:expense-generate')

    def test_management_200_worker_302_anon_302(self):
        for name in self.URLS:
            url = reverse(name)
            self.assertEqual(self.client.get(url).status_code, 302, name)  # anon
            self.client.force_login(self.worker)
            r = self.client.get(url)                        # _ManagementOnly wall
            self.assertIn(r.status_code, (302, 403), name)
            self.client.logout()
            for u in (self.mgr, self.sa):
                self.client.force_login(u)
                self.assertEqual(self.client.get(url).status_code, 200, name)
                self.client.logout()

    def test_sidebar_menu_item_for_management_only(self):
        target = reverse('expense:expense-template-list')
        self.client.force_login(self.mgr)
        body = self.client.get(reverse('expense:factory-expense-list')).content.decode()
        self.assertIn(f'href="{target}"', body)
        self.client.logout()

    def test_sa_lever_enforced_by_service_not_view(self):
        # Manager reaches the page but the SA levers refuse at the service.
        t = self._tpl()
        self.client.force_login(self.mgr)
        self.client.post(reverse('expense:expense-template-list'),
                         {'action': 'deactivate', 'template_id': t.pk})
        t.refresh_from_db()
        self.assertTrue(t.is_active)          # refused — message, no write


class MeeDFullIdentityMatrixTests(_Base):
    """MEE-D certification: the complete identity matrix on the three engine
    surfaces + POST negative controls (a reachable page must still refuse the
    write at the service; an unauthorized identity must write NOTHING)."""

    URLS = ('expense:expense-template-list', 'expense:expense-template-add',
            'expense:expense-generate')

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.acct = _user('surd-acct@test', 'accountant')
        cls.listing = _user('surd-list@test', 'listing_team')

    # Owner ruling 2026-08-02: the ACCOUNTANT read tier. Their expectation is now
    # PER-SURFACE, not one value — the register is a READ (the per-template status
    # comes from `generate_monthly_expenses(confirm=False)`, a pure preview), while
    # add/generate stay writes. Every other identity is unchanged.
    ACCOUNTANT_READS = {'expense:expense-template-list'}

    def test_every_identity_every_surface(self):
        expectations = [
            (None, (302,)), (self.worker, (302, 403)),
            (self.acct, (302, 403)), (self.listing, (302, 403)),
            (self.mgr, (200,)), (self.sa, (200,)),
        ]
        for user, allowed in expectations:
            if user:
                self.client.force_login(user)
            for name in self.URLS:
                expected = allowed
                if user is self.acct and name in self.ACCOUNTANT_READS:
                    expected = (200,)
                r = self.client.get(reverse(name))
                self.assertIn(r.status_code, expected,
                              f"{getattr(user, 'email', 'anon')} → {name}")
            self.client.logout()

    def test_post_negative_controls_write_nothing(self):
        t = self._tpl()
        gen_url = reverse('expense:expense-generate') + '?month=2026-07'
        for user in (None, self.worker, self.acct, self.listing):
            if user:
                self.client.force_login(user)
            self.client.post(gen_url, {'action': 'confirm'})
            self.client.post(reverse('expense:expense-template-list'),
                             {'action': 'deactivate', 'template_id': t.pk})
            self.client.logout()
        self.assertEqual(FactoryExpense.objects.count(), 0)
        self.assertEqual(ExpenseGenerationRecord.objects.count(), 0)
        t.refresh_from_db()
        self.assertTrue(t.is_active)

    def test_mgt_c_levers_unchanged_with_the_engine_present(self):
        # MGT-C re-proof: manual create = management; void = SA + reason.
        from expense.services.expense_service import record_expense
        e = record_expense(category='rent', amount=Decimal('10'),
                           expense_date=date(2026, 7, 2), actor=self.mgr)
        self.client.force_login(self.mgr)
        self.client.post(reverse('expense:factory-expense-list'),
                         {'expense_id': e.pk, 'void_reason': 'x'})
        e.refresh_from_db()
        self.assertIsNone(e.voided_at)          # manager void refused (SA lever)
        self.client.force_login(self.sa)
        self.client.post(reverse('expense:factory-expense-list'),
                         {'expense_id': e.pk, 'void_reason': 'mgt-c re-proof'})
        e.refresh_from_db()
        self.assertIsNotNone(e.voided_at)       # SA + reason still the only door


class SurfaceFlowTests(_Base):
    def test_create_template_via_the_page(self):
        self.client.force_login(self.sa)
        r = self.client.post(reverse('expense:expense-template-add'), {
            'label': 'Electricity — Main', 'category': 'electricity',
            'amount': '1500', 'start_date': '2026-07-01', 'notes': ''})
        self.assertEqual(r.status_code, 302)
        t = ExpenseTemplate.objects.get(label='Electricity — Main')
        self.assertEqual(t.created_by, self.sa)   # actor threaded to the service

    def test_preview_page_is_read_only_and_confirm_generates(self):
        self._tpl()
        self.client.force_login(self.mgr)
        url = reverse('expense:expense-generate') + '?month=2026-07'
        r = self.client.get(url)
        self.assertContains(r, 'Rent — Main')
        self.assertEqual(FactoryExpense.objects.count(), 0)   # GET wrote nothing
        r = self.client.post(url, {'action': 'confirm'})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(FactoryExpense.objects.count(), 1)
        self.assertEqual(ExpenseGenerationRecord.objects.count(), 1)
        # review = the EXISTING expense list; the generated row shows there
        review = self.client.get(
            reverse('expense:factory-expense-list') + '?month=2026-07')
        self.assertContains(review, 'Generated from template')

    def test_template_list_shows_current_period_status(self):
        self._tpl()          # side effect: creates the template this asserts on
        self.client.force_login(self.mgr)
        url = reverse('expense:expense-template-list') + '?month=2026-07'
        self.assertContains(self.client.get(url), 'Pending generation')
        generate_monthly_expenses(2026, 7, actor=self.mgr, confirm=True)
        self.assertContains(self.client.get(url), 'already generated')

    def test_amount_change_action_writes_the_audited_pair(self):
        t = self._tpl()
        self.client.force_login(self.sa)
        self.client.post(reverse('expense:expense-template-list'), {
            'action': 'change_amount', 'template_id': t.pk,
            'new_amount': '1800', 'reason': 'landlord revised'})
        t.refresh_from_db()
        self.assertEqual(t.amount, Decimal('1800'))
        self.assertEqual(ExpenseTemplateAmountAudit.objects.filter(
            template=t).count(), 1)   # the indivisible service pair fired

    def test_regenerate_action_via_the_page(self):
        t = self._tpl()
        rec = generate_monthly_expenses(2026, 7, actor=self.mgr,
                                        confirm=True)['created'][0]
        void_expense(rec.expense, actor=self.sa, reason='wrong amount')
        self.client.force_login(self.sa)
        url = reverse('expense:expense-generate') + '?month=2026-07'
        self.assertContains(self.client.get(url), 'Regenerate')
        self.client.post(url, {'action': 'regenerate', 'template_id': t.pk,
                               'reason': 'corrected'})
        self.assertEqual(ExpenseGenerationRecord.objects.filter(
            template=t, superseded_at__isnull=True).count(), 1)
        self.assertEqual(FactoryExpense.objects.count(), 2)  # voided + new
