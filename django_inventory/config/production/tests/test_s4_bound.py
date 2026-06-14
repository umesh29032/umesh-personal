"""Foundation S4 / Phase 4 — complete-time allocation bound (Strict).

Σ(good+alter+missing) per REPORTED (worker, stage, colour, size) ≤ Σ active allocated.
Per-dimension + independent: under-consuming an allocated dim passes; a reported-but-
UNALLOCATED dim fails. Production-capacity ONLY — never reads verified/settlement/rate/
earning/cost. Gated by ENFORCE_ALLOCATION_BOUND (default False = no check).
"""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.utils import timezone

from accounts.models import User
from inventory.models import Role
from production.constants import ALLOC_DIM_COLOR_SIZE, ALLOC_DIM_NONE, STAGE_CUTTING
from production.models import (
    Adda, AddaProductSizeColorPieceBreakdown, AddaStageRecord, CuttingRecord, Product,
    ProductSize, Stage, WorkerStageTask, WorkflowStage,
)
from production.services import pool_service, stage_rate_service
from production.services.worker_task_service import (
    complete_worker_task, report_contributions, set_stage_workers,
)
from raw_materials.models import ClothColor


def _user(email, code):
    u = User.objects.create_user(email=email, password='x')
    u.role = Role.objects.get(code=code); u.save()
    return u


class _Base(TestCase):
    def _setup(self, *, consuming_grain=ALLOC_DIM_COLOR_SIZE):
        self._seq = getattr(self, '_seq', 0) + 1
        product = Product.objects.create(code=f'S4B{id(self) % 9999}_{self._seq}', name='b')
        cstage, _ = Stage.objects.get_or_create(code=STAGE_CUTTING, defaults={'name': 'Cutting'})
        cws = WorkflowStage.objects.create(product=product, stage=cstage, order=1,
                                           cost_rate=Decimal('2'), allocation_dimensions=ALLOC_DIM_COLOR_SIZE)
        adda = Adda.objects.create(code=f'S4B-{product.code}', product=product, status=Adda.Status.IN_PROGRESS)
        csr = AddaStageRecord.objects.create(adda=adda, workflow_stage=cws,
                                             started_at=timezone.now(), completed_at=timezone.now())
        self._cr = CuttingRecord.objects.create(stage_record=csr, pieces_cut=1000)
        self.csr = csr
        self.mgr = _user(f's4b-mk-{product.code}@t', 'super_admin')
        self.worker = _user(f's4b-w-{product.code}@t', 'worker')
        self.red = ClothColor.objects.get_or_create(name='S4B Red')[0]
        self.blue = ClothColor.objects.get_or_create(name='S4B Blue')[0]
        self.m = ProductSize.objects.create(product=product, code='m', label='M', display_order=1)
        self.l = ProductSize.objects.create(product=product, code='l', label='L', display_order=2)
        sstage, _ = Stage.objects.get_or_create(code='stitching', defaults={'name': 'Stitching'})
        sws = WorkflowStage.objects.create(product=product, stage=sstage, order=2,
                                           cost_rate=Decimal('3'), credits_workers=True,
                                           allocation_dimensions=consuming_grain)
        ssr = AddaStageRecord.objects.create(adda=adda, workflow_stage=sws, started_at=timezone.now())
        stage_rate_service.ensure_stage_role_rates(ssr)
        set_stage_workers(ssr, [self.worker.pk])
        self.task = WorkerStageTask.objects.get(stage_record=ssr, worker=self.worker)
        return ssr

    def _cut(self, color, size, n):
        AddaProductSizeColorPieceBreakdown.objects.create(
            adda=self.csr.adda, product=self.csr.adda.product, cutting_record=self._cr,
            color=color, size=size, verified_piece_count=n, created_by=self.mgr)

    def _alloc(self, ssr, color, size, qty):
        pool_service.allocate(ssr, self.worker, qty=qty, actor=self.mgr,
                              color_id=color.pk, size_id=size.pk)

    def _report(self, lines):
        report_contributions(self.task, [{k: v for k, v in ln.items() if k in
                                          ('reported_quantity', 'color_id', 'size_id')}
                                         for ln in lines], actor=self.worker)
        for ln, c in zip(lines, list(self.task.contributions.all())):
            if ln.get('alter') or ln.get('missing'):
                c.alter_quantity = Decimal(str(ln.get('alter', 0)))
                c.missing_quantity = Decimal(str(ln.get('missing', 0)))
                c.save(update_fields=['alter_quantity', 'missing_quantity'])


