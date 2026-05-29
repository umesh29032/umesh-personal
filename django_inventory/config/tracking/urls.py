"""URL routes for tracking app."""
from django.urls import path

from tracking import views

app_name = 'tracking'

urlpatterns = [
    path('',                                views.BarcodeDashboardView.as_view(),    name='dashboard'),
    path('barcodes/<str:adda_code>/',       views.BarcodeListForAddaView.as_view(),  name='barcode-list'),
    path('barcodes/<str:adda_code>/print/', views.BarcodePrintSheetView.as_view(),   name='barcode-print'),
    path('barcodes/<str:adda_code>/export/', views.barcode_export_csv,               name='barcode-export'),
    path('scan/<str:value>/',               views.scan_piece,                        name='scan'),
    path('history/roll/<int:roll_pk>/',     views.RollHistoryView.as_view(),         name='roll-history'),
    path('history/adda/<str:adda_code>/',   views.AddaHistoryView.as_view(),         name='adda-history'),

    # Barcode exports (PR-D 2026-05-29) — manifest-tracked + re-downloadable
    # Per-Adda export triggers (POST). Service refuses if barcode_generation
    # stage is not yet complete.
    path('exports/',                              views.ExportListView.as_view(),   name='export-list'),
    path('exports/<str:adda_code>/csv/',          views.ExportCSVView.as_view(),    name='export-csv'),
    path('exports/<str:adda_code>/xlsx/',         views.ExportXLSXView.as_view(),   name='export-xlsx'),
    path('exports/<str:adda_code>/pdf/',          views.ExportPDFView.as_view(),    name='export-pdf'),
    path('exports/<str:export_code>/download/',   views.ReDownloadView.as_view(),   name='export-download'),
]
