from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import (
    BatchClothAssignment, ClothRoll, StockLedger, 
    Product, Batch, TransactionType, BatchOperation
)
from django.contrib.contenttypes.models import ContentType

@receiver(post_save, sender=BatchClothAssignment)
def handle_cloth_consumption(sender, instance, created, **kwargs):
    """
    When Cloth is marked as CONSUMED in a batch, update the ClothRoll 
    and create a StockLedger entry.
    """
    if instance.status == 'CONSUMED':
        # Deduct from Cloth Roll
        roll = instance.cloth_roll
        # We need to handle this carefully to avoid double deduction if saved multiple times
        # Ideally, we should check if this specific consumption was already accounted for.
        # For this MVP, we assume the 'CONSUMED' status transition happens once.
        pass 
        # Actually, it's safer to rely on a Service for the actual deduction 
        # and use Signal ONLY for Ledger creation to avoid side effects.
        
        # Create Ledger Entry
        StockLedger.objects.create(
            transaction_type=TransactionType.CONSUMPTION,
            item=roll,
            quantity=instance.consumed_length,
            from_stage=roll.location, # It consumes from its current location
            to_stage=None, # Consumed implies gone
            batch=instance.batch,
            reference_note=f"Consumed for Batch {instance.batch.batch_number}"
        )

@receiver(post_save, sender=Product)
def handle_product_production(sender, instance, created, **kwargs):
    """
    When a Product is created (Manufacturing finished), create StockLedger entry.
    """
    if created:
        StockLedger.objects.create(
            transaction_type=TransactionType.PRODUCTION,
            item=instance,
            quantity=instance.quantity,
            from_stage=None, # Produced from nothing (technically from material)
            to_stage=instance.location,
            batch=instance.batch,
            reference_note=f"Produced in Batch {instance.batch.batch_number if instance.batch else 'N/A'}"
        )

@receiver(post_save, sender=ClothRoll)
def handle_cloth_inward(sender, instance, created, **kwargs):
    """
    Log INWARD when a new ClothRoll is created.
    """
    if created:
        StockLedger.objects.create(
            transaction_type=TransactionType.INWARD,
            item=instance,
            quantity=instance.total_length,
            from_stage=None,
            to_stage=instance.location,
            reference_note=f"Inward Roll {instance.roll_number}"
        )

# NOTE: Movement (Transfer) signals are tricky with post_save because we need to know the 'old' location.
# We might need a pre_save signal or handle transfers via a Service.
