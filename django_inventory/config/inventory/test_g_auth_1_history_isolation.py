"""G-AUTH-1: object-level isolation on the history routes.

AddaHistoryView + RollHistoryView were role-gated only (any production role could
read ANY Adda's / roll's history by URL). Now they apply the dashboard's
assigned-Adda isolation: management sees all; a worker sees only Addas they hold
a live task on (and rolls that touched such an Adda). Proves: assigned worker =
200, unassigned worker = 403, manager = 200, super_admin = 200 — for BOTH views.
"""
from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from inventory.models import Role
from production.models import (
    Adda, AddaStageRecord, Product, Stage, WorkflowStage,
)
from production.services.worker_task_service import set_stage_workers
from raw_materials.models import ClothColor, ClothType, StorageLocation
from raw_materials.services import bulk_create_rolls
from tracking.models import AddaHistory


def _u(email, role_code, *, is_super=False):
    u = User.objects.create_user(email=email, password='x', is_superuser=is_super)
    u.role = Role.objects.get(code=role_code)
    u.save()
    return u


class HistoryIsolationTests(TestCase):
    def setUp(self):
        self.sa = _u('hi-sa@test', 'super_admin', is_super=True)
        self.mgr = _u('hi-mgr@test', 'manager')
        self.assigned = _u('hi-aw@test', 'worker')
        self.unassigned = _u('hi-uw@test', 'worker')

        product = Product.objects.create(code='HIS', name='HIS Prod')
        stage, _ = Stage.objects.get_or_create(code='his_s', defaults={'name': 'HIS S'})
        ws = WorkflowStage.objects.create(
            product=product, stage=stage, order=1,
            cost_rate=Decimal('3'), credits_workers=True)
        self.adda = Adda.objects.create(
            code='HIS-001', product=product, status=Adda.Status.IN_PROGRESS)
        self.sr = AddaStageRecord.objects.create(
            adda=self.adda, workflow_stage=ws, started_at=timezone.now())
        set_stage_workers(self.sr, [self.assigned.pk])   # only `assigned` gets a task

        rolls = bulk_create_rolls(
            user=self.sa, cloth_type=ClothType.objects.get(name='Cotton'),
            storage_location=StorageLocation.objects.get(code='ROHINI'),
            purchased_date=date.today(),
            breakup=[{'color': ClothColor.objects.get(name='Red'), 'qty': 1}])
        self.roll = rolls[0]
        # Link the roll to the Adda (roll↔Adda via an AddaHistory row).
        AddaHistory.objects.create(
            adda=self.adda, change_type=AddaHistory.ChangeType.ROLL_ASSIGNED,
            roll=self.roll, actor=self.mgr)

    def _adda_url(self):
        return reverse('tracking:adda-history', args=[self.adda.code])

    def _roll_url(self):
        return reverse('tracking:roll-history', args=[self.roll.pk])

    def _status(self, user, url):
        self.client.force_login(user)
        return self.client.get(url).status_code

    # ── Adda history ──────────────────────────────────────────────────────
    def test_adda_assigned_worker_allowed(self):
        self.assertEqual(self._status(self.assigned, self._adda_url()), 200)

    def test_adda_unassigned_worker_denied(self):
        self.assertEqual(self._status(self.unassigned, self._adda_url()), 403)

    def test_adda_manager_allowed(self):
        self.assertEqual(self._status(self.mgr, self._adda_url()), 200)

    def test_adda_super_admin_allowed(self):
        self.assertEqual(self._status(self.sa, self._adda_url()), 200)

    # ── Roll history (same rule) ────────────────────────────────────────────
    def test_roll_assigned_worker_allowed(self):
        self.assertEqual(self._status(self.assigned, self._roll_url()), 200)

    def test_roll_unassigned_worker_denied(self):
        self.assertEqual(self._status(self.unassigned, self._roll_url()), 403)

    def test_roll_manager_allowed(self):
        self.assertEqual(self._status(self.mgr, self._roll_url()), 200)

    def test_roll_super_admin_allowed(self):
        self.assertEqual(self._status(self.sa, self._roll_url()), 200)


class FinancialHistoryLeakTests(TestCase):
    """PA-03-1: supplier/cost_per_kg are financial fields (view-gated to
    FINANCIAL_ROLES on the roll list/detail). Their CHANGE history must not leak
    those values via the roll-history timeline to non-financial users who can
    still reach the page (assigned worker, manager)."""

    def setUp(self):
        from raw_materials.services import update_roll_details
        self.sa = _u('fh-sa@test', 'super_admin', is_super=True)   # management + financial
        self.mgr = _u('fh-mgr@test', 'manager')                    # management, NOT financial
        self.worker = _u('fh-w@test', 'worker')                    # assigned, NOT financial

        product = Product.objects.create(code='FHL', name='FHL Prod')
        stage, _ = Stage.objects.get_or_create(code='fhl_s', defaults={'name': 'FHL S'})
        ws = WorkflowStage.objects.create(
            product=product, stage=stage, order=1,
            cost_rate=Decimal('3'), credits_workers=True)
        self.adda = Adda.objects.create(
            code='FHL-001', product=product, status=Adda.Status.IN_PROGRESS)
        self.sr = AddaStageRecord.objects.create(
            adda=self.adda, workflow_stage=ws, started_at=timezone.now())
        set_stage_workers(self.sr, [self.worker.pk])

        rolls = bulk_create_rolls(
            user=self.sa, cloth_type=ClothType.objects.get(name='Cotton'),
            storage_location=StorageLocation.objects.get(code='ROHINI'),
            purchased_date=date.today(),
            breakup=[{'color': ClothColor.objects.get(name='Red'), 'qty': 1}])
        self.roll = rolls[0]
        AddaHistory.objects.create(
            adda=self.adda, change_type=AddaHistory.ChangeType.ROLL_ASSIGNED,
            roll=self.roll, actor=self.mgr)
        # super-admin (financial) sets a cost → creates a cost_per_kg history row
        update_roll_details(user=self.sa, roll=self.roll, cost_per_kg=Decimal('123.45'))

    def _html(self, user):
        self.client.force_login(user)
        return self.client.get(reverse('tracking:roll-history', args=[self.roll.pk])).content.decode()

    def test_assigned_worker_does_not_see_cost_value(self):
        html = self._html(self.worker)
        self.assertNotIn('123.45', html)
        self.assertNotIn('cost_per_kg', html)

    def test_manager_does_not_see_cost_value(self):
        html = self._html(self.mgr)
        self.assertNotIn('123.45', html)
        self.assertNotIn('cost_per_kg', html)

    def test_super_admin_sees_cost_value(self):
        # financial role → the cost change IS visible (proves the data exists and
        # is only filtered for non-financial users, not globally hidden).
        self.assertIn('123.45', self._html(self.sa))
