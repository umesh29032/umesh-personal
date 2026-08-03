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
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.generic import TemplateView

from accounts.services import MANAGEMENT_ROLES, user_has_role
from inventory.views.mixins import ProductionRoleMixin as _ProductionRoleMixin
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


class BarcodeDashboardView(LoginRequiredMixin, _ProductionRoleMixin, TemplateView):
    """Dashboard listing every Adda that has barcodes, with status breakdown.

    Filterable by Adda-creation date range via ?from= and ?to=.
    """

    template_name = 'tracking/barcode_dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # V1.1 Item 3: template hides Export CSV action for non-management.
        # getattr: PA-13-1 test drives get_context_data with a bare RequestFactory
        # request (no auth middleware → no .user attribute).
        _user = getattr(self.request, 'user', None)
        ctx['is_management'] = bool(_user) and user_has_role(_user, MANAGEMENT_ROLES)

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

        # PA-13-1: per-Adda totals + scanned counts come from TWO different multi-valued
        # relations (BarcodeBatch.total_pieces vs BatchBarcode rows). Annotating both in
        # ONE .annotate() cross-joins them — Sum(total_pieces) gets multiplied by the
        # #barcodes and each Count(barcodes) by the #batches, so every per-row figure was
        # inflated the moment a multi-batch Adda had any scanned piece (and contradicted
        # the KPI cards). Compute each from a SEPARATE grouped query (same approach as the
        # KPI cards below) and attach in Python — no cross-join.
        addas = list(
            addas_qs.select_related('product').order_by('-started_at').distinct())
        adda_ids = [a.pk for a in addas]
        total_by_adda = {
            r['adda']: r['t'] for r in
            BarcodeBatch.objects.filter(adda_id__in=adda_ids)
            .values('adda').annotate(t=Sum('total_pieces'))
        }
        scanned_by_adda = {}
        for r in (BatchBarcode.objects
                  .filter(adda_id__in=adda_ids,
                          status__in=('packed', 'dispatched', 'missing'))
                  .values('adda', 'status').annotate(n=Count('id'))):
            scanned_by_adda.setdefault(r['adda'], {})[r['status']] = r['n']
        for a in addas:
            sc = scanned_by_adda.get(a.pk, {})
            a.total = total_by_adda.get(a.pk, 0) or 0
            a.packed = sc.get('packed', 0)
            a.dispatched = sc.get('dispatched', 0)
            a.missing = sc.get('missing', 0)
            a.pending = max(a.total - (a.packed + a.dispatched + a.missing), 0)

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

    V1.1 Item 3 (2026-07-12): exports = MANAGEMENT_ROLES only (same source
    as tracking_exports views) — workers scan barcodes but never export.
    """
    if not user_has_role(request.user, MANAGEMENT_ROLES):
        return HttpResponse(status=403)
    adda = get_object_or_404(Adda, code=adda_code)
    # Reuse render-only helper from export service (no manifest row written).
    from production.stages.barcode_generation.export_service import _render_csv_bytes
    payload = _render_csv_bytes(adda)
    response = HttpResponse(payload, content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = (
        f'attachment; filename="{adda.code}-barcodes.csv"'
    )
    return response
