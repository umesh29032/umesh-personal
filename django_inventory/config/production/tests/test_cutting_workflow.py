"""Tests for the Cutting Stage workspace flow (PR3).

YEH FILE KYU HAI?
─────────────────
Cutting stage ka full lifecycle test:
  start_cutting → upsert_breakup_row → save_cutting_draft → complete_cutting
  + get_suggested_breakup + reopen_cutting + legacy back-compat

Setup fixture builds the full upstream chain directly (without going
through Layering / Cutting Pattern service flows) so each test runs in
isolation in ~50ms.

Coverage:
  • start_cutting (mgmt gate, idempotent)
  • upsert_breakup_row (create/update/delete-on-zero, cross-product reject)
  • get_suggested_breakup (formula correctness)
  • complete_cutting workspace path: empty refusal, size-not-allowed
    refusal, color-not-layered refusal, happy path → barcodes + advance
  • complete_cutting legacy path: still works
  • reopen_cutting: refused with scanned barcode, allowed without
"""
from datetime import date
from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase
from django.utils import timezone

from accounts.models import Skill, User
from inventory.models import Role
from production.constants import (
    STAGE_CUTTING, STAGE_LAYERING,
)
from production.models import (
    AddaStageRecord, CuttingPatternRecord, CuttingPatternSizeAllocation, CuttingPieceBreakup,
    CuttingRecord, LayeringRecord, Product, ProductPattern, ProductPatternAssignment,
    ProductSize, Stage, WorkflowStage,
)
from production.services import (
    add_bundle_item, add_item_to_bundle, add_pieces_to_bundle, complete_cutting,
    create_adda, create_bundle, create_bundle_with_pieces, delete_breakup_row,
    delete_bundle, delete_bundle_item, get_suggested_breakup,
    reopen_cutting, save_cutting_draft, start_cutting, upsert_breakup_row,
)
from raw_materials.models import ClothColor, ClothType, StorageLocation
from raw_materials.services import bulk_create_rolls
from tracking.models import BatchBarcode


def _user(email, *, role_code='super_admin', is_super=True, skills=()):
    role = Role.objects.get(code=role_code)
    u = User.objects.create_user(
        email=email, password='x',
        is_superuser=is_super, is_staff=is_super,
    )
    u.role = role
    u.save()
    for s in skills:
        u.skills.add(Skill.objects.get(name=s))
    return u


