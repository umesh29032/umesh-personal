"""PR-D tests — barcode export service + views.

YEH FILE KYU HAI?
─────────────────
PR-D 2026-05-29: BarcodeExportBatch manifest + CSV/XLSX/PDF generation
+ re-download + gate (barcode_generation stage must be complete).

Coverage:
  • CSV bytes contain expected headers + rows
  • XLSX bytes are valid (openpyxl can re-open)
  • PDF bytes start with %PDF- header
  • Export refused before barcode_generation stage complete (ValidationError)
  • Export creates BarcodeExportBatch manifest row
  • export_code sequencer increments
  • Re-download by export_code returns same content (idempotent regen)
  • View triggers (POST) return file Content-Disposition + correct content-type
  • ExportListView lists recent exports
"""
from datetime import date
from decimal import Decimal
import io

from django.core.exceptions import ValidationError
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Skill, User
from inventory.models import Role
from production.constants import (
    STAGE_BARCODE_GENERATION, STAGE_CUTTING, STAGE_CUTTING_PATTERN,
    STAGE_LAYERING,
)
from production.models import (
    AddaStageRecord, CuttingPatternRecord, CuttingPatternSizeAllocation, LayeringRecord,
    Product, ProductPattern, ProductPatternAssignment, ProductSize,
    Stage, WorkflowStage,
)
from production.services import (
    add_pieces_to_bundle, complete_barcode_generation, complete_cutting,
    create_adda, create_bundle, generate_barcodes, start_barcode_generation,
    start_cutting, upsert_breakup_row,
)
from raw_materials.models import ClothColor, ClothType, StorageLocation
from raw_materials.services import bulk_create_rolls
from production.stages.barcode_generation.export_service import (
    generate_csv, generate_pdf_summary, generate_xlsx, regenerate_for_export,
)


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


def _user_with_role(email, role_code):
    """Plain user carrying a seeded Role — for V1.1 Item 3 permission tests."""
    u = User.objects.create_user(email=email, password='x')
    u.role = Role.objects.get(code=role_code)
    u.save()
    return u


class _ExportFixture(TestCase):
    """Adda with barcode_generation stage COMPLETED + 20 barcodes ready."""

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
        # PAY-2 opt-out: this fixture exercises barcode-export mechanics, not payroll.
        # Cutting is seeded credits_workers=True (mig 0030); not relevant here.
        cls.cutting_wf.credits_workers = False
        cls.cutting_wf.save(update_fields=['credits_workers'])
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
        self.admin = _admin(f'ex{id(self)}@bg.test')
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
        b = upsert_breakup_row(
            adda=self.adda, size_id=self.s_m.id, color_id=self.red.id,
            pattern_id=self.front.id, count=20, user=self.admin,
        )
        # GAP-5: completion (the join) first; bundling follows post-join.
        complete_cutting(adda=self.adda, user=self.admin)
        bundle = create_bundle(
            adda=self.adda, size_id=self.s_m.id, user=self.admin,
        )
        add_pieces_to_bundle(
            adda=self.adda, bundle_id=bundle.id,
            selections=[{'breakup_id': b.id, 'take_count': 20}],
            user=self.admin,
        )
        self.adda.refresh_from_db()


class GateTests(_ExportFixture):
    """Service-layer gate: barcode_generation stage must be complete."""

    def test_export_refused_before_barcode_stage_started(self):
        with self.assertRaises(ValidationError):
            generate_csv(self.adda, self.admin)
        with self.assertRaises(ValidationError):
            generate_xlsx(self.adda, self.admin)
        with self.assertRaises(ValidationError):
            generate_pdf_summary(self.adda, self.admin)

    def test_export_refused_when_started_but_not_complete(self):
        start_barcode_generation(
            adda=self.adda, worker_ids=[self.admin.pk], user=self.admin,
        )
        generate_barcodes(adda=self.adda, user=self.admin)
        # NOT yet completed → refuse
        with self.assertRaises(ValidationError):
            generate_csv(self.adda, self.admin)


class _PostCompleteFixture(_ExportFixture):
    """Subclass that completes barcode_generation in setUp — exports allowed."""

    def setUp(self):
        super().setUp()
        start_barcode_generation(
            adda=self.adda, worker_ids=[self.admin.pk], user=self.admin,
        )
        generate_barcodes(adda=self.adda, user=self.admin)
        complete_barcode_generation(adda=self.adda, user=self.admin)
        self.adda.refresh_from_db()


