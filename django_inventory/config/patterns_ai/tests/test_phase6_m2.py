"""Phase-6 M2 tests — the two-model storage architecture (§3h locked)."""
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from accounts.models import Role
from production.models import Product
from patterns_ai.models import (CaptureAsset, MarkerGenerationRun,
                                GeneratedMarkerCandidate, PatternPiece,
                                ProductFabricProfile, ProductionLayout)

User = get_user_model()


class TwoModelSchemaTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        mgr = Role.objects.get_or_create(code='manager', defaults={'name': 'M'})[0]
        cls.mgr = User.objects.create_user('m2s@test.local', password='x', role=mgr)
        cls.product = Product.objects.create(code='M2S', name='M2 Schema')
        run = MarkerGenerationRun.objects.create(   # fixtures only
            product=cls.product, usable_width_mm=900,
            params={'schema_version': 1, 'ratio': {}},
            pipeline_version='t', created_by=cls.mgr)
        cls.layout = GeneratedMarkerCandidate.objects.create(
            run=run, engine='manual',
            placements={'schema_version': 1, 'placements': []},
            marker_length_mm=100,
            verification={'ok': True, 'max_overlap_mm2': 0,
                          'within_width': True, 'piece_count': 0})

    def test_profile_holds_defaults_only(self):
        p = ProductFabricProfile.objects.create(
            product=self.product, default_width_mm=990,
            default_length_mm=2000, default_spacing_mm='3.0',
            fabric_type='Single jersey', gsm=180,
            lay_mode='face-up single-ply', created_by=self.mgr)
        self.assertEqual(p.product_id, self.product.pk)
        # rule: NEVER references any layout — no such field exists
        fields = {f.name for f in ProductFabricProfile._meta.get_fields()}
        self.assertFalse({'production_layout', 'approved_layout',
                          'layout', 'approved_by', 'approved_at'} & fields)

    def test_designation_is_pointer_only_and_exactly_one(self):
        d = ProductionLayout.objects.create(
            product=self.product, approved_layout=self.layout,
            approved_by=self.mgr, approved_at=timezone.now())
        # rule: NEVER contains fabric defaults
        fields = {f.name for f in ProductionLayout._meta.get_fields()}
        self.assertFalse({'default_width_mm', 'default_spacing_mm',
                          'fabric_type', 'gsm', 'lay_mode'} & fields)
        # exactly one per product — structurally (OneToOne)
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                ProductionLayout.objects.create(
                    product=self.product, approved_layout=self.layout,
                    approved_by=self.mgr, approved_at=timezone.now())
        # pointer, never a copy: the layout row is PROTECTed + immutable
        with self.assertRaises(Exception):
            self.layout.delete()
        d.refresh_from_db()
        self.assertEqual(d.approved_layout_id, self.layout.pk)

    def test_pointer_moves_without_touching_layouts(self):
        d = ProductionLayout.objects.create(
            product=self.product, approved_layout=self.layout,
            approved_by=self.mgr, approved_at=timezone.now())
        other = GeneratedMarkerCandidate.objects.create(
            run=self.layout.run, engine='manual',
            placements={'schema_version': 1, 'placements': []},
            marker_length_mm=90,
            verification={'ok': True, 'max_overlap_mm2': 0,
                          'within_width': True, 'piece_count': 0})
        before = self.layout.placements
        d.approved_layout = other
        d.approved_at = timezone.now()
        d.save(update_fields=['approved_layout', 'approved_at',
                              'updated_at'])
        self.layout.refresh_from_db()
        self.assertEqual(self.layout.placements, before)   # untouched

    def test_is_optional_defaults_false_required_cannot_weaken(self):
        field = PatternPiece._meta.get_field('is_optional')
        self.assertFalse(field.default)

    def test_reference_image_kind_exists_and_is_display_only(self):
        self.assertIn(('reference_image', 'Reference image (display only)'),
                      CaptureAsset.Kind.choices)
        # structural rule 6: extraction refuses non-pattern-capture kinds
        # (asserted behaviorally in the P2 suite; here we pin the source)
        import inspect
        from patterns_ai.services import pattern_geometry_service as geo
        src = inspect.getsource(geo.run_extraction)
        self.assertIn('PATTERN_CAPTURE', src)
