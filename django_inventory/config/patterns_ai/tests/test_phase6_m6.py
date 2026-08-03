"""Phase-6 M6 tests — Pattern Design Hub (Rules J/K/L/M/N §2d):
derived-only readiness, validation before generation, reference-image UI,
optional/required UI, collect-once."""
import struct
import zlib

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import Role
from production.models import (Product, ProductPattern,
                               ProductPatternAssignment, ProductSize)
from patterns_ai.models import (CaptureAsset, PatternPiece,
                                PieceSizeGeometry, ProductFabricProfile)
from patterns_ai.services import pattern_geometry_service as geo
from patterns_ai.tests.test_p3_generation import rect_um
from patterns_ai.views import _hub_readiness

import shutil
import tempfile

User = get_user_model()
MEDIA = tempfile.mkdtemp(prefix='pai-m6-media-')


def png_bytes(w=32, h=32, rgb=(200, 60, 60)):
    """Minimal REAL PNG (the capture door sniffs magic bytes)."""
    def chunk(tag, data):
        c = tag + data
        return (struct.pack('>I', len(data)) + c
                + struct.pack('>I', zlib.crc32(c) & 0xffffffff))
    raw = b''.join(b'\x00' + bytes(rgb) * w for _ in range(h))
    return (b'\x89PNG\r\n\x1a\n'
            + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
            # level 0 = stored, keeps the file above the door's 1 KB minimum
            + chunk(b'IDAT', zlib.compress(raw, 0))
            + chunk(b'IEND', b''))


@override_settings(MEDIA_ROOT=MEDIA)
class _M6Base(TestCase):
    @classmethod
    def setUpTestData(cls):
        mgr = Role.objects.get_or_create(code='manager', defaults={'name': 'M'})[0]
        wk = Role.objects.get_or_create(code='worker', defaults={'name': 'W'})[0]
        sa = Role.objects.get_or_create(code='super_admin',
                                        defaults={'name': 'SA'})[0]
        cls.mgr = User.objects.create_user('m6@test.local', password='x', role=mgr)
        cls.worker = User.objects.create_user('m6w@test.local', password='x', role=wk)
        # Phase 2: Blueprint posts need the strict perm (super-admin bypass)
        cls.admin = User.objects.create_user('m6sa@test.local', password='x',
                                             role=sa)
        cls.product = Product.objects.create(code='M6P', name='M6 Product')
        cls.size_m = ProductSize.objects.create(product=cls.product, code='m',
                                                label='M', display_order=1)
        cls.size_xl = ProductSize.objects.create(product=cls.product,
                                                 code='xl', label='XL',
                                                 display_order=2)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    @classmethod
    def _piece(cls, code, name, **kwargs):
        pattern = ProductPattern.objects.create(code=code, name=name)
        ProductPatternAssignment.objects.create(product=cls.product,
                                                pattern=pattern,
                                                pieces_count=1)
        return geo.create_piece(user=cls.mgr, product=cls.product,
                                pattern=pattern, fabric_group='body',
                                **kwargs)

    @classmethod
    def _geometry(cls, piece, sizes, confirm=True):
        draft = geo.get_or_create_draft(user=cls.mgr, piece=piece)
        for s in sizes:
            PieceSizeGeometry.objects.create(       # test fixture only
                version=draft, size=s, geometry=rect_um(200, 300),
                trust_grade='photo_calibrated', created_by=cls.mgr)
        if confirm:
            geo.confirm_version(user=cls.mgr, version=draft)
        return draft

    def _hub_url(self):
        return (reverse('patterns_ai:piece-list')
                + f'?product={self.product.pk}')

    def _post(self, data, files=None):
        self.client.force_login(self.mgr)
        payload = {'product': self.product.pk, **data}
        if files:
            payload.update(files)
        return self.client.post(reverse('patterns_ai:piece-list'), payload)

    def _bp_post(self, data):
        # Phase 2: rule/structure actions live on the Blueprint module
        self.client.force_login(self.admin)
        payload = {'product': self.product.pk, **data}
        return self.client.post(reverse('patterns_ai:blueprint'), payload)


