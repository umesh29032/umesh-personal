"""M2.7b: worker-credit payability + guard (unit tests, not wired yet).

stage_is_payable(): data-driven (credits_workers + self-paid).
ensure_worker_credit(): blocks a payable stage with zero allocations; passes with
>=1; no-op for non-payable. Wiring into advance_to_next_stage is M2.7c.
"""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from accounts.models import Skill, User
from expense.services import allocate_stage_work
from production.models import AddaStageRecord, Product, Stage, WorkflowStage
from production.services import create_adda
from production.stages.base import ensure_worker_credit, stage_is_payable


class StageCreditTest(TestCase):
    def setUp(self):
        cut = Stage.objects.get_or_create(code='cutting', defaults={'name': 'Cutting'})[0]
        self.product = Product.objects.create(code='CREDIT', name='Credit Test')
        self.ws = WorkflowStage.objects.create(
            product=self.product, stage=cut, order=1,
            cost_rate=Decimal('10'), credits_workers=True)
        skill = Skill.objects.get_or_create(name='cutting_master', defaults={'label': 'Cutting Master'})[0]
        self.mgr = User.objects.create_user(
            email='credit-mgr@test', password='x', is_superuser=True, is_staff=True)
        self.mgr.skills.add(skill)
        self.worker = User.objects.create_user(email='credit-worker@test', password='x')
        self.adda = create_adda(self.mgr, product=self.product)
        self.sr = AddaStageRecord.objects.create(
            adda=self.adda, workflow_stage=self.ws, started_at=timezone.now())

    # ── stage_is_payable ──────────────────────────────────────────────────────
    def test_payable_when_flag_set_and_self_paid(self):
        self.assertTrue(stage_is_payable(self.ws))

    def test_not_payable_when_flag_false(self):
        self.ws.credits_workers = False
        self.assertFalse(stage_is_payable(self.ws))

    def test_not_payable_when_grouped(self):
        packing = Stage.objects.get_or_create(code='packing', defaults={'name': 'Packing'})[0]
        payer = WorkflowStage.objects.create(
            product=self.product, stage=packing, order=2, cost_rate=Decimal('5'))
        self.ws.cost_billed_at = payer
        self.assertFalse(stage_is_payable(self.ws))   # member billed at payer

    # ── ensure_worker_credit ─────────────────────────────────────────────────
    def test_guard_blocks_payable_with_zero_allocations(self):
        with self.assertRaisesMessage(ValidationError, 'allocate at least one worker'):
            ensure_worker_credit(self.sr)

    def test_guard_passes_with_one_allocation(self):
        allocate_stage_work(
            user=self.mgr, stage_record=self.sr, worker=self.worker, allocated_quantity=3)
        ensure_worker_credit(self.sr)   # no raise

    def test_guard_noop_for_non_payable_stage(self):
        self.ws.credits_workers = False
        self.ws.save(update_fields=['credits_workers'])
        ensure_worker_credit(self.sr)   # no raise even with zero allocations
