"""Piece-pool read + materialisation dispatch (Foundation S4 / D2-D3, Option B).

Thin dispatcher over the stage HANDLER's pool strategy — NO stage-name conditionals
(open-closed). The handler decides the source:
  • Cutting   → AddaProductSizeColorPieceBreakdown (the single source of truth, C1/B)
  • downstream → StagePoolSnapshot (materialised write-once at complete)

Pool-only — touches NO money/settlement/costing. The allocation draw-down (Phase 3)
will compute `available = pool_good − Σ non-voided allocations` under the D2 advisory
lock keyed by (source_stage_record_id, color_id, size_id); this module is the read +
freeze foundation it builds on.

Current-flow note (2026-06-14): with cutting the only piece stage and nothing downstream
consuming it, materialisation writes no rows today (cutting uses APSCPB; pre-piece stages
are NONE). The machinery lands ahead of future piece-consuming stages (e.g. stitching).
"""
import logging

from django.db import transaction

logger = logging.getLogger('production')


def _handler_for(stage_record):
    """The registered StageHandler for a stage record's stage code, or None."""
    from production.stages.base import registry
    code = stage_record.workflow_stage.stage.code
    return registry.get(code) if registry.has(code) else None


def pool_good(stage_record) -> dict:
    """The frozen good this stage makes available to allocate downstream, as
    ``{(color_id, size_id): Decimal}`` at its grain. Handler-dispatched (cutting→APSCPB,
    downstream→StagePoolSnapshot). Empty dict for an unregistered/NONE-grain stage."""
    handler = _handler_for(stage_record)
    return handler.pool_good(stage_record) if handler is not None else {}


@transaction.atomic
def materialize_stage_pool(stage_record) -> int:
    """Freeze this stage's pool good (write-once) via the handler's strategy. Returns
    the number of StagePoolSnapshot rows written (0 for cutting — APSCPB is its source —
    and for NONE-grain / unregistered stages). Call at the producing stage's complete."""
    handler = _handler_for(stage_record)
    if handler is None:
        return 0
    n = handler.materialize_pool(stage_record)
    if n:
        logger.info("pool.materialize sr=%s rows=%s", stage_record.pk, n)
    return n


@transaction.atomic
def clear_stage_pool(stage_record) -> int:
    """Delete a stage's StagePoolSnapshot rows (reopen clears + refreezes — the immutable
    snapshot is rebuilt on re-complete). No-op for cutting (APSCPB is cleared by cutting's
    own reopen). Returns rows deleted. Wired into reopen with the Era-A guard (Phase 5)."""
    from production.models import StagePoolSnapshot
    deleted, _ = StagePoolSnapshot.objects.filter(stage_record=stage_record).delete()
    if deleted:
        logger.info("pool.clear sr=%s rows=%s", stage_record.pk, deleted)
    return deleted
