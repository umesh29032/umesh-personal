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

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F, Max

from production.models import Adda, AddaStageRecord, Product, Stage, WorkflowStage

from ._shared import _ensure_can_manage


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
    return WorkflowStage.objects.create(
        product=product, stage=stage, order=next_order,
    )


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
