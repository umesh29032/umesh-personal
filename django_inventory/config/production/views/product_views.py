"""Product CRUD views — Sirf Super Admin allowed.

YEH FILE KYU HAI?
─────────────────
Product create/edit/archive views. SuperAdminOnlyMixin se gate hote hain —
warna naya product banane se Adda codes ki structure unstable ho sakti hai.
Services pe delegate karte hain (CLAUDE.md rule #4).
"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, TemplateView, UpdateView, View

from accounts.services import ROLE_SUPER_ADMIN, user_has_role
from production.forms import ProductForm
from production.models import Product
from production.services import (
    add_product_size, archive_product, archive_product_size, create_product,
    reactivate_product_size, update_product, update_product_size,
)

from .mixins import SuperAdminOnlyMixin, ManagementRoleMixin


class ProductListView(LoginRequiredMixin, ManagementRoleMixin, ListView):
    template_name = 'production/product_list.html'
    model = Product
    context_object_name = 'products'

    def get_queryset(self):
        return Product.objects.all().order_by('name')

    def get_context_data(self, **kwargs):
        # Pre-compute add-product permission so template avoids raw is_superuser
        # check (CLAUDE.md rule 6). Only Super Admin can create new products.
        ctx = super().get_context_data(**kwargs)
        ctx['can_add_product'] = user_has_role(self.request.user, {ROLE_SUPER_ADMIN})
        return ctx


class ProductCreateView(LoginRequiredMixin, SuperAdminOnlyMixin, CreateView):
    template_name = 'production/product_form.html'
    form_class = ProductForm
    success_url = reverse_lazy('production:product-list')

    def form_valid(self, form):
        try:
            p = create_product(
                user=self.request.user,
                code=form.cleaned_data['code'],
                name=form.cleaned_data['name'],
                description=form.cleaned_data.get('description', ''),
            )
        except ValidationError as exc:
            form.add_error(None, str(exc))
            return self.form_invalid(form)
        messages.success(self.request, f"Product {p.code} created.")
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['is_edit'] = False
        return ctx


class ProductUpdateView(LoginRequiredMixin, SuperAdminOnlyMixin, UpdateView):
    template_name = 'production/product_form.html'
    form_class = ProductForm
    model = Product
    success_url = reverse_lazy('production:product-list')

    def form_valid(self, form):
        update_product(
            user=self.request.user,
            product=self.object,
            name=form.cleaned_data['name'],
            description=form.cleaned_data.get('description', ''),
        )
        messages.success(self.request, f"Product {self.object.code} updated.")
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['is_edit'] = True
        return ctx


class ProductArchiveView(LoginRequiredMixin, SuperAdminOnlyMixin, View):
    """POST-only archive endpoint."""

    def get(self, request, pk):
        from django.shortcuts import render
        obj = Product.objects.get(pk=pk)
        return render(request, 'production/product_confirm_archive.html', {'object': obj})

    def post(self, request, pk):
        obj = Product.objects.get(pk=pk)
        archive_product(request.user, obj)
        messages.success(request, f"Product {obj.code} archived.")
        return redirect('production:product-list')


class ProductSizesEditView(LoginRequiredMixin, SuperAdminOnlyMixin, TemplateView):
    """Per-product size chart editor (PR5 2026-05-28).

    URL: /production/products/<pk>/sizes/

    Mirror of `ProductPatternsEditView`. Single POST endpoint with hidden
    `action` field:
      • action=add       → new ProductSize row banao
      • action=remove    → soft-archive (set is_active=False) row
      • action=update    → label / display_order update
      • action=reactivate → archived size ko phir se active
    """

    template_name = 'production/product_sizes_edit.html'

    def get_product(self):
        return Product.objects.get(pk=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        product = self.get_product()
        ctx['product'] = product
        ctx['active_sizes'] = product.sizes.filter(is_active=True).order_by(
            'display_order', 'code',
        )
        ctx['archived_sizes'] = product.sizes.filter(is_active=False).order_by(
            'display_order', 'code',
        )
        return ctx

    def post(self, request, pk):
        product = self.get_product()
        action = request.POST.get('action', '')

        # Service-layer dispatch — har action ek atomic service call.
        # ValidationError ko user-friendly message banake redirect.
        try:
            order = int(request.POST.get('display_order') or 0)
        except (TypeError, ValueError):
            order = 0

        try:
            if action == 'add':
                size = add_product_size(
                    request.user, product=product,
                    code=request.POST.get('code') or '',
                    label=request.POST.get('label') or '',
                    display_order=order,
                )
                messages.success(request, f"Size {size.code.upper()} added.")
            elif action == 'update':
                update_product_size(
                    request.user, product=product,
                    size_id=int(request.POST.get('size_id') or 0),
                    label=request.POST.get('label') or '',
                    display_order=order,
                )
                messages.success(request, "Size updated.")
            elif action == 'archive':
                archive_product_size(
                    request.user, product=product,
                    size_id=int(request.POST.get('size_id') or 0),
                )
                messages.success(request, "Size archived.")
            elif action == 'reactivate':
                reactivate_product_size(
                    request.user, product=product,
                    size_id=int(request.POST.get('size_id') or 0),
                )
                messages.success(request, "Size reactivated.")
        except ValidationError as exc:
            msg = getattr(exc, 'messages', None)
            messages.error(request, ' '.join(msg) if msg else str(exc))
        except (TypeError, ValueError):
            messages.error(request, "Invalid size id.")

        return redirect('production:product-sizes', pk=pk)
