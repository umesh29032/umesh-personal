"""
Inventory domain models — production lifecycle from cloth roll to payment.

Django ORM primitives used heavily in this file:
  - models.Model            → one Python class = one Postgres table.
  - ForeignKey / M2M        → relational links; `on_delete=` rules cascade behavior.
  - CharField(choices=...)  → enum-like column; choices live in `constants.py`.
  - auto_now_add            → set on INSERT (created_at).
  - auto_now                → set on every UPDATE (updated_at).
  - GenericForeignKey       → "polymorphic" FK via (content_type, object_id);
                              used by StockLedger to track ClothRoll / Product / future items.
  - CheckConstraint         → enforced by Postgres; app cannot violate it.
  - UniqueConstraint        → multi-column uniqueness (db-level).
  - Meta.indexes            → composite B-tree indexes for dashboard queries.
"""
from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

# All TextChoices enums live in one place so they can be reused by services + forms.
from .constants import (
    StageType, StageCategory, BatchStatus, BatchStageStatus,
    MachineAssignmentStatus, DispatchStatus, PaymentStatus, PaymentMode,
    ClothType, UnitChoice, RoleChoice, TransactionType, ColorChoice,
)


class Stage(models.Model):
    """
    Master stage catalog — physical or logical step in the production lifecycle.
    Examples: Layering, Marking, Cutting, Stitching, Packing, Vendor Dispatch, Payment.
    """
    name = models.CharField(max_length=255)
    code = models.SlugField(
        max_length=64, unique=True, null=True, blank=True,
        help_text="Stable identifier used by services (e.g. 'stitching'). Auto-slugified from name if blank.",
    )
    description = models.TextField(blank=True, null=True)
    stage_type = models.CharField(
        max_length=20,
        choices=StageType.choices,
        default=StageType.PROCESSING,
        db_index=True,
    )
    category = models.CharField(
        max_length=20,
        choices=StageCategory.choices,
        default=StageCategory.PRODUCTION,
        db_index=True,
        help_text="High-level lifecycle bucket for reporting and dashboards.",
    )
    default_is_mandatory = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"


class BatchType(models.Model):
    """
    Dynamic product category that owns a template of default stages.
    Examples: T-Shirt, Lower, 3-Patti. Users (with permission) can add new types at runtime.
    """
    name = models.CharField(max_length=100, unique=True)
    code = models.SlugField(max_length=40, unique=True, help_text="Used in batch_number prefix e.g. '3patti'")
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True, db_index=True)

    stages = models.ManyToManyField(
        Stage,
        through='BatchTypeStage',
        related_name='batch_types',
        help_text="Ordered default stages cloned onto each new batch of this type.",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_batch_types'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class BatchTypeStage(models.Model):
    """Template join: ordered stages that belong to a BatchType."""
    batch_type = models.ForeignKey(BatchType, on_delete=models.CASCADE, related_name='stage_templates')
    stage = models.ForeignKey(Stage, on_delete=models.PROTECT, related_name='type_templates')
    sequence_order = models.PositiveIntegerField(help_text="1-based ordinal within the batch type workflow.")
    is_mandatory = models.BooleanField(default=True)

    class Meta:
        ordering = ['batch_type', 'sequence_order']
        constraints = [
            models.UniqueConstraint(
                fields=['batch_type', 'stage'], name='unique_batchtype_stage'
            ),
            models.UniqueConstraint(
                fields=['batch_type', 'sequence_order'], name='unique_batchtype_sequence'
            ),
        ]

    def __str__(self):
        return f"{self.batch_type.code}#{self.sequence_order}: {self.stage.name}"


class Machine(models.Model):
    """
    Represents a machine used in the manufacturing process.
    Linked to a specific stage.
    """
    name = models.CharField(max_length=255)
    machine_type = models.CharField(max_length=100, blank=True)
    stage = models.ForeignKey(Stage, on_delete=models.CASCADE, related_name='machines')
    is_active = models.BooleanField(default=True, db_index=True)

    def __str__(self):
        return f"{self.name} - {self.stage.name}"


class ClothRoll(models.Model):
    """
    Represents raw material (Cloth Rolls).
    """
    roll_number = models.CharField(max_length=100, unique=True)
    cloth_type = models.CharField(max_length=20, choices=ClothType.choices, db_index=True)
    color = models.CharField(max_length=20, choices=ColorChoice.choices, default=ColorChoice.RED)
    width = models.DecimalField(max_digits=10, decimal_places=2, help_text="Width in inches/cm")
    gsm = models.IntegerField(help_text="Grams per Square Meter", blank=True, null=True)

    total_length = models.DecimalField(max_digits=10, decimal_places=2, help_text="Original length in meters")
    remaining_length = models.DecimalField(max_digits=10, decimal_places=2, help_text="Current usable length")

    supplier = models.CharField(max_length=255, blank=True, null=True)
    cost_per_meter = models.DecimalField(max_digits=10, decimal_places=2)
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, editable=False, default=0)

    location = models.ForeignKey(Stage, on_delete=models.SET_NULL, null=True, related_name='cloth_rolls')
    batch_alloted = models.ForeignKey(
        'Batch', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='alloted_cloth_rolls', verbose_name="Alloted Batch"
    )
    purchased_date = models.DateField(blank=True, null=True, verbose_name="Purchased Date")
    exhaustion_date = models.DateField(blank=True, null=True, verbose_name="Exhaustion Date")

    status = models.CharField(
        max_length=20,
        choices=[
            ('AVAILABLE', 'Available'),
            ('PARTIALLY_USED', 'Partially Used'),
            ('EXHAUSTED', 'Exhausted'),
        ],
        default='AVAILABLE',
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Recalculate total cost
        self.total_cost = self.total_length * self.cost_per_meter
        # Auto-update status based on remaining length
        if self.remaining_length <= 0:
            self.status = 'EXHAUSTED'
        elif self.remaining_length < self.total_length:
            self.status = 'PARTIALLY_USED'
        else:
            # remaining == total means untouched roll → reset to AVAILABLE
            self.status = 'AVAILABLE'
        super().save(*args, **kwargs)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(remaining_length__gte=0),
                name="clothroll_remaining_nonneg",
            ),
        ]

    def __str__(self):
        return f"Roll {self.roll_number} - {self.get_cloth_type_display()} ({self.remaining_length}m left)"


