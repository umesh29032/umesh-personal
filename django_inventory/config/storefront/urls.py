"""
Storefront URL configuration.

Public:
  /          → public_home  (mounted at root by config/urls.py)

Backend (authenticated, listing_team role):
  /storefront/products/              → ProductListView
  /storefront/products/add/          → ProductCreateView
  /storefront/products/<pk>/edit/    → ProductUpdateView
  /storefront/products/<pk>/delete/  → ProductDeleteView
  /storefront/categories/            → CategoryListView
  /storefront/categories/add/        → CategoryCreateView
  /storefront/categories/<pk>/edit/  → CategoryUpdateView
  /storefront/categories/<pk>/delete/→ CategoryDeleteView
"""
from django.urls import path
from .views import (
    ProductListView, ProductCreateView, ProductUpdateView, ProductDeleteView,
    CategoryListView, CategoryCreateView, CategoryUpdateView, CategoryDeleteView,
)

app_name = 'storefront'

urlpatterns = [
    # ── Featured Products ─────────────────────────────────────────────────────
    path('products/', ProductListView.as_view(), name='product_list'),
    path('products/add/', ProductCreateView.as_view(), name='product_add'),
    path('products/<int:pk>/edit/', ProductUpdateView.as_view(), name='product_edit'),
    path('products/<int:pk>/delete/', ProductDeleteView.as_view(), name='product_delete'),

    # ── Categories ────────────────────────────────────────────────────────────
    path('categories/', CategoryListView.as_view(), name='category_list'),
    path('categories/add/', CategoryCreateView.as_view(), name='category_add'),
    path('categories/<int:pk>/edit/', CategoryUpdateView.as_view(), name='category_edit'),
    path('categories/<int:pk>/delete/', CategoryDeleteView.as_view(), name='category_delete'),
]
