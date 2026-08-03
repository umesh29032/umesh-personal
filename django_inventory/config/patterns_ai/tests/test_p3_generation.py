"""P3 tests — marker generation & optimization: REAL engines (BLF +
SVGnest/node), independent verification, run/candidate immutability,
derived-at-read metrics, benchmark gate, promotion single-writer, views.
"""
import shutil
import tempfile
import unittest
from decimal import Decimal
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import Role
from production.models import (Product, ProductPattern,
                               ProductPatternAssignment, ProductSize)
from patterns_ai.models import (GeneratedMarkerCandidate, Marker,
                                MarkerGenerationRun, MarkerTransitionEvent,
                                PatternPieceVersion, PieceSizeGeometry)
from patterns_ai.services import compute_bridge
from patterns_ai.services import marker_feedback_service as fb
from patterns_ai.services import marker_generation_service as gen
from patterns_ai.services import marker_service as ms
from patterns_ai.services import pattern_geometry_service as geo
from patterns_ai.services.svg_render import marker_svg

User = get_user_model()
MEDIA = tempfile.mkdtemp(prefix='pai-p3-media-')
RUNTIME_OK = compute_bridge.runtime_available()


def rect_um(w_mm, h_mm):
    w, h = int(w_mm * 1000), int(h_mm * 1000)
    return {'schema_version': 1, 'units': 'um', 'origin': 'bbox_min',
            'axes': 'x_right_y_up', 'chord_tolerance_um': 500,
            'outer': [[0, 0], [w, 0], [w, h], [0, h]], 'holes': [],
            'features': {'grain': {'angle_cdeg': 9000}, 'notches': [],
                         'drills': [], 'internal_lines': [],
                         'fold_edge': None, 'seam_allowance': 'as_cut'},
            'grade_rule': None}


@unittest.skipUnless(RUNTIME_OK, 'compute runtime required (ADR-F)')
@override_settings(MEDIA_ROOT=MEDIA)
class _Base(TestCase):
    @classmethod
    def setUpTestData(cls):
        mgr = Role.objects.get_or_create(code='manager', defaults={'name': 'M'})[0]
        wk = Role.objects.get_or_create(code='worker', defaults={'name': 'W'})[0]
        cls.mgr = User.objects.create_user('p3@test.local', password='x', role=mgr)
        cls.worker = User.objects.create_user('p3w@test.local', password='x', role=wk)
        cls.product = Product.objects.create(code='P3PROD', name='P3 Product')
        cls.size_m = ProductSize.objects.create(product=cls.product, code='m',
                                                label='M', display_order=1)
        # two pieces: FRONT 400x600 (pair), CUFF 200x300
        cls.front = cls._piece('p3-front', 'Front', is_pair=True)
        cls.cuff = cls._piece('p3-cuff', 'Cuff')
        cls._confirm_geometry(cls.front, rect_um(400, 600))
        cls._confirm_geometry(cls.cuff, rect_um(200, 300))

    @classmethod
    def _piece(cls, code, name, is_pair=False, on_fold=False):
        pattern = ProductPattern.objects.create(code=code, name=name)
        ProductPatternAssignment.objects.create(product=cls.product,
                                                pattern=pattern,
                                                pieces_count=1)
        piece = geo.create_piece(user=cls.mgr, product=cls.product,
                                 pattern=pattern, fabric_group='body',
                                 is_pair=is_pair)
        if on_fold:                          # flag set post-create for tests
            piece.on_fold = True
            piece.save(update_fields=['on_fold'])
        return piece

    @classmethod
    def _confirm_geometry(cls, piece, payload, size=None):
        draft = geo.get_or_create_draft(user=cls.mgr, piece=piece)
        PieceSizeGeometry.objects.create(       # test fixture only
            version=draft, size=size or cls.size_m, geometry=payload,
            trust_grade='photo_calibrated', created_by=cls.mgr)
        geo.confirm_version(user=cls.mgr, version=draft)
        return draft

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    def run_real(self, engine='auto', width=900, ratio_count=1, **kw):
        return gen.start_run(user=self.mgr, product=self.product,
                             usable_width_mm=width,
                             ratio={self.size_m: ratio_count},
                             timebox_s=8, engine=engine, **kw)


