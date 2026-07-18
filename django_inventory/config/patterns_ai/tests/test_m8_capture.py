"""M8 — REAL PATTERN CAPTURE (owner-frozen workflow 2026-07-10): plain
photo + human tape numbers = the Evidence-SET adapter. Photos join the
set silently (no per-item adapter); Build Geometry From Evidence makes
ONE proposal from the whole stack — width/height tape = per-axis scale
truth, every other stated number = recorded ADVISORY cross-check; trust
stays UNCALIBRATED until the publish tape gate (the one path up)."""
import io
import shutil
import tempfile
import unittest
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import Role
from production.models import (Product, ProductPattern,
                               ProductPatternAssignment, ProductSize)
from patterns_ai.models import EvidenceItem, GeometryExtraction
from patterns_ai.services import acquisition_service as acq
from patterns_ai.services import compute_bridge
from patterns_ai.services import pattern_geometry_service as geo
from patterns_ai.tests.test_p3_generation import rect_um

User = get_user_model()
MEDIA = tempfile.mkdtemp(prefix='pai_m8_')
RUNTIME_OK = compute_bridge.runtime_available()


def _jpeg(name='plain.jpg', w=80, h=60, rect=None):
    """Tiny real JPEG (Pillow) — dark rectangle on light table."""
    from PIL import Image, ImageDraw
    img = Image.new('RGB', (w, h), (231, 226, 214))
    if rect:
        ImageDraw.Draw(img).rectangle(rect, fill=(96, 74, 52))
    buf = io.BytesIO()
    img.save(buf, format='JPEG')
    return SimpleUploadedFile(name, buf.getvalue(), 'image/jpeg')


def _tool_ok(width_mm=510.0, height_mm=330.0, stability=0.85):
    """Realistic extract_plain result (contract mirror of the tool)."""
    payload = rect_um(width_mm, height_mm)
    payload['chord_tolerance_um'] = 2000
    payload['features']['grain'] = None
    return {'ok': True,
            'gate': {'passed': True, 'reasons': [],
                     'stability': stability},
            'geometry': payload,
            'confidence': {'overall': 87,
                           'segmentation_stability': stability},
            'provenance': {'pipeline_version': 'plain-1', 'params': {}},
            'segmentation': {'stability': stability, 'vertices': 4},
            'metrics': {}, 'checks': {'area_frac': 0.4}}


@override_settings(MEDIA_ROOT=MEDIA)
class _M8Base(TestCase):
    @classmethod
    def setUpTestData(cls):
        mgr = Role.objects.get_or_create(code='manager',
                                         defaults={'name': 'M'})[0]
        cls.mgr = User.objects.create_user('m8@test.local', password='x',
                                           role=mgr)
        cls.product = Product.objects.create(code='M8P', name='M8 Capture')
        cls.size = ProductSize.objects.create(product=cls.product,
                                              code='m', label='M',
                                              display_order=1)
        pattern = ProductPattern.objects.create(code='m8-body', name='Body')
        ProductPatternAssignment.objects.create(product=cls.product,
                                                pattern=pattern,
                                                pieces_count=1)
        cls.piece = geo.create_piece(user=cls.mgr, product=cls.product,
                                     pattern=pattern, fabric_group='body')

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    def _add_plain(self, view='top_full', measurements=None, **kw):
        return acq.add_evidence(
            user=self.mgr, piece=self.piece, size=self.size,
            kind='photo_plain', uploaded_file=kw.pop('file', _jpeg()),
            params={'view': view,
                    'measurements': measurements or {}}, **kw)


class PlainEvidenceIntakeTests(_M8Base):
    def test_photo_plain_in_available_ladder(self):
        self.assertIn('photo_plain', acq.AVAILABLE_KINDS)
        self.assertIn('png', acq.UNAVAILABLE_KINDS)   # png stays honest-off

    def test_plain_photo_joins_set_without_adapter(self):
        ev, proposal = self._add_plain(
            view='top_full', measurements={'width': '510', 'Height mm': 330})
        self.assertIsNone(proposal)                   # SET adapter runs later
        self.assertEqual(ev.status, EvidenceItem.Status.RECEIVED)
        self.assertEqual(ev.kind, 'photo_plain')
        # params normalized: names lowercased, _mm suffixed, floats
        self.assertEqual(ev.params['view'], 'top_full')
        self.assertEqual(ev.params['measurements'],
                         {'width_mm': 510.0, 'height_mm': 330.0})
        self.assertEqual(ev.proposals.count(), 0)

    def test_plain_photo_requires_file(self):
        with self.assertRaisesMessage(ValidationError, 'choose a file'):
            acq.add_evidence(user=self.mgr, piece=self.piece,
                             size=self.size, kind='photo_plain',
                             params={'view': 'top_full'})

    def test_params_validation_refuses_bad_input(self):
        with self.assertRaisesMessage(ValidationError, 'unknown view'):
            self._add_plain(view='selfie')
        with self.assertRaisesMessage(ValidationError, 'not a number'):
            self._add_plain(measurements={'width': 'five hundred'})
        with self.assertRaisesMessage(ValidationError, '0–10000'):
            self._add_plain(measurements={'width': -3})


