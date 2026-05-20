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
]
