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

# M6 — layering-side layout provider (the SAME registry species as
# cutting_pattern.LAYOUT_PROVIDER; MANUFACTURING_INTEGRATION_REVIEW §4).
# Contract: LAYOUT_PROVIDER(adda) -> {'groups': [{'group', 'uid',
# 'length_mm', 'layering_type'}]} | None — plain data, ADVISORY display
# only (the operator's layer length stays the manufacturing fact).
# Registered by patterns_ai in apps.ready(); production calls it wrapped.
LAYOUT_PROVIDER = None


@register
class LayeringHandler(StageHandler):
    code = STAGE_LAYERING
    name = 'Layering'
    template_partial = 'production/_stage_panel_layering.html'

    def snapshot(self, adda):
        from production.services import get_layering_snapshot
        return get_layering_snapshot(adda)

    def admin_snapshot(self, adda):
        # R8 generic snapshot: layering's output as a management reference for
        # the NEXT stage (Pattern Design). LIVE reads only — get_layering_snapshot
        # + the per-roll entries; nothing frozen, nothing duplicated.
        from production.services import get_layering_snapshot
        snap = get_layering_snapshot(adda)
        if snap['state'] in ('absent', 'not_started'):
            return None
        sr = snap['stage_record']
        roll_rows = []
        if sr is not None:
            for e in (sr.layering_roll_entries
                      .select_related('roll__cloth_type', 'roll__cloth_color')
                      .order_by('attached_at')):
                roll_rows.append((
                    f"Roll #{e.roll_id} · {e.roll.cloth_type.name} · {e.roll.cloth_color.name}",
                    f"{e.layers_on_roll or '—'} layers · width {e.width_verified_inch or '—'}\" · {e.weight_verified_kg or '—'} kg",
                ))
        totals = [
            ('Total layers', snap['lay_count'] if snap['lay_count'] is not None else '—'),
            ('Layer length', f"{snap['layer_length']} m" if snap['layer_length'] is not None else '—'),
            ('Colours', snap['total_colors'] if snap['total_colors'] is not None else '—'),
            ('Rolls used', snap['rolls_count']),
            ('Leftover cloth', f"{snap['leftover_length_sum']} m · {snap['leftover_weight_sum']} kg"),
        ]
        sections = [{'label': 'Totals', 'rows': totals}]
        if roll_rows:
            sections.append({'label': 'Colour-wise rolls', 'rows': roll_rows})
        return {'title': 'Layering — reference', 'sections': sections}

    def panel_context(self, request, adda, record):
        from production.views.stage_views import _build_layering_context
        return _build_layering_context(request, adda)

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
        return Decimal(lr.lay_count) if lr is not None and lr.lay_count is not None else None

    def contribution_schema(self, adda, worker=None):
        # R2 (PDD §14): layering workers report LAYERS, not pieces — override
        # only the label/unit of the base single-quantity schema. Dimensionless
        # (no colour/size at this stage); the report view/parser stay generic.
        return {
            'line_label': 'layers',
            'fields': [
                {'key': 'reported_quantity', 'kind': 'quantity',
                 'label': 'Layers laid', 'required': True, 'unit': 'layers'},
            ],
        }
