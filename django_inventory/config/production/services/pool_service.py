"""THE piece-pool chokepoint (Foundation S4 — addendum C1/C2/D2/D3, Option B).

Single writer of `StagePoolSnapshot` AND `WorkerStageAllocation`, and the single reader
of pool good. Two halves of one domain:

  SNAPSHOT (Phase 2) — the frozen good a stage makes available, handler-dispatched (no
    stage-name conditionals): Cutting → AddaProductSizeColorPieceBreakdown (single source of
    truth, C1/B — never duplicated); downstream → StagePoolSnapshot (materialised write-once
    at complete; reopen clears + refreezes).
  DRAW-DOWN (Phase 3) — a worker is allocated a slice of a CONSUMING stage's available
    upstream pool (`available = pool_good(source)↓grain + recovered − Σ non-voided
    allocations`); over-allocation refused (pool integrity); void returns qty.

Named pool_service (NOT allocation_service) deliberately — `expense.services.
allocation_service` is the unrelated legacy era-A earning path. This is THE production-truth
pool, no money.

🔒 DECOUPLING CONTRACT (owner 2026-06-14): this module reads pool good (production truth) and
writes StagePoolSnapshot + WorkerStageAllocation (capacity/quantity). It MUST NOT import or
call cost_service / stage_rate_service / settlement, and allocated_quantity MUST NOT feed any
earning / rate / costing / settlement math. Costing-method behaviour (per_layer / fixed_cost /
per_piece …) lives on WorkflowStage.cost_method + cost_service, independent of allocation.
Money is decided only at settlement (good × frozen rate). Guarded by the no-money +
import-decoupling tests in test_s4_allocation.py.

Lock (D2): the draw-down serialises on a pg advisory XACT lock in the TWO-INT namespace
`(_POOL_LOCK_CLASS, objid(source_sr, color, size))` — a DIFFERENT namespace from settlement's
single-bigint `pg_advisory_xact_lock(5374)`, so the production-allocation and settlement lock
domains share no lock object (disjoint, no deadlock). Never locks AddaStageRecord.

Current-flow note (2026-06-14): cutting is the only piece stage and nothing downstream
consumes it → no SPS rows materialise and `allocate` is unreached in the live 4-stage flow
(pool source, no consumer). Built ahead of future piece-consuming stages (e.g. stitching);
exercised via tests today.
"""
import logging
from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection, transaction

from production.constants import ALLOC_DIM_COLOR_SIZE, ALLOC_DIM_NONE, ALLOC_DIM_QUANTITY

logger = logging.getLogger('production')

# Distinct from settlement's bigint 5374 — AND the two-int form is a separate advisory
# namespace from the single-bigint form, so collision is impossible either way.
_POOL_LOCK_CLASS = 5375
_INT4_MAX = 2_147_483_647


def _handler_for(stage_record):
    """The registered StageHandler for a stage record's stage code, or None."""
    from production.stages.base import registry
    code = stage_record.workflow_stage.stage.code
    return registry.get(code) if registry.has(code) else None


# ── Snapshot half (Phase 2) ──────────────────────────────────────────────────

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


# ── Draw-down half (Phase 3) ─────────────────────────────────────────────────

def _objid(source_sr_id: int, color_id, size_id) -> int:
    """Deterministic int4 key for (source stage record, colour, size). Stable across
    processes (no Python hash randomisation); collisions only cost extra serialisation,
    never correctness."""
    return (source_sr_id * 1_000_003 + (color_id or 0) * 1009 + (size_id or 0)) % _INT4_MAX


def _acquire_pool_lock(source_sr_id: int, color_id, size_id) -> None:
    """Hold the per-(source, dims) advisory xact lock. Caller MUST be atomic."""
    with connection.cursor() as cur:
        cur.execute('SELECT pg_advisory_xact_lock(%s, %s)',
                    [_POOL_LOCK_CLASS, _objid(source_sr_id, color_id, size_id)])


