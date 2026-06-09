"""Tests for raw_materials master service (archive/restore/hard_delete)."""
from django.core.exceptions import PermissionDenied
from django.test import TestCase

from accounts.models import User, UserType
from inventory.models import Role
from raw_materials.models import ClothColor, ClothType
from raw_materials.services import archive_master, hard_delete_master, restore_master


class MasterServiceTests(TestCase):
    def setUp(self):
        super_admin_role = Role.objects.get(code='super_admin')
        self.admin = User.objects.create_user(email='admin@test.com', password='x', is_superuser=True, is_staff=True)
        self.admin.role = super_admin_role
        self.admin.save()
        # A nobody user with no role at all. UserType 'normal' maps to None role.
        normal_type = UserType.objects.filter(code='normal').first()
        self.no_role = User.objects.create_user(email='nobody@test.com', password='x')
        self.no_role.user_type = normal_type
        self.no_role.save(update_fields=['user_type'])

    def test_archive_flips_is_active(self):
        ct = ClothType.objects.create(name='SilkSample')
        archive_master(self.admin, ct)
        ct.refresh_from_db()
        self.assertFalse(ct.is_active)

    def test_archive_is_idempotent(self):
        ct = ClothType.objects.create(name='LinenSample', is_active=False)
        archive_master(self.admin, ct)  # no error
        ct.refresh_from_db()
        self.assertFalse(ct.is_active)

    def test_restore_flips_is_active(self):
        ct = ClothType.objects.create(name='Velvet', is_active=False)
        restore_master(self.admin, ct)
        ct.refresh_from_db()
        self.assertTrue(ct.is_active)

    def test_no_role_user_cannot_archive(self):
        ct = ClothType.objects.create(name='Denim')
        with self.assertRaises(PermissionDenied):
            archive_master(self.no_role, ct)

    def test_hard_delete_without_references_succeeds(self):
        cc = ClothColor.objects.create(name='OrangeTest')
        hard_delete_master(self.admin, cc)
        self.assertFalse(ClothColor.objects.filter(pk=cc.pk).exists())
