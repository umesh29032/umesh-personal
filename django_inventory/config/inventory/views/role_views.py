"""Role CRUD — Super Admin only."""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from ..forms import RoleForm
from ..models import Role
from ..services import permissions_qs_by_app
from .mixins import SuperAdminOnlyMixin


class RoleListView(LoginRequiredMixin, SuperAdminOnlyMixin, ListView):
    model = Role
    template_name = 'inventory/role_list.html'
    context_object_name = 'roles'
    ordering = ['name']

    def get_queryset(self):
        return super().get_queryset().prefetch_related('permissions', 'users')


class RoleCreateView(LoginRequiredMixin, SuperAdminOnlyMixin, CreateView):
    model = Role
    form_class = RoleForm
    template_name = 'inventory/role_form.html'
    success_url = reverse_lazy('inventory:role_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['grouped_permissions'] = _group_permissions(permissions_qs_by_app())
        return ctx


class RoleUpdateView(LoginRequiredMixin, SuperAdminOnlyMixin, UpdateView):
    model = Role
    form_class = RoleForm
    template_name = 'inventory/role_form.html'
    success_url = reverse_lazy('inventory:role_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['grouped_permissions'] = _group_permissions(permissions_qs_by_app())
        return ctx


class RoleDeleteView(LoginRequiredMixin, SuperAdminOnlyMixin, DeleteView):
    model = Role
    template_name = 'inventory/role_confirm_delete.html'
    success_url = reverse_lazy('inventory:role_list')

    def form_valid(self, form):
        if self.object.is_system:
            messages.error(self.request, f"Cannot delete system role '{self.object.name}'.")
            return redirect('inventory:role_list')
        if self.object.users.exists():
            messages.error(self.request, f"'{self.object.name}' is still assigned to users. Reassign them first.")
            return redirect('inventory:role_list')
        return super().form_valid(form)


def _group_permissions(qs):
    """Group permissions by app + model for a cleaner checkbox layout in the form."""
    groups: dict[str, list] = {}
    for perm in qs:
        key = f"{perm.content_type.app_label} · {perm.content_type.model}"
        groups.setdefault(key, []).append(perm)
    return sorted(groups.items())
