"""Block-3E tests — the Yield Board (pure read model over facts)."""
from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from accounts.models import Role
from production.models import Adda, Product, Stage, WorkflowStage
from patterns_ai.models import Marker
from patterns_ai.services import marker_service as ms
from patterns_ai.services import marker_feedback_service as fb
from patterns_ai.services import marker_query_service as q

User = get_user_model()


class _Base(TestCase):
    @classmethod
    def setUpTestData(cls):
        mgr = Role.objects.get_or_create(code='manager', defaults={'name': 'M'})[0]
        wk = Role.objects.get_or_create(code='worker', defaults={'name': 'W'})[0]
        cls.mgr = User.objects.create_user('pai3e@test.local', password='x', role=mgr)
        cls.worker = User.objects.create_user('pai3e-w@test.local', password='x', role=wk)
        cls.product = Product.objects.create(code='PAI3E', name='PAI 3E')
        st, _ = Stage.objects.get_or_create(code='pai3e_s', defaults={'name': 'S'})
        ws = WorkflowStage.objects.create(product=cls.product, stage=st, order=1)
        cls.adda = Adda.objects.create(code='PAI3E-001', product=cls.product,
                                       current_stage=ws)

    def marker(self, **kw):
        d = dict(user=self.mgr, product=self.product,
                 origin=Marker.Origin.IMPORTED, usable_width_mm=940)
        d.update(kw)
        return ms.create_marker(**d)

    def with_outcome(self, marker, fabric_mm, cut, n=1):
        for _ in range(n):
            u = fb.record_usage(user=self.mgr, marker=marker, adda=self.adda,
                                plies=10)
            fb.record_outcome(user=self.mgr, usage=u, fabric_in_mm=fabric_mm,
                              garments_cut=cut)


class AggregationTests(_Base):
    def test_board_math_and_default_best_first(self):
        good = self.marker(label='good')
        bad = self.marker(label='bad')
        empty = self.marker(label='no facts')
        self.with_outcome(good, 30000, 50)        # 60.00 m/100
        self.with_outcome(bad, 45000, 50)         # 90.00 m/100
        rows = q.get_product_yield_board(self.product)      # sort=avg
        refs = [r['reference'] for r in rows]
        self.assertEqual(refs[0], good.reference)           # best first
        self.assertEqual(refs[1], bad.reference)
        self.assertEqual(refs[2], empty.reference)          # NULLs last
        self.assertEqual(str(rows[0]['avg_meters_per_100']), '60.00')
        self.assertEqual(str(rows[0]['avg_meters_per_garment']), '0.60')
        self.assertIsNone(rows[2]['avg_meters_per_100'])    # honest NULL
        self.assertEqual(rows[2]['n_for_average'], 0)

    def test_multi_outcome_average_and_n(self):
        m = self.marker()
        self.with_outcome(m, 30000, 50)                     # 60
        self.with_outcome(m, 45000, 50)                     # 90
        row = q.get_product_yield_board(self.product)[0]
        self.assertEqual(str(row['avg_meters_per_100']), '75.00')
        self.assertEqual(row['n_for_average'], 2)
        self.assertEqual(row['usage_count'], 2)

    def test_orderings(self):
        a = self.marker(); b = self.marker()
        self.with_outcome(a, 30000, 50)
        self.with_outcome(b, 45000, 50, n=2)
        by_usage = q.get_product_yield_board(self.product, sort='usage')
        self.assertEqual(by_usage[0]['reference'], b.reference)
        by_recent = q.get_product_yield_board(self.product, sort='recent')
        self.assertEqual(by_recent[0]['reference'], b.reference)
        by_ref = q.get_product_yield_board(self.product, sort='reference')
        self.assertEqual([r['reference'] for r in by_ref],
                         sorted(r['reference'] for r in by_ref))

    def test_zero_persistence(self):
        m = self.marker()
        self.with_outcome(m, 30000, 50)
        with CaptureQueriesContext(connection) as ctx:
            q.get_product_yield_board(self.product)
        writes = [x['sql'] for x in ctx.captured_queries
                  if x['sql'].split()[0].upper() not in
                  ('SELECT', 'SAVEPOINT', 'RELEASE')]
        self.assertEqual(writes, [])

    def test_performance_sanity_linear_queries(self):
        for i in range(8):
            self.with_outcome(self.marker(), 30000 + i * 1000, 50)
        with CaptureQueriesContext(connection) as ctx:
            q.get_product_yield_board(self.product)
        # O(markers) by design (no optimization ordered): sanity ceiling only.
        self.assertLessEqual(len(ctx.captured_queries), 4 + 8 * 4)


class ViewTests(_Base):
    def test_board_renders_columns_and_honest_language(self):
        good = self.marker(label='good')
        self.with_outcome(good, 30000, 50)
        self.marker(label='empty')
        self.client.force_login(self.mgr)
        resp = self.client.get(reverse('patterns_ai:yield-board'))
        self.assertContains(resp, good.reference)
        self.assertContains(resp, '60.00')                  # avg m/100
        self.assertContains(resp, '0.60')                   # avg m/garment
        self.assertContains(resp, 'n=1')
        self.assertContains(resp, 'n=0')
        self.assertContains(resp, '— (no facts yet)')       # honest NULL
        self.assertContains(resp, 'derived at read')

    def test_product_switch_and_sort_params(self):
        p2 = Product.objects.create(code='PAI3E-B', name='B')
        m2 = ms.create_marker(user=self.mgr, product=p2,
                              origin=Marker.Origin.IMPORTED,
                              usable_width_mm=900)
        m1 = self.marker()
        self.client.force_login(self.mgr)
        resp = self.client.get(reverse('patterns_ai:yield-board'),
                               {'product': p2.pk, 'sort': 'usage'})
        self.assertContains(resp, m2.reference)
        # rows are scoped to the selected product (dropdown may name others)
        self.assertNotContains(resp, m1.reference)
        bad_sort = self.client.get(reverse('patterns_ai:yield-board'),
                                   {'product': p2.pk, 'sort': 'evil'})
        self.assertEqual(bad_sort.status_code, 200)         # falls back to avg

    def test_empty_state_no_products(self):
        self.client.force_login(self.mgr)
        resp = self.client.get(reverse('patterns_ai:yield-board'))
        self.assertContains(resp, 'No markers recorded yet')

    def test_permissions(self):
        url = reverse('patterns_ai:yield-board')
        self.client.force_login(self.worker)
        self.assertEqual(self.client.get(url).status_code, 403)
        self.client.logout()
        self.assertEqual(self.client.get(url).status_code, 302)
