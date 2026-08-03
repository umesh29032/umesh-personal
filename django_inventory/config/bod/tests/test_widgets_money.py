"""BOD-D — the money wave (owner-authorized 2026-07-18). The no-second-truth
instrument for every financial tile: tile == owning service == the source PAGE
the owner already trusts, on the same DB. Plus: the FINANCIAL_ROLES wall on
top of the page gate, the read-only proof (rendering the board moves NO money
row anywhere), the {% money %}-tag rendering law, and the ≤30 budget with all
17 widgets live."""

from decimal import Decimal

from django.apps import apps
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from bod.tests.test_widgets_wave1 import make_sa, tiles_by_id

MONEY_IDS = ["expected-payouts", "expense-categories", "month-expenses",
             "outstanding-advances", "outstanding-payments"]


def seed_money_world(sa):
    """A small but REAL money world: one FactoryExpense this month, one
    worker advance, one ledger credit (through the certified writers)."""
    FactoryExpense = apps.get_model("expense", "FactoryExpense")
    WorkerAdvance = apps.get_model("expense", "WorkerAdvance")
    User = apps.get_model("accounts", "User")
    worker = User.objects.create_user("dev.bod.money.w@test.local", "x")
    today = timezone.localtime().date()
    FactoryExpense.objects.create(
        category=FactoryExpense.Category.RENT, amount=Decimal("1500.00"),
        expense_date=today, entered_by=sa)
    FactoryExpense.objects.create(
        category=FactoryExpense.Category.ELECTRICITY, amount=Decimal("250.50"),
        expense_date=today, entered_by=sa)
    WorkerAdvance.objects.create(worker=worker, amount=Decimal("400.00"),
                                 advance_date=today, entered_by=sa)
    from expense.services import ledger_service
    ledger_service.log_credit(
        worker=worker, category="adjustment", amount=Decimal("120.00"),
        entry_date=today, created_by=sa, notes="DEV bod money test")
    return worker


class MoneyCrossCheckTests(TestCase):
    """Every ₹ tile equals its owning service AND its source page."""

    def setUp(self):
        self.sa = make_sa("dev.bod.money.sa@test.local")
        self.worker = seed_money_world(self.sa)

    def _tiles(self):
        self.client.force_login(self.sa)
        r = self.client.get(reverse("bod:dashboard"))
        self.assertEqual(r.status_code, 200)
        return tiles_by_id(r), r

    def test_money_tiles_equal_their_owning_services(self):
        from expense.services import (adda_settlement_service, expense_service,
                                      payroll_service)
        tiles, _ = self._tiles()

        totals = payroll_service.payroll_totals()
        self.assertEqual(tiles["outstanding-payments"]["tile"]["value"],
                         totals["pending_payable"])
        self.assertEqual(tiles["outstanding-advances"]["tile"]["value"],
                         totals["advance_exposure"])
        self.assertEqual(tiles["outstanding-payments"]["tile"]["value"],
                         Decimal("120.00"))
        self.assertEqual(tiles["outstanding-advances"]["tile"]["value"],
                         Decimal("400.00"))

        now = timezone.localtime()
        month = expense_service.monthly_totals(now.year, now.month)
        self.assertEqual(tiles["month-expenses"]["tile"]["value"], month["total"])
        self.assertEqual(tiles["month-expenses"]["tile"]["value"],
                         Decimal("1750.50"))
        self.assertEqual(dict(tiles["expense-categories"]["tile"]["money_sub"]),
                         {v["label"]: v["total"]
                          for v in month["by_category"].values()})

        queue = adda_settlement_service.settlement_queue()
        self.assertEqual(tiles["expected-payouts"]["tile"]["value"],
                         sum((r["expected"] for r in queue["ready"]),
                             Decimal("0.00")))

    def test_money_tiles_equal_their_source_pages(self):
        # The owner-trusted surfaces themselves: payroll overview totals and
        # the factory-expense list's monthly totals (SAME certified call).
        tiles, _ = self._tiles()
        payroll = self.client.get(reverse("expense:payroll-overview"))
        self.assertEqual(tiles["outstanding-payments"]["tile"]["value"],
                         payroll.context["total_payable"])
        self.assertEqual(tiles["outstanding-advances"]["tile"]["value"],
                         payroll.context["total_advance_out"])
        expenses = self.client.get(reverse("expense:factory-expense-list"))
        self.assertEqual(tiles["month-expenses"]["tile"]["value"],
                         expenses.context["totals"]["total"])

    def test_voided_expense_leaves_the_tile(self):
        # Void-awareness flows straight from monthly_totals — no BOD copy.
        FactoryExpense = apps.get_model("expense", "FactoryExpense")
        tiles, _ = self._tiles()
        self.assertEqual(tiles["month-expenses"]["tile"]["value"],
                         Decimal("1750.50"))
        e = FactoryExpense.objects.get(amount=Decimal("250.50"))
        e.voided_at = timezone.now()
        e.voided_by = self.sa
        e.save(update_fields=["voided_at", "voided_by"])
        tiles, _ = self._tiles()
        self.assertEqual(tiles["month-expenses"]["tile"]["value"],
                         Decimal("1500.00"))

    def test_rupee_rendered_via_money_tag_in_financial_tiles(self):
        # core.finance {% money %} = "₹" + floatformat:2 — the single owner.
        _, r = self._tiles()
        self.assertIn("₹120.00", r.content.decode())    # outstanding payments
        self.assertIn("₹1750.50", r.content.decode())   # month expenses


