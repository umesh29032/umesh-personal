from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.db.models import Q, Sum
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, View

from ..models import Batch, BatchClothAssignment, BatchUserAssignment, BatchOperation
from ..forms import BatchForm, BatchClothAssignmentForm, BatchUserAssignmentForm, BatchOperationForm
from ..constants import BatchStatus
from ..services import BatchService
from .mixins import ManagerOrAdminMixin


class BatchListView(LoginRequiredMixin, ListView):
    model = Batch
    template_name = "inventory/batch_list.html"
    context_object_name = "batches"
    paginate_by = 10
    ordering = ['-created_at']

    def get_queryset(self):
        qs = super().get_queryset().select_related('current_stage', 'created_by')
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


class BatchCreateView(LoginRequiredMixin, ManagerOrAdminMixin, CreateView):
    model = Batch
    form_class = BatchForm
    template_name = "inventory/batch_form.html"
    success_url = reverse_lazy('inventory:batch_list')

    def form_valid(self, form):
        BatchService.create_batch(form.cleaned_data, user=self.request.user)
        messages.success(self.request, "Batch created successfully.")
        return redirect(self.success_url)


class BatchUpdateView(LoginRequiredMixin, ManagerOrAdminMixin, UpdateView):
    model = Batch
    form_class = BatchForm
    template_name = "inventory/batch_form.html"
    success_url = reverse_lazy('inventory:batch_list')

    def form_valid(self, form):
        new_status = form.cleaned_data.get('status')
        batch = form.instance
        # If status changed, enforce transition rules via service
        if new_status and new_status != batch.status:
            try:
                # Save non-status fields first
                batch = form.save(commit=False)
                batch.status = self.get_object().status  # restore old status temporarily
                batch.save()
                BatchService.transition_status(batch, new_status)
            except ValidationError as e:
                form.add_error('status', e)
                return self.form_invalid(form)
        else:
            form.save()
        messages.success(self.request, "Batch updated.")
        return redirect(self.success_url)


class BatchDeleteView(LoginRequiredMixin, ManagerOrAdminMixin, DeleteView):
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
        context['cloth_assignments'] = (
            batch.cloth_assignments
            .select_related('cloth_roll')
            .order_by('-assigned_at')
        )
        context['user_assignments'] = (
            batch.user_assignments
            .select_related('user')
            .filter(is_active=True)
            .order_by('-assigned_at')
        )
        context['operations'] = (
            batch.operations
            .select_related('stage', 'user', 'machine')
            .order_by('-start_time')
        )
        context['products'] = batch.products.select_related('location').order_by('-created_at')

        agg = batch.cloth_assignments.aggregate(
            total_reserved=Sum('reserved_length'),
            total_consumed=Sum('consumed_length'),
            total_wastage=Sum('wastage_length'),
        )
        context['total_reserved'] = agg['total_reserved'] or 0
        context['total_consumed'] = agg['total_consumed'] or 0
        context['total_wastage'] = agg['total_wastage'] or 0
        u = self.request.user
        context['can_manage'] = u.is_superuser or getattr(u, 'user_type', '') in ('admin', 'manager')
        _transitions = {
            BatchStatus.PLANNED: [BatchStatus.WIP, BatchStatus.CANCELLED],
            BatchStatus.WIP: [BatchStatus.COMPLETED, BatchStatus.CANCELLED],
        }
        context['allowed_transitions'] = _transitions.get(batch.status, [])
        return context


# ── Cloth Assignments ─────────────────────────────────────────────────────────

class BatchClothAssignmentCreateView(LoginRequiredMixin, ManagerOrAdminMixin, CreateView):
    model = BatchClothAssignment
    form_class = BatchClothAssignmentForm
    template_name = "inventory/batch_cloth_assignment_form.html"

    def get_batch(self):
        return get_object_or_404(Batch, pk=self.kwargs['batch_pk'])

    def form_valid(self, form):
        batch = self.get_batch()
        cloth_roll = form.cleaned_data['cloth_roll']
        reserved_length = form.cleaned_data['reserved_length']
        try:
            BatchService.assign_cloth(batch, cloth_roll, reserved_length, created_by=self.request.user)
        except ValidationError as e:
            form.add_error(None, e)
            return self.form_invalid(form)
        messages.success(self.request, "Cloth roll assigned to batch.")
        return redirect(reverse('inventory:batch_detail', kwargs={'pk': self.kwargs['batch_pk']}))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['batch'] = self.get_batch()
        return context


class BatchClothAssignmentUpdateView(LoginRequiredMixin, ManagerOrAdminMixin, UpdateView):
    model = BatchClothAssignment
    form_class = BatchClothAssignmentForm
    template_name = "inventory/batch_cloth_assignment_form.html"

    def form_valid(self, form):
        assignment = form.instance
        new_status = form.cleaned_data.get('status')

        # If marking as CONSUMED, use the service for proper ledger logging
        if new_status == 'CONSUMED' and assignment.status != 'CONSUMED':
            consumed = form.cleaned_data.get('consumed_length', 0)
            wastage = form.cleaned_data.get('wastage_length', 0)
            try:
                BatchService.process_cutting(assignment, consumed, wastage, created_by=self.request.user)
            except ValidationError as e:
                form.add_error(None, e)
                return self.form_invalid(form)
        else:
            form.save()

        messages.success(self.request, "Cloth assignment updated.")
        return redirect(reverse('inventory:batch_detail', kwargs={'pk': self.kwargs['batch_pk']}))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['batch'] = get_object_or_404(Batch, pk=self.kwargs['batch_pk'])
        return context

    def get_success_url(self):
        return reverse('inventory:batch_detail', kwargs={'pk': self.kwargs['batch_pk']})


