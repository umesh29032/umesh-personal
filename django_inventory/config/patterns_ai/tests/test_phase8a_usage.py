"""Phase 8A — ApprovedLayoutUsage foundation (owner freezes F1-F3 +
refinements 1-3). Service-level milestone: no UI, zero production-file
changes — proven entirely here."""
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from accounts.models import Role
from production.models import (Adda, Product, ProductPattern,
                               ProductPatternAssignment, ProductSize)
from patterns_ai.models import ApprovedLayoutUsage
from patterns_ai.services import layout_library_service as lib
from patterns_ai.services import layout_usage_service as usage_svc
from patterns_ai.services import marker_generation_service as gen
from patterns_ai.services import pattern_geometry_service as geo
from patterns_ai.models import PieceSizeGeometry
from patterns_ai.tests.test_p3_generation import rect_um

User = get_user_model()


def _ring(x, y, w, h):
    return [[x, y], [x + w, y], [x + w, y + h], [x, y + h]]


class _P8ABase(TestCase):
    @classmethod
    def setUpTestData(cls):
        mgr = Role.objects.get_or_create(code='manager',
                                         defaults={'name': 'M'})[0]
        cls.mgr = User.objects.create_user('p8a@test.local', password='x',
                                           role=mgr)
        cls.product = Product.objects.create(code='P8A', name='P8A Usage')
        cls.size_s = ProductSize.objects.create(product=cls.product,
                                                code='s', label='S',
                                                display_order=1)
        cls.size_m = ProductSize.objects.create(product=cls.product,
                                                code='m', label='M',
                                                display_order=2)
        cls.front = cls._piece('p8a-front', 'Front', 'body')
        cls.rib = cls._piece('p8a-rib', 'Rib', 'rib')
        for piece, sizes in ((cls.front, (cls.size_s, cls.size_m)),
                             (cls.rib, (cls.size_s,))):
            d = geo.get_or_create_draft(user=cls.mgr, piece=piece)
            for s in sizes:
                PieceSizeGeometry.objects.create(   # fixture only
                    version=d, size=s, geometry=rect_um(300, 200),
                    trust_grade='photo_calibrated', created_by=cls.mgr)
            geo.confirm_version(user=cls.mgr, version=d)
        cls.adda = Adda.objects.create(code='P8A-001',
                                       product=cls.product,
                                       created_by=cls.mgr)

    @classmethod
    def _piece(cls, code, name, group):
        pattern = ProductPattern.objects.create(code=code, name=name)
        ProductPatternAssignment.objects.create(product=cls.product,
                                                pattern=pattern,
                                                pieces_count=1)
        return geo.create_piece(user=cls.mgr, product=cls.product,
                                pattern=pattern, fabric_group=group)

    def _layout(self, group='body', placements=None):
        # engine frame [along, across]; body default: 2×S front + 1×M front
        placements = placements or [
            {'key': f'{self.front.pk}:{self.size_s.pk}', 'instance': 1,
             'polygon_mm': _ring(10, 10, 200, 300)},
            {'key': f'{self.front.pk}:{self.size_s.pk}', 'instance': 2,
             'polygon_mm': _ring(10, 320, 200, 300), 'mirrored': True},
            {'key': f'{self.front.pk}:{self.size_m.pk}', 'instance': 3,
             'polygon_mm': _ring(220, 10, 200, 300)},
        ]
        _, cand = gen.save_table_layout(
            user=self.mgr, product=self.product, width_mm=900,
            height_mm=2000, spacing_mm=2.0, fabric_group=group,
            placements=placements)
        return lib.approve_table_layout(user=self.mgr,
                                        product=self.product,
                                        candidate=cand)


class RecordUsageGuards(_P8ABase):
    def test_records_active_layout_and_freezes_group(self):
        lay = self._layout()
        u = usage_svc.record_usage(user=self.mgr, adda=self.adda,
                                   layout=lay)
        self.assertEqual(u.fabric_group, 'body')     # the sanctioned denorm
        self.assertIsNone(u.voided_at)
        self.assertEqual(u.recorded_by, self.mgr)

    def test_refuses_inactive_stale_crossproduct_and_dup_group(self):
        lay = self._layout()
        usage_svc.record_usage(user=self.mgr, adda=self.adda, layout=lay)
        # duplicate active (adda, group)
        lay2 = self._layout(placements=[
            {'key': f'{self.front.pk}:{self.size_s.pk}', 'instance': 1,
             'polygon_mm': _ring(5, 5, 200, 300)}])
        with self.assertRaises(ValidationError) as ctx:
            usage_svc.record_usage(user=self.mgr, adda=self.adda,
                                   layout=lay2)
        self.assertIn('void that usage first', str(ctx.exception))
        # archived layout refused
        lib.archive_layout(user=self.mgr, layout=lay2)
        with self.assertRaises(ValidationError):
            usage_svc.record_usage(user=self.mgr, adda=self.adda,
                                   layout=lay2)
        # STALE refused — LAW 11 finally gates (new confirmed version)
        lay3 = self._layout(group='rib', placements=[
            {'key': f'{self.rib.pk}:{self.size_s.pk}', 'instance': 1,
             'polygon_mm': _ring(10, 10, 200, 300)}])
        d2 = geo.start_next_version(user=self.mgr, piece=self.rib)
        geo.confirm_version(user=self.mgr, version=d2)
        with self.assertRaises(ValidationError) as ctx:
            usage_svc.record_usage(user=self.mgr, adda=self.adda,
                                   layout=lay3)
        self.assertIn('STALE', str(ctx.exception))
        # cross-product refused
        other = Product.objects.create(code='P8AX', name='Other')
        alien_adda = Adda.objects.create(product=other,
                                         created_by=self.mgr)
        with self.assertRaises(ValidationError):
            usage_svc.record_usage(user=self.mgr, adda=alien_adda,
                                   layout=lay)

    def test_multiple_groups_per_adda_ok(self):
        body = self._layout()
        rib = self._layout(group='rib', placements=[
            {'key': f'{self.rib.pk}:{self.size_s.pk}', 'instance': 1,
             'polygon_mm': _ring(10, 10, 200, 300)}])
        usage_svc.record_usage(user=self.mgr, adda=self.adda, layout=body)
        usage_svc.record_usage(user=self.mgr, adda=self.adda, layout=rib)
        self.assertEqual(ApprovedLayoutUsage.objects.filter(
            adda=self.adda, voided_at__isnull=True).count(), 2)


