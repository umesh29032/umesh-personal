"""Campaign M9 (2026-07-11): roll edit/assign = MANAGEMENT acts —
the old ProductionRoleMixin let any worker mutate stock + cost truth
(found live in browser; same class as the M3 AddaCreateView fix)."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounts.models import Role
from raw_materials.models import (ClothColor, ClothRoll, ClothType,
                                  StorageLocation)

User = get_user_model()


class RollMasterDataGateTests(TestCase):
    def test_worker_cannot_edit_or_assign_roll(self):
        wk = Role.objects.get_or_create(code='worker', defaults={'name': 'W'})[0]
        worker = User.objects.create_user('m9w@test.local', password='x',
                                          role=wk)
        mgr_role = Role.objects.get_or_create(code='manager',
                                              defaults={'name': 'M'})[0]
        manager = User.objects.create_user('m9m@test.local', password='x',
                                           role=mgr_role)
        from django.utils import timezone
        roll = ClothRoll.objects.create(
            cloth_type=ClothType.objects.create(name='M9T'),
            cloth_color=ClothColor.objects.create(name='M9C'),
            storage_location=StorageLocation.objects.create(
                name='M9L', code='M9L'),
            purchased_date=timezone.now().date(),
        )
        edit = reverse('raw_materials:roll-edit', args=[roll.pk])
        assign = reverse('raw_materials:roll-assign', args=[roll.pk])
        self.client.force_login(worker)
        self.assertEqual(self.client.get(edit).status_code, 403)
        self.assertEqual(self.client.get(assign).status_code, 403)
        self.client.force_login(manager)
        self.assertEqual(self.client.get(edit).status_code, 200)
        self.assertEqual(self.client.get(assign).status_code, 200)
