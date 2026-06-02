"""End-to-end golden path: bulk rolls → Adda → layering → cutting → barcodes."""
from datetime import date
from decimal import Decimal

from django.test import TestCase

from accounts.models import User
from inventory.models import Role
from production.models import Adda, Product
from production.services import (
    attach_roll_to_layering, complete_cutting, complete_layering,
    create_adda, record_remaining_cloth, start_layering,
)
from raw_materials.models import ClothColor, ClothType, StorageLocation
from raw_materials.services import bulk_create_rolls
from tracking.models import AddaHistory, ClothRollHistory


def _superuser():
    role = Role.objects.get(code='super_admin')
    u = User.objects.create_user(email='admin@golden.test', password='x', is_superuser=True, is_staff=True)
    u.role = role
    u.save()
    return u


class GoldenPathTest(TestCase):
    def test_full_flow_produces_barcodes_and_history(self):
        user = _superuser()
        # Phase 4: create_adda requires ≥1 skilled user in the system
        from accounts.models import Skill
        user.skills.add(Skill.objects.get(name='cutting_master'))
        cotton = ClothType.objects.get(name='Cotton')
        red = ClothColor.objects.get(name='Red')
        blue = ClothColor.objects.get(name='Blue')
        location = StorageLocation.objects.get(code='ROHINI')
        nikkar = Product.objects.get(code='NIKKAR')

        # 1. Bulk create 5 rolls
        rolls = bulk_create_rolls(
            user=user,
            cloth_type=cotton,
            storage_location=location,
            purchased_date=date.today(),
            breakup=[{'color': red, 'qty': 3}, {'color': blue, 'qty': 2}],
        )
        self.assertEqual(len(rolls), 5)
        self.assertTrue(all(r.roll_id.startswith('CR-') for r in rolls))

        # 2. Start Adda
        adda = create_adda(user, product=nikkar)
        self.assertEqual(adda.code, 'NIKKAR-001')

        # 3. Manager refines workers on the auto-created Layering stage_record
        sr = start_layering(adda=adda, worker_ids=[user.pk], user=user)

        # 4. Attach each roll inside the layering workspace (status flips to USED here)
        entries = []
        for r in rolls:
            entries.append(attach_roll_to_layering(
                stage_record=sr, roll=r,
                width_verified_inch=42, weight_verified_kg=Decimal('25.0'),
                user=user,
            ))

        adda.refresh_from_db()
        self.assertEqual(adda.rolls.count(), 5)

        # 5. Leftover mandatory per roll before complete (Phase 6)
        for e in entries:
            record_remaining_cloth(
                entry=e, remaining_weight_kg=Decimal('0'),
                remaining_length_meters=Decimal('0'), user=user,
            )
        # 6. Complete layering — overall layer length + per-roll layer breakup
        complete_layering(
            adda=adda, duration_minutes=30,
            layer_length_meters=Decimal('2.0'),
            per_entry_layers={e.pk: 2 for e in entries},
            notes='', user=user,
        )
        adda.refresh_from_db()
        self.assertEqual(adda.current_stage.stage_type, 'cutting')

        # 6. Complete cutting — generates 100 barcodes
        complete_cutting(adda=adda, pieces_cut=100,
                         worker_ids=[user.pk], notes='', user=user)
        adda.refresh_from_db()

        self.assertEqual(adda.status, Adda.Status.COMPLETED)
        self.assertIsNone(adda.current_stage)
        # PR6: BarcodeBatch range covers all 100 pieces; BatchBarcode lazy.
        from tracking.models import BarcodeBatch
        batches = list(BarcodeBatch.objects.filter(adda=adda))
        self.assertEqual(len(batches), 1)
        self.assertEqual(batches[0].total_pieces, 100)
        self.assertEqual(batches[0].start_value, 'NIKKAR-001-0001')
        self.assertEqual(batches[0].end_value, 'NIKKAR-001-0100')

        # 7. History tables populated
        self.assertGreaterEqual(AddaHistory.objects.filter(adda=adda).count(), 4)
        # at least: CREATED + 5 ROLL_ASSIGNED + 2 STAGE_ADVANCED + COMPLETED
        # Roll history: each roll has CREATED + STATUS_CHANGED
        self.assertEqual(ClothRollHistory.objects.filter(roll=rolls[0]).count(), 2)
