"""R1.3 (PDD §27-D6): "new Adda started" dashboard broadcast tests.

Every worker sees that production started (read-only, no financials, no link);
only assigned workers get the actionable Active-Addas entry. Management
dashboards are unchanged (they already list all Addas).
"""
from django.test import TestCase

from accounts.models import Skill, User
from inventory.models import Role
from production.models import Product
from production.services import create_adda
from production.services import worker_task_service as wts


def _user(email, role_code, *, skill='cutting_master', superuser=False):
    u = User.objects.create_user(email=email, password='x',
                                 is_superuser=superuser, is_staff=superuser)
    u.role = Role.objects.get(code=role_code)
    u.save()
    u.skills.add(Skill.objects.get(name=skill))
    return u


class BroadcastRowTests(TestCase):
    def setUp(self):
        self.admin = _user('admin@r1b.test', 'super_admin', superuser=True)
        self.assigned = _user('assigned@r1b.test', 'worker')
        self.other = _user('other@r1b.test', 'worker')
        self.adda = create_adda(self.admin, product=Product.objects.get(code='T-SHIRT'))
        wts.set_stage_workers(self.adda.stage_records.first(), [self.assigned.pk])
        self.url = '/inventory/my-dashboard/'

    def test_unassigned_worker_sees_broadcast_without_link(self):
        self.client.force_login(self.other)
        resp = self.client.get(self.url)
        self.assertContains(resp, 'New Addas Started')
        self.assertContains(resp, self.adda.code)
        # Read-only: the broadcast section carries NO link into the Adda.
        html = resp.content.decode()
        section = html[html.index('New Addas Started'):html.index('Active Addas') if 'Active Addas' in html else len(html)]
        self.assertNotIn('href="/production/addas/', section)

    def test_assigned_worker_gets_actionable_list_not_duplicate_broadcast(self):
        self.client.force_login(self.assigned)
        resp = self.client.get(self.url)
        # Assigned → the Adda lives in Active Addas (actionable), NOT broadcast.
        self.assertContains(resp, 'Active Addas')
        self.assertNotContains(resp, 'New Addas Started')

    def test_management_dashboard_has_no_broadcast_section(self):
        self.client.force_login(self.admin)
        resp = self.client.get(self.url)
        self.assertNotContains(resp, 'New Addas Started')  # mgmt sees all anyway
