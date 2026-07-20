"""SEED-C wave-1 money suite — the deterministic golden world
(`feature-settlement`): full journey through the certified chokepoints, golden
₹150.00 byte-assert, ledger recount, idempotency, layer-7 journey for
`minimal`. U8-hostile: every money row = a service outcome (see test_purity)."""

from decimal import Decimal

from django.apps import apps
from django.test import TestCase

from devseed import core


class MinimalJourneyTests(TestCase):
    """Layer 7 on the `minimal` scenario (journey, no money)."""

    def test_minimal_journey_completes_adda(self):
        manifest = core.seed_scenario("minimal")
        Adda = apps.get_model("production", "Adda")
        adda = Adda.objects.get(product__code="DEV-MIN-TEE")
        self.assertEqual(adda.status, Adda.Status.COMPLETED)
        self.assertEqual(manifest["counts"]["7-production-truth"], {"created": 1, "skipped": 0})
        # Production truth exists as SERVICE OUTCOMES:
        WSC = apps.get_model("production", "WorkerStageContribution")
        self.assertEqual(
            WSC.objects.filter(task__stage_record__adda=adda).count(), 1)  # the one generic stage

    def test_minimal_journey_idempotent(self):
        core.seed_scenario("minimal")
        m2 = core.seed_scenario("minimal")
        self.assertEqual(m2["counts"]["7-production-truth"], {"created": 0, "skipped": 1})


class GoldenSettlementTests(TestCase):
    """Layer 8: the deterministic money world — golden ₹150.00."""

    def test_golden_settlement_150(self):
        manifest = core.seed_scenario("feature-settlement")
        self.assertIsNotNone(manifest["money"])
        self.assertEqual(manifest["money"]["expected_total"], "150.00")
        AS_ = apps.get_model("expense", "AddaSettlement")
        s = AS_.objects.get(reference=manifest["money"]["settlement"])
        self.assertEqual(s.status, "finalized")
        self.assertEqual(s.expected_total, Decimal("150.00"))

    def test_ledger_recount_delta_fully_explained(self):
        manifest = core.seed_scenario("feature-settlement")
        before = Decimal(manifest["money"]["ledger_before"]["sum"])
        after = Decimal(manifest["money"]["ledger_after"]["sum"])
        self.assertEqual(after - before, Decimal("150.00"))
        # And the worker's balance == the golden total (single credit).
        from expense.services import ledger_service
        User = apps.get_model("accounts", "User")
        worker = User.objects.get(email="dev.min.worker@test.local")
        self.assertEqual(ledger_service.worker_balance(worker), Decimal("150.00"))

    def test_money_world_idempotent(self):
        core.seed_scenario("feature-settlement")
        L = apps.get_model("expense", "WorkerLedgerEntry")
        n1 = L.objects.count()
        m2 = core.seed_scenario("feature-settlement")
        self.assertEqual(L.objects.count(), n1)  # zero new ledger rows
        self.assertEqual(m2["counts"]["7-production-truth"], {"created": 0, "skipped": 1})
        self.assertEqual(m2["counts"]["8-money"], {"created": 0, "skipped": 1})

    def test_flags_never_touched(self):
        # Seeding must never flip an enforcement flag. (ENFORCE_ALLOCATION_BOUND was retired
        # 2026-07-20 — the bound is now unconditional; the settlement flag remains the lever.)
        from django.conf import settings
        core.seed_scenario("feature-settlement")
        self.assertFalse(getattr(settings, "ENFORCE_SETTLEMENT_RECONCILIATION", False))
