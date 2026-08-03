"""P2 view tests — permissions on every new URL, the capture->review->
confirm->export browser path (real compute), editor, DXF import, tampered
ids. Views stay parse->gate->delegate; these tests prove the wiring."""
import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import Role
from production.models import (Product, ProductPattern,
                               ProductPatternAssignment, ProductSize)
from patterns_ai.models import (CalibrationMat, GeometryExtraction,
                                PieceSizeGeometry)
from patterns_ai.services import calibration_service as cal
from patterns_ai.services import pattern_geometry_service as geo
from patterns_ai.tests.test_p2_geometry import (BOARD, RUNTIME_OK,
                                                TAPE, synth_golden)
import unittest

User = get_user_model()
MEDIA = tempfile.mkdtemp(prefix='pai-p2v-media-')


@unittest.skipUnless(RUNTIME_OK, 'compute runtime required (ADR-F)')
@override_settings(MEDIA_ROOT=MEDIA)
class _Base(TestCase):
    @classmethod
    def setUpTestData(cls):
        mgr = Role.objects.get_or_create(code='manager', defaults={'name': 'M'})[0]
        wk = Role.objects.get_or_create(code='worker', defaults={'name': 'W'})[0]
        cls.mgr = User.objects.create_user('p2v@test.local', password='x', role=mgr)
        cls.worker = User.objects.create_user('p2vw@test.local', password='x', role=wk)
        cls.product = Product.objects.create(code='P2V', name='P2 View Product')
        cls.size = ProductSize.objects.create(product=cls.product, code='m',
                                              label='M', display_order=1)
        cls.pattern = ProductPattern.objects.create(code='p2v-front', name='Front')
        ProductPatternAssignment.objects.create(product=cls.product,
                                                pattern=cls.pattern,
                                                pieces_count=1)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    def login_mgr(self):
        self.client.force_login(self.mgr)

    def make_piece(self):
        return geo.create_piece(user=self.mgr, product=self.product,
                                pattern=self.pattern, fabric_group='body')

    def make_active_mat(self, code='MAT-V'):
        mat = cal.register_mat(user=self.mgr, mat_code=code)
        mat, _ = cal.commission_mat(user=self.mgr, mat=mat, board_spec=BOARD,
                                    control_distances=TAPE)
        return mat


class PermissionSweepTests(_Base):
    """Every P2 URL: worker 403, anonymous 302->login (V1 rule 6)."""

    def urls(self):
        piece = self.make_piece()
        mat = self.make_active_mat('MAT-PERM')
        draft = geo.get_or_create_draft(user=self.mgr, piece=piece)
        row = PieceSizeGeometry.objects.create(   # test fixture only
            version=draft, size=self.size,
            geometry={'schema_version': 1, 'units': 'um',
                      'origin': 'bbox_min', 'axes': 'x_right_y_up',
                      'chord_tolerance_um': 500,
                      'outer': [[0, 0], [10000, 0], [10000, 10000], [0, 10000]],
                      'holes': [], 'features': {'grain': None},
                      'grade_rule': None},
            created_by=self.mgr)
        return [
            reverse('patterns_ai:mat-list'),
            reverse('patterns_ai:mat-new'),
            reverse('patterns_ai:mat-detail', args=[mat.pk]),
            reverse('patterns_ai:piece-list'),
            reverse('patterns_ai:piece-detail', args=[piece.pk]),
            reverse('patterns_ai:pattern-capture', args=[piece.pk]),
            reverse('patterns_ai:dxf-import', args=[piece.pk]),
            reverse('patterns_ai:version-detail', args=[draft.pk]),
            reverse('patterns_ai:geometry-edit', args=[row.pk]),
            reverse('patterns_ai:geometry-svg', args=[row.pk]),
            reverse('patterns_ai:geometry-dxf', args=[row.pk]),
            reverse('patterns_ai:geometry-print', args=[row.pk]),
        ]

    def test_worker_403_anonymous_redirect_everywhere(self):
        urls = self.urls()
        self.client.force_login(self.worker)
        for url in urls:
            self.assertEqual(self.client.get(url).status_code, 403, url)
        self.client.logout()
        for url in urls:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 302, url)
            self.assertIn('/app/', resp['Location'])

    def test_worker_403_on_action_posts(self):
        piece = self.make_piece()
        draft = geo.get_or_create_draft(user=self.mgr, piece=piece)
        self.client.force_login(self.worker)
        for name, args in [('mat-commission', [1]), ('mat-retire', [1]),
                           ('version-confirm', [draft.pk]),
                           ('version-reject', [draft.pk]),
                           ('version-next', [piece.pk])]:
            resp = self.client.post(reverse(f'patterns_ai:{name}', args=args))
            self.assertEqual(resp.status_code, 403, name)

    def test_tampered_ids_404_not_500(self):
        self.login_mgr()
        self.assertEqual(
            self.client.get(reverse('patterns_ai:piece-list')
                            + '?product=abc').status_code, 404)
        self.assertEqual(
            self.client.get(reverse('patterns_ai:yield-board')
                            + '?product=abc').status_code, 404)


