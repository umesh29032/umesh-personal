"""BatchType CRUD + stage-template editor."""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from ..forms import BatchTypeForm
from ..models import BatchType, BatchTypeStage, Stage
from ..services import BatchTypeService
from .mixins import ManagerOrAdminMixin


class BatchTypeListView(LoginRequiredMixin, ManagerOrAdminMixin, ListView):
    model = BatchType
    template_name = 'inventory/batch_type_list.html'
    context_object_name = 'batch_types'
    ordering = ['name']

    def get_queryset(self):
        return super().get_queryset().prefetch_related('stage_templates__stage')


class BatchTypeCreateView(LoginRequiredMixin, ManagerOrAdminMixin, CreateView):
    model = BatchType
    form_class = BatchTypeForm
    template_name = 'inventory/batch_type_form.html'
    success_url = reverse_lazy('inventory:batch_type_list')

    def form_valid(self, form):
        obj = BatchTypeService.create(form.cleaned_data, self.request.user)
        messages.success(self.request, f"Batch type '{obj.name}' created. Add stages next.")
        return redirect('inventory:batch_type_stages', pk=obj.pk)


class BatchTypeUpdateView(LoginRequiredMixin, ManagerOrAdminMixin, UpdateView):
    model = BatchType
    form_class = BatchTypeForm
    template_name = 'inventory/batch_type_form.html'
    success_url = reverse_lazy('inventory:batch_type_list')


class BatchTypeDeleteView(LoginRequiredMixin, ManagerOrAdminMixin, DeleteView):
    model = BatchType
    template_name = 'inventory/batch_type_confirm_delete.html'
    success_url = reverse_lazy('inventory:batch_type_list')

    def form_valid(self, form):
        if self.object.batches.exists():
            messages.error(self.request, f"Cannot delete '{self.object.name}' — batches already reference it.")
            return redirect('inventory:batch_type_list')
        return super().form_valid(form)


class BatchTypeStagesView(LoginRequiredMixin, ManagerOrAdminMixin, View):
    """Edit the ordered stage template for a BatchType."""
    template_name = 'inventory/batch_type_stages.html'

    def get(self, request, pk):
        batch_type = get_object_or_404(BatchType, pk=pk)
        template = BatchTypeService.get_template(batch_type)
        available = BatchTypeService.available_stages_for(batch_type)
        return render(request, self.template_name, {
            'batch_type': batch_type,
            'template_rows': template,
            'available_stages': available,
        })

    def post(self, request, pk):
        batch_type = get_object_or_404(BatchType, pk=pk)

        # Parse form data: paired stage_id[], sequence_order[], is_mandatory[] lists.
        stage_ids = request.POST.getlist('stage_id')
        orders = request.POST.getlist('sequence_order')
        mandatory_ids = set(request.POST.getlist('is_mandatory'))  # checkbox values

        entries = []
        for sid, order in zip(stage_ids, orders):
            if not sid or not order:
                continue
            entries.append({
                'stage_id': sid,
                'sequence_order': order,
                'is_mandatory': sid in mandatory_ids,
            })
        try:
            BatchTypeService.set_stages(batch_type, entries)
            messages.success(request, f"Stage template for '{batch_type.name}' updated ({len(entries)} stages).")
        except ValidationError as e:
            messages.error(request, '; '.join(e.messages))
        return redirect('inventory:batch_type_stages', pk=pk)


class BatchTypeStageAddView(LoginRequiredMixin, ManagerOrAdminMixin, View):
    """Append a single stage to a BatchType template from the 'available stages' list."""
    def post(self, request, pk):
        batch_type = get_object_or_404(BatchType, pk=pk)
        stage_id = request.POST.get('stage_id')
        if not stage_id:
            messages.error(request, 'No stage selected.')
            return redirect('inventory:batch_type_stages', pk=pk)
        stage = get_object_or_404(Stage, pk=stage_id)
        last = BatchTypeStage.objects.filter(batch_type=batch_type).order_by('-sequence_order').first()
        order = (last.sequence_order + 1) if last else 1
        BatchTypeStage.objects.get_or_create(
            batch_type=batch_type, stage=stage,
            defaults={'sequence_order': order, 'is_mandatory': stage.default_is_mandatory},
        )
        messages.success(request, f"Added '{stage.name}' to the template.")
        return redirect('inventory:batch_type_stages', pk=pk)
