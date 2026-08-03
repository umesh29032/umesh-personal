"""M6 — manufacturing completion (plan + MANUFACTURING_INTEGRATION_
REVIEW §4): the layering ADVISORY edge · the cutting-completion stamp
listener · the enforcement gates (flags default OFF = byte-identical).
"""
from datetime import date
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import Role, Skill
from production.models import (Adda, AddaStageRecord, Product,
                               ProductPattern, ProductPatternAssignment,
                               ProductSize, Stage, WorkflowStage)
from production.stages.cutting import service as cutting_svc
from production.stages.layering import handler as layering_handler
from patterns_ai.models import ApprovedLayoutUsage, PieceSizeGeometry
from patterns_ai.services import layout_library_service as lib
from patterns_ai.services import layout_usage_service as usage_svc
from patterns_ai.services import marker_generation_service as gen
from patterns_ai.services import pattern_geometry_service as geo
from patterns_ai.tests.test_p3_generation import rect_um

User = get_user_model()


def _ring(x, y, w, h):
    return [[x, y], [x + w, y], [x + w, y + h], [x, y + h]]


class _M6Base(TestCase):
    @classmethod
    def setUpTestData(cls):
        Role.objects.get_or_create(code='super_admin',
                                   defaults={'name': 'SA'})
        mgr = Role.objects.get_or_create(code='manager',
                                         defaults={'name': 'M'})[0]
        cls.mgr = User.objects.create_user('m6@test.local', password='x',
                                           role=mgr)
        # completer: super-admin role (passes the helper-skill gate)
        cls.admin = User.objects.create_user(
            'm6sa@test.local', password='x',
            role=Role.objects.get(code='super_admin'))
        cls.product = Product.objects.create(code='M6P', name='M6 Bridge')
        cls.size_s = ProductSize.objects.create(product=cls.product,
                                                code='s', label='S',
                                                display_order=1)
        cls.pattern = ProductPattern.objects.create(code='m6-f',
                                                    name='Front')
        ProductPatternAssignment.objects.create(product=cls.product,
                                                pattern=cls.pattern,
                                                pieces_count=1)
        cls.piece = geo.create_piece(user=cls.mgr, product=cls.product,
                                     pattern=cls.pattern,
                                     fabric_group='body')
        d = geo.get_or_create_draft(user=cls.mgr, piece=cls.piece)
        PieceSizeGeometry.objects.create(       # fixture only
            version=d, size=cls.size_s, geometry=rect_um(300, 200),
            trust_grade='photo_calibrated', created_by=cls.mgr)
        geo.confirm_version(user=cls.mgr, version=d)
        lay_st, _ = Stage.objects.get_or_create(
            code='layering', defaults={'name': 'Layering'})
        cut_st, _ = Stage.objects.get_or_create(
            code='cutting', defaults={'name': 'Cutting'})
        cls.ws_lay = WorkflowStage.objects.create(product=cls.product,
                                                  stage=lay_st, order=1)
        cls.ws_cut = WorkflowStage.objects.create(product=cls.product,
                                                  stage=cut_st, order=2)
        cls.adda = Adda.objects.create(code='M6-001',
                                       product=cls.product,
                                       current_stage=cls.ws_cut,
                                       created_by=cls.mgr)

    def _layering(self, lay_count=10):
        from production.models import LayeringRecord
        from raw_materials.models import (ClothColor, ClothRoll, ClothType,
                                          StorageLocation)
        sr = AddaStageRecord.objects.create(adda=self.adda,
                                            workflow_stage=self.ws_lay)
        rec = LayeringRecord.objects.create(stage_record=sr,
                                            lay_count=lay_count,
                                            total_colors=1,
                                            duration_minutes=5,
                                            layer_length_meters=2)
        ct, _ = ClothType.objects.get_or_create(name='M6 Cotton')
        cc, _ = ClothColor.objects.get_or_create(name='M6 Black')
        loc, _ = StorageLocation.objects.get_or_create(name='M6 Rack')
        roll = ClothRoll.objects.create(
            roll_id=f'M6-R{lay_count}', cloth_type=ct, cloth_color=cc,
            storage_location=loc, purchased_date=date.today())
        rec.rolls_used.add(roll)
        self.color = cc
        return rec

    def _usage(self, marker_s_count=3):
        placements = [
            {'key': f'{self.piece.pk}:{self.size_s.pk}', 'instance': i + 1,
             'polygon_mm': _ring(10 + i * 320, 10, 300, 400)}
            for i in range(marker_s_count)]
        _, cand = gen.save_table_layout(
            user=self.mgr, product=self.product, width_mm=1600,
            height_mm=2000, spacing_mm=2.0, fabric_group='body',
            placements=placements)
        lay = lib.approve_table_layout(user=self.mgr,
                                       product=self.product,
                                       candidate=cand)
        return usage_svc.record_usage(user=self.mgr, adda=self.adda,
                                      layout=lay)

    def _cutting_ready(self, cut_count):
        """Start cutting + one BREAKUP row so completion reaches the gates
        (GAP-5: breakups are the actuals; bundles are post-join containers)."""
        cutting_svc.start_cutting(adda=self.adda, worker_ids=[],
                                  user=self.mgr)
        cutting_svc.upsert_breakup_row(
            adda=self.adda, size_id=self.size_s.pk,
            pattern_id=self.pattern.pk, color_id=self.color.pk,
            count=cut_count, user=self.mgr)

    def _complete(self):
        # isolate the post-completion ERP fan-out (advance/barcodes have
        # their own suites); THE SEAM under test (gates → completion →
        # listeners) runs REAL.
        with patch('production.stages.cutting.service.'
                   'advance_to_next_stage'), \
             patch('production.stages.barcode_generation.assembly.'
                   'generate_for_cutting'):
            return cutting_svc.complete_cutting_from_bundles(
                adda=self.adda, user=self.admin)