def _upstream_pool_source(consuming_sr):
    """The nearest preceding stage record in this Adda's flow (by workflow_stage.order)
    whose stage is a piece-pool participant (allocation_dimensions != NONE). None if there
    is no upstream pool (e.g. the consuming stage is itself the first piece stage)."""
    from production.models import AddaStageRecord
    return (
        AddaStageRecord.objects
        .filter(adda_id=consuming_sr.adda_id,
                workflow_stage__order__lt=consuming_sr.workflow_stage.order)
        .exclude(workflow_stage__allocation_dimensions=ALLOC_DIM_NONE)
        .select_related('workflow_stage')
        .order_by('-workflow_stage__order')
        .first()
    )


def recovered_alter(source_sr, color_id=None, size_id=None) -> Decimal:
    """Pool top-up from rework-recovered pieces at the source stage/dims (M-7 accessor).
    Returns 0 until the Rework module ships — defined now so the pool formula is stable."""
    return Decimal('0')


def found_missing(source_sr, color_id=None, size_id=None) -> Decimal:
    """Pool top-up from reappeared-missing pieces (M-7 accessor). 0 until Missing ships."""
    return Decimal('0')


def _source_good_for(consuming_sr, source_sr, color_id, size_id) -> Decimal:
    """Source good aggregated DOWN to the consuming stage's grain (monotonicity guarantees
    grain(consuming) ≤ grain(source), so this only ever coarsens = sum)."""
    src = pool_good(source_sr)   # {(color_id, size_id): Decimal}
    dim = consuming_sr.workflow_stage.allocation_dimensions
    if dim == ALLOC_DIM_QUANTITY:
        return sum(src.values(), Decimal('0'))            # coarsen: Σ over all (c,s)
    return src.get((color_id, size_id), Decimal('0'))     # COLOR_SIZE: exact dim


def _allocated_for(consuming_sr, color_id, size_id) -> Decimal:
    from django.db.models import Sum

    from production.models import WorkerStageAllocation
    agg = (WorkerStageAllocation.objects
           .filter(stage_record=consuming_sr, color_id=color_id, size_id=size_id,
                   voided_at__isnull=True)
           .aggregate(q=Sum('allocated_quantity')))
    return agg['q'] or Decimal('0')


def available(consuming_sr, color_id=None, size_id=None) -> Decimal:
    """`pool_good(source)↓grain + recovered − Σ non-voided allocations` at the consuming
    stage's dims. 0 when there is no upstream pool source."""
    source = _upstream_pool_source(consuming_sr)
    if source is None:
        return Decimal('0')
    return (_source_good_for(consuming_sr, source, color_id, size_id)
            + recovered_alter(source, color_id, size_id)
            - _allocated_for(consuming_sr, color_id, size_id))


def _validate_dims(consuming_sr, color_id, size_id):
    """Allocation dims must match the consuming stage's grain (NONE = not allocatable)."""
    dim = consuming_sr.workflow_stage.allocation_dimensions
    if dim == ALLOC_DIM_NONE:
        raise ValidationError("This stage is not a piece-pool stage — nothing to allocate.")
    if dim == ALLOC_DIM_COLOR_SIZE and (color_id is None or size_id is None):
        raise ValidationError("Colour and size are required to allocate on this stage.")
    if dim == ALLOC_DIM_QUANTITY and (color_id is not None or size_id is not None):
        raise ValidationError("This stage allocates at quantity grain — no colour/size.")


