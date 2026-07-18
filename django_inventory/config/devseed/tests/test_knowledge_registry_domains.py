"""KS-D — permanent detector tests for the registry domains (7 · 8) + the
severity-engine certification (acceptance interactions · threshold behavior)
+ the eight-domain completeness meta-pin. All constructed failures use
injected inputs — the real registries are never modified."""

from django.test import SimpleTestCase, TestCase

from devseed.knowledge import BLOCKER, INFO, WARN, Finding
from devseed.knowledge.acceptance import ACCEPTED_FINDINGS, apply_acceptance
from devseed.knowledge.d7_dataset_spec import (
    detect_dataset_registry,
    detect_golden_spec_agreement,
    detect_spec_version_pins,
)
from devseed.knowledge.d8_verification_registry import (
    CERTIFIED_CHECK_IDS,
    detect_citation_integrity,
    detect_report_schema_dependency,
    detect_verification_registry,
    extract_registry,
)
from devseed.knowledge.report import build_sync_report, exit_code


def by_id(findings):
    return {f.id: f for f in findings}


class Domain7Tests(SimpleTestCase):
    def test_missing_registry_entry_implemented_not_declared(self):
        r = by_id(detect_dataset_registry(
            scenarios={"a": {"class": "minimal", "implemented": True}},
            content={"a": {}, "ghost-world": {}}))
        self.assertEqual(list(r), ["d7.registry.implemented-not-declared:ghost-world"])
        self.assertEqual(r[list(r)[0]].severity, WARN)
        self.assertEqual(r[list(r)[0]].venue, "spec-registry")

    def test_implemented_state_mismatch_declared_without_content(self):
        r = by_id(detect_dataset_registry(
            scenarios={"a": {"class": "minimal", "implemented": True}}, content={}))
        self.assertIn("d7.registry.declared-without-content:a", r)

    def test_invalid_registry_reference_unknown_class(self):
        r = by_id(detect_dataset_registry(
            scenarios={"a": {"class": "mystery", "implemented": False}}, content={}))
        self.assertIn("d7.registry.invalid-class:a", r)

    def test_duplicate_golden_is_info(self):
        r = by_id(detect_dataset_registry(
            scenarios={"a": {"class": "regression", "implemented": False, "expected": "9.00"},
                       "b": {"class": "regression", "implemented": False, "expected": "9.00"}},
            content={}))
        self.assertEqual(r["d7.registry.duplicate-golden:9.00"].severity, INFO)

    def test_spec_version_mismatch(self):
        r = detect_spec_version_pins(devseed_pin="1.0.0", engine_pin="1.0.0",
                                     spec_reader=lambda: "**v2.0.0 / frozen-v2**")
        self.assertEqual(r[0].id, "d7.spec-version.mismatch")
        self.assertEqual(r[0].evidence["DEV_DATASET_ARCHITECTURE §10"], "2.0.0")
        self.assertEqual(detect_spec_version_pins(
            devseed_pin="1.0.0", engine_pin="1.0.0",
            spec_reader=lambda: "**v1.0.0 / frozen-v1**"), [])

    def test_scenario_golden_spec_drift(self):
        r = detect_golden_spec_agreement(
            scenarios={"regression-x": {"class": "regression", "implemented": True,
                                        "expected": "777.77"}},
            spec_reader=lambda: "the spec mentions ₹801.00 and ₹344.25 only")
        self.assertEqual(r[0].id, "d7.golden.spec-disagreement:regression-x")
        self.assertEqual(detect_golden_spec_agreement(
            scenarios={"regression-x": {"expected": "801.00"}},
            spec_reader=lambda: "settled ₹801.00"), [])

    def test_real_registries_are_clean(self):
        # The live four-surface agreement (SEED-F) holds today.
        self.assertEqual(detect_dataset_registry(), [])
        self.assertEqual(detect_spec_version_pins(), [])
        self.assertEqual(detect_golden_spec_agreement(), [])


