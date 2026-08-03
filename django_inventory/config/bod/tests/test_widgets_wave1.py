"""BOD-C Wave 1 — the digest-backed L1 board. THE standing no-second-truth
proof: every BOD tile shows the SAME number its authoritative surface shows on
the SAME database (both read the one owner service — divergence is
structurally impossible, and this test keeps it that way). Plus fail-soft and
the BOD-D6 query budget with live widgets."""

from django.apps import apps
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse


def make_sa(email="dev.bod.w1.sa@test.local"):
    User = apps.get_model("accounts", "User")
    Role = apps.get_model("accounts", "Role")
    return User.objects.create_user(email, "x",
                                    role=Role.objects.get(code="super_admin"))


def tiles_by_id(response):
    out = {}
    for section in response.context["sections"]:
        for entry in section["widgets"]:
            out[entry["widget"].kpi_id] = entry
    return out


class Wave1CrossCheckTests(TestCase):
    """BOD numbers == the owning services' numbers on the same DB."""

    def test_bod_tiles_equal_their_authoritative_sources(self):
        from expense.services import adda_settlement_service
        from machines.services import machine_service
        from production.services.operations_digest import operations_digest

        self.client.force_login(make_sa())
        r = self.client.get(reverse("bod:dashboard"))
        self.assertEqual(r.status_code, 200)
        tiles = tiles_by_id(r)

        digest = operations_digest()
        self.assertEqual(tiles["stalled-addas"]["tile"]["value"], digest["stalled_count"])
        self.assertEqual(tiles["pending-reports"]["tile"]["value"], digest["pending_reports"])
        self.assertEqual(tiles["active-addas"]["tile"]["value"], digest["active_addas"])
        self.assertEqual(tiles["completed-today"]["tile"]["value"], digest["completed_today"])

        queue = adda_settlement_service.settlement_queue()
        self.assertEqual(tiles["settlements-ready"]["tile"]["value"], len(queue["ready"]))
        self.assertEqual(tiles["settlements-blocked"]["tile"]["value"], len(queue["waiting"]))

        counts = machine_service.register_counts()
        self.assertEqual(tiles["machine-counts"]["tile"]["value"], counts["total"])
        self.assertEqual(dict(tiles["machine-counts"]["tile"]["sub"])["assigned now"],
                         counts["assigned_now"])

    def test_bod_matches_the_operations_dashboard_digest_live(self):
        # The same numbers as rendered ON the certified page (context compare).
        sa = make_sa("dev.bod.w1b.sa@test.local")
        self.client.force_login(sa)
        ops = self.client.get(reverse("production:dashboard"))
        bod = self.client.get(reverse("bod:dashboard"))
        digest = ops.context["digest"]
        tiles = tiles_by_id(bod)
        self.assertEqual(tiles["active-addas"]["tile"]["value"], digest["active_addas"])
        self.assertEqual(tiles["stalled-addas"]["tile"]["value"], digest["stalled_count"])

    def test_no_money_values_in_non_financial_tiles(self):
        # BOD-D authorized money — but ONLY on financial=True widgets. Every
        # NON-financial tile stays money-free (the BOD-C law, now scoped).
        self.client.force_login(make_sa("dev.bod.w1c.sa@test.local"))
        r = self.client.get(reverse("bod:dashboard"))
        for kpi_id, entry in tiles_by_id(r).items():
            if entry["widget"].financial:
                continue
            blob = str(entry["tile"])
            for token in ("pending_payable", "advance_exposure", "₹", "payable"):
                self.assertNotIn(token, blob, kpi_id)


class Wave1FailSoftTests(TestCase):
    def test_one_broken_owner_call_degrades_to_an_error_tile_never_500(self):
        import unittest.mock as mock
        self.client.force_login(make_sa("dev.bod.w1d.sa@test.local"))
        # Break the OWNING service the adapter resolves at call time — the
        # realistic failure class (fail-soft contract §6.2).
        with mock.patch("machines.services.machine_service.register_counts",
                        side_effect=RuntimeError("owner call exploded")):
            r = self.client.get(reverse("bod:dashboard"))
        self.assertEqual(r.status_code, 200)
        body = r.content.decode()
        self.assertIn("Unavailable right now", body)   # the error tile
        self.assertIn("Active Addas", body)            # siblings unaffected


class Wave1BudgetTests(TestCase):
    def test_query_budget_with_live_widgets(self):
        from django.db import connection
        self.client.force_login(make_sa("dev.bod.w1e.sa@test.local"))
        self.client.get(reverse("bod:dashboard"))  # warm session
        with CaptureQueriesContext(connection) as ctx:
            r = self.client.get(reverse("bod:dashboard"))
        self.assertEqual(r.status_code, 200)
        n = len(ctx.captured_queries)
        self.assertLessEqual(n, 30, f"BOD-D6 budget blown: {n} queries")
