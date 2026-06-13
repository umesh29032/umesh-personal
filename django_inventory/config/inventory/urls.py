"""Inventory URLConf — dashboards + Access Control surfaces (mounted at /inventory/).

Route groups / workflows:
  dashboard/           role-aware home (worker: active stages + report badges;
                       management: ops summary)
  access-control/…     the Super-Admin hub: roles, skills, per-user access
  sidebar-access/…     menu+URL gating rules (SidebarItemRule editor)
The /tracking/ section lives in inventory/tracking_urls.py (P4.2 ownership)."""
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

    # Sidebar Access Control (Super Admin only) — edits SidebarItemRule rows.
    path('sidebar-access/', views.SidebarAccessListView.as_view(), name='sidebar-access'),

    # Access Control hub (Super Admin only) — read-only RBAC overview matrices.
    path('access/', views.AccessControlHubView.as_view(), name='access-control'),
]