class Domain8Tests(SimpleTestCase):
    def test_certified_census_extraction_matches_live_registry(self):
        rows = extract_registry()
        live = {cid for cid, _, _ in rows}
        self.assertEqual(live, set(CERTIFIED_CHECK_IDS))
        self.assertEqual(detect_verification_registry(), [])

    def test_verification_check_drift_both_directions(self):
        rows = [("prod.brand-new-check", "cited", "x.py"),
                ("all.composition", "cited", "compose.py")]
        r = by_id(detect_verification_registry(rows=rows))
        self.assertIn("d8.registry.uncertified-check:prod.brand-new-check", r)
        self.assertIn("d8.registry.missing-check:dev.assertions.rerun", r)

    def test_unreadable_registry(self):
        r = detect_verification_registry(rows=[])
        self.assertEqual(r[0].id, "d8.registry.unreadable")

    def test_missing_citation(self):
        r = by_id(detect_citation_integrity(rows=[("prod.x", "", "production.py")]))
        self.assertIn("d8.citation.missing:prod.x", r)
        self.assertIn("VER-D4", str(r["d8.citation.missing:prod.x"].evidence))

    def test_broken_citation_target(self):
        r = by_id(detect_citation_integrity(
            rows=[("prod.x", "per ARCHITECTURE_V2 §11", "production.py")],
            path_exists=lambda p: False))
        self.assertIn("d8.citation.broken:prod.x:ARCHITECTURE_V2", r)
        self.assertEqual(detect_citation_integrity(
            rows=[("prod.x", "per ARCHITECTURE_V2 §11", "p.py")],
            path_exists=lambda p: True), [])

    def test_live_citations_resolve(self):
        self.assertEqual(detect_citation_integrity(), [])

    def test_report_schema_dependency_drift_and_live_agreement(self):
        r = by_id(detect_report_schema_dependency(
            envelope_keys=frozenset({"command"}), body_keys=frozenset({"id"})))
        self.assertIn("d8.schema.envelope-drift", r)
        self.assertIn("d8.schema.body-drift", r)
        self.assertIn("P19/20/21", str(r["d8.schema.envelope-drift"].evidence))
        self.assertEqual(detect_report_schema_dependency(), [])  # live schema = certified


class SeverityEngineCertification(TestCase):
    def mixed(self):
        return [
            Finding(id="a.blocker", domain="dataset-spec", severity=BLOCKER,
                    venue="spec-registry"),
            Finding(id="b.warn", domain="dataset-spec", severity=WARN,
                    venue="spec-registry"),
            Finding(id="c.info", domain="dataset-spec", severity=INFO,
                    venue="spec-registry"),
        ]

    def test_threshold_only_unaccepted_blockers_fail(self):
        rep = build_sync_report(mode="sweep", findings=self.mixed())
        self.assertEqual(exit_code(rep), 1)
        no_blocker = [f for f in self.mixed() if f.severity != BLOCKER]
        self.assertEqual(exit_code(build_sync_report(mode="sweep",
                                                     findings=no_blocker)), 0)

    def test_acceptance_interaction_full_cycle(self):
        ACCEPTED_FINDINGS["a.blocker"] = {"date": "2026-07-17", "owner": "test",
                                          "reason": "constructed"}
        ACCEPTED_FINDINGS["z.stale-entry"] = {"date": "2026-07-17", "owner": "test",
                                              "reason": "no longer fires"}
        try:
            findings = apply_acceptance(self.mixed())
            live_ids = {f.id for f in findings}
            stale = sorted(set(ACCEPTED_FINDINGS) - live_ids)
            rep = build_sync_report(mode="sweep", findings=findings,
                                    stale_acceptance=stale)
            self.assertEqual(exit_code(rep), 0)              # accepted BLOCKER exempt
            row = [x for x in rep["body"] if x["id"] == "a.blocker"][0]
            self.assertTrue(row["accepted"])                  # still PRINTED
            self.assertEqual(rep["envelope"]["stale_acceptance"], ["z.stale-entry"])
        finally:
            ACCEPTED_FINDINGS.clear()

    def test_command_surfaces_stale_acceptance(self):
        import io
        import tempfile
        from django.core.management import call_command
        from django.core.management.base import CommandError
        ACCEPTED_FINDINGS["never.fires.anywhere"] = {"date": "2026-07-17",
                                                     "owner": "test", "reason": "stale"}
        try:
            with tempfile.TemporaryDirectory() as d:
                out = io.StringIO()
                try:
                    call_command("knowledge_sync", skip=["graph.validator"],
                                 report=d, stdout=out)
                except CommandError:
                    pass
                self.assertIn("STALE acceptance entries", out.getvalue())
                self.assertIn("never.fires.anywhere", out.getvalue())
        finally:
            ACCEPTED_FINDINGS.clear()


class EightDomainCompletenessPin(SimpleTestCase):
    def test_every_domain_has_at_least_one_registered_detector(self):
        # The full constructed-drift matrix spans KS-B/C/D test files; this
        # meta-pin guarantees no domain ever loses its detector coverage.
        from devseed.knowledge import DOMAINS
        from devseed.management.commands.knowledge_sync import DETECTORS
        covered = {
            "code-docs": "code-docs.change-impact",
            "code-graph": "graph.validator",
            "docs-graph": "graph.census",
            "generated-drift": "generated.stale-banner",
            "manifest-sync": "manifest.paths",
            "ownership-metadata": "ownership.matrix",
            "dataset-spec": "dataset.registry",
            "verification-registry": "verification.registry",
        }
        self.assertEqual(set(covered), set(DOMAINS))
        for domain, det in covered.items():
            self.assertIn(det, DETECTORS, f"domain {domain} lost its detector")
