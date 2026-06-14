"""Product → WorkflowStage flow management.

YEH FILE KYU HAI?
─────────────────
Production flow = ordered list of Stage rows per Product. Admin yeh
manage karta hai Product Flow page se. Yahan ke services CRUD atomic
karte hain aur safety checks lagaate hain (Adda already-running waale
stages delete na ho sake, etc).

Pattern: views call service; service raises ValidationError on guard
failure; @transaction.atomic ensures order remains consistent across
swaps (no half-applied reorders).
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F, Max

from production.constants import (
    ALLOC_DIM_COLOR_SIZE, ALLOC_DIM_NONE, ALLOC_DIM_QUANTITY,
)
from production.models import (
    Adda, AddaStageRecord, AllocationDimensions, CostMethod, Product, Stage,
    WorkflowStage,
)

from ._shared import _ensure_can_manage

# Piece-pool grain ranks (S4/D1). NONE is excluded — pre-piece stages do NOT
# participate in the chain. Among PARTICIPANTS, finer = higher rank; grain may
# only coarsen (non-increasing) downstream. POOL-ONLY — never gates settlement/cost.
_GRAIN_RANK = {ALLOC_DIM_COLOR_SIZE: 2, ALLOC_DIM_QUANTITY: 1}


def _validate_grain_monotonicity(product: Product) -> None:
    """Refuse a flow where a piece-pool stage is FINER than an earlier piece-pool
    stage (re-fining downstream = inventing per-colour data). Checks only non-NONE
    (piece-pool) stages in flow order; NONE (pre-piece) stages are skipped — so the
    legitimate layering(NONE)→cutting(COLOR_SIZE) step is not a violation. Cutting,
    the first piece-pool stage, is the source (finest)."""
    participants = [
        ws for ws in WorkflowStage.objects.filter(product=product).order_by('order')
        if ws.allocation_dimensions != ALLOC_DIM_NONE
    ]
    prev_rank = None
    prev_label = None
    for ws in participants:
        rank = _GRAIN_RANK[ws.allocation_dimensions]
        if prev_rank is not None and rank > prev_rank:
            raise ValidationError(
                f"'{ws.stage.name}' tracks a finer piece-pool grain "
                f"({ws.get_allocation_dimensions_display()}) than the earlier "
                f"'{prev_label}'. Piece-pool grain may only coarsen downstream — "
                "it can never re-fine.")
        prev_rank, prev_label = rank, ws.stage.name


@transaction.atomic
def set_stage_grain(*, user, workflow_stage: WorkflowStage, allocation_dimensions: str) -> WorkflowStage:
    """Set a WorkflowStage's PIECE-POOL grain (S4/D1). POOL-ONLY — does not touch
    settlement (credits_workers) or costing (cost_method). Validates monotonicity
    across the product's flow (rolls back on violation)."""
    _ensure_can_manage(user)
    if allocation_dimensions not in AllocationDimensions.values:
        raise ValidationError(f"Invalid allocation dimensions: {allocation_dimensions!r}")
    workflow_stage.allocation_dimensions = allocation_dimensions
    workflow_stage.save(update_fields=['allocation_dimensions', 'updated_at'])
    _validate_grain_monotonicity(workflow_stage.product)
    return workflow_stage


@transaction.atomic
def add_stage_to_product_flow(*, user, product: Product, stage: Stage) -> WorkflowStage:
    """Append a stage to the end of a product's flow.

    Raises ValidationError if:
      - stage already exists in flow (unique_together would IntegrityError otherwise)
      - stage is inactive (admin must reactivate first)
    """
    _ensure_can_manage(user)
    if not stage.is_active:
        raise ValidationError(f"Stage '{stage.name}' is inactive — reactivate it first.")
    if WorkflowStage.objects.filter(product=product, stage=stage).exists():
        raise ValidationError(f"'{stage.name}' is already in this product's flow.")

    # Compute next order = (current max + 1). If flow is empty, start at 1.
    next_order = (
        WorkflowStage.objects.filter(product=product).aggregate(m=Max('order'))['m']
        or 0
    ) + 1
    # Seed the binding cost from the Stage library defaults (admin can edit
    # later via set_stage_cost). cost_rate stays NULL if no default seeded —
    # surfaced as an "unpriced" badge; freeze tolerates it (succeed-and-flag).
    # S4/D1: seed the piece-pool grain from the stage handler's pool_grain
    # (data-driven; NONE if no handler registered). POOL-ONLY — independent of
    # cost_method / credits_workers above.
    from production.stages.base import registry
    pool_grain = (
        registry.get(stage.code).pool_grain
        if registry.has(stage.code) else ALLOC_DIM_NONE
    )
    ws = WorkflowStage.objects.create(
        product=product, stage=stage, order=next_order,
        cost_method=stage.default_cost_method or CostMethod.PER_PIECE,
        cost_rate=stage.default_cost_rate,
        allocation_dimensions=pool_grain,
    )
    # A finer piece-pool stage appended after a coarser one is illegal (re-fining).
    _validate_grain_monotonicity(product)
    return ws


