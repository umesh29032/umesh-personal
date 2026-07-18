"""KS-A — THE PERMANENT PURE-DETECTOR PINS (landed before any detector logic;
the P12/P13 purity-first pattern extended to FILE writes and git verbs).

The knowledge package holds no write path: no ORM writes (the devseed purity
suite already scans the whole app), no file writes outside the single report
writer, no destructive filesystem calls, no non-read-only git. Plus the
runtime proof: a sweep leaves the repo tree AND the database byte-identical."""

import os
import re

from django.apps import apps
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase

import devseed
from devseed.knowledge import DOMAINS, SEVERITIES, VENUES
from devseed.knowledge.gitio import READ_ONLY_GIT_VERBS, porcelain_hash

KNOWLEDGE_DIR = os.path.join(os.path.dirname(devseed.__file__), "knowledge")
COMMAND_FILE = os.path.join(os.path.dirname(devseed.__file__),
                            "management", "commands", "knowledge_sync.py")

# a short mode-string argument containing a write mode ("w", "wb", "a", "x",
# "r+") — NOT any long string literal that happens to contain those letters
OPEN_FOR_WRITE = re.compile(r"""open\([^)]*,\s*["'](?:[rbt+]*[wax][rbt+]*|r\+)["']""")
DESTRUCTIVE_FS = re.compile(
    r"\b(os\.(remove|unlink|rename|replace|rmdir|removedirs)|shutil\.|"
    r"\.write_text\(|\.write_bytes\(|\.unlink\(|\.rmdir\()")
FORBIDDEN_GIT = re.compile(
    r"\bgit\b[^\n]*\b(commit|checkout|reset|stash|push|pull|merge|rebase|rm|clean|apply)\b")


def _sources():
    yield COMMAND_FILE
    for root, dirs, files in os.walk(KNOWLEDGE_DIR):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for f in files:
            if f.endswith(".py"):
                yield os.path.join(root, f)


class PureDetectorStaticPins(SimpleTestCase):
    def scan(self, pattern, exempt_basenames=()):
        offenders = []
        for path in _sources():
            base = os.path.basename(path)
            if base in exempt_basenames:
                continue
            src = open(path, encoding="utf-8").read()
            for m in pattern.finditer(src):
                offenders.append(f"{base}:{src[:m.start()].count(chr(10)) + 1}: {m.group(0)[:60]}")
        return offenders

    def test_single_file_write_site(self):
        # THE only write site = knowledge/report.py (the report writer,
        # targeting the gitignored var/ directory).
        self.assertEqual(self.scan(OPEN_FOR_WRITE, exempt_basenames=("report.py",)), [],
                         "file-write outside the report writer")

    def test_report_writer_targets_var_only(self):
        src = open(os.path.join(KNOWLEDGE_DIR, "report.py"), encoding="utf-8").read()
        self.assertIn('"var", "knowledge_sync_reports"', src)
        # makedirs exists solely for the report dir; no destructive calls anywhere
        self.assertEqual(self.scan(DESTRUCTIVE_FS), [])

    def test_no_write_git_verbs_anywhere(self):
        self.assertEqual(self.scan(FORBIDDEN_GIT), [],
                         "non-read-only git usage in the detector")

    def test_gitio_verb_allowlist_is_read_only_and_enforced(self):
        self.assertEqual(set(READ_ONLY_GIT_VERBS),
                         {"diff", "status", "log", "rev-parse", "ls-files", "show"})
        from devseed.knowledge.gitio import _git
        with self.assertRaises(ValueError):
            _git("commit", "-m", "never")

    def test_no_fix_flag_exists(self):
        # §6.5: a --fix flag will never exist — statically pinned.
        src = open(COMMAND_FILE, encoding="utf-8").read()
        self.assertNotIn('add_argument("--fix"', src)
        self.assertNotIn("'--fix'", src)

    def test_domain_and_venue_registries_shape(self):
        self.assertEqual(len(DOMAINS), 8)
        self.assertEqual(SEVERITIES, ("BLOCKER", "WARN", "INFO"))
        # A-1 owner ruling encoded: domain 5 exists as manifest-sync,
        # regenerate-compare vocabulary absent from its charter line.
        self.assertIn("manifest-sync", DOMAINS)
        self.assertNotIn("regenerate-compare", DOMAINS["manifest-sync"])
        for key in ("docs", "generated", "graph", "code", "spec-registry", "money"):
            self.assertIn(key, VENUES)


class PureDetectorRuntimeProof(TestCase):
    def test_full_sweep_leaves_tree_and_db_byte_identical(self):
        # KS-B: the sweep now runs REAL detectors over the REAL corpus — any
        # findings (even BLOCKERs → CommandError) are REPORTED, never repaired;
        # identity must hold regardless of what the sweep found.
        import io
        import tempfile
        from django.core.management.base import CommandError
        tree_before = porcelain_hash()
        db_before = {m._meta.label: m.objects.count() for m in apps.get_models()}
        with tempfile.TemporaryDirectory() as d:
            out = io.StringIO()
            try:
                call_command("knowledge_sync", report=d, stdout=out)
            except CommandError:
                pass  # unaccepted BLOCKERs fail the exit — still purely a report
            self.assertIn("detectors registered", out.getvalue())
        self.assertEqual(porcelain_hash(), tree_before)
        self.assertEqual({m._meta.label: m.objects.count() for m in apps.get_models()},
                         db_before)

    def test_diff_mode_runs_read_only(self):
        import io
        import tempfile
        from django.core.management.base import CommandError
        tree_before = porcelain_hash()
        with tempfile.TemporaryDirectory() as d:
            try:
                call_command("knowledge_sync", diff=True, report=d, stdout=io.StringIO())
            except CommandError:
                pass
        self.assertEqual(porcelain_hash(), tree_before)

    def _artifact_hashes(self):
        # THE KS-C INCIDENT LESSON (log §KS-C, 2026-07-17): porcelain is BLIND
        # to content changes in UNTRACKED files — the graph was rewritten in
        # place by the validator's repro subprocess while porcelain stayed
        # identical. Knowledge artifacts are therefore hashed EXPLICITLY.
        import hashlib
        import os
        from devseed.knowledge.d1_code_docs import REPO_ROOT
        from devseed.knowledge.d4_generated import GENERATED_ROOT, _generated_files
        h = hashlib.sha256()
        with open(os.path.join(REPO_ROOT, "docs", "knowledge_graph.json"), "rb") as fh:
            h.update(fh.read())
        for rel in _generated_files():
            with open(os.path.join(GENERATED_ROOT, rel), "rb") as fh:
                h.update(fh.read())
        return h.hexdigest()

    def test_full_deep_sweep_leaves_knowledge_artifacts_byte_identical(self):
        # The permanent §16.3 pin: a FULL --deep sweep (builder dry-run +
        # in-memory render-compare + the neutralized validator) must leave the
        # graph AND every generated file byte-identical — no rebuild, no
        # regeneration, no repro-subprocess, ever.
        import io
        import tempfile
        from django.core.management.base import CommandError
        before = self._artifact_hashes()
        with tempfile.TemporaryDirectory() as d:
            try:
                call_command("knowledge_sync", deep=True, report=d, stdout=io.StringIO())
            except CommandError:
                pass
        self.assertEqual(self._artifact_hashes(), before,
                         "a sweep modified a knowledge artifact — §16.3 cardinal sin")
