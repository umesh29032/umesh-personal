"""Phase 6A — physics (server-side truths).

Collision/spacing/snap/utilization run client-side (browser-verified);
Django pins the inputs the physics depends on: area in the payload,
the spacing rule from the profile, the live Grid control, the live
readout slots — and that the table still writes NOTHING."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounts.models import Role
from production.models import (Product, ProductPattern,
                               ProductPatternAssignment, ProductSize)
from patterns_ai.models import PieceSizeGeometry, ProductFabricProfile
from patterns_ai.services import pattern_geometry_service as geo
from patterns_ai.tests.test_p3_generation import rect_um

User = get_user_model()


class Phase6APhysicsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        mgr = Role.objects.get_or_create(code='manager',
                                         defaults={'name': 'M'})[0]
        cls.mgr = User.objects.create_user('p6a@test.local', password='x',
                                           role=mgr)
        cls.product = Product.objects.create(code='P6A', name='P6A Physics')
        cls.size_s = ProductSize.objects.create(product=cls.product,
                                                code='s', label='S',
                                                display_order=1)
        pattern = ProductPattern.objects.create(code='p6a-f', name='Front')
        ProductPatternAssignment.objects.create(product=cls.product,
                                                pattern=pattern,
                                                pieces_count=1)
        piece = geo.create_piece(user=cls.mgr, product=cls.product,
                                 pattern=pattern, fabric_group='body')
        d = geo.get_or_create_draft(user=cls.mgr, piece=piece)
        PieceSizeGeometry.objects.create(       # fixture only
            version=d, size=cls.size_s, geometry=rect_um(400, 300),
            trust_grade='photo_calibrated', created_by=cls.mgr)
        geo.confirm_version(user=cls.mgr, version=d)
        ProductFabricProfile.objects.create(
            product=cls.product, default_width_mm=1600,
            default_spacing_mm='3.0', created_by=cls.mgr)

    def _html(self):
        self.client.force_login(self.mgr)
        return self.client.get(reverse('patterns_ai:cutting-table',
                                       args=[self.product.pk])
                               ).content.decode()

    def _js(self):
        # M4 §18-f conscious update: the session engine lives in the
        # STATIC dct.js — source-level physics assertions read it there.
        from django.contrib.staticfiles import finders
        return open(finders.find('patterns_ai/dct.js')).read()

    def test_payload_carries_area_for_utilization(self):
        html = self._html()
        # 400×300 mm rect = 1200 cm² — the utilization input, facade truth
        self.assertIn('"area": 1200.0', html)

    def test_spacing_rule_from_profile_reaches_the_pipeline(self):
        html = self._html()
        # M4: spacing reaches the engine via the ws-config DATA hand-off
        self.assertIn('"spacing_mm": 3.0', html)
        self.assertIn('Spacing:</b> 3.0 mm', html)
        self.assertIn('CONFIG.spacing_mm', self._js())

    def test_grid_live_and_physics_slots_present(self):
        html = self._html()
        js = self._js()
        self.assertIn('id="tb-grid"', html)              # live control
        self.assertIn('SNAP_MM = 10', js)                # internal config
        self.assertIn('id="ws-collisions"', html)
        self.assertEqual(html.count('class="c-util"'), 2)   # LI + status
        self.assertIn('c-length', html)
        # frozen coordinate system documented at the source
        self.assertIn('world = MILLIMETRES', js)

    def test_still_zero_writes_and_no_post(self):
        before = PieceSizeGeometry.objects.count()
        self._html()
        self.assertEqual(PieceSizeGeometry.objects.count(), before)
        r = self.client.post(reverse('patterns_ai:cutting-table',
                                     args=[self.product.pk]), {})
        self.assertEqual(r.status_code, 405)