class EngineGoldenTests(_Base):
    """Real engines through the real bridge."""

    def test_auto_run_generates_verified_candidates(self):
        run, rows = self.run_real()
        self.assertGreaterEqual(len(rows), 1)
        engines = {r.engine for r in rows}
        self.assertIn('blf', engines)            # the always-available floor
        for r in rows:
            self.assertTrue(r.verification['ok'], r.verification)
            self.assertEqual(r.verification['max_overlap_mm2'], 0.0)
            self.assertTrue(r.verification['within_width'])
            # FRONT is a pair: 2 instances/garment + 1 cuff = 3 pieces
            self.assertEqual(r.verification['piece_count'], 3)
            self.assertGreater(r.marker_length_mm, 0)
        # run params = full reproducibility spine
        self.assertEqual(run.params['schema_version'], 1)
        self.assertEqual(len(run.params['pieces']), 2)
        for src in run.params['pieces']:
            self.assertIn('geometry_row_id', src)

    def test_blf_is_deterministic(self):
        _, rows1 = self.run_real(engine='blf')
        _, rows2 = self.run_real(engine='blf')
        self.assertEqual(rows1[0].placements, rows2[0].placements)
        self.assertEqual(rows1[0].marker_length_mm,
                         rows2[0].marker_length_mm)

    def test_width_too_small_refuses_honestly(self):
        with self.assertRaises(ValidationError) as cm:
            self.run_real(engine='blf', width=300)   # front needs 400+spacing
        self.assertIn('fit', str(cm.exception))
        self.assertEqual(MarkerGenerationRun.objects.count(), 0)

    def test_verify_layout_catches_crafted_overlap(self):
        """The independent verifier is itself verified: feed nest.py's
        verifier an overlapping layout via a candidate row and read the
        stored verdict path (unit-level, through the runtime)."""
        import json as _json
        from pathlib import Path
        base = compute_bridge.compute_dir()
        with tempfile.TemporaryDirectory() as td:
            jin = Path(td) / 'j.json'
            jout = Path(td) / 'o.json'
            # two identical rectangles on top of each other must FAIL —
            # crafted via a direct verifier exercise: run blf on one piece
            # then duplicate its placement by running with qty 2 width huge
            jin.write_text(_json.dumps({
                'width_mm': 2000, 'engine': 'blf', 'spacing_mm': 3,
                'pieces': [{'key': 'a', 'qty': 2, 'allow_180': False,
                            'allow_mirror': False,
                            'polygon_mm': [[0, 0], [100, 0], [100, 100],
                                           [0, 100]]}]}))
            import subprocess
            subprocess.run([str(base / 'venv/bin/python'),
                            str(base / 'nest.py'), '--in', str(jin),
                            '--out', str(jout)], check=True,
                           capture_output=True)
            res = _json.loads(jout.read_text())
            good = res['candidates'][0]
            self.assertTrue(good['verification']['ok'])
            # now CORRUPT the layout: stack both instances at instance 0's spot
            bad = dict(good)
            p0 = dict(bad['placements'][0])
            p1 = dict(bad['placements'][1])
            p1['polygon_mm'] = p0['polygon_mm']
            jin.write_text(_json.dumps({'width_mm': 2000, 'spacing_mm': 3,
                                        'placements': [p0, p1]}))
            # verifier is importable inside the runtime; exercise via python -c
            code = ('import json,sys; sys.path.insert(0,%r); '
                    'from nest import verify_layout; '
                    'j=json.load(open(%r)); '
                    'v,l=verify_layout(j["width_mm"], j["placements"], 3); '
                    'print(json.dumps(v))' % (str(base), str(jin)))
            out = subprocess.run([str(base / 'venv/bin/python'), '-c', code],
                                 capture_output=True, text=True, check=True)
            verdict = _json.loads(out.stdout)
            self.assertFalse(verdict['ok'])
            self.assertGreater(verdict['max_overlap_mm2'], 100)


