import logging

from django.db import transaction

from ..models import Product
from ..constants import TransactionType
from .stock_service import StockService

logger = logging.getLogger(__name__)


class ProductService:
    """
    Domain service for finished goods (Product) operations.
    """

    @staticmethod
    @transaction.atomic
    def create_product(data: dict, created_by=None) -> Product:
        """
        Create a finished product and log a PRODUCTION entry in the StockLedger.
        The batch link is required for a traceable production record.
        """
        product = Product.objects.create(**data)

        batch = product.batch
        batch_label = batch.batch_number if batch else 'N/A'

        StockService.log(
            transaction_type=TransactionType.PRODUCTION,
            item=product,
            quantity=product.quantity,
            batch=batch,
            to_stage=product.location,
            reference_note=f"Produced in Batch {batch_label}",
            created_by=created_by,
        )
        logger.info("Product %s created (qty=%s) from batch %s", product.sku, product.quantity, batch_label)
        return product
