"""VER-B — dev-world verification proofs: green runs on REAL seeded worlds,
intentionally constructed failing worlds per category, report/exit-code
correctness, determinism, manifest refusal, and the single-source pins
(no duplicated assertion logic, ZERO golden literals in the engine).

Command-level runs stay impossible in the battery BY DESIGN (polarity refuses
under DEBUG=False — pinned in test_guard); engine logic is proven here via the
check runner directly, and the live command end-to-end proof is VER-B log
evidence on a scratch world (the Phase-12 pattern)."""

import os
import re
from decimal import Decimal

from django.apps import apps
from django.test import TestCase

import verification
from devseed import core
from verification.checks import dev_world
from verification.manifests import ManifestMissing, latest_manifest
from verification.report import build_report, exit_code


def by_id(results):
    return {r.id: r for r in results}


class DevWorldGreenTests(TestCase):
    """Pass proofs on a REAL seeded demo world (test DB = the world's DB, so
    the database-match check exercises its true semantics)."""

    def seed_demo(self):
        return core.seed_scenario("demo")

    def test_demo_world_verifies_green(self):
        manifest = self.seed_demo()
        results, skipped = dev_world.run_checks("demo", manifest)
        self.assertEqual(skipped, [])
        statuses = {r.id: r.status for r in results}
        self.assertEqual({s for s in statuses.values()}, {"pass"}, statuses)
        # every check carries a citation (VER-D4)
        self.assertTrue(all(r.citation for r in results))
        report = build_report(command="verify_demo", environment="dev", results=results)
        self.assertEqual(exit_code(report), 0)
        # golden check consumed the certified ₹ value — from the source, not a literal
        golden = by_id(results)["dev.golden.settlement-total"]
        from devseed.scenarios.minimal_money import MINIMAL_MONEY
        self.assertEqual(golden.measured["expected"],
                         MINIMAL_MONEY["settlement"]["expected_total"])

    def test_reports_are_deterministic_across_runs(self):
        manifest = self.seed_demo()
        r1, _ = dev_world.run_checks("demo", manifest)
        r2, _ = dev_world.run_checks("demo", manifest)
        rep1 = build_report(command="verify_demo", environment="dev", results=r1)
        rep2 = build_report(command="verify_demo", environment="dev", results=r2)
        self.assertEqual(rep1["envelope"]["body_hash"], rep2["envelope"]["body_hash"])
        self.assertEqual(rep1["body"], rep2["body"])

    def test_skip_is_explicit_and_reported(self):
        manifest = self.seed_demo()
        results, skipped = dev_world.run_checks("demo", manifest,
                                                skip_categories=["smoke"])
        self.assertEqual(skipped, ["smoke"])
        self.assertFalse([r for r in results if r.category == "smoke"])
        rep = build_report(command="verify_demo", environment="dev",
                           results=results, skipped_categories=skipped)
        self.assertEqual(rep["envelope"]["skipped_categories"], ["smoke"])


class DevWorldConstructedFailTests(TestCase):
    """A verifier that can only say yes never certifies — every category
    demonstrably catches its failure class (constructed in the test DB)."""

    def test_tampered_spec_version_fails(self):
        manifest = core.seed_scenario("demo")
        manifest["spec_version"] = "9.9.9"
        r = by_id(dev_world.run_checks("demo", manifest)[0])
        self.assertEqual(r["dev.manifest.spec-version"].status, "fail")

    def test_database_mismatch_fails(self):
        manifest = core.seed_scenario("demo")
        manifest["database"] = "inventory_seed_scratch_1"  # not THIS connection
        r = by_id(dev_world.run_checks("demo", manifest)[0])
        self.assertEqual(r["dev.manifest.database-match"].status, "fail")

    def test_world_drift_caught_by_assertion_rerun(self):
        manifest = core.seed_scenario("demo")
        # Constructed drift: a seeded master handle vanishes (rename).
        CT = apps.get_model("raw_materials", "ClothType")
        CT.objects.filter(name="DEV-DEMO-COTTON").update(name="DEV-DEMO-GONE")
        r = by_id(dev_world.run_checks("demo", manifest)[0])
        self.assertEqual(r["dev.assertions.rerun"].status, "fail")
        self.assertIn("DEV-DEMO-COTTON", str(r["dev.assertions.rerun"].measured))

    def test_golden_total_tamper_fails_with_nonzero_exit(self):
        manifest = core.seed_scenario("demo")
        AS_ = apps.get_model("expense", "AddaSettlement")
        AS_.objects.filter(adda__product__code="DEV-DEMO-TEE").update(
            expected_total=Decimal("151.00"))
        results, _ = dev_world.run_checks("demo", manifest)
        r = by_id(results)
        self.assertEqual(r["dev.golden.settlement-total"].status, "fail")
        self.assertEqual(r["dev.golden.settlement-total"].measured["got"], "151.00")
        rep = build_report(command="verify_demo", environment="dev", results=results)
        self.assertGreaterEqual(exit_code(rep), 1)

    def test_smoke_catches_unresolvable_route(self):
        r = dev_world.check_smoke_urlconf(routes=("no_such_route_name",))
        self.assertEqual(r.status, "fail")
        self.assertEqual(r.measured["unresolved"], ["no_such_route_name"])

    def test_smoke_catches_missing_cast_identity(self):
        r = dev_world.check_smoke_render_critical("dev.nobody@test.local")
        self.assertEqual(r.status, "fail")


