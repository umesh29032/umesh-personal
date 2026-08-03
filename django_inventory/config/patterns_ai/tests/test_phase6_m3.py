"""Phase-6 M3 tests — the frozen single-writer service contract
(approved review F-1..F-6 + Rule A eligibility + Rule B defaults-only +
the resolve_generation_geometry rename)."""
import json
import unittest

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase

from accounts.models import Role
from production.models import (Product, ProductPattern,
                               ProductPatternAssignment, ProductSize)
from patterns_ai.models import (CaptureAsset, GeneratedMarkerCandidate,
                                MarkerGenerationRun, PieceSizeGeometry,
                                ProductFabricProfile, ProductionLayout)
from patterns_ai.services import compute_bridge
from patterns_ai.services import fabric_profile_service as fps
from patterns_ai.services import marker_generation_service as gen
from patterns_ai.services import pattern_geometry_service as geo
from patterns_ai.services import production_layout_service as pls
from patterns_ai.tests.test_p3_generation import rect_um

User = get_user_model()
RUNTIME_OK = compute_bridge.runtime_available()

SQUARE = [[0.0, 0.0], [100.0, 0.0], [100.0, 100.0], [0.0, 100.0]]


class _M3Base(TestCase):
    """Pure-DB fixtures (no compute runtime): a product with confirmed
    geometry, saved layouts in every Rule-A eligibility state, users."""

    @classmethod
    def setUpTestData(cls):
        mgr = Role.objects.get_or_create(code='manager', defaults={'name': 'M'})[0]
        wk = Role.objects.get_or_create(code='worker', defaults={'name': 'W'})[0]
        cls.mgr = User.objects.create_user('m3@test.local', password='x', role=mgr)
        cls.mgr2 = User.objects.create_user('m3b@test.local', password='x', role=mgr)
        cls.worker = User.objects.create_user('m3w@test.local', password='x', role=wk)
        cls.product = Product.objects.create(code='M3P', name='M3 Product')
        cls.other_product = Product.objects.create(code='M3O', name='M3 Other')
        cls.size_m = ProductSize.objects.create(product=cls.product, code='m',
                                                label='M', display_order=1)
        cls.size_xl = ProductSize.objects.create(product=cls.product, code='xl',
                                                 label='XL', display_order=2)
        # front: required, designs for M + XL in one confirmed version
        cls.front = cls._piece('m3-front', 'Front')
        draft = geo.get_or_create_draft(user=cls.mgr, piece=cls.front)
        for size in (cls.size_m, cls.size_xl):
            PieceSizeGeometry.objects.create(       # test fixture only
                version=draft, size=size, geometry=rect_um(400, 600),
                trust_grade='photo_calibrated', created_by=cls.mgr)
        geo.confirm_version(user=cls.mgr, version=draft)
        # saved layouts across the Rule-A states
        cls.layout_ok = cls._candidate(cls.product, ok=True)
        cls.layout_ok2 = cls._candidate(cls.product, ok=True)
        cls.layout_unverified = cls._candidate(cls.product, ok=False)
        cls.layout_empty = cls._candidate(cls.product, ok=True, placements=[])
        cls.layout_foreign = cls._candidate(cls.other_product, ok=True)

    @classmethod
    def _piece(cls, code, name, product=None, **kwargs):
        product = product or cls.product
        pattern = ProductPattern.objects.create(code=code, name=name)
        ProductPatternAssignment.objects.create(product=product,
                                                pattern=pattern,
                                                pieces_count=1)
        return geo.create_piece(user=cls.mgr, product=product,
                                pattern=pattern, fabric_group='body',
                                **kwargs)

    @classmethod
    def _candidate(cls, product, ok=True, placements=None):
        run = MarkerGenerationRun.objects.create(   # test fixture only
            product=product, usable_width_mm=900,
            params={'schema_version': 1, 'ratio': {}},
            pipeline_version='t', created_by=cls.mgr)
        if placements is None:
            placements = [{'key': 'Front·m', 'instance': 1, 'mirrored': False,
                           'rotation_deg': 0, 'polygon_mm': SQUARE}]
        return GeneratedMarkerCandidate.objects.create(
            run=run, engine='manual',
            placements={'schema_version': 1, 'placements': placements},
            marker_length_mm=100,
            verification={'ok': ok, 'max_overlap_mm2': 0,
                          'within_width': ok, 'piece_count': len(placements)})

    @staticmethod
    def _asset(product, kind, user, sha, status=CaptureAsset.Status.STORED):
        reason = '' if status == CaptureAsset.Status.STORED else 'test retire'
        return CaptureAsset.objects.create(         # test fixture only
            product=product, kind=kind, source=CaptureAsset.Source.GALLERY,
            original_filename='x.png', content_type='image/png',
            size_bytes=2048, sha256=sha, status=status, status_reason=reason,
            metadata={'schema_version': 1}, uploaded_by=user,
            file=f'patterns_ai/{product.pk}/originals/{sha[:16]}.png')