class FlagOffTests(_Base):
    def test_flag_off_does_not_check(self):
        # ENFORCE default False → over-report completes (back-compat), no allocation needed.
        self._setup()
        self._report([{'reported_quantity': '999', 'color_id': self.red.pk, 'size_id': self.m.pk}])
        complete_worker_task(self.task, actor=self.worker)
        self.assertEqual(self.task.status, WorkerStageTask.Status.COMPLETED)


@override_settings(ENFORCE_ALLOCATION_BOUND=True)
class BoundEnforcedTests(_Base):
    def test_within_bound_completes(self):
        ssr = self._setup()
        self._cut(self.red, self.m, 50)
        self._alloc(ssr, self.red, self.m, 50)
        self._report([{'reported_quantity': '40', 'color_id': self.red.pk, 'size_id': self.m.pk}])
        complete_worker_task(self.task, actor=self.worker)
        self.assertEqual(self.task.status, WorkerStageTask.Status.COMPLETED)

    def test_over_bound_refused(self):
        ssr = self._setup()
        self._cut(self.red, self.m, 50)
        self._alloc(ssr, self.red, self.m, 30)
        self._report([{'reported_quantity': '40', 'color_id': self.red.pk, 'size_id': self.m.pk}])
        with self.assertRaisesMessage(ValidationError, 'allocated'):
            complete_worker_task(self.task, actor=self.worker)

    def test_multiple_allocations_sum(self):
        ssr = self._setup()
        self._cut(self.red, self.m, 60)
        self._alloc(ssr, self.red, self.m, 30)
        self._alloc(ssr, self.red, self.m, 30)   # two active rows → Σ = 60
        self._report([{'reported_quantity': '55', 'color_id': self.red.pk, 'size_id': self.m.pk}])
        complete_worker_task(self.task, actor=self.worker)   # 55 ≤ 60
        self.assertEqual(self.task.status, WorkerStageTask.Status.COMPLETED)

    def test_partial_void_reduces_total(self):
        ssr = self._setup()
        self._cut(self.red, self.m, 60)
        self._alloc(ssr, self.red, self.m, 30)
        wsa2 = pool_service.allocate(ssr, self.worker, qty=30, actor=self.mgr,
                                     color_id=self.red.pk, size_id=self.m.pk)
        pool_service.void_allocation(wsa2, actor=self.mgr)   # active now 30
        self._report([{'reported_quantity': '40', 'color_id': self.red.pk, 'size_id': self.m.pk}])
        with self.assertRaisesMessage(ValidationError, 'allocated'):
            complete_worker_task(self.task, actor=self.worker)   # 40 > 30

    def test_unallocated_dimension_refused(self):
        self._setup()
        self._cut(self.red, self.m, 50)   # no allocation created
        self._report([{'reported_quantity': '10', 'color_id': self.red.pk, 'size_id': self.m.pk}])
        with self.assertRaisesMessage(ValidationError, 'allocated'):
            complete_worker_task(self.task, actor=self.worker)   # allocated=0

    def test_per_dimension_under_consume_passes(self):
        # Owner example 1: alloc Red/M=50 + Red/L=50; report only Red/M=40 → passes.
        ssr = self._setup()
        self._cut(self.red, self.m, 50); self._cut(self.red, self.l, 50)
        self._alloc(ssr, self.red, self.m, 50)
        self._alloc(ssr, self.red, self.l, 50)
        self._report([{'reported_quantity': '40', 'color_id': self.red.pk, 'size_id': self.m.pk}])
        complete_worker_task(self.task, actor=self.worker)
        self.assertEqual(self.task.status, WorkerStageTask.Status.COMPLETED)

    def test_per_dimension_unallocated_reported_dim_fails(self):
        # Owner example 2: alloc Red/M=50; report Red/M=40 + Blue/L=10 → Blue/L unallocated → fail.
        ssr = self._setup()
        self._cut(self.red, self.m, 50)
        self._alloc(ssr, self.red, self.m, 50)
        self._report([
            {'reported_quantity': '40', 'color_id': self.red.pk, 'size_id': self.m.pk},
            {'reported_quantity': '10', 'color_id': self.blue.pk, 'size_id': self.l.pk},
        ])
        with self.assertRaisesMessage(ValidationError, 'allocated'):
            complete_worker_task(self.task, actor=self.worker)

    def test_none_stage_never_bounded(self):
        self._setup(consuming_grain=ALLOC_DIM_NONE)
        self._report([{'reported_quantity': '999'}])
        complete_worker_task(self.task, actor=self.worker)
        self.assertEqual(self.task.status, WorkerStageTask.Status.COMPLETED)

    def test_alter_missing_count_toward_bound(self):
        # good=40 + alter=20 = 60 > 50 → refused (alter/missing ARE in the LHS).
        ssr = self._setup()
        self._cut(self.red, self.m, 50)
        self._alloc(ssr, self.red, self.m, 50)
        self._report([{'reported_quantity': '40', 'color_id': self.red.pk, 'size_id': self.m.pk,
                       'alter': '20'}])
        with self.assertRaisesMessage(ValidationError, 'allocated'):
            complete_worker_task(self.task, actor=self.worker)

    def test_bound_ignores_verified_quantity(self):
        # DECOUPLING proof: verified=100 (> allocated 50) would FAIL if used; bound uses
        # good=40 → completes. Never reads verified/money.
        ssr = self._setup()
        self._cut(self.red, self.m, 50)
        self._alloc(ssr, self.red, self.m, 50)
        self._report([{'reported_quantity': '40', 'color_id': self.red.pk, 'size_id': self.m.pk}])
        c = self.task.contributions.get()
        c.verified_quantity = Decimal('100'); c.save(update_fields=['verified_quantity'])
        complete_worker_task(self.task, actor=self.worker)
        self.assertEqual(self.task.status, WorkerStageTask.Status.COMPLETED)