class CsvExportTests(_PostCompleteFixture):

    def test_csv_creates_manifest_and_bytes(self):
        batch, payload = generate_csv(self.adda, self.admin)
        self.assertIsInstance(payload, bytes)
        text = payload.decode('utf-8')
        # Headers row
        self.assertIn('barcode,qr_payload,adda,product,bundle,size,color,piece_seq', text)
        # 20 data rows + 1 header
        self.assertEqual(text.strip().count('\n'), 20)
        # Manifest row stored
        self.assertEqual(batch.total_labels, 20)
        self.assertTrue(batch.export_code.startswith('EXP-'))
        self.assertEqual(batch.export_method, 'csv')


class XlsxExportTests(_PostCompleteFixture):

    def test_xlsx_bytes_valid(self):
        batch, payload = generate_xlsx(self.adda, self.admin)
        self.assertIsInstance(payload, bytes)
        # Re-open with openpyxl to confirm valid xlsx
        from openpyxl import load_workbook
        wb = load_workbook(io.BytesIO(payload), read_only=True)
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
        self.assertEqual(rows[0][0], 'barcode')  # header row
        self.assertEqual(len(rows), 21)  # header + 20 data rows
        self.assertEqual(batch.export_method, 'xlsx')


class PdfExportTests(_PostCompleteFixture):

    def test_pdf_bytes_start_with_pdf_header(self):
        batch, payload = generate_pdf_summary(self.adda, self.admin)
        self.assertIsInstance(payload, bytes)
        self.assertTrue(payload.startswith(b'%PDF-'))
        self.assertEqual(batch.export_method, 'pdf')


class ExportCodeSequencerTests(_PostCompleteFixture):

    def test_code_increments(self):
        b1, _ = generate_csv(self.adda, self.admin)
        b2, _ = generate_csv(self.adda, self.admin)
        b3, _ = generate_xlsx(self.adda, self.admin)
        codes = [b1.export_code, b2.export_code, b3.export_code]
        # All start with same EXP-YYYY- prefix
        prefix = b1.export_code.rsplit('-', 1)[0]
        self.assertTrue(all(c.startswith(prefix) for c in codes))
        # Numeric suffix strictly increasing
        nums = [int(c.rsplit('-', 1)[1]) for c in codes]
        self.assertEqual(nums, sorted(set(nums)))
        self.assertEqual(len(set(codes)), 3)


class ReDownloadTests(_PostCompleteFixture):

    def test_redownload_returns_equivalent_bytes(self):
        batch, original = generate_csv(self.adda, self.admin)
        regenerated = regenerate_for_export(batch, self.admin)
        # Both reference live data; barcodes unchanged → equal content
        self.assertEqual(original, regenerated)


