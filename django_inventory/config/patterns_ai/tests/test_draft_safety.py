"""M8.1 — BARE-DRAFT SAFETY (owner-ordered workflow fix, 2026-07-10):
a published version must never lose confirmed sizes by accident.
Layer 1 prevention: EVERY draft-creating path copy-forwards the latest
confirmed version's rows (ADR-D2 §3 now applies beyond the Reopen
button). Layer 2 backstop: confirm refuses to drop an ACTIVE size the
current confirmed version covers (archived sizes exempt — deliberate
retirement stays possible)."""
import shutil
import tempfile
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings

from accounts.models import Role
from production.models import (Product, ProductPattern,
                               ProductPatternAssignment, ProductSize)
from patterns_ai.models import PatternPieceVersion, PieceSizeGeometry
from patterns_ai.services import acquisition_service as acq
from patterns_ai.services import compute_bridge
from patterns_ai.services import pattern_geometry_service as geo
from patterns_ai.tests.test_p3_generation import rect_um

User = get_user_model()
MEDIA = tempfile.mkdtemp(prefix='pai_m81_')


@override_settings(MEDIA_ROOT=MEDIA)
class _Base(TestCase):
    @classmethod
    def setUpTestData(cls):
        mgr = Role.objects.get_or_create(code='manager',
                                         defaults={'name': 'M'})[0]
        cls.mgr = User.objects.create_user('m81@test.local', password='x',
                                           role=mgr)
        cls.product = Product.objects.create(code='M81P', name='M81 Guard')
        cls.size_s = ProductSize.objects.create(product=cls.product,
                                                code='s', label='S',
                                                display_order=1)
        cls.size_m = ProductSize.objects.create(product=cls.product,
                                                code='m', label='M',
                                                display_order=2)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    def _piece(self, code='m81-body', name='Body'):
        pattern = ProductPattern.objects.create(code=code, name=name)
        ProductPatternAssignment.objects.create(product=self.product,
                                                pattern=pattern,
                                                pieces_count=1)
        return geo.create_piece(user=self.mgr, product=self.product,
                                pattern=pattern, fabric_group='body')

    def _publish_v1(self, piece):
        """Confirmed v1 covering BOTH sizes (fixture rows, grain baked)."""
        draft = geo.get_or_create_draft(user=self.mgr, piece=piece)
        for size, w in ((self.size_s, 300), (self.size_m, 350)):
            PieceSizeGeometry.objects.create(     # test fixture only
                version=draft, size=size, geometry=rect_um(w, 200),
                trust_grade='photo_calibrated', created_by=self.mgr)
        return geo.confirm_version(user=self.mgr, version=draft)

    def _accept_dims_proposal(self, piece, size, w=340, h=190):
        _, proposal = acq.add_evidence(
            user=self.mgr, piece=piece, size=size, kind='manual_dims',
            params={'width_mm': w, 'height_mm': h})
        return geo.accept_extraction(user=self.mgr, extraction=proposal)


