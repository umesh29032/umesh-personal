"""Audit-close 2026-07-11 (FOUNDATION_V1_AUDIT §1/§8 item 1): Gate-1
overlay print TILES for pieces larger than one sheet — same 190×277 mm
window / 180×267 mm step / 10 mm dashed match-line grid as the layout
print. Small pieces stay one sheet. True scale everywhere."""
import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import Role
from production.models import (Product, ProductPattern,
                               ProductPatternAssignment, ProductSize)
from patterns_ai.models import PieceSizeGeometry
from patterns_ai.services import pattern_geometry_service as geo
from patterns_ai.tests.test_p3_generation import rect_um

User = get_user_model()
MEDIA = tempfile.mkdtemp(prefix='pai_g1t_')


@override_settings(MEDIA_ROOT=MEDIA)
class Gate1TilingTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        mgr = Role.objects.get_or_create(code='manager',
                                         defaults={'name': 'M'})[0]
        cls.mgr = User.objects.create_user('g1t@test.local', password='x',
                                           role=mgr)
        cls.product = Product.objects.create(code='G1TP', name='G1 Tiling')
        cls.size = ProductSize.objects.create(product=cls.product,
                                              code='m', label='M',
                                              display_order=1)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    def _row(self, code, w_mm, h_mm):
        pattern = ProductPattern.objects.create(code=code, name=code)
        ProductPatternAssignment.objects.create(product=self.product,
                                                pattern=pattern,
                                                pieces_count=1)
        piece = geo.create_piece(user=self.mgr, product=self.product,
                                 pattern=pattern, fabric_group='body')
        draft = geo.get_or_create_draft(user=self.mgr, piece=piece)
        return PieceSizeGeometry.objects.create(     # fixture only
            version=draft, size=self.size, geometry=rect_um(w_mm, h_mm),
            trust_grade='uncalibrated', created_by=self.mgr)

    def _get(self, row):
        self.client.force_login(self.mgr)
        return self.client.get(reverse('patterns_ai:geometry-print',
                                       args=[row.pk]))

    def test_large_piece_tiles_on_the_candidate_grid(self):
        # the REAL case that exposed the gap: 350×510 mm ⇒
        # cols = ceil(350/180) = 2 · rows = ceil(510/267) = 2 ⇒ 4 sheets
        row = self._row('g1t-body', 350, 510)
        resp = self._get(row)
        self.assertContains(resp, '4 sheet(s)')
        for label in ('C1-R1', 'C2-R1', 'C1-R2', 'C2-R2'):
            self.assertContains(resp, f'tile {label}')
        self.assertContains(resp, 'stroke-dasharray')   # match lines
        self.assertContains(resp, 'Assembly: columns')  # multi-sheet note
        # every sheet carries the honesty bar (SVG text node per tile)
        self.assertEqual(resp.content.decode().count('>10 cm</text>'), 4)
        # true-scale window: fixed mm-sized tile svg
        self.assertContains(resp, 'width="190.0mm" height="277.0mm"')

    def test_small_piece_stays_one_sheet(self):
        row = self._row('g1t-pocket', 130, 140)
        resp = self._get(row)
        self.assertContains(resp, '1 sheet(s)')
        self.assertContains(resp, 'tile C1-R1')
        self.assertNotContains(resp, 'C2-R1')
        self.assertNotContains(resp, 'Assembly: columns')
