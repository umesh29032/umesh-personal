"""Inventory URLConf — dashboards + Access Control surfaces (mounted at /inventory/).

Route groups / workflows:
  dashboard/           role-aware home (worker: active stages + report badges;
                       management: ops summary)
  access-control/…     the Super-Admin hub: roles, skills, per-user access
  sidebar-access/…     menu+URL gating rules (SidebarItemRule editor)
The /tracking/ section lives in inventory/tracking_urls.py (P4.2 ownership)."""
from django.contrib.auth.decorators import login_required
from django.urls import path
from django.views.generic import TemplateView

from . import views

app_name = 'inventory'

urlpatterns = [
    # Dashboards — ONE live page (F-1 polish 2026-07-05). `my_dashboard` is the
    # canonical url_name (fresh name = no legacy SidebarItemRule row, so the
    # single menu item renders for every role). The two historical url_names are
    # kept as permanent redirects for old bookmarks; middleware exempts all three.
    path('my-dashboard/', views.user_dashboard, name='my_dashboard'),
    path('dashboard/', views.dashboard_redirect, name='inventory_dashboard'),
    path('my-dashboard/legacy/', views.dashboard_redirect, name='user_dashboard'),

    # Design-system styleguide — living component gallery (login-only; no business logic).
    # TemplateView (Django generic) renders a static template; no SidebarItemRule = open to any authed user.
    path('styleguide/', login_required(
        TemplateView.as_view(template_name='inventory/styleguide.html')), name='styleguide'),

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