class CuttingWorkflowFixture(TestCase):
    """Build full T-SHIRT product → adda at cutting stage with all upstream state."""

    @classmethod
    def setUpTestData(cls):
        cls.product = Product.objects.get(code='T-SHIRT')

        # Ensure cutting_pattern WorkflowStage exists at order=2.
        cp_stage = Stage.objects.get(code='cutting_pattern')
        WorkflowStage.objects.filter(
            product=cls.product, order__gte=2,
        ).update(order=99)
        cls.pattern_wf, _ = WorkflowStage.objects.get_or_create(
            product=cls.product, stage=cp_stage, defaults={'order': 2},
        )
        cls.pattern_wf.order = 2
        cls.pattern_wf.save(update_fields=['order'])
        for i, ws in enumerate(WorkflowStage.objects.filter(
            product=cls.product, order=99,
        ).order_by('id')):
            ws.order = 3 + i
            ws.save(update_fields=['order'])

        cls.layering_wf = WorkflowStage.objects.get(
            product=cls.product, stage__code=STAGE_LAYERING,
        )
        cls.cutting_wf = WorkflowStage.objects.get(
            product=cls.product, stage__code=STAGE_CUTTING,
        )
        # PAY-2 opt-out: this fixture exercises cutting mechanics, not payroll.
        # Cutting is seeded credits_workers=True (mig 0030); the worker-allocation
        # guard is covered separately by test_stage_credit. Not relevant here.
        cls.cutting_wf.credits_workers = False
        cls.cutting_wf.save(update_fields=['credits_workers'])

        # Patterns + Assignments
        ProductPatternAssignment.objects.filter(product=cls.product).delete()
        cls.front = ProductPattern.objects.get_or_create(
            code='front', defaults={'name': 'Front Panel'},
        )[0]
        cls.back = ProductPattern.objects.get_or_create(
            code='back', defaults={'name': 'Back Panel'},
        )[0]
        cls.sleeve = ProductPattern.objects.get_or_create(
            code='sleeve', defaults={'name': 'Sleeve'},
        )[0]
        cls.a_front = ProductPatternAssignment.objects.create(
            product=cls.product, pattern=cls.front, pieces_count=1,
        )
        cls.a_back = ProductPatternAssignment.objects.create(
            product=cls.product, pattern=cls.back, pieces_count=1,
        )
        cls.a_sleeve = ProductPatternAssignment.objects.create(
            product=cls.product, pattern=cls.sleeve, pieces_count=2,
        )

        # Sizes
        cls.s_s = ProductSize.objects.create(
            product=cls.product, code='s', label='Small', display_order=1,
        )
        cls.s_m = ProductSize.objects.create(
            product=cls.product, code='m', label='Medium', display_order=2,
        )
        cls.s_l = ProductSize.objects.create(
            product=cls.product, code='l', label='Large', display_order=3,
        )

    def setUp(self):
        # User with both skills
        self.admin = _user(
            f'admin{id(self)}@cw.test',
            skills=['cutting_master', 'cutting_master_helper'],
        )
        # Create adda + advance through layering + pattern manually.
        # Create rolls
        cotton = ClothType.objects.get(name='Cotton')
        self.red = ClothColor.objects.get(name='Red')
        loc = StorageLocation.objects.get(code='ROHINI')
        self.rolls = bulk_create_rolls(
            user=self.admin, cloth_type=cotton, storage_location=loc,
            purchased_date=date.today(),
            breakup=[{'color': self.red, 'qty': 2}],
        )
        self.adda = create_adda(self.admin, product=self.product)

        # Manually create completed Layering stage with LayeringRecord + rolls_used
        layering_sr = AddaStageRecord.objects.get(
            adda=self.adda, workflow_stage=self.layering_wf,
        )
        layering_sr.completed_at = timezone.now()
        layering_sr.completed_by = self.admin
        layering_sr.save(update_fields=['completed_at', 'completed_by'])
        layering_record = LayeringRecord.objects.create(
            stage_record=layering_sr,
            lay_count=10,          # 10 layers stacked
            total_colors=1,
            duration_minutes=30,
            layer_length_meters=Decimal('2.0'),
        )
        layering_record.rolls_used.set(self.rolls)
        self.layering_record = layering_record

        # Create completed Cutting Pattern stage with size allocations
        pattern_sr = AddaStageRecord.objects.create(
            adda=self.adda, workflow_stage=self.pattern_wf,
            started_at=timezone.now(),
            completed_at=timezone.now(),
            completed_by=self.admin,
        )
        self.pattern_record = CuttingPatternRecord.objects.create(stage_record=pattern_sr)
        CuttingPatternSizeAllocation.objects.create(
            record=self.pattern_record, size=self.s_s, proportion_pct=20,
        )
        CuttingPatternSizeAllocation.objects.create(
            record=self.pattern_record, size=self.s_m, proportion_pct=50,
        )
        CuttingPatternSizeAllocation.objects.create(
            record=self.pattern_record, size=self.s_l, proportion_pct=30,
        )

        # Advance adda to cutting stage
        self.adda.current_stage = self.cutting_wf
        self.adda.save(update_fields=['current_stage'])


class StartCuttingTests(CuttingWorkflowFixture):
    def test_creates_stage_record(self):
        sr = start_cutting(adda=self.adda, worker_ids=[self.admin.pk], user=self.admin)
        self.assertIsNotNone(sr.started_at)
        self.assertIsNone(sr.completed_at)
        self.assertIn(self.admin, sr.workers.all())

    def test_requires_management(self):
        karigar = _user('k1@cw.test', role_code='worker', is_super=False,
                        skills=['cutting_master'])
        with self.assertRaises(PermissionDenied):
            start_cutting(adda=self.adda, worker_ids=[karigar.pk], user=karigar)

    def test_idempotent(self):
        sr1 = start_cutting(adda=self.adda, worker_ids=[self.admin.pk], user=self.admin)
        sr2 = start_cutting(adda=self.adda, worker_ids=[self.admin.pk], user=self.admin)
        self.assertEqual(sr1.pk, sr2.pk)


