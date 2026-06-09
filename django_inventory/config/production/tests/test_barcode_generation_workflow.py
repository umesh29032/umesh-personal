"""PR-C tests — Barcode Generation stage end-to-end workflow.

YEH FILE KYU HAI?
─────────────────
PR-C 2026-05-29: barcode generation = standalone stage. Cutting completes
+ materializes breakdown; bg stage consumes breakdown + generates barcodes;
complete validates count match + advances.

Coverage:
  • start_barcode_generation requires mgmt
  • start creates AddaStageRecord with workers + BarcodeGenerationRecord
  • generate_barcodes creates BarcodeBatch rows from breakdown
  • generate_barcodes one-shot (second call raises)
  • complete refuses if not generated
  • complete refuses on count mismatch (manual injection)
  • complete advances Adda
  • complete to COMPLETED if last stage in workflow
  • reopen refused if any scanned barcode
  • reopen refused if any export exists
  • reopen clears generated_at + deletes BarcodeBatch rows
"""
from datetime import date
from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase
from django.utils import timezone

from accounts.models import Skill, User
from inventory.models import Role
from production.constants import (
    STAGE_BARCODE_GENERATION, STAGE_CUTTING, STAGE_CUTTING_PATTERN,
    STAGE_LAYERING,
)
from production.models import (
    Adda, AddaStageRecord, CuttingPatternRecord,
    CuttingPatternSizeAllocation, LayeringRecord,
    Product, ProductPattern, ProductPatternAssignment,
    ProductSize, Stage, WorkflowStage,
)
from production.services import (
    add_pieces_to_bundle, complete_barcode_generation, complete_cutting,
    create_adda, create_bundle, generate_barcodes, reopen_barcode_generation,
    start_barcode_generation, start_cutting, upsert_breakup_row,
)
from raw_materials.models import ClothColor, ClothType, StorageLocation
from raw_materials.services import bulk_create_rolls
from tracking.models import BarcodeBatch, BarcodeExportBatch, BatchBarcode


def _admin(email):
    role = Role.objects.get(code='super_admin')
    u = User.objects.create_user(
        email=email, password='x', is_superuser=True, is_staff=True,
    )
    u.role = role
    u.save()
    for s in ('cutting_master', 'cutting_master_helper'):
        u.skills.add(Skill.objects.get(name=s))
    return u


def _karigar(email):
    role = Role.objects.get(code='worker')
    u = User.objects.create_user(email=email, password='x')
    u.role = role
    u.save()
    return u


