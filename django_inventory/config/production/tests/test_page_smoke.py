"""Page smoke test (PR-6 QA) — GET key pages as super admin, assert no 500.

Catches template/context errors across dashboards, stage workspaces, and the
payroll UI in one pass — the headless equivalent of clicking through the app.
"""
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Skill, User
from inventory.models import Role
from production.models import (
    AddaStageRecord, CuttingBundle, CuttingBundleItem, CuttingRecord,
    Product, ProductPattern, ProductSize,
)
from production.services import create_adda
from raw_materials.models import ClothColor


def _superuser():
    role = Role.objects.get(code='super_admin')
    u = User.objects.create_user(email='smoke@test.test', password='x', is_superuser=True, is_staff=True)
    u.role = role
    u.save()
    u.skills.add(Skill.objects.get(name='cutting_master'))
    return u


class PageSmokeTests(TestCase):
    def setUp(self):
        self.user = _superuser()
        self.client.force_login(self.user)
        self.product = Product.objects.get(code='NIKKAR')
        self.adda = create_adda(self.user, product=self.product)
        # Build a cutting stage with one bundle item so the cutting workspace
        # exercises the new allocation UI path.
        cutting_wf = self.product.workflow_stages.get(stage__code='cutting')
        cutting_wf.cost_rate = Decimal('3')
        cutting_wf.save(update_fields=['cost_rate'])
        # Put the Adda AT the cutting stage so the workspace shows bundles.
        self.adda.current_stage = cutting_wf
        self.adda.save(update_fields=['current_stage'])
        sr = AddaStageRecord.objects.create(
            adda=self.adda, workflow_stage=cutting_wf, started_at=timezone.now(),
        )
        cr = CuttingRecord.objects.create(stage_record=sr, pieces_cut=0)
        size = ProductSize.objects.create(product=self.product, code='m', label='M')
        color, _ = ClothColor.objects.get_or_create(name='Red')
        pat, _ = ProductPattern.objects.get_or_create(code='front-smoke', defaults={'name': 'Front'})
        bundle = CuttingBundle.objects.create(cutting_record=cr, size=size, total_pieces=10)
        CuttingBundleItem.objects.create(bundle=bundle, pattern=pat, color=color, count=10)

    def _ok(self, name, **kw):
        resp = self.client.get(reverse(name, kwargs=kw) if kw else reverse(name))
        self.assertIn(resp.status_code, (200, 302), f"{name} → {resp.status_code}")
        return resp

    def test_core_pages_render(self):
        for name in [
            'inventory:inventory_dashboard', 'inventory:user_dashboard',
            'production:dashboard', 'production:costing',
            'production:adda-list', 'production:product-list',
            'production:pattern-list', 'production:stage-list',
            'raw_materials:dashboard', 'raw_materials:roll-list',
            'tracking:dashboard',
            'expense:my-earnings', 'expense:payroll-overview',
            'expense:advance-add',
        ]:
            self._ok(name)

    def test_worker_detail_self(self):
        self._ok('expense:worker-detail', pk=self.user.pk)

    def test_settlement_and_profile_pages(self):
        self._ok('expense:settlement-create', pk=self.user.pk)
        self._ok('expense:worker-profile', pk=self.user.pk)

    def test_adda_and_stage_pages(self):
        self._ok('production:adda-detail', code=self.adda.code)
        self._ok('production:product-flow', pk=self.product.pk)
        self._ok('production:layering-workspace', code=self.adda.code)

    def test_cutting_workspace_renders(self):
        # The bundle workspace (with the PR-6 per-item allocation UI) renders
        # only when the product has pattern assignments + layered colors; the
        # allocation block itself is covered by expense.tests.test_allocation_ui.
        # Here we just assert the workspace page renders without a 500.
        resp = self.client.get(reverse('production:cutting-workspace', kwargs={'code': self.adda.code}))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, self.adda.code)
