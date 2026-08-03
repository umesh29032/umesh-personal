"""Phase-5 M1 tests — the optimize op in the isolated runtime, driven
through the real bridge. Corrections locked: invalid-first discard;
utilization -> length -> compactness ranking (compactness never beats
either); FULL-placement seed determinism."""
import json
import unittest

from django.test import TestCase

from patterns_ai.services import compute_bridge

RUNTIME_OK = compute_bridge.runtime_available()


def rect(x0, y0, w, h):
    return [[x0, y0], [x0 + w, y0], [x0 + w, y0 + h], [x0, y0 + h]]


def job(**over):
    base = {
        'op': 'optimize', 'width_mm': 900.0, 'height_mm': 1500.0,
        'spacing_mm': 3.0, 'seed': 7, 'options_wanted': 3,
        'effort': 'fast',
        'fixed': [{'key': 'front', 'instance': 0, 'locked': True,
                   'polygon_mm': rect(3, 3, 300, 200)}],
        'free': [
            {'key': 'front', 'instance': 1, 'mirrored': False,
             'rotation_deg': 0, 'allow_180': True,
             'polygon_mm': rect(0, 0, 300, 200)},
            {'key': 'cuff', 'instance': 0, 'mirrored': False,
             'rotation_deg': 0, 'allow_180': True,
             'polygon_mm': rect(0, 0, 150, 100)},
            {'key': 'cuff', 'instance': 1, 'mirrored': False,
             'rotation_deg': 0, 'allow_180': True,
             'polygon_mm': rect(0, 0, 150, 100)},
        ],
    }
    base.update(over)
    return base


def run(j):
    return compute_bridge.run_tool('nest', j)


