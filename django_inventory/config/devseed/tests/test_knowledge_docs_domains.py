"""KS-B — permanent detector tests for the three documentation domains, with
a CONSTRUCTED drift case per failure class (a detector that can only say yes
never certifies). All constructed cases use injected inputs — the real corpus
is never touched (pure-detector law)."""

from django.test import SimpleTestCase, TestCase

from devseed.knowledge import BLOCKER, INFO, WARN
from devseed.knowledge.d1_code_docs import (
    detect_change_impact,
    detect_model_map,
    detect_route_map,
)
from devseed.knowledge.d5_manifest import (
    detect_manifest_consistency,
    detect_manifest_coverage,
    detect_manifest_paths,
)
from devseed.knowledge.d6_ownership_metadata import (
    detect_lifecycle,
    detect_metadata,
    detect_ownership,
)
from devseed.knowledge.report import build_sync_report


def by_id(findings):
    return {f.id: f for f in findings}


FAKE_GRAPH = {"nodes": [
    {"kind": "url", "id": "url:inventory:my_dashboard"},
    {"kind": "url", "id": "url:_unnamed:ghost-route"},
    {"kind": "model", "id": "model:accounts.Role"},
    {"kind": "model", "id": "model:expense.GhostModel"},
    {"kind": "doc", "id": "doc:docs/KNOWN.md", "anchors": ["docs/KNOWN.md"]},
]}