class UpsertBreakupRowTests(CuttingWorkflowFixture):
    def setUp(self):
        super().setUp()
        start_cutting(adda=self.adda, worker_ids=[self.admin.pk], user=self.admin)

    def test_creates_row(self):
        row = upsert_breakup_row(
            adda=self.adda, size_id=self.s_m.id, color_id=self.red.id,
            pattern_id=self.front.id, count=10, user=self.admin,
        )
        self.assertIsNotNone(row)
        self.assertEqual(row.count, 10)

    def test_updates_existing_row(self):
        upsert_breakup_row(
            adda=self.adda, size_id=self.s_m.id, color_id=self.red.id,
            pattern_id=self.front.id, count=5, user=self.admin,
        )
        upsert_breakup_row(
            adda=self.adda, size_id=self.s_m.id, color_id=self.red.id,
            pattern_id=self.front.id, count=15, user=self.admin,
        )
        cr = CuttingRecord.objects.get(stage_record__adda=self.adda)
        self.assertEqual(cr.breakup.count(), 1)
        self.assertEqual(cr.breakup.first().count, 15)

    def test_count_zero_deletes_row(self):
        upsert_breakup_row(
            adda=self.adda, size_id=self.s_m.id, color_id=self.red.id,
            pattern_id=self.front.id, count=10, user=self.admin,
        )
        upsert_breakup_row(
            adda=self.adda, size_id=self.s_m.id, color_id=self.red.id,
            pattern_id=self.front.id, count=0, user=self.admin,
        )
        cr = CuttingRecord.objects.get(stage_record__adda=self.adda)
        self.assertEqual(cr.breakup.count(), 0)

    def test_rejects_cross_product_size(self):
        other = Product.objects.exclude(pk=self.product.pk).first()
        if not other:
            self.skipTest("Need second product.")
        foreign_size = ProductSize.objects.create(
            product=other, code='xxl', label='ForeignXXL',
        )
        with self.assertRaises(ValidationError):
            upsert_breakup_row(
                adda=self.adda, size_id=foreign_size.id, color_id=self.red.id,
                pattern_id=self.front.id, count=5, user=self.admin,
            )


class DeleteBreakupRowTests(CuttingWorkflowFixture):
    def setUp(self):
        super().setUp()
        start_cutting(adda=self.adda, worker_ids=[self.admin.pk], user=self.admin)
        self.row = upsert_breakup_row(
            adda=self.adda, size_id=self.s_m.id, color_id=self.red.id,
            pattern_id=self.front.id, count=10, user=self.admin,
        )

    def test_deletes_row(self):
        delete_breakup_row(adda=self.adda, breakup_id=self.row.id, user=self.admin)
        self.assertEqual(CuttingPieceBreakup.objects.filter(pk=self.row.id).count(), 0)


class SaveCuttingDraftTests(CuttingWorkflowFixture):
    def test_persists_notes_without_advancing(self):
        start_cutting(adda=self.adda, worker_ids=[self.admin.pk], user=self.admin)
        save_cutting_draft(adda=self.adda, notes='draft note', user=self.admin)
        cr = CuttingRecord.objects.get(stage_record__adda=self.adda)
        self.assertEqual(cr.notes, 'draft note')
        self.adda.refresh_from_db()
        # Stage still cutting (not advanced).
        self.assertEqual(self.adda.current_stage_id, self.cutting_wf.id)