class LayeringEdgeTests(_M6Base):
    def test_recommendation_dict_is_plies_free(self):
        self._usage(marker_s_count=3)
        rec = layering_handler.LAYOUT_PROVIDER(self.adda)
        self.assertEqual(len(rec['groups']), 1)
        g = rec['groups'][0]
        self.assertEqual(g['group'], 'body')
        self.assertTrue(g['uid'].startswith('LAY-M6P-'))
        self.assertGreater(g['length_mm'], 0)
        self.assertEqual(g['layering_type'], 'single')
        self.assertNotIn('lay_count', str(rec))     # NEVER plies

    def test_no_usage_means_none(self):
        self.assertIsNone(layering_handler.LAYOUT_PROVIDER(self.adda))

    def test_layering_page_shows_advisory_and_survives_provider_failure(self):
        # the advisory matters BEFORE completion — stage started, roll
        # attached (panel 4 renders with entries), lay not yet laid
        from decimal import Decimal
        from production.stages.layering.service import (
            attach_roll_to_layering)
        from raw_materials.models import (ClothColor, ClothRoll,
                                          ClothType, StorageLocation)
        self._usage()
        self.adda.current_stage = self.ws_lay      # roll-attach guard
        self.adda.save(update_fields=['current_stage'])
        sr = AddaStageRecord.objects.create(adda=self.adda,
                                            workflow_stage=self.ws_lay)
        ct, _ = ClothType.objects.get_or_create(name='M6 Cotton')
        cc, _ = ClothColor.objects.get_or_create(name='M6 Black')
        loc, _ = StorageLocation.objects.get_or_create(name='M6 Rack')
        roll = ClothRoll.objects.create(
            roll_id='M6-RA', cloth_type=ct, cloth_color=cc,
            storage_location=loc, purchased_date=date.today(),
            width_inch=42)
        attach_roll_to_layering(stage_record=sr, roll=roll,
                                width_verified_inch=42,
                                weight_verified_kg=Decimal('10'),
                                user=self.admin)
        self.client.force_login(self.admin)
        url = reverse('production:layering-workspace',
                      args=[self.adda.code])
        html = self.client.get(url).content.decode()
        self.assertIn('Recommended layer length', html)
        self.assertIn('your measured length stands', html)
        # provider failure → page still 200, section absent (wrapped)
        original = layering_handler.LAYOUT_PROVIDER
        try:
            layering_handler.LAYOUT_PROVIDER = lambda adda: 1 / 0
            r = self.client.get(url)
            self.assertEqual(r.status_code, 200)
            self.assertNotIn('Recommended layer length',
                             r.content.decode())
        finally:
            layering_handler.LAYOUT_PROVIDER = original


