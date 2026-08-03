"""URL routes for the /tracking/ surface — INVENTORY-owned (P4.2 D1).

Views moved out of the tracking app so tracking imports no production;
the `tracking:` namespace + every URL name/path is preserved (templates and
reverse() calls unchanged).
"""
from django.urls import path

from inventory.views import tracking_barcodes, tracking_dashboard, tracking_exports, tracking_history

app_name = 'tracking'

urlpatterns = [
    path('',                                tracking_dashboard.BarcodeDashboardView.as_view(),    name='dashboard'),
    path('barcodes/<str:adda_code>/',       tracking_barcodes.BarcodeListForAddaView.as_view(),  name='barcode-list'),
    path('barcodes/<str:adda_code>/print/', tracking_barcodes.BarcodePrintSheetView.as_view(),   name='barcode-print'),
    path('barcodes/<str:adda_code>/export/', tracking_dashboard.barcode_export_csv,               name='barcode-export'),
    path('scan/<str:value>/',               tracking_barcodes.scan_piece,                        name='scan'),
    path('scan/<str:value>/status/',        tracking_barcodes.update_piece_status,               name='scan-status'),
    path('history/roll/<int:roll_pk>/',     tracking_history.RollHistoryView.as_view(),         name='roll-history'),
    path('history/adda/<str:adda_code>/',   tracking_history.AddaHistoryView.as_view(),         name='adda-history'),

    # Barcode exports (PR-D 2026-05-29) — manifest-tracked + re-downloadable
    # Per-Adda export triggers (POST). Service refuses if barcode_generation
    # stage is not yet complete.
    path('exports/',                              tracking_exports.ExportListView.as_view(),   name='export-list'),
    path('exports/<str:adda_code>/csv/',          tracking_exports.ExportCSVView.as_view(),    name='export-csv'),
    path('exports/<str:adda_code>/xlsx/',         tracking_exports.ExportXLSXView.as_view(),   name='export-xlsx'),
    path('exports/<str:adda_code>/pdf/',          tracking_exports.ExportPDFView.as_view(),    name='export-pdf'),
    path('exports/<str:export_code>/download/',   tracking_exports.ReDownloadView.as_view(),   name='export-download'),
]
