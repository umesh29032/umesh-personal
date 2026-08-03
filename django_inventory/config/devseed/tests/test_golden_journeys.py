"""SEED-C Wave-2 — the three executable golden journeys, replayed from the
extracted certified recipes. The totals are asserted to EMERGE from
rates × good quantities through the certified services (never hardcoded in
the engine). Per-worker item breakdowns are asserted against the extracted
settlement truth (ADST-0004/0005/0006)."""

from decimal import Decimal

from django.apps import apps
from django.test import TestCase

from devseed import core

W = "@test.local"

# Extracted per-worker settlement truth (read-only extraction 2026-07-17).
EXPECTED_ITEMS = {
    "regression-lower": {
        "dev.ow.a" + W: "47.50", "dev.ow.b" + W: "50.00", "dev.flat.a" + W: "39.00",
        "dev.sn.a" + W: "29.25", "dev.el.a" + W: "78.00", "dev.chk.a" + W: "27.00",
        "dev.iron.a" + W: "36.00", "dev.fin.a" + W: "37.50",
    },
    "regression-tshirt": {
        "dev.ow.a" + W: "45.00", "dev.ow.b" + W: "315.00", "dev.sw.b" + W: "120.00",
        "dev.flat.a" + W: "120.00", "dev.sn.a" + W: "45.00", "dev.chk.a" + W: "42.00",
        "dev.iron.a" + W: "56.00", "dev.fin.a" + W: "58.00",
    },
    "regression-3patti": {
        "dev.ow.a" + W: "205.00", "dev.ow.b" + W: "85.00", "dev.flat.a" + W: "87.00",
        "dev.sn.a" + W: "43.50", "dev.el.a" + W: "116.00", "dev.chk.a" + W: "40.50",
        "dev.fin.a" + W: "29.00", "dev.fin.b" + W: "27.00",
    },
}

GOLDEN = {"regression-lower": "344.25", "regression-tshirt": "801.00",
          "regression-3patti": "633.00"}


class GoldenJourneyReplayTests(TestCase):
    maxDiff = None

    def replay_and_assert(self, slug):
        manifest = core.seed_scenario(slug)
        # the golden EMERGED through the services and matched the recipe target
        self.assertEqual(manifest["money"]["expected_total"], GOLDEN[slug])
        AS_ = apps.get_model("expense", "AddaSettlement")
        s = AS_.objects.get(reference=manifest["money"]["settlement"])
        self.assertEqual(str(s.expected_total), GOLDEN[slug])
        self.assertEqual(s.status, "finalized")
        # per-worker breakdown == the extracted certified items
        got = {i.worker.email: str(i.expected_earning) for i in s.items.all()}
        self.assertEqual(got, EXPECTED_ITEMS[slug])
        # ledger delta fully explained
        before = Decimal(manifest["money"]["ledger_before"]["sum"])
        after = Decimal(manifest["money"]["ledger_after"]["sum"])
        self.assertEqual(after - before, Decimal(GOLDEN[slug]))
        return manifest

    def test_lower_replays_344_25(self):
        self.replay_and_assert("regression-lower")

    def test_tshirt_replays_801_00(self):
        self.replay_and_assert("regression-tshirt")

    def test_3patti_replays_633_00(self):
        self.replay_and_assert("regression-3patti")

    def test_golden_journey_idempotent(self):
        core.seed_scenario("regression-3patti")
        L = apps.get_model("expense", "WorkerLedgerEntry")
        n = L.objects.count()
        m2 = core.seed_scenario("regression-3patti")
        self.assertEqual(m2["counts"]["7-production-truth"], {"created": 0, "skipped": 1})
        self.assertEqual(m2["counts"]["8-money"], {"created": 0, "skipped": 1})
        self.assertEqual(L.objects.count(), n)
