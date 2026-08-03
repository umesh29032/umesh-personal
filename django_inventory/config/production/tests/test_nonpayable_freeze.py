"""A360 follow-up (owner rule 2026-07-05) — non-payable stages freeze ZERO.

One consistent rule via the F2 chokepoint (`effective_pay_rate`): a
`credits_workers=False` stage behaves exactly like a grouped member — rate 0,
expected 0 at freeze AND rerate; payable stages unchanged; grouped unchanged.
"""
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from accounts.models import User
from inventory.models import Role
from production.models import (
    Adda, AddaStageRecord, Product, Stage, WorkflowStage,
)
from production.services.cost_service import effective_pay_rate
from production.services.worker_task_service import (
    complete_worker_task, report_contributions, set_stage_workers,
)


def _role_user(email, role_code, **extra):
    u = User.objects.create_user(email=email, password='x', **extra)
    u.role = Role.objects.get(code=role_code)
    u.save()
    return u


class NonPayableFreezeTests(TestCase):
    def setUp(self):
        self.sa = _role_user('npf-sa@test', 'super_admin',
                             is_superuser=True, is_staff=True)
        self.w = _role_user('npf-w@test', 'worker')
        self.product = Product.objects.create(code='NPF', name='NPF P')
        s1, _ = Stage.objects.get_or_create(code='npf_s1', defaults={'name': 'NPF One'})
        s2, _ = Stage.objects.get_or_create(code='npf_s2', defaults={'name': 'NPF Two'})
        # Non-payable stage with a NON-ZERO rate (standard cost only).
        self.ws_np = WorkflowStage.objects.create(
            product=self.product, stage=s1, order=1,
            cost_rate=Decimal('10'), credits_workers=False)
        self.ws_pay = WorkflowStage.objects.create(
            product=self.product, stage=s2, order=2,
            cost_rate=Decimal('5'), credits_workers=True)
        self.adda = Adda.objects.create(code='NPF-001', product=self.product)
        now = timezone.now()
        self.sr_np = AddaStageRecord.objects.create(
            adda=self.adda, workflow_stage=self.ws_np, started_at=now)
        self.sr_pay = AddaStageRecord.objects.create(
            adda=self.adda, workflow_stage=self.ws_pay, started_at=now)

    def _complete(self, sr, qty):
        set_stage_workers(sr, [self.w.pk])
        t = sr.worker_tasks.get(worker=self.w)
        report_contributions(t, [{'reported_quantity': str(qty)}], actor=self.w)
        complete_worker_task(t, actor=self.w)
        return t.contributions.get()

    def test_guard_zeroes_nonpayable_keeps_payable(self):
        self.assertEqual(effective_pay_rate(self.ws_np, Decimal('10')),
                         Decimal('0'))
        self.assertEqual(effective_pay_rate(self.ws_pay, Decimal('5')),
                         Decimal('5'))

    def test_freeze_is_zero_on_nonpayable_stage(self):
        c = self._complete(self.sr_np, 30)
        self.assertEqual(c.expected_rate, Decimal('0'))
        self.assertEqual(c.expected_earning, Decimal('0.00'))
        # Payable colleague-stage unchanged: 20 × ₹5.
        c2 = self._complete(self.sr_pay, 20)
        self.assertEqual(c2.expected_earning, Decimal('100.00'))

    def test_rerate_cannot_resurrect_a_nonpayable_rate(self):
        from production.services.stage_rate_service import rerate_stage_role
        c = self._complete(self.sr_np, 30)
        rerate_stage_role(stage_record=self.sr_np, role=self.w.role,
                          new_rate=Decimal('99'), reason='attempt',
                          actor=self.sa)
        c.refresh_from_db()
        self.assertEqual(c.expected_rate, Decimal('0'))    # guard wins
        self.assertEqual(c.expected_earning, Decimal('0.00'))
