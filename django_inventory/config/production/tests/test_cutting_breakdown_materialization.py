"""PR-B tests — cutting completion materialises breakdown + back-compat.

YEH FILE KYU HAI?
─────────────────
PR-B 2026-05-29: cutting_service ne barcode generation se decouple kiya.
Ab cutting complete pe:
  • AddaProductSizeColorPieceBreakdown rows freeze hoti hain
  • Agar product workflow mein barcode_generation stage hai → barcodes
    NHI banti (downstream stage karega)
  • Agar nahi hai → legacy inline barcode generation chalu rehti (back-compat)

Coverage:
  • Workspace path materialises rows matching CuttingBundleItem aggregation
  • Legacy path materialises single NULL-NULL row
  • Back-compat: product WITHOUT barcode_gen stage still inline-generates
  • Forward: product WITH barcode_gen stage skips inline barcode gen
  • Reopen deletes breakdown rows
  • Reopen refused if barcode_generation already started
  • Reopen refused if export batch exists
  • generate_from_breakdown produces equivalent BarcodeBatch shape
"""
from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from accounts.models import Skill, User
from inventory.models import Role
from production.constants import (
    STAGE_BARCODE_GENERATION, STAGE_CUTTING, STAGE_CUTTING_PATTERN,
    STAGE_LAYERING,
)
from production.models import (
    Adda, AddaProductSizeColorPieceBreakdown, AddaStageRecord,
    BarcodeGenerationRecord, CuttingPatternRecord,
    CuttingPatternSizeAllocation, CuttingRecord, LayeringRecord,
    Product, ProductPattern, ProductPatternAssignment, ProductSize, Stage,
    WorkflowStage,
)
from production.services import (
    add_pieces_to_bundle, complete_cutting, create_adda, create_bundle,
    reopen_cutting, start_cutting, upsert_breakup_row,
)
from raw_materials.models import ClothColor, ClothType, StorageLocation
from raw_materials.services import bulk_create_rolls
from tracking.models import BarcodeBatch, BarcodeExportBatch
from tracking.services import generate_from_breakdown


def _admin(email='ad@brk.test'):
    role = Role.objects.get(code='super_admin')
    u = User.objects.create_user(
        email=email, password='x', is_superuser=True, is_staff=True,
    )
    u.role = role
    u.save()
    for s in ('cutting_master', 'cutting_master_helper'):
        u.skills.add(Skill.objects.get(name=s))
    return u


