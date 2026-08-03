"""Phase-6 M7 tests — Approve UI (summary BEFORE approve, §3g) +
Production Layout Summary (§3f)."""
import unittest

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounts.models import Role
from production.models import Product, ProductSize
from patterns_ai.models import (GeneratedMarkerCandidate,
                                MarkerGenerationRun, ProductionLayout)
from patterns_ai.services import compute_bridge
from patterns_ai.services import marker_generation_service as gen

User = get_user_model()
RUNTIME_OK = compute_bridge.runtime_available()

SQUARE = [[0.0, 0.0], [100.0, 0.0], [100.0, 100.0], [0.0, 100.0]]


class _M7Base(TestCase):
    @classmethod
    def setUpTestData(cls):
        mgr = Role.objects.get_or_create(code='manager', defaults={'name': 'M'})[0]
        wk = Role.objects.get_or_create(code='worker', defaults={'name': 'W'})[0]
        cls.mgr = User.objects.create_user('m7@test.local', password='x', role=mgr)
        cls.worker = User.objects.create_user('m7w@test.local', password='x', role=wk)
        cls.product = Product.objects.create(code='M7P', name='M7 Product')
        cls.size = ProductSize.objects.create(product=cls.product, code='m',
                                              label='M', display_order=1)
        cls.l1 = cls._layout(cls.product)
        cls.l2 = cls._layout(cls.product)
        cls.bad = cls._layout(cls.product, ok=False)

    @classmethod
    def _layout(cls, product, ok=True):
        run = MarkerGenerationRun.objects.create(   # test fixture only
            product=product, usable_width_mm=900,
            params={'schema_version': 1,
                    'ratio': {str(cls.size.pk): 2}},
            pipeline_version='t', created_by=cls.mgr)
        return GeneratedMarkerCandidate.objects.create(
            run=run, engine='manual',
            placements={'schema_version': 1, 'placements': [
                {'key': 'F·m', 'instance': 1, 'mirrored': False,
                 'rotation_deg': 0, 'polygon_mm': SQUARE}]},
            marker_length_mm=100,
            verification={'ok': ok, 'max_overlap_mm2': 0,
                          'within_width': ok, 'piece_count': 1})

    def _detail(self, layout):
        return self.client.get(reverse('patterns_ai:candidate-detail',
                                       args=[layout.pk])).content.decode()

    def _approve_url(self, layout):
        return reverse('patterns_ai:candidate-approve', args=[layout.pk])


class SummaryTests(_M7Base):
    def test_summary_matches_derivation(self):
        self.client.force_login(self.mgr)
        m = gen.derive_candidate_metrics(self.l1)
        html = self._detail(self.l1)
        self.assertIn('Production Layout Summary', html)
        self.assertIn('900 mm', html)                       # width fact
        self.assertIn(f'{m["length_mm"]} mm', html)          # length fact
        self.assertIn(f'{m["utilization_pct"]}% / {m["waste_pct"]}%', html)
        self.assertIn(f'{m["piece_count"]} pieces', html)
        self.assertIn('M×2', html)                           # ratio
        self.assertIn('Approve for production…', html)

    def test_unverified_layout_hides_approve(self):
        self.client.force_login(self.mgr)
        html = self._detail(self.bad)
        self.assertIn('Unverified layouts cannot be approved', html)
        self.assertNotIn('Approve for production…', html)

    def test_review_step_before_approve(self):
        # owner refinement 5: the summary is READ before the act
        self.client.force_login(self.mgr)
        html = self.client.get(self._approve_url(self.l1)).content.decode()
        self.assertIn('Production Layout Summary', html)
        self.assertIn('FIRST production', html)   # wraps across lines
        self.assertIn('★ Approve for production', html)
        # the act itself is a POST — the GET wrote nothing
        self.assertEqual(ProductionLayout.objects.count(), 0)


