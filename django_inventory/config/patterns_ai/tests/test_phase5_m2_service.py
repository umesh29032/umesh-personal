"""Phase-5 M2 tests — the stateless optimize service + workspace AJAX
endpoint. Clarifications pinned: payload-complete statelessness, server
remembers nothing (zero writes), stable in-response option ids."""
import json
import shutil
import tempfile
import unittest

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from accounts.models import Role
from production.models import (Product, ProductPattern,
                               ProductPatternAssignment, ProductSize)
from patterns_ai.models import (GeneratedMarkerCandidate,
                                MarkerGenerationRun, PieceSizeGeometry,
                                SuggestionEvent)
from patterns_ai.services import compute_bridge
from patterns_ai.services import marker_generation_service as gen
from patterns_ai.services import pattern_geometry_service as geo
from patterns_ai.tests.test_p3_generation import rect_um

User = get_user_model()
MEDIA = tempfile.mkdtemp(prefix='pai-ph5m2-media-')
RUNTIME_OK = compute_bridge.runtime_available()


def rect(x0, y0, w, h):
    return [[x0, y0], [x0 + w, y0], [x0 + w, y0 + h], [x0, y0 + h]]


def layout():
    """A 3-piece current layout: one locked, two free."""
    return [
        {'key': 'front', 'instance': 0, 'mirrored': False,
         'rotation_deg': 0, 'locked': True,
         'polygon_mm': rect(3, 3, 300, 200)},
        {'key': 'front', 'instance': 1, 'mirrored': False,
         'rotation_deg': 0, 'locked': False,
         'polygon_mm': rect(3, 250, 300, 200)},
        {'key': 'cuff', 'instance': 0, 'mirrored': False,
         'rotation_deg': 0, 'locked': False,
         'polygon_mm': rect(3, 500, 150, 100)},
    ]


@unittest.skipUnless(RUNTIME_OK, 'compute runtime required (ADR-F)')
@override_settings(MEDIA_ROOT=MEDIA)
class _Base(TestCase):
    @classmethod
    def setUpTestData(cls):
        mgr = Role.objects.get_or_create(code='manager', defaults={'name': 'M'})[0]
        wk = Role.objects.get_or_create(code='worker', defaults={'name': 'W'})[0]
        cls.mgr = User.objects.create_user('m2@test.local', password='x', role=mgr)
        cls.worker = User.objects.create_user('m2w@test.local', password='x', role=wk)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    def optimize(self, **over):
        kw = dict(user=self.mgr, width_mm=900, height_mm=1500,
                  spacing_mm=3.0, placements=layout(), selected=[],
                  options_wanted=3, effort='fast', seed=7)
        kw.update(over)
        return gen.optimize_layout(**kw)


class OptimizeServiceTests(_Base):
    def test_stateless_reproducibility_full_payload(self):
        r1 = self.optimize()
        r2 = self.optimize()
        self.assertEqual(json.dumps(r1['options'], sort_keys=True),
                         json.dumps(r2['options'], sort_keys=True))

    def test_server_writes_nothing(self):
        with CaptureQueriesContext(connection) as ctx:
            self.optimize()
        writes = [q for q in ctx.captured_queries
                  if q['sql'].split()[0].upper() in
                  ('INSERT', 'UPDATE', 'DELETE')]
        self.assertEqual(writes, [])
        self.assertEqual(MarkerGenerationRun.objects.count(), 0)
        self.assertEqual(GeneratedMarkerCandidate.objects.count(), 0)
        self.assertEqual(SuggestionEvent.objects.count(), 0)

    def test_stable_option_ids_in_response(self):
        r = self.optimize(options_wanted=5, effort='balanced')
        ids = [o['id'] for o in r['options']]
        self.assertEqual(ids, [f'option-{i}'
                               for i in range(1, len(ids) + 1)])

    def test_current_metrics_and_deltas(self):
        r = self.optimize()
        cur = r['current']
        self.assertGreater(cur['length_mm'], 0)
        self.assertIsNotNone(cur['utilization_pct'])
        self.assertAlmostEqual(cur['utilization_pct'] + cur['waste_pct'],
                               100.0, places=1)
        for o in r['options']:
            self.assertIn('delta_length_mm', o)
            self.assertIn('worse_than_current', o)
            # honesty math: shorter or equal-length options never flagged worse
            if (o['delta_length_mm'] is not None
                    and o['delta_length_mm'] <= 0
                    and (o['delta_utilization_pct'] or 0) >= 0):
                self.assertFalse(o['worse_than_current'])

    def test_locked_pieces_pass_through_every_option(self):
        r = self.optimize()
        for o in r['options']:
            locked = [p for p in o['placements'] if p.get('locked')]
            self.assertEqual(len(locked), 1)
            self.assertEqual(locked[0]['polygon_mm'], rect(3, 3, 300, 200))

    def test_scope_selection_intersection(self):
        # select ONLY the cuff -> front#1 (unlocked, unselected) must be
        # fixed too: byte-identical in every option
        r = self.optimize(selected=[['cuff', 0]])
        for o in r['options']:
            f1 = next(p for p in o['placements']
                      if p['key'] == 'front' and p['instance'] == 1)
            self.assertEqual(f1['polygon_mm'], rect(3, 250, 300, 200))

    def test_scope_honest_errors(self):
        with self.assertRaises(ValidationError) as cm:   # selected all locked
            self.optimize(selected=[['front', 0]])
        self.assertIn('everything selected is locked', str(cm.exception))
        all_locked = [dict(p, locked=True) for p in layout()]
        with self.assertRaises(ValidationError) as cm:
            self.optimize(placements=all_locked)
        self.assertIn('every piece is locked', str(cm.exception))

    def test_controls_validation(self):
        for bad in [dict(options_wanted=0), dict(options_wanted=9),
                    dict(effort='turbo'), dict(spacing_mm=0.1),
                    dict(spacing_mm=99), dict(width_mm=100),
                    dict(height_mm=0), dict(width_mm='x')]:
            with self.assertRaises(ValidationError, msg=bad):
                self.optimize(**bad)
        with self.assertRaises(ValidationError):
            self.optimize(selected=[['front']])          # bad pair
        with self.assertRaises(ValidationError):
            self.optimize(placements=[{'key': 'a'}])     # bad piece

    def test_permission_gate(self):
        with self.assertRaises(PermissionDenied):
            self.optimize(user=self.worker)

    def test_height_refusal_bubbles_honestly(self):
        with self.assertRaises(ValidationError) as cm:
            self.optimize(height_mm=50)
        self.assertIn('fabric height', str(cm.exception))


