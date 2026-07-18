"""Phase-5 M3 tests — the optimize UI lives inline in the workspace page.
Canvas behavior is browser-proven (M3 report); these pin the rendered
controls, the product language, and that Phase-4 behavior kept working.
"""
import shutil
import tempfile
import unittest

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import Role
from production.models import (Product, ProductPattern,
                               ProductPatternAssignment, ProductSize)
from patterns_ai.models import PieceSizeGeometry
from patterns_ai.services import compute_bridge
from patterns_ai.services import marker_generation_service as gen
from patterns_ai.services import pattern_geometry_service as geo
from patterns_ai.tests.test_p3_generation import rect_um

User = get_user_model()
MEDIA = tempfile.mkdtemp(prefix='pai-ph5m3-media-')
RUNTIME_OK = compute_bridge.runtime_available()


@unittest.skipUnless(RUNTIME_OK, 'compute runtime required (ADR-F)')
@override_settings(MEDIA_ROOT=MEDIA)
class WorkspaceOptimizeUiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        mgr = Role.objects.get_or_create(code='manager', defaults={'name': 'M'})[0]
        cls.mgr = User.objects.create_user('m3@test.local', password='x', role=mgr)
        cls.product = Product.objects.create(code='M3PROD', name='M3')
        cls.size = ProductSize.objects.create(product=cls.product, code='m',
                                              label='M', display_order=1)
        pattern = ProductPattern.objects.create(code='m3-front', name='Front')
        ProductPatternAssignment.objects.create(product=cls.product,
                                                pattern=pattern,
                                                pieces_count=1)
        piece = geo.create_piece(user=cls.mgr, product=cls.product,
                                 pattern=pattern, fabric_group='body')
        draft = geo.get_or_create_draft(user=cls.mgr, piece=piece)
        PieceSizeGeometry.objects.create(      # test fixture only
            version=draft, size=cls.size, geometry=rect_um(300, 200),
            trust_grade='photo_calibrated', created_by=cls.mgr)
        geo.confirm_version(user=cls.mgr, version=draft)
        _, rows = gen.start_run(user=cls.mgr, product=cls.product,
                                usable_width_mm=900, ratio={cls.size: 2},
                                timebox_s=6, engine='blf')
        cls.candidate = rows[0]

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    def page(self):
        self.client.force_login(self.mgr)
        return self.client.get(reverse('patterns_ai:workspace',
                                       args=[self.candidate.pk]))

    def test_optimizer_controls_render_inline(self):
        resp = self.page()
        for needle in ('Layout options', 'id="opt_n"', 'id="opt_mode"',
                       'Fast', 'Balanced', 'Best', 'Piece spacing',
                       'Rotation: 0° / 180° (grain rule)',
                       '✨ Optimize', 'id="strip"', 'id="previewbar"'):
            self.assertContains(resp, needle)
        # no dialogs/wizards: strip + previewbar are inline divs
        self.assertNotContains(resp, '<dialog')

    def test_product_language_and_honest_hints(self):
        resp = self.page()
        self.assertContains(resp, 'Layout editor')
        self.assertContains(resp, 'Keep this option')
        self.assertContains(resp, 'Current Layout')
        self.assertContains(resp, 'the server decides at')
        # internal vocabulary stays out of the flow copy
        self.assertNotContains(resp, 'candidate</h1>')
        self.assertNotContains(resp, 'verifier')

    def test_multiselect_and_preview_wiring_present(self):
        resp = self.page()
        for needle in ('id="selchip"', 'shift-click', 'selected',
                       'Worse than Current', 'previewing'):
            self.assertContains(resp, needle)

    def test_phase4_controls_still_render(self):
        resp = self.page()
        for needle in ('id="ws"', 'Grid', 'Snap', 'Rotate 180',
                       'Lock/Unlock', 'Width mm', 'Height mm',
                       'Save layout', 'utilization', 'wastage'):
            self.assertContains(resp, needle)


@unittest.skipUnless(RUNTIME_OK, 'compute runtime required (ADR-F)')
@override_settings(MEDIA_ROOT=MEDIA)
class UndoRedoUiTests(WorkspaceOptimizeUiTests):
    """M4 — undo/redo controls + wording pass (canvas behavior is
    browser-proven; these pin the rendered surface)."""

    def test_undo_redo_controls_render(self):
        resp = self.page()
        for needle in ('id="undo"', 'id="redo"', '↶ Undo', '↷ Redo',
                       'pushHistory', 'stateFromPlacements',
                       'ZERO history entries'):
            self.assertContains(resp, needle)

    def test_save_toast_speaks_product_language(self):
        import json as _json
        self.client.force_login(self.mgr)
        pl = self.candidate.placements['placements']
        resp = self.client.post(
            reverse('patterns_ai:workspace', args=[self.candidate.pk]),
            {'placements': _json.dumps(pl), 'width_mm': '900',
             'height_mm': '2500'}, follow=True)
        self.assertContains(resp, 'Layout saved')
        self.assertContains(resp, 'editing the saved version')  # (apostrophe html-escapes)
        self.assertNotContains(resp, 'candidate #')   # internal vocabulary out
