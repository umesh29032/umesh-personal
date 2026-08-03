"""Phase 5 — workspace interactions (server-side truths).

The interactions themselves are client-session-only (browser-verified);
Django proves: the payload contract, the import affordances, the
interaction chrome, and — above all — that the shell still WRITES
NOTHING and accepts no POST."""
import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounts.models import Role
from production.models import (Product, ProductPattern,
                               ProductPatternAssignment, ProductSize)
from patterns_ai.models import PatternPiece, PieceSizeGeometry
from patterns_ai.services import pattern_geometry_service as geo
from patterns_ai.tests.test_p3_generation import rect_um

User = get_user_model()


class _P5Base(TestCase):
    @classmethod
    def setUpTestData(cls):
        mgr = Role.objects.get_or_create(code='manager',
                                         defaults={'name': 'M'})[0]
        cls.mgr = User.objects.create_user('p5@test.local', password='x',
                                           role=mgr)
        cls.product = Product.objects.create(code='P5I', name='P5 Interact')
        cls.size_s = ProductSize.objects.create(product=cls.product,
                                                code='s', label='S',
                                                display_order=1)
        # strict-grain PAIR piece (body) + free-grain non-pair (rib, optional)
        cls.sleeve = cls._piece('p5-slv', 'Sleeve', 'body', is_pair=True)
        geo.set_piece_rules(user=cls.mgr, piece=cls.sleeve,
                            grain_rule='strict')
        d = geo.get_or_create_draft(user=cls.mgr, piece=cls.sleeve)
        PieceSizeGeometry.objects.create(       # fixture only
            version=d, size=cls.size_s, geometry=rect_um(380, 220),
            trust_grade='photo_calibrated', created_by=cls.mgr)
        geo.confirm_version(user=cls.mgr, version=d)
        cls.rib = cls._piece('p5-rib', 'Neck Rib', 'rib')
        geo.set_piece_optional(user=cls.mgr, piece=cls.rib,
                               is_optional=True)
        geo.set_piece_rules(user=cls.mgr, piece=cls.rib, grain_rule='free')
        d2 = geo.get_or_create_draft(user=cls.mgr, piece=cls.rib)
        PieceSizeGeometry.objects.create(
            version=d2, size=cls.size_s, geometry=rect_um(300, 40),
            trust_grade='photo_calibrated', created_by=cls.mgr)
        geo.confirm_version(user=cls.mgr, version=d2)

    @classmethod
    def _piece(cls, code, name, group, **kw):
        pattern = ProductPattern.objects.create(code=code, name=name)
        ProductPatternAssignment.objects.create(product=cls.product,
                                                pattern=pattern,
                                                pieces_count=1)
        return geo.create_piece(user=cls.mgr, product=cls.product,
                                pattern=pattern, fabric_group=group, **kw)

    def _html(self):
        self.client.force_login(self.mgr)
        return self.client.get(reverse('patterns_ai:cutting-table',
                                       args=[self.product.pk])
                               ).content.decode()


class WorkspacePayloadTests(_P5Base):
    def test_payload_carries_geometry_and_rules(self):
        html = self._html()
        start = html.index('id="ws-payload"')
        blob = html[html.index('>', start) + 1:html.index('</script>', start)]
        payload = json.loads(blob)
        self.assertEqual(len(payload), 2)          # both confirmed designs
        slv = payload[f'{self.sleeve.pk}:{self.size_s.pk}']
        # M4.5 R2-A conscious update: the payload ships the
        # CAPABILITIES contract instead of loose flags
        self.assertEqual(slv['caps']['rotation'], 'strict')
        self.assertTrue(slv['caps']['mirror'])
        self.assertEqual(slv['group'], 'body')
        self.assertEqual(slv['w'], 380.0)
        self.assertTrue(len(slv['outline']) >= 4)   # real mm outline
        rib = payload[f'{self.rib.pk}:{self.size_s.pk}']
        self.assertEqual(rib['caps']['rotation'], 'free')
        self.assertFalse(rib['caps']['mirror'])

    def test_import_affordance_and_chrome_rendered(self):
        # M4 conscious update (§18-c/§18-f): the import affordance moved
        # into the client-built IMPORT QUEUE (static dct.js renders
        # .q-import buttons from payload × plan); the server ships the
        # queue container + the same payload; workspace chrome unchanged.
        html = self._html()
        self.assertIn('id="queue-body"', html)
        self.assertIn('patterns_ai/dct', html)          # the engine file
        self.assertIn(f'{self.sleeve.pk}:{self.size_s.pk}', html)  # payload
        for el in ('id="ws-svg"', 'id="pieces-layer"', 'id="selbar"',
                   'id="act-rotate"', 'id="act-mirror"', 'id="act-delete"',
                   'id="act-undo"', 'id="ws-hint"'):
            self.assertIn(el, html)
        # live-counter hooks in Layout Info + status bar (2 each)
        self.assertEqual(html.count('c-imported'), 2)
        self.assertEqual(html.count('c-remaining'), 2)

    def test_toolbar_still_frozen_and_disabled(self):
        html = self._html()
        # 6A/6B/6C conscious rework: Grid + Zoom + AI are LIVE (their
        # phases arrived); the rest stay disabled spans. M4 conscious
        # updates: AI wording = "Suggest Better Layout" (R5); the legacy
        # Generate link RETIRED from navigation (§18-d).
        for label in ('Import', 'Select', 'Rotate', 'Mirror'):
            self.assertIn(f'>{label}</span>', html)   # still spans, disabled
        self.assertIn('id="tb-grid"', html)           # Grid = live (6A)
        self.assertIn('id="tb-zoom"', html)           # Zoom = live (6B)
        self.assertIn('id="tb-ai"', html)             # AI = live (6C)
        self.assertNotIn('Generate (current tool)', html)

    def test_still_zero_writes_and_no_post(self):
        before = (PatternPiece.objects.count(),
                  PieceSizeGeometry.objects.count())
        self._html()
        self.assertEqual(before, (PatternPiece.objects.count(),
                                  PieceSizeGeometry.objects.count()))
        r = self.client.post(reverse('patterns_ai:cutting-table',
                                     args=[self.product.pk]), {})
        self.assertEqual(r.status_code, 405)       # session-only, no writes
