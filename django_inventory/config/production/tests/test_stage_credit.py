"""M2.7b: worker-credit payability + guard (unit tests, not wired yet).

stage_is_payable(): data-driven (credits_workers + self-paid).
ensure_worker_credit(): blocks a payable stage with zero allocations; passes with
>=1; no-op for non-payable. Wiring into advance_to_next_stage is M2.7c.
"""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.utils import timezone

from accounts.models import Skill, User
from expense.services import allocate_stage_work
from production.models import AddaStageRecord, Product, Stage, WorkflowStage
from production.services import create_adda
from production.stages.base import ensure_worker_credit, stage_is_payable


# V2-3 PR-B lever-regression pin: this suite exercises the LEGACY allocation
# path, kept alive behind the rollback lever. Default is settlement-only.
@override_settings(LEDGER_CREDIT_AT_ALLOCATION=True)
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

    # ── M2.7c wiring: advance_to_next_stage enforces the guard ───────────────
    def test_advance_blocks_payable_stage_without_allocation(self):
        from production.services import advance_to_next_stage
        self.adda.current_stage = self.ws
        self.adda.save(update_fields=['current_stage'])
        with self.assertRaisesMessage(ValidationError, 'allocate at least one worker'):
            advance_to_next_stage(self.adda, self.mgr)

    def test_advance_passes_with_allocation(self):
        from production.services import advance_to_next_stage
        allocate_stage_work(
            user=self.mgr, stage_record=self.sr, worker=self.worker, allocated_quantity=2)
        self.adda.current_stage = self.ws
        self.adda.save(update_fields=['current_stage'])
        advance_to_next_stage(self.adda, self.mgr)            # no raise
        self.adda.refresh_from_db()
        self.assertEqual(self.adda.status, self.adda.Status.COMPLETED)   # only stage -> done

    def test_advance_legacy_optout_skips_guard(self):
        from production.services import advance_to_next_stage
        self.adda.current_stage = self.ws
        self.adda.save(update_fields=['current_stage'])
        advance_to_next_stage(self.adda, self.mgr, enforce_worker_credit=False)   # no raise
        self.adda.refresh_from_db()
        self.assertEqual(self.adda.status, self.adda.Status.COMPLETED)


# PA-10-1: the SETTLEMENT-FIRST default (flag OFF). No StageWorkAssignment exists
# pre-settlement (allocate refuses; settlement SWA is created at finalize, AFTER
# completion), so reading SWA blocked EVERY payable-stage completion in the default
# config. The guard now reads the production truth settlement pays: a COMPLETED/
# VERIFIED WorkerStageContribution. (No @override_settings → real default False.)
class StageCreditSettlementFirstTest(TestCase):
    def setUp(self):
        cut = Stage.objects.get_or_create(code='cutting', defaults={'name': 'Cutting'})[0]
        self.product = Product.objects.create(code='SF-CREDIT', name='SF Credit Test')
        self.ws = WorkflowStage.objects.create(
            product=self.product, stage=cut, order=1,
            cost_rate=Decimal('10'), credits_workers=True)
        skill = Skill.objects.get_or_create(
            name='cutting_master', defaults={'label': 'Cutting Master'})[0]
        self.mgr = User.objects.create_user(
            email='sf-credit-mgr@test', password='x', is_superuser=True, is_staff=True)
        self.mgr.skills.add(skill)
        self.worker = User.objects.create_user(email='sf-credit-worker@test', password='x')
        self.adda = create_adda(self.mgr, product=self.product)
        self.sr = AddaStageRecord.objects.create(
            adda=self.adda, workflow_stage=self.ws, started_at=timezone.now())

    def _complete_contribution(self):
        from production.models import WorkerStageContribution, WorkerStageTask
        task = WorkerStageTask.objects.create(
            stage_record=self.sr, worker=self.worker,
            status=WorkerStageTask.Status.COMPLETED, completed_at=timezone.now())
        WorkerStageContribution.objects.create(
            task=task, reported_quantity=Decimal('5'), good_quantity=Decimal('5'))

    def test_guard_blocks_payable_without_completed_contribution(self):
        # No allocation possible (flag off) AND no completed contribution → blocked.
        with self.assertRaisesMessage(ValidationError, 'complete their reported work'):
            ensure_worker_credit(self.sr)

    def test_guard_passes_with_completed_contribution(self):
        self._complete_contribution()
        ensure_worker_credit(self.sr)   # no raise — settlement will pay this line

    def test_advance_blocks_without_contribution_in_default_mode(self):
        from production.services import advance_to_next_stage
        self.adda.current_stage = self.ws
        self.adda.save(update_fields=['current_stage'])
        with self.assertRaisesMessage(ValidationError, 'complete their reported work'):
            advance_to_next_stage(self.adda, self.mgr)

    def test_advance_passes_with_contribution_in_default_mode(self):
        from production.services import advance_to_next_stage
        self._complete_contribution()
        self.adda.current_stage = self.ws
        self.adda.save(update_fields=['current_stage'])
        advance_to_next_stage(self.adda, self.mgr)   # no raise — the real default-mode path
        self.adda.refresh_from_db()
        self.assertEqual(self.adda.status, self.adda.Status.COMPLETED)