class ApproveFlowTests(_M7Base):
    def test_approve_moves_pointer_audited(self):
        self.client.force_login(self.mgr)
        r = self.client.post(self._approve_url(self.l1))
        self.assertRedirects(r, reverse('patterns_ai:candidate-detail',
                                        args=[self.l1.pk]))
        d = ProductionLayout.objects.get(product=self.product)
        self.assertEqual(d.approved_layout_id, self.l1.pk)
        self.assertEqual(d.approved_by_id, self.mgr.pk)
        # the page now carries the ★ banner + audit line
        html = self._detail(self.l1)
        self.assertIn('THE production layout', html)
        self.assertIn('Approved by', html)

    def test_replace_shows_old_pointer_and_moves(self):
        self.client.force_login(self.mgr)
        self.client.post(self._approve_url(self.l1))
        confirm = self.client.get(self._approve_url(self.l2)).content.decode()
        self.assertIn(f'#{self.l1.pk}', confirm)             # names the old
        self.assertIn('stays in the Layout switcher history', confirm)
        self.client.post(self._approve_url(self.l2))
        d = ProductionLayout.objects.get(product=self.product)
        self.assertEqual(d.approved_layout_id, self.l2.pk)
        # old layout page: no ★, offers approve again
        html = self._detail(self.l1)
        self.assertNotIn('THE production layout', html)
        self.assertIn('Approve for production…', html)

    def test_reapprove_is_noop_with_honest_message(self):
        self.client.force_login(self.mgr)
        self.client.post(self._approve_url(self.l1))
        first_at = ProductionLayout.objects.get(
            product=self.product).approved_at
        r = self.client.post(self._approve_url(self.l1), follow=True)
        self.assertContains(r, 'already the production layout')
        self.assertEqual(ProductionLayout.objects.get(
            product=self.product).approved_at, first_at)

    def test_unverified_post_refused(self):
        self.client.force_login(self.mgr)
        r = self.client.post(self._approve_url(self.bad), follow=True)
        self.assertContains(r, 'not verified')
        self.assertEqual(ProductionLayout.objects.count(), 0)

    def test_worker_403(self):
        self.client.force_login(self.worker)
        self.assertEqual(self.client.get(
            self._approve_url(self.l1)).status_code, 403)
        self.assertEqual(self.client.post(
            self._approve_url(self.l1)).status_code, 403)
        self.assertEqual(ProductionLayout.objects.count(), 0)

    def test_star_flips_in_workspace_and_switcher(self):
        self.client.force_login(self.mgr)
        self.client.post(self._approve_url(self.l1))
        ws = self.client.get(reverse('patterns_ai:workspace',
                                     args=[self.l1.pk])).content.decode()
        self.assertIn('★ Production', ws)
        self.assertIn(f'★ Production · #{self.l1.pk}', ws)   # switcher head
        ws2 = self.client.get(reverse('patterns_ai:workspace',
                                      args=[self.l2.pk])).content.decode()
        self.assertNotIn('Layout #%d · ★ Production' % self.l2.pk, ws2)


@unittest.skipUnless(RUNTIME_OK, 'compute runtime required (ADR-F)')
class SaveNeverMovesDesignationTests(_M7Base):
    """§3g law — Save creates a DRAFT; the designation is untouched."""

    def test_save_manual_layout_leaves_designation(self):
        self.client.force_login(self.mgr)
        self.client.post(self._approve_url(self.l1))
        before = ProductionLayout.objects.get(product=self.product)
        _run, saved = gen.save_manual_layout(
            user=self.mgr, source_candidate=self.l1, width_mm=900,
            height_mm=500,
            placements=[{'key': 'F·m', 'instance': 1,
                         'polygon_mm': SQUARE, 'rotation_deg': 0,
                         'mirrored': False, 'locked': False}])
        after = ProductionLayout.objects.get(product=self.product)
        self.assertEqual(after.approved_layout_id, before.approved_layout_id)
        self.assertEqual(after.approved_at, before.approved_at)
        self.assertNotEqual(saved.pk, self.l1.pk)   # a NEW draft exists