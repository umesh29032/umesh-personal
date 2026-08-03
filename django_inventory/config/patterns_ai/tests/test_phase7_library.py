"""Phase 7 — the Approved Layout Library (all 10 owner persistence
rules + the immutable layout_uid recommendation)."""
import json

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from accounts.models import Role
from production.models import (Product, ProductPattern,
                               ProductPatternAssignment, ProductSize)
from patterns_ai.models import (ApprovedLayout, GeneratedMarkerCandidate,
                                MarkerGenerationRun, PieceSizeGeometry)
from patterns_ai.services import layout_library_service as lib
from patterns_ai.services import marker_generation_service as gen
from patterns_ai.services import pattern_geometry_service as geo
from patterns_ai.tests.test_p3_generation import rect_um

User = get_user_model()


def _ring(x, y, w, h):
    return [[x, y], [x + w, y], [x + w, y + h], [x, y + h]]


class _P7Base(TestCase):
    @classmethod
    def setUpTestData(cls):
        mgr = Role.objects.get_or_create(code='manager',
                                         defaults={'name': 'M'})[0]
        wk = Role.objects.get_or_create(code='worker',
                                        defaults={'name': 'W'})[0]
        cls.mgr = User.objects.create_user('p7@test.local', password='x',
                                           role=mgr)
        cls.worker = User.objects.create_user('p7w@test.local', password='x',
                                              role=wk)
        cls.product = Product.objects.create(code='P7L', name='P7 Library')
        cls.size = ProductSize.objects.create(product=cls.product, code='s',
                                              label='S', display_order=1)
        cls.front = cls._piece('p7-front', 'Front', 'body')
        cls.rib = cls._piece('p7-rib', 'Rib', 'rib')
        for piece, dims in ((cls.front, (300, 200)), (cls.rib, (200, 40))):
            d = geo.get_or_create_draft(user=cls.mgr, piece=piece)
            PieceSizeGeometry.objects.create(       # fixture only
                version=d, size=cls.size, geometry=rect_um(*dims),
                trust_grade='photo_calibrated', created_by=cls.mgr)
            geo.confirm_version(user=cls.mgr, version=d)

    @classmethod
    def _piece(cls, code, name, group):
        pattern = ProductPattern.objects.create(code=code, name=name)
        ProductPatternAssignment.objects.create(product=cls.product,
                                                pattern=pattern,
                                                pieces_count=1)
        return geo.create_piece(user=cls.mgr, product=cls.product,
                                pattern=pattern, fabric_group=group)

    def _key(self, piece):
        return f'{piece.pk}:{self.size.pk}'

    def _save(self, placements=None, group='body'):
        # engine frame: [along-length, across-width]
        placements = placements or [
            {'key': self._key(self.front), 'instance': 1,
             'polygon_mm': _ring(10, 10, 200, 300),
             'locked': False, 'rotation_deg': 0, 'mirrored': False}]
        return gen.save_table_layout(
            user=self.mgr, product=self.product, width_mm=900,
            height_mm=2000, spacing_mm=2.0, fabric_group=group,
            placements=placements)


class SaveTableLayoutTests(_P7Base):
    def test_save_is_selfcontained_and_verbatim(self):
        run, cand = self._save()
        # rule 3: placements stored EXACTLY as sent
        self.assertEqual(cand.placements['placements'][0]['polygon_mm'],
                         _ring(10, 10, 200, 300))
        self.assertEqual(cand.engine, 'table')
        # rule 4/6: self-contained spine — version + geometry row resolved
        spec = run.params['pieces'][0]
        row = PieceSizeGeometry.objects.get(pk=spec['geometry_row_id'])
        self.assertEqual(row.version_id, spec['version_id'])
        self.assertEqual(spec['qty'], 1)
        self.assertEqual(run.params['fabric_group'], 'body')
        self.assertEqual(run.params['ratio'], {})   # honest: no cut plan yet
        self.assertTrue(run.params['table'])
        self.assertTrue(cand.verification['ok'])

    def test_save_refusals(self):
        # LAW 12 server-side: rib piece on a body layout
        with self.assertRaises(ValidationError) as ctx:
            self._save(placements=[
                {'key': self._key(self.rib), 'instance': 1,
                 'polygon_mm': _ring(10, 10, 40, 200)}], group='body')
        self.assertIn('LAW 12', str(ctx.exception))
        # unknown design key
        with self.assertRaises(ValidationError):
            self._save(placements=[{'key': '999999:1', 'instance': 1,
                                    'polygon_mm': _ring(0, 0, 10, 10)}])
        # verifier refusal: two overlapping copies
        with self.assertRaises(ValidationError) as ctx:
            self._save(placements=[
                {'key': self._key(self.front), 'instance': 1,
                 'polygon_mm': _ring(10, 10, 200, 300)},
                {'key': self._key(self.front), 'instance': 2,
                 'polygon_mm': _ring(50, 50, 200, 300)}])
        self.assertIn('verifier', str(ctx.exception))


