"""SEED-A guard suite — every guard factor negatively tested (PHASE_12 §3.2),
pinned forever. SimpleTestCase: no DB rows are read or written by any test
here (the guard reads connection SETTINGS, never data)."""

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase

from devseed import guard
from devseed.scenarios import SCENARIOS, spec_classes_present, valid_slugs


class GuardFactorTests(SimpleTestCase):
    """Pure-function factor tests: wrong value → refusal string; right → None."""

    def test_factor1_settings_module(self):
        self.assertIsNotNone(guard.check_settings_module("config.settings.production"))
        self.assertIsNotNone(guard.check_settings_module("config.settings.base"))
        self.assertIsNone(guard.check_settings_module("config.settings.local"))

    def test_factor2_dev_marker(self):
        self.assertIsNotNone(guard.check_dev_marker(False))
        self.assertIsNone(guard.check_dev_marker(True))

    def test_factor3_db_allowlist_refuses_primary_and_test_dbs(self):
        # The PRIMARY dev DB is deliberately not allowlisted (owner SEED-D5).
        self.assertIsNotNone(guard.check_db_allowlist("inventory_db"))
        self.assertIsNotNone(guard.check_db_allowlist("test_inventory_db"))
        self.assertIsNotNone(guard.check_db_allowlist(""))

    def test_factor3_db_allowlist_accepts_only_ratified_scratch_names(self):
        self.assertIsNone(guard.check_db_allowlist("inventory_seed_scratch_1"))
        self.assertIsNone(guard.check_db_allowlist("inventory_seed_scratch_2"))
        self.assertEqual(len(guard.SCRATCH_DB_ALLOWLIST), 2)

    def test_factor4_reset_confirmation_exact_string(self):
        self.assertIsNotNone(guard.check_reset_confirmation("inventory_seed_scratch_1", None))
        self.assertIsNotNone(
            guard.check_reset_confirmation("inventory_seed_scratch_1", "inventory_seed_scratch_2")
        )
        self.assertIsNone(
            guard.check_reset_confirmation("inventory_seed_scratch_1", "inventory_seed_scratch_1")
        )

    def test_all_factors_pass_with_good_values(self):
        self.assertEqual(
            guard.guard_failures(
                "seed",
                settings_module="config.settings.local",
                debug=True,
                db_name="inventory_seed_scratch_1",
            ),
            [],
        )

    def test_reset_collects_every_failing_factor(self):
        # Never short-circuits: the operator sees the whole wall.
        failures = guard.guard_failures(
            "reset",
            settings_module="config.settings.production",
            debug=False,
            db_name="inventory_db",
            confirmed_db=None,
        )
        self.assertEqual(len(failures), 4)


class CommandGuardTests(SimpleTestCase):
    """Command-level refusals: under the TEST environment DEBUG is False and the
    connection DB is the (non-allowlisted) test DB — so every command must
    refuse via the guard. This doubles as the standing proof that seeder
    commands can never touch a battery/test database."""

    def assert_guard_refused(self, *args, **kwargs):
        with self.assertRaises(CommandError) as ctx:
            call_command(*args, **kwargs)
        self.assertIn("GUARD REFUSED", str(ctx.exception))
        return str(ctx.exception)

    def test_seed_demo_refuses(self):
        msg = self.assert_guard_refused("seed_demo")
        self.assertIn("not an allowlisted scratch DB", msg)

    def test_seed_factory_refuses(self):
        self.assert_guard_refused("seed_factory")

    def test_seed_feature_refuses_with_valid_slug(self):
        self.assert_guard_refused("seed_feature", "feature-machines")

    def test_check_dry_run_does_not_bypass_guard(self):
        # --check is a dry-run, not a guard bypass (guards-before-features law).
        self.assert_guard_refused("seed_demo", check=True)

    def test_reset_refuses_without_confirmation(self):
        msg = self.assert_guard_refused("reset_demo")
        self.assertIn("destructive confirmation missing or mismatched", msg)

    def test_reset_refuses_mismatched_confirmation(self):
        msg = self.assert_guard_refused(
            "reset_demo", db="inventory_seed_scratch_1", confirm_scratch_2=True
        )
        self.assertIn("--i-understand-this-destroys-inventory_seed_scratch_1", msg)

    def test_seed_feature_unknown_slug_lists_valid_ones(self):
        with self.assertRaises(CommandError) as ctx:
            call_command("seed_feature", "no-such-scenario")
        msg = str(ctx.exception)
        self.assertIn("Unknown scenario", msg)
        self.assertIn("feature-machines", msg)  # the list is printed


class RegistryTests(SimpleTestCase):
    """The scenario registry mirrors the frozen spec §7 taxonomy."""

    def test_all_six_spec_classes_present(self):
        self.assertEqual(
            spec_classes_present(),
            ["edge-case", "feature", "full-demo", "minimal", "performance", "regression"],
        )

    def test_golden_regression_values_pinned(self):
        # Golden values = business truth (owner-change-control; spec §7 + §12 A1).
        self.assertEqual(SCENARIOS["regression-tshirt"]["expected"], "801.00")
        self.assertEqual(SCENARIOS["regression-lower"]["expected"], "344.25")
        self.assertEqual(SCENARIOS["regression-3patti"]["expected"], "633.00")
        # Spec A1 (owner option (b)): ₹225 = historical evidence, no executable
        # recipe on disk — pinned as non-executable until an authoritative recipe.
        self.assertIsNone(SCENARIOS["regression-settlement-225"]["expected"])

    def test_implemented_set_matches_waves(self):
        # SEED-D state: EVERYTHING executable is implemented; exactly two stay
        # ruled-out — regression-settlement-225 (spec §12 A1, historical
        # evidence) and performance (DATA-D6, owner-deferred targets).
        not_implemented = {k for k, s in SCENARIOS.items() if not s["implemented"]}
        self.assertEqual(not_implemented, {"regression-settlement-225", "performance"})

    def test_registry_slugs_stable(self):
        self.assertEqual(len(valid_slugs()), len(SCENARIOS))
