from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum, Count, Q
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError

from .models import (
    ClothRoll, Product, Batch, StockLedger, BatchClothAssignment,
    BatchUserAssignment, BatchOperation, Stage, Machine
)
from .forms import (
    ClothRollForm, BatchClothAssignmentForm, BatchUserAssignmentForm,
    BatchOperationForm, ProductForm, StageForm, MachineForm
)
from .constants import ClothType, BatchStatus
from .services.batch_service import BatchService


# =============================================================================
# PERMISSION MIXINS
# =============================================================================

class ManagerOrSuperuserMixin(UserPassesTestMixin):
    """Allow only managers and superusers."""
    def test_func(self):
        u = self.request.user
        return u.is_superuser or getattr(u, 'user_type', None) in ('admin', 'manager')


# =============================================================================
# DASHBOARD
# =============================================================================

@login_required
def dashboard(request):
    """
    Inventory Dashboard with High-level KPIs and summaries.
    """
    total_cloth_length = ClothRoll.objects.exclude(status='EXHAUSTED').aggregate(
        total=Sum('remaining_length')
    )['total'] or 0

    total_products = Product.objects.aggregate(
        total=Sum('quantity')
    )['total'] or 0

    active_batches = Batch.objects.filter(status='WIP').count()

    total_wastage = BatchClothAssignment.objects.aggregate(
        total=Sum('wastage_length')
    )['total'] or 0

    cloth_stock_by_type = ClothRoll.objects.values('cloth_type').annotate(
        total_length=Sum('remaining_length'),
        roll_count=Count('id')
    ).order_by('-total_length')

    recent_movements = StockLedger.objects.all().select_related('from_stage', 'to_stage', 'batch')[:10]

    total_cloth_rolls = ClothRoll.objects.count()
    total_stages = Stage.objects.filter(is_active=True).count()

    context = {
        'total_cloth_length': total_cloth_length,
        'total_products': total_products,
        'active_batches': active_batches,
        'total_wastage': total_wastage,
        'cloth_stock_by_type': cloth_stock_by_type,
        'recent_movements': recent_movements,
        'total_cloth_rolls': total_cloth_rolls,
        'total_stages': total_stages,
    }
    return render(request, 'inventory/dashboard.html', context)


# =============================================================================
# PRODUCT CRUD
# =============================================================================

class ProductListView(LoginRequiredMixin, ListView):
    model = Product
    template_name = "inventory/product_list.html"
    context_object_name = "products"
    paginate_by = 10
    ordering = ['-created_at']

    def get_queryset(self):
        qs = super().get_queryset()
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


