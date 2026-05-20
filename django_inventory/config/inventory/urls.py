from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    # Dashboards
    path('dashboard/', views.dashboard, name='inventory_dashboard'),
    path('my-dashboard/', views.user_dashboard, name='user_dashboard'),

    # Roles & Permissions (Super Admin only)
    path('roles/', views.RoleListView.as_view(), name='role_list'),
    path('roles/add/', views.RoleCreateView.as_view(), name='role_add'),
    path('roles/<int:pk>/edit/', views.RoleUpdateView.as_view(), name='role_edit'),
    path('roles/<int:pk>/delete/', views.RoleDeleteView.as_view(), name='role_delete'),
]
