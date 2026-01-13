from django.contrib import admin
from .models import (
    Stage, Machine, ClothRoll, Batch, 
    BatchClothAssignment, BatchUserAssignment, BatchOperation, 
    Product, StockLedger
)

@admin.register(Stage)
class StageAdmin(admin.ModelAdmin):
    list_display = ('name', 'stage_type', 'is_active')
    search_fields = ('name',)
    list_filter = ('stage_type', 'is_active')

@admin.register(Machine)
class MachineAdmin(admin.ModelAdmin):
    list_display = ('name', 'machine_type', 'stage', 'is_active')
    list_filter = ('stage', 'is_active')
    search_fields = ('name', 'machine_type')

@admin.register(ClothRoll)
class ClothRollAdmin(admin.ModelAdmin):
    list_display = ('roll_number', 'cloth_type', 'remaining_length', 'location', 'status')
    list_filter = ('cloth_type', 'status', 'location')
    search_fields = ('roll_number', 'supplier')

class BatchClothAssignmentInline(admin.TabularInline):
    model = BatchClothAssignment
    extra = 1

class BatchUserAssignmentInline(admin.TabularInline):
    model = BatchUserAssignment
    extra = 1

@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ('batch_number', 'name', 'current_stage', 'status', 'created_at')
    list_filter = ('status', 'current_stage')
    search_fields = ('batch_number', 'name')
    inlines = [BatchClothAssignmentInline, BatchUserAssignmentInline]

@admin.register(BatchOperation)
class BatchOperationAdmin(admin.ModelAdmin):
    list_display = ('batch', 'stage', 'user', 'machine', 'start_time', 'output_quantity')
    list_filter = ('stage', 'user', 'machine')
    search_fields = ('batch__batch_number',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('sku', 'name', 'batch', 'quantity', 'location')
    search_fields = ('sku', 'name')
    list_filter = ('category', 'location')

@admin.register(StockLedger)
class StockLedgerAdmin(admin.ModelAdmin):
    list_display = ('date', 'transaction_type', 'item', 'quantity', 'from_stage', 'to_stage', 'batch')
    list_filter = ('transaction_type', 'date')
    search_fields = ('batch__batch_number',)