class Batch(models.Model):
    """
    Central production run. Moves through a sequence of BatchStage rows cloned
    from its BatchType template at creation time.
    """
    batch_number = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255, help_text="E.g. 3patti-2026-04-24")

    batch_type = models.ForeignKey(
        BatchType, on_delete=models.PROTECT, null=True, blank=True,
        related_name='batches',
        help_text="Product category — determines the default stage sequence.",
    )
    current_stage = models.ForeignKey(
        Stage, on_delete=models.SET_NULL, null=True, related_name='current_batches'
    )
    status = models.CharField(
        max_length=20, choices=BatchStatus.choices, default=BatchStatus.PLANNED, db_index=True
    )

    initial_quantity = models.PositiveIntegerField(
        default=0, help_text="Target input pieces at batch start."
    )
    final_quantity = models.PositiveIntegerField(
        default=0, help_text="Final pieces produced after last stage."
    )

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_date = models.DateTimeField(null=True, blank=True)

    is_active = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=['status', '-created_at'], name='batch_status_created_idx'),
            models.Index(fields=['batch_type', 'status'], name='batch_type_status_idx'),
        ]

    def save(self, *args, **kwargs):
        if self.status == BatchStatus.COMPLETED and not self.completed_date:
            self.completed_date = timezone.now()
        elif self.status != BatchStatus.COMPLETED:
            self.completed_date = None
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.batch_number} - {self.name} ({self.status})"


class BatchStage(models.Model):
    """
    Execution instance of a Stage for a specific Batch.
    Cloned from BatchTypeStage when the batch is created; users with permission
    may also add ad-hoc stages to a single batch without mutating the template.
    """
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='stages')
    stage = models.ForeignKey(Stage, on_delete=models.PROTECT, related_name='executions')
    sequence_order = models.PositiveIntegerField()
    is_mandatory = models.BooleanField(default=True)

    status = models.CharField(
        max_length=20,
        choices=BatchStageStatus.choices,
        default=BatchStageStatus.PENDING,
        db_index=True,
    )

    input_qty = models.PositiveIntegerField(default=0, help_text="Pieces entering this stage.")
    output_qty = models.PositiveIntegerField(default=0, help_text="Pieces produced by this stage.")
    wastage_qty = models.PositiveIntegerField(default=0, help_text="Pieces discarded at this stage.")

    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['batch', 'sequence_order']
        constraints = [
            models.UniqueConstraint(
                fields=['batch', 'sequence_order'], name='unique_batch_sequence'
            ),
            models.UniqueConstraint(
                fields=['batch', 'stage'], name='unique_batch_stage'
            ),
            models.CheckConstraint(
                check=models.Q(input_qty__gte=models.F('output_qty') + models.F('wastage_qty')),
                name='batchstage_qty_reconciliation',
            ),
        ]
        indexes = [
            models.Index(fields=['batch', 'status'], name='batchstage_batch_status_idx'),
            models.Index(fields=['stage', 'status'], name='batchstage_stage_status_idx'),
        ]

    def __str__(self):
        return f"{self.batch.batch_number} · #{self.sequence_order} {self.stage.name}"


