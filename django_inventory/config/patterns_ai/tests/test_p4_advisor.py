"""P4 tests — the Cut Advisor: ranking honesty (reality beats theory),
width bands, saving math, confidence components, SELECT-only brain,
suggestion decision spine (one-shot, guarded), views.
"""
import tempfile

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from accounts.models import Role
from production.models import (Adda, Product, Stage,
                               WorkflowStage)
from patterns_ai.models import Marker, SuggestionEvent
from patterns_ai.services import advisor_service as adv
from patterns_ai.services import marker_feedback_service as fb
from patterns_ai.services import marker_service as ms
from patterns_ai.services import suggestion_service as sug

User = get_user_model()
MEDIA = tempfile.mkdtemp(prefix='pai-p4-media-')


@override_settings(MEDIA_ROOT=MEDIA)
class _Base(TestCase):
    @classmethod
    def setUpTestData(cls):
        mgr = Role.objects.get_or_create(code='manager', defaults={'name': 'M'})[0]
        wk = Role.objects.get_or_create(code='worker', defaults={'name': 'W'})[0]
        cls.mgr = User.objects.create_user('p4@test.local', password='x', role=mgr)
        cls.worker = User.objects.create_user('p4w@test.local', password='x', role=wk)
        cls.product = Product.objects.create(code='P4PROD', name='P4 Product')
        st, _ = Stage.objects.get_or_create(code='p4_s', defaults={'name': 'S'})
        ws = WorkflowStage.objects.create(product=cls.product, stage=st, order=1)
        cls.adda = Adda.objects.create(code='P4-ADDA', product=cls.product,
                                       current_stage=ws)

    def marker(self, width=900, ratio=None, label='m'):
        return ms.create_marker(user=self.mgr, product=self.product,
                                origin=Marker.Origin.IMPORTED,
                                usable_width_mm=width,
                                ratio_counts=ratio or {}, label=label)

    def outcome(self, marker, m_per_100, garments=10):
        usage = fb.record_usage(user=self.mgr, marker=marker,
                                adda=self.adda, plies=garments, repeats=1)
        fb.record_outcome(user=self.mgr, usage=usage,
                          fabric_in_mm=int(m_per_100 * 10 * garments),
                          garments_cut=garments)
        return usage


