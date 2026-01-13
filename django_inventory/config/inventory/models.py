from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from .constants import (
    StageType, BatchStatus, ClothType, UnitChoice, 
    RoleChoice, TransactionType, ColorChoice
)

class Stage(models.Model):
    """
    Represents a physical or logical location/stage in the manufacturing process.
    E.g., "Adda 1 (Cutting)", "Warehouse", "Stitching Unit".
    """
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    stage_type = models.CharField(
        max_length=20, 
        choices=StageType.choices, 
        default=StageType.PROCESSING
    )
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.stage_type})"


class Machine(models.Model):
    """
    Represents a machine used in the manufacturing process.
    Linked to a specific stage.
    """
    name = models.CharField(max_length=255)
    machine_type = models.CharField(max_length=100, blank=True)  # E.g., "Single Needle", "Overlock"
    stage = models.ForeignKey(Stage, on_delete=models.CASCADE, related_name='machines')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - {self.stage.name}"


class ClothRoll(models.Model):
    """
    Represents raw material (Cloth Rolls).
    """
    roll_number = models.CharField(max_length=100, unique=True)
    cloth_type = models.CharField(max_length=20, choices=ClothType.choices)
    color = models.CharField(max_length=20, choices=ColorChoice.choices, default=ColorChoice.RED)
    width = models.DecimalField(max_digits=10, decimal_places=2, help_text="Width in inches/cm")
    gsm = models.IntegerField(help_text="Grams per Square Meter", blank=True, null=True)
    
    total_length = models.DecimalField(max_digits=10, decimal_places=2, help_text="Original length in meters")
    remaining_length = models.DecimalField(max_digits=10, decimal_places=2, help_text="Current usable length")
    
    supplier = models.CharField(max_length=255, blank=True, null=True)
    cost_per_meter = models.DecimalField(max_digits=10, decimal_places=2)
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, editable=False)
    
    # Location tracking - usually starts in Storage
    location = models.ForeignKey(Stage, on_delete=models.SET_NULL, null=True, related_name='cloth_rolls')
    batch_alloted = models.ForeignKey('Batch', on_delete=models.SET_NULL, null=True, blank=True, related_name='alloted_cloth_rolls', verbose_name="Alloted Batch")
    purchased_date = models.DateField(blank=True, null=True,verbose_name="Purchased Date")
    exhaustion_date = models.DateField(blank=True, null=True,verbose_name="Exhaustion Date")

    
    status = models.CharField(
        max_length=20, 
        choices=[
            ('AVAILABLE', 'Available'),
            ('PARTIALLY_USED', 'Partially Used'),
            ('EXHAUSTED', 'Exhausted')
        ],
        default='AVAILABLE'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.total_cost = self.total_length * self.cost_per_meter
        if self.remaining_length <= 0:
            self.status = 'EXHAUSTED'
        elif self.remaining_length < self.total_length:
            self.status = 'PARTIALLY_USED'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Roll {self.roll_number} - {self.get_cloth_type_display()} ({self.remaining_length}m left)"


class Batch(models.Model):
    """
    The central entity representing a production run.
    Moves through stages.
    """
    batch_number = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255, help_text="E.g. T-Shirt Order #102")
    
    current_stage = models.ForeignKey(Stage, on_delete=models.SET_NULL, null=True, related_name='current_batches')
    status = models.CharField(max_length=20, choices=BatchStatus.choices, default=BatchStatus.PLANNED)
    
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_date = models.DateTimeField(null=True, blank=True)
    
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        from django.utils import timezone
        if self.status == BatchStatus.COMPLETED and not self.completed_date:
            self.completed_date = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.batch_number} - {self.name} ({self.status})"


class BatchClothAssignment(models.Model):
    """
    Step 1 & 2: Link Cloth Rolls to Batch.
    Handles Reservation (Lay Plan) and Actual Consumption (Cutting).
    """
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='cloth_assignments')
    cloth_roll = models.ForeignKey(ClothRoll, on_delete=models.CASCADE, related_name='batch_assignments')
    
    reserved_length = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Planned usage")
    consumed_length = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Actual usage")
    wastage_length = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Wastage during cutting")
    
    status = models.CharField(
        max_length=20,
        choices=[('RESERVED', 'Reserved'), ('CONSUMED', 'Consumed')],
        default='RESERVED'
    )
    
    assigned_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.batch.batch_number} - {self.cloth_roll.roll_number}"


class BatchUserAssignment(models.Model):
    """
    Step 4: Assign Users (Karigars) to a Batch.
    Many Users can be assigned to One Batch.
    One User can be assigned to Many Batches.
    """
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='user_assignments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='batch_assignments')
    role = models.CharField(max_length=50, choices=RoleChoice.choices)
    
    assigned_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('batch', 'user', 'role')

    def __str__(self):
        return f"{self.user.username} - {self.batch.batch_number} ({self.role})"


class BatchOperation(models.Model):
    """
    Step 5, 6, 7: Granular tracking of work performed on a batch.
    Tracks User, Machine, Time, and Stage.
    """
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='operations')
    stage = models.ForeignKey(Stage, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    machine = models.ForeignKey(Machine, on_delete=models.SET_NULL, null=True, blank=True)
    
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    
    output_quantity = models.IntegerField(default=0, help_text="Qty processed in this session")
    notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.batch.batch_number} - {self.stage.name} - {self.user.username if self.user else 'Unknown'}"


class Product(models.Model):
    """
    Step 8: Finished Goods.
    """
    sku = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=100, blank=True)  # T-Shirt, Pants, etc.
    size = models.CharField(max_length=20)
    color = models.CharField(max_length=50)
    
    batch = models.ForeignKey(Batch, on_delete=models.SET_NULL, null=True, related_name='products')
    
    quantity = models.IntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Selling Price")
    manufacturing_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    location = models.ForeignKey(Stage, on_delete=models.SET_NULL, null=True, help_text="Warehouse Location")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.sku})"


class StockLedger(models.Model):
    """
    Universal Stock Ledger - The Single Source of Truth for all movements.
    Tracks Cloth Rolls, Products, and potentially standard items.
    """
    transaction_type = models.CharField(max_length=50, choices=TransactionType.choices)
    date = models.DateTimeField(auto_now_add=True)
    
    # Generic relation to track what item moved (ClothRoll or Product)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    item = GenericForeignKey('content_type', 'object_id')
    
    quantity = models.DecimalField(max_digits=10, decimal_places=2, help_text="Qty or Length")
    
    from_stage = models.ForeignKey(Stage, on_delete=models.SET_NULL, null=True, blank=True, related_name='outward_ledger')
    to_stage = models.ForeignKey(Stage, on_delete=models.SET_NULL, null=True, blank=True, related_name='inward_ledger')
    
    batch = models.ForeignKey(Batch, on_delete=models.SET_NULL, null=True, blank=True, help_text="Context of movement")
    reference_note = models.CharField(max_length=255, blank=True)
    
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.transaction_type} - {self.item} ({self.quantity})"
