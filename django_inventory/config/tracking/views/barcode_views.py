"""Barcode list, print sheet, scan handler views.

YEH FILE KYU HAI?
─────────────────
BarcodeListForAddaView   — ek Adda ke saare barcodes paginated.
BarcodePrintSheetView    — A4 print sheet with QR grid + size/status filter.
scan_piece               — phone se QR scan karne pe yaha land karta hai.
                           Updates last_scanned_at/by, renders piece detail.
"""
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.generic import ListView

from inventory.services import PRODUCTION_ROLES, user_has_role
from production.models import Adda
from tracking.models import BatchBarcode
from tracking.services import qr_data_uri


class _ProductionRoleMixin(UserPassesTestMixin):
    def test_func(self):
        return user_has_role(self.request.user, PRODUCTION_ROLES)


class BarcodeListForAddaView(LoginRequiredMixin, _ProductionRoleMixin, ListView):
    template_name = 'tracking/barcode_list.html'
    context_object_name = 'barcodes'
    paginate_by = 100

    def get_adda(self):
        return get_object_or_404(Adda, code=self.kwargs['adda_code'])

    def get_queryset(self):
        return self.get_adda().barcodes.order_by('piece_seq')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['adda'] = self.get_adda()
        return ctx


class BarcodePrintSheetView(LoginRequiredMixin, _ProductionRoleMixin, ListView):
    """A4 sticker sheet of QR codes.

    Query params:
      ?size=small|medium|large   (default: small — max density, still reliable)
      ?status=pending|packed|... (optional filter — useful for reprints)
    """

    template_name = 'tracking/barcode_print_sheet.html'
    context_object_name = 'barcodes'
    paginate_by = None

    # box_size in pixels per QR module — drives the rendered PNG size.
    # ECC Q already takes care of damage tolerance, so we can run dense.
    # Sticker dimensions are picked for reliable phone scan from 15-20cm:
    #   small  → ~22mm QR, 6 cols × 9 rows = 54 stickers / A4
    #   medium → ~30mm QR, 5 cols × 7 rows = 35 stickers / A4
    #   large  → ~42mm QR, 4 cols × 6 rows = 24 stickers / A4
    SIZE_SPECS = {
        'small':  {'cols': 6, 'rows': 9, 'qr_mm': 22, 'box_size': 4, 'label': 'Small (54 / page)'},
        'medium': {'cols': 5, 'rows': 7, 'qr_mm': 30, 'box_size': 6, 'label': 'Medium (35 / page)'},
        'large':  {'cols': 4, 'rows': 6, 'qr_mm': 42, 'box_size': 8, 'label': 'Large (24 / page)'},
    }

    def get_adda(self):
        return get_object_or_404(Adda, code=self.kwargs['adda_code'])

    def _spec(self):
        size = self.request.GET.get('size', 'small')
        return self.SIZE_SPECS.get(size, self.SIZE_SPECS['small']), size

    def get_queryset(self):
        qs = self.get_adda().barcodes.order_by('piece_seq')
        status = self.request.GET.get('status')
        if status in {'pending', 'packed', 'dispatched', 'missing'}:
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        spec, size = self._spec()
        adda = self.get_adda()
        base = self.request.build_absolute_uri('/')

        ctx['adda'] = adda
        ctx['size'] = size
        ctx['spec'] = spec
        ctx['size_options'] = [
            ('small',  self.SIZE_SPECS['small']['label']),
            ('medium', self.SIZE_SPECS['medium']['label']),
            ('large',  self.SIZE_SPECS['large']['label']),
        ]
        ctx['status_options'] = [
            ('', 'All barcodes'),
            ('pending', 'Pending only (unprinted/unpacked)'),
            ('packed', 'Packed only'),
            ('dispatched', 'Dispatched only'),
            ('missing', 'Missing only'),
        ]
        ctx['active_status'] = self.request.GET.get('status', '')
        # Pre-compute QR images at the chosen box_size.
        ctx['barcode_rows'] = [
            {'bc': bc, 'qr': qr_data_uri(bc, base, box_size=spec['box_size'])}
            for bc in self.get_queryset()
        ]
        ctx['per_page'] = spec['cols'] * spec['rows']
        ctx['total_pages'] = (len(ctx['barcode_rows']) + ctx['per_page'] - 1) // ctx['per_page'] if ctx['barcode_rows'] else 0
        return ctx


@login_required
def scan_piece(request, value):
    """Public-after-login QR landing page. Updates last_scanned_at/by."""
    bc = get_object_or_404(BatchBarcode.objects.select_related('adda', 'adda__product'), value=value)
    bc.last_scanned_at = timezone.now()
    bc.last_scanned_by = request.user
    bc.save(update_fields=['last_scanned_at', 'last_scanned_by'])
    return render(request, 'tracking/scan_detail.html', {'barcode': bc})