class ProductCreateView(LoginRequiredMixin, ManagerOrSuperuserMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = "inventory/product_form.html"
    success_url = reverse_lazy('inventory:product_list')


class ProductUpdateView(LoginRequiredMixin, ManagerOrSuperuserMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = "inventory/product_form.html"
    success_url = reverse_lazy('inventory:product_list')


class ProductDeleteView(LoginRequiredMixin, ManagerOrSuperuserMixin, DeleteView):
    model = Product
    template_name = "inventory/product_confirm_delete.html"
    success_url = reverse_lazy('inventory:product_list')


# =============================================================================
# CLOTH ROLL CRUD
# =============================================================================

class ClothRollListView(LoginRequiredMixin, ListView):
    model = ClothRoll
    template_name = "inventory/clothroll_list.html"
    context_object_name = "cloth_rolls"
    paginate_by = 10
    ordering = ['-created_at']

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get('q', '').strip()
        status = self.request.GET.get('status', '')
        cloth_type = self.request.GET.get('cloth_type', '')
        if q:
            qs = qs.filter(Q(roll_number__icontains=q) | Q(supplier__icontains=q))
        if status:
            qs = qs.filter(status=status)
        if cloth_type:
            qs = qs.filter(cloth_type=cloth_type)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        context['selected_status'] = self.request.GET.get('status', '')
        context['selected_type'] = self.request.GET.get('cloth_type', '')
        context['status_choices'] = [
            ('AVAILABLE', 'Available'),
            ('PARTIALLY_USED', 'Partially Used'),
            ('EXHAUSTED', 'Exhausted'),
        ]
        context['type_choices'] = ClothType.choices
        return context


class ClothRollCreateView(LoginRequiredMixin, ManagerOrSuperuserMixin, CreateView):
    model = ClothRoll
    form_class = ClothRollForm
    template_name = "inventory/clothroll_form.html"
    success_url = reverse_lazy('inventory:cloth_roll_list')


class ClothRollUpdateView(LoginRequiredMixin, ManagerOrSuperuserMixin, UpdateView):
    model = ClothRoll
    form_class = ClothRollForm
    template_name = "inventory/clothroll_form.html"
    success_url = reverse_lazy('inventory:cloth_roll_list')


class ClothRollDeleteView(LoginRequiredMixin, ManagerOrSuperuserMixin, DeleteView):
    model = ClothRoll
    template_name = "inventory/clothroll_confirm_delete.html"
    success_url = reverse_lazy('inventory:cloth_roll_list')


# =============================================================================
# BATCH CRUD
# =============================================================================

class BatchListView(LoginRequiredMixin, ListView):
    model = Batch
    template_name = "inventory/batch_list.html"
    context_object_name = "batches"
    paginate_by = 10
    ordering = ['-created_at']

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get('q', '').strip()
        status = self.request.GET.get('status', '')
        if q:
            qs = qs.filter(Q(batch_number__icontains=q) | Q(name__icontains=q))
        if status:
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        context['selected_status'] = self.request.GET.get('status', '')
        context['status_choices'] = BatchStatus.choices
        return context


class BatchCreateView(LoginRequiredMixin, ManagerOrSuperuserMixin, CreateView):
    model = Batch
    fields = ['batch_number', 'name', 'current_stage', 'status']
    template_name = "inventory/batch_form.html"
    success_url = reverse_lazy('inventory:batch_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class BatchUpdateView(LoginRequiredMixin, ManagerOrSuperuserMixin, UpdateView):
    model = Batch
    fields = ['batch_number', 'name', 'current_stage', 'status']
    template_name = "inventory/batch_form.html"
    success_url = reverse_lazy('inventory:batch_list')


class BatchDeleteView(LoginRequiredMixin, ManagerOrSuperuserMixin, DeleteView):
    model = Batch
    template_name = "inventory/batch_confirm_delete.html"
    success_url = reverse_lazy('inventory:batch_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        batch = self.object
        context['cloth_count'] = batch.cloth_assignments.count()
        context['worker_count'] = batch.user_assignments.count()
        context['operation_count'] = batch.operations.count()
        context['product_count'] = batch.products.count()
        return context


class BatchDetailView(LoginRequiredMixin, DetailView):
    model = Batch
    template_name = "inventory/batch_detail.html"
    context_object_name = "batch"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        batch = self.object
        context['cloth_assignments'] = batch.cloth_assignments.select_related('cloth_roll').order_by('-assigned_at')
        context['user_assignments'] = batch.user_assignments.select_related('user').filter(is_active=True).order_by('-assigned_at')
        context['operations'] = batch.operations.select_related('stage', 'user', 'machine').order_by('-start_time')
        context['products'] = batch.products.all().order_by('-created_at')
        agg = batch.cloth_assignments.aggregate(
            total_reserved=Sum('reserved_length'),
            total_consumed=Sum('consumed_length'),
            total_wastage=Sum('wastage_length'),
        )
        context['total_reserved'] = agg['total_reserved'] or 0
        context['total_consumed'] = agg['total_consumed'] or 0
        context['total_wastage'] = agg['total_wastage'] or 0
        context['can_manage'] = (
            self.request.user.is_superuser
            or getattr(self.request.user, 'user_type', None) in ('admin', 'manager')
        )
        # Allowed status transitions for action buttons
        _transitions = {
            BatchStatus.PLANNED: [BatchStatus.WIP, BatchStatus.CANCELLED],
            BatchStatus.WIP: [BatchStatus.COMPLETED, BatchStatus.CANCELLED],
        }
        context['allowed_transitions'] = _transitions.get(batch.status, [])
        return context


# =============================================================================
# BATCH STATUS TRANSITION
# =============================================================================

class BatchTransitionView(LoginRequiredMixin, ManagerOrSuperuserMixin, View):
    """POST-only view to transition a batch to a new status."""

    def post(self, request, pk):
        batch = get_object_or_404(Batch, pk=pk)
        new_status = request.POST.get('new_status', '')
        try:
            BatchService.transition_status(batch, new_status)
            label = dict(BatchStatus.choices).get(new_status, new_status)
            messages.success(request, f"Batch {batch.batch_number} moved to '{label}'.")
        except ValidationError as e:
            messages.error(request, str(e.message))
        return redirect('inventory:batch_detail', pk=pk)


# =============================================================================
# BATCH CLOTH ASSIGNMENT CRUD
# =============================================================================

class BatchClothAssignmentCreateView(LoginRequiredMixin, ManagerOrSuperuserMixin, CreateView):
    model = BatchClothAssignment
    form_class = BatchClothAssignmentForm
    template_name = "inventory/batch_cloth_assignment_form.html"

    def get_batch(self):
        return get_object_or_404(Batch, pk=self.kwargs['batch_pk'])

    def form_valid(self, form):
        form.instance.batch = self.get_batch()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('inventory:batch_detail', kwargs={'pk': self.kwargs['batch_pk']})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['batch'] = self.get_batch()
        return context


class BatchClothAssignmentUpdateView(LoginRequiredMixin, ManagerOrSuperuserMixin, UpdateView):
    model = BatchClothAssignment
    form_class = BatchClothAssignmentForm
    template_name = "inventory/batch_cloth_assignment_form.html"

    def form_valid(self, form):
        assignment = form.save(commit=False)
        # If being marked CONSUMED, run through the service so StockLedger is updated
        if assignment.status == 'CONSUMED':
            try:
                BatchService.process_cutting(
                    assignment=assignment,
                    consumed_length=assignment.consumed_length,
                    wastage_length=assignment.wastage_length,
                    created_by=self.request.user,
                )
                return redirect(self.get_success_url())
            except ValidationError as e:
                form.add_error(None, e.message)
                return self.form_invalid(form)
        assignment.save()
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('inventory:batch_detail', kwargs={'pk': self.kwargs['batch_pk']})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['batch'] = get_object_or_404(Batch, pk=self.kwargs['batch_pk'])
        return context


# =============================================================================
# BATCH USER ASSIGNMENT CRUD
# =============================================================================

class BatchUserAssignmentCreateView(LoginRequiredMixin, ManagerOrSuperuserMixin, CreateView):
    model = BatchUserAssignment
    form_class = BatchUserAssignmentForm
    template_name = "inventory/batch_user_assignment_form.html"

    def get_batch(self):
        return get_object_or_404(Batch, pk=self.kwargs['batch_pk'])

    def form_valid(self, form):
        form.instance.batch = self.get_batch()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('inventory:batch_detail', kwargs={'pk': self.kwargs['batch_pk']})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['batch'] = self.get_batch()
        return context


class BatchUserAssignmentUpdateView(LoginRequiredMixin, ManagerOrSuperuserMixin, UpdateView):
    model = BatchUserAssignment
    form_class = BatchUserAssignmentForm
    template_name = "inventory/batch_user_assignment_form.html"

    def get_success_url(self):
        return reverse('inventory:batch_detail', kwargs={'pk': self.kwargs['batch_pk']})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['batch'] = get_object_or_404(Batch, pk=self.kwargs['batch_pk'])
        return context


class BatchUserAssignmentDeleteView(LoginRequiredMixin, ManagerOrSuperuserMixin, DeleteView):
    model = BatchUserAssignment
    template_name = "inventory/batch_user_assignment_confirm_remove.html"

    def get_success_url(self):
        return reverse('inventory:batch_detail', kwargs={'pk': self.kwargs['batch_pk']})

    def form_valid(self, form):
        # Soft-delete: deactivate instead of hard delete to preserve history
        self.object.is_active = False
        self.object.save()
        return redirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['batch'] = get_object_or_404(Batch, pk=self.kwargs['batch_pk'])
        return context


# =============================================================================
# BATCH OPERATION CRUD
# =============================================================================

class BatchOperationCreateView(LoginRequiredMixin, CreateView):
    model = BatchOperation
    form_class = BatchOperationForm
    template_name = "inventory/batch_operation_form.html"

    def get_batch(self):
        return get_object_or_404(Batch, pk=self.kwargs['batch_pk'])

    def form_valid(self, form):
        form.instance.batch = self.get_batch()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('inventory:batch_detail', kwargs={'pk': self.kwargs['batch_pk']})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['batch'] = self.get_batch()
        return context


class BatchOperationUpdateView(LoginRequiredMixin, UpdateView):
    model = BatchOperation
    form_class = BatchOperationForm
    template_name = "inventory/batch_operation_form.html"

    def get_success_url(self):
        return reverse('inventory:batch_detail', kwargs={'pk': self.kwargs['batch_pk']})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['batch'] = get_object_or_404(Batch, pk=self.kwargs['batch_pk'])
        return context


class BatchOperationDeleteView(LoginRequiredMixin, ManagerOrSuperuserMixin, DeleteView):
    model = BatchOperation
    template_name = "inventory/batch_operation_confirm_delete.html"

    def get_success_url(self):
        return reverse('inventory:batch_detail', kwargs={'pk': self.kwargs['batch_pk']})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['batch'] = get_object_or_404(Batch, pk=self.kwargs['batch_pk'])
        return context


# =============================================================================
# STAGE CRUD
# =============================================================================

class StageListView(LoginRequiredMixin, ListView):
    model = Stage
    template_name = "inventory/stage_list.html"
    context_object_name = "stages"
    ordering = ['name']


class StageCreateView(LoginRequiredMixin, ManagerOrSuperuserMixin, CreateView):
    model = Stage
    form_class = StageForm
    template_name = "inventory/stage_form.html"
    success_url = reverse_lazy('inventory:stage_list')


class StageUpdateView(LoginRequiredMixin, ManagerOrSuperuserMixin, UpdateView):
    model = Stage
    form_class = StageForm
    template_name = "inventory/stage_form.html"
    success_url = reverse_lazy('inventory:stage_list')


class StageDeleteView(LoginRequiredMixin, ManagerOrSuperuserMixin, DeleteView):
    model = Stage
    template_name = "inventory/stage_confirm_delete.html"
    success_url = reverse_lazy('inventory:stage_list')

    def form_valid(self, form):
        stage = self.object
        if Batch.objects.filter(current_stage=stage, status='WIP').exists():
            messages.error(self.request, f"Cannot delete '{stage.name}' — it has active (WIP) batches assigned to it.")
            return redirect('inventory:stage_list')
        return super().form_valid(form)


# =============================================================================
# MACHINE CRUD
# =============================================================================

class MachineListView(LoginRequiredMixin, ListView):
    model = Machine
    template_name = "inventory/machine_list.html"
    context_object_name = "machines"
    ordering = ['stage__name', 'name']

    def get_queryset(self):
        return super().get_queryset().select_related('stage')


class MachineCreateView(LoginRequiredMixin, ManagerOrSuperuserMixin, CreateView):
    model = Machine
    form_class = MachineForm
    template_name = "inventory/machine_form.html"
    success_url = reverse_lazy('inventory:machine_list')


class MachineUpdateView(LoginRequiredMixin, ManagerOrSuperuserMixin, UpdateView):
    model = Machine
    form_class = MachineForm
    template_name = "inventory/machine_form.html"
    success_url = reverse_lazy('inventory:machine_list')


class MachineDeleteView(LoginRequiredMixin, ManagerOrSuperuserMixin, DeleteView):
    model = Machine
    template_name = "inventory/machine_confirm_delete.html"
    success_url = reverse_lazy('inventory:machine_list')
