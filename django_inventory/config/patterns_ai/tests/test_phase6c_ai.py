"""Phase 6C — Auto Place + AI Optimize (server-side truths).

Auto Place is client-side deterministic (browser-verified); Django
proves THE ENDPOINT: stateless (zero DB writes through a REAL engine
call), engine reuse (no new engine code), honest contract, gates."""
import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounts.models import Role
from production.models import (Product, ProductPattern,
                               ProductPatternAssignment, ProductSize)
from patterns_ai.models import PieceSizeGeometry
from patterns_ai.services import pattern_geometry_service as geo
from patterns_ai.tests.test_p3_generation import rect_um

User = get_user_model()


def _rect_ring(x, y, w, h):
    return [[x, y], [x + w, y], [x + w, y + h], [x, y + h]]


class Phase6CAiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        mgr = Role.objects.get_or_create(code='manager',
                                         defaults={'name': 'M'})[0]
        wk = Role.objects.get_or_create(code='worker',
                                        defaults={'name': 'W'})[0]
        cls.mgr = User.objects.create_user('p6c@test.local', password='x',
                                           role=mgr)
        cls.worker = User.objects.create_user('p6cw@test.local',
                                              password='x', role=wk)
        cls.product = Product.objects.create(code='P6C', name='P6C AI')
        size = ProductSize.objects.create(product=cls.product, code='s',
                                          label='S', display_order=1)
        pattern = ProductPattern.objects.create(code='p6c-f', name='Front')
        ProductPatternAssignment.objects.create(product=cls.product,
                                                pattern=pattern,
                                                pieces_count=1)
        piece = geo.create_piece(user=cls.mgr, product=cls.product,
                                 pattern=pattern, fabric_group='body')
        d = geo.get_or_create_draft(user=cls.mgr, piece=piece)
        PieceSizeGeometry.objects.create(       # fixture only
            version=d, size=size, geometry=rect_um(400, 300),
            trust_grade='photo_calibrated', created_by=cls.mgr)
        geo.confirm_version(user=cls.mgr, version=d)

    def _url(self):
        return reverse('patterns_ai:cutting-table-optimize',
                       args=[self.product.pk])

    def _optimize(self, placements, **extra):
        self.client.force_login(self.mgr)
        body = {'width_mm': 900, 'height_mm': 2000, 'spacing_mm': 2.0,
                'placements': placements}
        body.update(extra)
        return self.client.post(self._url(), json.dumps(body),
                                content_type='application/json')

    def test_stateless_real_engine_call_zero_writes(self):
        # a wasteful vertical stack the engine can beat — REAL engine run
        placements = [
            {'key': 'a:1', 'instance': 1,
             'polygon_mm': _rect_ring(10, 10, 300, 200),
             'locked': False, 'rotation_deg': 0, 'mirrored': False,
             'allow_180': True},
            {'key': 'a:2', 'instance': 2,
             'polygon_mm': _rect_ring(10, 700, 300, 200),
             'locked': False, 'rotation_deg': 0, 'mirrored': False,
             'allow_180': True},
        ]
        {t: 0 for t in ()}
        rows_before = (PieceSizeGeometry.objects.count(),
                       Product.objects.count())
        r = self._optimize(placements, effort='fast')
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(data['ok'])
        self.assertIn('current', data)          # deltas born server-side
        self.assertTrue(data['options'])
        opt = data['options'][0]
        for k in ('placements', 'utilization_pct', 'delta_utilization_pct',
                  'worse_than_current'):
            self.assertIn(k, opt)
        # THE CONTRACT: positions only — and absolutely no persistence
        self.assertEqual(rows_before, (PieceSizeGeometry.objects.count(),
                                       Product.objects.count()))

    def test_locked_pieces_are_absolute(self):
        # rule 4: everything locked → the engine refuses honestly
        placements = [{'key': 'a:1', 'instance': 1,
                       'polygon_mm': _rect_ring(10, 10, 300, 200),
                       'locked': True, 'rotation_deg': 0,
                       'mirrored': False, 'allow_180': True}]
        r = self._optimize(placements)
        self.assertEqual(r.status_code, 400)
        self.assertIn('locked', r.json()['error'])

    def test_bad_body_and_gates(self):
        self.client.force_login(self.mgr)
        r = self.client.post(self._url(), 'not-json',
                             content_type='application/json')
        self.assertEqual(r.status_code, 400)
        r = self.client.get(self._url())
        self.assertEqual(r.status_code, 405)    # POST-only
        self.client.force_login(self.worker)
        r = self.client.post(self._url(), '{}',
                             content_type='application/json')
        self.assertEqual(r.status_code, 403)

    def test_chrome_auto_vs_ai_separated(self):
        # M4 conscious update (§18-f + R5): engine source lives in the
        # static dct.js; the AI button now reads "Suggest Better Layout".
        from django.contrib.staticfiles import finders
        self.client.force_login(self.mgr)
        html = self.client.get(reverse('patterns_ai:cutting-table',
                                       args=[self.product.pk])
                               ).content.decode()
        js = open(finders.find('patterns_ai/dct.js')).read()
        self.assertIn('id="act-autoplace"', html)   # deterministic assist
        self.assertIn('id="tb-ai"', html)           # the search engine
        self.assertIn('Suggest Better Layout', html)     # R5 wording
        self.assertIn('deterministic first-fit', html)   # button title
        self.assertIn('never', html.lower())        # separation stated
        self.assertIn("state.stage", js)            # rule-6 stage machine
        self.assertIn('Optimized (unsaved)', js)
        self.assertIn("never 'approved'", js)       # human-only approval