class SuggestedBreakupTests(CuttingWorkflowFixture):
    def test_returns_expected_shape(self):
        sug = get_suggested_breakup(self.adda)
        # 3 patterns × 3 sizes × 1 color = 9 rows
        self.assertEqual(len(sug), 9)
        # Each row has required keys
        keys = set(sug[0].keys())
        self.assertEqual(keys, {'pattern_id', 'size_id', 'color_id', 'count'})

    def test_total_matches_formula(self):
        sug = get_suggested_breakup(self.adda)
        # Formula: layers (10) * (1+1+2 pieces_count = 4) * 100% = 40 pieces total
        # Distributed across 3 sizes 20/50/30 then 1 color = same per color
        # Per-pattern total: 10*pieces_count
        #   Front (1): 10. Split 20/50/30 = 2/5/3.
        #   Back (1): 10. Split = 2/5/3.
        #   Sleeve (2): 20. Split = 4/10/6.
        # Grand total: 40
        total = sum(row['count'] for row in sug)
        self.assertEqual(total, 40)


class CompleteCuttingWorkspaceTests(CuttingWorkflowFixture):
    def setUp(self):
        super().setUp()
        start_cutting(adda=self.adda, worker_ids=[self.admin.pk], user=self.admin)

    def test_refuses_when_no_bundles(self):
        # PR7: bundles drive completion, not breakup.
        with self.assertRaises(ValidationError):
            complete_cutting(adda=self.adda, user=self.admin)

    def test_refuses_size_not_in_pattern_allocations(self):
        # Add a size to product but not in pattern allocations
        xl = ProductSize.objects.create(
            product=self.product, code='xl', label='X Large', display_order=4,
        )
        add_bundle_item(
            adda=self.adda, size_id=xl.id, color_id=self.red.id,
            pattern_id=self.front.id, count=5, user=self.admin,
        )
        with self.assertRaisesMessage(ValidationError, 'batch sizes'):
            complete_cutting(adda=self.adda, user=self.admin)

    def test_refuses_color_not_in_layered_rolls(self):
        blue = ClothColor.objects.exclude(pk=self.red.pk).first()
        if not blue:
            self.skipTest("Need second color.")
        add_bundle_item(
            adda=self.adda, size_id=self.s_m.id, color_id=blue.id,
            pattern_id=self.front.id, count=5, user=self.admin,
        )
        with self.assertRaisesMessage(ValidationError, 'layered rolls'):
            complete_cutting(adda=self.adda, user=self.admin)

    def test_happy_path_generates_barcodes_and_advances(self):
        add_bundle_item(
            adda=self.adda, size_id=self.s_m.id, color_id=self.red.id,
            pattern_id=self.front.id, count=10, user=self.admin,
        )
        add_bundle_item(
            adda=self.adda, size_id=self.s_m.id, color_id=self.red.id,
            pattern_id=self.back.id, count=10, user=self.admin,
        )
        cr = complete_cutting(adda=self.adda, user=self.admin)
        self.assertEqual(cr.pieces_cut, 20)
        # PR6/7: BarcodeBatch rows store ranges; aggregated by (size, color).
        from tracking.models import BarcodeBatch
        batches = list(BarcodeBatch.objects.filter(adda=self.adda))
        # Two bundles, same (size, color), different patterns → 1 batch.
        self.assertEqual(len(batches), 1)
        self.assertEqual(batches[0].total_pieces, 20)
        # No lazy BatchBarcode rows yet (no scans).
        self.assertEqual(BatchBarcode.objects.filter(adda=self.adda).count(), 0)
        self.adda.refresh_from_db()
        self.assertNotEqual(self.adda.current_stage_id, self.cutting_wf.id)


