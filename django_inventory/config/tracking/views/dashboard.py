"""Barcode dashboard + CSV export.

YEH FILE KYU HAI?
─────────────────
/tracking/ pe Adda-wise barcode counts dikhata hai — pending/packed/dispatched/missing.
Har row pe Print QR + Export CSV actions hain (factory mein use karne ke liye).

annotate() + filter pattern:
  Conditional Count via filter=Q(...) — single SQL query mein har status ka count.
"""
from datetime import datetime, time

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.generic import TemplateView

from inventory.services import PRODUCTION_ROLES, user_has_role
from production.models import Adda
from django.db.models import Sum
from tracking.models import BarcodeBatch, BatchBarcode


def _parse_date(s):
    if not s:
        return None
    try:
        d = datetime.strptime(s, '%Y-%m-%d').date()
    except ValueError:
        return None
    return timezone.make_aware(datetime.combine(d, time.min))


class _ProductionRoleMixin(UserPassesTestMixin):
    def test_func(self):
        return user_has_role(self.request.user, PRODUCTION_ROLES)


class BarcodeDashboardView(LoginRequiredMixin, _ProductionRoleMixin, TemplateView):
    """Dashboard listing every Adda that has barcodes, with status breakdown.

    Filterable by Adda-creation date range via ?from= and ?to=.
    """

    template_name = 'tracking/barcode_dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        from_dt = _parse_date(self.request.GET.get('from'))
        to_dt = _parse_date(self.request.GET.get('to'))
        if to_dt:
            to_dt = to_dt + timezone.timedelta(days=1)

        # PR6: filter Adda by BarcodeBatch existence (BatchBarcode is lazy).
        addas_qs = Adda.objects.filter(barcode_batches__isnull=False)
        if from_dt:
            addas_qs = addas_qs.filter(created_at__gte=from_dt)
        if to_dt:
            addas_qs = addas_qs.filter(created_at__lt=to_dt)

        # Total per-Adda = SUM(BarcodeBatch.total_pieces). Scanned counts
        # come from BatchBarcode (lazy). Pending = total - scanned.
        addas = (
            addas_qs.annotate(
                total=Sum('barcode_batches__total_pieces'),
                packed=Count('barcodes', filter=Q(barcodes__status='packed')),
                dispatched=Count('barcodes', filter=Q(barcodes__status='dispatched')),
                missing=Count('barcodes', filter=Q(barcodes__status='missing')),
            )
            .select_related('product')
            .order_by('-started_at')
            .distinct()
        )
        # Pending = total - (packed + dispatched + missing). Computed in Python
        # to avoid double-counted M2M JOIN explosion.
        for a in addas:
            scanned = (a.packed or 0) + (a.dispatched or 0) + (a.missing or 0)
            a.pending = max((a.total or 0) - scanned, 0)

        # KPIs across all filtered Addas.
        total_pieces = (
            BarcodeBatch.objects.filter(adda__in=addas_qs)
            .aggregate(total=Sum('total_pieces'))['total'] or 0
        )
        scanned_qs = BatchBarcode.objects.filter(adda__in=addas_qs)
        scanned_total = scanned_qs.count()

        ctx['addas'] = addas
        ctx['total_barcodes'] = total_pieces
        ctx['by_status'] = {
            'pending': max(total_pieces - scanned_total, 0),
            'packed': scanned_qs.filter(status='packed').count(),
            'dispatched': scanned_qs.filter(status='dispatched').count(),
            'missing': scanned_qs.filter(status='missing').count(),
        }
        ctx['filter_from'] = self.request.GET.get('from', '')
        ctx['filter_to'] = self.request.GET.get('to', '')
        # Time logs — AddaHistory ke latest 30 events (barcodes Adda lifecycle se hi ban-te hain)
        from tracking.models import AddaHistory
        ctx['adda_events'] = (
            AddaHistory.objects
            .select_related(
                'adda', 'adda__product', 'stage_from', 'stage_to',
                'roll', 'roll__cloth_type', 'roll__cloth_color', 'actor',
            )
            .order_by('-created_at')[:30]
        )
        return ctx


@login_required
def barcode_export_csv(request, adda_code):
    """Legacy CSV export endpoint — quick download without manifest tracking.

    PR-D 2026-05-29: this view is the back-compat / quick-download path
    used by `barcode_list.html` toolbar. New canonical path is
    `tracking:export-csv` which creates a `BarcodeExportBatch` manifest
    row + supports re-download. Both paths return the same CSV bytes.

    Why keep this view?
      • Pre-completion download (works even if barcode_generation stage
        not yet complete — diagnostic + sanity)
      • Lightweight URL stable for any saved bookmarks
    """
    if not user_has_role(request.user, PRODUCTION_ROLES):
        return HttpResponse(status=403)
    adda = get_object_or_404(Adda, code=adda_code)
    # Reuse render-only helper from export service (no manifest row written).
    from tracking.services.barcode_export_service import _render_csv_bytes
    payload = _render_csv_bytes(adda)
    response = HttpResponse(payload, content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = (
        f'attachment; filename="{adda.code}-barcodes.csv"'
    )
    return response
