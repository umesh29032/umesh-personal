"""Per-Product Production Flow editor (Phase B).

YEH FILE KYU HAI?
─────────────────
Admin per-product flow define karta hai — kaunsi Stages, kis order mein.
Layering default first stage hota hai (create_product service-side seed
karta hai). Yahan se admin reorder, add, remove karta hai.

Permission: Super Admin only — flow structure production correctness pe
direct asar daalti hai, isliye narrow gate. (Manager Product details
edit kar sakte hain via product_views, but flow change Super Admin only.)
"""
from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import TemplateView

from accounts.services import ROLE_SUPER_ADMIN, user_has_role
from production.models import CostMethod, Product, Stage, WorkflowStage
from production.services import (
    add_stage_to_product_flow,
    move_stage_in_product_flow,
    remove_stage_from_product_flow,
    set_stage_cost,
)


class _SuperAdminOnly(UserPassesTestMixin):
    def test_func(self):
        return user_has_role(self.request.user, {ROLE_SUPER_ADMIN})


class ProductFlowEditView(LoginRequiredMixin, _SuperAdminOnly, TemplateView):
    template_name = 'production/product_flow.html'

    def _product(self) -> Product:
        return get_object_or_404(Product, pk=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        product = self._product()
        # Current flow rows, ordered. Prefetch Stage M2Ms so the template can
        # render skill + role chips inline without N+1 queries.
        flow_rows = list(
            product.workflow_stages
            .select_related('stage')
            .prefetch_related('stage__access_by_skill', 'stage__access_by_role')
            .order_by('order')
        )
        used_stage_ids = {ws.stage_id for ws in flow_rows}
        # Library — only ACTIVE stages NOT already in this product's flow.
        available_stages = (
            Stage.active
            .exclude(id__in=used_stage_ids)
            .order_by('name')
        )
        ctx.update({
            'product': product,
            'flow_rows': flow_rows,
            'available_stages': available_stages,
            'flow_count': len(flow_rows),
            'cost_methods': CostMethod.choices,
        })
        return ctx

    def post(self, request, *args, **kwargs):
        product = self._product()
        action = request.POST.get('action', '')

        try:
            if action == 'add':
                stage_id = int(request.POST.get('stage_id') or 0)
                stage = get_object_or_404(Stage, pk=stage_id)
                add_stage_to_product_flow(user=request.user, product=product, stage=stage)
                messages.success(request, f"Added '{stage.name}' to the flow.")

            elif action == 'remove':
                ws_id = int(request.POST.get('workflow_stage_id') or 0)
                ws = get_object_or_404(WorkflowStage, pk=ws_id, product=product)
                stage_name = ws.stage.name
                remove_stage_from_product_flow(user=request.user, workflow_stage=ws)
                messages.success(request, f"Removed '{stage_name}' from the flow.")

            elif action in ('move_up', 'move_down'):
                ws_id = int(request.POST.get('workflow_stage_id') or 0)
                ws = get_object_or_404(WorkflowStage, pk=ws_id, product=product)
                direction = 'up' if action == 'move_up' else 'down'
                move_stage_in_product_flow(
                    user=request.user, workflow_stage=ws, direction=direction,
                )

            elif action == 'set_cost':
                ws_id = int(request.POST.get('workflow_stage_id') or 0)
                ws = get_object_or_404(WorkflowStage, pk=ws_id, product=product)
                billed_raw = request.POST.get('cost_billed_at') or ''
                set_stage_cost(
                    user=request.user, workflow_stage=ws,
                    cost_method=request.POST.get('cost_method') or '',
                    cost_rate=request.POST.get('cost_rate'),
                    cost_billed_at_id=int(billed_raw) if billed_raw.isdigit() else None,
                )
                messages.success(request, f"Updated cost for '{ws.stage.name}'.")

            else:
                messages.error(request, f"Unknown action: {action!r}")

        except ValidationError as exc:
            messages.error(request, exc.message if hasattr(exc, 'message') else str(exc))

        return redirect(reverse('production:product-flow', args=[product.pk]))
