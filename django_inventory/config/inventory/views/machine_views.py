from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from ..models import Machine
from ..forms import MachineForm
from .mixins import ManagerOrAdminMixin


class MachineListView(LoginRequiredMixin, ListView):
    model = Machine
    template_name = "inventory/machine_list.html"
    context_object_name = "machines"
    ordering = ['stage__name', 'name']

    def get_queryset(self):
        return super().get_queryset().select_related('stage')


class MachineCreateView(LoginRequiredMixin, ManagerOrAdminMixin, CreateView):
    model = Machine
    form_class = MachineForm
    template_name = "inventory/machine_form.html"
    success_url = reverse_lazy('inventory:machine_list')


class MachineUpdateView(LoginRequiredMixin, ManagerOrAdminMixin, UpdateView):
    model = Machine
    form_class = MachineForm
    template_name = "inventory/machine_form.html"
    success_url = reverse_lazy('inventory:machine_list')


class MachineDeleteView(LoginRequiredMixin, ManagerOrAdminMixin, DeleteView):
    model = Machine
    template_name = "inventory/machine_confirm_delete.html"
    success_url = reverse_lazy('inventory:machine_list')
