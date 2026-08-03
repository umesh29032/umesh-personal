"""BOD-A permanent pins — read-only architecture (purity + zero-POST),
the Owner/SA-only gate (all five roles + anonymous), the empty widget-registry
framework, the D1 section order, the D5 refresh surface, and the D6 query
budget. Widgets/KPIs deliberately DO NOT EXIST yet (owner order)."""

import os
import re

from django.apps import apps
from django.conf import settings
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

import bod
from bod.registry import REGISTRY, SECTIONS, Widget

BOD_DIR = os.path.dirname(bod.__file__)

ORM_WRITE = re.compile(
    r"\.objects\.(create|bulk_create|update|delete|get_or_create|update_or_create|bulk_update)\s*\(")
INSTANCE_WRITE = re.compile(r"\.(save|delete)\s*\(")


def _sources():
    for root, dirs, files in os.walk(BOD_DIR):
        dirs[:] = [d for d in dirs if d not in ("__pycache__", "tests")]
        for f in files:
            if f.endswith(".py"):
                yield os.path.join(root, f)


class BODPurityTests(TestCase):
    """THE window-never-engine pins (landed WITH the skeleton, before any KPI)."""

    def test_no_orm_or_instance_writes_in_bod_source(self):
        offenders = []
        for path in _sources():
            src = open(path, encoding="utf-8").read()
            for pat in (ORM_WRITE, INSTANCE_WRITE):
                for m in pat.finditer(src):
                    offenders.append(f"{os.path.relpath(path, BOD_DIR)}: {m.group(0)}")
        self.assertEqual(offenders, [], "write calls in the read-only BOD")

    def test_structurally_write_free_shape(self):
        # Zero models, zero migrations, zero forms — read-only by architecture.
        for forbidden in ("models.py", "migrations", "forms.py"):
            self.assertFalse(os.path.exists(os.path.join(BOD_DIR, forbidden)),
                             f"bod/{forbidden} exists")

    def test_registered_in_base_settings(self):
        self.assertIn("bod", settings.INSTALLED_APPS)

    def test_zero_post_route_census(self):
        # v1 has exactly ONE route, GET-only (BOD-D4: zero POST surfaces).
        from bod import urls as bod_urls
        self.assertEqual(len(bod_urls.urlpatterns), 1)
        from bod.views import BODDashboardView
        self.assertEqual(BODDashboardView.http_method_names, ["get", "head", "options"])


class BODGateTests(TestCase):
    """The BOD-D4 matrix: Owner/SA in; every other identity refused."""

    @classmethod
    def setUpTestData(cls):
        User = apps.get_model("accounts", "User")
        Role = apps.get_model("accounts", "Role")
        cls.users = {}
        for code in ("super_admin", "manager", "worker", "accountant", "listing_team"):
            cls.users[code] = User.objects.create_user(
                f"dev.bod.{code}@test.local", "x", role=Role.objects.get(code=code))
        cls.url = reverse("bod:dashboard")

    def test_super_admin_renders_the_shell(self):
        self.client.force_login(self.users["super_admin"])
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)
        body = r.content.decode()
        for label in ("Business Attention", "Production",
                      "Raw Materials &amp; Warehouses",   # Django auto-escapes '&'
                      "Workers", "Financial Overview", "Machines"):
            self.assertIn(label, body)
        self.assertIn("Last Updated", body)   # BOD-D5 visible as-of
        self.assertIn("Refresh", body)        # BOD-D5 manual refresh

    def test_every_other_role_is_refused_403(self):
        for code in ("manager", "worker", "accountant", "listing_team"):
            self.client.force_login(self.users[code])
            self.assertEqual(self.client.get(self.url).status_code, 403, code)

    def test_anonymous_is_sent_to_login(self):
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 302)
        # LOGIN_URL = /app/ (the email-step login); next preserves the target
        self.assertTrue(r["Location"].startswith("/app/"))
        self.assertIn("next=/bod/", r["Location"])

    def test_post_is_refused_even_for_sa(self):
        self.client.force_login(self.users["super_admin"])
        self.assertEqual(self.client.post(self.url).status_code, 405)

    def test_render_is_read_only_and_within_query_budget(self):
        # Runtime pin: a dashboard GET writes nothing and stays ≤ the ratified
        # BOD-D6 ceiling (≤30 queries/page — the shell should be far under).
        self.client.force_login(self.users["super_admin"])
        self.client.get(self.url)  # warm the session row
        from django.db import connection
        before = {m._meta.label: m.objects.count() for m in apps.get_models()}
        with CaptureQueriesContext(connection) as ctx:
            r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)
        self.assertLessEqual(len(ctx.captured_queries), 30,
                             f"query budget blown: {len(ctx.captured_queries)}")
        self.assertEqual({m._meta.label: m.objects.count() for m in apps.get_models()},
                         before)


class BODRegistryFrameworkTests(TestCase):
    def test_registry_money_widgets_live_only_behind_the_financial_wall(self):
        # BOD-D state (owner-authorized 2026-07-18): every entry's ladder row
        # closed at BOD-B; the FIVE approved money widgets (F1/F2/F5/F6/F3-W3)
        # are ALL financial=True AND all in the charter's financial section —
        # a money tile outside that gated section is structurally impossible.
        self.assertTrue(REGISTRY)
        money = [w for w in REGISTRY if w.financial]
        self.assertEqual(sorted(w.kpi_id for w in money),
                         ["expected-payouts", "expense-categories",
                          "month-expenses", "outstanding-advances",
                          "outstanding-payments"])
        self.assertTrue(all(w.section == "financial" for w in money))
        # And the reverse: the financial section holds ONLY financial widgets.
        self.assertTrue(all(w.financial for w in REGISTRY
                            if w.section == "financial"))

    def test_sections_pin_the_charter_order(self):
        self.assertEqual([k for k, _ in SECTIONS],
                         ["attention", "production", "materials",
                          "workers", "financial", "machines"])

    def test_widget_contract_shape(self):
        fields = set(Widget.__dataclass_fields__)
        self.assertEqual(fields, {"kpi_id", "section", "title", "read_call",
                                  "drill_down", "responsive_strategy",
                                  "financial", "gate"})

    def test_sidebar_item_sa_only(self):
        from accounts.services.permission_service import SIDEBAR
        items = [i for s in SIDEBAR for i in s.items if i.url_name == "bod:dashboard"]
        self.assertEqual(len(items), 1)
        item = items[0]
        User = apps.get_model("accounts", "User")
        Role = apps.get_model("accounts", "Role")
        sa = User.objects.create_user("dev.bod.sb.sa@test.local", "x",
                                      role=Role.objects.get(code="super_admin"))
        mgr = User.objects.create_user("dev.bod.sb.mgr@test.local", "x",
                                       role=Role.objects.get(code="manager"))
        self.assertTrue(item.predicate(sa))
        self.assertFalse(item.predicate(mgr))
        self.assertFalse(item.hidden)
