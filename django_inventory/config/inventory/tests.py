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
        resp = self.client.get(reverse('inventory:my_dashboard'))
        self.assertEqual(resp.status_code, 200)
        self.assertIsNone(resp.context.get('helper_data'))

    def test_helper_user_sees_helper_data_with_active_layering(self):
        helper = _make_user('h@dash.test', role_code='worker',
                            skill_names=['cutting_master_helper'])
        self.client.force_login(helper)
        # C-2 (freeze closeout): the board is access-gated AND assignment-
        # scoped for non-management — an UNASSIGNED helper sees the board
        # section but ZERO rows (was: every active layering factory-wide).
        adda, sr, _entry = _start_layering_on_new_adda(self.admin)

        resp = self.client.get(reverse('inventory:my_dashboard'))
        self.assertEqual(resp.status_code, 200)
        data = resp.context['helper_data']
        self.assertIsNotNone(data)
        self.assertEqual(len(data['active_layering']), 0)
        self.assertEqual(data['completed_count'], 0)
        # Assign them → the row appears (manager assignment = the only source).
        from production.services.worker_task_service import set_stage_workers
        set_stage_workers(sr, [helper.pk])
        data2 = self.client.get(reverse('inventory:my_dashboard')).context['helper_data']
        self.assertEqual(len(data2['active_layering']), 1)
        self.assertEqual(data2['active_assigned_count'], 1)

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
        resp = self.client.get(reverse('inventory:my_dashboard'))
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


class SidebarSingleSourceTest(TestCase):
    """P3.4: the DB SidebarItemRule rows must not drift from the code SIDEBAR
    registry (the single source of truth for menu items). Every rule must point at
    a real menu item — an orphan means a rename/removal left stale access data."""

    def test_no_orphan_sidebar_rules(self):
        from accounts.models import SidebarItemRule
        from accounts.services.permission_service import SIDEBAR
        code_url_names = {item.url_name for section in SIDEBAR for item in section.items}
        rule_url_names = set(SidebarItemRule.objects.values_list('url_name', flat=True))
        orphans = rule_url_names - code_url_names
        self.assertEqual(
            orphans, set(),
            f"SidebarItemRule rows reference menu items absent from the code SIDEBAR "
            f"registry (drift from a rename/removal): {orphans}",
        )


class RoleDeleteGuardTests(TestCase):
    """PA-05A-2: deleting a Role must be refused while it is assigned to ANY user
    — primary role (`users`) OR stacked via extra_roles (`extra_users`). The
    extra_roles M2M would otherwise cascade and silently strip the role."""

    def setUp(self):
        self.admin = _make_user('rdg-admin@t.com', role_code='super_admin', is_super=True)
        self.client.force_login(self.admin)

    def _delete(self, role):
        return self.client.post(reverse('inventory:role_delete', args=[role.pk]))

    def test_blocked_when_used_as_extra_role(self):
        role = Role.objects.create(name='Extra Only', code='extra_only')
        u = _make_user('rdg-u@t.com', role_code='worker')
        u.extra_roles.add(role)
        self._delete(role)
        self.assertTrue(Role.objects.filter(pk=role.pk).exists())  # not deleted

    def test_blocked_when_system_role(self):
        sysrole = Role.objects.get(code='manager')  # seeded, is_system
        self._delete(sysrole)
        self.assertTrue(Role.objects.filter(pk=sysrole.pk).exists())

    def test_deletes_when_unused_and_not_system(self):
        role = Role.objects.create(name='Disposable', code='disposable')
        self._delete(role)
        self.assertFalse(Role.objects.filter(pk=role.pk).exists())