class CopyForwardPreventionTests(_Base):
    def test_accept_on_published_piece_carries_all_sizes(self):
        piece = self._piece()
        self._publish_v1(piece)
        self._accept_dims_proposal(piece, self.size_m)
        draft = piece.versions.get(status=PatternPieceVersion.Status.DRAFT)
        rows = {r.size_id: r for r in
                draft.size_geometries.select_related('size')}
        # BOTH sizes present: S = carried copy, M = the accepted geometry
        self.assertEqual(set(rows), {self.size_s.pk, self.size_m.pk})
        self.assertIsNotNone(rows[self.size_s.pk].copied_from_id)
        self.assertIsNone(rows[self.size_m.pk].copied_from_id)
        self.assertIsNotNone(rows[self.size_m.pk].source_extraction_id)
        # exactly one row per size — replace, never duplicate
        self.assertEqual(draft.size_geometries.count(), 2)

    def test_carried_row_keeps_original_contract_and_trust(self):
        piece = self._piece('m81-b2', 'Body2')
        v1 = self._publish_v1(piece)
        s_row = v1.size_geometries.get(size=self.size_s)
        self._accept_dims_proposal(piece, self.size_m)
        draft = piece.versions.get(status=PatternPieceVersion.Status.DRAFT)
        carried = draft.size_geometries.get(size=self.size_s)
        self.assertEqual(carried.trust_grade, s_row.trust_grade)
        self.assertEqual(carried.geometry_contract_version,
                         s_row.geometry_contract_version)
        self.assertEqual(carried.geometry, s_row.geometry)

    def test_fresh_piece_still_starts_bare_v1(self):
        piece = self._piece('m81-b3', 'Body3')
        self._accept_dims_proposal(piece, self.size_s)
        draft = piece.versions.get()
        self.assertEqual(draft.version_no, 1)
        self.assertEqual(draft.size_geometries.count(), 1)

    def test_open_draft_reused_no_duplicate_copies(self):
        piece = self._piece('m81-b4', 'Body4')
        self._publish_v1(piece)
        d1 = geo.get_or_create_draft(user=self.mgr, piece=piece)
        d2 = geo.get_or_create_draft(user=self.mgr, piece=piece)
        self.assertEqual(d1.pk, d2.pk)
        self.assertEqual(d1.size_geometries.count(), 2)   # copied ONCE

    def test_import_dxf_path_carries_sizes_too(self):
        piece = self._piece('m81-b5', 'Body5')
        self._publish_v1(piece)
        dxf_ok = {'ok': True, 'pieces': [rect_um(340, 190)]}
        with mock.patch.object(compute_bridge, 'run_tool',
                               return_value=dxf_ok):
            geo.import_dxf(user=self.mgr, piece=piece, size=self.size_m,
                           dxf_path='/nonexistent/fixture.dxf')
        draft = piece.versions.get(status=PatternPieceVersion.Status.DRAFT)
        self.assertEqual(draft.size_geometries.count(), 2)

    def test_start_next_version_semantics_preserved(self):
        piece = self._piece('m81-b6', 'Body6')
        with self.assertRaisesMessage(ValidationError, 'no confirmed'):
            geo.start_next_version(user=self.mgr, piece=piece)
        self._publish_v1(piece)
        draft = geo.start_next_version(user=self.mgr, piece=piece)
        self.assertEqual(draft.size_geometries.count(), 2)
        with self.assertRaisesMessage(ValidationError, 'already exists'):
            geo.start_next_version(user=self.mgr, piece=piece)


class ConfirmBackstopTests(_Base):
    def _bare_draft_missing_s(self, piece):
        """The exotic path the backstop guards: a draft crafted WITHOUT
        the service (only M), on a piece whose v1 covers S+M."""
        draft = PatternPieceVersion.objects.create(
            piece=piece, version_no=2, created_by=self.mgr)
        PieceSizeGeometry.objects.create(
            version=draft, size=self.size_m, geometry=rect_um(350, 200),
            trust_grade='uncalibrated', created_by=self.mgr)
        return draft

    def test_confirm_refuses_dropping_active_size(self):
        piece = self._piece('m81-b7', 'Body7')
        self._publish_v1(piece)
        draft = self._bare_draft_missing_s(piece)
        with self.assertRaisesMessage(ValidationError,
                                      'would drop size(s) S'):
            geo.confirm_version(user=self.mgr, version=draft)
        draft.refresh_from_db()
        self.assertEqual(draft.status, PatternPieceVersion.Status.DRAFT)

    def test_confirm_allows_dropping_archived_size(self):
        piece = self._piece('m81-b8', 'Body8')
        self._publish_v1(piece)
        # deliberate retirement: archive S first — the ONE legal way out
        self.size_s.is_active = False
        self.size_s.save(update_fields=['is_active'])
        try:
            draft = self._bare_draft_missing_s(piece)
            confirmed = geo.confirm_version(user=self.mgr, version=draft)
            self.assertEqual(confirmed.status,
                             PatternPieceVersion.Status.CONFIRMED)
        finally:
            self.size_s.is_active = True
            self.size_s.save(update_fields=['is_active'])

    def test_published_piece_full_loop_keeps_both_sizes(self):
        """The M8 browser scenario end-to-end: publish v1 → accept on M →
        publish v2 → v2 covers BOTH sizes, v1 superseded."""
        piece = self._piece('m81-b9', 'Body9')
        self._publish_v1(piece)
        self._accept_dims_proposal(piece, self.size_m)
        draft = piece.versions.get(status=PatternPieceVersion.Status.DRAFT)
        # manual-dims payload carries no grain — state it at confirm,
        # exactly like the publish dialog does
        v2 = geo.confirm_version(user=self.mgr, version=draft,
                                 grain_by_size={self.size_m.pk: 9000})
        self.assertEqual(v2.size_geometries.count(), 2)
        v1 = piece.versions.get(version_no=1)
        self.assertEqual(v1.status, PatternPieceVersion.Status.SUPERSEDED)