class _BgWorkflowFixture(TestCase):
    """T-SHIRT with cutting completed AND barcode_generation in workflow.

    Adda is positioned at barcode_generation stage with breakdown rows ready.
    """

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

        # Attach barcode_generation Stage to T-SHIRT workflow as last stage
        bg_stage = Stage.objects.get(code=STAGE_BARCODE_GENERATION)
        max_order = WorkflowStage.objects.filter(product=cls.product).count()
        cls.bg_wf, _ = WorkflowStage.objects.get_or_create(
            product=cls.product, stage=bg_stage,
            defaults={'order': max_order + 1},
        )

        ProductPatternAssignment.objects.filter(product=cls.product).delete()
        cls.front = ProductPattern.objects.get_or_create(
            code='front', defaults={'name': 'Front'},
        )[0]
        ProductPatternAssignment.objects.create(
            product=cls.product, pattern=cls.front, pieces_count=1,
        )

        cls.s_m = ProductSize.objects.create(
            product=cls.product, code='m', label='M', display_order=1,
        )

    def setUp(self):
        self.admin = _admin(f'a{id(self)}@bg.test')
        cotton = ClothType.objects.get(name='Cotton')
        self.red = ClothColor.objects.get(name='Red')
        loc = StorageLocation.objects.get(code='ROHINI')
        rolls = bulk_create_rolls(
            user=self.admin, cloth_type=cotton, storage_location=loc,
            purchased_date=date.today(),
            breakup=[{'color': self.red, 'qty': 1}],
        )
        self.adda = create_adda(self.admin, product=self.product)

        layering_sr = AddaStageRecord.objects.get(
            adda=self.adda, workflow_stage=self.layering_wf,
        )
        layering_sr.completed_at = timezone.now()
        layering_sr.completed_by = self.admin
        layering_sr.save(update_fields=['completed_at', 'completed_by'])
        lr = LayeringRecord.objects.create(
            stage_record=layering_sr, lay_count=5, total_colors=1,
            duration_minutes=20, layer_length_meters=Decimal('1.5'),
        )
        lr.rolls_used.set(rolls)

        # Pattern stage completed with 100% size_m allocation
        pattern_sr = AddaStageRecord.objects.create(
            adda=self.adda, workflow_stage=self.pattern_wf,
            started_at=timezone.now(), completed_at=timezone.now(),
            completed_by=self.admin,
        )
        rec = CuttingPatternRecord.objects.create(stage_record=pattern_sr)
        CuttingPatternSizeAllocation.objects.create(
            record=rec, size=self.s_m, proportion_pct=100,
        )

        self.adda.current_stage = self.cutting_wf
        self.adda.save(update_fields=['current_stage'])
        start_cutting(adda=self.adda, worker_ids=[self.admin.pk], user=self.admin)
        b_front_m = upsert_breakup_row(
            adda=self.adda, size_id=self.s_m.id, color_id=self.red.id,
            pattern_id=self.front.id, count=20, user=self.admin,
        )
        bundle = create_bundle(
            adda=self.adda, size_id=self.s_m.id, user=self.admin,
        )
        add_pieces_to_bundle(
            adda=self.adda, bundle_id=bundle.id,
            selections=[{'breakup_id': b_front_m.id, 'take_count': 20}],
            user=self.admin,
        )
        complete_cutting(adda=self.adda, user=self.admin)
        self.adda.refresh_from_db()
        # Adda now at barcode_generation stage (cutting completed; bg in workflow)
        self.assertEqual(self.adda.current_stage_id, self.bg_wf.id)


class StartBarcodeGenerationTests(_BgWorkflowFixture):

    def test_start_requires_management(self):
        worker = _karigar(f'k{id(self)}@bg.test')
        with self.assertRaises(PermissionDenied):
            start_barcode_generation(
                adda=self.adda, worker_ids=[worker.pk], user=worker,
            )

    def test_start_creates_sr_and_record(self):
        sr = start_barcode_generation(
            adda=self.adda, worker_ids=[self.admin.pk], user=self.admin,
        )
        self.assertIsNotNone(sr.started_at)
        self.assertIn(self.admin, sr.workers.all())
        # BarcodeGenerationRecord auto-created
        self.assertIsNotNone(getattr(sr, 'barcode_generation', None))


class GenerateBarcodesTests(_BgWorkflowFixture):

    def setUp(self):
        super().setUp()
        start_barcode_generation(
            adda=self.adda, worker_ids=[self.admin.pk], user=self.admin,
        )

    def test_generate_creates_batches_from_breakdown(self):
        rec = generate_barcodes(adda=self.adda, user=self.admin)
        self.assertEqual(rec.total_barcodes, 20)
        self.assertIsNotNone(rec.generated_at)
        batches = list(BarcodeBatch.objects.filter(adda=self.adda))
        self.assertEqual(len(batches), 1)
        self.assertEqual(batches[0].total_pieces, 20)
        self.assertEqual(batches[0].size_id, self.s_m.id)
        self.assertEqual(batches[0].color_id, self.red.id)

    def test_generate_one_shot_refuses_second_call(self):
        generate_barcodes(adda=self.adda, user=self.admin)
        with self.assertRaises(ValidationError):
            generate_barcodes(adda=self.adda, user=self.admin)