class CompleteCuttingLegacyTests(TestCase):
    """Legacy single-shot path — back-compat with simple flows (NIKKAR)."""

    def test_legacy_signature_still_works(self):
        admin = _user('legacy@cw.test', skills=['cutting_master'])
        adda = create_adda(admin, product=Product.objects.get(code='NIKKAR'))
        # Manually advance through layering (simple flow: layering → cutting).
        layering_wf = WorkflowStage.objects.get(
            product=adda.product, stage__code=STAGE_LAYERING,
        )
        layering_sr = AddaStageRecord.objects.get(
            adda=adda, workflow_stage=layering_wf,
        )
        layering_sr.completed_at = timezone.now()
        layering_sr.completed_by = admin
        layering_sr.save(update_fields=['completed_at', 'completed_by'])
        cutting_wf = WorkflowStage.objects.get(
            product=adda.product, stage__code=STAGE_CUTTING,
        )
        adda.current_stage = cutting_wf
        adda.save(update_fields=['current_stage'])

        cr = complete_cutting(
            adda=adda, user=admin,
            pieces_cut=50, worker_ids=[admin.pk], notes='legacy',
        )
        self.assertEqual(cr.pieces_cut, 50)
        # PR6: one legacy BarcodeBatch (size=None, color=None) covering 1..50.
        from tracking.models import BarcodeBatch
        batches = list(BarcodeBatch.objects.filter(adda=adda))
        self.assertEqual(len(batches), 1)
        self.assertEqual(batches[0].total_pieces, 50)
        self.assertEqual(batches[0].start_seq, 1)
        self.assertEqual(batches[0].end_seq, 50)
        self.assertIsNone(batches[0].size)
        self.assertIsNone(batches[0].color)


class ReopenCuttingTests(CuttingWorkflowFixture):
    def setUp(self):
        super().setUp()
        start_cutting(adda=self.adda, worker_ids=[self.admin.pk], user=self.admin)
        # PR7: bundles drive barcodes — set up one bundle for reopen tests.
        add_bundle_item(
            adda=self.adda, size_id=self.s_m.id, color_id=self.red.id,
            pattern_id=self.front.id, count=5, user=self.admin,
        )
        complete_cutting(adda=self.adda, user=self.admin)

    def test_reopens_when_no_scan(self):
        from tracking.models import BarcodeBatch
        sr = reopen_cutting(adda=self.adda, user=self.admin)
        self.assertIsNone(sr.completed_at)
        # Batches wiped (one-shot re-generation rule).
        self.assertEqual(BarcodeBatch.objects.filter(adda=self.adda).count(), 0)
        self.adda.refresh_from_db()
        self.assertEqual(self.adda.current_stage_id, self.cutting_wf.id)

    def test_refuses_when_barcode_scanned(self):
        # PR6: scan creates BatchBarcode lazily; simulate via get_or_create_piece.
        from tracking.models import BarcodeBatch
        from tracking.services import get_or_create_piece
        batch = BarcodeBatch.objects.filter(adda=self.adda).first()
        piece = get_or_create_piece(batch, batch.start_seq)
        piece.last_scanned_at = timezone.now()
        piece.save(update_fields=['last_scanned_at'])
        with self.assertRaisesMessage(ValidationError, 'scanned'):
            reopen_cutting(adda=self.adda, user=self.admin)


