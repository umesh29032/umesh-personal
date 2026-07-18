"""M2 — the PATTERN INTELLIGENCE STUDIO (UI_WORKFLOW_FREEZE §1/§2/§4 +
PRODUCT_DESIGN_FREEZE §7/§8): 5-station rail · Browse shelf (tabs,
checklist, conveyor) · Work mode (Evidence Stack, adapters on the ONE
contract, compare, confidence display-only, publish→conveyor) · phone
hand-off · adr-c.2 notches + Blueprint metadata slots."""
import shutil
import tempfile
import unittest

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import Role
from production.models import (Product, ProductPattern,
                               ProductPatternAssignment, ProductSize)
from patterns_ai.models import (EvidenceItem, GeometryExtraction,
                                PatternPieceVersion, PieceSizeGeometry)
from patterns_ai.services import acquisition_service as acq
from patterns_ai.services import pattern_geometry_service as geo
from patterns_ai.services import compute_bridge
from patterns_ai.tests.test_p3_generation import rect_um

User = get_user_model()
MEDIA = tempfile.mkdtemp(prefix='pai_m2_')
RUNTIME_OK = compute_bridge.runtime_available()

SVG_RECT = (b'<svg xmlns="http://www.w3.org/2000/svg">'
            b'<polygon points="0,0 120,0 120,80 0,80"/></svg>')
SVG_CURVE = (b'<svg xmlns="http://www.w3.org/2000/svg">'
             b'<path d="M0 0 C 10 10, 20 10, 30 0 Z"/></svg>')


@override_settings(MEDIA_ROOT=MEDIA)
class _M2Base(TestCase):
    @classmethod
    def setUpTestData(cls):
        mgr = Role.objects.get_or_create(code='manager',
                                         defaults={'name': 'M'})[0]
        wk = Role.objects.get_or_create(code='worker',
                                        defaults={'name': 'W'})[0]
        cls.mgr = User.objects.create_user('m2@test.local', password='x',
                                           role=mgr)
        cls.worker = User.objects.create_user('m2w@test.local', password='x',
                                              role=wk)
        cls.product = Product.objects.create(code='M2P', name='M2 Studio')
        cls.size_s = ProductSize.objects.create(product=cls.product,
                                                code='s', label='S',
                                                display_order=1)
        cls.size_m = ProductSize.objects.create(product=cls.product,
                                                code='m', label='M',
                                                display_order=2)
        cls.front = cls._piece('m2-front', 'Front')
        cls.back = cls._piece('m2-back', 'Back')

    @classmethod
    def _piece(cls, code, name, **kw):
        pattern = ProductPattern.objects.create(code=code, name=name)
        ProductPatternAssignment.objects.create(product=cls.product,
                                                pattern=pattern,
                                                pieces_count=1)
        return geo.create_piece(user=cls.mgr, product=cls.product,
                                pattern=pattern, fabric_group='body', **kw)

    @classmethod
    def _confirm(cls, piece, size, payload=None):
        draft = geo.get_or_create_draft(user=cls.mgr, piece=piece)
        PieceSizeGeometry.objects.create(          # test fixture only
            version=draft, size=size, geometry=payload or rect_um(300, 200),
            trust_grade='photo_calibrated', created_by=cls.mgr)
        return geo.confirm_version(user=cls.mgr, version=draft)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    def _work_url(self, piece=None, size=None):
        return reverse('patterns_ai:studio-work',
                       args=[(piece or self.front).pk,
                             (size or self.size_s).pk])

    def login(self):
        self.client.force_login(self.mgr)


class RailTests(_M2Base):
    """§2.1 — the dashboard is the 5-station rail with live verdicts."""

    def test_rail_shows_five_stations_with_verdicts(self):
        self.login()
        html = self.client.get(reverse('patterns_ai:dashboard')
                               + f'?product={self.product.pk}'
                               ).content.decode()
        for station in ('Pattern Blueprint', 'Pattern Intelligence Studio',
                        'Digital Cutting Table', 'Layout Library',
                        'Manufacturing'):
            self.assertIn(station, html)
        self.assertIn('0 active layout', html)
        self.assertIn('0 active layout contract', html)
        self.assertIn(reverse('patterns_ai:studio'), html)

    def test_rail_manager_station_gone(self):
        self.login()
        html = self.client.get(reverse('patterns_ai:dashboard')
                               + f'?product={self.product.pk}'
                               ).content.decode()
        self.assertNotIn('Open Pattern Manager', html)


