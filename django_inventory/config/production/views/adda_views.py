"""Adda ke views — list, create, detail.

YEH FILE KYU HAI?
─────────────────
AddaListView    — filterable batch list, paginated
AddaCreateView  — naya Adda start karne ka form (service per-product counter increment)
AddaDetailView  — Adda ka full view: workflow pills, stage records, rolls, barcodes
"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import DetailView, FormView, ListView

from production.forms import AddaCreateForm
from production.models import Adda, WorkflowStage
from production.services import create_adda

from .mixins import ProductionRoleMixin


class AddaListView(LoginRequiredMixin, ProductionRoleMixin, ListView):
    template_name = 'production/adda_list.html'
    model = Adda
    context_object_name = 'addas'
    paginate_by = 50

    def get_queryset(self):
        qs = Adda.objects.select_related('product', 'current_stage').order_by('-started_at')
        status = self.request.GET.get('status')
        stage_type = self.request.GET.get('stage')
        if status:
            qs = qs.filter(status=status)
        if stage_type:
            qs = qs.filter(current_stage__stage_type=stage_type)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['filters'] = {
            'status': self.request.GET.get('status', ''),
            'stage': self.request.GET.get('stage', ''),
        }
        ctx['stage_types'] = WorkflowStage.StageType.choices
        ctx['status_choices'] = Adda.Status.choices
        return ctx


class AddaCreateView(LoginRequiredMixin, ProductionRoleMixin, FormView):
    template_name = 'production/adda_form.html'
    form_class = AddaCreateForm
    success_url = reverse_lazy('production:adda-list')

    def form_valid(self, form):
        try:
            adda = create_adda(user=self.request.user, product=form.cleaned_data['product'])
        except ValidationError as exc:
            form.add_error(None, str(exc))
            return self.form_invalid(form)
        messages.success(self.request, f"Adda {adda.code} started.")
        return redirect('production:adda-detail', code=adda.code)


class AddaDetailView(LoginRequiredMixin, ProductionRoleMixin, DetailView):
    """Adda detail = tabbed dashboard (Phase 4).

    Each WorkflowStage becomes a tab. Default tab = current stage; if Adda is
    completed, default = last stage. Activity feed at bottom (all users on this Adda).

    All tab content is pre-rendered server-side; JS toggles visibility (decision D12).
    """

    template_name = 'production/adda_detail.html'
    model = Adda
    context_object_name = 'adda'
    slug_field = 'code'
    slug_url_kwarg = 'code'

    def get_object(self, queryset=None):
        return get_object_or_404(Adda, code=self.kwargs['code'])

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        adda = self.object
        stages = list(adda.product.workflow_stages.order_by('order'))

        # Stage records keyed by stage_type for template lookup.
        # select_related = forward + reverse OneToOne (single FK join).
        # prefetch_related = M2M + reverse FK (separate query, joined in Python).
        sr_qs = (
            adda.stage_records
            .select_related('workflow_stage', 'completed_by', 'layering', 'cutting')
            .prefetch_related(
                'workers',
                'layering__rolls_used__cloth_type',
                'layering__rolls_used__cloth_color',
                'layering_roll_entries__roll__cloth_type',
                'layering_roll_entries__roll__cloth_color',
                'layering_roll_entries__attached_by',
            )
        )
        sr_by_type = {sr.workflow_stage.stage_type: sr for sr in sr_qs}

        # Default tab: current stage_type or last stage if completed
        if adda.current_stage is not None:
            default_tab = adda.current_stage.stage_type
        elif stages:
            default_tab = stages[-1].stage_type
        else:
            default_tab = ''

        # Lazy import — activity_service depends on tracking models
        from production.services import adda_activity, get_layering_snapshot
        activity = adda_activity(adda, limit=50)
        layering_snap = get_layering_snapshot(adda)

        ctx.update({
            'rolls': (
                adda.rolls.select_related('cloth_type', 'cloth_color').all()
                if hasattr(adda, 'rolls') else []
            ),
            'stages': stages,
            'stage_records': sr_qs.order_by('workflow_stage__order'),
            'sr_by_type': sr_by_type,
            'default_tab': default_tab,
            'activity': activity,
            'layering_snap': layering_snap,
        })
        return ctx
