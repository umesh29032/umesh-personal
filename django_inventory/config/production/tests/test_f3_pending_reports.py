"""F-3: pending-reports drill-down view.

Proves: management/super_admin see all actionable pending reports (assigned/
in-progress tasks on open stages), oldest-waiting first; the count reconciles
with the digest tile (both use pending_report_tasks()); a worker sees ONLY their
own queue.
"""
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from inventory.models import Role
from production.models import (
    Adda, AddaStageRecord, Product, Stage, WorkflowStage,
)
from production.services.operations_digest import operations_digest
from production.services.worker_task_service import set_stage_workers


def _u(email, role_code, *, is_super=False):
    u = User.objects.create_user(email=email, password='x', is_superuser=is_super)
    u.role = Role.objects.get(code=role_code)
    u.save()
    return u


class PendingReportsDrilldownTests(TestCase):
    def setUp(self):
        self.sa = _u('pr-sa@test', 'super_admin', is_super=True)
        self.mgr = _u('pr-mgr@test', 'manager')
        self.w1 = _u('pr-w1@test', 'worker')
        self.w2 = _u('pr-w2@test', 'worker')
        product = Product.objects.create(code='PR', name='PR Prod')
        stage, _ = Stage.objects.get_or_create(code='pr_s', defaults={'name': 'PR Stage'})
        ws = WorkflowStage.objects.create(
            product=product, stage=stage, order=1,
            cost_rate=Decimal('3'), credits_workers=True)
        now = timezone.now()
        self.adda_a = Adda.objects.create(code='PR-A', product=product, status=Adda.Status.IN_PROGRESS)
        self.sr_a = AddaStageRecord.objects.create(adda=self.adda_a, workflow_stage=ws, started_at=now)
        self.adda_b = Adda.objects.create(code='PR-B', product=product, status=Adda.Status.IN_PROGRESS)
        self.sr_b = AddaStageRecord.objects.create(adda=self.adda_b, workflow_stage=ws, started_at=now)
        set_stage_workers(self.sr_a, [self.w1.pk])   # W1 pending on A (created first → oldest)
        set_stage_workers(self.sr_b, [self.w2.pk])   # W2 pending on B
        self.url = reverse('production:pending-reports')

    def _rows(self, user):
        self.client.force_login(user)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        return resp.context['rows']

    def test_management_sees_all_oldest_first(self):
        rows = self._rows(self.mgr)
        self.assertEqual({r['adda'].code for r in rows}, {'PR-A', 'PR-B'})
        # oldest-waiting first: assigned timestamps non-decreasing.
        self.assertLessEqual(rows[0]['assigned'], rows[1]['assigned'])
        self.assertEqual(rows[0]['adda'].code, 'PR-A')   # assigned before B

    def test_reconciles_with_digest_count(self):
        rows = self._rows(self.mgr)
        self.assertEqual(operations_digest()['pending_reports'], len(rows))  # single source

    def test_worker_sees_only_own_queue(self):
        rows = self._rows(self.w1)
        self.assertEqual([r['adda'].code for r in rows], ['PR-A'])
        self.assertEqual(rows[0]['worker'], self.w1)     # never W2's task

    def test_super_admin_sees_all(self):
        self.assertEqual(len(self._rows(self.sa)), 2)
