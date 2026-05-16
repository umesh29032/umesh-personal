from django.db import models

class StageType(models.TextChoices):
    STORAGE = 'STORAGE', 'Storage (Warehouse)'
    PROCESSING = 'PROCESSING', 'Processing (Factory Floor)'

class StageCategory(models.TextChoices):
    """High-level classification of a stage across production lifecycle."""
    PRODUCTION = 'PRODUCTION', 'Production'
    LOGISTICS = 'LOGISTICS', 'Logistics'
    FINANCIAL = 'FINANCIAL', 'Financial'

class BatchStatus(models.TextChoices):
    DRAFT = 'DRAFT', 'Draft'
    PLANNED = 'PLANNED', 'Planned'
    WIP = 'WIP', 'Work In Progress'
    COMPLETED = 'COMPLETED', 'Completed'
    CANCELLED = 'CANCELLED', 'Cancelled'

class BatchStageStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
    COMPLETED = 'COMPLETED', 'Completed'
    SKIPPED = 'SKIPPED', 'Skipped'

class MachineAssignmentStatus(models.TextChoices):
    ASSIGNED = 'ASSIGNED', 'Assigned'
    IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
    COMPLETED = 'COMPLETED', 'Completed'

class DispatchStatus(models.TextChoices):
    SCHEDULED = 'SCHEDULED', 'Scheduled'
    IN_TRANSIT = 'IN_TRANSIT', 'In Transit'
    DELIVERED = 'DELIVERED', 'Delivered'
    RETURNED = 'RETURNED', 'Returned'

class PaymentStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    PARTIAL = 'PARTIAL', 'Partially Received'
    RECEIVED = 'RECEIVED', 'Received'
    FAILED = 'FAILED', 'Failed'

class PaymentMode(models.TextChoices):
    CASH = 'CASH', 'Cash'
    BANK_TRANSFER = 'BANK_TRANSFER', 'Bank Transfer'
    UPI = 'UPI', 'UPI'
    CHEQUE = 'CHEQUE', 'Cheque'
    OTHER = 'OTHER', 'Other'

class ClothType(models.TextChoices):
    COTTON = 'COTTON', 'Cotton'
    HOSIERY = 'HOSIERY', 'Hosiery'
    POLYESTER = 'POLYESTER', 'Polyester'
    LINEN = 'LINEN', 'Linen'
    OTHER = 'OTHER', 'Other'

class ColorChoice(models.TextChoices):
    RED = 'Red', 'Red'
    BLUE = 'Blue', 'Blue'
    GREEN = 'Green', 'Green'
    YELLOW = 'Yellow', 'Yellow'
    RAMA = 'Rama', 'Rama'

class UnitChoice(models.TextChoices):
    METER = 'METER', 'Meter'
    KG = 'KG', 'Kilogram'
    PIECE = 'PIECE', 'Piece'

class RoleChoice(models.TextChoices):
    SUPERVISOR = 'SUPERVISOR', 'Supervisor'
    CUTTING_MASTER = 'CUTTING_MASTER', 'Cutting Master'
    KARIGAR = 'KARIGAR', 'Karigar'
    HELPER = 'HELPER', 'Helper'

class TransactionType(models.TextChoices):
    INWARD = 'INWARD', 'Inward (Purchase)'
    OUTWARD = 'OUTWARD', 'Outward (Sale/Dispatch)'
    CONSUMPTION = 'CONSUMPTION', 'Consumption'
    WASTAGE = 'WASTAGE', 'Wastage'
    TRANSFER = 'TRANSFER', 'Transfer (Location Change)'
    PRODUCTION = 'PRODUCTION', 'Production (Finished Goods)'
    ADJUSTMENT = 'ADJUSTMENT', 'Adjustment'
