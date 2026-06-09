"""Cutting Pattern stage handler — thin adapter over cutting_pattern_service (M2.3).

Adapter-first: delegates to the existing service; behavior identical. Code moves
into this package only after dispatch is migrated and proven (post-M2.6).
"""
from __future__ import annotations

from decimal import Decimal

from production.constants import STAGE_CUTTING_PATTERN
from production.stages.base import CompletionResult, ReopenResult, StageHandler, register


@register
class CuttingPatternHandler(StageHandler):
    code = STAGE_CUTTING_PATTERN
    name = 'Cutting Pattern'
    template_partial = 'production/_stage_panel_cutting_pattern.html'
    pays_workers = False   # verification stage — no allocation-driven earnings

    def panel_context(self, adda, record):
        from production.services import get_pattern_snapshot
        return get_pattern_snapshot(adda)

    def start(self, *, user_id, adda, record, data):
        from accounts.models import User
        from production.services import start_pattern_stage
        return start_pattern_stage(
            adda=adda, worker_ids=data.get('worker_ids', []),
            user=User.objects.get(pk=user_id))

    def complete(self, *, user_id, adda, record, data):
        from accounts.models import User
        from production.services import complete_pattern_stage
        complete_pattern_stage(adda=adda, user=User.objects.get(pk=user_id))
        return CompletionResult()

    def reopen(self, *, user_id, record):
        from accounts.models import User
        from production.services import reopen_pattern_stage
        reopen_pattern_stage(adda=record.adda, user=User.objects.get(pk=user_id))
        return ReopenResult()

    def cost_quantity(self, record):
        # Verification stage — no per-unit quantity (fixed / unpriced).
        return Decimal('0')