class StampListenerTests(_M6Base):
    def test_completion_stamps_active_usages_once(self):
        usage = self._usage(marker_s_count=3)
        self._layering(lay_count=10)
        self._cutting_ready(cut_count=30)      # matches 3 × 10
        self._complete()
        usage.refresh_from_db()
        self.assertIsNotNone(usage.stage_record_id)
        self.assertEqual(usage.stage_record.workflow_stage_id,
                         self.ws_cut.pk)

    def test_stamper_failure_never_breaks_cutting(self):
        self._usage()
        self._layering()
        self._cutting_ready(cut_count=30)
        def boom(adda, sr):
            raise RuntimeError('listener down')
        cutting_svc.CUTTING_COMPLETE_LISTENERS.insert(0, boom)
        try:
            cr = self._complete()               # must still succeed
            self.assertGreater(cr.pieces_cut, 0)
        finally:
            cutting_svc.CUTTING_COMPLETE_LISTENERS.remove(boom)

    def test_flags_default_off(self):
        from django.conf import settings
        self.assertFalse(settings.REQUIRE_APPROVED_LAYOUT)
        self.assertFalse(settings.ENFORCE_LAYOUT_RECONCILIATION)
        self.assertEqual(settings.LAYOUT_RECONCILIATION_TOLERANCE, 0)


class RequireGateTests(_M6Base):
    def test_off_completes_without_usage(self):
        self._layering()
        self._cutting_ready(cut_count=5)
        cr = self._complete()                   # no usage, flag OFF
        self.assertEqual(cr.pieces_cut, 5)

    @override_settings(REQUIRE_APPROVED_LAYOUT=True)
    def test_on_refuses_without_usage_naming_the_fix(self):
        self._layering()
        self._cutting_ready(cut_count=5)
        with self.assertRaises(ValidationError) as ctx:
            self._complete()
        self.assertIn('Manufacturing Layouts', str(ctx.exception))
        # nothing completed
        sr = AddaStageRecord.objects.get(adda=self.adda,
                                         workflow_stage=self.ws_cut)
        self.assertIsNone(sr.completed_at)

    @override_settings(REQUIRE_APPROVED_LAYOUT=True)
    def test_on_passes_with_usage(self):
        self._usage(marker_s_count=3)
        self._layering(lay_count=10)
        self._cutting_ready(cut_count=30)
        self.assertEqual(self._complete().pieces_cut, 30)


class EnforceGateTests(_M6Base):
    def test_off_mismatch_completes_warn_only(self):
        self._usage(marker_s_count=3)
        self._layering(lay_count=10)            # expected 30
        self._cutting_ready(cut_count=25)       # operator's number wins
        self.assertEqual(self._complete().pieces_cut, 25)

    @override_settings(ENFORCE_LAYOUT_RECONCILIATION=True)
    def test_on_mismatch_refuses_with_both_numbers(self):
        self._usage(marker_s_count=3)
        self._layering(lay_count=10)
        self._cutting_ready(cut_count=25)
        with self.assertRaises(ValidationError) as ctx:
            self._complete()
        msg = str(ctx.exception)
        self.assertIn('expected 30', msg)
        self.assertIn('cut 25', msg)

    @override_settings(ENFORCE_LAYOUT_RECONCILIATION=True,
                       LAYOUT_RECONCILIATION_TOLERANCE=5)
    def test_tolerance_absorbs_small_diff(self):
        self._usage(marker_s_count=3)
        self._layering(lay_count=10)
        self._cutting_ready(cut_count=25)       # |25−30| = 5 ≤ tol
        self.assertEqual(self._complete().pieces_cut, 25)

    @override_settings(ENFORCE_LAYOUT_RECONCILIATION=True)
    def test_on_exact_match_passes(self):
        self._usage(marker_s_count=3)
        self._layering(lay_count=10)
        self._cutting_ready(cut_count=30)
        self.assertEqual(self._complete().pieces_cut, 30)