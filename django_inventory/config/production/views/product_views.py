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
from django.views.generic import CreateView, ListView, UpdateView, View

from production.forms import ProductForm
from production.models import Product
from production.services import create_product, update_product, archive_product

from .mixins import SuperAdminOnlyMixin, ProductionRoleMixin


class ProductListView(LoginRequiredMixin, ProductionRoleMixin, ListView):
    template_name = 'production/product_list.html'
    model = Product
    context_object_name = 'products'

    def get_queryset(self):
        return Product.objects.all().order_by('name')


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
