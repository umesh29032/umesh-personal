"""Block-2B service tests — exhaustive walk of both single writers.

Covers: happy paths · every illegal transition · duplicate/collision-safe
references · promotion (D11 incl. wrong-origin refusal) · rejection/retirement
reasons · append-only guarantees (facts never change; usage void-not-edit) ·
lineage validation (cross-product + rejected targets + PROTECT) · width_band
stamping · quantization (I-4) · derived-at-read (versioned, never persisted).
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase

from accounts.models import Role
from production.models import Adda, Product, Stage, WorkflowStage
from patterns_ai.models import Marker, MarkerOutcome
from patterns_ai.services import marker_service as ms
from patterns_ai.services import marker_feedback_service as fb
from patterns_ai.services.units import mm_to_m, q2, to_int_mm, width_band

User = get_user_model()


class _Base(TestCase):
    @classmethod
    def setUpTestData(cls):
        mgr = Role.objects.get_or_create(code='manager', defaults={'name': 'Manager'})[0]
        wk = Role.objects.get_or_create(code='worker', defaults={'name': 'Worker'})[0]
        cls.mgr = User.objects.create_user('pai2b-m@test.local', password='x', role=mgr)
        cls.worker = User.objects.create_user('pai2b-w@test.local', password='x', role=wk)
        cls.product = Product.objects.create(code='PAI2B', name='PAI 2B')
        cls.other_product = Product.objects.create(code='PAI2B-X', name='Other')
        st, _ = Stage.objects.get_or_create(code='pai2b_s', defaults={'name': 'S'})
        ws = WorkflowStage.objects.create(product=cls.product, stage=st, order=1)
        cls.adda = Adda.objects.create(code='PAI2B-001', product=cls.product,
                                       current_stage=ws)
        cls.adda2 = Adda.objects.create(code='PAI2B-002', product=cls.product,
                                        current_stage=ws)

    def mk(self, **kw):
        d = dict(user=self.mgr, product=self.product,
                 origin=Marker.Origin.IMPORTED, usable_width_mm=937)
        d.update(kw)
        return ms.create_marker(**d)


class UnitsTests(TestCase):
    def test_quantization_home(self):
        self.assertEqual(to_int_mm('45.4'), 45)
        self.assertEqual(to_int_mm('45.5'), 46)          # HALF_UP
        self.assertEqual(mm_to_m(45000), Decimal('45.00'))
        self.assertEqual(mm_to_m(45005), Decimal('45.01'))  # 2dp HALF_UP
        self.assertEqual(q2('79.305'), Decimal('79.31'))
        self.assertEqual(width_band(937), 93)
        self.assertEqual(width_band(940), 94)


class CreateMarkerTests(_Base):
    def test_happy_marker_reference_and_band(self):
        # imported origin here (photo-less legitimate); the manual+photo path
        # is covered end-to-end in test_block3b_workflow.
        m = self.mk(ratio_counts={'1': 2, '2': 1}, label='chalk 37in')
        self.assertRegex(m.reference, r'^MRK-\d{6}$')
        self.assertEqual(m.usable_width_band, 93)          # stamped floor(937/10)
        self.assertEqual(m.ratio, {'schema_version': 1, 'counts': {'1': 2, '2': 1}})
        m2 = self.mk()
        self.assertNotEqual(m.reference, m2.reference)     # unique sequence

    def test_gate_management_only(self):
        with self.assertRaises(PermissionDenied):
            self.mk(user=self.worker)

    def test_d11_adda_xor_origin(self):
        with self.assertRaises(ValidationError):
            self.mk(origin=Marker.Origin.ADDA_TEMPORARY)               # temp w/o adda
        with self.assertRaises(ValidationError):
            self.mk(adda=self.adda)                                    # non-temp w/ adda
        t = self.mk(origin=Marker.Origin.ADDA_TEMPORARY, adda=self.adda)
        self.assertEqual(t.status, Marker.Status.CANDIDATE)

    def test_strategy_only_for_generated(self):
        # P3 conscious rework: GENERATED markers now REQUIRE their immutable
        # candidate (D11 evidence chain) — fixture added, rule asserted.
        from patterns_ai.models import (GeneratedMarkerCandidate,
                                        MarkerGenerationRun)
        with self.assertRaises(ValidationError):
            self.mk(strategy='mixed')
        with self.assertRaises(ValidationError):      # generated w/o candidate
            self.mk(origin=Marker.Origin.GENERATED, strategy='mixed')
        run = MarkerGenerationRun.objects.create(     # test fixture only
            product=self.product, usable_width_mm=900,
            params={'schema_version': 1, 'ratio': {}},
            pipeline_version='test', created_by=self.mgr)
        cand = GeneratedMarkerCandidate.objects.create(
            run=run, engine='blf',
            placements={'schema_version': 1, 'placements': []},
            marker_length_mm=100,
            verification={'ok': True, 'max_overlap_mm2': 0,
                          'within_width': True, 'piece_count': 0})
        g = self.mk(origin=Marker.Origin.GENERATED, strategy='mixed',
                    candidate=cand)
        self.assertEqual(g.strategy, 'mixed')
        with self.assertRaises(ValidationError):      # candidate on non-generated
            self.mk(candidate=cand)

    def test_lineage_same_product_and_not_rejected(self):
        base = self.mk()
        with self.assertRaises(ValidationError):
            ms.create_marker(user=self.mgr, product=self.other_product,
                             origin=Marker.Origin.MANUAL_PHOTO,
                             usable_width_mm=900, benchmarked_against=base)
        bad = self.mk()
        ms.transition_marker(user=self.mgr, marker=bad,
                             to_status=Marker.Status.REJECTED, reason='test')
        with self.assertRaises(ValidationError):
            self.mk(benchmarked_against=bad)

    def test_supersede_flips_old_marker(self):
        old = self.mk()
        new = self.mk(supersedes=old)
        old.refresh_from_db()
        self.assertEqual(old.status, Marker.Status.SUPERSEDED)
        self.assertIn(new.reference, old.status_reason)


class TransitionTests(_Base):
    def test_full_legal_paths(self):
        m = self.mk()
        ms.transition_marker(user=self.mgr, marker=m, to_status='validated')
        m.refresh_from_db(); self.assertEqual(m.status, 'validated')
        ms.transition_marker(user=self.mgr, marker=m, to_status='retired',
                             reason='worn out')
        m.refresh_from_db(); self.assertEqual(m.status, 'retired')

    def test_terminal_states_lock(self):
        m = self.mk()
        ms.transition_marker(user=self.mgr, marker=m, to_status='rejected',
                             reason='bad ratio')
        for target in ('candidate', 'validated', 'promoted', 'retired'):
            with self.assertRaises(ValidationError):
                ms.transition_marker(user=self.mgr, marker=m, to_status=target,
                                     reason='x')

    def test_negative_requires_reason(self):
        m = self.mk()
        with self.assertRaises(ValidationError):
            ms.transition_marker(user=self.mgr, marker=m, to_status='rejected')
        with self.assertRaises(ValidationError):
            ms.transition_marker(user=self.mgr, marker=m, to_status='retired',
                                 reason='   ')

    def test_promotion_d11(self):
        normal = self.mk()
        with self.assertRaises(ValidationError):
            ms.transition_marker(user=self.mgr, marker=normal, to_status='promoted')
        temp = self.mk(origin=Marker.Origin.ADDA_TEMPORARY, adda=self.adda)
        ms.transition_marker(user=self.mgr, marker=temp, to_status='promoted')
        temp.refresh_from_db()
        self.assertEqual(temp.status, 'promoted')
        # promoted marker continues the ladder
        ms.transition_marker(user=self.mgr, marker=temp, to_status='validated')

    def test_illegal_jump(self):
        m = self.mk()
        with self.assertRaises(ValidationError):
            ms.transition_marker(user=self.mgr, marker=m, to_status='superseded')


class UsageTests(_Base):
    def test_happy_usage_and_void(self):
        m = self.mk()
        u = fb.record_usage(user=self.mgr, marker=m, adda=self.adda,
                            plies=30, repeats=3, measured_usable_width_mm=932)
        self.assertEqual((u.plies, u.repeats), (30, 3))
        with self.assertRaises(ValidationError):
            fb.void_usage(user=self.mgr, usage=u, reason='  ')
        fb.void_usage(user=self.mgr, usage=u, reason='wrong marker picked')
        u.refresh_from_db()
        self.assertIsNotNone(u.voided_at)
        with self.assertRaises(ValidationError):
            fb.void_usage(user=self.mgr, usage=u, reason='again')   # already voided

    def test_unusable_marker_refused_with_reason_in_error(self):
        m = self.mk()
        ms.transition_marker(user=self.mgr, marker=m, to_status='retired',
                             reason='mat damaged')
        with self.assertRaises(ValidationError) as ctx:
            fb.record_usage(user=self.mgr, marker=m, adda=self.adda, plies=10)
        self.assertIn('mat damaged', str(ctx.exception))

    def test_temporary_marker_only_on_its_adda(self):
        t = self.mk(origin=Marker.Origin.ADDA_TEMPORARY, adda=self.adda)
        with self.assertRaises(ValidationError):
            fb.record_usage(user=self.mgr, marker=t, adda=self.adda2, plies=5)
        u = fb.record_usage(user=self.mgr, marker=t, adda=self.adda, plies=5)
        self.assertEqual(u.adda_id, self.adda.pk)


class OutcomeTests(_Base):
    def _usage(self):
        m = self.mk()
        return fb.record_usage(user=self.mgr, marker=m, adda=self.adda,
                               plies=30, repeats=3)

    def test_record_and_one_per_usage(self):
        u = self._usage()
        fb.record_outcome(user=self.mgr, usage=u, fabric_in_mm=45000,
                          garments_cut=60, quality_flags=['dev_fixture'])
        from django.db import IntegrityError, transaction as tx
        with self.assertRaises(IntegrityError), tx.atomic():
            MarkerOutcome.objects.create(usage=u, recorded_by=self.mgr)

    def test_voided_usage_refuses_outcome(self):
        u = self._usage()
        fb.void_usage(user=self.mgr, usage=u, reason='redo')
        with self.assertRaises(ValidationError):
            fb.record_outcome(user=self.mgr, usage=u)

    def test_facts_fill_null_only_never_change(self):
        u = self._usage()
        o = fb.record_outcome(user=self.mgr, usage=u, fabric_in_mm=45000)
        fb.update_outcome_facts(user=self.mgr, outcome=o, garments_cut=60)
        o.refresh_from_db(); self.assertEqual(o.garments_cut, 60)
        with self.assertRaises(ValidationError):
            fb.update_outcome_facts(user=self.mgr, outcome=o, garments_cut=61)
        with self.assertRaises(ValidationError):
            fb.update_outcome_facts(user=self.mgr, outcome=o, nonsense=1)

    def test_derive_at_read_versioned_and_never_persisted(self):
        u = self._usage()
        o = fb.record_outcome(user=self.mgr, usage=u, fabric_in_mm=45000,
                              garments_cut=60, leftover_mm=1200)
        m = fb.derive_metrics(o)
        self.assertEqual(m['metrics_version'], fb.METRICS_VERSION)
        self.assertEqual(m['fabric_in_m'], Decimal('45.00'))
        self.assertEqual(m['meters_per_garment'], Decimal('0.75'))
        self.assertEqual(m['meters_per_100'], Decimal('75.00'))
        self.assertEqual(m['leftover_m'], Decimal('1.20'))
        self.assertIsNone(m['utilization_pct'])            # honest until geometry
        # nothing persisted by deriving
        before = MarkerOutcome.objects.filter(pk=o.pk).values()[0]
        fb.derive_metrics(o)
        after = MarkerOutcome.objects.filter(pk=o.pk).values()[0]
        self.assertEqual(before, after)

    def test_derive_honest_nulls(self):
        u = self._usage()
        o = fb.record_outcome(user=self.mgr, usage=u)     # all facts NULL
        m = fb.derive_metrics(o)
        self.assertIsNone(m['fabric_in_m'])
        self.assertIsNone(m['meters_per_garment'])
