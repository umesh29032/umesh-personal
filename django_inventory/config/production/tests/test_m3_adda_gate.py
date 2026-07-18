"""Production campaign module 3 (2026-07-11): Adda CREATION is a
management act. The old ProductionRoleMixin let any worker open and
POST the create form (create_adda has no role gate — the view is the
wall). Found live in browser during campaign verification."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounts.models import Role, Skill
from production.models import Adda, Product

User = get_user_model()


class AddaCreateGateTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        mgr = Role.objects.get_or_create(code='manager',
                                         defaults={'name': 'M'})[0]
        wk = Role.objects.get_or_create(code='worker',
                                        defaults={'name': 'W'})[0]
        cls.mgr = User.objects.create_user('m3m@test.local', password='x',
                                           role=mgr)
        # Spec-D6: create_adda needs a skilled cutting pool to exist
        cls.mgr.skills.add(Skill.objects.get(name='cutting_master'))
        cls.worker = User.objects.create_user('m3w@test.local', password='x',
                                              role=wk)
        cls.product = Product.objects.get(code='T-SHIRT')   # seeded flow

    def test_worker_cannot_reach_or_post_create(self):
        self.client.force_login(self.worker)
        url = reverse('production:adda-create')
        self.assertEqual(self.client.get(url).status_code, 403)
        resp = self.client.post(url, {'product': self.product.pk})
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(Adda.objects.filter(product=self.product).count(),
                         0)                      # nothing created

    def test_manager_still_creates(self):
        self.client.force_login(self.mgr)
        resp = self.client.post(reverse('production:adda-create'),
                                {'product': self.product.pk})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Adda.objects.filter(product=self.product).count(),
                         1)