class SetAdapterTests(_M8Base):
    def test_build_requires_plain_photo_primary(self):
        dims, _ = acq.add_evidence(
            user=self.mgr, piece=self.piece, size=self.size,
            kind='manual_dims', params={'width_mm': 100, 'height_mm': 50})
        with self.assertRaisesMessage(ValidationError, 'plain-background'):
            acq.build_from_evidence(user=self.mgr, piece=self.piece,
                                    size=self.size, primary=dims)

    def test_build_refuses_cross_row_primary(self):
        other = ProductSize.objects.create(product=self.product, code='l',
                                           label='L', display_order=2)
        ev, _ = self._add_plain()
        with self.assertRaisesMessage(ValidationError, 'different'):
            acq.build_from_evidence(user=self.mgr, piece=self.piece,
                                    size=other, primary=ev)

    def test_build_without_width_height_is_recorded_refusal(self):
        ev, _ = self._add_plain(measurements={'waist': 400})
        proposal = acq.build_from_evidence(user=self.mgr, piece=self.piece,
                                           size=self.size, primary=ev)
        self.assertFalse(proposal.gate['passed'])
        self.assertIn('width_mm', proposal.gate['reasons'][0])
        self.assertIsNone(proposal.geometry)
        ev.refresh_from_db()
        self.assertEqual(ev.status, EvidenceItem.Status.REFUSED)
        self.assertIn('width_mm', ev.refusal_reason)

    def test_build_passes_scale_and_stamps_primary(self):
        ev, _ = self._add_plain(
            measurements={'width': 510, 'height': 330})
        with mock.patch.object(compute_bridge, 'run_tool',
                               return_value=_tool_ok()) as rt:
            proposal = acq.build_from_evidence(
                user=self.mgr, piece=self.piece, size=self.size, primary=ev)
        job = rt.call_args[0][1]
        self.assertEqual(rt.call_args[0][0], 'extract_plain')
        self.assertEqual((job['width_mm'], job['height_mm']), (510.0, 330.0))
        self.assertTrue(proposal.gate['passed'])
        self.assertEqual(proposal.backend, 'photo_plain')
        self.assertEqual(proposal.confidence['overall'], 87)
        ev.refresh_from_db()
        self.assertEqual(ev.status, EvidenceItem.Status.PROPOSED)

    def test_measurements_merge_across_set_primary_wins(self):
        # older photo states height+diagonal+waist; PRIMARY states width
        # and a CLASHING height — primary's number must win the clash
        self._add_plain(view='folded', measurements={
            'height': 320, 'diagonal': 600, 'waist': 400})
        primary, _ = self._add_plain(
            measurements={'width': 510, 'height': 330})
        with mock.patch.object(compute_bridge, 'run_tool',
                               return_value=_tool_ok()):
            proposal = acq.build_from_evidence(
                user=self.mgr, piece=self.piece, size=self.size,
                primary=primary)
        merged = proposal.result['set']['measurements']
        self.assertEqual(merged['height_mm'], 330.0)    # primary won
        self.assertEqual(merged['diagonal_mm'], 600.0)  # set filled in
        self.assertEqual(merged['waist_mm'], 400.0)
        self.assertEqual(len(proposal.result['set']['evidence_ids']), 2)
        self.assertEqual(proposal.result['set']['primary_evidence_id'],
                         primary.pk)

    def test_cross_checks_are_advisory_records(self):
        ev, _ = self._add_plain(measurements={
            'width': 510, 'height': 330, 'diagonal': 600, 'waist': 400})
        with mock.patch.object(compute_bridge, 'run_tool',
                               return_value=_tool_ok()):
            proposal = acq.build_from_evidence(
                user=self.mgr, piece=self.piece, size=self.size, primary=ev)
        cross = proposal.result['set']['cross_checks']
        # bbox diagonal = hypot(510, 330) = 607.5 → delta +7.5 ADVISORY,
        # gate still PASSED (the human judges at review)
        self.assertTrue(proposal.gate['passed'])
        self.assertAlmostEqual(cross['diagonal_mm']['derived'], 607.5,
                               places=1)
        self.assertAlmostEqual(cross['diagonal_mm']['delta_mm'], 7.5,
                               places=1)
        self.assertIsNone(cross['waist_mm']['derived'])  # stated-only
        self.assertEqual(cross['width_mm']['delta_mm'], 0.0)

    def test_tool_gate_refusal_recorded_not_raised(self):
        ev, _ = self._add_plain(measurements={'width': 510, 'height': 330})
        refused = {'ok': True,
                   'gate': {'passed': False, 'stability': 0.2,
                            'reasons': ['piece touches the photo edge on '
                                        '1 side(s) — retake']},
                   'geometry': None, 'confidence': {},
                   'provenance': {'pipeline_version': 'plain-1',
                                  'params': {}},
                   'segmentation': {}, 'metrics': {}, 'checks': {}}
        with mock.patch.object(compute_bridge, 'run_tool',
                               return_value=refused):
            proposal = acq.build_from_evidence(
                user=self.mgr, piece=self.piece, size=self.size, primary=ev)
        self.assertFalse(proposal.gate['passed'])
        self.assertIsNone(proposal.geometry)
        ev.refresh_from_db()
        self.assertEqual(ev.status, EvidenceItem.Status.REFUSED)
        self.assertIn('touches the photo edge', ev.refusal_reason)

    def test_trust_law_plain_photo_stays_uncalibrated(self):
        ev, _ = self._add_plain(measurements={'width': 510, 'height': 330})
        with mock.patch.object(compute_bridge, 'run_tool',
                               return_value=_tool_ok()):
            proposal = acq.build_from_evidence(
                user=self.mgr, piece=self.piece, size=self.size, primary=ev)
        row = geo.accept_extraction(user=self.mgr, extraction=proposal)
        # no mat ⇒ NEVER photo_calibrated; the publish tape gate is the
        # one path up to measured (M2 trust-by-adapter law)
        self.assertEqual(row.trust_grade, 'uncalibrated')


