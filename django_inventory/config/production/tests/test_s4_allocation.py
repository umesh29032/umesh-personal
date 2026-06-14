"""Foundation S4 / Phase 3 — WorkerStageAllocation + pool draw-down.

WSA = production-truth capacity only (NO money). A consuming stage draws from its nearest
upstream pool source (cutting → APSCPB), aggregated to the consuming grain. Over-allocation
refused (pool integrity, always on); void credits back; reverse-first. Decoupled from
costing/earning/settlement.
"""
from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase
from django.utils import timezone

from accounts.models import User
from inventory.models import Role
from production.constants import (
    ALLOC_DIM_COLOR_SIZE, ALLOC_DIM_NONE, ALLOC_DIM_QUANTITY, STAGE_CUTTING,
)
from production.models import (
    Adda, AddaProductSizeColorPieceBreakdown, AddaStageRecord, CuttingRecord, Product,
    ProductSize, Stage, WorkflowStage, WorkerStageAllocation,
)
from production.services import pool_service
from raw_materials.models import ClothColor


def _user(email, code):
    u = User.objects.create_user(email=email, password='x')
    u.role = Role.objects.get(code=code); u.save()
    return u


class _Base(TestCase):
    def _build(self, *, consuming_grain, cutting_rows, consuming_order=2, gap_none=False):
        """cutting (COLOR_SIZE source, APSCPB) → [optional NONE gap] → consuming stage."""
        self._seq = getattr(self, '_seq', 0) + 1   # unique product code per _build call
        product = Product.objects.create(code=f'S4A{id(self) % 9999}_{self._seq}', name='a')
        cstage, _ = Stage.objects.get_or_create(code=STAGE_CUTTING, defaults={'name': 'Cutting'})
        cws = WorkflowStage.objects.create(product=product, stage=cstage, order=1,
                                           cost_rate=Decimal('2'), allocation_dimensions=ALLOC_DIM_COLOR_SIZE)
        adda = Adda.objects.create(code=f'S4A-{product.code}', product=product, status=Adda.Status.IN_PROGRESS)
        csr = AddaStageRecord.objects.create(adda=adda, workflow_stage=cws,
                                             started_at=timezone.now(), completed_at=timezone.now())
        cr = CuttingRecord.objects.create(stage_record=csr, pieces_cut=sum(r[2] for r in cutting_rows))
        actor = _user(f's4a-mk-{product.code}@t', 'super_admin')
        self.red = ClothColor.objects.get_or_create(name='S4A Red')[0]
        self.m = ProductSize.objects.create(product=product, code='m', label='M', display_order=1)
        for (color, size, n) in cutting_rows:
            AddaProductSizeColorPieceBreakdown.objects.create(
                adda=adda, product=product, cutting_record=cr, color=color, size=size,
                verified_piece_count=n, created_by=actor)
        if gap_none:   # a pre-piece NONE stage between cutting and the consumer
            ns, _ = Stage.objects.get_or_create(code='gap_none', defaults={'name': 'Gap'})
            WorkflowStage.objects.create(product=product, stage=ns, order=2,
                                         cost_rate=Decimal('1'), allocation_dimensions=ALLOC_DIM_NONE)
        sstage, _ = Stage.objects.get_or_create(code='stitching', defaults={'name': 'Stitching'})
        sws = WorkflowStage.objects.create(product=product, stage=sstage, order=consuming_order,
                                           cost_rate=Decimal('2'), allocation_dimensions=consuming_grain)
        ssr = AddaStageRecord.objects.create(adda=adda, workflow_stage=sws, started_at=timezone.now())
        self.mgr = actor
        self.worker = _user(f's4a-w-{product.code}@t', 'worker')
        return csr, ssr


class ColorSizeAllocationTests(_Base):
    def test_color_size_allocation_flow(self):
        csr, ssr = self._build(consuming_grain=ALLOC_DIM_COLOR_SIZE, cutting_rows=[])
        # cutting (red, M) = 50
        AddaProductSizeColorPieceBreakdown.objects.create(
            adda=csr.adda, product=csr.adda.product, cutting_record=csr.cutting,
            color=self.red, size=self.m, verified_piece_count=50, created_by=self.mgr)
        self.assertEqual(pool_service.available(ssr, self.red.pk, self.m.pk), Decimal('50'))
        pool_service.allocate(ssr, self.worker, qty=40, actor=self.mgr,
                                    color_id=self.red.pk, size_id=self.m.pk)
        self.assertEqual(pool_service.available(ssr, self.red.pk, self.m.pk), Decimal('10'))
        with self.assertRaisesMessage(ValidationError, 'available'):
            pool_service.allocate(ssr, self.worker, qty=20, actor=self.mgr,
                                        color_id=self.red.pk, size_id=self.m.pk)

    def test_void_credits_back(self):
        csr, ssr = self._build(consuming_grain=ALLOC_DIM_COLOR_SIZE, cutting_rows=[])
        AddaProductSizeColorPieceBreakdown.objects.create(
            adda=csr.adda, product=csr.adda.product, cutting_record=csr.cutting,
            color=self.red, size=self.m, verified_piece_count=50, created_by=self.mgr)
        wsa = pool_service.allocate(ssr, self.worker, qty=40, actor=self.mgr,
                                          color_id=self.red.pk, size_id=self.m.pk)
        self.assertEqual(pool_service.available(ssr, self.red.pk, self.m.pk), Decimal('10'))
        pool_service.void_allocation(wsa, actor=self.mgr)
        self.assertEqual(pool_service.available(ssr, self.red.pk, self.m.pk), Decimal('50'))
        # reallocate the freed qty
        pool_service.allocate(ssr, self.worker, qty=50, actor=self.mgr,
                                    color_id=self.red.pk, size_id=self.m.pk)
        self.assertEqual(pool_service.available(ssr, self.red.pk, self.m.pk), Decimal('0'))


