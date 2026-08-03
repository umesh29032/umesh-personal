"""BOD-C Waves 2+3 — same no-second-truth proof as wave 1: materials tiles ==
roll_service, production extras == the G-4 extraction, workers tile == the
distinct over pending_report_tasks, and Section 7 = navigation cards ONLY
(owner taste ruling 2026-07-18: pure links, zero counts)."""

from django.test import TestCase
from django.urls import reverse

from bod.tests.test_widgets_wave1 import make_sa, tiles_by_id


class Wave2MaterialsCrossCheckTests(TestCase):
    def test_materials_tiles_equal_roll_service(self):
        from raw_materials.services import roll_service
        self.client.force_login(make_sa("dev.bod.w2.sa@test.local"))
        r = self.client.get(reverse("bod:dashboard"))
        tiles = tiles_by_id(r)

        c = roll_service.stock_status_counts()
        self.assertEqual(tiles["roll-stock"]["tile"]["value"], c["available"])
        self.assertEqual(dict(tiles["roll-stock"]["tile"]["sub"])["total"], c["total"])

        rows = list(roll_service.stock_by_location())
        self.assertEqual(tiles["stock-by-warehouse"]["tile"]["value"], len(rows))


class Wave3ProductionCrossCheckTests(TestCase):
    def test_wave3_tiles_equal_their_authoritative_sources(self):
        from production.services.operations_digest import (
            adda_status_counts, pending_report_tasks, stage_breakdown)
        self.client.force_login(make_sa("dev.bod.w3.sa@test.local"))
        r = self.client.get(reverse("bod:dashboard"))
        tiles = tiles_by_id(r)

        self.assertEqual(tiles["on-hold-addas"]["tile"]["value"],
                         adda_status_counts()["on_hold"])

        chips = stage_breakdown()
        self.assertEqual(tiles["stage-chips"]["tile"]["sub"],
                         [(c["label"], c["count"]) for c in chips])
        self.assertEqual(tiles["stage-chips"]["tile"].get("kind"), "chips")

        n = pending_report_tasks().values("worker").distinct().count()
        self.assertEqual(tiles["workers-active"]["tile"]["value"], n)


class Section7NavCardTests(TestCase):
    def test_nav_cards_are_pure_links_with_no_counts(self):
        from bod.registry import NAV_CARDS
        self.client.force_login(make_sa("dev.bod.w3b.sa@test.local"))
        r = self.client.get(reverse("bod:dashboard"))
        body = r.content.decode()
        self.assertIn("Other Business Modules", body)
        self.assertEqual(len(NAV_CARDS), 3)
        for title, url_name, desc in NAV_CARDS:
            self.assertIn(f'href="{reverse(url_name)}"', body)
            self.assertIn(title, body)
        # nav_cards carry NO numeric payload anywhere in their declaration
        for card in NAV_CARDS:
            self.assertEqual(len(card), 3)
            self.assertTrue(all(isinstance(x, str) for x in card))
