"""KS-A — deterministic report scaffolding pins (SYNC-D5: the P13 conventions
as FORMAT law) + acceptance mechanics + exit-code threshold (SYNC-D3)."""

import json
import os
import tempfile

from django.test import SimpleTestCase

from devseed.knowledge import BLOCKER, INFO, WARN, Finding
from devseed.knowledge.acceptance import ACCEPTED_FINDINGS, apply_acceptance
from devseed.knowledge.report import (
    build_sync_report,
    exit_code,
    write_report,
)


def sample():
    return [
        Finding(id="b.stale-output", domain="generated-drift", severity=WARN,
                evidence={"path": "docs/features/x.md", "graph": "old!=new"},
                venue="generated"),
        Finding(id="a.hand-edit", domain="generated-drift", severity=BLOCKER,
                evidence={"path": "docs/features/y.md"}, venue="generated"),
        Finding(id="c.verified-date", domain="ownership-metadata", severity=INFO,
                evidence={"path": "docs/z.md"}, venue="docs"),
    ]


class SyncReportTests(SimpleTestCase):
    def test_body_sorted_hash_stable_timestamp_in_envelope_only(self):
        r1 = build_sync_report(mode="sweep", findings=sample())
        r2 = build_sync_report(mode="sweep", findings=sample())
        self.assertEqual([row["id"] for row in r1["body"]],
                         ["a.hand-edit", "b.stale-output", "c.verified-date"])
        self.assertEqual(r1["envelope"]["body_hash"], r2["envelope"]["body_hash"])
        self.assertNotIn("ran_at", json.dumps(r1["body"]))
        self.assertIn("ran_at", r1["envelope"])

    def test_totals_and_threshold_exit(self):
        r = build_sync_report(mode="sweep", findings=sample())
        t = r["envelope"]["totals"]
        self.assertEqual((t["BLOCKER"], t["WARN"], t["INFO"], t["accepted"]),
                         (1, 1, 1, 0))
        self.assertEqual(exit_code(r), 1)      # the one unaccepted BLOCKER
        green = build_sync_report(mode="sweep",
                                  findings=[f for f in sample() if f.severity != BLOCKER])
        self.assertEqual(exit_code(green), 0)  # WARN/INFO are report-only (SYNC-D3)

    def test_accepted_blocker_is_printed_but_exempt_from_exit(self):
        ACCEPTED_FINDINGS["a.hand-edit"] = {"date": "2026-07-17", "owner": "test",
                                            "reason": "constructed"}
        try:
            findings = apply_acceptance(sample())
            r = build_sync_report(mode="sweep", findings=findings)
            row = [x for x in r["body"] if x["id"] == "a.hand-edit"][0]
            self.assertTrue(row["accepted"])            # visible, never filtered
            self.assertEqual(row["severity"], BLOCKER)  # severity unchanged
            self.assertEqual(r["envelope"]["totals"]["accepted"], 1)
            self.assertEqual(exit_code(r), 0)           # exempt from the threshold
        finally:
            ACCEPTED_FINDINGS.clear()

    def test_skips_are_explicit(self):
        r = build_sync_report(mode="sweep", findings=[], skipped_detectors=["code-docs"])
        self.assertEqual(r["envelope"]["skipped_detectors"], ["code-docs"])

    def test_write_report_round_trips(self):
        with tempfile.TemporaryDirectory() as d:
            r = build_sync_report(mode="sweep", findings=sample())
            path = write_report(r, report_dir=d)
            self.assertTrue(os.path.basename(path).startswith("knowledge_sync-"))
            on_disk = json.load(open(path, encoding="utf-8"))
            self.assertEqual(on_disk["envelope"]["body_hash"], r["envelope"]["body_hash"])
            self.assertEqual(on_disk["body"], r["body"])
