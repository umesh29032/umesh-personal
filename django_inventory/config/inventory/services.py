from django.db import transaction
from django.utils import timezone
from .models import (
    Batch, BatchClothAssignment, ClothRoll, 
    StockLedger, TransactionType, Stage,
    BatchOperation, BatchUserAssignment, Product
)
from .constants import BatchStatus

class InventoryService:
    @staticmethod
    @transaction.atomic
    def create_batch(batch_data, cloth_rolls):
        """
        Step 1: Create Batch types and Reserve Cloth.
        """
        batch = Batch.objects.create(**batch_data)
        
        for roll_id, reserved_len in cloth_rolls.items():
            roll = ClothRoll.objects.get(id=roll_id)
            BatchClothAssignment.objects.create(
                batch=batch,
                cloth_roll=roll,
                reserved_length=reserved_len,
                status='RESERVED'
            )
        return batch

    @staticmethod
    @transaction.atomic
    def process_cutting(batch_id, cutting_data):
        """
        Step 2: Cutting Stage - Record actual consumption.
        cutting_data = { roll_id: {consumed: 50, wastage: 2}, ... }
        """
        batch = Batch.objects.get(id=batch_id)
        
        for roll_id, data in cutting_data.items():
            assignment = BatchClothAssignment.objects.get(batch=batch, cloth_roll_id=roll_id)
            
            consumed = data['consumed']
            wastage = data['wastage']
            
            # Update Assignment
            assignment.consumed_length = consumed
            assignment.wastage_length = wastage
            assignment.status = 'CONSUMED'
            assignment.save()
            
            # Reduce Cloth Roll
            roll = assignment.cloth_roll
            roll.remaining_length -= (consumed + wastage)
            
            # Handle exhaustion logic if needed (Roll auto-updates status on save)
            roll.save() 
            
            # Ledger is handled by Signal on Assignment save (optional) 
            # OR we can do it here explicitly for better control.
            
        return batch

    @staticmethod
    @transaction.atomic
    def move_batch(batch_id, to_stage_id):
        """
        Step 3: Move Batch to next stage.
        """
        batch = Batch.objects.get(id=batch_id)
        current_stage = batch.current_stage
        to_stage = Stage.objects.get(id=to_stage_id)
        
        batch.current_stage = to_stage
        batch.save()
        
        # Log Movement in Ledger? 
        # Batches themselves are not usually "Stock" quantities in the ledger 
        # unless we track "WIP Units".
        
        return batch

    @staticmethod
    def log_operation(batch_id, user, machine_id, stage_id, start_time):
        """
        Start an operation (e.g. Stitching).
        """
        return BatchOperation.objects.create(
            batch_id=batch_id,
            user=user,
            machine_id=machine_id,
            stage_id=stage_id,
            start_time=start_time
        )

    @staticmethod
    @transaction.atomic
    def finish_batch(batch_id, product_data):
        """
        Step 8: Finish Batch and Create Products.
        product_data = { sku, name, size, color, quantity, price, location_id }
        """
        batch = Batch.objects.get(id=batch_id)
        
        # Create Product
        product = Product.objects.create(
            batch=batch,
            **product_data
        )
        
        # Update Batch Status
        batch.status = BatchStatus.COMPLETED
        batch.save()
        
        # Ledger is handled by Signal on Product creation
        
        return product
