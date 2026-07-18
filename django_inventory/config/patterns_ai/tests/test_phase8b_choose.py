"""Phase 8B — the Adda chooses (choose page + LAYOUT_PROVIDER inversion
+ the pattern-stage Manufacturing Layout panel). Rule 9 lived: the page
offers ONLY the library; production renders plain dicts."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounts.models import Role
from production.models import (Adda, Product, ProductPattern,
                               ProductPatternAssignment, ProductSize,
                               Stage, WorkflowStage)
from production.stages.cutting_pattern import handler as cp_handler
from patterns_ai.models import ApprovedLayoutUsage, PieceSizeGeometry
from patterns_ai.services import layout_library_service as lib
from patterns_ai.services import layout_usage_service as usage_svc
from patterns_ai.services import marker_generation_service as gen
from patterns_ai.services import pattern_geometry_service as geo
from patterns_ai.tests.test_p3_generation import rect_um

User = get_user_model()


def _ring(x, y, w, h):
    return [[x, y], [x + w, y], [x + w, y + h], [x, y + h]]


class _P8BBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        mgr = Role.objects.get_or_create(code='manager',
                                         defaults={'name': 'M'})[0]
        wk = Role.objects.get_or_create(code='worker',
                                        defaults={'name': 'W'})[0]
        cls.mgr = User.objects.create_user('p8b@test.local', password='x',
                                           role=mgr)
        cls.worker = User.objects.create_user('p8bw@test.local',
                                              password='x', role=wk)
        cls.product = Product.objects.create(code='P8B', name='P8B Choose')
        cls.size = ProductSize.objects.create(product=cls.product, code='s',
                                              label='S', display_order=1)
        pattern = ProductPattern.objects.create(code='p8b-f', name='Front')
        ProductPatternAssignment.objects.create(product=cls.product,
                                                pattern=pattern,
                                                pieces_count=1)
        cls.piece = geo.create_piece(user=cls.mgr, product=cls.product,
                                     pattern=pattern, fabric_group='body')
        d = geo.get_or_create_draft(user=cls.mgr, piece=cls.piece)
        PieceSizeGeometry.objects.create(       # fixture only
            version=d, size=cls.size, geometry=rect_um(300, 200),
            trust_grade='photo_calibrated', created_by=cls.mgr)
        geo.confirm_version(user=cls.mgr, version=d)
        # a real pattern stage on the Adda's workflow (panel integration)
        st, _ = Stage.objects.get_or_create(
            code='cutting_pattern', defaults={'name': 'Pattern Design'})
        cls.ws = WorkflowStage.objects.create(product=cls.product,
                                              stage=st, order=1)
        cls.adda = Adda.objects.create(code='P8B-001',
                                       product=cls.product,
                                       current_stage=cls.ws,
                                       created_by=cls.mgr)

    def _layout(self):
        _, cand = gen.save_table_layout(
            user=self.mgr, product=self.product, width_mm=900,
            height_mm=2000, spacing_mm=2.0, fabric_group='body',
            placements=[{'key': f'{self.piece.pk}:{self.size.pk}',
                         'instance': 1,
                         'polygon_mm': _ring(10, 10, 200, 300)}])
        return lib.approve_table_layout(user=self.mgr,
                                        product=self.product,
                                        candidate=cand)

    def _url(self):
        return reverse('patterns_ai:choose-layout', args=[self.adda.pk])


class ChoosePageTests(_P8BBase):
    def test_lists_active_only_and_records(self):
        lay = self._layout()
        self.client.force_login(self.mgr)
        html = self.client.get(self._url()).content.decode()
        self.assertIn(lay.layout_uid, html)
        self.assertIn('Use for BODY', html)
        r = self.client.post(self._url(), {'action': 'record',
                                           'layout': lay.pk})
        self.assertEqual(r.status_code, 302)
        u = ApprovedLayoutUsage.objects.get(adda=self.adda)
        self.assertEqual(u.layout_id, lay.pk)
        # group taken → the option greys, the contract shows
        html = self.client.get(self._url()).content.decode()
        self.assertIn('group has a contract', html)
        self.assertIn('void reason (required)', html)

    def test_stale_disabled_and_archived_hidden(self):
        lay = self._layout()
        # a newer confirmed version → STALE
        d2 = geo.start_next_version(user=self.mgr, piece=self.piece)
        geo.confirm_version(user=self.mgr, version=d2)
        self.client.force_login(self.mgr)
        html = self.client.get(self._url()).content.decode()
        self.assertIn('STALE — cannot manufacture', html)
        self.assertNotIn('Use for BODY', html)   # no record button
        lib.archive_layout(user=self.mgr, layout=lay)
        html = self.client.get(self._url()).content.decode()
        self.assertNotIn(lay.layout_uid, html)   # archived = not offered

    def test_void_flow_and_worker_403(self):
        lay = self._layout()
        u = usage_svc.record_usage(user=self.mgr, adda=self.adda,
                                   layout=lay)
        self.client.force_login(self.mgr)
        self.client.post(self._url(), {'action': 'void', 'usage': u.pk,
                                       'reason': 'wrong pick'})
        u.refresh_from_db()
        self.assertIsNotNone(u.voided_at)
        self.client.force_login(self.worker)
        self.assertEqual(self.client.get(self._url()).status_code, 403)


class ProviderPanelTests(_P8BBase):
    def test_provider_registered_and_returns_contract(self):
        self.assertIsNotNone(cp_handler.LAYOUT_PROVIDER)   # apps.ready()
        lay = self._layout()
        usage_svc.record_usage(user=self.mgr, adda=self.adda, layout=lay)
        panel = cp_handler.LAYOUT_PROVIDER(self.adda)
        self.assertTrue(panel['has_usage'])
        self.assertEqual(panel['groups'][0]['uid'], lay.layout_uid)
        self.assertFalse(panel['groups'][0]['stale'])
        self.assertIn(str(self.adda.pk), panel['choose_url'])

    def test_stage_workspace_renders_the_contract(self):
        lay = self._layout()
        usage_svc.record_usage(user=self.mgr, adda=self.adda, layout=lay)
        self.client.force_login(self.mgr)
        html = self.client.get(
            reverse('production:pattern-workspace',
                    args=[self.adda.code])).content.decode()
        self.assertIn('Manufacturing Layout', html)
        self.assertIn(lay.layout_uid, html)
        self.assertIn('Manage layouts', html)

    def test_provider_failure_never_breaks_the_page(self):
        original = cp_handler.LAYOUT_PROVIDER

        def boom(adda):
            raise RuntimeError('provider exploded')
        cp_handler.LAYOUT_PROVIDER = boom
        try:
            self.client.force_login(self.mgr)
            r = self.client.get(reverse('production:pattern-workspace',
                                        args=[self.adda.code]))
            self.assertEqual(r.status_code, 200)   # section absent, page OK
            self.assertNotIn('Manufacturing Layout',
                             r.content.decode())
        finally:
            cp_handler.LAYOUT_PROVIDER = original