@transaction.atomic
def allocate(consuming_sr, worker, *, qty, actor, color_id=None, size_id=None):
    """Allocate `worker` a `qty` slice of `consuming_sr`'s available upstream pool.
    Management only. Refuses if qty exceeds available (pool integrity — always on,
    independent of ENFORCE_ALLOCATION_BOUND). NO money. Returns the WorkerStageAllocation."""
    from accounts.services import MANAGEMENT_ROLES, user_has_role
    from production.models import WorkerStageAllocation

    if not user_has_role(actor, MANAGEMENT_ROLES):
        raise PermissionDenied("Only management can allocate stage work.")
    qty = Decimal(str(qty))
    if qty <= 0:
        raise ValidationError("Allocated quantity must be greater than 0.")
    _validate_dims(consuming_sr, color_id, size_id)

    source = _upstream_pool_source(consuming_sr)
    if source is None:
        raise ValidationError("No upstream pool to allocate from.")
    # Serialise the read-compute-write on this (source, dims) — no over-allocation.
    _acquire_pool_lock(source.pk, color_id, size_id)
    avail = available(consuming_sr, color_id, size_id)
    if qty > avail:
        raise ValidationError(
            f"Cannot allocate {qty}: only {avail} available in the pool for these dimensions.")
    wsa = WorkerStageAllocation.objects.create(
        stage_record=consuming_sr, worker=worker, color_id=color_id, size_id=size_id,
        allocated_quantity=qty, created_by=actor)
    logger.info("pool.allocate sr=%s worker=%s c=%s s=%s qty=%s by=%s",
                consuming_sr.pk, getattr(worker, 'pk', worker), color_id, size_id, qty,
                getattr(actor, 'pk', None))
    return wsa


def worker_allocated(stage_record, worker, color_id=None, size_id=None) -> Decimal:
    """Σ active (non-voided) allocated_quantity for (worker, stage_record, dims) — the
    TOTAL across ALL allocation rows, never a single row. Multiple allocations sum; voided
    rows excluded; reallocation reflects the current active total."""
    from django.db.models import Sum

    from production.models import WorkerStageAllocation
    agg = (WorkerStageAllocation.objects
           .filter(stage_record=stage_record, worker=worker,
                   color_id=color_id, size_id=size_id, voided_at__isnull=True)
           .aggregate(q=Sum('allocated_quantity')))
    return agg['q'] or Decimal('0')


def preview_bound_violations(adda=None) -> list:
    """S5 / S4-005 rollout safety — the PRE-FLIP audit. Returns every COMPLETED contribution
    set that WOULD fail the allocation bound if ENFORCE_ALLOCATION_BOUND were enabled, on
    pool-participant stages (allocation_dimensions != NONE): `over_bound` (Σ good+alter+missing
    > Σ active allocated) or `unallocated` (allocated=0, reported>0). Read-only. `adda=None`
    scans all; else one Adda. Run this + clear violations BEFORE flipping the flag on."""
    from collections import defaultdict

    from django.db.models import Sum

    from production.models import (
        AddaStageRecord, WorkerStageAllocation, WorkerStageContribution, WorkerStageTask,
    )
    done = (WorkerStageTask.Status.COMPLETED, WorkerStageTask.Status.VERIFIED)
    srs = (AddaStageRecord.objects
           .exclude(workflow_stage__allocation_dimensions=ALLOC_DIM_NONE)
           .select_related('workflow_stage__stage', 'adda'))
    if adda is not None:
        srs = srs.filter(adda=adda)
    out = []
    for sr in srs:
        produced = defaultdict(lambda: Decimal('0'))
        for c in (WorkerStageContribution.objects
                  .filter(task__stage_record=sr, task__status__in=done)
                  .select_related('task')):
            produced[(c.task.worker_id, c.color_id, c.size_id)] += (
                c.good_quantity + c.alter_quantity + c.missing_quantity)
        for (worker_id, color_id, size_id), got in produced.items():
            allocated = (WorkerStageAllocation.objects
                         .filter(stage_record=sr, worker_id=worker_id,
                                 color_id=color_id, size_id=size_id, voided_at__isnull=True)
                         .aggregate(q=Sum('allocated_quantity'))['q'] or Decimal('0'))
            kind = None
            if allocated == 0 and got > 0:
                kind = 'unallocated'
            elif got > allocated:
                kind = 'over_bound'
            if kind:
                out.append({
                    'adda': sr.adda.code, 'stage': sr.workflow_stage.stage.code,
                    'worker_id': worker_id, 'color_id': color_id, 'size_id': size_id,
                    'reported': got, 'allocated': allocated, 'kind': kind,
                })
    return out