class RolePermissionCurationTests(TestCase):
    """OWN-D carry-in fix (2026-07-13): the RoleForm.permissions field queryset
    is the form's VALIDATION gate — only pks in it can be POSTed. It must equal
    the CURATED editor allowlist (ROLE_EDITOR_SECTIONS content types), not the
    whole app (ROLE_EDITABLE_APPS). The app-level filter let a hand-crafted POST
    persist a grant on a service-only model the editor never renders (e.g.
    production.change_machinetype), and live view gates (user_has_perm) honored it."""

    def setUp(self):
        self.admin = _make_user('rpc-admin@t.com', role_code='super_admin', is_super=True)
        self.client.force_login(self.admin)

    def test_queryset_equals_curated_allowlist(self):
        from django.contrib.auth.models import Permission
        from accounts.services.permission_service import permissions_qs_by_app
        from inventory.forms import RoleForm
        offered = set(RoleForm().fields['permissions'].queryset.values_list('pk', flat=True))
        curated = {p.pk for p in permissions_qs_by_app()}
        self.assertEqual(offered, curated)
        # an in-app-but-non-curated perm (service-only model) must NOT be offered
        mt = Permission.objects.get(content_type__app_label='production', codename='change_machinetype')
        self.assertNotIn(mt.pk, offered)

    def test_handcrafted_noncurated_perm_rejected(self):
        from django.contrib.auth.models import Permission
        role = Role.objects.create(name='Carry In', code='carry_in')
        view_stage = Permission.objects.get(content_type__app_label='production', codename='view_stage')
        mt = Permission.objects.get(content_type__app_label='production', codename='change_machinetype')
        resp = self.client.post(reverse('inventory:role_edit', args=[role.pk]), {
            'name': role.name, 'code': role.code, 'description': '',
            'permissions': [view_stage.pk, mt.pk],  # mt is offered by app but not curated
        })
        self.assertEqual(resp.status_code, 200)  # form re-renders with an error
        self.assertIn('permissions', resp.context['form'].errors)
        self.assertFalse(role.permissions.filter(pk=mt.pk).exists())  # nothing persisted


class SidebarAccessSaveTests(TestCase):
    """RCP-1A F1: the sidebar-access save is SERVICE-owned (Law 4 — the view only
    parses POST into primitives). Behaviour preserved: checkbox lists update the
    M2Ms, super_admin is NEVER persisted even if posted, an un-posted rule clears."""

    def setUp(self):
        self.admin = _make_user('sb-admin@test.test', role_code='super_admin', is_super=True)
        self.manager = _make_user('sb-mgr@test.test', role_code='manager')
        from accounts.models import SidebarItemRule
        self.rule = SidebarItemRule.objects.create(
            url_name='inventory:my_dashboard', section='Main', label='Dashboard')

    def test_post_updates_roles_and_excludes_super_admin(self):
        from accounts.models import SidebarItemRule
        sa_role = Role.objects.get(code='super_admin')
        mgr_role = Role.objects.get(code='manager')
        self.client.force_login(self.admin)
        resp = self.client.post(reverse('inventory:sidebar-access'), {
            f'roles_{self.rule.id}': [str(mgr_role.id), str(sa_role.id)],
        })
        self.assertEqual(resp.status_code, 302)
        rule = SidebarItemRule.objects.get(pk=self.rule.pk)
        codes = set(rule.allowed_roles.values_list('code', flat=True))
        self.assertEqual(codes, {'manager'})  # SA posted but excluded at write

    def test_unposted_rule_is_cleared(self):
        from accounts.models import SidebarItemRule
        self.rule.allowed_roles.set([Role.objects.get(code='manager')])
        self.client.force_login(self.admin)
        resp = self.client.post(reverse('inventory:sidebar-access'), {})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            SidebarItemRule.objects.get(pk=self.rule.pk).allowed_roles.count(), 0)

    def test_service_is_the_writer(self):
        # Law-4 pin: the view module performs no M2M writes itself.
        import inspect
        from inventory.views import sidebar_access_views as v
        src = inspect.getsource(v.SidebarAccessListView.post)
        self.assertIn('save_sidebar_rules', src)
        self.assertNotIn('.set(', src)