class RegressionWorldTests(TestCase):
    """Golden byte-match + certified worker-item truth on a replayed golden
    journey (single source: the extracted SEED-C W2 maps)."""

    def test_3patti_golden_and_items_verify_green(self):
        manifest = core.seed_scenario("regression-3patti")
        results, _ = dev_world.run_checks("regression-3patti", manifest)
        r = by_id(results)
        self.assertEqual(r["dev.golden.settlement-total"].status, "pass")
        self.assertEqual(r["dev.golden.settlement-total"].measured["expected"], "633.00")
        self.assertEqual(r["dev.golden.worker-items"].status, "pass")

    def test_tampered_worker_item_fails(self):
        manifest = core.seed_scenario("regression-3patti")
        ASI = apps.get_model("expense", "AddaSettlementItem")
        item = ASI.objects.filter(
            adda_settlement__adda__product__code="3-PATTI").order_by("id").first()
        ASI.objects.filter(pk=item.pk).update(expected_earning=Decimal("999.00"))
        r = by_id(dev_world.run_checks("regression-3patti", manifest)[0])
        self.assertEqual(r["dev.golden.worker-items"].status, "fail")


class FactoryCompositeTests(TestCase):
    """The composite world: all three goldens + items + child assertion
    re-runs through ONE verify pass."""

    def test_factory_verifies_green_with_all_three_goldens(self):
        manifest = core.seed_scenario("factory")
        results, _ = dev_world.run_checks("factory", manifest)
        r = by_id(results)
        expected = {"regression-lower": "344.25", "regression-tshirt": "801.00",
                    "regression-3patti": "633.00"}
        for child, golden in expected.items():
            total = r[f"dev.child.{child}.golden.settlement-total"]
            self.assertEqual(total.status, "pass", total.measured)
            self.assertEqual(total.measured["expected"], golden)
            self.assertEqual(r[f"dev.child.{child}.golden.worker-items"].status, "pass")
            self.assertEqual(r[f"dev.child.{child}.assertions.rerun"].status, "pass")
        self.assertEqual({res.status for res in results}, {"pass"})


class ManifestIngestionTests(TestCase):
    def test_missing_manifest_refusal_names_the_seeder(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            for slug, remedy in (("demo", "seed_demo"), ("factory", "seed_factory"),
                                 ("feature-fnf", "seed_feature feature-fnf")):
                with self.assertRaises(ManifestMissing) as ctx:
                    latest_manifest(slug, d)
                self.assertIn(remedy, str(ctx.exception))
                self.assertIn("never seeds", str(ctx.exception))

    def test_latest_manifest_picks_newest(self):
        import json
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            for stamp, marker in (("2026-07-17T010000", "old"), ("2026-07-17T020000", "new")):
                with open(os.path.join(d, f"demo-{stamp}.json"), "w") as fh:
                    json.dump({"marker": marker}, fh)
            self.assertEqual(latest_manifest("demo", d)["marker"], "new")

    def test_feature_slug_validation(self):
        self.assertIsNone(dev_world.feature_slug_failure("feature-settlement"))
        self.assertIn("Unknown scenario", dev_world.feature_slug_failure("nope"))
        self.assertIn("not executable",
                      dev_world.feature_slug_failure("regression-settlement-225"))


class SingleSourceTests(TestCase):
    """Owner VER-B law: never duplicate assertion logic or golden constants."""

    def test_no_golden_literals_in_engine_source(self):
        pattern = re.compile(r"\b(344\.25|801\.00|633\.00|150\.00|10,?880)\b")
        offenders = []
        vdir = os.path.dirname(verification.__file__)
        for root, dirs, files in os.walk(vdir):
            dirs[:] = [x for x in dirs if x != "__pycache__"]
            if os.sep + "tests" in root:
                continue
            for f in files:
                if f.endswith(".py"):
                    src = open(os.path.join(root, f), encoding="utf-8").read()
                    if pattern.search(src):
                        offenders.append(os.path.relpath(os.path.join(root, f), vdir))
        self.assertEqual(offenders, [], "golden literals duplicated in the engine")

    def test_rerun_check_uses_the_shared_library(self):
        # The rerun check calls verification.assertions.run_post_seed — the
        # SEED-D6 single implementation (no second assertion engine exists;
        # test_shared_library pins the tree-wide uniqueness).
        import inspect
        src = inspect.getsource(dev_world.check_assertions_rerun)
        self.assertIn("from verification.assertions import", src)
