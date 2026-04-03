from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from ..models import Stage
from ..forms import StageForm
from ..services import BatchService
from .mixins import ManagerOrAdminMixin


class StageListView(LoginRequiredMixin, ListView):
    model = Stage
    template_name = "inventory/stage_list.html"
    context_object_name = "stages"
    ordering = ['name']


class StageCreateView(LoginRequiredMixin, ManagerOrAdminMixin, CreateView):
    model = Stage
    form_class = StageForm
    template_name = "inventory/stage_form.html"
    success_url = reverse_lazy('inventory:stage_list')


class StageUpdateView(LoginRequiredMixin, ManagerOrAdminMixin, UpdateView):
    model = Stage
    form_class = StageForm
    template_name = "inventory/stage_form.html"
    success_url = reverse_lazy('inventory:stage_list')


class StageDeleteView(LoginRequiredMixin, ManagerOrAdminMixin, DeleteView):
    model = Stage
    template_name = "inventory/stage_confirm_delete.html"
    success_url = reverse_lazy('inventory:stage_list')

    def form_valid(self, form):
        # Business rule: cannot delete a stage with active WIP batches
        if not BatchService.can_delete_stage(self.object):
            messages.error(
                self.request,
                f"Cannot delete '{self.object.name}' — it has active (WIP) batches assigned to it."
            )
            return redirect('inventory:stage_list')
        return super().form_valid(form)
