"""
StockService — single writer for the StockLedger.

Why a service (vs a signal)? Signals fire OUTSIDE the calling transaction.
A failed downstream save would leave a phantom ledger entry. By calling
`StockService.log(...)` from inside `@transaction.atomic`, the ledger row
commits or rolls back atomically with the rest of the operation.

`ContentType.objects.get_for_model(item)` resolves the polymorphic FK
backing `StockLedger.item` (a GenericForeignKey).
"""
from django.contrib.contenttypes.models import ContentType

from ..models import StockLedger
from ..constants import TransactionType


class StockService:
    """
    Central service for writing to the StockLedger.
    All ledger entries MUST go through this method — never via signals.
    This ensures every entry is part of an atomic transaction in the calling service.
    """

    @staticmethod
    def log(
        transaction_type: str,
        item,
        quantity,
        batch=None,
        from_stage=None,
        to_stage=None,
        reference_note: str = '',
        created_by=None,
    ) -> StockLedger:
        """
        Create a single ledger entry.

        Args:
            transaction_type: One of TransactionType choices
            item: Any model instance (ClothRoll, Product, etc.)
            quantity: Amount moved/consumed/produced
            batch: Optional Batch context
            from_stage: Origin stage (for transfers, consumptions)
            to_stage: Destination stage (for inwards, transfers, production)
            reference_note: Human-readable description
            created_by: User who triggered this (request.user)
        """
        return StockLedger.objects.create(
            transaction_type=transaction_type,
            content_type=ContentType.objects.get_for_model(item),
            object_id=item.pk,
            quantity=quantity,
            batch=batch,
            from_stage=from_stage,
            to_stage=to_stage,
            reference_note=reference_note,
            created_by=created_by,
        )
