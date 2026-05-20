"""Tests for raw_materials roll service: sequence + bulk create + RBAC gating."""
from datetime import date
from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase, TransactionTestCase

from accounts.models import User
from inventory.models import Role
from raw_materials.models import ClothColor, ClothRoll, ClothType, StorageLocation
from raw_materials.services import _next_roll_id, bulk_create_rolls, update_roll_details


def _superuser():
    role = Role.objects.get(code='super_admin')
    u = User.objects.create_user(email=f'admin-{ClothRoll.objects.count()}-{role.pk}@t.test', password='x', is_superuser=True, is_staff=True)
    u.role = role
    u.save()
    return u


def _karigar_user(suffix=''):
    role = Role.objects.get(code='karigar')
    u = User.objects.create_user(email=f'k{suffix}@t.test', password='x')
    u.role = role
    u.save()
    return u


class RollSequenceTests(TransactionTestCase):
    """nextval('cloth_roll_seq') tests must run as TransactionTestCase since the
    sequence is global state and TestCase wraps each test in a rollback."""

    def test_sequence_returns_zero_padded_codes(self):
        c1 = _next_roll_id()
        c2 = _next_roll_id()
        self.assertTrue(c1.startswith('CR-'))
        self.assertEqual(len(c1), 9)  # CR-NNNNNN
        self.assertNotEqual(c1, c2)


class BulkCreateRollsTests(TestCase):
    def setUp(self):
        self.admin = _superuser()
        self.karigar = _karigar_user()
        self.cotton = ClothType.objects.get(name='Cotton')
        self.red = ClothColor.objects.get(name='Red')
        self.blue = ClothColor.objects.get(name='Blue')
        self.rohini = StorageLocation.objects.get(code='ROHINI')

    def test_bulk_create_with_breakup(self):
        rolls = bulk_create_rolls(
            user=self.admin,
            cloth_type=self.cotton,
            storage_location=self.rohini,
            purchased_date=date.today(),
            breakup=[
                {'color': self.red, 'qty': 3},
                {'color': self.blue, 'qty': 2},
            ],
        )
        self.assertEqual(len(rolls), 5)
        self.assertEqual(sum(1 for r in rolls if r.cloth_color == self.red), 3)
        self.assertEqual(sum(1 for r in rolls if r.cloth_color == self.blue), 2)
        roll_ids = {r.roll_id for r in rolls}
        self.assertEqual(len(roll_ids), 5, "roll_ids must be unique")

    def test_empty_breakup_fails(self):
        with self.assertRaises(ValidationError):
            bulk_create_rolls(
                user=self.admin,
                cloth_type=self.cotton,
                storage_location=self.rohini,
                purchased_date=date.today(),
                breakup=[],
            )

    def test_zero_qty_fails(self):
        with self.assertRaises(ValidationError):
            bulk_create_rolls(
                user=self.admin,
                cloth_type=self.cotton,
                storage_location=self.rohini,
                purchased_date=date.today(),
                breakup=[{'color': self.red, 'qty': 0}],
            )

    def test_karigar_cannot_set_supplier_or_cost(self):
        with self.assertRaises(PermissionDenied):
            bulk_create_rolls(
                user=self.karigar,
                cloth_type=self.cotton,
                storage_location=self.rohini,
                purchased_date=date.today(),
                breakup=[{'color': self.red, 'qty': 1}],
                supplier='Acme Mills',
                cost_per_kg=Decimal('120'),
            )

    def test_archived_color_is_rejected(self):
        self.red.is_active = False
        self.red.save(update_fields=['is_active'])
        with self.assertRaises(ValidationError):
            bulk_create_rolls(
                user=self.admin,
                cloth_type=self.cotton,
                storage_location=self.rohini,
                purchased_date=date.today(),
                breakup=[{'color': self.red, 'qty': 1}],
            )


class UpdateRollDetailsTests(TestCase):
    def setUp(self):
        self.admin = _superuser()
        self.cotton = ClothType.objects.get(name='Cotton')
        self.red = ClothColor.objects.get(name='Red')
        self.rohini = StorageLocation.objects.get(code='ROHINI')
        rolls = bulk_create_rolls(
            user=self.admin, cloth_type=self.cotton, storage_location=self.rohini,
            purchased_date=date.today(),
            breakup=[{'color': self.red, 'qty': 1}],
        )
        self.roll = rolls[0]

    def test_updates_width_and_weight(self):
        self.assertIsNone(self.roll.width_inch)
        self.assertIsNone(self.roll.weight_kg)
        update_roll_details(
            user=self.admin, roll=self.roll,
            width_inch=42, weight_kg=Decimal('25.50'),
        )
        self.roll.refresh_from_db()
        self.assertEqual(self.roll.width_inch, 42)
        self.assertEqual(self.roll.weight_kg, Decimal('25.50'))

    def test_survives_mutated_instance(self):
        """Regression: ModelForm._post_clean mutates instance before service runs.

        Simulates UpdateView behaviour where form.instance.width_inch is already
        set to the new value before update_roll_details receives it. Service
        must refresh_from_db internally to recover OLD value for diff.
        """
        # Pre-mutate in-memory instance (mimics what ModelForm does to form.instance)
        self.roll.width_inch = 42
        # Caller passes the SAME new value — without refresh_from_db, diff would
        # be False (in-memory 42 == param 42) and nothing would save.
        update_roll_details(user=self.admin, roll=self.roll, width_inch=42)
        # Verify the DB row actually got updated despite the pre-mutation
        fresh = ClothRoll.objects.get(pk=self.roll.pk)
        self.assertEqual(fresh.width_inch, 42)

    def test_blocks_edit_on_used_roll(self):
        self.roll.status = ClothRoll.Status.USED
        self.roll.save(update_fields=['status'])
        with self.assertRaises(ValidationError):
            update_roll_details(user=self.admin, roll=self.roll, width_inch=40)
