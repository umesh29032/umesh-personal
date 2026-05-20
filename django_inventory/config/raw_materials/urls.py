"""URL routes for raw_materials app."""
from django.urls import path

from raw_materials import views

app_name = 'raw_materials'

urlpatterns = [
    # Overall raw-material index (cloth live, future materials placeholder).
    path('',                      views.RawMaterialDashboardView.as_view(),  name='dashboard'),
    # Cloth-only dashboard with Type × Color breakup + color filter.
    path('cloth/',                views.ClothDashboardView.as_view(),        name='cloth-dashboard'),

    # Cloth Rolls
    path('rolls/',                views.RollListView.as_view(),         name='roll-list'),
    path('rolls/bulk-add/',       views.RollBulkCreateView.as_view(),   name='roll-bulk-create'),
    path('rolls/<int:pk>/',       views.RollDetailView.as_view(),       name='roll-detail'),
    path('rolls/<int:pk>/edit/',  views.RollUpdateView.as_view(),       name='roll-edit'),
    path('rolls/<int:pk>/assign/', views.RollAssignView.as_view(),      name='roll-assign'),

    # Cloth Types
    path('cloth-types/',                  views.ClothTypeListView.as_view(),    name='cloth-type-list'),
    path('cloth-types/add/',              views.ClothTypeCreateView.as_view(),  name='cloth-type-create'),
    path('cloth-types/<int:pk>/edit/',    views.ClothTypeUpdateView.as_view(),  name='cloth-type-update'),
    path('cloth-types/<int:pk>/archive/', views.ClothTypeArchiveView.as_view(), name='cloth-type-archive'),
    path('cloth-types/<int:pk>/delete/',  views.ClothTypeDeleteView.as_view(),  name='cloth-type-delete'),

    # Cloth Colors
    path('cloth-colors/',                  views.ClothColorListView.as_view(),    name='cloth-color-list'),
    path('cloth-colors/add/',              views.ClothColorCreateView.as_view(),  name='cloth-color-create'),
    path('cloth-colors/<int:pk>/edit/',    views.ClothColorUpdateView.as_view(),  name='cloth-color-update'),
    path('cloth-colors/<int:pk>/archive/', views.ClothColorArchiveView.as_view(), name='cloth-color-archive'),
    path('cloth-colors/<int:pk>/delete/',  views.ClothColorDeleteView.as_view(),  name='cloth-color-delete'),

    # Storage Locations
    path('storage-locations/',                  views.StorageLocationListView.as_view(),    name='storage-list'),
    path('storage-locations/add/',              views.StorageLocationCreateView.as_view(),  name='storage-create'),
    path('storage-locations/<int:pk>/edit/',    views.StorageLocationUpdateView.as_view(),  name='storage-update'),
    path('storage-locations/<int:pk>/archive/', views.StorageLocationArchiveView.as_view(), name='storage-archive'),
    path('storage-locations/<int:pk>/delete/',  views.StorageLocationDeleteView.as_view(),  name='storage-delete'),
]
