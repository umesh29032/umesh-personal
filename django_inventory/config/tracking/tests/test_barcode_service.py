"""Tests for tracking barcode_service."""
from datetime import date
from decimal import Decimal

from django.db import IntegrityError
from django.test import TestCase

from accounts.models import User
from inventory.models import Role
from production.models import Product
from production.services import (
    attach_roll_to_layering, complete_cutting, complete_layering,
    create_adda, record_remaining_cloth, start_layering,
)
from raw_materials.models import ClothColor, ClothType, StorageLocation
from raw_materials.services import bulk_create_rolls
from tracking.models import BatchBarcode
from tracking.services import generate_for_cutting


def _user():
    role = Role.objects.get(code='super_admin')
    u = User.objects.create_user(email='admin@bc.test', password='x', is_superuser=True, is_staff=True)
    u.role = role
    u.save()
    return u


def _seed_completed_cutting():
    """Helper: build an Adda all the way through Layering, leaving it at Cutting stage."""
    from accounts.models import Skill

    user = _user()
    # Phase 4: create_adda requires ≥1 skilled user before the call
    user.skills.add(Skill.objects.get(name='cutting_master'))
    cotton = ClothType.objects.get(name='Cotton')
    red = ClothColor.objects.get(name='Red')
    loc = StorageLocation.objects.get(code='ROHINI')
    prod = Product.objects.get(code='NIKKAR')
    rolls = bulk_create_rolls(user=user, cloth_type=cotton, storage_location=loc,
                              purchased_date=date.today(),
                              breakup=[{'color': red, 'qty': 1}])
    adda = create_adda(user, product=prod)
    sr = start_layering(adda=adda, worker_ids=[user.pk], user=user)
    entries = []
    for r in rolls:
        entries.append(attach_roll_to_layering(
            stage_record=sr, roll=r,
            width_verified_inch=40, weight_verified_kg=Decimal('20'),
            user=user,
        ))
    # Leftover record mandatory before complete
    for e in entries:
        record_remaining_cloth(
            entry=e, remaining_weight_kg=Decimal('0'), remaining_length_meters=Decimal('0'),
            user=user,
        )
    complete_layering(
        adda=adda, duration_minutes=10,
        layer_length_meters=Decimal('1.5'),
        per_entry_layers={e.pk: 3 for e in entries},
        notes='', user=user,
    )
    return user, adda


class BarcodeGenerationTests(TestCase):
    def test_pieces_count_matches_barcode_count(self):
        user, adda = _seed_completed_cutting()
        complete_cutting(adda=adda, pieces_cut=7, worker_ids=[user.pk], notes='', user=user)
        self.assertEqual(BatchBarcode.objects.filter(adda=adda).count(), 7)

    def test_barcode_values_are_unique_and_sequential(self):
        user, adda = _seed_completed_cutting()
        complete_cutting(adda=adda, pieces_cut=4, worker_ids=[user.pk], notes='', user=user)
        bcs = list(BatchBarcode.objects.filter(adda=adda).order_by('piece_seq'))
        values = [b.value for b in bcs]
        self.assertEqual(values, [
            f'{adda.code}-0001', f'{adda.code}-0002',
            f'{adda.code}-0003', f'{adda.code}-0004',
        ])
        self.assertEqual(len(set(values)), 4)
