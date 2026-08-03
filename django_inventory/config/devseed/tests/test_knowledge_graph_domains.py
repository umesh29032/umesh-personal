"""KS-C — permanent detector tests for the graph + generation domains
(2 · 3 · 4), with every owner-ordered constructed failure class planted via
injected inputs. The real graph/corpus is never touched; nothing is rebuilt
or regenerated (the deep tier renders IN MEMORY only)."""

import io
import tempfile

from django.test import SimpleTestCase, TestCase

from devseed.knowledge import BLOCKER, WARN
from devseed.knowledge.d2_graph import (
    detect_graph_deep_rebuild,
    detect_graph_validator,
)
from devseed.knowledge.d3_graph_census import (
    detect_graph_census,
    detect_graph_completeness,
    detect_graph_consistency,
)
from devseed.knowledge.d4_generated import (
    detect_fence_integrity,
    detect_generated_stale,
    detect_hand_edits,
)


def by_id(findings):
    return {f.id: f for f in findings}


GOOD_CARD = ("---\nid: url-card-x\ntype: url-card\nstatus: generated\nowner: generated\n"
             "scope: route\nanchors: config/config/urls.py\nverified: graph:aaaaaaaaaaaa\n---\n\n"
             "# URL card\n\n> ⚙️ GENERATED — an index, not truth. Do not hand-edit.\n"
             "> Generator: `scripts/generate_docs.py` · graph: `aaaaaaaaaaaa`\n"
             "> Regenerate: `env/bin/python scripts/generate_docs.py --out docs/features`\n")


class Domain2Tests(SimpleTestCase):
    class FakeValidator:
        """Stands in for the imported Phase-8 validator module."""
        def __init__(self, fatal=(), findings=(), info=(), crash=False):
            self._f, self._w, self._i, self._crash = list(fatal), list(findings), list(info), crash

        def main(self):
            self.FATAL, self.FINDINGS, self.INFO = self._f, self._w, self._i
            if self._crash:
                raise ValueError("schema unreadable")
            if self.FATAL:
                raise SystemExit(1)

    def test_validator_failure_propagation(self):
        v = self.FakeValidator(fatal=["node id pattern: FAIL"], findings=["soft"], info=["fyi"])
        r = detect_graph_validator(validator=v)
        sev = {f.severity for f in r}
        self.assertEqual(sev, {BLOCKER, WARN, "INFO"})
        blockers = [f for f in r if f.severity == BLOCKER]
        self.assertIn("node id pattern", str(blockers[0].evidence))
        self.assertEqual(blockers[0].venue, "graph")

    def test_validator_clean_run_no_findings(self):
        self.assertEqual(detect_graph_validator(validator=self.FakeValidator()), [])

    def test_real_validator_repro_subprocess_is_neutralized(self):
        # THE §16.3 INCIDENT PIN (2026-07-17): the imported Phase-8 validator's
        # repro check spawns the builder and REWRITES the graph in place — the
        # wrapper must no-op that subprocess AND disclose the vacuous check.
        import hashlib
        import os
        from devseed.knowledge.d1_code_docs import REPO_ROOT
        p = os.path.join(REPO_ROOT, "docs", "knowledge_graph.json")
        before = hashlib.sha256(open(p, "rb").read()).hexdigest()
        findings = detect_graph_validator()   # the REAL validator
        self.assertEqual(hashlib.sha256(open(p, "rb").read()).hexdigest(), before,
                         "the validator wrapper let the repro subprocess write the graph")
        self.assertIn("d2.validator.repro-check-neutralized",
                      [f.id for f in findings])
        import validate_knowledge_graph as v
        import subprocess as real_subprocess
        self.assertIs(v.subprocess.run, real_subprocess.run)  # restored after

    def test_validator_crash_is_blocker(self):
        r = detect_graph_validator(validator=self.FakeValidator(crash=True))
        self.assertEqual(r[0].id, "d2.validator.crashed")
        self.assertEqual(r[0].severity, BLOCKER)

    def test_deep_rebuild_comparison_both_ways(self):
        differ = detect_graph_deep_rebuild(rebuilt_hash="sha256:bbb",
                                           current_hash="sha256:aaa")
        self.assertEqual(differ[0].id, "d2.deep-rebuild.would-differ")
        self.assertEqual(differ[0].severity, WARN)
        self.assertEqual(differ[0].venue, "graph")
        self.assertEqual(detect_graph_deep_rebuild(rebuilt_hash="sha256:aaa",
                                                   current_hash="sha256:aaa"), [])


class Domain3Tests(SimpleTestCase):
    def test_census_mismatch(self):
        graph = {"nodes": [{"kind": "app", "id": "app:a"}, {"kind": "doc", "id": "doc:x",
                                                            "anchors": ["x.md"]}]}
        r = by_id(detect_graph_census(graph=graph, live_counts={"app": 3, "doc": 1}))
        self.assertEqual(list(r), ["d3.census.count-mismatch:app"])
        self.assertEqual(r["d3.census.count-mismatch:app"].evidence["live_census"], 3)

    def test_completeness_failure_unindexed_doc(self):
        graph = {"nodes": [{"kind": "doc", "id": "doc:x", "anchors": ["docs/OLD.md"]}]}
        r = by_id(detect_graph_completeness(graph=graph,
                                            census=["docs/OLD.md", "docs/BRAND_NEW.md"]))
        self.assertEqual(list(r), ["d3.completeness.unindexed:docs/BRAND_NEW.md"])
        self.assertEqual(r[list(r)[0]].venue, "graph")

    def test_graph_hash_mismatch_is_blocker(self):
        def refusing_loader():
            raise SystemExit("REFUSED: graph content-hash mismatch (hand-edit guard)")
        r = detect_graph_consistency(loader=refusing_loader)
        self.assertEqual(r[0].id, "d3.consistency.graph-integrity")
        self.assertEqual(r[0].severity, BLOCKER)
        self.assertIn("hand-edit guard", r[0].evidence["refusal"])
        self.assertEqual(detect_graph_consistency(loader=lambda: {"ok": True}), [])


