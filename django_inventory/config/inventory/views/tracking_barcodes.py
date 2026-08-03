"""Barcode batch list, print sheet, scan handler views.

YEH FILE KYU HAI?
─────────────────
PR6 (2026-05-28) ke baad barcodes BarcodeBatch ranges mein store hote hain.
Individual BatchBarcode rows lazy-created on scan. Views ko dono se kaam
karna padta hai:

  BarcodeListForAddaView   — Adda ke batches summary table + per-batch
                              piece count + scanned state link.
  BarcodePrintSheetView    — A4 print sheet: batches expand to virtual
                              stickers (seq 1..N rendered on the fly).
  scan_piece               — phone QR scan endpoint. resolve_value()
                              parses + finds batch + lazy creates piece row.
"""
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.generic import TemplateView

from accounts.services import MANAGEMENT_ROLES, PRODUCTION_ROLES, user_has_role
from inventory.views.mixins import ProductionRoleMixin as _ProductionRoleMixin
from production.models import Adda
from tracking.models import BatchBarcode
from tracking.services import get_or_create_piece, qr_data_uri, resolve_value


def _expand_batches_to_pieces(batches, limit: int | None = None):
    """Iterate BarcodeBatch rows, yield per-piece dicts for templating.

    Each batch is expanded to its seq range. Returns lightweight dict per
    piece — DOES NOT touch BatchBarcode table. Status defaults to 'pending'
    unless a BatchBarcode row exists (lazy scan state).

    Optionally caps total yielded pieces at `limit`.
    """
    # Pre-fetch scanned pieces for these batches to merge actual status.
    if not batches:
        return
    adda = batches[0].adda
    scanned = {
        bc.piece_seq: bc for bc in
        BatchBarcode.objects.filter(adda=adda).only(
            'piece_seq', 'value', 'status', 'last_scanned_at',
        )
    }
    yielded = 0
    for batch in batches:
        for seq in range(batch.start_seq, batch.end_seq + 1):
            if limit is not None and yielded >= limit:
                return
            value = batch.value_for_seq(seq)
            bc = scanned.get(seq)
            yield {
                'batch': batch,
                'seq': seq,
                'value': value,
                'status': bc.status if bc else 'pending',
                'last_scanned_at': bc.last_scanned_at if bc else None,
            }
            yielded += 1


class BarcodeListForAddaView(LoginRequiredMixin, _ProductionRoleMixin, TemplateView):
    """Per-Adda barcode summary: batches table + drill-down to virtual pieces."""

    template_name = 'tracking/barcode_list.html'

    def get_adda(self):
        return get_object_or_404(Adda, code=self.kwargs['adda_code'])

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        adda = self.get_adda()
        batches = list(
            adda.barcode_batches
            .select_related('size', 'color', 'product')
            .order_by('start_seq')
        )
        ctx['adda'] = adda
        ctx['batches'] = batches
        ctx['total_pieces'] = sum(b.total_pieces for b in batches)
        # Scanned count — how many pieces have BatchBarcode rows.
        ctx['scanned_count'] = BatchBarcode.objects.filter(adda=adda).count()
        # V1.1 Item 3: template hides export buttons for non-management
        # (list/print/scan stay PRODUCTION_ROLES — workers legitimately scan).
        ctx['is_management'] = user_has_role(self.request.user, MANAGEMENT_ROLES)
        return ctx


class BarcodePrintSheetView(LoginRequiredMixin, _ProductionRoleMixin, TemplateView):
    """A4 sticker sheet of QR codes.

    Query params:
      ?size=small|medium|large   (default: small — max density, still reliable)
      ?status=pending|packed|... (optional filter — useful for reprints)
    """

    template_name = 'tracking/barcode_print_sheet.html'

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

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        spec, size = self._spec()
        adda = self.get_adda()
        base = self.request.build_absolute_uri('/')

        batches = list(
            adda.barcode_batches
            .select_related('size', 'color')
            .order_by('start_seq')
        )

        # Status filter against scanned-state rows. If filtering, only show
        # pieces with matching status; 'pending' includes virtual (not-yet-scanned).
        status_filter = self.request.GET.get('status', '')
        pieces = list(_expand_batches_to_pieces(batches))
        if status_filter in {'pending', 'packed', 'dispatched', 'missing'}:
            pieces = [p for p in pieces if p['status'] == status_filter]

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
        ctx['active_status'] = status_filter
        ctx['barcode_rows'] = [
            {'bc': p, 'qr': qr_data_uri(p['value'], base, box_size=spec['box_size'])}
            for p in pieces
        ]
        ctx['per_page'] = spec['cols'] * spec['rows']
        ctx['total_pages'] = (len(ctx['barcode_rows']) + ctx['per_page'] - 1) // ctx['per_page'] if ctx['barcode_rows'] else 0
        return ctx


@login_required
@transaction.atomic
def scan_piece(request, value):
    """Public-after-login QR landing. Resolves via BarcodeBatch, lazy-creates
    BatchBarcode scan-state row, stamps last_scanned_at/by.

    @transaction.atomic wrap (audit follow-up 2026-05-29): get_or_create_piece
    apne andar atomic hai, par uske baad ka last_scanned_at/by update
    separate SQL tha — race window mein concurrent scan ka stamp + concurrent
    status update interleave kar sakta tha. Ab dono ek transaction ke andar.
    SELECT FOR UPDATE bhi lagaya gaya hai BatchBarcode row pe taaki
    parallel scans serialize ho jaayen.

    RBAC (review fix 2026-06-02): production-floor only. Mutates audit fields
    (last_scanned_at/by), so a bare @login_required let any authenticated user
    (office/normal) stamp scans. Gate to PRODUCTION_ROLES like the sibling views.
    """
    if not user_has_role(request.user, PRODUCTION_ROLES):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("Scanning is restricted to production staff.")
    hit = resolve_value(value)
    if hit is None:
        from django.http import Http404
        raise Http404(f"barcode '{value}' not recognized")
    batch, seq = hit
    bc = get_or_create_piece(batch, seq)
    # select_for_update lock — same piece ka concurrent scan/status-change
    # serialise. last write wins on stamp, but no interleaved corruption.
    bc = BatchBarcode.objects.select_for_update().get(pk=bc.pk)
    bc.last_scanned_at = timezone.now()
    bc.last_scanned_by = request.user
    bc.save(update_fields=['last_scanned_at', 'last_scanned_by'])
    return render(request, 'tracking/scan_detail.html', {'barcode': bc, 'batch': batch})

@login_required
@transaction.atomic
def update_piece_status(request, value):
    """One-tap status update from the scan page (Module 8, 2026-07-11).
    Thin wire to the EXISTING single-writer tracking service —
    mark_status owns validation, gating semantics mirror scan_piece
    (production staff only; a status write is an audit act)."""
    if request.method != 'POST':
        from django.http import HttpResponseNotAllowed
        return HttpResponseNotAllowed(['POST'])
    if not user_has_role(request.user, PRODUCTION_ROLES):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("Scanning is restricted to production staff.")
    from django.contrib import messages
    from django.core.exceptions import ValidationError
    from django.shortcuts import redirect
    from tracking.services import mark_status
    try:
        piece = mark_status(request.user, value,
                            request.POST.get('status', ''))
        messages.success(request,
                         f'{piece.value} → {piece.get_status_display()}')
    except ValidationError as exc:
        messages.error(request, '; '.join(getattr(exc, 'messages', [str(exc)])))
    return redirect('tracking:scan', value=value)
