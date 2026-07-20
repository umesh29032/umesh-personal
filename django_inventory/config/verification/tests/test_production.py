"""VER-C — production-safe verification proofs: green runs, planted
DEV-contamination, migration/flag/integrity constructed fails, the runtime
read-only proof (STRICT row-count identity — this subset never touches the
request cycle), and environment-aware composition.

The battery env classifies as 'prod' (DEBUG False) — which is exactly what
makes production-mode checks and the two everywhere-commands fully testable
here (test DBs are DEV-clean until a test plants contamination)."""

import io
import tempfile
from decimal import Decimal

from django.apps import apps
from django.core.management import CommandError, call_command
from django.test import TestCase, override_settings

from devseed import core
from verification.checks import production
from verification.checks.compose import compose_all
from verification.guard import environment
from verification.report import build_report, exit_code


def by_id(results):
    return {r.id: r for r in results}


class ProductionSubsetGreenTests(TestCase):
    def test_battery_env_classifies_prod(self):
        self.assertEqual(environment(), "prod")

    def test_green_production_verification_on_clean_db(self):
        results = production.run_production_checks("prod")
        statuses = {r.id: r.status for r in results}
        self.assertEqual(set(statuses.values()), {"pass"}, statuses)
        self.assertTrue(all(r.citation for r in results))
        self.assertEqual(exit_code(build_report(command="verify_production",
                                                environment="prod", results=results)), 0)

    def test_runtime_read_only_strict_row_count_identity(self):
        # A REAL world on the DB, then the full subset — STRICT identity
        # (no sessions: this subset never touches the request cycle).
        core.seed_scenario("demo")
        before = {m._meta.label: m.objects.count() for m in apps.get_models()}
        production.run_production_checks("prod")
        production.run_production_checks("dev")
        after = {m._meta.label: m.objects.count() for m in apps.get_models()}
        self.assertEqual(before, after)

    def test_command_verify_production_green(self):
        with tempfile.TemporaryDirectory() as d:
            out = io.StringIO()
            call_command("verify_production", report=d, stdout=out)
            self.assertIn("fail=0", out.getvalue())
            self.assertIn("env=prod", out.getvalue())

    def test_command_verify_all_prod_composes_subset_only(self):
        with tempfile.TemporaryDirectory() as d:
            out = io.StringIO()
            call_command("verify_all", report=d, stdout=out)
            text = out.getvalue()
            self.assertIn("fail=0", text)
            self.assertNotIn("world.", text)          # no dev worlds in prod mode
            self.assertIn("all.composition", text)


class ContaminationTests(TestCase):
    def plant(self):
        User = apps.get_model("accounts", "User")
        Role = apps.get_model("accounts", "Role")
        User.objects.create_user("dev.planted@test.local", "x",
                                 role=Role.objects.get(code="worker"))

    def test_clean_db_passes_prod_mode(self):
        r = production.check_dev_contamination("prod")
        self.assertEqual(r.status, "pass")
        self.assertEqual(r.measured["hits"], {})

    def test_planted_dev_handle_is_caught_in_prod_mode(self):
        self.plant()
        r = production.check_dev_contamination("prod")
        self.assertEqual(r.status, "fail")
        self.assertEqual(r.measured["hits"], {"accounts.User": 1})

    def test_dev_rehearsal_reports_hits_informationally(self):
        self.plant()
        r = production.check_dev_contamination("dev")
        self.assertEqual(r.status, "pass")
        self.assertEqual(r.measured["hits"], {"accounts.User": 1})
        self.assertIn("informational", r.measured["note"])

    def test_planted_contamination_fails_the_whole_command(self):
        self.plant()
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(CommandError) as ctx:
                call_command("verify_production", report=d, stdout=io.StringIO())
            self.assertIn("red check", str(ctx.exception))


