from django.db import models

class StageType(models.TextChoices):
    STORAGE = 'STORAGE', 'Storage (Warehouse)'
    PROCESSING = 'PROCESSING', 'Processing (Factory Floor)'

class BatchStatus(models.TextChoices):
    PLANNED = 'PLANNED', 'Planned'
    WIP = 'WIP', 'Work In Progress'
    COMPLETED = 'COMPLETED', 'Completed'
    CANCELLED = 'CANCELLED', 'Cancelled'

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
