"""Stage manufacturing-cost service — freeze / clear the cost snapshot.

YEH FILE KYU HAI?
─────────────────
Har stage execution (AddaStageRecord) ki MANUFACTURING COST yahan freeze hoti
hai — price-at-time-of-order pattern. Rate `WorkflowStage` pe bind karta hai
(editable over time); completion pe method+rate+quantity+computed cost
`AddaStageRecord` pe FREEZE ho jaate hain. Baad mein rate edit karo to purane
Adda ki cost nahi badalti.

YEH WORKER PAY NAHI HAI. `processing_cost` = manufacturing cost (product
costing + profitability). Worker earnings allocation-driven hain aur future
`expense` app mein compute hongi.

Single-writer: yehi module `AddaStageRecord` ke cost_* columns likhta hai,
apne dedicated `save(update_fields=[cost cols])` se — taaki complete_* ke
narrow update_fields lists naye columns ko silently drop na karein.

Freeze site: `adda_service.advance_to_next_stage` (the one choke point every
complete_* funnels through). Clear site: har `reopen_*`.
"""
from __future__ import annotations

import logging  # module logger — debug-trace money writes (cost freeze/clear)
from decimal import Decimal, ROUND_HALF_UP

from django.utils import timezone

from production.models import CostMethod

logger = logging.getLogger(__name__)

# Columns this module owns — written together as one atomic UPDATE.
_COST_FIELDS = [
    'cost_method_snapshot', 'cost_rate_snapshot', 'cost_quantity_snapshot',
    'processing_cost', 'cost_frozen_at', 'updated_at',
]
_CENT = Decimal('0.01')


def _quantity_for(sr, method: str) -> Decimal | None:
    """Resolve the cost quantity from the stage's HANDLER (registry-driven, M2.10#2).

    Delegates to the stage handler's cost_quantity (which reads the typed record):
      per_layer  → LayeringRecord.lay_count
      per_bundle → CuttingBundle row count
      per_piece  → CuttingRecord.pieces_cut OR BarcodeGenerationRecord.total_barcodes
      fixed_cost → None (quantity-independent)

    Returns None when no quantity is available (unpriced → processing_cost stays
    NULL, never 0) OR when the stage has no registered handler (preserves the
    pre-M2.10 fallback). NULL != 0.00 — see compute_processing_cost.
    """
    if method == CostMethod.FIXED:
        return None
    # Import-safe here: production.stages.base does not back-import cost_service.
    from production.stages import base as stage_registry
    code = sr.workflow_stage.stage.code
    if not stage_registry.has(code):
        return None
    return stage_registry.get(code).cost_quantity(sr)


def compute_processing_cost(sr) -> tuple[str, Decimal | None, Decimal | None, Decimal | None]:
    """Pure compute (no DB write) → (method, rate, quantity, processing_cost).

    Used by freeze_stage_cost + the invariant test. Encodes all the rules:
      • grouped (billed elsewhere)  → ('', None, None, 0.00)
      • unpriced (no method/rate)   → (method, rate, None, None)
      • fixed_cost                  → (method, rate, None, rate)
      • per_x with quantity         → (method, rate, qty, quantize(rate*qty))
      • per_x missing quantity      → (method, rate, None, None)
    """
    ws = sr.workflow_stage
    # Grouped stage: labour billed at the payer stage → priced-zero (NOT NULL).
    if ws.cost_billed_at_id is not None:
        return '', None, None, Decimal('0.00')

    method = ws.cost_method or ''
    rate = ws.cost_rate
    if not method or rate is None:
        return method, rate, None, None   # unpriced — honest NULL, never 0
    if method == CostMethod.FIXED:
        return method, rate, None, rate.quantize(_CENT, rounding=ROUND_HALF_UP)
    qty = _quantity_for(sr, method)
    if qty is None:
        return method, rate, None, None
    cost = (rate * qty).quantize(_CENT, rounding=ROUND_HALF_UP)
    return method, rate, qty, cost


