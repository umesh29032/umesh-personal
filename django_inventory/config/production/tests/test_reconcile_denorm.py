"""P5.3 / DM-4: denormalized-counter reconciliation (read-only verifier)."""
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from production.models import (
    Adda, AddaStageRecord, CuttingPieceBreakup, CuttingRecord, Product,
    ProductPattern, ProductSize, Stage, WorkflowStage,
)
from production.services.reconciliation_service import reconcile_denorm
from raw_materials.models import ClothColor


class DenormReconciliationTest(TestCase):
    def setUp(self):
        self.product = Product.objects.create(code='RD', name='RD Product')
        cut = Stage.objects.get_or_create(code='cutting', defaults={'name': 'Cutting'})[0]
        self.ws = WorkflowStage.objects.create(
            product=self.product, stage=cut, order=1, cost_rate=Decimal('0'))
        self.adda = Adda.objects.create(code='RD-001', product=self.product)
        self.sr = AddaStageRecord.objects.create(
            adda=self.adda, workflow_stage=self.ws,
            started_at=timezone.now(), completed_at=timezone.now())
        self.size = ProductSize.objects.create(
            product=self.product, code='m', label='M', display_order=1)
        self.color = ClothColor.objects.get_or_create(
            name='Red', defaults={'hex_code': '#c0392b'})[0]
        self.pattern = ProductPattern.objects.create(code='rd-pat', name='RD Pattern')

    def _cutting(self, pieces_cut, breakup_count):
        cr = CuttingRecord.objects.create(stage_record=self.sr, pieces_cut=pieces_cut)
        CuttingPieceBreakup.objects.create(
            cutting_record=cr, size=self.size, color=self.color,
            pattern=self.pattern, count=breakup_count)
        return cr

    def test_clean_when_counter_matches_source(self):
        self._cutting(pieces_cut=7, breakup_count=7)
        self.assertEqual(reconcile_denorm(), [])

    def test_detects_pieces_cut_drift(self):
        cr = self._cutting(pieces_cut=10, breakup_count=7)   # drift: 10 stored, source 7
        mismatches = reconcile_denorm()
        self.assertEqual(len(mismatches), 1)
        m = mismatches[0]
        self.assertEqual(m['model'], 'CuttingRecord')
        self.assertEqual(m['pk'], cr.pk)
        self.assertEqual(m['field'], 'pieces_cut')
        self.assertEqual(m['stored'], 10)
        self.assertEqual(m['source'], 7)
        self.assertEqual(m['adda'], 'RD-001')

    def test_empty_db_is_clean(self):
        self.assertEqual(reconcile_denorm(), [])
