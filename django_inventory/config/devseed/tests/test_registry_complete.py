"""SEED-D — registry completeness: every implemented scenario seeds through
the engine, its post-step evidence holds, and a second run converges (skip,
never duplicate). The whole-registry test simulates the shared-scratch-DB
reality: ALL worlds on ONE database, sequentially, twice."""

from decimal import Decimal

from django.apps import apps
from django.test import TestCase

from devseed import core
from devseed.scenarios import SCENARIOS

W = "@test.local"

# The 3 golden recipes are proven byte-identical in test_golden_journeys (and
# re-converged here via the factory composite) — excluded from the loop to
# keep battery runtime honest (D9: runtimes recorded, goldens stay covered).
LOOP_EXCLUDED = {"regression-lower", "regression-tshirt", "regression-3patti"}


def implemented_slugs():
    return [k for k, s in SCENARIOS.items() if s["implemented"]]


class RegistryCompleteTests(TestCase):
    maxDiff = None

    # ── whole-registry: one DB, every world, twice ───────────────────────────
    def test_whole_registry_seeds_and_converges_on_one_database(self):
        slugs = [s for s in implemented_slugs() if s not in LOOP_EXCLUDED]
        for slug in slugs:
            m = core.seed_scenario(slug)
            self.assertEqual(m["assertions"]["result"], "PASS", slug)
        # second pass: pure convergence — nothing new anywhere
        for slug in slugs:
            m2 = core.seed_scenario(slug)
            self.assertEqual(m2["assertions"]["result"], "PASS", slug)
            for layer, c in m2["counts"].items():
                self.assertEqual(c["created"], 0, f"{slug} {layer} re-created rows")

    # ── demo / factory (SEED-D2) ─────────────────────────────────────────────
    def test_demo_is_a_settled_minimal_plus_world(self):
        m = core.seed_scenario("demo")
        self.assertEqual(m["money"]["expected_total"], "150.00")
        self.assertEqual(m["assertions"]["result"], "PASS")

    def test_factory_composite_carries_the_three_goldens_plus_machines(self):
        m = core.seed_scenario("factory")
        self.assertEqual(
            set(m["composite"]),
            {"regression-lower", "regression-tshirt", "regression-3patti",
             "feature-machines"})
        goldens = {c: cm["money"]["expected_total"]
                   for c, cm in m["composite"].items() if cm["money"]}
        self.assertEqual(goldens, {"regression-lower": "344.25",
                                   "regression-tshirt": "801.00",
                                   "regression-3patti": "633.00"})
        MA = apps.get_model("machines", "MachineAssignment")
        self.assertTrue(MA.objects.filter(machine__code="DEV-MCH-M1",
                                          end_at__isnull=True).exists())

    # ── feature slices ───────────────────────────────────────────────────────
    def test_allocation_world_draws_down_a_real_pool(self):
        m = core.seed_scenario("feature-allocation")
        WSA = apps.get_model("production", "WorkerStageAllocation")
        wsa = WSA.objects.get(
            stage_record__adda__product__code="DEV-ALC-TEE", voided_at__isnull=True)
        self.assertEqual(wsa.allocated_quantity, Decimal("30"))
        self.assertEqual(Decimal(m["post"]["available_after"]), Decimal("20"))

    def test_fnf_world_deactivates_the_dedicated_leaver_only(self):
        core.seed_scenario("feature-fnf")
        User = apps.get_model("accounts", "User")
        self.assertFalse(User.objects.get(email="dev.min.leaver" + W).is_active)
        # the shared cast member is untouched — isolation law
        self.assertTrue(User.objects.get(email="dev.min.worker" + W).is_active)

    def test_machines_world_opens_a_possession_window(self):
        core.seed_scenario("feature-machines")
        MA = apps.get_model("machines", "MachineAssignment")
        self.assertEqual(MA.objects.filter(machine__code="DEV-MCH-M1",
                                           end_at__isnull=True).count(), 1)

    def test_patterns_world_registers_sizes_and_patterns(self):
        core.seed_scenario("feature-patterns-ai")
        PS = apps.get_model("production", "ProductSize")
        PPA = apps.get_model("production", "ProductPatternAssignment")
        self.assertEqual(PS.objects.filter(product__code="DEV-PAI-TEE").count(), 2)
        self.assertEqual(PPA.objects.filter(product__code="DEV-PAI-TEE").count(), 2)

    def test_storefront_world_seeds_category_and_featured_product(self):
        core.seed_scenario("feature-storefront")
        Category = apps.get_model("storefront", "Category")
        FP = apps.get_model("storefront", "FeaturedProduct")
        self.assertTrue(Category.objects.filter(name="DEV-SF Category").exists())
        self.assertTrue(FP.objects.filter(name="DEV-SF Featured Tee").exists())

    def test_tracking_world_inline_generates_barcodes(self):
        m = core.seed_scenario("feature-tracking-exports")
        self.assertGreater(m["post"]["barcode_batches"], 0)

    def test_monthly_expense_world_templates_generation_and_voided_example(self):
        # A3 (MEE-E): templates + generated period + one voided example,
        # all through the census-ADDENDUM-1 writers.
        m = core.seed_scenario("feature-monthly-expense")
        self.assertGreaterEqual(m["post"]["covers_2026_07"], 2)
        Tpl = apps.get_model("expense", "ExpenseTemplate")
        Cover = apps.get_model("expense", "ExpenseGenerationRecord")
        self.assertEqual(Tpl.objects.filter(
            label__startswith="DEV-MEE").count(), 2)
        rent = Cover.objects.get(template__label="DEV-MEE Rent",
                                 period_key="2026-07",
                                 superseded_at__isnull=True)
        self.assertIsNotNone(rent.expense.voided_at)   # the voided example
        sal = Cover.objects.get(template__label="DEV-MEE Salary",
                                period_key="2026-07",
                                superseded_at__isnull=True)
        self.assertIsNone(sal.expense.voided_at)

    def test_rm_expense_world_fixtures(self):
        # A4 (RMX-F): priced/unpriced/damaged + the REAL leftover chain.
        m = core.seed_scenario("feature-rm-expense")
        self.assertTrue(m["post"]["leftover_consumed"])
        ClothRoll = apps.get_model("raw_materials", "ClothRoll")
        rolls = {r.roll_id: r for r in ClothRoll.objects.filter(
            cloth_type__name="DEV-RME-COTTON")}
        self.assertEqual(rolls[m["post"]["priced_roll"]].cost_per_kg,
                         Decimal("100.00"))
        self.assertEqual(rolls[m["post"]["damaged_roll"]].status, "damaged")
        # the journey's consumed roll stays UNPRICED — the banner world
        consumed = next(r for r in rolls.values()
                        if r.status == "used")
        self.assertIsNone(consumed.cost_per_kg)
        # the chain: source adda's derive is net of the remnant; the target
        # carries leftover_in at SOURCE price — but source roll is unpriced,
        # so BOTH stay honest (flags, not rupees).
        from production.services.cost_service import material_cost_for_adda
        Adda = apps.get_model("production", "Adda")
        target = Adda.objects.get(code=m["post"]["chain_target"])
        t = material_cost_for_adda(target)
        self.assertEqual(t["net"], Decimal("0.00"))      # unpriced source roll
        self.assertEqual(t["unpriced_rolls"], 1)         # honest flag carried

    def test_bod_world_lights_the_dashboard_owning_services(self):
        # D8 (spec amendment A2): settled money + one DEV expense, proven at
        # the board's OWNING services (the BOD itself owns nothing).
        m = core.seed_scenario("feature-bod")
        self.assertGreaterEqual(Decimal(m["post"]["month_total"]),
                                Decimal("100.00"))
        self.assertGreater(Decimal(m["post"]["pending_payable"]), Decimal("0"))
        FE = apps.get_model("expense", "FactoryExpense")
        self.assertEqual(FE.objects.filter(
            notes__startswith="DEV feature-bod", voided_at__isnull=True).count(), 1)

    # ── edge-case worlds ─────────────────────────────────────────────────────
    def test_overallocation_is_refused_verbatim(self):
        m = core.seed_scenario("edge-overallocation-m6")
        self.assertIn("Cannot allocate", m["post"]["refusal"])

    def test_damaged_roll_round_trips_to_available(self):
        m = core.seed_scenario("edge-damaged-rolls")
        self.assertEqual(m["post"]["final_status"], "not_used")

    def test_monthly_worker_pay_basis_is_set(self):
        core.seed_scenario("edge-monthly-worker")
        WP = apps.get_model("expense", "WorkerProfile")
        self.assertTrue(WP.objects.filter(
            user__email="dev.min.monthly" + W, pay_basis=WP.PayBasis.MONTHLY).exists())

    def test_inactive_user_world(self):
        core.seed_scenario("edge-inactive-users")
        User = apps.get_model("accounts", "User")
        self.assertFalse(User.objects.get(email="dev.min.inactive" + W).is_active)

    def test_reopen_guard_refuses_on_the_settled_world(self):
        m = core.seed_scenario("edge-reopen-guard")
        self.assertTrue(m["post"]["refusal"])

    def test_composite_roles_world(self):
        core.seed_scenario("edge-composite-roles")
        from accounts.services import permission_service
        User = apps.get_model("accounts", "User")
        u = User.objects.get(email="dev.min.acct.mgr" + W)
        self.assertTrue(permission_service.user_has_role(u, ["manager"]))
        self.assertTrue(permission_service.user_has_role(u, ["accountant"]))

    def test_rate_correction_recalcs_and_audits(self):
        core.seed_scenario("edge-rate-correction")
        Audit = apps.get_model("production", "RateCorrectionAudit")
        WSC = apps.get_model("production", "WorkerStageContribution")
        self.assertTrue(Audit.objects.filter(
            stage_record__adda__product__code="DEV-RRC-TEE").exists())
        wsc = WSC.objects.get(task__stage_record__adda__product__code="DEV-RRC-TEE")
        # 50 good × corrected ₹4 — the recalc law (S1.1 auto-recalc)
        self.assertEqual(wsc.expected_earning, Decimal("200"))

    def test_settlement_supersession_chain(self):
        m = core.seed_scenario("edge-settlement-supersession")
        AS_ = apps.get_model("expense", "AddaSettlement")
        original = AS_.objects.get(adda__product__code="DEV-SUP-TEE",
                                   status="superseded")
        successor = original.superseded_by.get()
        self.assertEqual(successor.status, "finalized")
        self.assertEqual(str(successor.expected_total), "150.00")
        self.assertIn("→", m["post"]["chain"])
