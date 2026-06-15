"""Phase 13 — PA-13-1: barcode dashboard per-Adda counts must not cross-join."""
from django.test import RequestFactory, TestCase

from accounts.models import User
from inventory.views.tracking_dashboard import BarcodeDashboardView
from production.models import Adda, Product
from tracking.models import BarcodeBatch, BatchBarcode


class BarcodeDashboardCountTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='bd@t.test', password='x',
                                              is_superuser=True, is_staff=True)
        self.product = Product.objects.create(code='BD', name='BD P')
        self.adda = Adda.objects.create(code='BD-001', product=self.product)
        # Two batches (multi-(color,size) Adda): 60 + 40 = 100 real pieces.
        BarcodeBatch.objects.create(adda=self.adda, product=self.product,
                                    start_seq=1, end_seq=60, total_pieces=60)
        BarcodeBatch.objects.create(adda=self.adda, product=self.product,
                                    start_seq=61, end_seq=100, total_pieces=40)
        # Three scanned pieces: 2 packed, 1 dispatched.
        for i, st in enumerate(('packed', 'packed', 'dispatched')):
            BatchBarcode.objects.create(adda=self.adda, value=f'BD-001-{i:04d}',
                                        status=st, piece_seq=i + 1)

    def test_per_adda_counts_are_not_crossjoined(self):
        # PA-13-1: pre-fix the single mixed .annotate() cross-joined batches × barcodes
        # → total=300 (100×3 barcodes), packed=4 (2×2 batches). Must be the real values.
        view = BarcodeDashboardView()
        view.request = RequestFactory().get('/')
        ctx = view.get_context_data()
        row = next(a for a in ctx['addas'] if a.pk == self.adda.pk)
        self.assertEqual(row.total, 100)
        self.assertEqual(row.packed, 2)
        self.assertEqual(row.dispatched, 1)
        self.assertEqual(row.missing, 0)
        self.assertEqual(row.pending, 97)
        # Per-row figures must reconcile with the (separately-computed) KPI cards.
        self.assertEqual(row.total, ctx['total_barcodes'])
        self.assertEqual(row.packed, ctx['by_status']['packed'])
