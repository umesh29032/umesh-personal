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


# GAP-1 grain (registry #6, mirrors adda_service.FABRIC_GROUPS_PROVIDER):
# patterns_ai registers mandatory_pattern_ids_for_product(product) -> set[int].
# None / failure / <2 mandatory patterns ⇒ legacy per-dimension math (fail-open).
MANDATORY_PATTERNS_PROVIDER = None


def _upstream_pool_sources(consuming_sr):
    """ALL stage records at the nearest preceding pool-participant ORDER — one per
    cutting lane (GAP-1, frozen lifecycle §2: the ops pool is the Σ-over-streams
    read; `.first()` used to pick ONE arbitrary lane). Empty list = no upstream."""
    from production.models import AddaStageRecord
    qs = (
        AddaStageRecord.objects
        .filter(adda_id=consuming_sr.adda_id,
                workflow_stage__order__lt=consuming_sr.workflow_stage.order)
        .exclude(workflow_stage__allocation_dimensions=ALLOC_DIM_NONE)
        .select_related('workflow_stage')
        .order_by('-workflow_stage__order', 'id')
    )
    sources = []
    top_order = None
    for sr in qs:
        if top_order is None:
            top_order = sr.workflow_stage.order
        if sr.workflow_stage.order != top_order:
            break
        sources.append(sr)
    return sources


def _upstream_pool_source(consuming_sr):
    """Back-compat single-source accessor (panel labels, lock anchor): the first
    of `_upstream_pool_sources` — deterministic (order, id)."""
    sources = _upstream_pool_sources(consuming_sr)
    return sources[0] if sources else None


# OP-1: public name for panel/read callers (the underscore original predates
# external readers; same object — pool_service stays the one pool reader).
def upstream_pool_source(consuming_sr):
    return _upstream_pool_source(consuming_sr)


def recovered_alter(source_sr, color_id=None, size_id=None) -> Decimal:
    """Pool top-up from rework-recovered pieces at the source stage/dims (M-7 accessor).
    Returns 0 until the Rework module ships — defined now so the pool formula is stable."""
    return Decimal('0')


def found_missing(source_sr, color_id=None, size_id=None) -> Decimal:
    """Pool top-up from reappeared-missing pieces (M-7 accessor). 0 until Missing ships."""
    return Decimal('0')


def _source_good_for(consuming_sr, source_srs, color_id, size_id) -> Decimal:
    """Σ source good across ALL lane sources (GAP-1), aggregated DOWN to the consuming
    stage's grain (monotonicity guarantees grain(consuming) ≤ grain(source), so this
    only ever coarsens = sum). Accepts one SR (legacy callers) or a list."""
    if not isinstance(source_srs, (list, tuple)):
        source_srs = [source_srs]
    dim = consuming_sr.workflow_stage.allocation_dimensions
    total = Decimal('0')
    for source_sr in source_srs:
        src = pool_good(source_sr)   # {(color_id, size_id): Decimal}
        if dim == ALLOC_DIM_QUANTITY:
            total += sum(src.values(), Decimal('0'))       # coarsen: Σ over all (c,s)
        else:
            total += src.get((color_id, size_id), Decimal('0'))   # exact dim
    return total


def _mandatory_pattern_needs(adda):
    """{pattern_id: pieces_per_garment} for the product's MANDATORY Production
    Components, via the Blueprint provider. {} when the provider is absent, fails,
    or reports <2 mandatory patterns — callers then use the legacy per-dim math
    (single-component products are byte-identical by construction: min over one
    pattern IS its piece count)."""
    if MANDATORY_PATTERNS_PROVIDER is None:
        return {}
    try:
        mandatory_ids = set(MANDATORY_PATTERNS_PROVIDER(adda.product) or ())
    except Exception:
        logger.exception('mandatory-patterns provider failed — legacy pool math')
        return {}
    if not mandatory_ids:
        return {}
    from production.models import ProductPatternAssignment
    needs = {
        a.pattern_id: max(a.pieces_count or 1, 1)
        for a in ProductPatternAssignment.objects.filter(
            product=adda.product, pattern_id__in=mandatory_ids)
    }
    return needs if len(needs) >= 2 else {}