class ReadinessDerivationTests(_M6Base):
    """Rule J — derived only, never stored; Rule L — exact naming."""

    def test_empty_product_not_ready(self):
        bare = Product.objects.create(code='M6E', name='Empty')
        r = _hub_readiness(bare)
        self.assertFalse(r['ready'])
        labels = {c[0]: c[1] for c in r['checklist']}
        self.assertFalse(labels['Product Sizes'])
        self.assertFalse(labels['Pattern Types'])

    def test_partial_geometry_blocks_with_exact_names(self):
        front = self._piece('m6-front', 'Front Panel')
        self._geometry(front, [self.size_m])         # XL missing
        r = _hub_readiness(self.product)
        self.assertFalse(r['ready'])
        self.assertIn('Front Panel — missing XL geometry', r['blockers'])

    def test_draft_is_warning_not_confirmed(self):
        back = self._piece('m6-back', 'Back Panel')
        self._geometry(back, [self.size_m, self.size_xl], confirm=False)
        r = _hub_readiness(self.product)
        self.assertIn('Back Panel — M, XL drawn but not confirmed',
                      r['warnings'])
        # drafts never count as done cells
        states = dict((s.pk, st) for s, st in r['rows'][0]['cells'])
        self.assertEqual(states[self.size_m.pk], 'draft')

    def test_optional_missing_is_warning_not_blocker(self):
        pocket = self._piece('m6-pocket', 'Pocket')
        geo.set_piece_optional(user=self.mgr, piece=pocket,
                               is_optional=True)
        r = _hub_readiness(self.product)
        self.assertFalse(any('Pocket' in b for b in r['blockers']))
        self.assertTrue(any(w.startswith('Pocket — missing')
                            for w in r['warnings']))

    def test_on_fold_blocker_law_upgraded(self):
        # M4.5 conscious update: the blanket on-fold blocker RETIRED —
        # an on-fold piece with confirmed geometry blocks ONLY until its
        # fold edge is marked (the blocker names the fix); a geometry-
        # less on-fold piece raises no fold blocker (missing-geometry
        # rules already handle it).
        yoke = self._piece('m6-yoke', 'Yoke', on_fold=True)
        geo.set_piece_optional(user=self.mgr, piece=yoke, is_optional=True)
        r = _hub_readiness(self.product)
        self.assertFalse(any('on-fold' in b for b in r['blockers']))
        # confirm geometry WITHOUT a fold edge → the named-fix blocker
        self._geometry(yoke, [self.size_m])
        r = _hub_readiness(self.product)
        self.assertTrue(any('mark the fold edge in the Studio' in b
                            for b in r['blockers']))

    def test_full_product_is_ready_and_100(self):
        front = self._piece('m6-front2', 'Front')
        self._geometry(front, [self.size_m, self.size_xl])
        asset = CaptureAsset.objects.create(        # fixture only
            product=self.product, kind=CaptureAsset.Kind.REFERENCE_IMAGE,
            source='gallery', original_filename='r.png',
            content_type='image/png', size_bytes=2048, sha256='e' * 64,
            metadata={'schema_version': 1}, uploaded_by=self.mgr,
            file='patterns_ai/x/originals/e.png')
        geo.set_reference_image(user=self.mgr, piece=front, asset=asset)
        from patterns_ai.services import fabric_profile_service as fps
        fps.set_fabric_profile(user=self.mgr, product=self.product,
                               default_width_mm=990)
        r = _hub_readiness(self.product)
        self.assertTrue(r['ready'])
        self.assertEqual(r['pct'], 100)
        self.assertEqual(r['rows'][0]['next_step'], 'Ready ✓')

    def test_rule_k_next_step_ladder(self):
        piece = self._piece('m6-lad', 'Ladder')
        self.assertEqual(_hub_readiness(self.product)['rows'][0]
                         ['next_step'], 'Capture or import geometry')
        self._geometry(piece, [self.size_m])          # XL still missing
        self.assertEqual(_hub_readiness(self.product)['rows'][0]
                         ['next_step'], 'Add XL geometry')
        self._geometry(piece, [self.size_xl], confirm=False)  # XL drawn
        self.assertEqual(_hub_readiness(self.product)['rows'][0]
                         ['next_step'], 'Confirm the drawn sizes')


