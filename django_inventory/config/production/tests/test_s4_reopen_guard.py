"""Foundation S4 / Phase 5 — Era-A downstream-consumer reopen guard (M-4).

Reopening a source stage is refused while a downstream consumer of its pool output exists
(non-voided WorkerStageAllocation OR completed/verified WorkerStageContribution). Transitive
across the chain; names the furthest blocking stage + blocker + corrective action. Strict but
recoverable (reverse-first peel).
"""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from accounts.models import User
from inventory.models import Role
from production.constants import ALLOC_DIM_COLOR_SIZE, ALLOC_DIM_QUANTITY, STAGE_CUTTING
from production.models import (
    Adda, AddaStageRecord, Product, Stage, WorkflowStage, WorkerStageAllocation,
    WorkerStageContribution, WorkerStageTask,
)
from production.services._shared import reopen_stage_record


def _user(email, code):
    u = User.objects.create_user(email=email, password='x')
    u.role = Role.objects.get(code=code); u.save()
    return u


class ReopenConsumerGuardTests(TestCase):
    def setUp(self):
        self.mgr = _user('s4r-mgr@test', 'super_admin')
        self.worker = _user('s4r-w@test', 'worker')
        self.product = Product.objects.create(code='S4R', name='S4R')
        self.adda = Adda.objects.create(code='S4R-1', product=self.product, status=Adda.Status.IN_PROGRESS)
        self.sr = {}
        for order, code, grain in ((1, STAGE_CUTTING, ALLOC_DIM_COLOR_SIZE),
                                   (2, 'stitching', ALLOC_DIM_QUANTITY),
                                   (3, 'finishing', ALLOC_DIM_QUANTITY)):
            stage, _ = Stage.objects.get_or_create(code=code, defaults={'name': code.title()})
            ws = WorkflowStage.objects.create(product=self.product, stage=stage, order=order,
                                              cost_rate=Decimal('2'), allocation_dimensions=grain)
            self.sr[code] = AddaStageRecord.objects.create(
                adda=self.adda, workflow_stage=ws,
                started_at=timezone.now(), completed_at=timezone.now())

    def _wsa(self, code):
        return WorkerStageAllocation.objects.create(
            stage_record=self.sr[code], worker=self.worker,
            allocated_quantity=Decimal('10'), created_by=self.mgr)

    def _completed_wsc(self, code):
        t = WorkerStageTask.objects.create(stage_record=self.sr[code], worker=self.worker,
                                           status=WorkerStageTask.Status.COMPLETED)
        return WorkerStageContribution.objects.create(
            task=t, reported_quantity=Decimal('5'), good_quantity=Decimal('5')), t

    def _reopen(self, code):
        return reopen_stage_record(adda=self.adda, stage_code=code,
                                   stage_label=code.title(), user=self.mgr)

    # 1 — downstream active allocation blocks
    def test_blocked_by_downstream_allocation(self):
        self._wsa('stitching')
        with self.assertRaisesMessage(ValidationError, 'active worker allocations'):
            self._reopen(STAGE_CUTTING)

    # 2 — downstream completed good/alter/missing blocks
    def test_blocked_by_downstream_completed_contribution(self):
        self._completed_wsc('stitching')
        with self.assertRaisesMessage(ValidationError, 'completed production'):
            self._reopen(STAGE_CUTTING)

    # 3 — after all downstream allocations voided (no completed contribution) → allowed
    def test_reopen_allowed_after_allocations_voided(self):
        wsa = self._wsa('stitching')
        wsa.voided_at = timezone.now(); wsa.save(update_fields=['voided_at'])
        sr = self._reopen(STAGE_CUTTING)
        self.assertIsNone(sr.completed_at)   # reopened, guard did not block

    # 4 — settlement reversal alone is insufficient: the completed contribution still blocks
    def test_settlement_reversal_alone_insufficient(self):
        _c, task = self._completed_wsc('stitching')
        # (a settled-then-reversed downstream voids the SWA but leaves the contribution
        # completed — the guard checks task status, so reopen is still blocked)
        with self.assertRaisesMessage(ValidationError, 'completed production'):
            self._reopen(STAGE_CUTTING)
        # only handling the downstream contribution (reopen downstream → task cancelled) clears it
        task.status = WorkerStageTask.Status.CANCELLED; task.save(update_fields=['status'])
        sr = self._reopen(STAGE_CUTTING)
        self.assertIsNone(sr.completed_at)

    # 5 — chain: furthest downstream named; upstream is never a consumer
    def test_chain_names_furthest_and_upstream_not_consumer(self):
        self._wsa('finishing')   # two stages downstream of cutting
        with self.assertRaisesMessage(ValidationError, 'Finishing'):
            self._reopen(STAGE_CUTTING)          # blocked by Finishing (furthest)
        with self.assertRaisesMessage(ValidationError, 'Finishing'):
            self._reopen('stitching')            # Finishing is downstream of Stitching too
        sr = self._reopen('finishing')           # nothing downstream of Finishing → allowed
        self.assertIsNone(sr.completed_at)       # (upstream Cutting/Stitching never block it)

    # 6 — recovery sequence: reverse-first peel, furthest inward
    def test_recovery_sequence(self):
        ws_s = self._wsa('stitching')
        ws_f = self._wsa('finishing')
        with self.assertRaises(ValidationError):
            self._reopen(STAGE_CUTTING)          # blocked (Finishing furthest)
        ws_f.voided_at = timezone.now(); ws_f.save(update_fields=['voided_at'])
        with self.assertRaisesMessage(ValidationError, 'Stitching'):
            self._reopen(STAGE_CUTTING)          # now Stitching is the blocker
        ws_s.voided_at = timezone.now(); ws_s.save(update_fields=['voided_at'])
        sr = self._reopen(STAGE_CUTTING)         # all downstream cleared → reopen succeeds
        self.assertIsNone(sr.completed_at)

    # actionable message: names stage + blocker + corrective verbs
    def test_message_is_actionable(self):
        self._wsa('stitching')
        try:
            self._reopen(STAGE_CUTTING)
            self.fail("expected ValidationError")
        except ValidationError as exc:
            msg = '; '.join(exc.messages)
            self.assertIn('Stitching', msg)                    # which downstream stage
            self.assertIn('active worker allocations', msg)    # blocker type
            self.assertIn('reverse', msg.lower())              # corrective action
            self.assertIn('void', msg.lower())
            self.assertIn('reopen', msg.lower())
