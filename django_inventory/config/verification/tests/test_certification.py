"""VER-D — the engine certification pins (permanent): report SCHEMA ·
body-hash determinism per command shape · exit-code matrix · --skip
transparency. From engine 1.0.0 the schema is CERTIFIED — changing any key
set below = a new engine version + a dated Design-Record amendment (this
suite is the tripwire)."""

import hashlib
import io
import json
import tempfile

from django.core.management import CommandError, call_command
from django.test import TestCase

from devseed import core
from verification.checks import dev_world, production
from verification.checks import CATEGORIES
from verification.checks.compose import compose_all
from verification.report import (
    CheckResult,
    build_report,
    exit_code,
    write_report,
)

# ── THE CERTIFIED SCHEMA (engine 1.0.0) ──────────────────────────────────────
ENVELOPE_KEYS = {"command", "engine_version", "spec_version", "environment",
                 "totals", "skipped_categories", "body_hash", "ran_at"}
BODY_ROW_KEYS = {"id", "citation", "category", "status", "measured"}
STATUSES = {"pass", "fail", "skip"}


def make(n_fail=0, n_pass=1):
    rs = [CheckResult(id=f"p{i}", citation="U10", category="integrity",
                      status="pass") for i in range(n_pass)]
    rs += [CheckResult(id=f"f{i}", citation="U10", category="integrity",
                       status="fail") for i in range(n_fail)]
    return rs


class ReportSchemaCertificationTests(TestCase):
    def assert_certified_schema(self, report):
        self.assertEqual(set(report["envelope"]), ENVELOPE_KEYS)
        self.assertEqual(report["envelope"]["engine_version"], "1.0.0")
        ids = [row["id"] for row in report["body"]]
        self.assertEqual(ids, sorted(ids))                    # sorted body
        self.assertEqual(len(ids), len(set(ids)), "duplicate check ids")
        for row in report["body"]:
            self.assertEqual(set(row), BODY_ROW_KEYS)
            self.assertIn(row["status"], STATUSES)
            self.assertIn(row["category"], CATEGORIES)
            self.assertTrue(row["citation"])
        # body-hash recomputed INDEPENDENTLY of the engine
        recomputed = hashlib.sha256(json.dumps(
            report["body"], sort_keys=True, separators=(",", ":")
        ).encode("utf-8")).hexdigest()
        self.assertEqual(report["envelope"]["body_hash"], recomputed)
        # the ONLY timestamp lives in the envelope
        self.assertNotIn("ran_at", json.dumps(report["body"]))
        t = report["envelope"]["totals"]
        self.assertEqual(t["pass"] + t["fail"] + t["skip"], len(report["body"]))

    def test_production_report_schema_certified(self):
        results = production.run_production_checks("prod")
        self.assert_certified_schema(build_report(
            command="verify_production", environment="prod", results=results))

    def test_dev_world_report_schema_certified(self):
        manifest = core.seed_scenario("demo")
        results, skipped = dev_world.run_checks("demo", manifest)
        self.assert_certified_schema(build_report(
            command="verify_demo", environment="dev", results=results,
            skipped_categories=skipped))

    def test_compose_report_schema_certified(self):
        results, skipped = compose_all("prod")
        self.assert_certified_schema(build_report(
            command="verify_all", environment="prod", results=results,
            skipped_categories=skipped))


class DeterminismPairTests(TestCase):
    """Body-hash pairs per command SHAPE — two runs on an unchanged world
    produce identical bodies (the live per-command pairs are VER-D log
    evidence via the real commands)."""

    def pair(self, run):
        h = []
        for _ in (1, 2):
            rep = build_report(command="x", environment="dev", results=run())
            h.append(rep["envelope"]["body_hash"])
        self.assertEqual(h[0], h[1])

    def test_demo_pair(self):
        m = core.seed_scenario("demo")
        self.pair(lambda: dev_world.run_checks("demo", m)[0])

    def test_factory_pair(self):
        m = core.seed_scenario("factory")
        self.pair(lambda: dev_world.run_checks("factory", m)[0])

    def test_feature_pair(self):
        m = core.seed_scenario("feature-settlement")
        self.pair(lambda: dev_world.run_checks("feature-settlement", m)[0])

    def test_production_pair_both_modes(self):
        core.seed_scenario("demo")  # non-empty world under the subset
        self.pair(lambda: production.run_production_checks("prod"))
        self.pair(lambda: production.run_production_checks("dev"))

    def test_compose_pair_both_modes(self):
        with tempfile.TemporaryDirectory() as d:
            core.seed_scenario("demo", manifest_dir=d)
            self.pair(lambda: compose_all("dev", manifest_dir=d)[0])
        self.pair(lambda: compose_all("prod")[0])


class ExitCodeMatrixTests(TestCase):
    def rep(self, n_fail, n_pass=1):
        return build_report(command="x", environment="prod",
                            results=make(n_fail=n_fail, n_pass=n_pass))

    def test_matrix(self):
        # 0 = all green · nonzero = the red COUNT · capped for shell safety
        self.assertEqual(exit_code(self.rep(0)), 0)
        self.assertEqual(exit_code(self.rep(1)), 1)
        self.assertEqual(exit_code(self.rep(7)), 7)
        self.assertEqual(exit_code(self.rep(300)), 250)

    def test_command_green_completes_and_red_raises(self):
        with tempfile.TemporaryDirectory() as d:
            call_command("verify_production", report=d, stdout=io.StringIO())  # green
            from django.apps import apps
            User = apps.get_model("accounts", "User")
            Role = apps.get_model("accounts", "Role")
            User.objects.create_user("dev.planted@test.local", "x",
                                     role=Role.objects.get(code="worker"))
            with self.assertRaises(CommandError) as ctx:
                call_command("verify_production", report=d, stdout=io.StringIO())
            self.assertIn("1 red check", str(ctx.exception))


class SkipTransparencyTests(TestCase):
    def test_skip_surfaces_in_envelope_body_and_stdout(self):
        import os
        with tempfile.TemporaryDirectory() as d:
            out = io.StringIO()
            call_command("verify_production", report=d, skip=["integrity"],
                         stdout=out)
            self.assertIn("skipped categories (explicit): integrity", out.getvalue())
            on_disk = json.load(open(os.path.join(d, os.listdir(d)[0]), encoding="utf-8"))
            self.assertEqual(on_disk["envelope"]["skipped_categories"], ["integrity"])
            self.assertFalse([r for r in on_disk["body"]
                              if r["category"] == "integrity"])

    def test_no_flag_exists_to_skip_silently(self):
        # The ONLY exclusion mechanism is --skip, and it always reports.
        rep = build_report(command="x", environment="prod", results=make(),
                           skipped_categories=["smoke"])
        self.assertEqual(rep["envelope"]["skipped_categories"], ["smoke"])

    def test_write_report_preserves_certified_content(self):
        with tempfile.TemporaryDirectory() as d:
            rep = build_report(command="verify_production", environment="prod",
                               results=make(n_pass=3))
            path = write_report(rep, report_dir=d)
            on_disk = json.load(open(path, encoding="utf-8"))
            self.assertEqual(on_disk, json.loads(json.dumps(rep)))
