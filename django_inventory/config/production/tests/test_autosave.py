"""PR-6 auto-save: draft endpoints return 204 on AJAX + persist (no advance)."""
from django.test import TestCase
from django.urls import reverse

from accounts.models import Skill, User
from inventory.models import Role
from production.models import AddaStageRecord, Product
from production.services import create_adda


def _manager():
    role = Role.objects.get(code='super_admin')
    u = User.objects.create_user(email='mgr@auto.test', password='x', is_superuser=True, is_staff=True)
    u.role = role
    u.save()
    u.skills.add(Skill.objects.get(name='cutting_master'))
    return u


class AutoSaveDraftTests(TestCase):
    def setUp(self):
        self.mgr = _manager()
        self.adda = create_adda(self.mgr, product=Product.objects.get(code='NIKKAR'))
        self.client.force_login(self.mgr)

    def test_layering_draft_ajax_returns_204_and_persists(self):
        url = reverse('production:layering-complete', args=[self.adda.code])
        resp = self.client.post(
            url, {'notes': 'auto draft note', 'duration_minutes': '', 'layer_length_meters': ''},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(resp.status_code, 204)        # no redirect on auto-save
        sr = AddaStageRecord.objects.get(adda=self.adda, workflow_stage=self.adda.current_stage)
        self.assertEqual(sr.draft_notes, 'auto draft note')

    def test_layering_draft_full_page_redirects(self):
        url = reverse('production:layering-complete', args=[self.adda.code])
        resp = self.client.post(url, {'action': 'draft', 'notes': 'manual'})
        self.assertEqual(resp.status_code, 302)        # manual button still redirects
