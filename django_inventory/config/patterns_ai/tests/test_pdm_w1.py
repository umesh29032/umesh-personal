"""PDM W1 tests — the read-only design facade (plan §0b): Design Rows
as complete business objects, legacy-readiness parity, zero writes."""
from django.contrib.auth import get_user_model
from django.test import TestCase

from accounts.models import Role
from production.models import (Product, ProductPattern,
                               ProductPatternAssignment, ProductSize)
from patterns_ai.models import (CaptureAsset, PieceSizeGeometry)
from patterns_ai.services import pattern_design_facade as facade
from patterns_ai.services import pattern_geometry_service as geo
from patterns_ai.tests.test_p3_generation import rect_um
from patterns_ai.views import _hub_readiness_legacy_reference

User = get_user_model()


class _W1Base(TestCase):
    @classmethod
    def setUpTestData(cls):
        mgr = Role.objects.get_or_create(code='manager', defaults={'name': 'M'})[0]
        cls.mgr = User.objects.create_user('w1@test.local', password='x', role=mgr)
        cls.product = Product.objects.create(code='W1P', name='W1 Product')
        cls.size_s = ProductSize.objects.create(product=cls.product, code='s',
                                                label='S', display_order=1)
        cls.size_m = ProductSize.objects.create(product=cls.product, code='m',
                                                label='M', display_order=2)
        # Front: confirmed S+M (tape-accepted via confirm)
        cls.front = cls._piece('w1-front', 'Front Panel')
        draft = geo.get_or_create_draft(user=cls.mgr, piece=cls.front)
        tape = {}
        for size, (w, h) in ((cls.size_s, (480, 660)), (cls.size_m, (505, 675))):
            PieceSizeGeometry.objects.create(   # fixture only
                version=draft, size=size, geometry=rect_um(w, h),
                trust_grade='photo_calibrated', created_by=cls.mgr)
            tape[size.pk] = {'width_mm': w, 'height_mm': h}
        geo.confirm_version(user=cls.mgr, version=draft, tape_by_size=tape)
        # a v2 draft in progress for Front. M8.1 conscious update: post-
        # confirm drafts COPY-FORWARD every size now (bare-draft safety),
        # so the in-progress S edit lands on the CARRIED row — the real
        # workflow, not a hand-made single-size draft.
        cls.front_v2 = geo.get_or_create_draft(user=cls.mgr, piece=cls.front)
        _s_row = cls.front_v2.size_geometries.get(size=cls.size_s)
        _s_row.geometry = rect_um(482, 660)
        _s_row.save()
        # Pocket: optional, confirmed S only, WITHOUT tape (unverified dims)
        cls.pocket = cls._piece('w1-pocket', 'Pocket')
        geo.set_piece_optional(user=cls.mgr, piece=cls.pocket,
                               is_optional=True)
        d2 = geo.get_or_create_draft(user=cls.mgr, piece=cls.pocket)
        PieceSizeGeometry.objects.create(
            version=d2, size=cls.size_s, geometry=rect_um(130, 140),
            trust_grade='photo_calibrated', created_by=cls.mgr)
        geo.confirm_version(user=cls.mgr, version=d2)
        # reference image on Front only
        asset = CaptureAsset.objects.create(          # fixture only
            product=cls.product, kind=CaptureAsset.Kind.REFERENCE_IMAGE,
            source='gallery', original_filename='r.png',
            content_type='image/png', size_bytes=2048, sha256='f' * 64,
            metadata={'schema_version': 1}, uploaded_by=cls.mgr,
            file='patterns_ai/x/originals/f.png')
        geo.set_reference_image(user=cls.mgr, piece=cls.front, asset=asset)
        cls.ref_id = asset.pk

    @classmethod
    def _piece(cls, code, name):
        pattern = ProductPattern.objects.create(code=code, name=name)
        ProductPatternAssignment.objects.create(product=cls.product,
                                                pattern=pattern,
                                                pieces_count=1)
        return geo.create_piece(user=cls.mgr, product=cls.product,
                                pattern=pattern, fabric_group='body')


