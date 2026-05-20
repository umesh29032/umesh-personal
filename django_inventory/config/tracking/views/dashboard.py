"""Barcode dashboard + CSV export.

YEH FILE KYU HAI?
─────────────────
/tracking/ pe Adda-wise barcode counts dikhata hai — pending/packed/dispatched/missing.
Har row pe Print QR + Export CSV actions hain (factory mein use karne ke liye).

annotate() + filter pattern:
  Conditional Count via filter=Q(...) — single SQL query mein har status ka count.
"""
import csv
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
from tracking.models import BatchBarcode


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

        addas_qs = Adda.objects.filter(barcodes__isnull=False)
        if from_dt:
            addas_qs = addas_qs.filter(created_at__gte=from_dt)
        if to_dt:
            addas_qs = addas_qs.filter(created_at__lt=to_dt)

        addas = (
            addas_qs.annotate(
                total=Count('barcodes'),
                pending=Count('barcodes', filter=Q(barcodes__status='pending')),
                packed=Count('barcodes', filter=Q(barcodes__status='packed')),
                dispatched=Count('barcodes', filter=Q(barcodes__status='dispatched')),
                missing=Count('barcodes', filter=Q(barcodes__status='missing')),
            )
            .select_related('product')
            .order_by('-started_at')
            .distinct()
        )

        # Status KPIs apply across the filtered Addas only.
        barcodes_qs = BatchBarcode.objects.filter(adda__in=addas_qs)

        ctx['addas'] = addas
        ctx['total_barcodes'] = barcodes_qs.count()
        ctx['by_status'] = {
            'pending': barcodes_qs.filter(status='pending').count(),
            'packed': barcodes_qs.filter(status='packed').count(),
            'dispatched': barcodes_qs.filter(status='dispatched').count(),
            'missing': barcodes_qs.filter(status='missing').count(),
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
    """Download all barcode values + status for one Adda as CSV."""
    if not user_has_role(request.user, PRODUCTION_ROLES):
        return HttpResponse(status=403)
    adda = get_object_or_404(Adda, code=adda_code)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{adda.code}-barcodes.csv"'
    writer = csv.writer(response)
    writer.writerow(['piece_seq', 'value', 'status', 'created_at', 'updated_at', 'last_scanned_at', 'last_scanned_by'])
    for bc in adda.barcodes.order_by('piece_seq').select_related('last_scanned_by'):
        writer.writerow([
            bc.piece_seq, bc.value, bc.status,
            bc.created_at.isoformat(),
            bc.updated_at.isoformat(),
            bc.last_scanned_at.isoformat() if bc.last_scanned_at else '',
            bc.last_scanned_by.email if bc.last_scanned_by else '',
        ])
    return response
