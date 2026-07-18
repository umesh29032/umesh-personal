"""Factory-wide manufacturing costing dashboard (PR-7, Q4/Q8).

Super-admin / manager view: every Adda with its total manufacturing cost
(SUM of frozen per-stage processing_cost), pieces, worker earnings, and margin
gap. Honest-NULL: unpriced stages are surfaced, never silently counted as 0.
"""
from __future__ import annotations

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from decimal import Decimal

from django.db.models import Sum
from django.views.generic import TemplateView

from accounts.services import MANAGEMENT_ROLES, user_has_role
from production.models import Adda, AddaStageRecord
# FUTURE-STAGE-REDESIGN: StageWorkAssignment is transitional — V2-2 settlement
# repoints worker earnings; this costing read moves to the settlement source then
# (production->expense one-way edge; see docs/ARCHITECTURE_V2.md §11).
from expense.models import StageWorkAssignment


class _ManagementOnly(UserPassesTestMixin):
    def test_func(self):
        return user_has_role(self.request.user, MANAGEMENT_ROLES)


class ProductionCostingView(LoginRequiredMixin, _ManagementOnly, TemplateView):
    """Per-Adda manufacturing cost rollup. Management only."""
    template_name = 'production/costing.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        addas = list(
            Adda.objects.select_related('product', 'current_stage__stage')
            # Annotate pieces in ONE query — shadows the Adda.total_pieces
            # property so we don't fire a per-Adda aggregate in the loop (N+1).
            # APSCPB = the canonical cut-piece truth (ops-master §2 rule 6);
            # barcode batches are optional per flow and read 0 when unused.
            .annotate(pieces=Sum('size_color_breakdowns__verified_piece_count'))
            .order_by('-started_at')[:200]
        )
        # Total manufacturing cost per Adda (only frozen+priced stage rows).
        cost_map = {
            r['adda']: r['c'] for r in
            AddaStageRecord.objects.filter(processing_cost__isnull=False)
            .values('adda').annotate(c=Sum('processing_cost'))
        }
        # M13 (2026-07-12): variance must compare LIKE with LIKE — settled
        # labor can only ever cover PAYABLE stages, so the vs-settled variance
        # uses the payable standard; non-payable priced cost (e.g. layering)
        # is its own honest column, never mixed into that drift. (GLDN-001
        # exposed the mix: ₹128.75 'variance' was mostly layering's ₹164.)
        payable_cost_map = {
            r['adda']: r['c'] for r in
            AddaStageRecord.objects.filter(
                processing_cost__isnull=False,
                workflow_stage__credits_workers=True)
            .values('adda').annotate(c=Sum('processing_cost'))
        }
        # Unpriced completed stages per Adda — surfaced, never coerced to 0.
        from django.db.models import Count
        unpriced_map = {
            r['adda']: r['n'] for r in
            AddaStageRecord.objects.filter(
                completed_at__isnull=False, processing_cost__isnull=True,
            ).values('adda').annotate(n=Count('id'))
        }
        # C-1 (ADR-0009 honest-NULL): consumed-but-UNPRICED rolls make an
        # Adda's material costing incomplete — surfaced, never coerced to 0.
        from raw_materials.models import ClothRoll
        unpriced_rolls_map = {
            r['adda']: r['n'] for r in
            ClothRoll.objects.filter(adda__isnull=False, cost_per_kg__isnull=True)
            .values('adda').annotate(n=Count('id'))
        }
        earn_map = {
            r['stage_record__adda']: r['e'] for r in
            StageWorkAssignment.objects.filter(voided_at__isnull=True)
            .values('stage_record__adda').annotate(e=Sum('earning_amount_snapshot'))
        }
        rows = []
        grand_cost = 0
        for a in addas:
            cost = cost_map.get(a.pk) or 0
            payable_cost = payable_cost_map.get(a.pk) or 0
            grand_cost += cost
            earnings = earn_map.get(a.pk, 0)
            rows.append({
                'adda': a,
                'current_stage': a.current_stage.stage.name if a.current_stage else '—',
                'pieces': a.pieces or 0,   # annotation (see queryset), not the N+1 property
                'total_cost': cost,
                'payable_cost': payable_cost,
                'nonpayable_cost': cost - payable_cost,
                'worker_earnings': earnings,
                # A360/P-COST: the ADR-0009 duality made explicit — variance =
                # PAYABLE standard − actual settled labor (like-for-like; the
                # declared home for this drift).
                'variance': payable_cost - earnings,
                'unpriced': unpriced_map.get(a.pk, 0),
                'unpriced_rolls': unpriced_rolls_map.get(a.pk, 0),
            })
        # RMX-D (Phase 17, charter = PDD entry 8): the Model-B completion —
        # Material + Full Cost columns from THE certified Decision-2 assembly
        # (cost_service.full_costs_for_addas; A360 reads the same function).
        # The view calculates NOTHING: values pass through; the grand line is
        # a presentation-sum of the certified per-Adda figures.
        from production.services.cost_service import full_costs_for_addas
        fc = full_costs_for_addas([a.pk for a in addas])
        grand_full = Decimal('0.00')
        for row in rows:
            f = fc[row['adda'].pk]
            row['material_net'] = f['material']['net']
            row['material_unpriced_rolls'] = f['material']['unpriced_rolls']
            row['has_material'] = f['material']['has_material']
            row['full_cost'] = f['full_cost']
            grand_full += f['full_cost']
        ctx['rows'] = rows
        ctx['grand_cost'] = grand_cost
        ctx['grand_full_cost'] = grand_full
        ctx['total_unpriced_rolls'] = sum(unpriced_rolls_map.values())
        return ctx