def bound_soft_warning(task):
    """S5 / S4-005 — non-blocking over-allocation hint for the worker report UI. Returns a
    message if this task's good+alter+missing would exceed the worker's allocation on a
    pool-participant stage (else None). NEVER raises; independent of ENFORCE_ALLOCATION_BOUND
    (it warns during the ramp, before the hard gate is ever turned on)."""
    from collections import defaultdict

    sr = task.stage_record
    if sr.workflow_stage.allocation_dimensions == ALLOC_DIM_NONE:
        return None
    reported = defaultdict(lambda: Decimal('0'))
    for c in task.contributions.all():
        reported[(c.color_id, c.size_id)] += (
            c.good_quantity + c.alter_quantity + c.missing_quantity)
    for (color_id, size_id), got in reported.items():
        if got > worker_allocated(sr, task.worker, color_id, size_id):
            return ("Heads up: reported quantity exceeds what's allocated to this worker for "
                    "these dimensions. Allowed now, but refused once allocation enforcement is on.")
    return None


def check_allocation_bound(task) -> None:
    """Strict complete-time bound (S4/Phase 4, I-5). For each DIMENSION the worker actually
    REPORTED on a pool-participant stage, refuse if Σ(good+alter+missing) exceeds Σ active
    allocated for (worker, stage, dims). Evaluated per-reported-dimension and independently:
    an allocated-but-unreported dim is never checked (no need to consume all); a reported-
    but-UNALLOCATED dim has allocated=0 → refused.

    PRODUCTION-CAPACITY ONLY: reads good/alter/missing (observations) + allocated_quantity
    (capacity). Reads NO verified_quantity / settlement / rate / earning / cost_method.
    No-op unless ENFORCE_ALLOCATION_BOUND is on AND the stage is a pool participant
    (allocation_dimensions != NONE).
    """
    from collections import defaultdict

    from django.conf import settings

    if not getattr(settings, 'ENFORCE_ALLOCATION_BOUND', False):
        return
    sr = task.stage_record
    if sr.workflow_stage.allocation_dimensions == ALLOC_DIM_NONE:
        return   # pre-piece / non-pool stage — never bounded

    # Σ(good+alter+missing) grouped by the dimensions the worker REPORTED.
    reported = defaultdict(lambda: Decimal('0'))
    for c in task.contributions.all():
        reported[(c.color_id, c.size_id)] += (
            c.good_quantity + c.alter_quantity + c.missing_quantity)

    source = _upstream_pool_source(sr)
    for (color_id, size_id), produced in sorted(
            reported.items(), key=lambda kv: (kv[0][0] or 0, kv[0][1] or 0)):
        # Serialise vs concurrent allocate/void on this (source, dims).
        if source is not None:
            _acquire_pool_lock(source.pk, color_id, size_id)
        allocated = worker_allocated(sr, task.worker, color_id, size_id)
        if produced > allocated:
            raise ValidationError(
                f"Reported {produced} for this dimension but only {allocated} is allocated "
                f"to the worker on this stage. Allocate more (or correct the report) first.")


@transaction.atomic
def void_allocation(wsa, *, actor):
    """Void an allocation (correction) — qty returns to `available`. Management only.
    Append-only (sets voided_at; never deletes). Idempotent. Held under the pool lock so
    the credit-back serialises with concurrent allocates."""
    from django.utils import timezone

    from accounts.services import MANAGEMENT_ROLES, user_has_role
    from production.models import WorkerStageAllocation

    if not user_has_role(actor, MANAGEMENT_ROLES):
        raise PermissionDenied("Only management can void an allocation.")
    row = WorkerStageAllocation.objects.select_for_update().get(pk=wsa.pk)
    if row.voided_at is not None:
        return row   # idempotent
    source = _upstream_pool_source(row.stage_record)
    if source is not None:
        _acquire_pool_lock(source.pk, row.color_id, row.size_id)
    row.voided_at = timezone.now()
    row.save(update_fields=['voided_at', 'updated_at'])
    logger.info("pool.void sr=%s wsa=%s by=%s",
                row.stage_record_id, row.pk, getattr(actor, 'pk', None))
    return row
