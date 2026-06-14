"""H-2B: stalled-Adda drill-down view.

Proves: management/super_admin see all stalled Addas, longest-first, with
warning/critical severity; worker isolation holds; and the drill-down count
ALWAYS reconciles with the digest tile count (both use stalled_stage_records()).
"""
from datetime import timedelta
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


class StalledDrilldownTests(TestCase):
    def setUp(self):
        self.sa = _u('sd-sa@test', 'super_admin', is_super=True)
        self.mgr = _u('sd-mgr@test', 'manager')
        self.worker = _u('sd-w@test', 'worker')
        product = Product.objects.create(code='SD', name='SD Prod')
        stage, _ = Stage.objects.get_or_create(code='sd_s', defaults={'name': 'SD Stage'})
        ws = WorkflowStage.objects.create(
            product=product, stage=stage, order=1,
            cost_rate=Decimal('3'), credits_workers=True)
        now = timezone.now()
        # A: 4 days open → warning (>3, <6). B: 8 days → critical (>=6).
        self.adda_a = Adda.objects.create(code='SD-A', product=product, status=Adda.Status.IN_PROGRESS)
        AddaStageRecord.objects.create(adda=self.adda_a, workflow_stage=ws, started_at=now - timedelta(days=4))
        self.sr_a = self.adda_a.stage_records.get()
        self.adda_b = Adda.objects.create(code='SD-B', product=product, status=Adda.Status.IN_PROGRESS)
        AddaStageRecord.objects.create(adda=self.adda_b, workflow_stage=ws, started_at=now - timedelta(days=8))
        set_stage_workers(self.sr_a, [self.worker.pk])   # worker assigned to A only
        self.url = reverse('production:stalled-addas')

    def _rows(self, user):
        self.client.force_login(user)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        return resp.context['rows']

    def test_management_sees_all_longest_first(self):
        rows = self._rows(self.mgr)
        self.assertEqual([r['adda'].code for r in rows], ['SD-B', 'SD-A'])  # 8d before 4d

    def test_severity_warning_vs_critical(self):
        rows = self._rows(self.mgr)
        by_code = {r['adda'].code: r for r in rows}
        self.assertEqual(by_code['SD-B']['severity'], 'critical')  # 8d ≥ 3×2
        self.assertEqual(by_code['SD-A']['severity'], 'warning')   # 4d ≥ 3, < 6

    def test_drilldown_reconciles_with_digest_count(self):
        rows = self._rows(self.mgr)
        self.assertEqual(operations_digest()['stalled_count'], len(rows))  # single source

    def test_worker_sees_only_assigned(self):
        rows = self._rows(self.worker)
        self.assertEqual([r['adda'].code for r in rows], ['SD-A'])  # not SD-B

    def test_super_admin_sees_all(self):
        self.assertEqual(len(self._rows(self.sa)), 2)
