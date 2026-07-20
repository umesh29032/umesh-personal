"""AE-1 — bundle allocation engine hardening (owner bundle model 2026-07-20).

Covers the Adapt-&-Harden changes: whole-bundle allocation (default), partial (explicit),
HARD always-on over-report bound (no flag), unallocated-(colour,size)-pair refusal, and the
`bundle_service` read-model. Fully self-contained fixture: cutting (COLOR_SIZE, APSCPB) →
stitching (COLOR_SIZE consumer). No migration-seed reliance.
"""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from accounts.models import User
from inventory.models import Role
from production.constants import ALLOC_DIM_COLOR_SIZE, STAGE_CUTTING
from production.models import (
    Adda, AddaProductSizeColorPieceBreakdown, AddaStageRecord, CuttingRecord, Product,
    ProductSize, Stage, WorkerStageAllocation, WorkerStageTask, WorkflowStage,
)
from production.services import bundle_service, pool_service
from production.services.worker_task_service import (
    complete_worker_task, save_draft_contributions,
)
from production.stages.base import registry
from raw_materials.models import ClothColor


def _user(email, code):
    u = User.objects.create_user(email=email, password='x')
    u.role = Role.objects.get(code=code)
    u.save()
    return u


class _Base(TestCase):
    def _build(self, cutting_rows):
        """cutting (COLOR_SIZE, APSCPB) → stitching (COLOR_SIZE). cutting_rows = [(color,size,n)]."""
        self._seq = getattr(self, '_seq', 0) + 1
        product = Product.objects.create(code=f'AE1{id(self) % 9999}_{self._seq}', name='ae1')
        cstage, _ = Stage.objects.get_or_create(code=STAGE_CUTTING, defaults={'name': 'Cutting'})
        cws = WorkflowStage.objects.create(product=product, stage=cstage, order=1,
                                           cost_rate=Decimal('2'),
                                           allocation_dimensions=ALLOC_DIM_COLOR_SIZE)
        adda = Adda.objects.create(code=f'AE1-{product.code}', product=product,
                                   status=Adda.Status.IN_PROGRESS)
        csr = AddaStageRecord.objects.create(adda=adda, workflow_stage=cws,
                                             started_at=timezone.now(), completed_at=timezone.now())
        cr = CuttingRecord.objects.create(stage_record=csr, pieces_cut=sum(r[2] for r in cutting_rows))
        actor = _user(f'ae1-mk-{product.code}@t', 'super_admin')
        for (color, size, n) in cutting_rows:
            AddaProductSizeColorPieceBreakdown.objects.create(
                adda=adda, product=product, cutting_record=cr, color=color, size=size,
                verified_piece_count=n, created_by=actor)
        sstage, _ = Stage.objects.get_or_create(code='overlock', defaults={'name': 'Overlock'})
        sws = WorkflowStage.objects.create(product=product, stage=sstage, order=2,
                                           cost_rate=Decimal('2'),
                                           allocation_dimensions=ALLOC_DIM_COLOR_SIZE)
        ssr = AddaStageRecord.objects.create(adda=adda, workflow_stage=sws, started_at=timezone.now())
        self.adda, self.ssr, self.mgr = adda, ssr, actor
        self.worker = _user(f'ae1-w-{product.code}@t', 'worker')
        self.worker2 = _user(f'ae1-w2-{product.code}@t', 'worker')
        return ssr

    def _size(self, label='M'):
        return ProductSize.objects.create(product=self.adda.product, code=label.lower(),
                                          label=label, display_order=1)


