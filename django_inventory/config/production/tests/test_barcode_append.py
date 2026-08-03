"""IDENTITY LAW — append generation for late Cutting Streams
(owner-approved BARCODE_IMPLEMENTATION_READINESS + BARCODE_IDENTITY_REVIEW,
2026-07-11): per-(size,color) deficit coverage · sequences continue at
Max(end_seq)+1, never renumbered · existing batches untouched ·
"nothing new to cover" honesty · lane provenance in the audit event."""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from accounts.models import Role, Skill
from production.models import (Adda, AddaProductSizeColorPieceBreakdown,
                               AddaStageRecord, CuttingRecord, CuttingStream,
                               Product, ProductSize, Stage, StageCategory,
                               WorkflowStage)
from production.stages.barcode_generation.assembly import (
    append_uncovered_batches, generate_for_adda)
from raw_materials.models import ClothColor
from tracking.models import BarcodeBatch

User = get_user_model()


class AppendWorld(TestCase):
    def setUp(self):
        role = Role.objects.get(code='super_admin')
        self.user = User.objects.create_user('bca@test.local', password='x',
                                             is_superuser=True)
        self.user.role = role
        self.user.save()
        self.product = Product.objects.create(code='BCA', name='Append')
        self.size = ProductSize.objects.create(product=self.product,
                                               code='m', label='M',
                                               display_order=1)
        self.color = ClothColor.objects.create(name='BCA Red')
        cutting = Stage.objects.get(code='cutting')
        self.ws = WorkflowStage.objects.create(
            product=self.product, stage=cutting, order=1,
            cost_rate=Decimal('1'))
        self.adda = Adda.objects.create(code='BCA-001', product=self.product,
                                        current_stage=self.ws)

    def _lane(self, group='body', seq=1, reason=''):
        return CuttingStream.objects.create(
            adda=self.adda, fabric_group=group, sequence=seq,
            reason=reason, is_blocking=True)

    def _cut_rows(self, lane, count):
        sr = AddaStageRecord.objects.create(
            adda=self.adda, workflow_stage=self.ws, stream=lane,
            started_at=timezone.now(), completed_at=timezone.now())
        cr = CuttingRecord.objects.create(stage_record=sr,
                                          pieces_cut=count, notes='')
        AddaProductSizeColorPieceBreakdown.objects.create(
            cutting_record=cr, adda=self.adda, product=self.product,
            size=self.size, color=self.color,
            verified_piece_count=count, created_by=self.user)
        return cr

    def test_append_continues_sequence_max_plus_one(self):
        lane1 = self._lane()
        self._cut_rows(lane1, 60)
        generate_for_adda(self.adda)
        first = BarcodeBatch.objects.get(adda=self.adda)
        self.assertEqual((first.start_seq, first.end_seq), (1, 60))

        recut = self._lane(seq=2, reason='Recut — 12 failed checking')
        self._cut_rows(recut, 12)
        appended, lanes = append_uncovered_batches(self.adda)
        self.assertEqual(appended, 12)
        new = BarcodeBatch.objects.filter(adda=self.adda).order_by(
            '-end_seq').first()
        self.assertEqual((new.start_seq, new.end_seq), (61, 72))
        # existing identity range untouched
        first.refresh_from_db()
        self.assertEqual((first.start_seq, first.end_seq), (1, 60))
        # lane provenance surfaces for the audit event
        self.assertTrue(any('Recut' in n for n in lanes))

    def test_nothing_new_to_cover_is_an_honest_refusal(self):
        lane1 = self._lane()
        self._cut_rows(lane1, 10)
        generate_for_adda(self.adda)
        with self.assertRaisesMessage(ValidationError,
                                      'Nothing new to cover'):
            append_uncovered_batches(self.adda)

    def test_deficit_math_covers_only_the_gap(self):
        lane1 = self._lane()
        self._cut_rows(lane1, 30)
        generate_for_adda(self.adda)
        # additional production lane, SAME (size,color): +8
        extra = self._lane(seq=2, reason='Additional production')
        self._cut_rows(extra, 8)
        appended, _ = append_uncovered_batches(self.adda)
        self.assertEqual(appended, 8)
        total = sum(b.total_pieces
                    for b in BarcodeBatch.objects.filter(adda=self.adda))
        self.assertEqual(total, 38)

    def test_double_append_refused_after_coverage(self):
        lane1 = self._lane()
        self._cut_rows(lane1, 5)
        generate_for_adda(self.adda)
        self._cut_rows(self._lane(seq=2, reason='Recut'), 3)
        append_uncovered_batches(self.adda)
        with self.assertRaisesMessage(ValidationError,
                                      'Nothing new to cover'):
            append_uncovered_batches(self.adda)

    def test_first_generation_unchanged_when_no_batches(self):
        lane1 = self._lane()
        self._cut_rows(lane1, 15)
        total = generate_for_adda(self.adda)
        self.assertEqual(total, 15)
        b = BarcodeBatch.objects.get(adda=self.adda)
        self.assertEqual((b.start_seq, b.end_seq, b.total_pieces),
                         (1, 15, 15))

    def test_scan_resolves_appended_range(self):
        lane1 = self._lane()
        self._cut_rows(lane1, 60)
        generate_for_adda(self.adda)
        self._cut_rows(self._lane(seq=2, reason='Recut'), 12)
        append_uncovered_batches(self.adda)
        from tracking.services.barcode_service import resolve_value
        batch, seq = resolve_value('BCA-001-0065')
        self.assertEqual(seq, 65)
        self.assertEqual(batch.size_id, self.size.pk)
        self.assertEqual(batch.color_id, self.color.pk)