class GenerationServiceTests(_Base):
    def test_ratio_and_geometry_validations(self):
        with self.assertRaises(ValidationError):    # empty ratio
            gen.start_run(user=self.mgr, product=self.product,
                          usable_width_mm=900, ratio={})
        with self.assertRaises(ValidationError):    # width bounds
            self.run_real(width=100)
        with self.assertRaises(PermissionDenied):
            gen.start_run(user=self.worker, product=self.product,
                          usable_width_mm=900, ratio={self.size_m: 1})

    def test_missing_confirmed_geometry_named(self):
        naked = self._piece('p3-naked', 'Sleeve')   # no confirmed version
        with self.assertRaises(ValidationError) as cm:
            self.run_real(engine='blf')
        self.assertIn('Sleeve', str(cm.exception))
        self.assertIn('no confirmed version', str(cm.exception))

    def test_on_fold_refused_honestly(self):
        folded = self._piece('p3-fold', 'Back Yoke', on_fold=True)
        self._confirm_geometry(folded, rect_um(100, 100))
        with self.assertRaises(ValidationError) as cm:
            self.run_real(engine='blf')
        self.assertIn('on-fold', str(cm.exception))
        self.assertIn('Back Yoke', str(cm.exception))

    def test_run_and_candidate_are_immutable(self):
        run, rows = self.run_real(engine='blf')
        run.usable_width_mm = 999
        with self.assertRaises(ValueError):
            run.save()
        with self.assertRaises(ValueError):
            run.delete()
        c = rows[0]
        c.marker_length_mm = Decimal('1')
        with self.assertRaises(ValueError):
            c.save()
        with self.assertRaises(ValueError):
            c.delete()

    def test_metrics_derived_not_stored(self):
        _, rows = self.run_real(engine='blf')
        c = rows[0]
        m = gen.derive_candidate_metrics(c)
        self.assertTrue(m['verified'])
        self.assertEqual(m['garments'], 1)
        self.assertEqual(m['piece_count'], 3)
        # honest math: piece area / (length x width)
        area = 2 * 400 * 600 + 200 * 300
        expect = Decimal(str(round(
            area / (float(c.marker_length_mm) * 900) * 100, 2)))
        self.assertEqual(m['utilization_pct'], expect)
        self.assertEqual(m['waste_pct'], Decimal('100') - expect)
        # no metric column exists on the model (schema honesty)
        fields = {f.name for f in GeneratedMarkerCandidate._meta.fields}
        self.assertFalse({'utilization', 'utilization_pct', 'waste',
                          'waste_pct'} & fields)


