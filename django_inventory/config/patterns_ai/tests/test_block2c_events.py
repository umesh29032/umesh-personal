"""Block-2C tests — immutable events + biography read model.

Covers: one event per transition (creation, governed transitions,
supersede-flip) · append-only guarantees (update/delete refused at model
level) · event ordering · biography correctness across superseded / rejected
/ promoted chains · lineage · summary calculations (honest n) · query helpers
write NOTHING (SELECT-only proof).
"""
from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from accounts.models import Role
from production.models import Adda, Product, Stage, WorkflowStage
from patterns_ai.models import Marker, MarkerTransitionEvent
from patterns_ai.services import marker_service as ms
from patterns_ai.services import marker_feedback_service as fb
from patterns_ai.services import marker_query_service as q

User = get_user_model()


class _Base(TestCase):
    @classmethod
    def setUpTestData(cls):
        mgr = Role.objects.get_or_create(code='manager', defaults={'name': 'M'})[0]
        cls.mgr = User.objects.create_user('pai2c@test.local', password='x', role=mgr)
        cls.product = Product.objects.create(code='PAI2C', name='PAI 2C')
        st, _ = Stage.objects.get_or_create(code='pai2c_s', defaults={'name': 'S'})
        ws = WorkflowStage.objects.create(product=cls.product, stage=st, order=1)
        cls.adda = Adda.objects.create(code='PAI2C-001', product=cls.product,
                                       current_stage=ws)

    def mk(self, **kw):
        d = dict(user=self.mgr, product=self.product,
                 origin=Marker.Origin.IMPORTED, usable_width_mm=940)
        d.update(kw)
        return ms.create_marker(**d)


class EventTests(_Base):
    def test_creation_emits_exactly_one_event(self):
        m = self.mk()
        evs = list(m.transition_events.all())
        self.assertEqual(len(evs), 1)
        self.assertEqual((evs[0].from_status, evs[0].to_status), ('', 'candidate'))
        self.assertEqual(evs[0].actor_id, self.mgr.pk)
        self.assertEqual(evs[0].transition_version, ms.TRANSITIONS_VERSION)
        self.assertEqual(evs[0].metadata['schema_version'], 1)

    def test_transition_emits_exactly_one_event_no_duplicates(self):
        m = self.mk()
        ms.transition_marker(user=self.mgr, marker=m, to_status='validated')
        ms.transition_marker(user=self.mgr, marker=m, to_status='retired',
                             reason='worn')
        evs = list(MarkerTransitionEvent.objects.filter(marker=m).order_by('id'))
        self.assertEqual([(e.from_status, e.to_status) for e in evs],
                         [('', 'candidate'), ('candidate', 'validated'),
                          ('validated', 'retired')])
        self.assertEqual(evs[-1].reason, 'worn')

    def test_failed_transition_emits_nothing(self):
        m = self.mk()
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            ms.transition_marker(user=self.mgr, marker=m, to_status='superseded')
        self.assertEqual(m.transition_events.count(), 1)   # creation only

    def test_supersede_flip_emits_event_on_old_marker(self):
        old = self.mk()
        new = self.mk(supersedes=old)
        ev = old.transition_events.order_by('id').last()
        self.assertEqual((ev.from_status, ev.to_status), ('candidate', 'superseded'))
        self.assertEqual(ev.metadata.get('superseded_by'), new.reference)

    def test_append_only_no_update_no_delete(self):
        m = self.mk()
        ev = m.transition_events.first()
        ev.reason = 'tamper'
        with self.assertRaises(RuntimeError):
            ev.save()
        with self.assertRaises(RuntimeError):
            ev.delete()
        # queryset-level delete is not reachable through any service; the
        # I-1 guard keeps writes inside services, which never call it.


