"""Cutting stage handler — thin adapter over cutting_service (M2.4).

Adapter-first: delegates to the existing service; behavior identical. Code (and the
1189-line service's bundle/breakup/completion split) moves into this package only
after dispatch is migrated and proven (post-M2.6).

complete() delegates to the MODERN workspace path (complete_cutting_from_bundles).
The legacy form path (complete_cutting_legacy) is still wired in stage_views and is
handled there until the dispatch switch (M2.6) reconciles both.

Cutting is where worker earnings are allocated (payability = WorkflowStage.credits_workers,
seeded True for cutting). Allocation is currently a SEPARATE manual step, so complete()
returns no allocations yet; the PAY-2 guard (M2.7) blocks completing without one.
"""
from __future__ import annotations

from decimal import Decimal

from production.constants import ALLOC_DIM_COLOR_SIZE, STAGE_CUTTING
from production.stages.base import CompletionResult, ReopenResult, StageHandler, register


@register
class CuttingHandler(StageHandler):
    code = STAGE_CUTTING
    name = 'Cutting'
    template_partial = 'production/_stage_panel_cutting.html'
    # S4/D1: Cutting is the piece-pool SOURCE — first stage where piece quantities +
    # the (colour,size) breakup exist. Owner-locked 2026-06-14.
    pool_grain = ALLOC_DIM_COLOR_SIZE

    # S4/D3 (Option B): Cutting's pool good is AddaProductSizeColorPieceBreakdown — the
    # single source of truth (C1), NOT duplicated into StagePoolSnapshot.
    def pool_good(self, stage_record) -> dict:
        """{(color_id, size_id): Decimal} from the verified cut-piece breakdown
        (APSCPB), never from StagePoolSnapshot. Empty if cutting not completed."""
        from decimal import Decimal

        from django.db.models import Sum

        from production.models import AddaProductSizeColorPieceBreakdown as Breakdown
        cr = getattr(stage_record, 'cutting', None)   # OneToOne reverse; None pre-complete
        if cr is None:
            return {}
        rows = (Breakdown.objects.filter(cutting_record=cr)
                .values('color_id', 'size_id').annotate(g=Sum('verified_piece_count')))
        return {(r['color_id'], r['size_id']): Decimal(r['g']) for r in rows}

    def materialize_pool(self, stage_record) -> int:
        """No-op: APSCPB is materialised by cutting completion (_materialize_breakdown),
        and is the single source of truth — cutting writes NO StagePoolSnapshot row."""
        return 0

    def snapshot(self, adda):
        from production.services import get_cutting_snapshot
        return get_cutting_snapshot(adda)

    def panel_context(self, request, adda, record):
        from accounts.services import MANAGEMENT_ROLES, user_has_role
        from production.forms import CuttingForm
        from production.views.stage_views import _build_cutting_context
        # Mirrors the legacy StagePanelView cutting branch exactly.
        ctx = {
            'cutting_form': CuttingForm(),
            'can_complete_cutting': (
                user_has_role(request.user, MANAGEMENT_ROLES)
                and adda.current_stage is not None
                and adda.current_stage.stage_type == self.code
            ),
        }
        ctx.update(_build_cutting_context(request, adda))
        return ctx

    def start(self, *, user_id, adda, record, data):
        from accounts.models import User
        from production.services import start_cutting
        return start_cutting(
            adda=adda, worker_ids=data.get('worker_ids', []),
            user=User.objects.get(pk=user_id))

    def complete(self, *, user_id, adda, record, data):
        from accounts.models import User
        from production.services import complete_cutting_from_bundles
        complete_cutting_from_bundles(adda=adda, user=User.objects.get(pk=user_id))
        return CompletionResult()   # allocation is a separate step today (PAY-2; M2.7)

    def reopen(self, *, user_id, record):
        from accounts.models import User
        from production.services import reopen_cutting
        reopen_cutting(adda=record.adda, user=User.objects.get(pk=user_id))
        return ReopenResult()

    def cost_quantity(self, record):
        cr = getattr(record, 'cutting', None)
        if cr is None:
            return None   # no record -> unpriced (NULL), not 0
        # Mirrors cost_service._quantity_for: per_bundle -> bundle count, else pieces.
        if record.workflow_stage.cost_method == 'per_bundle':
            return Decimal(cr.bundles.count())
        return Decimal(cr.pieces_cut) if cr.pieces_cut is not None else None

    def contribution_schema(self, adda, worker=None):
        """REFERENCE impl of the open-closed worker-contribution schema: Cutting
        workers report pieces per colour + size. Colours = active cloth palette;
        sizes = the product's active ProductSizes. (Not the final shape of all
        stages — a later stage-taxonomy review may revise this; the FRAMEWORK is the
        point. Default base schema = quantity-only.)"""
        from raw_materials.models import ClothColor
        from production.models import ProductSize
        colors = ClothColor.active.all().order_by('name')
        sizes = ProductSize.objects.filter(
            product=adda.product, is_active=True).order_by('display_order')
        return {
            'line_label': 'piece line',
            'fields': [
                {'key': 'color_id', 'kind': 'choice', 'label': 'Colour', 'required': False,
                 'options': [{'value': c.pk, 'label': c.name, 'swatch': c.hex_code or ''}
                             for c in colors]},
                {'key': 'size_id', 'kind': 'choice', 'label': 'Size', 'required': False,
                 'options': [{'value': s.pk, 'label': s.label} for s in sizes]},
                {'key': 'reported_quantity', 'kind': 'quantity', 'label': 'Quantity',
                 'required': True, 'unit': 'pieces'},
            ],
        }