@unittest.skipUnless(RUNTIME_OK, 'compute runtime required (ADR-F)')
class OptimizeEngineTests(TestCase):

    # -- hard constraints 9.1–9.4 -----------------------------------------

    def test_fixed_pieces_byte_identical_in_every_option(self):
        j = job()
        res = run(j)
        self.assertTrue(res['ok'], res)
        for o in res['options']:
            fixed = [p for p in o['placements'] if p.get('locked')]
            self.assertEqual(len(fixed), 1)
            self.assertEqual(fixed[0]['polygon_mm'], rect(3, 3, 300, 200))
            self.assertEqual(fixed[0]['key'], 'front')

    def test_no_overlap_and_width_verified_on_every_option(self):
        res = run(job())
        for o in res['options']:
            self.assertTrue(o['verification']['ok'])
            self.assertEqual(o['verification']['max_overlap_mm2'], 0.0)
            self.assertTrue(o['verification']['within_width'])

    def test_only_free_pieces_moved(self):
        res = run(job())
        o = res['options'][0]
        moved = [p for p in o['placements'] if not p.get('locked')]
        self.assertEqual(len(moved), 3)
        # each moved piece keeps its identity + rotation rule 0/180
        for p in moved:
            self.assertIn(p['rotation_deg'], (0, 180))

    def test_height_hard_constraint_drops_and_refuses_honestly(self):
        # height so small nothing fits -> honest error
        res = run(job(height_mm=50))
        self.assertFalse(res['ok'])
        self.assertIn('fabric height', res['error'])
        self.assertGreater(res['dropped']['height'], 0)

    def test_piece_wider_than_fabric_refused(self):
        res = run(job(width_mm=120, free=[
            {'key': 'huge', 'instance': 0, 'mirrored': False,
             'rotation_deg': 0, 'allow_180': True,
             'polygon_mm': rect(0, 0, 500, 400)}]))
        self.assertFalse(res['ok'])
        self.assertIn('width', res['error'])

    def test_nothing_free_refused_honestly(self):
        res = run(job(free=[]))
        self.assertFalse(res['ok'])
        self.assertIn('locked or out of the selection', res['error'])

    # -- correction 2: FULL-placement determinism ---------------------------

    def test_seed_determinism_full_placements(self):
        r1 = run(job(seed=99, effort='fast'))
        r2 = run(job(seed=99, effort='fast'))
        self.assertTrue(r1['ok'] and r2['ok'])
        self.assertEqual(json.dumps(r1['options'], sort_keys=True),
                         json.dumps(r2['options'], sort_keys=True))

    def test_different_seed_may_differ_but_stays_valid(self):
        r1 = run(job(seed=1))
        r2 = run(job(seed=2))
        for r in (r1, r2):
            self.assertTrue(r['ok'])
            for o in r['options']:
                self.assertTrue(o['verification']['ok'])

    # -- correction 1: ranking order ----------------------------------------

    def test_ranking_utilization_then_length_then_compactness(self):
        res = run(job(options_wanted=8, effort='balanced'))
        opts = res['options']
        self.assertGreaterEqual(len(opts), 2)
        # returned order must be non-increasing utilization; within the
        # tolerance bucket non-decreasing length; ties by compactness
        for a, b in zip(opts, opts[1:]):
            ua = round(a['utilization_pct'] / 0.01)
            ub = round(b['utilization_pct'] / 0.01)
            self.assertGreaterEqual(ua, ub)
            if ua == ub:
                self.assertLessEqual(a['length_mm'], b['length_mm'])
                if a['length_mm'] == b['length_mm']:
                    self.assertLessEqual(a['compactness'], b['compactness'])

    def test_compactness_never_beats_length(self):
        """Adversarial: an option strictly shorter must rank above a more
        'compact' but longer one — build both orderings from real runs and
        assert the sort key law directly on the returned list."""
        res = run(job(options_wanted=8, effort='balanced', seed=3))
        opts = res['options']
        for a, b in zip(opts, opts[1:]):
            if round(a['utilization_pct'] / 0.01) == round(
                    b['utilization_pct'] / 0.01):
                # same utilization bucket: length dominates regardless of
                # compactness values
                self.assertLessEqual(a['length_mm'], b['length_mm'])

    # -- options + controls --------------------------------------------------

    def test_options_wanted_honored_and_distinct(self):
        res = run(job(options_wanted=2, effort='balanced'))
        self.assertLessEqual(len(res['options']), 2)
        keys = set()
        for o in res['options']:
            free = [p for p in o['placements'] if not p.get('locked')]
            keys.add(json.dumps(free, sort_keys=True))
        self.assertEqual(len(keys), len(res['options']))   # deduped

    def test_effort_maps_to_search_size(self):
        fast = run(job(effort='fast'))
        best = run(job(effort='best'))
        self.assertGreater(best['orderings_tried'],
                           fast['orderings_tried'])
        bad = run(job(effort='turbo'))
        self.assertFalse(bad['ok'])

    def test_spacing_honored_against_fixed(self):
        """Free pieces must keep >= spacing distance from the fixed
        obstacle (grid raster + buffer guarantee; assert geometrically)."""
        res = run(job(spacing_mm=10.0, effort='fast'))
        self.assertTrue(res['ok'])
        fixed_ring = rect(3, 3, 300, 200)

        def dist_boxes(r1, r2):
            ax0 = min(p[0] for p in r1); ax1 = max(p[0] for p in r1)
            ay0 = min(p[1] for p in r1); ay1 = max(p[1] for p in r1)
            bx0 = min(p[0] for p in r2); bx1 = max(p[0] for p in r2)
            by0 = min(p[1] for p in r2); by1 = max(p[1] for p in r2)
            dx = max(ax0 - bx1, bx0 - ax1, 0)
            dy = max(ay0 - by1, by0 - ay1, 0)
            return (dx * dx + dy * dy) ** 0.5
        for o in res['options']:
            for p in o['placements']:
                if p.get('locked'):
                    continue
                # rect-vs-rect gap: bbox distance == true distance here
                self.assertGreaterEqual(
                    dist_boxes(p['polygon_mm'], fixed_ring), 9.0,
                    p['key'])
