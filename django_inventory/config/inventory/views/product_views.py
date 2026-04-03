from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView

from ..models import Product
from ..forms import ProductForm
from ..services import ProductService
from .mixins import ManagerOrAdminMixin


class ProductListView(LoginRequiredMixin, ListView):
    model = Product
    template_name = "inventory/product_list.html"
    context_object_name = "products"
    paginate_by = 10
    ordering = ['-created_at']

    def get_queryset(self):
        qs = super().get_queryset().select_related('batch', 'location')
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(sku__icontains=q) | Q(category__icontains=q))
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        return context


class ProductDetailView(LoginRequiredMixin, DetailView):
    model = Product
    template_name = "inventory/product_detail.html"
    context_object_name = "product"


class ProductCreateView(LoginRequiredMixin, ManagerOrAdminMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = "inventory/product_form.html"
    success_url = reverse_lazy('inventory:product_list')

    def form_valid(self, form):
        # Use ProductService so ledger entry is created atomically
        ProductService.create_product(form.cleaned_data, created_by=self.request.user)
        messages.success(self.request, "Product created and logged in stock ledger.")
        return redirect(self.success_url)


class ProductUpdateView(LoginRequiredMixin, ManagerOrAdminMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = "inventory/product_form.html"
    success_url = reverse_lazy('inventory:product_list')


class ProductDeleteView(LoginRequiredMixin, ManagerOrAdminMixin, DeleteView):
    model = Product
    template_name = "inventory/product_confirm_delete.html"
    success_url = reverse_lazy('inventory:product_list')