class BiographyTests(_Base):
    def test_full_lifecycle_biography_order(self):
        m = self.mk(label='chalk')
        ms.transition_marker(user=self.mgr, marker=m, to_status='validated')
        u = fb.record_usage(user=self.mgr, marker=m, adda=self.adda,
                            plies=30, repeats=3)
        fb.record_outcome(user=self.mgr, usage=u, fabric_in_mm=45000,
                          garments_cut=60)
        fb.void_usage(user=self.mgr, usage=u, reason='recount')
        bio = q.get_marker_biography(m)
        kinds = [e['kind'] for e in bio]
        self.assertEqual(kinds[0], 'transition')            # creation first
        self.assertIn('usage', kinds)
        self.assertIn('outcome', kinds)
        self.assertIn('usage_void', kinds)
        ats = [e['at'] for e in bio]
        self.assertEqual(ats, sorted(ats))                  # oldest first

    def test_promoted_chain_biography(self):
        t = self.mk(origin=Marker.Origin.ADDA_TEMPORARY, adda=self.adda)
        ms.transition_marker(user=self.mgr, marker=t, to_status='promoted')
        ms.transition_marker(user=self.mgr, marker=t, to_status='validated')
        trans = [(e['from'], e['to']) for e in q.get_marker_biography(t)
                 if e['kind'] == 'transition']
        self.assertEqual(trans, [(None, 'candidate'), ('candidate', 'promoted'),
                                 ('promoted', 'validated')])

    def test_rejected_chain_biography(self):
        m = self.mk()
        ms.transition_marker(user=self.mgr, marker=m, to_status='rejected',
                             reason='bad ratio')
        last = [e for e in q.get_marker_biography(m) if e['kind'] == 'transition'][-1]
        self.assertEqual(last['to'], 'rejected')
        self.assertEqual(last['reason'], 'bad ratio')


class LineageTests(_Base):
    def test_superseded_chain_and_benchmarks(self):
        a = self.mk()
        b = self.mk(supersedes=a)
        c = self.mk(supersedes=b, benchmarked_against=a)
        lin = q.get_marker_lineage(c)
        self.assertEqual(lin['supersedes_chain'], [b, a])   # walk backward
        self.assertEqual(lin['benchmarked_against'], a)
        lin_a = q.get_marker_lineage(a)
        self.assertEqual(lin_a['superseded_by'], [b])
        self.assertEqual(lin_a['benchmark_children'], [c])


class SummaryTests(_Base):
    def test_summary_counts_and_honest_average(self):
        m = self.mk()
        s0 = q.get_marker_summary(m)
        self.assertEqual((s0['usage_count'], s0['n_for_average']), (0, 0))
        self.assertIsNone(s0['avg_meters_per_100'])
        u1 = fb.record_usage(user=self.mgr, marker=m, adda=self.adda, plies=30)
        fb.record_outcome(user=self.mgr, usage=u1, fabric_in_mm=45000,
                          garments_cut=60)                   # 75.00 m/100
        u2 = fb.record_usage(user=self.mgr, marker=m, adda=self.adda, plies=20)
        fb.record_outcome(user=self.mgr, usage=u2, fabric_in_mm=30000,
                          garments_cut=50)                   # 60.00 m/100
        u3 = fb.record_usage(user=self.mgr, marker=m, adda=self.adda, plies=5)
        fb.void_usage(user=self.mgr, usage=u3, reason='mistake')
        s = q.get_marker_summary(m)
        self.assertEqual(s['usage_count'], 2)
        self.assertEqual(s['voided_usage_count'], 1)
        self.assertEqual(s['n_for_average'], 2)
        self.assertEqual(str(s['avg_meters_per_100']), '67.50')
        self.assertIsNotNone(s['last_used_at'])

    def test_voided_outcome_excluded_from_average(self):
        m = self.mk()
        u = fb.record_usage(user=self.mgr, marker=m, adda=self.adda, plies=30)
        fb.record_outcome(user=self.mgr, usage=u, fabric_in_mm=45000,
                          garments_cut=60)
        fb.void_usage(user=self.mgr, usage=u, reason='bad count')
        s = q.get_marker_summary(m)
        self.assertEqual(s['n_for_average'], 0)
        self.assertIsNone(s['avg_meters_per_100'])


class ReadOnlyProofTests(_Base):
    def test_query_service_issues_only_selects(self):
        m = self.mk()
        ms.transition_marker(user=self.mgr, marker=m, to_status='validated')
        u = fb.record_usage(user=self.mgr, marker=m, adda=self.adda, plies=30)
        fb.record_outcome(user=self.mgr, usage=u, fabric_in_mm=45000,
                          garments_cut=60)
        with CaptureQueriesContext(connection) as ctx:
            q.get_marker_biography(m)
            q.get_marker_lineage(m)
            q.get_marker_usage_history(m)
            q.get_marker_outcomes(m)
            q.get_marker_summary(m)
        writes = [qq['sql'] for qq in ctx.captured_queries
                  if qq['sql'].split()[0].upper() not in ('SELECT', 'SAVEPOINT', 'RELEASE')]
        self.assertEqual(writes, [], 'query service must be pure read')