class OptimizeEndpointTests(_Base):
    """The AJAX branch rides the Phase-4 workspace URL — build one real
    candidate to own the page."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.product = Product.objects.create(code='M2PROD', name='M2')
        cls.size = ProductSize.objects.create(product=cls.product, code='m',
                                              label='M', display_order=1)
        pattern = ProductPattern.objects.create(code='m2-front', name='Front')
        ProductPatternAssignment.objects.create(product=cls.product,
                                                pattern=pattern,
                                                pieces_count=1)
        piece = geo.create_piece(user=cls.mgr, product=cls.product,
                                 pattern=pattern, fabric_group='body')
        draft = geo.get_or_create_draft(user=cls.mgr, piece=piece)
        PieceSizeGeometry.objects.create(      # test fixture only
            version=draft, size=cls.size, geometry=rect_um(300, 200),
            trust_grade='photo_calibrated', created_by=cls.mgr)
        geo.confirm_version(user=cls.mgr, version=draft)
        _, rows = gen.start_run(user=cls.mgr, product=cls.product,
                                usable_width_mm=900, ratio={cls.size: 2},
                                timebox_s=6, engine='blf')
        cls.candidate = rows[0]

    def url(self):
        return reverse('patterns_ai:workspace', args=[self.candidate.pk])

    def post_optimize(self, **over):
        data = {'action': 'optimize', 'width_mm': '900',
                'height_mm': '1500', 'spacing_mm': '3',
                'options_wanted': '3', 'effort': 'fast', 'seed': '7',
                'placements': json.dumps(layout()),
                'selected': '[]'}
        data.update(over)
        return self.client.post(self.url(), data)

    def test_endpoint_returns_options_json(self):
        self.client.force_login(self.mgr)
        resp = self.post_optimize()
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertTrue(body['ok'], body)
        self.assertGreaterEqual(len(body['options']), 1)
        self.assertEqual(body['options'][0]['id'], 'option-1')
        self.assertIn('current', body)
        self.assertIn('worse_than_current', body['options'][0])

    def test_endpoint_persists_nothing(self):
        self.client.force_login(self.mgr)
        runs_before = MarkerGenerationRun.objects.count()
        cands_before = GeneratedMarkerCandidate.objects.count()
        self.post_optimize()
        self.assertEqual(MarkerGenerationRun.objects.count(), runs_before)
        self.assertEqual(GeneratedMarkerCandidate.objects.count(),
                         cands_before)

    def test_endpoint_error_paths(self):
        self.client.force_login(self.mgr)
        body = self.post_optimize(placements='not json').json()
        self.assertFalse(body['ok'])
        self.assertIn('bad layout payload', body['error'])
        body = self.post_optimize(effort='turbo').json()
        self.assertFalse(body['ok'])
        self.assertIn('Fast, Balanced or Best', body['error'])

    def test_endpoint_permissions(self):
        self.client.force_login(self.worker)
        self.assertEqual(self.post_optimize().status_code, 403)
        self.client.logout()
        self.assertEqual(self.post_optimize().status_code, 302)