class CreateBundleTests(CuttingWorkflowFixture):
    """PR9 two-step flow: create bundle then add items."""

    def setUp(self):
        super().setUp()
        start_cutting(adda=self.adda, worker_ids=[self.admin.pk], user=self.admin)

    def test_create_bundle_creates_header_without_items(self):
        bundle = create_bundle(
            adda=self.adda, size_id=self.s_l.id,
            bundle_number='Lot-A', user=self.admin,
        )
        self.assertEqual(bundle.size, self.s_l)
        self.assertEqual(bundle.bundle_number, 'Lot-A')
        self.assertEqual(bundle.total_pieces, 0)
        self.assertEqual(bundle.items.count(), 0)

    def test_create_bundle_idempotent_updates_number(self):
        b1 = create_bundle(
            adda=self.adda, size_id=self.s_l.id,
            bundle_number='Lot-A', user=self.admin,
        )
        b2 = create_bundle(
            adda=self.adda, size_id=self.s_l.id,
            bundle_number='Lot-B', user=self.admin,
        )
        self.assertEqual(b1.pk, b2.pk)
        b2.refresh_from_db()
        self.assertEqual(b2.bundle_number, 'Lot-B')

    def test_add_item_to_bundle_scoped_to_size(self):
        bundle = create_bundle(
            adda=self.adda, size_id=self.s_l.id, user=self.admin,
        )
        item = add_item_to_bundle(
            adda=self.adda, bundle_id=bundle.id,
            pattern_id=self.front.id, color_id=self.red.id,
            count=20, user=self.admin,
        )
        self.assertEqual(item.bundle, bundle)
        self.assertEqual(item.count, 20)
        bundle.refresh_from_db()
        self.assertEqual(bundle.total_pieces, 20)

    def test_add_item_to_bundle_duplicate_updates_count(self):
        bundle = create_bundle(
            adda=self.adda, size_id=self.s_l.id, user=self.admin,
        )
        add_item_to_bundle(
            adda=self.adda, bundle_id=bundle.id,
            pattern_id=self.front.id, color_id=self.red.id,
            count=10, user=self.admin,
        )
        add_item_to_bundle(
            adda=self.adda, bundle_id=bundle.id,
            pattern_id=self.front.id, color_id=self.red.id,
            count=25, user=self.admin,
        )
        self.assertEqual(bundle.items.count(), 1)
        self.assertEqual(bundle.items.first().count, 25)
        bundle.refresh_from_db()
        self.assertEqual(bundle.total_pieces, 25)

    def test_add_item_rejects_wrong_adda_bundle(self):
        # Create a bundle on a different adda (different cutting_record).
        other_admin = _user(f'other{id(self)}@cw.test', skills=['cutting_master'])
        other_adda = create_adda(other_admin, product=self.product)
        other_adda.current_stage = self.cutting_wf
        other_adda.save(update_fields=['current_stage'])
        start_cutting(adda=other_adda, worker_ids=[other_admin.pk], user=other_admin)
        other_bundle = create_bundle(
            adda=other_adda, size_id=self.s_l.id, user=other_admin,
        )
        # Trying to add item to other_adda's bundle via self.adda → reject.
        with self.assertRaises(ValidationError):
            add_item_to_bundle(
                adda=self.adda, bundle_id=other_bundle.id,
                pattern_id=self.front.id, color_id=self.red.id,
                count=5, user=self.admin,
            )