class DesignLibraryTests(_W1Base):
    def _lib(self):
        return facade.product_design_library(self.product)

    def test_sections_follow_size_chart(self):
        lib = self._lib()
        self.assertEqual([s['size'].code for s in lib['sections']],
                         ['s', 'm'])
        # every section lists EVERY piece (ghosts in place);
        # W2R conscious update: rows order ISSUES-FIRST, so the S
        # section (both confirmed) is alphabetical, while M floats the
        # missing Pocket above the confirmed Front Panel.
        self.assertEqual([r['piece_name'] for r in lib['sections'][0]['rows']],
                         ['Front Panel', 'Pocket'])
        self.assertEqual([r['piece_name'] for r in lib['sections'][1]['rows']],
                         ['Pocket', 'Front Panel'])

    def test_design_row_is_a_complete_business_object(self):
        lib = self._lib()
        row = lib['sections'][0]['rows'][0]           # Front · S
        self.assertEqual(row['design_key'],
                         f'{self.front.pk}:{self.size_s.pk}')
        self.assertEqual(row['status'], 'confirmed')
        self.assertEqual(row['version_no'], 1)
        self.assertTrue(row['draft_in_progress'])     # v2 draft exists
        self.assertEqual(row['draft_version_no'], 2)
        self.assertEqual(row['dims'],
                         {'w_mm': 480.0, 'h_mm': 660.0,
                          'measured': True, 'label': 'tape-accepted'})
        self.assertEqual(row['reference_asset_id'], self.ref_id)
        self.assertEqual(row['outline_mm'][2], [480.0, 660.0])
        self.assertIsNotNone(row['geometry_row_id'])
        self.assertEqual(row['badges'],
                         {'optional': False, 'pair': False, 'fold': False})
        self.assertEqual(row['next_step'], 'Ready ✓')

    def test_unverified_dims_carry_honest_label(self):
        lib = self._lib()
        pocket_s = lib['sections'][0]['rows'][1]
        self.assertEqual(pocket_s['status'], 'confirmed')
        self.assertFalse(pocket_s['dims']['measured'])
        self.assertNotEqual(pocket_s['dims']['label'], 'tape-accepted')
        self.assertEqual(pocket_s['dims']['w_mm'], 130.0)

    def test_ghost_row_for_missing_design(self):
        lib = self._lib()
        # W2R: issues float up — the missing Pocket is FIRST in M
        pocket_m = lib['sections'][1]['rows'][0]      # Pocket · M missing
        self.assertEqual(pocket_m['status'], 'missing')
        self.assertIsNone(pocket_m['outline_mm'])
        self.assertIsNone(pocket_m['dims'])
        self.assertEqual(pocket_m['next_step'], 'Add geometry')
        self.assertTrue(pocket_m['badges']['optional'])

    def test_draft_only_row(self):
        # Front S has v1 confirmed; make a fresh piece with draft only
        sleeve = self._piece('w1-sleeve', 'Sleeve')
        d = geo.get_or_create_draft(user=self.mgr, piece=sleeve)
        PieceSizeGeometry.objects.create(
            version=d, size=self.size_s, geometry=rect_um(380, 220),
            trust_grade='photo_calibrated', created_by=self.mgr)
        lib = self._lib()
        row = [r for r in lib['sections'][0]['rows']
               if r['piece_name'] == 'Sleeve'][0]
        self.assertEqual(row['status'], 'draft')
        self.assertEqual(row['next_step'], 'Confirm the draft')
        self.assertIsNone(row['version_no'])

    def test_summary_counts(self):
        lib = self._lib()
        s = lib['summary']
        self.assertEqual(s['sizes_count'], 2)
        self.assertEqual(s['pieces_count'], 2)
        self.assertEqual(s['designs_confirmed'], 3)   # F·S F·M P·S
        self.assertEqual(s['designs_total'], 4)
        self.assertIn('pct', s); self.assertIn('blockers', s)

    def test_sizeless_product_payload(self):
        bare = Product.objects.create(code='W1B', name='Bare')
        lib = facade.product_design_library(bare)
        self.assertEqual(lib['sections'], [])
        self.assertEqual(lib['summary']['sizes_count'], 0)
        self.assertFalse(lib['summary']['ready'])

    def test_facade_reads_never_write(self):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        with CaptureQueriesContext(connection) as ctx:
            facade.product_design_library(self.product)
        writes = [q for q in ctx.captured_queries
                  if q['sql'].split()[0].upper() in
                  ('INSERT', 'UPDATE', 'DELETE')]
        self.assertEqual(writes, [])


class ReadinessParityTests(_W1Base):
    def test_facade_readiness_equals_legacy_verbatim(self):
        new = facade.product_readiness(self.product)
        old = _hub_readiness_legacy_reference(self.product)
        self.assertEqual(new['pct'], old['pct'])
        self.assertEqual(new['ready'], old['ready'])
        self.assertEqual(new['blockers'], old['blockers'])
        self.assertEqual(new['warnings'], old['warnings'])
        self.assertEqual(new['checklist'], old['checklist'])
        self.assertEqual(
            [(r['name'], r['next_step'],
              [(s.pk, st) for s, st in r['cells']]) for r in new['rows']],
            [(r['name'], r['next_step'],
              [(s.pk, st) for s, st in r['cells']]) for r in old['rows']])

    def test_hub_and_generate_pages_still_render(self):
        self.client.force_login(self.mgr)
        hub = self.client.get(
            f'/patterns/pieces/?product={self.product.pk}')
        self.assertContains(hub, 'Pattern Manager')  # W2R vocabulary
        gen = self.client.get(
            f'/patterns/generate/?product={self.product.pk}')
        self.assertContains(gen, 'Readiness — pieces × sizes')
