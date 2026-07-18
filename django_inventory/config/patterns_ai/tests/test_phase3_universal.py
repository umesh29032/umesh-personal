"""Phase 3 — Universal Size workflow + archive guard.

D-1: Universal materializes at exactly two WRITE moments (auto inside
register_pattern_definition · explicit [Start with Universal] POST) —
GET stays write-free. D-2: production's product_size_service owns the
row. D-3: the confirmed-designs archive guard runs via the validator
registry (ADR-H wall intact)."""
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from accounts.models import Role
from production.models import Product, ProductSize
from production.services import product_size_service as pss
from patterns_ai.models import PieceSizeGeometry
from patterns_ai.services import pattern_geometry_service as geo
from patterns_ai.tests.test_p3_generation import rect_um

User = get_user_model()


class _P3Base(TestCase):
    @classmethod
    def setUpTestData(cls):
        sa = Role.objects.get_or_create(code='super_admin',
                                        defaults={'name': 'SA'})[0]
        wk = Role.objects.get_or_create(code='worker',
                                        defaults={'name': 'W'})[0]
        cls.admin = User.objects.create_user('p3@test.local', password='x',
                                             role=sa)
        cls.worker = User.objects.create_user('p3w@test.local', password='x',
                                              role=wk)
        cls.product = Product.objects.create(code='P3U', name='P3 Universal')

    def _register(self, name='Front Panel'):
        return geo.register_pattern_definition(
            user=self.admin, product=self.product, name=name)

    def _confirm_for(self, piece, size):
        d = geo.get_or_create_draft(user=self.admin, piece=piece)
        PieceSizeGeometry.objects.create(       # fixture only
            version=d, size=size, geometry=rect_um(200, 300),
            trust_grade='photo_calibrated', created_by=self.admin)
        geo.confirm_version(user=self.admin, version=d)


class AutoMaterializeTests(_P3Base):
    def test_first_definition_creates_universal(self):
        self.assertEqual(self.product.sizes.count(), 0)
        self._register('Front Panel')
        u = self.product.sizes.get(code='universal')
        self.assertTrue(u.is_active)
        self.assertEqual(u.label, 'Universal')
        self.assertEqual(u.display_order, 0)
        # idempotent: second definition adds no second size
        self._register('Back Panel')
        self.assertEqual(self.product.sizes.count(), 1)

    def test_no_auto_when_real_sizes_exist(self):
        ProductSize.objects.create(product=self.product, code='m',
                                   label='M', display_order=1)
        self._register()
        self.assertFalse(self.product.sizes.filter(
            code='universal').exists())

    def test_ensure_reactivates_instead_of_duplicating(self):
        u = pss.ensure_universal_size(self.product)
        u.is_active = False
        u.save(update_fields=['is_active'])
        again = pss.ensure_universal_size(self.product)
        self.assertEqual(again.pk, u.pk)
        self.assertTrue(again.is_active)
        self.assertEqual(self.product.sizes.count(), 1)


class StartUniversalButtonTests(_P3Base):
    def test_post_creates_and_get_never_does(self):
        self.client.force_login(self.admin)
        url = reverse('patterns_ai:piece-list')
        # GET (Manager no-sizes state) writes nothing
        html = self.client.get(url + f'?product={self.product.pk}'
                               ).content.decode()
        self.assertIn('Start with Universal', html)
        self.assertEqual(self.product.sizes.count(), 0)
        # POST materializes
        r = self.client.post(url, {'product': self.product.pk,
                                   'action': 'start_universal'})
        self.assertEqual(r.status_code, 302)
        self.assertTrue(self.product.sizes.filter(
            code='universal', is_active=True).exists())

    def test_dashboard_carries_button_and_worker_403(self):
        self.client.force_login(self.admin)
        html = self.client.get(reverse('patterns_ai:dashboard')
                               + f'?product={self.product.pk}'
                               ).content.decode()
        self.assertIn('Start with Universal', html)
        self.assertIn('start_universal', html)
        self.client.force_login(self.worker)
        r = self.client.post(reverse('patterns_ai:piece-list'),
                             {'product': self.product.pk,
                              'action': 'start_universal'})
        self.assertEqual(r.status_code, 403)
        self.assertEqual(self.product.sizes.count(), 0)

    def test_universal_renders_as_normal_size_card(self):
        # owner note #1: Universal = a normal size, same component
        pss.ensure_universal_size(self.product)
        self._register()
        self.client.force_login(self.admin)
        html = self.client.get(reverse('patterns_ai:piece-list')
                               + f'?product={self.product.pk}'
                               ).content.decode()
        self.assertIn('Universal', html)
        self.assertIn('Manage Pattern Designs', html)   # same card verdict
        self.assertNotIn('special', html.lower())


class ArchiveGuardTests(_P3Base):
    def setUp(self):
        self.piece = self._register()
        self.universal = self.product.sizes.get(code='universal')

    def test_sole_confirmed_design_size_refused(self):
        self._confirm_for(self.piece, self.universal)
        with self.assertRaises(ValidationError) as ctx:
            pss.archive_product_size(self.admin, product=self.product,
                                     size_id=self.universal.pk)
        self.assertIn('only confirmed Pattern Designs',
                      str(ctx.exception))
        self.universal.refresh_from_db()
        self.assertTrue(self.universal.is_active)      # unchanged

    def test_archive_allowed_when_another_active_size_has_designs(self):
        m = ProductSize.objects.create(product=self.product, code='m',
                                       label='M', display_order=1)
        self._confirm_for(self.piece, self.universal)
        # copy-forward keeps the Universal row, add M, confirm → the
        # confirmed version now covers BOTH sizes; Universal not sole
        d2 = geo.start_next_version(user=self.admin, piece=self.piece)
        PieceSizeGeometry.objects.create(
            version=d2, size=m, geometry=rect_um(210, 310),
            trust_grade='photo_calibrated', created_by=self.admin)
        geo.confirm_version(user=self.admin, version=d2)
        out = pss.archive_product_size(self.admin, product=self.product,
                                       size_id=self.universal.pk)
        self.assertFalse(out.is_active)

    def test_designless_size_archives_freely(self):
        m = ProductSize.objects.create(product=self.product, code='m',
                                       label='M', display_order=1)
        out = pss.archive_product_size(self.admin, product=self.product,
                                       size_id=m.pk)
        self.assertFalse(out.is_active)

    def test_guard_registered_exactly_once(self):
        from patterns_ai.services.size_guards import (
            refuse_archiving_sole_design_size)
        self.assertEqual(
            pss.ARCHIVE_VALIDATORS.count(refuse_archiving_sole_design_size),
            1)
