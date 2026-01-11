
import os
import django
import sys

# Setup Django Environment
sys.path.append('/home/tech/umesh-personal/django_inventory/config')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from inventory.models import *
from inventory.services import InventoryService
from inventory.constants import *
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

def run_verification():
    print(">>> Setting up test data...")
    # Cleanup Old Data
    Batch.objects.filter(batch_number='BATCH-101').delete()
    ClothRoll.objects.filter(roll_number='ROLL-001').delete()
    Product.objects.filter(sku='TSHIRT-RED-M').delete()

    # Create Staff
    user, _ = User.objects.get_or_create(email='admin@test.com', defaults={'first_name': 'Test', 'last_name': 'Admin'})
    
    # Create Stages
    warehouse, _ = Stage.objects.get_or_create(name='Warehouse', stage_type=StageType.STORAGE)
    cutting, _ = Stage.objects.get_or_create(name='Cutting Floor', stage_type=StageType.PROCESSING)
    stitching, _ = Stage.objects.get_or_create(name='Stitching Unit', stage_type=StageType.PROCESSING)
    
    # Create Machine
    machine, _ = Machine.objects.get_or_create(name='Juki 9000', stage=stitching, machine_type='Single Needle')

    # Create Cloth Roll
    roll = ClothRoll.objects.create(
        roll_number='ROLL-001',
        cloth_type=ClothType.COTTON,
        color=ColorChoice.RED,
        width=44,
        total_length=100,
        remaining_length=100,
        cost_per_meter=100,
        location=warehouse
    )
    print(f"Created Roll: {roll}")

    print("\n>>> Step 1: Create Batch & Reserve Cloth")
    batch_data = {
        'batch_number': 'BATCH-101',
        'name': 'Red T-Shirts',
        'current_stage': warehouse,
        'created_by': user
    }
    # Reserve 60m
    batch = InventoryService.create_batch(batch_data, {roll.id: 60})
    print(f"Created Batch: {batch}")
    print(f"Assignments: {batch.cloth_assignments.all()}")

    print("\n>>> Step 2: Cutting (Consumption)")
    # Consume 58m, Wastage 2m
    InventoryService.process_cutting(batch.id, {roll.id: {'consumed': 58, 'wastage': 2}})
    
    roll.refresh_from_db()
    print(f"Roll after cutting: {roll.remaining_length}m (Expected 40.00)")
    
    # Check Ledger
    ledger = StockLedger.objects.filter(batch=batch, transaction_type=TransactionType.CONSUMPTION).first()
    print(f"Ledger Entry: {ledger}")

    print("\n>>> Step 3: Move to Stitching")
    InventoryService.move_batch(batch.id, stitching.id)
    batch.refresh_from_db()
    print(f"Batch Location: {batch.current_stage.name}")

    print("\n>>> Step 5: Log Stitching Operation")
    op = InventoryService.log_operation(batch.id, user, machine.id, stitching.id, timezone.now())
    print(f"Logged Operation: {op}")

    print("\n>>> Step 8: Finish & Create Products")
    prod_data = {
        'sku': 'TSHIRT-RED-M',
        'name': 'Red T-Shirt M',
        'size': 'M',
        'color': 'Red',
        'quantity': 50,
        'price': 500,
        'location': warehouse
    }
    product = InventoryService.finish_batch(batch.id, prod_data)
    print(f"Created Product: {product} Qty: {product.quantity}")
    
    # Check Batch Status
    batch.refresh_from_db()
    print(f"Final Batch Status: {batch.status}")

    # Check Product Stock Ledger
    prod_ledger = StockLedger.objects.filter(batch=batch, transaction_type=TransactionType.PRODUCTION).first()
    print(f"Product Ledger: {prod_ledger}")

if __name__ == '__main__':
    try:
        run_verification()
        print("\n✅ VERIFICATION SUCCESSFUL")
    except Exception as e:
        print(f"\n❌ VERIFICATION FAILED: {e}")
        import traceback
        traceback.print_exc()