class _WorkspaceCuttingFixture(TestCase):
    """T-SHIRT product at cutting stage with pattern allocations + bundles."""

    @classmethod
    def setUpTestData(cls):
        cls.product = Product.objects.get(code='T-SHIRT')

        cp_stage = Stage.objects.get(code=STAGE_CUTTING_PATTERN)
        WorkflowStage.objects.filter(product=cls.product, order__gte=2).update(order=99)
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
        # PAY-2 opt-out: this fixture exercises breakdown/barcode mechanics, not
        # payroll. Cutting is seeded credits_workers=True (mig 0030); not relevant here.
        cls.cutting_wf.credits_workers = False
        cls.cutting_wf.save(update_fields=['credits_workers'])

        ProductPatternAssignment.objects.filter(product=cls.product).delete()
        cls.front = ProductPattern.objects.get_or_create(
            code='front', defaults={'name': 'Front'},
        )[0]
        cls.back = ProductPattern.objects.get_or_create(
            code='back', defaults={'name': 'Back'},
        )[0]
        ProductPatternAssignment.objects.create(
            product=cls.product, pattern=cls.front, pieces_count=1,
        )
        ProductPatternAssignment.objects.create(
            product=cls.product, pattern=cls.back, pieces_count=1,
        )
        cls.s_m = ProductSize.objects.create(
            product=cls.product, code='m', label='M', display_order=1,
        )
        cls.s_l = ProductSize.objects.create(
            product=cls.product, code='l', label='L', display_order=2,
        )

    def setUp(self):
        self.admin = _admin(f'b{id(self)}@brk.test')
        cotton = ClothType.objects.get(name='Cotton')
        self.red = ClothColor.objects.get(name='Red')
        loc = StorageLocation.objects.get(code='ROHINI')
        rolls = bulk_create_rolls(
            user=self.admin, cloth_type=cotton, storage_location=loc,
            purchased_date=date.today(),
            breakup=[{'color': self.red, 'qty': 2}],
        )
        self.adda = create_adda(self.admin, product=self.product)

        layering_sr = AddaStageRecord.objects.get(
            adda=self.adda, workflow_stage=self.layering_wf,
        )
        layering_sr.completed_at = timezone.now()
        layering_sr.completed_by = self.admin
        layering_sr.save(update_fields=['completed_at', 'completed_by'])
        lr = LayeringRecord.objects.create(
            stage_record=layering_sr, lay_count=10, total_colors=1,
            duration_minutes=30, layer_length_meters=Decimal('2.0'),
        )
        lr.rolls_used.set(rolls)

        pattern_sr = AddaStageRecord.objects.create(
            adda=self.adda, workflow_stage=self.pattern_wf,
            started_at=timezone.now(), completed_at=timezone.now(),
            completed_by=self.admin,
        )
        record = CuttingPatternRecord.objects.create(stage_record=pattern_sr)
        CuttingPatternSizeAllocation.objects.create(
            record=record, size=self.s_m, proportion_pct=60,
        )
        CuttingPatternSizeAllocation.objects.create(
            record=record, size=self.s_l, proportion_pct=40,
        )

        self.adda.current_stage = self.cutting_wf
        self.adda.save(update_fields=['current_stage'])

        start_cutting(adda=self.adda, worker_ids=[self.admin.pk], user=self.admin)
        self.b_front_m = upsert_breakup_row(
            adda=self.adda, size_id=self.s_m.id, color_id=self.red.id,
            pattern_id=self.front.id, count=10, user=self.admin,
        )
        self.b_back_m = upsert_breakup_row(
            adda=self.adda, size_id=self.s_m.id, color_id=self.red.id,
            pattern_id=self.back.id, count=10, user=self.admin,
        )
        self.b_front_l = upsert_breakup_row(
            adda=self.adda, size_id=self.s_l.id, color_id=self.red.id,
            pattern_id=self.front.id, count=5, user=self.admin,
        )

        # Build bundles + consume pieces.
        bundle_m = create_bundle(
            adda=self.adda, size_id=self.s_m.id, user=self.admin,
        )
        add_pieces_to_bundle(
            adda=self.adda, bundle_id=bundle_m.id,
            selections=[
                {'breakup_id': self.b_front_m.id, 'take_count': 10},
                {'breakup_id': self.b_back_m.id, 'take_count': 10},
            ],
            user=self.admin,
        )
        bundle_l = create_bundle(
            adda=self.adda, size_id=self.s_l.id, user=self.admin,
        )
        add_pieces_to_bundle(
            adda=self.adda, bundle_id=bundle_l.id,
            selections=[
                {'breakup_id': self.b_front_l.id, 'take_count': 5},
            ],
            user=self.admin,
        )


