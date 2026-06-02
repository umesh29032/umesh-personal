"""Inventory app tests — dashboard role gating + helper-skill section.

YEH FILE KYU HAI?
─────────────────
user_dashboard view tests:
  • Non-helper user → no helper_data, only my_active_stages
  • Helper user → helper_data populated with active layering + personal stats
  • Helper sees ALL active layering (not just assigned) — spec requirement
"""
from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from accounts.models import Skill, User
from inventory.models import Role
from production.models import Product
from production.services import (
    attach_roll_to_layering, complete_layering, create_adda,
    record_remaining_cloth, start_layering,
)
from raw_materials.models import ClothColor, ClothType, StorageLocation
from raw_materials.services import bulk_create_rolls


def _make_user(email, *, role_code, is_super=False, skill_names=()):
    role = Role.objects.get(code=role_code)
    u = User.objects.create_user(
        email=email, password='pw', is_superuser=is_super, is_staff=is_super,
    )
    u.role = role
    u.save()
    for s in skill_names:
        u.skills.add(Skill.objects.get(name=s))
    return u


def _start_layering_on_new_adda(admin):
    """Helper: spin up a fresh Adda with Layering started + 1 roll attached.

    Returns (adda, stage_record, attached_entry).
    """
    cotton = ClothType.objects.get(name='Cotton')
    red = ClothColor.objects.get(name='Red')
    loc = StorageLocation.objects.get(code='ROHINI')
    product = Product.objects.get(code='T-SHIRT')
    rolls = bulk_create_rolls(
        user=admin, cloth_type=cotton, storage_location=loc,
        purchased_date=date.today(),
        breakup=[{'color': red, 'qty': 1}],
    )
    adda = create_adda(admin, product=product)
    sr = start_layering(adda=adda, worker_ids=[admin.pk], user=admin)
    entry = attach_roll_to_layering(
        stage_record=sr, roll=rolls[0],
        width_verified_inch=42, weight_verified_kg=Decimal('25'),
        user=admin,
    )
    return adda, sr, entry


class UserDashboardHelperTests(TestCase):
    def setUp(self):
        # Admin needs cutting_master skill to start the layering
        self.admin = _make_user('admin@dash.test', role_code='super_admin',
                                is_super=True, skill_names=['cutting_master'])

    def test_non_helper_user_has_no_helper_data(self):
        karigar = _make_user('k@dash.test', role_code='worker')
        self.client.force_login(karigar)
        resp = self.client.get(reverse('inventory:user_dashboard'))
        self.assertEqual(resp.status_code, 200)
        self.assertIsNone(resp.context.get('helper_data'))

    def test_helper_user_sees_helper_data_with_active_layering(self):
        helper = _make_user('h@dash.test', role_code='worker',
                            skill_names=['cutting_master_helper'])
        self.client.force_login(helper)
        # Spin up an active layering elsewhere — helper not assigned, but should still see it.
        _start_layering_on_new_adda(self.admin)  # returns (adda, sr, entry) — unused

        resp = self.client.get(reverse('inventory:user_dashboard'))
        self.assertEqual(resp.status_code, 200)
        data = resp.context['helper_data']
        self.assertIsNotNone(data)
        # Spec: helper sees ALL active Layering, even if not assigned to this one.
        self.assertEqual(len(data['active_layering']), 1)
        self.assertEqual(data['active_assigned_count'], 0)
        self.assertEqual(data['completed_count'], 0)

    def test_helper_stats_update_after_completion(self):
        helper = _make_user('h2@dash.test', role_code='worker',
                            skill_names=['cutting_master_helper'])
        adda, _sr, entry = _start_layering_on_new_adda(self.admin)
        # Leftover mandatory (Phase 6) — record before complete
        record_remaining_cloth(
            entry=entry, remaining_weight_kg=Decimal('0'),
            remaining_length_meters=Decimal('0'), user=self.admin,
        )
        # Helper completes the layering — superuser-bypass not in play; helper has the skill.
        complete_layering(
            adda=adda, duration_minutes=22,
            layer_length_meters=Decimal('1.5'),
            per_entry_layers={entry.pk: 4},
            notes='', user=helper,
        )
        self.client.force_login(helper)
        resp = self.client.get(reverse('inventory:user_dashboard'))
        data = resp.context['helper_data']
        self.assertEqual(data['completed_count'], 1)
        self.assertEqual(data['total_layers'], 4)
        self.assertEqual(data['total_minutes'], 22)
        # Layering is finished → no active layerings
        self.assertEqual(len(data['active_layering']), 0)


class AccessControlHubTests(TestCase):
    """The unified RBAC overview page: renders for super_admin, 403 for others
    (direct-URL protection — fails safe, not just sidebar-hidden)."""

    def setUp(self):
        self.admin = _make_user('ac-admin@test.test', role_code='super_admin', is_super=True)
        self.manager = _make_user('ac-mgr@test.test', role_code='manager')
        self.karigar = _make_user('ac-kar@test.test', role_code='worker')

    def test_super_admin_sees_all_matrices(self):
        self.client.force_login(self.admin)
        resp = self.client.get(reverse('inventory:access-control'))
        self.assertEqual(resp.status_code, 200)
        for key in ('roles', 'page_sections', 'stage_rows', 'user_rows', 'role_summary'):
            self.assertIn(key, resp.context)
        # Page-visibility matrix is built from the SIDEBAR registry.
        self.assertTrue(resp.context['page_sections'])

    def test_manager_denied_direct_url(self):
        self.client.force_login(self.manager)
        # Managed panel item → SidebarAccessMiddleware redirects (302) with a
        # message, rather than a bare 403. Denied either way.
        self.assertEqual(self.client.get(reverse('inventory:access-control')).status_code, 302)

    def test_karigar_denied_direct_url(self):
        self.client.force_login(self.karigar)
        # Managed panel item → SidebarAccessMiddleware redirects (302) with a
        # message, rather than a bare 403. Denied either way.
        self.assertEqual(self.client.get(reverse('inventory:access-control')).status_code, 302)
