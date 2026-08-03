"""VER-A — polarity matrix (contract §6.3), every cell negative-tested.

Under the TEST environment DEBUG is False ⇒ dev-world commands must REFUSE
(the standing proof they can never touch a battery/test DB), while
verify_production / verify_all pass polarity everywhere and stop at the VER-A
wave gate ("not implemented", zero checks run)."""

from django.core.management import CommandError, call_command
from django.test import SimpleTestCase

from verification.guard import (
    DEV_SETTINGS_MODULE,
    DEV_WORLD_COMMANDS,
    EVERYWHERE_COMMANDS,
    polarity_failures,
)


class PolarityMatrixTests(SimpleTestCase):
    """Pure-function matrix — the §6.3 table, cell by cell."""

    def test_dev_world_commands_pass_only_in_dev(self):
        for cmd in DEV_WORLD_COMMANDS:
            self.assertEqual(
                polarity_failures(cmd, DEV_SETTINGS_MODULE, True), [], cmd)

    def test_dev_world_commands_refuse_production_settings(self):
        for cmd in DEV_WORLD_COMMANDS:
            failures = polarity_failures(cmd, "config.settings.production", False)
            self.assertEqual(len(failures), 2, cmd)  # whole wall, never short-circuit

    def test_dev_world_commands_refuse_debug_false_alone(self):
        for cmd in DEV_WORLD_COMMANDS:
            failures = polarity_failures(cmd, DEV_SETTINGS_MODULE, False)
            self.assertEqual(len(failures), 1, cmd)
            self.assertIn("DEBUG is False", failures[0])

    def test_everywhere_commands_never_refuse_on_environment(self):
        for cmd in EVERYWHERE_COMMANDS:
            self.assertEqual(polarity_failures(cmd, "config.settings.production", False), [], cmd)
            self.assertEqual(polarity_failures(cmd, DEV_SETTINGS_MODULE, True), [], cmd)

    def test_unknown_command_has_no_silent_polarity(self):
        self.assertTrue(polarity_failures("verify_everything", DEV_SETTINGS_MODULE, True))

    def test_polarity_classes_are_disjoint_and_complete(self):
        self.assertEqual(DEV_WORLD_COMMANDS & EVERYWHERE_COMMANDS, frozenset())
        self.assertEqual(len(DEV_WORLD_COMMANDS | EVERYWHERE_COMMANDS), 5)


class CommandPolarityTests(SimpleTestCase):
    """Command-level: the test env (DEBUG False) is 'not dev' — dev-world
    commands refuse; everywhere-commands reach the VER-A wave gate."""

    def refuse(self, needle, *args, **kwargs):
        with self.assertRaises(CommandError) as ctx:
            call_command(*args, **kwargs)
        self.assertIn(needle, str(ctx.exception))
        return str(ctx.exception)

    def test_verify_demo_refuses_outside_dev(self):
        self.refuse("POLARITY REFUSED", "verify_demo")

    def test_verify_factory_refuses_outside_dev(self):
        self.refuse("POLARITY REFUSED", "verify_factory")

    def test_verify_feature_refuses_outside_dev(self):
        # Refusal precedes slug validation — devseed may not even exist here.
        self.refuse("POLARITY REFUSED", "verify_feature", "demo")

    # VER-C: verify_production / verify_all are LIVE everywhere — their green
    # command-level runs are proven in test_production (they need a DB, which
    # SimpleTestCase forbids); polarity coverage here stays pure-function
    # (test_everywhere_commands_never_refuse_on_environment above).