class RankingTests(_Base):
    def test_proven_beats_theory_always(self):
        good = self.marker(label='proven-good')
        self.outcome(good, 80)
        # theory-only generated marker with a spectacular number
        from patterns_ai.models import (GeneratedMarkerCandidate,
                                        MarkerGenerationRun)
        run = MarkerGenerationRun.objects.create(     # test fixture only
            product=self.product, usable_width_mm=900,
            params={'schema_version': 1, 'ratio': {'1': 1}},
            pipeline_version='t', created_by=self.mgr)
        cand = GeneratedMarkerCandidate.objects.create(
            run=run, engine='blf',
            placements={'schema_version': 1, 'placements': []},
            marker_length_mm=100,
            verification={'ok': True, 'max_overlap_mm2': 0,
                          'within_width': True, 'piece_count': 0})
        ms.create_marker(user=self.mgr, product=self.product,
                         origin=Marker.Origin.GENERATED,
                         usable_width_mm=900, candidate=cand,
                         label='theory-spectacular')
        rec = adv.recommend(self.product)
        self.assertEqual(rec['best']['reference'], good.reference)
        self.assertEqual(len(rec['untested']), 1)
        self.assertEqual(rec['untested'][0]['origin'], 'generated')
        self.assertIsNotNone(rec['untested'][0]['theoretical_m_per_100'])

    def test_reality_ranking_and_ties(self):
        a = self.marker(label='a')
        b = self.marker(label='b')
        self.outcome(a, 90)
        self.outcome(b, 70)
        self.outcome(b, 74)
        rec = adv.recommend(self.product)
        self.assertEqual(rec['best']['reference'], b.reference)
        self.assertEqual(rec['best']['n'], 2)
        self.assertEqual([r['reference'] for r in rec['proven']],
                         [b.reference, a.reference])

    def test_saving_vs_current_practice(self):
        habitual = self.marker(label='habitual')
        better = self.marker(label='better')
        # habitual: used 3x at 100 m/100; better: once at 80
        for _ in range(3):
            self.outcome(habitual, 100)
        self.outcome(better, 80)
        rec = adv.recommend(self.product)
        self.assertEqual(rec['best']['reference'], better.reference)
        s = rec['saving']
        self.assertFalse(s['already_best'])
        self.assertEqual(s['baseline_reference'], habitual.reference)
        self.assertEqual(str(s['delta_m_per_100']), '20.00')
        self.assertEqual(str(s['pct']), '20.00')

    def test_already_best_honesty(self):
        only = self.marker(label='only')
        self.outcome(only, 95)
        self.outcome(only, 95)
        rec = adv.recommend(self.product)
        self.assertTrue(rec['saving']['already_best'])

    def test_width_scoping_and_fallback(self):
        wide = self.marker(width=1200, label='wide')
        narrow = self.marker(width=900, label='narrow')
        self.outcome(wide, 60)
        self.outcome(narrow, 90)
        rec = adv.recommend(self.product, width_mm=900)
        self.assertEqual(rec['best']['reference'], narrow.reference)
        self.assertEqual(rec['best']['width_match'], 'exact')
        rec_all = adv.recommend(self.product)
        self.assertEqual(rec_all['best']['reference'], wide.reference)
        # width with NO match anywhere -> honest fallback flag, all shown
        rec_fb = adv.recommend(self.product, width_mm=2000)
        self.assertTrue(rec_fb['width_fallback_used'])
        self.assertIsNotNone(rec_fb['best'])

    def test_width_advice_bands(self):
        w9 = self.marker(width=900, label='w9')
        w12 = self.marker(width=1200, label='w12')
        self.outcome(w9, 90)
        self.outcome(w12, 75)
        advice = adv.recommend(self.product)['width_advice']
        self.assertEqual(advice[0]['best_reference'], w12.reference)
        self.assertEqual(len(advice), 2)

    def test_no_facts_honesty(self):
        self.marker(label='virgin')
        rec = adv.recommend(self.product)
        self.assertTrue(rec['no_facts'])
        self.assertIsNone(rec['best'])

    def test_confidence_components(self):
        m = self.marker(label='conf')
        for _ in range(5):
            self.outcome(m, 88)
        rec = adv.recommend(self.product)
        comp = rec['confidence']['components']
        self.assertEqual(comp['evidence_depth'], 1.0)     # n=5
        self.assertGreaterEqual(comp['recency'], 0.99)    # just now
        self.assertEqual(comp['consistency'], 1.0)        # identical outcomes
        self.assertEqual(comp['width_match'], 0.85)       # 'any'
        self.assertIn('human decides', rec['confidence']['note'])

    def test_advisor_is_select_only(self):
        m = self.marker(label='ro')
        self.outcome(m, 90)
        with CaptureQueriesContext(connection) as ctx:
            adv.recommend(self.product)
        writes = [q for q in ctx.captured_queries
                  if q['sql'].split()[0].upper() in
                  ('INSERT', 'UPDATE', 'DELETE')]
        self.assertEqual(writes, [])

    def test_offer_payload_is_json_safe(self):
        import json
        m = self.marker(label='payload', ratio={'s': 2})
        self.outcome(m, 85)
        payload = adv.offer_payload(adv.recommend(self.product))
        json.dumps(payload)                                # must not raise
        self.assertEqual(payload['schema_version'], 1)
        self.assertEqual(payload['best']['reference'], m.reference)