class WholeAllocationTests(_Base):
    def test_whole_takes_full_available_and_empties_bundle(self):
        red = ClothColor.objects.get_or_create(name='AE1 Red')[0]
        ssr = self._build([(red, None, 0)])
        size = self._size()
        AddaProductSizeColorPieceBreakdown.objects.filter(adda=self.adda).delete()
        AddaProductSizeColorPieceBreakdown.objects.create(
            adda=self.adda, product=self.adda.product,
            cutting_record=CuttingRecord.objects.get(stage_record__adda=self.adda),
            color=red, size=size, verified_piece_count=100, created_by=self.mgr)

        wsa = pool_service.allocate_whole(ssr, self.worker, actor=self.mgr,
                                          color_id=red.id, size_id=size.id)
        self.assertEqual(wsa.allocated_quantity, Decimal('100'))
        self.assertEqual(wsa.allocation_mode, WorkerStageAllocation.Mode.WHOLE)
        # bundle now empty → nothing left available on that dim
        self.assertEqual(pool_service.available(ssr, red.id, size.id), Decimal('0'))

    def test_whole_on_partially_allocated_grabs_remaining(self):
        red = ClothColor.objects.get_or_create(name='AE1 Red2')[0]
        ssr = self._build([])
        size = self._size()
        AddaProductSizeColorPieceBreakdown.objects.create(
            adda=self.adda, product=self.adda.product,
            cutting_record=CuttingRecord.objects.get(stage_record__adda=self.adda),
            color=red, size=size, verified_piece_count=100, created_by=self.mgr)
        pool_service.allocate(ssr, self.worker, qty=40, actor=self.mgr,
                              color_id=red.id, size_id=size.id)   # partial 40
        wsa = pool_service.allocate_whole(ssr, self.worker2, actor=self.mgr,
                                          color_id=red.id, size_id=size.id)  # whole → 60
        self.assertEqual(wsa.allocated_quantity, Decimal('60'))
        self.assertEqual(pool_service.available(ssr, red.id, size.id), Decimal('0'))

    def test_whole_on_empty_bundle_refused(self):
        red = ClothColor.objects.get_or_create(name='AE1 Red3')[0]
        ssr = self._build([])
        size = self._size()
        AddaProductSizeColorPieceBreakdown.objects.create(
            adda=self.adda, product=self.adda.product,
            cutting_record=CuttingRecord.objects.get(stage_record__adda=self.adda),
            color=red, size=size, verified_piece_count=50, created_by=self.mgr)
        pool_service.allocate_whole(ssr, self.worker, actor=self.mgr,
                                    color_id=red.id, size_id=size.id)
        with self.assertRaises(ValidationError):
            pool_service.allocate_whole(ssr, self.worker2, actor=self.mgr,
                                        color_id=red.id, size_id=size.id)


class PartialAllocationTests(_Base):
    def test_partial_slice_leaves_remainder_and_stamps_mode(self):
        red = ClothColor.objects.get_or_create(name='AE1 Blue')[0]
        ssr = self._build([])
        size = self._size()
        AddaProductSizeColorPieceBreakdown.objects.create(
            adda=self.adda, product=self.adda.product,
            cutting_record=CuttingRecord.objects.get(stage_record__adda=self.adda),
            color=red, size=size, verified_piece_count=100, created_by=self.mgr)
        wsa = pool_service.allocate(ssr, self.worker, qty=40, actor=self.mgr,
                                    color_id=red.id, size_id=size.id)
        self.assertEqual(wsa.allocation_mode, WorkerStageAllocation.Mode.PARTIAL)
        self.assertEqual(pool_service.available(ssr, red.id, size.id), Decimal('60'))


class HardOverReportBoundTests(_Base):
    """The bound is ALWAYS on now — no ENFORCE_ALLOCATION_BOUND flag."""

    def _setup(self, alloc_qty):
        self.red = ClothColor.objects.get_or_create(name='AE1 Grn')[0]
        ssr = self._build([])
        self.size = self._size()
        AddaProductSizeColorPieceBreakdown.objects.create(
            adda=self.adda, product=self.adda.product,
            cutting_record=CuttingRecord.objects.get(stage_record__adda=self.adda),
            color=self.red, size=self.size, verified_piece_count=100, created_by=self.mgr)
        pool_service.allocate(ssr, self.worker, qty=alloc_qty, actor=self.mgr,
                              color_id=self.red.id, size_id=self.size.id)
        task = WorkerStageTask.objects.create(
            stage_record=ssr, worker=self.worker, status=WorkerStageTask.Status.ASSIGNED)
        return ssr, task

    def _line(self, good, alter=0, missing=0, damaged=0):
        return [{'color_id': self.red.id, 'size_id': self.size.id,
                 'reported_quantity': str(good), 'alter_quantity': str(alter),
                 'missing_quantity': str(missing), 'damaged_quantity': str(damaged)}]

    def test_within_allocation_ok(self):
        ssr, task = self._setup(40)
        save_draft_contributions(task, self._line(39, alter=1), actor=self.worker)
        complete_worker_task(task, actor=self.worker)   # 39+1 = 40 ≤ 40
        self.assertEqual(task.status, WorkerStageTask.Status.COMPLETED)

    def test_good_over_allocation_hard_refused(self):
        ssr, task = self._setup(40)
        save_draft_contributions(task, self._line(41), actor=self.worker)
        with self.assertRaises(ValidationError):
            complete_worker_task(task, actor=self.worker)   # 41 > 40

    def test_good_plus_defect_over_allocation_hard_refused(self):
        ssr, task = self._setup(40)
        save_draft_contributions(task, self._line(39, alter=2), actor=self.worker)
        with self.assertRaises(ValidationError):
            complete_worker_task(task, actor=self.worker)   # 39+2 = 41 > 40

    def test_unallocated_pair_reported_refused_at_complete(self):
        ssr, task = self._setup(40)
        other = ProductSize.objects.create(product=self.adda.product, code='xl',
                                           label='XL', display_order=2)
        # report a size the worker was NOT allocated → allocated=0 for that dim
        save_draft_contributions(task, [{
            'color_id': self.red.id, 'size_id': other.id,
            'reported_quantity': '5', 'alter_quantity': '0',
            'missing_quantity': '0', 'damaged_quantity': '0'}], actor=self.worker)
        with self.assertRaises(ValidationError):
            complete_worker_task(task, actor=self.worker)


