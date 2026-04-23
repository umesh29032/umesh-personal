import logging

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from ..models import (
    Batch, BatchClothAssignment, BatchUserAssignment,
    BatchOperation, ClothRoll, Stage,
)
from ..constants import BatchStatus, TransactionType
from .stock_service import StockService

logger = logging.getLogger(__name__)

# Allowed status transitions — enforced at service level.
# Exported so views can show available transitions without duplicating the map.
VALID_TRANSITIONS = {
    BatchStatus.PLANNED:   [BatchStatus.WIP, BatchStatus.CANCELLED],
    BatchStatus.WIP:       [BatchStatus.COMPLETED, BatchStatus.CANCELLED],
    BatchStatus.COMPLETED: [],
    BatchStatus.CANCELLED: [],
}


class BatchService:
    """
    Domain service for all Batch workflow operations.
    All write operations are atomic and explicit — no signals involved.
    """

    # ── Batch lifecycle ───────────────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def create_batch(data: dict, user) -> Batch:
        data['created_by'] = user
        batch = Batch.objects.create(**data)
        logger.info("Batch %s created by %s", batch.batch_number, user)
        return batch

    @staticmethod
    @transaction.atomic
    def transition_status(batch: Batch, new_status: str) -> Batch:
        """
        Move a batch to a new status, enforcing the allowed transition rules.
        Raises ValidationError for invalid transitions.
        """
        allowed = VALID_TRANSITIONS.get(batch.status, [])
        if new_status not in allowed:
            raise ValidationError(
                f"Cannot move batch from '{batch.status}' to '{new_status}'. "
                f"Allowed: {allowed or 'none (terminal state)'}."
            )
        batch.status = new_status
        batch.save()
        logger.info("Batch %s transitioned to %s", batch.batch_number, new_status)
        return batch

    @staticmethod
    @transaction.atomic
    def move_to_stage(batch: Batch, to_stage: Stage) -> Batch:
        batch.current_stage = to_stage
        batch.save()
        return batch

    # ── Cloth assignments ─────────────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def assign_cloth(batch: Batch, cloth_roll: ClothRoll, reserved_length, created_by=None) -> BatchClothAssignment:
        """Reserve cloth for a batch (Lay Plan step)."""
        if reserved_length <= 0:
            raise ValidationError("Reserved length must be greater than 0.")
        # Re-fetch with lock to prevent race conditions
        cloth_roll = ClothRoll.objects.select_for_update().get(pk=cloth_roll.pk)
        if reserved_length > cloth_roll.remaining_length:
            raise ValidationError(
                f"Reserved length ({reserved_length}m) exceeds available cloth "
                f"on roll '{cloth_roll.roll_number}' ({cloth_roll.remaining_length}m)."
            )

        assignment = BatchClothAssignment.objects.create(
            batch=batch,
            cloth_roll=cloth_roll,
            reserved_length=reserved_length,
            status='RESERVED',
        )
        logger.info("Cloth roll %s reserved (%sm) for batch %s", cloth_roll.roll_number, reserved_length, batch.batch_number)
        return assignment

    @staticmethod
    @transaction.atomic
    def process_cutting(
        assignment: BatchClothAssignment,
        consumed_length,
        wastage_length,
        created_by=None,
    ) -> BatchClothAssignment:
        """
        Record actual cloth consumption and wastage for a batch.
        Updates the cloth roll's remaining length and logs both CONSUMPTION
        and WASTAGE entries in the StockLedger explicitly.
        """
        if consumed_length < 0 or wastage_length < 0:
            raise ValidationError("Consumed and wastage lengths cannot be negative.")

        total_used = consumed_length + wastage_length
        if total_used > assignment.reserved_length:
            raise ValidationError(
                f"Consumed ({consumed_length}m) + wastage ({wastage_length}m) = {total_used}m "
                f"exceeds reserved length ({assignment.reserved_length}m)."
            )

        roll = ClothRoll.objects.select_for_update().get(pk=assignment.cloth_roll_id)
        if total_used > roll.remaining_length:
            raise ValidationError(
                f"Not enough cloth on roll '{roll.roll_number}'. "
                f"Remaining: {roll.remaining_length}m, Required: {total_used}m."
            )

        # Update assignment
        assignment.consumed_length = consumed_length
        assignment.wastage_length = wastage_length
        assignment.status = 'CONSUMED'
        assignment.save()

        # Deduct from cloth roll (triggers status auto-update in ClothRoll.save)
        roll.remaining_length -= total_used
        roll.save()

        # Explicit ledger entries — no signals
        StockService.log(
            transaction_type=TransactionType.CONSUMPTION,
            item=roll,
            quantity=consumed_length,
            batch=assignment.batch,
            from_stage=roll.location,
            reference_note=f"Consumed for Batch {assignment.batch.batch_number}",
            created_by=created_by,
        )
        if wastage_length > 0:
            StockService.log(
                transaction_type=TransactionType.WASTAGE,
                item=roll,
                quantity=wastage_length,
                batch=assignment.batch,
                from_stage=roll.location,
                reference_note=f"Wastage from Batch {assignment.batch.batch_number}",
                created_by=created_by,
            )

        logger.info(
            "Cutting processed for batch %s: consumed=%sm, wastage=%sm on roll %s",
            assignment.batch.batch_number, consumed_length, wastage_length, roll.roll_number,
        )
        return assignment

    # ── Worker assignments ────────────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def assign_user(batch: Batch, user, role: str) -> BatchUserAssignment:
        """
        Assign a worker to a batch. Re-activates if already existed as inactive.
        """
        assignment, created = BatchUserAssignment.objects.get_or_create(
            batch=batch, user=user, role=role,
            defaults={'is_active': True},
        )
        if not created and not assignment.is_active:
            assignment.is_active = True
            assignment.save()
        return assignment

    @staticmethod
    @transaction.atomic
    def remove_user(assignment: BatchUserAssignment) -> BatchUserAssignment:
        """
        Soft-delete a worker assignment. Preserves history for audit purposes.
        """
        assignment.is_active = False
        assignment.save()
        logger.info("Worker %s soft-removed from batch %s", assignment.user.email, assignment.batch.batch_number)
        return assignment

    # ── Operations ────────────────────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def log_operation(
        batch: Batch,
        stage: Stage,
        user,
        machine,
        start_time,
        end_time=None,
        output_quantity: int = 0,
        notes: str = '',
    ) -> BatchOperation:
        return BatchOperation.objects.create(
            batch=batch,
            stage=stage,
            user=user,
            machine=machine,
            start_time=start_time,
            end_time=end_time,
            output_quantity=output_quantity,
            notes=notes,
        )

    # ── Validation helpers ────────────────────────────────────────────────────

    @staticmethod
    def can_delete_stage(stage: Stage) -> bool:
        """
        Returns False if any WIP batch is currently assigned to this stage.
        Used by StageDeleteView before allowing deletion.
        """
        return not Batch.objects.filter(current_stage=stage, status=BatchStatus.WIP).exists()
