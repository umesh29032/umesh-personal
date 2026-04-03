import logging

from django.core.exceptions import ValidationError
from django.db import transaction

from ..models import ClothRoll
from ..constants import TransactionType
from .stock_service import StockService

logger = logging.getLogger(__name__)


class ClothService:
    """
    Domain service for ClothRoll operations.
    Handles inward stock, updates, and transfers while keeping the StockLedger in sync.
    """

    @staticmethod
    @transaction.atomic
    def create_cloth_roll(data: dict, created_by=None) -> ClothRoll:
        """
        Register a new cloth roll as INWARD stock.
        Creates the roll and logs the inward movement in one atomic operation.
        """
        roll = ClothRoll.objects.create(**data)
        StockService.log(
            transaction_type=TransactionType.INWARD,
            item=roll,
            quantity=roll.total_length,
            to_stage=roll.location,
            reference_note=f"Inward Roll {roll.roll_number}",
            created_by=created_by,
        )
        logger.info("ClothRoll %s created (inward) by %s", roll.roll_number, created_by)
        return roll

    @staticmethod
    @transaction.atomic
    def transfer_cloth_roll(roll: ClothRoll, to_stage, created_by=None) -> ClothRoll:
        """
        Move a cloth roll from its current location to another stage.
        Logs a TRANSFER entry in the ledger.
        """
        from_stage = roll.location
        if from_stage == to_stage:
            raise ValidationError("Cannot transfer a roll to the same stage it is already in.")

        roll.location = to_stage
        roll.save()

        StockService.log(
            transaction_type=TransactionType.TRANSFER,
            item=roll,
            quantity=roll.remaining_length,
            from_stage=from_stage,
            to_stage=to_stage,
            reference_note=f"Transfer Roll {roll.roll_number}",
            created_by=created_by,
        )
        logger.info("ClothRoll %s transferred from %s to %s", roll.roll_number, from_stage, to_stage)
        return roll