class Domain4Tests(SimpleTestCase):
    def test_stale_generated_documentation(self):
        stale = GOOD_CARD.replace("aaaaaaaaaaaa", "999999999999")
        r = by_id(detect_generated_stale(
            graph12="aaaaaaaaaaaa", files=["x/x.md"], reader=lambda rel: stale))
        f = r["d4.stale:docs/features/x/x.md"]
        self.assertEqual(f.severity, WARN)
        self.assertEqual(f.evidence["stamped"], "999999999999")
        self.assertIn("generate_docs.py", f.evidence["remedy"])  # remedy quoted from ITS banner

    def test_banner_corruption_is_blocker(self):
        corrupted = GOOD_CARD.replace("> Regenerate: `env/bin/python "
                                      "scripts/generate_docs.py --out docs/features`\n", "")
        r = by_id(detect_generated_stale(
            graph12="aaaaaaaaaaaa", files=["x/x.md"], reader=lambda rel: corrupted))
        f = r["d4.banner.corrupt:docs/features/x/x.md"]
        self.assertEqual(f.severity, BLOCKER)
        self.assertEqual(f.evidence["missing"], ["regenerate-line"])

    def test_clean_generated_file_no_findings(self):
        self.assertEqual(detect_generated_stale(
            graph12="aaaaaaaaaaaa", files=["x/x.md"], reader=lambda rel: GOOD_CARD), [])

    def test_handwritten_kos_satellite_is_not_a_generated_artifact(self):
        """docs/features/ holds generated cards AND one hand-written KOS guide
        (added by the KOS v1.0 commit). The guide has no generated banner by
        design, so scanning it produced a permanent false BLOCKER that stopped
        knowledge_sync from ever exiting clean. Excluded by exact filename —
        NOT by `owner: handwritten`, which is editable and would let a real
        hand-edited card opt out of detection."""
        from devseed.knowledge.d4_generated import _generated_files, _HANDWRITTEN
        import os
        import tempfile
        self.assertIn("HUMAN_GUIDE.md", _HANDWRITTEN)
        with tempfile.TemporaryDirectory() as d:
            for name in ("card.md", "HUMAN_GUIDE.md"):
                with open(os.path.join(d, name), "w") as fh:
                    fh.write("x")
            self.assertEqual(_generated_files(root=d), ["card.md"])

    def test_fence_corruption(self):
        docs = {
            "docs/clean.md": "no fences here\n",
            "docs/paired.md": "<!-- KOS:GEN begin x --> body <!-- KOS:GEN end x -->\n",
            "docs/orphan.md": "<!-- KOS:GEN begin x --> body, never closed\n",
        }
        r = by_id(detect_fence_integrity(census=list(docs), reader=lambda p: docs[p]))
        self.assertEqual(list(r), ["d4.fence.corrupt:docs/orphan.md"])
        self.assertEqual(r[list(r)[0]].severity, BLOCKER)

    def test_hand_edited_generated_document(self):
        expected = {"x/x.md": GOOD_CARD}
        edited = GOOD_CARD + "\nsomeone's hand-written addition\n"
        r = by_id(detect_hand_edits(expected=expected, actual={"x/x.md": edited}))
        f = r["d4.hand-edit:docs/features/x/x.md"]
        self.assertEqual(f.severity, BLOCKER)
        self.assertEqual(f.venue, "generated")

    def test_stale_file_is_not_double_reported_as_hand_edit(self):
        expected = {"x/x.md": GOOD_CARD}
        stale = GOOD_CARD.replace("aaaaaaaaaaaa", "999999999999")
        self.assertEqual(detect_hand_edits(expected=expected,
                                           actual={"x/x.md": stale}), [])

    def test_orphan_generated_file_is_warn(self):
        r = detect_hand_edits(expected={}, actual={"x/x.md": GOOD_CARD})
        self.assertEqual(r[0].id, "d4.hand-edit.orphan:docs/features/x/x.md")
        self.assertEqual(r[0].severity, WARN)

    def test_diff_mode_scopes_to_changed_generated_files(self):
        stale = GOOD_CARD.replace("aaaaaaaaaaaa", "999999999999")
        findings = detect_generated_stale(
            diff=True, graph12="aaaaaaaaaaaa", files=["a/a.md", "b/b.md"],
            reader=lambda rel: stale,
            changed=["docs/features/b/b.md", "config/unrelated.py"])
        self.assertEqual([f.id for f in findings], ["d4.stale:docs/features/b/b.md"])


class DeepGatingTests(TestCase):
    def test_deep_gated_detectors_are_recorded_never_silent(self):
        import json
        import glob
        import os
        from django.core.management import call_command
        from django.core.management.base import CommandError
        with tempfile.TemporaryDirectory() as d:
            out = io.StringIO()
            try:
                call_command("knowledge_sync", report=d, stdout=out)
            except CommandError:
                pass
            rep = json.load(open(sorted(glob.glob(os.path.join(d, "*.json")))[-1]))
            self.assertIn("generated.hand-edit (deep-gated)",
                          rep["envelope"]["skipped_detectors"])
            self.assertIn("graph.deep-rebuild (deep-gated)",
                          rep["envelope"]["skipped_detectors"])
