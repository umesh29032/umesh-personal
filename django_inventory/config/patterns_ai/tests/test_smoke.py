"""Block-1 smoke: URL wired, RBAC gated, template renders."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounts.models import Role


class SmokeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        sa = Role.objects.get_or_create(code='super_admin', defaults={'name': 'Super Admin'})[0]
        wk = Role.objects.get_or_create(code='worker', defaults={'name': 'Worker'})[0]
        cls.admin = User.objects.create_user('pai_admin@test.local', password='x', role=sa)
        cls.worker = User.objects.create_user('pai_worker@test.local', password='x', role=wk)

    def test_home_renders_for_management(self):
        self.client.force_login(self.admin)
        r = self.client.get(reverse('patterns_ai:home'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Pattern Intelligence')

    def test_home_forbidden_for_worker(self):
        self.client.force_login(self.worker)
        r = self.client.get(reverse('patterns_ai:home'))
        self.assertEqual(r.status_code, 403)