class BatchStageMachineAssignment(models.Model):
    """
    Stitching-phase fan-out: within a single BatchStage, work is distributed
    across multiple (machine, worker) pairs. Worker chosen by required skill.
    Sum of completed_qty across assignments reconciles with BatchStage.output_qty.
    """
    batch_stage = models.ForeignKey(
        BatchStage, on_delete=models.CASCADE, related_name='machine_assignments'
    )
    machine = models.ForeignKey('Machine', on_delete=models.PROTECT, related_name='batch_assignments')
    worker = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='machine_assignments'
    )
    skill_used = models.ForeignKey(
        'accounts.Skill', on_delete=models.SET_NULL, null=True, blank=True, related_name='machine_assignments'
    )

    assigned_qty = models.PositiveIntegerField(default=0)
    completed_qty = models.PositiveIntegerField(default=0)
    wastage_qty = models.PositiveIntegerField(default=0)

    status = models.CharField(
        max_length=20,
        choices=MachineAssignmentStatus.choices,
        default=MachineAssignmentStatus.ASSIGNED,
        db_index=True,
    )
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    assigned_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['batch_stage', 'machine', 'worker'],
                name='unique_stage_machine_worker',
            ),
            models.CheckConstraint(
                check=models.Q(assigned_qty__gte=models.F('completed_qty') + models.F('wastage_qty')),
                name='machineasg_qty_reconciliation',
            ),
        ]
        indexes = [
            models.Index(fields=['worker', 'status'], name='machasg_worker_status_idx'),
            models.Index(fields=['machine', 'status'], name='machasg_machine_status_idx'),
        ]

    def __str__(self):
        return f"{self.batch_stage} · {self.machine.name} · {self.worker.email}"


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
        default='RESERVED',
        db_index=True,
    )

    assigned_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['batch', 'status'], name='batchcloth_batch_status_idx'),
        ]

    def __str__(self):
        return f"{self.batch.batch_number} - {self.cloth_roll.roll_number}"


class BatchUserAssignment(models.Model):
    """
    Step 4: Assign Users (Karigars) to a Batch.
    """
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='user_assignments')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='batch_assignments'
    )
    role = models.CharField(max_length=50, choices=RoleChoice.choices, db_index=True)

    assigned_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['batch', 'user', 'role'],
                name='unique_batch_user_role',
            ),
        ]

    def __str__(self):
        # User model uses email as identifier (no username field)
        return f"{self.user.email} - {self.batch.batch_number} ({self.role})"


class BatchOperation(models.Model):
    """
    Granular worker-session log — who worked on which batch/stage/machine and for how long.
    One BatchStage contains many BatchOperation rows (one per worker session).
    """
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='operations')
    batch_stage = models.ForeignKey(
        BatchStage, on_delete=models.CASCADE, null=True, blank=True,
        related_name='operations',
        help_text="Execution-layer link. Nullable for legacy rows predating BatchStage.",
    )
    stage = models.ForeignKey(Stage, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    machine = models.ForeignKey(Machine, on_delete=models.SET_NULL, null=True, blank=True)
    skill_used = models.ForeignKey(
        'accounts.Skill', on_delete=models.SET_NULL, null=True, blank=True, related_name='operations'
    )

    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)

    output_quantity = models.IntegerField(default=0, help_text="Qty processed in this session")
    wastage_quantity = models.IntegerField(default=0, help_text="Qty wasted in this session")
    notes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'end_time'], name='op_user_endtime_idx'),
            models.Index(fields=['batch_stage', 'user'], name='op_bstage_user_idx'),
        ]

    def __str__(self):
        user_label = self.user.email if self.user else 'Unknown'
        return f"{self.batch.batch_number} - {self.stage.name} - {user_label}"


