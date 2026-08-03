"""Phase 2 — the PATTERN BLUEPRINT module (frozen responsibility #1):
structure + rules, single surface, atomic registration, refuse-if-history
removal; V-1/V-2 migrated off the Library; facade contract-additive."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounts.models import Role
from production.models import (Product, ProductPattern,
                               ProductPatternAssignment, ProductSize)
from patterns_ai.models import PatternPiece, PieceSizeGeometry
from patterns_ai.services import pattern_design_facade as facade
from patterns_ai.services import pattern_geometry_service as geo
from patterns_ai.tests.test_p3_generation import rect_um

User = get_user_model()


class _P2Base(TestCase):
    @classmethod
    def setUpTestData(cls):
        sa = Role.objects.get_or_create(code='super_admin',
                                        defaults={'name': 'SA'})[0]
        wk = Role.objects.get_or_create(code='worker',
                                        defaults={'name': 'W'})[0]
        cls.admin = User.objects.create_user('p2@test.local', password='x',
                                             role=sa)
        cls.worker = User.objects.create_user('p2w@test.local', password='x',
                                              role=wk)
        cls.product = Product.objects.create(code='P2B', name='P2 Blueprint')
        cls.size_s = ProductSize.objects.create(product=cls.product,
                                                code='s', label='S',
                                                display_order=1)

    def _post(self, data):
        self.client.force_login(self.admin)
        return self.client.post(reverse('patterns_ai:blueprint'),
                                {'product': self.product.pk, **data})

    def _html(self):
        self.client.force_login(self.admin)
        return self.client.get(reverse('patterns_ai:blueprint')
                               + f'?product={self.product.pk}'
                               ).content.decode()


class AtomicRegisterTests(_P2Base):
    def test_add_creates_all_three_rows_with_rules(self):
        r = self._post({'action': 'add', 'name': 'Front Panel',
                        'pieces_count': '2', 'fabric_group': 'body',
                        'grain_rule': 'strict', 'is_pair': '1',
                        'is_optional': '1'})
        self.assertEqual(r.status_code, 302)
        pattern = ProductPattern.objects.get(name='Front Panel')
        a = ProductPatternAssignment.objects.get(product=self.product,
                                                 pattern=pattern)
        self.assertEqual(a.pieces_count, 2)
        piece = PatternPiece.objects.get(product=self.product,
                                         pattern=pattern)
        self.assertTrue(piece.is_pair)
        self.assertTrue(piece.is_optional)
        self.assertEqual(piece.grain_rule, 'strict')
        self.assertEqual(piece.fabric_group, 'body')

    def test_duplicate_name_honest_error_and_no_partial_rows(self):
        self._post({'action': 'add', 'name': 'Pocket'})
        before = (ProductPattern.objects.count(),
                  ProductPatternAssignment.objects.count(),
                  PatternPiece.objects.count())
        r = self.client.post(reverse('patterns_ai:blueprint'),
                             {'product': self.product.pk, 'action': 'add',
                              'name': 'Pocket'}, follow=True)
        self.assertContains(r, 'already in this product')
        self.assertEqual(before, (ProductPattern.objects.count(),
                                  ProductPatternAssignment.objects.count(),
                                  PatternPiece.objects.count()))

    def test_blank_name_refused(self):
        self.client.force_login(self.admin)
        r = self.client.post(reverse('patterns_ai:blueprint'),
                             {'product': self.product.pk, 'action': 'add',
                              'name': '  '}, follow=True)
        self.assertContains(r, 'name is required')
        self.assertEqual(PatternPiece.objects.count(), 0)

    def test_register_unregistered_assignment(self):
        # continuity: an old-editor assignment with no PDM piece row
        pattern = ProductPattern.objects.create(code='p2-back', name='Back')
        ProductPatternAssignment.objects.create(product=self.product,
                                                pattern=pattern,
                                                pieces_count=1)
        html = self._html()
        self.assertIn('not registered', html)
        self._post({'action': 'register', 'pattern': pattern.pk})
        self.assertTrue(PatternPiece.objects.filter(
            product=self.product, pattern=pattern).exists())
        self.assertNotIn('not registered', self._html())


class RuleEditingTests(_P2Base):
    def _piece(self, name='Sleeve'):
        self._post({'action': 'add', 'name': name})
        return PatternPiece.objects.get(product=self.product,
                                        pattern__name=name)

    def test_set_rules_and_count_and_optional(self):
        piece = self._piece()
        self._post({'action': 'set_rules', 'piece': piece.pk,
                    'is_pair': '1', 'on_fold': '1',
                    'grain_rule': 'free', 'fabric_group': 'rib'})
        piece.refresh_from_db()
        self.assertTrue(piece.is_pair)
        self.assertTrue(piece.on_fold)
        self.assertEqual(piece.grain_rule, 'free')
        self.assertEqual(piece.fabric_group, 'rib')
        self._post({'action': 'set_count', 'piece': piece.pk,
                    'pieces_count': '4'})
        piece.refresh_from_db()
        self.assertEqual(piece.assignment.pieces_count, 4)
        self._post({'action': 'set_optional', 'piece': piece.pk,
                    'is_optional': '1'})
        piece.refresh_from_db()
        self.assertTrue(piece.is_optional)

    def test_bad_grain_rule_refused(self):
        piece = self._piece('Cuff')
        r = self.client.post(reverse('patterns_ai:blueprint'),
                             {'product': self.product.pk,
                              'action': 'set_rules', 'piece': piece.pk,
                              'grain_rule': 'diagonal',
                              'fabric_group': 'body'}, follow=True)
        self.assertContains(r, 'unknown grain rule')
        piece.refresh_from_db()
        self.assertEqual(piece.grain_rule, 'two_way')   # default intact

    def test_remove_refused_with_design_history(self):
        piece = self._piece('Collar')
        d = geo.get_or_create_draft(user=self.admin, piece=piece)
        PieceSizeGeometry.objects.create(     # fixture only
            version=d, size=self.size_s, geometry=rect_um(100, 100),
            trust_grade='photo_calibrated', created_by=self.admin)
        r = self.client.post(reverse('patterns_ai:blueprint'),
                             {'product': self.product.pk,
                              'action': 'remove', 'piece': piece.pk},
                             follow=True)
        self.assertContains(r, 'design history')
        self.assertTrue(PatternPiece.objects.filter(pk=piece.pk).exists())

    def test_remove_clean_piece_removes_assignment_too(self):
        piece = self._piece('Label')
        assignment_pk = piece.assignment_id
        self._post({'action': 'remove', 'piece': piece.pk})
        self.assertFalse(PatternPiece.objects.filter(pk=piece.pk).exists())
        self.assertFalse(ProductPatternAssignment.objects.filter(
            pk=assignment_pk).exists())


class SurfaceAndContractTests(_P2Base):
    def test_worker_403_and_get_writes_nothing(self):
        self.client.force_login(self.worker)
        self.assertEqual(self.client.get(
            reverse('patterns_ai:blueprint')
            + f'?product={self.product.pk}').status_code, 403)
        self.client.force_login(self.admin)
        before = PatternPiece.objects.count()
        self._html()
        self.assertEqual(PatternPiece.objects.count(), before)

    def test_production_url_redirects_here(self):
        self.client.force_login(self.admin)
        r = self.client.get(reverse('production:product-pattern-blueprint',
                                    args=[self.product.pk]))
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r['Location'],
                         reverse('patterns_ai:blueprint')
                         + f'?product={self.product.pk}')

    def test_facade_rows_carry_grain_and_fabric_group(self):
        self._post({'action': 'add', 'name': 'Front',
                    'grain_rule': 'strict', 'fabric_group': 'rib'})
        library = facade.product_design_library(self.product)
        row = library['sections'][0]['rows'][0]
        self.assertEqual(row['grain_rule'], 'strict')
        self.assertEqual(row['fabric_group'], 'rib')
        self.assertIn('design_key', row)               # contract intact

    def test_library_lost_registration_and_toggle(self):
        self._post({'action': 'add', 'name': 'Front'})
        self.client.force_login(self.admin)
        html = self.client.get(reverse('patterns_ai:piece-list')
                               + f'?product={self.product.pk}&size=s'
                               ).content.decode()
        self.assertNotIn('+ Add Pattern Design', html)
        self.assertNotIn('make optional', html)
        self.assertIn(reverse('patterns_ai:blueprint')
                      + f'?product={self.product.pk}', html)
        self.assertIn('add ref', html)                 # reference stays