@transaction.atomic
def remove_stage_from_product_flow(*, user, workflow_stage: WorkflowStage) -> None:
    """Remove a stage from a product's flow + close the order gap.

    Refuses to delete when:
      - any Adda is currently on this stage (current_stage FK PROTECT)
      - any AddaStageRecord references it (history would be orphaned)
      - this is the product's last remaining stage (flow mandatory)

    After delete, all higher-order stages shift down by 1 so order stays
    contiguous (1, 2, 3, ...).
    """
    _ensure_can_manage(user)
    product = workflow_stage.product
    removed_order = workflow_stage.order

    if WorkflowStage.objects.filter(product=product).count() <= 1:
        raise ValidationError(
            "Cannot remove the last stage — products need at least one stage."
        )
    if Adda.objects.filter(current_stage=workflow_stage).exists():
        raise ValidationError(
            f"An Adda is currently at '{workflow_stage.stage.name}'. "
            "Wait for it to advance before removing this stage."
        )
    if AddaStageRecord.objects.filter(workflow_stage=workflow_stage).exists():
        raise ValidationError(
            f"'{workflow_stage.stage.name}' has historical records on completed Addas. "
            "Removing it would orphan that history."
        )
    # Cost-grouping guard: other stages bill their labour at this one. Removing
    # it would leave them pointing at nothing (SET_NULL would silently
    # un-group + un-price them). Force the admin to re-home first.
    if workflow_stage.billed_stages.exists():
        raise ValidationError(
            f"Other stages are billed at '{workflow_stage.stage.name}'. "
            "Re-home their cost grouping before removing this stage."
        )

    workflow_stage.delete()
    # Close the gap: every stage with order > removed_order shifts down by 1.
    (
        WorkflowStage.objects
        .filter(product=product, order__gt=removed_order)
        .update(order=F('order') - 1)
    )


@transaction.atomic
def move_stage_in_product_flow(*, user, workflow_stage: WorkflowStage, direction: str) -> None:
    """Swap order with the neighbor in the given direction ('up' or 'down').

    No-op (no error) at the ends — pressing Up on the first stage just stays.
    """
    _ensure_can_manage(user)
    if direction not in ('up', 'down'):
        raise ValidationError(f"Invalid direction: {direction!r}")

    product = workflow_stage.product
    # F3 (hostile-review fix 2026-06-14): never reorder a flow while an Adda is in-flight.
    # Reordering changes stage `order` → changes pool_service._upstream_pool_source for an
    # active Adda → the void/allocate source-resolution race (S4-VOID-007). The upstream
    # pool source must stay STABLE for an active Adda's lifetime. Terminal Addas
    # (completed/cancelled) don't constrain it.
    if (Adda.objects.filter(product=product)
            .exclude(status__in=(Adda.Status.COMPLETED, Adda.Status.CANCELLED))
            .exists()):
        raise ValidationError(
            "Cannot reorder this product's flow while an Adda is in progress — the upstream "
            "pool source must stay stable for the life of an active Adda. Complete or cancel "
            "the in-flight Addas first.")
    if direction == 'up':
        neighbor = (
            WorkflowStage.objects
            .filter(product=product, order__lt=workflow_stage.order)
            .order_by('-order').first()
        )
    else:
        neighbor = (
            WorkflowStage.objects
            .filter(product=product, order__gt=workflow_stage.order)
            .order_by('order').first()
        )
    if neighbor is None:
        return  # At an end; silent no-op

    # Two-step swap because (product, order) is unique_together — can't briefly
    # collide. Park current at a guaranteed-free slot first.
    parking_order = (
        WorkflowStage.objects.filter(product=product).aggregate(m=Max('order'))['m']
        or 0
    ) + 100
    a_order = workflow_stage.order
    b_order = neighbor.order

    workflow_stage.order = parking_order
    workflow_stage.save(update_fields=['order'])
    neighbor.order = a_order
    neighbor.save(update_fields=['order'])
    workflow_stage.order = b_order
    workflow_stage.save(update_fields=['order'])

    # Re-validate cost grouping after the swap. A reorder can otherwise place a
    # grouped (member) stage AFTER the payer it bills to, which would freeze the
    # payer before the member's work. Raising here rolls back the atomic swap.
    bad = WorkflowStage.objects.filter(
        product=product, cost_billed_at__isnull=False,
        cost_billed_at__order__lte=F('order'),
    )
    if bad.exists():
        raise ValidationError(
            "This reorder would place a stage at or after the stage it is billed "
            "at. Ungroup the cost first, then reorder."
        )
    # S4/D1: a reorder can place a finer piece-pool stage after a coarser one
    # (re-fining). Re-validate; raising rolls back the atomic swap.
    _validate_grain_monotonicity(product)


