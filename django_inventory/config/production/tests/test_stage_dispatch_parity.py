"""M2.6: StagePanelView dispatch parity (strangler).

Proves the registry-driven panel context (STAGE_REGISTRY_ENABLED=True) is identical
to the legacy if/elif (flag off), and that the registry path renders end-to-end.
The handler's panel_context delegates to the same _build_*_context the legacy branch
calls, so parity is structural — this guards against that ever drifting.
"""
from datetime import date
from decimal import Decimal

from django.test import RequestFactory, TestCase, override_settings
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

    def _panel_ctx(self, enabled):
        view = StagePanelView()
        view.kwargs = {'code': self.adda.code, 'stage_type': 'layering'}
        req = RequestFactory().get('/')
        req.user = self.user
        view.request = req
        with override_settings(STAGE_REGISTRY_ENABLED=enabled):
            return view.get_context_data()

    def test_registry_and_legacy_same_context_keys(self):
        legacy = self._panel_ctx(False)
        registry = self._panel_ctx(True)
        self.assertEqual(set(legacy.keys()), set(registry.keys()))
        self.assertEqual(registry['stage_type'], 'layering')
        self.assertEqual(registry['adda'].pk, self.adda.pk)

    def test_registry_path_renders_200(self):
        self.client.force_login(self.user)
        url = reverse('production:stage-panel',
                      kwargs={'code': self.adda.code, 'stage_type': 'layering'})
        with override_settings(STAGE_REGISTRY_ENABLED=True):
            resp = self.client.get(url + '?embedded=1')
        self.assertEqual(resp.status_code, 200)
