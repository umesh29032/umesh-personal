"""Foundation S4 / Phase 1 (D1) — allocation_dimensions + grain monotonicity.

Owner-locked: the piece-pool starts at CUTTING; pre-piece stages (layering,
cutting_pattern, barcode) are NONE. allocation_dimensions governs PIECE-POOL behaviour
ONLY — orthogonal to settlement (credits_workers) + costing (cost_method). Monotonicity
(non-increasing) applies only among non-NONE participants; NONE is skipped.
"""
from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase

from accounts.models import User
from inventory.models import Role
from production.constants import (
    ALLOC_DIM_COLOR_SIZE, ALLOC_DIM_NONE, ALLOC_DIM_QUANTITY, STAGE_CUTTING,
)
from production.models import CostMethod, Product, Stage, WorkflowStage
from production.services import flow_service


def _mgr(email='s4-mgr@test'):
    u = User.objects.create_user(email=email, password='x')
    u.role = Role.objects.get(code='super_admin'); u.save()
    return u


def _stage(code):
    return Stage.objects.get_or_create(code=code, defaults={'name': code})[0]


class FieldDefaultAndSeedTests(TestCase):
    def test_field_default_is_none(self):
        p = Product.objects.create(code='S4D', name='S4D')
        ws = WorkflowStage.objects.create(product=p, stage=_stage('zzz'), order=1, cost_rate=Decimal('1'))
        self.assertEqual(ws.allocation_dimensions, ALLOC_DIM_NONE)   # pool is opt-in

    def test_add_stage_seeds_cutting_color_size_others_none(self):
        # add_stage_to_product_flow seeds from the handler's pool_grain (data-driven).
        p = Product.objects.create(code='S4SEED', name='S4SEED')
        mgr = _mgr('s4-seed@test')
        cut = flow_service.add_stage_to_product_flow(user=mgr, product=p, stage=_stage(STAGE_CUTTING))
        self.assertEqual(cut.allocation_dimensions, ALLOC_DIM_COLOR_SIZE)   # pool source
        lay = flow_service.add_stage_to_product_flow(user=mgr, product=p, stage=_stage('layering'))
        self.assertEqual(lay.allocation_dimensions, ALLOC_DIM_NONE)         # pre-piece


class MonotonicityTests(TestCase):
    def _flow(self, dims_by_order):
        p = Product.objects.create(code='S4M' + str(len(dims_by_order)) + dims_by_order[0][:1], name='m')
        for i, dim in enumerate(dims_by_order, start=1):
            WorkflowStage.objects.create(
                product=p, stage=_stage(f'm{i}_{dim}_{p.code}'), order=i,
                cost_rate=Decimal('1'), allocation_dimensions=dim)
        return p

    def test_layering_none_then_cutting_colorsize_is_valid(self):
        # The real flow: NONE → COLOR_SIZE is NOT a violation (NONE skipped).
        p = self._flow([ALLOC_DIM_NONE, ALLOC_DIM_COLOR_SIZE, ALLOC_DIM_NONE])
        flow_service._validate_grain_monotonicity(p)   # no raise

    def test_coarsen_downstream_is_valid(self):
        p = self._flow([ALLOC_DIM_COLOR_SIZE, ALLOC_DIM_QUANTITY])   # fine → coarse OK
        flow_service._validate_grain_monotonicity(p)

    def test_refine_downstream_is_rejected(self):
        # Two participants, later one finer → re-fining → reject.
        p = self._flow([ALLOC_DIM_QUANTITY, ALLOC_DIM_COLOR_SIZE])
        with self.assertRaisesMessage(ValidationError, 'coarsen'):
            flow_service._validate_grain_monotonicity(p)

    def test_none_between_participants_skipped(self):
        # COLOR_SIZE → NONE → QUANTITY: NONE skipped, CS→Q still coarsening → valid.
        p = self._flow([ALLOC_DIM_COLOR_SIZE, ALLOC_DIM_NONE, ALLOC_DIM_QUANTITY])
        flow_service._validate_grain_monotonicity(p)


