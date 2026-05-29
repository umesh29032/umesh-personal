"""scan_piece view + mark_status tests — audit follow-up 2026-05-29.

YEH FILE KYU HAI?
─────────────────
Audit ne flag kiya: tracking/views/barcode_views.scan_piece pe koi test
nahi tha. Coverage gaps:
  • scan_piece happy path → 200 + scan_detail render + last_scanned stamp
  • scan_piece 404 on unknown value
  • scan_piece idempotent (repeat scan returns same row, updates timestamp)
  • mark_status validation (rejects unknown status)
  • mark_status lazy creates BatchBarcode + 404 on unknown barcode
"""
from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import Skill, User
from inventory.models import Role
from production.models import Product
from production.services import (
    attach_roll_to_layering, complete_cutting, complete_layering,
    create_adda, record_remaining_cloth, start_layering,
)
from raw_materials.models import ClothColor, ClothType, StorageLocation
from raw_materials.services import bulk_create_rolls
from tracking.models import BatchBarcode
from tracking.services import mark_status


def _user(email='admin@scan.test'):
    role = Role.objects.get(code='super_admin')
    u = User.objects.create_user(
        email=email, password='x', is_superuser=True, is_staff=True,
    )
    u.role = role
    u.save()
    u.skills.add(Skill.objects.get(name='cutting_master'))
    return u


def _completed_adda_with_barcodes(user):
    """Adda all the way through Layering + Cutting → 50 barcodes generated."""
    cotton = ClothType.objects.get(name='Cotton')
    red = ClothColor.objects.get(name='Red')
    loc = StorageLocation.objects.get(code='ROHINI')
    prod = Product.objects.get(code='NIKKAR')
    rolls = bulk_create_rolls(
        user=user, cloth_type=cotton, storage_location=loc,
        purchased_date=date.today(),
        breakup=[{'color': red, 'qty': 1}],
    )
    adda = create_adda(user, product=prod)
    sr = start_layering(adda=adda, worker_ids=[user.pk], user=user)
    entries = [
        attach_roll_to_layering(
            stage_record=sr, roll=r,
            width_verified_inch=40, weight_verified_kg=Decimal('20'),
            user=user,
        ) for r in rolls
    ]
    for e in entries:
        record_remaining_cloth(
            entry=e, remaining_weight_kg=Decimal('0'),
            remaining_length_meters=Decimal('0'), user=user,
        )
    complete_layering(
        adda=adda, duration_minutes=10,
        layer_length_meters=Decimal('1.5'),
        per_entry_layers={e.pk: 3 for e in entries},
        notes='', user=user,
    )
    complete_cutting(
        adda=adda, pieces_cut=50, worker_ids=[user.pk], notes='', user=user,
    )
    adda.refresh_from_db()
    return adda


class ScanPieceViewTests(TestCase):
    """Phone QR scan endpoint /tracking/scan/<value>/ flows."""

    def setUp(self):
        self.user = _user()
        self.adda = _completed_adda_with_barcodes(self.user)
        self.client = Client()
        self.client.force_login(self.user)

    def test_scan_happy_path(self):
        value = f'{self.adda.code}-0001'
        url = reverse('tracking:scan', args=[value])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'tracking/scan_detail.html')
        # BatchBarcode lazy-created with scan stamp.
        bc = BatchBarcode.objects.get(adda=self.adda, piece_seq=1)
        self.assertEqual(bc.value, value)
        self.assertIsNotNone(bc.last_scanned_at)
        self.assertEqual(bc.last_scanned_by, self.user)

    def test_scan_unknown_value_returns_404(self):
        # Adda code matches but seq out of range → no batch hit.
        url = reverse('tracking:scan', args=[f'{self.adda.code}-9999'])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

    def test_scan_malformed_value_returns_404(self):
        # No hyphen + seq pattern. parse_value returns None → 404.
        url = reverse('tracking:scan', args=['garbage'])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

    def test_scan_unknown_adda_returns_404(self):
        url = reverse('tracking:scan', args=['NOPE-0001'])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)

    def test_scan_idempotent_same_row_timestamp_updated(self):
        """Same barcode scan twice = same row, but last_scanned_at moves forward."""
        value = f'{self.adda.code}-0005'
        url = reverse('tracking:scan', args=[value])
        self.client.get(url)
        first = BatchBarcode.objects.get(adda=self.adda, piece_seq=5)
        first_stamp = first.last_scanned_at

        # Second scan — value resolves to same row.
        self.client.get(url)
        second = BatchBarcode.objects.get(adda=self.adda, piece_seq=5)
        self.assertEqual(first.pk, second.pk)
        # Stamp updated (auto_now path) — at least non-decreasing.
        self.assertGreaterEqual(second.last_scanned_at, first_stamp)
        # Still exactly 1 row for piece_seq=5 (no duplicate insert).
        self.assertEqual(
            BatchBarcode.objects.filter(adda=self.adda, piece_seq=5).count(),
            1,
        )

    def test_scan_requires_login(self):
        """Unauthenticated request → redirect to login."""
        self.client.logout()
        url = reverse('tracking:scan', args=[f'{self.adda.code}-0001'])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/app/', resp.url)


class MarkStatusTests(TestCase):
    """mark_status() service validation + lazy row creation."""

    def setUp(self):
        self.user = _user(email='admin@status.test')
        self.adda = _completed_adda_with_barcodes(self.user)

    def test_invalid_status_rejected(self):
        value = f'{self.adda.code}-0001'
        with self.assertRaises(ValidationError):
            mark_status(self.user, value, 'bogus')

    def test_unknown_barcode_rejected(self):
        with self.assertRaises(ValidationError):
            mark_status(self.user, f'{self.adda.code}-9999', 'packed')

    def test_packed_status_lazy_creates_row(self):
        value = f'{self.adda.code}-0010'
        # Pre-condition: no row for seq=10 yet.
        self.assertFalse(BatchBarcode.objects.filter(
            adda=self.adda, piece_seq=10).exists())
        bc = mark_status(self.user, value, 'packed')
        self.assertEqual(bc.status, 'packed')
        self.assertEqual(bc.piece_seq, 10)

    def test_dispatched_after_packed(self):
        value = f'{self.adda.code}-0020'
        mark_status(self.user, value, 'packed')
        bc = mark_status(self.user, value, 'dispatched')
        self.assertEqual(bc.status, 'dispatched')
        # Still one row only.
        self.assertEqual(
            BatchBarcode.objects.filter(adda=self.adda, piece_seq=20).count(),
            1,
        )