class HubPageTests(_M6Base):
    def test_dashboard_and_matrix_render(self):
        front = self._piece('m6-r1', 'Front Panel')
        self._geometry(front, [self.size_m])
        self.client.force_login(self.mgr)
        html = self.client.get(self._hub_url()).content.decode()
        # W2 conscious rework: the Hub evolved into the Workspace —
        # same truths, new frame (summary expander + matrix overlay).
        self.assertIn('Pattern Manager', html)   # W2R vocabulary
        self.assertIn('Front Panel — missing XL geometry', html)
        self.assertIn('Readiness matrix', html)
        self.assertIn('rm-missing', html)
        self.assertIn('Blocks generation', html)

    def test_rule_c_no_selector_with_product_chooser_without(self):
        self.client.force_login(self.mgr)
        with_product = self.client.get(self._hub_url()).content.decode()
        self.assertNotIn('name="product" onchange', with_product)
        bare = self.client.get(reverse('patterns_ai:piece-list')
                               ).content.decode()
        self.assertIn('Pick a product', bare)

    def test_generate_page_carries_matrix(self):
        front = self._piece('m6-r2', 'Front Panel')
        self._geometry(front, [self.size_m])
        self.client.force_login(self.mgr)
        html = self.client.get(reverse('patterns_ai:generate')
                               + f'?product={self.product.pk}'
                               ).content.decode()
        self.assertIn('Readiness — pieces × sizes', html)
        self.assertIn('rm-missing', html)

    def test_get_writes_nothing(self):
        self._piece('m6-r3', 'Front')
        self.client.force_login(self.mgr)
        before = (PatternPiece.objects.count(),
                  CaptureAsset.objects.count(),
                  ProductFabricProfile.objects.count())
        self.client.get(self._hub_url())
        self.assertEqual(before, (PatternPiece.objects.count(),
                                  CaptureAsset.objects.count(),
                                  ProductFabricProfile.objects.count()))

    def test_worker_403(self):
        self.client.force_login(self.worker)
        self.assertEqual(self.client.get(self._hub_url()).status_code, 403)
        self.assertEqual(self.client.post(
            reverse('patterns_ai:piece-list'),
            {'product': self.product.pk, 'action': 'save_profile'}
        ).status_code, 403)


