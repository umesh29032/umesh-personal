"""P1-1: role-based landing + management Operations digest.

Covers: HomeView routes management → Operations, worker → My Dashboard; the
operations_digest tiles + STALLED_ADDA_DAYS-driven stalled detection (threshold
is a setting, not hardcoded); digest is management-gated in the view.
"""
from datetime import timedelta
from decimal import Decimal

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from inventory.models import Role
from production.models import (
    Adda, AddaStageRecord, Product, Stage, WorkflowStage,
)


def _mgr(email):
    u = User.objects.create_user(email=email, password='x')
    u.role = Role.objects.get(code='manager')
    u.save()
    return u


def _worker(email):
    u = User.objects.create_user(email=email, password='x')
    u.role = Role.objects.get(code='worker')
    u.save()
    return u


class LandingRoutingTests(TestCase):
    def test_super_admin_lands_on_bod(self):
        # D9 landing override (BOD-E, owner charter 2026-07-18): Owner/SA → BOD;
        # every other role keeps its P1-1 landing (the tests below, unchanged).
        sa = User.objects.create_user(email='p11-sa@test', password='x')
        sa.role = Role.objects.get(code='super_admin')
        sa.save()
        self.client.force_login(sa)
        resp = self.client.get(reverse('accounts:home'))
        self.assertRedirects(resp, reverse('bod:dashboard'),
                             fetch_redirect_response=False)

    def test_management_lands_on_operations(self):
        self.client.force_login(_mgr('p11-mgr@test'))
        resp = self.client.get(reverse('accounts:home'))
        self.assertRedirects(resp, reverse('production:dashboard'),
                             fetch_redirect_response=False)

    def test_worker_lands_on_my_dashboard(self):
        self.client.force_login(_worker('p11-w@test'))
        resp = self.client.get(reverse('accounts:home'))
        self.assertRedirects(resp, reverse('inventory:my_dashboard'),
                             fetch_redirect_response=False)


class OperationsDigestTests(TestCase):
    def setUp(self):
        product = Product.objects.create(code='P11', name='P11 Prod')
        stage, _ = Stage.objects.get_or_create(
            code='p11s', defaults={'name': 'P11 Stage'})
        ws = WorkflowStage.objects.create(
            product=product, stage=stage, order=1,
            cost_rate=Decimal('3'), credits_workers=True)
        self.adda = Adda.objects.create(
            code='P11-001', product=product, status=Adda.Status.IN_PROGRESS)
        # An OPEN stage started 5 days ago → stalled at the default 3-day threshold.
        self.sr = AddaStageRecord.objects.create(
            adda=self.adda, workflow_stage=ws,
            started_at=timezone.now() - timedelta(days=5))

    def test_digest_tiles_and_stalled_detection(self):
        from production.services.operations_digest import operations_digest
        d = operations_digest()
        self.assertEqual(d['stalled_count'], 1)        # 5d open > 3d threshold
        self.assertEqual(d['stalled_threshold_days'], 3)
        self.assertEqual(d['active_addas'], 1)
        self.assertEqual(d['completed_today'], 0)
        for k in ('pending_reports', 'pending_payable', 'advance_exposure'):
            self.assertIn(k, d)

    @override_settings(STALLED_ADDA_DAYS=10)
    def test_stalled_threshold_is_configurable(self):
        from production.services.operations_digest import operations_digest
        d = operations_digest()
        self.assertEqual(d['stalled_count'], 0)        # 5d open < 10d threshold
        self.assertEqual(d['stalled_threshold_days'], 10)

    def test_digest_present_for_management_view(self):
        self.client.force_login(_mgr('p11-mgr2@test'))
        resp = self.client.get(reverse('production:dashboard'))
        self.assertEqual(resp.status_code, 200)
        self.assertIsNotNone(resp.context['digest'])
        self.assertEqual(resp.context['digest']['stalled_count'], 1)