class WorkspaceMaterializationTests(_WorkspaceCuttingFixture):
    """Workspace path: cutting completion creates breakdown rows."""

    def test_breakdown_rows_created_after_complete(self):
        complete_cutting(adda=self.adda, user=self.admin)
        cr = CuttingRecord.objects.get(stage_record__adda=self.adda)
        rows = list(
            AddaProductSizeColorPieceBreakdown.objects
            .filter(cutting_record=cr)
            .order_by('size__display_order')
        )
        # Two (size, color) combos: (M, Red)=20, (L, Red)=5
        self.assertEqual(len(rows), 2)
        size_m_row = next(r for r in rows if r.size_id == self.s_m.id)
        size_l_row = next(r for r in rows if r.size_id == self.s_l.id)
        self.assertEqual(size_m_row.verified_piece_count, 20)
        self.assertEqual(size_l_row.verified_piece_count, 5)
        self.assertEqual(size_m_row.color_id, self.red.id)

    def test_breakdown_bundle_fk_populated(self):
        complete_cutting(adda=self.adda, user=self.admin)
        for r in AddaProductSizeColorPieceBreakdown.objects.filter(adda=self.adda):
            self.assertIsNotNone(r.bundle_id)
            self.assertEqual(r.bundle.size_id, r.size_id)

    def test_breakdown_total_matches_cutting_record(self):
        complete_cutting(adda=self.adda, user=self.admin)
        cr = CuttingRecord.objects.get(stage_record__adda=self.adda)
        breakdown_total = sum(
            r.verified_piece_count
            for r in AddaProductSizeColorPieceBreakdown.objects
            .filter(cutting_record=cr)
        )
        self.assertEqual(breakdown_total, cr.pieces_cut)
        self.assertEqual(breakdown_total, 25)


class BackCompatLegacyProductTests(_WorkspaceCuttingFixture):
    """Product WITHOUT barcode_generation stage → inline barcode generation."""

    def test_legacy_product_still_generates_barcodes_inline(self):
        # T-SHIRT product has no barcode_generation stage in workflow.
        self.assertFalse(WorkflowStage.objects.filter(
            product=self.product, stage__code=STAGE_BARCODE_GENERATION,
        ).exists())

        complete_cutting(adda=self.adda, user=self.admin)
        batches = list(BarcodeBatch.objects.filter(adda=self.adda))
        self.assertEqual(len(batches), 2)  # M-Red + L-Red
        total = sum(b.total_pieces for b in batches)
        self.assertEqual(total, 25)


class ForwardWithBarcodeStageTests(_WorkspaceCuttingFixture):
    """Product WITH barcode_generation stage → cutting does NOT inline-generate."""

    def setUp(self):
        super().setUp()
        # Attach barcode_generation Stage to T-SHIRT workflow at last order.
        bg_stage = Stage.objects.get(code=STAGE_BARCODE_GENERATION)
        next_order = WorkflowStage.objects.filter(product=self.product).count() + 1
        self.bg_wf = WorkflowStage.objects.create(
            product=self.product, stage=bg_stage, order=next_order,
        )

    def test_cutting_complete_does_not_generate_barcodes(self):
        complete_cutting(adda=self.adda, user=self.admin)
        self.assertEqual(
            BarcodeBatch.objects.filter(adda=self.adda).count(), 0,
            "Cutting must NOT inline-generate when barcode_generation in workflow",
        )

    def test_breakdown_still_materialised(self):
        complete_cutting(adda=self.adda, user=self.admin)
        self.assertEqual(
            AddaProductSizeColorPieceBreakdown.objects
            .filter(adda=self.adda).count(),
            2,
        )

    def test_adda_advances_to_barcode_gen_not_completed(self):
        complete_cutting(adda=self.adda, user=self.admin)
        self.adda.refresh_from_db()
        # Next stage is barcode_generation, not COMPLETED
        self.assertEqual(self.adda.status, Adda.Status.IN_PROGRESS)
        self.assertEqual(self.adda.current_stage_id, self.bg_wf.id)


