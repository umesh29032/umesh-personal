"""Allocation service — sole writer of StageWorkAssignment (+ its credit).

Earnings are ALLOCATION-DRIVEN: a worker earns for the quantity THEY did, at
the stage's binding rate, frozen at allocation time. This deliberately rejects
the `stage_cost ÷ num_workers` shortcut (workers do different quantities).
"""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from expense.models import StageWorkAssignment, WorkerLedgerEntry
from expense.services import ledger_service
from ._shared import _ensure_management

_CENT = Decimal('0.01')


def item_allocation_summary(bundle_item) -> dict:
    """How much of a CuttingBundleItem is already allocated to workers.

    Returns {'allocated': Decimal, 'remaining': Decimal} — drives the cutting
    workspace allocation UI (shows X/count + defaults the quantity input).
    """
    allocated = (
        StageWorkAssignment.objects
        .filter(bundle_item=bundle_item, voided_at__isnull=True)
        .aggregate(s=Sum('allocated_quantity'))['s'] or Decimal('0')
    )
    remaining = Decimal(bundle_item.count) - allocated
    return {'allocated': allocated, 'remaining': remaining if remaining > 0 else Decimal('0')}


@transaction.atomic
def allocate_stage_work(*, user, stage_record, worker, allocated_quantity,
                        bundle_item=None, bundle=None, size=None, color=None,
                        pattern=None, notes='', entry_date=None):
    """Allocate a slice of a stage's work to a worker + book the earning.

    Per-bundle-item: pass `bundle_item` and size/color/pattern/bundle are
    derived from it (explicit args still win). Rate comes from the stage's
    WorkflowStage.cost_rate (frozen onto the assignment). A grouped stage
    (billed elsewhere) or an unpriced stage has no own rate → allocate at the
    paying stage instead. Quantity must be > 0, and (for item allocation) the
    item can't be over-allocated beyond its cut count.
    """
    _ensure_management(user)

    ws = stage_record.workflow_stage
    if ws.cost_billed_at_id is not None:
        raise ValidationError(
            "This stage's labour is billed at another stage — allocate work "
            "on the paying stage, not this one."
        )
    # Role-based rate (Q7): a worker's role can override the stage rate; falls
    # back to the binding ws.cost_rate. Snapshot freezes it onto the assignment.
    from production.services.cost_service import role_rate_for
    rate = role_rate_for(ws, getattr(worker, 'role', None)) or ws.cost_rate
    if rate is None:
        raise ValidationError("Set a cost rate on this stage before allocating work.")

    qty = Decimal(str(allocated_quantity))
    if qty <= 0:
        raise ValidationError("Allocated quantity must be greater than 0.")

    # Derive work dimensions from the bundle item (explicit args override).
    if bundle_item is not None:
        # Lock the item row so two concurrent allocations can't both pass the
        # over-allocation check (race-safe within this atomic block).
        from production.models import CuttingBundleItem
        bundle_item = CuttingBundleItem.objects.select_for_update().get(pk=bundle_item.pk)
        bundle = bundle or bundle_item.bundle
        size = size or bundle_item.bundle.size
        color = color or bundle_item.color
        pattern = pattern or bundle_item.pattern
        # Over-allocation guard — can't pay for more pieces than were cut.
        already = (
            StageWorkAssignment.objects
            .filter(bundle_item=bundle_item, voided_at__isnull=True)
            .aggregate(s=Sum('allocated_quantity'))['s'] or Decimal('0')
        )
        if already + qty > Decimal(bundle_item.count):
            raise ValidationError(
                f"Over-allocation: {already + qty} > {bundle_item.count} cut "
                f"for this item ({already} already allocated)."
            )

    amount = (rate * qty).quantize(_CENT, rounding=ROUND_HALF_UP)

    assignment = StageWorkAssignment.objects.create(
        stage_record=stage_record, worker=worker,
        bundle_item=bundle_item, bundle=bundle, size=size, color=color, pattern=pattern,
        allocated_quantity=qty, earning_rate_snapshot=rate,
        earning_amount_snapshot=amount, notes=notes, entered_by=user,
    )
    ledger_service.log_credit(
        worker=worker, category=WorkerLedgerEntry.Category.STAGE_EARNING,
        amount=amount, entry_date=entry_date or timezone.now().date(),
        created_by=user, assignment=assignment,
        notes=f"{stage_record.adda.code} · {ws.stage.name}",
    )
    return assignment


@transaction.atomic
def void_allocation(assignment, *, user):
    """Correct a mistaken allocation: reverse its ledger credit (balance nets
    to 0) + mark voided. Immutable — the row + entries are kept for audit; the
    item's allocated total frees up for re-allocation."""
    _ensure_management(user)
    # Lock the row + re-check under the lock so two concurrent voids can't both
    # pass the guard and double-reverse the credit (worker under-paid).
    assignment = StageWorkAssignment.objects.select_for_update().get(pk=assignment.pk)
    if assignment.voided_at is not None:
        raise ValidationError("Allocation is already voided.")
    credit = WorkerLedgerEntry.objects.filter(
        assignment=assignment,
        entry_type=WorkerLedgerEntry.EntryType.CREDIT,
        category=WorkerLedgerEntry.Category.STAGE_EARNING,
    ).first()
    if credit is not None and not credit.reversed_by.exists():
        ledger_service.reverse_entry(credit, actor=user, notes='Allocation voided')
    assignment.voided_at = timezone.now()
    assignment.save(update_fields=['voided_at', 'updated_at'])
    return assignment
