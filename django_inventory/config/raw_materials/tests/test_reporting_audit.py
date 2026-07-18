"""Phase 13 — reporting/filter/visibility regressions on the roll list + dashboards."""
from datetime import date

from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from inventory.models import Role
from raw_materials.models import ClothColor, ClothRoll, ClothType, StorageLocation
from tracking.models import ClothRollHistory


def _user(email, role_code, *, is_super=False):
    u = User.objects.create_user(email=email, password='x',
                                 is_superuser=is_super, is_staff=is_super)
    u.role = Role.objects.get(code=role_code)
    u.save()
    return u


class RollListReportingTests(TestCase):
    def setUp(self):
        self.worker = _user('rl-worker@t.test', 'worker')           # non-financial
        self.admin = _user('rl-admin@t.test', 'super_admin', is_super=True)  # financial
        self.ct = ClothType.objects.get(name='Cotton')
        self.cc = ClothColor.objects.get(name='Red')
        self.sl = StorageLocation.objects.get(code='ROHINI')
        self.roll = ClothRoll.objects.create(
            roll_id='CR-RPT001', purchased_date=date(2026, 6, 15),
            cloth_type=self.ct, cloth_color=self.cc, storage_location=self.sl)

    # ── PA-13-2: non-numeric id filter must not 500 ──────────────────────────
    # (H-3 2026-07-06: worker role is sidebar-locked out of raw-materials pages —
    # these filter/chip pins exercise the VIEW, so they run as admin now.)
    def test_non_numeric_id_filters_do_not_500(self):
        self.client.force_login(self.admin)
        for qs in ('cloth_type=abc', 'color=xyz', 'location=!!', 'cloth_type=1; DROP'):
            resp = self.client.get(reverse('raw_materials:roll-list') + '?' + qs)
            self.assertEqual(resp.status_code, 200, f"500 on ?{qs}")

    # ── PA-13-5: invalid status → no misleading chip, full list ──────────────
    def test_garbage_status_shows_no_status_chip(self):
        self.client.force_login(self.admin)
        resp = self.client.get(reverse('raw_materials:roll-list') + '?status=garbage')
        self.assertEqual(resp.status_code, 200)
        chips = resp.context['active_filter_chips']
        self.assertFalse([c for c in chips if c['group'] == 'Status'],
                         "an invalid status must not render a Status filter chip")

    # ── PA-13-3: cost_per_kg/supplier change values hidden from non-financial ─
    def _cost_history(self):
        ClothRollHistory.objects.create(
            roll=self.roll, change_type=ClothRollHistory.ChangeType.WEIGHT_UPDATED,
            field_name='cost_per_kg', old_value='', new_value='999.77', actor=self.admin)

    def test_roll_list_timelog_hides_cost_from_worker(self):
        self._cost_history()
        self.client.force_login(self.worker)
        body = self.client.get(reverse('raw_materials:roll-list')).content.decode()
        self.assertNotIn('999.77', body)        # non-financial viewer: value hidden

    def test_roll_list_timelog_shows_cost_to_financial(self):
        self._cost_history()
        self.client.force_login(self.admin)
        body = self.client.get(reverse('raw_materials:roll-list')).content.decode()
        self.assertIn('999.77', body)           # financial viewer: value shown