class SetStageGrainTests(TestCase):
    def setUp(self):
        self.mgr = _mgr()
        self.p = Product.objects.create(code='S4SG', name='S4SG')
        self.a = WorkflowStage.objects.create(product=self.p, stage=_stage('sg_a'), order=1, cost_rate=Decimal('1'))
        self.b = WorkflowStage.objects.create(product=self.p, stage=_stage('sg_b'), order=2, cost_rate=Decimal('1'))

    def test_set_grain_valid(self):
        flow_service.set_stage_grain(user=self.mgr, workflow_stage=self.a, allocation_dimensions=ALLOC_DIM_COLOR_SIZE)
        self.a.refresh_from_db()
        self.assertEqual(self.a.allocation_dimensions, ALLOC_DIM_COLOR_SIZE)

    def test_set_grain_refuses_refine_downstream(self):
        flow_service.set_stage_grain(user=self.mgr, workflow_stage=self.a, allocation_dimensions=ALLOC_DIM_QUANTITY)
        with self.assertRaisesMessage(ValidationError, 'coarsen'):
            # b (order 2) finer than a (order 1) → reject; rolls back.
            flow_service.set_stage_grain(user=self.mgr, workflow_stage=self.b, allocation_dimensions=ALLOC_DIM_COLOR_SIZE)
        self.b.refresh_from_db()
        self.assertEqual(self.b.allocation_dimensions, ALLOC_DIM_NONE)   # rolled back

    def test_set_grain_invalid_value(self):
        with self.assertRaises(ValidationError):
            flow_service.set_stage_grain(user=self.mgr, workflow_stage=self.a, allocation_dimensions='bogus')

    def test_set_grain_non_production_role_refused(self):
        # set_stage_grain uses the same production-role gate as the sibling flow
        # functions (_ensure_can_manage). A non-production role (accountant) is refused.
        acct = User.objects.create_user(email='s4-acct@test', password='x')
        acct.role = Role.objects.get(code='accountant'); acct.save()
        with self.assertRaises(PermissionDenied):
            flow_service.set_stage_grain(user=acct, workflow_stage=self.a, allocation_dimensions=ALLOC_DIM_QUANTITY)


class OrthogonalityTests(TestCase):
    """allocation_dimensions must NOT touch settlement (credits_workers) or costing
    (cost_method) — owner lock."""
    def test_none_stage_can_still_settle_and_price(self):
        p = Product.objects.create(code='S4O', name='S4O')
        ws = WorkflowStage.objects.create(
            product=p, stage=_stage('o_lay'), order=1,
            cost_method=CostMethod.PER_LAYER, cost_rate=Decimal('3'),
            credits_workers=True, allocation_dimensions=ALLOC_DIM_NONE)
        # NONE pool grain, yet fully payable + priced per-layer.
        self.assertEqual(ws.allocation_dimensions, ALLOC_DIM_NONE)
        self.assertTrue(ws.credits_workers)
        self.assertEqual(ws.cost_method, CostMethod.PER_LAYER)

    def test_set_grain_does_not_change_settlement_or_costing(self):
        mgr = _mgr('s4-orth@test')
        p = Product.objects.create(code='S4O2', name='S4O2')
        ws = WorkflowStage.objects.create(
            product=p, stage=_stage('o2'), order=1, cost_method=CostMethod.PER_PIECE,
            cost_rate=Decimal('5'), credits_workers=True)
        flow_service.set_stage_grain(user=mgr, workflow_stage=ws, allocation_dimensions=ALLOC_DIM_COLOR_SIZE)
        ws.refresh_from_db()
        self.assertTrue(ws.credits_workers)                 # unchanged
        self.assertEqual(ws.cost_method, CostMethod.PER_PIECE)   # unchanged
        self.assertEqual(ws.cost_rate, Decimal('5'))            # unchanged
