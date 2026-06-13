"""M2.2: LayeringHandler adapter parity.

Proves (a) autodiscover registered the handler under the layering code, and
(b) completing via the registry-dispatched handler produces the same outcome as
the existing service (the handler delegates to it). Adapter-only — no code moved.
"""
from datetime import date
from decimal import Decimal

from django.test import TestCase

from accounts.models import Skill, User
from inventory.models import Role
from production.constants import STAGE_LAYERING
from production.models import LayeringRecord, Product
from production.services import (
    attach_roll_to_layering, create_adda, get_layering_snapshot,
    record_remaining_cloth, start_layering,
)
from production.stages import base
from production.stages.layering.handler import LayeringHandler
from raw_materials.models import ClothColor, ClothType, StorageLocation
from raw_materials.services import bulk_create_rolls


class LayeringHandlerParityTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='lh@test', password='x', is_superuser=True, is_staff=True)
        self.user.role = Role.objects.get(code='super_admin')
        self.user.save()
        self.user.skills.add(
            Skill.objects.get(name='cutting_master'),
            Skill.objects.get(name='cutting_master_helper'))
        self.nikkar = Product.objects.get(code='NIKKAR')

    def _ready_adda(self):
        """An Adda whose Layering stage is fully set up and ready to complete."""
        cotton = ClothType.objects.get(name='Cotton')
        red = ClothColor.objects.get(name='Red')
        loc = StorageLocation.objects.get(code='ROHINI')
        rolls = bulk_create_rolls(
            user=self.user, cloth_type=cotton, storage_location=loc,
            purchased_date=date.today(), breakup=[{'color': red, 'qty': 2}])
        adda = create_adda(self.user, product=self.nikkar)
        sr = start_layering(adda=adda, worker_ids=[self.user.pk], user=self.user)
        entries = []
        for r in rolls:
            e = attach_roll_to_layering(
                stage_record=sr, roll=r, width_verified_inch=42,
                weight_verified_kg=Decimal('25.0'), user=self.user)
            entries.append(e)
            record_remaining_cloth(
                entry=e, remaining_weight_kg=Decimal('0'),
                remaining_length_meters=Decimal('0'), user=self.user)
        return adda, sr, entries

    def test_autodiscover_registered_layering_handler(self):
        handler = base.get(STAGE_LAYERING)
        self.assertIsInstance(handler, LayeringHandler)
        self.assertEqual(handler.template_partial, 'production/_stage_panel_layering.html')

    def test_snapshot_matches_service(self):
        adda, sr, _ = self._ready_adda()
        snap = base.get(STAGE_LAYERING).snapshot(adda)
        # Delegates to get_layering_snapshot — same dict shape (values include live
        # QuerySets, so compare keys, not the dicts directly).
        self.assertEqual(set(snap.keys()), set(get_layering_snapshot(adda).keys()))
        self.assertEqual(snap['state'], 'in_progress')

    def test_complete_via_handler_advances_like_service(self):
        adda, sr, entries = self._ready_adda()
        handler = base.get(STAGE_LAYERING)
        handler.complete(
            user_id=self.user.pk, adda=adda, record=sr,
            data={
                'duration_minutes': 30,
                'layer_length_meters': Decimal('2.0'),
                'per_entry_layers': {e.pk: 2 for e in entries},
                'notes': '',
            })
        adda.refresh_from_db()
        self.assertEqual(adda.current_stage.stage_type, 'cutting')   # advanced
        sr.refresh_from_db()
        self.assertIsNotNone(sr.completed_at)
        self.assertTrue(LayeringRecord.objects.filter(stage_record=sr).exists())