class BrowseModeTests(_M2Base):
    """§2.3 — the shelf: size tabs, creation checklist, conveyor."""

    def test_browse_tabs_checklist_and_conveyor(self):
        self._confirm(self.front, self.size_s)
        self.login()
        html = self.client.get(reverse('patterns_ai:studio')
                               + f'?product={self.product.pk}&size=s'
                               ).content.decode()
        self.assertIn('size-tabs', html)
        self.assertIn('✓ Front', html)              # checklist chip done
        self.assertIn('✖ Back', html)               # mandatory missing
        self.assertIn('Digitize next missing piece', html)
        self.assertIn('Open in Studio', html)
        self.assertIn('mandatory design', html)      # not-ready banner

    def test_browse_ready_banner_when_all_mandatory_confirmed(self):
        self._confirm(self.front, self.size_s)
        self._confirm(self.back, self.size_s)
        self.login()
        html = self.client.get(reverse('patterns_ai:studio')
                               + f'?product={self.product.pk}&size=s'
                               ).content.decode()
        self.assertIn('READY FOR CUTTING', html)

    def test_worker_denied(self):
        self.client.force_login(self.worker)
        r = self.client.get(reverse('patterns_ai:studio')
                            + f'?product={self.product.pk}')
        self.assertEqual(r.status_code, 403)

    def test_conveyor_order_and_wrap(self):
        # size-first, then facade order (alphabetical within the bucket):
        # Back·S is the first missing mandatory design
        nxt = acq.next_missing_design(self.product)
        self.assertEqual((nxt['piece_name'], nxt['size_code']),
                         ('Back', 's'))
        after = acq.next_missing_design(
            self.product, after_key=f'{self.back.pk}:{self.size_s.pk}')
        self.assertEqual((after['piece_name'], after['size_code']),
                         ('Front', 's'))


class AdapterContractTests(_M2Base):
    """§7 — every input runs the SAME contract: evidence → proposal
    (honest refusals recorded) → one-shot review → draft."""

    def test_svg_evidence_becomes_proposal_with_display_confidence(self):
        ev, proposal = acq.add_evidence(
            user=self.mgr, piece=self.front, size=self.size_s, kind='svg',
            uploaded_file=SimpleUploadedFile('front.svg', SVG_RECT,
                                             'image/svg+xml'))
        self.assertEqual(ev.status, EvidenceItem.Status.PROPOSED)
        self.assertTrue(proposal.gate['passed'])
        self.assertEqual(proposal.confidence['overall'], 95)
        self.assertIsNone(proposal.capture_id)
        self.assertEqual(proposal.evidence_id, ev.pk)
        w = max(p[0] for p in proposal.geometry['outer'])
        self.assertEqual(w, 120000)                  # 120 mm in µm

    def test_svg_curves_refused_and_recorded(self):
        ev, proposal = acq.add_evidence(
            user=self.mgr, piece=self.front, size=self.size_s, kind='svg',
            uploaded_file=SimpleUploadedFile('c.svg', SVG_CURVE,
                                             'image/svg+xml'))
        self.assertEqual(ev.status, EvidenceItem.Status.REFUSED)
        self.assertIn('DXF', ev.refusal_reason)
        self.assertFalse(proposal.gate['passed'])
        self.assertIsNone(proposal.geometry)

    def test_manual_dims_constructs_rectangle_confidence_100(self):
        ev, proposal = acq.add_evidence(
            user=self.mgr, piece=self.front, size=self.size_s,
            kind='manual_dims',
            params={'width_mm': 250, 'height_mm': 100})
        self.assertTrue(proposal.gate['passed'])
        self.assertEqual(proposal.confidence['overall'], 100)
        self.assertEqual(proposal.geometry['outer'][2], [250000, 100000])

    def test_accept_stamps_trust_by_adapter_and_contract_c2(self):
        _, proposal = acq.add_evidence(
            user=self.mgr, piece=self.front, size=self.size_s, kind='svg',
            uploaded_file=SimpleUploadedFile('front.svg', SVG_RECT,
                                             'image/svg+xml'))
        row = geo.accept_extraction(user=self.mgr, extraction=proposal)
        self.assertEqual(row.trust_grade,
                         PieceSizeGeometry.TrustGrade.UNCALIBRATED)
        # M4.5 conscious update: the current contract is adr-c.3
        self.assertEqual(row.geometry_contract_version, 'adr-c.3')
        # one-shot: a second accept refuses
        with self.assertRaises(ValidationError):
            geo.accept_extraction(user=self.mgr, extraction=proposal)

    def test_photo_proposals_keep_photo_calibrated_trust(self):
        # fixture-grade extraction with a capture link (the real capture
        # path is runtime-tested elsewhere; trust dispatch is the point)
        from patterns_ai.models import CaptureAsset
        asset = CaptureAsset.objects.create(
            product=self.product, kind='pattern_capture', source='camera',
            file=SimpleUploadedFile('p.jpg', b'x' * 10, 'image/jpeg'),
            content_type='image/jpeg', size_bytes=10, sha256='a' * 64,
            uploaded_by=self.mgr)
        x = GeometryExtraction.objects.create(
            capture=asset, piece=self.front, size=self.size_s,
            backend='classical', pipeline_version='t',
            gate={'passed': True}, geometry=rect_um(100, 50),
            created_by=self.mgr)
        row = geo.accept_extraction(user=self.mgr, extraction=x)
        self.assertEqual(row.trust_grade,
                         PieceSizeGeometry.TrustGrade.PHOTO_CALIBRATED)

    def test_unavailable_kinds_refuse_honestly_without_rows(self):
        for kind in ('pdf', 'png', 'ai_api'):
            with self.assertRaises(ValidationError):
                acq.add_evidence(user=self.mgr, piece=self.front,
                                 size=self.size_s, kind=kind)
        self.assertEqual(EvidenceItem.objects.count(), 0)

    def test_evidence_is_immutable_knowledge(self):
        ev, _ = acq.add_evidence(
            user=self.mgr, piece=self.front, size=self.size_s,
            kind='manual_dims', params={'width_mm': 10, 'height_mm': 10})
        with self.assertRaises(ValueError):
            ev.delete()
        ev.refusal_reason = 'tamper'
        with self.assertRaises(ValueError):
            ev.save()