class MatWorkflowTests(_Base):
    def test_register_commission_retire_via_ui(self):
        self.login_mgr()
        resp = self.client.post(reverse('patterns_ai:mat-new'),
                                {'mat_code': 'MAT-UI', 'name': 'Table mat'})
        mat = CalibrationMat.objects.get(mat_code='MAT-UI')
        self.assertRedirects(resp, reverse('patterns_ai:mat-detail',
                                           args=[mat.pk]))
        resp = self.client.post(
            reverse('patterns_ai:mat-commission', args=[mat.pk]),
            {'squares_x': 8, 'squares_y': 6, 'square_mm': 50,
             'marker_mm': 37, 'aruco_dict': 'DICT_5X5_1000',
             'distances_text': '0,6,300.0', 'notes': 'tape by owner'},
            follow=True)
        mat.refresh_from_db()
        self.assertEqual(mat.status, 'active')
        self.assertContains(resp, 'commissioned')
        # detail shows the PASS check row
        resp = self.client.get(reverse('patterns_ai:mat-detail', args=[mat.pk]))
        self.assertContains(resp, 'PASS')
        self.assertContains(resp, 'Commissioning')
        # retire without reason -> error message, still active
        resp = self.client.post(reverse('patterns_ai:mat-retire',
                                        args=[mat.pk]), {'reason': '  '},
                                follow=True)
        mat.refresh_from_db()
        self.assertEqual(mat.status, 'active')
        self.assertContains(resp, 'reason')

    def test_commission_bad_distances_line_rejected(self):
        self.login_mgr()
        mat = cal.register_mat(user=self.mgr, mat_code='MAT-BADLINE')
        resp = self.client.post(
            reverse('patterns_ai:mat-commission', args=[mat.pk]),
            {'squares_x': 8, 'squares_y': 6, 'square_mm': 50,
             'marker_mm': 37, 'aruco_dict': 'DICT_5X5_1000',
             'distances_text': 'garbage line'}, follow=True)
        mat.refresh_from_db()
        self.assertEqual(mat.status, 'uncommissioned')
        self.assertContains(resp, 'from_id,to_id,expected_mm')


class CaptureToConfirmFlowTests(_Base):
    """The whole Era-2 entry path through the BROWSER interface, real
    compute: capture -> annotator -> accept -> confirm -> exports."""

    def test_full_flow(self):
        self.login_mgr()
        piece = self.make_piece()
        mat = self.make_active_mat('MAT-FLOW')

        png = synth_golden('viewflow')
        resp = self.client.post(
            reverse('patterns_ai:pattern-capture', args=[piece.pk]),
            {'size': self.size.pk, 'mat': mat.pk, 'source': 'camera',
             'photo': SimpleUploadedFile('flow.png', png, 'image/png')})
        self.assertEqual(resp.status_code, 302)
        x = GeometryExtraction.objects.latest('id')
        self.assertIn(reverse('patterns_ai:extraction-review', args=[x.pk]),
                      resp['Location'])

        # annotator shows gate PASS + confidence components + overlay svg
        resp = self.client.get(resp['Location'])
        self.assertContains(resp, 'PASSED')
        self.assertContains(resp, 'nothing auto-accepts')  # honesty language
        self.assertContains(resp, '<svg')
        self.assertContains(resp, 'board_coverage')

        # human accepts -> draft version row
        resp = self.client.post(
            reverse('patterns_ai:extraction-review', args=[x.pk]),
            {'action': 'accept'})
        row = PieceSizeGeometry.objects.get()
        self.assertRedirects(resp, reverse('patterns_ai:version-detail',
                                           args=[row.version_id]))
        self.assertEqual(row.trust_grade, 'photo_calibrated')

        # version page shows the draft card + confirm form
        resp = self.client.get(reverse('patterns_ai:version-detail',
                                       args=[row.version_id]))
        self.assertContains(resp, 'Draft')
        self.assertContains(resp, f'grain_{self.size.pk}')

        # confirm with grain + honest tape (truth 150x100)
        resp = self.client.post(
            reverse('patterns_ai:version-confirm', args=[row.version_id]),
            {f'grain_{self.size.pk}': '90',
             f'tape_w_{self.size.pk}': '150.0',
             f'tape_h_{self.size.pk}': '100.0'}, follow=True)
        self.assertContains(resp, 'CONFIRMED')
        row.refresh_from_db()
        self.assertEqual(row.trust_grade, 'measured')
        version = row.version
        self.assertEqual(version.status, 'confirmed')

        # exports: SVG true-scale, DXF via runtime, Gate-1 print page
        resp = self.client.get(reverse('patterns_ai:geometry-svg',
                                       args=[row.pk]))
        self.assertEqual(resp['Content-Type'], 'image/svg+xml')
        self.assertIn(b'mm"', resp.getvalue()[:400])
        resp = self.client.get(reverse('patterns_ai:geometry-dxf',
                                       args=[row.pk]))
        self.assertEqual(resp['Content-Type'], 'application/dxf')
        self.assertIn(b'LWPOLYLINE', resp.getvalue())
        resp = self.client.get(reverse('patterns_ai:geometry-print',
                                       args=[row.pk]))
        self.assertContains(resp, '10 cm')          # printed scale bar
        self.assertContains(resp, 'Measured')

    def test_gate_refusal_shows_reasons_and_blocks_accept(self):
        self.login_mgr()
        piece = self.make_piece()
        mat = self.make_active_mat('MAT-REFUSE')
        # piece rammed against the mat edge -> border keep-out refusal
        png = synth_golden('edge', piece_polygon_mm=[[2, 2], [180, 2],
                                                     [180, 120], [2, 120]])
        resp = self.client.post(
            reverse('patterns_ai:pattern-capture', args=[piece.pk]),
            {'size': self.size.pk, 'mat': mat.pk, 'source': 'camera',
             'photo': SimpleUploadedFile('edge.png', png, 'image/png')},
            follow=True)
        self.assertContains(resp, 'REFUSED')
        x = GeometryExtraction.objects.latest('id')
        self.assertFalse(x.gate['passed'])
        resp = self.client.post(
            reverse('patterns_ai:extraction-review', args=[x.pk]),
            {'action': 'accept'}, follow=True)
        x.refresh_from_db()
        self.assertEqual(x.status, 'proposed')      # accept refused
        self.assertContains(resp, 'cannot be accepted')


