"""Block-3D tests — usage + outcome recording workflows (immutable facts)."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounts.models import Role
from production.models import Adda, Product, Stage, WorkflowStage
from patterns_ai.models import Marker, MarkerOutcome, MarkerUsage
from patterns_ai.services import marker_service as ms
from patterns_ai.services import marker_feedback_service as fb
from patterns_ai.services.units import m_to_mm

User = get_user_model()


class _Base(TestCase):
    @classmethod
    def setUpTestData(cls):
        mgr = Role.objects.get_or_create(code='manager', defaults={'name': 'M'})[0]
        wk = Role.objects.get_or_create(code='worker', defaults={'name': 'W'})[0]
        cls.mgr = User.objects.create_user('pai3d@test.local', password='x', role=mgr)
        cls.worker = User.objects.create_user('pai3d-w@test.local', password='x', role=wk)
        cls.product = Product.objects.create(code='PAI3D', name='PAI 3D')
        st, _ = Stage.objects.get_or_create(code='pai3d_s', defaults={'name': 'S'})
        ws = WorkflowStage.objects.create(product=cls.product, stage=st, order=1)
        cls.adda = Adda.objects.create(code='PAI3D-001', product=cls.product,
                                       current_stage=ws)

    def marker(self, **kw):
        d = dict(user=self.mgr, product=self.product,
                 origin=Marker.Origin.IMPORTED, usable_width_mm=940)
        d.update(kw)
        return ms.create_marker(**d)


class UnitsEdgeTests(TestCase):
    def test_m_to_mm(self):
        self.assertEqual(m_to_mm('45.00'), 45000)
        self.assertEqual(m_to_mm('45.0005'), 45001)     # HALF_UP at mm


class UsageWorkflowTests(_Base):
    def test_record_usage_via_ui_and_biography_updates(self):
        m = self.marker()
        self.client.force_login(self.mgr)
        url = reverse('patterns_ai:usage-new', kwargs={'reference': m.reference})
        self.assertEqual(self.client.get(url).status_code, 200)
        resp = self.client.post(url, {'adda': self.adda.pk, 'plies': 30,
                                      'repeats': 3, 'notes': 'first lay'})
        self.assertEqual(resp.status_code, 302)
        u = MarkerUsage.objects.get(marker=m)
        self.assertEqual((u.plies, u.repeats), (30, 3))
        detail = self.client.get(resp.url)
        self.assertContains(detail, 'PAI3D-001')            # usage row
        self.assertContains(detail, 'record outcome')       # CTA when no outcome
        self.assertContains(detail, 'used on')              # biography updated

    def test_unusable_marker_error_surfaced_in_form(self):
        m = self.marker()
        ms.transition_marker(user=self.mgr, marker=m, to_status='retired',
                             reason='old mat')
        self.client.force_login(self.mgr)
        resp = self.client.post(
            reverse('patterns_ai:usage-new', kwargs={'reference': m.reference}),
            {'adda': self.adda.pk, 'plies': 10, 'repeats': 1})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'old mat')                # service reason shown
        self.assertEqual(MarkerUsage.objects.count(), 0)

    def test_void_via_ui_requires_reason_and_keeps_history(self):
        m = self.marker()
        u = fb.record_usage(user=self.mgr, marker=m, adda=self.adda, plies=5)
        self.client.force_login(self.mgr)
        void_url = reverse('patterns_ai:usage-void', kwargs={'pk': u.pk})
        self.client.post(void_url, {'reason': ''})          # refused by service
        u.refresh_from_db(); self.assertIsNone(u.voided_at)
        self.client.post(void_url, {'reason': 'wrong adda'})
        u.refresh_from_db(); self.assertIsNotNone(u.voided_at)
        detail = self.client.get(reverse('patterns_ai:marker-detail',
                                         kwargs={'reference': m.reference}))
        self.assertContains(detail, 'voided')
        self.assertContains(detail, 'wrong adda')


class OutcomeWorkflowTests(_Base):
    def _usage(self, m=None):
        m = m or self.marker()
        return fb.record_usage(user=self.mgr, marker=m, adda=self.adda,
                               plies=30, repeats=3)

    def test_record_outcome_via_ui_meters_converted_metrics_flashed(self):
        u = self._usage()
        self.client.force_login(self.mgr)
        url = reverse('patterns_ai:outcome-new', kwargs={'pk': u.pk})
        self.assertEqual(self.client.get(url).status_code, 200)
        resp = self.client.post(url, {'fabric_in_m': '45.00',
                                      'garments_cut': 60,
                                      'garments_packed': 54,
                                      'leftover_m': '1.20'}, follow=True)
        o = MarkerOutcome.objects.get(usage=u)
        self.assertEqual(o.fabric_in_mm, 45000)             # meters→mm edge
        self.assertEqual(o.leftover_mm, 1200)
        self.assertContains(resp, '75.00 m per 100')        # flashed derived metric
        self.assertContains(resp, '75.00 m/100')            # detail row metric

    def test_honest_null_outcome_renders_pending(self):
        u = self._usage()
        self.client.force_login(self.mgr)
        resp = self.client.post(
            reverse('patterns_ai:outcome-new', kwargs={'pk': u.pk}),
            {}, follow=True)
        self.assertContains(resp, 'honest-NULL')            # flash
        self.assertContains(resp, 'metrics pending')        # detail row
        o = MarkerOutcome.objects.get(usage=u)
        self.assertIsNone(o.fabric_in_mm)

    def test_double_outcome_surfaced_as_form_error(self):
        u = self._usage()
        fb.record_outcome(user=self.mgr, usage=u, fabric_in_mm=1000)
        self.client.force_login(self.mgr)
        resp = self.client.post(
            reverse('patterns_ai:outcome-new', kwargs={'pk': u.pk}),
            {'garments_cut': 5})
        self.assertEqual(resp.status_code, 200)             # re-rendered w/ error
        self.assertEqual(MarkerOutcome.objects.filter(usage=u).count(), 1)

    def test_update_outcome_facts_null_fill_still_service_only(self):
        u = self._usage()
        o = fb.record_outcome(user=self.mgr, usage=u, fabric_in_mm=45000)
        fb.update_outcome_facts(user=self.mgr, outcome=o, garments_cut=60)
        o.refresh_from_db()
        self.assertEqual(o.garments_cut, 60)


class PermissionTests(_Base):
    def test_worker_forbidden_everywhere(self):
        m = self.marker()
        u = fb.record_usage(user=self.mgr, marker=m, adda=self.adda, plies=5)
        self.client.force_login(self.worker)
        urls = [
            reverse('patterns_ai:usage-new', kwargs={'reference': m.reference}),
            reverse('patterns_ai:outcome-new', kwargs={'pk': u.pk}),
        ]
        for url in urls:
            self.assertEqual(self.client.get(url).status_code, 403)
            self.assertEqual(self.client.post(url, {}).status_code, 403)
        self.assertEqual(self.client.post(
            reverse('patterns_ai:usage-void', kwargs={'pk': u.pk}),
            {'reason': 'x'}).status_code, 403)
        u.refresh_from_db(); self.assertIsNone(u.voided_at)