class ProductionSafetyFailTests(TestCase):
    # AE-1 (2026-07-20): ENFORCE_ALLOCATION_BOUND retired from the declaration (bound is now
    # always-on). Mismatch detection is proven with the remaining declared flag.
    @override_settings(ENFORCE_SETTLEMENT_RECONCILIATION=True)
    def test_flag_mismatch_fails(self):
        r = production.check_flags_vs_declaration()
        self.assertEqual(r.status, "fail")
        self.assertTrue(r.measured["actual"]["ENFORCE_SETTLEMENT_RECONCILIATION"])

    def test_migrations_consistent_live(self):
        self.assertEqual(production.check_migrations_consistency().status, "pass")

    def test_migration_mismatch_fails_via_injection(self):
        r = production.check_migrations_consistency(
            _plan=lambda: (["expense.0099_future"], []))
        self.assertEqual(r.status, "fail")
        self.assertEqual(r.measured["unapplied"], ["expense.0099_future"])
        r2 = production.check_migrations_consistency(
            _plan=lambda: ([], ["ghost.0001_applied_but_unknown"]))
        self.assertEqual(r2.status, "fail")

    def test_settings_sanity_prod_mode_requires_debug_off(self):
        # battery: DEBUG False → prod-mode sanity passes
        self.assertEqual(production.check_settings_sanity("prod").status, "pass")

    @override_settings(DEBUG=True)
    def test_settings_sanity_fails_with_debug_on_in_prod_mode(self):
        self.assertEqual(production.check_settings_sanity("prod").status, "fail")


class IntegrityFailTests(TestCase):
    def test_settlement_items_sum_catches_tamper(self):
        core.seed_scenario("demo")
        AS_ = apps.get_model("expense", "AddaSettlement")
        AS_.objects.filter(adda__product__code="DEV-DEMO-TEE").update(
            expected_total=Decimal("151.00"))
        r = production.check_settlement_items_sum()
        self.assertEqual(r.status, "fail")
        self.assertEqual(r.measured["violations"][0]["expected_total"], "151.00")

    def test_settlement_items_sum_green_on_real_world(self):
        core.seed_scenario("demo")
        self.assertEqual(production.check_settlement_items_sum().status, "pass")

    def test_reversal_imbalance_fails_via_injection(self):
        r = production.check_ledger_reversals_net(_violators=lambda: 2)
        self.assertEqual(r.status, "fail")
        self.assertEqual(r.measured["mismatched"], 2)

    def test_constraint_predicates_fail_via_injection(self):
        # The DB's own CheckConstraints refuse violating INSERTs — the
        # constructed fail is injected (the run_reset precedent).
        self.assertEqual(production.check_constraint_ledger_amount_positive(
            _violators=lambda: 1).status, "fail")
        self.assertEqual(production.check_constraint_wsc_gam(
            _violators=lambda: 3).status, "fail")

    def test_supersession_chain_green_on_superseded_world(self):
        core.seed_scenario("edge-settlement-supersession")
        self.assertEqual(production.check_supersession_chain().status, "pass")


class CompositionTests(TestCase):
    def test_prod_composition_is_subset_only(self):
        results, _ = compose_all("prod")
        ids = [r.id for r in results]
        self.assertTrue(all(i.startswith(("prod.", "all.")) for i in ids), ids)
        summary = by_id(results)["all.composition"]
        self.assertEqual(summary.measured["worlds_verified"], [])

    def test_dev_composition_is_manifest_driven_and_reports_absent_worlds(self):
        with tempfile.TemporaryDirectory() as d:
            core.seed_scenario("demo", manifest_dir=d)  # ONE manifest present
            results, _ = compose_all("dev", manifest_dir=d)
            ids = [r.id for r in results]
            self.assertTrue(any(i.startswith("world.demo.") for i in ids))
            self.assertFalse(any(i.startswith("world.factory.") for i in ids))
            summary = by_id(results)["all.composition"]
            self.assertEqual(summary.measured["worlds_verified"], ["demo"])
            self.assertIn("factory", summary.measured["worlds_without_manifest"])
            # aggregate is green end-to-end
            rep = build_report(command="verify_all", environment="dev", results=results)
            self.assertEqual(rep["envelope"]["totals"]["fail"], 0)

    def test_composition_never_fails_fast(self):
        # Plant contamination + run prod composition: the red check is
        # AGGREGATED (summary still present after it) — no fail-fast.
        User = apps.get_model("accounts", "User")
        Role = apps.get_model("accounts", "Role")
        User.objects.create_user("dev.planted@test.local", "x",
                                 role=Role.objects.get(code="worker"))
        results, _ = compose_all("prod")
        r = by_id(results)
        self.assertEqual(r["prod.contamination.dev-namespace"].status, "fail")
        self.assertIn("all.composition", r)  # aggregation completed