class FabricProfileServiceTests(_M3Base):
    def test_set_replace_idempotent_one_row(self):
        a = fps.set_fabric_profile(user=self.mgr, product=self.product,
                                   default_width_mm=990,
                                   default_length_mm=2000,
                                   default_spacing_mm='3.0',
                                   fabric_type='Single jersey', gsm=180,
                                   lay_mode='face-up')
        b = fps.set_fabric_profile(user=self.mgr, product=self.product,
                                   default_width_mm=990,
                                   default_length_mm=2000,
                                   default_spacing_mm='3.0',
                                   fabric_type='Single jersey', gsm=180,
                                   lay_mode='face-up')
        self.assertEqual(a.pk, b.pk)
        self.assertEqual(ProductFabricProfile.objects.count(), 1)
        # full-replace: omitted fields clear
        c = fps.set_fabric_profile(user=self.mgr, product=self.product,
                                   default_width_mm=1200)
        self.assertEqual(c.pk, a.pk)
        self.assertEqual(c.default_width_mm, 1200)
        self.assertIsNone(c.default_length_mm)
        self.assertEqual(c.fabric_type, '')

    def test_bounds_reuse_generation_limits(self):
        for bad in ({'default_width_mm': 100},        # < MIN_WIDTH_MM
                    {'default_width_mm': 9999},       # > MAX_WIDTH_MM
                    {'default_length_mm': 0},
                    {'default_spacing_mm': -1},
                    {'gsm': -5}):                     # full_clean positive
            with self.assertRaises(ValidationError, msg=bad):
                fps.set_fabric_profile(user=self.mgr, product=self.product,
                                       **bad)

    def test_gate(self):
        with self.assertRaises(PermissionDenied):
            fps.set_fabric_profile(user=self.worker, product=self.product,
                                   default_width_mm=990)

    def test_rule_b_history_byte_identical(self):
        # defaults only affect NEW work: existing runs/layouts/designation
        # stay byte-identical through a profile change.
        pls.approve_production_layout(user=self.mgr, product=self.product,
                                      layout=self.layout_ok)
        self.layout_ok.refresh_from_db()   # DB representation, not in-memory
        before = json.dumps([self.layout_ok.placements,
                             str(self.layout_ok.marker_length_mm),
                             self.layout_ok.verification,
                             self.layout_ok.run.params], sort_keys=True)
        approved_before = ProductionLayout.objects.get(
            product=self.product).approved_layout_id
        fps.set_fabric_profile(user=self.mgr, product=self.product,
                               default_width_mm=2500,
                               default_spacing_mm='9.5')
        self.layout_ok.refresh_from_db()
        after = json.dumps([self.layout_ok.placements,
                            str(self.layout_ok.marker_length_mm),
                            self.layout_ok.verification,
                            self.layout_ok.run.params], sort_keys=True)
        self.assertEqual(before, after)
        self.assertEqual(ProductionLayout.objects.get(
            product=self.product).approved_layout_id, approved_before)


