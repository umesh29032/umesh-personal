"""P5 tests — insights layer (SELECT-only, composed from existing derive
paths), health command, workflow-integration links, hardening fixes."""
import io
import tempfile

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import connection
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from accounts.models import Role
from production.models import (Adda, Product, Stage,
                               WorkflowStage)
from patterns_ai.models import Marker
from patterns_ai.services import advisor_service as adv
from patterns_ai.services import intelligence_service as intel
from patterns_ai.services import marker_feedback_service as fb
from patterns_ai.services import marker_service as ms
from patterns_ai.services import suggestion_service as sug

User = get_user_model()
MEDIA = tempfile.mkdtemp(prefix='pai-p5-media-')


@override_settings(MEDIA_ROOT=MEDIA)
class _Base(TestCase):
    @classmethod
    def setUpTestData(cls):
        mgr = Role.objects.get_or_create(code='manager', defaults={'name': 'M'})[0]
        wk = Role.objects.get_or_create(code='worker', defaults={'name': 'W'})[0]
        cls.mgr = User.objects.create_user('p5@test.local', password='x', role=mgr)
        cls.worker = User.objects.create_user('p5w@test.local', password='x', role=wk)
        cls.product = Product.objects.create(code='P5PROD', name='P5 Product')
        st, _ = Stage.objects.get_or_create(code='p5_s', defaults={'name': 'S'})
        cls.ws = WorkflowStage.objects.create(product=cls.product, stage=st,
                                              order=1)
        cls.adda = Adda.objects.create(code='P5-ADDA', product=cls.product,
                                       current_stage=cls.ws)

    def marker_with_reality(self, m_per_100, uses=1, label='m', width=900):
        marker = ms.create_marker(user=self.mgr, product=self.product,
                                  origin=Marker.Origin.IMPORTED,
                                  usable_width_mm=width, label=label)
        for _ in range(uses):
            usage = fb.record_usage(user=self.mgr, marker=marker,
                                    adda=self.adda, plies=10, repeats=1)
            fb.record_outcome(user=self.mgr, usage=usage,
                              fabric_in_mm=int(m_per_100 * 100),
                              garments_cut=10)
        return marker


class InsightsServiceTests(_Base):
    def test_dashboard_composes_and_is_select_only(self):
        best = self.marker_with_reality(80, uses=2, label='best')
        habitual = self.marker_with_reality(100, uses=3, label='habit')
        with CaptureQueriesContext(connection) as ctx:
            dash = intel.executive_dashboard()
        writes = [q for q in ctx.captured_queries
                  if q['sql'].split()[0].upper() in
                  ('INSERT', 'UPDATE', 'DELETE')]
        self.assertEqual(writes, [])
        row = next(r for r in dash['products']
                   if r['product'].pk == self.product.pk)
        self.assertEqual(row['best_reference'], best.reference)
        self.assertEqual(row['practice_reference'], habitual.reference)
        self.assertFalse(row['saving']['already_best'])
        self.assertEqual(str(row['saving']['delta_m_per_100']), '20.00')
        self.assertEqual(dash['kpis']['markers_total'], 2)
        self.assertEqual(dash['kpis']['outcomes'], 5)
        origins = {o['origin']: o for o in dash['origins']}
        self.assertEqual(origins['imported']['with_reality'], 2)

    def test_suggestion_followup_derives_reality_since_decision(self):
        m = self.marker_with_reality(90, label='sf')
        payload = adv.offer_payload(adv.recommend(self.product))
        ev = sug.record_offer(user=self.mgr, product=self.product,
                              payload=payload, source='advisor:v1')
        sug.decide(user=self.mgr, event=ev, outcome='accepted')
        # one MORE outcome AFTER the decision
        usage = fb.record_usage(user=self.mgr, marker=m, adda=self.adda,
                                plies=10, repeats=1)
        fb.record_outcome(user=self.mgr, usage=usage, fabric_in_mm=7000,
                          garments_cut=10)
        stats = intel.suggestion_stats()
        self.assertEqual(stats['counts']['accepted'], 1)
        self.assertEqual(str(stats['acceptance_rate_pct']), '100.00')
        f = stats['accepted_followups'][0]
        self.assertEqual(f['shown_reference'], m.reference)
        self.assertEqual(f['since']['n'], 1)          # only the post-decision one
        self.assertEqual(str(f['since']['avg_m_per_100']), '70.00')

    def test_trend_buckets(self):
        self.marker_with_reality(90, uses=2, label='tr')
        trend = intel.outcome_trend(months=3)
        self.assertEqual(len(trend), 3)
        self.assertEqual(trend[-1]['count'], 2)       # this month
        self.assertEqual(trend[-1]['bar_pct'], 100)

    def test_empty_factory_is_honest(self):
        dash = intel.executive_dashboard()
        self.assertEqual(dash['kpis']['markers_total'], 0)
        self.assertEqual(dash['products'], [])
        self.assertIsNone(dash['suggestions']['acceptance_rate_pct'])


