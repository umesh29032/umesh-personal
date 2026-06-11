"""C-1 pre-deploy hardening (ADR-0009/0010): the runtime items.

1. Grouped-member guard — a WorkflowStageRoleRate surviving on a grouped
   MEMBER stage must NOT become a second payment: the expected-rate freeze
   yields 0, settlement books ₹0 for member lines (pay lives at the payer).
2. Leftover-consumption write path — single-writer semantics proven before
   any UI exists (whole-piece, no double-consume, never the source Adda).
3. Honest-NULL surface — consumed-but-unpriced rolls counted, never coerced.
"""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone
from datetime import date

from accounts.models import User
from inventory.models import Role
from production.models import (
    Adda, AddaStageRecord, Product, RemainingClothOfClothRoll, Stage,
    WorkflowStage, WorkflowStageRoleRate, WorkerStageTask,
)
from production.services.cost_service import role_rate_for
from production.services.worker_task_service import (
    complete_worker_task, report_contributions, set_stage_workers,
)
from raw_materials.models import ClothColor, ClothRoll, ClothType, StorageLocation
from raw_materials.services import consume_leftover




def _roll(roll_id, **kw):
    """Minimal valid ClothRoll (required FKs filled once, not per test)."""
    ct, _ = ClothType.objects.get_or_create(name='C1 Cotton')
    cc, _ = ClothColor.objects.get_or_create(name='C1 Red')
    loc, _ = StorageLocation.objects.get_or_create(name='C1 Rack')
    defaults = dict(cloth_type=ct, cloth_color=cc, storage_location=loc,
                    purchased_date=date.today())
    defaults.update(kw)
    return ClothRoll.objects.create(roll_id=roll_id, **defaults)


def _mgmt(email='c1-mgmt@test'):
    u = User.objects.create_user(email=email, password='x')
    u.role = Role.objects.get(code='manager')
    u.save()
    return u


class GroupedMemberGuardTests(TestCase):
    """ADR-0009: grouped members never pay twice."""

    def setUp(self):
        self.mgmt = _mgmt()
        self.worker = User.objects.create_user(email='c1-w@test', password='x')
        self.worker.role = Role.objects.get(code='worker')
        self.worker.save()
        self.product = Product.objects.create(code='C1G', name='C1G P')
        payer_stage, _ = Stage.objects.get_or_create(
            code='c1_payer', defaults={'name': 'C1 Payer'})
        member_stage, _ = Stage.objects.get_or_create(
            code='c1_member', defaults={'name': 'C1 Member'})
        self.ws_payer = WorkflowStage.objects.create(
            product=self.product, stage=payer_stage, order=1,
            cost_rate=Decimal('10'), credits_workers=True)
        # member: cost_rate nulled (flow_service grouping behavior) + grouped
        self.ws_member = WorkflowStage.objects.create(
            product=self.product, stage=member_stage, order=2,
            cost_rate=None, cost_billed_at=self.ws_payer, credits_workers=True)
        # the LEAK fixture: a role rate row SURVIVING on the grouped member
        WorkflowStageRoleRate.objects.create(
            workflow_stage=self.ws_member, role=self.worker.role,
            cost_rate=Decimal('7'))
        self.adda = Adda.objects.create(code='C1G-001', product=self.product)
        self.sr_member = AddaStageRecord.objects.create(
            adda=self.adda, workflow_stage=self.ws_member,
            started_at=timezone.now())

    def test_role_rate_for_returns_none_on_grouped_member(self):
        self.assertIsNone(role_rate_for(self.ws_member, self.worker.role))
        # ungrouped stage with a role rate still pays the override
        WorkflowStageRoleRate.objects.create(
            workflow_stage=self.ws_payer, role=self.worker.role,
            cost_rate=Decimal('12'))
        self.assertEqual(role_rate_for(self.ws_payer, self.worker.role),
                         Decimal('12'))

    def test_member_contribution_freezes_zero_rate(self):
        set_stage_workers(self.sr_member, [self.worker.pk])
        task = WorkerStageTask.objects.get(
            stage_record=self.sr_member, worker=self.worker)
        report_contributions(task, [{'reported_quantity': '50'}],
                             actor=self.worker)
        complete_worker_task(task, actor=self.worker)
        c = task.contributions.get()
        self.assertEqual(c.expected_rate, Decimal('0'))
        self.assertEqual(c.expected_earning, Decimal('0.00'))


class ConsumeLeftoverTests(TestCase):
    """ADR-0009: the sole writer of leftover consumption."""

    def setUp(self):
        self.mgmt = _mgmt('c1-mgmt2@test')
        self.product = Product.objects.create(code='C1L', name='C1L P')
        self.adda_a = Adda.objects.create(code='C1L-A', product=self.product)
        self.adda_b = Adda.objects.create(code='C1L-B', product=self.product)
        self.roll = _roll('CR-C10001', cost_per_kg=Decimal('200'))
        self.leftover = RemainingClothOfClothRoll.objects.create(
            roll=self.roll, source_adda=self.adda_a,
            remaining_weight_kg=Decimal('3.5'),
            remaining_length_meters=Decimal('4.2'))

    def test_consume_happy_path(self):
        lo = consume_leftover(self.mgmt, leftover=self.leftover,
                              adda=self.adda_b, notes='reused in B')
        self.assertTrue(lo.is_consumed)
        self.assertEqual(lo.consumed_in_adda, self.adda_b)
        self.assertIsNotNone(lo.consumed_at)

    def test_double_consume_refused(self):
        consume_leftover(self.mgmt, leftover=self.leftover, adda=self.adda_b)
        with self.assertRaisesMessage(ValidationError, 'already consumed'):
            consume_leftover(self.mgmt, leftover=self.leftover,
                             adda=self.adda_b)

    def test_source_adda_refused(self):
        with self.assertRaisesMessage(ValidationError, 'produced it'):
            consume_leftover(self.mgmt, leftover=self.leftover,
                             adda=self.adda_a)

    def test_management_only(self):
        worker = User.objects.create_user(email='c1-w2@test', password='x')
        from django.core.exceptions import PermissionDenied
        with self.assertRaises(PermissionDenied):
            consume_leftover(worker, leftover=self.leftover, adda=self.adda_b)


class UnpricedRollSurfaceTests(TestCase):
    """ADR-0009 honest-NULL: unknown price is surfaced, never ₹0."""

    def test_costing_view_counts_consumed_unpriced_rolls(self):
        mgmt = _mgmt('c1-mgmt3@test')
        product = Product.objects.create(code='C1U', name='C1U P')
        adda = Adda.objects.create(code='C1U-001', product=product)
        _roll('CR-C1U001', adda=adda, cost_per_kg=None)   # consumed, unpriced
        _roll('CR-C1U002', adda=adda, cost_per_kg=Decimal('150'))
        _roll('CR-C1U003', cost_per_kg=None)              # unconsumed — not counted
        self.client.force_login(mgmt)
        resp = self.client.get('/production/costing/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['total_unpriced_rolls'], 1)
        self.assertContains(resp, 'material costing is incomplete')