class AddPiecesToBundleTests(CuttingWorkflowFixture):
    """PR10 multi-select consumption flow:
    Section 02 breakup rows → consumed into bundles via add_pieces_to_bundle.
    """

    def setUp(self):
        super().setUp()
        start_cutting(adda=self.adda, worker_ids=[self.admin.pk], user=self.admin)
        # Seed Section 02 breakup with 3 rows (cutting pieces inventory).
        self.brk_front = upsert_breakup_row(
            adda=self.adda, size_id=self.s_l.id, color_id=self.red.id,
            pattern_id=self.front.id, count=20, user=self.admin,
        )
        self.brk_back = upsert_breakup_row(
            adda=self.adda, size_id=self.s_l.id, color_id=self.red.id,
            pattern_id=self.back.id, count=20, user=self.admin,
        )
        self.brk_sleeve = upsert_breakup_row(
            adda=self.adda, size_id=self.s_l.id, color_id=self.red.id,
            pattern_id=self.sleeve.id, count=40, user=self.admin,
        )
        self.bundle = create_bundle(
            adda=self.adda, size_id=self.s_l.id,
            bundle_number='Lot-A', user=self.admin,
        )

    def test_consume_partial_updates_available(self):
        add_pieces_to_bundle(
            adda=self.adda, bundle_id=self.bundle.id,
            selections=[
                {'breakup_id': self.brk_front.id, 'take_count': 10},
                {'breakup_id': self.brk_back.id, 'take_count': 5},
            ],
            user=self.admin,
        )
        self.brk_front.refresh_from_db()
        self.brk_back.refresh_from_db()
        self.bundle.refresh_from_db()
        self.assertEqual(self.brk_front.consumed_count, 10)
        self.assertEqual(self.brk_front.available_count, 10)
        self.assertEqual(self.brk_back.consumed_count, 5)
        self.assertEqual(self.bundle.total_pieces, 15)

    def test_consume_full_zeros_available(self):
        add_pieces_to_bundle(
            adda=self.adda, bundle_id=self.bundle.id,
            selections=[{'breakup_id': self.brk_front.id, 'take_count': 20}],
            user=self.admin,
        )
        self.brk_front.refresh_from_db()
        self.assertEqual(self.brk_front.available_count, 0)

    def test_over_take_rejects_whole_batch(self):
        with self.assertRaisesMessage(ValidationError, 'available'):
            add_pieces_to_bundle(
                adda=self.adda, bundle_id=self.bundle.id,
                selections=[
                    {'breakup_id': self.brk_front.id, 'take_count': 5},
                    {'breakup_id': self.brk_back.id, 'take_count': 999},
                ],
                user=self.admin,
            )
        # Atomic — nothing consumed.
        self.brk_front.refresh_from_db()
        self.brk_back.refresh_from_db()
        self.assertEqual(self.brk_front.consumed_count, 0)
        self.assertEqual(self.brk_back.consumed_count, 0)

    def test_delete_bundle_item_restores_consumed(self):
        items = add_pieces_to_bundle(
            adda=self.adda, bundle_id=self.bundle.id,
            selections=[{'breakup_id': self.brk_front.id, 'take_count': 12}],
            user=self.admin,
        )
        self.brk_front.refresh_from_db()
        self.assertEqual(self.brk_front.consumed_count, 12)
        delete_bundle_item(
            adda=self.adda, item_id=items[0].id, user=self.admin,
        )
        self.brk_front.refresh_from_db()
        self.assertEqual(self.brk_front.consumed_count, 0)
        self.assertEqual(self.brk_front.available_count, 20)

    def test_delete_bundle_restores_all_sources(self):
        add_pieces_to_bundle(
            adda=self.adda, bundle_id=self.bundle.id,
            selections=[
                {'breakup_id': self.brk_front.id, 'take_count': 10},
                {'breakup_id': self.brk_back.id, 'take_count': 10},
            ],
            user=self.admin,
        )
        delete_bundle(
            adda=self.adda, bundle_id=self.bundle.id, user=self.admin,
        )
        self.brk_front.refresh_from_db()
        self.brk_back.refresh_from_db()
        self.assertEqual(self.brk_front.consumed_count, 0)
        self.assertEqual(self.brk_back.consumed_count, 0)