class ApproveProductionLayoutTests(_M3Base):
    def test_approve_happy_audited(self):
        d = pls.approve_production_layout(user=self.mgr, product=self.product,
                                          layout=self.layout_ok)
        self.assertEqual(d.approved_layout_id, self.layout_ok.pk)
        self.assertEqual(d.approved_by_id, self.mgr.pk)
        self.assertIsNotNone(d.approved_at)
        self.assertEqual(ProductionLayout.objects.count(), 1)

    def test_rule_a_refusals(self):
        cases = [
            (self.layout_unverified, 'not verified'),
            (self.layout_empty, 'no pieces'),
            (self.layout_foreign, 'different product'),
            (GeneratedMarkerCandidate(run=self.layout_ok.run,
                                      engine='manual',
                                      placements={}, marker_length_mm=1,
                                      verification={'ok': True}),
             'saved layout'),                         # unsaved instance
        ]
        for layout, needle in cases:
            with self.assertRaises(ValidationError, msg=needle) as ctx:
                pls.approve_production_layout(user=self.mgr,
                                              product=self.product,
                                              layout=layout)
            self.assertIn(needle, str(ctx.exception))
        self.assertEqual(ProductionLayout.objects.count(), 0)

    def test_same_layout_reapprove_strict_noop(self):
        d1 = pls.approve_production_layout(user=self.mgr, product=self.product,
                                           layout=self.layout_ok)
        first_at, first_by = d1.approved_at, d1.approved_by_id
        # even ANOTHER manager re-approving the same layout restamps nothing
        d2 = pls.approve_production_layout(user=self.mgr2, product=self.product,
                                           layout=self.layout_ok)
        self.assertEqual(d2.pk, d1.pk)
        self.assertEqual(d2.approved_at, first_at)
        self.assertEqual(d2.approved_by_id, first_by)

    def test_move_fresh_audit_layouts_untouched(self):
        pls.approve_production_layout(user=self.mgr, product=self.product,
                                      layout=self.layout_ok)
        old_updated = GeneratedMarkerCandidate.objects.get(
            pk=self.layout_ok.pk).updated_at
        before = json.dumps(self.layout_ok.placements, sort_keys=True)
        d = pls.approve_production_layout(user=self.mgr2, product=self.product,
                                          layout=self.layout_ok2)
        self.assertEqual(d.approved_layout_id, self.layout_ok2.pk)
        self.assertEqual(d.approved_by_id, self.mgr2.pk)
        # the replaced layout row: byte-identical, not even re-saved
        self.layout_ok.refresh_from_db()
        self.assertEqual(json.dumps(self.layout_ok.placements,
                                    sort_keys=True), before)
        self.assertEqual(self.layout_ok.updated_at, old_updated)
        self.assertEqual(ProductionLayout.objects.count(), 1)

    def test_gate(self):
        with self.assertRaises(PermissionDenied):
            pls.approve_production_layout(user=self.worker,
                                          product=self.product,
                                          layout=self.layout_ok)


class PieceSetterTests(_M3Base):
    def test_set_optional_toggle_idempotent(self):
        self.assertFalse(self.front.is_optional)     # default = required
        p = geo.set_piece_optional(user=self.mgr, piece=self.front,
                                   is_optional=True)
        self.assertTrue(p.is_optional)
        p = geo.set_piece_optional(user=self.mgr, piece=p, is_optional=True)
        self.assertTrue(p.is_optional)               # no-op, still one truth
        p = geo.set_piece_optional(user=self.mgr, piece=p, is_optional=False)
        p.refresh_from_db()
        self.assertFalse(p.is_optional)

    def test_reference_image_happy_and_clear(self):
        ref = self._asset(self.product, CaptureAsset.Kind.REFERENCE_IMAGE,
                          self.mgr, 'a' * 64)
        p = geo.set_reference_image(user=self.mgr, piece=self.front,
                                    asset=ref)
        self.assertEqual(p.reference_image_id, ref.pk)
        p = geo.set_reference_image(user=self.mgr, piece=p, asset=None)
        self.assertIsNone(p.reference_image_id)

    def test_reference_image_refusals(self):
        wrong_kind = self._asset(self.product,
                                 CaptureAsset.Kind.PATTERN_CAPTURE,
                                 self.mgr, 'b' * 64)
        foreign = self._asset(self.other_product,
                              CaptureAsset.Kind.REFERENCE_IMAGE,
                              self.mgr, 'c' * 64)
        retired = self._asset(self.product,
                              CaptureAsset.Kind.REFERENCE_IMAGE,
                              self.mgr, 'd' * 64,
                              status=CaptureAsset.Status.RETIRED)
        for asset, needle in ((wrong_kind, 'only reference_image'),
                              (foreign, 'different product'),
                              (retired, 'retired or corrupt')):
            with self.assertRaises(ValidationError) as ctx:
                geo.set_reference_image(user=self.mgr, piece=self.front,
                                        asset=asset)
            self.assertIn(needle, str(ctx.exception))
        self.front.refresh_from_db()
        self.assertIsNone(self.front.reference_image_id)

    def test_gates(self):
        with self.assertRaises(PermissionDenied):
            geo.set_piece_optional(user=self.worker, piece=self.front,
                                   is_optional=True)
        with self.assertRaises(PermissionDenied):
            geo.set_reference_image(user=self.worker, piece=self.front,
                                    asset=None)


