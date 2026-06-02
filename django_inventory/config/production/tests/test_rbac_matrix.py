"""RBAC review (2026-06-02) — direct-URL protection matrix.

Asserts the master-spec access expectations the review called out:
  /production/products/  → Super Admin ✔, Manager ✔, Worker ✖, no-role ✖
  /tracking/scan/<v>/    → production roles only (audit-field mutation)
"""
from django.test import TestCase
from django.urls import reverse

from accounts.models import Skill, User
from inventory.models import Role
from production.models import Product, Stage
from production.services import create_adda


def _user(email, *, role_code=None, user_type='worker', is_super=False, skills=()):
    u = User.objects.create_user(
        email=email, password='pw', is_superuser=is_super, is_staff=is_super,
        user_type=user_type,
    )
    if role_code:
        u.role = Role.objects.get(code=role_code)
        u.save()
    for s in skills:
        u.skills.add(Skill.objects.get(name=s))
    return u


class ProductsAccessMatrixTests(TestCase):
    def setUp(self):
        self.super_admin = _user('m-super@test.test', role_code='super_admin', is_super=True)
        self.manager = _user('m-mgr@test.test', role_code='manager')          # "Admin" tier
        self.worker = _user('m-worker@test.test', role_code='worker')        # Worker
        # 'normal' type + no role → no privileged role at all (Supplier analog).
        self.norole = _user('m-none@test.test', role_code=None, user_type='normal')
        self.url = reverse('production:product-list')

    def test_super_admin_allowed(self):
        self.client.force_login(self.super_admin)
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_manager_allowed(self):
        self.client.force_login(self.manager)
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_worker_denied(self):
        # product-list is a managed sidebar item → middleware redirects (302).
        self.client.force_login(self.worker)
        self.assertEqual(self.client.get(self.url).status_code, 302)

    def test_no_role_denied(self):
        self.client.force_login(self.norole)
        self.assertEqual(self.client.get(self.url).status_code, 302)


class ScanPieceAccessTests(TestCase):
    def setUp(self):
        self.worker = _user('s-worker@test.test', role_code='worker')
        self.norole = _user('s-none@test.test', role_code=None, user_type='normal')
        self.url = reverse('tracking:scan', kwargs={'value': 'NOPE-0001'})

    def test_non_production_denied(self):
        self.client.force_login(self.norole)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_production_passes_role_gate(self):
        # Karigar clears the role gate; a garbage value then 404s (not 403).
        self.client.force_login(self.worker)
        self.assertEqual(self.client.get(self.url).status_code, 404)


class SidebarRuleUrlEnforcementTests(TestCase):
    """Removing a role from a menu item in the Access-Control panel
    (SidebarItemRule) must block its URL too, not just hide the sidebar link.
    SidebarAccessMiddleware enforces it; redirect (302) on deny, super_admin bypass."""

    def setUp(self):
        from inventory.models import Role, SidebarItemRule
        self.worker = _user('sr-worker@test.test', role_code='worker')
        self.manager = _user('sr-mgr@test.test', role_code='manager')
        self.admin = _user('sr-admin@test.test', role_code='super_admin', is_super=True)
        # Lock Adda Dashboard to manager only (remove worker) — mimics the panel.
        rule = SidebarItemRule.objects.get(url_name='production:dashboard')
        rule.allowed_roles.set(Role.objects.filter(code='manager'))
        rule.allowed_skills.clear()
        self.url = reverse('production:dashboard')

    def test_worker_blocked_at_url_after_rule_removed(self):
        self.client.force_login(self.worker)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 302)   # redirected away, not 200

    def test_manager_still_allowed(self):
        self.client.force_login(self.manager)
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_super_admin_bypasses_rule(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(self.url).status_code, 200)


class StageViewSkillGateTests(TestCase):
    """Stage workspace/panel VIEWS are skill-gated (not just their actions),
    mirroring AddaDetailView. Direct-URL into a stage you lack the skill for → 403.
    Management bypasses; the matching skill passes."""

    def setUp(self):
        self.admin = _user('sv-admin@test.test', role_code='super_admin', is_super=True)
        # A skilled user must exist before create_adda (service precondition);
        # this user also serves as the "allowed by skill" persona.
        self.skilled = _user('sv-skill@test.test', role_code='worker',
                             skills=['cutting_master_helper'])
        self.worker = _user('sv-noskill@test.test', role_code='worker')
        # Configure the layering Stage to require ONLY cutting_master_helper skill
        # (no role grant) so the gate is purely skill-driven for non-management.
        stage = Stage.objects.get(code='layering')
        stage.access_by_role.clear()
        stage.access_by_skill.set([Skill.objects.get(name='cutting_master_helper')])
        self.adda = create_adda(self.admin, product=Product.objects.get(code='NIKKAR'))
        self.url = reverse('production:layering-workspace', kwargs={'code': self.adda.code})

    def test_management_bypasses(self):
        self.client.force_login(self.admin)
        self.assertIn(self.client.get(self.url).status_code, (200, 302))

    def test_karigar_without_skill_denied(self):
        self.client.force_login(self.worker)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_karigar_with_skill_allowed(self):
        self.client.force_login(self.skilled)
        self.assertIn(self.client.get(self.url).status_code, (200, 302))