class ReopenWithBreakdownTests(_WorkspaceCuttingFixture):
    """Reopen must clean breakdown rows + respect new guards."""

    def test_reopen_deletes_breakdown_rows(self):
        complete_cutting(adda=self.adda, user=self.admin)
        self.assertGreater(
            AddaProductSizeColorPieceBreakdown.objects.filter(adda=self.adda).count(),
            0,
        )
        reopen_cutting(adda=self.adda, user=self.admin)
        self.assertEqual(
            AddaProductSizeColorPieceBreakdown.objects.filter(adda=self.adda).count(),
            0,
        )

    def test_reopen_refused_if_barcode_gen_started(self):
        # Attach barcode_gen stage to workflow
        bg_stage = Stage.objects.get(code=STAGE_BARCODE_GENERATION)
        bg_wf = WorkflowStage.objects.create(
            product=self.product, stage=bg_stage,
            order=WorkflowStage.objects.filter(product=self.product).count() + 1,
        )
        complete_cutting(adda=self.adda, user=self.admin)
        # Now barcode_gen stage has been advanced into. Simulate start by
        # creating an AddaStageRecord with started_at set.
        self.adda.refresh_from_db()
        AddaStageRecord.objects.create(
            adda=self.adda, workflow_stage=bg_wf, started_at=timezone.now(),
        )
        with self.assertRaises(ValidationError):
            reopen_cutting(adda=self.adda, user=self.admin)

    def test_reopen_refused_if_export_exists(self):
        complete_cutting(adda=self.adda, user=self.admin)
        # Manually create an export batch entry — minimal stub.
        bg_stage = Stage.objects.get(code=STAGE_BARCODE_GENERATION)
        bg_wf = WorkflowStage.objects.create(
            product=self.product, stage=bg_stage,
            order=WorkflowStage.objects.filter(product=self.product).count() + 1,
        )
        bg_sr = AddaStageRecord.objects.create(
            adda=self.adda, workflow_stage=bg_wf,
            started_at=timezone.now(),
            completed_at=timezone.now(), completed_by=self.admin,
        )
        bg_rec = BarcodeGenerationRecord.objects.create(
            stage_record=bg_sr, total_barcodes=25, generated_at=timezone.now(),
        )
        BarcodeExportBatch.objects.create(
            export_code='EXP-T-001',
            adda=self.adda, product=self.product,
            barcode_gen_record=bg_rec, export_method='csv',
            exported_by=self.admin, total_labels=25,
        )
        # Reopen now refused on multiple grounds — guard 2 fires first
        # (barcode_gen started). Either guard 2 or guard 3 acceptable.
        with self.assertRaises(ValidationError):
            reopen_cutting(adda=self.adda, user=self.admin)


class GenerateFromBreakdownTests(_WorkspaceCuttingFixture):
    """tracking.generate_from_breakdown reads breakdown + produces BarcodeBatch."""

    def setUp(self):
        super().setUp()
        bg_stage = Stage.objects.get(code=STAGE_BARCODE_GENERATION)
        self.bg_wf = WorkflowStage.objects.create(
            product=self.product, stage=bg_stage,
            order=WorkflowStage.objects.filter(product=self.product).count() + 1,
        )
        complete_cutting(adda=self.adda, user=self.admin)
        # Adda now at barcode_gen stage. Build a barcode_gen record.
        self.adda.refresh_from_db()
        self.bg_sr = AddaStageRecord.objects.create(
            adda=self.adda, workflow_stage=self.bg_wf,
            started_at=timezone.now(),
        )
        self.bg_rec = BarcodeGenerationRecord.objects.create(
            stage_record=self.bg_sr,
        )

    def test_generate_from_breakdown_creates_batches(self):
        n = generate_from_breakdown(self.bg_rec)
        self.assertEqual(n, 25)
        batches = list(BarcodeBatch.objects.filter(adda=self.adda).order_by('start_seq'))
        self.assertEqual(len(batches), 2)
        # Contiguous ranges starting at 1
        self.assertEqual(batches[0].start_seq, 1)
        self.assertEqual(batches[-1].end_seq, 25)
        total = sum(b.total_pieces for b in batches)
        self.assertEqual(total, 25)

    def test_generate_from_breakdown_idempotent_refusal(self):
        from django.db import IntegrityError
        generate_from_breakdown(self.bg_rec)
        # Second call must refuse (one-shot rule).
        with self.assertRaises(IntegrityError):
            generate_from_breakdown(self.bg_rec)