def _garment_sets_remaining(consuming_sr, needs, size_id=None) -> Decimal:
    """GARMENT-EQUIVALENT capacity (ratified 2026-07-11, BUNDLE review §Q4):
    per size, min over mandatory components of (Σ cut pieces across ALL lanes ÷
    pieces-per-garment) — minus Σ active allocations at that size (every colour:
    a garment spans colours, so sets are SIZE-grain; cloth colour is a component
    attribute). size_id=None ⇒ Σ over all sizes (QUANTITY-grain consumers).
    Capacity only — never money (S4 decoupling contract unchanged)."""
    from django.db.models import Sum

    from production.models import CuttingPieceBreakup, WorkerStageAllocation
    rows = (CuttingPieceBreakup.objects
            .filter(cutting_record__stage_record__adda_id=consuming_sr.adda_id,
                    pattern_id__in=needs)
            .values('size_id', 'pattern_id')
            .annotate(n=Sum('count')))
    per_size = {}
    for r in rows:
        per_size.setdefault(r['size_id'], {})[r['pattern_id']] = r['n']
    def sets_of(sz):
        cuts = per_size.get(sz, {})
        return min((cuts.get(pid, 0) // need for pid, need in needs.items()),
                   default=0)
    if size_id is not None:
        sets = Decimal(sets_of(size_id))
        drawn = (WorkerStageAllocation.objects
                 .filter(stage_record=consuming_sr, size_id=size_id,
                         voided_at__isnull=True)
                 .aggregate(q=Sum('allocated_quantity'))['q'] or Decimal('0'))
    else:
        sets = Decimal(sum(sets_of(sz) for sz in per_size))
        drawn = (WorkerStageAllocation.objects
                 .filter(stage_record=consuming_sr, voided_at__isnull=True)
                 .aggregate(q=Sum('allocated_quantity'))['q'] or Decimal('0'))
    return sets - drawn


def _allocated_for(consuming_sr, color_id, size_id) -> Decimal:
    from django.db.models import Sum

    from production.models import WorkerStageAllocation
    agg = (WorkerStageAllocation.objects
           .filter(stage_record=consuming_sr, color_id=color_id, size_id=size_id,
                   voided_at__isnull=True)
           .aggregate(q=Sum('allocated_quantity')))
    return agg['q'] or Decimal('0')


def garment_readiness(adda):
    """GAP-5 approved DERIVE-ONLY panel (BUNDLE review §6): per size — each
    mandatory Production Component's cut total, sets it supports, the
    bottleneck flag; complete sets; leftover pieces (count − consumed).
    Returns None for single-component products (pieces ARE sets — no panel).
    Reads breakups + assignments + the registry-#6 provider. Stores NOTHING."""
    needs = _mandatory_pattern_needs(adda)
    if not needs:
        return None
    from django.db.models import Sum

    from production.models import CuttingPieceBreakup, ProductPattern, ProductSize
    names = {p.pk: p.name for p in ProductPattern.objects.filter(pk__in=needs)}
    rows = (CuttingPieceBreakup.objects
            .filter(cutting_record__stage_record__adda=adda,
                    pattern_id__in=needs)
            .values('size_id', 'pattern_id')
            .annotate(cut=Sum('count'), consumed=Sum('consumed_count')))
    per_size = {}
    for r in rows:
        per_size.setdefault(r['size_id'], {})[r['pattern_id']] = r
    sizes = []
    total_sets = 0
    total_pieces = 0
    for size in ProductSize.objects.filter(product=adda.product).order_by(
            'display_order'):
        cuts = per_size.get(size.pk)
        if not cuts:
            continue
        comps = []
        for pid, need in needs.items():
            cut = (cuts.get(pid) or {}).get('cut', 0) or 0
            total_pieces += cut
            comps.append({'name': names.get(pid, pid), 'cut': cut,
                          'need': need, 'sets': cut // need})
        sets = min(c['sets'] for c in comps)
        def _free_sets(pid, need):
            row = cuts.get(pid) or {}
            cut_n = row.get('cut') or 0
            used_n = row.get('consumed') or 0
            return (cut_n - used_n) // need
        unbundled = min(_free_sets(pid, need) for pid, need in needs.items())
        for c in comps:
            c['is_min'] = c['sets'] == sets
        total_sets += sets
        sizes.append({'size': size, 'sets': sets, 'components': comps,
                      'blocked': sets == 0, 'unbundled_sets': max(unbundled, 0),
                      'bottleneck': ' + '.join(c['name'] for c in comps
                                               if c['is_min'])})
    leftovers = []
    for b in (CuttingPieceBreakup.objects
              .filter(cutting_record__stage_record__adda=adda)
              .select_related('pattern', 'size')):
        left = b.count - b.consumed_count
        if left > 0:
            leftovers.append({'component': b.pattern.name,
                              'size': b.size.label, 'count': left})
    return {'sizes': sizes, 'total_sets': total_sets,
            'total_pieces': total_pieces, 'leftovers': leftovers}


def available(consuming_sr, color_id=None, size_id=None) -> Decimal:
    """`Σ pool_good(sources)↓grain + recovered − Σ non-voided allocations` at the
    consuming stage's dims — sources = EVERY lane at the nearest upstream order
    (GAP-1). Multi-component products (≥2 mandatory Blueprint patterns) are
    additionally capped by the GARMENT-EQUIVALENT sets remaining at the SIZE
    grain — sewing can never be allocated more sets than every mandatory
    component supports (45 sets ≠ 143 pieces). 0 when no upstream pool."""
    sources = _upstream_pool_sources(consuming_sr)
    if not sources:
        return Decimal('0')
    per_dim = (_source_good_for(consuming_sr, sources, color_id, size_id)
               + recovered_alter(sources[0], color_id, size_id)
               - _allocated_for(consuming_sr, color_id, size_id))
    needs = _mandatory_pattern_needs(consuming_sr.adda)
    if not needs:
        return per_dim
    sets_left = _garment_sets_remaining(consuming_sr, needs, size_id)
    return min(per_dim, sets_left)


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
def allocate(consuming_sr, worker, *, qty, actor, color_id=None, size_id=None, mode='partial'):
    """Allocate `worker` a `qty` slice of `consuming_sr`'s available upstream pool.
    Management only. Refuses if qty exceeds available (pool integrity — ALWAYS on).
    `mode` records the manager's intent (whole|partial) for audit; whole callers
    come through `allocate_whole`. NO money. Returns the WorkerStageAllocation."""
    from accounts.services import MANAGEMENT_ROLES, user_has_role
    from production.models import WorkerStageAllocation

    if not user_has_role(actor, MANAGEMENT_ROLES):
        raise PermissionDenied("Only management can allocate stage work.")
    if mode not in (WorkerStageAllocation.Mode.WHOLE, WorkerStageAllocation.Mode.PARTIAL):
        raise ValidationError("Allocation mode must be 'whole' or 'partial'.")
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
        allocated_quantity=qty, allocation_mode=mode, created_by=actor)
    logger.info("pool.allocate sr=%s worker=%s c=%s s=%s qty=%s mode=%s by=%s",
                consuming_sr.pk, getattr(worker, 'pk', worker), color_id, size_id, qty,
                mode, getattr(actor, 'pk', None))
    return wsa


@transaction.atomic
def allocate_whole(consuming_sr, worker, *, actor, color_id=None, size_id=None):
    """AE-1 (owner bundle model): assign the WHOLE remaining bundle to `worker` in
    one act — the factory's DEFAULT workflow. No quantity is typed; we take the
    entire `available` for these dims and stamp `mode='whole'`. If the bundle was
    already partially allocated, this grabs the REMAINING (owner decision 3).
    Compute-and-write happens inside the pool lock (via `allocate`) so two
    concurrent 'whole' clicks cannot both claim the same remainder. Refuses when
    the bundle has nothing left."""
    _validate_dims(consuming_sr, color_id, size_id)
    source = _upstream_pool_source(consuming_sr)
    if source is None:
        raise ValidationError("No upstream pool to allocate from.")
    # Lock first, THEN read available, THEN allocate — all under the same advisory
    # lock so the remaining qty we hand over cannot be stolen mid-flight.
    _acquire_pool_lock(source.pk, color_id, size_id)
    remaining = available(consuming_sr, color_id, size_id)
    if remaining <= 0:
        raise ValidationError(
            "This bundle is already fully allocated — nothing left to assign.")
    return allocate(consuming_sr, worker, qty=remaining, actor=actor,
                    color_id=color_id, size_id=size_id, mode='whole')


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


def _contribution_load(c) -> Decimal:
    """THE single definition of a contribution row's load against its allocation:
    good + alter + missing + damaged. Both the enforcement (`check_allocation_bound`)
    and the legacy-row audit (`preview_bound_violations`) sum THIS one helper, so the
    over-report bound can never silently diverge between them (e.g. if a 5th
    observation column is ever added, or `damaged` is ever excluded)."""
    return (c.good_quantity + c.alter_quantity
            + c.missing_quantity + c.damaged_quantity)


def preview_bound_violations(adda=None) -> list:
    """Legacy-row audit. The allocation bound is now always-on, so new completions can't
    violate it — this scans PRE-EXISTING COMPLETED contributions (created before the bound
    went hard) that would fail it, on pool-participant stages (allocation_dimensions != NONE):
    `over_bound` (Σ good+alter+missing > Σ active allocated) or `unallocated` (allocated=0,
    reported>0). Read-only. `adda=None`
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
        # AE-1: skip pool PRODUCERS (no upstream source) — their reports create the
        # pool and are never allocated, so they are not bound violations (mirrors
        # check_allocation_bound). Audits only CONSUMING stages.
        if _upstream_pool_source(sr) is None:
            continue
        produced = defaultdict(lambda: Decimal('0'))
        for c in (WorkerStageContribution.objects
                  .filter(task__stage_record=sr, task__status__in=done)
                  .select_related('task')):
            produced[(c.task.worker_id, c.color_id, c.size_id)] += _contribution_load(c)
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


def check_allocation_bound(task) -> None:
    """Strict complete-time bound. For each DIMENSION the worker actually REPORTED on a
    pool-participant stage, refuse if Σ(good+alter+missing+damaged) exceeds Σ active
    allocated for (worker, stage, dims). Evaluated per-reported-dimension and independently:
    an allocated-but-unreported dim is never checked (no need to consume all); a reported-
    but-UNALLOCATED dim has allocated=0 → refused (this also closes the flat-list
    unallocated-pair hole — a worker can never report a (colour,size) pair they were not given).

    AE-1 (owner ruling 2026-07-20): HARD validation, ALWAYS enforced — no feature flag, no
    warning mode. (Previously gated by `ENFORCE_ALLOCATION_BOUND`, now removed; the FAT proved
    the soft/off default let workers over-report.)

    PRODUCTION-CAPACITY ONLY: reads good/alter/missing (observations) + allocated_quantity
    (capacity). Reads NO verified_quantity / settlement / rate / earning / cost_method.
    No-op when the stage is not a pool participant (allocation_dimensions == NONE) OR when the
    stage is a pool PRODUCER (no upstream source) — a producer's workers report to CREATE the
    pool and are never allocated, so there is nothing to over-consume. The bound is a CONSUMER
    rule: you cannot report more than you were allocated FROM an upstream pool.
    """
    from collections import defaultdict

    sr = task.stage_record
    if sr.workflow_stage.allocation_dimensions == ALLOC_DIM_NONE:
        return   # pre-piece / non-pool stage — never bounded

    source = _upstream_pool_source(sr)
    if source is None:
        return   # pool PRODUCER (e.g. cutting / first dimensioned stage) — reports create the pool

    # Σ(good+alter+missing) grouped by the dimensions the worker REPORTED.
    reported = defaultdict(lambda: Decimal('0'))
    for c in task.contributions.all():
        reported[(c.color_id, c.size_id)] += _contribution_load(c)

    for (color_id, size_id), produced in sorted(
            reported.items(), key=lambda kv: (kv[0][0] or 0, kv[0][1] or 0)):
        # Serialise vs concurrent allocate/void on this (source, dims).
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
    the credit-back serialises with concurrent allocates.

    H-2 (owner-approved 2026-07-06): once the worker has SUBMITTED production
    against this allocation's dimension, the void is refused unless the remaining
    allocation still covers the submitted total — an allocation is not a free
    undo lever after work happened. The explicit correction flow is Report
    Review (`set_verified_quantity`): correct the report first, then void."""
    from django.utils import timezone

    from accounts.services import MANAGEMENT_ROLES, user_has_role
    from production.models import (
        WorkerStageAllocation, WorkerStageContribution, WorkerStageTask,
    )

    if not user_has_role(actor, MANAGEMENT_ROLES):
        raise PermissionDenied("Only management can void an allocation.")
    row = WorkerStageAllocation.objects.select_for_update().get(pk=wsa.pk)
    if row.voided_at is not None:
        return row   # idempotent
    source = _upstream_pool_source(row.stage_record)
    if source is not None:
        _acquire_pool_lock(source.pk, row.color_id, row.size_id)
    # Submitted production on this (worker, dims): Σ(verified-else-good + alter
    # + missing) of the worker's completed/verified tasks — verified is the
    # final business truth (owner 2026-07-06), so a Report-Review correction
    # genuinely frees allocation for a subsequent void. Must still fit inside
    # the allocation that would REMAIN after this void.
    done = (WorkerStageTask.Status.COMPLETED, WorkerStageTask.Status.VERIFIED)
    produced = Decimal('0')
    for c in WorkerStageContribution.objects.filter(
            task__stage_record=row.stage_record, task__worker_id=row.worker_id,
            task__status__in=done, color_id=row.color_id, size_id=row.size_id):
        good = c.verified_quantity if c.verified_quantity is not None else c.good_quantity
        produced += good + c.alter_quantity + c.missing_quantity + c.damaged_quantity
    if produced > 0:
        remaining = worker_allocated(
            row.stage_record, row.worker, row.color_id, row.size_id,
        ) - row.allocated_quantity
        if produced > remaining:
            raise ValidationError(
                f"Cannot void: the worker already submitted {produced} for this "
                f"dimension and only {remaining} allocation would remain. Correct "
                "the report in Report Review first (verification), or re-allocate.")
    row.voided_at = timezone.now()
    row.save(update_fields=['voided_at', 'updated_at'])
    logger.info("pool.void sr=%s wsa=%s by=%s",
                row.stage_record_id, row.pk, getattr(actor, 'pk', None))
    return row
