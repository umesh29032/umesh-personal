"""KS-E — THE SYNC-D4 PERMANENT GUARD SUBSET (owner-ratified default, KS-0):
the drift classes promoted to BUILD-RED forever — dead-CI-guarded-path ·
hand-edit/fence-integrity · graph-invariant violations. These are the
PkalsNavigationGuardTests extension pattern: each test runs an EXISTING
detector against the LIVE corpus and fails the battery on its BLOCKER class
(everything else stays report-only, per SYNC-D3/D4). No new detection logic —
the detectors are the KS-B/KS-C implementations, reused."""

from django.test import SimpleTestCase

from devseed.knowledge import BLOCKER
from devseed.knowledge.d2_graph import detect_graph_validator
from devseed.knowledge.d3_graph_census import detect_graph_consistency
from devseed.knowledge.d4_generated import detect_fence_integrity
from devseed.knowledge.d5_manifest import detect_manifest_paths


class SyncGuardSubsetTests(SimpleTestCase):
    """Battery-red on the owner-promoted BLOCKER classes (SYNC-D4)."""

    def test_guard_no_dead_manifest_paths(self):
        # The dead-CI-guarded-path class: the canonical manifest may never
        # route to a missing doc (report-side twin of PkalsNavigationGuardTests).
        blockers = [f for f in detect_manifest_paths() if f.severity == BLOCKER]
        self.assertEqual(blockers, [],
                         "dead canonical-manifest path(s): "
                         + ", ".join(f.id for f in blockers))

    def test_guard_no_fence_corruption(self):
        # The hand-edit-in-fence class, fence half: corpus-wide pairing.
        self.assertEqual(detect_fence_integrity(), [])

    def test_guard_graph_invariants_hold(self):
        # The graph-invariant class: the imported Phase-8 validator must
        # report zero FATALs against today's tree (its repro subprocess stays
        # neutralized — the §16.3 pin).
        blockers = [f for f in detect_graph_validator() if f.severity == BLOCKER]
        self.assertEqual(blockers, [],
                         "graph invariant violation(s): "
                         + ", ".join(f.id for f in blockers))

    def test_guard_graph_integrity_gate(self):
        # The hand-edited-graph class: the P9 load_graph gate (content-hash
        # recompute + schema pin) must accept the on-disk graph.
        self.assertEqual(detect_graph_consistency(), [])
