"""ROADMAP_V2 Phase 4 tests — the interactive marker workspace: the
verify op (same verifier as generation), save_manual_layout rules,
workspace view + save/reload round-trip."""
import json
import shutil
import tempfile
import unittest

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import Role
from production.models import (Product, ProductPattern,
                               ProductPatternAssignment, ProductSize)
from patterns_ai.models import (GeneratedMarkerCandidate,
                                MarkerGenerationRun, PieceSizeGeometry)
from patterns_ai.services import compute_bridge
from patterns_ai.services import marker_generation_service as gen
from patterns_ai.services import pattern_geometry_service as geo
from patterns_ai.tests.test_p3_generation import rect_um

User = get_user_model()
MEDIA = tempfile.mkdtemp(prefix='pai-ph4-media-')
RUNTIME_OK = compute_bridge.runtime_available()


@unittest.skipUnless(RUNTIME_OK, 'compute runtime required (ADR-F)')
@override_settings(MEDIA_ROOT=MEDIA)
class _Base(TestCase):
    @classmethod
    def setUpTestData(cls):
        mgr = Role.objects.get_or_create(code='manager', defaults={'name': 'M'})[0]
        wk = Role.objects.get_or_create(code='worker', defaults={'name': 'W'})[0]
        cls.mgr = User.objects.create_user('ph4@test.local', password='x', role=mgr)
        cls.worker = User.objects.create_user('ph4w@test.local', password='x', role=wk)
        cls.product = Product.objects.create(code='PH4PROD', name='Ph4 Product')
        cls.size = ProductSize.objects.create(product=cls.product, code='m',
                                              label='M', display_order=1)
        pattern = ProductPattern.objects.create(code='ph4-front', name='Front')
        ProductPatternAssignment.objects.create(product=cls.product,
                                                pattern=pattern,
                                                pieces_count=1)
        piece = geo.create_piece(user=cls.mgr, product=cls.product,
                                 pattern=pattern, fabric_group='body')
        draft = geo.get_or_create_draft(user=cls.mgr, piece=piece)
        PieceSizeGeometry.objects.create(     # test fixture only
            version=draft, size=cls.size, geometry=rect_um(300, 200),
            trust_grade='photo_calibrated', created_by=cls.mgr)
        geo.confirm_version(user=cls.mgr, version=draft)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    def source_candidate(self):
        _, rows = gen.start_run(user=self.mgr, product=self.product,
                                usable_width_mm=900,
                                ratio={self.size: 2}, timebox_s=6,
                                engine='blf')
        return rows[0]

    @staticmethod
    def shift(placements, key_instance, dx=0, dy=0):
        out = json.loads(json.dumps(placements))
        for p in out:
            if (p['key'], p['instance']) == key_instance:
                p['polygon_mm'] = [[x + dx, y + dy]
                                   for x, y in p['polygon_mm']]
        return out


class VerifyOpTests(_Base):
    def test_verify_op_reuses_the_one_verifier(self):
        c = self.source_candidate()
        res = compute_bridge.run_tool('nest', {
            'op': 'verify', 'width_mm': 900.0, 'spacing_mm': 3.0,
            'placements': c.placements['placements']})
        self.assertTrue(res['ok'])
        self.assertTrue(res['verification']['ok'])
        self.assertAlmostEqual(float(res['length_mm']),
                               float(c.marker_length_mm), places=1)

    def test_verify_op_catches_overlap(self):
        c = self.source_candidate()
        pl = c.placements['placements']
        stacked = json.loads(json.dumps(pl))
        stacked[1]['polygon_mm'] = stacked[0]['polygon_mm']
        res = compute_bridge.run_tool('nest', {
            'op': 'verify', 'width_mm': 900.0, 'placements': stacked})
        self.assertFalse(res['verification']['ok'])
        self.assertGreater(res['verification']['max_overlap_mm2'], 100)


