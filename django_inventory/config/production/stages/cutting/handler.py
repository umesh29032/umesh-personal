"""Cutting stage handler — thin adapter over cutting_service (M2.4).

Adapter-first: delegates to the existing service; behavior identical. Code (and the
1189-line service's bundle/breakup/completion split) moves into this package only
after dispatch is migrated and proven (post-M2.6).

complete() delegates to the MODERN workspace path (complete_cutting_from_bundles).
The legacy form path (complete_cutting_legacy) is still wired in stage_views and is
handled there until the dispatch switch (M2.6) reconciles both.

pays_workers=True: cutting is where worker earnings are allocated — but allocation
is currently a SEPARATE manual step (the PAY-2 gap), so complete() returns no
allocations yet. M2.7 folds allocation into the base service's completion path.
"""
from __future__ import annotations

from decimal import Decimal

from production.constants import STAGE_CUTTING
from production.stages.base import CompletionResult, ReopenResult, StageHandler, register


@register
class CuttingHandler(StageHandler):
    code = STAGE_CUTTING
    name = 'Cutting'
    template_partial = 'production/_stage_panel_cutting.html'
    pays_workers = True

    def panel_context(self, adda, record):
        from production.services import get_cutting_snapshot
        return get_cutting_snapshot(adda)

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
            return Decimal('0')
        # Mirrors cost_service._quantity_for: per_bundle -> bundle count, else pieces.
        if record.workflow_stage.cost_method == 'per_bundle':
            return Decimal(cr.bundles.count())
        return Decimal(cr.pieces_cut) if cr.pieces_cut is not None else Decimal('0')