class PairValidationSchemaTests(_Base):
    """gap-E: worker form refuses a (colour,size) pair never allocated (flat-list hole)."""

    def test_parse_refuses_unallocated_pair(self):
        from production.views.worker_report_views import _parse_lines
        red = ClothColor.objects.get_or_create(name='AE1 Pk')[0]
        blue = ClothColor.objects.get_or_create(name='AE1 Pk2')[0]
        ssr = self._build([])
        m = self._size('M')
        xl = ProductSize.objects.create(product=self.adda.product, code='xl',
                                        label='XL', display_order=2)
        cr = CuttingRecord.objects.get(stage_record__adda=self.adda)
        for c, s in [(red, m), (blue, xl)]:
            AddaProductSizeColorPieceBreakdown.objects.create(
                adda=self.adda, product=self.adda.product, cutting_record=cr,
                color=c, size=s, verified_piece_count=50, created_by=self.mgr)
        # allocate Red/M and Blue/XL to the worker (two valid pairs)
        pool_service.allocate(ssr, self.worker, qty=10, actor=self.mgr, color_id=red.id, size_id=m.id)
        pool_service.allocate(ssr, self.worker, qty=10, actor=self.mgr, color_id=blue.id, size_id=xl.id)
        schema = registry.get('overlock').contribution_schema(self.adda, worker=self.worker)
        self.assertEqual(set(schema['allowed_pairs']), {(red.id, m.id), (blue.id, xl.id)})
        # Red/XL is a valid colour + valid size but NEVER an allocated PAIR → refused
        post = {'line-count': '1', 'line-0-color_id': str(red.id),
                'line-0-size_id': str(xl.id), 'line-0-reported_quantity': '5'}
        with self.assertRaises(ValidationError):
            _parse_lines(post, schema)
        # the real pair passes
        post['line-0-size_id'] = str(m.id)
        self.assertEqual(len(_parse_lines(post, schema)), 1)


class BundleReadModelTests(_Base):
    def test_projection_totals_and_holders(self):
        red = ClothColor.objects.get_or_create(name='AE1 Or')[0]
        ssr = self._build([])
        size = self._size()
        AddaProductSizeColorPieceBreakdown.objects.create(
            adda=self.adda, product=self.adda.product,
            cutting_record=CuttingRecord.objects.get(stage_record__adda=self.adda),
            color=red, size=size, verified_piece_count=100, created_by=self.mgr)
        pool_service.allocate(ssr, self.worker, qty=40, actor=self.mgr,
                              color_id=red.id, size_id=size.id)
        bundles = bundle_service.bundles_for_stage(ssr)
        self.assertEqual(len(bundles), 1)
        b = bundles[0]
        self.assertEqual((b['total'], b['assigned'], b['available']),
                         (Decimal('100'), Decimal('40'), Decimal('60')))
        self.assertEqual(b['state'], 'partial')
        self.assertEqual(len(b['holders']), 1)
        # worker view
        wb = bundle_service.worker_bundles(ssr, self.worker)
        self.assertEqual(len(wb), 1)
        self.assertEqual((wb[0]['allocated'], wb[0]['completed'], wb[0]['remaining']),
                         (Decimal('40'), Decimal('0'), Decimal('40')))