# ── User Assignments ──────────────────────────────────────────────────────────

class BatchUserAssignmentCreateView(LoginRequiredMixin, ManagerOrAdminMixin, CreateView):
    model = BatchUserAssignment
    form_class = BatchUserAssignmentForm
    template_name = "inventory/batch_user_assignment_form.html"

    def get_batch(self):
        return get_object_or_404(Batch, pk=self.kwargs['batch_pk'])

    def form_valid(self, form):
        batch = self.get_batch()
        try:
            BatchService.assign_user(batch, form.cleaned_data['user'], form.cleaned_data['role'])
        except Exception as e:
            form.add_error(None, str(e))
            return self.form_invalid(form)
        messages.success(self.request, "Worker assigned to batch.")
        return redirect(reverse('inventory:batch_detail', kwargs={'pk': self.kwargs['batch_pk']}))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['batch'] = self.get_batch()
        return context


class BatchUserAssignmentUpdateView(LoginRequiredMixin, ManagerOrAdminMixin, UpdateView):
    model = BatchUserAssignment
    form_class = BatchUserAssignmentForm
    template_name = "inventory/batch_user_assignment_form.html"

    def get_success_url(self):
        return reverse('inventory:batch_detail', kwargs={'pk': self.kwargs['batch_pk']})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['batch'] = get_object_or_404(Batch, pk=self.kwargs['batch_pk'])
        return context


class BatchUserAssignmentDeleteView(LoginRequiredMixin, ManagerOrAdminMixin, DeleteView):
    model = BatchUserAssignment
    template_name = "inventory/batch_user_assignment_confirm_remove.html"

    def form_valid(self, form):
        # Soft-delete via service — preserves history for audit
        BatchService.remove_user(self.object)
        messages.success(self.request, "Worker removed from batch.")
        return redirect(reverse('inventory:batch_detail', kwargs={'pk': self.kwargs['batch_pk']}))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['batch'] = get_object_or_404(Batch, pk=self.kwargs['batch_pk'])
        return context

    def get_success_url(self):
        return reverse('inventory:batch_detail', kwargs={'pk': self.kwargs['batch_pk']})


# ── Status Transition ─────────────────────────────────────────────────────────

class BatchTransitionView(LoginRequiredMixin, ManagerOrAdminMixin, View):
    """POST-only: move a batch to a new status via BatchService."""

    def post(self, request, pk):
        batch = get_object_or_404(Batch, pk=pk)
        new_status = request.POST.get('new_status', '')
        try:
            BatchService.transition_status(batch, new_status)
            label = dict(BatchStatus.choices).get(new_status, new_status)
            messages.success(request, f"Batch {batch.batch_number} moved to '{label}'.")
        except ValidationError as e:
            messages.error(request, e.message)
        return redirect(reverse('inventory:batch_detail', kwargs={'pk': pk}))


# ── Operations ────────────────────────────────────────────────────────────────

class BatchOperationCreateView(LoginRequiredMixin, CreateView):
    model = BatchOperation
    form_class = BatchOperationForm
    template_name = "inventory/batch_operation_form.html"

    def get_batch(self):
        return get_object_or_404(Batch, pk=self.kwargs['batch_pk'])

    def form_valid(self, form):
        batch = self.get_batch()
        cd = form.cleaned_data
        BatchService.log_operation(
            batch=batch,
            stage=cd['stage'],
            user=cd['user'],
            machine=cd.get('machine'),
            start_time=cd['start_time'],
            end_time=cd.get('end_time'),
            output_quantity=cd.get('output_quantity', 0),
            notes=cd.get('notes', ''),
        )
        messages.success(self.request, "Operation logged.")
        return redirect(reverse('inventory:batch_detail', kwargs={'pk': self.kwargs['batch_pk']}))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['batch'] = self.get_batch()
        return context


class BatchOperationUpdateView(LoginRequiredMixin, ManagerOrAdminMixin, UpdateView):
    model = BatchOperation
    form_class = BatchOperationForm
    template_name = "inventory/batch_operation_form.html"

    def get_success_url(self):
        return reverse('inventory:batch_detail', kwargs={'pk': self.kwargs['batch_pk']})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['batch'] = get_object_or_404(Batch, pk=self.kwargs['batch_pk'])
        return context


class BatchOperationDeleteView(LoginRequiredMixin, ManagerOrAdminMixin, DeleteView):
    model = BatchOperation
    template_name = "inventory/batch_operation_confirm_delete.html"

    def get_success_url(self):
        return reverse('inventory:batch_detail', kwargs={'pk': self.kwargs['batch_pk']})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['batch'] = get_object_or_404(Batch, pk=self.kwargs['batch_pk'])
        return context
