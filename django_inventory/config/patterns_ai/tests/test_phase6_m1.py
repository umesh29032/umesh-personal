"""Phase-6 M1 tests — BLF internal timebox (finding F1): the Quick
method gives up honestly instead of hanging until the bridge kills it.
Real runtime through the real bridge."""
import unittest

from django.test import TestCase

from patterns_ai.services import compute_bridge

RUNTIME_OK = compute_bridge.runtime_available()


def rect(w, h):
    return [[0, 0], [w, 0], [w, h], [0, h]]


def big_generation_job(timebox_s):
    """The F1 shape: many mid-size pieces = long marker = the scan that
    used to hang. 60 pieces of 200x150 on 900 mm."""
    return {'width_mm': 900.0, 'spacing_mm': 3.0, 'engine': 'blf',
            'timebox_s': timebox_s, 'seed': 7,
            'pieces': [{'key': 'p', 'polygon_mm': rect(200, 150),
                        'qty': 60, 'allow_180': True,
                        'allow_mirror': False}]}


@unittest.skipUnless(RUNTIME_OK, 'compute runtime required (ADR-F)')
class BlfTimeboxTests(TestCase):

    def test_generation_blf_gives_up_honestly_within_box(self):
        import time
        t0 = time.time()
        res = compute_bridge.run_tool('nest', big_generation_job(1))
        elapsed = time.time() - t0
        # honest error, well before the bridge's kill window
        self.assertLess(elapsed, 30)
        self.assertFalse(res['candidates'])
        self.assertIn('blf', res['errors'])
        self.assertIn('ran out of time', res['errors']['blf'])
        self.assertIn('Thorough', res['errors']['blf'])

    def test_generation_blf_still_succeeds_with_enough_time(self):
        job = big_generation_job(90)
        job['pieces'][0]['qty'] = 8          # small set, generous box
        res = compute_bridge.run_tool('nest', job)
        self.assertTrue(res['ok'], res)
        self.assertTrue(res['candidates'][0]['verification']['ok'])

    def test_small_sets_byte_identical_to_before(self):
        """The timebox check must not perturb determinism on sets that
        finish in time: two runs, full placements equal."""
        import json
        job = big_generation_job(60)
        job['pieces'][0]['qty'] = 6
        r1 = compute_bridge.run_tool('nest', job)
        r2 = compute_bridge.run_tool('nest', job)
        self.assertTrue(r1['ok'] and r2['ok'])
        self.assertEqual(
            json.dumps(r1['candidates'][0]['placements'], sort_keys=True),
            json.dumps(r2['candidates'][0]['placements'], sort_keys=True))

    def test_optimize_op_inherits_the_honest_giveup(self):
        """Locked-piece optimizer (BLF-based) with a big free set + tiny
        timebox: zero options, timeout surfaced in the drop counters,
        the honest message returned."""
        job = {'op': 'optimize', 'width_mm': 900.0, 'height_mm': 100000.0,
               'spacing_mm': 3.0, 'seed': 7, 'options_wanted': 3,
               'effort': 'fast',
               'fixed': [{'key': 'lock', 'instance': 0, 'locked': True,
                          'polygon_mm': rect(300, 200)}],
               'free': [{'key': 'p', 'instance': i, 'mirrored': False,
                         'rotation_deg': 0, 'allow_180': True,
                         'polygon_mm': rect(200, 150)}
                        for i in range(60)]}
        # effort 'fast' = 3 s box — the 60-piece pass cannot finish
        res = compute_bridge.run_tool('nest', job)
        self.assertFalse(res['ok'])
        self.assertGreaterEqual(res['dropped']['timeout'], 1)
        self.assertIn('ran out of time', res['error'])

    def test_optimize_small_sets_unaffected(self):
        job = {'op': 'optimize', 'width_mm': 900.0, 'height_mm': 2000.0,
               'spacing_mm': 3.0, 'seed': 7, 'options_wanted': 2,
               'effort': 'fast',
               'fixed': [{'key': 'lock', 'instance': 0, 'locked': True,
                          'polygon_mm': rect(300, 200)}],
               'free': [{'key': 'p', 'instance': i, 'mirrored': False,
                         'rotation_deg': 0, 'allow_180': True,
                         'polygon_mm': rect(200, 150)}
                        for i in range(3)]}
        res = compute_bridge.run_tool('nest', job)
        self.assertTrue(res['ok'], res)
        self.assertEqual(res['dropped']['timeout'], 0)
        for o in res['options']:
            self.assertTrue(o['verification']['ok'])