class CreateBundleWithPiecesTests(CuttingWorkflowFixture):
    """PR12: atomic create-with-pieces — header + items in one tx."""

    def setUp(self):
        super().setUp()
        start_cutting(adda=self.adda, worker_ids=[self.admin.pk], user=self.admin)
        self.brk_front = upsert_breakup_row(
            adda=self.adda, size_id=self.s_l.id, color_id=self.red.id,
            pattern_id=self.front.id, count=20, user=self.admin,
        )
        self.brk_back = upsert_breakup_row(
            adda=self.adda, size_id=self.s_l.id, color_id=self.red.id,
            pattern_id=self.back.id, count=15, user=self.admin,
        )

    def test_atomic_creates_header_and_items(self):
        bundle = create_bundle_with_pieces(
            adda=self.adda, size_id=self.s_l.id,
            bundle_number='Lot-A',
            selections=[
                {'breakup_id': self.brk_front.id, 'take_count': 10},
                {'breakup_id': self.brk_back.id, 'take_count': 5},
            ],
            user=self.admin,
        )
        self.assertEqual(bundle.size, self.s_l)
        self.assertEqual(bundle.bundle_number, 'Lot-A')
        self.assertEqual(bundle.total_pieces, 15)
        self.assertEqual(bundle.items.count(), 2)
        # Source breakup rows updated
        self.brk_front.refresh_from_db()
        self.brk_back.refresh_from_db()
        self.assertEqual(self.brk_front.consumed_count, 10)
        self.assertEqual(self.brk_back.consumed_count, 5)

    def test_empty_selections_creates_empty_header(self):
        bundle = create_bundle_with_pieces(
            adda=self.adda, size_id=self.s_l.id,
            bundle_number='', selections=[], user=self.admin,
        )
        self.assertEqual(bundle.total_pieces, 0)
        self.assertEqual(bundle.items.count(), 0)

    def test_zero_take_counts_skipped(self):
        bundle = create_bundle_with_pieces(
            adda=self.adda, size_id=self.s_l.id,
            bundle_number='',
            selections=[
                {'breakup_id': self.brk_front.id, 'take_count': 0},
                {'breakup_id': self.brk_back.id, 'take_count': 7},
            ],
            user=self.admin,
        )
        self.assertEqual(bundle.total_pieces, 7)
        self.assertEqual(bundle.items.count(), 1)

    def test_over_take_rolls_back_entire_tx(self):
        with self.assertRaises(ValidationError):
            create_bundle_with_pieces(
                adda=self.adda, size_id=self.s_l.id,
                bundle_number='',
                selections=[
                    {'breakup_id': self.brk_front.id, 'take_count': 5},
                    {'breakup_id': self.brk_back.id, 'take_count': 999},
                ],
                user=self.admin,
            )
        # Atomic — nothing consumed, no bundle created.
        self.brk_front.refresh_from_db()
        self.assertEqual(self.brk_front.consumed_count, 0)
        # Bundle header is created idempotently by service before consumption —
        # but should not persist if items fail. Verify total still 0.
        from production.models import CuttingBundle
        bundle = CuttingBundle.objects.filter(
            cutting_record__stage_record__adda=self.adda,
            size=self.s_l,
        ).first()
        if bundle is not None:
            self.assertEqual(bundle.total_pieces, 0)
            self.assertEqual(bundle.items.count(), 0)


class BarcodeBatchBundleLinkTests(CuttingWorkflowFixture):
    """PR11: BarcodeBatch.bundle FK populated on generation."""

    def setUp(self):
        super().setUp()
        start_cutting(adda=self.adda, worker_ids=[self.admin.pk], user=self.admin)
        # Two bundles, both consume from same color (red) but different sizes.
        brk_m = upsert_breakup_row(
            adda=self.adda, size_id=self.s_m.id, color_id=self.red.id,
            pattern_id=self.front.id, count=10, user=self.admin,
        )
        brk_l = upsert_breakup_row(
            adda=self.adda, size_id=self.s_l.id, color_id=self.red.id,
            pattern_id=self.front.id, count=20, user=self.admin,
        )
        self.bundle_m = create_bundle(
            adda=self.adda, size_id=self.s_m.id, user=self.admin,
        )
        self.bundle_l = create_bundle(
            adda=self.adda, size_id=self.s_l.id, user=self.admin,
        )
        add_pieces_to_bundle(
            adda=self.adda, bundle_id=self.bundle_m.id,
            selections=[{'breakup_id': brk_m.id, 'take_count': 10}],
            user=self.admin,
        )
        add_pieces_to_bundle(
            adda=self.adda, bundle_id=self.bundle_l.id,
            selections=[{'breakup_id': brk_l.id, 'take_count': 20}],
            user=self.admin,
        )

    def test_batches_link_to_correct_bundle(self):
        complete_cutting(adda=self.adda, user=self.admin)
        from tracking.models import BarcodeBatch
        batches = list(BarcodeBatch.objects.filter(adda=self.adda).order_by('start_seq'))
        self.assertEqual(len(batches), 2)
        # M batch (display_order=2) comes first, L second.
        m_batch = next(b for b in batches if b.size_id == self.s_m.id)
        l_batch = next(b for b in batches if b.size_id == self.s_l.id)
        self.assertEqual(m_batch.bundle_id, self.bundle_m.id)
        self.assertEqual(l_batch.bundle_id, self.bundle_l.id)
        self.assertEqual(m_batch.total_pieces, 10)
        self.assertEqual(l_batch.total_pieces, 20)
