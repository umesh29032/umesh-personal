"""Phase-6 M8 tests — production exports: pure-python PDF (page 1 =
summary, tiled true-scale marker), tiled print page, SVG summary
stamping. Verified layouts only."""
import unittest

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounts.models import Role
from production.models import Product, ProductSize
from patterns_ai.models import GeneratedMarkerCandidate, MarkerGenerationRun
from patterns_ai.services import compute_bridge

User = get_user_model()
RUNTIME_OK = compute_bridge.runtime_available()

SQUARE = [[0.0, 0.0], [600.0, 0.0], [600.0, 500.0], [0.0, 500.0]]


class _M8Base(TestCase):
    @classmethod
    def setUpTestData(cls):
        mgr = Role.objects.get_or_create(code='manager', defaults={'name': 'M'})[0]
        wk = Role.objects.get_or_create(code='worker', defaults={'name': 'W'})[0]
        cls.mgr = User.objects.create_user('m8@test.local', password='x', role=mgr)
        cls.worker = User.objects.create_user('m8w@test.local', password='x', role=wk)
        cls.product = Product.objects.create(code='M8P', name='M8 Product')
        cls.size = ProductSize.objects.create(product=cls.product, code='l',
                                              label='L', display_order=1)
        cls.ok = cls._layout(True)
        cls.bad = cls._layout(False)

    @classmethod
    def _layout(cls, ok):
        run = MarkerGenerationRun.objects.create(   # test fixture only
            product=cls.product, usable_width_mm=990,
            params={'schema_version': 1, 'ratio': {str(cls.size.pk): 1}},
            pipeline_version='t', created_by=cls.mgr)
        return GeneratedMarkerCandidate.objects.create(
            run=run, engine='manual',
            placements={'schema_version': 1, 'placements': [
                {'key': 'Front·l', 'instance': 0, 'mirrored': False,
                 'rotation_deg': 0, 'polygon_mm': SQUARE}]},
            marker_length_mm='1291.09',
            verification={'ok': ok, 'max_overlap_mm2': 0,
                          'within_width': ok, 'piece_count': 1})

    def _get(self, name, layout, **kw):
        return self.client.get(reverse(f'patterns_ai:{name}',
                                       args=[layout.pk]), **kw)


class PrintPageTests(_M8Base):
    def test_tile_grid_math_and_labels(self):
        self.client.force_login(self.mgr)
        html = self._get('candidate-print', self.ok).content.decode()
        # W=990 → 6 cols (step 180) · L=1291.09 → 5 rows (step 267)
        self.assertIn('6 column(s) × 5 row(s) = 30 tile', html)
        self.assertIn('tile C1-R1', html)
        self.assertIn('tile C6-R5', html)
        self.assertEqual(html.count('TRUE SCALE — print at 100%'), 30)
        self.assertIn('@page { size:A4 portrait; margin:10mm; }', html)
        self.assertIn('10 cm', html)                 # honesty bar
        # true-scale tile svg: mm-sized window + windowed viewBox
        self.assertIn('width="190.0mm" height="277.0mm"', html)
        self.assertIn('viewBox="180.0 0.0 190.0 277.0"', html)   # C2-R1
        # summary block present
        self.assertIn('Production Layout Summary', html)
        self.assertIn('990 mm', html)
        self.assertIn('1291.09 mm', html)

    def test_unverified_refused(self):
        self.client.force_login(self.mgr)
        r = self._get('candidate-print', self.bad, follow=True)
        self.assertContains(r, 'cannot be printed for production')

    def test_worker_403(self):
        self.client.force_login(self.worker)
        self.assertEqual(self._get('candidate-print', self.ok)
                         .status_code, 403)
        self.assertEqual(self._get('candidate-pdf', self.ok)
                         .status_code, 403)


class SvgStampTests(_M8Base):
    def test_download_carries_summary_metadata(self):
        self.client.force_login(self.mgr)
        svg = self._get('candidate-svg', self.ok).content.decode()
        self.assertIn('<metadata id="production-layout-summary">', svg)
        self.assertIn('<desc>Production Layout Summary', svg)
        self.assertIn('"utilization_pct"', svg)
        self.assertIn('"product_code": "M8P"', svg)
        self.assertIn('L×1', svg)                    # ratio inside metadata
        # drawable content unchanged: pieces still render
        self.assertIn('<polygon points=', svg)


class ButtonTests(_M8Base):
    def test_export_buttons_verified_only(self):
        self.client.force_login(self.mgr)
        ok_html = self._get('candidate-detail', self.ok).content.decode()
        self.assertIn('Production PDF', ok_html)
        self.assertIn('Print tiles', ok_html)
        bad_html = self._get('candidate-detail', self.bad).content.decode()
        self.assertNotIn('Production PDF', bad_html)
        self.assertNotIn('Print tiles', bad_html)


class PdfRefusalTests(_M8Base):
    def test_unverified_pdf_refused_before_bridge(self):
        # no runtime needed — the gate fires before any compute call
        self.client.force_login(self.mgr)
        r = self._get('candidate-pdf', self.bad, follow=True)
        self.assertContains(r, 'cannot be exported for production')


@unittest.skipUnless(RUNTIME_OK, 'compute runtime required (ADR-F)')
class PdfDocumentTests(_M8Base):
    """The artifact itself — structure, pages, summary, true scale."""

    def test_pdf_document(self):
        self.client.force_login(self.mgr)
        r = self._get('candidate-pdf', self.ok)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r['Content-Type'], 'application/pdf')
        self.assertIn('layout_%d_production.pdf' % self.ok.pk,
                      r['Content-Disposition'])
        pdf = r.content
        self.assertTrue(pdf.startswith(b'%PDF-1.4'))
        body = pdf.decode('cp1252', 'replace')
        # 1 summary page + 6×5 tiles
        self.assertIn('/Count 31', body)
        self.assertIn('Production Layout Summary', body)
        self.assertIn('990', body)
        self.assertIn('1291.09', body)
        self.assertIn('C6-R5', body)                 # last tile numbered
        self.assertIn('100 mm scale bar', body)
        # TRUE-SCALE pin: the 100 mm bar ends at margin + 283.46 pt
        self.assertIn('311.81', body)
        self.assertIn('%%EOF', body)
