"""Layering stage handler — thin adapter over layering_service (M2.2).

Adapter-first: this delegates to the EXISTING service so the registry + handler
contract are proven against a real stage without moving any code. Behavior is
identical (the service remains the single implementation). After dispatch is
switched to the registry and proven (M2.6), the service/models/views move into
this package and the logic lands here.

Services are imported lazily inside methods (the production.services facade) so
importing this handler at app-ready time stays cheap and import-safe.
"""
from __future__ import annotations

from decimal import Decimal

from production.constants import STAGE_LAYERING
from production.stages.base import CompletionResult, ReopenResult, StageHandler, register


@register
class LayeringHandler(StageHandler):
    code = STAGE_LAYERING
    name = 'Layering'
    template_partial = 'production/_stage_panel_layering.html'
    # Layering assigns workers (M2M) but books NO allocation-driven earnings today
    # — worker pay is allocated at the cutting stage — so it credits no one here.
    pays_workers = False

    def panel_context(self, adda, record):
        from production.services import get_layering_snapshot
        return get_layering_snapshot(adda)

    def start(self, *, user_id, adda, record, data):
        from accounts.models import User
        from production.services import start_layering
        return start_layering(
            adda=adda,
            worker_ids=data.get('worker_ids', []),
            user=User.objects.get(pk=user_id),
        )

    def complete(self, *, user_id, adda, record, data):
        from accounts.models import User
        from production.services import complete_layering
        complete_layering(
            adda=adda,
            duration_minutes=data.get('duration_minutes'),
            layer_length_meters=data.get('layer_length_meters'),
            per_entry_layers=data.get('per_entry_layers', {}),
            notes=data.get('notes', ''),
            user=User.objects.get(pk=user_id),
        )
        return CompletionResult()   # no allocation-driven earnings at layering

    def reopen(self, *, user_id, record):
        from accounts.models import User
        from production.services import reopen_layering
        reopen_layering(adda=record.adda, user=User.objects.get(pk=user_id))
        return ReopenResult()

    def cost_quantity(self, record):
        # Priced per_layer → quantity = LayeringRecord.lay_count (mirrors
        # cost_service._quantity_for's per_layer branch).
        lr = getattr(record, 'layering', None)
        return Decimal(lr.lay_count) if lr is not None and lr.lay_count is not None else Decimal('0')
