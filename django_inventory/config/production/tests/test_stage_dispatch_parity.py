"""M2.6: StagePanelView registry dispatch.

The legacy if/elif was removed in M2.6c after parity was proven; StagePanelView now
builds per-stage context only through the registry. This guards that the registry
dispatch yields the stage builder's context and renders end-to-end.
"""
from datetime import date
from decimal import Decimal

from django.test import RequestFactory, TestCase
from django.urls import reverse

from accounts.models import Skill, User
from inventory.models import Role
from production.models import Product
from production.services import (
    attach_roll_to_layering, create_adda, record_remaining_cloth, start_layering,
)
from production.views.stage_views import StagePanelView
from raw_materials.models import ClothColor, ClothType, StorageLocation
from raw_materials.services import bulk_create_rolls


class StageDispatchParityTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='parity@test', password='x', is_superuser=True, is_staff=True)
        self.user.role = Role.objects.get(code='super_admin')
        self.user.save()
        self.user.skills.add(
            Skill.objects.get(name='cutting_master'),
            Skill.objects.get(name='cutting_master_helper'))
        nikkar = Product.objects.get(code='NIKKAR')
        cotton = ClothType.objects.get(name='Cotton')
        red = ClothColor.objects.get(name='Red')
        loc = StorageLocation.objects.get(code='ROHINI')
        rolls = bulk_create_rolls(
            user=self.user, cloth_type=cotton, storage_location=loc,
            purchased_date=date.today(), breakup=[{'color': red, 'qty': 2}])
        self.adda = create_adda(self.user, product=nikkar)
        sr = start_layering(adda=self.adda, worker_ids=[self.user.pk], user=self.user)
        for r in rolls:
            e = attach_roll_to_layering(
                stage_record=sr, roll=r, width_verified_inch=42,
                weight_verified_kg=Decimal('25.0'), user=self.user)
            record_remaining_cloth(
                entry=e, remaining_weight_kg=Decimal('0'),
                remaining_length_meters=Decimal('0'), user=self.user)

    def _panel_ctx(self):
        view = StagePanelView()
        view.kwargs = {'code': self.adda.code, 'stage_type': 'layering'}
        req = RequestFactory().get('/')
        req.user = self.user
        view.request = req
        return view.get_context_data()

    def test_registry_dispatch_builds_stage_context(self):
        from production.views.stage_views import _build_layering_context
        ctx = self._panel_ctx()
        req = RequestFactory().get('/')
        req.user = self.user
        builder_keys = set(_build_layering_context(req, self.adda).keys())
        # Registry-driven panel context includes the stage builder's keys + base.
        self.assertTrue(builder_keys <= set(ctx.keys()))
        self.assertEqual(ctx['stage_type'], 'layering')
        self.assertEqual(ctx['adda'].pk, self.adda.pk)

    def test_registry_path_renders_200(self):
        self.client.force_login(self.user)
        url = reverse('production:stage-panel',
                      kwargs={'code': self.adda.code, 'stage_type': 'layering'})
        resp = self.client.get(url + '?embedded=1')
        self.assertEqual(resp.status_code, 200)