class BenchmarkAndPromotionTests(_Base):
    def make_adda(self, code):
        from production.models import Adda, Stage, WorkflowStage
        st, _ = Stage.objects.get_or_create(code='p3_s', defaults={'name': 'S'})
        ws = WorkflowStage.objects.filter(product=self.product,
                                          stage=st).first()
        if ws is None:
            ws = WorkflowStage.objects.create(product=self.product,
                                              stage=st, order=1)
        return Adda.objects.create(code=code, product=self.product,
                                   current_stage=ws)

    def manual_marker_with_outcome(self, m_per_100):
        """A manual-origin marker with ONE recorded outcome at the given
        actual consumption (reality baseline)."""
        marker = ms.create_marker(user=self.mgr, product=self.product,
                                  origin=Marker.Origin.IMPORTED,
                                  usable_width_mm=900,
                                  label='manual baseline')
        adda = self.make_adda('P3-ADDA-1')
        usage = fb.record_usage(user=self.mgr, marker=marker, adda=adda,
                                plies=10, repeats=1)
        # m/100 = fabric_mm/plies / garments_per_ply(=ratio garments) ... use
        # the service's own math: garments = plies * repeats * ratio(=1 dflt)
        # target m/100 -> fabric_in_mm so that derive gives m_per_100
        garments = 10
        fabric_mm = int(m_per_100 * 10 * garments)   # m/100 -> mm/garment*100
        fb.record_outcome(user=self.mgr, usage=usage,
                          fabric_in_mm=fabric_mm, garments_cut=garments)
        return marker

    def test_promotion_no_baseline_allowed_with_honest_evidence(self):
        _, rows = self.run_real(engine='blf')
        c = rows[0]
        bench = gen.benchmark_candidate(c)
        self.assertEqual(bench['verdict'], 'no_baseline')
        marker, bench2 = gen.promote_candidate(user=self.mgr, candidate=c,
                                               label='gen one')
        self.assertEqual(marker.origin, Marker.Origin.GENERATED)
        self.assertEqual(marker.candidate_id, c.pk)
        self.assertEqual(marker.usable_width_mm, 900)
        ev = MarkerTransitionEvent.objects.filter(marker=marker).first()
        self.assertEqual(ev.metadata.get('benchmark_evidence', {}).get('verdict'),
                         'no_baseline')
        with self.assertRaises(ValidationError):     # promote once
            gen.promote_candidate(user=self.mgr, candidate=c)

    def test_promotion_refused_when_not_beating_baseline(self):
        # crafted GOOD reality: manual marker at 50 m/100 actual —
        # candidate theory (~1.2m length for 1 garment => ~120 m/100) loses
        self.manual_marker_with_outcome(m_per_100=50)
        _, rows = self.run_real(engine='blf')
        c = rows[0]
        bench = gen.benchmark_candidate(c)
        self.assertEqual(bench['verdict'], 'does_not_beat')
        with self.assertRaises(ValidationError) as cm:
            gen.promote_candidate(user=self.mgr, candidate=c)
        self.assertIn('does not beat', str(cm.exception))
        self.assertEqual(Marker.objects.filter(
            origin=Marker.Origin.GENERATED).count(), 0)

    def test_promotion_allowed_when_beating_baseline(self):
        # crafted BAD reality: manual at 500 m/100 — candidate theory wins
        base = self.manual_marker_with_outcome(m_per_100=500)
        _, rows = self.run_real(engine='blf')
        c = rows[0]
        marker, bench = gen.promote_candidate(user=self.mgr, candidate=c)
        self.assertEqual(bench['verdict'], 'beats')
        self.assertEqual(marker.benchmarked_against_id, base.pk)
        ev = MarkerTransitionEvent.objects.filter(marker=marker).first()
        evidence = ev.metadata['benchmark_evidence']
        self.assertEqual(evidence['baseline_actual_m_per_100'], '500.00')
        self.assertIn('THEORY', evidence['labels'])

    def test_unverified_candidate_never_promotes(self):
        run, rows = self.run_real(engine='blf')
        bad = GeneratedMarkerCandidate.objects.create(   # test fixture only
            run=run, engine='blf',
            placements=rows[0].placements,
            marker_length_mm=rows[0].marker_length_mm,
            verification={'ok': False, 'max_overlap_mm2': 999.0,
                          'within_width': False, 'piece_count': 3})
        with self.assertRaises(ValidationError) as cm:
            gen.promote_candidate(user=self.mgr, candidate=bad)
        self.assertIn('verification', str(cm.exception))

    def test_promoted_marker_flows_into_p1_machinery(self):
        """The point of it all: a promoted marker is a real marker — usage,
        outcome and the Yield Board treat it identically (frozen P1)."""
        _, rows = self.run_real(engine='blf')
        marker, _ = gen.promote_candidate(user=self.mgr, candidate=rows[0])
        adda = self.make_adda('P3-ADDA-2')
        usage = fb.record_usage(user=self.mgr, marker=marker, adda=adda,
                                plies=5, repeats=1)
        fb.record_outcome(user=self.mgr, usage=usage, fabric_in_mm=6000,
                          garments_cut=5)
        from patterns_ai.services import marker_query_service as q
        board = q.get_product_yield_board(self.product)
        row = next(r for r in board if r['marker'].pk == marker.pk)
        self.assertIsNotNone(row['avg_meters_per_100'])