class StudioUiTests(_M8Base):
    def _url(self):
        return reverse('patterns_ai:studio-work',
                       args=[self.piece.pk, self.size.pk])

    def test_post_add_plain_photo_and_stack_chips(self):
        self.client.force_login(self.mgr)
        resp = self.client.post(self._url(), {
            'action': 'add_plain_photo', 'view': 'top_full',
            'm_name': ['width', 'height', ''],
            'm_mm': ['510', '330', ''],
            'evidence_file': _jpeg()})
        self.assertEqual(resp.status_code, 302)
        ev = EvidenceItem.objects.get(piece=self.piece, kind='photo_plain')
        self.assertEqual(ev.params['measurements'],
                         {'width_mm': 510.0, 'height_mm': 330.0})
        page = self.client.get(self._url()).content.decode()
        self.assertIn('top_full', page)                # view chip
        self.assertIn('Build geometry from evidence', page)
        self.assertIn('width 510', page)               # measurement chip

    def test_post_build_from_evidence_shows_cross_checks(self):
        ev, _ = self._add_plain(measurements={
            'width': 510, 'height': 330, 'diagonal': 600})
        self.client.force_login(self.mgr)
        with mock.patch.object(compute_bridge, 'run_tool',
                               return_value=_tool_ok()):
            resp = self.client.post(self._url(), {
                'action': 'build_from_evidence', 'primary': ev.pk})
        self.assertEqual(resp.status_code, 302)
        proposal = GeometryExtraction.objects.get(evidence=ev)
        self.assertTrue(proposal.gate['passed'])
        page = self.client.get(self._url()).content.decode()
        self.assertIn('Tape cross-checks', page)
        self.assertIn('607.5', page)                   # derived diagonal


@unittest.skipUnless(RUNTIME_OK, 'compute runtime required (ADR-F)')
class RealRuntimeTests(_M8Base):
    def test_synthetic_dark_rect_lands_on_stated_dims(self):
        # 400×240 px dark rect in an 800×600 light frame, stated
        # 510×330 mm → per-axis tape scale puts the bbox EXACTLY there
        ev, _ = self._add_plain(
            file=_jpeg('rect.jpg', w=800, h=600, rect=(200, 180, 599, 419)),
            measurements={'width': 510, 'height': 330})
        proposal = acq.build_from_evidence(user=self.mgr, piece=self.piece,
                                           size=self.size, primary=ev)
        self.assertTrue(proposal.gate['passed'], proposal.gate)
        xs = [p[0] for p in proposal.geometry['outer']]
        ys = [p[1] for p in proposal.geometry['outer']]
        self.assertEqual(max(xs) - min(xs), 510000)    # µm, exact
        self.assertEqual(max(ys) - min(ys), 330000)