@unittest.skipUnless(RUNTIME_OK, 'compute runtime required (ADR-F)')
class DxfAdapterTests(_M2Base):
    def test_dxf_evidence_round_trips_through_the_runtime(self):
        # export a confirmed rect as DXF, re-import it as evidence
        self._confirm(self.front, self.size_s, rect_um(200, 150))
        row = PieceSizeGeometry.objects.get(
            version__piece=self.front, size=self.size_s)
        data = geo.export_dxf_bytes(row)
        ev, proposal = acq.add_evidence(
            user=self.mgr, piece=self.back, size=self.size_s, kind='dxf',
            uploaded_file=SimpleUploadedFile('b.dxf', data,
                                             'application/dxf'))
        self.assertEqual(ev.status, EvidenceItem.Status.PROPOSED)
        self.assertTrue(proposal.gate['passed'])
        self.assertEqual(proposal.confidence['overall'], 99)
        w = max(p[0] for p in proposal.geometry['outer'])
        self.assertEqual(w, 200000)


class WorkModeTests(_M2Base):
    """§2.4/§2.5 — the room: stack, compare, publish→conveyor, QR."""

    def _add_svg(self, piece=None):
        return acq.add_evidence(
            user=self.mgr, piece=piece or self.front, size=self.size_s,
            kind='svg',
            uploaded_file=SimpleUploadedFile('f.svg', SVG_RECT,
                                             'image/svg+xml'))

    def test_work_page_renders_stack_canvas_inspector_qr(self):
        self._add_svg()
        self.login()
        html = self.client.get(self._work_url()).content.decode()
        self.assertIn('Evidence stack (1)', html)
        self.assertIn('Use this proposal', html)
        self.assertIn('confidence 95', html)
        self.assertIn('display only', html)          # never a gate
        self.assertIn('Capture on the phone', html)
        self.assertIn(f'?size={self.size_s.pk}', html)   # QR link preselects
        self.assertIn('arrives with a later runtime upgrade', html)  # honest slots

    def test_add_evidence_via_post_and_compare_view(self):
        self.login()
        r = self.client.post(self._work_url(),
                             {'action': 'add_dims', 'width_mm': '100',
                              'height_mm': '60'})
        self.assertEqual(r.status_code, 302)
        self.client.post(self._work_url(), {
            'action': 'add_svg',
            'evidence_file': SimpleUploadedFile('f.svg', SVG_RECT,
                                                'image/svg+xml')})
        ids = list(GeometryExtraction.objects.filter(
            piece=self.front, size=self.size_s)
            .values_list('pk', flat=True))
        self.assertEqual(len(ids), 2)
        html = self.client.get(
            self._work_url() + f'?compare={ids[0]},{ids[1]}'
        ).content.decode()
        self.assertIn('proposals overlaid', html)
        self.assertIn('cmp-table', html)
        self.assertIn('never auto-selects', html)

    def test_use_proposal_then_publish_advances_conveyor(self):
        _, proposal = self._add_svg()
        self.login()
        r = self.client.post(self._work_url(),
                             {'action': 'use_proposal',
                              'proposal': proposal.pk})
        self.assertEqual(r.status_code, 302)
        r = self.client.post(self._work_url(),
                             {'action': 'publish',
                              f'grain_{self.size_s.pk}': '90'})
        # conveyor: next missing mandatory design = Back · S
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r.url, self._work_url(piece=self.back))
        v = self.front.versions.get()
        self.assertEqual(v.status, PatternPieceVersion.Status.CONFIRMED)

    def test_publish_tape_gate_refuses_beyond_tolerance(self):
        _, proposal = self._add_svg()
        self.login()
        self.client.post(self._work_url(), {'action': 'use_proposal',
                                            'proposal': proposal.pk})
        self.client.post(self._work_url(),
                         {'action': 'publish',
                          f'grain_{self.size_s.pk}': '90',
                          f'tape_w_{self.size_s.pk}': '400',   # SVG is 120
                          f'tape_h_{self.size_s.pk}': '80'})
        v = self.front.versions.get()
        self.assertEqual(v.status, PatternPieceVersion.Status.DRAFT)

    def test_evidence_count_poll_endpoint(self):
        self._add_svg()
        self.login()
        r = self.client.get(reverse('patterns_ai:studio-evidence-count',
                                    args=[self.front.pk, self.size_s.pk]))
        self.assertEqual(r.json(), {'count': 1})

    def test_tamper_wall_foreign_proposal_404(self):
        _, proposal = self._add_svg(piece=self.front)
        self.login()
        r = self.client.post(self._work_url(piece=self.back),
                             {'action': 'use_proposal',
                              'proposal': proposal.pk})
        self.assertEqual(r.status_code, 404)