class PreviewAndSoftWarnTests(_Base):
    """S5 / S4-005 rollout safety — preview (pre-flip audit) + non-blocking soft-warn.
    ENFORCE_ALLOCATION_BOUND stays OFF (default) so over-bound contributions can complete."""

    def test_preview_lists_over_bound(self):
        ssr = self._setup()
        self._cut(self.red, self.m, 50); self._alloc(ssr, self.red, self.m, 5)
        self._report([{'reported_quantity': '8', 'color_id': self.red.pk, 'size_id': self.m.pk}])
        complete_worker_task(self.task, actor=self.worker)   # flag off → completes
        v = pool_service.preview_bound_violations(adda=ssr.adda)
        self.assertTrue(any(x['kind'] == 'over_bound' for x in v))

    def test_preview_lists_unallocated(self):
        ssr = self._setup()
        self._cut(self.red, self.m, 50)                       # NO allocation created
        self._report([{'reported_quantity': '4', 'color_id': self.red.pk, 'size_id': self.m.pk}])
        complete_worker_task(self.task, actor=self.worker)
        v = pool_service.preview_bound_violations(adda=ssr.adda)
        self.assertTrue(any(x['kind'] == 'unallocated' for x in v))

    def test_preview_clean_within_bound(self):
        ssr = self._setup()
        self._cut(self.red, self.m, 50); self._alloc(ssr, self.red, self.m, 10)
        self._report([{'reported_quantity': '8', 'color_id': self.red.pk, 'size_id': self.m.pk}])
        complete_worker_task(self.task, actor=self.worker)
        self.assertEqual(pool_service.preview_bound_violations(adda=ssr.adda), [])

    def test_soft_warning_over_returns_message(self):
        ssr = self._setup()
        self._cut(self.red, self.m, 50); self._alloc(ssr, self.red, self.m, 5)
        self._report([{'reported_quantity': '8', 'color_id': self.red.pk, 'size_id': self.m.pk}])
        self.assertIsNotNone(pool_service.bound_soft_warning(self.task))   # 8 > 5

    def test_soft_warning_within_bound_none(self):
        ssr = self._setup()
        self._cut(self.red, self.m, 50); self._alloc(ssr, self.red, self.m, 10)
        self._report([{'reported_quantity': '8', 'color_id': self.red.pk, 'size_id': self.m.pk}])
        self.assertIsNone(pool_service.bound_soft_warning(self.task))      # 8 ≤ 10
