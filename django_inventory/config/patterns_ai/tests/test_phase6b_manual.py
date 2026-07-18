"""Phase 6B — manual optimization (server-side truths).

Compact/zoom/pan/nudge run client-side (browser-verified); Django pins:
the boundary constraint exists as pipeline layer 0, camera≠world is
structural, nudge constants internal, Compact control present — and the
table still writes NOTHING."""
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


class Phase6BManualTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        mgr = Role.objects.get_or_create(code='manager',
                                         defaults={'name': 'M'})[0]
        cls.mgr = User.objects.create_user('p6b@test.local', password='x',
                                           role=mgr)
        cls.product = Product.objects.create(code='P6B', name='P6B Manual')
        size = ProductSize.objects.create(product=cls.product, code='s',
                                          label='S', display_order=1)
        pattern = ProductPattern.objects.create(code='p6b-f', name='Front')
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

    def _html(self):
        self.client.force_login(self.mgr)
        return self.client.get(reverse('patterns_ai:cutting-table',
                                       args=[self.product.pk])
                               ).content.decode()

    def _js(self):
        # M4 §18-f conscious update: source-level physics assertions
        # read the STATIC engine file (behavior unchanged, home moved).
        from django.contrib.staticfiles import finders
        return open(finders.find('patterns_ai/dct.js')).read()

    def test_boundary_is_pipeline_layer_zero(self):
        js = self._js()
        self.assertIn('boundaryViolation', js)
        self.assertIn('placementStatus', js)        # the ONE pipeline
        self.assertIn('col-bound', js)              # its paint channel
        self.assertIn('col-bound', self._html())    # CSS channel present

    def test_camera_is_not_world(self):
        js = self._js()
        self.assertIn('camera ≠ world', js.lower())
        self.assertIn('applyCamera', js)
        self.assertIn('id="tb-zoom"', self._html())  # Zoom live (6B)

    def test_compact_and_nudge_internal_constants(self):
        js = self._js()
        self.assertIn('id="act-compact"', self._html())
        self.assertIn('not an optimizer', js)       # rule 4, in source
        self.assertIn('NUDGE_MM = 1', js)
        self.assertIn('NUDGE_FAST_MM = 10', js)
        self.assertIn('NUDGE_JUMP_MM = 100', js)    # future constant only

    def test_still_zero_writes_and_no_post(self):
        before = PieceSizeGeometry.objects.count()
        self._html()
        self.assertEqual(PieceSizeGeometry.objects.count(), before)
        r = self.client.post(reverse('patterns_ai:cutting-table',
                                     args=[self.product.pk]), {})
        self.assertEqual(r.status_code, 405)