class LateLaneNoRegressTests(AppendWorld):
    """Frozen lifecycle §2: a post-join lane NEVER regresses the Adda —
    the join gate has no memory (found LIVE: recut completion pulled the
    pointer back from an ops stage to Barcode Generation)."""

    def test_post_join_lane_completion_keeps_pointer(self):
        from production.services.adda_service import advance_lane
        ops = Stage.objects.exclude(
            code__in=('layering', 'cutting_pattern', 'cutting')).first()
        ops_ws = WorkflowStage.objects.create(
            product=self.product, stage=ops, order=5,
            cost_rate=Decimal('1'))
        lane1 = self._lane()
        cr = self._cut_rows(lane1, 10)
        # simulate: adda already joined and moved into ops
        self.adda.current_stage = ops_ws
        self.adda.save(update_fields=['current_stage'])
        recut = self._lane(seq=2, reason='Recut')
        cr2 = self._cut_rows(recut, 3)
        advance_lane(self.adda, stream=recut,
                     leaving_sr=cr2.stage_record, user=self.user,
                     enforce_worker_credit=False)
        self.adda.refresh_from_db()
        self.assertEqual(self.adda.current_stage_id, ops_ws.pk)  # no regress


class ScanStatusButtonTests(AppendWorld):
    """M8: the one-tap status wire (thin view → mark_status single writer)."""

    def test_status_post_updates_and_worker_gate(self):
        from django.urls import reverse
        lane = self._lane()
        self._cut_rows(lane, 5)
        generate_for_adda(self.adda)
        url = reverse('tracking:scan-status', kwargs={'value': 'BCA-001-0003'})
        self.client.force_login(self.user)          # super_admin = production
        resp = self.client.post(url, {'status': 'packed'}, follow=True)
        self.assertEqual(resp.status_code, 200)
        from tracking.models import BatchBarcode
        piece = BatchBarcode.objects.get(value='BCA-001-0003')
        self.assertEqual(piece.status, 'packed')
        # invalid status = honest refusal, no change
        self.client.post(url, {'status': 'vaporized'}, follow=True)
        piece.refresh_from_db()
        self.assertEqual(piece.status, 'packed')