def freeze_stage_cost(sr, *, user=None):
    """Freeze the manufacturing-cost snapshot onto a completed stage record.

    Idempotent — safe to re-run on re-complete after a reopen; overwrites the
    snapshot and advances cost_frozen_at. Does its OWN save(update_fields=[...])
    so it never depends on the caller's narrow update_fields list.

    Side effects:
      • Writes AddaStageRecord cost columns (cost_method_snapshot,
        cost_rate_snapshot, cost_quantity_snapshot, processing_cost,
        cost_frozen_at, updated_at) — the frozen money snapshot.
      • Reads WorkflowStage (method/rate/cost_billed_at) + typed stage records
        (LayeringRecord/CuttingRecord/CuttingBundle/BarcodeGenerationRecord) via
        compute_processing_cost for the quantity. No cross-app service calls.
    """
    method, rate, qty, cost = compute_processing_cost(sr)
    sr.cost_method_snapshot = method
    sr.cost_rate_snapshot = rate
    sr.cost_quantity_snapshot = qty
    sr.processing_cost = cost
    sr.cost_frozen_at = timezone.now()
    sr.save(update_fields=_COST_FIELDS)
    logger.info(
        "cost.freeze adda=%s stage_record=%s workflow_stage=%s method=%s "
        "rate=%s qty=%s processing_cost=%s user=%s",
        getattr(sr, 'adda_id', None), sr.pk, sr.workflow_stage_id,
        method or None, rate, qty, cost, getattr(user, 'pk', None),
    )
    return sr


def clear_stage_cost(sr):
    """Wipe the cost snapshot (for reopen). A reopened-but-not-recompleted
    stage must carry NO money; re-complete re-freezes via advance_to_next_stage.

    Side effects:
      • Writes AddaStageRecord cost columns (cost_method_snapshot,
        cost_rate_snapshot, cost_quantity_snapshot, processing_cost,
        cost_frozen_at, updated_at) back to empty/NULL — clears the money
        snapshot. No reads of other models, no cross-app service calls.
    """
    sr.cost_method_snapshot = ''
    sr.cost_rate_snapshot = None
    sr.cost_quantity_snapshot = None
    sr.processing_cost = None
    sr.cost_frozen_at = None
    sr.save(update_fields=_COST_FIELDS)
    logger.info(
        "cost.clear adda=%s stage_record=%s workflow_stage=%s",
        getattr(sr, 'adda_id', None), sr.pk, sr.workflow_stage_id,
    )
    return sr


def role_rate_for(workflow_stage, role):
    """Per-role rate override for a stage (Q7), or None to fall back to the
    stage's binding cost_rate. Drives worker EARNING (allocation); the stage's
    manufacturing processing_cost stays on ws.cost_rate (role-independent)."""
    if role is None:
        return None
    from production.models import WorkflowStageRoleRate
    rr = WorkflowStageRoleRate.objects.filter(
        workflow_stage=workflow_stage, role=role,
    ).first()
    return rr.cost_rate if rr is not None else None


def adda_cost_summary(adda) -> dict:
    """Per-Adda manufacturing-cost rollup (Q3/Q4/Q8). Honest-NULL: surfaces how
    many stages are unpriced rather than coercing NULL→0 (which would silently
    understate true cost). total_cost sums only frozen, priced rows.
    """
    from django.db.models import Sum
    from production.models import AddaStageRecord
    rows = list(
        AddaStageRecord.objects.filter(adda=adda)
        .select_related('workflow_stage__stage')
        .order_by('workflow_stage__order')
    )
    stages = [{
        'stage': sr.workflow_stage.stage.name,
        'method': sr.cost_method_snapshot or sr.workflow_stage.cost_method,
        'cost': sr.processing_cost,
        'frozen': sr.cost_frozen_at is not None,
    } for sr in rows]
    total = (
        AddaStageRecord.objects.filter(adda=adda, processing_cost__isnull=False)
        .aggregate(s=Sum('processing_cost'))['s']
    )
    unpriced = sum(
        1 for sr in rows
        if sr.completed_at is not None and sr.processing_cost is None
    )
    return {'stages': stages, 'total_cost': total, 'unpriced_count': unpriced}