class SuggestionSpineTests(_Base):
    def offer(self):
        m = self.marker(label='sp')
        self.outcome(m, 90)
        payload = adv.offer_payload(adv.recommend(self.product))
        return sug.record_offer(user=self.mgr, product=self.product,
                                payload=payload, source=adv.ADVISOR_VERSION)

    def test_offer_and_one_shot_decide(self):
        ev = self.offer()
        self.assertEqual(ev.outcome, 'offered')
        self.assertEqual(ev.source, 'advisor:v1')
        sug.decide(user=self.mgr, event=ev, outcome='accepted')
        ev.refresh_from_db()
        self.assertEqual(ev.outcome, 'accepted')
        self.assertEqual(ev.decided_by, self.mgr)
        with self.assertRaises(ValidationError):          # one-shot
            sug.decide(user=self.mgr, event=ev, outcome='rejected',
                       reason='changed mind')

    def test_reject_needs_reason_and_worker_blocked(self):
        ev = self.offer()
        with self.assertRaises(ValidationError):
            sug.decide(user=self.mgr, event=ev, outcome='rejected',
                       reason='  ')
        with self.assertRaises(PermissionDenied):
            sug.decide(user=self.worker, event=ev, outcome='accepted')
        with self.assertRaises(ValidationError):          # non-human outcome
            sug.decide(user=self.mgr, event=ev, outcome='offered')

    def test_payload_needs_schema_version(self):
        with self.assertRaises(ValidationError):
            sug.record_offer(user=self.mgr, product=self.product,
                             payload={'best': None}, source='advisor:v1')

    def test_rows_are_guarded(self):
        ev = self.offer()
        ev.source = 'hacked'
        with self.assertRaises(ValueError):
            ev.save()
        with self.assertRaises(ValueError):
            ev.delete()


class AdvisorViewTests(_Base):
    def test_permissions_and_tampering(self):
        url = reverse('patterns_ai:advisor')
        self.client.force_login(self.worker)
        self.assertEqual(self.client.get(url).status_code, 403)
        self.client.logout()
        self.assertEqual(self.client.get(url).status_code, 302)
        self.client.force_login(self.mgr)
        self.assertEqual(self.client.get(url + '?product=abc').status_code,
                         404)

    def test_page_renders_recommendation_and_honesty(self):
        m = self.marker(label='ui')
        self.outcome(m, 85)
        self.client.force_login(self.mgr)
        resp = self.client.get(reverse('patterns_ai:advisor')
                               + f'?product={self.product.pk}')
        self.assertContains(resp, 'Best marker: ' + m.reference)
        self.assertContains(resp, 'confidence')
        self.assertContains(resp, 'YOU decide')
        self.assertContains(resp, 'best-proven marker')   # already-best save

    def test_no_facts_page(self):
        self.marker(label='bare')
        self.client.force_login(self.mgr)
        resp = self.client.get(reverse('patterns_ai:advisor')
                               + f'?product={self.product.pk}')
        self.assertContains(resp, 'No proven facts yet')

    def test_offer_and_decide_via_ui(self):
        m = self.marker(label='flow')
        self.outcome(m, 85)
        self.client.force_login(self.mgr)
        url = reverse('patterns_ai:advisor')
        resp = self.client.post(url, {'product': self.product.pk,
                                      'action': 'offer'}, follow=True)
        self.assertContains(resp, 'recorded')
        ev = SuggestionEvent.objects.latest('id')
        self.assertEqual(ev.payload['best']['reference'], m.reference)
        resp = self.client.post(url, {'product': self.product.pk,
                                      'action': f'decide_{ev.pk}',
                                      'outcome': 'accepted'}, follow=True)
        self.assertContains(resp, 'Decision recorded')
        ev.refresh_from_db()
        self.assertEqual(ev.outcome, 'accepted')
        # rejected without reason -> error message, still offered? (decided
        # already here) — fresh offer:
        resp = self.client.post(url, {'product': self.product.pk,
                                      'action': 'offer'}, follow=True)
        ev2 = SuggestionEvent.objects.latest('id')
        resp = self.client.post(url, {'product': self.product.pk,
                                      'action': f'decide_{ev2.pk}',
                                      'outcome': 'rejected', 'reason': ''},
                                follow=True)
        self.assertContains(resp, 'reason')
        ev2.refresh_from_db()
        self.assertEqual(ev2.outcome, 'offered')

    def test_worker_cannot_post_decisions(self):
        ev = SuggestionEvent.objects.create(   # fixture
            product=self.product, source='advisor:v1',
            payload={'schema_version': 1}, created_by=self.mgr)
        self.client.force_login(self.worker)
        resp = self.client.post(reverse('patterns_ai:advisor'),
                                {'product': self.product.pk,
                                 'action': f'decide_{ev.pk}',
                                 'outcome': 'accepted'})
        self.assertEqual(resp.status_code, 403)
        ev.refresh_from_db()
        self.assertEqual(ev.outcome, 'offered')
