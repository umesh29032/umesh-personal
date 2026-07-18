"""M5 — Layout Library polish (readiness: M5_READINESS.md): rows carry
the frozen plan facts (recipe · notes · lay · roll · lineage · thumb) ·
live search hooks · recipe management (deactivate) · legacy rows
default-safe. Product engineering — zero models, zero migrations."""
import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Role
from production.models import (Product, ProductPattern,
                               ProductPatternAssignment, ProductSize)
from patterns_ai.models import (ApprovedLayout, GeneratedMarkerCandidate,
                                ManufacturingStrategy, MarkerGenerationRun,
                                PieceSizeGeometry)
from patterns_ai.services import pattern_geometry_service as geo
from patterns_ai.services import strategy_service
from patterns_ai.tests.test_p3_generation import rect_um

User = get_user_model()
SQUARE = [[0.0, 0.0], [100.0, 0.0], [100.0, 100.0], [0.0, 100.0]]


class _M5Base(TestCase):
    @classmethod
    def setUpTestData(cls):
        mgr = Role.objects.get_or_create(code='manager',
                                         defaults={'name': 'M'})[0]
        cls.mgr = User.objects.create_user('m5@test.local', password='x',
                                           role=mgr)
        cls.product = Product.objects.create(code='M5P', name='M5 Lib')
        cls.size_s = ProductSize.objects.create(product=cls.product,
                                                code='s', label='S',
                                                display_order=1)
        pattern = ProductPattern.objects.create(code='m5-f', name='Front')
        ProductPatternAssignment.objects.create(product=cls.product,
                                                pattern=pattern,
                                                pieces_count=1)
        cls.piece = geo.create_piece(user=cls.mgr, product=cls.product,
                                     pattern=pattern, fabric_group='body')
        d = geo.get_or_create_draft(user=cls.mgr, piece=cls.piece)
        PieceSizeGeometry.objects.create(       # fixture only
            version=d, size=cls.size_s, geometry=rect_um(300, 200),
            trust_grade='photo_calibrated', created_by=cls.mgr)
        geo.confirm_version(user=cls.mgr, version=d)

    @classmethod
    def _layout(cls, name, params_extra=None, supersedes=None):
        run = MarkerGenerationRun.objects.create(
            product=cls.product, usable_width_mm=1040,
            params={'schema_version': 1, 'table': True,
                    **(params_extra or {})},
            pipeline_version='table-v1', created_by=cls.mgr)
        cand = GeneratedMarkerCandidate.objects.create(
            run=run, engine='table',
            placements={'schema_version': 1, 'placements': [
                {'key': f'{cls.piece.pk}:{cls.size_s.pk}', 'instance': 1,
                 'polygon_mm': SQUARE, 'rotation_deg': 0,
                 'mirrored': False}]},
            marker_length_mm=500,
            verification={'ok': True, 'max_overlap_mm2': 0,
                          'within_width': True, 'piece_count': 1})
        return ApprovedLayout.objects.create(
            product=cls.product, candidate=cand, name=name,
            layout_uid=f'LAY-M5P-{cand.pk:06d}', version_no=cand.pk,
            fabric_group='body', approved_by=cls.mgr,
            approved_at=timezone.now(), supersedes=supersedes)

    def _html(self):
        self.client.force_login(self.mgr)
        return self.client.get(reverse('patterns_ai:cutting-table',
                                       args=[self.product.pk])
                               ).content.decode()


class LibraryRowFactsTests(_M5Base):
    def test_rows_carry_plan_facts_and_lineage(self):
        old = self._layout('old marker')
        self._layout('rich marker', params_extra={
            'recipe': 'Body+Pocket · double',
            'notes': 'works only on 42in',
            'layering_type': 'double_folded',
            'roll': {'id': 1, 'label': 'CR-X · 42″'}},
            supersedes=old)
        html = self._html()
        self.assertIn('📋 Body+Pocket · double', html)
        self.assertIn('📝 works only on 42in', html)
        self.assertIn('double_folded lay', html)
        self.assertIn('planned on CR-X · 42″', html)
        self.assertIn(f'supersedes {old.layout_uid}', html)
        self.assertIn('lib-thumb', html)          # preview per row
        self.assertIn('candidates/', html)        # svg thumb url

    def test_legacy_rows_render_clean_without_plan_keys(self):
        # pre-M4 assets have NO recipe/notes/lay keys — honest defaults
        self._layout('legacy marker')
        html = self._html()
        self.assertIn('legacy marker', html)
        self.assertNotIn('📋', html.split('Marker Recipes')[0]
                         if 'Marker Recipes' in html else html)
        self.assertNotIn('📝', html)
        self.assertNotIn('None lay', html)

    def test_search_hooks_present(self):
        self._layout('searchable')
        html = self._html()
        self.assertIn('id="lib-search"', html)
        self.assertIn('data-search=', html)
        self.assertIn('lib-noresults', html)


class RecipeManagementTests(_M5Base):
    def _recipe(self):
        return strategy_service.save_recipe(
            user=self.mgr, product=self.product, name='R1',
            fabric_group='body', layering_type='double_folded',
            piece_ids=[self.piece.pk],
            size_ratio={self.size_s.pk: 1})

    def test_recipe_block_renders_with_deactivate(self):
        self._recipe()
        self._layout('any')                      # library section renders
        html = self._html()
        self.assertIn('Marker Recipes', html)
        self.assertIn('recipe-deactivate', html)
        self.assertIn('📋 R1', html)

    def test_deactivate_endpoint_one_shot(self):
        r = self._recipe()
        self.client.force_login(self.mgr)
        url = reverse('patterns_ai:table-recipe', args=[self.product.pk])
        resp = self.client.post(url, json.dumps(
            {'action': 'deactivate', 'recipe_id': r.pk}),
            content_type='application/json')
        self.assertTrue(resp.json()['ok'])
        self.assertEqual(resp.json()['recipes'], [])
        r.refresh_from_db()
        self.assertFalse(r.is_active)             # knowledge kept, off list
        self.assertTrue(ManufacturingStrategy.objects.filter(
            pk=r.pk).exists())                    # never deleted

    def test_deactivate_foreign_recipe_404(self):
        other = Product.objects.create(code='M5X', name='Other')
        r = ManufacturingStrategy.objects.create(
            product=other, name='foreign', fabric_group='body',
            created_by=self.mgr)
        self.client.force_login(self.mgr)
        url = reverse('patterns_ai:table-recipe', args=[self.product.pk])
        resp = self.client.post(url, json.dumps(
            {'action': 'deactivate', 'recipe_id': r.pk}),
            content_type='application/json')
        self.assertEqual(resp.status_code, 404)   # tamper wall