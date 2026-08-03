"""SEED-B layer suite — foundation executors 2–6: service-path fidelity,
idempotency (double-seed converge), divergence REPORT-never-pave, DEV-marking,
and service-refusal propagation. TestCase: every test runs on the isolated
test database (created/destroyed by the runner); commands stay guard-refused
there (SEED-A suite) — these tests exercise the ORCHESTRATION CORE directly,
the contract's testable-without-CLI design."""

from django.apps import apps
from django.core.exceptions import PermissionDenied
from django.test import TestCase

from devseed import core
from devseed.layers import DivergenceError
from devseed.layers.machines import seed_machines
from devseed.scenarios.minimal import MINIMAL


class MinimalScenarioTests(TestCase):
    def counts(self):
        g = apps.get_model
        return {
            "users": g("accounts", "User").objects.filter(email__startswith="dev.min.").count(),
            "types": g("raw_materials", "ClothType").objects.filter(name__startswith="DEV-MIN").count(),
            "colors": g("raw_materials", "ClothColor").objects.filter(name__startswith="DEV-MIN").count(),
            "storage": g("raw_materials", "StorageLocation").objects.filter(name__startswith="DEV-MIN").count(),
            "cats": g("production", "StageCategory").objects.filter(code="dev-min").count(),
            "stages": g("production", "Stage").objects.filter(code__startswith="dev-min-").count(),
            "products": g("production", "Product").objects.filter(code="DEV-MIN-TEE").count(),
            "flow": g("production", "WorkflowStage").objects.filter(product__code="DEV-MIN-TEE").count(),
            "rolls": g("raw_materials", "ClothRoll").objects.filter(cloth_type__name="DEV-MIN-COTTON").count(),
        }

    def test_minimal_foundation_slice_seeds_and_asserts(self):
        manifest = core.seed_scenario("minimal")
        self.assertEqual(manifest["assertions"]["result"], "PASS")
        self.assertEqual(
            self.counts(),
            {"users": 3, "types": 1, "colors": 1, "storage": 1, "cats": 1,
             "stages": 1, "products": 1, "flow": 3, "rolls": 1},  # flow = layering + cutting + stitching
        )

    def test_idempotency_double_seed_converges(self):
        core.seed_scenario("minimal")
        first = self.counts()
        manifest2 = core.seed_scenario("minimal")
        self.assertEqual(self.counts(), first)  # zero new rows anywhere
        for layer, c in manifest2["counts"].items():
            self.assertEqual(c["created"], 0, f"{layer} created rows on re-seed")

    def test_flow_order_matches_scenario(self):
        core.seed_scenario("minimal")
        WorkflowStage = apps.get_model("production", "WorkflowStage")
        codes = list(
            WorkflowStage.objects.filter(product__code="DEV-MIN-TEE")
            .order_by("order").values_list("stage__code", flat=True)
        )
        # layering = the service-attached mandatory first stage (production law)
        self.assertEqual(codes, ["layering", "cutting", "dev-min-stitching"])

    def test_rolls_created_via_service_with_history_and_no_financials(self):
        core.seed_scenario("minimal")
        ClothRoll = apps.get_model("raw_materials", "ClothRoll")
        roll = ClothRoll.objects.get(cloth_type__name="DEV-MIN-COTTON")
        self.assertTrue(roll.roll_id.startswith("CR-"))  # sequence-assigned output handle
        self.assertIsNone(roll.cost_per_kg)  # honest-NULL: manager actor, no FINANCIAL_ROLES
        self.assertEqual(roll.supplier, "")
        History = apps.get_model("tracking", "ClothRollHistory")
        # CREATED (intake) + ROLL_ASSIGNED (journey attach) — both via history_service.
        self.assertEqual(History.objects.filter(roll_id=roll.pk).count(), 2)

    def test_divergence_reported_never_paved(self):
        core.seed_scenario("minimal")
        User = apps.get_model("accounts", "User")
        Role = apps.get_model("accounts", "Role")
        u = User.objects.get(email="dev.min.mgr@test.local")
        u.role = Role.objects.get(code="worker")
        u.save(update_fields=["role"])
        with self.assertRaises(DivergenceError):
            core.seed_scenario("minimal")
        u.refresh_from_db()
        self.assertEqual(u.role.code, "worker")  # NOT auto-corrected

    def test_world_rolls_back_atomically_on_midseed_failure(self):
        # Unknown stage code in the flow → get() raises INSIDE the atomic block
        # → the whole world (incl. cast + masters) must vanish.
        broken = {**MINIMAL, "flow": ["cutting", "no-such-stage"]}
        core.CONTENT["broken-minimal"] = broken
        try:
            with self.assertRaises(Exception):
                core.seed_scenario("broken-minimal")
        finally:
            core.CONTENT.pop("broken-minimal", None)
        self.assertEqual(self.counts()["users"], 0)
        self.assertEqual(self.counts()["products"], 0)

    def test_service_refusal_propagates_never_swallowed(self):
        # Worker actor may not create products (super_admin-only gate) — the
        # service refusal must surface verbatim (contract §4: never
        # catch-and-ignore).
        worker_first = {**MINIMAL, "sa_handle": "dev.min.worker@test.local"}
        core.CONTENT["worker-first"] = worker_first
        try:
            with self.assertRaises(PermissionDenied):
                core.seed_scenario("worker-first")
        finally:
            core.CONTENT.pop("worker-first", None)


class MachinesExecutorTests(TestCase):
    """Layer 5 executor (minimal scenario skips it — proven directly)."""

    def _actor(self):
        User = apps.get_model("accounts", "User")
        Role = apps.get_model("accounts", "Role")
        return User.objects.create_user(
            "dev.min.machinist@test.local", "Dev@12345",
            role=Role.objects.get(code="manager"))

    SPEC = {"machine_type": "DEV-MIN Machine",
            "machines": [{"code": "DEV-MIN-M1", "name": "DEV-MIN Overlock"}]}

    def test_machines_seed_and_idempotency(self):
        actor = self._actor()
        r1 = seed_machines(self.SPEC, actor=actor)
        self.assertEqual(r1["created"], 2)  # type + machine
        r2 = seed_machines(self.SPEC, actor=actor)
        self.assertEqual(r2["created"], 0)
        self.assertEqual(r2["skipped"], 2)
        Machine = apps.get_model("machines", "Machine")
        self.assertEqual(Machine.objects.filter(code="DEV-MIN-M1").count(), 1)
