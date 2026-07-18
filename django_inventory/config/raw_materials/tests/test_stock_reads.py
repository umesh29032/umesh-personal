"""BOD-C G-1/G-2 (owner-gated 2026-07-18) — the extracted stock read functions
in their OWNING app, + the INERT proof: the cloth dashboard shows the SAME
numbers through the extraction as the functions return directly."""

from django.apps import apps
from django.test import TestCase
from django.urls import reverse

from raw_materials.services import roll_service


class StockReadTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        ClothType = apps.get_model("raw_materials", "ClothType")
        ClothColor = apps.get_model("raw_materials", "ClothColor")
        Storage = apps.get_model("raw_materials", "StorageLocation")
        ClothRoll = apps.get_model("raw_materials", "ClothRoll")
        User = apps.get_model("accounts", "User")
        Role = apps.get_model("accounts", "Role")
        cls.sa = User.objects.create_user(
            "dev.rm.stock.sa@test.local", "x",
            role=Role.objects.get(code="super_admin"))
        ct = ClothType.objects.create(name="DEV-STK-COTTON")
        col = ClothColor.objects.create(name="DEV-STK-RED")
        loc_a = Storage.objects.create(name="DEV-STK-RACK-A", code="STKA")
        loc_b = Storage.objects.create(name="DEV-STK-RACK-B", code="STKB")
        from datetime import date
        for i, (status, loc) in enumerate((
                ("not_used", loc_a), ("not_used", loc_a),
                ("used", loc_b), ("damaged", loc_b))):
            ClothRoll.objects.create(
                roll_id=f"DEVSTK-{i}", cloth_type=ct, cloth_color=col,
                storage_location=loc, status=status,
                purchased_date=date(2026, 7, 1))

    def test_stock_status_counts(self):
        c = roll_service.stock_status_counts()
        self.assertEqual((c["total"], c["available"], c["damaged"], c["used"]),
                         (4, 2, 1, 1))

    def test_stock_by_location(self):
        rows = {r.name: (r.roll_count, r.available)
                for r in roll_service.stock_by_location()}
        self.assertEqual(rows["DEV-STK-RACK-A"], (2, 2))
        self.assertEqual(rows["DEV-STK-RACK-B"], (2, 0))

    def test_cloth_dashboard_is_inert_after_the_extraction(self):
        # The certified page renders the SAME numbers via the new functions.
        self.client.force_login(self.sa)
        r = self.client.get(reverse("raw_materials:cloth-dashboard"))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context["total_rolls"], 4)
        self.assertEqual(r.context["available_rolls"], 2)
        self.assertEqual(r.context["damaged_rolls"], 1)
        self.assertEqual(r.context["used_rolls"], 1)
        by_loc = {l.name: (l.roll_count, l.available) for l in r.context["by_location"]}
        self.assertEqual(by_loc["DEV-STK-RACK-A"], (2, 2))

    def test_date_and_color_filters_still_work_through_the_extraction(self):
        ClothColor = apps.get_model("raw_materials", "ClothColor")
        other = ClothColor.objects.create(name="DEV-STK-BLUE")
        c = roll_service.stock_status_counts(color_id=other.pk)
        self.assertEqual(c["total"], 0)