class HubActionTests(_M6Base):
    """Every POST lands in a frozen M3 writer — orchestration only."""

    def test_optional_toggle_roundtrip(self):
        # Phase 2 conscious rework: set_optional moved to the Blueprint
        # module (frozen resp. #1 — rules never edited from the Manager).
        piece = self._piece('m6-a1', 'Pocket')
        r = self._bp_post({'action': 'set_optional', 'piece': piece.pk,
                           'is_optional': '1'})
        self.assertEqual(r.status_code, 302)
        piece.refresh_from_db()
        self.assertTrue(piece.is_optional)
        self._bp_post({'action': 'set_optional', 'piece': piece.pk,
                       'is_optional': '0'})
        piece.refresh_from_db()
        self.assertFalse(piece.is_optional)
        # and the Manager surface refuses the retired action outright
        r = self._post({'action': 'set_optional', 'piece': piece.pk,
                        'is_optional': '1'})
        piece.refresh_from_db()
        self.assertFalse(piece.is_optional)      # nothing written

    def test_reference_upload_replace_and_clear(self):
        piece = self._piece('m6-a2', 'Front')
        up = SimpleUploadedFile('ref.png', png_bytes(),
                                content_type='image/png')
        self._post({'action': 'upload_reference', 'piece': piece.pk},
                   files={'reference': up})
        piece.refresh_from_db()
        self.assertIsNotNone(piece.reference_image_id)
        first = piece.reference_image
        self.assertEqual(first.kind, CaptureAsset.Kind.REFERENCE_IMAGE)
        # replace with a different image → pointer moves, old asset stays
        up2 = SimpleUploadedFile('ref2.png', png_bytes(rgb=(20, 90, 160)),
                                 content_type='image/png')
        self._post({'action': 'upload_reference', 'piece': piece.pk},
                   files={'reference': up2})
        piece.refresh_from_db()
        self.assertNotEqual(piece.reference_image_id, first.pk)
        first.refresh_from_db()                     # immutably stored
        self.assertEqual(first.kind, CaptureAsset.Kind.REFERENCE_IMAGE)
        # clear
        self._post({'action': 'clear_reference', 'piece': piece.pk})
        piece.refresh_from_db()
        self.assertIsNone(piece.reference_image_id)

    def test_reference_upload_never_enters_geometry(self):
        # the uploaded kind is FORCED to reference_image by the view —
        # extraction structurally refuses it (kind gate, M2-pinned).
        piece = self._piece('m6-a3', 'Front')
        up = SimpleUploadedFile('ref.png', png_bytes(rgb=(9, 9, 9)),
                                content_type='image/png')
        self._post({'action': 'upload_reference', 'piece': piece.pk},
                   files={'reference': up})
        piece.refresh_from_db()
        self.assertEqual(piece.reference_image.kind,
                         CaptureAsset.Kind.REFERENCE_IMAGE)

    def test_cross_product_piece_tamper_404(self):
        other = Product.objects.create(code='M6O', name='Other')
        pattern = ProductPattern.objects.create(code='m6-x', name='X')
        ProductPatternAssignment.objects.create(product=other,
                                                pattern=pattern,
                                                pieces_count=1)
        foreign = geo.create_piece(user=self.mgr, product=other,
                                   pattern=pattern, fabric_group='body')
        # Phase 2: tamper wall now lives on the Blueprint module
        r = self._bp_post({'action': 'set_optional', 'piece': foreign.pk,
                           'is_optional': '1'})
        self.assertEqual(r.status_code, 404)

    def test_profile_save_and_prefill_display(self):
        r = self._post({'action': 'save_profile',
                        'default_width_mm': '990',
                        'default_length_mm': '2000',
                        'default_spacing_mm': '3.0',
                        'fabric_type': 'Jersey', 'gsm': '180',
                        'lay_mode': 'face-up'})
        self.assertEqual(r.status_code, 302)
        profile = ProductFabricProfile.objects.get(product=self.product)
        self.assertEqual(profile.default_width_mm, 990)
        html = self.client.get(self._hub_url()).content.decode()
        self.assertIn('value="990"', html)
        self.assertIn('value="Jersey"', html)

    def test_profile_bad_value_shows_honest_error(self):
        r = self._post({'action': 'save_profile',
                        'default_width_mm': '50'})   # < MIN_WIDTH_MM
        self.assertEqual(r.status_code, 302)
        self.assertFalse(ProductFabricProfile.objects.filter(
            product=self.product).exists())
        follow = self.client.get(self._hub_url()).content.decode()
        self.assertIn('default width 50 mm outside', follow)

    def test_register_form_optional_checkbox_wires_through(self):
        # Phase 2 conscious rework: piece-new retired — registration is
        # the Blueprint's atomic add (register_pattern_definition).
        self._bp_post({'action': 'add', 'name': 'Loop',
                       'fabric_group': 'body', 'is_optional': '1'})
        piece = PatternPiece.objects.get(product=self.product,
                                         pattern__name='Loop')
        self.assertTrue(piece.is_optional)
