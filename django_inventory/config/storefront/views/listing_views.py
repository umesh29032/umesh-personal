"""
Authenticated backend views for managing storefront product and category listings.

Access is gated to listing_team role (or Super Admin). These views replace the
Django admin for day-to-day listing management — polished UI, RBAC-controlled.

Pattern mirrors inventory CBVs: LoginRequiredMixin + role mixin + generic CBV.
Service layer handles all writes (CLAUDE.md rule #4).
"""
from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView, DeleteView, ListView, UpdateView,
)

from ..models import Category, FeaturedProduct
from ..forms import CategoryForm, FeaturedProductForm
from ..services import ListingService
from inventory.services import user_has_role, ROLE_SUPER_ADMIN, ROLE_LISTING_TEAM


class ListingTeamMixin(UserPassesTestMixin):
    """Gate storefront write views to listing_team role and Super Admin."""
    def test_func(self):
        return user_has_role(self.request.user, {ROLE_SUPER_ADMIN, ROLE_LISTING_TEAM})


# ── FeaturedProduct ───────────────────────────────────────────────────────────

class ProductListView(LoginRequiredMixin, ListingTeamMixin, ListView):
    """List all featured products with badge/status server-filter; DataTables handles text search."""
    model = FeaturedProduct
    template_name = 'storefront/listing/product_list.html'
    context_object_name = 'products'
    # paginate_by hata diya — DataTables client-side pagination handle karega

    def get_queryset(self):
        qs = super().get_queryset().select_related('category')
        badge = self.request.GET.get('badge', '').strip()
        active = self.request.GET.get('active', '').strip()
        if badge:
            qs = qs.filter(badge=badge)
        if active in ('1', '0'):
            qs = qs.filter(is_active=(active == '1'))
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['filter_badge'] = self.request.GET.get('badge', '')
        ctx['filter_active'] = self.request.GET.get('active', '')
        ctx['badge_choices'] = FeaturedProduct.BADGE_CHOICES
        # KPI counts — template mein stats cards ke liye
        ctx['total_count'] = FeaturedProduct.objects.count()
        ctx['active_count'] = FeaturedProduct.objects.filter(is_active=True).count()
        ctx['hidden_count'] = FeaturedProduct.objects.filter(is_active=False).count()
        return ctx


class ProductCreateView(LoginRequiredMixin, ListingTeamMixin, CreateView):
    model = FeaturedProduct
    form_class = FeaturedProductForm
    template_name = 'storefront/listing/product_form.html'
    success_url = reverse_lazy('storefront:product_list')

    def form_valid(self, form):
        # FeaturedProductForm.save() runs Pillow image processing — call via super().
        response = super().form_valid(form)
        messages.success(self.request, f'Product "{self.object.name}" created.')
        return response

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['action'] = 'Create'
        ctx['categories'] = Category.objects.filter(is_active=True).order_by('name')
        return ctx


class ProductUpdateView(LoginRequiredMixin, ListingTeamMixin, UpdateView):
    model = FeaturedProduct
    form_class = FeaturedProductForm
    template_name = 'storefront/listing/product_form.html'
    success_url = reverse_lazy('storefront:product_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Product "{self.object.name}" updated.')
        return response

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['action'] = 'Edit'
        ctx['categories'] = Category.objects.filter(is_active=True).order_by('name')
        return ctx


class ProductDeleteView(LoginRequiredMixin, ListingTeamMixin, DeleteView):
    model = FeaturedProduct
    template_name = 'storefront/listing/product_confirm_delete.html'
    success_url = reverse_lazy('storefront:product_list')

    def form_valid(self, form):
        name = self.object.name
        ListingService.delete_product(self.object)
        messages.success(self.request, f'Product "{name}" deleted.')
        return redirect(self.success_url)


# ── Category ──────────────────────────────────────────────────────────────────

class CategoryListView(LoginRequiredMixin, ListingTeamMixin, ListView):
    model = Category
    template_name = 'storefront/listing/category_list.html'
    context_object_name = 'categories'
    # paginate_by hata diya — DataTables client-side pagination handle karega

    def get_queryset(self):
        qs = super().get_queryset()
        active = self.request.GET.get('active', '').strip()
        if active in ('1', '0'):
            qs = qs.filter(is_active=(active == '1'))
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['filter_active'] = self.request.GET.get('active', '')
        # KPI counts — template mein stats cards ke liye
        ctx['total_count'] = Category.objects.count()
        ctx['active_count'] = Category.objects.filter(is_active=True).count()
        ctx['hidden_count'] = Category.objects.filter(is_active=False).count()
        return ctx


class CategoryCreateView(LoginRequiredMixin, ListingTeamMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'storefront/listing/category_form.html'
    success_url = reverse_lazy('storefront:category_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Category "{self.object.name}" created.')
        return response

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['action'] = 'Create'
        return ctx


class CategoryUpdateView(LoginRequiredMixin, ListingTeamMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = 'storefront/listing/category_form.html'
    success_url = reverse_lazy('storefront:category_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Category "{self.object.name}" updated.')
        return response

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['action'] = 'Edit'
        return ctx


class CategoryDeleteView(LoginRequiredMixin, ListingTeamMixin, DeleteView):
    model = Category
    template_name = 'storefront/listing/category_confirm_delete.html'
    success_url = reverse_lazy('storefront:category_list')

    def form_valid(self, form):
        name = self.object.name
        ListingService.delete_category(self.object)
        messages.success(self.request, f'Category "{name}" deleted.')
        return redirect(self.success_url)