class ApproveLifecycleTests(_P7Base):
    def test_uid_version_supersede_archive_chain(self):
        _, c1 = self._save()
        lay1 = lib.approve_table_layout(user=self.mgr, product=self.product,
                                        candidate=c1)
        self.assertEqual(lay1.layout_uid, 'LAY-P7L-000001')   # immutable ID
        self.assertEqual(lay1.version_no, 1)                  # human counter
        self.assertEqual(lay1.status, 'active')
        self.assertEqual(lay1.fabric_group, 'body')
        # V2 supersedes V1 — append-only chain (rule 5)
        _, c2 = self._save(placements=[
            {'key': self._key(self.front), 'instance': 1,
             'polygon_mm': _ring(5, 5, 200, 300)}])
        lay2 = lib.approve_table_layout(user=self.mgr, product=self.product,
                                        candidate=c2, supersedes=lay1)
        lay1.refresh_from_db()
        self.assertEqual(lay2.layout_uid, 'LAY-P7L-000002')
        self.assertEqual(lay2.supersedes_id, lay1.pk)
        self.assertEqual(lay1.status, 'superseded')           # never edited
        self.assertEqual(lay2.status, 'active')
        # archive (rule 4's other verb)
        lib.archive_layout(user=self.mgr, layout=lay2)
        lay2.refresh_from_db()
        self.assertEqual(lay2.status, 'archived')

    def test_immutability_and_gates(self):
        _, c1 = self._save()
        lay = lib.approve_table_layout(user=self.mgr, product=self.product,
                                       candidate=c1)
        # rule 1/4: rows are frozen — direct edits raise
        lay.name = 'hacked'
        with self.assertRaises(ValueError):
            lay.save()
        with self.assertRaises(ValueError):
            lay.delete()
        # once-only approval per candidate
        with self.assertRaises(ValidationError):
            lib.approve_table_layout(user=self.mgr, product=self.product,
                                     candidate=c1)
        # non-table candidates refused (the ★ flow keeps them)
        run = MarkerGenerationRun.objects.create(
            product=self.product, usable_width_mm=900,
            params={'schema_version': 1}, pipeline_version='x',
            errors={}, created_by=self.mgr)
        alien = GeneratedMarkerCandidate.objects.create(
            run=run, engine='blf',
            placements={'schema_version': 1, 'placements': []},
            marker_length_mm=100, verification={'ok': True}, seed=1)
        with self.assertRaises(ValidationError) as ctx:
            lib.approve_table_layout(user=self.mgr, product=self.product,
                                     candidate=alien)
        self.assertIn('Cutting-Table saves', str(ctx.exception))

    def test_staleness_is_derived_never_stored(self):
        _, c1 = self._save()
        lay = lib.approve_table_layout(user=self.mgr, product=self.product,
                                       candidate=c1)
        self.assertFalse(lib.layout_is_stale(lay))
        # a NEWER confirmed version supersedes the frozen one → STALE
        d2 = geo.start_next_version(user=self.mgr, piece=self.front)
        geo.confirm_version(user=self.mgr, version=d2)
        self.assertFalse(hasattr(lay, 'stale'))     # rule 6: no column
        self.assertTrue(lib.layout_is_stale(lay))   # derived, live truth


class EndpointTests(_P7Base):
    def _save_http(self):
        self.client.force_login(self.mgr)
        return self.client.post(
            reverse('patterns_ai:table-save', args=[self.product.pk]),
            json.dumps({'width_mm': 900, 'height_mm': 2000,
                        'spacing_mm': 2.0, 'fabric_group': 'body',
                        'placements': [
                            {'key': self._key(self.front), 'instance': 1,
                             'polygon_mm': _ring(10, 10, 200, 300),
                             'locked': False, 'rotation_deg': 0,
                             'mirrored': False}]}),
            content_type='application/json')

    def test_save_endpoint_then_human_approve_flow(self):
        r = self._save_http()
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(data['ok'])
        # rule 2/8: SAVE created a draft, NEVER an approval
        self.assertEqual(ApprovedLayout.objects.count(), 0)
        # the review step (GET) renders the facts
        review = self.client.get(data['approve_url']).content.decode()
        self.assertIn('freeze as manufacturing layout', review)
        self.assertIn('BODY', review)
        # the explicit human act (POST)
        r2 = self.client.post(data['approve_url'], {'name': 'Body run'})
        self.assertEqual(r2.status_code, 302)
        lay = ApprovedLayout.objects.get()
        self.assertEqual(lay.name, 'Body run')
        self.assertEqual(lay.approved_by, self.mgr)
        # library renders on the shell w/ uid + actions + exports links
        html = self.client.get(reverse('patterns_ai:cutting-table',
                                       args=[self.product.pk])
                               ).content.decode()
        self.assertIn('LAY-P7L-000001', html)
        self.assertIn(reverse('patterns_ai:candidate-pdf',
                              args=[lay.candidate_id]), html)
        self.assertIn('?view=', html)
        self.assertIn('?duplicate=', html)
        # view mode = read-only banner + initial payload
        v = self.client.get(reverse('patterns_ai:cutting-table',
                                    args=[self.product.pk])
                            + f'?view={lay.pk}').content.decode()
        self.assertIn('READ-ONLY', v)
        self.assertIn('id="ws-initial"', v)
        self.assertIn('Export PDF', v)              # rule 7 gate opens

    def test_gates(self):
        self.client.force_login(self.worker)
        r = self.client.post(
            reverse('patterns_ai:table-save', args=[self.product.pk]),
            '{}', content_type='application/json')
        self.assertEqual(r.status_code, 403)
        self.client.force_login(self.mgr)
        r = self.client.get(reverse('patterns_ai:table-save',
                                    args=[self.product.pk]))
        self.assertEqual(r.status_code, 405)        # POST-only
        r = self._save_http()
        cand = r.json()['candidate_id']
        # approving a candidate of ANOTHER product 404s
        other = Product.objects.create(code='P7X', name='Other')
        r = self.client.get(reverse('patterns_ai:table-approve',
                                    args=[other.pk, cand]))
        self.assertEqual(r.status_code, 404)
