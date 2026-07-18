"""VER-A — report scaffolding pins (VER-D5): deterministic sorted body ·
body-hash stable · the run timestamp lives in the ENVELOPE only · totals math ·
no silent skips · exit-code law."""

import json
import os
import tempfile

from django.test import SimpleTestCase

from verification.report import (
    CheckResult,
    build_report,
    exit_code,
    write_report,
)


def sample_results():
    return [
        CheckResult(id="b-check", citation="spec §7", category="golden", status="pass",
                    measured={"expected": "150.00", "got": "150.00"}),
        CheckResult(id="a-check", citation="U10", category="production-safety", status="pass"),
        CheckResult(id="c-check", citation="ADR-0009", category="integrity", status="fail",
                    measured={"delta": "1.00"}),
    ]


class ReportTests(SimpleTestCase):
    def test_body_sorted_and_timestamp_free(self):
        r = build_report(command="verify_demo", environment="dev", results=sample_results())
        self.assertEqual([row["id"] for row in r["body"]], ["a-check", "b-check", "c-check"])
        self.assertNotIn("ran_at", json.dumps(r["body"]))
        self.assertIn("ran_at", r["envelope"])

    def test_body_hash_deterministic_across_runs(self):
        r1 = build_report(command="verify_demo", environment="dev", results=sample_results())
        r2 = build_report(command="verify_demo", environment="dev", results=sample_results())
        self.assertEqual(r1["envelope"]["body_hash"], r2["envelope"]["body_hash"])
        self.assertEqual(r1["body"], r2["body"])

    def test_body_hash_changes_with_measured_state(self):
        changed = sample_results()
        changed[2] = CheckResult(id="c-check", citation="ADR-0009", category="integrity",
                                 status="pass")
        r1 = build_report(command="verify_demo", environment="dev", results=sample_results())
        r2 = build_report(command="verify_demo", environment="dev", results=changed)
        self.assertNotEqual(r1["envelope"]["body_hash"], r2["envelope"]["body_hash"])

    def test_totals_and_exit_code(self):
        r = build_report(command="verify_all", environment="prod", results=sample_results())
        self.assertEqual(r["envelope"]["totals"], {"pass": 2, "fail": 1, "skip": 0})
        self.assertEqual(exit_code(r), 1)
        green = build_report(command="verify_all", environment="prod",
                             results=[s for s in sample_results() if s.status == "pass"])
        self.assertEqual(exit_code(green), 0)

    def test_skips_are_explicit_in_envelope(self):
        r = build_report(command="verify_demo", environment="dev",
                         results=sample_results(), skipped_categories=["smoke"])
        self.assertEqual(r["envelope"]["skipped_categories"], ["smoke"])

    def test_write_report_round_trips(self):
        with tempfile.TemporaryDirectory() as d:
            r = build_report(command="verify_demo", environment="dev", results=sample_results())
            path = write_report(r, report_dir=d)
            self.assertTrue(os.path.basename(path).startswith("verify_demo-"))
            on_disk = json.load(open(path, encoding="utf-8"))
            self.assertEqual(on_disk["envelope"]["body_hash"], r["envelope"]["body_hash"])
            self.assertEqual(on_disk["body"], r["body"])
