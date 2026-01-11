from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('dashboard/', views.dashboard, name='inventory_dashboard'),
    path('products/', views.ProductListView.as_view(), name='product_list'),
    
    # Cloth Roll CRUD
    path('cloth/list/', views.ClothRollListView.as_view(), name='cloth_roll_list'),
    path('cloth/add/', views.ClothRollCreateView.as_view(), name='cloth_roll_add'),
    path('cloth/edit/<int:pk>/', views.ClothRollUpdateView.as_view(), name='cloth_roll_edit'),
    path('cloth/delete/<int:pk>/', views.ClothRollDeleteView.as_view(), name='cloth_roll_delete'),

    # Batch CRUD
    path('batches/list/', views.BatchListView.as_view(), name='batch_list'),
    path('batches/add/', views.BatchCreateView.as_view(), name='batch_add'),
    path('batches/edit/<int:pk>/', views.BatchUpdateView.as_view(), name='batch_edit'),
    path('batches/delete/<int:pk>/', views.BatchDeleteView.as_view(), name='batch_delete'),
]
