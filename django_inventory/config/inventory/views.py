from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Product

class ProductListView(LoginRequiredMixin, ListView):
    model = Product
    template_name = "inventory/product_list.html"
    context_object_name = "products"
    paginate_by = 10
    ordering = ['-created_at']
