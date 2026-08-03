"""BOD-E certification pins (owner-authorized 2026-07-18) — no new widgets,
no new logic: the D9 landing matrix, the full permission matrix, drill-down
certification (every destination resolves AND serves the SA a 200), the
no-duplicate-service-calls proof, and the sidebar-visibility matrix."""

from django.apps import apps
from django.test import TestCase
from django.urls import reverse

from bod.registry import NAV_CARDS, REGISTRY
from bod.tests.test_widgets_wave1 import make_sa


def make_role_user(email, code):
    User = apps.get_model("accounts", "User")
    Role = apps.get_model("accounts", "Role")
    return User.objects.create_user(email, "x", role=Role.objects.get(code=code))


class LandingMatrixTests(TestCase):
    """D9: Owner/SA → BOD; EVERY other role keeps its pre-D9 landing."""

    def _landing(self, user):
        self.client.force_login(user)
        return self.client.get(reverse("accounts:home"))

    def test_super_admin_lands_on_bod(self):
        r = self._landing(make_sa("dev.bod.e.sa@test.local"))
        self.assertRedirects(r, reverse("bod:dashboard"),
                             fetch_redirect_response=False)

    def test_other_roles_keep_their_existing_landings(self):
        expectations = {
            "manager": reverse("production:dashboard"),
            "worker": reverse("inventory:my_dashboard"),
            "accountant": reverse("inventory:my_dashboard"),
            "listing_team": reverse("inventory:my_dashboard"),
        }
        for code, target in expectations.items():
            u = make_role_user(f"dev.bod.e.{code}@test.local", code)
            r = self._landing(u)
            self.assertRedirects(r, target, fetch_redirect_response=False,
                                 msg_prefix=code)

    def test_anonymous_still_redirects_to_login(self):
        r = self.client.get(reverse("accounts:home"))
        self.assertEqual(r.status_code, 302)


class PermissionMatrixTests(TestCase):
    """The BOD page itself, every supported role (BOD-D4 re-certified)."""

    def test_full_matrix(self):
        url = reverse("bod:dashboard")
        # anonymous → login redirect carrying next=
        r = self.client.get(url)
        self.assertEqual(r.status_code, 302)
        self.assertIn("next=", r["Location"])
        # super admin → 200 with ALL 17 widgets incl. the 5 financial
        self.client.force_login(make_sa("dev.bod.e.pm.sa@test.local"))
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        rendered = [e["widget"].kpi_id
                    for s in r.context["sections"] for e in s["widgets"]]
        self.assertEqual(len(rendered), len(REGISTRY))
        self.assertEqual(len([k for k in rendered if k in (
            "month-expenses", "expense-categories", "outstanding-payments",
            "outstanding-advances", "expected-payouts")]), 5)
        self.client.logout()
        # every non-SA role → 403 (v1 Owner/SA only)
        for code in ("manager", "worker", "accountant", "listing_team"):
            u = make_role_user(f"dev.bod.e.pm.{code}@test.local", code)
            self.client.force_login(u)
            self.assertEqual(self.client.get(url).status_code, 403, code)
            self.client.logout()

    def test_sidebar_visibility_matrix(self):
        # The rendered sidebar carries the BOD link ONLY for the super admin.
        target = reverse("bod:dashboard")
        self.client.force_login(make_sa("dev.bod.e.sb.sa@test.local"))
        body = self.client.get(reverse("production:dashboard")).content.decode()
        self.assertIn(f'href="{target}"', body)
        self.client.logout()
        mgr = make_role_user("dev.bod.e.sb.mgr@test.local", "manager")
        self.client.force_login(mgr)
        body = self.client.get(reverse("production:dashboard")).content.decode()
        self.assertNotIn(f'href="{target}"', body)


class DrillDownCertificationTests(TestCase):
    """Every widget + nav card destination resolves and serves the SA."""

    def test_every_destination_resolves_and_returns_200(self):
        self.client.force_login(make_sa("dev.bod.e.dd.sa@test.local"))
        targets = {w.kpi_id: w.drill_down for w in REGISTRY}
        targets.update({f"nav:{t}": u for t, u, _ in NAV_CARDS})
        for key, url_name in targets.items():
            url = reverse(url_name)          # dead link ⇒ NoReverseMatch here
            r = self.client.get(url, follow=True)
            self.assertEqual(r.status_code, 200, f"{key} → {url_name} ({url})")

    def test_destination_map_is_the_certified_mapping(self):
        # No incorrect destinations: pin widget → owning-module URL name.
        expected = {
            "stalled-addas": "production:stalled-addas",
            "pending-reports": "production:pending-reports",
            "settlements-ready": "expense:adda-settlement-list",
            "settlements-blocked": "expense:adda-settlement-list",
            "active-addas": "production:dashboard",
            "completed-today": "production:dashboard",
            "machine-counts": "machines:list",
            "roll-stock": "raw_materials:cloth-dashboard",
            "stock-by-warehouse": "raw_materials:cloth-dashboard",
            "on-hold-addas": "production:dashboard",
            "stage-chips": "production:dashboard",
            "workers-active": "production:pending-reports",
            "month-expenses": "expense:factory-expense-list",
            "expense-categories": "expense:factory-expense-list",
            "outstanding-payments": "expense:payroll-overview",
            "outstanding-advances": "expense:payroll-overview",
            "expected-payouts": "expense:adda-settlement-list",
        }
        self.assertEqual({w.kpi_id: w.drill_down for w in REGISTRY}, expected)


class NoDuplicateServiceCallTests(TestCase):
    """BOD-E performance law: one page render = at most ONE call per shared
    owning service (the per-request cache is doing its job)."""

    def test_shared_services_called_once_per_render(self):
        import unittest.mock as mock
        counts = {}

        def counting(path):
            module_path, func = path.rsplit(".", 1)
            import importlib
            real = getattr(importlib.import_module(module_path), func)

            def wrapper(*a, **kw):
                counts[path] = counts.get(path, 0) + 1
                return real(*a, **kw)
            return mock.patch(path, side_effect=wrapper)

        self.client.force_login(make_sa("dev.bod.e.dc.sa@test.local"))
        with counting("production.services.operations_digest.operations_digest"), \
             counting("expense.services.adda_settlement_service.settlement_queue"), \
             counting("machines.services.machine_service.register_counts"), \
             counting("expense.services.expense_service.monthly_totals"), \
             counting("expense.services.payroll_service.payroll_totals"):
            r = self.client.get(reverse("bod:dashboard"))
        self.assertEqual(r.status_code, 200)
        for path, n in counts.items():
            self.assertLessEqual(n, 1, f"{path} called {n}× in one render")
        # payroll_totals runs INSIDE the digest only — F5/F6 reuse that call.
        self.assertEqual(
            counts.get("expense.services.payroll_service.payroll_totals", 0), 1)
