from django.shortcuts import render
from django.db.models import Sum, Count, F
from .models import ClothRoll, Product, Batch, StockLedger, TransactionType

def dashboard(request):
    """
    Inventory Dashboard with High-level KPIs and summaries.
    """
    # KPI 1: Total Cloth Stock (Meters)
    total_cloth_length = ClothRoll.objects.exclude(status='EXHAUSTED').aggregate(
        total=Sum('remaining_length')
    )['total'] or 0

    # KPI 2: Total Finished Products
    total_products = Product.objects.aggregate(
        total=Sum('quantity')
    )['total'] or 0

    # KPI 3: Active Batches
    active_batches = Batch.objects.filter(status='WIP').count()
    
    # KPI 4: Wastage (Total from Consumed assignments)
    # We can calculate this from BatchClothAssignment or Ledger
    # Using Ledger for "Wastage" type reference if we tracked it explicitly as a separate txn
    # Or just Sum wastage_length from BatchClothAssignment
    from .models import BatchClothAssignment
    total_wastage = BatchClothAssignment.objects.aggregate(
        total=Sum('wastage_length')
    )['total'] or 0

    # Section: Stock by Cloth Type
    cloth_stock_by_type = ClothRoll.objects.values('cloth_type').annotate(
        total_length=Sum('remaining_length'),
        roll_count=Count('id')
    ).order_by('-total_length')

    # Section: Recent Movements (Ledger)
    recent_movements = StockLedger.objects.all().select_related('from_stage', 'to_stage', 'batch')[:10]

    context = {
        'total_cloth_length': total_cloth_length,
        'total_products': total_products,
        'active_batches': active_batches,
        'total_wastage': total_wastage,
        'cloth_stock_by_type': cloth_stock_by_type,
        'recent_movements': recent_movements,
    }
    return render(request, 'inventory/dashboard.html', context)

from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin

class ProductListView(LoginRequiredMixin, ListView):
    model = Product
    template_name = "inventory/product_list.html"
    context_object_name = "products"
    paginate_by = 10
    ordering = ['-created_at']


from django.views.generic import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import ClothRoll
from .forms import ClothRollForm

class ClothRollListView(LoginRequiredMixin, ListView):
    model = ClothRoll
    template_name = "inventory/clothroll_list.html"
    context_object_name = "cloth_rolls"
    paginate_by = 10
    ordering = ['-created_at']

class ClothRollCreateView(LoginRequiredMixin, CreateView):
    model = ClothRoll
    form_class = ClothRollForm
    template_name = "inventory/clothroll_form.html"
    success_url = reverse_lazy('inventory:cloth_roll_list')

class ClothRollUpdateView(LoginRequiredMixin, UpdateView):
    model = ClothRoll
    form_class = ClothRollForm
    template_name = "inventory/clothroll_form.html"
    success_url = reverse_lazy('inventory:cloth_roll_list')

class ClothRollDeleteView(LoginRequiredMixin, DeleteView):
    model = ClothRoll
    template_name = "inventory/clothroll_confirm_delete.html"
    success_url = reverse_lazy('inventory:cloth_roll_list')

# -----------------------------------------------------------------------------
# BATCH CRUD
# -----------------------------------------------------------------------------
from .models import Batch

class BatchListView(LoginRequiredMixin, ListView):
    model = Batch
    template_name = "inventory/batch_list.html"
    context_object_name = "batches"
    paginate_by = 10
    ordering = ['-created_at']

class BatchCreateView(LoginRequiredMixin, CreateView):
    model = Batch
    fields = ['batch_number', 'name', 'current_stage', 'status']
    template_name = "inventory/batch_form.html"
    success_url = reverse_lazy('inventory:batch_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

class BatchUpdateView(LoginRequiredMixin, UpdateView):
    model = Batch
    fields = ['batch_number', 'name', 'current_stage', 'status']
    template_name = "inventory/batch_form.html"
    success_url = reverse_lazy('inventory:batch_list')

class BatchDeleteView(LoginRequiredMixin, DeleteView):
    model = Batch
    template_name = "inventory/batch_confirm_delete.html"
    success_url = reverse_lazy('inventory:batch_list')