class InsightsViewTests(_Base):
    def test_permissions(self):
        url = reverse('patterns_ai:insights')
        self.client.force_login(self.worker)
        self.assertEqual(self.client.get(url).status_code, 403)
        self.client.logout()
        self.assertEqual(self.client.get(url).status_code, 302)

    def test_renders_honestly(self):
        self.marker_with_reality(80, label='ui-best')
        self.marker_with_reality(100, uses=2, label='ui-habit')
        self.client.force_login(self.mgr)
        resp = self.client.get(reverse('patterns_ai:insights'))
        self.assertContains(resp, 'POTENTIAL')        # saving label
        self.assertContains(resp, '20.00 m/100')
        self.assertContains(resp, 'derived live from immutable facts')
        self.assertContains(resp, "the facts don't exist yet")  # footer honesty


class HealthCommandTests(_Base):
    def test_healthy_run(self):
        out = io.StringIO()
        call_command('patterns_ai_health', stdout=out)
        text = out.getvalue()
        self.assertIn('HEALTHY', text)
        self.assertIn('compute venv', text)
        self.assertIn('tool nest', text)
        self.assertIn('media integrity', text)

    def test_degraded_exit_on_missing_runtime(self):
        with override_settings(PATTERNS_AI_COMPUTE_DIR='/nonexistent'):
            out = io.StringIO()
            with self.assertRaises(SystemExit) as cm:
                call_command('patterns_ai_health', stdout=out)
            self.assertEqual(cm.exception.code, 1)
            self.assertIn('DEGRADED', out.getvalue())


class WorkflowIntegrationTests(_Base):
    def test_adda_detail_shows_advisor_links_to_management(self):
        self.client.force_login(self.mgr)
        resp = self.client.get(reverse('production:adda-detail',
                                       args=[self.adda.code]))
        self.assertContains(resp, 'Cut Advisor')
        self.assertContains(
            resp, f"/patterns/advisor/?product={self.product.pk}")
        self.assertContains(resp, 'Pattern Library')
        # and the link target actually serves the prefilled advisor
        resp = self.client.get(f'/patterns/advisor/?product={self.product.pk}')
        self.assertEqual(resp.status_code, 200)

    def test_boundary_still_holds(self):
        """The integration is template-level ONLY — the python walls that
        enforce ADR-H must still pass (they run in test_purity too; this
        is the P5-local assertion that the edit kept the direction)."""
        import pathlib
        import re
        config_dir = pathlib.Path(__file__).resolve().parents[2]
        pat = re.compile(r'^\s*(from|import)\s+patterns_ai', re.M)
        offenders = [str(p) for p in (config_dir / 'production').rglob('*.py')
                     if 'migrations' not in p.parts
                     and pat.search(p.read_text(errors='ignore'))]
        self.assertEqual(offenders, [])