class ResolveGenerationGeometryTests(_M3Base):
    """Rule 6 — required blocks by name; optional skips per (piece, size)
    with an honest warning; nothing is ever silent."""

    def test_required_missing_still_blocks_by_name(self):
        self._piece('m3-req', 'Required Thing')      # no confirmed version
        with self.assertRaises(ValidationError) as ctx:
            gen.resolve_generation_geometry(self.product,
                                            {self.size_m: 1})
        self.assertIn('Required Thing (no confirmed version)',
                      str(ctx.exception))

    def test_optional_missing_piece_skipped_with_warning(self):
        pocket = self._piece('m3-pocket', 'Pocket')  # no confirmed version
        geo.set_piece_optional(user=self.mgr, piece=pocket, is_optional=True)
        payload, sources, warnings = gen.resolve_generation_geometry(
            self.product, {self.size_m: 1})
        self.assertEqual(warnings,
                         ['Pocket — skipped (optional, no confirmed design)'])
        self.assertEqual({p['key'] for p in payload}, {'Front·m'})
        self.assertEqual(len(sources), 1)

    def test_optional_missing_size_skipped_per_size(self):
        pocket = self._piece('m3-pocket2', 'Pocket')
        draft = geo.get_or_create_draft(user=self.mgr, piece=pocket)
        PieceSizeGeometry.objects.create(            # M design only
            version=draft, size=self.size_m, geometry=rect_um(100, 120),
            trust_grade='photo_calibrated', created_by=self.mgr)
        geo.confirm_version(user=self.mgr, version=draft)
        geo.set_piece_optional(user=self.mgr, piece=pocket, is_optional=True)
        payload, _sources, warnings = gen.resolve_generation_geometry(
            self.product, {self.size_m: 1, self.size_xl: 1})
        # M pockets cut; XL pocket honestly skipped; Front covers both sizes
        keys = {p['key'] for p in payload}
        self.assertEqual(keys, {'Front·m', 'Front·xl', 'Pocket·m'})
        self.assertEqual(warnings, ['Pocket / XL — skipped (optional, '
                                    'no design for this size)'])

    def test_optional_with_designs_included_no_warning(self):
        pocket = self._piece('m3-pocket3', 'Pocket')
        draft = geo.get_or_create_draft(user=self.mgr, piece=pocket)
        for size in (self.size_m, self.size_xl):
            PieceSizeGeometry.objects.create(
                version=draft, size=size, geometry=rect_um(100, 120),
                trust_grade='photo_calibrated', created_by=self.mgr)
        geo.confirm_version(user=self.mgr, version=draft)
        geo.set_piece_optional(user=self.mgr, piece=pocket, is_optional=True)
        payload, _sources, warnings = gen.resolve_generation_geometry(
            self.product, {self.size_m: 1, self.size_xl: 1})
        self.assertEqual(warnings, [])
        self.assertIn('Pocket·m', {p['key'] for p in payload})

    def test_on_fold_blocks_even_when_optional(self):
        folded = self._piece('m3-fold', 'Folded Yoke', on_fold=True)
        geo.set_piece_optional(user=self.mgr, piece=folded, is_optional=True)
        with self.assertRaises(ValidationError) as ctx:
            gen.resolve_generation_geometry(self.product, {self.size_m: 1})
        self.assertIn('on-fold', str(ctx.exception))

    def test_everything_skipped_is_still_honest(self):
        bare = Product.objects.create(code='M3B', name='Bare')
        size = ProductSize.objects.create(product=bare, code='m', label='M',
                                          display_order=1)
        lonely = self._piece('m3-lonely', 'Lonely Pocket', product=bare)
        geo.set_piece_optional(user=self.mgr, piece=lonely, is_optional=True)
        with self.assertRaises(ValidationError) as ctx:
            gen.resolve_generation_geometry(bare, {size: 1})
        self.assertIn('nothing to nest', str(ctx.exception))


@unittest.skipUnless(RUNTIME_OK, 'compute runtime required (ADR-F)')
class OptionalSkipPersistedTests(_M3Base):
    """The reproducibility spine records skips (rule 6, persisted)."""

    def test_run_params_record_optional_skipped(self):
        pocket = self._piece('m3-pocket4', 'Pocket')
        geo.set_piece_optional(user=self.mgr, piece=pocket, is_optional=True)
        run, _rows = gen.start_run(user=self.mgr, product=self.product,
                                   usable_width_mm=900,
                                   ratio={self.size_m: 1}, timebox_s=10,
                                   engine='blf')
        self.assertEqual(run.params['optional_skipped'],
                         ['Pocket — skipped (optional, no confirmed design)'])

    def test_no_skip_no_key(self):
        run, _rows = gen.start_run(user=self.mgr, product=self.product,
                                   usable_width_mm=900,
                                   ratio={self.size_m: 1}, timebox_s=10,
                                   engine='blf')
        self.assertNotIn('optional_skipped', run.params)
