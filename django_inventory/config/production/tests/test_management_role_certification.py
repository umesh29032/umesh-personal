"""Management Role Certification — MGT-B pins (Production 2/2, 2026-07-12).

Pins the bug found + fixed during the management-role audit:

  MGT-B-1 adda_views.py caught `except (ValidationError, PermissionDenied)`
          in AddaAddLaneView / AddaCancelLaneView but never imported
          PermissionDenied — so EVERY service refusal on the two lane
          management surfaces crashed 500 via NameError instead of the
          designed error flash (UI-reachable: submitting the add-lane form
          without a reason). Fix = import PermissionDenied in adda_views.

Certification report: docs/MANAGEMENT_ROLE_CERTIFICATION.md (MGT-B).
"""
from django.test import TestCase

from accounts.models import Role, User
from production.models import Adda, CuttingStream, Product


def _user(email, *, role_code):
    u = User.objects.create_user(email=email, password='x')
    u.role = Role.objects.get(code=role_code)
    u.save()
    return u


class LaneViewsServiceRefusalTests(TestCase):
    """MGT-B-1: lane service refusals must flash + redirect, never 500."""

    @classmethod
    def setUpTestData(cls):
        cls.mgr = _user('mcert-m1@test', role_code='manager')
        cls.worker = _user('mcert-w1@test', role_code='worker')
        product = Product.objects.create(code='MCERT1', name='MCert1')
        cls.adda = Adda.objects.create(code='MCERT1-001', product=product)

    def test_manager_add_lane_refusal_flashes_not_500(self):
        # Empty POST → adda_service.add_stream raises the mandatory-reason
        # ValidationError; the view's except-clause must catch it (the bug
        # was a NameError on the uninported PermissionDenied in that clause).
        self.client.force_login(self.mgr)
        resp = self.client.post(
            f'/production/addas/{self.adda.code}/lanes/add/', {}, follow=True)
        self.assertEqual(resp.status_code, 200)          # rendered, not 500
        self.assertContains(resp, 'reason is required')  # flashed refusal
        self.assertEqual(
            CuttingStream.objects.filter(adda=self.adda).count(), 0)

    def test_manager_cancel_lane_refusal_flashes_not_500(self):
        self.client.force_login(self.mgr)
        resp = self.client.post(
            f'/production/addas/{self.adda.code}/lanes/cancel/', {}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'reason is required')

    def test_worker_blocked_at_dispatch_on_both_lane_views(self):
        # Regression guard: ManagementRoleMixin fires before any service code.
        self.client.force_login(self.worker)
        for url in (f'/production/addas/{self.adda.code}/lanes/add/',
                    f'/production/addas/{self.adda.code}/lanes/cancel/'):
            resp = self.client.post(url, {})
            self.assertEqual(resp.status_code, 403, url)
