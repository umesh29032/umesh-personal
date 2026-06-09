"""Barcode Generation stage handler — thin adapter over barcode_generation_service
(M2.5).

Adapter-first: delegates to the existing service; behavior identical. The stage's
extra `generate_barcodes` action (not part of the generic lifecycle contract) stays
on the service and is routed directly by dispatch until M2.6 reconciles it.
"""
from __future__ import annotations

from decimal import Decimal

from production.constants import STAGE_BARCODE_GENERATION
from production.stages.base import CompletionResult, ReopenResult, StageHandler, register


@register
class BarcodeGenerationHandler(StageHandler):
    code = STAGE_BARCODE_GENERATION
    name = 'Barcode Generation'
    template_partial = 'production/_stage_panel_barcode_gen.html'

    def snapshot(self, adda):
        from production.services import get_barcode_snapshot
        return get_barcode_snapshot(adda)

    def panel_context(self, request, adda, record):
        from production.views.barcode_gen_views import _build_barcode_gen_context
        return _build_barcode_gen_context(request, adda)

    def start(self, *, user_id, adda, record, data):
        from accounts.models import User
        from production.services import start_barcode_generation
        return start_barcode_generation(
            adda=adda, worker_ids=data.get('worker_ids', []),
            user=User.objects.get(pk=user_id))

    def complete(self, *, user_id, adda, record, data):
        from accounts.models import User
        from production.services import complete_barcode_generation
        complete_barcode_generation(adda=adda, user=User.objects.get(pk=user_id))
        return CompletionResult()

    def reopen(self, *, user_id, record):
        from accounts.models import User
        from production.services import reopen_barcode_generation
        reopen_barcode_generation(adda=record.adda, user=User.objects.get(pk=user_id))
        return ReopenResult()

    def cost_quantity(self, record):
        # Priced per_piece → quantity = BarcodeGenerationRecord.total_barcodes.
        bg = getattr(record, 'barcode_generation', None)
        return Decimal(bg.total_barcodes) if bg is not None and bg.total_barcodes is not None else None