class Product(models.Model):
    """
    Step 8: Finished Goods.
    """
    sku = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=100, blank=True)
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
    Universal Stock Ledger — Single Source of Truth for all movements.
    Tracks Cloth Rolls, Products, and any future item types.
    Entries are created EXPLICITLY by services — never via signals.
    """
    transaction_type = models.CharField(
        max_length=50, choices=TransactionType.choices, db_index=True
    )
    date = models.DateTimeField(auto_now_add=True, db_index=True)

    # Generic relation: tracks ClothRoll or Product
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField(db_index=True)
    item = GenericForeignKey('content_type', 'object_id')

    quantity = models.DecimalField(max_digits=10, decimal_places=2, help_text="Qty or Length")

    from_stage = models.ForeignKey(
        Stage, on_delete=models.SET_NULL, null=True, blank=True, related_name='outward_ledger'
    )
    to_stage = models.ForeignKey(
        Stage, on_delete=models.SET_NULL, null=True, blank=True, related_name='inward_ledger'
    )

    batch = models.ForeignKey(
        Batch, on_delete=models.SET_NULL, null=True, blank=True,
        help_text="Context of movement", db_index=True
    )
    reference_note = models.CharField(max_length=255, blank=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ['-date']
        indexes = [
            # Composite index for the most common dashboard/report query
            models.Index(fields=['batch', 'transaction_type', '-date'], name='ledger_batch_type_date_idx'),
        ]

    def __str__(self):
        item_label = self.item or f"{self.content_type} #{self.object_id} (deleted)"
        return f"{self.transaction_type} - {item_label} ({self.quantity})"


# ═══════════════════════════════════════════════════════════════════
# LOGISTICS & FINANCE
# ═══════════════════════════════════════════════════════════════════

class Vendor(models.Model):
    """External vendor / buyer to whom finished batches are dispatched."""
    name = models.CharField(max_length=255, unique=True)
    contact_person = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    gst_number = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class VendorDispatch(models.Model):
    """Records a shipment of one batch (or part of it) to a vendor."""
    batch = models.ForeignKey(Batch, on_delete=models.PROTECT, related_name='dispatches')
    batch_stage = models.ForeignKey(
        BatchStage, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='dispatches',
    )
    vendor = models.ForeignKey(Vendor, on_delete=models.PROTECT, related_name='dispatches')

    vehicle_no = models.CharField(max_length=50, blank=True)
    driver_name = models.CharField(max_length=100, blank=True)
    driver_phone = models.CharField(max_length=20, blank=True)

    dispatched_qty = models.PositiveIntegerField(default=0)
    received_qty = models.PositiveIntegerField(default=0, help_text="Pieces confirmed by vendor on receipt.")
    transit_wastage = models.PositiveIntegerField(default=0)
    transport_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    status = models.CharField(
        max_length=20,
        choices=DispatchStatus.choices,
        default=DispatchStatus.SCHEDULED,
        db_index=True,
    )
    dispatched_at = models.DateTimeField(null=True, blank=True)
    received_at = models.DateTimeField(null=True, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='dispatches_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-dispatched_at', '-created_at']
        indexes = [
            models.Index(fields=['batch', 'status'], name='dispatch_batch_status_idx'),
            models.Index(fields=['vendor', 'status'], name='dispatch_vendor_status_idx'),
        ]

    def __str__(self):
        return f"Dispatch {self.batch.batch_number} → {self.vendor.name}"


class Payment(models.Model):
    """Payment received from a vendor against one or more dispatches of a batch."""
    batch = models.ForeignKey(Batch, on_delete=models.PROTECT, related_name='payments')
    vendor = models.ForeignKey(Vendor, on_delete=models.PROTECT, related_name='payments')
    dispatch = models.ForeignKey(
        VendorDispatch, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments'
    )

    amount = models.DecimalField(max_digits=12, decimal_places=2)
    mode = models.CharField(max_length=20, choices=PaymentMode.choices, default=PaymentMode.BANK_TRANSFER)
    reference = models.CharField(max_length=100, blank=True, help_text="Txn id / cheque no / UTR")
    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        db_index=True,
    )
    received_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='payments_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-received_at', '-created_at']
        indexes = [
            models.Index(fields=['batch', 'status'], name='payment_batch_status_idx'),
            models.Index(fields=['vendor', 'status'], name='payment_vendor_status_idx'),
        ]

    def __str__(self):
        return f"Payment ₹{self.amount} · {self.vendor.name} · {self.status}"


# ═══════════════════════════════════════════════════════════════════
# ROLE-BASED ACCESS CONTROL
# ═══════════════════════════════════════════════════════════════════

class Role(models.Model):
    """
    Named bundle of Django permissions. A User.role points to one Role.
    Superuser bypasses all checks; everyone else is gated by their role's permissions.
    Seeded defaults: Super Admin, Manager, Karigar (see migration data).
    """
    name = models.CharField(max_length=64, unique=True)
    code = models.SlugField(max_length=32, unique=True)
    description = models.TextField(blank=True)
    is_system = models.BooleanField(
        default=False,
        help_text="System roles (admin/manager/karigar) cannot be deleted.",
    )
    permissions = models.ManyToManyField(
        'auth.Permission', blank=True, related_name='inventory_roles',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name