class EditorAndImportTests(_Base):
    def draft_row(self):
        piece = self.make_piece()
        draft = geo.get_or_create_draft(user=self.mgr, piece=piece)
        return PieceSizeGeometry.objects.create(
            version=draft, size=self.size,
            geometry={'schema_version': 1, 'units': 'um',
                      'origin': 'bbox_min', 'axes': 'x_right_y_up',
                      'chord_tolerance_um': 500,
                      'outer': [[0, 0], [150000, 0], [150000, 100000],
                                [0, 100000]],
                      'holes': [],
                      'features': {'grain': None, 'notches': [],
                                   'drills': [], 'internal_lines': [],
                                   'fold_edge': None,
                                   'seam_allowance': 'as_cut'},
                      'grade_rule': None},
            created_by=self.mgr)

    def test_editor_get_and_save(self):
        self.login_mgr()
        row = self.draft_row()
        resp = self.client.get(reverse('patterns_ai:geometry-edit',
                                       args=[row.pk]))
        self.assertContains(resp, 'drafts only')
        resp = self.client.post(
            reverse('patterns_ai:geometry-edit', args=[row.pk]),
            {'outer_um': '[[0,0],[160000,0],[160000,100000],[0,100000]]',
             'grain_cdeg': '4500'})
        self.assertEqual(resp.status_code, 302)
        row.refresh_from_db()
        self.assertEqual(max(p[0] for p in row.geometry['outer']), 160000)
        self.assertEqual(row.geometry['features']['grain'],
                         {'angle_cdeg': 4500})

    def test_editor_bad_payload_message(self):
        self.login_mgr()
        row = self.draft_row()
        resp = self.client.post(
            reverse('patterns_ai:geometry-edit', args=[row.pk]),
            {'outer_um': 'not json'}, follow=True)
        self.assertContains(resp, 'bad vertex payload')

    def test_dxf_import_via_ui(self):
        self.login_mgr()
        row = self.draft_row()                      # gives geometry to export
        data = geo.export_dxf_bytes(row)
        # import into a NEW piece (own pattern + assignment)
        pattern2 = ProductPattern.objects.create(code='p2v-b2', name='Back2')
        ProductPatternAssignment.objects.create(product=self.product,
                                                pattern=pattern2,
                                                pieces_count=1)
        piece2 = geo.create_piece(user=self.mgr, product=self.product,
                                  pattern=pattern2, fabric_group='body')
        resp = self.client.post(
            reverse('patterns_ai:dxf-import', args=[piece2.pk]),
            {'size': self.size.pk,
             'dxf_file': SimpleUploadedFile('in.dxf', data,
                                            'application/dxf')},
            follow=True)
        self.assertContains(resp, 'uncalibrated')
        new_row = PieceSizeGeometry.objects.exclude(pk=row.pk).get()
        self.assertEqual(new_row.geometry['outer'],
                         row.geometry['outer'])
