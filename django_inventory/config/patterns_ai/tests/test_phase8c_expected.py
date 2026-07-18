"""Phase 8C — expected pieces + advisory reconciliation.

The count hierarchy in code: marker CONTENT from the approved layout
(provider — never plies) × lay_count (production's truth) = advisory
expected. Fallback formula intact; warnings never block."""
from django.contrib.auth import get_user_model
from django.test import TestCase

from accounts.models import Role
from production.models import (Adda, AddaStageRecord, Product,
                               ProductPattern, ProductPatternAssignment,
                               ProductSize, Stage, WorkflowStage)
from production.stages.cutting import service as cutting_svc
from production.stages.cutting_pattern import handler as cp_handler
from patterns_ai.models import PieceSizeGeometry
from patterns_ai.services import layout_library_service as lib
from patterns_ai.services import layout_usage_service as usage_svc
from patterns_ai.services import marker_generation_service as gen
from patterns_ai.services import pattern_geometry_service as geo
from patterns_ai.tests.test_p3_generation import rect_um

User = get_user_model()


def _ring(x, y, w, h):
    return [[x, y], [x + w, y], [x + w, y + h], [x, y + h]]


class _P8CBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        mgr = Role.objects.get_or_create(code='manager',
                                         defaults={'name': 'M'})[0]
        cls.mgr = User.objects.create_user('p8c@test.local', password='x',
                                           role=mgr)
        cls.product = Product.objects.create(code='P8C', name='P8C Exp')
        cls.size_s = ProductSize.objects.create(product=cls.product,
                                                code='s', label='S',
                                                display_order=1)
        cls.pattern = ProductPattern.objects.create(code='p8c-f',
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
        # workflow: layering → cutting (suggestion needs both records)
        lay_st, _ = Stage.objects.get_or_create(
            code='layering', defaults={'name': 'Layering'})
        cut_st, _ = Stage.objects.get_or_create(
            code='cutting', defaults={'name': 'Cutting'})
        cls.ws_lay = WorkflowStage.objects.create(product=cls.product,
                                                  stage=lay_st, order=1)
        cls.ws_cut = WorkflowStage.objects.create(product=cls.product,
                                                  stage=cut_st, order=2)
        cls.adda = Adda.objects.create(code='P8C-001',
                                       product=cls.product,
                                       current_stage=cls.ws_cut,
                                       created_by=cls.mgr)

    def _layering(self, lay_count):
        from datetime import date
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
        ct, _ = ClothType.objects.get_or_create(name='P8C Cotton')
        cc, _ = ClothColor.objects.get_or_create(name='P8C Black')
        loc, _ = StorageLocation.objects.get_or_create(name='P8C Rack')
        roll = ClothRoll.objects.create(
            roll_id='P8C-R1' + str(lay_count), cloth_type=ct,
            cloth_color=cc, storage_location=loc,
            purchased_date=date.today())
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


class ContentAndSourceTests(_P8CBase):
    def test_provider_content_only_no_plies(self):
        self._usage(marker_s_count=3)
        panel = cp_handler.LAYOUT_PROVIDER(self.adda)
        self.assertEqual(panel['content_by_pattern_size'],
                         [{'pattern_id': self.pattern.pk,
                           'size_id': self.size_s.pk, 'count': 3}])
        # hierarchy #2: NOTHING plies-like in the provider payload
        import json
        blob = json.dumps(panel)
        self.assertNotIn('plies', blob)
        self.assertNotIn('lay_count', blob)
        self.assertNotIn('expected', blob)

    def test_source_label(self):
        self.assertEqual(cutting_svc.get_suggestion_source(self.adda),
                         {'kind': 'formula'})
        u = self._usage()
        src = cutting_svc.get_suggestion_source(self.adda)
        self.assertEqual(src['kind'], 'layout')
        self.assertEqual(src['uids'], [u.layout.layout_uid])


class SuggestionTests(_P8CBase):
    def test_marker_branch_hand_math_and_fallback(self):
        self._layering(lay_count=12)
        # NO usage → classic formula path → needs pattern record;
        # absent → honest empty (fallback intact)
        self.assertEqual(cutting_svc.get_suggested_breakup(self.adda), [])
        # WITH usage: expected = 3 pieces/marker × 12 plies = 36, 1 color
        self._usage(marker_s_count=3)
        rows = cutting_svc.get_suggested_breakup(self.adda)
        self.assertEqual(rows, [{'pattern_id': self.pattern.pk,
                                 'size_id': self.size_s.pk,
                                 'color_id': self.color.pk, 'count': 36}])

    def test_reconciliation_advisory_math(self):
        self._layering(lay_count=10)
        self.assertIsNone(cutting_svc.layout_reconciliation(self.adda))
        self._usage(marker_s_count=2)      # expected S = 2 × 10 = 20
        recon = cutting_svc.layout_reconciliation(self.adda)
        self.assertEqual(recon['expected'], {self.size_s.pk: 20})
        self.assertEqual(recon['actual'], {})            # nothing cut yet
        self.assertEqual(recon['mismatches'][0]['expected'], 20)
        self.assertEqual(recon['mismatches'][0]['actual'], 0)


    def test_provider_failure_falls_back_silently(self):
        original = cp_handler.LAYOUT_PROVIDER

        def boom(adda):
            raise RuntimeError('x')
        cp_handler.LAYOUT_PROVIDER = boom
        try:
            self.assertEqual(
                cutting_svc.get_suggestion_source(self.adda),
                {'kind': 'formula'})
            self.assertIsNone(
                cutting_svc.layout_reconciliation(self.adda))
        finally:
            cp_handler.LAYOUT_PROVIDER = original