class QuantityAllocationTests(_Base):
    def test_quantity_consumer_draws_sum_of_cutting(self):
        # consuming QUANTITY draws Σ over all cutting (colour,size): 60 + 40 = 100.
        csr, ssr = self._build(consuming_grain=ALLOC_DIM_QUANTITY, cutting_rows=[])
        sl = ProductSize.objects.create(product=csr.adda.product, code='l', label='L', display_order=2)
        for size, n in ((self.m, 60), (sl, 40)):
            AddaProductSizeColorPieceBreakdown.objects.create(
                adda=csr.adda, product=csr.adda.product, cutting_record=csr.cutting,
                color=self.red, size=size, verified_piece_count=n, created_by=self.mgr)
        self.assertEqual(pool_service.available(ssr), Decimal('100'))
        # sequential over-allocation proof (the advisory lock serialises the true race)
        pool_service.allocate(ssr, self.worker, qty=60, actor=self.mgr)
        self.assertEqual(pool_service.available(ssr), Decimal('40'))
        with self.assertRaisesMessage(ValidationError, 'available'):
            pool_service.allocate(ssr, self.worker, qty=50, actor=self.mgr)

    def test_source_resolution_skips_none_gap(self):
        # cutting(1) → NONE gap(2) → consuming(3): source must resolve to cutting.
        csr, ssr = self._build(consuming_grain=ALLOC_DIM_QUANTITY, cutting_rows=[], consuming_order=3, gap_none=True)
        AddaProductSizeColorPieceBreakdown.objects.create(
            adda=csr.adda, product=csr.adda.product, cutting_record=csr.cutting,
            color=self.red, size=self.m, verified_piece_count=25, created_by=self.mgr)
        self.assertEqual(pool_service.available(ssr), Decimal('25'))   # skipped the NONE stage


class GuardTests(_Base):
    def setUp(self):
        self.csr, self.ssr = self._build(consuming_grain=ALLOC_DIM_QUANTITY, cutting_rows=[])
        AddaProductSizeColorPieceBreakdown.objects.create(
            adda=self.csr.adda, product=self.csr.adda.product, cutting_record=self.csr.cutting,
            color=self.red, size=self.m, verified_piece_count=10, created_by=self.mgr)

    def test_non_management_refused(self):
        with self.assertRaises(PermissionDenied):
            pool_service.allocate(self.ssr, self.worker, qty=1, actor=self.worker)

    def test_quantity_stage_rejects_color_size(self):
        with self.assertRaises(ValidationError):
            pool_service.allocate(self.ssr, self.worker, qty=1, actor=self.mgr,
                                        color_id=self.red.pk, size_id=self.m.pk)

    def test_none_stage_not_allocatable(self):
        # the cutting stage record's downstream NONE-grain: build a NONE consuming stage.
        csr, ssr = self._build(consuming_grain=ALLOC_DIM_NONE, cutting_rows=[])
        with self.assertRaisesMessage(ValidationError, 'not a piece-pool stage'):
            pool_service.allocate(ssr, self.worker, qty=1, actor=self.mgr)


class NoMoneyDecouplingTests(TestCase):
    def test_wsa_has_no_money_fields(self):
        names = {f.name for f in WorkerStageAllocation._meta.get_fields()}
        for forbidden in ('rate', 'earning', 'cost', 'amount', 'ledger',
                          'settlement', 'settlement_line', 'adda_settlement', 'cost_method'):
            self.assertNotIn(forbidden, names,
                             f"WorkerStageAllocation must carry no money — found {forbidden!r}")

    def test_allocation_service_does_not_import_costing_or_settlement(self):
        # Decoupling contract: the allocation module must not reach costing/settlement code.
        import inspect

        from production.services import pool_service as mod
        src = inspect.getsource(mod)
        # crude but effective: no import lines pulling costing/settlement/earning
        for line in src.splitlines():
            s = line.strip()
            if s.startswith(('import ', 'from ')):
                for bad in ('cost_service', 'stage_rate_service', 'adda_settlement', 'settlement_service'):
                    self.assertNotIn(bad, s, f"allocation_service must not import {bad}")