class HistoryForeverTests(_P8ABase):
    def test_void_keeps_history_and_reopens_the_slot(self):
        lay = self._layout()
        u = usage_svc.record_usage(user=self.mgr, adda=self.adda,
                                   layout=lay)
        with self.assertRaises(ValidationError):
            usage_svc.void_usage(user=self.mgr, usage=u, reason='  ')
        usage_svc.void_usage(user=self.mgr, usage=u,
                             reason='wrong marker picked')
        u.refresh_from_db()
        self.assertIsNotNone(u.voided_at)
        self.assertEqual(u.void_reason, 'wrong marker picked')
        # the slot reopens — a NEW usage records (never reassign)
        lay2 = self._layout(placements=[
            {'key': f'{self.front.pk}:{self.size_s.pk}', 'instance': 1,
             'polygon_mm': _ring(5, 5, 200, 300)}])
        u2 = usage_svc.record_usage(user=self.mgr, adda=self.adda,
                                    layout=lay2)
        self.assertNotEqual(u.pk, u2.pk)
        self.assertEqual(ApprovedLayoutUsage.objects.count(), 2)  # both kept

    def test_never_delete_never_reassign(self):
        lay = self._layout()
        u = usage_svc.record_usage(user=self.mgr, adda=self.adda,
                                   layout=lay)
        with self.assertRaises(ValueError):
            u.delete()                                   # F1
        lay2 = self._layout(placements=[
            {'key': f'{self.front.pk}:{self.size_m.pk}', 'instance': 1,
             'polygon_mm': _ring(5, 5, 200, 300)}])
        u.layout = lay2                                  # refinement 1
        with self.assertRaises(ValueError):
            u.save()

    def test_stage_record_stamps_once(self):
        from production.models import (AddaStageRecord, Stage,
                                       WorkflowStage)
        st, _ = Stage.objects.get_or_create(code='p8a_s1',
                                            defaults={'name': 'P8A S1'})
        ws = WorkflowStage.objects.create(product=self.product, stage=st,
                                          order=1)
        sr = AddaStageRecord.objects.create(adda=self.adda,
                                            workflow_stage=ws)
        lay = self._layout()
        u = usage_svc.record_usage(user=self.mgr, adda=self.adda,
                                   layout=lay)
        usage_svc.stamp_stage_record(usage=u, stage_record=sr)
        u.refresh_from_db()
        self.assertEqual(u.stage_record_id, sr.pk)
        usage_svc.stamp_stage_record(usage=u, stage_record=sr)  # idempotent
        st2, _ = Stage.objects.get_or_create(code='p8a_s2',
                                             defaults={'name': 'P8A S2'})
        ws2 = WorkflowStage.objects.create(product=self.product,
                                           stage=st2, order=2)
        sr2 = AddaStageRecord.objects.create(adda=self.adda,
                                             workflow_stage=ws2)
        with self.assertRaises(ValidationError):
            usage_svc.stamp_stage_record(usage=u, stage_record=sr2)


class DerivedForeverTests(_P8ABase):
    def test_marker_content_counts_placements_per_size(self):
        lay = self._layout()   # 2×S + 1×M (one mirrored — counts once)
        content = usage_svc.marker_content(lay)
        self.assertEqual(content, {self.size_s.pk: 2, self.size_m.pk: 1})

    def test_expected_pieces_times_lay_count_computed_never_stored(self):
        lay = self._layout()
        u = usage_svc.record_usage(user=self.mgr, adda=self.adda,
                                   layout=lay)
        self.assertEqual(usage_svc.expected_pieces(u, 12),
                         {self.size_s.pk: 24, self.size_m.pk: 12})
        self.assertEqual(usage_svc.expected_pieces(u, 0), {
            self.size_s.pk: 0, self.size_m.pk: 0})
        # refinement 3: no stored expected anywhere on the row
        field_names = {f.name for f in ApprovedLayoutUsage._meta.fields}
        self.assertFalse({'expected', 'expected_pieces',
                          'placements', 'geometry',
                          'utilization'} & field_names)   # F2 pointer-only