def _validate_cost_grouping(ws: WorkflowStage, method: str, rate, billed_at) -> None:
    """Validate a proposed cost config for one WorkflowStage (R1 + R3 guards).

    billed_at = the payer WorkflowStage (this stage is a grouped MEMBER), or
    None (this stage is SELF-PAID / a payer). Raises ValidationError on any
    violation. This is the authoritative boundary (CLAUDE rule #4) — the
    flow-editor view + any future form must route through set_stage_cost.
    """
    if billed_at is not None:
        # ── This stage is a grouped MEMBER → billed at `billed_at` ──────────
        # A payer-with-members can't also become a member (no 2-level chains).
        if ws.pk and ws.billed_stages.exists():
            raise ValidationError(
                "This stage is a paying stage for others — it cannot also be grouped."
            )
        if billed_at.product_id != ws.product_id:
            raise ValidationError("The paying stage must be in the same product flow.")
        if billed_at.pk == ws.pk:
            raise ValidationError("A stage cannot be billed at itself.")
        if billed_at.order <= ws.order:
            raise ValidationError("The paying stage must come later in the flow.")
        if billed_at.cost_billed_at_id is not None:
            raise ValidationError(
                "Cannot bill at a stage that is itself grouped (single-hop only)."
            )
        if billed_at.cost_rate is None:
            raise ValidationError("Set a rate on the paying stage first.")
        if billed_at.cost_method == CostMethod.FIXED:
            raise ValidationError("A fixed-cost stage cannot be the payer for a group.")
    else:
        # ── This stage is SELF-PAID / a payer → must be priced ──────────────
        if rate is None:
            raise ValidationError("A self-paid stage must have a cost rate.")
        if rate <= 0:
            raise ValidationError("Cost rate must be greater than 0.")
        # A payer with grouped members can't be fixed_cost (no per-unit qty).
        if ws.pk and ws.billed_stages.exists() and method == CostMethod.FIXED:
            raise ValidationError(
                "A paying stage with grouped members cannot use the fixed-cost method."
            )


@transaction.atomic
def set_stage_cost(
    *, user, workflow_stage: WorkflowStage,
    cost_method: str, cost_rate, cost_billed_at_id=None,
) -> WorkflowStage:
    """Set the binding cost config for a WorkflowStage (R1 mandatory rate + R3
    grouping). Parses + validates, then writes only the cost columns.

    cost_rate: '', None, or a numeric string/Decimal. Empty → NULL (only valid
    for a grouped member). cost_billed_at_id: pk of the payer WorkflowStage, or
    falsy for self-paid.
    """
    _ensure_can_manage(user)

    # Parse rate.
    rate = None
    if cost_rate not in (None, ''):
        try:
            rate = Decimal(str(cost_rate))
        except (InvalidOperation, ValueError):
            raise ValidationError("Cost rate must be a number.")

    # Resolve payer (cost grouping target).
    billed_at = None
    if cost_billed_at_id:
        billed_at = WorkflowStage.objects.filter(pk=cost_billed_at_id).first()
        if billed_at is None:
            raise ValidationError("Selected paying stage not found.")

    method = cost_method or CostMethod.PER_PIECE
    if method not in CostMethod.values:
        raise ValidationError(f"Invalid cost method: {method!r}")

    _validate_cost_grouping(workflow_stage, method, rate, billed_at)

    workflow_stage.cost_method = method
    # A grouped member's own rate is irrelevant — null it to avoid confusion.
    workflow_stage.cost_rate = None if billed_at is not None else rate
    workflow_stage.cost_billed_at = billed_at
    workflow_stage.save(update_fields=[
        'cost_method', 'cost_rate', 'cost_billed_at', 'updated_at',
    ])
    return workflow_stage
