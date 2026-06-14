"""Foundation S4 / Phase 2 — StagePoolSnapshot + handler-dispatched pool_good (Option B).

Locked: Cutting's pool good = AddaProductSizeColorPieceBreakdown (single source of truth,
NOT duplicated into StagePoolSnapshot). StagePoolSnapshot is materialised (write-once) only
for downstream pool-producing stages. Pool source is handler-dispatched — no stage-name
conditionals. Pool-only — touches no settlement/costing.
"""
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from accounts.models import User
from inventory.models import Role
from production.constants import ALLOC_DIM_NONE, ALLOC_DIM_QUANTITY, STAGE_CUTTING
from production.models import (
    Adda, AddaProductSizeColorPieceBreakdown, AddaStageRecord, Product, ProductSize,
    Stage, StagePoolSnapshot, WorkflowStage, WorkerStageContribution, WorkerStageTask,
)
from production.services import pool_service
from raw_materials.models import ClothColor


def _worker(email='s4p-w@test'):
    u = User.objects.create_user(email=email, password='x')
    u.role = Role.objects.get(code='worker'); u.save()
    return u


class CuttingPoolFromBreakdownTests(TestCase):
    """pool_good(cutting) reads APSCPB — never StagePoolSnapshot, never cost_quantity_snapshot."""
    def test_cutting_pool_good_sums_breakdown_by_color_size(self):
        from production.models import CuttingRecord
        product = Product.objects.create(code='S4PC', name='S4PC')
        stage, _ = Stage.objects.get_or_create(code=STAGE_CUTTING, defaults={'name': 'Cutting'})
        ws = WorkflowStage.objects.create(product=product, stage=stage, order=1, cost_rate=Decimal('2'))
        adda = Adda.objects.create(code='S4P-C', product=product, status=Adda.Status.IN_PROGRESS)
        sr = AddaStageRecord.objects.create(adda=adda, workflow_stage=ws,
                                            started_at=timezone.now(), completed_at=timezone.now())
        cr = CuttingRecord.objects.create(stage_record=sr, pieces_cut=80)
        red = ClothColor.objects.get_or_create(name='S4P Red')[0]
        sm = ProductSize.objects.create(product=product, code='m', label='M', display_order=1)
        sl = ProductSize.objects.create(product=product, code='l', label='L', display_order=2)
        actor = _worker('s4p-cut@test')
        # APSCPB is unique per (cutting_record, size, color) → one row per (colour,size).
        AddaProductSizeColorPieceBreakdown.objects.create(
            adda=adda, product=product, cutting_record=cr, size=sm, color=red,
            verified_piece_count=50, created_by=actor)
        AddaProductSizeColorPieceBreakdown.objects.create(
            adda=adda, product=product, cutting_record=cr, size=sl, color=red,
            verified_piece_count=30, created_by=actor)
        good = pool_service.pool_good(sr)
        self.assertEqual(good, {(red.pk, sm.pk): Decimal('50'), (red.pk, sl.pk): Decimal('30')})
        # And cutting writes NO StagePoolSnapshot row (APSCPB is the source).
        self.assertEqual(pool_service.materialize_stage_pool(sr), 0)
        self.assertFalse(StagePoolSnapshot.objects.filter(stage_record=sr).exists())


class DownstreamSnapshotTests(TestCase):
    """A downstream pool-producing stage (base handler, QUANTITY grain) materialises
    StagePoolSnapshot from Σ WorkerStageContribution.good_quantity; pool_good reads it."""
    def _quantity_stage_with_good(self, goods):
        # 'layering' code → base handler (no pool override); force QUANTITY grain to make
        # it a synthetic downstream pool-producing stage.
        product = Product.objects.create(code='S4PD', name='S4PD')
        stage, _ = Stage.objects.get_or_create(code='layering', defaults={'name': 'Layering'})
        ws = WorkflowStage.objects.create(product=product, stage=stage, order=1,
                                          cost_rate=Decimal('2'), allocation_dimensions=ALLOC_DIM_QUANTITY)
        adda = Adda.objects.create(code='S4P-D', product=product, status=Adda.Status.IN_PROGRESS)
        sr = AddaStageRecord.objects.create(adda=adda, workflow_stage=ws,
                                            started_at=timezone.now(), completed_at=timezone.now())
        w = _worker('s4p-d@test')
        task = WorkerStageTask.objects.create(stage_record=sr, worker=w,
                                              status=WorkerStageTask.Status.COMPLETED)
        for g in goods:
            WorkerStageContribution.objects.create(
                task=task, reported_quantity=Decimal(g), good_quantity=Decimal(g))
        return sr

    def test_materialize_then_pool_good_scalar(self):
        sr = self._quantity_stage_with_good(['10', '20'])
        self.assertEqual(pool_service.materialize_stage_pool(sr), 1)   # one scalar row
        row = StagePoolSnapshot.objects.get(stage_record=sr)
        self.assertEqual(row.good, Decimal('30'))                      # 10 + 20
        self.assertIsNone(row.color_id); self.assertIsNone(row.size_id)
        self.assertEqual(pool_service.pool_good(sr), {(None, None): Decimal('30')})

    def test_materialize_is_write_once(self):
        sr = self._quantity_stage_with_good(['5'])
        self.assertEqual(pool_service.materialize_stage_pool(sr), 1)
        self.assertEqual(pool_service.materialize_stage_pool(sr), 0)   # idempotent
        self.assertEqual(StagePoolSnapshot.objects.filter(stage_record=sr).count(), 1)

    def test_clear_then_refreeze(self):
        sr = self._quantity_stage_with_good(['7'])
        pool_service.materialize_stage_pool(sr)
        self.assertEqual(pool_service.clear_stage_pool(sr), 1)         # reopen clears
        self.assertEqual(pool_service.pool_good(sr), {})
        self.assertEqual(pool_service.materialize_stage_pool(sr), 1)   # refreeze


class NoneStageTests(TestCase):
    def test_none_grain_stage_materializes_nothing(self):
        product = Product.objects.create(code='S4PN', name='S4PN')
        stage, _ = Stage.objects.get_or_create(code='layering', defaults={'name': 'Layering'})
        ws = WorkflowStage.objects.create(product=product, stage=stage, order=1,
                                          cost_rate=Decimal('2'), allocation_dimensions=ALLOC_DIM_NONE)
        adda = Adda.objects.create(code='S4P-N', product=product, status=Adda.Status.IN_PROGRESS)
        sr = AddaStageRecord.objects.create(adda=adda, workflow_stage=ws,
                                            started_at=timezone.now(), completed_at=timezone.now())
        self.assertEqual(pool_service.materialize_stage_pool(sr), 0)   # pre-piece → no pool
        self.assertEqual(pool_service.pool_good(sr), {})