class GenerationViewTests(_Base):
    def test_permissions_and_tampering(self):
        run, rows = self.run_real(engine='blf')
        urls = [reverse('patterns_ai:generate'),
                reverse('patterns_ai:generation-run', args=[run.pk]),
                reverse('patterns_ai:candidate-detail', args=[rows[0].pk]),
                reverse('patterns_ai:candidate-svg', args=[rows[0].pk])]
        self.client.force_login(self.worker)
        for u in urls:
            self.assertEqual(self.client.get(u).status_code, 403, u)
        self.client.logout()
        for u in urls:
            self.assertEqual(self.client.get(u).status_code, 302, u)
        self.client.force_login(self.mgr)
        self.assertEqual(self.client.get(
            reverse('patterns_ai:generate') + '?product=abc').status_code,
            404)

    def test_generate_via_ui_and_pages_render(self):
        self.client.force_login(self.mgr)
        resp = self.client.post(reverse('patterns_ai:generate'), {
            'product': self.product.pk, f'count_{self.size_m.pk}': '1',
            'usable_width_mm': '900', 'spacing_mm': '3', 'engine': 'blf'})
        self.assertEqual(resp.status_code, 302)
        run = MarkerGenerationRun.objects.latest('id')
        resp = self.client.get(resp['Location'])
        self.assertContains(resp, 'derived at read')
        self.assertContains(resp, 'Utilization')
        self.assertContains(resp, 'PASS')
        c = run.candidates.first()
        resp = self.client.get(reverse('patterns_ai:candidate-detail',
                                       args=[c.pk]))
        self.assertContains(resp, '<svg')            # visualization
        self.assertContains(resp, 'No manual baseline yet')  # honest labeling
        resp = self.client.get(reverse('patterns_ai:candidate-svg',
                                       args=[c.pk]))
        self.assertEqual(resp['Content-Type'], 'image/svg+xml')

    def test_promote_via_ui(self):
        self.client.force_login(self.mgr)
        _, rows = self.run_real(engine='blf')
        resp = self.client.post(
            reverse('patterns_ai:candidate-detail', args=[rows[0].pk]),
            {'label': 'from ui'}, follow=True)
        self.assertContains(resp, 'Promoted as MRK-')
        marker = Marker.objects.filter(
            origin=Marker.Origin.GENERATED).latest('id')
        self.assertContains(resp, marker.reference)

    def test_bad_ratio_message(self):
        self.client.force_login(self.mgr)
        resp = self.client.post(reverse('patterns_ai:generate'), {
            'product': self.product.pk, f'count_{self.size_m.pk}': 'x',
            'usable_width_mm': '900'}, follow=True)
        self.assertContains(resp, 'must be a number')


class MarkerSvgTests(TestCase):
    def test_marker_svg_renders_layout(self):
        placements = [{'key': 'front·m', 'instance': 0, 'mirrored': False,
                       'rotation_deg': 0,
                       'polygon_mm': [[0, 0], [600, 0], [600, 400], [0, 400]]}]
        svg = marker_svg(placements, 900, 600)
        self.assertIn('<svg', svg)
        self.assertIn('rect', svg)                    # fabric
        self.assertIn('front·m #1', svg)              # tooltip title
        self.assertIn('900.0', svg)