class FinancialWallTests(TestCase):
    def test_financial_widgets_vanish_without_financial_role(self):
        # Charter D1.6: the FINANCIAL_ROLES wall sits ON TOP of the page gate.
        # Simulate a future page audience without financial rights.
        import unittest.mock as mock
        self.client.force_login(make_sa("dev.bod.money.wall@test.local"))
        with mock.patch("accounts.services.user_can_view_financials",
                        return_value=False):
            r = self.client.get(reverse("bod:dashboard"))
        self.assertEqual(r.status_code, 200)
        tiles = tiles_by_id(r)
        for kpi_id in MONEY_IDS:
            self.assertNotIn(kpi_id, tiles)
        self.assertIn("active-addas", tiles)   # non-money board intact

    def test_sa_sees_all_financial_widgets(self):
        self.client.force_login(make_sa("dev.bod.money.sa2@test.local"))
        tiles = tiles_by_id(self.client.get(reverse("bod:dashboard")))
        for kpi_id in MONEY_IDS:
            self.assertIn(kpi_id, tiles)


class MoneyReadOnlyRegressionTests(TestCase):
    """The owner's regression demand: rendering the board changes NOTHING in
    the accounting system — ledger, settlements, advances, expenses, balances
    all byte-identical before/after."""

    def test_board_render_moves_no_money(self):
        from django.db.models import Sum
        sa = make_sa("dev.bod.money.ro@test.local")
        seed_money_world(sa)
        Ledger = apps.get_model("expense", "WorkerLedgerEntry")
        Advance = apps.get_model("expense", "WorkerAdvance")
        Expense = apps.get_model("expense", "FactoryExpense")
        Settlement = apps.get_model("expense", "AddaSettlement")

        def money_state():
            return {
                "ledger": (Ledger.objects.count(),
                           Ledger.objects.aggregate(s=Sum("amount"))["s"]),
                "advances": (Advance.objects.count(),
                             Advance.objects.aggregate(s=Sum("amount"))["s"]),
                "expenses": (Expense.objects.count(),
                             Expense.objects.aggregate(s=Sum("amount"))["s"]),
                "settlements": (Settlement.objects.count(),
                                Settlement.objects.aggregate(
                                    s=Sum("expected_total"))["s"]),
            }

        before = money_state()
        self.client.force_login(sa)
        for _ in range(2):
            r = self.client.get(reverse("bod:dashboard"))
            self.assertEqual(r.status_code, 200)
        self.assertEqual(money_state(), before)


class MoneyBudgetTests(TestCase):
    def test_query_budget_with_all_seventeen_widgets_live(self):
        from django.db import connection
        sa = make_sa("dev.bod.money.q@test.local")
        seed_money_world(sa)
        self.client.force_login(sa)
        self.client.get(reverse("bod:dashboard"))   # warm session
        with CaptureQueriesContext(connection) as ctx:
            r = self.client.get(reverse("bod:dashboard"))
        self.assertEqual(r.status_code, 200)
        n = len(ctx.captured_queries)
        self.assertLessEqual(n, 30, f"BOD-D6 budget blown: {n} queries")