class SaveManualLayoutTests(_Base):
    def test_happy_save_creates_manual_run_and_candidate(self):
        c = self.source_candidate()
        moved = self.shift(c.placements['placements'],
                           (c.placements['placements'][0]['key'], 1),
                           dx=50)
        moved[0]['locked'] = True
        run, saved = gen.save_manual_layout(
            user=self.mgr, source_candidate=c, width_mm=900,
            height_mm=2000, placements=moved)
        self.assertEqual(saved.engine, 'manual')
        self.assertTrue(saved.verification['ok'])
        self.assertTrue(run.params['manual'])
        self.assertEqual(run.params['source_candidate_id'], c.pk)
        self.assertEqual(run.params['height_mm'], 2000)
        self.assertEqual(run.params['ratio'], c.run.params['ratio'])
        # locked flag persisted inside the immutable placements payload
        self.assertTrue(saved.placements['placements'][0]['locked'])
        # immutability inherited
        saved.engine = 'hacked'
        with self.assertRaises(ValueError):
            saved.save()
        # derived metrics still work on manual candidates (garments carried)
        m = gen.derive_candidate_metrics(saved)
        self.assertEqual(m['garments'], 2)
        self.assertIsNotNone(m['utilization_pct'])

    def test_overlap_refused_with_numbers(self):
        c = self.source_candidate()
        pl = json.loads(json.dumps(c.placements['placements']))
        pl[1]['polygon_mm'] = pl[0]['polygon_mm']
        with self.assertRaises(ValidationError) as cm:
            gen.save_manual_layout(user=self.mgr, source_candidate=c,
                                   width_mm=900, height_mm=2000,
                                   placements=pl)
        self.assertIn('overlap', str(cm.exception))
        self.assertEqual(GeneratedMarkerCandidate.objects.filter(
            engine='manual').count(), 0)

    def test_height_exceeded_refused(self):
        c = self.source_candidate()
        with self.assertRaises(ValidationError) as cm:
            gen.save_manual_layout(
                user=self.mgr, source_candidate=c, width_mm=900,
                height_mm=100,                    # marker is longer than 100mm
                placements=c.placements['placements'])
        self.assertIn('exceeds the fabric height', str(cm.exception))

    def test_width_escape_refused(self):
        c = self.source_candidate()
        pl = self.shift(c.placements['placements'],
                        (c.placements['placements'][0]['key'], 0), dy=880)
        with self.assertRaises(ValidationError) as cm:
            gen.save_manual_layout(user=self.mgr, source_candidate=c,
                                   width_mm=900, height_mm=2000,
                                   placements=pl)
        self.assertIn('verifier', str(cm.exception))

    def test_piece_set_must_match(self):
        c = self.source_candidate()
        pl = json.loads(json.dumps(c.placements['placements']))
        with self.assertRaises(ValidationError):       # remove a piece
            gen.save_manual_layout(user=self.mgr, source_candidate=c,
                                   width_mm=900, height_mm=2000,
                                   placements=pl[:-1])
        extra = pl + [dict(pl[0], instance=99)]        # add a piece
        with self.assertRaises(ValidationError):
            gen.save_manual_layout(user=self.mgr, source_candidate=c,
                                   width_mm=900, height_mm=2000,
                                   placements=extra)

    def test_bounds_and_permissions(self):
        c = self.source_candidate()
        pl = c.placements['placements']
        with self.assertRaises(ValidationError):
            gen.save_manual_layout(user=self.mgr, source_candidate=c,
                                   width_mm=100, height_mm=2000,
                                   placements=pl)
        with self.assertRaises(ValidationError):
            gen.save_manual_layout(user=self.mgr, source_candidate=c,
                                   width_mm=900, height_mm=0,
                                   placements=pl)
        with self.assertRaises(PermissionDenied):
            gen.save_manual_layout(user=self.worker, source_candidate=c,
                                   width_mm=900, height_mm=2000,
                                   placements=pl)


class WorkspaceViewTests(_Base):
    def test_permissions_and_tamper(self):
        c = self.source_candidate()
        url = reverse('patterns_ai:workspace', args=[c.pk])
        self.client.force_login(self.worker)
        self.assertEqual(self.client.get(url).status_code, 403)
        self.client.logout()
        self.assertEqual(self.client.get(url).status_code, 302)
        self.client.force_login(self.mgr)
        self.assertEqual(self.client.get(
            reverse('patterns_ai:workspace', args=[999999])).status_code, 404)

    def test_workspace_renders_canvas_and_controls(self):
        c = self.source_candidate()
        self.client.force_login(self.mgr)
        resp = self.client.get(reverse('patterns_ai:workspace', args=[c.pk]))
        # M3 conscious rework: the product-language pass replaced the
        # 'server verifier' hint with user words ('the server decides') —
        # internal vocabulary never reaches the flow (owner rule).
        for needle in ('id="ws"', 'Grid', 'Snap', 'Rotate 180',
                       'Lock/Unlock', 'Width mm', 'Height mm',
                       'utilization', 'wastage', 'Save layout',
                       'the server decides'):
            self.assertContains(resp, needle)
        # placements delivered to the client (escapejs-encoded payload —
        # assert on the escape-stable parts)
        self.assertContains(resp, 'polygon_mm')
        self.assertContains(resp, 'Front')

    def test_save_and_reload_round_trip(self):
        c = self.source_candidate()
        self.client.force_login(self.mgr)
        moved = self.shift(c.placements['placements'],
                           (c.placements['placements'][0]['key'], 1), dx=40)
        moved[0]['locked'] = True
        resp = self.client.post(
            reverse('patterns_ai:workspace', args=[c.pk]),
            {'placements': json.dumps(moved), 'width_mm': '900',
             'height_mm': '2500'})
        self.assertEqual(resp.status_code, 302)
        saved = GeneratedMarkerCandidate.objects.get(engine='manual')
        self.assertIn(reverse('patterns_ai:workspace', args=[saved.pk]),
                      resp['Location'])
        self.assertTrue(saved.placements['placements'][0]['locked'])
        # reload: the workspace opens the SAVED layout (lock riding along)
        resp = self.client.get(resp['Location'])
        self.assertContains(resp, 'locked')
        # M4 conscious rework: the wording pass renamed the page title to
        # 'Layout editor · #N' (product language) — assert the new form.
        self.assertContains(resp, 'Layout editor · #%d' % saved.pk)

    def test_bad_save_shows_error_and_persists_nothing(self):
        c = self.source_candidate()
        self.client.force_login(self.mgr)
        pl = json.loads(json.dumps(c.placements['placements']))
        pl[1]['polygon_mm'] = pl[0]['polygon_mm']
        resp = self.client.post(
            reverse('patterns_ai:workspace', args=[c.pk]),
            {'placements': json.dumps(pl), 'width_mm': '900',
             'height_mm': '2500'}, follow=True)
        self.assertContains(resp, 'refused by the verifier')
        self.assertEqual(GeneratedMarkerCandidate.objects.filter(
            engine='manual').count(), 0)
        resp = self.client.post(
            reverse('patterns_ai:workspace', args=[c.pk]),
            {'placements': 'not json', 'width_mm': '900',
             'height_mm': '2500'}, follow=True)
        self.assertContains(resp, 'bad layout payload')
