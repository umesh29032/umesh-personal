from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from ..models import ClothRoll
from ..forms import ClothRollForm
from ..constants import ClothType
from ..services import ClothService
from .mixins import ManagerOrAdminMixin


class ClothRollListView(LoginRequiredMixin, ListView):
    model = ClothRoll
    template_name = "inventory/clothroll_list.html"
    context_object_name = "cloth_rolls"
    # Disable Django pagination — DataTables handles client-side paging
    paginate_by = None
    ordering = ['-created_at']

    def get_queryset(self):
        qs = super().get_queryset().select_related('location', 'batch_alloted')
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
        # KPI counts — full unfiltered queryset for accurate totals
        all_rolls = ClothRoll.objects.all()
        context['total_rolls'] = all_rolls.count()
        context['available_count'] = all_rolls.filter(status='AVAILABLE').count()
        context['partial_count'] = all_rolls.filter(status='PARTIALLY_USED').count()
        context['exhausted_count'] = all_rolls.filter(status='EXHAUSTED').count()
        return context


class ClothRollCreateView(LoginRequiredMixin, ManagerOrAdminMixin, CreateView):
    model = ClothRoll
    form_class = ClothRollForm
    template_name = "inventory/clothroll_form.html"
    success_url = reverse_lazy('inventory:cloth_roll_list')

    def form_valid(self, form):
        # Use ClothService so ledger entry is created atomically
        data = form.cleaned_data
        ClothService.create_cloth_roll(data, created_by=self.request.user)
        messages.success(self.request, f"Cloth roll '{data['roll_number']}' added to stock.")
        return self._redirect_to_success()

    def _redirect_to_success(self):
        from django.shortcuts import redirect
        return redirect(self.success_url)


class ClothRollUpdateView(LoginRequiredMixin, ManagerOrAdminMixin, UpdateView):
    model = ClothRoll
    form_class = ClothRollForm
    template_name = "inventory/clothroll_form.html"
    success_url = reverse_lazy('inventory:cloth_roll_list')


class ClothRollDeleteView(LoginRequiredMixin, ManagerOrAdminMixin, DeleteView):
    model = ClothRoll
    template_name = "inventory/clothroll_confirm_delete.html"
    success_url = reverse_lazy('inventory:cloth_roll_list')
