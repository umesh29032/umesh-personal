"""P1-2 (C-2): sidebar information-architecture order.

build_menu_for renders sections in SIDEBAR tuple order, so these assert the
NEW order — Production directly below Main, Raw Materials production-adjacent,
Storefront below them — for super_admin / manager / worker. Pure ordering:
no permission, URL, or visibility assertions here beyond what each role sees.
"""
from django.test import TestCase

from accounts.models import User
from accounts.services.permission_service import build_menu_for
from inventory.models import Role


def _user(email, role_code, *, is_super=False):
    u = User.objects.create_user(email=email, password='x', is_superuser=is_super)
    u.role = Role.objects.get(code=role_code)
    u.save()
    return u


def _labels(user):
    return [s['label'] for s in build_menu_for(user)]


class SidebarOrderTests(TestCase):
    def _assert_core_order(self, labels):
        """Invariants that must hold for every role (over whatever it can see)."""
        self.assertEqual(labels[0], 'Main', f'Main must be first: {labels}')
        if 'Production' in labels:
            # Production is the FIRST operational section (directly below Main).
            self.assertEqual(labels[1], 'Production', f'Production must follow Main: {labels}')
        if 'Production' in labels and 'Raw Materials' in labels:
            self.assertLess(labels.index('Production'), labels.index('Raw Materials'), labels)
        if 'Production' in labels and 'Storefront' in labels:
            self.assertLess(labels.index('Production'), labels.index('Storefront'), labels)
        if 'Raw Materials' in labels and 'Storefront' in labels:
            self.assertLess(labels.index('Raw Materials'), labels.index('Storefront'), labels)

    def test_super_admin_full_order(self):
        labels = _labels(_user('so-sa@test', 'super_admin', is_super=True))
        self._assert_core_order(labels)
        # super_admin sees all → assert the exact target subsequence.
        idx = {l: i for i, l in enumerate(labels)}
        for earlier, later in (('Main', 'Production'), ('Production', 'Raw Materials'),
                               ('Raw Materials', 'Storefront')):
            self.assertIn(earlier, idx); self.assertIn(later, idx)
            self.assertLess(idx[earlier], idx[later], labels)

    def test_manager_order(self):
        labels = _labels(_user('so-mgr@test', 'manager'))
        self.assertIn('Production', labels)
        self.assertIn('Raw Materials', labels)
        self._assert_core_order(labels)

    def test_worker_order(self):
        # H-3 lockdown (owner 2026-07-06): a worker's sidebar is ONLY their own
        # world — Main (My Dashboard / My Earnings). No Production / Raw
        # Materials / Tracking sections.
        labels = _labels(_user('so-w@test', 'worker'))
        self.assertEqual(labels, ['Main'])
        self._assert_core_order(labels)