class CompleteBarcodeGenerationTests(_BgWorkflowFixture):

    def setUp(self):
        super().setUp()
        start_barcode_generation(
            adda=self.adda, worker_ids=[self.admin.pk], user=self.admin,
        )

    def test_complete_refuses_before_generate(self):
        with self.assertRaises(ValidationError):
            complete_barcode_generation(adda=self.adda, user=self.admin)

    def test_complete_advances_to_completed_when_last_stage(self):
        generate_barcodes(adda=self.adda, user=self.admin)
        complete_barcode_generation(adda=self.adda, user=self.admin)
        self.adda.refresh_from_db()
        self.assertEqual(self.adda.status, Adda.Status.COMPLETED)
        self.assertIsNone(self.adda.current_stage)

    def test_complete_refuses_on_count_mismatch(self):
        generate_barcodes(adda=self.adda, user=self.admin)
        # Simulate counter drift on the generation-record denorm so it disagrees
        # with the actual barcode batches. (A batch's total_pieces is now
        # DB-constrained to its seq-range width — tracking_batch_pieces_consistent
        # — so we drift the record side instead, which is a reachable state.)
        sr = AddaStageRecord.objects.get(adda=self.adda, workflow_stage=self.bg_wf)
        rec = sr.barcode_generation
        rec.total_barcodes = rec.total_barcodes + 1
        rec.save(update_fields=['total_barcodes'])
        with self.assertRaises(ValidationError):
            complete_barcode_generation(adda=self.adda, user=self.admin)


class ReopenBarcodeGenerationTests(_BgWorkflowFixture):

    def setUp(self):
        super().setUp()
        start_barcode_generation(
            adda=self.adda, worker_ids=[self.admin.pk], user=self.admin,
        )
        generate_barcodes(adda=self.adda, user=self.admin)
        complete_barcode_generation(adda=self.adda, user=self.admin)
        self.adda.refresh_from_db()

    def test_reopen_clears_artefacts(self):
        # Re-advance Adda to bg stage for reopen test
        # (after complete, current_stage = None since bg was last stage)
        reopen_barcode_generation(adda=self.adda, user=self.admin)
        self.adda.refresh_from_db()
        self.assertEqual(self.adda.current_stage_id, self.bg_wf.id)
        self.assertEqual(self.adda.status, Adda.Status.IN_PROGRESS)
        # Barcodes deleted
        self.assertEqual(
            BarcodeBatch.objects.filter(adda=self.adda).count(), 0,
        )
        # Record cleared
        sr = AddaStageRecord.objects.get(adda=self.adda, workflow_stage=self.bg_wf)
        rec = sr.barcode_generation
        self.assertIsNone(rec.generated_at)
        self.assertEqual(rec.total_barcodes, 0)

    def test_reopen_refused_if_scanned(self):
        # Manually create a BatchBarcode (simulating scan)
        batch = BarcodeBatch.objects.filter(adda=self.adda).first()
        BatchBarcode.objects.create(
            adda=self.adda, batch=batch, piece_seq=1,
            value=f'{self.adda.code}-0001',
            size=batch.size, color=batch.color,
        )
        with self.assertRaises(ValidationError):
            reopen_barcode_generation(adda=self.adda, user=self.admin)

    def test_reopen_refused_if_export_exists(self):
        # Create an export batch
        sr = AddaStageRecord.objects.get(adda=self.adda, workflow_stage=self.bg_wf)
        rec = sr.barcode_generation
        BarcodeExportBatch.objects.create(
            export_code='EXP-RO-001',
            adda=self.adda, product=self.product,
            barcode_gen_record=rec, export_method='csv',
            exported_by=self.admin, total_labels=20,
        )
        with self.assertRaises(ValidationError):
            reopen_barcode_generation(adda=self.adda, user=self.admin)


class WorkspaceViewTests(_BgWorkflowFixture):
    """Smoke test — workspace renders without errors."""

    def setUp(self):
        super().setUp()
        from django.test import Client
        self.client = Client()
        self.client.force_login(self.admin)

    def test_workspace_renders(self):
        resp = self.client.get(
            f'/production/addas/{self.adda.code}/barcode-gen/',
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'production/barcode_gen_workspace.html')

    def test_embedded_panel_renders(self):
        resp = self.client.get(
            f'/production/addas/{self.adda.code}/stage/barcode_generation/?embedded=1',
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'production/stage_panel_embedded.html')
