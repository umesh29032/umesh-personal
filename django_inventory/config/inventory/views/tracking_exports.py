"""Barcode export views — CSV / XLSX / PDF triggers + re-download + history.

YEH FILE KYU HAI?
─────────────────
PR-D 2026-05-29 (BARCODE_STAGE_PLAN.md): export endpoints for vendor /
factory label printing. Service layer karta hai actual generation
(barcode_export_service). Views thin — POST → service → HTTP file response.

URL TABLE:
  POST exports/<adda_code>/csv/      ExportCSVView
  POST exports/<adda_code>/xlsx/     ExportXLSXView
  POST exports/<adda_code>/pdf/      ExportPDFView
  GET  exports/<export_code>/download/  ReDownloadView
  GET  exports/                      ExportListView (recent exports global)

PERMISSIONS:
  MANAGEMENT_ROLES gate (V1.1 Item 3, 2026-07-12) — exports are management
  functionality; workers scan/list barcodes but never export production data.
  Service layer re-checks the same role set (defense-in-depth) and also
  gates by barcode_generation stage completion.
"""
from __future__ import annotations

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views import View
from django.views.generic import ListView

from inventory.views.mixins import ManagerOrAdminMixin
from production.models import Adda
from tracking.models import BarcodeExportBatch
from production.stages.barcode_generation.export_service import (
    content_type_for, filename_for, generate_csv, generate_pdf_summary,
    generate_xlsx, regenerate_for_export,
)


def _build_file_response(batch, payload: bytes) -> HttpResponse:
    """Common response shape — content-type + attachment header + bytes."""
    resp = HttpResponse(payload, content_type=content_type_for(batch.export_method))
    resp['Content-Disposition'] = (
        f'attachment; filename="{filename_for(batch)}"'
    )
    return resp


class _BaseExportTriggerView(LoginRequiredMixin, ManagerOrAdminMixin, View):
    """POST-only export trigger — subclass picks the service function."""

    http_method_names = ['post']
    service_fn = None  # subclass override

    def post(self, request, adda_code):
        adda = get_object_or_404(Adda, code=adda_code)
        try:
            # PermissionDenied from the service backstop bubbles up → Django 403.
            batch, payload = self.__class__.service_fn(adda, request.user)
        except ValidationError as exc:
            msg = getattr(exc, 'messages', None)
            return HttpResponse(
                ' '.join(msg) if msg else str(exc),
                status=400, content_type='text/plain',
            )
        return _build_file_response(batch, payload)


class ExportCSVView(_BaseExportTriggerView):
    service_fn = staticmethod(generate_csv)


class ExportXLSXView(_BaseExportTriggerView):
    service_fn = staticmethod(generate_xlsx)


class ExportPDFView(_BaseExportTriggerView):
    service_fn = staticmethod(generate_pdf_summary)


class ReDownloadView(LoginRequiredMixin, ManagerOrAdminMixin, View):
    """Re-download an existing export by export_code.

    Regenerates from live barcode data — may differ from original if
    barcodes were reopened + regenerated since. Manifest total_labels
    stays frozen (audit invariant).
    """

    def get(self, request, export_code):
        batch = get_object_or_404(BarcodeExportBatch, export_code=export_code)
        try:
            payload = regenerate_for_export(batch, request.user)
        except ValidationError as exc:
            msg = getattr(exc, 'messages', None)
            return HttpResponse(
                ' '.join(msg) if msg else str(exc),
                status=400, content_type='text/plain',
            )
        return _build_file_response(batch, payload)


class ExportListView(LoginRequiredMixin, ManagerOrAdminMixin, ListView):
    """Global recent-exports dashboard."""

    template_name = 'tracking/export_list.html'
    model = BarcodeExportBatch
    context_object_name = 'exports'
    paginate_by = 50

    def get_queryset(self):
        return (
            BarcodeExportBatch.objects
            .select_related('adda', 'product', 'exported_by')
            .order_by('-created_at')
        )
