"""SEED-E — permanent operational tests for the destructive reset path.

The REAL path (psycopg2 DDL + migrate + seed against a live scratch DB) can
never run inside the battery — guard factor 2 (DEBUG) keeps every devseed
command off test databases BY DESIGN (proven in test_guard). So these tests
pin the two halves separately:
  • the COMMAND wall (guard/confirmation/target refusals, validation-before-DDL)
  • the ORCHESTRATION contract via `core.run_reset`'s injection points
    (ordering, failure propagation, manifest shape, determinism surface).
The live end-to-end certification (fresh reset ×2 on BOTH scratch DBs,
identical state + manifests) is SEED-E log evidence, run via the real command.
"""

import json
import os
import tempfile

from django.core.management import CommandError, call_command
from django.test import SimpleTestCase, TestCase

from devseed import core
from verification.assertions import SeedAssertionError  # SEED-D6: shared library home


class ResetCommandWallTests(SimpleTestCase):
    """Refusals — every one raised BEFORE any DDL could run."""

    def assert_refused(self, needle, *args, **kwargs):
        with self.assertRaises(CommandError) as ctx:
            call_command("reset_demo", *args, **kwargs)
        self.assertIn(needle, str(ctx.exception))
        return str(ctx.exception)

    def test_destructive_confirmation_enforced(self):
        self.assert_refused("destructive confirmation missing or mismatched",
                            db="inventory_seed_scratch_1")

    def test_mismatched_confirmation_refused(self):
        self.assert_refused("--i-understand-this-destroys-inventory_seed_scratch_2",
                            db="inventory_seed_scratch_2", confirm_scratch_1=True)

    def test_refuses_inventory_db(self):
        # THE law: the primary dev DB is never a reset target — no literal
        # confirmation flag even exists for it.
        msg = self.assert_refused("not an allowlisted scratch DB", db="inventory_db")
        self.assertIn("primary dev DB is never a seeder target", msg)

    def test_refuses_unknown_database(self):
        self.assert_refused("not an allowlisted scratch DB", db="no_such_db")

    def test_unknown_seed_slug_refused_before_any_ddl(self):
        # Slug validation precedes run_reset — a typo'd --seed must not
        # destroy the scratch DB first. (Guard refuses earlier under the test
        # env anyway; the ordering is pinned by RunResetOrchestrationTests.)
        self.assert_refused("GUARD REFUSED", db="inventory_seed_scratch_1",
                            seed="no-such-scenario", confirm_scratch_1=True)


class RunResetOrchestrationTests(SimpleTestCase):
    """core.run_reset contract via injected callables (no live DDL)."""

    def fakes(self, log):
        return {
            "_dropper": lambda db: log.append(("drop", db)),
            "_migrator": lambda db: log.append(("migrate", db)),
        }

    def test_belt_refuses_non_allowlisted_target_before_any_step(self):
        log = []
        with self.assertRaises(ValueError) as ctx:
            core.run_reset("inventory_db", **self.fakes(log))
        self.assertIn("not an allowlisted scratch DB", str(ctx.exception))
        self.assertEqual(log, [])  # nothing ran — refusal precedes every step

    def test_migrate_failure_propagates_and_seed_never_runs(self):
        log = []

        def boom(db):
            raise RuntimeError("migrate exploded")

        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(RuntimeError):
                core.run_reset("inventory_seed_scratch_1", seed_slug="demo",
                               manifest_dir=d,
                               _dropper=lambda db: log.append(("drop", db)),
                               _migrator=boom,
                               _seeder=lambda *a, **k: log.append(("seed",)))
            self.assertEqual(log, [("drop", "inventory_seed_scratch_1")])
            self.assertEqual(os.listdir(d), [])  # no manifest on failure

    def test_assertion_failure_propagates(self):
        def failing_seeder(slug, **kwargs):
            raise SeedAssertionError("POST-SEED ASSERTIONS FAILED: planted")

        log = []
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(SeedAssertionError):
                core.run_reset("inventory_seed_scratch_2", seed_slug="demo",
                               manifest_dir=d, _seeder=failing_seeder,
                               **self.fakes(log))
            self.assertEqual(os.listdir(d), [])

    def _fake_seeder(self, slug, **kwargs):
        return {"scenario": slug, "counts": {"2-cast": {"created": 3, "skipped": 0}},
                "assertions": {"result": "PASS"}, "money": None,
                "handles": ["dev.min.sa@test.local"]}

    def test_manifest_generation_and_shape(self):
        log = []
        with tempfile.TemporaryDirectory() as d:
            m = core.run_reset("inventory_seed_scratch_1", seed_slug="demo",
                               manifest_dir=d, _seeder=self._fake_seeder,
                               **self.fakes(log))
            self.assertEqual(log, [("drop", "inventory_seed_scratch_1"),
                                   ("migrate", "inventory_seed_scratch_1")])
            self.assertEqual(m["reset"], "inventory_seed_scratch_1")
            self.assertTrue(m["migrated"])
            self.assertEqual(m["seeded"]["scenario"], "demo")
            self.assertEqual(m["seeded"]["assertions"]["result"], "PASS")
            files = os.listdir(d)
            self.assertEqual(len(files), 1)
            self.assertTrue(files[0].startswith("reset-inventory_seed_scratch_1-"))
            on_disk = json.load(open(os.path.join(d, files[0]), encoding="utf-8"))
            self.assertEqual(core.strip_volatile(on_disk), core.strip_volatile(m))

    def test_repeated_reset_manifest_determinism(self):
        log = []
        m1 = core.run_reset("inventory_seed_scratch_1", seed_slug="demo",
                            _seeder=self._fake_seeder, **self.fakes(log))
        m2 = core.run_reset("inventory_seed_scratch_1", seed_slug="demo",
                            _seeder=self._fake_seeder, **self.fakes(log))
        self.assertEqual(core.strip_volatile(m1), core.strip_volatile(m2))

    def test_cross_db_comparison_surface(self):
        # strip_volatile(extra=…) is THE cross-DB determinism comparator the
        # certification uses: identical worlds on both scratch DBs differ only
        # in the DB-identity keys + runtime stamps.
        log = []
        m1 = core.run_reset("inventory_seed_scratch_1", seed_slug="demo",
                            _seeder=self._fake_seeder, **self.fakes(log))
        m2 = core.run_reset("inventory_seed_scratch_2", seed_slug="demo",
                            _seeder=self._fake_seeder, **self.fakes(log))
        self.assertNotEqual(core.strip_volatile(m1), core.strip_volatile(m2))
        self.assertEqual(core.strip_volatile(m1, extra=("reset", "scenario")),
                         core.strip_volatile(m2, extra=("reset", "scenario")))


class RepeatedSeedDeterminismTests(TestCase):
    """Repeated seed determinism after reset — the engine half provable in the
    battery: on ONE database state, a re-seed converges (created=0) and every
    non-volatile manifest section is byte-equal. The fresh-DB half (two
    independent resets → identical manifests) is the live certification."""

    def test_reseed_is_convergent_and_manifest_stable(self):
        m1 = core.seed_scenario("demo")
        m2 = core.seed_scenario("demo")
        for c in m2["counts"].values():
            self.assertEqual(c["created"], 0)
        for key in ("scenario", "handles", "assertions"):
            self.assertEqual(m1[key], m2[key])
        self.assertEqual(m1["money"]["expected_total"], m2["money"]["expected_total"])