class Domain1Tests(TestCase):
    def make_matrix(self, tmpdir, rows):
        import os
        path = os.path.join(tmpdir, "matrix.md")
        body = "| Changed file/area | Docs to review & update |\n|---|---|\n"
        body += "\n".join(rows) + "\n"
        open(path, "w").write(body)
        return path

    def test_matrix_routing_failure_unrouted_changed_file(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            path = self.make_matrix(d, ["| `config/expense/services/x.py` | docs/A.md |"])
            findings = detect_change_impact(
                diff=True, matrix_path=path,
                changed=["config/expense/services/x.py",       # routed
                         "config/production/views/unrouted.py"],  # NOT routed
                path_exists=lambda p: True)
            r = by_id(findings)
            self.assertIn("d1.matrix.unrouted:config/production/views/unrouted.py", r)
            self.assertEqual(
                r["d1.matrix.unrouted:config/production/views/unrouted.py"].severity, WARN)
            self.assertNotIn("d1.matrix.unrouted:config/expense/services/x.py", r)

    def test_matrix_dead_doc_reference(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            path = self.make_matrix(d, ["| `config/x.py` | docs/DEAD_REFERENCE.md |"])
            findings = detect_change_impact(
                diff=False, matrix_path=path,
                path_exists=lambda p: p != "docs/DEAD_REFERENCE.md")
            r = by_id(findings)
            self.assertIn("d1.matrix.dead-doc-ref:docs/DEAD_REFERENCE.md", r)
            self.assertEqual(r["d1.matrix.dead-doc-ref:docs/DEAD_REFERENCE.md"].venue, "docs")

    def test_route_map_drift_both_directions(self):
        findings = detect_route_map(
            graph=FAKE_GRAPH,
            live_ids={"url:inventory:my_dashboard", "url:new:brand_new_route"})
        r = by_id(findings)
        self.assertEqual(r["d1.route-map.missing:url:new:brand_new_route"].severity, WARN)
        self.assertEqual(r["d1.route-map.missing:url:new:brand_new_route"].venue, "graph")
        self.assertIn("d1.route-map.ghost:url:_unnamed:ghost-route", r)

    def test_model_map_drift_both_directions(self):
        findings = detect_model_map(
            graph=FAKE_GRAPH,
            live_ids={"model:accounts.Role", "model:production.BrandNew"})
        r = by_id(findings)
        self.assertIn("d1.model-map.missing:model:production.BrandNew", r)
        self.assertIn("d1.model-map.ghost:model:expense.GhostModel", r)

    def test_clean_inputs_produce_zero_findings(self):
        self.assertEqual(detect_route_map(
            graph={"nodes": [{"kind": "url", "id": "url:a"}]}, live_ids={"url:a"}), [])
        self.assertEqual(detect_model_map(
            graph={"nodes": [{"kind": "model", "id": "model:a.B"}]},
            live_ids={"model:a.B"}), [])


class Domain6Tests(SimpleTestCase):
    def make_ownership_matrix(self, tmpdir, rows):
        import os
        path = os.path.join(tmpdir, "own.md")
        body = "| Doc | Owner concept | Update trigger (event) |\n|---|---|---|\n"
        body += "\n".join(rows) + "\n"
        open(path, "w").write(body)
        return path

    def test_ownership_failure_unowned_doc(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            path = self.make_ownership_matrix(
                d, ["| docs/apps/<app>/GUIDE | app file map | files change |",
                    "| ARCHITECTURE_V2 | worker truth | WST change |"])
            findings = detect_ownership(
                matrix_path=path,
                census=["docs/apps/devseed/GUIDE.md",   # family-owned
                        "docs/ARCHITECTURE_V2.md",       # name-owned
                        "docs/TOTALLY_ORPHAN_DOC.md"])   # unowned
            r = by_id(findings)
            self.assertEqual(list(r), ["d6.ownership.unowned:docs/TOTALLY_ORPHAN_DOC.md"])
            self.assertEqual(r[list(r)[0]].severity, WARN)

    def test_metadata_failures_missing_incomplete_badstatus(self):
        docs = {
            "docs/no_fm.md": "# no frontmatter here\n",
            "docs/incomplete.md": "---\nid: x\ntype: note\n---\nbody\n",
            "docs/bad_status.md": ("---\nid: y\ntype: note\nstatus: zombie\nowner: o\n"
                                   "scope: s\nanchors: a\nverified: 2026-07-17\n---\nbody\n"),
            "docs/good.md": ("---\nid: z\ntype: note\nstatus: active\nowner: o\n"
                             "scope: s\nanchors: a\nverified: 2026-07-17\n---\nbody\n"),
        }
        findings = detect_metadata(census=list(docs), reader=lambda p: docs[p])
        r = by_id(findings)
        self.assertIn("d6.metadata.missing-frontmatter:docs/no_fm.md", r)
        self.assertIn("d6.metadata.incomplete:docs/incomplete.md", r)
        self.assertIn("status", str(r["d6.metadata.incomplete:docs/incomplete.md"].evidence))
        self.assertIn("d6.metadata.bad-status:docs/bad_status.md", r)
        self.assertEqual([i for i in r if "good.md" in i], [])

    def test_lifecycle_failure_bannerless_superseded(self):
        docs = {
            "docs/dead.md": ("---\nid: d\ntype: note\nstatus: superseded\nowner: o\n"
                             "scope: s\nanchors: a\nverified: 2026-07-17\n---\n"
                             "just content, no banner\n"),
            "docs/ok.md": ("---\nid: k\ntype: note\nstatus: superseded\nowner: o\n"
                           "scope: s\nanchors: a\nverified: 2026-07-17\n---\n"
                           "> **ARCHIVED 2026-07-17** — superseded by docs/new.md.\n"),
        }
        findings = detect_lifecycle(census=list(docs), reader=lambda p: docs[p])
        r = by_id(findings)
        self.assertEqual(list(r), ["d6.lifecycle.no-banner:docs/dead.md"])


class Domain5Tests(SimpleTestCase):
    MANIFEST = {
        "entry": {"front_door": "docs/START.md"},
        "topics": [
            {"match": ["settlement"], "canonical": "docs/KNOWN.md", "also": ["docs/ALSO.md"]},
            {"match": ["orphan topic"], "canonical": "docs/UNKNOWN_TO_GRAPH.md", "also": []},
            {"match": [], "canonical": "", "also": []},
            {"match": ["settlement"], "canonical": "docs/OTHER.md", "also": []},
        ],
    }

    def test_manifest_path_failure_is_blocker(self):
        findings = detect_manifest_paths(
            manifest=self.MANIFEST,
            path_exists=lambda p: p != "docs/ALSO.md")
        r = by_id(findings)
        self.assertEqual(r["d5.paths.dead:docs/ALSO.md"].severity, BLOCKER)
        self.assertEqual(r["d5.paths.dead:docs/ALSO.md"].venue, "docs")

    def test_manifest_unreadable_is_blocker(self):
        import unittest.mock as mock
        with mock.patch("devseed.knowledge.d5_manifest._load_manifest",
                        return_value=(None, "boom")):
            findings = detect_manifest_paths()
            self.assertEqual(findings[0].id, "d5.paths.unreadable")
            self.assertEqual(findings[0].severity, BLOCKER)

    def test_topic_coverage_failure(self):
        findings = detect_manifest_coverage(manifest=self.MANIFEST, graph=FAKE_GRAPH)
        r = by_id(findings)
        self.assertIn("d5.coverage.graph-unknown:docs/UNKNOWN_TO_GRAPH.md", r)
        self.assertEqual(r["d5.coverage.graph-unknown:docs/UNKNOWN_TO_GRAPH.md"].severity, WARN)
        self.assertNotIn("d5.coverage.graph-unknown:docs/KNOWN.md", r)

    def test_consistency_failures(self):
        findings = detect_manifest_consistency(manifest=self.MANIFEST)
        r = by_id(findings)
        self.assertIn("d5.consistency.incomplete-topic:2", r)
        self.assertEqual(r["d5.consistency.incomplete-topic:2"].severity, WARN)
        self.assertIn("d5.consistency.ambiguous-term:settlement", r)
        self.assertEqual(r["d5.consistency.ambiguous-term:settlement"].severity, INFO)


class DetectorContractTests(SimpleTestCase):
    def test_every_finding_carries_the_six_fields_and_reports_deterministically(self):
        findings = (detect_manifest_paths(manifest=Domain5Tests.MANIFEST,
                                          path_exists=lambda p: False)
                    + detect_manifest_consistency(manifest=Domain5Tests.MANIFEST))
        for f in findings:
            row = f.as_body_row()
            self.assertEqual(set(row), {"id", "domain", "severity", "evidence",
                                        "venue", "accepted"})
            self.assertIn(f.severity, (BLOCKER, WARN, INFO))
        r1 = build_sync_report(mode="sweep", findings=findings,
                               registered_detectors=9)
        r2 = build_sync_report(mode="sweep", findings=list(reversed(findings)),
                               registered_detectors=9)
        self.assertEqual(r1["envelope"]["body_hash"], r2["envelope"]["body_hash"])

    def test_registry_has_all_domain_detectors(self):
        from devseed.management.commands.knowledge_sync import DEEP_ONLY, DETECTORS
        self.assertEqual(sorted(DETECTORS), [
            "code-docs.change-impact", "code-docs.model-map", "code-docs.route-map",
            "dataset.golden-agreement", "dataset.registry", "dataset.spec-version",
            "generated.fences", "generated.hand-edit", "generated.stale-banner",
            "graph.census", "graph.completeness", "graph.consistency",
            "graph.deep-rebuild", "graph.validator",
            "manifest.consistency", "manifest.coverage", "manifest.paths",
            "ownership.lifecycle", "ownership.matrix", "ownership.metadata",
            "verification.citations", "verification.registry",
            "verification.report-schema",
        ])
        self.assertEqual(DEEP_ONLY, frozenset({"graph.deep-rebuild", "generated.hand-edit"}))
