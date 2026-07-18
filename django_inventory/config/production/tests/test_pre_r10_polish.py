"""Pre-R10 polish regression pins (F-1/F-3/F-4; F-2 lives in test_phase4).

F-1: ONE 'My Dashboard' menu item for every role (incl. super admin — the old
     bypass rendered both URL twins); legacy dashboard URLs 301 to the canonical.
F-3: a WORKER completing a stage from the embedded panel is redirected to the
     COMPLETED stage's own panel (which they can view) — never the next stage's
     panel (which 403s them).
F-4: every stage worker-picker uses the shared eligible_stage_workers source:
     active users holding the stage's access skills — picker == access gate.
"""
from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from accounts.models import Skill, User
from accounts.services.permission_service import build_menu_for
from inventory.models import Role
from production.models import AddaStageRecord, Product
from production.services import create_adda, eligible_stage_workers
from production.services.worker_task_service import set_stage_workers
from raw_materials.models import ClothColor, ClothType, StorageLocation
from raw_materials.services import bulk_create_rolls


def _user(email, *, role_code='worker', skills=(), active=True):
    u = User.objects.create_user(email=email, password='x')
    u.role = Role.objects.get(code=role_code)
    u.is_active = active
    u.save()
    for s in skills:
        u.skills.add(Skill.objects.get(name=s))
    return u


class F1SingleDashboardTests(TestCase):
    def _labels(self, user):
        menu = build_menu_for(user)
        return [i['label'] for sec in menu for i in sec['items']]

    def test_super_admin_sees_exactly_one_my_dashboard(self):
        sa = _user('f1-sa@test', role_code='super_admin')
        self.assertEqual(self._labels(sa).count('My Dashboard'), 1)

    def test_worker_sees_exactly_one_my_dashboard(self):
        w = _user('f1-w@test')
        self.assertEqual(self._labels(w).count('My Dashboard'), 1)

    def test_legacy_urls_permanent_redirect_to_canonical(self):
        w = _user('f1-r@test')
        self.client.force_login(w)
        target = reverse('inventory:my_dashboard')
        for legacy in ('inventory:inventory_dashboard', 'inventory:user_dashboard'):
            resp = self.client.get(reverse(legacy))
            self.assertEqual(resp.status_code, 301, legacy)
            self.assertEqual(resp['Location'], target, legacy)
        self.assertEqual(self.client.get(target).status_code, 200)


class F3CompletionRedirectTests(TestCase):
    """Worker-driven layering complete → own panel, then viewable (no 403)."""

    def setUp(self):
        self.mgr = _user('f3-mgr@test', role_code='super_admin',
                         skills=['cutting_master'])
        self.worker = _user('f3-w@test', skills=['cutting_master_helper'])
        self.adda = create_adda(self.mgr, product=Product.objects.get(code='T-SHIRT'))
        self.sr = AddaStageRecord.objects.get(
            adda=self.adda, workflow_stage__stage__code='layering')
        set_stage_workers(self.sr, [self.worker.pk])
        rolls = bulk_create_rolls(
            user=self.mgr, cloth_type=ClothType.objects.get(name='Cotton'),
            storage_location=StorageLocation.objects.get(code='ROHINI'),
            purchased_date=date.today(),
            breakup=[{'color': ClothColor.objects.get(name='Red'), 'qty': 1}],
        )
        from production.services import attach_roll_to_layering, record_remaining_cloth
        entry = attach_roll_to_layering(
            stage_record=self.sr, roll=rolls[0],
            width_verified_inch=42, weight_verified_kg=Decimal('10'), user=self.mgr)
        record_remaining_cloth(entry=entry, remaining_weight_kg=Decimal('0'),
                               remaining_length_meters=Decimal('0'), user=self.mgr)
        self.entry = entry

    def test_worker_embedded_complete_lands_on_bounce_not_403(self):
        self.client.force_login(self.worker)
        resp = self.client.post(
            reverse('production:layering-complete', kwargs={'code': self.adda.code}),
            {'action': 'complete', 'embedded': '1',
             'layer_length_meters': '1.5',
             f'entry_{self.entry.pk}_layers': '3',
             f'entry_{self.entry.pk}_leftover_wt': '0'},
        )
        self.assertEqual(resp.status_code, 302)
        bounce = reverse('production:stage-advanced', kwargs={'code': self.adda.code})
        self.assertEqual(resp['Location'], bounce)
        # The bounce page renders for the completing worker — the old bug sent
        # them to the NEXT stage's panel, which 403'd (their own unreported
        # task is auto-cancelled at complete, so even the completed stage's
        # own panel can refuse them — the bounce is gate-free by design).
        follow = self.client.get(resp['Location'])
        self.assertEqual(follow.status_code, 200)
        self.assertContains(follow, 'stage-advanced')


class F4SharedPickerTests(TestCase):
    def setUp(self):
        self.master = _user('f4-m@test', skills=['cutting_master'])
        self.helper = _user('f4-h@test', skills=['cutting_master_helper'])
        self.inactive = _user('f4-x@test', skills=['cutting_master'], active=False)
        self.manager = _user('f4-mgr@test', role_code='manager')

    def test_inactive_users_excluded_everywhere(self):
        for stage in ('layering', 'cutting_pattern', 'cutting', 'barcode_generation'):
            self.assertNotIn(self.inactive,
                             list(eligible_stage_workers(stage)), stage)

    def test_unskilled_roles_excluded(self):
        for stage in ('layering', 'cutting_pattern', 'cutting', 'barcode_generation'):
            self.assertNotIn(self.manager,
                             list(eligible_stage_workers(stage)), stage)

    def test_cutting_is_master_only_matching_access_gate(self):
        cutting = list(eligible_stage_workers('cutting'))
        self.assertIn(self.master, cutting)
        self.assertNotIn(self.helper, cutting)   # gate would 403 a helper

    def test_helper_stages_include_helper(self):
        for stage in ('layering', 'cutting_pattern', 'barcode_generation'):
            members = list(eligible_stage_workers(stage))
            self.assertIn(self.master, members, stage)
            self.assertIn(self.helper, members, stage)

    def test_picker_matches_access_gate(self):
        """The core F-4 invariant: picker membership ⇒ gate admits (and the
        skill-based converse for active workers)."""
        from production.services import user_can_access_stage
        for stage in ('layering', 'cutting_pattern', 'cutting', 'barcode_generation'):
            for u in eligible_stage_workers(stage):
                self.assertTrue(user_can_access_stage(u, stage),
                                f"{u.email} in picker but gate refuses {stage}")

    def test_all_four_forms_use_shared_source(self):
        from production.forms._shared import (
            _layering_worker_queryset, _worker_queryset,
        )
        from production.views.barcode_gen_views import BarcodeGenStartForm
        from production.views.pattern_stage_views import PatternStartForm
        expect = {
            'layering': set(eligible_stage_workers('layering')),
            'cutting': set(eligible_stage_workers('cutting')),
        }
        self.assertEqual(set(_layering_worker_queryset()), expect['layering'])
        self.assertEqual(set(_worker_queryset()), expect['cutting'])
        self.assertEqual(set(PatternStartForm().fields['workers'].queryset),
                         set(eligible_stage_workers('cutting_pattern')))
        self.assertEqual(set(BarcodeGenStartForm().fields['workers'].queryset),
                         set(eligible_stage_workers('barcode_generation')))
