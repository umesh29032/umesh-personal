"""Vendor, VendorDispatch, Payment CRUD."""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from ..forms import PaymentForm, VendorDispatchForm, VendorForm
from ..models import Payment, Vendor, VendorDispatch
from ..services import DispatchService, PaymentService, VendorService, user_has_role, ROLE_SUPER_ADMIN
from .mixins import ManagerOrAdminMixin


# ── Vendor ─────────────────────────────────────────────────────────────────

class VendorListView(LoginRequiredMixin, ManagerOrAdminMixin, ListView):
    model = Vendor
    template_name = 'inventory/vendor_list.html'
    context_object_name = 'vendors'
    ordering = ['name']


class VendorCreateView(LoginRequiredMixin, ManagerOrAdminMixin, CreateView):
    model = Vendor
    form_class = VendorForm
    template_name = 'inventory/vendor_form.html'
    success_url = reverse_lazy('inventory:vendor_list')

    def form_valid(self, form):
        VendorService.create(form.cleaned_data)
        messages.success(self.request, f"Vendor '{form.cleaned_data['name']}' added.")
        return redirect(self.success_url)


class VendorUpdateView(LoginRequiredMixin, ManagerOrAdminMixin, UpdateView):
    model = Vendor
    form_class = VendorForm
    template_name = 'inventory/vendor_form.html'
    success_url = reverse_lazy('inventory:vendor_list')


class VendorDeleteView(LoginRequiredMixin, ManagerOrAdminMixin, DeleteView):
    model = Vendor
    template_name = 'inventory/vendor_confirm_delete.html'
    success_url = reverse_lazy('inventory:vendor_list')


# ── Dispatch ───────────────────────────────────────────────────────────────

class DispatchListView(LoginRequiredMixin, ManagerOrAdminMixin, ListView):
    model = VendorDispatch
    template_name = 'inventory/dispatch_list.html'
    context_object_name = 'dispatches'
    paginate_by = 25

    def get_queryset(self):
        return (
            super().get_queryset()
            .select_related('batch', 'vendor', 'batch_stage__stage')
            .order_by('-created_at')
        )


class DispatchCreateView(LoginRequiredMixin, ManagerOrAdminMixin, CreateView):
    model = VendorDispatch
    form_class = VendorDispatchForm
    template_name = 'inventory/dispatch_form.html'
    success_url = reverse_lazy('inventory:dispatch_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class DispatchUpdateView(LoginRequiredMixin, ManagerOrAdminMixin, UpdateView):
    model = VendorDispatch
    form_class = VendorDispatchForm
    template_name = 'inventory/dispatch_form.html'
    success_url = reverse_lazy('inventory:dispatch_list')


class DispatchDeleteView(LoginRequiredMixin, ManagerOrAdminMixin, DeleteView):
    model = VendorDispatch
    template_name = 'inventory/dispatch_confirm_delete.html'
    success_url = reverse_lazy('inventory:dispatch_list')


# ── Payment (Super Admin only) ─────────────────────────────────────────────

class SuperAdminOnlyMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser or user_has_role(self.request.user, [ROLE_SUPER_ADMIN])


class PaymentListView(LoginRequiredMixin, SuperAdminOnlyMixin, ListView):
    model = Payment
    template_name = 'inventory/payment_list.html'
    context_object_name = 'payments'
    paginate_by = 25

    def get_queryset(self):
        return super().get_queryset().select_related('batch', 'vendor', 'dispatch').order_by('-created_at')


class PaymentCreateView(LoginRequiredMixin, SuperAdminOnlyMixin, CreateView):
    model = Payment
    form_class = PaymentForm
    template_name = 'inventory/payment_form.html'
    success_url = reverse_lazy('inventory:payment_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class PaymentUpdateView(LoginRequiredMixin, SuperAdminOnlyMixin, UpdateView):
    model = Payment
    form_class = PaymentForm
    template_name = 'inventory/payment_form.html'
    success_url = reverse_lazy('inventory:payment_list')


class PaymentDeleteView(LoginRequiredMixin, SuperAdminOnlyMixin, DeleteView):
    model = Payment
    template_name = 'inventory/payment_confirm_delete.html'
    success_url = reverse_lazy('inventory:payment_list')
