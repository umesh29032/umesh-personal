"""PDM W2R tests — the LOCKED two-page workflow:
Product Pattern Manager (sizes only, gated CT) → per-size Pattern
Design Library (the Design-Row atoms, issues first)."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounts.models import Role
from production.models import (Product, ProductPattern,
                               ProductPatternAssignment, ProductSize)
from patterns_ai.models import (CaptureAsset, PatternPiece,
                                PieceSizeGeometry, ProductFabricProfile)
from patterns_ai.services import pattern_geometry_service as geo
from patterns_ai.tests.test_p3_generation import rect_um

User = get_user_model()


class _W2RBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        mgr = Role.objects.get_or_create(code='manager', defaults={'name': 'M'})[0]
        wk = Role.objects.get_or_create(code='worker', defaults={'name': 'W'})[0]
        cls.mgr = User.objects.create_user('w2r@test.local', password='x', role=mgr)
        cls.worker = User.objects.create_user('w2rw@test.local', password='x', role=wk)
        cls.product = Product.objects.create(code='W2R', name='W2R Product')
        cls.size_s = ProductSize.objects.create(product=cls.product, code='s',
                                                label='S', display_order=1)
        cls.size_l = ProductSize.objects.create(product=cls.product, code='l',
                                                label='L', display_order=2)
        # Front (REQUIRED): confirmed S only → L NOT ready
        cls.front = cls._piece('w2r-front', 'Front Panel')
        d = geo.get_or_create_draft(user=cls.mgr, piece=cls.front)
        PieceSizeGeometry.objects.create(           # fixture only
            version=d, size=cls.size_s, geometry=rect_um(480, 660),
            trust_grade='photo_calibrated', created_by=cls.mgr)
        geo.confirm_version(user=cls.mgr, version=d,
                            tape_by_size={cls.size_s.pk:
                                          {'width_mm': 480,
                                           'height_mm': 660}})
        cls.front_version = d
        # Pocket (OPTIONAL): nothing anywhere → warnings only
        cls.pocket = cls._piece('w2r-pocket', 'Pocket')
        geo.set_piece_optional(user=cls.mgr, piece=cls.pocket,
                               is_optional=True)

    @classmethod
    def _piece(cls, code, name):
        pattern = ProductPattern.objects.create(code=code, name=name)
        ProductPatternAssignment.objects.create(product=cls.product,
                                                pattern=pattern,
                                                pieces_count=1)
        return geo.create_piece(user=cls.mgr, product=cls.product,
                                pattern=pattern, fabric_group='body')

    def _get(self, qs):
        self.client.force_login(self.mgr)
        return self.client.get(reverse('patterns_ai:piece-list') + qs)


class ManagerPageTests(_W2RBase):
    def test_size_cards_with_verdicts_no_rows(self):
        html = self._get(f'?product={self.product.pk}').content.decode()
        self.assertIn('Ready for Cutting ✓', html)        # S (🟢)
        self.assertIn('Missing Designs', html)            # L = 🔴 (1 required missing, 0 confirmed for L? no — tier rule)
        self.assertIn('Missing: Front Panel', html)       # required only
        self.assertIn('Manage Pattern Designs', html)
        self.assertIn('+ Add Size', html)
        self.assertIn(reverse('production:product-sizes',
                              args=[self.product.pk]), html)
        # THE law: no design rows on the manager
        self.assertNotIn('data-design-key', html)
        self.assertNotIn('NO DESIGN YET', html)

    def test_gate_enabled_when_one_size_ready(self):
        html = self._get(f'?product={self.product.pk}').content.decode()
        # S is Ready (required Front confirmed; Pocket optional) → enabled
        self.assertIn(reverse('patterns_ai:cutting-table', args=[self.product.pk]),
                      html)
        self.assertNotIn('no size is ready yet', html)

    def test_gate_disabled_when_no_size_ready(self):
        bare = Product.objects.create(code='W2RB', name='Bare')
        ProductSize.objects.create(product=bare, code='m', label='M',
                                   display_order=1)
        pattern = ProductPattern.objects.create(code='w2rb-f', name='F')
        ProductPatternAssignment.objects.create(product=bare,
                                                pattern=pattern,
                                                pieces_count=1)
        geo.create_piece(user=self.mgr, product=bare, pattern=pattern,
                         fabric_group='body')       # required, no design
        html = self._get(f'?product={bare.pk}').content.decode()
        self.assertIn('aria-disabled="true"', html)
        self.assertIn('no size is ready yet', html)
        self.assertNotIn(reverse('patterns_ai:cutting-table', args=[bare.pk]), html)

    def test_manager_keeps_details_sheet_and_matrix(self):
        html = self._get(f'?product={self.product.pk}').content.decode()
        self.assertIn('readiness checklist', html)
        self.assertIn('Warnings (never block)', html)
        self.assertIn('Save defaults', html)
        self.assertIn('Readiness matrix — pieces × sizes', html)

    def test_no_sizes_state(self):
        bare = Product.objects.create(code='W2RC', name='Sizeless')
        html = self._get(f'?product={bare.pk}').content.decode()
        self.assertIn('no sizes yet', html)
        self.assertIn('+ Add Size', html)

    def test_chooser_and_worker(self):
        self.client.force_login(self.mgr)
        bare = self.client.get(reverse('patterns_ai:piece-list')
                               ).content.decode()
        self.assertIn('Pick a product', bare)
        self.client.force_login(self.worker)
        self.assertEqual(self._get_status(f'?product={self.product.pk}'),
                         403)

    def _get_status(self, qs):
        return self.client.get(reverse('patterns_ai:piece-list') + qs
                               ).status_code


class LibraryPageTests(_W2RBase):
    def _lib_html(self, size_code='l'):
        return self._get(f'?product={self.product.pk}&size={size_code}'
                         ).content.decode()

    def test_one_size_only_with_issues_first(self):
        html = self._lib_html('l')
        self.assertIn('Preparing Size L', html)   # W2R2 preparation title
        self.assertIn('Needs Attention ⚠', html)
        self.assertIn('Missing:', html)
        # issues first: missing REQUIRED Front floats above optional Pocket
        self.assertLess(html.find('Front Panel'), html.find('Pocket'))
        # only L rows (2 pieces = 2 atoms)
        self.assertEqual(html.count('data-design-key='), 2)
        self.assertIn(f':{self.size_l.pk}"', html)
        self.assertNotIn(f':{self.size_s.pk}"', html)

    def test_confirmed_row_full_facts(self):
        html = self._lib_html('s')
        self.assertIn('Ready for Cutting ✓', html)
        self.assertIn('v1 · Confirmed ✓', html)
        self.assertIn('480.0 × 660.0 mm', html)
        self.assertIn('cm²', html)                        # area
        self.assertIn('(tape-accepted)', html)
        self.assertIn('updated ', html)                   # last updated
        self.assertIn(reverse('patterns_ai:geometry-dxf', args=[
            self.front_version.size_geometries.first().pk]), html)
        self.assertIn(
            reverse('patterns_ai:version-detail',
                    args=[self.front_version.pk])
            + f'#size-{self.size_s.pk}', html)
        self.assertIn('← Sizes', html)

    def test_contextual_actions(self):
        html = self._lib_html('l')
        self.assertIn('+ Add geometry', html)             # missing required
        s_html = self._lib_html('s')
        self.assertIn('Edit →', s_html)                   # confirmed

    def test_manage_in_place_labeled(self):
        # Phase 2 conscious rework (frozen resp. #1): the optional RULE
        # moved to the Blueprint; the Library keeps reference management
        # (documentation) + a pointer to the Blueprint.
        html = self._lib_html('l')
        self.assertIn('applies to all sizes of Front Panel', html)
        self.assertNotIn('make optional', html)
        self.assertNotIn('make required', html)
        self.assertIn('add ref', html)
        self.assertIn(reverse('patterns_ai:blueprint')
                      + f'?product={self.product.pk}', html)

    def test_post_actions_work_from_library(self):
        # Phase 2 conscious rework: set_optional retired from the Manager
        # surface — it must NOT write; the Blueprint module owns it.
        self.client.force_login(self.mgr)
        r = self.client.post(reverse('patterns_ai:piece-list'),
                             {'product': self.product.pk,
                              'action': 'set_optional',
                              'piece': self.pocket.pk, 'is_optional': '0'})
        self.assertEqual(r.status_code, 302)
        self.pocket.refresh_from_db()
        self.assertTrue(self.pocket.is_optional)   # unchanged — refused

    def test_unknown_size_404_and_worker_403(self):
        self.client.force_login(self.mgr)
        self.assertEqual(self.client.get(
            reverse('patterns_ai:piece-list')
            + f'?product={self.product.pk}&size=zz').status_code, 404)
        self.client.force_login(self.worker)
        self.assertEqual(self.client.get(
            reverse('patterns_ai:piece-list')
            + f'?product={self.product.pk}&size=l').status_code, 403)

    def test_get_writes_nothing(self):
        self.client.force_login(self.mgr)
        before = (PatternPiece.objects.count(),
                  CaptureAsset.objects.count(),
                  ProductFabricProfile.objects.count())
        self._lib_html('l'); self._get(f'?product={self.product.pk}')
        self.assertEqual(before, (PatternPiece.objects.count(),
                                  CaptureAsset.objects.count(),
                                  ProductFabricProfile.objects.count()))


class W2R2PreparationTests(_W2RBase):
    def test_traffic_light_tiers(self):
        # S = 🟢 ready; L = 🔴 (required missing AND zero confirmed for L)
        html = self._get(f'?product={self.product.pk}').content.decode()
        self.assertIn('🟢 Ready for Cutting', html)
        self.assertIn('🔴 Missing Designs', html)
        # make L a 🟡: confirm Front for L (1 confirmed, 0 required gaps →
        # ready actually) — instead build attention case: new required
        # piece w/o design while Front·L confirmed
        d2 = geo.get_or_create_draft(user=self.mgr, piece=self.front)
        PieceSizeGeometry.objects.create(
            version=d2, size=self.size_l, geometry=rect_um(500, 680),
            trust_grade='photo_calibrated', created_by=self.mgr)
        geo.confirm_version(user=self.mgr, version=d2)
        self._piece('w2r-back', 'Back Panel')   # required, no design
        html = self._get(f'?product={self.product.pk}').content.decode()
        self.assertIn('🟡 Needs Attention', html)
        self.assertIn('Missing: Back Panel', html)

    def test_preparation_buckets_order(self):
        # S has both a missing (Pocket) and a completed (Front) bucket
        html = self._get(f'?product={self.product.pk}&size=s'
                         ).content.decode()
        m = html.find('✖ Missing')
        d = html.find('✓ Completed')
        self.assertGreater(m, -1)
        self.assertGreater(d, m)                 # todo-first order

    def _lib_html_l(self):
        return self._get(f'?product={self.product.pk}&size=l'
                         ).content.decode()

    def test_cut_checklist_per_row(self):
        html = self._get(f'?product={self.product.pk}&size=s'
                         ).content.decode()
        # confirmed Front·S: Geometry ✓ Confirmed ✓ DXF ✓; Reference ✖
        self.assertIn('Geometry</b> ✓', html)
        self.assertIn('Confirmed</b> ✓', html)
        self.assertIn('DXF</b> ✓', html)
        self.assertIn('Reference</b> ✖', html)
        # missing Pocket·S: Geometry ✖
        self.assertIn('Geometry</b> ✖', html)


class VocabularyTests(_W2RBase):
    def test_production_patterns_action_opens_dashboard(self):
        # Phase 1 conscious rework: the Patterns action now redirects to
        # the Pattern Dashboard (owner-frozen entry); the Blueprint page
        # carries the STEP 2 hand-off to the Manager.
        sa = User.objects.create_user(
            'w2rsa@test.local', password='x',
            role=Role.objects.get(code='super_admin'))
        self.client.force_login(sa)
        r = self.client.get(reverse('production:product-patterns',
                                    args=[self.product.pk]))
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r['Location'],
                         reverse('patterns_ai:dashboard')
                         + f'?product={self.product.pk}')
        # Phase 2: production blueprint URL redirects to the patterns_ai
        # module (D-1) — follow to the real page.
        html = self.client.get(
            reverse('production:product-pattern-blueprint',
                    args=[self.product.pk]), follow=True).content.decode()
        self.assertIn('Pattern Blueprint', html)
        self.assertIn(f'/patterns/pieces/?product={self.product.pk}', html)