class AdrC2Tests(_M2Base):
    """adr-c.2 — notches typed in the payload; Blueprint metadata slots."""

    def _draft_row(self):
        draft = geo.get_or_create_draft(user=self.mgr, piece=self.front)
        return PieceSizeGeometry.objects.create(
            version=draft, size=self.size_s, geometry=rect_um(100, 50),
            trust_grade='uncalibrated', created_by=self.mgr), draft

    def test_edit_draft_stores_reanchored_notches(self):
        row, draft = self._draft_row()
        geo.edit_draft_geometry(
            user=self.mgr, version=draft, size=self.size_s,
            outer_um=[[1000, 1000], [101000, 1000], [101000, 51000],
                      [1000, 51000]],
            notches=[{'x_um': 51000, 'y_um': 1000, 'label': 'cb'}])
        row.refresh_from_db()
        notches = row.geometry['features']['notches']
        self.assertEqual(notches, [{'x_um': 50000, 'y_um': 0,
                                    'label': 'cb'}])
        # M4.5 conscious update: the current contract is adr-c.3
        self.assertEqual(row.geometry_contract_version, 'adr-c.3')

    def test_bad_notch_refused(self):
        row, draft = self._draft_row()
        with self.assertRaises(ValidationError):
            geo.edit_draft_geometry(
                user=self.mgr, version=draft, size=self.size_s,
                outer_um=row.geometry['outer'],
                notches=[{'x_um': 'nope'}])

    def test_blueprint_metadata_slots_save_and_clear(self):
        geo.set_piece_rules(user=self.mgr, piece=self.front,
                            expected_notches='3', seam_allowance_mm='7.5')
        self.front.refresh_from_db()
        self.assertEqual(self.front.expected_notches, 3)
        self.assertEqual(str(self.front.seam_allowance_mm), '7.5')
        geo.set_piece_rules(user=self.mgr, piece=self.front,
                            expected_notches='', seam_allowance_mm='')
        self.front.refresh_from_db()
        self.assertIsNone(self.front.expected_notches)
        self.assertIsNone(self.front.seam_allowance_mm)

    def test_blueprint_page_carries_the_new_slots(self):
        self.client.force_login(
            User.objects.create_user('m2sa@test.local', password='x',
                                     role=Role.objects.get_or_create(
                                         code='super_admin',
                                         defaults={'name': 'SA'})[0]))
        html = self.client.get(reverse('patterns_ai:blueprint')
                               + f'?product={self.product.pk}'
                               ).content.decode()
        self.assertIn('expected_notches', html)
        self.assertIn('seam_allowance_mm', html)