class ViewIntegrationTests(_PostCompleteFixture):

    def setUp(self):
        super().setUp()
        self.client = Client()
        self.client.force_login(self.admin)

    def test_csv_view_returns_csv_download(self):
        resp = self.client.post(
            reverse('tracking:export-csv', args=[self.adda.code]),
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'text/csv; charset=utf-8')
        self.assertIn('attachment', resp['Content-Disposition'])

    def test_xlsx_view_returns_xlsx_download(self):
        resp = self.client.post(
            reverse('tracking:export-xlsx', args=[self.adda.code]),
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn('spreadsheetml', resp['Content-Type'])

    def test_pdf_view_returns_pdf_download(self):
        resp = self.client.post(
            reverse('tracking:export-pdf', args=[self.adda.code]),
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'application/pdf')

    def test_redownload_view_by_export_code(self):
        batch, _ = generate_csv(self.adda, self.admin)
        resp = self.client.get(
            reverse('tracking:export-download', args=[batch.export_code]),
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn('attachment', resp['Content-Disposition'])
        self.assertIn(batch.export_code, resp['Content-Disposition'])

    def test_export_list_view_renders(self):
        generate_csv(self.adda, self.admin)
        generate_xlsx(self.adda, self.admin)
        resp = self.client.get(reverse('tracking:export-list'))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'tracking/export_list.html')
        self.assertEqual(len(resp.context['exports']), 2)

    def test_csv_view_refused_before_bg_complete(self):
        # Fresh fixture — no bg complete
        from production.services import reopen_barcode_generation
        reopen_barcode_generation(adda=self.adda, user=self.admin)
        resp = self.client.post(
            reverse('tracking:export-csv', args=[self.adda.code]),
        )
        self.assertEqual(resp.status_code, 400)


class ExportPermissionTests(_PostCompleteFixture):
    """V1.1 Item 3 (2026-07-12): exports = MANAGEMENT_ROLES only.

    Browser-proven HIGH: worker could GET /tracking/exports/ + POST CSV.
    Root cause: PRODUCTION_ROLES gate (includes worker) — now
    ManagerOrAdminMixin on every export view + service backstop.
    Barcode list/print/scan gates UNTOUCHED (workers legitimately scan).
    """

    def setUp(self):
        super().setUp()
        self.worker = _user_with_role(f'w{id(self)}@perm.test', 'worker')
        self.manager = _user_with_role(f'm{id(self)}@perm.test', 'manager')
        self.client = Client()

    # ── Worker: every export entry point → 403 ────────────────────────────

    def test_worker_export_list_403(self):
        self.client.force_login(self.worker)
        resp = self.client.get(reverse('tracking:export-list'))
        self.assertEqual(resp.status_code, 403)

    def test_worker_export_triggers_403(self):
        self.client.force_login(self.worker)
        for name in ('export-csv', 'export-xlsx', 'export-pdf'):
            resp = self.client.post(
                reverse(f'tracking:{name}', args=[self.adda.code]),
            )
            self.assertEqual(resp.status_code, 403, name)
        # No manifest row was written by any refused trigger.
        from tracking.models import BarcodeExportBatch
        self.assertEqual(BarcodeExportBatch.objects.count(), 0)

    def test_worker_redownload_403(self):
        batch, _ = generate_csv(self.adda, self.admin)
        self.client.force_login(self.worker)
        resp = self.client.get(
            reverse('tracking:export-download', args=[batch.export_code]),
        )
        self.assertEqual(resp.status_code, 403)

    def test_worker_quick_csv_403(self):
        # Legacy no-manifest CSV (tracking:barcode-export) — same bug class.
        self.client.force_login(self.worker)
        resp = self.client.get(
            reverse('tracking:barcode-export', args=[self.adda.code]),
        )
        self.assertEqual(resp.status_code, 403)

    # ── Service backstop (defense-in-depth) ───────────────────────────────

    def test_service_refuses_worker_directly(self):
        from django.core.exceptions import PermissionDenied
        for fn in (generate_csv, generate_xlsx, generate_pdf_summary):
            with self.assertRaises(PermissionDenied):
                fn(self.adda, self.worker)
        batch, _ = generate_csv(self.adda, self.admin)
        with self.assertRaises(PermissionDenied):
            regenerate_for_export(batch, self.worker)

    # ── Manager: everything still works ───────────────────────────────────

    def test_manager_export_list_200(self):
        self.client.force_login(self.manager)
        resp = self.client.get(reverse('tracking:export-list'))
        self.assertEqual(resp.status_code, 200)

    def test_manager_csv_export_200(self):
        self.client.force_login(self.manager)
        resp = self.client.post(
            reverse('tracking:export-csv', args=[self.adda.code]),
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn('attachment', resp['Content-Disposition'])

    def test_manager_quick_csv_200(self):
        self.client.force_login(self.manager)
        resp = self.client.get(
            reverse('tracking:barcode-export', args=[self.adda.code]),
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'text/csv; charset=utf-8')


class FormulaInjectionTests(_PostCompleteFixture):
    """PA-13-6: free-text color/size labels must not become live spreadsheet
    formulas when the CSV/XLSX manifest is opened in Excel/LibreOffice."""

    def test_csv_safe_neutralizes_formula_triggers(self):
        from production.stages.barcode_generation.export_service import _csv_safe
        for bad in ('=HYPERLINK("http://evil","x")', '+1+1', '-2', '@SUM(A1)',
                    '\tred', '\rred'):
            self.assertEqual(_csv_safe(bad), "'" + bad)
        # Safe values untouched.
        self.assertEqual(_csv_safe('Red'), 'Red')
        self.assertEqual(_csv_safe('CR-000001'), 'CR-000001')
        self.assertEqual(_csv_safe(42), 42)

    def test_csv_export_neutralizes_malicious_color_name(self):
        from raw_materials.models import ClothColor
        from production.stages.barcode_generation.export_service import _render_csv_bytes
        # Rename a color used by this Adda's barcodes to a formula payload.
        c = ClothColor.objects.filter(rolls__adda=self.adda).first() or ClothColor.objects.first()
        c.name = '=cmd|calc'
        c.save(update_fields=['name'])
        text = _render_csv_bytes(self.adda).decode('utf-8')
        # The raw formula must NOT appear as a cell start; the neutralized form does.
        self.assertNotIn(',=cmd|calc', text)
        if 'cmd|calc' in text:
            self.assertIn("'=cmd|calc", text)
